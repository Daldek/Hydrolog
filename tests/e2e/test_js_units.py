"""The pure JavaScript modules of the GUI (plan D9, D11, D16, slice S2) in Chromium.

No Node toolchain (D17): each test opens the page of the real server and imports
the modules there. ``format.js`` writes Polish numbers (D9); ``forms/model.js``
turns REAL catalog documents (fetched from ``api/commands``) into fields, checks
and the options of a run, and honours ``requires``, ``excludes``, ``section`` and
``format`` (D11) on a fixture command, as Hydrolog's catalog has none; catalog
examples go through the form to ``api/run`` and run. ``router.js``,
``persist.js``, ``labels/errors.js`` and ``labels/notices.js`` (on errors of the
real server), ``ui/info.js``, Polecenia's ``state.js`` and
``forms/result-view.js`` (on real envelopes) follow.
"""

import math
from typing import Any

import pytest

from tests.e2e.conftest import Tab

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


def test_catalog_examples_fill_the_form_and_run(page: Any) -> None:
    got = js(
        page,
        """const lagModel = m.fieldModel(await doc('route lag'));
        const lagCalls = (await doc('route lag')).commands[0].examples
          .map((e) => e.call);
        const outputs = m.fieldModel(await doc('route network')).fields
          .filter((x) => x.kind === 'file-out').map(m.defaultOutputName);
        const runs = [];
        for (const name of ['uh nash', 'scs effective']) {
          const catalog = await doc(name);
          for (const example of catalog.commands[0].examples) {
            const values = m.valuesFromCall(m.fieldModel(catalog), example.call);
            const model = m.fieldModel(catalog, {values});
            const options = m.toOptions(model, values);
            const answer = await run(name, options);
            runs.push({name, chosen: values['#one_of'],
              problems: m.validate(model, values), options, status: answer.status,
              outcome: answer.body.status, inputs: answer.body.inputs});
          }
        }
        return {
          words: [
            m.shellWords(`a 'b c' "d \\\\"e\\\\" \\\\$x" f\\\\ g "" ''  h`),
            m.shellWords(`--x=1 "it's" 'a\\\\b'`),
          ],
          lag: [m.valuesFromCall(lagModel, lagCalls[0]),
                m.valuesFromCall(lagModel, lagCalls[0], ['in/flood_inflow.csv']),
                m.valuesFromCall(lagModel, lagCalls[1])],
          own: m.valuesFromCall(lagModel, `hydrolog route lag --lag-min=12.5
            --times-min '0,10' --discharge-m3s "1.5,2" --output dir/sub/o.csv
            --force --no-check --unknown 3`),
          chips: m.valuesFromCall(m.fieldModel(await doc('stats flood-frequency')),
            'hydrolog stats flood-frequency --values 1,2'
            + ' --dates 2020-01-01,2020-01-02'),
          outputs,
          fallback: m.defaultOutputName({name: 'report', examples: []}),
          runs,
        };""",
    )
    assert got["words"] == [
        ["a", "b c", 'd "e" $x', "f g", "", "", "h"],
        ["--x=1", "it's", "a\\b"],
    ]
    # route lag's first example reads a file: the form opens on „Plik”, the file
    # left to be uploaded unless the session holds one of that name.
    empty, held, series = got["lag"]
    assert empty == {
        "lag_min": "30",
        "input_file": "",
        "output": "outflow.csv",
        "#one_of": 1,
    }
    assert held["input_file"] == "in/flood_inflow.csv" and held["#one_of"] == 1
    assert series == {
        "lag_min": "25",
        "times_min": "0; 10; 20; 30; 40; 50; 60; 70",
        "discharge_m3s": "0; 10; 40; 90; 60; 30; 10; 0",
        "#one_of": 0,
    }
    assert got["own"] == {
        "lag_min": "12,5",
        "times_min": "0; 10",
        "discharge_m3s": "1,5; 2",
        "output": "o.csv",
        "force": True,
        "check": False,
        "#one_of": 0,
    }
    assert got["chips"] == {
        "values": "1; 2",
        "dates": ["2020-01-01", "2020-01-02"],
        "#one_of": 0,
    }
    assert got["outputs"] == ["network_out", "network.svg"]
    assert got["fallback"] == "report"
    # Every example of uh nash (one per parameter group) and scs effective goes
    # through the form unchanged and runs on the server.
    assert [(item["name"], item["chosen"]) for item in got["runs"]] == [
        ("uh nash", 0),
        ("uh nash", 1),
        ("uh nash", 2),
        ("scs effective", 0),
        ("scs effective", 0),
        ("scs effective", 1),
    ]
    for item in got["runs"]:
        assert item["problems"] == {}, item
        assert (item["status"], item["outcome"]) == (200, "ok"), item
        assert item["inputs"].items() >= item["options"].items(), item
    assert got["runs"][1]["options"]["lutz_urban_pct"] == 5
    assert got["runs"][5]["options"]["values"] == [2.5, 5, 12.5, 15, 8, 4, 3]


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
    assert got["keys"] == ["hydrolog-gui/polecenia/1", "hydrolog-gui/layout/2"]
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
        {"text": "Something odd" + EN, "english": True},
    ]


def test_ranges_of_applicability(page: Any) -> None:
    # Ranges as Hydrolog serves them (`typical_ranges` of a command's catalog document)
    got = js(
        page,
        """const range = {minimum: 0, maximum: 80};
        const slope = {method: 'kirpich', parameter: 'slope_m_per_m',
          inputs: ['channel_slope_m_per_m', 'mean_slope_m_per_m'], minimum: 0.03,
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
          value: [info.rangeValue(slope, {channel_slope_m_per_m: 0.0142,
                    mean_slope_m_per_m: 0.082}),
                  info.rangeValue(slope, {mean_slope_m_per_m: 0.082}),
                  info.rangeValue(slope, {channel_slope_m_per_m: '0,02'}),
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
    assert got["value"] == [
        {"field": "channel_slope_m_per_m", "value": 0.0142},
        {"field": "mean_slope_m_per_m", "value": 0.082},
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
