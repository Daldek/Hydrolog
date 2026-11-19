"""Build datasets.csv: the frozen input data of the trend-regime oracles.

Every series is written once, as decimal text, and read by both the R oracle
(r_oracle.R) and the Hydrolog comparison (compare_hydrolog.py).

Sources of the published series
-------------------------------
gilbert_ex16_1     Gilbert (1987), Exercise 16.1 (p. 224): ND, 1.1, ND, 3, 1.5, 1.2, 4 at
                   times 1..7; the NDs set to 0.25 = half the detection limit 0.5 as in
                   Exercise 16.2(b) (any common value < 1.1 gives the same S and ties).
gilbert_ex16_2a    Exercise 16.2(a): the NDs treated as missing (times 2, 4, 5, 6, 7).
gilbert_ex16_5     Example 16.3/16.5 (pp. 214-219): (10,1) (22,1) (21,1) (30,2) (22,3)
                   (30,3) (40,4) (40,5) -- several values per time period.
helsel_ex10_1      Helsel et al. (2020), USGS TM 4-A3, Example 10.1 (p. 269): y = 1, 2,
                   3, 4, 5, 16, 7 at x = 1..7.
kzgw_*             KZGW (2017) Metodyka, Tables 1.1, 1.2 (= 3.5), 3.10, 3.13: annual
                   maxima Qmax [m3/s] of Bobr-Bukowka 1965-2005, Czarna-Polana 1972-2005,
                   Rypienica-Rypin 1975-2005, Swislina-Rzepin 1976-2005. Bobr 1995 is
                   printed "4,7,0" in the source; 4.70 is taken (see the case notes).
helsel_ex5_1       Helsel et al. (2020), Example 5.1 (p. 120): NH4orgN [mg/L], group 1
                   "indust" (10 values) then group 2 "residen" (10 values).
luke_peaks         USGS NWIS peak-flow file of 01598500 North Branch Potomac River at
                   Luke, MD, water years 1952-2014 [ft3/s] (Helsel et al. 2020, Example
                   12.3); group 1 = WY 1952-1981, group 2 = WY 1982-2014.
pettitt_page, nile, maxau_Q, maxau_s   exported from R by r_export_datasets.R.
seeded_ties        numpy default_rng(20261118): 60 gamma(2, 50) values + 0.8 i, rounded
                   to integers (many ties).
seeded_step        numpy default_rng(20261119): 25 N(100, 15) then 25 N(120, 15), rounded
                   to 0.1.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def rows_of(name, values, times=None, groups=None):
    out = []
    for i, value in enumerate(values):
        out.append(
            {
                "dataset": name,
                "index": i + 1,
                "time": (times[i] if times is not None else i + 1),
                "group": (groups[i] if groups is not None else "NA"),
                "value": value if isinstance(value, str) else repr(float(value)),
            }
        )
    return out


def main(r_csv: Path, luke_csv: Path, out_csv: Path) -> None:
    rows = []
    rows += rows_of("gilbert_ex16_1", ["0.25", "1.1", "0.25", "3", "1.5", "1.2", "4"])
    rows += rows_of(
        "gilbert_ex16_2a", ["1.1", "3", "1.5", "1.2", "4"], times=[2, 4, 5, 6, 7]
    )
    rows += rows_of(
        "gilbert_ex16_5",
        ["10", "22", "21", "30", "22", "30", "40", "40"],
        times=[1, 1, 1, 2, 3, 3, 4, 5],
    )
    rows += rows_of("helsel_ex10_1", ["1", "2", "3", "4", "5", "16", "7"])
    bobr = (
        "18.6 13.2 22.1 20.4 23.0 10.7 27.8 14.7 8.62 15.9 22.1 16.6 27.8 4.76 "
        "11.3 32.3 32.3 33.8 21.7 9.23 14.3 8.28 10.7 9.16 10.3 6.72 4.43 6.72 "
        "3.08 7.26 4.70 6.05 8.75 5.24 6.59 4.7 4.16 4.97 3.25 5.92 1.9"
    ).split()
    rows += rows_of("kzgw_bobr_bukowka", bobr, times=list(range(1965, 2006)))
    czarna = (
        "10.2 9.24 58.8 8.23 16.2 4.92 26.8 25.1 97.2 23.5 22.3 21.1 59.9 55.1 "
        "16.2 24.6 14.8 73.8 28.9 18.6 18.2 25.8 14.5 11.2 54.5 111 35.1 43.0 "
        "52.0 45.4 8.90 9.72 57.4 50.8"
    ).split()
    rows += rows_of("kzgw_czarna_polana", czarna, times=list(range(1972, 2006)))
    rypienica = (
        "3.26 2.40 3.32 1.91 4.62 10.9 3.29 5.10 1.66 1.21 2.11 1.91 2.24 2.02 "
        "2.84 0.83 0.97 0.81 1.11 3.35 2.30 5.10 1.89 2.50 3.56 2.84 1.73 7.70 "
        "4.33 4.00 3.90"
    ).split()
    rows += rows_of("kzgw_rypienica_rypin", rypienica, times=list(range(1975, 2006)))
    swislina = (
        "19.3 8.32 7.88 24.4 28.0 17.6 10.3 10.3 2.52 11.0 8.92 5.34 3.22 2.73 "
        "2.35 4.0 2.09 7.88 9.52 2.28 29.2 10.9 3.06 9.37 18.5 39.8 8.90 9.68 "
        "5.65 38.0"
    ).split()
    rows += rows_of("kzgw_swislina_rzepin", swislina, times=list(range(1976, 2006)))
    indust = "0.59 0.87 1.10 1.10 1.20 1.30 1.60 1.70 3.20 4.00".split()
    residen = "0.30 0.36 0.50 0.70 0.70 0.90 0.92 1.00 1.30 9.70".split()
    rows += rows_of("helsel_ex5_1", indust + residen, groups=[1] * 10 + [2] * 10)
    with open(luke_csv, newline="") as handle:
        luke = list(csv.DictReader(handle))
    rows += rows_of(
        "luke_peaks",
        [row["peak_cfs"] for row in luke],
        times=[int(row["water_year"]) for row in luke],
        groups=[1 if int(row["water_year"]) <= 1981 else 2 for row in luke],
    )
    with open(r_csv, newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "dataset": row["dataset"],
                    "index": int(row["index"]),
                    "time": int(row["time"]),
                    "group": "NA",
                    "value": row["value"],
                }
            )
    rng = np.random.default_rng(20261118)
    ties = np.round(rng.gamma(2.0, 50.0, size=60) + 0.8 * np.arange(60), 0)
    rows += rows_of("seeded_ties", [repr(float(v)) for v in ties])
    rng = np.random.default_rng(20261119)
    step = np.round(
        np.concatenate([rng.normal(100, 15, 25), rng.normal(120, 15, 25)]), 1
    )
    rows += rows_of(
        "seeded_step", [repr(float(v)) for v in step], groups=[1] * 25 + [2] * 25
    )
    with open(out_csv, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["dataset", "index", "time", "group", "value"]
        )
        writer.writeheader()
        writer.writerows(rows)
    names = sorted({row["dataset"] for row in rows})
    print(len(rows), "rows;", len(names), "datasets:", ", ".join(names))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), HERE / "datasets.csv")
