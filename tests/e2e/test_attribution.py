"""The providers' lines in the GUI (Nogat DEV-20, ECO-060), browser.

Against the real server of ``gui_server``: Statystyka przepływów opened from
Archiwista's hand-off of a station's series shows IMGW-PIB's attribution and terms
notice visibly with the result, from the hand-off's own lines and, for an older hand-off
without them, from the provider its provenance names; Hydrogram zlewni with a PMAXTP
depth shows PMAXTP's lines under its results, carries them into the CSV (DEV-20.5's two
columns), the hand-off, the print view and the PNG (taller by its footer); a result
without provider data has no footer and a CSV without those columns. The lines come from
``hydrolog._attribution``, the one source of them.
"""

import csv
import io
import json
import struct
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect

from hydrolog._attribution import provider_lines
from tests.e2e.conftest import Tab, open_part, seed_hydrogram
from tests.e2e.test_exports import download, handoff_button
from tests.e2e.test_hydrogram import MOCKUP, shows
from tests.e2e.test_statystyka import (
    MAXIMA,
    RIGHT,
    SECTION,
    compute,
    highlight,
    open_handoff,
    visit,
)

HG = 'section.section[data-section="hydrogram"]'
SETS = provider_lines()
IMGW = SETS["imgw"]
PMAXTP = SETS["pmaxtp"]


def footer_rows(page: Page, where: str) -> list[str]:
    """Return the visible lines of the footer „Źródła danych” in ``where``."""
    footer = page.locator(f'{where} footer.attribution[data-attribution="result"]')
    expect(footer).to_be_visible()
    return [row.strip() for row in footer.locator("p").all_inner_texts()]


def maxima_payload() -> dict[str, Any]:
    """Return the guide's annual maxima as Archiwista's hydrolog-series/1."""
    rows = [line.split(",") for line in MAXIMA.read_text("utf-8").splitlines()[1:]]
    return {
        "schema": "hydrolog-series/1",
        "name": "Raba — Q max",
        "variable": "Q",
        "unit": "m3/s",
        "step": "year",
        "statistic": "max",
        "year_type": "hydrological",
        "years": [int(year) for year, _ in rows],
        "values": [float(value) for _, value in rows],
    }


def archiwista(lines: bool) -> dict[str, Any]:
    """Return Archiwista's hand-off of the maxima, with its lines or (older) without."""
    doc: dict[str, Any] = {
        "schema": "nogat-handoff/1",
        "created_at": "2026-11-13T08:00:00Z",
        "producer": {"tool": "archiwista", "version": "0.4.0"},
        "subject": "Raba — maksima roczne",
        "provenance": {"series": {"source": "imgw-pib", "station": "149190310"}},
    }
    if lines:
        doc["attribution"] = IMGW["attribution"]
        doc["terms_notice"] = IMGW["terms_notice"]
    doc["payload"] = maxima_payload()
    return doc


def test_statystyka_from_archiwista_shows_imgws_lines_with_the_result(
    new_tab: Any, tmp_path: Path
) -> None:
    expected = [*IMGW["attribution"], *IMGW["terms_notice"]]
    # the hand-off's own lines, then an older one's provider named by its provenance
    for given in (True, False):
        page = visit(new_tab())
        open_handoff(page, archiwista(given), tmp_path)
        highlight(page, "100")
        response = compute(page)
        sent = response.request.post_data_json
        assert sent is not None
        assert sent["attribution"] == expected
        envelope = response.json()
        assert envelope["attribution"] == IMGW["attribution"]
        assert envelope["terms_notice"] == IMGW["terms_notice"]
        # Visible with the result (S, P, N, RD), in the centre and in the panel Wyniki
        assert footer_rows(page, f"{SECTION} .view-center") == expected
        assert footer_rows(page, RIGHT) == expected
        # And in the card of the hand-off in the panel Dane
        card = page.locator(
            f'{SECTION} [data-handoff-source="archiwista"] '
            '[data-attribution="handoff"] p'
        )
        expect(card).to_have_text(expected)
        # The quantiles' CSV carries them in its two trailing columns
        open_part_statystyka(page)
        _, data = download(
            page, page.locator(f"{RIGHT} .export-row button", has_text="CSV")
        )
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
        assert rows[0][-2:] == ["attribution", "terms_notice"]
        assert [row[-2] for row in rows[1:3]] == IMGW["attribution"]
        assert [row[-1] for row in rows[1:3]] == IMGW["terms_notice"]


def open_part_statystyka(page: Page) -> None:
    """Open Statystyka's part „Eksport” of the panel Wyniki."""
    part = page.locator(f'{RIGHT} details[data-part="exports"]')
    if part.get_attribute("open") is None:
        part.locator("summary").click()
    expect(part).to_have_attribute("open", "")


def png_height(data: bytes) -> int:
    """Return the height of a PNG from its IHDR."""
    return int(struct.unpack(">I", data[20:24])[0])


def test_hydrogram_with_pmaxtp_shows_and_carries_pmaxtps_lines(
    new_tab: Any, tmp_path: Path
) -> None:
    expected = [*PMAXTP["attribution"], *PMAXTP["terms_notice"]]
    tab = new_tab()
    seed_hydrogram(
        tab
    )  # the depth kept before the lines came: GET api/session gives them
    with tab.page.expect_request(
        lambda request: "/api/run/hydrograph/generate" in request.url
    ) as sent:
        tab.open("#hydrogram")
    page = tab.page
    shows(page, *MOCKUP[("scs", "kirpich", "II")])
    assert (sent.value.post_data_json or {})["attribution"] == expected
    right = f"{HG} .view-panel.right"
    assert footer_rows(page, f"{HG} .view-center") == expected
    assert footer_rows(page, right) == expected
    links = page.locator(
        f'{right} footer.attribution a[href="https://klimat.imgw.pl/opady-maksymalne"]'
    )
    expect(links.first).to_be_visible()

    # CSV: the hydrograph with DEV-20.5's two columns, one line per cell from the top
    open_part(page, HG, "exports")
    _, data = download(
        page, page.locator(f"{right} .export-row button", has_text="CSV")
    )
    rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
    assert rows[0] == [
        "time_min",
        "discharge_m3s",
        "precipitation_mm",
        "effective_precipitation_mm",
        "attribution",
        "terms_notice",
    ]
    assert [row[4] for row in rows[1:4]] == PMAXTP["attribution"]
    assert [row[5] for row in rows[1:3]] == PMAXTP["terms_notice"]
    assert {row[4] for row in rows[4:]} == {""}

    # PNG: the chart with the lines drawn below, so taller than the chart alone
    svg = page.locator(f"{HG} .view-center .chart.wide svg").first
    drawn = svg.evaluate("(svg) => Math.round(svg.getBoundingClientRect().height)")
    _, image = download(
        page, page.locator(f"{right} .export-row button", has_text="PNG")
    )
    assert png_height(image) > 2 * drawn

    # The hand-off carries both arrays
    _, handed = download(page, handoff_button(page, HG, "file"))
    doc = json.loads(handed)
    assert doc["attribution"] == PMAXTP["attribution"]
    assert doc["terms_notice"] == PMAXTP["terms_notice"]

    # On paper: the lines once, at the end of the results
    page.emulate_media(media="print")
    expect(page.locator(f"{right} footer.attribution")).to_be_visible()
    expect(page.locator(f"{HG} .view-center footer.attribution")).to_be_hidden()
    page.emulate_media(media="screen")


def test_a_result_without_provider_data_has_no_footer_and_no_columns(tab: Tab) -> None:
    page = visit(tab)
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    values = [line.split(",")[1] for line in MAXIMA.read_text("utf-8").splitlines()[1:]]
    page.locator(f"{SECTION} #st-values").fill("; ".join(values))
    highlight(page, "100")
    response = compute(page)
    assert "attribution" not in (response.request.post_data_json or {})
    assert "attribution" not in response.json()
    expect(page.locator(f"{SECTION} footer.attribution")).to_have_count(0)
    open_part_statystyka(page)
    _, data = download(
        page, page.locator(f"{RIGHT} .export-row button", has_text="CSV")
    )
    header = data.decode("utf-8").splitlines()[0]
    assert "attribution" not in header and "terms_notice" not in header
