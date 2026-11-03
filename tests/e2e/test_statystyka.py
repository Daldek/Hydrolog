"""„Statystyka przepływów” (plan S5, D13, D14, D16) in Chromium.

Against the real server of ``gui_server``: a first visit uploads the shipped sample
(the years 1998 to 2023 of ``tests/fixtures/annual_maxima.csv``) and „Oblicz” runs
``stats flood-frequency`` on it, giving the mockup's GEV „Q 1% 307,3 m³/s”, the KZGW
notice in Polish, the probability plot and the ranked maxima with their years; the call
shown is the options sent. A daily series takes its date column from its header; pasted
maxima run as ``values``; „Do porównania” hands the stressed quantile to the store.
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, Response, expect

from hydrolog.catalog import format_command, parse_command, run_command
from tests.e2e.conftest import Tab

COMMAND = "stats flood-frequency"
WEB = Path(__file__).resolve().parents[2] / "src" / "hydrolog" / "gui" / "web"
SAMPLE = WEB / "examples" / "maksima_roczne.csv"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SECTION = 'section[data-section="statystyka"]'
RIGHT = f"{SECTION} .view-panel.right"
BADGE = ".topbar .badge.status"
DEFAULT_PERIODS = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]


def open_section(tab: Tab) -> Page:
    """Open the section and wait for the sample's columns (a first visit uploads it)."""
    tab.open("#statystyka")
    expect(
        tab.page.locator(f'{SECTION} .handoff[data-file="in/maksima_roczne.csv"]')
    ).to_contain_text("26 wierszy")
    return tab.page


def compute(page: Page) -> Response:
    """Press „Oblicz”; return the answer of the run of the tables (not the curves)."""
    with page.expect_response(
        lambda response: response.url.endswith("channel=statystyka")
    ) as answer:
        page.locator(f"{SECTION} .panel-foot .btn.primary").click()
    return answer.value


def sent(response: Response) -> dict[str, Any]:
    """Return the options a run sent."""
    options = response.request.post_data_json
    assert isinstance(options, dict)
    return options


def test_the_sample_gives_the_mockups_gev_quantile_and_the_kzgw_notice(
    tab: Tab,
) -> None:
    page = open_section(tab)
    lines = SAMPLE.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "year,Qmax [m3/s]" and len(lines) == 27
    fixture = (FIXTURES / "annual_maxima.csv").read_text(encoding="utf-8").splitlines()
    assert lines[1:] == [
        line for line in fixture[1:] if 1998 <= int(line.split(",")[0]) <= 2023
    ]
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Qmax")

    response = compute(page)
    options = sent(response)
    assert options == {
        "input_file": "in/maksima_roczne.csv",
        "value_column": "Qmax",
        "distribution": "all",
        "return_periods": DEFAULT_PERIODS,
    }
    envelope = response.json()
    expected = run_command(COMMAND, {**options, "input_file": str(SAMPLE)}).to_dict()
    assert envelope["result"]["distributions"] == expected["result"]["distributions"]

    right = page.locator(RIGHT)
    expect(right.locator('.kpi[data-key="distribution"] .v')).to_have_text("GEV")
    expect(right.locator('.kpi[data-key="q-100"] .k')).to_have_text("Q 1%")
    expect(right.locator('.kpi[data-key="q-100"] .v')).to_have_text("307,3 m³/s")
    expect(right.locator('.kpi[data-key="n_years"] .v')).to_have_text("26 lat")
    kzgw = right.locator('.notes li[data-code="short_record"]')
    expect(kzgw).to_contain_text(
        "Liczba lat w szeregu: 26; KZGW (2017) wymaga co najmniej 30 lat danych"
    )
    expect(kzgw).not_to_contain_text("(EN)")
    expect(right.locator(".dtable tr.best th")).to_contain_text("GEV")
    expect(right.locator(".dtable tr.hl")).to_contain_text("307,3")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(page.locator(".crumb-context")).to_have_text(
        "maksima_roczne.csv · 26 lat (1998–2023)"
    )

    # The plot: 26 points, four curves (the best thicker), the quantile marked
    chart = page.locator(f"{SECTION} .view-center .chart svg")
    expect(chart.locator(".emp circle")).to_have_count(26)
    expect(chart.locator("path.ser")).to_have_count(4)
    expect(chart.locator("path.ser.best")).to_have_count(1)
    expect(chart.locator(".peak-label")).to_have_text("Q 1% = 307,3 m³/s (GEV)")

    # The call is the options sent, the file as the person named it
    shown = right.locator(".cli pre")
    expect(shown).to_have_text(re.compile(r"^hydrolog stats flood-frequency"))
    line = (shown.text_content() or "").replace(" \\\n  ", " ")
    assert line == format_command(
        COMMAND, {**options, "input_file": "maksima_roczne.csv"}
    )
    assert parse_command(line).options["value_column"] == "Qmax"

    # A change makes the result stale
    page.locator(f"{SECTION} #st-distribution").select_option("gev")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "stale")


def test_the_ranked_maxima_carry_their_years(tab: Tab) -> None:
    page = open_section(tab)
    compute(page)
    page.locator(f"{SECTION} .view-bar").get_by_role(
        "radio", name="Maksima roczne"
    ).click()
    rows = page.locator(f"{SECTION} .view-center .dtable tbody tr")
    expect(rows).to_have_count(26)
    expect(rows.first.locator("th, td")).to_have_text(["1", "2006", "315,4", "3,7"])
    expect(rows.nth(16).locator("th, td")).to_have_text(["17", "2022", "123,8", "63,0"])
    expect(rows.last.locator("th, td")).to_have_text(["26", "2020", "81,6", "96,3"])


def test_a_daily_series_takes_its_date_column(tab: Tab) -> None:
    page = open_section(tab)
    page.locator(
        f'{SECTION} [data-option="input_file"] input[type="file"]'
    ).set_input_files(FIXTURES / "daily_flows_3y.csv")
    expect(page.locator(f"{SECTION} #st-input_file")).to_have_value(
        "in/daily_flows_3y.csv"
    )
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Q")
    expect(page.locator(f"{SECTION} #st-date_column")).to_have_value("date")
    response = compute(page)
    assert sent(response)["date_column"] == "date"
    result = response.json()["result"]
    assert result["hydrological_years"] == [2022, 2023, 2024]
    page.locator(f"{SECTION} .view-bar").get_by_role(
        "radio", name="Maksima roczne"
    ).click()
    years = page.locator(f"{SECTION} .view-center .dtable tbody td.t")
    expect(years).to_have_text(["2024", "2022", "2023"])
    expect(page.locator(f'{RIGHT} .notes li[data-code="small_sample"]')).to_be_visible()


def test_pasted_maxima_run_and_go_to_the_comparison(tab: Tab) -> None:
    page = open_section(tab)
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    page.locator(f"{SECTION} #st-values").fill(
        "100,9; 148,6; 130; 140,3; 133,4; 87,2; 170,9; 141,1; 315,4; 126; 177,5; 116,9"
    )
    page.locator(f"{SECTION} .st-chosen").get_by_role(
        "button", name="50", exact=True
    ).click()
    response = compute(page)
    options = sent(response)
    assert set(options) == {"values", "distribution", "return_periods"}
    assert options["values"][:2] == [100.9, 148.6]
    result = response.json()["result"]
    best = next(
        fit
        for fit in result["distributions"]
        if fit["distribution_name"] == result["best_distribution"]
    )
    q50 = best["quantiles"][best["return_periods"].index(50.0)]
    right = page.locator(RIGHT)
    expect(right.locator('.kpi[data-key="q-50"]')).to_have_class(re.compile(r"\bhi\b"))
    expect(page.locator(".crumb-context")).to_have_text("wklejony szereg · 12 lat")

    hand = right.get_by_role("button", name="Do porównania")
    hand.click()
    expect(page.locator(".toast")).to_contain_text("Q 2% = ")
    reference = page.evaluate(
        "async () => (await import('./src/store.js')).getStore('reference')"
    )
    assert reference["peak_m3s"] == q50
    assert reference["label"].startswith("Q 2% (")
    assert reference["source"] == "stats flood-frequency · wklejony szereg"
    pressed = right.locator('button[aria-pressed="true"]')
    expect(pressed).to_have_count(1)
    pressed.click()
    assert (
        page.evaluate(
            "async () => (await import('./src/store.js')).getStore('reference')"
        )
        is None
    )


def test_a_phone_in_the_dark_computes_through_the_sheets(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    page = open_section(tab)
    sideways = """() => [document.documentElement,
      ...document.querySelectorAll('.view-panel.open .view-panel-body')]
      .filter((element) => element.scrollWidth > element.clientWidth).length"""
    page.locator(f"{SECTION} .view-bar").get_by_role(
        "button", name="Dane", exact=True
    ).click()
    left = page.locator(f"{SECTION} .view-panel.left")
    expect(left).to_be_visible()
    assert page.evaluate(sideways) == 0
    left.locator(".panel-foot .btn.primary").click()
    expect(page.locator(RIGHT)).to_be_visible()
    expect(page.locator(f'{RIGHT} .kpi[data-key="q-100"] .v')).to_have_text(
        "307,3 m³/s"
    )
    assert page.evaluate(sideways) == 0
