"""The hand-off, the Markdown report and the print view (GUI plan D14, D15, slice S6).

Against the real server of ``gui_server``: „Plik przekazania” of Hydrogram zlewni writes
``nogat-handoff/1`` (Nogat's schema, ``schemas/nogat/handoff-1.schema.json``) carrying a
valid ``hydrolog-network/1``, whose outlet through ``route network`` peaks as the run of
``hydrograph generate``; opened again with „Wczytaj z Hydrografa” it gives the same
inputs and result, and written once more the same hand-off. Nogat's own example (D15)
opens from the clipboard with its peak, 60,21 m³/s at 6:20 and 1 046 213 m³; a network
of two subcatchments from Hydrograf opens in Sieć and, computed, shows the producer's
version and result beside Hydrolog's; a refused hand-off lists why. The report downloads
as Markdown from ``report generate``; „Raport do druku” prints on A4 through
``css/print.css`` in the light theme with every part open. The browser's check of a
hand-off judges documents as jsonschema does, and the mapping of Hydrogram's options to
the node computes as ``hydrograph generate`` for every setting.
"""

import copy
import json
import math
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from playwright.sync_api import Locator, Page, expect

import hydrolog
from hydrolog.catalog import run_command
from hydrolog.testing import example_network_document
from tests.e2e.conftest import Tab

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "hydrolog" / "gui" / "web"
HANDOFF: dict[str, Any] = json.loads(
    (ROOT / "schemas" / "nogat" / "handoff-1.schema.json").read_text(encoding="utf-8")
)
NETWORK: dict[str, Any] = json.loads(
    (
        ROOT / "src" / "hydrolog" / "schemas" / "hydrolog-network-1.schema.json"
    ).read_text(encoding="utf-8")
)
ENVELOPE_CHECK = Draft202012Validator(HANDOFF)
NETWORK_CHECK = Draft202012Validator(NETWORK)
D15: dict[str, Any] = HANDOFF["examples"][0]
EXAMPLE = json.loads((WEB / "examples" / "kamiennik.json").read_text(encoding="utf-8"))
RUN = "/api/run/hydrograph/generate"
REPORT = "/api/run/report/generate"
BADGE = ".topbar .badge.status"
HG = 'section.section[data-section="hydrogram"]'
SIEC = 'section.section[data-section="siec"]'
SPACES = re.compile(r"[\s\u00a0\u202f]+")
# Annotations of a JSON Schema: the browser's copy of the envelope leaves them out.
ANNOTATIONS = {"$schema", "$id", "title", "description", "examples"}
# A network of two subcatchments joined below a Muskingum reach, as Hydrograf would join
# the subcatchments of two control points.
TWO: dict[str, Any] = {
    "schema": "hydrolog-network/1",
    "name": "Kamiennik — dwie zlewnie",
    "timestep_min": 10,
    "rainfall": {
        "kind": "design",
        "hietogram_type": "beta",
        "total_mm": 105.0,
        "duration_min": 720.0,
        "alpha": 2.0,
        "beta": 5.0,
    },
    "nodes": [
        {
            "id": "Z1",
            "type": "subcatchment",
            "watershed": {
                "name": "Kamiennik — źródła",
                "area_km2": 20.0,
                "perimeter_km": 22.0,
                "length_km": 8.5,
                "elevation_min_m": 330.0,
                "elevation_max_m": 475.1,
                "mean_slope_m_per_m": 0.09,
                "channel_length_km": 7.9,
                "channel_slope_m_per_m": 0.018,
                "cn": 66,
            },
            "runoff": {"model": "curve-number", "tc_method": "kirpich"},
        },
        {
            "id": "R1",
            "type": "reach",
            "from": ["Z1"],
            "method": "muskingum",
            "k_min": 40,
            "x": 0.2,
        },
        {
            "id": "Z2",
            "type": "subcatchment",
            "watershed": {
                "name": "Zlewnia różnicowa",
                "area_km2": 17.22,
                "perimeter_km": 21.0,
                "length_km": 7.6,
                "elevation_min_m": 257.3,
                "elevation_max_m": 420.0,
                "mean_slope_m_per_m": 0.07,
                "channel_length_km": 6.9,
                "channel_slope_m_per_m": 0.012,
                "cn": 64,
            },
            "runoff": {"model": "curve-number", "tc_method": "kirpich"},
        },
        {"id": "J1", "type": "junction", "from": ["R1", "Z2"]},
        {"id": "OUT", "type": "outlet", "from": ["J1"]},
    ],
}


def flat(text: str | None) -> str:
    """Return ``text`` with its runs of (non-breaking) spaces as one space."""
    return SPACES.sub(" ", text or "").strip()


def shows(page: Page, q: str, tp: str, volume: str) -> None:
    """Wait until Hydrogram's tiles show the peak, the time to peak and the volume."""
    right = f"{HG} .view-panel.right"
    expect(page.locator(f'{right} [data-kpi="q"] .v')).to_have_text(
        re.compile(rf"^{re.escape(q)}\s*m³/s$")
    )
    expect(page.locator(f'{right} [data-kpi="tp"] .v')).to_have_text(
        re.compile(rf"^{re.escape(tp)}\s*h$")
    )
    pattern = r"\s".join(re.escape(part) for part in volume.split(" "))
    expect(page.locator(f'{right} [data-kpi="volume"] .v')).to_have_text(
        re.compile(rf"^{pattern}\s*m³$")
    )
    expect(page.locator(BADGE)).to_have_text("Wynik aktualny")


def open_hydrogram(tab: Tab) -> Page:
    """Open Hydrogram zlewni on a first visit and wait for the Kamiennik result."""
    tab.open("#hydrogram")
    shows(tab.page, "60,21", "6:20", "1 046 213")
    return tab.page


def download(page: Page, trigger: Locator) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


def load_menu(page: Page, section: str) -> None:
    """Open the menu of „Wczytaj z Hydrografa” in a section's panel Dane."""
    page.locator(f"{section} .view-panel.left").get_by_role(
        "button", name="Wczytaj z Hydrografa"
    ).click()


def load_file(page: Page, section: str, path: Path) -> None:
    """Open a hand-off file with „Wczytaj z Hydrografa” → „Plik przekazania…”."""
    load_menu(page, section)
    with page.expect_file_chooser() as chooser:
        page.get_by_role("menuitem").filter(has_text="Plik przekazania").click()
    chooser.value.set_files(str(path))


def handoff_button(page: Page, section: str, which: str) -> Locator:
    """Return „Plik przekazania” (``file``) or „Do schowka” (``copy``) of a section."""
    return page.locator(
        f'{section} .view-panel.right [data-handoff-export] [data-handoff="{which}"]'
    )


def valid(doc: dict[str, Any]) -> None:
    """Check a hand-off against Nogat's schema and its payload against hydrolog's."""
    assert [error.message for error in ENVELOPE_CHECK.iter_errors(doc)] == []
    assert [error.message for error in NETWORK_CHECK.iter_errors(doc["payload"])] == []


def outlet(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the outlet of ``route network`` on ``payload``."""
    result = run_command("route network", {"network": payload}).to_dict()["result"]
    found: dict[str, Any] = next(
        node for node in result["nodes"] if node["id"] == result["outlet"]
    )
    return found


def without_moment(doc: dict[str, Any]) -> dict[str, Any]:
    """Return a hand-off without its ``created_at``."""
    return {key: value for key, value in doc.items() if key != "created_at"}


def compared(page: Page, section: str) -> dict[str, list[str]]:
    """Return the rows of the received producer's result: producer and Hydrolog."""
    rows = page.locator(f'{section} [data-table="handoff-compare"] tbody tr')
    found: dict[str, list[str]] = {}
    for index in range(rows.count()):
        row = rows.nth(index)
        cells = [flat(text) for text in row.locator("td").all_inner_texts()]
        found[row.get_attribute("data-row") or ""] = cells
    return found


def annotations_out(schema: Any, keyword_level: bool = True) -> Any:
    """Return a schema without its annotations (keys of properties and $defs kept)."""
    if isinstance(schema, list):
        return [annotations_out(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    if not keyword_level:
        return {name: annotations_out(item) for name, item in schema.items()}
    return {
        key: annotations_out(item, key not in {"properties", "$defs"})
        for key, item in schema.items()
        if key not in ANNOTATIONS
    }


# --- Hydrogram zlewni: write, read, write again -------------------------------------


def test_a_handoff_of_hydrogram_validates_reopens_and_round_trips(
    new_tab: Any, tmp_path: Path
) -> None:
    tab = new_tab()
    with tab.page.expect_response(lambda answer: RUN in answer.url) as answered:
        page = open_hydrogram(tab)
    envelope = answered.value.json()
    result = envelope["result"]

    name, data = download(page, handoff_button(page, HG, "file"))
    assert name == "Kamiennik — Świerzawa.handoff.json"
    doc = json.loads(data)
    valid(doc)
    assert doc["schema"] == "nogat-handoff/1"
    assert doc["producer"] == {
        "tool": "hydrolog",
        "version": hydrolog.__version__,
        "page": "#hydrogram",
    }
    assert doc["subject"] == "Kamiennik — Świerzawa"
    assert doc["provenance"] == {
        "rainfall": {"source": "pmaxtp", "probability_percent": 1, "duration_min": 720},
        "watershed": {"source": "hydrolog", "file": "examples/kamiennik.json"},
    }
    assert doc["result"] == {
        "command": "hydrograph generate",
        "peak_discharge_m3s": result["peak_discharge_m3s"],
        "time_to_peak_min": result["time_to_peak_min"],
        "total_volume_m3": result["total_volume_m3"],
    }
    payload = doc["payload"]
    assert payload["timestep_min"] == 10
    assert payload["nodes"] == [
        {
            "id": "Z1",
            "type": "subcatchment",
            "watershed": EXAMPLE,
            "runoff": {
                "model": "curve-number",
                "tc_method": "kirpich",
                "amc": "II",
                "uh_model": "scs",
            },
            "rainfall": {
                "kind": "design",
                "hietogram_type": "beta",
                "total_mm": 105,
                "duration_min": 720,
                "alpha": 2,
                "beta": 5,
            },
        },
        {"id": "OUT", "type": "outlet", "from": ["Z1"]},
    ]
    # The payload through `route network` peaks as `hydrograph generate` did
    routed = outlet(payload)
    assert math.isclose(routed["peak_m3s"], result["peak_discharge_m3s"], rel_tol=1e-9)
    assert routed["time_to_peak_min"] == result["time_to_peak_min"]
    assert math.isclose(routed["volume_m3"], result["total_volume_m3"], rel_tol=1e-9)

    # Opened in a new browser: the same inputs, result and hand-off
    saved = tmp_path / name
    saved.write_bytes(data)
    other = new_tab()
    page = open_hydrogram(other)
    load_file(page, HG, saved)
    left = f"{HG} .view-panel.left"
    expect(page.locator(f"{left} .handoff[data-origin]")).to_have_attribute(
        "data-origin", "Hydrolog"
    )
    expect(page.locator(f"{left} .handoff[data-origin] strong")).to_have_text(
        "Z Hydrologa: Kamiennik — Świerzawa"
    )
    version = hydrolog.__version__
    expect(page.locator(".toast")).to_have_text(
        f"Wczytano przekazanie „Kamiennik — Świerzawa” (Hydrolog {version})"
    )
    for field, value in {
        "name": "Kamiennik — Świerzawa",
        "area_km2": "37,22",
        "channel_length_km": "14,78",
        "channel_slope_m_per_m": "0,0142",
        "Lc_km": "6,76",
        "cn": "65",
    }.items():
        expect(page.locator(f"#hg-{field}")).to_have_value(value)
    shows(page, "60,21", "6:20", "1 046 213")
    received = page.locator(f"{HG} [data-handoff-received]")
    expect(received).to_have_attribute("data-handoff-received", "same")
    expect(page.locator(f"{HG} [data-handoff-verdict]")).to_have_attribute(
        "data-handoff-verdict", "ok"
    )
    assert compared(page, HG) == {
        "version": [f"Hydrolog {hydrolog.__version__}"] * 2,
        "q": ["60,21 m³/s", "60,21 m³/s"],
        "tp": ["6:20 h", "6:20 h"],
        "volume": ["1 046 213 m³", "1 046 213 m³"],
    }
    # The comparison fits the panel Wyniki, at its default width and at the narrowest
    # desktop's (1240 px, a panel of 340 px), without its columns scrolling out of sight
    wrap = page.locator(f"{HG} [data-handoff-received] .table-wrap")
    for width in (1440, 1240):
        page.set_viewport_size({"width": width, "height": 900})
        assert wrap.evaluate("(w) => w.scrollWidth <= w.clientWidth"), width
    page.set_viewport_size({"width": 1440, "height": 900})
    again = json.loads(download(page, handoff_button(page, HG, "file"))[1])
    assert without_moment(again) == without_moment(doc)


def test_nogats_example_opens_from_the_clipboard_with_its_peak(tab: Tab) -> None:
    tab.page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = open_hydrogram(tab)
    page.evaluate("(text) => navigator.clipboard.writeText(text)", json.dumps(D15))
    load_menu(page, HG)
    with page.expect_request(
        lambda request: (
            RUN in request.url
            and "Lc_km" not in (request.post_data_json or {})["watershed"]
        )
    ) as sent:
        page.get_by_role("menuitem").filter(has_text="Wklej ze schowka").click()
    node = D15["payload"]["nodes"][0]
    assert sent.value.post_data_json == {
        "watershed": {"name": "Kamiennik — Świerzawa", **node["watershed"]},
        "amc": "II",
        "tc_method": "kirpich",
        "hietogram_type": "beta",
        "total_mm": 105,
        "duration_min": 720,
        "alpha": 2,
        "beta": 5,
        "timestep_min": 10,
        "uh_model": "scs",
    }
    shows(page, "60,21", "6:20", "1 046 213")
    left = f"{HG} .view-panel.left"
    origin = page.locator(f"{left} .handoff[data-origin]")
    expect(origin.locator("strong")).to_have_text(
        "Z Hydrologa: zlewnia punktu 51,0154° N, 15,8900° E"
    )
    expect(origin.locator(".muted")).to_have_text(
        "2 lis 2026, 11:15 · 11 pól · nogat-handoff/1"
    )
    expect(page.locator(f"{left} #hg-area_km2")).to_have_value("37,22")
    expect(page.locator(f"{left} #hg-Lc_km")).to_have_value("")
    expect(page.locator(".crumbs .crumb-context")).to_have_text(
        "Kamiennik — Świerzawa · p 1% · 12 h"
    )
    expect(page.locator(f"{HG} [data-handoff-received]")).to_have_attribute(
        "data-handoff-received", "same"
    )
    assert compared(page, HG) == {
        "version": [f"Hydrolog {hydrolog.__version__}"] * 2,
        "q": ["60,21 m³/s", "60,21 m³/s"],
        "tp": ["6:20 h", "6:20 h"],
        "volume": ["1 046 213 m³", "1 046 213 m³"],
    }
    expect(page.locator(f"{HG} [data-handoff-verdict] li")).to_have_text(
        "Wynik producenta zgodny z wynikiem Hydrologa."
    )

    # „Do schowka” hands it on: the D15 example with this run's result
    handoff_button(page, HG, "copy").click()
    expect(page.locator(".toast")).to_have_text(
        "Skopiowano przekazanie do schowka (nogat-handoff/1)"
    )
    copied = json.loads(page.evaluate("() => navigator.clipboard.readText()"))
    valid(copied)
    assert copied["provenance"] == D15["provenance"]
    assert copied["payload"]["nodes"][0]["runoff"] == node["runoff"]
    assert copied["payload"]["nodes"][0]["rainfall"] == node["rainfall"]
    assert round(copied["result"]["peak_discharge_m3s"], 4) == 60.2148


def test_a_network_of_two_subcatchments_opens_in_siec_beside_hydrografs_result(
    tab: Tab, tmp_path: Path
) -> None:
    expected = outlet(TWO)
    handed: dict[str, Any] = {
        "schema": "nogat-handoff/1",
        "created_at": "2026-11-02T09:30:00Z",
        "producer": {"tool": "hydrograf", "version": "1.4.0", "page": "#analiza"},
        "subject": "Kamiennik — dwie zlewnie",
        "provenance": {
            "rainfall": {
                "source": "pmaxtp",
                "probability_percent": 1,
                "duration_min": 720,
            },
            "watershed": {
                "source": "hydrograf",
                "latitude": 51.0154,
                "longitude": 15.89,
            },
        },
        "payload": TWO,
        "result": {
            "command": "POST /api/network",
            "computed_with": {"tool": "hydrolog", "version": "0.6.3"},
            "peak_discharge_m3s": round(expected["peak_m3s"] - 1.5, 2),
            "time_to_peak_min": expected["time_to_peak_min"],
            "total_volume_m3": round(expected["volume_m3"]),
        },
    }
    valid(handed)
    path = tmp_path / "dwie.handoff.json"
    path.write_text(json.dumps(handed, ensure_ascii=False), encoding="utf-8")
    page = open_hydrogram(tab)
    load_file(page, HG, path)

    expect(page).to_have_url(re.compile(r"#siec$"))
    expect(page.locator("svg.schem g.node")).to_have_count(5)
    expect(page.locator(".toast")).to_have_text(
        "Wczytano przekazanie „Kamiennik — dwie zlewnie” (Hydrograf 1.4.0) "
        "w Sieci i trasowaniu: 5 węzłów"
    )
    left = f"{SIEC} .view-panel.left"
    expect(page.locator(f"{left} [data-network-file]")).to_have_attribute(
        "data-network-file", "Kamiennik — dwie zlewnie.json"
    )
    expect(
        page.locator(f'{left} [data-handoff-source="hydrograf"] strong')
    ).to_have_text("Z Hydrografa: Kamiennik — dwie zlewnie")
    received = page.locator(f"{SIEC} [data-handoff-received]")
    expect(received).to_have_attribute("data-handoff-received", "none")

    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(received).to_have_attribute("data-handoff-received", "same")
    peak = f"{expected['peak_m3s']:.2f}".replace(".", ",")
    assert compared(page, SIEC) == {
        "version": ["Hydrolog 0.6.3", f"Hydrolog {hydrolog.__version__}"],
        "q": [
            f"{handed['result']['peak_discharge_m3s']:.2f}".replace(".", ",") + " m³/s",
            f"{peak} m³/s",
        ],
        "tp": ["5:50 h", "5:50 h"],
        "volume": ["1 051 246 m³", "1 051 246 m³"],
    }
    rows = page.locator(f'{SIEC} [data-table="handoff-compare"] tbody tr')
    expect(rows.locator("xpath=self::*[@class='conflict']")).to_have_count(2)
    expect(page.locator(f"{SIEC} [data-handoff-verdict] li")).to_have_text(
        "Wyniki się różnią: producent liczył wersją Hydrolog 0.6.3, "
        f"ten wynik to Hydrolog {hydrolog.__version__}."
    )

    # Written again from Sieć: the same network, its provenance and Hydrolog's outlet
    name, data = download(page, handoff_button(page, SIEC, "file"))
    assert name == "Kamiennik — dwie zlewnie.handoff.json"
    doc = json.loads(data)
    valid(doc)
    assert doc["payload"] == TWO
    assert doc["provenance"] == handed["provenance"]
    assert doc["producer"] == {
        "tool": "hydrolog",
        "version": hydrolog.__version__,
        "page": "#siec",
    }
    assert doc["result"]["command"] == "route network"
    assert math.isclose(
        doc["result"]["peak_discharge_m3s"], expected["peak_m3s"], rel_tol=1e-9
    )
    assert doc["result"]["time_to_peak_min"] == expected["time_to_peak_min"]


def test_a_refused_handoff_says_why_and_changes_nothing(tab: Tab) -> None:
    page = open_hydrogram(tab)
    runs: list[str] = []
    page.on(
        "request",
        lambda request: runs.append(request.url) if RUN in request.url else None,
    )
    load_menu(page, HG)
    # Without the clipboard's permission the page offers a field to paste into
    page.get_by_role("menuitem").filter(has_text="Wklej ze schowka").click()
    area = page.locator(f"{HG} [data-handoff-paste] textarea")
    expect(area).to_be_focused()
    broken = copy.deepcopy(D15)
    broken["producer"]["tool"] = "Hydrograf"
    broken["payload"]["nodes"][0]["watershed"]["lc_km"] = 6.76
    broken["payload"]["nodes"][0]["watershed"]["cn"] = 150
    area.fill(json.dumps(broken))
    page.locator(f"{HG} [data-handoff-paste]").get_by_role(
        "button", name="Wczytaj"
    ).click()
    problems = page.locator(f"{HG} [data-handoff-problems]")
    expect(problems.locator("strong")).to_have_text("Nie wczytano przekazania")
    expect(problems.locator("li")).to_have_text(
        [
            "producer.tool: niepoprawny zapis",
            "payload.nodes[0] (Z1).watershed.cn: musi być ≤ 100",
            "payload.nodes[0] (Z1).watershed: nieznane pole „lc_km”",
        ]
    )
    # A network document is not a hand-off: the page says where it opens
    load_menu(page, HG)
    page.get_by_role("menuitem").filter(has_text="Wklej ze schowka").click()
    area.fill(json.dumps(example_network_document()))
    page.locator(f"{HG} [data-handoff-paste]").get_by_role(
        "button", name="Wczytaj"
    ).click()
    expect(problems.locator("li")).to_have_text(
        [
            "To nie jest przekazanie nogat-handoff/1 (schema: hydrolog-network/1).",
            (
                "To jest sieć hydrolog-network/1: wczytaj ją w Sieci i trasowaniu "
                "przyciskiem „Plik sieci…”."
            ),
        ]
    )
    expect(
        page.locator(f"{HG} .view-panel.left .handoff[data-origin]")
    ).to_have_attribute("data-origin", "przykład")
    expect(page.locator("#hg-cn")).to_have_value("65")
    assert runs == []
    problems.get_by_role("button", name="Zamknij").click()
    expect(problems).to_have_count(0)


# --- the Markdown report and the print view ----------------------------------------


def test_the_markdown_report_downloads_from_report_generate(tab: Tab) -> None:
    with tab.page.expect_request(lambda request: RUN in request.url) as first:
        page = open_hydrogram(tab)
    options: dict[str, Any] = first.value.post_data_json or {}
    button = page.locator(f"{HG} .view-panel.right .export-row button", has_text="MD")
    expect(button).to_have_text("MDRaport")
    with page.expect_request(lambda request: REPORT in request.url) as asked:
        name, data = download(page, button)
    assert asked.value.post_data_json == {
        **options,
        "output": "out/Kamiennik _ Swierzawa.md",
        "force": True,
    }
    assert name == "Kamiennik _ Swierzawa.md"
    report = data.decode("utf-8")
    assert report.startswith("# Raport Hydrologiczny: Kamiennik — Świerzawa\n")
    assert f"Hydrolog v{hydrolog.__version__}" in report
    assert "60.21" in report
    expect(page.locator(f"{HG} .view-panel.right .file-list a")).to_have_attribute(
        "download", "Kamiennik _ Swierzawa.md"
    )


def test_the_print_view_is_linked_and_fits_a4(new_tab: Any) -> None:
    tab = new_tab(theme="dark")
    page = open_hydrogram(tab)
    link = page.locator('head link[rel="stylesheet"][href="css/print.css"]')
    expect(link).to_have_attribute("media", "print")
    answer = page.request.get(tab.base + "css/print.css")
    assert answer.status == 200
    assert answer.headers["content-type"].startswith("text/css")

    # „Raport do druku”: printed in the light theme with every part open, then put back
    page.evaluate(
        """() => {
          window.printed = [];
          window.print = () => {
            const root = document.documentElement;
            window.printed.push({
              theme: root.dataset.theme ?? null,
              printing: root.dataset.printing ?? null,
              closed: document.querySelectorAll(
                'section.section:not([hidden]) details:not([open])').length,
            });
          };
        }"""
    )
    right = f"{HG} .view-panel.right"
    page.locator(f"{right} .export-row button", has_text="druku").click()
    assert page.evaluate("() => window.printed") == [
        {"theme": "light", "printing": "true", "closed": 0}
    ]
    assert page.evaluate("() => document.documentElement.dataset.theme ?? null") is None
    expect(
        page.locator(f'{right} details[data-part="parameters"]')
    ).not_to_have_attribute("open", "")
    page.goto(tab.base + "#siec")
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    page.locator('[data-export="print"]').click()
    # The same document (only the hash changed): Sieć's „Raport do druku” printed too
    assert (
        page.evaluate("() => window.printed")
        == [{"theme": "light", "printing": "true", "closed": 0}] * 2
    )
    # On paper (A4 less the margins, 703 px): the section in one column, no controls
    page.goto(tab.base + "#hydrogram")
    shows(page, "60,21", "6:20", "1 046 213")
    page.emulate_media(media="print")
    page.set_viewport_size({"width": 703, "height": 1000})
    assert page.evaluate("() => document.documentElement.scrollWidth") <= 703
    for hidden in (
        ".rail",
        ".topbar .top-actions",
        f"{right} .export-row",
        f"{HG} .view-bar",
        f'{right} [data-handoff-export="hydrogram"]',
        SIEC,
    ):
        expect(page.locator(hidden).first).to_be_hidden()
    for shown in (
        ".crumbs",
        f"{HG} .view-center .chart.wide svg",
        f'{right} [data-kpi="q"]',
        f"{right} pre.code",
        f"{HG} .view-panel.left #hg-area_km2",
    ):
        expect(page.locator(shown).first).to_be_visible()
    code = page.locator(f"{right} pre.code")
    assert (
        code.evaluate("(element) => getComputedStyle(element).backgroundColor")
        == "rgba(0, 0, 0, 0)"
    )
    pdf = page.pdf(format="A4")
    pages = re.search(rb"/Count (\d+)", pdf)
    assert pages is not None and 1 <= int(pages.group(1)) <= 8
    box = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", pdf)
    assert box is not None
    assert abs(float(box.group(1)) - 595.3) < 1 and abs(float(box.group(2)) - 841.9) < 1


# --- the pure modules ---------------------------------------------------------------


def test_the_browsers_check_judges_handoffs_as_jsonschema_does(tab: Tab) -> None:
    tab.open("#hydrogram")
    page = tab.page
    copy_of = page.evaluate(
        "async () => (await import('./src/handoff/envelope.js')).ENVELOPE_SCHEMA"
    )
    assert copy_of == annotations_out(HANDOFF)

    def changed(**parts: Any) -> dict[str, Any]:
        doc = copy.deepcopy(D15)
        doc.update(parts)
        return doc

    def without(*keys: str) -> dict[str, Any]:
        return {
            key: value for key, value in copy.deepcopy(D15).items() if key not in keys
        }

    envelopes = [
        D15,
        without("result"),
        changed(producer={"tool": "hydrograf", "version": "0.9.0"}),
        changed(provenance={}),
        changed(created_at="2026-11-02T11:15:00.123+01:00"),
        changed(payload={"schema": "imgw-pmaxtp/1", "depth_mm": 105.0}),
        changed(result={"computed_with": {"tool": "hydrolog", "version": "0.6.3"}}),
        changed(page_title="unknown fields are allowed"),
        *[
            without(key)
            for key in (
                "schema",
                "created_at",
                "producer",
                "subject",
                "provenance",
                "payload",
            )
        ],
        changed(schema="nogat-handoff/2"),
        changed(created_at="2026-11-02T10:15:00"),
        changed(created_at="2026-11-02"),
        changed(producer={"tool": "Hydrolog", "version": "1.0.0"}),
        changed(producer={"tool": "hydrolog"}),
        changed(producer={"tool": "hydrolog", "version": "1.0.0", "page": ""}),
        changed(subject=""),
        changed(provenance={"rainfall": {"probability_percent": 1}}),
        changed(provenance={"Rainfall": {"source": "pmaxtp"}}),
        changed(provenance={"rainfall": "pmaxtp"}),
        changed(provenance={"rainfall": {"source": "PMAXTP"}}),
        changed(payload={"name": "no schema", "nodes": []}),
        changed(payload={"schema": "network"}),
        changed(payload={"schema": "hydrolog-network/0"}),
        changed(payload=[]),
        changed(result={}),
        changed(result={"peak_discharge_m3s": -1.0}),
        changed(result={"peak_discharge_m3s": "60,2"}),
        changed(result={"computed_with": {"tool": "hydrolog"}}),
        changed(result={"command": ""}),
        [],
    ]
    judged = page.evaluate(
        """async (docs) => {
          const { schemaProblems } = await import('./src/handoff/validate.js');
          const { ENVELOPE_SCHEMA } = await import('./src/handoff/envelope.js');
          return docs.map((doc) => schemaProblems(ENVELOPE_SCHEMA, doc).length === 0);
        }""",
        envelopes,
    )
    assert judged == [ENVELOPE_CHECK.is_valid(doc) for doc in envelopes]
    assert judged.count(True) == 8

    base = D15["payload"]

    def network(change: Any) -> dict[str, Any]:
        doc = copy.deepcopy(base)
        change(doc)
        return doc

    payloads = [
        base,
        TWO,
        example_network_document(),
        network(
            lambda doc: doc["nodes"][0].update(
                rainfall={
                    "kind": "series",
                    "depths_mm": [0, 5.5, 12, 3],
                    "timestep_min": 10,
                }
            )
        ),
        network(
            lambda doc: doc["nodes"][0]["runoff"].update(
                uh_model="nash", nash_n=3.2, nash_k_min=41.5
            )
        ),
        network(
            lambda doc: doc["nodes"].insert(
                0,
                {
                    "id": "Ś1",
                    "type": "subcatchment",
                    "times_min": [0, 10],
                    "discharge_m3s": [0, 1.5],
                },
            )
        ),
        network(lambda doc: doc["nodes"][0]["watershed"].update(lc_km=6.76)),
        network(lambda doc: doc["nodes"][0]["watershed"].update(cn=150)),
        network(lambda doc: doc["nodes"][0]["runoff"].update(amc="IV")),
        network(lambda doc: doc["nodes"][0].pop("runoff")),
        network(lambda doc: doc["nodes"][0].update(id="Z 1")),
        network(lambda doc: doc["nodes"][0].update(id="CON")),
        network(lambda doc: doc["nodes"][0].update(type="zlewnia")),
        network(lambda doc: doc["nodes"][0]["rainfall"].update(total_mm=0)),
        network(lambda doc: doc["nodes"][0]["rainfall"].update(kind="file")),
        network(lambda doc: doc.update(timestep_min=0)),
        network(lambda doc: doc.update(extra=True)),
        network(
            lambda doc: doc["nodes"].append(
                {
                    "id": "R1",
                    "type": "reach",
                    "from": ["Z1", "Z1"],
                    "method": "lag",
                    "lag_min": 20,
                }
            )
        ),
        network(
            lambda doc: doc["nodes"].append(
                {"id": "R1", "type": "reach", "from": ["Z1"], "method": "kinematic"}
            )
        ),
        network(
            lambda doc: doc["nodes"].append(
                {"id": "Q1", "type": "subcatchment", "times_min": [0, 10]}
            )
        ),
        network(
            lambda doc: doc["nodes"].append(
                {
                    "id": "Q1",
                    "type": "subcatchment",
                    "times_min": [0],
                    "discharge_m3s": [0],
                    "value_column": "Q1",
                }
            )
        ),
        network(lambda doc: doc.update(nodes=[])),
    ]
    judged = page.evaluate(
        """async ([schema, docs]) => {
          const { schemaProblems } = await import('./src/handoff/validate.js');
          return docs.map((doc) => schemaProblems(schema, doc).length === 0);
        }""",
        [NETWORK, payloads],
    )
    assert judged == [NETWORK_CHECK.is_valid(doc) for doc in payloads]
    assert judged.count(True) == 6


def test_the_mapping_computes_as_hydrograph_generate_for_every_setting(
    tab: Tab,
) -> None:
    tab.open("#hydrogram")
    page = tab.page
    settings: list[dict[str, Any]] = [
        {},
        {"amc": "III", "tc_method": "nrcs"},
        {"tc_manual": True, "tc_min": "150"},
        {"uh_model": "clark", "clark_kind": "ratio", "clark_r_tc_ratio": "0,5"},
        {"uh_model": "clark", "clark_kind": "r", "clark_r_min": "90"},
        {
            "uh_model": "nash",
            "nash_source": "given",
            "nash_n": "3,2",
            "nash_k_min": "41,5",
        },
        {"uh_model": "snyder"},
        {
            "rain_source": "design",
            "total_mm": "80",
            "duration_min": "360",
            "hietogram_type": "triangular",
            "peak_position": "0,4",
        },
        {
            "rain_source": "design",
            "hietogram_type": "block",
            "total_mm": "60",
            "duration_min": "120",
        },
        {
            "rain_source": "pmaxtp",
            "pmaxtp_probability_pct": "0.5",
            "pmaxtp_duration_min": "1440",
            "total_mm": "130",
            "hietogram_type": "euler_ii",
        },
        {
            "rain_source": "series",
            "values": "0; 2,5; 8; 14,5; 6; 1",
            "timestep_min": "15",
        },
        {"ia_coefficient": "0,1", "timestep_min": ""},
    ]
    mapped = page.evaluate(
        """async ([example, settings]) => {
          const state = await import('./src/sections/hydrogram/state.js');
          const mapping = await import('./src/handoff/mapping.js');
          const { buildHandoff } = await import('./src/handoff/handoff.js');
          const watershed = state.readWatershed(example).texts;
          return settings.map((setting) => {
            const start = { ...state.initialState(), watershed, ...setting };
            const inputs = state.normalize(start);
            const options = state.toOptions(inputs);
            const payload = mapping.hydrogramPayload(options, 'Kamiennik');
            const provenance = mapping.hydrogramProvenance(inputs);
            const doc = buildHandoff({
              subject: 'Kamiennik', provenance, payload, version: 'test',
            });
            const opened = state.normalize(mapping.hydrogramInputs(doc));
            return { options, payload, back: state.toOptions(opened) };
          });
        }""",
        [EXAMPLE, settings],
    )
    for setting, item in zip(settings, mapped, strict=True):
        options, payload = item["options"], item["payload"]
        assert [error.message for error in NETWORK_CHECK.iter_errors(payload)] == [], (
            setting
        )
        generated = run_command("hydrograph generate", options).to_dict()["result"]
        routed = outlet(payload)
        assert math.isclose(
            routed["peak_m3s"], generated["peak_discharge_m3s"], rel_tol=1e-9
        ), setting
        assert routed["time_to_peak_min"] == generated["time_to_peak_min"], setting
        assert math.isclose(
            routed["volume_m3"], generated["total_volume_m3"], rel_tol=1e-9
        ), setting
        assert item["back"] == options, setting

    # Nash by Lutz: n and K of `uh nash` travel with the node, Lutz in the provenance
    nash = {"uh_model": "nash"}
    lutz = page.evaluate(
        """async ([example, setting]) => {
          const state = await import('./src/sections/hydrogram/state.js');
          const watershed = state.readWatershed(example).texts;
          const start = { ...state.initialState(), watershed, ...setting };
          return state.lutzOptions(state.normalize(start));
        }""",
        [EXAMPLE, nash],
    )
    parameters = run_command("uh nash", lutz).to_dict()["result"]["parameters"]
    item = page.evaluate(
        """async ([example, setting, parameters]) => {
          const state = await import('./src/sections/hydrogram/state.js');
          const mapping = await import('./src/handoff/mapping.js');
          const { buildHandoff } = await import('./src/handoff/handoff.js');
          const watershed = state.readWatershed(example).texts;
          const start = { ...state.initialState(), watershed, ...setting };
          const inputs = state.normalize(start);
          const options = state.toOptions(inputs, parameters);
          const provenance = mapping.hydrogramProvenance(inputs);
          const payload = mapping.hydrogramPayload(options, 'Kamiennik');
          const doc = buildHandoff({
            subject: 'Kamiennik', provenance, payload, version: 'test',
          });
          const source = mapping.hydrogramInputs(doc).nash_source;
          return { options, provenance, payload, source };
        }""",
        [EXAMPLE, nash, parameters],
    )
    assert item["provenance"]["runoff"] == {
        "source": "hydrolog",
        "command": "uh nash",
        "method": "lutz",
    }
    assert item["payload"]["nodes"][0]["runoff"]["nash_n"] == parameters["n"]
    assert item["source"] == "lutz"
    generated = run_command("hydrograph generate", item["options"]).to_dict()["result"]
    assert math.isclose(
        outlet(item["payload"])["peak_m3s"],
        generated["peak_discharge_m3s"],
        rel_tol=1e-9,
    )
