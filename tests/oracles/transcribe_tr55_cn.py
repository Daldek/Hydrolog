"""Transcribe the TR-55 curve numbers Hydrolog uses from the PDF's text layer (CMP-2.5).

The second, independent transcription of the curve number table of
``src/hydrolog/_data/tables/tr55_cn.csv``: the rows of TR-55 tables 2-2a, 2-2b and 2-2c
read from the text layer of the PDF (``pdftotext -layout``, poppler 25.03), not
typed. The first is the table of Hydrolog 0.8.1, typed by hand
(``tr55_cn_hydrolog_0_8_1.csv``); ``tests/unit/test_formulas_cn_table.py`` compares
the three. Run once (2026-11-18); its output is kept, not regenerated.

Usage::

    pdftotext -layout TR-55_Manual.pdf tr55.txt   # https://www.hydrocad.net/pdf/TR-55%20Manual.pdf
    cd tests/oracles && python transcribe_tr55_cn.py tr55.txt > tr55_cn_text_layer.csv
"""

import csv
import re
import sys
from pathlib import Path

# (land cover, condition, table, page, the row's label in the text layer, the n-th
# line matching it). A row of a condition of table 2-2b or 2-2c is its own line.
ROWS = (
    ("fallow", "", "2-2b", "2-6", r"^Fallow\s+Bare soil", 0),
    ("row_crops", "poor", "2-2b", "2-6", r"^Row crops\s+Straight row \(SR\)\s+Poor", 0),
    ("row_crops", "good", "2-2b", "2-6", r"^Row crops", 1),
    ("small_grain", "poor", "2-2b", "2-6", r"^Small grain\s+SR\s+Poor", 0),
    ("small_grain", "good", "2-2b", "2-6", r"^Small grain", 1),
    ("pasture", "poor", "2-2c", "2-7", r"^Pasture, grassland, or range", 0),
    ("pasture", "fair", "2-2c", "2-7", r"^Pasture, grassland, or range", 1),
    ("pasture", "good", "2-2c", "2-7", r"^Pasture, grassland, or range", 2),
    ("meadow", "", "2-2c", "2-7", r"^Meadow", 0),
    ("brush", "poor", "2-2c", "2-7", r"^Brush", 0),
    ("brush", "fair", "2-2c", "2-7", r"^Brush", 1),
    ("brush", "good", "2-2c", "2-7", r"^Brush", 2),
    ("woods_grass", "poor", "2-2c", "2-7", r"^Woods.grass combination", 0),
    ("woods_grass", "fair", "2-2c", "2-7", r"^Woods.grass combination", 1),
    ("woods_grass", "good", "2-2c", "2-7", r"^Woods.grass combination", 2),
    ("forest", "poor", "2-2c", "2-7", r"^Woods\. ", 0),
    ("forest", "fair", "2-2c", "2-7", r"^Woods\. ", 1),
    ("forest", "good", "2-2c", "2-7", r"^Woods\. ", 2),
    ("farmstead", "", "2-2c", "2-7", r"^Farmsteads", 0),
    ("open_space", "poor", "2-2a", "2-5", r"^\s+Poor condition \(grass cover", 0),
    ("open_space", "fair", "2-2a", "2-5", r"^\s+Fair condition \(grass cover", 0),
    ("open_space", "good", "2-2a", "2-5", r"^\s+Good condition \(grass cover", 0),
    ("paved", "", "2-2a", "2-5", r"^\s+\(excluding right-of-way\) \.", 0),
    ("paved_road_open_ditches", "", "2-2a", "2-5", r"^\s+Paved; open ditches", 0),
    ("gravel", "", "2-2a", "2-5", r"^\s+Gravel \(including", 0),
    ("dirt", "", "2-2a", "2-5", r"^\s+Dirt \(including", 0),
    ("commercial", "", "2-2a", "2-5", r"^\s+Commercial and business", 0),
    ("industrial", "", "2-2a", "2-5", r"^\s+Industrial \.", 0),
    ("residential_high", "", "2-2a", "2-5", r"^\s+1/8 acre or less", 0),
    ("residential_quarter_acre", "", "2-2a", "2-5", r"^\s+1/4 acre \.", 0),
    ("residential_medium", "", "2-2a", "2-5", r"^\s+1/3 acre \.", 0),
    ("residential_low", "", "2-2a", "2-5", r"^\s+2 acres \.", 0),
)
"""A condition row after the first of its cover type has no label: it is the n-th
line from the label's line that holds four numbers."""


def _numbers(line: str) -> list[int]:
    """The last four curve numbers of a line, without footnote marks (``30 4/``)."""
    cleaned = re.sub(r"\d+/", " ", line.split("..")[-1] if ".." in line else line)
    return [int(x) for x in re.findall(r"\b\d+\b", cleaned)][-4:]


def transcribe(text: str) -> list[dict[str, str]]:
    """Return one row per land cover and condition of :data:`ROWS`."""
    lines = text.splitlines()
    found = []
    for cover, condition, table, page, label, offset in ROWS:
        start = next(i for i, line in enumerate(lines) if re.search(label, line))
        rows = [i for i in range(start, start + 8) if len(_numbers(lines[i])) == 4]
        values = _numbers(lines[rows[offset]])
        found.append(
            {
                "land_cover": cover,
                "condition": condition,
                **dict(zip("ABCD", map(str, values), strict=True)),
                "table": table,
                "page": page,
            }
        )
    return found


if __name__ == "__main__":
    rows = transcribe(Path(sys.argv[1]).read_text(encoding="utf-8"))
    writer = csv.DictWriter(
        sys.stdout,
        ["land_cover", "condition", "A", "B", "C", "D", "table", "page"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
