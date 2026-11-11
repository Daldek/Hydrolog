"""A subcatchment's panel in „Sieć i trasowanie” (plan 2026-11-10-network-wizard, W4).

A chosen subcatchment made from rainfall opens Hydrogram zlewni's own three steps in a
panel beside „Dane” (D1, D2). The contract of A3 (D11): for each of the 24 model choices
(SCS and Clark with tc given or by each of the six methods, Clark also with R or R/tc;
Nash with n and K given or by Lutz; Snyder) the panel's fields, filled with Kamiennik's
values, are exactly the fields of the saved node, whose runoff holds the choice and the
library reads back; the library reads no field of the watershed the panel does not
show and every one of step 3; the fields the panel marks as needed are exactly those the
library cannot do without, and without nothing else it computes the node. Over every
choice the library reads each field the panel shows but the watershed's name and step
1's descriptive fields of the plan's Q2 (`perimeter_km`, `length_km`,
`elevation_max_m`); Snyder's L and Lc are the copy the mapping declares. Hydrogram
zlewni shows the same fields for the same choice. Kamiennik in Hydrogram zlewni and as
the one subcatchment of a network give the same peak. „Wczytaj z Hydrografa” of the
panel fills the chosen node, which keeps its id, links, position and description, in
one step of the history, and refuses a network. At 1440 px the panel stands beside
„Dane” with a centre of at least 480 px and its ✕ closes it while the node stays
chosen; at 1180 px „Wyniki” takes the panel's place on its button; on a 390 px phone in
the dark theme „Dane” and the panel alternate. The stored node keeps Hydrogram's
inputs, no flat key of the former form.
"""

import copy
import dataclasses
import json
import re
from pathlib import Path
from typing import Any
from unittest import mock

from playwright.sync_api import FloatRect, Page, expect

from hydrolog.exceptions import HydrologError
from hydrolog.morphometry import WatershedParameters
from hydrolog.routing import RoutingNetwork
from hydrolog.routing.runoff import runoff_from_document
from tests.e2e.conftest import (
    KAMIENNIK,
    Tab,
    input_text,
    kamiennik_inputs,
    seed_hydrogram,
)
from tests.e2e.test_siec import BADGE, NODE, SIDEWAYS, canvas_cells
from tests.e2e.test_siec_editor import (
    PANEL,
    SECTION,
    cell_point,
    drag_link,
    drop,
    menu_item,
    said,
    save_document,
    start,
    structure,
    type_network,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
HYDROGRAF = FIXTURES / "handoff_hydrograf.json"
"""Hydrograf's hand-off of one watershed with its PMAXTP rainfall and SCS."""
LEFT = f"{SECTION} .view-panel.left"
RIGHT = f"{SECTION} .view-panel.right"
CENTRE = f"{SECTION} .view-center"
STORED = "() => JSON.parse(localStorage.getItem('hydrolog-gui/siec/3'))"
RUNOFF_VALUES: dict[str, float] = {
    "tc_min": 120.0,
    "clark_r_min": 90.0,
    "clark_r_tc_ratio": 0.5,
    "nash_n": 3.6,
    "nash_k_min": 82.0,
    "snyder_ct": 1.4,
    "snyder_cp": 0.65,
    "ia_coefficient": 0.15,
}
"""The values of the runoff's fields the panel shows, each other than the library's
default, so that the canonical runoff keeps it."""
VALUES: dict[str, Any] = {**KAMIENNIK, **RUNOFF_VALUES}
WATERSHED = {field.name for field in dataclasses.fields(WatershedParameters)}
"""The fields of a watershed (WatershedParameters)."""
TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
MODELS = {"scs": "SCS", "nash": "Nash", "clark": "Clark", "snyder": "Snyder"}
CLARK = {"ratio": "R/tc", "r": "R [min]"}
NASH = {"lutz": "Metoda Lutza", "given": "Podane n i K"}
CHOICES: list[dict[str, str]] = [
    *(
        {"model": model, "tc": tc, **({"clark": kind} if kind else {})}
        for model in ("scs", "clark")
        for tc in ("manual", *TC_METHODS)
        for kind in (("ratio", "r") if model == "clark" else ("",))
    ),
    {"model": "nash", "nash": "given"},
    {"model": "nash", "nash": "lutz"},
    {"model": "snyder"},
]
"""The 24 model choices: SCS and Clark with tc given or by each method, Clark with R/tc
or R; Nash with n and K given or by Lutz; Snyder."""
CHOICE_KEYS = {"model", "uh_model", "amc", "tc_method", "nash_estimation"}
"""The keys of a runoff that are its choices, not fields the panel shows."""
SNYDER_COPIES = {
    "channel_length_km": "snyder_length_km",
    "Lc_km": "snyder_centroid_length_km",
}
"""Snyder's L and Lc: the watershed's fields the mapping copies into the runoff, the one
copy it declares."""
NOT_READ = {"name", "perimeter_km", "length_km", "elevation_max_m"}
"""The fields of step 1 no choice reads: the watershed's name and the descriptive fields
of the plan's Q2 (read by `morphometry watershed`, carried by the hand-off)."""
FIELDS = """(prefix) => {
  const steps = document.getElementById(`${prefix}-uh-label`).closest('.steps');
  const listed = (step) => [...steps.querySelectorAll(
    `[data-step="${step}"] input[type="text"]:not([readonly])`)]
    .map((input) => input.id.slice(prefix.length + 1));
  return { watershed: listed('watershed'), hydrograph: listed('hydrograph') };
}"""
"""The fields a person types in steps 1 and 3 of the steps of ``prefix``, in order."""
NEEDED = """(prefix) => {
  const steps = document.getElementById(`${prefix}-uh-label`).closest('.steps');
  return [...steps.querySelectorAll(
    '[data-step="watershed"] [data-field], [data-step="hydrograph"] [data-field]')]
    .filter((row) => /· required$/.test(
      (row.querySelector('.err .reason') || {}).textContent || ''))
    .map((row) => row.dataset.field);
}"""
"""The fields of steps 1 and 3 whose emptiness the steps mark as missing."""


def typed(value: Any) -> str:
    """Return a value as a person types it into a field."""
    return value if isinstance(value, str) else input_text(value)


def open_panel(tab: Tab) -> Page:
    """Start a network of the guide's rainfall, Z1 flowing into OUT; open Z1's panel."""
    page = start(tab)
    type_network(page, "mouse")
    drop(page, "outlet", (1, 0))
    said(page, "Dodano OUT (wylot).")
    drop(page, "subcatchment", (0, 0))
    said(page, "Dodano Z1 (zlewnia).")
    drag_link(page, "Z1", "OUT")
    said(page, "Połączono Z1 → OUT.")
    expect(page.locator(f"{PANEL} h2")).to_have_text("Zlewnia Z1")
    return page


def choose(page: Page, group: str, label: str) -> None:
    """Click the choice ``label`` of the segmented control labelled by ``group``."""
    page.locator(f'[aria-labelledby="{group}"]').get_by_role(
        "radio", name=label, exact=True
    ).click()


def set_choice(page: Page, prefix: str, choice: dict[str, str]) -> None:
    """Set a model choice in the steps of ``prefix`` ("sn": Sieć's panel, "hg")."""
    choose(page, f"{prefix}-uh-label", MODELS[choice["model"]])
    if "tc" in choice:
        manual = page.locator(f"#{prefix}-tc_manual")
        if choice["tc"] == "manual":
            manual.check()
        else:
            manual.uncheck()
            page.locator(f"#{prefix}-tc_method").select_option(choice["tc"])
    if "clark" in choice:
        choose(page, f"{prefix}-clark-label", CLARK[choice["clark"]])
    if "nash" in choice:
        choose(page, f"{prefix}-nash-source-label", NASH[choice["nash"]])


def library_reads(document: dict[str, Any]) -> set[str]:
    """Return the fields of the watershed the library reads routing ``document``."""
    network = RoutingNetwork.from_document(document)
    read: set[str] = set()
    plain = WatershedParameters.__getattribute__

    def spy(self: WatershedParameters, name: str) -> Any:
        if name in WATERSHED:
            read.add(name)
        return plain(self, name)

    with mock.patch.object(WatershedParameters, "__getattribute__", spy):
        network.route()
    return read


def refusal(document: dict[str, Any]) -> str | None:
    """Return why the library refuses to route ``document``, None when it routes."""
    try:
        RoutingNetwork.from_document(document).route()
    except HydrologError as error:
        return str((error.details or {}).get("reason"))
    return None


def with_node(document: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Return ``document`` with its node of ``node``'s id replaced by it."""
    nodes = [node if item["id"] == node["id"] else item for item in document["nodes"]]
    return {**document, "nodes": nodes}


def without(node: dict[str, Any], names: set[str]) -> dict[str, Any]:
    """Return ``node`` without the fields ``names`` the panel shows.

    A field of the watershed leaves the watershed (with Snyder's copy of it in the
    runoff), any other one the runoff.
    """
    made = copy.deepcopy(node)
    for name in names:
        if name in WATERSHED:
            made["watershed"].pop(name, None)
            made["runoff"].pop(SNYDER_COPIES.get(name, ""), None)
        else:
            made["runoff"].pop(name, None)
    return made


def test_each_model_choice_saves_and_needs_what_the_library_reads(
    tab: Tab, tmp_path: Path
) -> None:
    assert len(CHOICES) == 24
    page = open_panel(tab)
    save = page.locator(f'{LEFT} [data-action="save"]')
    union_shown: set[str] = set()
    union_read: set[str] = set()
    for choice in CHOICES:
        set_choice(page, "sn", choice)
        fields = page.evaluate(FIELDS, "sn")
        names = [*fields["watershed"], *fields["hydrograph"]]
        for name in names:
            page.locator(f"#sn-{name}").fill(typed(VALUES[name]))
        # Every field the choice shows given: the network is complete, not a draft
        expect(save).to_have_attribute("data-draft", "false")
        document = save_document(page, tmp_path / "siec.json")
        for name in names:
            page.locator(f"#sn-{name}").fill("")
        needed = set(page.evaluate(NEEDED, "sn"))

        node = next(item for item in document["nodes"] if item["id"] == "Z1")
        shown = set(names)
        shown_watershed = shown & WATERSHED
        step3_watershed = set(fields["hydrograph"]) & WATERSHED
        copied = set(SNYDER_COPIES) if choice["model"] == "snyder" else set()
        # The node's watershed holds exactly the fields shown, with their values
        assert node["watershed"] == {name: VALUES[name] for name in shown_watershed}
        # Its runoff: the model, the choice and the fields shown, nothing of another
        # model; the library reads it back keeping every field shown
        runoff = node["runoff"]
        assert runoff["model"] == "curve-number"
        assert runoff["uh_model"] == choice["model"]
        assert runoff["amc"] == "II"
        if choice.get("tc") == "manual":
            assert "tc_method" not in runoff
        elif "tc" in choice:
            assert runoff["tc_method"] == choice["tc"]
        if choice.get("nash") == "lutz":
            assert runoff["nash_estimation"] == "lutz"
        shown_runoff = shown - WATERSHED
        assert set(runoff) - CHOICE_KEYS - {SNYDER_COPIES[name] for name in copied} == (
            shown_runoff
        ), choice
        for name, option in SNYDER_COPIES.items():
            if name in copied:
                assert runoff[option] == VALUES[name]
        canonical = runoff_from_document(runoff).to_document()
        assert runoff_from_document(canonical) == runoff_from_document(runoff)
        assert shown_runoff <= set(canonical), choice
        # The library reads no field of the watershed the panel does not show, and every
        # field of the watershed step 3 shows but Snyder's copied L and Lc
        read = library_reads(document)
        assert read <= shown_watershed, choice
        assert step3_watershed - copied <= read, choice
        union_shown |= shown_watershed
        union_read |= read | copied
        # The fields marked needed are enough for the library, and each is needed
        assert needed <= shown, choice
        least = without(node, shown - needed)
        assert refusal(with_node(document, least)) is None, choice
        for name in sorted(needed):
            reason = refusal(with_node(document, without(least, {name})))
            # Clark without R and R/tc is the library's `one_of` (exactly one of them)
            refused = {"missing_field", "required", "one_of"}
            assert reason in refused, (choice, name, reason)
    # Over every choice the library reads each field shown but those of NOT_READ
    assert union_shown - union_read == NOT_READ


def test_hydrogram_zlewni_shows_the_same_fields_for_each_choice(tab: Tab) -> None:
    page = open_panel(tab)
    in_siec = []
    for choice in CHOICES:
        set_choice(page, "sn", choice)
        in_siec.append(page.evaluate(FIELDS, "sn"))
    page.evaluate("() => { location.hash = '#hydrogram'; }")
    expect(
        page.locator('section[data-section="hydrogram"] #hg-uh-label')
    ).to_be_visible()
    in_hydrogram = []
    for choice in CHOICES:
        set_choice(page, "hg", choice)
        in_hydrogram.append(page.evaluate(FIELDS, "hg"))
    assert in_hydrogram == in_siec


def test_kamiennik_alone_and_as_a_networks_subcatchment_gives_one_peak(
    tab: Tab,
) -> None:
    # Hydrogram zlewni: the guide's Kamiennik, 105 mm in 12 h, Beta (2; 5), Δt 10, SCS
    inputs = kamiennik_inputs()
    seed_hydrogram(tab, inputs)
    tab.open("#hydrogram")
    page = tab.page
    alone = page.locator('section[data-section="hydrogram"] [data-kpi="q"] .v')
    expect(alone).to_have_text(re.compile(r"^57,88\s*m³/s$"))
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")
    page.evaluate("() => { location.hash = '#siec'; }")

    # Sieć: the same storm as the network's rainfall, Kamiennik's file in the panel
    page.get_by_role("button", name="Nowa sieć").click()
    step = page.locator(f'{SECTION} [data-step="network"]')
    step.locator("#siec-net-timestep_min").fill("10")
    rain = step.locator('[data-rain-part="siec-net"]')
    rain.get_by_role("radio", name="Hietogram", exact=True).click()
    rain.get_by_role("radio", name="Beta", exact=True).click()
    for name, value in (("total_mm", "105"), ("duration_min", "720")):
        rain.locator(f"#siec-net-{name}").fill(value)
    for name in ("alpha", "beta"):
        rain.locator(f"#siec-net-{name}").fill(inputs[name])
    drop(page, "outlet", (1, 0))
    said(page, "Dodano OUT (wylot).")
    drop(page, "subcatchment", (0, 0))
    said(page, "Dodano Z1 (zlewnia).")
    drag_link(page, "Z1", "OUT")
    said(page, "Połączono Z1 → OUT.")
    panel = page.locator(PANEL)
    with page.expect_file_chooser() as chooser:
        panel.get_by_role("button", name="Plik zlewni…").click()
    chooser.value.set_files(str(FIXTURES / "kamiennik.json"))
    expect(panel.locator("#sn-area_km2")).to_have_value("37,22")
    choose(page, "sn-uh-label", "SCS")
    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    page.get_by_role("radio", name="Tabela węzłów").click()
    cells = page.locator('.node-table tr[data-node-row="Z1"] td')
    expect(cells.nth(3)).to_have_text("57,88")
    outlet = page.locator('.node-table tr[data-node-row="OUT"] td')
    expect(outlet.nth(3)).to_have_text("57,88")
    # The values the run gave stand in the panel while the node is unchanged
    expect(panel.locator('[data-chip="tc"] .v')).not_to_have_text("–")
    expect(panel.locator('[data-calc="ok"]')).to_contain_text("ostatniego obliczenia")


def test_wczytaj_z_hydrografa_fills_the_chosen_node(tab: Tab, tmp_path: Path) -> None:
    page = open_panel(tab)
    description = page.locator(
        '[data-node-form="Z1"] [data-field="description"] textarea'
    )
    description.fill("Kamiennik w Świerzawie")
    description.blur()
    cells = canvas_cells(page)
    before = structure(page)
    panel = page.locator(PANEL)

    def handoff(path: Path) -> None:
        panel.get_by_role("button", name="Wczytaj z Hydrografa").click()
        with page.expect_file_chooser() as chooser:
            page.get_by_role("menuitem").filter(has_text="Plik przekazania").click()
        chooser.value.set_files(str(path))

    # A network is refused, saying the two ways to take it
    network = json.loads(HYDROGRAF.read_text(encoding="utf-8"))
    network["payload"]["nodes"].insert(
        1, {**network["payload"]["nodes"][0], "id": "Z2"}
    )
    network["payload"]["nodes"][-1]["from"] = ["Z1", "Z2"]
    network["payload"]["nodes"].insert(2, {"id": "J1", "type": "junction"})
    network["payload"]["nodes"][2]["from"] = ["Z1", "Z2"]
    network["payload"]["nodes"][-1]["from"] = ["J1"]
    path = tmp_path / "siec.handoff.json"
    path.write_text(json.dumps(network, ensure_ascii=False), encoding="utf-8")
    handoff(path)
    problems = panel.locator('[data-handoff-problems][data-handoff-reader="fill"]')
    expect(problems).to_contain_text("Nie wczytano zlewni")
    expect(problems).to_contain_text("Dodaj zlewnię z Hydrografa")
    expect(panel.locator("#sn-area_km2")).to_have_value("")

    # One watershed fills the node: its watershed, model and own rainfall
    handed = json.loads(HYDROGRAF.read_text(encoding="utf-8"))
    handoff(HYDROGRAF)
    watershed = handed["payload"]["nodes"][0]["watershed"]
    expect(panel.locator("#sn-area_km2")).to_have_value(
        input_text(watershed["area_km2"])
    )
    expect(panel.locator('.handoff[data-origin="Hydrograf"] strong')).to_contain_text(
        "Z Hydrografa"
    )
    expect(
        panel.locator('[aria-labelledby="sn-rain-source-label"] [aria-checked="true"]')
    ).to_have_text("PMAXTP")
    expect(page.locator(f'{SECTION} [data-note="load"] li')).to_have_text(
        [
            f"Wczytano zlewnię Z1 z przekazania „{handed['subject']}” "
            "(Hydrograf 0.5.0.dev0).",
            "Sieć nie podaje kroku czasowego i tak zostaje; przekazanie ma krok 5 min.",
            "Opad przekazania różni się od opadu sieci, więc jest opadem własnym "
            "zlewni Z1.",
        ]
    )
    # The node keeps its id, links, position and description
    assert structure(page) == before
    assert canvas_cells(page) == cells
    expect(description).to_have_value("Kamiennik w Świerzawie")
    # It keeps Hydrogram's inputs, no flat key of the former form
    stored = page.evaluate(STORED)["nodes"]["Z1"]
    assert stored["watershed"]["area_km2"] == input_text(watershed["area_km2"])
    assert not [
        key
        for key in stored
        if key.split(".")[0] in {"watershed", "runoff", "rainfall"} and "." in key
    ]
    # One step of the history
    page.locator('[data-canvas="undo"]').click()
    expect(panel.locator("#sn-area_km2")).to_have_value("")


def box(page: Page, selector: str) -> FloatRect:
    """Return the bounding box of an element that is shown."""
    found = page.locator(selector).bounding_box()
    assert found is not None, selector
    return found


def test_the_panel_stands_beside_dane_and_wyniki_gives_way_when_narrow(
    tab: Tab,
) -> None:
    page = open_panel(tab)
    # 1440 px: Dane, the panel, the centre of at least 480 px and Wyniki side by side
    dane, detail = box(page, LEFT), box(page, PANEL)
    centre, results = box(page, CENTRE), box(page, RIGHT)
    assert dane["x"] < detail["x"] < centre["x"] < results["x"]
    assert centre["width"] >= 480
    assert results["width"] == 340
    assert abs(dane["width"] - detail["width"]) <= 1
    # ✕ closes the panel and the node stays chosen; choosing it opens it again
    page.locator(PANEL).get_by_role("button", name="Zamknij panel", exact=True).click()
    expect(page.locator(PANEL)).to_have_count(0)
    expect(page.locator(NODE.format("Z1"))).to_have_attribute("aria-pressed", "true")
    page.locator(NODE.format("Z1")).click()
    expect(page.locator(PANEL)).to_be_visible()
    # Enter on the subcatchment moves the focus to the panel's first step
    page.locator(NODE.format("OUT")).click()
    expect(page.locator(PANEL)).to_have_count(0)
    page.locator(NODE.format("Z1")).focus()
    page.keyboard.press("Enter")
    expect(page.locator(f'{PANEL} [data-step="watershed"] > summary')).to_be_focused()

    # 1180 px: „Wyniki” gives the panel its place, and its button takes it back
    page.set_viewport_size({"width": 1180, "height": 800})
    expect(page.locator(RIGHT)).to_be_hidden()
    assert box(page, CENTRE)["width"] >= 480
    page.locator(f"{CENTRE} .view-bar .end button").click()
    expect(page.locator(RIGHT)).to_be_visible()
    expect(page.locator(PANEL)).to_be_hidden()
    assert box(page, CENTRE)["width"] >= 480
    page.locator(RIGHT).get_by_role("button", name="Zamknij panel wyników").click()
    expect(page.locator(PANEL)).to_be_visible()
    expect(page.locator(RIGHT)).to_be_hidden()


def test_a_phone_in_the_dark_alternates_dane_and_the_panel(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    tab.open("#siec")
    page = tab.page
    # „Nowa sieć” is in the sheet of „Dane”, which stays open at step 1
    page.get_by_role("button", name="Dane").click()
    page.get_by_role("button", name="Nowa sieć").click()
    type_network(page, "mouse")
    # Escape closes the sheet; the tap on a cell waits until it has slid away
    page.keyboard.press("Escape")
    expect(page.locator(LEFT)).to_be_hidden()
    page.get_by_role("button", name="Dodaj element").click()
    menu_item(page, "subcatchment")
    page.mouse.click(*cell_point(page, (0, 0)))
    said(page, "Dodano Z1 (zlewnia).")
    # Chosen on the canvas, the subcatchment shows its panel's sheet, not „Dane”
    page.locator(NODE.format("Z1")).click()
    expect(page.locator(f"{PANEL}.open")).to_be_visible()
    expect(page.locator(f"{LEFT}.open")).to_have_count(0)
    assert page.evaluate(SIDEWAYS) == []
    # „← Dane” shows „Dane”, „Dane zlewni →” of its step 3 the panel again
    page.locator(PANEL).get_by_role("button", name="← Dane", exact=True).click()
    expect(page.locator(f"{LEFT}.open")).to_be_visible()
    expect(page.locator(f"{PANEL}.open")).to_have_count(0)
    page.locator(f'{LEFT} [data-action="open-panel"]').click()
    expect(page.locator(f"{PANEL}.open")).to_be_visible()
    expect(page.locator(f"{LEFT}.open")).to_have_count(0)
    expect(page.locator(f'{PANEL} [data-step="watershed"] > summary')).to_be_focused()
    assert page.evaluate(SIDEWAYS) == []
