"""Freeze the SPI of climate_indices 3.2.0 on the fixture of Warszawa (Nogat CMP-6.4).

climate_indices (J. Adams, BSD-3-Clause) fits a gamma distribution to the k-month sums
of each calendar month by Thom's estimates, takes the probability of a zero sum as the
share of zero sums (``zero_handling`` "classic", H(0) = q) and holds the SPI within
-3.09 and 3.09: the conventions of Hydrolog's specs ``spi_gamma_fit`` and ``spi``. Its
input here is the monthly sums of the daily precipitation of
``tests/fixtures/warszawa_okecie_1991_2020.csv.gz`` (every day has a value), with the
calibration 1991-2020, which is the whole record, so the two programs see the same
sums (climate_indices lets the sums of a calibration that starts after the record's
first month reach before it; Hydrolog keeps them within the reference period).

The script imports no Hydrolog. Run it once from the repository's root in an
environment that has climate_indices 3.2.0, for example::

    uv run --no-project --with climate-indices==3.2.0 python \
        tests/oracles/spi_climate_indices.py

It writes ``tests/oracles/spi_climate_indices_warszawa.csv`` with its tool, packages,
platform and date; a later run goes to another file, never over this one.
"""

import csv
import gzip
import logging
import platform
import sys
import warnings
from datetime import date
from importlib.metadata import version
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "warszawa_okecie_1991_2020.csv.gz"
OUTPUT = ROOT / "tests" / "oracles" / "spi_climate_indices_warszawa.csv"
SCALES = (1, 3, 6, 12)
FIRST_YEAR, LAST_YEAR = 1991, 2020


def monthly_sums() -> list[float]:
    """Return the sums of each month of 1991-2020 from the daily rows."""
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    sums: dict[str, list[float]] = {}
    for row in rows:
        sums.setdefault(row["date"][:7], []).append(float(row["P [mm]"]))
    months = [
        f"{year}-{month:02d}"
        for year in range(FIRST_YEAR, LAST_YEAR + 1)
        for month in range(1, 13)
    ]
    return [round(sum(sums[month]), 6) for month in months]


def main() -> int:
    if OUTPUT.exists():
        print(f"{OUTPUT} exists: a frozen oracle is never regenerated into its file")
        return 1
    warnings.filterwarnings("ignore")
    logging.disable(logging.CRITICAL)
    from climate_indices import compute, indices  # type: ignore[import-not-found]

    totals = np.array(monthly_sums())
    columns = {
        scale: np.asarray(
            indices.spi(
                totals,
                scale,
                indices.Distribution.gamma,
                FIRST_YEAR,
                FIRST_YEAR,
                LAST_YEAR,
                compute.Periodicity.monthly,
            ),
            dtype=float,
        )
        for scale in SCALES
    }
    packages = ", ".join(
        f"{name} {version(name)}" for name in ("climate_indices", "numpy", "scipy")
    )
    header = [
        "tool: climate_indices 3.2.0, indices.spi (Distribution.gamma, "
        "Periodicity.monthly, calibration 1991-2020)",
        f"packages: {packages}",
        f"platform: {platform.platform()}, Python {platform.python_version()}",
        f"date: {date.today().isoformat()}",
        "script: tests/oracles/spi_climate_indices.py",
        "input: the monthly sums of P of "
        "tests/fixtures/warszawa_okecie_1991_2020.csv.gz",
        "conventions: Thom's estimates, q the share of zero sums, H(0) = q, the SPI "
        "within -3.09 and 3.09; spi<k> is empty where climate_indices gives NaN",
    ]
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        for line in header:
            stream.write(f"# {line}\n")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["year", "month", "total_mm", *(f"spi{s}" for s in SCALES)])
        for cell, total in enumerate(totals.tolist()):
            values = [columns[scale][cell] for scale in SCALES]
            texts = ["" if np.isnan(value) else repr(float(value)) for value in values]
            writer.writerow(
                [FIRST_YEAR + cell // 12, cell % 12 + 1, f"{total:.6f}", *texts]
            )
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
