"""„Hydrogram zlewni” (plan D13, D14, D16, slice S3; the author's three steps), browser.

Against the real server of ``gui_server``: a first visit shows the three steps empty and
runs nothing until a model is chosen; the guide's worked example (Kamiennik at
Świerzawa, ``tests/fixtures/kamiennik.json``, stored with ``seed_hydrogram`` with its
PMAXTP depth remembered at the mockup's 105 mm) shows its result, „57,88 m³/s” at „6:40”
and „1 046 713 m³”, as the server's ``hydrograph generate`` computed it.
PMAXTP fetches the depth of the point, p and the duration once (``precip pmaxtp``,
answered from the table recorded at the outlet: 101,82 mm and „54,20 m³/s”), shows it
read-only, kept with the inputs; a point outside the atlas stands on its field and
an unreachable IMGW-PIB on the depth, with „Pobierz ponownie”. Switching the tc method,
AMC and the unit hydrograph model reproduces the mockup's runs (Nash by Lutz in one run
of ``hydrograph generate`` with ``nash_estimation``, which shows the peak that ``uh
nash`` followed by ``hydrograph generate`` gave); only the chosen model's fields exist
and are sent; choosing a model marks the fields it lacks, a field no model reads may
stay empty, and a value outside its typical range is a warning on its field (from
Hydrolog's notice) while the run goes on.
A Nash unit hydrograph of years (n = 200, K = 1500 min) draws thinned and „Wyczyść”
drops it; a result that fails to draw is an error in its place, never the last result.
An invalid CN stands on its field and keeps the last result, marked; ten fast edits send
at most two runs and show the last; the command line, run by the CLI, gives the same
peak; errors stand on their field before the run or from the server, or above the
steps. A watershed file is read in the browser and its changed fields are marked; the
hydrograph exports as the CSV the ``route`` commands read, the envelope and a PNG; the
inputs survive a reload until „Wyczyść”, which empties the steps; Kalkulatory's route
sets the tc method; Statystyka's reference is drawn; a phone in the dark theme
recomputes through the sheets. The pure modules (the live channel, the state and what a
model needs, the CSV) are tested in the page. The explanations (i) show exactly the
typical ranges Hydrolog serves (``commands schema --command``), and the fields, the
explanations and Wyniki give the example the same verdicts.
"""

import json
import math
import re
import shlex
import struct
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, Request, Route, expect

from hydrolog import _pmaxtp
from hydrolog.catalog import format_command, run_command
from tests.conftest import recorded_pmaxtp
from tests.e2e.conftest import KAMIENNIK as EXAMPLE
from tests.e2e.conftest import (
    KAMIENNIK_POINT,
    PMAXTP_RUN,
    PMAXTP_TABLE,
    Tab,
    input_text,
    kamiennik_inputs,
    open_part,
    pmaxtp_route,
    seed_hydrogram,
)

RUN = "/api/run/hydrograph/generate"
LUTZ = "/api/run/uh/nash"
PMAXTP = "/api/run/precip/pmaxtp"
FETCHED = {
    **KAMIENNIK_POINT,
    "duration_min": 720,
    "probability_percent": 1,
    "method": "POT",
}
"""The options of the fetch of the example's PMAXTP depth (``precip pmaxtp``)."""
BADGE = ".topbar .badge.status"
SECTION = 'section.section[data-section="hydrogram"]'
LEFT = f"{SECTION} .view-panel.left"
RIGHT = f"{SECTION} .view-panel.right"
CENTER = f"{SECTION} .view-center"
SPACES = re.compile(r"[\s\u00a0\u202f]+")
STEP_ONE = [
    "name",
    "area_km2",
    "perimeter_km",
    "length_km",
    "elevation_min_m",
    "elevation_max_m",
    "elevation_mean_m",
    "mean_slope_m_per_m",
    "channel_length_km",
    "flow_path_length_km",
    "flow_path_slope_m_per_m",
    "cn",
]
"""The fields of the watershed in step 1, which a run sends when they hold a value."""
LUTZ_BLOCK = ["Lc_km", "manning_n", "forest_pct", "urban_pct"]
"""The watershed fields of Nash by Lutz's block in step 3."""
SENT = {name: EXAMPLE[name] for name in STEP_ONE}
"""The watershed of the example as SCS with Kirpich sends it: step 1's fields only."""
# The mockup's options of the Kamiennik run (its CLI line).
KAMIENNIK = {
    "watershed": SENT,
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
    "lutz_length_km": 15.88,
    "lutz_centroid_length_km": 6.76,
    "lutz_slope_m_per_m": 0.0114,
    "lutz_manning_n": 0.035,
    "lutz_forest_pct": 57.4,
    "lutz_urban_pct": 1.0,
    "timestep_min": 10,
}
"""The example's Nash by Lutz as ``uh nash`` takes it (L and J of the longest flow path,
which ``nash_estimation`` reads): the first of the two runs the page made before."""
# What the page writes in the KPI tiles (Qmax, time to peak, volume) for the mockup's
# runs (its #hg-data, 6 tc methods x AMC I-III x 4 models), by (model, tc method, AMC),
# as Hydrolog computes them: tc from the inputs each method's source defines (Kirpich
# and NRCS from the longest flow path), Snyder's peak since its unit hydrograph peaks at
# qpR, Nash by Lutz from L and J of the longest flow path (the mockup's tc and Snyder's
# 29,14 came before those changes).
MOCKUP = {
    ("scs", "kirpich", "II"): ("57,88", "6:40", "1 046 713"),
    ("scs", "nrcs", "II"): ("41,64", "9:00", "1 046 957"),
    ("scs", "giandotti", "II"): ("45,57", "8:20", "1 046 934"),
    ("scs", "kerby_kirpich", "II"): ("55,92", "6:50", "1 046 762"),
    ("scs", "kirpich", "III"): ("111,08", "6:00", "2 112 788"),
    ("scs", "kirpich", "I"): ("12,19", "7:50", "193 986"),
    ("clark", "kirpich", "II"): ("52,74", "7:10", "1 046 551"),
    ("nash", None, "II"): ("37,48", "9:10", "1 046 543"),
    ("snyder", None, "II"): ("27,46", "11:00", "1 046 551"),
}
# Scroll containers that must not scroll sideways: the page and an open sheet.
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""
STORED = "() => JSON.parse(localStorage.getItem('hydrolog-gui/hydrogram/2'))"
"""The inputs the page keeps."""
IDS = "items => items.map((item) => item.id)"
EXPLAINED = """async () => {
  const info = await import('./src/ui/info.js');
  const tables = await Promise.all([
    import('./src/labels/info/tc.js').then((module) => module.tcInfo),
    import('./src/labels/info/uh.js').then((module) => module.uhInfo),
    import('./src/labels/info/losses.js').then((module) => module.lossesInfo),
    import('./src/labels/info/rain.js').then((module) => module.rainInfo),
    import('./src/labels/info/stats.js').then((module) => module.statsInfo),
    import('./src/labels/info/routing.js').then((module) => module.routing),
  ]);
  const shown = {};
  for (const id of tables.flatMap(Object.keys)) {
    const ranges = info.infoRanges(id);
    const body = document.createElement('div');
    body.innerHTML = info.infoBody(info.infoText(id), {}, ranges);
    const rows = [...body.querySelectorAll('li[data-range]')]
      .map((row) => ({key: row.dataset.range, text: row.textContent}));
    shown[id] = {ranges, rows};
  }
  return shown;
}"""
"""Every explanation's registered ranges and the rows its body lists, by id."""


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


def shows_peak(page: Page, options: dict[str, Any]) -> dict[str, Any]:
    """Wait until the tiles show the peak of ``options`` computed here; return it."""
    result = expected(options)
    expect(kpi(page, "q")).to_have_text(
        re.compile(rf"^{comma(result['peak_discharge_m3s'])}\s*m³/s$")
    )
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    return result


def run_of(page: Page, **sent: Any) -> Any:
    """Expect the answer to the run whose options hold ``sent``."""
    return page.expect_response(
        lambda answer: (
            RUN in answer.url
            and all(
                (answer.request.post_data_json or {}).get(key) == value
                for key, value in sent.items()
            )
        )
    )


def open_hydrogram(tab: Tab, path: str = "#hydrogram") -> Page:
    """Open the section with the worked example stored; wait for its result."""
    seed_hydrogram(tab)
    tab.open(path)
    shows(tab.page, *MOCKUP[("scs", "kirpich", "II")])
    return tab.page


class Runs:
    """The options of every ``hydrograph generate``, ``uh nash`` and ``precip pmaxtp``
    a page sends."""

    def __init__(self, page: Page) -> None:
        self.generate: list[dict[str, Any]] = []
        self.lutz: list[dict[str, Any]] = []
        self.pmaxtp: list[dict[str, Any]] = []
        page.on("request", self._record)

    def _record(self, request: Request) -> None:
        body = request.post_data_json if request.method == "POST" else None
        if not isinstance(body, dict):
            return
        if RUN in request.url:
            self.generate.append(body)
        elif LUTZ in request.url:
            self.lutz.append(body)
        elif PMAXTP in request.url:
            self.pmaxtp.append(body)


def field(page: Page, name: str) -> Locator:
    """Return the control of the field ``name`` in the panel Dane."""
    return page.locator(f"#hg-{name}")


def message(page: Page, name: str) -> Locator:
    """Return the error under the field ``name``."""
    return page.locator(f'{LEFT} [data-field="{name}"] .err')


def warning(page: Page, name: str) -> Locator:
    """Return the warning under the field ``name``."""
    return page.locator(f'{LEFT} [data-field="{name}"] .warn')


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


def served(command: str) -> list[dict[str, Any]]:
    """Return the typical ranges Hydrolog serves for ``command`` (its catalog entry)."""
    entry = run_command("commands schema", {"command": command}).to_dict()["result"][
        "commands"
    ][0]
    found: list[dict[str, Any]] = entry["typical_ranges"]
    return found


def checked_field(found: dict[str, Any], values: dict[str, Any]) -> str | None:
    """Return the field a served range checks: the first of its inputs in ``values``."""
    return next((name for name in found["inputs"] if name in values), None)


def leaves(found: dict[str, Any], value: float) -> bool:
    """Return whether ``value`` lies outside the served range ``found`` (bounds in)."""
    low, high = found["minimum"], found["maximum"]
    return (low is not None and value < low) or (high is not None and value > high)


def one_line(shown: str) -> str:
    """Join a command line the panel wraps at `` --`` with ``\\``."""
    return shown.replace(" \\\n  ", " ")


def comma(value: float, digits: int = 2) -> str:
    """Return ``value`` with ``digits`` decimals and a comma, as the page writes it."""
    return f"{value:.{digits}f}".replace(".", ",")


def short(value: float) -> str:
    """Return ``value`` to four significant digits, as the page shows n and K."""
    return input_text(float(f"{value:.4g}"))


def download(page: Page, trigger: Locator) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


def typed(*names: str) -> dict[str, str]:
    """Return the example's fields ``names`` as the page holds them typed."""
    return {name: input_text(EXAMPLE[name]) for name in names}


# --- the first visit -----------------------------------------------------------


def test_a_first_visit_shows_three_empty_steps_and_runs_nothing(tab: Tab) -> None:
    # The inputs of the five steps (the version 1 key) are no longer read
    tab.page.add_init_script(
        "try { localStorage.setItem('hydrolog-gui/hydrogram/1',"
        " JSON.stringify({uh_model: 'scs', total_mm: '105', watershed: {cn: '65'}}));"
        " } catch (error) {}"
    )
    runs = Runs(tab.page)
    tab.open("#hydrogram")
    page = tab.page
    steps = page.locator(f"{LEFT} .step > summary")
    expect(steps.locator(".title")).to_have_text(["Zlewnia", "Hietogram", "Hydrogram"])
    expect(steps.locator(".meta")).to_have_text(
        ["brak danych", "brak danych", "wybierz model"]
    )
    boxes = page.locator(f'{LEFT} input[type="text"]')
    # the point, the fetched depth (read-only), alpha, beta, Δt and λ
    expect(boxes).to_have_count(len(STEP_ONE) + 7)
    assert set(boxes.evaluate_all("items => items.map((item) => item.value)")) == {""}
    expect(field(page, "pmaxtp_depth")).not_to_be_editable()
    expect(field(page, "pmaxtp_probability_pct")).to_have_value("")
    expect(field(page, "pmaxtp_duration_min")).to_have_value("")
    expect(field(page, "pmaxtp_method")).to_have_value("POT")
    expect(field(page, "timestep_min")).to_have_attribute("placeholder", "5")
    models = page.locator('[aria-labelledby="hg-uh-label"] [role="radio"]')
    expect(models).to_have_text(["SCS", "Nash", "Clark", "Snyder"])
    expect(models.and_(page.locator('[aria-checked="true"]'))).to_have_count(0)
    for name in ["tc_method", "snyder_ct", "nash_n", "clark_r_tc_ratio", "Lc_km"]:
        expect(field(page, name)).to_have_count(0)
    expect(page.locator(f'{LEFT} [aria-invalid="true"]')).to_have_count(0)
    expect(page.locator(f"{LEFT} .frow .err, {LEFT} .frow .warn")).to_have_count(0)
    expect(page.locator(f"{LEFT} .frow .need")).to_have_count(0)
    expect(page.locator(f'{LEFT} [data-summary="none"]')).to_have_text(
        re.compile(r"^Wybierz model: dopiero wtedy")
    )
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text("Wybierz model w kroku 3")
    expect(page.locator(BADGE)).to_be_hidden()
    expect(page.locator(".crumb-context")).to_have_count(0)
    expect(page.locator(RIGHT)).to_contain_text("Wynik pojawi się po pierwszym")
    hint = page.locator(f'{LEFT} [data-empty="hydrogram"]')
    expect(hint.get_by_role("link")).to_have_attribute("href", "instrukcja/#przyklad")

    # A value that is not a number is an error at once, model or not; nothing runs
    field(page, "area_km2").fill("abc")
    expect(message(page, "area_km2")).to_have_text(re.compile(r" · type$"))
    expect(field(page, "area_km2")).to_have_attribute("aria-invalid", "true")
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: area_km2")
    field(page, "area_km2").fill("")
    expect(page.locator(f'{LEFT} [aria-invalid="true"]')).to_have_count(0)
    page.wait_for_timeout(800)
    assert runs.generate == [] and runs.lutz == [] and runs.pmaxtp == []
    assert page.evaluate(STORED)["uh_model"] is None
    assert (
        page.evaluate(
            "async () => (await import('./src/store.js')).getStore('watershed')"
        )
        is None
    )


def test_the_worked_example_shows_the_result_of_the_mockup(tab: Tab) -> None:
    runs = Runs(tab.page)
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    envelope = answered.value.json()
    assert runs.generate[-1] == KAMIENNIK
    result = expected(KAMIENNIK)
    assert envelope["result"]["peak_discharge_m3s"] == result["peak_discharge_m3s"]
    assert envelope["result"]["total_volume_m3"] == result["total_volume_m3"]

    expect(kpi(page, "c")).to_have_text("0,268")
    # The PMAXTP depth remembered with the inputs: shown read-only, not fetched again
    expect(field(page, "pmaxtp_depth")).to_have_value("105")
    expect(page.locator(f'{LEFT} [data-field="pmaxtp_depth"] .aux')).to_have_text(
        "PMAXTP IMGW-PIB, metoda POT"
    )
    assert runs.pmaxtp == []
    expect(page.locator(".crumb-context")).to_have_text(
        "Kamiennik — Świerzawa · p 1% · 12 h"
    )
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Wynik aktualny · liczy się sam po każdej zmianie"
    )
    expect(page.locator(f"{LEFT} .step > summary .meta")).to_have_text(
        [
            "37,22 km² · kamiennik.json",
            "105,0 mm · 12 h · p 1%",
            "SCS · 187,4 min · Kirpich",
        ]
    )
    # Step 1 says which of its fields the model reads: Kirpich the longest flow path's
    # length and slope; step 3 has what it needs
    needs = page.locator(f"{LEFT} .frow .need")
    expect(needs).to_have_text(
        [
            "wymagane dla modelu SCS",
            "wymagane dla strat SCS-CN",
            "wymagane dla metody Kirpicha",
            "wymagane dla metody Kirpicha",
        ]
    )
    assert needs.evaluate_all(
        "items => items.map((item) => item.closest('.frow').dataset.field)"
    ) == ["area_km2", "cn", "flow_path_length_km", "flow_path_slope_m_per_m"]
    # The longest flow path's rows of step 1: its length in km, its slope in m/m with
    # the slope in % beside it
    flow_path = page.locator(
        f'{LEFT} [data-step="watershed"] [data-field^="flow_path_"]'
    )
    expect(flow_path.locator("label")).to_contain_text(
        ["Długość najdłuższej drogi spływu", "Spadek najdłuższej drogi spływu"]
    )
    expect(flow_path.locator(".unit")).to_have_text(["km", "m/m"])
    expect(flow_path.locator(".aux")).to_have_text("= 1,14 %")
    expect(page.locator(f'{LEFT} [data-summary="ok"]')).to_have_text(
        "Model ma wszystkie potrzebne dane."
    )
    expect(page.locator(f'{LEFT} [data-chips="losses"] .chip')).to_have_text(
        ["CN 65", "S = 136,8 mm", "Ia = λ·S = 27,4 mm"]
    )
    expect(page.locator(f'{LEFT} [data-chips="uh"] .chip')).to_have_text(
        ["tc = 187,4 min", "tp = 117,4 min", "qp = 3,96 m³/s na 1 mm"]
    )

    # The hyetograph hangs above the hydrograph; the peak is the result's
    chart = page.locator(f"{CENTER} .card").first
    expect(chart.locator("[data-chart-sub]")).to_have_text(
        "SCS · Kirpich · AMC II · PMAXTP p 1%, 12 h, Beta (2; 5) · Δt 10 min"
    )
    expect(chart.locator(".bars.bar-p rect")).to_have_count(72)
    expect(chart.locator(".peak-label")).to_have_text("Qmax 57,88 m³/s · 6:40 h")
    effective = sum(1 for value in result["effective_precipitation_mm"] if value > 0)
    expect(chart.locator(".bars.bar-pe rect")).to_have_count(effective)
    parts = page.locator('[data-chart="cumulative"], [data-chart="uh"]')
    expect(parts.locator("svg")).to_have_count(2)
    expect(page.locator('[data-chart="uh"] .peak-tag')).to_have_text(
        "qp 3,96 · tp 1:57"
    )

    # The balance of the rainfall and the notes: Hydrolog's notices, the example lying
    # outside Kirpich's data (the verdicts are compared below)
    balance = page.locator(f'{RIGHT} [data-table="balance"] td:nth-child(2)')
    expect(balance).to_have_text(["105,00", "27,35", "49,53", "28,12", "136,77"])
    assert [notice["code"] for notice in envelope["notices"]] == [
        "outside_typical_range"
    ] * 2
    expect(page.locator(f"{RIGHT} .notes li[data-code]")).to_have_count(2)

    # The table of the series: the peak row, P and Pe of the step ending at t
    page.locator(f"{CENTER} .view-bar").get_by_role("radio", name="Tabela").click()
    peak = page.locator(f"{CENTER} tr.peak")
    expect(peak.locator("th")).to_have_text("6:40")
    expect(peak.locator("td").last).to_have_text("57,88")
    rows = page.locator(f"{CENTER} .dtable tbody tr")
    expect(rows).to_have_count(len(result["times_min"]))
    expect(rows.nth(1).locator("td").nth(1)).to_have_text("0,30")

    # Kalkulatory reads the whole watershed from the store
    stored = page.evaluate(
        "async () => (await import('./src/store.js')).getStore('watershed')"
    )
    assert stored == EXAMPLE


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
    expect(warning(page, "area_km2")).to_have_text(
        "Poza typowym zakresem od 170 do 70\u00a0000 (giandotti)"
        " · outside_typical_range"
    )
    method.select_option("kerby_kirpich")
    sent = check("scs", "kerby_kirpich", "II")
    assert sent["watershed"] == {
        **SENT,
        **{
            name: EXAMPLE[name]
            for name in ["overland_length_km", "overland_slope_m_per_m", "retardance"]
        },
    }
    # Kamiennik lies inside every range of Kerby–Kirpich: no notice, no warning
    expect(notices).to_have_count(0)
    expect(page.locator(f"{LEFT} [data-field] .warn")).to_have_count(0)
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

    # Nash by Lutz: one run of `hydrograph generate` estimates n and K from the
    # watershed (`nash_estimation`), with no `uh nash` before it
    choose(page, "hg-uh-label", "Nash")
    sent = check("nash", None, "II")
    assert runs.lutz == []
    assert sent["nash_estimation"] == "lutz"
    assert not {"nash_n", "nash_k_min"} & set(sent)
    assert sent["watershed"] == {**SENT, **{name: EXAMPLE[name] for name in LUTZ_BLOCK}}
    # The peak shown is the library's, and the one the two runs of before gave: `uh
    # nash` by Lutz, then `hydrograph generate` with its n and K
    result = shows_peak(page, sent)
    parameters = run_command("uh nash", LUTZ_OPTIONS).to_dict()["result"]["parameters"]
    before = expected(
        {
            **{key: value for key, value in sent.items() if key != "nash_estimation"},
            "nash_n": parameters["n"],
            "nash_k_min": parameters["k_min"],
        }
    )
    assert comma(before["peak_discharge_m3s"]) == comma(result["peak_discharge_m3s"])
    assert before["time_to_peak_min"] == result["time_to_peak_min"]
    # n and K, read-only, are the shown result's
    for name, key in [("nash_n", "n"), ("nash_k_min", "k_min")]:
        expect(field(page, name)).to_have_value(short(result["uh_parameters"][key]))
        expect(field(page, name)).not_to_be_editable()
    expect(page.locator(f"{RIGHT} .notes li").first).to_have_text(
        re.compile("Model Nash nie używa tc")
    )
    # Estimated n and K are not checked against the ranges of given ones, by Hydrolog
    # or the page: Nash's confirmation names Lutz's area only
    expect(
        page.locator(f'{RIGHT} [data-notes="gui"] li').filter(has_text="Nash:")
    ).to_contain_text("Nash: A (Lutz) = 37,22\u00a0km² w zakresie stosowania.")
    # n and K typed instead: the copy of Lutz's, rounded as shown
    with page.expect_request(lambda request: RUN in request.url) as asked:
        choose(page, "hg-nash-source-label", "Podane n i K")
    given = asked.value.post_data_json
    assert isinstance(given, dict)
    assert (given["nash_n"], given["nash_k_min"]) == (3.61, 92.13)
    assert "nash_estimation" not in given and given["watershed"] == SENT
    shows_peak(page, given)

    choose(page, "hg-uh-label", "Snyder")
    sent = check("snyder", None, "II")
    assert (sent["snyder_length_km"], sent["snyder_centroid_length_km"]) == (
        14.78,
        6.76,
    )
    choose(page, "hg-uh-label", "SCS")
    check("scs", "kirpich", "II")


# --- what the chosen model needs -------------------------------------------------


def test_only_the_chosen_models_fields_exist_and_are_sent(tab: Tab) -> None:
    page = open_hydrogram(tab)
    others = [
        "snyder_ct",
        "snyder_cp",
        "nash_n",
        "nash_k_min",
        "clark_r_min",
        "clark_r_tc_ratio",
        *LUTZ_BLOCK,
        "overland_length_km",
        "overland_slope_m_per_m",
        "runoff_coeff",
        "retardance",
    ]
    for name in others:
        expect(field(page, name)).to_have_count(0)

    # Snyder's block: Lc of the watershed and its coefficients, no tc
    choose(page, "hg-uh-label", "Snyder")
    expect(field(page, "tc_method")).to_have_count(0)
    expect(field(page, "Lc_km")).to_have_value("6,76")
    with page.expect_request(
        lambda request: (
            RUN in request.url
            and (request.post_data_json or {}).get("snyder_cp") == 0.7
        )
    ):
        field(page, "snyder_ct").fill("1,4")
        field(page, "snyder_cp").fill("0,7")
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")

    # Back to SCS: Ct and Cp are kept but not sent, nor is Lc
    with page.expect_request(lambda request: RUN in request.url) as asked:
        choose(page, "hg-uh-label", "SCS")
    sent = asked.value.post_data_json
    assert isinstance(sent, dict)
    assert sent == KAMIENNIK
    shows(page, "57,88", "6:40", "1 046 713")
    for name in others:
        expect(field(page, name)).to_have_count(0)
    line = page.locator(f"{RIGHT} .cli pre")
    expect(line).to_contain_text("--uh-model scs")
    assert not re.search(r"snyder|nash|clark|Lc_km|manning", line.inner_text())
    stored = page.evaluate(STORED)
    assert (stored["snyder_ct"], stored["snyder_cp"]) == ("1,4", "0,7")


def test_choosing_a_model_marks_the_fields_it_lacks(tab: Tab) -> None:
    basic = typed("area_km2", "cn", "channel_length_km")
    seed_hydrogram(tab, kamiennik_inputs(watershed=basic, origin=None, uh_model=None))
    runs = Runs(tab.page)
    tab.open("#hydrogram")
    page = tab.page
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text("Wybierz model w kroku 3")
    invalid = page.locator(f'{LEFT} [aria-invalid="true"]')
    expect(invalid).to_have_count(0)

    # Nash by Lutz reads L and J of the longest flow path, for which the channel the
    # watershed gives does not stand in, then Lc and Manning's n: exactly those
    choose(page, "hg-uh-label", "Nash")
    expect(invalid).to_have_count(4)
    assert invalid.evaluate_all(IDS) == [
        "hg-flow_path_length_km",
        "hg-flow_path_slope_m_per_m",
        "hg-Lc_km",
        "hg-manning_n",
    ]
    expect(message(page, "flow_path_length_km")).to_have_text(
        "Podaj wartość: potrzebna dla metody Lutza · required"
    )
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: flow_path_length_km")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Dane niepełne: Długość najdłuższej drogi spływu"
    )
    missing = page.locator(f'{LEFT} [data-summary="missing"]')
    expect(missing).to_have_text(
        "Brakuje: Długość najdłuższej drogi spływu (krok 1), Spadek najdłuższej drogi"
        " spływu (krok 1), Długość do środka ciężkości (krok 3), Szorstkość koryta"
        " (krok 3)"
    )
    missing.get_by_role("button", name="Szorstkość koryta").click()
    expect(field(page, "manning_n")).to_be_focused()

    # SCS by Kirpich reads the longest flow path, nothing in its place: with the channel
    # given, its length and slope are asked for, no other way named, and nothing runs
    choose(page, "hg-uh-label", "SCS")
    expect(invalid).to_have_count(2)
    assert invalid.evaluate_all(IDS) == [
        "hg-flow_path_length_km",
        "hg-flow_path_slope_m_per_m",
    ]
    expect(message(page, "flow_path_slope_m_per_m")).to_have_text(
        "Podaj wartość: potrzebna dla metody Kirpicha · required"
    )
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: flow_path_length_km")
    page.wait_for_timeout(600)
    assert runs.generate == []
    field(page, "flow_path_length_km").fill("15,88")
    with page.expect_request(lambda request: RUN in request.url) as asked:
        field(page, "flow_path_slope_m_per_m").fill("0,0114")
    sent = asked.value.post_data_json
    assert isinstance(sent, dict)
    assert (
        sent["watershed"]["flow_path_length_km"],
        sent["watershed"]["flow_path_slope_m_per_m"],
    ) == (15.88, 0.0114)
    shows_peak(page, sent)

    # Back to Nash by Lutz: Lc and Manning's n are left; the fields of step 1 that Lutz
    # reads say so, the channel's do not
    choose(page, "hg-uh-label", "Nash")
    expect(invalid).to_have_count(2)
    assert invalid.evaluate_all(IDS) == ["hg-Lc_km", "hg-manning_n"]
    needs = page.locator(f"{LEFT} .frow .need")
    expect(needs).to_have_text(
        [
            "wymagane dla modelu Nasha",
            "wymagane dla strat SCS-CN",
            "wymagane dla metody Lutza",
            "wymagane dla metody Lutza",
        ]
    )
    assert needs.evaluate_all(
        "items => items.map((item) => item.closest('.frow').dataset.field)"
    ) == ["area_km2", "cn", "flow_path_length_km", "flow_path_slope_m_per_m"]
    # Lutz refuses a centroid farther than the flow path is long: said before any run
    before = len(runs.generate)
    field(page, "manning_n").fill("0,035")
    field(page, "Lc_km").fill("20")
    expect(message(page, "Lc_km")).to_have_text(
        "Nie może być większa od długości najdłuższej drogi spływu (15,88 km): "
        "tego wymaga metoda Lutza · maximum"
    )
    page.wait_for_timeout(600)
    assert len(runs.generate) == before

    # Lc given: one run of `hydrograph generate` estimates n and K, none of `uh nash`
    with page.expect_request(lambda request: RUN in request.url) as asked:
        field(page, "Lc_km").fill("6,76")
    sent = asked.value.post_data_json
    assert isinstance(sent, dict)
    assert sent["nash_estimation"] == "lutz"
    assert not {"nash_n", "nash_k_min"} & set(sent)
    expect(invalid).to_have_count(0)
    shows_peak(page, sent)
    assert runs.lutz == []


def test_fields_no_model_reads_may_stay_empty(tab: Tab) -> None:
    basic = {
        "name": "Kamiennik — Świerzawa",
        **typed("area_km2", "cn", "flow_path_length_km", "flow_path_slope_m_per_m"),
    }
    seed_hydrogram(tab, kamiennik_inputs(watershed=basic, origin=None))
    runs = Runs(tab.page)
    tab.open("#hydrogram")
    page = tab.page
    # Kirpich reads the longest flow path alone: the example's result without the
    # other fields
    shows(page, "57,88", "6:40", "1 046 713")
    assert runs.generate[-1]["watershed"] == {
        "name": "Kamiennik — Świerzawa",
        "area_km2": 37.22,
        "flow_path_length_km": 15.88,
        "flow_path_slope_m_per_m": 0.0114,
        "cn": 65,
    }
    expect(page.locator(f'{LEFT} [aria-invalid="true"]')).to_have_count(0)

    # The hand-off carries a full watershed: offered once step 1 has one
    buttons = page.locator(f'{RIGHT} [data-handoff-export="hydrogram"] button')
    expect(buttons).to_have_count(2)
    for index in range(2):
        expect(buttons.nth(index)).to_be_disabled()
    incomplete = page.locator(f"{RIGHT} [data-handoff-incomplete]")
    expect(incomplete).to_have_text(
        "Przekazanie niesie pełną zlewnię: uzupełnij w kroku 1 pola „Obwód”, "
        "„Długość zlewni”, „Wysokość min.”, „Wysokość maks.”."
    )

    # Every model runs without them: Clark, Nash with n and K, Snyder with its own L
    # (the watershed has no channel to take it from) and Lc
    with run_of(page, uh_model="clark") as answered:
        choose(page, "hg-uh-label", "Clark")
    shows_peak(page, answered.value.request.post_data_json)
    choose(page, "hg-uh-label", "Nash")
    choose(page, "hg-nash-source-label", "Podane n i K")
    with run_of(page, uh_model="nash", nash_k_min=82) as answered:
        field(page, "nash_n").fill("3,6")
        field(page, "nash_k_min").fill("82")
    shows_peak(page, answered.value.request.post_data_json)
    choose(page, "hg-uh-label", "Snyder")
    expect(message(page, "channel_length_km")).to_have_text(
        "Podaj wartość: potrzebna dla modelu Snydera · required"
    )
    expect(message(page, "Lc_km")).to_have_text(
        "Podaj wartość: potrzebna dla modelu Snydera · required"
    )
    expect(field(page, "snyder_length_km")).to_have_count(0)
    expect(field(page, "snyder_centroid_length_km")).to_have_count(0)
    field(page, "channel_length_km").fill("14,78")
    with run_of(page, uh_model="snyder", snyder_centroid_length_km=6.76) as answered:
        field(page, "Lc_km").fill("6,76")
    shows_peak(page, answered.value.request.post_data_json)
    allowed = {
        "name",
        "area_km2",
        "cn",
        "flow_path_length_km",
        "flow_path_slope_m_per_m",
    }
    assert all(
        set(sent["watershed"]) <= allowed | {"channel_length_km", "Lc_km"}
        for sent in runs.generate
    )

    # Step 1 complete: the hand-off is offered
    for name in ["perimeter_km", "length_km", "elevation_min_m", "elevation_max_m"]:
        field(page, name).fill(input_text(EXAMPLE[name]))
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    expect(buttons.first).to_be_enabled()
    expect(incomplete).to_have_count(0)


def test_a_value_outside_its_typical_range_is_a_warning_and_runs(tab: Tab) -> None:
    page = open_hydrogram(tab)
    slope = field(page, "flow_path_slope_m_per_m")
    row = page.locator(f'{LEFT} [data-field="flow_path_slope_m_per_m"]')
    with page.expect_response(lambda answer: RUN in answer.url) as answered:
        slope.fill("0,2")
    envelope = answered.value.json()
    assert {
        item["details"]["field"]: item["details"]["value"]
        for item in envelope["notices"]
        if item["code"] == "outside_typical_range"
    } == {"area_km2": 37.22, "flow_path_slope_m_per_m": 0.2}
    expect(row).to_have_attribute("data-level", "warning")
    expect(warning(page, "flow_path_slope_m_per_m")).to_have_text(
        "Poza typowym zakresem od 0,03 do 0,1 (kirpich) · outside_typical_range"
    )
    expect(slope).to_have_attribute("aria-invalid", "false")
    # The run went on: the result is current, the notice is in Wyniki too
    shows_peak(
        page, {**KAMIENNIK, "watershed": {**SENT, "flow_path_slope_m_per_m": 0.2}}
    )
    notices = page.locator(f'{RIGHT} .notes li[data-code="outside_typical_range"]')
    expect(notices.filter(has_text="slope_m_per_m")).to_have_text(
        re.compile(r"kirpich: slope_m_per_m = 0,2 poza typowym zakresem")
    )
    outside = page.locator(f'{LEFT} [data-summary="warnings"]')
    expect(outside).to_have_text(
        "Poza typowym zakresem: Powierzchnia (krok 1), "
        "Spadek najdłuższej drogi spływu (krok 1)"
    )
    expect(page.locator(f'{LEFT} [data-summary="ok"]')).to_have_count(1)
    outside.get_by_role("button", name="Spadek najdłuższej drogi spływu").click()
    expect(slope).to_be_focused()

    # Changed, the field drops the run's warning; inside the range, none comes
    slope.fill("0,05")
    expect(row.locator(".warn")).to_have_count(0)
    shows_peak(
        page, {**KAMIENNIK, "watershed": {**SENT, "flow_path_slope_m_per_m": 0.05}}
    )
    expect(row.locator(".warn")).to_have_count(0)
    expect(notices.filter(has_text="slope_m_per_m")).to_have_count(0)
    expect(outside).to_have_text("Poza typowym zakresem: Powierzchnia (krok 1)")

    # A coefficient of a model: Snyder's Ct
    choose(page, "hg-uh-label", "Snyder")
    field(page, "snyder_ct").fill("2")
    expect(warning(page, "snyder_ct")).to_have_text(
        "Poza typowym zakresem od 1,35 do 1,65 (snyder) · outside_typical_range"
    )
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")


def test_a_given_nash_n_outside_its_range_to_be_verified_says_so(tab: Tab) -> None:
    page = open_hydrogram(tab)
    choose(page, "hg-uh-label", "Nash")
    choose(page, "hg-nash-source-label", "Podane n i K")
    # The note and the confirmation quote Hydrolog's ranges of n and K, to be verified
    expect(page.locator(f"{LEFT} p.note").filter(has_text="n i K")).to_have_text(
        "n i K skalibrowane albo z innego źródła; typowo "
        "n od 1 do 10 (do weryfikacji), K od 10 do 200 min (do weryfikacji)."
    )
    with run_of(page, uh_model="nash", nash_n=3.6, nash_k_min=82):
        field(page, "nash_n").fill("3,6")
        field(page, "nash_k_min").fill("82")
    confirmed = page.locator(f'{RIGHT} [data-notes="gui"] li').filter(has_text="Nash:")
    expect(confirmed).to_contain_text(
        "n = 3,6 (do weryfikacji), K = 82\u00a0min (do weryfikacji)"
    )

    with run_of(page, uh_model="nash", nash_n=12) as answered:
        field(page, "nash_n").fill("12")
    envelope = answered.value.json()
    assert [
        item["details"]["field"]
        for item in envelope["notices"]
        if item["code"] == "outside_unverified_range"
    ] == ["nash_n"]
    expect(warning(page, "nash_n")).to_have_text(
        "Poza typowym zakresem od 1 do 10 (nash); zakres do weryfikacji "
        "· outside_unverified_range"
    )
    expect(warning(page, "nash_k_min")).to_have_count(0)
    expect(
        page.locator(f'{RIGHT} .notes li[data-code="outside_unverified_range"]')
    ).to_contain_text("nash: n = 12 poza typowym zakresem od 1 do 10")
    expect(confirmed).to_have_count(0)

    # The explanation marks both ranges „do weryfikacji”, n outside, K inside
    page.locator(f"{LEFT} .label-row:has(#hg-uh-label) .info-btn").click()
    rows = page.locator(".info-pop .range-list li")
    expect(rows.first).to_be_visible()
    marked = rows.evaluate_all(
        "items => Object.fromEntries(items.map((item) => [item.dataset.range,"
        " [item.className, item.dataset.verified || null]]))"
    )
    assert marked == {
        **{key: [state, None] for key, (state, _) in marked.items()},
        "nash.n": ["warn", "false"],
        "nash.k_min": ["ok", "false"],
    }
    expect(rows.and_(page.locator('[data-range="nash.n"]'))).to_contain_text(
        "do weryfikacji"
    )


def test_a_unit_hydrograph_of_years_draws_thinned_and_clears(tab: Tab) -> None:
    # Nash with n = 200, K = 1500 min: Hydrolog's unit hydrograph lasts 5·n·K (~3 years)
    seed_hydrogram(
        tab,
        kamiennik_inputs(
            uh_model="nash", nash_source="given", nash_n="12", nash_k_min="300"
        ),
    )
    tab.open("#hydrogram")
    page = tab.page
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    before = kpi(page, "q").inner_text()
    with run_of(page, nash_n=200, nash_k_min=1500) as answered:
        field(page, "nash_n").fill("200")
        field(page, "nash_k_min").fill("1500")
    result = answered.value.json()["result"]
    steps = len(result["times_min"])
    assert len(result["uh_discharge_m3s_per_mm"]) > 100_000 and steps > 100_000
    # The new result is shown and current (no stack overflow: the tab records errors)
    expect(kpi(page, "q")).to_have_text(
        re.compile(rf"^{comma(result['peak_discharge_m3s'])}\s*m³/s$")
    )
    assert flat(kpi(page, "q").inner_text()) != flat(before)
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    # Drawn thinned: a few points per column of the plot, not one per step
    for chart, series in [(CENTER, "q"), (f'{CENTER} [data-chart="uh"]', "u")]:
        line = page.locator(f'{chart} path.ser[data-series="{series}"]').first
        expect(line).to_be_attached()
        assert 100 < len(re.findall(r"[ML]", line.get_attribute("d") or "")) < 4_000
    # The table keeps every step (cut on screen, whole in the exports)
    page.locator(CENTER).get_by_role("radio", name="Tabela").click()
    expect(page.locator(f"{CENTER} .table-more")).to_contain_text(
        re.compile(rf"z {steps // 1000}\s{steps % 1000:03d} wiersz")
    )

    # „Wyczyść” drops the result
    page.locator(LEFT).get_by_role("button", name="Wyczyść").click()
    expect(kpi(page, "q")).to_have_count(0)
    expect(page.locator(f"{CENTER} .chart")).to_have_count(0)
    expect(page.locator(RIGHT)).to_contain_text("Wynik pojawi się po pierwszym")
    expect(page.locator(BADGE)).to_be_hidden()


def test_a_result_that_fails_to_draw_is_an_error_not_the_last_result(
    tab: Tab,
) -> None:
    page = open_hydrogram(tab)

    def broken(route: Route) -> None:
        answer = route.fetch()
        envelope = answer.json()
        envelope["result"]["discharge_m3s"] = None  # the table cannot read it
        route.fulfill(response=answer, json=envelope)

    page.route(f"**{RUN}?*", broken)
    with page.expect_response(lambda answer: RUN in answer.url):
        field(page, "cn").fill("70")
    center = page.locator(f'{CENTER} [data-render-error="center"]')
    expect(center).to_contain_text("Nie udało się pokazać wyniku")
    expect(page.locator(f"{CENTER} .chart")).to_have_count(0)  # not the last charts
    expect(page.locator(BADGE)).to_have_text("Błąd wyświetlania")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Błąd wyświetlania: wynik nie jest pokazany"
    )

    # A result that draws is current again; „Wyczyść” drops a failed one
    page.unroute(f"**{RUN}?*")
    field(page, "cn").fill("65")
    shows(page, "57,88", "6:40", "1 046 713")
    expect(center).to_have_count(0)
    page.route(f"**{RUN}?*", broken)
    field(page, "cn").fill("70")
    expect(center).to_be_visible()
    page.locator(LEFT).get_by_role("button", name="Wyczyść").click()
    expect(center).to_have_count(0)
    expect(kpi(page, "q")).to_have_count(0)
    expect(page.locator(RIGHT)).to_contain_text("Wynik pojawi się po pierwszym")
    expect(page.locator(BADGE)).to_be_hidden()


def test_requirements_follow_the_model_and_the_tc_method(tab: Tab) -> None:
    tab.open("#polecenia")
    got = tab.page.evaluate(
        """async (example) => {
          const s = await import('./src/sections/hydrogram/state.js');
          const full = s.readWatershed(example).texts;
          const pick = (...names) =>
            Object.fromEntries(names.map((name) => [name, full[name]]));
          const base = {...s.initialState(), watershed: full};
          const needs = (patch) => Object.fromEntries(
            Object.entries(s.requirements({...base, ...patch}).required).map(
              ([name, need]) => [name, need.or ? [need.purpose, need.or] : need.purpose]
            ),
          );
          const fields = (patch) => s.panelFields({...base, ...patch});
          return {
            none: needs({}),
            kirpich: needs({uh_model: 'scs'}),
            bare: needs({uh_model: 'scs', watershed: pick('area_km2', 'cn')}),
            relief: needs({uh_model: 'clark', watershed: pick(
              'area_km2', 'cn', 'length_km', 'elevation_min_m', 'elevation_max_m')}),
            nrcs: needs({uh_model: 'scs', tc_method: 'nrcs'}),
            giandotti: needs({uh_model: 'scs', tc_method: 'giandotti'}),
            giandottiMax: needs({uh_model: 'scs', tc_method: 'giandotti',
              watershed: pick('area_km2', 'cn', 'length_km', 'elevation_min_m',
                'elevation_max_m')}),
            faa: needs({uh_model: 'scs', tc_method: 'faa'}),
            kerby: needs({uh_model: 'clark', tc_method: 'kerby', clark_kind: 'r'}),
            kerbyKirpich: needs({uh_model: 'scs', tc_method: 'kerby_kirpich'}),
            manual: needs({uh_model: 'clark', tc_manual: true, tc_method: 'faa'}),
            lutz: needs({uh_model: 'nash', rain_source: 'design'}),
            given: needs({uh_model: 'nash', nash_source: 'given',
              rain_source: 'series'}),
            snyder: needs({uh_model: 'snyder', watershed: pick('area_km2', 'cn')}),
            migrated: s.normalize({
              snyder_length_km: '12', snyder_centroid_length_km: '5',
              watershed: {Lc_km: '6'}}),
            fieldsScs: fields({uh_model: 'scs'}),
            fieldsFaa: fields({uh_model: 'clark', tc_method: 'faa'}),
            fieldsSnyder: fields({uh_model: 'snyder', rain_source: 'design',
              hietogram_type: 'triangular'}),
            sentScs: s.sentFields({...base, uh_model: 'scs'}),
            sentLutz: s.sentFields({...base, uh_model: 'nash'}),
          };
        }""",
        EXAMPLE,
    )
    pmaxtp = {
        "pmaxtp_latitude": "pmaxtp",
        "pmaxtp_longitude": "pmaxtp",
        "pmaxtp_probability_pct": "pmaxtp",
        "pmaxtp_duration_min": "pmaxtp",
    }
    scs = {"area_km2": "scs", "cn": "losses", **pmaxtp}
    clark = {"area_km2": "clark", "cn": "losses", **pmaxtp}
    flow_path = {"flow_path_length_km": "kirpich", "flow_path_slope_m_per_m": "kirpich"}
    assert got["none"] == {}
    assert got["kirpich"] == {**scs, **flow_path}
    # Nothing stands in for a method's own fields: neither a watershed lacking them
    # (no other way named) nor the watershed's length and relief
    assert got["bare"] == {**scs, **flow_path}
    assert got["relief"] == {**clark, **flow_path, "clark_r_tc_ratio": "clark"}
    assert got["nrcs"] == {
        **scs,
        "flow_path_length_km": "nrcs",
        "mean_slope_m_per_m": "nrcs",
    }
    giandotti = {
        "channel_length_km": "giandotti",
        "elevation_min_m": "giandotti",
        "elevation_mean_m": "giandotti",
    }
    assert got["giandotti"] == {**scs, **giandotti}
    assert got["giandottiMax"] == {**scs, **giandotti}
    overland = {"overland_length_km": "faa", "overland_slope_m_per_m": "faa"}
    assert got["faa"] == {**scs, **overland, "runoff_coeff": "faa"}
    assert got["kerby"] == {
        **clark,
        "overland_length_km": "kerby",
        "overland_slope_m_per_m": "kerby",
        "retardance": "kerby",
        "clark_r_min": "clark",
    }
    assert got["kerbyKirpich"] == {
        **scs,
        "overland_length_km": "kerby_kirpich",
        "overland_slope_m_per_m": "kerby_kirpich",
        "retardance": "kerby_kirpich",
        "flow_path_length_km": "kerby_kirpich",
        "flow_path_slope_m_per_m": "kerby_kirpich",
    }
    assert got["manual"] == {**clark, "tc_min": "tc_min", "clark_r_tc_ratio": "clark"}
    assert got["lutz"] == {
        "area_km2": "nash",
        "cn": "losses",
        "total_mm": "hietogram",
        "duration_min": "hietogram",
        "flow_path_length_km": "lutz",
        "Lc_km": "lutz",
        "flow_path_slope_m_per_m": "lutz",
        "manning_n": "lutz",
    }
    assert got["given"] == {
        "area_km2": "nash",
        "cn": "losses",
        "values": "series",
        "nash_n": "nash",
        "nash_k_min": "nash",
    }
    assert got["snyder"] == {
        "area_km2": "snyder",
        "cn": "losses",
        **pmaxtp,
        "channel_length_km": "snyder",
        "Lc_km": "snyder",
    }
    # Snyder's own L and Lc of an earlier visit fill the watershed's empty fields only
    assert got["migrated"]["watershed"] == {"channel_length_km": "12", "Lc_km": "6"}
    assert "snyder_length_km" not in got["migrated"]
    assert "snyder_centroid_length_km" not in got["migrated"]
    rain = [
        "pmaxtp_latitude",
        "pmaxtp_longitude",
        "pmaxtp_probability_pct",
        "pmaxtp_duration_min",
        "pmaxtp_method",
        "pmaxtp_depth",
    ]
    assert got["fieldsScs"] == [
        *STEP_ONE[:2],
        "cn",
        *STEP_ONE[2:-1],
        *rain,
        "alpha",
        "beta",
        "timestep_min",
        "ia_coefficient",
    ]
    assert got["fieldsFaa"][-6:] == [
        "timestep_min",
        "overland_length_km",
        "overland_slope_m_per_m",
        "runoff_coeff",
        "clark_r_tc_ratio",
        "ia_coefficient",
    ]
    assert got["fieldsSnyder"][-7:] == [
        "duration_min",
        "peak_position",
        "timestep_min",
        "Lc_km",
        "snyder_ct",
        "snyder_cp",
        "ia_coefficient",
    ]
    assert got["sentScs"] == [*STEP_ONE, "source", "crs"]
    assert got["sentLutz"] == [*STEP_ONE, *LUTZ_BLOCK, "source", "crs"]


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
    expect(page.locator(f'{LEFT} [data-summary="invalid"]')).to_have_text(
        "Popraw: CN dla AMC II (krok 1)"
    )
    stale = page.locator('[data-stale="invalid"]')
    expect(stale).to_have_count(2)  # the centre and the panel Wyniki
    expect(stale.first).to_have_text(
        "Wynik dla poprzednich danych: popraw pole „CN dla AMC II” w panelu Dane."
    )
    expect(kpi(page, "q")).to_have_text(re.compile(r"^57,88"))
    page.wait_for_timeout(600)
    assert runs.generate == []  # invalid data run nothing

    cn.fill("72")
    shows_peak(page, {**KAMIENNIK, "watershed": {**SENT, "cn": 72}})
    expect(stale).to_have_count(0)
    expect(message(page, "cn")).to_have_count(0)
    # The changed field is marked against the file it came from, and restored
    mark = page.locator(f'{LEFT} [data-field="cn"] .chg')
    expect(mark).to_have_text(re.compile(r"zmieniono · kamiennik\.json: 65"))
    expect(page.locator(f'{LEFT} [data-field="cn"]')).to_have_class(
        re.compile(r"\bedited\b")
    )
    expect(page.locator(f'{LEFT} [data-field="area_km2"]')).not_to_have_class(
        re.compile(r"\bedited\b")
    )
    mark.get_by_role("button", name="przywróć").click()
    expect(cn).to_have_value("65")
    shows(page, "57,88", "6:40", "1 046 713")


def test_ten_fast_edits_send_at_most_two_runs_and_show_the_last(tab: Tab) -> None:
    # The depth typed for „Hietogram” (PMAXTP's is fetched, never typed)
    seed_hydrogram(tab, kamiennik_inputs(rain_source="design", duration_min="720"))
    tab.open("#hydrogram")
    page = tab.page
    shows(page, "57,88", "6:40", "1 046 713")
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
    shows_peak(page, {**KAMIENNIK, "total_mm": 100.123456})
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
        # Nash by Lutz (the example's choice): the command estimates n and K itself
        if model == "Nash":
            assert "--nash-estimation lutz" in line
            assert not re.search(r"--nash-(n|k-min) ", line)
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


def test_errors_stand_on_their_field_before_or_after_the_run_or_above(tab: Tab) -> None:
    page = open_hydrogram(tab)
    # A tc method's field missing: marked at once, nothing runs
    field(page, "tc_method").select_option("faa")
    shows(page, "71,57", "4:30", "1 038 431")
    runs = Runs(page)
    field(page, "runoff_coeff").fill("")
    expect(message(page, "runoff_coeff")).to_have_text(
        "Podaj wartość: potrzebna dla metody FAA · required"
    )
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: runoff_coeff")
    expect(page.locator(f'{LEFT} [data-summary="missing"]')).to_have_text(
        "Brakuje: Współczynnik spływu (krok 3)"
    )
    page.wait_for_timeout(600)
    assert runs.generate == []
    field(page, "runoff_coeff").fill("0,25")
    shows(page, "71,57", "4:30", "1 038 431")
    field(page, "tc_method").select_option("kirpich")
    shows(page, "57,88", "6:40", "1 046 713")

    # The highest elevation not above the lowest: an error at once
    before = len(runs.generate)
    field(page, "elevation_max_m").fill("200")
    expect(message(page, "elevation_max_m")).to_have_text(
        "Musi być większa od wysokości min. (257,3 m n.p.m.) · exclusive_minimum"
    )
    page.wait_for_timeout(600)
    assert len(runs.generate) == before
    field(page, "elevation_max_m").fill("475,1")
    shows(page, "57,88", "6:40", "1 046 713")

    # An error of the server on its field: Clark's step above 2R
    choose(page, "hg-uh-label", "Clark")
    choose(page, "hg-clark-label", "R [min]")
    field(page, "clark_r_min").fill("4")
    expect(message(page, "timestep_min")).to_have_text(
        re.compile(r" · unstable_timestep$")
    )
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    expect(page.locator('[data-stale="error"]').first).to_have_text(
        re.compile(r"^Wynik dla poprzednich danych: Hydrolog nie policzył")
    )
    expect(page.locator(f'{LEFT} [data-summary="invalid"]')).to_have_text(
        "Popraw: Krok czasowy (krok 2)"
    )
    field(page, "clark_r_min").fill("90")
    expect(message(page, "timestep_min")).to_have_count(0)
    shows_peak(page, {**KAMIENNIK, "uh_model": "clark", "clark_r_min": 90})
    choose(page, "hg-uh-label", "SCS")
    shows(page, "57,88", "6:40", "1 046 713")

    # Kerby–Kirpich's channel is the flow path minus the overland segment: a flow path
    # not longer than the overland one is the server's error on its field
    field(page, "tc_method").select_option("kerby_kirpich")
    shows(page, *MOCKUP[("scs", "kerby_kirpich", "II")])
    field(page, "flow_path_length_km").fill("0,2")
    expect(message(page, "flow_path_length_km")).to_have_text(
        "Musi być większa od 0,3 (podano 0,2) · exclusive_minimum"
    )
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    field(page, "flow_path_length_km").fill("15,88")
    shows(page, *MOCKUP[("scs", "kerby_kirpich", "II")])
    field(page, "tc_method").select_option("kirpich")
    shows(page, "57,88", "6:40", "1 046 713")

    # A library error without an option stands above the steps, in English marked (EN)
    choose(page, "hg-rain-source-label", "Hietogram")
    field(page, "duration_min").fill("5")
    above = page.locator(f"{LEFT} [data-form-error]")
    expect(above).to_contain_text("Nieprawidłowe dane wejściowe")
    expect(above).to_contain_text("cannot exceed duration_min (5.0) (EN)")
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Błąd danych: wynik dla poprzednich danych"
    )
    expect(kpi(page, "q")).to_have_text(re.compile(r"^57,88"))
    field(page, "duration_min").fill("720")
    expect(above).to_have_count(0)
    shows(page, "57,88", "6:40", "1 046 713")


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
    source = page.locator(f"{LEFT} .handoff")
    expect(source.locator("strong")).to_have_text("Z pliku: potok.json")
    expect(source.locator(".muted")).to_have_text(re.compile(r"· 20 pól$"))
    shows_peak(page, {**KAMIENNIK, "watershed": {name: own[name] for name in STEP_ONE}})
    expect(page.locator(".crumb-context")).to_have_text("Potok testowy · p 1% · 12 h")
    assert "Lc_km" not in page.evaluate(STORED)["watershed"]

    field(page, "perimeter_km").fill("30")
    mark = page.locator(f'{LEFT} [data-field="perimeter_km"] .chg')
    expect(mark).to_have_text(re.compile(r"zmieniono · potok\.json: 40,89"))
    mark.get_by_role("button", name="przywróć").click()
    expect(field(page, "perimeter_km")).to_have_value("40,89")
    expect(mark).to_have_count(0)

    # A file without an area is not a watershed and changes nothing
    bad = tmp_path / "zle.json"
    bad.write_text('{"name": "Bez powierzchni", "cn": 70}', encoding="utf-8")
    page.locator(f'{LEFT} input[type="file"]').set_input_files(str(bad))
    expect(page.locator(".toast")).to_have_text(
        re.compile(r"^Nie udało się wczytać zlewni z zle\.json: .*area_km2")
    )
    expect(field(page, "name")).to_have_value("Potok testowy")


# --- exports -------------------------------------------------------------------


def test_the_hydrograph_exports_csv_json_and_png(tab: Tab, tmp_path: Path) -> None:
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    envelope = answered.value.json()
    result = envelope["result"]
    open_part(page, SECTION, "exports")
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
    options = {
        **KAMIENNIK,
        "watershed": {**SENT, "cn": 70},
        "uh_model": "clark",
        "clark_r_tc_ratio": 0.5,
    }
    shows_peak(page, options)
    stored = page.evaluate(STORED)
    assert stored["watershed"]["cn"] == "70" and stored["uh_model"] == "clark"
    assert "envelope" not in json.dumps(stored)  # inputs only, no results

    page.reload()
    expect(field(page, "cn")).to_have_value("70")
    shows_peak(page, options)

    # „Wyczyść” empties the steps, as on a first visit, and the store's watershed
    runs = Runs(page)
    page.locator(LEFT).get_by_role("button", name="Wyczyść").click()
    expect(field(page, "cn")).to_have_value("")
    for name in ("pmaxtp_latitude", "pmaxtp_longitude", "pmaxtp_depth"):
        expect(field(page, name)).to_have_value("")
    expect(
        page.locator('[aria-labelledby="hg-uh-label"] [aria-checked="true"]')
    ).to_have_count(0)
    expect(page.locator(f"{LEFT} .step > summary .meta")).to_have_text(
        ["brak danych", "brak danych", "wybierz model"]
    )
    expect(page.locator(BADGE)).to_be_hidden()
    expect(page.locator(RIGHT)).to_contain_text("Wynik pojawi się po pierwszym")
    assert (
        page.evaluate(
            "async () => (await import('./src/store.js')).getStore('watershed')"
        )
        is None
    )
    page.reload()
    expect(field(page, "area_km2")).to_have_value("")
    page.wait_for_timeout(600)
    assert runs.generate == [] and runs.pmaxtp == []


def test_kalkulatory_sets_the_tc_method_through_the_route(
    tab: Tab, new_tab: Callable[..., Tab]
) -> None:
    seed_hydrogram(tab)
    tab.open("#hydrogram/tc_method/nrcs")
    page = tab.page
    shows(page, *MOCKUP[("scs", "nrcs", "II")])
    expect(field(page, "tc_method")).to_have_value("nrcs")
    expect(page).to_have_url(re.compile(r"#hydrogram$"))
    # The inputs are stored by an effect after the next frame, later on a slower runner
    page.wait_for_function(f"() => ({STORED})()?.tc_method === 'nrcs'")
    stored = page.evaluate(STORED)
    assert (stored["tc_method"], stored["tc_manual"], stored["uh_model"]) == (
        "nrcs",
        False,
        "scs",
    )

    # Before a model is chosen the method waits for SCS or Clark
    fresh = new_tab()
    fresh.open("#hydrogram/tc_method/giandotti")
    expect(fresh.page).to_have_url(re.compile(r"#hydrogram$"))
    expect(field(fresh.page, "tc_method")).to_have_count(0)
    fresh.page.wait_for_function(f"() => ({STORED})()?.tc_method === 'giandotti'")
    choose(fresh.page, "hg-uh-label", "SCS")
    expect(field(fresh.page, "tc_method")).to_have_value("giandotti")


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


def test_the_explanations_show_exactly_the_ranges_hydrolog_serves(tab: Tab) -> None:
    page = open_hydrogram(tab)
    # Statystyka and Sieć, mounted with the shell, register theirs once their documents
    # arrive
    page.evaluate("async () => { window.testInfo = await import('./src/ui/info.js'); }")
    page.wait_for_function(
        "() => ['stats-flood-frequency', 'routing.muskingum']"
        ".every((id) => window.testInfo.infoRanges(id).length > 0)"
    )
    shown: dict[str, dict[str, Any]] = page.evaluate(EXPLAINED)
    documents = {
        command: served(command)
        for command in ["hydrograph generate", "tc watershed", "stats flood-frequency"]
    }
    every = [found for ranges in documents.values() for found in ranges]
    schema = page.request.get(tab.base + "api/schemas/hydrolog-network-1.schema.json")
    muskingum = next(
        branch["properties"]["x"]
        for branch in schema.json()["$defs"]["node"]["oneOf"]
        if branch["properties"].get("method", {}).get("const") == "muskingum"
    )

    # Nothing of the GUI's own: each range is one Hydrolog serves, as it serves it, and
    # Muskingum's X has the bounds of the network's schema
    for info, entry in shown.items():
        for found in entry["ranges"]:
            if info.startswith("routing."):
                assert (found["parameter"], found["minimum"], found["maximum"]) == (
                    "x",
                    muskingum["minimum"],
                    muskingum["maximum"],
                )
            else:
                assert found in every, (info, found)
    # Nothing left out: every range of the documents the sections check
    registered = [found for entry in shown.values() for found in entry["ranges"]]
    for found in [
        *documents["hydrograph generate"],
        *documents["tc watershed"],
        *documents["stats flood-frequency"],
    ]:
        assert found in registered, found
    # Lutz's area, which `hydrograph generate` serves, in Nash's explanation
    lutz = [
        found for found in documents["hydrograph generate"] if found["method"] == "lutz"
    ]
    assert lutz
    assert lutz == [
        found for found in shown["uh-nash"]["ranges"] if found["method"] == "lutz"
    ]

    # One row per range, with its source in Polish; the four unit hydrograph models
    # serve one range of the time step, listed once
    rows = {info: len(entry["rows"]) for info, entry in shown.items()}
    assert rows == {
        **{info: len(entry["ranges"]) for info, entry in shown.items()},
        "rain-timestep": 1,
    }
    for info, entry in shown.items():
        sources = {
            f"{found['method']}.{found['parameter']}": found.get("i18n", {})
            .get("pl", {})
            .get("source", found["source"])
            for found in entry["ranges"]
        }
        for row in entry["rows"]:
            assert row["text"].endswith(f"({sources[row['key']]})"), (info, row)
    words = {
        row["key"]: row["text"] for entry in shown.values() for row in entry["rows"]
    }
    assert "A: od 0,005 do 0,45 km²" in words["kirpich.area_km2"]
    assert "A: od 170 do 70\u00a0000 km²" in words["giandotti.area_km2"]
    assert "Δt: najwyżej 0,25·tp (" in words["scs.timestep_min"]
    assert "Długość szeregu N: co najmniej 30 lat" in words["flood_frequency.years"]
    assert "X: najwyżej 0,5" in words["muskingum.x"]


def test_the_explanations_check_hydrologs_ranges_against_the_watershed(
    tab: Tab,
) -> None:
    page = open_hydrogram(tab)
    popover = page.locator(".info-pop")
    title = popover.locator("#info-pop-title")
    rows = popover.locator(".range-list li")
    notes = page.locator(f'{RIGHT} [data-notes="gui"] li')
    # The example's confirmations: SCS-CN, SCS and the time step against the unit
    # hydrograph's time to peak (0,25 · 117,43 min); none for Kirpich, which Hydrolog's
    # notices put outside its data
    expect(notes).to_have_count(3)
    expect(notes.nth(0)).to_contain_text(
        "SCS-CN: CN (AMC I i III) = 65 w zakresie stosowania."
    )
    expect(notes.nth(1)).to_contain_text(
        "SCS: A = 37,22\u00a0km² w zakresie stosowania."
    )
    expect(notes.nth(2)).to_contain_text(
        "Krok Δt = 10 min ≤ 0,25·tp hydrogramu jednostkowego (29,36 min)."
    )
    assert set(notes.evaluate_all("items => items.map((item) => item.className)")) == {
        "ok"
    }
    # The note of the time step opens its explanation: the range of the four models once
    notes.nth(2).get_by_role("button", name="objaśnienie").click()
    expect(title).to_have_text("Krok czasowy Δt")
    expect(rows).to_have_count(1)
    expect(rows).to_have_attribute("data-range", "scs.timestep_min")
    expect(rows).to_have_attribute("data-field", "timestep_min")
    expect(rows).to_have_class("ok")
    expect(rows).to_contain_text("Δt = 10 min: najwyżej 0,25·tp = 29,36 min (")
    page.keyboard.press("Escape")
    expect(popover).to_be_hidden()

    # Kerby–Kirpich: each of its ranges checked on the field it reads, all inside
    field(page, "tc_method").select_option("kerby_kirpich")
    shows(page, *MOCKUP[("scs", "kerby_kirpich", "II")])
    page.locator(f"{LEFT} [data-block=tc] .info-btn").click()
    expect(title).to_have_text("Kerby–Kirpich: spływ po stoku i korytem")
    ranges = [
        found
        for found in served("hydrograph generate")
        if found["method"] == "kerby_kirpich"
    ]
    expect(rows).to_have_count(len(ranges))
    assert rows.evaluate_all(
        "items => items.map((item) => [item.dataset.range, item.dataset.field,"
        " item.className])"
    ) == [
        [f"kerby_kirpich.{found['parameter']}", checked_field(found, EXAMPLE), "ok"]
        for found in ranges
    ]
    page.keyboard.press("Escape")
    expect(popover).to_be_hidden()
    # Its confirmation in Wyniki opens the same explanation
    note = notes.filter(has_text="Kerby–Kirpich:")
    expect(note).to_contain_text("w zakresie stosowania.")
    note.get_by_role("button", name="objaśnienie").click()
    expect(title).to_have_text("Kerby–Kirpich: spływ po stoku i korytem")


def test_the_fields_the_explanation_and_wyniki_agree_on_the_example(tab: Tab) -> None:
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    # Hydrolog's verdict, twice: the ranges it serves for the methods of the run
    # (Kirpich, SCS, SCS-CN) against the example, and the notices of the run
    ranges = [
        found
        for found in served("hydrograph generate")
        if found["method"] in {"kirpich", "scs", "scs_cn_amc"}
        and "relative_to" not in found
    ]
    outside = set()
    for found in ranges:
        name = checked_field(found, EXAMPLE)
        if name is not None and leaves(found, EXAMPLE[name]):
            outside.add(name)
    assert outside == {"area_km2", "flow_path_slope_m_per_m"}
    notices = [
        notice
        for notice in answered.value.json()["notices"]
        if notice["code"] == "outside_typical_range"
    ]
    assert {notice["details"]["field"] for notice in notices} == outside

    # The fields: a warning on each of them, none elsewhere, and the summary says so
    warned = page.locator(f"{LEFT} [data-field] .warn")
    expect(warned).to_have_count(len(outside))
    fields = warned.evaluate_all(
        "items => items.map((item) => item.closest('[data-field]').dataset.field)"
    )
    assert set(fields) == outside
    expect(page.locator(f'{LEFT} [data-summary="warnings"] [data-goto]')).to_have_count(
        len(outside)
    )
    # Wyniki: the same notices; the GUI confirms nothing of Kirpich
    expect(
        page.locator(f'{RIGHT} .notes li[data-code="outside_typical_range"]')
    ).to_have_count(len(notices))
    expect(
        page.locator(f'{RIGHT} [data-notes="gui"] li').filter(has_text="Kirpich")
    ).to_have_count(0)
    # The explanation of Kirpich: outside on the same fields
    page.locator(f"{LEFT} [data-block=tc] .info-btn").click()
    rows = page.locator(".info-pop .range-list li")
    expect(rows).to_have_count(sum(found["method"] == "kirpich" for found in ranges))
    marked = rows.evaluate_all(
        "items => items.map((item) => [item.className, item.dataset.field])"
    )
    assert {name for _, name in marked} == outside
    assert {state for state, _ in marked} == {"warn"}


# --- the phone -----------------------------------------------------------------


def test_a_phone_in_the_dark_theme_recomputes_through_the_sheets(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    seed_hydrogram(tab)
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
          const {createChannel} = await import('./src/recompute.js');
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
        """async ([example, stored]) => {
          const s = await import('./src/sections/hydrogram/state.js');
          const doc = await (await fetch('api/commands/hydrograph/generate')).json();
          const schema = await (
            await fetch('api/schemas/hydrolog-network-1.schema.json')
          ).json();
          const pmaxtpDoc = await (await fetch('api/commands/precip/pmaxtp')).json();
          const models = s.inputModels(doc, schema, pmaxtpDoc);
          const read = s.readWatershed(example);
          const base = s.normalize({...stored, watershed: read.texts});
          const variant = (patch) => ({...base, ...patch});
          const check = (patch, last) => s.checkInputs(variant(patch), models, last);
          const slope = {
            level: 'warning', code: 'outside_typical_range', message: '',
            details: {method: 'kirpich', parameter: 'slope_m_per_m',
              field: 'flow_path_slope_m_per_m', value: 0.2,
              minimum: 0.03, maximum: 0.1},
          };
          const steep = variant({
            watershed: {...read.texts, flow_path_slope_m_per_m: '0,2'},
          });
          return {
            kamiennik: s.toOptions(base),
            nash: s.toOptions(variant({uh_model: 'nash'})),
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
            noModel: check({
              uh_model: null, total_mm: '', watershed: {area_km2: 'abc'},
            }),
            manualEmpty: check({tc_manual: true}),
            lutzMissing: check({
              uh_model: 'nash', watershed: {...read.texts, Lc_km: ''},
            }),
            // Lc against L, the longest flow path (15,88 km), not the channel (14,78)
            lutzLc: ['15', '16'].map((lc) => check({
              uh_model: 'nash', watershed: {...read.texts, Lc_km: lc},
            }).errors),
            seriesBad: check({rain_source: 'series', values: '1; x'}),
            warned: s.checkInputs(steep, models, {inputs: steep, notices: [slope]}),
            changed: check({}, {inputs: steep, notices: [slope]}),
            otherModel: s.checkInputs({...steep, uh_model: 'clark'}, models,
              {inputs: steep, notices: [slope]}),
            missing: s.readWatershed({name: 'x', cn: 70}).missing,
            areaOnly: s.readWatershed({area_km2: 3}).texts,
            wrapped: s.readWatershed({watershed: example}).values.area_km2,
            lists: [s.PMAXTP_PROBABILITIES, s.PMAXTP_DURATIONS, s.PMAXTP_METHODS],
            fetchOptions: s.pmaxtpOptions(base),
            otherPoint:
              s.toOptions(variant({pmaxtp_latitude: '52,23'})).total_mm ?? null,
            pointBad: check({pmaxtp_latitude: '60'}).errors,
          };
        }""",
        [EXAMPLE, kamiennik_inputs()],
    )
    assert got["kamiennik"] == KAMIENNIK
    assert got["nash"] == {
        **{key: KAMIENNIK[key] for key in KAMIENNIK if key != "tc_method"},
        "watershed": {**SENT, **{name: EXAMPLE[name] for name in LUTZ_BLOCK}},
        "uh_model": "nash",
        "nash_estimation": "lutz",
    }
    assert (got["given"]["nash_n"], got["given"]["nash_k_min"]) == (3.6, 82)
    assert got["given"]["watershed"] == SENT
    assert "tc_method" not in got["snyder"]
    assert got["snyder"]["watershed"] == {**SENT, "Lc_km": 6.76}
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
    assert got["ok"] == {"errors": {}, "warnings": {}}
    assert got["cn"]["errors"] == {"cn": "Najwyżej 100 (podano 150) · maximum"}
    assert got["area"]["errors"] == {
        "area_km2": "Podaj wartość: potrzebna dla modelu SCS · required"
    }
    assert list(got["noModel"]["errors"]) == ["area_km2"]  # a type, nothing required
    assert got["noModel"]["errors"]["area_km2"].endswith(" · type")
    assert got["manualEmpty"]["errors"] == {
        "tc_min": "Podaj wartość: potrzebna dla tc podanego ręcznie · required"
    }
    assert got["lutzMissing"]["errors"] == {
        "Lc_km": "Podaj wartość: potrzebna dla metody Lutza · required"
    }
    assert got["lutzLc"] == [
        {},
        {
            "Lc_km": "Nie może być większa od długości najdłuższej drogi spływu"
            " (15,88 km): tego wymaga metoda Lutza · maximum"
        },
    ]
    assert list(got["seriesBad"]["errors"]) == ["values"]
    # A run's notice stands on its field while the field and the setting are the run's
    assert got["warned"] == {
        "errors": {},
        "warnings": {
            "flow_path_slope_m_per_m": (
                "Poza typowym zakresem od 0,03 do 0,1 (kirpich) · outside_typical_range"
            )
        },
    }
    assert got["changed"]["warnings"] == {}
    assert got["otherModel"]["warnings"] == {}
    assert got["missing"] == ["area_km2"]
    assert got["areaOnly"] == {"area_km2": "3"}
    assert got["wrapped"] == 37.22
    # The GUI offers exactly the probabilities, durations and methods of the atlas
    probabilities, durations, methods = got["lists"]
    assert [float(value) for value in probabilities] == list(
        _pmaxtp.PROBABILITIES_PERCENT
    )
    assert [int(value) for value in durations] == list(_pmaxtp.DURATIONS_MIN)
    assert methods == list(_pmaxtp.METHODS)
    assert got["fetchOptions"] == FETCHED
    assert got["otherPoint"] is None  # the kept depth is the outlet's: fetched again
    assert got["pointBad"] == {"pmaxtp_latitude": "Najwyżej 55 (podano 60) · maximum"}


# --- PMAXTP --------------------------------------------------------------------


def test_pmaxtp_fetches_the_depth_of_the_point_once_and_keeps_it(tab: Tab) -> None:
    # The example typed, its depth not fetched yet: the recorded table answers
    seed_hydrogram(tab, kamiennik_inputs(pmaxtp_fetched=None))
    runs = Runs(tab.page)
    with tab.page.expect_response(lambda answer: PMAXTP in answer.url) as answered:
        tab.open("#hydrogram")
    page = tab.page
    assert answered.value.request.post_data_json == FETCHED
    result = answered.value.json()["result"]
    assert result["depth_mm"] == 101.82
    depth = field(page, "pmaxtp_depth")
    expect(depth).to_have_value("101,82")
    expect(depth).not_to_be_editable()
    source = page.locator(f'{LEFT} [data-field="pmaxtp_depth"] .aux')
    expect(source).to_have_text("PMAXTP IMGW-PIB, metoda POT")
    expect(page.locator(f'{LEFT} [data-attribution="pmaxtp"]')).to_have_text(
        f"{result['attribution']}."
    )
    # The run waits for the depth and takes it: the guide's numbers
    shows(page, "54,20", "6:40", "977 225")
    expect(kpi(page, "c")).to_have_text("0,258")
    assert [run["total_mm"] for run in runs.generate] == [101.82]
    assert page.evaluate(STORED)["pmaxtp_fetched"] == {**FETCHED, "depth_mm": 101.82}

    # A reload shows the kept depth without fetching it again
    page.reload()
    shows(page, "54,20", "6:40", "977 225")
    expect(depth).to_have_value("101,82")
    page.wait_for_timeout(600)
    assert len(runs.pmaxtp) == 1

    # Another probability or method fetches anew
    table = recorded_pmaxtp(PMAXTP_TABLE)["data"]["ks"]
    with page.expect_response(lambda answer: PMAXTP in answer.url) as again:
        field(page, "pmaxtp_probability_pct").select_option("0.5")
    assert again.value.request.post_data_json == {**FETCHED, "probability_percent": 0.5}
    expect(depth).to_have_value(input_text(table["720"]["0.5"]))
    shows_peak(page, {**KAMIENNIK, "total_mm": table["720"]["0.5"]})
    with page.expect_response(lambda answer: PMAXTP in answer.url) as amp:
        field(page, "pmaxtp_method").select_option("AMP")
    assert (amp.value.request.post_data_json or {}).get("method") == "AMP"
    expect(source).to_have_text("PMAXTP IMGW-PIB, metoda AMP")


def test_a_point_outside_the_atlas_or_an_unreachable_imgw_stand_on_their_field(
    tab: Tab,
) -> None:
    import obserwator

    def failing(error: Exception) -> Callable[..., Any]:
        def fetch_pmaxtp(*args: Any, **kwargs: Any) -> Any:
            raise error

        return fetch_pmaxtp

    page = open_hydrogram(tab)
    runs = Runs(page)
    # A latitude outside Poland: an error at once, nothing fetched or run
    field(page, "pmaxtp_latitude").fill("60")
    expect(message(page, "pmaxtp_latitude")).to_have_text(
        "Najwyżej 55 (podano 60) · maximum"
    )
    expect(page.locator(BADGE)).to_have_text("Dane niepełne: pmaxtp_latitude")
    page.wait_for_timeout(600)
    assert runs.pmaxtp == [] and runs.generate == []

    # A point at sea: Obserwator refuses it and the error stands on the latitude
    outside = obserwator.ObserwatorValidationError("outside the PMAXTP grid")
    page.route(PMAXTP_RUN, pmaxtp_route(failing(outside)))
    field(page, "pmaxtp_latitude").fill("54,7")
    expect(message(page, "pmaxtp_latitude")).to_have_text(
        "Punkt poza atlasem PMAXTP: podaj punkt w Polsce, nie na morzu · outside_pmaxtp"
    )
    expect(page.locator(BADGE)).to_have_text("Błąd danych")
    expect(page.locator(f"{LEFT} .calc-state")).to_have_text(
        "Nie pobrano wysokości opadu PMAXTP"
    )
    expect(page.locator(f'{LEFT} [data-retry="pmaxtp"]')).to_have_count(0)
    expect(kpi(page, "q")).to_have_text(re.compile(r"^57,88"))  # the last, marked
    assert runs.generate == []

    # IMGW-PIB unreachable: the error stands on the depth; „Pobierz ponownie” retries
    down = obserwator.ObserwatorConnectionError(
        "timed out", details={"url": "https://imgw.example/", "reason": "timeout"}
    )
    page.route(PMAXTP_RUN, pmaxtp_route(failing(down)))
    field(page, "pmaxtp_latitude").fill("52,23")
    expect(message(page, "pmaxtp_depth")).to_have_text(
        "IMGW-PIB nie odpowiedział na czas: spróbuj ponownie później · timeout"
    )
    page.unroute(PMAXTP_RUN)
    with page.expect_response(lambda answer: PMAXTP in answer.url):
        page.locator(f'{LEFT} [data-retry="pmaxtp"]').click()
    expect(field(page, "pmaxtp_depth")).to_have_value("101,82")
    shows(page, "54,20", "6:40", "977 225")
