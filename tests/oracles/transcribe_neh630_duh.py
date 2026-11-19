"""Transcribe NEH 630 table 16-1 from the PDF's text layer (CMP-2.5).

The second, independent transcription of the dimensionless unit hydrograph of
``src/hydrolog/_data/tables/neh630_duh.csv``: the time and discharge ratios of table
16-1 of NEH 630 chapter 16 (USDA-NRCS 2007, p. 16-4), read from the text layer of the
PDF (``pdftotext -layout``, poppler 25.03), not typed. The first is the table of
Hydrolog 0.8.1, typed by hand (``neh630_duh_hydrolog_0_8_1.csv``);
``tests/unit/test_formulas_unit_hydrographs.py`` compares the three. Run once
(2026-11-19); its output is kept, not regenerated.

Usage::

    pdftotext -layout H_210_630_16.pdf neh630_16.txt
    # https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf
    cd tests/oracles && python transcribe_neh630_duh.py neh630_16.txt \
        > neh630_duh_text_layer.csv
"""

import csv
import re
import sys
from pathlib import Path

ROW = re.compile(r"^\s*(\d*\.?\d+)\s+(\.\d{3}|1\.000)\s+(\.\d{3}|1\.000)(\s|$)")
"""A row of the table: the time ratio, the discharge ratio and the mass curve ratio,
printed without a leading zero (``  .1   .030   .001``)."""


def _decimal(text: str) -> str:
    """Return a printed ratio with its leading zero (``.030`` -> ``0.030``)."""
    return f"0{text}" if text.startswith(".") else text


def transcribe(text: str) -> list[dict[str, str]]:
    """Return the rows of table 16-1: from its column heading to the page footer."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("Time ratios"))
    rows: list[dict[str, str]] = []
    for line in lines[start:]:
        if "(210–VI–NEH" in line:
            break
        found = ROW.match(line)
        if found:
            time, discharge = found.group(1), found.group(2)
            rows.append(
                {
                    "t_over_tp": f"{float(_decimal(time)):.1f}",
                    "q_over_qp": _decimal(discharge),
                }
            )
    return rows


if __name__ == "__main__":
    rows = transcribe(Path(sys.argv[1]).read_text(encoding="utf-8"))
    writer = csv.DictWriter(sys.stdout, ["t_over_tp", "q_over_qp"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
