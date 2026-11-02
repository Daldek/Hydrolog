"""„Wszystkie polecenia” (plan D5, D7, D11, D14, D16, D17, slice S2) in Chromium.

Against the real server of ``gui_server`` (its catalog, workers and session files):
the list offers every command the server does (the catalog less ``gui serve``,
``config show`` and ``commands guide``), by group under Polish titles, with the
catalog's Polish summaries; its search folds case and diacritics, and a command is
chosen in the list or by the hash. The forms of ``uh nash`` and ``scs effective``
check the catalog's bounds and the members of the chosen ``one_of`` group before a
run, send only that group, and show the meanings of the allowed values; a library
error without an option stands above the form under the server's Polish title.
Files uploaded through a path option feed a run whose output downloads; a result
exports CSV, JSON, a PNG twice the chart's size and its call (CLI, Python, MCP); the
inputs, not the results, survive a reload until „Wyczyść”; a phone in the dark theme
runs a command through the sheets without scrolling sideways.
"""

import hashlib
import json
import math
import re
import struct
from collections.abc import Callable
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, Response, expect

from hydrolog.catalog import (
    command_schema,
    format_command,
    get_command,
    list_commands,
    parse_command,
)
from tests.e2e.conftest import Tab

FIRST = "uh nash"
"""The command a first visit opens (the mockup's)."""
EXCLUDED = frozenset({"gui serve", "config show", "commands guide"})
"""Commands the server does not offer (plan D5)."""
FLOOD_INFLOW = Path(__file__).resolve().parents[1] / "fixtures" / "flood_inflow.csv"
POL = 'section[data-section="polecenia"]'
"""The section: other sections use the same classes (lists, forms, panels)."""
HEAD = f"{POL} .cmd-form .cmd-head code"
BADGE = ".topbar .badge.status"
RIGHT = f"{POL} .view-panel.right"
HYETOGRAPH = "2,5; 5; 12,5; 15; 8; 4; 3"
"""The third example of ``scs effective``, typed with decimal commas."""
# The list as rendered: each group's heading and the commands under it.
GROUPED = """list => [...list.children].reduce((groups, li) => {
  if (li.classList.contains('cmd-group')) groups.push([li.textContent, []]);
  else if (li.dataset.command) groups.at(-1)[1].push(li.dataset.command);
  return groups;
}, [])"""
OPTION_OF = (
    "fields => fields.map((field) => field.closest('[data-option]').dataset.option)"
)
# What scrolls sideways: the page, or the body of an open sheet.
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""


def entry(command: str) -> dict[str, Any]:
    """Return the catalog entry (commands-1) of ``command``."""
    document: dict[str, Any] = command_schema(get_command(command)).to_dict()
    return dict(document["commands"][0])


def offered(tab: Tab) -> list[str]:
    """Return the names of the commands the server offers (``GET api/commands``)."""
    document = tab.page.request.get(tab.base + "api/commands").json()
    return [item["name"] for item in document["commands"]]


def open_section(tab: Tab, command: str | None = None) -> Page:
    """Open the section (at ``command``'s hash when given) and wait for the form."""
    tab.open(f"#polecenia/{command.replace(' ', '/')}" if command else "#polecenia")
    expect(tab.page.locator(HEAD)).to_have_text(command or FIRST)
    return tab.page


def option(page: Page, name: str) -> Locator:
    """Return the field of the option ``name`` in the form."""
    return page.locator(f'{POL} .cmd-form [data-option="{name}"]')


def number(page: Page, name: str) -> Locator:
    """Return the text box of the option ``name``."""
    return option(page, name).locator("input")


def panes(page: Page) -> Locator:
    """Return the choices of the form's ``one_of`` panes, in catalog order."""
    return page.locator(f'{POL} .cmd-form .one-of [role="radio"]')


def pane_options(page: Page) -> list[str]:
    """Return the options shown in the chosen ``one_of`` pane."""
    shown: list[str] = page.locator(
        f"{POL} .cmd-form .one-of .pane [data-option]"
    ).evaluate_all("fields => fields.map((field) => field.dataset.option)")
    return shown


def run(page: Page) -> Response:
    """Press „Uruchom” and return the server's answer to this section's run."""
    with page.expect_response(
        lambda response: (
            "/api/run/" in response.url and "channel=polecenia" in response.url
        )
    ) as answer:
        page.get_by_role("button", name="Uruchom").click()
    return answer.value


def sent(response: Response) -> dict[str, Any]:
    """Return the options a run sent (its JSON body)."""
    options = response.request.post_data_json
    assert isinstance(options, dict)
    return options


def call(panel: Locator, view: str) -> str:
    """Show the call of a result in ``view`` (``cli``, ``py``, ``mcp``); return it."""
    shown = panel.locator(".cli pre")
    if view != "cli":
        names = {"py": "Python", "mcp": "MCP"}
        panel.locator(".cli-head").get_by_role("radio", name=names[view]).click()
    expect(shown).to_have_attribute("data-view", view)
    expect(shown).to_have_text(re.compile(r"^hydrolog " if view == "cli" else r"\S"))
    return shown.text_content() or ""


def one_line(shown: str) -> str:
    """Join a command line the panel wraps at `` --`` with ``\\``."""
    return shown.replace(" \\\n  ", " ")


def session_files(tab: Tab) -> dict[str, dict[str, Any]]:
    """Return the files of the tab's session by path (``GET api/session``)."""
    document = tab.page.request.get(tab.base + "api/session").json()
    return {item["path"]: item for item in document["files"]}


def download(page: Page, trigger: Locator) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


def as_typed(value: float) -> str:
    """Write a number as the form shows it: the shortest form, a decimal comma."""
    return repr(value).removesuffix(".0").replace(".", ",")


# --- the list ------------------------------------------------------------------


def test_the_list_offers_the_servers_commands_under_polish_titles(tab: Tab) -> None:
    page = open_section(tab)
    names = offered(tab)
    catalog = [item["name"] for item in list_commands().to_dict()["commands"]]
    assert names == [name for name in catalog if name not in EXCLUDED]
    assert len(names) == 43  # 46 commands less the three the GUI leaves out

    items = page.locator(f"{POL} .cmd-list .cmd-item")
    expect(items).to_have_count(len(names))
    # Each command under its group, the groups in catalog order, each with a title
    groups: dict[str, list[str]] = {}
    for name in names:
        groups.setdefault(name.split(" ")[0], []).append(name)
    shown = page.locator(f"{POL} .cmd-list").evaluate(GROUPED)
    assert [(heading.split(" · ")[0], under) for heading, under in shown] == list(
        groups.items()
    )
    assert all(heading.partition(" · ")[2] for heading, _ in shown), shown
    expect(page.locator(f"{POL} .cmd-tools select option")).to_have_count(
        len(groups) + 1
    )
    # The summaries are the catalog's Polish ones, once each command's entry is in
    summaries = [entry(name)["i18n"]["pl"]["summary"] for name in names]
    expect(items.locator("button > span")).to_have_text(summaries)


def test_the_search_folds_case_and_diacritics_and_clearing_restores_the_list(
    tab: Tab,
) -> None:
    page = open_section(tab)
    total = len(offered(tab))
    items = page.locator(f"{POL} .cmd-list .cmd-item")
    expect(items).to_have_count(total)
    search = page.get_by_role("searchbox")

    # A word of one Polish summary in capitals, an English name with a space for its
    # hyphen, the Polish word without its diacritics: each change shows another hit
    for query, hit in (
        ("NIŻÓWEK", "stats low-flow"),
        ("level pool", "route level-pool"),
        ("nizowek", "stats low-flow"),
    ):
        search.fill(query)
        expect(items).to_have_count(1)
        expect(items).to_have_attribute("data-command", hit)
        expect(page.locator(f"{POL} .cmd-list .cmd-group")).to_have_text(
            re.compile(f"^{hit.split(' ')[0]} · ")
        )
    search.fill("zzz-nic-takiego")
    expect(items).to_have_count(0)
    expect(page.locator(f"{POL} .cmd-list .cmd-empty")).to_be_visible()
    search.fill("")
    expect(items).to_have_count(total)

    # A group narrows the list to its commands, and back
    routes = [name for name in offered(tab) if name.startswith("route ")]
    groups = page.locator(f"{POL} .cmd-tools select")
    groups.select_option("route")
    expect(items).to_have_count(len(routes))
    expect(page.locator(f"{POL} .cmd-list .cmd-group")).to_have_count(1)
    groups.select_option("")
    expect(items).to_have_count(total)


def test_a_command_chosen_in_the_list_is_in_the_hash_and_a_hash_opens_it(
    tab: Tab,
) -> None:
    page = open_section(tab)
    lag = page.locator(f'{POL} .cmd-item[data-command="route lag"] button')
    lag.click()
    expect(page.locator(HEAD)).to_have_text("route lag")
    assert page.evaluate("location.hash") == "#polecenia/route/lag"
    expect(lag).to_have_attribute("aria-current", "true")
    expect(page.locator(".crumb-context")).to_contain_text("route lag")

    page.evaluate("location.hash = '#polecenia/scs/effective'")
    expect(page.locator(HEAD)).to_have_text("scs effective")
    expect(
        page.locator(f'{POL} .cmd-item[data-command="scs effective"] button')
    ).to_have_attribute("aria-current", "true")
    expect(lag).not_to_have_attribute("aria-current", "true")

    # A command the server does not offer: its hash opens the last one chosen
    page.evaluate("location.hash = '#polecenia/gui/serve'")
    page.reload()
    expect(page.locator(HEAD)).to_have_text("scs effective")
    expect(page.locator(f'{POL} .cmd-item[data-command="gui serve"]')).to_have_count(0)


# --- uh nash -------------------------------------------------------------------


def test_uh_nash_checks_its_bounds_and_runs_through_the_server(tab: Tab) -> None:
    page = open_section(tab)  # a first visit: uh nash, from its first example
    example = parse_command(entry(FIRST)["examples"][0]["call"])
    for name, value in example.options.items():
        expect(number(page, name)).to_have_value(as_typed(value))
        # numbers are not words: no spell-check underlines
        expect(number(page, name)).to_have_attribute("spellcheck", "false")
    expect(panes(page).first).to_have_attribute("aria-checked", "true")
    assert set(pane_options(page)) == {"n", "k_min"}

    badge = page.locator(BADGE)
    start = page.get_by_role("button", name="Uruchom")
    area = option(page, "area_km2")
    number(page, "area_km2").fill("0")
    expect(area.locator(".err")).to_have_text(
        "Musi być większa od 0 (podano 0) · exclusive_minimum"
    )
    expect(number(page, "area_km2")).to_have_attribute("aria-invalid", "true")
    expect(start).to_be_disabled()
    expect(badge).to_have_attribute("data-state", "invalid")
    number(page, "area_km2").fill("45,3")
    expect(area.locator(".err")).to_have_count(0)
    expect(start).to_be_enabled()

    response = run(page)
    assert response.ok
    assert sent(response) == example.options
    result = response.json()["result"]
    expect(badge).to_have_attribute("data-state", "ok")
    expect(badge).to_have_text("Wynik aktualny")
    right = page.locator(RIGHT)
    # The tiles of the mockup, n, K, t_lag = n·K and q_p, in Polish numbers
    expect(right.locator(".summary .kpi .v")).to_have_text(
        ["3", "30 min", "90 min", "6,797 m³/s na 1 mm"]
    )
    expect(page.locator(f"{POL} .view-center .dtable tbody tr")).to_have_count(
        len(result["times_min"])
    )
    expect(right.locator(".chart svg")).to_be_visible()
    assert one_line(call(right, "cli")) == format_command(FIRST, sent(response))

    # A change makes the result stale; the inputs of the result make it current again
    number(page, "timestep_min").fill("10")
    expect(badge).to_have_attribute("data-state", "stale")
    number(page, "timestep_min").fill("5")
    expect(badge).to_have_attribute("data-state", "ok")


def test_a_library_error_without_an_option_stands_above_the_form(tab: Tab) -> None:
    page = open_section(tab, FIRST)
    lutz_group = entry(FIRST)["one_of"][1]
    start = page.get_by_role("button", name="Uruchom")
    panes(page).nth(1).click()  # Lutz
    # Every member of the chosen group is required, checked when a run is asked for
    start.click()
    invalid = page.locator(f'{POL} .cmd-form [aria-invalid="true"]')
    expect(invalid).to_have_count(len(lutz_group))
    assert set(invalid.evaluate_all(OPTION_OF)) == set(lutz_group)
    expect(invalid.first).to_be_focused()
    expect(start).to_be_disabled()
    lutz = {
        "lutz_length_km": "4",
        "lutz_centroid_length_km": "8,2",  # Lc > L, which only the library checks
        "lutz_slope_m_per_m": "0,023",
        "lutz_manning_n": "0,035",
    }
    for name, text in lutz.items():
        number(page, name).fill(text)

    response = run(page)
    error = response.json()
    assert response.status == 400
    assert "option" not in error["details"]  # nothing for a field to show
    # Only the chosen group is sent: neither n nor k_min of the example
    assert set(sent(response)) == {"area_km2", "timestep_min", *lutz}

    box = page.locator(f"{POL} .cmd-form .form-errors")
    expect(box.locator("strong")).to_have_text(error["title"])  # the server's, Polish
    expect(box.locator("li")).to_have_text(f"{error['message']} (EN)")
    above = box.bounding_box()
    field = page.locator(f"{POL} .cmd-form [data-option]").first.bounding_box()
    assert above is not None and field is not None
    assert above["y"] + above["height"] <= field["y"]
    badge = page.locator(BADGE)
    expect(badge).to_have_attribute("data-state", "error")
    expect(badge).to_have_text("Błąd danych")
    expect(start).to_be_disabled()  # the same data would fail again

    # A change takes the error away; corrected data run
    number(page, "lutz_centroid_length_km").fill("2")
    expect(box).to_have_count(0)
    expect(start).to_be_enabled()
    assert run(page).ok
    expect(badge).to_have_attribute("data-state", "ok")


# --- scs effective -------------------------------------------------------------


def test_scs_effective_under_a_prefix_sends_only_the_chosen_pane(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(prefixed=True)
    page = open_section(tab, "scs effective")
    scs = entry("scs effective")
    groups: list[list[str]] = scs["one_of"]
    members = {name for group in groups for name in group}
    expect(panes(page)).to_have_count(len(groups))
    for index, group in enumerate(groups):
        panes(page).nth(index).click()
        expect(page.locator(f"{POL} .cmd-form .one-of .pane")).to_have_attribute(
            "data-pane", str(index)
        )
        assert set(group) <= set(pane_options(page))
        for name in members - set(group):
            expect(option(page, name)).to_have_count(0)

    # AMC: its allowed values with their meanings, the chosen one's below (the default)
    amc = next(item for item in scs["options"] if item["name"] == "amc")
    meanings = amc["i18n"]["pl"]["enum"]
    values = [item["value"] for item in amc["enum"]]
    field = option(page, "amc")
    choices = field.get_by_role("radio")
    expect(choices).to_have_text(values)
    assert choices.evaluate_all("items => items.map((item) => item.title)") == [
        meanings[value] for value in values
    ]
    default = field.get_by_role("radio", name=amc["default"], exact=True)
    expect(default).to_have_attribute("aria-checked", "true")
    expect(field.locator(".meaning")).to_have_text(
        f"{amc['default']} {meanings[amc['default']]}"
    )
    field.get_by_role("radio", name="III", exact=True).click()
    expect(field.locator(".meaning")).to_have_text(f"III {meanings['III']}")

    # CN above its maximum
    start = page.get_by_role("button", name="Uruchom")
    number(page, "cn").fill("150")
    expect(option(page, "cn").locator(".err")).to_have_text(
        "Najwyżej 100 (podano 150) · maximum"
    )
    expect(start).to_be_disabled()
    number(page, "cn").fill("72")

    # The hyetograph pane: values with decimal commas; the example's total is not sent
    panes(page).nth(groups.index(["values"])).click()
    option(page, "values").locator("textarea").fill(HYETOGRAPH)
    response = run(page)
    assert response.url.startswith(tab.base + "api/run/scs/effective")
    assert sent(response) == {
        "cn": 72,
        "values": [2.5, 5, 12.5, 15, 8, 4, 3],
        "amc": "III",
    }
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(page.locator(f'{RIGHT} .kpi[data-key="cn_adjusted"] .v')).to_have_text(
        str(response.json()["result"]["cn_adjusted"])
    )


# --- files ---------------------------------------------------------------------


def test_uploaded_files_feed_a_run_whose_output_downloads(tab: Tab) -> None:
    page = open_section(tab, "route lag")
    panes(page).nth(1).click()  # the inflow from a file
    source = option(page, "input_file")
    picker = source.locator('input[type="file"]')
    picker.set_input_files(FLOOD_INFLOW)
    expect(source.locator("select")).to_have_value("in/flood_inflow.csv")
    content = FLOOD_INFLOW.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    assert session_files(tab)["in/flood_inflow.csv"] == {
        "path": "in/flood_inflow.csv",
        "size_bytes": len(content),
        "sha256": digest,
    }

    # A Polish file name: folded to what the server takes, its case kept
    picker.set_input_files(
        {"name": "Dopływ Kamiennika.csv", "mimeType": "text/csv", "buffer": content}
    )
    expect(source.locator("select")).to_have_value("in/Doplyw Kamiennika.csv")
    expect(source.locator("select option")).to_have_count(3)  # none, and both files
    assert session_files(tab)["in/Doplyw Kamiennika.csv"]["sha256"] == digest
    expect(number(page, "output")).to_have_value("outflow.csv")  # the example's name

    response = run(page)
    assert sent(response) == {
        "lag_min": 30,
        "input_file": "in/Doplyw Kamiennika.csv",
        "output": "out/outflow.csv",
    }
    right = page.locator(RIGHT)
    link = right.locator(".file-list a")
    expect(link).to_have_count(1)
    name, data = download(page, link)
    assert name == "outflow.csv"
    assert data.decode().splitlines()[0] == "time_min,discharge_m3s"
    written = session_files(tab)["out/outflow.csv"]
    assert hashlib.sha256(data).hexdigest() == written["sha256"]
    # The call names the files as the person gave them
    assert one_line(call(right, "cli")) == format_command(
        "route lag",
        {"lag_min": 30, "input_file": "Doplyw Kamiennika.csv", "output": "outflow.csv"},
    )


# --- exports -------------------------------------------------------------------


def test_a_result_exports_csv_json_png_and_its_call(tab: Tab) -> None:
    tab.page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = open_section(tab, FIRST)
    response = run(page)
    envelope = response.json()
    options = sent(response)
    result = envelope["result"]
    right = page.locator(RIGHT)
    chart = right.locator(".chart svg")
    expect(chart).to_be_visible()
    buttons = right.locator(".export-row button")

    name, data = download(page, buttons.filter(has_text="CSV"))
    assert name == "uh-nash.csv"
    header, *rows = [line.split(",") for line in data.decode().splitlines()]
    assert header == ["times_min", "ordinates_m3s_per_mm"]
    assert [float(row[0]) for row in rows] == result["times_min"]
    assert [float(row[1]) for row in rows] == result["ordinates_m3s_per_mm"]

    name, data = download(page, buttons.filter(has_text="JSON"))
    assert name == "uh-nash.result.json"
    assert json.loads(data) == envelope

    name, data = download(page, buttons.filter(has_text="PNG"))
    assert name == "uh-nash.png"
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    box = chart.bounding_box()
    assert box is not None
    drawn = (math.floor(box["width"] + 0.5), math.floor(box["height"] + 0.5))
    assert struct.unpack(">II", data[16:24]) == (2 * drawn[0], 2 * drawn[1])

    # The command line as shown is copied; it is the options sent, formatted
    shown = call(right, "cli")
    assert one_line(shown) == format_command(FIRST, options)
    assert parse_command(one_line(shown)).options == options
    right.get_by_role("button", name="Kopiuj wywołanie").click()
    expect(page.locator(".toast")).to_have_text("Skopiowano do schowka")
    assert page.evaluate("() => navigator.clipboard.readText()") == shown
    # Python runs as shown and gives the same result; MCP names the tool and options
    namespace: dict[str, Any] = {}
    exec(call(right, "py"), namespace)
    assert json.loads(json.dumps(namespace["result"].to_dict()["result"])) == result
    tool, arguments = call(right, "mcp").split("\n", 1)
    assert tool.endswith(entry(FIRST)["operation_id"])
    assert json.loads(arguments) == options


# --- persistence ---------------------------------------------------------------


def test_the_inputs_survive_a_reload_until_cleared(tab: Tab) -> None:
    page = open_section(tab)
    urban = {"area_km2": "1,3", "urban_effective_precip_mm": "1,305"}
    panes(page).nth(2).click()  # the urban regression
    for name, text in urban.items():
        number(page, name).fill(text)
    number(page, "urban_duration_h").fill("0,167")
    assert run(page).ok
    expect(page.locator(f"{RIGHT} .summary")).to_be_visible()

    page.reload()
    expect(page.locator(HEAD)).to_have_text(FIRST)
    expect(panes(page).nth(2)).to_have_attribute("aria-checked", "true")
    for name, text in urban.items():
        expect(number(page, name)).to_have_value(text)
    expect(page.locator(f"{RIGHT} .summary")).to_have_count(0)  # inputs, no results

    assert run(page).ok
    badge = page.locator(BADGE)
    expect(badge).to_have_attribute("data-state", "ok")
    page.get_by_role("button", name="Wyczyść").click()
    expect(panes(page).first).to_have_attribute("aria-checked", "true")
    expect(number(page, "area_km2")).to_have_value("45,3")  # the example again
    expect(page.locator(f"{RIGHT} .summary")).to_have_count(0)  # its result is gone
    expect(badge).to_be_hidden()
    page.reload()
    expect(panes(page).first).to_have_attribute("aria-checked", "true")
    expect(number(page, "area_km2")).to_have_value("45,3")


# --- a phone -------------------------------------------------------------------


def test_a_phone_in_the_dark_runs_a_command_through_the_sheets(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    page = open_section(tab)
    surface = page.evaluate(
        "() => getComputedStyle(document.documentElement)"
        ".getPropertyValue('--surface').trim()"
    )
    assert surface == "#161b22"  # Nogat's dark surface (tokens.css)
    assert page.evaluate(SIDEWAYS) == []
    left = page.locator(f"{POL} .view-panel.left")
    right = page.locator(RIGHT)

    page.get_by_role("button", name="Dane", exact=True).click()
    expect(left).to_be_visible()
    left.locator('.cmd-item[data-command="scs effective"] button').click()
    expect(page.locator(HEAD)).to_have_text("scs effective")
    expect(left).to_be_visible()  # choosing a command keeps the sheet
    panes(page).nth(1).click()
    option(page, "values").locator("textarea").fill(HYETOGRAPH)
    option(page, "amc").get_by_role("radio", name="III", exact=True).click()
    assert page.evaluate(SIDEWAYS) == []

    left.get_by_role("button", name="Uruchom").click()
    expect(right).to_be_visible()
    expect(left).to_be_hidden()
    expect(right.locator(".summary .kpi").first).to_be_visible()
    expect(right.locator(".chart svg")).to_be_visible()
    expect(right.locator(".cli pre")).to_have_text(re.compile(r"^hydrolog scs"))
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    assert page.evaluate(SIDEWAYS) == []
