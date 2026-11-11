"""The pure JavaScript modules of the GUI (plan D9, D11, D16, slice S2) in Chromium.

No Node toolchain (D17): each test opens the page of the real server and imports
the modules there. ``format.js`` writes Polish numbers (D9); ``forms/model.js``
turns REAL catalog documents (fetched from ``api/commands``) into fields, checks
and the options of a run, and honours ``requires``, ``excludes``, ``section`` and
``format`` (D11) on a fixture command, as Hydrolog's catalog has none; catalog
examples go through the form to ``api/run`` and run. ``router.js``,
``persist.js``, ``labels/errors.js`` and ``labels/notices.js`` (on errors of the
real server), ``ui/info.js``, Polecenia's ``state.js`` and
``forms/result-view.js`` (on real envelopes) follow. The geometry of Sieć's canvas
(plan 2026-11-10-network-editor, D5, D6, D10: ``editor/geometry.js``) draws rule D
and ranks the lines as the library does, computed here in Python, also on the document
of the structure alone that Sieć sends Hydrolog to lay out (``state.js``'
``structureDocument``, ADR-0025: only positive areas weigh), and its edits
(``editor/edits.js``) share the nodes they do not change. Sieć's editor follows:
``editor/graph.js`` reports every structure reason with the library's details, judges
links and ids, and finds the problem ``RoutingNetwork.from_document`` raises on each
document of a one-problem corpus; ``editor/edits.js``' new edits (add, connect, a
junction, remove, rename, describe), ``editor/history.js``, the hints of
``editor/geometry.js`` and ``words.js`` are checked on small networks. The rainfall of
Hydrogram's step 2 and of Sieć's network (plan 2026-11-10-network-wizard, D4) goes from
``rainfall`` of hydrolog-network/1 to the step's inputs and back (``mapping.js``'
``rainfallInputs``, ``rainfallOf``), and ``RainStep`` shows a subcatchment's „Jak w
sieci” with the network's time step read-only. A subcatchment made from rainfall goes to
Hydrogram's inputs and back (``subcatchmentInputs``, ``subcatchmentNode``; D3): the
inputs of each model choice, the guide's subcatchments and a hand-off's. The origin
of each node (D9) follows Nogat's precedence (``nodeOrigins``, a key of no node left
out and said) and is written again by Sieć under the current ids with the changes
marked (``siecNodeProvenance``), renamed, edited, drawn and added nodes included.
"""

import json
import math
import random
from typing import Any

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import (
    Hydrograph,
    MuskingumCungeReach,
    MuskingumReach,
    RoutingNetwork,
    structure_schematic,
)
from hydrolog.routing._layout import edge_route, layout
from hydrolog.testing import example_network_document
from tests.e2e.conftest import FIXTURES, Tab, kamiennik_inputs
from tests.e2e.test_siec import as_written
from tests.e2e.test_siec_subcatchment import CHOICES, RUNOFF_VALUES
from tests.unit._network_documents import STRUCTURE_CORPUS
from tests.unit._schematic_checks import random_tree

NBSP = "\u00a0"
MINUS = "\u2212"
EN = " (EN)"
INVALID = "Nieprawidłowe dane wejściowe"
# Imported before every body; `doc(name)` fetches a command's catalog document,
# `run(name, options)` posts a run and gives {status, body}.
PRELUDE = """
const f = await import('./src/format.js');
const m = await import('./src/forms/model.js');
const router = await import('./src/router.js');
const persist = await import('./src/persist.js');
const errors = await import('./src/labels/errors.js');
const notices = await import('./src/labels/notices.js');
const info = await import('./src/ui/info.js');
const state = await import('./src/sections/polecenia/state.js');
const rv = await import('./src/forms/result-view.js');
const path = (name) => name.replaceAll(' ', '/');
const doc = async (name) => (await fetch(`api/commands/${path(name)}`)).json();
const run = async (name, options) => {
  const response = await fetch(`api/run/${path(name)}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(options),
  });
  return {status: response.status, body: await response.json()};
};
const nan = (value) => (Number.isNaN(value) ? 'NaN' : value);
"""
# A command of the commands-1 shape with the optional fields of the platform plan
# (item 8): `requires`, `excludes`, `section` and `format`.
FIXTURE = """
const fixture = {schema: 'hydrolog-commands/1', commands: [{
  name: 'demo period',
  options: [
    {name: 'value', type: 'number', required: true},
    {name: 'start', type: 'string', format: 'date', section: 'Okres',
     requires: ['end']},
    {name: 'end', type: 'string', format: 'date', section: 'Okres'},
    {name: 'stamp', type: 'string', format: 'date-time'},
    {name: 'all_nodes', type: 'boolean', default: false, excludes: ['nodes']},
    {name: 'nodes', type: 'array', items: 'string', section: 'Węzły'},
  ],
}]};
"""


@pytest.fixture
def page(tab: Tab) -> Any:
    """Return the GUI's page (the tab checks console errors and the CSP)."""
    tab.open()
    return tab.page


def js(page: Any, body: str) -> Any:
    """Evaluate ``body`` (statements ending in ``return``) after ``PRELUDE``."""
    return page.evaluate(f"async () => {{ {PRELUDE} {body} }}")


# --- format.js ---------------------------------------------------------------


def test_numbers_are_written_in_polish_and_read_back(page: Any) -> None:
    got = js(
        page,
        """return {
          num: [f.num(1234.5), f.num(12345.678), f.num(-1234567.5, 1),
                f.num(-3.5, 1), f.num(-0.001, 1), f.num(0.004, 2), f.num(null),
                f.num(NaN), f.num(Infinity)],
          auto: [f.auto(30), f.auto(12345), f.auto(1046213.2), f.auto(60.2148),
                 f.auto(0.26778), f.auto(0.0001234), f.auto(-12.3456),
                 f.auto(9999.5)],
          back: [-1234567.25, 12345.678, -0.5, 0.0142]
            .map((v) => f.parseNumber(f.num(v, 4))),
          input: [f.inputText(0.0142), f.inputText(12345.5), f.inputText(undefined)],
          inputBack: [-1.5, 12345.5, 1e-7].map((v) => f.parseNumber(f.inputText(v))),
        };""",
    )
    # A separator between thousands from five digits only, the minus sign U+2212,
    # no "−0,0" for a negative rounded to zero, a dash for what is not a number.
    assert got["num"] == [
        "1234,50",
        f"12{NBSP}345,68",
        f"{MINUS}1{NBSP}234{NBSP}567,5",
        f"{MINUS}3,5",
        "0,0",
        "0,00",
        "–",
        "–",
        "–",
    ]
    # Whole numbers whole, otherwise four significant digits.
    assert got["auto"] == [
        "30",
        f"12{NBSP}345",
        f"1{NBSP}046{NBSP}213",
        "60,21",
        "0,2678",
        "0,0001234",
        f"{MINUS}12,35",
        f"10{NBSP}000",
    ]
    # What the GUI writes, a person can paste back into a field.
    assert got["back"] == [-1234567.25, 12345.678, -0.5, 0.0142]
    assert got["input"] == ["0,0142", "12345,5", ""]
    assert got["inputBack"] == [-1.5, 12345.5, 1e-7]


def test_typed_numbers_take_a_comma_or_a_dot_and_junk_is_refused(page: Any) -> None:
    got = js(
        page,
        """return [
          '1 234,5', '1\\u00a0234,5', '12\\u202f345', '1.5', '\\u22123,5', '+2', ',5',
          '1e3', '', '   ', null, 7,
          '1,2,3', '1.234,5', '12 mm', 'abc', '--1', '1.2.3', 'e3', Infinity,
        ].map((text) => nan(f.parseNumber(text)));""",
    )
    assert got[:12] == [
        1234.5,
        1234.5,
        12345,
        1.5,
        -3.5,
        2,
        0.5,
        1000,
        None,
        None,
        None,
        7,
    ]
    assert got[12:] == ["NaN"] * 8


def test_times_sizes_plurals_and_search_folding(page: Any) -> None:
    got = js(
        page,
        """const files = ['plik', 'pliki', 'plików'];
        return {
          hmm: [380, 59.6, 5, 0, -90, NaN].map(f.hmm),
          bytes: [0, 1023, 1024, 1048576, 1234567, 12345678].map(f.bytes),
          plural: [0, 1, 2, 4, 5, 11, 12, 14, 21, 22, 24, 25, 102, 112, 10002]
            .map((n) => f.plural(n, files)),
          fold: [f.fold('Łódź ŻÓŁW Gęś'), f.fold('Śnieżka Źródło')],
        };""",
    )
    assert got["hmm"] == ["6:20", "1:00", "0:05", "0:00", f"{MINUS}1:30", "–"]
    assert got["bytes"] == ["0 B", "1023 B", "1,0 kB", "1,0 MB", "1,2 MB", "11,8 MB"]
    assert got["plural"] == [
        "0 plików",
        "1 plik",
        "2 pliki",
        "4 pliki",
        "5 plików",
        "11 plików",
        "12 plików",
        "14 plików",
        "21 plików",
        "22 pliki",
        "24 pliki",
        "25 plików",
        "102 pliki",
        "112 plików",
        f"10{NBSP}002 pliki",
    ]
    assert got["fold"] == ["lodz zolw ges", "sniezka zrodlo"]


# --- forms/model.js on the real catalog ---------------------------------------


def test_fields_and_panes_of_real_commands(page: Any) -> None:
    got = js(
        page,
        """const pick = (model, ...names) => Object.fromEntries(model.fields
          .filter((x) => names.includes(x.name))
          .map((x) => [x.name, {kind: x.kind, unit: x.unitLabel, required: x.required,
            min: x.min, max: x.max, above: x.exclusiveMinimum, groups: x.groups,
            member: x.member, defaultText: x.defaultText, choices: x.choices}]));
        const panes = (model) => model.groups.map((g) => [g.id, g.title, g.names]);
        const one = (model) => ({title: model.oneOf.title, chosen: model.oneOf.chosen,
          groups: model.oneOf.groups.map((g) => [g.label, g.names])});
        const nash = m.fieldModel(await doc('uh nash'));
        const scs = m.fieldModel(await doc('scs effective'));
        const lag = m.fieldModel(await doc('route lag'));
        const net = m.fieldModel(await doc('route network'));
        const musk = m.fieldModel(await doc('route muskingum'));
        const flood = m.fieldModel(await doc('stats flood-frequency'));
        return {
          nash: [pick(nash, 'area_km2', 'lutz_urban_pct', 'urban_fraction',
                      'timestep_min'), panes(nash), one(nash)],
          scs: [pick(scs, 'values', 'input_file', 'value_column', 'amc',
                     'ia_coefficient'), panes(scs), one(scs)],
          lag: [pick(lag, 'output', 'force'), panes(lag), one(lag)],
          net: [pick(net, 'network', 'nodes', 'output_dir'), panes(net)],
          musk: pick(musk, 'subreaches'),
          flood: [pick(flood, 'distribution', 'dates', 'return_periods',
                       'date_column'), one(flood)],
        };""",
    )
    fields, panes, one_of = got["nash"]
    assert fields["area_km2"] == {
        "kind": "number",
        "unit": "km²",
        "required": True,
        "min": None,
        "max": None,
        "above": 0,
        "groups": [],
        "member": False,
        "defaultText": None,
        "choices": [],
    }
    # lutz_* options outside every group go with the Lutz group, urban_* with the
    # urban one; neither is required there.
    lutz = fields["lutz_urban_pct"]
    assert (lutz["unit"], lutz["min"], lutz["max"]) == ("%", 0, 100)
    assert (lutz["groups"], lutz["member"]) == ([1], False)
    assert (fields["urban_fraction"]["groups"], fields["urban_fraction"]["member"]) == (
        [2],
        False,
    )
    assert fields["timestep_min"]["defaultText"] == "5"
    assert one_of["title"] == "Grupa parametrów" and one_of["chosen"] == 0
    assert [label for label, _ in one_of["groups"]] == [
        "n i K",
        "Lutz",
        "Regresja miejska",
    ]
    assert one_of["groups"][1][1][-2:] == ["lutz_urban_pct", "lutz_forest_pct"]
    # Optional options without a default go into „Opcje dodatkowe”.
    assert panes == [
        ["main", None, ["area_km2", "#one_of", "timestep_min"]],
        ["more", "Opcje dodatkowe", ["rainfall_duration_min", "total_duration_min"]],
    ]

    fields, panes, one_of = got["scs"]
    assert (fields["values"]["kind"], fields["values"]["unit"]) == ("series", "mm")
    assert fields["values"]["min"] == 0
    assert fields["input_file"]["kind"] == "file-in"
    # A file's column goes with the group holding input_file.
    assert (fields["value_column"]["groups"], fields["value_column"]["member"]) == (
        [2],
        False,
    )
    amc = fields["amc"]
    assert (amc["kind"], amc["defaultText"]) == ("choice", "II")
    assert amc["choices"] == [
        {"value": "I", "meaning": "Sucho przed opadem; CN obniżone."},
        {"value": "II", "meaning": "Przeciętna wilgotność; CN bez zmian."},
        {"value": "III", "meaning": "Mokro przed opadem; CN podwyższone."},
    ]
    assert fields["ia_coefficient"]["defaultText"] == "0,2"
    assert panes == [["main", None, ["cn", "#one_of", "amc", "ia_coefficient"]]]
    assert one_of["title"] == "Opad"
    assert one_of["groups"] == [
        ["Suma", ["precipitation_mm"]],
        ["Hietogram", ["values"]],
        ["Plik", ["input_file", "value_column"]],
    ]

    fields, panes, one_of = got["lag"]
    assert fields["output"]["kind"] == "file-out"
    assert fields["force"]["kind"] == "boolean"
    assert panes == [
        ["main", None, ["lag_min", "#one_of", "output", "force", "check"]],
        ["more", "Opcje dodatkowe", ["initial_outflow_m3s", "extend_min"]],
    ]
    assert one_of["groups"] == [
        ["Szereg", ["times_min", "discharge_m3s"]],
        ["Plik", ["input_file", "time_column", "value_column"]],
    ]

    fields, panes = got["net"]
    assert [fields[name]["kind"] for name in ("network", "nodes", "output_dir")] == [
        "json",
        "chips",
        "file-out",
    ]
    assert panes[1] == [
        "more",
        "Opcje dodatkowe",
        ["inflows_file", "time_column", "nodes", "main_stem"],
    ]

    subreaches = got["musk"]["subreaches"]
    assert (subreaches["kind"], subreaches["min"]) == ("integer", 1)

    fields, one_of = got["flood"]
    distribution = fields["distribution"]
    assert distribution["kind"] == "choice" and len(distribution["choices"]) == 5
    assert distribution["choices"][2] == {
        "value": "gev",
        "meaning": "Uogólniony rozkład wartości ekstremalnych (GEV).",
    }
    assert fields["dates"]["kind"] == "chips"
    periods = fields["return_periods"]
    assert (periods["kind"], periods["above"]) == ("series", 1)
    assert periods["defaultText"] == "2; 5; 10; 20; 50; 100; 500; 1000"
    assert fields["date_column"]["groups"] == [1]
    assert one_of["groups"] == [
        ["Wartości", ["values"]],
        ["Plik", ["input_file", "value_column", "date_column"]],
    ]


def test_validation_of_real_commands(page: Any) -> None:
    got = js(
        page,
        """const nashDoc = await doc('uh nash');
        const scsDoc = await doc('scs effective');
        const nash = m.fieldModel(nashDoc);
        const lutz = m.fieldModel(nashDoc, {values: {'#one_of': 1}});
        const scs = m.fieldModel(scsDoc, {values: {'#one_of': 1}});
        const musk = m.fieldModel(await doc('route muskingum'));
        const lag = m.fieldModel(await doc('route lag'));
        const net = m.fieldModel(await doc('route network'));
        const lutzValues = {area_km2: '45,3', lutz_length_km: '8,2',
          lutz_centroid_length_km: '4,5', lutz_slope_m_per_m: '0,023',
          lutz_manning_n: '0,035'};
        return {
          nash: m.validate(nash, {area_km2: '0', n: '3', k_min: '', timestep_min: 'abc',
            rainfall_duration_min: '-1', lutz_urban_pct: '150'}),
          nashEdge: m.validate(nash, {area_km2: '0,001', n: '0.5', k_min: '30'}),
          lutz: m.validate(lutz, {...lutzValues, n: 'abc', lutz_urban_pct: '150',
            lutz_forest_pct: '-1'}),
          lutzEdge: m.validate(lutz, {...lutzValues, lutz_urban_pct: '100',
            lutz_forest_pct: '0'}),
          scs: m.validate(scs, {cn: '101', precipitation_mm: 'abc',
            values: '2,5; 5; -1', amc: 'IV'}),
          scs2: m.validate(scs, {cn: '0,5', values: '2,5; x; 3', amc: 'III'}),
          scsEdge: m.validate(scs, {cn: '100', values: '0.29,0.84,1'}),
          scsEmpty: m.validate(scs, {cn: '1', values: ''}),
          musk: m.validate(musk, {k_min: '40', x: '0,6', subreaches: '1,5',
            times_min: '0; 10', discharge_m3s: '1; 2'}),
          musk2: m.validate(musk, {k_min: '40', x: '0,5', subreaches: '0',
            times_min: '0; 10', discharge_m3s: '1; 2'}),
          lag: m.validate(lag, {lag_min: '30', times_min: '0; 10',
            discharge_m3s: '1; 2', output: '../x.csv'}),
          net: [m.validate(net, {network: '[1]'}).network,
                m.validate(net, {network: '{'}).network],
        };""",
    )
    assert got["nash"] == {
        "area_km2": "Musi być większa od 0 (podano 0) · exclusive_minimum",
        "k_min": "Podaj wartość: opcja wymagana · required",
        "timestep_min": "Podaj liczbę, np. 14,78 · type",
        "rainfall_duration_min": (
            "Musi być większa od 0 (podano -1) · exclusive_minimum"
        ),
    }  # lutz_urban_pct belongs to a group not chosen: not checked
    assert got["nashEdge"] == {}
    assert got["lutz"] == {
        "lutz_urban_pct": "Najwyżej 100 (podano 150) · maximum",
        "lutz_forest_pct": "Najmniej 0 (podano -1) · minimum",
    }
    assert got["lutzEdge"] == {}
    assert got["scs"] == {
        "cn": "Najwyżej 100 (podano 101) · maximum",
        "values": "Wartość 3: Najmniej 0 (podano -1) · minimum",
        "amc": "Dozwolone wartości: I, II, III · choice",
    }
    assert got["scs2"] == {
        "cn": "Najmniej 1 (podano 0,5) · minimum",
        "values": "Wartość 2 („x”) nie jest liczbą · type",
    }
    assert got["scsEdge"] == {}
    assert got["scsEmpty"] == {"values": "Podaj wartość: opcja wymagana · required"}
    assert got["musk"] == {
        "x": "Najwyżej 0,5 (podano 0,6) · maximum",
        "subreaches": "Podaj liczbę całkowitą · type",
    }
    assert got["musk2"] == {"subreaches": "Najmniej 1 (podano 0) · minimum"}
    assert got["lag"] == {
        "output": "Nazwa pliku: litery, cyfry, kropka, myślnik, podkreślenie lub "
        "spacja, do 128 znaków · invalid_path"
    }
    wrong_kind, broken = got["net"]
    assert wrong_kind == "Oczekiwano obiektu JSON · type"
    assert broken.startswith("Nieprawidłowy JSON: ") and broken.endswith(" · type")


def test_options_sent_by_a_form(page: Any) -> None:
    got = js(
        page,
        """const scsDoc = await doc('scs effective');
        const scs = m.fieldModel(scsDoc, {values: {'#one_of': 1}});
        const lag = m.fieldModel(await doc('route lag'), {values: {'#one_of': 1}});
        const net = m.fieldModel(await doc('route network'));
        return [
          m.toOptions(scs, {cn: '72', precipitation_mm: '50',
            values: '2,5; 5\\t12,5\\n3', input_file: 'in/a.csv', amc: 'III',
            ia_coefficient: ''}),
          m.toOptions(lag, {lag_min: '30', times_min: '0;10',
            input_file: 'in/flood.csv', time_column: ' t ', output: ' out.csv ',
            force: true, check: false, extend_min: ''}),
          m.toOptions(net, {network: '{"schema": "hydrolog-network/1", "nodes": []}',
            nodes: ['OUT', 'J1'], main_stem: [], force: false}),
        ];""",
    )
    # Typed text becomes numbers, only the chosen group is sent, empty optionals
    # and booleans at their default are left out, output files go under out/.
    assert got == [
        {"cn": 72, "values": [2.5, 5, 12.5, 3], "amc": "III"},
        {
            "lag_min": 30,
            "input_file": "in/flood.csv",
            "time_column": "t",
            "output": "out/out.csv",
            "force": True,
        },
        {
            "network": {"schema": "hydrolog-network/1", "nodes": []},
            "nodes": ["OUT", "J1"],
        },
    ]


def test_a_new_form_holds_only_the_names_of_required_outputs(page: Any) -> None:
    got = js(
        page,
        """const outputs = m.fieldModel(await doc('route network')).fields
          .filter((x) => x.kind === 'file-out').map(m.defaultOutputName);
        return {
          outputs,
          fallback: m.defaultOutputName({name: 'report', examples: []}),
          defaults: [m.outputDefaults(m.fieldModel(await doc('route lag'))),
                     m.outputDefaults(m.fieldModel(await doc('uh nash'))),
                     m.outputDefaults(m.fieldModel(await doc('soil hsg')))],
        };""",
    )
    assert got["outputs"] == ["network_out", "network.svg"]
    assert got["fallback"] == "report"
    # No example value: an optional output stays empty, a required one gets its name
    assert got["defaults"] == [{}, {}, {"output": "hsg.tif"}]


def test_requires_excludes_sections_and_dates_of_a_fixture_command(page: Any) -> None:
    got = js(
        page,
        FIXTURE
        + """const base = m.fieldModel(fixture);
        const ticked = m.fieldModel(fixture, {values: {all_nodes: true}});
        const unticked = m.fieldModel(fixture, {values: {all_nodes: false}});
        const nodes = (model) => model.fields.find((x) => x.name === 'nodes');
        const check = (values) => m.validate(base, {value: '1', ...values});
        return {
          panes: base.groups.map((g) => [g.id, g.title, g.names]),
          requires: [check({start: '2024-02-29'}),
                     check({start: '2024-01-01', end: '2024-12-31'}),
                     check({end: '2024-12-31'})],
          dates: [check({start: '2023-02-29', end: '2024-13-01'}),
                  check({start: '2024-1-5', end: '2024-02-30'})],
          stamps: ['2024-05-01T12:30', '2024-05-01 23:59:59.5+02:00',
                   '2024-05-01T12:30Z', '2024-05-01', '2024-05-01T24:00',
                   '2024-05-01T12:60', '2024-02-30T10:00']
            .map((stamp) => check({stamp}).stamp || null),
          ticked: [nodes(ticked).disabledBy, m.isActive(ticked, nodes(ticked)),
                   m.validate(ticked, {value: '1', all_nodes: true}),
                   m.toOptions(ticked, {value: '1', all_nodes: true, nodes: ['A']})],
          both: check({all_nodes: true, nodes: ['A', 'B']}),
          unticked: [nodes(unticked).disabledBy,
                     m.validate(unticked, {value: '1', all_nodes: false,
                                           nodes: ['A']}),
                     m.toOptions(unticked, {value: '1', all_nodes: false,
                                            nodes: ['A']})],
        };""",
    )
    # Named sections stand as their own groups, between the main one and
    # „Opcje dodatkowe”, in catalog order.
    assert got["panes"] == [
        ["main", None, ["value", "all_nodes"]],
        ["Okres", "Okres", ["start", "end"]],
        ["Węzły", "Węzły", ["nodes"]],
        ["more", "Opcje dodatkowe", ["stamp"]],
    ]
    # A given option asks for its partners; the partner alone asks for nothing.
    assert got["requires"] == [
        {
            "start": "Podaj też: end · requires",
            "end": "Podaj wartość: opcja wymagana · required",
        },
        {},
        {},
    ]
    date = "Podaj datę w formacie RRRR-MM-DD · format"
    assert got["dates"] == [{"start": date, "end": date}, {"start": date, "end": date}]
    stamp = "Podaj datę i godzinę w formacie RRRR-MM-DDTgg:mm · format"
    assert got["stamps"] == [None, None, None, stamp, stamp, stamp, stamp]
    # A ticked flag disables what it excludes: not checked, not sent.
    disabled_by, active, problems, options = got["ticked"]
    assert (disabled_by, active, problems) == ("all_nodes", False, {})
    assert options == {"value": 1, "all_nodes": True}
    assert got["both"] == {"all_nodes": "Nie łącz z: nodes · excludes"}
    # Unticked again (false, its default), it excludes nothing.
    assert got["unticked"] == [None, {}, {"value": 1, "nodes": ["A"]}]


# --- router, persist, labels, info --------------------------------------------


def test_routes_and_stored_inputs(page: Any) -> None:
    got = js(
        page,
        """const odd = ['a b/c', 'ł#?', '100%'];
        const stored = () => {
          persist.saveState('js-units', {command: 'uh nash', values: {n: '3'}});
          const raw = localStorage.getItem('hydrolog-gui/js-units/1');
          const back = persist.loadState('js-units', 'first');
          persist.clearState('js-units');
          return [raw, back, persist.loadState('js-units', 'first')];
        };
        localStorage.setItem('hydrolog-gui/broken/1', '{bad');
        const broken = persist.loadState('broken', 'first');
        localStorage.removeItem('hydrolog-gui/broken/1');
        return {
          parse: ['#polecenia/uh/nash', '', '#', '#nowhere//a/',
                  '#polecenia/a%20b/%E2%9C%93', '#x/%E0%A4%A'].map(router.parseHash),
          hash: [router.routeHash('polecenia', ['uh', 'nash']),
                 router.routeHash('polecenia'), router.routeHash('polecenia', odd)],
          back: router.parseHash(router.routeHash('polecenia', odd)),
          keys: [persist.storageKey('polecenia'), persist.storageKey('layout', 2)],
          stored: stored(),
          broken,
        };""",
    )
    assert got["parse"] == [
        {"section": "polecenia", "path": ["uh", "nash"]},
        {"section": "", "path": []},
        {"section": "", "path": []},
        {"section": "nowhere", "path": ["a"]},  # unknown sections are the shell's call
        {"section": "polecenia", "path": ["a b", "✓"]},
        {"section": "x", "path": ["%E0%A4%A"]},  # a broken escape stays as it is
    ]
    assert got["hash"] == [
        "#polecenia/uh/nash",
        "#polecenia",
        "#polecenia/a%20b%2Fc/%C5%82%23%3F/100%25",
    ]
    assert got["back"] == {"section": "polecenia", "path": ["a b/c", "ł#?", "100%"]}
    assert got["keys"] == ["hydrolog-gui/polecenia/2", "hydrolog-gui/layout/2"]
    raw, back, cleared = got["stored"]
    assert raw == '{"command":"uh nash","values":{"n":"3"}}'
    assert back == {"command": "uh nash", "values": {"n": "3"}}
    assert cleared == "first"  # „Wyczyść”: a first visit again
    assert got["broken"] == "first"


def test_errors_of_the_server_in_polish(page: Any) -> None:
    got = js(
        page,
        """const nashDoc = await doc('uh nash');
        const answers = [
          await run('uh nash', {area_km2: 0, n: 3, k_min: 30}),
          await run('scs effective', {cn: 72, amc: 'IV', precipitation_mm: 50}),
          await run('uh nash', {area_km2: 45, lutz_length_km: 10,
            lutz_centroid_length_km: 16, lutz_slope_m_per_m: 0.02,
            lutz_manning_n: 0.035}),
          await run('scs effective', {cn: 72}),
          await run('scs effective', {cn: 72, input_file: '../x.csv'}),
        ];
        return {
          statuses: answers.map((a) => a.status),
          described: answers.map((a) => errors.describeError(a.body)),
          form: m.validate(m.fieldModel(nashDoc),
            {area_km2: '0', n: '3', k_min: '30'}).area_km2,
          reasons: [
            errors.reasonText('one_of', {groups: [['a', 'b'], ['c']]}),
            errors.reasonText('one_of', {groups: [['a', 'b'], ['c']], missing: []}),
            errors.reasonText('too_large', {limit_bytes: 5 * 1024 * 1024}),
            errors.reasonText('maximum', {maximum: 0.5, value: 0.6, index: 2}),
            errors.reasonText('type', {expected: 'integer'}),
            errors.reasonText('type', {expected: 'mystery'}),
            errors.reasonText('nonsense', {}),
          ],
          bare: [errors.describeError({message: 'Boom'}), errors.describeError(null)],
        };""",
    )
    assert got["statuses"] == [400, 400, 400, 400, 403]
    bound, choice, library, group, outside = got["described"]
    assert bound == {
        "option": "area_km2",
        "reason": "exclusive_minimum",
        "title": INVALID,
        "text": "Musi być większa od 0 (podano 0)",
        "english": False,
    }
    # The field says the same before a run as the server after it.
    assert got["form"] == bound["text"] + " · exclusive_minimum"
    assert (choice["option"], choice["text"]) == (
        "amc",
        "Dozwolone wartości: I, II, III",
    )
    # A library relation error names its field (Lc of Lutz), so it stands on it.
    assert (library["option"], library["reason"]) == (
        "lutz_centroid_length_km",
        "maximum",
    )
    assert library["title"] == INVALID
    assert (group["option"], group["reason"]) == ("precipitation_mm", "one_of")
    assert group["text"] == (
        "Podaj dokładnie jedną kompletną grupę: precipitation_mm albo values albo "
        "input_file; brakuje: precipitation_mm"
    )
    assert (outside["option"], outside["english"]) == ("input_file", False)
    assert outside["text"] == "Plik musi leżeć w katalogu sesji (in/… albo out/…)"
    assert got["reasons"] == [
        "Podano kilka grup naraz; zostaw jedną: a + b albo c",
        "Podaj dokładnie jedną kompletną grupę: a + b albo c",
        "Za duże: najwięcej 5,0 MB",
        "Wartość 3: Najwyżej 0,5 (podano 0,6)",
        "Podaj liczbę całkowitą",
        "Nieprawidłowy rodzaj wartości",
        None,
    ]
    boom, nothing = got["bare"]
    assert (boom["title"], boom["text"], boom["english"]) == (
        INVALID,
        "Boom" + EN,
        True,
    )
    assert (nothing["option"], nothing["text"]) == (None, "")


def test_a_file_over_the_session_limit_is_refused_before_it_is_sent(page: Any) -> None:
    got = js(
        page,
        """const files = await import('./src/controls/file-field.js');
        const before = await files.refreshSession();
        const size = before.limits.file_bytes + 1024 * 1024;
        const big = new File([new Uint8Array(size)], 'Dopływ.csv');
        let message = null;
        try {
          await files.uploadFile(big);
        } catch (failure) {
          message = failure.message;
        }
        const after = await files.refreshSession();
        return {limit: before.limits.file_bytes, message,
          stored: [before.files.length, after.files.length]};""",
    )
    assert got["limit"] == 20 * 1024 * 1024
    assert got["message"] == "za duży (21,0 MB, najwięcej 20,0 MB)"
    assert got["stored"] == [0, 0]


def test_notices_in_polish(page: Any) -> None:
    got = js(
        page,
        """return [
          {code: 'timeout', message: 'Stopped', details: {timeout_s: 30}},
          {code: 'timeout', message: 'Stopped'},
          {code: 'incomplete_years', message: 'm', details: {skipped: 2, total: 10}},
          {code: 'tc_not_used', message: 'm',
           details: {uh_model: 'nash', tc_min: 12345.6, node_id: 'A'}},
          {code: 'incomplete_years', message: 'm', details: {skipped: 2, total: 10,
            years: [2001, 2005]}},
          {code: 'user_warning', message: 'Careful'},
          {code: 'homogeneity_rejected', message: 'm',
           details: {tests: ['mann_whitney', 'pettitt'], alpha: 0.05}},
          {code: 'no_such_code', message: 'Something odd'},
        ].map(notices.describeNotice);""",
    )
    assert got == [
        {"text": "Obliczenie przerwano po 30 s: trwało za długo.", "english": False},
        # without its values, the plain form
        {"text": "Obliczenie przerwano: trwało za długo.", "english": False},
        {"text": "Pominięto lata z niepełnymi danymi.", "english": False},
        {
            "text": "Węzeł A: Model nash nie używa czasu koncentracji: "
            f"tc = 12{NBSP}346 min pominięto.",
            "english": False,
        },
        {
            "text": "Pominięto 2 z 10 lat z niepełnymi danymi: 2001, 2005.",
            "english": False,
        },
        {"text": "Ostrzeżenie biblioteki: Careful" + EN, "english": True},
        # the codes of a detail by their Polish names
        {
            "text": "Testy odrzucające jednorodność ciągu przy α = 0,05: "
            "Mann-Whitney, Pettitt.",
            "english": False,
        },
        {"text": "Something odd" + EN, "english": True},
    ]


def test_ranges_of_applicability(page: Any) -> None:
    # Ranges as Hydrolog serves them (`typical_ranges` of a command's catalog document)
    got = js(
        page,
        """const range = {minimum: 0, maximum: 80};
        const slope = {method: 'kirpich', parameter: 'slope_m_per_m',
          inputs: ['flow_path_slope_m_per_m'], minimum: 0.03,
          maximum: 0.1, unit: 'm/m', source: 'Kirpich (1940)'};
        const years = {method: 'flood_frequency', parameter: 'years', inputs: [],
          result: 'n_years', minimum: 30, maximum: null, unit: 'years', source: 'KZGW'};
        const step = {method: 'scs', parameter: 'timestep_min',
          inputs: ['timestep_min'], minimum: 0, maximum: 0.25, unit: 'min',
          relative_to: 'uh_time_to_peak_min', source: 'NEH 630 ch. 16',
          i18n: {pl: {source: 'NEH 630 rozdz. 16'}}};
        const area = (method, minimum, maximum) => ({method, parameter: 'area_km2',
          inputs: ['area_km2'], minimum, maximum, unit: 'km2', source: method});
        return {
          state: [info.rangeState(range, 0), info.rangeState(range, 80),
                  info.rangeState(range, 80.01), info.rangeState(range, -0.01),
                  info.rangeState({minimum: 0.002, maximum: null}, 1e6),
                  info.rangeState({maximum: 5}, -10),
                  info.rangeState(range, '5'), info.rangeState(range, NaN),
                  info.rangeState(range, null),
                  info.rangeState(step, 25, 100), info.rangeState(step, 25.01, 100),
                  info.rangeState(step, 25, null)],
          value: [info.rangeValue(slope, {flow_path_slope_m_per_m: 0.0114,
                    mean_slope_m_per_m: 0.082}),
                  info.rangeValue(slope, {mean_slope_m_per_m: 0.082}),
                  info.rangeValue(slope, {flow_path_slope_m_per_m: '0,02'}),
                  info.rangeValue(years, {n_years: 26}),
                  info.rangeValue(years, {})],
          scale: [info.rangeScale(slope, {}),
                  info.rangeScale(step, {uh_time_to_peak_min: 102.76}),
                  info.rangeScale(step, {}),
                  info.rangeScale(step, {uh_time_to_peak_min: 0})],
          text: [info.rangeText(slope), info.rangeText(area('scs', 0, 52)),
                 info.rangeText(years), info.rangeText(area('giandotti', 170, 70000)),
                 info.rangeText({minimum: 1, maximum: 10, unit: '-'}),
                 info.rangeText(step, {symbol: 'tp'}),
                 info.rangeText(step, {symbol: 'tp', scale: 102.76}),
                 info.rangeText({minimum: 0.2, maximum: 1.5, unit: 'min',
                   relative_to: 'tc_min'}, {symbol: 'tc', scale: 100}),
                 info.rangeText({})],
          source: [info.rangeSource(step), info.rangeSource(slope)],
          listed: info.listedRanges({symbols: {timestep_min: 'Δt', area_km2: 'A'}}, [
            step, {...step, method: 'nash'}, {...step, method: 'clark'},
            area('scs', 0, 52), area('snyder', 26, 26000),
          ]).map((item) => [info.rangeKey(item.range), item.label]),
        };""",
    )
    assert got["state"] == [
        *["ok", "ok", "warn", "warn", "ok", "ok", None, None, None],
        *["ok", "warn", None],  # a share of 100: up to 25 inside, none without it
    ]
    # The field the range names, never another one in its place, and only a number
    assert got["value"] == [
        {"field": "flow_path_slope_m_per_m", "value": 0.0114},
        None,
        None,
        {"field": "n_years", "value": 26},
        None,
    ]
    assert got["scale"] == [1, 102.76, None, None]
    assert got["text"] == [
        "od 0,03 do 0,1 m/m",
        "najwyżej 52 km²",
        "co najmniej 30 lat",
        f"od 170 do 70{NBSP}000 km²",
        "od 1 do 10",
        "najwyżej 0,25·tp",
        "najwyżej 0,25·tp = 25,69 min",
        "od 0,2·tc do 1,5·tc (od 20 do 150 min)",
        "",
    ]
    assert got["source"] == ["NEH 630 rozdz. 16", "Kirpich (1940)"]
    # The time step of three models listed once; an area of two methods names its method
    assert got["listed"] == [
        ["scs.timestep_min", "Δt"],
        ["scs.area_km2", "A (scs)"],
        ["snyder.area_km2", "A (snyder)"],
    ]


# --- Polecenia's state and the result view -----------------------------------


def test_command_list_groups_and_search(page: Any) -> None:
    got = js(
        page,
        """const list = (await (await fetch('api/commands')).json()).commands;
        const docs = new Map();
        await Promise.all(list.map(async (item) => {
          docs.set(item.name, await doc(item.name));
        }));
        const find = (group, query) => state.filterCommands(list, docs, group, query)
          .map((item) => item.name);
        const groups = state.groupsOf(list);
        return {
          names: list.map((item) => item.name),
          groups: groups.map((g) => [g.group, g.title, g.commands.map((c) => c.name)]),
          nash: [find('', 'NASH'), find('', 'metoda lutza'), find('uh', 'Lutz manning'),
                 find('uh', 'lutz-manning'), find('uh', 'lutz_manning')],
          scs: [find('', 'opad EFEKTYWNY'), find('', 'iii'), find('scs', ''),
                find('', 'efektywny łódź')],
          lost: find('', ' '),
        };""",
    )
    names = got["names"]
    groups = got["groups"]
    # Every command in exactly one group, the groups in catalog order, named in Polish.
    assert [name for _, _, members in groups for name in members] == names
    for group, title, members in groups:
        assert title, group
        assert all(name.split(" ")[0] == group for name in members)
    assert {group: title for group, title, _ in groups}[
        "uh"
    ] == "Hydrogramy jednostkowe"
    assert len({group for group, _, _ in groups}) == len(groups)
    # Folded words, all of them, in the name, the Polish texts, option names
    # (with "_" or "-" as spaces) and allowed values; a group narrows the list.
    by_name, by_polish, *by_option = got["nash"]
    assert "uh nash" in by_name and "uh nash" in by_polish
    assert by_option == [["uh nash"]] * 3
    effective, by_value, scs_group, nothing = got["scs"]
    assert "scs effective" in effective and "scs effective" in by_value
    assert scs_group == [name for name in names if name.startswith("scs ")]
    assert nothing == []
    assert got["lost"] == names  # a blank search hides nothing


def test_result_view_of_real_runs(page: Any) -> None:
    got = js(
        page,
        """const nash = await run('uh nash', {area_km2: 45.3, n: 3, k_min: 30});
        const kirpich = await run('tc kirpich', {length_km: 8.2, slope_m_per_m: 0.023});
        const a = rv.analyzeResult(nash.body);
        const k = rv.analyzeResult(kirpich.body);
        return {
          envelope: nash.body,
          analysis: {schema: a.schema, status: a.status,
            scalar: a.scalars.find((s) => s.key === 'area_km2'),
            series: a.series.map((g) => ({length: g.length, x: g.x.name, unit: g.x.unit,
              ys: g.ys.map((y) => [y.key, y.unit])}))},
          tiles: rv.headline(a, nash.body.inputs).map((t) => t.key),
          chosen: rv.headline(a, {}, ['parameters.n', 'lag_time_min', 'nope'])
            .map((t) => t.value),
          csv: rv.resultCsv(a),
          scalarCsv: rv.resultCsv(k),
          cells: ['a,b', 'say "hi"', 'x\\ny', null, 1.5].map(rv.csvCell),
          empty: rv.analyzeResult(null),
        };""",
    )
    envelope = got["envelope"]
    result = envelope["result"]
    analysis = got["analysis"]
    assert (analysis["schema"], analysis["status"]) == ("hydrolog-uh-nash/1", "ok")
    assert analysis["scalar"] == {
        "key": "area_km2",
        "label": "Powierzchnia zlewni",
        "value": 45.3,
        "unit": "km²",
    }
    length = len(result["times_min"])
    assert analysis["series"] == [
        {
            "length": length,
            "x": "times_min",
            "unit": "min",
            "ys": [["ordinates_m3s_per_mm", "m³/s na 1 mm"]],
        }
    ]
    # Tiles never repeat an input (area 45.3, timestep 5).
    assert got["tiles"] == [
        "duration_min",
        "lag_time_min",
        "time_to_peak_min",
        "peak_discharge_m3s_per_mm",
    ]
    assert got["chosen"] == [3, result["lag_time_min"]]
    # The CSV: a header of field names, one row per step, decimal dots, exact values.
    lines = got["csv"].splitlines()
    assert got["csv"].endswith("\n")
    assert lines[0] == "times_min,ordinates_m3s_per_mm"
    assert len(lines) == length + 1
    rows = [tuple(float(cell) for cell in line.split(",")) for line in lines[1:]]
    assert rows == list(
        zip(result["times_min"], result["ordinates_m3s_per_mm"], strict=True)
    )
    scalars = got["scalarCsv"].splitlines()
    assert scalars[0] == "name,value,unit"
    assert "method,kirpich," in scalars
    assert "parameters.length_km,8.2,km" in scalars
    tc = next(line for line in scalars if line.startswith("tc_min,"))
    _, value, unit = tc.split(",")
    assert unit == "min" and math.isclose(float(value), 85.97, rel_tol=1e-3)
    assert got["cells"] == ['"a,b"', '"say ""hi"""', '"x\ny"', "", "1.5"]
    empty = got["empty"]
    assert (empty["schema"], empty["series"], empty["scalars"]) == (None, [], [])


# --- Sieć's canvas: editor/geometry.js, editor/edits.js -----------------------


GEOMETRY = "const g = await import('./src/sections/siec/editor/geometry.js');"
# The guide's network at the cells of the library's layout (the ids of its nodes, their
# inflows and cells: x downstream, y sideways).
GUIDE_CELLS = """const guide = [
  {id: 'A', from: null, cell: [0, 1]},
  {id: 'B', from: null, cell: [1, 0]},
  {id: 'C', from: null, cell: [3, 2]},
  {id: 'R_A', from: ['A'], cell: [1, 1]},
  {id: 'J1', from: ['R_A', 'B'], cell: [2, 1]},
  {id: 'R_J1', from: ['J1'], cell: [3, 1]},
  {id: 'J2', from: ['R_J1', 'C'], cell: [4, 1]},
  {id: 'OUT', from: ['J2'], cell: [5, 1]},
];"""


def test_rule_d_of_the_canvas_is_the_librarys(page: Any) -> None:
    cells = [(x, y) for x in range(-3, 4) for y in range(-3, 4)]
    pairs = [[start, end] for start in cells for end in cells if start != end]
    got = page.evaluate(
        f"""async (pairs) => {{ {GEOMETRY}
          return pairs.map(([start, end]) => g.edgeRoute(start, end)); }}""",
        pairs,
    )
    expected = [
        [list(corner) for corner in edge_route(start, end)] for start, end in pairs
    ]
    assert got == expected


def test_the_canvas_ranks_the_lines_as_the_library_does(page: Any) -> None:
    cases = []
    for seed in range(40):
        root, inflows = random_tree(
            3 + 3 * seed, seed, fan_in=1 + seed % 5, deep=(seed % 4) / 4
        )
        heads = [node for node, ups in inflows.items() if not ups]
        chance = random.Random(seed)
        areas = {node: round(chance.uniform(0.5, 50), 2) for node in heads}
        weighed = areas if seed % 2 else {}
        drawn = layout(root, inflows, weight=weighed or None)
        skeleton = []
        for node, ups in inflows.items():
            kind = "junction" if ups else "subcatchment"
            skeleton.append(
                {"id": node, "type": "outlet" if node == root else kind, "from": ups}
            )
        lines = {
            node: {"main": line.index == 0, "joins": line.joins}
            for line in drawn.lines
            for node in line.nodes
        }
        cases.append({"skeleton": skeleton, "areas": weighed, "lines": lines})
    got = page.evaluate(
        f"""async (cases) => {{ {GEOMETRY}
          return cases.map(({{skeleton, areas}}) => Object.fromEntries(
            g.linesOf(skeleton, new Map(Object.entries(areas))))); }}""",
        cases,
    )
    # The main stem and the node each tributary joins, so the colours and the sides of
    # the labels are the library's, with areas and with counts of nodes
    assert got == [case["lines"] for case in cases]


def test_the_structure_sent_to_hydrolog_ranks_the_lines_as_the_canvas(
    page: Any,
) -> None:
    cases: list[dict[str, Any]] = []
    for seed in range(24):
        root, inflows = random_tree(
            4 + 2 * seed, seed, fan_in=1 + seed % 4, deep=(seed % 4) / 4
        )
        heads = sorted(node for node, ups in inflows.items() if not ups)
        chance = random.Random(seed)
        areas: dict[str, float] = {
            node: round(chance.uniform(0.5, 50), 2) for node in heads
        }
        # Every head with a positive area, or one head with 0, a negative one or none
        odd = heads[seed % len(heads)]
        if seed % 4 == 1:
            areas[odd] = 0
        elif seed % 4 == 2:
            areas[odd] = -3.5
        elif seed % 4 == 3:
            del areas[odd]
        kinds = {1: "reach"}
        skeleton = [
            {
                "id": node,
                "type": kinds.get(len(ups), "junction") if ups else "subcatchment",
                "from": list(ups) or None,
            }
            for node, ups in inflows.items()
        ]
        skeleton.append({"id": "END", "type": "outlet", "from": [root]})
        cases.append({"skeleton": skeleton, "areas": areas})
    got = page.evaluate(
        f"""async (cases) => {{ {GEOMETRY}
          const s = await import('./src/sections/siec/state.js');
          return cases.map(({{skeleton, areas}}) => {{
            const known = new Map(Object.entries(areas));
            return {{
              document: s.structureDocument(skeleton, known),
              lines: Object.fromEntries(g.linesOf(skeleton, known)),
            }};
          }}); }}""",
        cases,
    )

    for case, found in zip(cases, got, strict=True):
        # The document: ids, types, links and the positive areas only
        expected = [
            {
                "id": node["id"],
                "type": node["type"],
                **({"from": node["from"]} if node["from"] else {}),
                **(
                    {"watershed": {"area_km2": case["areas"][node["id"]]}}
                    if case["areas"].get(node["id"], 0) > 0
                    else {}
                ),
            }
            for node in case["skeleton"]
        ]
        assert found["document"] == {"schema": "hydrolog-network/1", "nodes": expected}
        # The library's lines of the structure with every area as given, 0 and
        # negative ones included, are the canvas's
        given = {
            "schema": "hydrolog-network/1",
            "nodes": [
                {
                    **{key: value for key, value in node.items() if value is not None},
                    **(
                        {"watershed": {"area_km2": case["areas"][node["id"]]}}
                        if node["id"] in case["areas"]
                        else {}
                    ),
                }
                for node in case["skeleton"]
            ],
        }
        drawn = structure_schematic(given)
        lines = {
            node: {"main": line["role"] == "main", "joins": line.get("joins")}
            for line in drawn["lines"]
            for node in line["nodes"]
        }
        assert found["lines"] == lines


def test_free_cells_provisional_rows_and_the_cells_of_an_opened_network(
    page: Any,
) -> None:
    got = js(
        page,
        f"""{GEOMETRY} {GUIDE_CELLS}
        const taken = (...cells) => new Set(cells.map(g.cellKey));
        const looped = [
          {{id: 'A', from: ['B']}}, {{id: 'B', from: ['A']}}, {{id: 'C', from: null}},
          {{id: 'D', from: ['C', 'A']}},
        ];
        const opened = g.placeMissing([
          {{id: 'A', from: null, position: {{x: 0, y: 0}}}},
          {{id: 'B', from: null, position: {{x: 0, y: 0}}}},
          {{id: 'J', from: ['A', 'B'], position: {{x: 1, y: 0}}}},
          {{id: 'OUT', from: ['J']}},
        ]);
        const answer = await fetch('api/schemas/hydrolog-network-1.schema.json');
        const schema = await answer.json();
        return {{
          free: [
            g.freeCell(taken(), [2, 3], 'up'),
            g.freeCell(taken([2, 3]), [2, 3], 'up'),
            g.freeCell(taken([2, 3], [1, 3]), [2, 3], 'up'),
            g.freeCell(taken([2, 3], [1, 2], [1, 3], [1, 4]), [2, 3], 'up'),
            g.freeCell(taken([2, 3]), [2, 3], 'down'),
            g.freeCell(taken([-1000, 0]), [-1000, 0], 'up'),
          ],
          rows: Object.fromEntries(g.provisionalRows(guide)),
          looped: Object.fromEntries(g.provisionalRows(looped)),
          opened: {{cells: Object.fromEntries(opened.cells), moved: opened.moved}},
          read: [{{x: 2, y: -3}}, {{x: 2.5, y: 0}}, {{x: 1001, y: 0}}, {{x: 1}},
                 {{x: 1, y: 2, z: 3}}, [1, 2], null].map(g.cellOf),
          snapped: [[0, 0], [54, 36], [56, 38], [-56, -38], [1e6, -1e6]]
            .map(g.cellAt),
          bound: [g.MAX_POSITION, schema.$defs.position.properties.x.maximum,
                  schema.$defs.position.properties.y.minimum],
        }};""",
    )
    # The cell itself when free; else upstream first, straight before diagonal, the
    # right before the left, then level, then downstream; never off the grid
    assert got["free"] == [[2, 3], [1, 3], [1, 4], [2, 4], [3, 3], [-1000, 1]]
    # Rows by the longest distance from a headwater, centred, in the order of the
    # document; a cycle and what is below it go on the row after the last
    assert got["rows"] == {
        "A": [0, -1],
        "B": [0, 0],
        "C": [0, 1],
        "R_A": [1, 0],
        "J1": [2, 0],
        "R_J1": [3, 0],
        "J2": [4, 0],
        "OUT": [5, 0],
    }
    assert got["looped"] == {"A": [1, -1], "B": [1, 0], "C": [0, 0], "D": [1, 1]}
    # A shared cell stays with the first node; the others go beside a neighbour
    assert got["opened"] == {
        "cells": {"A": [0, 0], "B": [0, 1], "J": [1, 0], "OUT": [2, 0]},
        "moved": ["B", "OUT"],
    }
    assert got["read"] == [[2, -3], None, None, None, None, None, None]
    assert got["snapped"] == [[0, 0], [0, 0], [1, 1], [-1, -1], [-1000, 1000]]
    bound = got["bound"]
    assert bound == [1000, 1000, -1000]


def test_the_arrow_keys_go_to_the_nearest_node_that_way(page: Any) -> None:
    got = js(
        page,
        f"""{GEOMETRY} {GUIDE_CELLS}
        return [['OUT', 'up'], ['J2', 'up'], ['R_J1', 'right'], ['J1', 'left'],
                ['A', 'up'], ['A', 'down'], ['B', 'right'], ['C', 'left'],
                ['C', 'right']]
          .map(([from, way]) => g.nearestInDirection(guide, from, way));""",
    )
    # Straight ahead before diagonal, within 45 degrees before the rest; or nothing
    assert got == ["J2", "R_J1", "C", "B", None, "R_A", "R_A", "R_J1", None]


def test_moves_share_the_nodes_they_do_not_change(page: Any) -> None:
    got = js(
        page,
        """const e = await import('./src/sections/siec/editor/edits.js');
        const inputs = {network: {name: 'x'}, nodes: {A: {}}, selected: 'A',
          skeleton: [
            {id: 'A', type: 'subcatchment', from: null, position: {x: 0, y: 0}},
            {id: 'B', type: 'subcatchment', from: null, position: {x: 0, y: 1}},
            {id: 'OUT', type: 'outlet', from: ['A', 'B'], position: {x: 1, y: 0}},
          ]};
        const moved = e.moveNode(inputs, 'A', {x: -1, y: 0});
        const placed = e.placeAll(inputs,
          {A: {x: 5, y: 5}, OUT: {x: 6, y: 5}, Z: {x: 0, y: 0}});
        const same = (next) => next === inputs;
        return {
          moved: moved.skeleton.map((node) => node.position),
          shared: [moved.skeleton[1] === inputs.skeleton[1],
                   moved.skeleton[2] === inputs.skeleton[2],
                   moved.nodes === inputs.nodes, moved.network === inputs.network,
                   moved.selected],
          before: inputs.skeleton[0].position,
          refused: [same(e.moveNode(inputs, 'A', {x: 0, y: 1})),
                    same(e.moveNode(inputs, 'Z', {x: 3, y: 3})),
                    same(e.moveNode(inputs, 'A', {x: 1001, y: 0})),
                    same(e.moveNode(inputs, 'A', {x: 0.5, y: 0}))],
          placed: placed.skeleton.map((node) => node.position),
          kept: placed.skeleton[1] === inputs.skeleton[1],
        };""",
    )
    assert got["moved"] == [{"x": -1, "y": 0}, {"x": 0, "y": 1}, {"x": 1, "y": 0}]
    assert got["shared"] == [True, True, True, True, "A"]
    assert got["before"] == {"x": 0, "y": 0}
    # A taken cell, an unknown node or a cell off the grid leaves the inputs as they are
    assert got["refused"] == [True, True, True, True]
    assert got["placed"] == [{"x": 5, "y": 5}, {"x": 0, "y": 1}, {"x": 6, "y": 5}]
    assert got["kept"] is True


# --- Sieć's editor: editor/graph.js, edits.js, history.js, words.js -----------


# The structure module with the inflow rules of the real schema the page loads.
GRAPH = """const gr = await import('./src/sections/siec/editor/graph.js');
const schema = await (await fetch('api/schemas/hydrolog-network-1.schema.json')).json();
const rules = gr.inflowRules(schema);
"""
# Structure nodes by type: `s('C', 'A')` is a subcatchment C that lists A in `from`;
# `at(node, x, y)` places a node on a cell.
NODES = """const node = (type) => (id, ...from) =>
  ({id, type, from: from.length ? from : null});
const s = node('subcatchment');
const r = node('reach');
const zb = node('reservoir');
const j = node('junction');
const o = node('outlet');
const at = (made, x, y) => ({...made, position: {x, y}});
const froms = (inputs) =>
  Object.fromEntries(inputs.skeleton.map((n) => [n.id, n.from]));
"""
EDITS = "const e = await import('./src/sections/siec/editor/edits.js');\n"
HISTORY = (
    "const {createHistory} = await import('./src/sections/siec/editor/history.js');\n"
)


def test_inflow_rules_come_from_the_schema(page: Any) -> None:
    got = js(page, GRAPH + "return rules;")

    assert got == {
        "subcatchment": {"fewest": 0, "most": 0},
        "reach": {"fewest": 1, "most": 1},
        "reservoir": {"fewest": 1, "most": 1},
        "junction": {"fewest": 1, "most": None},
        "outlet": {"fewest": 1, "most": 1},
    }


def test_the_structure_reports_every_reason_with_its_details(page: Any) -> None:
    got = js(
        page,
        GRAPH
        + NODES
        + """const long = 'A'.repeat(65);
        const problems = (skeleton) => gr.graphProblems(skeleton, rules);
        return {
          complete: problems([s('A'), s('B'), r('R', 'A'), j('J', 'R', 'B'),
                              o('OUT', 'J')]),
          empty: problems([]),
          invalid: problems([s('A B'), s('A.'), s(long),
                             j('J', 'A B', 'A.', long, 'bad id'), o('OUT', 'J')]),
          reserved: problems([s('con'), s('LPT1.txt'), s('com\u00b9'),
                              j('J', 'con', 'LPT1.txt', 'com\u00b9', 'nul'),
                              o('OUT', 'J')]),
          duplicate: problems([s('A'), s('a'), s('STRASSE'), s('straße'),
                               j('J', 'A', 'a', 'STRASSE', 'straße'), o('OUT', 'J')]),
          unknown: problems([s('A'), j('J', 'A', 'X'), o('OUT', 'J')]),
          repeated: problems([s('A'), j('J', 'A', 'A'), o('OUT', 'J')]),
          count: problems([s('A'), s('B'), s('C', 'A'), r('R1', 'B', 'C'), r('R2'),
                           j('J0'), j('J', 'R1', 'R2', 'J0'), o('OUT', 'J')]),
          several: problems([s('A'), j('J1', 'A'), j('J2', 'A', 'J1'), o('OUT', 'J2')]),
          cycles: problems([s('A'), j('J', 'A', 'P'), o('OUT', 'J'), j('K', 'L'),
                            j('L', 'M'), j('M', 'K'), j('P', 'K'), j('S', 'S')]),
          noOutlet: problems([s('A'), j('J', 'A')]),
          outlets: problems([s('A'), s('B'), o('O2', 'B'), o('O1', 'A')]),
          outletDown: problems([s('A'), o('OUT', 'A'), j('J', 'OUT')]),
          disconnected: problems([s('A'), s('B'), j('J'), o('OUT', 'A')]),
          first: problems([s('A B'), o('O1', 'A B'), s('C'), o('O2', 'C')]),
          marked: [
            {reason: 'cycle', nodes: ['K', 'M', 'L']},
            {reason: 'invalid_id', node_id: 'bad id', listed_by: 'J'},
            {reason: 'several_outlets', nodes: ['O1', 'O2']},
            {reason: 'no_outlet'},
            {reason: 'disconnected_node', node_id: 'B'},
          ].map(gr.problemNodes),
        };""",
    )

    def problem(reason: str, node_id: str, **details: Any) -> dict[str, Any]:
        return {"reason": reason, "node_id": node_id, **details}

    assert got["complete"] == []
    assert got["empty"] == [{"reason": "empty"}]
    # A space, a trailing dot, 65 characters; an invalid id in `from` names its lister
    assert got["invalid"] == [
        problem("invalid_id", "A B"),
        problem("invalid_id", "A."),
        problem("invalid_id", "A" * 65),
        problem("invalid_id", "bad id", listed_by="J"),
    ]
    assert got["reserved"] == [
        problem("reserved_name", "con"),
        problem("reserved_name", "LPT1.txt"),
        problem("reserved_name", "com\u00b9"),
        problem("reserved_name", "nul", listed_by="J"),
    ]
    # Without regard to case, ß folded to ss as Python's casefold does; the earlier one
    # is the other
    assert got["duplicate"] == [
        problem("duplicate_node", "a", other_id="A"),
        problem("duplicate_node", "straße", other_id="STRASSE"),
    ]
    assert got["unknown"] == [problem("unknown_upstream", "J", upstream_id="X")]
    assert got["repeated"] == [problem("duplicate_upstream", "J")]
    assert got["count"] == [
        problem("upstream_count", "C", type="subcatchment", found=1),
        problem("upstream_count", "R1", type="reach", found=2),
        problem("upstream_count", "R2", type="reach", found=0),
        problem("upstream_count", "J0", type="junction", found=0),
    ]
    assert got["several"] == [
        problem("several_downstream", "A", downstream=["J1", "J2"])
    ]
    # Each cycle in flow order (K flows into M, M into L) from its smallest id; a
    # self-loop; P below the cycle, and what P flows into, are in none
    assert got["cycles"] == [
        problem("several_downstream", "K", downstream=["M", "P"]),
        {"reason": "cycle", "nodes": ["K", "M", "L"]},
        {"reason": "cycle", "nodes": ["S"]},
    ]
    assert got["noOutlet"] == [
        {"reason": "no_outlet"},
        problem("disconnected_node", "J"),
    ]
    assert got["outlets"] == [{"reason": "several_outlets", "nodes": ["O2", "O1"]}]
    assert got["outletDown"] == [
        problem("outlet_has_downstream", "OUT", downstream=["J"]),
        problem("disconnected_node", "J"),
    ]
    # Every node but the outlet that flows nowhere, in the order of the structure
    assert got["disconnected"] == [
        problem("disconnected_node", "B"),
        problem("upstream_count", "J", type="junction", found=0),
        problem("disconnected_node", "J"),
    ]
    # The problems of the whole network come first
    assert got["first"] == [
        {"reason": "several_outlets", "nodes": ["O1", "O2"]},
        problem("invalid_id", "A B"),
    ]
    # A cycle marks its nodes, an id in `from` its lister, the whole network none
    assert got["marked"] == [["K", "M", "L"], ["J"], [], [], ["B"]]


def test_a_link_is_judged_before_it_is_made(page: Any) -> None:
    got = js(
        page,
        GRAPH
        + NODES
        + """const skeleton = [s('A'), s('B'), s('C'), r('R', 'A'), j('K', 'R'),
          zb('ZB', 'B'), j('J', 'K', 'ZB'), o('OUT', 'J'), r('R2')];
        const verdict = ([from, to]) => gr.linkVerdict(skeleton, rules, from, to);
        return {
          ok: [['C', 'R2'], ['A', 'R'], ['R', 'R2'], ['C', 'J'], ['C', 'K']]
            .map(verdict),
          cycle: [['J', 'J'], ['J', 'R'], ['K', 'R']].map(verdict),
          outlet: verdict(['OUT', 'R2']),
          source: verdict(['R2', 'C']),
          offer: [['C', 'R'], ['C', 'ZB'], ['C', 'OUT']].map(verdict),
        };""",
    )

    # A free reach, the link already made, a node that moves its link, two junctions
    assert got["ok"] == [{"ok": True}] * 5
    # A self link and the loops, in flow order from the node that would flow
    assert got["cycle"] == [
        {"ok": False, "reason": "cycle", "nodes": ["J"]},
        {"ok": False, "reason": "cycle", "nodes": ["J", "R", "K"]},
        {"ok": False, "reason": "cycle", "nodes": ["K", "R"]},
    ]
    assert got["outlet"] == {"ok": False, "reason": "outlet_has_downstream"}
    assert got["source"] == {"ok": False, "reason": "upstream_count"}
    # A second inflow of a reach, a reservoir or the outlet: a junction is offered
    assert (
        got["offer"]
        == [{"ok": False, "reason": "upstream_count", "offer": "junction"}] * 3
    )


def test_a_typed_id_is_checked_as_the_library_would(page: Any) -> None:
    got = js(
        page,
        GRAPH
        + NODES
        + """const skeleton = [s('z1'), s('A'), s('STRASSE')];
        return [
          ['Z2', null], ['a b', null], ['', null], ['-x', null], ['x.', null],
          ['ł_1.b-2', null], ['A'.repeat(64), null], ['A'.repeat(65), null],
          ['con', null], ['Aux.txt', null], ['COM10', null],
          ['Z1', null], ['a', null], ['straße', null], ['Z1', 'z1'], ['a', 'z1'],
        ].map(([id, self]) => gr.idProblem(id, skeleton, self));""",
    )

    assert got == [
        None,
        "invalid_id",
        "invalid_id",
        "invalid_id",
        "invalid_id",
        None,
        None,
        "invalid_id",
        "reserved_name",
        "reserved_name",
        None,
        "duplicate_node",
        "duplicate_node",
        "duplicate_node",
        # The node itself is no duplicate: z1 can become Z1
        None,
        "duplicate_node",
    ]


def test_the_canvas_finds_the_problem_the_library_raises(page: Any) -> None:
    raised = []
    for name, doc, _ in STRUCTURE_CORPUS:
        with pytest.raises(InvalidParameterError) as error:
            RoutingNetwork.from_document(doc)
        details = error.value.details
        raised.append((name, details["reason"], details.get("node_id")))
    got = page.evaluate(
        "async (docs) => { "
        + GRAPH
        + """const nm = await import('./src/sections/siec/node-model.js');
        return {
          reasons: gr.REASONS,
          found: docs.map((doc) => gr.graphProblems(nm.skeletonOf(doc), rules)
            .map((problem) => [problem.reason, problem.node_id ?? null])),
        }; }""",
        [doc for _, doc, _ in STRUCTURE_CORPUS],
    )

    # The library raises the reason each document was made for, and together they are
    # every reason the canvas reports
    assert [(name, reason) for name, reason, _ in raised] == [
        (name, reason) for name, _, reason in STRUCTURE_CORPUS
    ]
    assert {reason for _, reason, _ in raised} == set(got["reasons"])
    # The canvas lists the library's problem on the library's node
    missed = [
        (name, reason, node_id)
        for (name, reason, node_id), found in zip(raised, got["found"], strict=True)
        if [reason, node_id] not in found
    ]
    assert missed == []


def test_new_elements_get_free_ids_and_cells(page: Any) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const placed = [at(s('A'), 0, 0), at(s('B'), 0, 1), at(r('R', 'A'), 1, 0),
          at(o('OUT', 'R'), 2, 0)];
        return {
          ids: [
            e.nextId([], 'subcatchment'), e.nextId([s('z1')], 'subcatchment'),
            e.nextId([s('z1'), s('Z3')], 'subcatchment'), e.nextId([], 'outlet'),
            e.nextId([o('out')], 'outlet'), e.nextId([o('OUT'), o('OUT2')], 'outlet'),
            e.nextId([], 'reservoir'), e.nextId([], 'junction'),
            e.nextId([r('R1')], 'reach'),
          ],
          beside: [e.cellBeside(placed, 'A'), e.cellBeside(placed, 'R'),
                   e.cellBeside(placed, null), e.cellBeside([], null),
                   e.cellBeside([s('A')], 'A')],
          above: [e.cellAbove(placed, 'R'), e.cellAbove(placed, 'OUT'),
                  e.cellAbove(placed, 'A'), e.cellAbove([], 'A')],
        };""",
    )

    # The first number free without regard to case; the outlet is OUT, then OUT2
    assert got["ids"] == ["Z1", "Z2", "Z2", "OUT", "OUT2", "OUT3", "ZB1", "J1", "R2"]
    # Right of the node, else the nearest free cell upstream first; without the node,
    # right of the top row; [0, 0] in an empty network
    assert got["beside"] == [[-1, 1], [1, 1], [0, 2], [0, 0], [0, 0]]
    assert got["above"] == [[-1, 0], [0, -1], [-1, 0], [0, 0]]


def test_adding_and_linking_share_the_nodes_they_do_not_change(page: Any) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const inputs = {network: {name: 'x'}, selected: 'A',
          nodes: {A: {area_km2: '2'}, B: {}, R: {}, J: {}, OUT: {}},
          skeleton: [at(s('A'), 0, 0), at(s('B'), 0, 2), at(r('R', 'A'), 1, 0),
                     at(j('J', 'R'), 2, 0), at(o('OUT', 'J'), 3, 0)]};
        const same = (next) => next === inputs;
        const find = (from, id) => from.skeleton.find((n) => n.id === id);
        const kept = (next, ...ids) =>
          ids.map((id) => find(next, id) === find(inputs, id));
        const added = e.addNode(inputs, 'reach', {x: 1, y: 2});
        const linked = e.connect(inputs, 'B', 'J');
        const moved = e.connect(inputs, 'A', 'J');
        const split = {network: {}, nodes: {}, selected: null,
          skeleton: [s('A'), j('J1', 'A'), j('J2', 'A', 'J1'), o('OUT', 'J2')]};
        const one = e.disconnect(split, 'A', 'J2');
        return {
          added: [added.skeleton.length, added.skeleton.at(-1), added.nodes.R1],
          addedKept: [...kept(added, 'A', 'B', 'R', 'J', 'OUT'),
                      added.nodes.A === inputs.nodes.A,
                      added.network === inputs.network,
                      added.selected],
          addRefused: [same(e.addNode(inputs, 'reach', {x: 0, y: 2})),
                       same(e.addNode(inputs, 'weir', {x: 5, y: 5})),
                       same(e.addNode(inputs, 'reach', {x: 1001, y: 0})),
                       same(e.addNode(inputs, 'reach', {x: 0.5, y: 0}))],
          linked: froms(linked),
          linkedKept: [...kept(linked, 'A', 'B', 'R', 'OUT'),
                       linked.nodes === inputs.nodes],
          moved: froms(moved),
          movedKept: kept(moved, 'A', 'B', 'OUT'),
          relinked: froms(e.connect(linked, 'B', 'R')),
          connectRefused: [same(e.connect(inputs, 'A', 'R')),
                           same(e.connect(inputs, 'A', 'A')),
                           same(e.connect(inputs, 'A', 'X')),
                           same(e.connect(inputs, 'X', 'J'))],
          all: froms(e.disconnect(split, 'A')),
          one: froms(one),
          oneKept: one.skeleton[1] === split.skeleton[1],
          disconnectRefused: [e.disconnect(split, 'OUT') === split,
                              e.disconnect(split, 'A', 'OUT') === split],
        };""",
    )

    # The new node comes last, unconnected, with empty values
    assert got["added"] == [
        6,
        {"id": "R1", "type": "reach", "from": None, "position": {"x": 1, "y": 2}},
        {},
    ]
    assert got["addedKept"] == [True] * 7 + ["A"]
    # A taken cell, an unknown type and cells off the grid add nothing
    assert got["addRefused"] == [True] * 4
    # A link goes to the end of the target's inflows
    assert got["linked"] == {
        "A": None,
        "B": None,
        "R": ["A"],
        "J": ["R", "B"],
        "OUT": ["J"],
    }
    assert got["linkedKept"] == [True] * 5
    # The source's old link moves; a list left empty is null
    assert got["moved"] == {
        "A": None,
        "B": None,
        "R": None,
        "J": ["R", "A"],
        "OUT": ["J"],
    }
    assert got["movedKept"] == [True] * 3
    assert got["relinked"] == {
        "A": None,
        "B": None,
        "R": ["A", "B"],
        "J": ["R"],
        "OUT": ["J"],
    }
    # A link already made, a self link or an unknown node change nothing
    assert got["connectRefused"] == [True] * 4
    # Every link of a node that flows into two, or the one link named
    assert got["all"] == {"A": None, "J1": None, "J2": ["J1"], "OUT": ["J2"]}
    assert got["one"] == {"A": None, "J1": ["A"], "J2": ["J1"], "OUT": ["J2"]}
    assert got["oneKept"] is True
    assert got["disconnectRefused"] == [True, True]


def test_a_junction_takes_the_second_inflow_of_a_node_that_takes_one(
    page: Any,
) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const inputs = {network: {}, selected: null,
          nodes: {A: {}, B: {}, J1: {}, R: {lag_min: '25'}, OUT: {}},
          skeleton: [at(s('A'), 0, 0), at(s('B'), 0, 2), at(j('J1', 'B'), 1, 2),
                     at(r('R', 'A'), 2, 0), at(o('OUT', 'R'), 3, 0)]};
        const into = e.insertJunction(inputs, 'B', 'R');
        const below = e.insertJunction(inputs, 'B', 'OUT');
        const same = (next) => next === inputs;
        return {
          into: into.skeleton,
          values: [into.nodes.J2, Object.keys(into.nodes)],
          kept: [into.skeleton[0] === inputs.skeleton[0],
                 into.skeleton[1] === inputs.skeleton[1],
                 into.skeleton[5] === inputs.skeleton[4],
                 into.nodes.R === inputs.nodes.R],
          below: below.skeleton,
          refused: [same(e.insertJunction(inputs, 'B', 'B')),
                    same(e.insertJunction(inputs, 'B', 'X')),
                    same(e.insertJunction(inputs, 'X', 'R'))],
        };""",
    )

    def placed(
        node_id: str, kind: str, upstream: list[str] | None, x: int, y: int
    ) -> dict[str, Any]:
        return {
            "id": node_id,
            "type": kind,
            "from": upstream,
            "position": {"x": x, "y": y},
        }

    # The junction J2 stands before the target, on the free cell above it, takes the
    # target's inflow and the source; the source's other link goes
    assert got["into"] == [
        placed("A", "subcatchment", None, 0, 0),
        placed("B", "subcatchment", None, 0, 2),
        placed("J1", "junction", None, 1, 2),
        placed("J2", "junction", ["A", "B"], 1, 0),
        placed("R", "reach", ["J2"], 2, 0),
        placed("OUT", "outlet", ["R"], 3, 0),
    ]
    assert got["values"] == [{}, ["A", "B", "J1", "R", "OUT", "J2"]]
    assert got["kept"] == [True] * 4
    # Above the outlet stands R: the junction takes the nearest free cell upstream
    assert got["below"] == [
        placed("A", "subcatchment", None, 0, 0),
        placed("B", "subcatchment", None, 0, 2),
        placed("J1", "junction", None, 1, 2),
        placed("R", "reach", ["A"], 2, 0),
        placed("J2", "junction", ["R", "B"], 1, 0),
        placed("OUT", "outlet", ["J2"], 3, 0),
    ]
    assert got["refused"] == [True] * 3


def test_a_removed_node_takes_its_links_and_values(page: Any) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const inputs = {network: {}, selected: null,
          nodes: {A: {}, R: {lag_min: '25'}, B: {}, J: {}, OUT: {}},
          skeleton: [s('A'), r('R', 'A'), s('B'), j('J', 'R', 'B'), o('OUT', 'J')]};
        const view = (next) => [froms(next), Object.keys(next.nodes)];
        const bridged = e.removeNode(inputs, 'R', {bridge: true});
        return {
          can: ['A', 'R', 'B', 'J', 'OUT', 'X']
            .map((id) => e.canBridge(inputs.skeleton, id)),
          removed: view(e.removeNode(inputs, 'R')),
          bridged: view(bridged),
          kept: [bridged.skeleton[0] === inputs.skeleton[0],
                 bridged.skeleton[3] === inputs.skeleton[4]],
          unbridged: view(e.removeNode(inputs, 'J', {bridge: true})),
          refused: e.removeNode(inputs, 'X') === inputs,
        };""",
    )

    # Only a node with one inflow that flows into one node can be bridged
    assert got["can"] == [False, True, False, False, False, False]
    assert got["removed"] == [
        {"A": None, "B": None, "J": ["B"], "OUT": ["J"]},
        ["A", "B", "J", "OUT"],
    ]
    # The inflow takes the removed node's place in the node below it
    assert got["bridged"] == [
        {"A": None, "B": None, "J": ["A", "B"], "OUT": ["J"]},
        ["A", "B", "J", "OUT"],
    ]
    assert got["kept"] == [True, True]
    # A junction of two cannot be bridged: it is removed, the outlet left without inflow
    assert got["unbridged"] == [
        {"A": None, "R": ["A"], "B": None, "OUT": None},
        ["A", "R", "B", "OUT"],
    ]
    assert got["refused"] is True


def test_a_renamed_node_keeps_its_links_values_and_column(page: Any) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const inputs = {network: {}, selected: 'Z1',
          nodes: {Z1: {'#variant': 'file'},
                  Z2: {'#variant': 'file', value_column: 'Q2'},
                  Z3: {'#variant': 'rain', area_km2: '2'}, R: {lag_min: '25'}, J: {},
                  OUT: {}},
          skeleton: [s('Z1'), s('Z2'), s('Z3'), r('R', 'Z1'), j('J', 'R', 'Z2', 'Z3'),
                     o('OUT', 'J')]};
        const view = (next, id) => ({froms: froms(next), keys: Object.keys(next.nodes),
                                     values: next.nodes[id], selected: next.selected});
        const mid = e.renameNode(inputs, 'Z2', 'Mid');
        const lower = e.renameNode(inputs, 'R', 'r');
        return {
          top: view(e.renameNode(inputs, 'Z1', 'Top'), 'Top'),
          mid: view(mid, 'Mid'),
          midShared: mid.nodes.Mid === inputs.nodes.Z2,
          rain: view(e.renameNode(inputs, 'Z3', 'Deszcz'), 'Deszcz'),
          lower: view(lower, 'r'),
          lowerKept: lower.skeleton[0] === inputs.skeleton[0],
          refused: [['Z1', 'a b'], ['Z1', 'con'], ['Z1', 'z2'], ['Z1', 'j'],
                    ['Z1', 'Z1'],
                    ['Z1', ''], ['X', 'Y']]
            .map(([id, next]) => e.renameNode(inputs, id, next) === inputs),
        };""",
    )

    def froms(renamed: dict[str, str]) -> dict[str, list[str] | None]:
        name = {node: renamed.get(node, node) for node in ["Z1", "Z2", "Z3", "R", "J"]}
        return {
            name["Z1"]: None,
            name["Z2"]: None,
            name["Z3"]: None,
            name["R"]: [name["Z1"]],
            name["J"]: [name["R"], name["Z2"], name["Z3"]],
            "OUT": ["J"],
        }

    # The links follow, the values keep their place, the chosen node follows, and a
    # subcatchment that read its column by its id keeps that column
    assert got["top"] == {
        "froms": froms({"Z1": "Top"}),
        "keys": ["Top", "Z2", "Z3", "R", "J", "OUT"],
        "values": {"#variant": "file", "value_column": "Z1"},
        "selected": "Top",
    }
    assert got["mid"] == {
        "froms": froms({"Z2": "Mid"}),
        "keys": ["Z1", "Mid", "Z3", "R", "J", "OUT"],
        "values": {"#variant": "file", "value_column": "Q2"},
        "selected": "Z1",
    }
    assert got["midShared"] is True
    assert got["rain"] == {
        "froms": froms({"Z3": "Deszcz"}),
        "keys": ["Z1", "Z2", "Deszcz", "R", "J", "OUT"],
        "values": {"#variant": "rain", "area_km2": "2"},
        "selected": "Z1",
    }
    # Only the case changes: the node is no duplicate of itself
    assert got["lower"] == {
        "froms": froms({"R": "r"}),
        "keys": ["Z1", "Z2", "Z3", "r", "J", "OUT"],
        "values": {"lag_min": "25"},
        "selected": "Z1",
    }
    assert got["lowerKept"] is True
    # Invalid, reserved and duplicate ids, the same id and an unknown node
    assert got["refused"] == [True] * 7


def test_a_description_is_set_and_a_blank_one_removed(page: Any) -> None:
    got = js(
        page,
        EDITS
        + NODES
        + """const inputs = {network: {}, nodes: {}, selected: null,
          skeleton: [s('A'), o('OUT', 'A')]};
        const described = e.describeNode(inputs, 'A', 'Lewy dopływ\\nz łąk');
        const cleared = e.describeNode(described, 'A', '  \\n ');
        return {
          described: described.skeleton[0],
          kept: described.skeleton[1] === inputs.skeleton[1],
          cleared: [cleared.skeleton[0], 'description' in cleared.skeleton[0]],
          same: [e.describeNode(described, 'A', 'Lewy dopływ\\nz łąk') === described,
                 e.describeNode(inputs, 'A', ' ') === inputs,
                 e.describeNode(inputs, 'X', 'opis') === inputs],
        };""",
    )

    assert got["described"] == {
        "id": "A",
        "type": "subcatchment",
        "from": None,
        "description": "Lewy dopływ\nz łąk",
    }
    assert got["kept"] is True
    assert got["cleared"] == [{"id": "A", "type": "subcatchment", "from": None}, False]
    assert got["same"] == [True, True, True]


def test_the_history_steps_merges_and_seals(page: Any) -> None:
    got = js(
        page,
        HISTORY
        + """const [s0, s1, s2, s3, s4] = [0, 1, 2, 3, 4].map((n) => ({n}));
        const n = (inputs) => (inputs ? inputs.n : null);
        const fresh = createHistory();
        const first = [fresh.push(s0), fresh.steps, n(fresh.current)];
        const order = createHistory();
        order.reset(s0);
        const start = [order.steps, order.canUndo, order.canRedo, n(order.current)];
        const pushed = [order.push(s1), order.push(s2), order.push(s2), order.steps];
        const back = [n(order.undo()), n(order.undo()), n(order.undo()), order.canUndo,
                      order.canRedo];
        const forth = [n(order.redo()), n(order.redo()), n(order.redo()), order.steps];
        order.undo();
        const cleared = [order.push(s3), order.canRedo, n(order.redo()), order.steps,
                         n(order.undo()), n(order.undo())];
        const merged = createHistory();
        merged.reset(s0);
        merged.push(s1, {merge: 'field:A:area', at: 0});
        const joined = [merged.push(s2, {merge: 'field:A:area', at: 5}), merged.steps,
                        n(merged.current)];
        merged.seal();
        merged.push(s3, {merge: 'field:A:area', at: 6});
        merged.push(s4, {merge: 'field:A:cn', at: 7});
        const split = [merged.steps, n(merged.undo()), n(merged.undo()),
                       n(merged.undo())];
        const moves = createHistory();
        moves.reset(s0);
        const key = {merge: 'move:A', within: 1000};
        moves.push(s1, {...key, at: 10000});
        moves.push(s2, {...key, at: 10900});
        const inside = [moves.steps, n(moves.current)];
        moves.push(s3, {...key, at: 11901});
        moves.push(s4, {...key, at: 12901});
        const outside = [moves.steps, n(moves.undo()), n(moves.undo())];
        const undone = createHistory();
        undone.reset(s0);
        undone.push(s1, {merge: 'k'});
        undone.push(s2, {merge: 'other'});
        undone.undo();
        undone.push(s3, {merge: 'k'});
        const afterUndo = [undone.steps, n(undone.undo())];
        const redone = createHistory();
        redone.reset(s0);
        redone.push(s1, {merge: 'k'});
        redone.undo();
        redone.redo();
        redone.push(s2, {merge: 'k'});
        const afterRedo = [redone.steps, n(redone.undo())];
        return {first, start, pushed, back, forth, cleared, joined, split, inside,
                outside, afterUndo, afterRedo};""",
    )

    # The first push starts the history; it is not a step
    assert got["first"] == [False, 0, 0]
    assert got["start"] == [0, False, False, 0]
    # Pushing the current inputs again is no step
    assert got["pushed"] == [True, True, False, 2]
    assert got["back"] == [1, 0, None, False, True]
    assert got["forth"] == [1, 2, None, 2]
    # A step after an undo clears what could be redone
    assert got["cleared"] == [True, False, None, 2, 1, 0]
    # The same key replaces the open step until it is sealed; another key is a new step
    assert got["joined"] == [True, 1, 2]
    assert got["split"] == [3, 3, 2, 0]
    # Moves within 1000 ms are one step, 1001 ms apart two
    assert got["inside"] == [1, 2]
    assert got["outside"] == [2, 2, 0]
    # Undo and redo seal the step they reach: the next edit is a step of its own
    assert got["afterUndo"] == [2, 1]
    assert got["afterRedo"] == [2, 1]


def test_the_history_keeps_its_limit_and_rewrites_every_step(page: Any) -> None:
    got = js(
        page,
        HISTORY
        + """const filled = (history) => {
          history.reset({n: 0});
          for (let step = 1; step <= 150; step += 1) history.push({n: step});
          const steps = history.steps;
          let undone = 0;
          while (history.undo() !== null) undone += 1;
          return [steps, undone, history.current.n];
        };
        const told = createHistory();
        told.reset({n: 0});
        told.push({n: 1});
        told.push({n: 2});
        told.undo();
        told.rewrite((inputs) => ({...inputs, tidy: true}));
        return {
          limited: filled(createHistory({limit: 100})),
          small: filled(createHistory({limit: 3})),
          plain: filled(createHistory()),
          rewritten: [told.current, told.undo(), told.redo(), told.redo(),
                      told.canRedo],
        };""",
    )

    # 150 steps, 100 kept: the oldest state left is the one after step 50
    assert got["limited"] == [100, 100, 50]
    assert got["small"] == [3, 3, 147]
    assert got["plain"] == [100, 100, 50]
    # The steps before and after the current one are rewritten alike
    assert got["rewritten"] == [
        {"n": 1, "tidy": True},
        {"n": 0, "tidy": True},
        {"n": 1, "tidy": True},
        {"n": 2, "tidy": True},
        False,
    ]


def test_routes_through_cells_and_edges_through_nodes(page: Any) -> None:
    got = js(
        page,
        GEOMETRY
        + GUIDE_CELLS
        + """const routes = {
          straight: [[[0, 0], [3, 0]],
                     [[0, 0], [2, 0], [3, 0], [4, 0], [1, 1], [-1, 0]]],
          diagonal: [[[0, 0], [2, 2]], [[1, 1], [2, 2], [1, 0], [3, 3]]],
          corners: [[[0, 0], [0, 2], [2, 4]],
                    [[0, 1], [0, 2], [1, 3], [2, 4], [1, 2], [0, 3]]],
        };
        const through = [
          {id: 'A', type: 'subcatchment', from: null, position: {x: 0, y: 0}},
          {id: 'B', type: 'subcatchment', from: null, position: {x: 1, y: 0}},
          {id: 'OUT', type: 'outlet', from: ['A', 'B'], position: {x: 2, y: 0}},
        ];
        const kind = (n) =>
          (n.id === 'OUT' ? 'outlet' : n.from ? 'junction' : 'subcatchment');
        const placed = guide.map((n) => ({id: n.id, type: kind(n), from: n.from,
                                          position: {x: n.cell[0], y: n.cell[1]}}));
        return {
          on: Object.fromEntries(Object.entries(routes).map(([name, [route, cells]]) =>
            [name, cells.map((cell) => g.onRoute(route, cell))])),
          through: g.edgesThroughNodes(g.pictureOf(through, new Map())),
          guide: g.edgesThroughNodes(g.pictureOf(placed, new Map())),
        };""",
    )

    # On a segment, its ends and corners included; never beside or beyond it
    assert got["on"] == {
        "straight": [True, True, True, False, False, False],
        "diagonal": [True, True, False, False],
        "corners": [True, True, True, True, False, False],
    }
    assert got["through"] == [{"from": "A", "to": "OUT", "node": "B"}]
    # The library's layout runs no edge through a node
    assert got["guide"] == []


def test_every_reason_and_refusal_is_worded(page: Any) -> None:
    got = js(
        page,
        GRAPH
        + NODES
        + """const w = await import('./src/sections/siec/words.js');
        const details = {node_id: 'X', other_id: 'Y', upstream_id: 'U',
                         nodes: ['A', 'B'],
                         downstream: ['D'], type: 'reach', found: 2};
        const skeleton = [s('Z9'), s('Z8'), r('R7', 'Z9'), j('K4', 'R7'), j('J5', 'K4'),
                          o('OUT1', 'J5'), r('R6')];
        const refuse = (from, to) =>
          w.refusalText(gr.linkVerdict(skeleton, rules, from, to), skeleton, from, to);
        return {
          texts: gr.REASONS.map((reason) =>
            [reason, w.problemText({reason, ...details}, rules)]),
          refusals: {cycle: refuse('J5', 'R7'), outlet: refuse('OUT1', 'R6'),
                     source: refuse('R6', 'Z8'), full: refuse('Z8', 'R7')},
        };""",
    )

    texts = dict(got["texts"])
    unworded = [
        reason
        for reason, text in got["texts"]
        if not isinstance(text, str) or not text.strip() or "{" in text
    ]
    assert unworded == []
    assert "A → B → A" in texts["cycle"]
    assert "X" in texts["upstream_count"] and "2" in texts["upstream_count"]
    refusals = got["refusals"]
    assert "J5 → R7 → K4 → J5" in refusals["cycle"]
    assert "OUT1" in refusals["outlet"]
    assert "Z8" in refusals["source"]
    assert "R7" in refusals["full"] and "Z9" in refusals["full"]


def refusal_details(reach: Any, step_min: float = 5.0) -> dict[str, Any]:
    """Return the details of the library's refusal of a small flood by ``reach``."""
    times = [step_min * index for index in range(40)]
    flows = [
        10.0 * math.sin(math.pi * min(index, 20) / 20) + 0.1 for index in range(40)
    ]
    with pytest.raises(InvalidParameterError) as refused:
        reach.route(Hydrograph(times_min=times, discharge_m3s=flows))
    details: dict[str, Any] = refused.value.details
    assert details["reason"] == "unstable_timestep"
    return {**details, "node_id": "R1"}


def test_a_refusal_at_the_time_step_says_why_and_the_lag_that_stands_in(
    page: Any,
) -> None:
    flat = refusal_details(
        MuskingumCungeReach(0.0504, 0.0001, manning_n=0.04, bottom_width_m=5)
    )
    tiny = refusal_details(
        MuskingumCungeReach(0.005, 0.0001, manning_n=0.04, bottom_width_m=5)
    )
    window = refusal_details(MuskingumReach(k_min=60, x=0.2, subreaches=100))
    # routing/cunge.py's refusal of more than MAX_ORDINATES ordinates (a million: too
    # many to build here)
    ordinates = {
        "option": "times_min",
        "reason": "unstable_timestep",
        "timestep_min": 0.5,
        "substeps": 60,
        "maximum": 1_000_000,
        "node_id": "R1",
    }
    got = js(
        page,
        """const w = await import('./src/sections/siec/words.js');
        const cases = arguments_;
        return Object.fromEntries(Object.entries(cases).map(([name, details]) =>
          [name, {text: w.problemText(details), lag: w.lagMinutes(details),
                  ordinates: w.tooManyOrdinates(details)}]));""".replace(
            "arguments_",
            json.dumps(
                {"flat": flat, "tiny": tiny, "window": window, "ordinates": ordinates}
            ),
        ),
    )

    step = (
        "Krok czasowy sieci jest w kroku 1 „Sieć”, w polu „Krok czasowy”; puste pole "
        "to krok domyślny"
    )
    assert all(step in case["text"] for case in got.values())
    assert got["flat"]["text"].startswith(
        "Węzeł R1: odcinek 50,4 m jest za krótki albo za płaski dla metody "
        "Muskingum-Cunge"
    )
    assert "zmiana kroku nie pomoże" in got["flat"]["text"]
    # The wave's travel time in whole minutes, at least one
    assert got["flat"]["lag"] == max(1, round(50.4 / flat["celerity_m_per_s"] / 60))
    assert got["tiny"]["lag"] == 1
    assert got["window"]["lag"] is None and got["ordinates"]["lag"] is None
    assert got["window"]["text"].startswith(
        "Węzeł R1: krok czasowy jest za długi dla parametrów tej metody."
    )
    assert got["ordinates"]["text"].startswith(
        "Węzeł R1: przy kroku 0,5 min odcinek wymaga podziału kroku na 60 części"
    )
    assert [case["ordinates"] for case in got.values()] == [False, False, False, True]


def scattered_network(size: int, seed: int) -> list[dict[str, Any]]:
    """Return the structure of a random tree whose nodes stand on random free cells."""
    root, inflows = random_tree(size, seed, fan_in=3, deep=0.4)
    rng = random.Random(seed)
    side = int(math.sqrt(size)) + 4
    cells = rng.sample([(x, y) for x in range(side) for y in range(side)], len(inflows))
    nodes = []
    for (node, ups), (x, y) in zip(inflows.items(), cells, strict=True):
        kind = "outlet" if node == root else "junction" if ups else "subcatchment"
        nodes.append(
            {
                "id": node,
                "type": kind,
                "from": ups or None,
                "position": {"x": x, "y": y},
            }
        )
    return nodes


def test_the_work_kept_per_structure_equals_the_plain_one(page: Any) -> None:
    # A network of 300 nodes on random cells: lines cross and run through nodes
    nodes = scattered_network(300, 11)
    # and a loop: a junction's first inflow lists the junction, whose links are refused
    # with the loop named
    junction = next(node for node in nodes if node["type"] == "junction")
    up = next(at for at, node in enumerate(nodes) if node["id"] == junction["from"][0])
    nodes[up] = {**nodes[up], "from": [*(nodes[up]["from"] or []), junction["id"]]}
    got = js(
        page,
        GEOMETRY
        + GRAPH
        + f"const nodes = {json.dumps(nodes)};\n"
        + """const sources = nodes.filter((n, at) => at % 15 === 0).map((n) => n.id);
        const links = sources.every((from) => {
          const all = gr.linkVerdicts(nodes, rules, from);
          const one = (to) => gr.linkVerdict(nodes, rules, from, to);
          return nodes.every((n) => n.id === from
            || JSON.stringify(all.get(n.id)) === JSON.stringify(one(n.id)));
        });
        const picture = g.pictureOf(nodes, new Map());
        const grid = picture.nodes.map((n) =>
          ({id: n.id, col: n.cell[1], row: n.cell[0]}));
        const lines = picture.edges.map((e) =>
          ({points: e.route.map(([x, y]) => [y, x])}));
        const index = g.crowdIndex(grid, lines);
        let crowded = 0;
        const counts = grid.every((n) => g.PLACES.every((place) => {
          const plain = g.crowding(n, place, grid, lines);
          crowded += plain;
          return g.crowding(n, place, grid, lines, index) === plain;
        }));
        const loops = gr.graphProblems(nodes, rules)
          .filter((p) => p.reason === 'cycle').length;
        return {links, counts, crowded, loops, sources: sources.length};""",
    )
    assert got["loops"] == 1
    assert got["sources"] == 20
    # The verdicts of every target at once are linkVerdict's, one by one
    assert got["links"] is True
    # The labels' crowding through the index counts what the plain count counts
    assert got["crowded"] > 300
    assert got["counts"] is True


# The rainfall of step 2 and of Sieć's network (plan 2026-11-10-network-wizard, D4):
# `rainfall` of hydrolog-network/1 to the inputs of the step and back.
RAINFALL = """const mp = await import('./src/handoff/mapping.js');
const hs = await import('./src/sections/hydrogram/state.js');
const of = (patch) => ({...hs.initialRain(), ...patch});
const design = {kind: 'design', hietogram_type: 'block', total_mm: 30,
                duration_min: 60};
const series = {kind: 'series', depths_mm: [1.5, 2, 0.5], timestep_min: 10};
const storm = {kind: 'design', hietogram_type: 'beta', total_mm: 105, duration_min: 720,
               alpha: 2, beta: 5};
const own = {rainfall: {source: 'pmaxtp', latitude: 51.0154, longitude: 15.89,
                        probability_percent: 1, duration_min: 720, method: 'AMP'}};
const shed = {rainfall: {source: 'pmaxtp', probability_percent: 1, duration_min: 720},
              watershed: {source: 'hydrograf', latitude: 51.0154, longitude: 15.89}};
const back = (rainfall, origin) => mp.rainfallInputs(rainfall, origin);
const again = (rainfall, origin) => mp.rainfallOf(of(back(rainfall, origin)));
return {
  design: back(design), series: back(series), none: back(null),
  noneAtShed: back(null, shed), own: back(storm, own), shed: back(storm, shed),
  otherDuration: back({...storm, duration_min: 60}, own).rain_source,
  noPoint: back(storm, {rainfall: {...shed.rainfall}}).rain_source,
  round: [again(design), again(series), again(storm, own), again(storm)],
  unfetched: again(storm, shed),
  kinds: ['none', 'network'].map((source) => mp.rainfallOf(of({rain_source: source}))),
};"""


def test_a_rainfall_goes_to_the_steps_inputs_and_back(page: Any) -> None:
    got = js(page, RAINFALL)
    shape = {"hietogram_type": "block", "alpha": "", "beta": "", "peak_position": ""}
    assert got["design"] == {
        "rain_source": "design",
        "total_mm": "30",
        "duration_min": "60",
        **shape,
    }
    # A series keeps its step as the time step
    assert got["series"] == {
        "rain_source": "series",
        "values": "1,5; 2; 0,5",
        "timestep_min": "10",
    }
    # No rainfall is „Brak”, with the watershed's point ready for PMAXTP
    assert got["none"] == {"rain_source": "none"}
    assert got["noneAtShed"] == {
        "rain_source": "none",
        "pmaxtp_latitude": "51,0154",
        "pmaxtp_longitude": "15,89",
    }
    # PMAXTP: the record's own point keeps the depth as fetched there
    pmaxtp = {
        "rain_source": "pmaxtp",
        "pmaxtp_latitude": "51,0154",
        "pmaxtp_longitude": "15,89",
        "pmaxtp_probability_pct": "1",
        "pmaxtp_duration_min": "720",
        "total_mm": "105",
        "duration_min": "720",
        "hietogram_type": "beta",
        "alpha": "2",
        "beta": "5",
        "peak_position": "",
    }
    assert got["own"] == {
        **pmaxtp,
        "pmaxtp_method": "AMP",
        "pmaxtp_fetched": {
            "latitude": 51.0154,
            "longitude": 15.89,
            "duration_min": 720,
            "probability_percent": 1,
            "method": "AMP",
            "depth_mm": 105,
        },
    }
    # The watershed's point only: the page fetches the depth there
    assert got["shed"] == {**pmaxtp, "pmaxtp_method": "POT"}
    # Another duration, or no point at all: a design hyetograph
    assert got["otherDuration"] == "design"
    assert got["noPoint"] == "design"
    # Back to the document: the same rainfall, PMAXTP's depth as its total
    design = {"kind": "design", "hietogram_type": "block"}
    assert got["round"] == [
        {**design, "total_mm": 30, "duration_min": 60},
        {"kind": "series", "depths_mm": [1.5, 2, 0.5], "timestep_min": 10},
        {
            "kind": "design",
            "hietogram_type": "beta",
            "total_mm": 105,
            "duration_min": 720,
            "alpha": 2,
            "beta": 5,
        },
        {
            "kind": "design",
            "hietogram_type": "beta",
            "total_mm": 105,
            "duration_min": 720,
            "alpha": 2,
            "beta": 5,
        },
    ]
    # PMAXTP before its fetch has no depth yet
    assert got["unfetched"] == {
        "kind": "design",
        "hietogram_type": "beta",
        "duration_min": 720,
        "alpha": 2,
        "beta": 5,
    }
    # „Brak” and „Jak w sieci” are no rainfall of their own
    assert got["kinds"] == [None, None]


# RainStep for a subcatchment in Sieć: „Jak w sieci” with the network's rainfall in
# words and its link, and the network's time step shown read-only.
RAIN_STEP = """const hs = await import('./src/sections/hydrogram/state.js');
const { html, render } = await import('./src/html.js');
const { RainStep } = await import('./src/sections/hydrogram/rain-step.js');
const host = document.createElement('div');
document.body.append(host);
let opened = 0;
let patches = [];
render(html`<${RainStep} prefix="sn" title="Hietogram"
  kinds=${['network', 'pmaxtp', 'design', 'series']}
  inputs=${{...hs.initialRain(), rain_source: 'network'}}
  errors=${{}} warnings=${{}} required=${{}} set=${(patch) => patches.push(patch)}
  pmaxtp=${{depth: null, busy: false, onRetry: null}} timestep=${{network: '10'}}
  network=${{words: 'Opad sieci z kroku 1 · Hietogram: 30 mm · 1 h.',
             onOpen: () => { opened += 1; }}}
  infoValues=${{}} valuesField=${null} />`, host);
const step = host.querySelector('#sn-timestep_min');
host.querySelector('[data-goto="network-rain"]').click();
host.querySelector('[role="radio"][aria-checked="false"]').click();
const got = {
  part: host.querySelector('[data-rain-part]').dataset.rainPart,
  title: host.querySelector('#sn-rain-title').textContent,
  radios: [...host.querySelectorAll('[role="radio"]')].map((radio) =>
    [radio.textContent.trim(), radio.getAttribute('aria-checked')]),
  note: host.querySelector('[data-rain="network"]').textContent.trim(),
  step: [step.value, step.readOnly,
         step.closest('[data-field]').querySelector('.key').textContent],
  fields: ['pmaxtp_latitude', 'total_mm', 'values']
    .filter((name) => host.querySelector(`#sn-${name}`)),
  opened, patches,
};
render(null, host);
host.remove();
return got;"""


def test_the_rain_step_of_a_subcatchment_shows_the_networks_rainfall(
    page: Any,
) -> None:
    got = js(page, RAIN_STEP)
    assert got["part"] == "sn"
    assert got["title"] == "Hietogramjak w sieci"
    assert got["radios"] == [
        ["Jak w sieci", "true"],
        ["PMAXTP", "false"],
        ["Hietogram", "false"],
        ["Własna seria", "false"],
    ]
    assert got["note"] == (
        "Opad sieci z kroku 1 · Hietogram: 30 mm · 1 h. Opad sieci w kroku 1"
    )
    # Δt is the network's, shown and not edited; no field of an own rainfall
    assert got["step"] == ["10", True, "timestep_min · krok sieci"]
    assert got["fields"] == []
    # The link opens the network's rainfall; another source is a patch of the inputs
    assert got["opened"] == 1
    assert got["patches"] == [{"rain_source": "pmaxtp"}]


# A subcatchment of hydrolog-network/1 and Hydrogram's inputs (plan
# 2026-11-10-network-wizard, D3, D11): each model choice's inputs written as a node and
# read back, the guide's subcatchments read and written, and a hand-off's read with its
# record and written.
SUBCATCHMENT = """async ([stored, choices, runoff, guide, handoff]) => {
  const mp = await import('./src/handoff/mapping.js');
  const hs = await import('./src/sections/hydrogram/state.js');
  const f = await import('./src/format.js');
  const typed = Object.fromEntries(
    Object.entries(runoff).map(([name, value]) => [name, f.inputText(value)]));
  const inputsOf = (choice) => hs.normalize({
    ...stored, ...typed,
    uh_model: choice.model,
    tc_manual: choice.tc === 'manual',
    tc_method: choice.tc && choice.tc !== 'manual' ? choice.tc : 'kirpich',
    clark_kind: choice.clark || 'ratio',
    nash_source: choice.nash || 'lutz',
  });
  const placeOf = (node) => ({id: node.id, from: node.from,
    description: node.description, position: node.position});
  const sent = (inputs) => {
    const {timestep_min, ...options} = hs.toOptions(hs.normalize(inputs));
    return options;
  };
  const sub = handoff.payload.nodes.find((node) => node.type === 'subcatchment');
  return {
    choices: choices.map((choice) => {
      const inputs = inputsOf(choice);
      const node = mp.subcatchmentNode(inputs, {id: 'Z1'});
      const back = mp.subcatchmentInputs(node);
      return {node, again: mp.subcatchmentNode(back, {id: 'Z1'}),
              sent: sent(inputs), back: sent(back)};
    }),
    guide: guide.nodes.filter((node) => node.runoff)
      .map((node) => mp.subcatchmentNode(mp.subcatchmentInputs(node), placeOf(node))),
    handed: mp.subcatchmentNode(
      mp.subcatchmentInputs(sub, {origin: handoff}), placeOf(sub)),
  };
}"""


def test_a_subcatchment_goes_to_hydrograms_inputs_and_back(page: Any) -> None:
    handoff = json.loads((FIXTURES / "handoff_hydrograf.json").read_text("utf-8"))
    guide = example_network_document()
    got = page.evaluate(
        SUBCATCHMENT,
        [kamiennik_inputs(), CHOICES, RUNOFF_VALUES, guide, handoff],
    )
    for choice, item in zip(CHOICES, got["choices"], strict=True):
        # A node written of a choice reads back to the same node, and its inputs send
        # what they sent (the time step is the network's, not the node's)
        assert item["again"] == item["node"], choice
        assert item["back"] == item["sent"], choice
        assert item["node"]["runoff"]["uh_model"] == choice["model"], choice
    # The guide's subcatchments come back with the library's defaults written out
    written = as_written(guide)
    assert got["guide"] == [node for node in written["nodes"] if "runoff" in node]
    # Hydrograf's subcatchment, read with its record: as handed, but for the fields no
    # step shows for SCS (its channel's slope and Lc), its PMAXTP depth kept
    handed = as_written(
        handoff["payload"], frozenset({"channel_slope_m_per_m", "Lc_km"})
    )
    assert got["handed"] == handed["nodes"][0]


# The origin of each node of a network hand-off (plan 2026-11-10-network-wizard, D9):
# Nogat's second example and Hydrograf's own network (tests/fixtures), read and written
# again by Sieć's state as opening, editing, renaming and adding change it.
ORIGINS = """async ([nogat, hydrograf]) => {
  const mp = await import('./src/handoff/mapping.js');
  const st = await import('./src/sections/siec/state.js');
  const ed = await import('./src/sections/siec/editor/edits.js');
  const unknown = {...nogat, node_provenance: {...nogat.node_provenance,
    X9: {node: {source: 'hydrograf'}}}};
  const open = (doc) => st.stateOf(doc.payload,
    {name: 'x.json', kind: 'handoff', handoff: mp.siecReceived(doc, doc.payload)});
  const opened = open(nogat);
  const plain = (nodes) => ({schema: 'hydrolog-network/1', nodes});
  const handed = plain(nogat.payload.nodes);
  // Z2 renamed, Z1's CN and Z3's model changed, R1 given its section, Z4 drawn
  let state = ed.renameNode(opened, 'Z2', 'Z9');
  const nodes = state.nodes;
  state = {
    ...state,
    skeleton: [...state.skeleton, {id: 'Z4', type: 'subcatchment', from: null}],
    nodes: {
      ...nodes,
      Z1: {...nodes.Z1, watershed: {...nodes.Z1.watershed, cn: '70'}},
      Z3: {...nodes.Z3, uh_model: 'nash'},
      Z4: {'#variant': 'rain', watershed: {area_km2: '3'}, uh_model: 'scs'},
    },
  };
  const sectioned = plain(nogat.payload.nodes.map((node) => (node.id === 'R1'
    ? {...node, manning_n: 0.035, bottom_width_m: 8} : node)));
  const designed = {...state, network: {...state.network, rain_source: 'design'}};
  const joined = mp.siecAddition(opened, hydrograf);
  return {
    origins: mp.nodeOrigins(unknown),
    unknown: mp.unknownOrigins(unknown),
    note: mp.unknownOriginsNote(unknown),
    kept: mp.siecReceived(unknown, unknown.payload).node_provenance,
    same: {provenance: mp.siecProvenance(opened),
           nodes: mp.siecNodeProvenance(opened, handed)},
    edited: {provenance: mp.siecProvenance(state),
             nodes: mp.siecNodeProvenance(state, sectioned)},
    designed: {provenance: mp.siecProvenance(designed),
               nodes: mp.siecNodeProvenance(designed, sectioned)},
    joined: {added: joined.added, lines: joined.lines,
             nodes: mp.siecNodeProvenance(joined.inputs, handed)},
    words: ['Z1', 'Z2', 'Z3', 'J1', 'R1', 'J2', 'J5'].map((id) => {
      const entry = hydrograf.node_provenance[id];
      return mp.originWords(entry.watershed || entry.node);
    }),
    // Where a line of BDOT10k runs along a reach, Hydrograf adds its check length
    checked: mp.originWords({...hydrograf.node_provenance.R1.node,
      vector_length_km: 0.36, vector_source: 'bdot10k'}),
  };
}"""


def test_node_origins_are_read_shown_and_written_as_nogat_orders(page: Any) -> None:
    nogat = json.loads(
        (FIXTURES.parents[1] / "schemas" / "nogat" / "handoff-1.schema.json").read_text(
            "utf-8"
        )
    )["examples"][1]
    hydrograf = json.loads(
        (FIXTURES / "handoff_hydrograf_network.json").read_text("utf-8")
    )
    got = page.evaluate(ORIGINS, [nogat, hydrograf])
    own = nogat["node_provenance"]
    provenance = nogat["provenance"]
    # A node's entry wins over provenance, input by input; J2 and OUT take provenance;
    # a key that names no node is left out and said
    assert got["origins"]["Z1"] == {**provenance, **own["Z1"]}
    assert got["origins"]["R1"] == {**provenance, "node": own["R1"]["node"]}
    assert got["origins"]["J2"] == provenance
    assert got["origins"]["OUT"] == provenance
    assert "X9" not in got["origins"]
    assert got["unknown"] == ["X9"]
    assert got["note"] == [
        "Pominięto pochodzenie węzłów, których nie ma w sieci przekazania "
        "(node_provenance): X9."
    ]
    assert got["kept"] == own
    # Unchanged, the network's hand-off writes what it received
    assert got["same"] == {"provenance": provenance, "nodes": own}
    # Edited: the renamed node keeps its entry under its new id, a changed watershed
    # or reach names its changed fields, an edited runoff is the person's, and the
    # drawn Z4 is the person's where provenance would claim its watershed
    assert got["edited"]["provenance"] == provenance
    assert got["edited"]["nodes"] == {
        "Z1": {"watershed": {**own["Z1"]["watershed"], "changed": ["cn"]}},
        "Z9": own["Z2"],
        "J1": own["J1"],
        "R1": {
            "node": {**own["R1"]["node"], "changed": ["manning_n", "bottom_width_m"]}
        },
        "Z3": {**own["Z3"], "runoff": {"source": "user"}},
        "Z4": {"watershed": {"source": "user"}},
    }
    # Another rainfall of the network is the person's; the nodes that take it say
    # nothing of their own
    assert got["designed"]["provenance"] == {
        **provenance,
        "rainfall": {"source": "user"},
    }
    assert got["designed"]["nodes"] == got["edited"]["nodes"]
    # Added to the open network, Hydrograf's subcatchments renamed on the clash keep
    # their origins (their hand-off's provenance where they have no entry)
    subcatchments = [
        node["id"]
        for node in hydrograf["payload"]["nodes"]
        if node["type"] == "subcatchment"
    ]
    assert got["joined"]["added"] == ["Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10", "Z11"]
    assert got["joined"]["nodes"] == {
        **own,
        **{
            new: hydrograf["node_provenance"][old]
            for new, old in zip(got["joined"]["added"], subcatchments, strict=True)
        },
    }
    # Hydrograf's elements in words
    assert [item["what"] for item in got["words"]] == [
        "zlewnia górna",
        "dopływ do ujścia przy punkcie P3",
        "przyrzecze odcinka R1",
        "zbieg",
        "odcinek",
        "punkt kontrolny P4",
        "przekrój zamykający A",
    ]
    assert got["words"][4]["details"] == [
        "długość wzdłuż spływu",
        "spadek z NMT",
        "NMT 128,6 → 123,8 m n.p.m.",
    ]
    assert got["checked"]["details"][-1] == "długość kontrolna 0,36 km (BDOT10k)"
