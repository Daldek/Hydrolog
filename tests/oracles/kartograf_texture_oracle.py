"""Kartograf 0.8.2's texture classes and groups, run once as frozen oracles (CMP-6.4).

Kartograf keeps its own copy of the USDA texture rules and of the texture -> HSG table
(``kartograf.hydrology.hsg``, Kartograf ADR-025, the limits clay < 20 % and < 27 % of
its 0.8.2). Nogat's plan (step 7) proves Kartograf's and Hydrolog's rules equal by one
shared set of cases: every integer composition of the texture triangle in percent
(clay + sand + silt = 100, 5,151 compositions) and in g/kg (sum 1000, 501,501). This
script classifies them with Kartograf's ``classify_usda_texture_array`` and writes,
into the directory of this script:

- ``kartograf_0_8_2_texture_percent.csv``: one row per percent composition, its
  class code;
- ``kartograf_0_8_2_texture_gkg.csv``: the g/kg grid run-length encoded along sand:
  for each clay value, one row per run of sand values (``sand_from`` to ``sand_to``,
  both included, silt = 1000 - clay - sand) with one class code; lossless, the tests
  expand it;
- ``kartograf_0_8_2_texture_hsg.csv``: ``TEXTURE_TO_HSG`` and
  ``RAWLS_1982_KSAT_CM_H`` (Rawls et al. 1982, cm/h; no value for silt).

The codes are Kartograf's ``TEXTURE_CLASSES``, named in the header. Run once
(2026-11-19) in an unpacked ``git archive v0.8.2`` of Kartograf, whose own
environment imports ``kartograf``; the outputs are kept and never regenerated into
the same files::

    git -C ~/workspace/Kartograf archive v0.8.2 | tar -x -C /tmp/kartograf-0.8.2
    cd /tmp/kartograf-0.8.2 && uv sync --locked
    uv run --locked python <hydrolog>/tests/oracles/kartograf_texture_oracle.py
"""

import csv
import datetime
import platform
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
from kartograf.hydrology.hsg import (  # type: ignore[import-not-found]
    RAWLS_1982_KSAT_CM_H,
    TEXTURE_CLASSES,
    TEXTURE_TO_HSG,
    classify_usda_texture_array,
)

HERE = Path(__file__).resolve().parent
SCRIPT = "tests/oracles/kartograf_texture_oracle.py"


def _grid(total: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Every integer (clay, sand, silt) with the given sum, clay then sand rising."""
    clay, sand = np.array(
        [(c, s) for c in range(total + 1) for s in range(total + 1 - c)], dtype=np.int64
    ).T
    return clay, sand, total - clay - sand


def _header(description: str) -> list[str]:
    classes = " ".join(f"{code}={name}" for name, code in TEXTURE_CLASSES.items())
    return [
        (
            "# tool: Kartograf 0.8.2 (git tag v0.8.2, commit "
            "66197871f468869b437e8256e04bd00a0ea7c6aa), kartograf.hydrology.hsg"
        ),
        f"# packages: kartograf 0.8.2, numpy {np.__version__}, "
        f"python {sys.version.split()[0]}",
        f"# platform: {platform.platform()}",
        f"# date: {datetime.date.today().isoformat()}",
        f"# script: {SCRIPT}",
        f"# classes: {classes}",
        f"# contents: {description}",
    ]


def _write(
    name: str, header: list[str], columns: list[str], rows: list[list[object]]
) -> None:
    with (HERE / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(header) + "\n")
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def main() -> None:
    clay, sand, silt = _grid(100)
    codes = classify_usda_texture_array(clay, sand, silt)
    _write(
        "kartograf_0_8_2_texture_percent.csv",
        _header(
            "classify_usda_texture_array of every integer percent composition, "
            "clay + sand + silt = 100 (5151 rows)"
        ),
        ["clay", "sand", "silt", "code"],
        [
            [int(c), int(s), int(si), int(k)]
            for c, s, si, k in zip(clay, sand, silt, codes, strict=True)
        ],
    )

    clay, sand, silt = _grid(1000)
    codes = classify_usda_texture_array(clay, sand, silt)
    runs: list[list[object]] = []
    for c, s, k in zip(clay.tolist(), sand.tolist(), codes.tolist(), strict=True):
        if runs and runs[-1][0] == c and runs[-1][3] == k and runs[-1][2] == s - 1:
            runs[-1][2] = s
        else:
            runs.append([c, s, s, k])
    _write(
        "kartograf_0_8_2_texture_gkg.csv",
        _header(
            "classify_usda_texture_array of every integer g/kg composition, clay + "
            "sand + silt = 1000 (501501 compositions), run-length encoded along "
            "sand: each row is clay, the first and the last sand of a run (both "
            "included; silt = 1000 - clay - sand) and the code of every composition "
            "of the run"
        ),
        ["clay", "sand_from", "sand_to", "code"],
        runs,
    )

    _write(
        "kartograf_0_8_2_texture_hsg.csv",
        _header(
            "TEXTURE_TO_HSG and RAWLS_1982_KSAT_CM_H (cm/h, Rawls et al. 1982; empty "
            "where Kartograf has none) of kartograf.hydrology.hsg"
        ),
        ["texture_class", "hsg", "rawls_1982_ksat_cm_h"],
        [
            [name, TEXTURE_TO_HSG[name], RAWLS_1982_KSAT_CM_H.get(name, "")]
            for name in TEXTURE_CLASSES
        ],
    )
    print(f"kartograf {version('kartograf')}: {len(runs)} runs", file=sys.stderr)


if __name__ == "__main__":
    main()
