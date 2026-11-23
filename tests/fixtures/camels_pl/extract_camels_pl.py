"""Extract the reference inputs and cases of CAMELS-PL 2.1.0 (Nogat CMP-5.1, CMP-6.1).

CAMELS-PL 2.1.0 (Brzezińska et al. 2026, Zenodo record 23275336, CC BY 4.0) publishes
for each of its 869 gauges hydrological signatures computed from the daily discharge it
publishes beside them (``CAMELS_PL_hydrologic_attributes.csv``, the data description's
Table 7). Thirteen gauges, across sizes and regimes and with zero flows, are the
reference cases of Hydrolog's signatures (Nogat plan ``2026-11-22-camels-pl``, step 5).
This script copies from the release's ZIP only what the tests read:

* ``camels_pl_<gauge>.csv.gz``: the rows of the gauge's
  ``timeseries/CAMELS_PL_hydromet_timeseries_<gauge>.csv`` that have a discharge, with
  the columns ``date``, ``discharge_vol_obs`` and ``discharge_spec_obs`` as published;
* ``CAMELS_PL_hydrologic_attributes.csv``: the header and the rows of the thirteen
  gauges of the release's file, as published;
* ``CAMELS_PL_ATTRIBUTION.txt``: the release (record, version, DOI), the SHA-256 of
  the ZIP, of the data description and of each member read (Nogat CMP-6.10), the
  citation and the provider lines S, P, L and LP (Nogat DEV §20, DEV-20.12);
* ``tests/fixtures/formulas/camels-pl-cases.json``: the reference cases, each with the
  sample CAMELS-PL computed on and each step where its computation and Hydrolog's part
  (CMP-6.1), the baseflow index as a discrepancy with its cause (CMP-5.2); the locator
  of each names the release and the SHA-256 of the files it reads (CMP-6.10).

How CAMELS-PL computed each signature was found on all 869 gauges on 2026-11-23: the
code of CAMELS-DE (Dolich 2024, ``08_hydrologic_attributes.ipynb``) with the
hydrological year from 1 November and numpy's ``nearest`` quantiles reproduces every
value but the baseflow index, which the two-pass filter of the ``baseflow`` package
(Xie et al. 2020) reproduces on the data to 2023-12-31. The cases say so.

Run it once from the repository's root, with the two files of the release's record (a
newer release changes the cases only by a deliberate change, CMP-6.10)::

    uv run python tests/fixtures/camels_pl/extract_camels_pl.py CAMELS_PL_2.1.zip \\
        CAMELS_PL_Data_Description.pdf
"""

import csv
import gzip
import hashlib
import io
import json
import math
import sys
import textwrap
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from hydrolog._attribution import IMGW_PROCESSED, IMGW_SOURCE
from hydrolog.statistics.baseflow import baseflow_index, lyne_hollick_filter

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "tests" / "fixtures" / "camels_pl"
CASES = ROOT / "tests" / "fixtures" / "formulas" / "camels-pl-cases.json"
RELATIVE = "tests/fixtures/camels_pl"

RECORD = "23275336"
VERSION = "2.1.0"
DOI = "10.5281/zenodo.23275336"
"""The DOI of release 2.1.0, never the concept DOI (Nogat DEV §20)."""
RELEASE = f"CAMELS-PL {VERSION} (Zenodo record {RECORD}, doi:{DOI})"
ZIP_MD5 = "05d4c1884d535c78299477ac8a00703a"
"""The checksum the record lists for the ZIP."""
ZIP_SHA256 = "7e8425dd6e078150c98ad26ed4903a52052da1481f393a52f4ac936bbb15cf4e"
ZIP_SIZE = 1_670_805_350
DESCRIPTION = "CAMELS_PL_Data_Description.pdf"
DESCRIPTION_SHA256 = "46322337d184bc29107650e59309563e5ee3a94c35ddbcb53cea563e5734a1de"
GAUGES = (
    "150150030",
    "149180140",
    "149200260",
    "150190010",
    "152210050",
    "153199999",
    "152180100",
    "153170050",
    "152160060",
    "150160180",
    "153220170",
    "152140020",
    "154180150",
)
"""Thirteen gauges from 6 to 193,728 km2: mountain (Sudetes, Carpathians), upland,
lowland, lake-district and wetland rivers, the Odra and the Wisła; four with zero flows
(Brynica, Czarna, Gardęga, Noteć), two with days missing inside their complete years
(Łubinka, Czarna), three that start late (Kamienna at Jakuszyce, Gardęga, Łubinka)."""
FIRST_DAY, LAST_DAY = date(1951, 1, 1), date(2025, 10, 31)
"""The span of every series file of CAMELS-PL 2.1.0 (its data description, 6.1)."""
BFI_LAST_DAY = date(2023, 12, 31)
MISSING_PERCENT = 5

CITATION = (
    "Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., "
    "Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: "
    "hydro-meteorological time series and landscape attributes for 869 catchments in "
    "Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0"
)
DOI_URL = f"https://doi.org/{DOI}"
CAMELS_SOURCE = (
    f"Źródło danych: CAMELS-PL {VERSION} (Brzezińska i in., 2026), {DOI_URL}, licencja "
    "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)"
)
"""L of Nogat DEV §20 for release 2.1.0 (its record is of 2026)."""
CAMELS_PROCESSED = "Dane CAMELS-PL zostały przetworzone"
"""LP: the fixtures are a selection of rows and columns, recompressed (DEV-20.1)."""
XIE = {
    "citation": "Xie, J., Liu, X., Wang, K., Yang, T., Liang, K. and Liu, C. (2020). "
    "Evaluation of typical methods for baseflow separation in the contiguous United "
    "States. Journal of Hydrology 583, 124628; their Python package baseflow, "
    "github.com/xiejx5/baseflow",
    "locator": "baseflow/methods/LH.py: LH(Q, beta=0.925), b[0] = Q[0], b[i+1] = beta "
    "b[i] + (1 - beta)/2 (Q[i] + Q[i+1]) at most Q[i+1], then backward on that "
    "baseflow, at most it; separation.py: the days without a value dropped "
    "(utils.clean_streamflow)",
    "url": "https://github.com/xiejx5/baseflow",
    "access": "open",
}
REPRESENTATION = {
    "abs": 1e-12,
    "reason": "the decimals of the data and of the printed value are not exact in "
    "binary: a value exactly half a printed unit from the printed one differs from it "
    "by a few units in the last place more",
}


@dataclass(frozen=True)
class Gauge:
    """A gauge's published discharge on every day of the span, ``None`` without one."""

    gauge_id: str
    name: str
    river: str
    area_km2: str
    days: tuple[date, ...]
    vol: tuple[str | None, ...]
    spec: tuple[str | None, ...]


def _member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    """Return the one member whose name ends with ``suffix`` (layouts move roots)."""
    found = [info for info in archive.infolist() if info.filename.endswith(suffix)]
    if len(found) != 1:
        raise SystemExit(f"{len(found)} members end with {suffix}; expected 1")
    return found[0]


def _rows(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> list[dict[str, str]]:
    with archive.open(info) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline="")))


def _calendar() -> list[date]:
    count = (LAST_DAY - FIRST_DAY).days + 1
    return [FIRST_DAY + timedelta(days=offset) for offset in range(count)]


def _gauge(
    archive: zipfile.ZipFile, gauge_id: str, topography: dict[str, dict[str, str]]
) -> tuple[Gauge, bytes, zipfile.ZipInfo]:
    """Read a gauge's series; return it, its fixture's bytes and its member."""
    info = _member(archive, f"/timeseries/CAMELS_PL_hydromet_timeseries_{gauge_id}.csv")
    rows = _rows(archive, info)
    by_day = {row["date"]: row for row in rows}
    days = _calendar()
    if [row["date"] for row in rows] != [day.isoformat() for day in days]:
        raise SystemExit(f"{gauge_id}: the file does not span {FIRST_DAY}..{LAST_DAY}")
    vol = tuple(by_day[d.isoformat()]["discharge_vol_obs"] or None for d in days)
    spec = tuple(by_day[d.isoformat()]["discharge_spec_obs"] or None for d in days)
    if any((v is None) != (s is None) for v, s in zip(vol, spec, strict=True)):
        raise SystemExit(f"{gauge_id}: the two discharges miss different days")
    lines = ["date,discharge_vol_obs,discharge_spec_obs"]
    lines += [
        f"{row['date']},{row['discharge_vol_obs']},{row['discharge_spec_obs']}"
        for row in rows
        if row["discharge_vol_obs"]
    ]
    data = gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), 9, mtime=0)
    place = topography[gauge_id]
    gauge = Gauge(
        gauge_id=gauge_id,
        name=place["gauge_name"],
        river=place["water_body_name"],
        area_km2=place["area_metadata"],
        days=tuple(days),
        vol=vol,
        spec=spec,
    )
    return gauge, data, info


def _hydrological_years(days: tuple[date, ...]) -> Iterator[tuple[int, list[int]]]:
    """Yield each hydrological year of the span with the indices of its days in it."""
    for year in range(FIRST_DAY.year, LAST_DAY.year + 1):
        first, last = date(year - 1, 11, 1), date(year, 10, 31)
        inside = [i for i, day in enumerate(days) if first <= day <= last]
        yield year, inside


def _kept_years(gauge: Gauge) -> list[tuple[int, list[int]]]:
    """The years with at most 5 % of their days without a value, days before the span
    included, as CAMELS-DE's ``filter_complete_hydro_years`` keeps them."""
    kept = []
    for year, inside in _hydrological_years(gauge.days):
        length = (date(year, 11, 1) - date(year - 1, 11, 1)).days
        missing = length - sum(gauge.vol[i] is not None for i in inside)
        if 100 * missing <= MISSING_PERCENT * length:
            kept.append((year, inside))
    return kept


def _bracket(ascending: NDArray[np.float64], probability: float) -> tuple[float, float]:
    """The order statistics around numpy's ``nearest`` and Weibull's positions."""
    n = ascending.size
    nearest = (n - 1) * probability
    weibull = (n + 1) * probability - 1
    low = max(math.floor(min(nearest, weibull)), 0)
    high = min(math.ceil(max(nearest, weibull)), n - 1)
    return float(ascending[low]), float(ascending[high])


def _two_pass_bfi(flows: NDArray[np.float64]) -> float:
    """The two-pass filter of Xie et al.'s ``LH`` (alpha 0.925) and its index."""
    beta = 0.925
    base = np.empty_like(flows)
    base[0] = flows[0]
    for i in range(flows.size - 1):
        value = beta * base[i] + (1 - beta) / 2 * (flows[i] + flows[i + 1])
        base[i + 1] = min(value, flows[i + 1])
    first = base.copy()
    for i in range(flows.size - 2, -1, -1):
        value = beta * base[i + 1] + (1 - beta) / 2 * (first[i + 1] + first[i])
        base[i] = min(value, first[i])
    return math.fsum(base) / math.fsum(flows)


def _source(gauge_id: str, column: str) -> dict[str, str]:
    attributes = "CAMELS_PL_2.1/CAMELS_PL_hydrologic_attributes.csv"
    series = SERIES[gauge_id]
    return {
        "citation": CITATION,
        "locator": f"{RELEASE}: {attributes} (SHA-256 {SHA256[attributes]}), the row "
        f"of gauge {gauge_id}, column {column} ({RELATIVE}/CAMELS_PL_hydrologic_"
        f"attributes.csv), computed from {series} (SHA-256 {SHA256[series]}; "
        f"{RELATIVE}/camels_pl_{gauge_id}.csv.gz); its definition: {DESCRIPTION} "
        f"(SHA-256 {DESCRIPTION_SHA256}), Table 7",
        "url": DOI_URL,
        "access": "open",
    }


def _sample_text(gauge: Gauge, kept: list[tuple[int, list[int]]]) -> str:
    days = sum(len(inside) for _, inside in kept)
    with_value = sum(gauge.vol[i] is not None for _, inside in kept for i in inside)
    first, last = kept[0][0], kept[-1][0]
    return (
        f"the sample: the hydrological years (1 November - 31 October) of the file "
        f"({FIRST_DAY} to {LAST_DAY}; the year 1951 lacks November and December) with "
        f"at most {MISSING_PERCENT} % of their days without a value, as the code of "
        f"CAMELS-DE keeps them (filter_complete_hydro_years, tolerance 0.05): "
        f"{len(kept)} years from {first} to {last}, {days} days, {days - with_value} "
        "of them without a value, in order, the years one after another"
    )


def _cases(gauge: Gauge) -> list[dict[str, object]]:
    """The reference cases of one gauge."""
    attributes = ATTRIBUTES[gauge.gauge_id]
    kept = _kept_years(gauge)
    indices = [i for _, inside in kept for i in inside]
    spec_values = np.array(
        [math.nan if (text := gauge.spec[i]) is None else float(text) for i in indices]
    )
    known = np.sort(spec_values[~np.isnan(spec_values)])
    n_days, n_known = len(indices), int(known.size)
    file = f"{RELATIVE}/camels_pl_{gauge.gauge_id}.csv.gz"
    sample = _sample_text(gauge, kept)
    label = f"{gauge.name} ({gauge.river}, {gauge.area_km2} km2)"
    cases: list[dict[str, object]] = []

    for column, percent, probability in (("Q5", 95.0, 0.05), ("Q95", 5.0, 0.95)):
        low, high = _bracket(known, probability)
        cases.append(
            {
                "formula": "exceedance_values",
                "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}_{column.lower()}",
                "source": _source(gauge.gauge_id, column),
                "inputs": {
                    "file": file,
                    "column": "discharge_spec_obs",
                    "sample": "complete_years",
                    "exceedance_percent": [percent],
                },
                "expected": {"exceedance_values": [float(attributes[column])]},
                "printed_precision": {"exceedance_values": 0.01},
                "intermediate_rounding": [
                    {
                        "step": f"CAMELS-PL takes the order statistic nearest to the "
                        f"position (n - 1) P of the n = {n_known} values in ascending "
                        f"order, P = {probability} (numpy's quantile 'nearest'), "
                        "Hydrolog interpolates at the Weibull position (n + 1) P - 1: "
                        f"both lie between the order statistics {low!r} and {high!r} "
                        "mm/d around the two positions",
                        "effect": {"exceedance_values": high - low},
                    }
                ],
                "tolerance": REPRESENTATION,
                "conventions": [
                    f"{label}: CAMELS-PL's {column} is the {round(probability * 100)} "
                    "% quantile of the daily specific discharge [mm/d], Hydrolog's "
                    f"value equalled or exceeded on {percent:g} % of the days",
                    sample,
                    "the specific discharge as published (discharge_spec_obs, mm/d "
                    "to 3 decimals), the output printed to 2 decimals by Python's "
                    "round",
                ],
                "status": "single_source",
            }
        )

    flowing = known[known > 0]
    a_low, a_high = _bracket(flowing, 0.66)
    b_low, b_high = _bracket(flowing, 0.33)
    width = (math.log(a_high / a_low) + math.log(b_high / b_low)) / 0.33
    cases.append(
        {
            "formula": "fdc_slope",
            "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}",
            "source": _source(gauge.gauge_id, "slope_fdc"),
            "inputs": {
                "file": file,
                "column": "discharge_spec_obs",
                "sample": "complete_years_flowing",
                "from_percent": 34.0,
                "to_percent": 67.0,
            },
            "expected": {"slope": float(attributes["slope_fdc"])},
            "printed_precision": {"slope": 0.01},
            "intermediate_rounding": [
                {
                    "step": "CAMELS-PL takes the order statistics nearest to (n - 1) "
                    f"0.66 and (n - 1) 0.33 of the n = {flowing.size} flows above 0 "
                    "(numpy's 'nearest'), Hydrolog interpolates at the Weibull "
                    "positions of 34 and 67 %: the slope of any pair of values between "
                    f"the order statistics around them, {a_low!r} to {a_high!r} and "
                    f"{b_low!r} to {b_high!r} mm/d, lies within this width",
                    "effect": {"slope": width},
                }
            ],
            "tolerance": REPRESENTATION,
            "conventions": [
                f"{label}: CAMELS-PL's slope_fdc is (ln q66 - ln q33) / (0.66 - 0.33) "
                "of the 66th and 33rd percentiles, the flows exceeded on 34 and 67 % "
                "of the days (the non-exceedance percentiles of Addor et al. 2017, "
                "not Sawicz et al.'s exceedance 33 and 66 %): Hydrolog's slope from "
                "34 to 67 %",
                sample,
                "only the days with a specific discharge above 0: the code of "
                "CAMELS-DE drops the zero days before the percentiles",
            ],
            "status": "single_source",
        }
    )

    for formula, prefix in (("high_flow_days", "high_q"), ("low_flow_days", "low_q")):
        rule = (
            "above 9 times the median"
            if formula == "high_flow_days"
            else "below 0.2 times the mean"
        )
        cases.append(
            {
                "formula": formula,
                "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}",
                "source": _source(gauge.gauge_id, f"{prefix}_freq, {prefix}_dur"),
                "inputs": {
                    "file": file,
                    "column": "discharge_spec_obs",
                    "sample": "complete_years",
                },
                "expected": {
                    "days_per_year": float(attributes[f"{prefix}_freq"]),
                    "mean_duration_days": float(attributes[f"{prefix}_dur"]),
                },
                "printed_precision": {
                    "days_per_year": 0.01,
                    "mean_duration_days": 0.01,
                },
                "tolerance": REPRESENTATION,
                "conventions": [
                    f"{label}: the days with a specific discharge {rule} of the "
                    "sample's days with a value, per year of 365.25 days, and the "
                    "mean length of their runs; 0 and 0 without such a day",
                    sample,
                    "CAMELS-PL divides the days by every day of its years, "
                    f"{n_days}, the {n_days - n_known} without a value too (the length "
                    "of the frame in CAMELS-DE's code), Hydrolog by the "
                    f"{n_known} with a value (Addor et al.'s code): the case compares "
                    "Hydrolog's frequency times their ratio; a day without a value "
                    "ends a run in both",
                ],
                "status": "single_source",
            }
        )

    cases.append(
        {
            "formula": "zero_flow_fraction",
            "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}",
            "source": _source(gauge.gauge_id, "zero_q_freq"),
            "inputs": {
                "file": file,
                "column": "discharge_spec_obs",
                "sample": "complete_years",
            },
            "expected": {"fraction": float(attributes["zero_q_freq"])},
            "printed_precision": {"fraction": 0.01},
            "tolerance": REPRESENTATION,
            "conventions": [
                f"{label}: the share of the days whose specific discharge is 0, "
                "as published to 0.001 mm/d (a discharge that rounds to 0.000 mm/d "
                "counts)",
                sample,
                f"CAMELS-PL divides by every day of its years, {n_days}, Hydrolog by "
                f"the {n_known} with a value: the case compares Hydrolog's fraction "
                "times their ratio",
            ],
            "status": "single_source",
        }
    )

    ties = 0
    for _, inside in kept:
        year = [Fraction(gauge.vol[i] or 0) for i in inside]
        total, running = sum(year, Fraction(0)), Fraction(0)
        for flow in year:
            running += flow
            if 2 * running >= total:
                ties += 2 * running == total
                break
    steps = []
    if ties:
        steps.append(
            {
                "step": f"in {ties} of the {len(kept)} years the cumulative "
                "discharge equals half of the year's exactly on a day, in the "
                "published decimals: "
                "CAMELS-PL's floating-point sums and Hydrolog's exact sums of the "
                "binary values fall either side, so that year's date is the day or the "
                f"next; at most {ties} / {len(kept)} of a day in the mean",
                "effect": {"mean_day": ties / len(kept)},
            }
        )
    cases.append(
        {
            "formula": "half_flow_date",
            "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}",
            "source": _source(gauge.gauge_id, "hfd_mean"),
            "inputs": {
                "file": file,
                "column": "discharge_vol_obs",
                "sample": "complete_years_each",
            },
            "expected": {"mean_day": float(attributes["hfd_mean"])},
            "printed_precision": {"mean_day": 0.01},
            "intermediate_rounding": steps,
            "tolerance": REPRESENTATION,
            "conventions": [
                f"{label}: the day of each year, from 1 November as day 1, on which "
                "the discharge summed from 1 November first exceeds half of the "
                "year's (a day without a value adds nothing), the mean over the years",
                sample,
                "the volumetric discharge as published (discharge_vol_obs, m3/s to 3 "
                "significant digits), which the code of CAMELS-DE sums",
            ],
            "status": "single_source",
        }
    )

    window = [
        i
        for i, day in enumerate(gauge.days)
        if day <= BFI_LAST_DAY and gauge.spec[i] is not None
    ]
    flows = np.array([float(gauge.spec[i] or 0) for i in window])
    oracle = _two_pass_bfi(flows)
    hydrolog = baseflow_index(flows, lyne_hollick_filter(flows))
    cases.append(
        {
            "formula": "baseflow_index",
            "case_id": f"camels_pl_2_1_0_{gauge.gauge_id}",
            "source": _source(gauge.gauge_id, "baseflow_index"),
            "inputs": {
                "file": file,
                "column": "discharge_spec_obs",
                "sample": "with_value_to_2023",
            },
            "expected": {"bfi": float(attributes["baseflow_index"])},
            "printed_precision": {"bfi": 0.01},
            "conventions": [
                f"{label}: the baseflow index of the Lyne and Hollick filter with "
                "alpha 0.925 (the data description, Table 7)",
                f"the sample: the {flows.size} days from {FIRST_DAY} to {BFI_LAST_DAY} "
                "with a value, one after another (the index of every one of the 139 "
                "gauges without a missing day is reproduced on this window, not on the "
                "file's, which runs to 2025-10-31)",
            ],
            "second_source": XIE,
            "status": "discrepancy",
            "discrepancy": "a definition, not arithmetic: CAMELS-PL filters twice, "
            "forward and backward, the baseflow at most the flow of its pass, which "
            "clips the quickflow at 0 (the printed eq. 1 of Ladson et al. 2013), "
            "from b = Q on the first day, as the LH method of Xie et al.'s package; "
            "Hydrolog "
            "follows Ladson et al.'s standard approach, three passes with the "
            "quickflow unclipped and 30 values reflected at each end. On these days "
            f"the two-pass filter gives {oracle:.4f} (CAMELS-PL "
            f"{attributes['baseflow_index']}), Hydrolog's {hydrolog:.4f}",
        }
    )
    return cases


ATTRIBUTES: dict[str, dict[str, str]] = {}
SERIES: dict[str, str] = {}
"""The member of each gauge's series."""
SHA256: dict[str, str] = {}
"""The SHA-256 of each member read, by its name."""


def _digests(path: Path) -> tuple[str, str]:
    """The MD5 and SHA-256 of a file."""
    md5, sha256 = hashlib.md5(usedforsecurity=False), hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            md5.update(block)
            sha256.update(block)
    return md5.hexdigest(), sha256.hexdigest()


def _read(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
    """Record the SHA-256 of a member read."""
    SHA256[info.filename] = hashlib.sha256(archive.read(info)).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    path, description = Path(sys.argv[1]), Path(sys.argv[2])
    md5, sha256 = _digests(path)
    if (md5, sha256) != (ZIP_MD5, ZIP_SHA256) or path.stat().st_size != ZIP_SIZE:
        print(f"{path} is not CAMELS-PL {VERSION} (SHA-256 {sha256})")
        return 1
    if _digests(description)[1] != DESCRIPTION_SHA256:
        print(f"{description} is not the {DESCRIPTION} of CAMELS-PL {VERSION}")
        return 1
    with zipfile.ZipFile(path) as archive:
        hydrologic = _member(archive, "/CAMELS_PL_hydrologic_attributes.csv")
        topographic = _member(
            archive, "/CAMELS_PL_topographic_GLO_30_DEM_attributes.csv"
        )
        with archive.open(hydrologic) as raw:
            text = raw.read().decode("utf-8")
        lines = text.splitlines()
        rows = {line.split(",", 1)[0]: line for line in lines[1:]}
        for row in csv.DictReader(io.StringIO(text)):
            ATTRIBUTES[row["gauge_id"]] = row
        topography = {row["gauge_id"]: row for row in _rows(archive, topographic)}
        extract = "\n".join([lines[0], *(rows[g] for g in GAUGES)]) + "\n"
        (HERE / "CAMELS_PL_hydrologic_attributes.csv").write_text(
            extract, encoding="utf-8"
        )
        members = [hydrologic, topographic]
        cases: list[dict[str, object]] = []
        gauges = []
        for gauge_id in GAUGES:
            gauge, data, info = _gauge(archive, gauge_id, topography)
            (HERE / f"camels_pl_{gauge_id}.csv.gz").write_bytes(data)
            SERIES[gauge_id] = info.filename
            members.append(info)
            gauges.append(gauge)
        for info in members:
            _read(archive, info)
        for gauge in gauges:
            cases += _cases(gauge)
    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _attribution(members, gauges)
    return 0


def _attribution(members: list[zipfile.ZipInfo], gauges: list[Gauge]) -> None:
    def prose(text: str) -> list[str]:
        return textwrap.wrap(text, width=100, break_on_hyphens=False)

    lines = [
        *prose(
            "camels_pl_<gauge>.csv.gz: the rows with a discharge of "
            "CAMELS_PL_2.1/timeseries/CAMELS_PL_hydromet_timeseries_<gauge>.csv, the "
            "columns date, discharge_vol_obs [m3/s] and discharge_spec_obs [mm/d] as "
            "published (gzip, no time stamp)."
        ),
        *prose(
            "CAMELS_PL_hydrologic_attributes.csv: the header and the rows of these "
            "gauges of CAMELS_PL_2.1/CAMELS_PL_hydrologic_attributes.csv, as published."
        ),
        *prose(
            f"Release: {RELEASE}, {DOI_URL}. Extracted by extract_camels_pl.py on "
            f"{date.today().isoformat()} from the record's CAMELS_PL_2.1.zip "
            f"({ZIP_SIZE} B, MD5 {ZIP_MD5} as the record lists it); the files read, "
            "with their SHA-256 (Nogat CMP-6.10):"
        ),
        f"  CAMELS_PL_2.1.zip  {ZIP_SHA256}",
        f"  {DESCRIPTION}  {DESCRIPTION_SHA256}",
        *(f"  {info.filename}  {SHA256[info.filename]}" for info in members),
        "",
        "The gauges (IMGW-PIB code, name, river, area_metadata [km2]):",
        *(f"  {g.gauge_id}  {g.name}  {g.river}  {g.area_km2}" for g in gauges),
        "",
        *prose(f"{CITATION}."),
        f"{DOI_URL}; licence CC BY 4.0, https://creativecommons.org/licenses/by/4.0/.",
        "",
        *prose(
            "The lines of Nogat DEV §20 (DEV-20.12: discharge CAMELS-PL took from "
            "IMGW-PIB, selected and recompressed here), quoted as they stand:"
        ),
        IMGW_SOURCE,
        IMGW_PROCESSED,
        CAMELS_SOURCE,
        CAMELS_PROCESSED,
    ]
    (HERE / "CAMELS_PL_ATTRIBUTION.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
