"""Transcribe TR-55's texture groups (appendix A, p. A-1) from the PDF's text layer.

The comparison transcription of ``src/hydrolog/_data/tables/texture_hsg.csv`` where
it follows TR-55: the table „HSG / Soil textures” of appendix A („Disturbed soil
profiles”, p. A-1, after Brakensiek and Rawls 1983) read from the text layer of the
PDF (``pdftotext -raw``, poppler 25.03; the PDF's 103rd page), not typed.
``tests/unit/test_formulas_texture_hsg.py`` compares it with the data file, whose
three rows that follow NEH 630 ch. 7 instead (sandy loam, clay loam, silty clay loam)
and whose silt row (TR-55 has none) are the spec's documented deviations. Run once
(2026-11-19); its output is kept, not regenerated.

Usage::

    pdftotext -raw -f 103 -l 103 TR-55_Manual.pdf a1.txt   # https://www.hydrocad.net/pdf/TR-55%20Manual.pdf
    cd tests/oracles && python transcribe_tr55_hsg.py a1.txt > tr55_hsg_text_layer.csv
"""

import csv
import re
import sys
from pathlib import Path


def transcribe(text: str) -> list[dict[str, str]]:
    """Return one row per texture the table lists, with its group and page."""
    lines = text.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.strip() == "HSG Soil textures"
    )
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("Drainage"))
    groups: dict[str, str] = {}
    current = ""
    for line in lines[start + 1 : end]:
        found = re.match(r"^([ABCD]) (.+)$", line.strip())
        if found:
            current = found.group(1)
            groups[current] = found.group(2)
        else:
            groups[current] += " " + line.strip()
    rows = []
    for group, textures in groups.items():
        for texture in re.split(r",\s*(?:or\s+)?|\s+or\s+", textures):
            name = texture.strip().lower().replace(" ", "_")
            rows.append({"texture_class": name, "hsg": group, "page": "A-1"})
    return rows


if __name__ == "__main__":
    rows = transcribe(Path(sys.argv[1]).read_text(encoding="utf-8"))
    writer = csv.DictWriter(
        sys.stdout, ["texture_class", "hsg", "page"], lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
