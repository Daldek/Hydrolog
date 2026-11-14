"""The providers' lines in the GUI (Nogat DEV-20, ECO-060, ECO-064), browser.

Against the real server of ``gui_server``: Statystyka przepływów opened from
Archiwista's hand-off of a station's series shows IMGW-PIB's lines in the view's one
strip, from the hand-off's own lines and, for an older hand-off without them, from the
provider its provenance names; Hydrogram zlewni with a PMAXTP depth shows PMAXTP's lines
in its strip, carries them in full into the CSV (DEV-20.5's two columns), the hand-off,
the print view and the PNG (taller by its footer), and the welcome dialog lists them; a
result without provider data has no strip, a CSV without those columns and a welcome
dialog of its sentences alone. The strip shows the short lines (S, P, PS, PP) and
„Źródła i warunki”, whose dialog lists every line; no full block stands on screen. The
lines come from ``hydrolog._attribution``, the one source of them.
"""

import csv
import io
import json
import struct
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect

from hydrolog._attribution import provider_lines
from tests.e2e.conftest import (
    Tab,
    kamiennik_inputs,
    open_part,
    seed_hydrogram,
    sources_listed,
    sources_shown,
)
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
        # One strip under the centre: IMGW-PIB's S and P, every line in its dialog
        assert sources_shown(page, SECTION) == IMGW["attribution"]
        assert sources_listed(page, SECTION) == expected
        # No full block on screen: not under the results, nor in the hand-off's card
        expect(page.locator(f"{SECTION} footer.attribution:visible")).to_have_count(0)
        card = page.locator(
            f'{SECTION} [data-handoff-source="archiwista"] '
            '[data-attribution="handoff"] p'
        )
        expect(card).to_have_text(expected)
        expect(card.first).to_be_hidden()
        # The quantiles' CSV carries them in its two trailing columns
        open_part_statystyka(page)
        _, data = download(
            page, page.locator(f"{RIGHT} .export-row button", has_text="CSV")
        )
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
        assert rows[0][-2:] == ["attribution", "terms_notice"]
        assert [row[-2] for row in rows[1:3]] == IMGW["attribution"]
        assert [row[-1] for row in rows[1:3] if row[-1]] == IMGW["terms_notice"]


def test_an_older_chmi_handoff_shows_and_sends_on_one_cp(
    new_tab: Any, tmp_path: Path
) -> None:
    """Nogat ECO-071: a hand-off of before it says in parentheses how ČHMÚ's data were
    processed, twice; the page and the run give the one CP."""
    chmi = SETS["chmi"]["attribution"]
    doc = archiwista(False)
    doc["attribution"] = [
        chmi[0],
        "Dane ČHMÚ zostały przetworzone (normalizacja i zmiana formatu)",
        "Dane ČHMÚ zostały przetworzone (obliczenia hydrologiczne programem Hydrolog)",
    ]
    page = visit(new_tab())
    open_handoff(page, doc, tmp_path)
    card = page.locator(
        f'{SECTION} [data-handoff-source="archiwista"] [data-attribution="handoff"] p'
    )
    expect(card).to_have_text(chmi)
    highlight(page, "100")
    envelope = compute(page).json()
    assert envelope["attribution"] == chmi
    assert sources_listed(page, SECTION) == chmi


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
    # The strip shows PS and PP; the monograph and the terms are in its dialog
    assert sources_shown(page, HG) == PMAXTP["attribution"][:2]
    assert sources_listed(page, HG) == expected
    strip = page.locator(f"{HG} .view-center nogat-sources")
    expect(
        strip.locator('a[href="https://klimat.imgw.pl/opady-maksymalne"]').first
    ).to_be_visible()
    expect(page.locator(f"{HG} footer.attribution:visible")).to_have_count(0)

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
    assert [row[5] for row in rows[1:3] if row[5]] == PMAXTP["terms_notice"]
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

    # On paper: the full lines, at the end of the results and under the depth; no strip
    page.emulate_media(media="print")
    expect(page.locator(f"{right} footer.attribution")).to_be_visible()
    printed = page.locator(f'{right} footer.attribution[data-attribution="result"] p')
    expect(printed).to_have_text(expected)
    expect(page.locator(f'{HG} [data-attribution="pmaxtp"]')).to_be_visible()
    expect(strip).to_be_hidden()
    page.emulate_media(media="screen")

    # The welcome dialog, opened from „Instrukcja”, lists the lines of the page's data
    page.get_by_role("link", name="Instrukcja", exact=True).click()
    welcome = page.locator("dialog.welcome")
    expect(welcome).to_be_visible()
    listed = welcome.locator("[data-welcome-sources] li")
    expect(listed).to_have_text(expected)


def test_a_depth_kept_with_retired_lines_shows_the_current_ones(new_tab: Any) -> None:
    """A depth the browser kept before Nogat ECO-065 holds N and „Regulamin: …”."""
    expected = [*PMAXTP["attribution"], *PMAXTP["terms_notice"]]
    kept = {
        **kamiennik_inputs()["pmaxtp_fetched"],
        "attribution": PMAXTP["attribution"],
        "terms_notice": [
            "Dane IMGW-PIB można wykorzystywać nieodpłatnie do celów prywatnych "
            "(niezarobkowych). Wykorzystanie w działalności gospodarczej, na "
            "stronach z reklamami lub do celów wymienionych w regulaminie (m.in. "
            "planowanie w gospodarowaniu wodami, art. 317 Prawa wodnego) wymaga "
            "umowy z IMGW-PIB.",
            "Regulamin: https://klimat.imgw.pl/opady-maksymalne",
        ],
    }
    tab = new_tab()
    seed_hydrogram(tab, kamiennik_inputs(pmaxtp_fetched=kept))
    tab.open("#hydrogram")
    page = tab.page
    shows(page, *MOCKUP[("scs", "kirpich", "II")])

    assert sources_listed(page, HG) == expected
    page.emulate_media(media="print")
    printed = page.locator(f'{HG} [data-attribution="pmaxtp"] p')
    expect(printed).to_have_text(expected)
    page.emulate_media(media="screen")


def test_the_welcome_of_a_first_visit_has_its_sentences_alone(
    new_tab: Any,
) -> None:
    tab = new_tab(welcome=True)
    tab.open()
    welcome = tab.page.get_by_role("dialog", name="Witaj w Hydrologu")
    expect(welcome).to_be_visible()
    expect(welcome.locator("[data-welcome-sources]")).to_have_count(0)
    expect(tab.page.locator("nogat-sources:visible")).to_have_count(0)


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
    expect(page.locator(f"{SECTION} nogat-sources")).to_be_hidden()
    open_part_statystyka(page)
    _, data = download(
        page, page.locator(f"{RIGHT} .export-row button", has_text="CSV")
    )
    header = data.decode("utf-8").splitlines()[0]
    assert "attribution" not in header and "terms_notice" not in header
