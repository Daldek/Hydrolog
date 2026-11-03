"""„Hydrogram zlewni” (plan D13, D14, D16, slice S3) in Chromium.

Against the real server of ``gui_server``: a first visit opens the shipped Kamiennik
example and shows the mockup's result, „60,21 m³/s” at „6:20” and „1 046 213 m³”, as
the server's ``hydrograph generate`` computed it. Switching the tc method, AMC and the
unit hydrograph model reproduces the mockup's runs (Nash by Lutz through ``uh nash``);
an invalid CN stands on its field and keeps the last result, marked; ten fast edits
send at most two runs and show the last; the command line, run by the CLI, gives the
same peak; errors of the server stand on their field or above the steps. A watershed
file is read in the browser and its changed fields are marked; the hydrograph exports
as the CSV the ``route`` commands read, the envelope and a PNG; the inputs survive a
reload until „Wyczyść”; Kalkulatory's route sets the tc method; Statystyka's
reference is drawn; a phone in the dark theme recomputes through the sheets. The pure
modules (the live channel, the state, the CSV) are tested in the page.
"""

import json
import math
import re
import shlex
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, Request, expect

from hydrolog.catalog import format_command, run_command
from tests.e2e.conftest import Tab

WEB = Path(__file__).resolve().parents[2] / "src" / "hydrolog" / "gui" / "web"
EXAMPLE = json.loads((WEB / "examples" / "kamiennik.json").read_text(encoding="utf-8"))
"""The shipped example: a WatershedParameters JSON."""
RUN = "/api/run/hydrograph/generate"
LUTZ = "/api/run/uh/nash"
BADGE = ".topbar .badge.status"
SECTION = 'section.section[data-section="hydrogram"]'
LEFT = f"{SECTION} .view-panel.left"
RIGHT = f"{SECTION} .view-panel.right"
CENTER = f"{SECTION} .view-center"
SPACES = re.compile(r"[\s\u00a0\u202f]+")
# The mockup's options of the Kamiennik run (its CLI line), the example's watershed.
KAMIENNIK = {
    "watershed": EXAMPLE,
    "tc_method": "kirpich",
    "amc": "II",
    "hietogram_type": "beta",
    "total_mm": 105,
    "duration_min": 720,
    "alpha": 2,
    "beta": 5,
    "timestep_min": 10,
    "uh_model": "scs",
}
LUTZ_OPTIONS = {
    "area_km2": 37.22,
    "lutz_length_km": 14.78,
    "lutz_centroid_length_km": 6.76,
    "lutz_slope_m_per_m": 0.0142,
    "lutz_manning_n": 0.035,
    "lutz_forest_pct": 57.4,
    "lutz_urban_pct": 1.0,
    "timestep_min": 10,
}
# What the page writes in the KPI tiles (Qmax, time to peak, volume) for the mockup's
# runs (its #hg-data, 6 tc methods x AMC I-III x 4 models), by (model, tc method, AMC).
# Snyder's peak is the library's since its unit hydrograph peaks at qpR (the mockup's
# 29,14 came before that fix).
MOCKUP = {
    ("scs", "kirpich", "II"): ("60,21", "6:20", "1 046 213"),
    ("scs", "nrcs", "II"): ("43,01", "8:40", "1 046 869"),
    ("scs", "giandotti", "II"): ("45,57", "8:20", "1 046 934"),
    ("scs", "kerby_kirpich", "II"): ("57,90", "6:40", "1 046 735"),
    ("scs", "kirpich", "III"): ("115,23", "5:40", "2 111 780"),
    ("scs", "kirpich", "I"): ("12,79", "7:30", "193 894"),
    ("clark", "kirpich", "II"): ("55,61", "6:50", "1 046 551"),
    ("nash", None, "II"): ("40,28", "8:50", "1 046 544"),
    ("snyder", None, "II"): ("27,46", "11:00", "1 046 551"),
}
# Scroll containers that must not scroll sideways: the page and an open sheet.
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""


def flat(text: str | None) -> str:
    """Return ``text`` with its runs of (non-breaking) spaces as one space."""
    return SPACES.sub(" ", text or "").strip()


def kpi(page: Page, name: str) -> Locator:
    """Return the value of the tile ``name`` (``q``, ``tp``, ``volume``, ``c``)."""
    return page.locator(f'{RIGHT} [data-kpi="{name}"] .v')


def shows(page: Page, q: str, tp: str, volume: str) -> None:
    """Wait until the tiles show the peak, the time to peak and the volume, current."""
    expect(kpi(page, "q")).to_have_text(re.compile(rf"^{re.escape(q)}\s*m³/s$"))
    expect(kpi(page, "tp")).to_have_text(re.compile(rf"^{re.escape(tp)}\s*h$"))
    pattern = r"\s".join(re.escape(part) for part in volume.split(" "))
    expect(kpi(page, "volume")).to_have_text(re.compile(rf"^{pattern}\s*m³$"))
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")


def open_hydrogram(tab: Tab, path: str = "#hydrogram") -> Page:
    """Open the section on a first visit and wait for the Kamiennik result."""
    tab.open(path)
    shows(tab.page, "60,21", "6:20", "1 046 213")
    return tab.page


class Runs:
    """The options of every ``hydrograph generate`` and ``uh nash`` a page sends."""

    def __init__(self, page: Page) -> None:
        self.generate: list[dict[str, Any]] = []
        self.lutz: list[dict[str, Any]] = []
        page.on("request", self._record)

    def _record(self, request: Request) -> None:
        body = request.post_data_json if request.method == "POST" else None
        if not isinstance(body, dict):
            return
        if RUN in request.url:
            self.generate.append(body)
        elif LUTZ in request.url:
            self.lutz.append(body)


def field(page: Page, name: str) -> Locator:
    """Return the text box of the field ``name`` in the panel Dane."""
    return page.locator(f"#hg-{name}")


def message(page: Page, name: str) -> Locator:
    """Return the message under the field ``name``."""
    return page.locator(f'{LEFT} [data-field="{name}"] .err')


def choose(page: Page, group: str, label: str) -> None:
    """Click the choice ``label`` of the segmented control labelled by ``group``."""
    page.locator(f'[aria-labelledby="{group}"]').get_by_role(
        "radio", name=label, exact=True
    ).click()


def expected(options: dict[str, Any]) -> dict[str, Any]:
    """Return the result of ``hydrograph generate`` for ``options``, in this process."""
    result: dict[str, Any] = run_command("hydrograph generate", options).to_dict()[
        "result"
    ]
    return result


def one_line(shown: str) -> str:
    """Join a command line the panel wraps at `` --`` with ``\\``."""
    return shown.replace(" \\\n  ", " ")


def comma(value: float, digits: int = 2) -> str:
    """Return ``value`` with ``digits`` decimals and a comma, as the page writes it."""
    return f"{value:.{digits}f}".replace(".", ",")


def download(page: Page, trigger: Locator) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


# --- the first visit -----------------------------------------------------------


def test_a_first_visit_shows_the_kamiennik_result_of_the_mockup(tab: Tab) -> None:
    runs = Runs(tab.page)
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    envelope = answered.value.json()
    assert runs.generate[-1] == KAMIENNIK
    result = expected(KAMIENNIK)
    assert envelope["result"]["peak_discharge_m3s"] == result["peak_discharge_m3s"]
    assert envelope["result"]["total_volume_m3"] == result["total_volume_m3"]

    expect(kpi(page, "c")).to_have_text("0,268")
    expect(page.locator(".crumb-context")).to_have_text(
        "Kamiennik — Świerzawa · p 1% · 12 h"
    )
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Wynik aktualny · liczy się sam po każdej zmianie"
    )
    steps = page.locator(f"{LEFT} .step > summary .meta")
    expect(steps).to_have_text(
        [
            "37,22 km² · przykład",
            "162,9 min · Kirpich",
            "105,0 mm · 12 h · p 1%",
            "CN 65 · AMC II",
            "SCS",
        ]
    )
    expect(page.locator(f'{LEFT} [data-chips="losses"] .chip')).to_have_text(
        ["CN 65", "S = 136,8 mm", "Ia = λ·S = 27,4 mm"]
    )
    expect(page.locator(f'{LEFT} [data-chips="uh"] .chip')).to_have_text(
        ["tc = 162,9 min", "tp = 102,8 min", "qp = 4,52 m³/s na 1 mm"]
    )

    # The hyetograph hangs above the hydrograph; the peak is the result's
    chart = page.locator(f"{CENTER} .card").first
    expect(chart.locator("[data-chart-sub]")).to_have_text(
        "SCS · Kirpich · AMC II · PMAXTP p 1%, 12 h, Beta (2; 5) · Δt 10 min"
    )
    expect(chart.locator(".bars.bar-p rect")).to_have_count(72)
    expect(chart.locator(".peak-label")).to_have_text("Qmax 60,21 m³/s · 6:20 h")
    effective = sum(1 for value in result["effective_precipitation_mm"] if value > 0)
    expect(chart.locator(".bars.bar-pe rect")).to_have_count(effective)
    parts = page.locator('[data-chart="cumulative"], [data-chart="uh"]')
    expect(parts.locator("svg")).to_have_count(2)
    expect(page.locator('[data-chart="uh"] .peak-tag')).to_have_text(
        "qp 4,52 · tp 1:43"
    )

    # The balance of the rainfall and the notes
    balance = page.locator(f'{RIGHT} [data-table="balance"] td:nth-child(2)')
    expect(balance).to_have_text(["105,00", "27,35", "49,53", "28,12", "136,77"])
    notes = page.locator(f"{RIGHT} .notes li")
    expect(notes.filter(has_text="Brak uwag Hydrologa")).to_have_count(1)

    # The table of the series: the peak row, P and Pe of the step ending at t
    page.locator(f"{CENTER} .view-bar").get_by_role("radio", name="Tabela").click()
    peak = page.locator(f"{CENTER} tr.peak")
    expect(peak.locator("th")).to_have_text("6:20")
    expect(peak.locator("td").last).to_have_text("60,21")
    rows = page.locator(f"{CENTER} .dtable tbody tr")
    expect(rows).to_have_count(len(result["times_min"]))
    expect(rows.nth(1).locator("td").nth(1)).to_have_text("0,30")

    # Kalkulatory reads the watershed from the store
    stored = page.evaluate(
        "async () => (await import('./src/store.js')).getStore('watershed')"
    )
    assert stored == {key: EXAMPLE[key] for key in stored}
    assert set(stored) == set(EXAMPLE)


# --- the mockup's runs ---------------------------------------------------------


def test_the_tc_method_amc_and_model_reproduce_the_mockups_runs(tab: Tab) -> None:
    page = open_hydrogram(tab)
    runs = Runs(page)
    method = field(page, "tc_method")

    def check(model: str, tc: str | None, amc: str) -> dict[str, Any]:
        shows(page, *MOCKUP[(model, tc, amc)])
        sent = runs.generate[-1]
        assert sent["uh_model"] == model
        assert sent["amc"] == amc
        assert sent.get("tc_method") == tc
        return sent

    method.select_option("nrcs")
    check("scs", "nrcs", "II")
    method.select_option("giandotti")
    check("scs", "giandotti", "II")
    notices = page.locator(f'{RIGHT} .notes li[data-code="outside_typical_range"]')
    expect(notices).to_have_text(re.compile(r"giandotti: area_km2 = 37,22 poza"))
    method.select_option("kerby_kirpich")
    check("scs", "kerby_kirpich", "II")
    expect(notices).to_have_count(2)
    method.select_option("kirpich")
    choose(page, "hg-amc-label", "III")
    check("scs", "kirpich", "III")
    expect(page.locator(f'{LEFT} [data-hint="amc"]')).to_have_text(
        "Mokro przed opadem; CN podwyższone (CN 65 → 81)"
    )
    choose(page, "hg-amc-label", "I")
    check("scs", "kirpich", "I")
    choose(page, "hg-amc-label", "II")
    choose(page, "hg-uh-label", "Clark")
    assert check("clark", "kirpich", "II")["clark_r_tc_ratio"] == 0.5

    # Nash by Lutz: `uh nash` first, its n and K go on
    choose(page, "hg-uh-label", "Nash")
    sent = check("nash", None, "II")
    assert runs.lutz[-1] == LUTZ_OPTIONS
    parameters = run_command("uh nash", LUTZ_OPTIONS).to_dict()["result"]["parameters"]
    assert (sent["nash_n"], sent["nash_k_min"]) == (
        parameters["n"],
        parameters["k_min"],
    )
    expect(field(page, "nash_n")).to_have_value("3,631")
    expect(field(page, "nash_k_min")).to_have_value("82,35")
    expect(page.locator(f"{RIGHT} .notes li").first).to_have_text(
        re.compile("Model Nash nie używa tc")
    )
    # n and K typed instead: the copy of Lutz's, rounded as shown
    with page.expect_request(lambda request: RUN in request.url) as asked:
        choose(page, "hg-nash-source-label", "Podane n i K")
    given = asked.value.post_data_json
    assert isinstance(given, dict)
    assert (given["nash_n"], given["nash_k_min"]) == (3.631, 82.35)
    shows(page, "40,28", "8:50", "1 046 544")

    choose(page, "hg-uh-label", "Snyder")
    sent = check("snyder", None, "II")
    assert (sent["snyder_length_km"], sent["snyder_centroid_length_km"]) == (
        14.78,
        6.76,
    )
    choose(page, "hg-uh-label", "SCS")
    check("scs", "kirpich", "II")


# --- live recompute ------------------------------------------------------------


def test_an_invalid_cn_stands_on_its_field_and_keeps_the_last_result(tab: Tab) -> None:
    page = open_hydrogram(tab)
    runs = Runs(page)
    cn = field(page, "cn")
    cn.fill("150")
    expect(message(page, "cn")).to_have_text("Najwyżej 100 (podano 150) · maximum")
    expect(cn).to_have_attribute("aria-invalid", "true")
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: cn")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Dane niepełne: CN dla AMC II"
    )
    stale = page.locator('[data-stale="invalid"]')
    expect(stale).to_have_count(2)  # the centre and the panel Wyniki
    expect(stale.first).to_have_text(
        "Wynik dla poprzednich danych: popraw pole „CN dla AMC II” w panelu Dane."
    )
    expect(kpi(page, "q")).to_have_text(re.compile(r"^60,21"))
    page.wait_for_timeout(600)
    assert runs.generate == []  # invalid data run nothing

    cn.fill("72")
    result = expected({**KAMIENNIK, "watershed": {**EXAMPLE, "cn": 72}})
    expect(kpi(page, "q")).to_have_text(
        re.compile(rf"^{comma(result['peak_discharge_m3s'])}")
    )
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    expect(stale).to_have_count(0)
    expect(message(page, "cn")).to_have_count(0)
    # The changed field is marked against the example, and restored
    mark = page.locator(f'{LEFT} [data-field="cn"] .chg')
    expect(mark).to_have_text(re.compile(r"zmieniono · przykład: 65"))
    mark.get_by_role("button", name="przywróć").click()
    expect(cn).to_have_value("65")
    shows(page, "60,21", "6:20", "1 046 213")


def test_ten_fast_edits_send_at_most_two_runs_and_show_the_last(tab: Tab) -> None:
    page = open_hydrogram(tab)
    runs = Runs(page)
    badges: list[str] = []
    page.expose_function("hydrologBadge", lambda text: badges.append(text))
    page.evaluate(
        """() => {
          const badge = document.querySelector('.topbar .badge.status');
          new MutationObserver(() => window.hydrologBadge(badge.textContent.trim()))
            .observe(badge, {subtree: true, childList: true, characterData: true});
        }"""
    )
    total = field(page, "total_mm")
    total.fill("")
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: total_mm")
    total.press_sequentially("100,123456", delay=20)  # ten edits
    result = expected({**KAMIENNIK, "total_mm": 100.123456})
    peak = comma(result["peak_discharge_m3s"])
    expect(kpi(page, "q")).to_have_text(re.compile(rf"^{peak}"))
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    page.wait_for_timeout(400)
    assert 1 <= len(runs.generate) <= 2, runs.generate
    assert runs.generate[-1]["total_mm"] == 100.123456
    assert "Liczenie…" in badges  # shown while the newest run was on its way


def test_the_cli_line_run_by_the_cli_gives_the_same_peak(tab: Tab) -> None:
    page = open_hydrogram(tab)
    for model in ("SCS", "Nash"):
        with page.expect_response(lambda answer: RUN in answer.url) as answered:
            choose(page, "hg-uh-label", model)
            if model == "SCS":  # already chosen: change the step to run again
                field(page, "timestep_min").fill("5")
        envelope = answered.value.json()
        options = answered.value.request.post_data_json
        line = format_command("hydrograph generate", options)
        # The line shown, unwrapped, is the options sent, formatted by the server
        page.wait_for_function(
            r"""(line) => {
              const shown = document.querySelector('.view-panel.right .cli pre');
              return shown && shown.textContent.replaceAll(' \\\n  ', ' ') === line;
            }""",
            arg=line,
        )
        words = shlex.split(line)
        done = subprocess.run(
            [sys.executable, "-m", "hydrolog.cli", *words[1:], "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert done.returncode == 0, done.stderr
        cli = json.loads(done.stdout)["result"]
        assert cli["peak_discharge_m3s"] == envelope["result"]["peak_discharge_m3s"]
        assert cli["time_to_peak_min"] == envelope["result"]["time_to_peak_min"]


# --- errors --------------------------------------------------------------------


def test_errors_of_the_server_stand_on_their_field_or_above_the_steps(tab: Tab) -> None:
    page = open_hydrogram(tab)
    # A tc method without the fields it needs: the server names them
    page.locator(f"{LEFT} details.more > summary").click()
    field(page, "runoff_coeff").fill("")
    shows(page, "60,21", "6:20", "1 046 213")
    field(page, "tc_method").select_option("faa")
    for name in ("runoff_coeff",):
        expect(message(page, name)).to_have_text(
            "Metoda faa potrzebuje tej wartości · missing_field"
        )
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    expect(page.locator('[data-stale="error"]').first).to_have_text(
        re.compile(r"^Wynik dla poprzednich danych: Hydrolog nie policzył")
    )
    field(page, "runoff_coeff").fill("0,25")
    shows(page, "71,57", "4:30", "1 038 431")

    # A library error without an option stands above the steps, in English marked (EN)
    field(page, "tc_method").select_option("kirpich")
    shows(page, "60,21", "6:20", "1 046 213")
    choose(page, "hg-rain-source-label", "Hietogram")
    field(page, "duration_min").fill("5")
    above = page.locator(f"{LEFT} [data-form-error]")
    expect(above).to_contain_text("Nieprawidłowe dane wejściowe")
    expect(above).to_contain_text("cannot exceed duration_min (5.0) (EN)")
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Błąd danych: wynik dla poprzednich danych"
    )
    expect(kpi(page, "q")).to_have_text(re.compile(r"^60,21"))
    field(page, "duration_min").fill("720")
    expect(above).to_have_count(0)
    shows(page, "60,21", "6:20", "1 046 213")


# --- the watershed -------------------------------------------------------------


def test_a_watershed_file_is_read_in_the_browser(tab: Tab, tmp_path: Path) -> None:
    page = open_hydrogram(tab)
    own = {**EXAMPLE, "name": "Potok testowy", "area_km2": 20.5, "cn": 70}
    del own["Lc_km"]
    path = tmp_path / "potok.json"
    path.write_text(json.dumps(own), encoding="utf-8")
    page.locator(f'{LEFT} input[type="file"]').set_input_files(str(path))
    expect(page.locator(".toast")).to_have_text("Wczytano zlewnię z potok.json")
    expect(field(page, "name")).to_have_value("Potok testowy")
    expect(field(page, "area_km2")).to_have_value("20,5")
    expect(field(page, "Lc_km")).to_have_value("")
    source = page.locator(f"{LEFT} .handoff")
    expect(source.locator("strong")).to_have_text("Z pliku: potok.json")
    expect(source.locator(".muted")).to_have_text(re.compile(r"· 18 pól$"))
    result = expected({**KAMIENNIK, "watershed": own})
    peak = f"{result['peak_discharge_m3s']:.2f}".replace(".", ",")
    expect(kpi(page, "q")).to_have_text(re.compile(rf"^{peak}"))
    expect(page.locator(".crumb-context")).to_have_text("Potok testowy · p 1% · 12 h")

    field(page, "perimeter_km").fill("30")
    mark = page.locator(f'{LEFT} [data-field="perimeter_km"] .chg')
    expect(mark).to_have_text(re.compile(r"zmieniono · potok\.json: 40,89"))
    mark.get_by_role("button", name="przywróć").click()
    expect(field(page, "perimeter_km")).to_have_value("40,89")
    expect(mark).to_have_count(0)

    # A file that is not a watershed changes nothing
    bad = tmp_path / "zle.json"
    bad.write_text('{"area_km2": 3}', encoding="utf-8")
    page.locator(f'{LEFT} input[type="file"]').set_input_files(str(bad))
    expect(page.locator(".toast")).to_have_text(
        re.compile(r"^Nie udało się wczytać zlewni z zle\.json: .*perimeter_km")
    )
    expect(field(page, "name")).to_have_value("Potok testowy")


# --- exports -------------------------------------------------------------------


def test_the_hydrograph_exports_csv_json_and_png(tab: Tab, tmp_path: Path) -> None:
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    envelope = answered.value.json()
    result = envelope["result"]
    buttons = page.locator(f"{RIGHT} .export-row button")

    name, data = download(page, buttons.filter(has_text="CSV"))
    assert name == "Kamiennik — Świerzawa.csv"
    header, *rows = [line.split(",") for line in data.decode("utf-8").splitlines()]
    assert header == [
        "time_min",
        "discharge_m3s",
        "precipitation_mm",
        "effective_precipitation_mm",
    ]
    assert [float(row[0]) for row in rows] == result["times_min"]
    assert [float(row[1]) for row in rows] == result["discharge_m3s"]
    rain = [float(row[2]) for row in rows]
    steps = len(result["precipitation_mm"])
    assert rain[1 : 1 + steps] == result["precipitation_mm"]  # the step ending at t
    assert rain[0] == 0 and not any(rain[1 + steps :])
    effective = [float(row[3]) for row in rows]
    assert effective[1 : 1 + steps] == result["effective_precipitation_mm"]
    # A `route` command reads it as the hydrograph it routes
    table = tmp_path / "hydrogram.csv"
    table.write_bytes(data)
    routed = run_command("route lag", {"input_file": str(table), "lag_min": 30})
    assert routed.to_dict()["result"]["inflow_peak_m3s"] == result["peak_discharge_m3s"]

    name, data = download(page, buttons.filter(has_text="JSON"))
    assert name == "Kamiennik — Świerzawa.result.json"
    assert json.loads(data) == envelope

    name, data = download(page, buttons.filter(has_text="PNG"))
    assert name == "Kamiennik — Świerzawa.png"
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    box = page.locator(f"{CENTER} .chart.wide svg").bounding_box()
    assert box is not None
    drawn = (math.floor(box["width"] + 0.5), math.floor(box["height"] + 0.5))
    assert struct.unpack(">II", data[16:24]) == (2 * drawn[0], 2 * drawn[1])


# --- persistence, routes and shared state --------------------------------------


def test_the_inputs_survive_a_reload_until_cleared(tab: Tab) -> None:
    page = open_hydrogram(tab)
    field(page, "cn").fill("70")
    choose(page, "hg-uh-label", "Clark")
    result = expected(
        {
            **KAMIENNIK,
            "watershed": {**EXAMPLE, "cn": 70},
            "uh_model": "clark",
            "clark_r_tc_ratio": 0.5,
        }
    )
    expect(kpi(page, "q")).to_have_text(
        re.compile(rf"^{comma(result['peak_discharge_m3s'])}")
    )
    stored = page.evaluate(
        "() => JSON.parse(localStorage.getItem('hydrolog-gui/hydrogram/1'))"
    )
    assert stored["watershed"]["cn"] == "70" and stored["uh_model"] == "clark"
    assert "envelope" not in json.dumps(stored)  # inputs only, no results

    page.reload()
    expect(field(page, "cn")).to_have_value("70")
    expect(kpi(page, "q")).to_have_text(
        re.compile(rf"^{comma(result['peak_discharge_m3s'])}")
    )
    page.locator(LEFT).get_by_role("button", name="Wyczyść").click()
    expect(field(page, "cn")).to_have_value("65")
    shows(page, "60,21", "6:20", "1 046 213")


def test_kalkulatory_sets_the_tc_method_through_the_route(tab: Tab) -> None:
    tab.open("#hydrogram/tc_method/nrcs")
    page = tab.page
    shows(page, *MOCKUP[("scs", "nrcs", "II")])
    expect(field(page, "tc_method")).to_have_value("nrcs")
    expect(page).to_have_url(re.compile(r"#hydrogram$"))
    stored = page.evaluate(
        "() => JSON.parse(localStorage.getItem('hydrolog-gui/hydrogram/1'))"
    )
    assert (stored["tc_method"], stored["tc_manual"], stored["uh_model"]) == (
        "nrcs",
        False,
        "scs",
    )


def test_a_reference_of_statystyka_is_drawn_on_the_hydrograph(tab: Tab) -> None:
    page = open_hydrogram(tab)
    page.evaluate(
        """async () => (await import('./src/store.js')).setStore('reference',
          {label: 'Q1%', peak_m3s: 80.5, source: 'GEV'})"""
    )
    chart = page.locator(f"{CENTER} .chart.wide")
    expect(chart.locator(".mark.hline .peak-tag")).to_have_text("Q1%: 80,5 m³/s")
    expect(chart.locator(".chart-legend")).to_contain_text("Q1%: 80,5 m³/s (GEV)")
    page.locator(CENTER).get_by_role("button", name="Usuń odniesienie").click()
    expect(chart.locator(".mark.hline")).to_have_count(0)
    assert (
        page.evaluate(
            "async () => (await import('./src/store.js')).getStore('reference')"
        )
        is None
    )


# --- explanations (i) ----------------------------------------------------------


def test_the_explanations_check_their_ranges_against_the_watershed(tab: Tab) -> None:
    page = open_hydrogram(tab)
    entry = page.evaluate(
        "async () => (await import('./src/labels/info/tc.js')).tcInfo['tc-kirpich']"
    )
    page.locator(f"{LEFT} [data-step=tc] .info-btn").click()
    popover = page.locator(".info-pop")
    expect(popover).to_be_visible()
    expect(popover.locator("#info-pop-title")).to_have_text(entry["title"])
    states: dict[str, list[str]] = {"warn": [], "ok": []}
    for item in entry["ranges"]:
        value = EXAMPLE.get(item["option"])
        if value is None:
            continue
        low, high = item.get("min", -math.inf), item.get("max", math.inf)
        states["warn" if value < low or value > high else "ok"].append(item["option"])
    assert (
        states["warn"] and states["ok"]
    )  # Kamiennik leaves Kirpich's data, not its bounds
    for state, options in states.items():
        for option in set(options):
            marked = popover.locator(f'.range-list li[data-range="{option}"]')
            expect(marked.first).to_be_attached()
            assert state in marked.evaluate_all(
                "items => items.map((item) => item.className)"
            )
    page.keyboard.press("Escape")
    expect(popover).to_be_hidden()

    # The note of the method's range opens the same explanation
    note = page.locator(f'{RIGHT} [data-notes="gui"] li.warn').first
    expect(note).to_contain_text("Kirpich:")
    note.get_by_role("button", name="objaśnienie").click()
    expect(popover.locator("#info-pop-title")).to_have_text(entry["title"])


# --- the phone -----------------------------------------------------------------


def test_a_phone_in_the_dark_theme_recomputes_through_the_sheets(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    tab.open("#hydrogram")
    page = tab.page
    page.locator(f"{CENTER} .view-bar").get_by_role("button", name="Dane").click()
    sheet = page.locator(f"{LEFT}.open")
    expect(sheet).to_be_visible()
    choose(page, "hg-amc-label", "III")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    assert page.evaluate(SIDEWAYS) == []
    page.locator(f"{CENTER} .view-bar").get_by_role("button", name="Wyniki").click()
    expect(page.locator(f"{RIGHT}.open")).to_be_visible()
    shows(page, *MOCKUP[("scs", "kirpich", "III")])
    assert page.evaluate(SIDEWAYS) == []
    assert page.evaluate("() => document.documentElement.scrollHeight") <= 844


# --- pure modules --------------------------------------------------------------


def test_the_live_channel_debounces_and_applies_only_the_newest(tab: Tab) -> None:
    tab.open("#polecenia")
    got = tab.page.evaluate(
        """async () => {
          const {createChannel} = await import('./src/sections/hydrogram/recompute.js');
          const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
          const log = {busy: [], outcomes: [], started: []};
          const channel = createChannel({
            delay: 200, busyAfter: 100,
            onBusy: (busy) => log.busy.push(busy),
            onOutcome: (outcome) => log.outcomes.push(outcome),
          });
          const task = (name, ms, fail) => async (signal) => {
            log.started.push(name);
            await sleep(ms);
            if (signal.aborted) throw new DOMException('aborted', 'AbortError');
            if (fail) throw new Error(name);
            return name;
          };
          for (let index = 0; index < 10; index += 1) {
            channel.request(task(`edit ${index}`, 5));
            await sleep(10);
          }
          await sleep(400);
          const quick = {...log, busy: [...log.busy], outcomes: [...log.outcomes]};
          // A slow run is aborted by a newer one; only the newest reports
          log.started = []; log.outcomes = []; log.busy = [];
          channel.request(task('slow', 600));
          await sleep(400);
          channel.request(task('newest', 5));
          await sleep(700);
          const slow = {...log};
          // Cancelling (invalid data) drops what runs; an error is an outcome
          log.started = []; log.outcomes = []; log.busy = [];
          channel.request(task('dropped', 300));
          await sleep(250);
          channel.cancel();
          await sleep(350);
          channel.request(task('broken', 5, true));
          await sleep(400);
          channel.dispose();
          const outcomes = log.outcomes.map((o) => [o.ok, String(o.error || o.value)]);
          return {quick, slow, last: {...log, outcomes}};
        }"""
    )
    assert got["quick"]["started"] == ["edit 9"]
    assert got["quick"]["outcomes"] == [{"ok": True, "value": "edit 9"}]
    assert got["quick"]["busy"] == [True, False]
    assert got["slow"]["started"] == ["slow", "newest"]
    assert got["slow"]["outcomes"] == [{"ok": True, "value": "newest"}]
    assert got["slow"]["busy"] == [True, False]
    assert got["last"]["started"] == ["dropped", "broken"]
    assert got["last"]["outcomes"] == [[False, "Error: broken"]]
    assert got["last"]["busy"] == [True, False, True, False]


def test_the_state_gives_the_options_of_the_mockups_calls(tab: Tab) -> None:
    tab.open("#polecenia")
    got = tab.page.evaluate(
        """async (example) => {
          const s = await import('./src/sections/hydrogram/state.js');
          const doc = await (await fetch('api/commands/hydrograph/generate')).json();
          const schema = await (
            await fetch('api/schemas/hydrolog-network-1.schema.json')
          ).json();
          const models = s.inputModels(doc, schema);
          const read = s.readWatershed(example);
          const base = {...s.initialState(), watershed: read.texts};
          const variant = (patch) => ({...base, ...patch});
          const check = (patch) => s.checkInputs(variant(patch), models);
          return {
            kamiennik: s.toOptions(base),
            nash: s.toOptions(variant({uh_model: 'nash'}), {n: 3.5, k_min: 80}),
            lutz: s.lutzOptions(variant({uh_model: 'nash'})),
            given: s.toOptions(variant({
              uh_model: 'nash', nash_source: 'given', nash_n: '3,6', nash_k_min: '82',
            })),
            snyder: s.toOptions(variant({uh_model: 'snyder', snyder_ct: '1,4'})),
            clark: s.toOptions(variant({
              uh_model: 'clark', clark_kind: 'r', clark_r_min: '90',
            })),
            manual: s.toOptions(variant({tc_manual: true, tc_min: '120'})),
            series: s.toOptions(variant({
              rain_source: 'series', values: '20; 40,5; 1',
            })),
            triangle: s.toOptions(variant({
              rain_source: 'design', hietogram_type: 'triangular', duration_min: '360',
            })),
            ok: check({}),
            cn: check({watershed: {...read.texts, cn: '150'}}),
            area: check({watershed: {...read.texts, area_km2: ''}}),
            manualEmpty: check({tc_manual: true}),
            lutzMissing: check({
              uh_model: 'nash', watershed: {...read.texts, Lc_km: ''},
            }),
            seriesBad: check({rain_source: 'series', values: '1; x'}),
            missing: s.readWatershed({name: 'x', area_km2: 1}).missing,
            wrapped: s.readWatershed({watershed: example}).values.area_km2,
          };
        }""",
        EXAMPLE,
    )
    assert got["kamiennik"] == KAMIENNIK
    assert got["nash"] == {
        **{key: KAMIENNIK[key] for key in KAMIENNIK if key != "tc_method"},
        "uh_model": "nash",
        "nash_n": 3.5,
        "nash_k_min": 80,
    }
    assert got["lutz"] == LUTZ_OPTIONS
    assert (got["given"]["nash_n"], got["given"]["nash_k_min"]) == (3.6, 82)
    assert "tc_method" not in got["snyder"]
    assert {
        key: got["snyder"][key] for key in got["snyder"] if key.startswith("snyder")
    } == {
        "snyder_length_km": 14.78,
        "snyder_centroid_length_km": 6.76,
        "snyder_ct": 1.4,
    }
    assert got["clark"]["clark_r_min"] == 90 and "clark_r_tc_ratio" not in got["clark"]
    assert got["manual"]["tc_min"] == 120 and "tc_method" not in got["manual"]
    assert got["series"]["values"] == [20, 40.5, 1]
    assert not {"hietogram_type", "total_mm", "duration_min", "alpha"} & set(
        got["series"]
    )
    assert got["triangle"]["hietogram_type"] == "triangular"
    assert got["triangle"]["duration_min"] == 360
    assert not {"alpha", "beta", "peak_position"} & set(got["triangle"])
    # Every call the state gives runs
    for name in (
        "kamiennik",
        "nash",
        "given",
        "snyder",
        "clark",
        "manual",
        "series",
        "triangle",
    ):
        assert expected(got[name])["peak_discharge_m3s"] > 0, name
    assert got["ok"] == {}
    assert got["cn"] == {"cn": "Najwyżej 100 (podano 150) · maximum"}
    assert got["area"] == {"area_km2": "Podaj wartość: opcja wymagana · required"}
    assert got["manualEmpty"] == {
        "tc_min": "Podaj wartość: potrzebna dla tc podanego ręcznie · required"
    }
    assert got["lutzMissing"] == {
        "Lc_km": "Podaj wartość: potrzebna dla metody Lutza (uh nash) · required"
    }
    assert list(got["seriesBad"]) == ["values"]
    assert got["missing"] == [
        "perimeter_km",
        "length_km",
        "elevation_min_m",
        "elevation_max_m",
    ]
    assert got["wrapped"] == 37.22
