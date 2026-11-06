"""„Statystyka przepływów” (plan S5, D13, D14, D16; 2026-11-06, D3, D4, D5) in Chromium.

Against the real server of ``gui_server``: a first visit has no series and sends
nothing, a hint names what to load and links the guide's worked example; „Wyczyść”
returns there. The annual maxima of 1998 to 2023 (``tests/fixtures/maksima_roczne.csv``,
those years of ``annual_maxima.csv``) uploaded, T = 100 highlighted and „Oblicz” run
``stats flood-frequency``, giving the mockup's GEV „Q 1% 307,3 m³/s”, the KZGW notice
in Polish, the probability plot, the density and distribution-function charts (one curve
per distribution, a rug and the empirical points of the maxima) and the ranked maxima
with their years; the call shown is the options sent. A distribution ticked „W tabeli
kwantyli” adds its column of quantiles to the quantile table and the CSV, and a new
result ticks the best one alone again. A click on a row of the distributions table (or
Enter on it) makes that distribution the active one: the tiles, the full curve of the
three charts and „Do porównania” follow it, the other curves dimmed, until a new result;
the density chart is scaled to it (a GEV's spike on twelve maxima clipped at the frame).
No period is highlighted at first („brak”): no highlighted tile or row, no marked
quantile on the charts and „Do porównania” off until one is chosen, the choice stored.
A daily series takes its date column from its header; pasted maxima run
as ``values``; „Do porównania” hands the stressed quantile to the store. „Jednorodność
ciągu” runs ``stats homogeneity`` on the same series: the guide's pasted maxima pass
the three tests, split by their positions; a file with a step after 2010 fails them,
with the split and Pettitt's change point in years and the notice in Polish. A
station's series handed off by Archiwista (``hydrolog-series/1``, ADR-0020) opens here
with „Wczytaj z Archiwisty”: annual maxima as the pasted values without the missing
years, daily values as a file of the session with its columns; annual minima are
refused.
"""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Locator, Page, Request, Response, expect

from hydrolog.catalog import format_command, parse_command, run_command
from tests.e2e.conftest import Tab, open_part

COMMAND = "stats flood-frequency"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
GUIDE = (
    Path(__file__).resolve().parents[2] / "src/hydrolog/gui/web/instrukcja/index.html"
)
MAXIMA = FIXTURES / "maksima_roczne.csv"
SECTION = 'section[data-section="statystyka"]'
RIGHT = f"{SECTION} .view-panel.right"
BADGE = ".topbar .badge.status"
HOMOGENEITY = f'{RIGHT} [data-part="homogeneity"]'
PROBABILITY = f"{SECTION} .view-center .st-chart .chart svg"
DENSITY = f'{SECTION} .view-center [data-chart="density"] svg'
DISTRIBUTION = f'{SECTION} .view-center [data-chart="distribution"] svg'
DEFAULT_PERIODS = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]
NAMES = {
    "gev": "GEV",
    "log_normal": "log-normalny",
    "pearson3": "Pearson III",
    "weibull": "Weibull",
}


def open_section(tab: Tab) -> Page:
    """Open the section, upload the maxima of 1998–2023 and wait for their columns."""
    tab.open("#statystyka")
    upload(tab.page, MAXIMA)
    expect(
        tab.page.locator(f'{SECTION} .handoff[data-file="in/maksima_roczne.csv"]')
    ).to_contain_text("26 wierszy")
    return tab.page


def upload(page: Page, path: Path) -> None:
    """Upload ``path`` with the file field of the series."""
    page.locator(
        f'{SECTION} [data-option="input_file"] input[type="file"]'
    ).set_input_files(path)


def compute(page: Page) -> Response:
    """Press „Oblicz”; return the answer of the run of the tables (not the curves)."""
    with page.expect_response(
        lambda response: response.url.endswith("channel=statystyka")
    ) as answer:
        page.locator(f"{SECTION} .panel-foot .btn.primary").click()
    return answer.value


def compute_tested(page: Page) -> Response:
    """Press „Oblicz”; return the answer of the run of the homogeneity tests."""
    with page.expect_response(
        lambda response: response.url.endswith("channel=statystyka-jednorodnosc")
    ) as answer:
        compute(page)
    return answer.value


def sent(response: Response) -> dict[str, Any]:
    """Return the options a run sent."""
    options = response.request.post_data_json
    assert isinstance(options, dict)
    return options


def download(page: Page, trigger: Locator) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


def highlight(page: Page, period: str) -> None:
    """Choose ``period`` („brak” for none) in „Wyróżniony w wynikach”."""
    page.locator(f"{SECTION} .st-chosen").get_by_role(
        "button", name=period, exact=True
    ).click()


def test_a_first_visit_is_empty_and_clearing_returns_there(tab: Tab) -> None:
    posted: list[str] = []
    tab.page.on(
        "request",
        lambda request: (
            posted.append(request.url) if request.method == "POST" else None
        ),
    )
    tab.open("#statystyka")
    page = tab.page
    hint = page.locator(f'{SECTION} [data-empty="statystyka"]')
    expect(hint).to_contain_text("Wczytaj plik CSV")
    expect(hint.get_by_role("link")).to_have_attribute(
        "href", "instrukcja/#przyklad-statystyka"
    )
    expect(page.locator(f"{SECTION} #st-input_file")).to_have_value("")
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("")
    expect(page.locator(f"{SECTION} .handoff[data-file]")).to_have_count(0)
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    expect(page.locator(f"{SECTION} #st-values")).to_have_value("")
    expect(hint).to_contain_text("Wklej co najmniej kilka maksimów")
    assert posted == []  # no upload, no run

    # „Oblicz” on nothing: the required field says so, nothing is sent
    page.locator(f"{SECTION} .panel-foot .btn.primary").click()
    expect(page.locator(f"{SECTION} #st-values")).to_have_attribute(
        "aria-invalid", "true"
    )
    assert posted == []

    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Plik CSV").click()
    upload(page, MAXIMA)
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Qmax")
    page.locator(f"{SECTION} .panel-foot").get_by_role("button", name="Wyczyść").click()
    expect(page.locator(f"{SECTION} #st-input_file")).to_have_value("")
    expect(hint).to_be_visible()
    page.reload()
    expect(page.locator(f"{SECTION} #st-input_file")).to_have_value("")


def test_the_maxima_give_the_mockups_gev_quantile_and_the_kzgw_notice(
    tab: Tab,
) -> None:
    page = open_section(tab)
    lines = MAXIMA.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "year,Qmax [m3/s]" and len(lines) == 27
    fixture = (FIXTURES / "annual_maxima.csv").read_text(encoding="utf-8").splitlines()
    assert lines[1:] == [
        line for line in fixture[1:] if 1998 <= int(line.split(",")[0]) <= 2023
    ]
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Qmax")
    highlight(page, "100")

    response = compute(page)
    options = sent(response)
    assert options == {
        "input_file": "in/maksima_roczne.csv",
        "value_column": "Qmax",
        "distribution": "all",
        "return_periods": DEFAULT_PERIODS,
    }
    envelope = response.json()
    expected = run_command(COMMAND, {**options, "input_file": str(MAXIMA)}).to_dict()
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
    expect(right.locator('.dtable tr[aria-current="true"] th')).to_contain_text("GEV")
    expect(right.locator('.kpi[data-key="distribution"] .k')).to_have_text("Najlepszy")
    expect(right.locator(".dtable tr.hl")).to_contain_text("307,3")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(page.locator(".crumb-context")).to_have_text(
        "maksima_roczne.csv · 26 lat (1998–2023)"
    )

    # The plot: 26 points, four curves (the best one active, the others dimmed), the
    # quantile marked
    chart = page.locator(PROBABILITY)
    expect(chart.locator(".emp circle")).to_have_count(26)
    expect(chart.locator("path.ser")).to_have_count(4)
    expect(chart.locator('path.ser.active[data-series="gev"]')).to_have_count(1)
    expect(chart.locator("path.ser.dim")).to_have_count(3)
    expect(chart.locator(".peak-label")).to_have_text("Q 1% = 307,3 m³/s (GEV)")

    # The density: one curve per distribution, the maxima as a rug on the Q axis; the
    # distribution function: one curve per distribution and the maxima as points
    density = page.locator(DENSITY)
    expect(density.locator("path.ser")).to_have_count(4)
    expect(density.locator('path.ser.active[data-series="gev"]')).to_have_count(1)
    expect(density.locator("path.ser.dim")).to_have_count(3)
    expect(density.locator('.rug[data-series="maxima"] line')).to_have_count(26)
    distribution = page.locator(DISTRIBUTION)
    expect(distribution.locator("path.ser")).to_have_count(4)
    expect(distribution.locator('path.ser.active[data-series="gev"]')).to_have_count(1)
    expect(distribution.locator("path.ser.dim")).to_have_count(3)
    expect(distribution.locator(".emp circle")).to_have_count(26)

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


def test_a_fit_method_recomputes_both_runs_with_it(tab: Tab) -> None:
    page = open_section(tab)
    sent_by_channel: dict[str, Any] = {}

    def record(request: Request) -> None:
        if request.method == "POST" and "channel=" in request.url:
            channel = request.url.rsplit("channel=", 1)[-1]
            sent_by_channel[channel] = request.post_data_json

    page.on("request", record)
    highlight(page, "100")
    compute(page)
    right = page.locator(RIGHT)
    subtitle = page.locator(f"{SECTION} .st-chart .card-sub")
    expect(subtitle).to_have_attribute("data-fit-method", "mle")
    expect(right.locator('.kpi[data-key="q-100"] .v')).to_have_text("307,3 m³/s")
    assert "fit_method" not in sent_by_channel["statystyka"]

    page.locator(f"{SECTION} #st-fit_method").select_option("l_moments")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "stale")
    response = compute(page)

    assert sent_by_channel["statystyka"]["fit_method"] == "l_moments"
    assert sent_by_channel["statystyka-krzywe"]["fit_method"] == "l_moments"
    assert response.json()["result"]["fit_method"] == "l_moments"
    expect(subtitle).to_have_attribute("data-fit-method", "l_moments")
    expect(subtitle).to_contain_text("metodą L-momentów")
    expect(right.locator('.kpi[data-key="q-100"] .v')).to_have_text("324,9 m³/s")
    expect(right.locator(".cli pre")).to_contain_text("--fit-method l_moments")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")


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


def test_no_period_is_highlighted_until_one_is_chosen(tab: Tab) -> None:
    page = open_section(tab)
    chips = page.locator(f"{SECTION} .st-chosen button")
    expect(chips.filter(has_text="brak")).to_have_attribute("aria-pressed", "true")
    compute(page)
    right = page.locator(RIGHT)
    charts = [
        page.locator(PROBABILITY),
        page.locator(DENSITY),
        page.locator(DISTRIBUTION),
    ]
    hand = right.get_by_role("button", name="Do porównania")
    open_part(page, SECTION, "exports")

    # „brak”: no highlighted tile or row, no marked quantile, „Do porównania” off
    expect(right.locator(".kpi.hi")).to_have_count(0)
    expect(right.locator('.kpi[data-key="q-100"]')).to_have_count(0)
    expect(right.locator(".dtable tr.hl")).to_have_count(0)
    for chart in charts:
        expect(chart.locator("path.ser")).to_have_count(4)
        expect(chart.locator(".peak-dot, .peak-line, .peak-label")).to_have_count(0)
    expect(hand).to_be_disabled()
    expect(hand).to_have_attribute("title", re.compile("^Wybierz okres"))

    # A period chosen: its tile, its row, its quantile on the probability plot, and it
    # can be handed over; the choice is stored
    highlight(page, "100")
    expect(right.locator('.kpi[data-key="q-100"]')).to_have_class(re.compile(r"\bhi\b"))
    expect(right.locator(".dtable tr.hl th")).to_have_text("100")
    expect(charts[0].locator(".peak-label")).to_have_text("Q 1% = 307,3 m³/s (GEV)")
    expect(hand).to_be_enabled()
    page.reload()
    expect(chips.filter(has_text=re.compile(r"^100$"))).to_have_attribute(
        "aria-pressed", "true"
    )

    # „brak” again turns it all off
    highlight(page, "brak")
    compute(page)
    open_part(page, SECTION, "exports")
    expect(right.locator(".kpi.hi")).to_have_count(0)
    expect(right.locator(".dtable tr.hl")).to_have_count(0)
    expect(charts[0].locator(".peak-dot, .peak-line, .peak-label")).to_have_count(0)
    expect(hand).to_be_disabled()


def test_ticked_distributions_add_their_quantiles_to_the_table_and_the_csv(
    tab: Tab,
) -> None:
    page = open_section(tab)
    highlight(page, "100")
    result = compute(page).json()["result"]
    fits = result["distributions"]
    assert fits[0]["distribution_name"] == result["best_distribution"] == "gev"
    right = page.locator(RIGHT)
    boxes = right.get_by_role("checkbox", name=re.compile(r"^W tabeli kwantyli: "))
    expect(boxes).to_have_count(4)
    # Only the best one is ticked, and it cannot be the last one taken away
    best = right.get_by_role("checkbox", name="W tabeli kwantyli: GEV")
    expect(best).to_be_checked()
    expect(best).to_be_disabled()
    quantiles = right.get_by_role("region", name="Kwantyle: GEV")
    expect(quantiles.locator("thead th")).to_have_text(
        ["T [lata]", "p [%]", "Q GEV [m³/s]"]
    )

    # Ticked third, then second: the columns follow the distributions table
    third, second = fits[2], fits[1]
    for fit in (third, second):
        right.get_by_role(
            "checkbox", name=f"W tabeli kwantyli: {NAMES[fit['distribution_name']]}"
        ).check()
    shown = [fits[0], second, third]
    title = "Kwantyle: " + ", ".join(NAMES[fit["distribution_name"]] for fit in shown)
    expect(
        right.get_by_role("heading", name=re.compile(rf"^{re.escape(title)} "))
    ).to_be_visible()
    quantiles = right.get_by_role("region", name=title)
    expect(quantiles.locator("thead th")).to_have_text(
        ["T [lata]", "p [%]"]
        + [f"Q {NAMES[fit['distribution_name']]} [m³/s]" for fit in shown]
    )
    expect(best).to_be_enabled()
    rows = quantiles.locator("tbody tr")
    expect(rows).to_have_count(len(DEFAULT_PERIODS))
    for index in range(len(DEFAULT_PERIODS)):
        expect(rows.nth(index).locator("td").nth(-2)).to_have_text(
            f"{second['quantiles'][index]:.1f}".replace(".", ",")
        )
    # The highlighted period (T = 100) is still the marked row
    expect(quantiles.locator("tr.hl th")).to_have_text("100")
    expect(quantiles.locator("tr.hl td").nth(1)).to_have_text("307,3")

    open_part(page, SECTION, "exports")
    name, data = download(
        page, right.locator(".export-row button").filter(has_text="CSV")
    )
    assert name == "maksima_roczne-kwantyle.csv"
    header, *lines = [line.split(",") for line in data.decode("utf-8").splitlines()]
    assert header == [
        "return_period_years",
        "exceedance_probability",
        *(f"{fit['distribution_name']}_m3s" for fit in shown),
    ]
    assert [float(line[0]) for line in lines] == DEFAULT_PERIODS
    for column, fit in enumerate(shown, start=2):
        assert [float(line[column]) for line in lines] == fit["quantiles"]

    # A new result ticks the best one alone again
    compute(page)
    expect(right.get_by_role("checkbox", checked=True)).to_have_count(1)
    expect(best).to_be_checked()
    expect(right.get_by_role("region", name="Kwantyle: GEV")).to_be_visible()


def test_a_clicked_row_drives_the_tiles_the_plot_and_the_comparison(tab: Tab) -> None:
    page = open_section(tab)
    highlight(page, "100")
    result = compute(page).json()["result"]
    other = result["distributions"][1]
    name = other["distribution_name"]
    assert name == "log_normal" and result["best_distribution"] == "gev"
    q100 = other["quantiles"][other["return_periods"].index(100.0)]
    right = page.locator(RIGHT)
    tile = right.locator('.kpi[data-key="distribution"]')
    chart = page.locator(PROBABILITY)
    shapes = [page.locator(DENSITY), page.locator(DISTRIBUTION)]
    rows = right.get_by_role("region", name="Rozkłady").locator("tbody tr")

    rows.nth(1).locator("th").click()
    expect(tile.locator(".k")).to_have_text("Rozkład")
    expect(tile.locator(".v")).to_have_text("log-normalny")
    expect(right.locator('.kpi[data-key="q-100"] .v')).to_have_text(
        f"{q100:.1f}".replace(".", ",") + " m³/s"
    )
    expect(rows.nth(1)).to_have_attribute("aria-current", "true")
    expect(rows.nth(0)).not_to_have_attribute("aria-current", "true")
    expect(chart.locator(f'path.ser.active[data-series="{name}"]')).to_have_count(1)
    expect(chart.locator('path.ser.dim[data-series="gev"]')).to_have_count(1)
    expect(chart.locator("path.ser.dim")).to_have_count(3)
    for shape in shapes:
        expect(shape.locator(f'path.ser.active[data-series="{name}"]')).to_have_count(1)
        expect(shape.locator('path.ser.dim[data-series="gev"]')).to_have_count(1)
    expect(chart.locator(".peak-label")).to_have_text(
        f"Q 1% = {q100:.1f}".replace(".", ",") + " m³/s (Log-normalny)"
    )

    # A checkbox ticks, it does not make its distribution active
    rows.nth(2).get_by_role("checkbox").check()
    expect(rows.nth(1)).to_have_attribute("aria-current", "true")

    # „Do porównania” hands the active distribution's quantile
    open_part(page, SECTION, "exports")
    right.get_by_role("button", name="Do porównania").click()
    reference = page.evaluate(
        "async () => (await import('./src/store.js')).getStore('reference')"
    )
    assert reference["peak_m3s"] == q100
    assert reference["label"] == "Q 1% (log-normalny)"

    # The keyboard: Enter on a focused row; a new result makes the best one active again
    rows.nth(3).focus()
    page.keyboard.press("Enter")
    expect(tile.locator(".v")).to_have_text("Weibull")
    compute(page)
    expect(tile.locator(".k")).to_have_text("Najlepszy")
    expect(tile.locator(".v")).to_have_text("GEV")
    expect(chart.locator('path.ser.active[data-series="gev"]')).to_have_count(1)
    for shape in shapes:
        expect(shape.locator('path.ser.active[data-series="gev"]')).to_have_count(1)


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


def test_the_density_chart_is_scaled_to_the_active_distribution(tab: Tab) -> None:
    # Twelve maxima whose GEV has a spike at its lower bound (a density of about 53
    # against the best fit's, the log-normal's, 0,0096 at most)
    page = open_section(tab)
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    page.locator(f"{SECTION} #st-values").fill(
        "100,9; 148,6; 130; 140,3; 133,4; 87,2; 170,9; 141,1; 315,4; 126; 177,5; 116,9"
    )
    result = compute(page).json()["result"]
    assert result["best_distribution"] == "log_normal"
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    density = page.locator(DENSITY)
    expect(density.locator('path.ser.active[data-series="log_normal"]')).to_have_count(
        1
    )
    expect(density.locator("path.ser")).to_have_count(4)

    shown = density.evaluate(
        """svg => {
          const frame = svg.querySelector('g.grid.v line');
          const top = Number(frame.getAttribute('y1'));
          const bottom = Number(frame.getAttribute('y2'));
          return [...svg.querySelectorAll('path.ser')].map((path) =>
            [path.dataset.series, (bottom - path.getBBox().y) / (bottom - top)]);
        }"""
    )
    heights = dict(shown)
    # The active curve's peak in the upper part of the frame; the GEV's spike clipped at
    # its top, as every other curve stays within it
    assert heights["log_normal"] > 0.6
    assert heights["gev"] == pytest.approx(1.0, abs=0.01)
    assert max(heights.values()) <= 1.01


def test_pasted_maxima_run_and_go_to_the_comparison(tab: Tab) -> None:
    page = open_section(tab)
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    page.locator(f"{SECTION} #st-values").fill(
        "100,9; 148,6; 130; 140,3; 133,4; 87,2; 170,9; 141,1; 315,4; 126; 177,5; 116,9"
    )
    highlight(page, "50")
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
    open_part(page, SECTION, "exports")
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


def test_the_guides_series_passes_the_three_homogeneity_tests(tab: Tab) -> None:
    found = re.search(
        r'data-paste="statystyka-values">([^<]*)<', GUIDE.read_text(encoding="utf-8")
    )
    assert found
    tab.open("#statystyka")
    page = tab.page
    page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej").click()
    page.locator(f"{SECTION} #st-values").fill(found.group(1))

    response = compute_tested(page)
    options = sent(response)
    assert set(options) == {"values"} and len(options["values"]) == 26
    expected = run_command("stats homogeneity", options).to_dict()["result"]
    assert response.json()["result"] == expected
    panel = page.locator(HOMOGENEITY)
    table = panel.get_by_role("region", name="Jednorodność ciągu")
    rows = table.locator("tbody tr")
    expect(rows).to_have_count(3)
    expect(table.locator("thead th")).to_have_text(
        ["Test", "Statystyka", "p", "Jednorodny"]
    )
    expect(rows.nth(0).locator("th, td")).to_have_text(
        ["Mann-Whitney", "U = 94", "0,644", "✓ tak"]
    )
    expect(rows.nth(1).locator("th, td")).to_have_text(
        ["Kołmogorow-Smirnow", "D = 0,308", "0,588", "✓ tak"]
    )
    expect(rows.nth(2).locator("th, td")).to_have_text(
        ["Pettitt", "K = 50", "0,879", "✓ tak"]
    )
    # Pasted values have no years: the split and the change point are positions
    expect(panel.locator(".note")).to_have_text(
        "Podział: wartości 1–13 i 14–26. Najbardziej prawdopodobny punkt zmiany "
        "(Pettitt): po 22. wartości (nieistotny przy α = 0,05). Test odrzuca "
        "jednorodność, gdy p < α = 0,05."
    )
    expect(
        page.locator(f'{RIGHT} .notes li[data-code="homogeneity_rejected"]')
    ).to_have_count(0)
    panel.locator('[data-info="stats-homogeneity"]').click()
    expect(page.locator(".info-pop #info-pop-title")).to_have_text(
        "Jednorodność ciągu: testy Manna-Whitneya, Kołmogorowa-Smirnowa i Pettitta"
    )


def test_a_step_in_the_series_fails_the_tests_at_its_year(
    tab: Tab, tmp_path: Path
) -> None:
    path = tmp_path / "skok.csv"
    rows = [f"{2001 + index},{50 + index}" for index in range(10)]
    rows += [f"{2011 + index},{100 + index}" for index in range(10)]
    path.write_text("year,Qmax [m3/s]\n" + "\n".join(rows) + "\n", encoding="utf-8")
    tab.open("#statystyka")
    page = tab.page
    upload(page, path)
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Qmax")

    response = compute_tested(page)
    # The file's year column goes with it: the split and the change point have years
    assert sent(response) == {
        "input_file": "in/skok.csv",
        "value_column": "Qmax",
        "year_column": "year",
    }
    panel = page.locator(HOMOGENEITY)
    rows_shown = panel.get_by_role("region", name="Jednorodność ciągu")
    expect(rows_shown.locator("tbody tr td:last-child")).to_have_text(["✗ nie"] * 3)
    expect(rows_shown.locator("tbody tr td:nth-child(3)")).to_have_text(
        ["< 0,001", "< 0,001", "0,002"]
    )
    expect(panel.locator(".note")).to_have_text(
        "Podział od roku 2011: 10 lat wcześniej, 10 lat od 2011. Najbardziej "
        "prawdopodobny punkt zmiany (Pettitt): 2011, pierwszy rok po zmianie. Test "
        "odrzuca jednorodność, gdy p < α = 0,05."
    )
    rejected = page.locator(f'{RIGHT} .notes li[data-code="homogeneity_rejected"]')
    expect(rejected).to_contain_text(
        "Testy odrzucające jednorodność ciągu przy α = 0,05: Mann-Whitney, "
        "Kołmogorow-Smirnow, Pettitt."
    )
    expect(rejected).not_to_contain_text("(EN)")


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
    highlight(page, "100")
    left.locator(".panel-foot .btn.primary").click()
    expect(page.locator(RIGHT)).to_be_visible()
    expect(page.locator(f'{RIGHT} .kpi[data-key="q-100"] .v')).to_have_text(
        "307,3 m³/s"
    )
    assert page.evaluate(sideways) == 0


# --- a station's series handed off by Archiwista (ADR-0020) ------------------------


def handoff(payload: dict[str, Any], subject: str) -> dict[str, Any]:
    """Return a hand-off from Archiwista carrying ``payload``."""
    return {
        "schema": "nogat-handoff/1",
        "created_at": "2026-11-05T20:00:00Z",
        "producer": {"tool": "archiwista", "version": "0.3.0.dev0"},
        "subject": subject,
        "provenance": {"series": {"source": "imgw-pib", "station": "149190310"}},
        "payload": payload,
    }


def open_handoff(page: Page, doc: dict[str, Any], tmp_path: Path) -> None:
    """Open ``doc`` with „Wczytaj z Archiwisty” → „Plik przekazania…”."""
    path = tmp_path / "seria.handoff.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    page.locator(f"{SECTION} .view-panel.left").get_by_role(
        "button", name="Wczytaj z Archiwisty"
    ).click()
    with page.expect_file_chooser() as chooser:
        page.get_by_role("menuitem").filter(has_text="Plik przekazania").click()
    chooser.value.set_files(str(path))


def test_annual_maxima_from_archiwista_run_as_values_without_the_missing_years(
    tab: Tab, tmp_path: Path
) -> None:
    rows = [line.split(",") for line in MAXIMA.read_text("utf-8").splitlines()[1:]]
    maxima = [float(value) for _, value in rows]
    payload = {
        "schema": "hydrolog-series/1",
        "name": "Raba — Q max",
        "variable": "Q",
        "unit": "m3/s",
        "step": "year",
        "statistic": "max",
        "year_type": "hydrological",
        "years": [1997] + [int(year) for year, _ in rows],
        "values": [None, *maxima],
    }
    tab.open("#statystyka")
    page = tab.page

    open_handoff(page, handoff(payload, "Raba — maksima roczne"), tmp_path)

    expect(
        page.locator(f'{SECTION} [data-handoff-source="archiwista"]')
    ).to_contain_text("Z Archiwisty: Raba — maksima roczne")
    expect(
        page.locator(f"{SECTION} .step").first.get_by_role("radio", name="Wklej")
    ).to_be_checked()
    highlight(page, "100")
    options = sent(compute(page))
    assert options["values"] == maxima
    expect(page.locator(f'{RIGHT} .kpi[data-key="q-100"] .v')).to_have_text(
        "307,3 m³/s"
    )
    # A series typed over is the person's: the origin goes
    page.locator(f"{SECTION} #st-values").fill("100; 120; 140")
    expect(page.locator(f"{SECTION} [data-handoff-source]")).to_have_count(0)


def test_a_daily_series_from_archiwista_becomes_a_session_file_with_its_columns(
    tab: Tab, tmp_path: Path
) -> None:
    lines = (FIXTURES / "daily_flows_3y.csv").read_text("utf-8").splitlines()[1:]
    days = [line.split(",") for line in lines]
    payload = {
        "schema": "hydrolog-series/1",
        "name": "Raba — Q",
        "variable": "Q",
        "unit": "m3/s",
        "step": "day",
        "dates": [day for day, _ in days],
        "values": [float(value) for _, value in days],
    }
    tab.open("#statystyka")
    page = tab.page

    open_handoff(page, handoff(payload, "Raba — Q dobowe"), tmp_path)

    expect(page.locator(f"{SECTION} #st-input_file")).to_have_value(
        re.compile(r"^in/Raba.*Q dobowe\.csv$")
    )
    expect(page.locator(f"{SECTION} #st-value_column")).to_have_value("Q")
    expect(page.locator(f"{SECTION} #st-date_column")).to_have_value("date")
    response = compute(page)
    assert sent(response)["date_column"] == "date"
    assert response.json()["result"]["hydrological_years"] == [2022, 2023, 2024]


def test_annual_minima_and_a_short_series_are_refused_with_the_reason(
    tab: Tab, tmp_path: Path
) -> None:
    minima = {
        "schema": "hydrolog-series/1",
        "name": "Raba — Q min",
        "variable": "Q",
        "unit": "m3/s",
        "step": "year",
        "statistic": "min",
        "year_type": "hydrological",
        "years": [2020, 2021],
        "values": [1.2, 0.9],
    }
    tab.open("#statystyka")
    page = tab.page
    problems = page.locator(f"{SECTION} [data-handoff-problems] li")

    open_handoff(page, handoff(minima, "Raba — minima"), tmp_path)
    expect(problems).to_have_text([re.compile(r"^To są minima roczne")])

    open_handoff(
        page, handoff({**minima, "statistic": "max", "values": [1.2]}, "Raba"), tmp_path
    )
    expect(problems).to_have_text(
        ["Szereg ma 2 dat albo lat i 1 wartości: powinno być tyle samo."]
    )
    expect(page.locator(f"{SECTION} [data-handoff-source]")).to_have_count(0)
