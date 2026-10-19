"""Guide for AI agents (spec 7.3): AGENTS.md, llms.txt, ``commands guide``.

``AGENTS.md`` and ``llms.txt`` in the repository root are derived files: the drift
tests compare their bytes with the generator, also through the documented command.
The rest checks that the guide says what the catalog says (commands, options, effects,
errors), that its flows really run, and that nothing in it points at a file, a command
or an option that does not exist.
"""

import json
import os
import re
import shlex
import shutil
import threading
import tomllib
from fnmatch import fnmatch
from importlib.util import find_spec
from pathlib import Path
from typing import get_args

import pytest

from hydrolog import agent_guide as guide_module
from hydrolog.agent_guide import (
    _ERROR_ADVICE,
    _FLOWS,
    _GROUP_TITLES,
    _PRINCIPLES,
    _checked,
    _Flow,
    _render,
    _Step,
    GuideFormat,
    agent_guide,
    principles,
)
from hydrolog.catalog import (
    command_schema,
    data_commands,
    get_command,
    run_command,
    validate_command,
)
from hydrolog.catalog.dispatch import COMMANDS_SCHEMA
from hydrolog.catalog.envelope import RESULT_SCHEMA, FileRecord, Notice, sha256_file
from hydrolog.cli.main import main
from hydrolog.cli.parser import parse_command_line
from hydrolog.operations import commands_guide
from hydrolog.exceptions import (
    ERROR_CODES,
    ERROR_SCHEMA,
    ForbiddenPathError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
    error_document,
)

REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY / "tests" / "fixtures"
GUIDES = {"AGENTS.md": "agents", "llms.txt": "llms"}
LANGS = ["pl", "en"]
COMMANDS = data_commands()
GROUPS = list(dict.fromkeys(command.group for command in COMMANDS))
# Commands of other tools whose name looks like one of ours (group ``soil``).
FOREIGN_COMMANDS = {"soil download"}


@pytest.fixture(autouse=True)
def no_ambient_language(monkeypatch):
    """The developer's ``HYDROLOG_LANG`` must not reach the CLI."""
    monkeypatch.delenv("HYDROLOG_LANG", raising=False)


def text(format: str = "agents", lang: str = "pl") -> str:
    return agent_guide(format, lang)


def rows(markdown: str) -> list[list[str]]:
    """Cells of every table row of ``markdown`` (separator rows included)."""
    return [
        re.split(r"(?<!\\) \| ", line[2:-2])
        for line in markdown.splitlines()
        if line.startswith("| ") and line.endswith(" |")
    ]


def section(markdown: str, heading: str) -> str:
    """Text of the ``## heading`` section, up to the next ``## `` heading."""
    start = markdown.index(f"\n## {heading}\n")
    end = markdown.find("\n## ", start + 1)
    return markdown[start : None if end < 0 else end]


def command_rows(markdown: str) -> list[list[str]]:
    """The rows of the command tables: five cells, the first one a code span."""
    return [
        cells
        for cells in rows(markdown)
        if len(cells) == 5 and re.fullmatch(r"`[a-z]+ [a-z-]+`", cells[0])
    ]


def code_spans(markdown: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", markdown)


# --- derived files of the repository ---------------------------------------------------


@pytest.mark.parametrize(("name", "format"), GUIDES.items())
def test_repository_guides_are_the_bytes_of_the_generator(name, format):
    expected = text(format).encode("utf-8")

    assert (REPOSITORY / name).read_bytes() == expected, (
        f"{name} differs from the generator; regenerate it: hydrolog commands guide "
        f"--format {format} --lang pl --path {name}"
    )


@pytest.mark.parametrize(("name", "format"), GUIDES.items())
def test_the_documented_command_regenerates_the_repository_file(
    name, format, tmp_path, capsys
):
    """``--format F --lang pl --path FILE`` (the command in the guide) gives the file."""
    target = tmp_path / name

    code = main(
        ["commands", "guide", "--format", format, "--lang", "pl"]
        + ["--path", str(target)]
    )

    assert code == 0, capsys.readouterr().err
    assert target.read_bytes() == (REPOSITORY / name).read_bytes()


@pytest.mark.parametrize("format", GUIDES.values())
@pytest.mark.parametrize("lang", LANGS)
def test_guide_is_plain_deterministic_text(format, lang, tmp_path, monkeypatch):
    first = text(format, lang)
    monkeypatch.chdir(tmp_path)

    again = text(format, lang)

    assert again == first
    assert first.endswith("\n") and not first.endswith("\n\n")
    assert "\r" not in first
    assert all(line == line.rstrip() for line in first.splitlines())
    assert "<!-- hydrolog:" not in first
    assert str(tmp_path) not in first and str(REPOSITORY) not in first
    unlinked = re.sub(r"https://\S+", "", first)  # a link may carry a date
    assert not re.search(r"\b20\d\d-\d\d-\d\d\b", unlinked)  # no generation date


# --- the catalog in the guide ----------------------------------------------------------


@pytest.mark.parametrize("lang", LANGS)
def test_commands_table_follows_the_catalog(lang):
    """Every command, once, in catalog order, with its tool, summary, options, effect."""
    table = command_rows(text("agents", lang))

    assert [cells[0] for cells in table] == [f"`{c.name}`" for c in COMMANDS]
    for command, cells in zip(COMMANDS, table, strict=True):
        schema = command_schema(command, lang=lang)["commands"][0]
        properties = schema["input_schema"]["properties"]
        required = set(schema["input_schema"].get("required", ()))
        assert cells[1] == f"`{command.operation_id}`"
        assert cells[2] == schema["summary"]
        for name, prop in properties.items():
            word = name + ("*" if name in required else "")
            if "default" in prop:
                default = prop["default"]
                word += "=" + (
                    default
                    if isinstance(default, str)
                    else json.dumps(default, separators=(",", ":"))
                )
            assert f"`{word}`" in cells[3], (command.name, word)
        for alternative in schema["input_schema"].get("oneOf", ()):
            assert "+".join(f"`{n}`" for n in alternative["required"]) in cells[3]
        assert ("(exactly one" in cells[3]) == (lang == "en" and bool(command.one_of))
        assert ("(dokładnie" in cells[3]) == (lang == "pl" and bool(command.one_of))


@pytest.mark.parametrize("lang", LANGS)
def test_effect_column_tells_what_a_command_writes(lang):
    reading = "read" if lang == "en" else "odczyt"
    table = {cells[0]: cells[4] for cells in command_rows(text("agents", lang))}

    for command in COMMANDS:
        effect = table[f"`{command.name}`"]
        outputs = [option for option in command.options if option.writes]
        if not outputs:
            assert effect == reading
            continue
        assert all(f"`{option.name}`" in effect for option in outputs)
        starts_with_read = effect.startswith(reading + ";")
        assert starts_with_read == (not any(option.required for option in outputs))


@pytest.mark.parametrize("lang", LANGS)
def test_every_group_has_a_titled_section(lang):
    guide = text("agents", lang)

    for group in GROUPS:
        assert group in _GROUP_TITLES, f"add the title of the group {group!r}"
        title = _GROUP_TITLES[group][1 if lang == "en" else 0]
        assert f"\n### `{group}` — {title}\n" in guide
    assert set(_GROUP_TITLES) == set(GROUPS)


@pytest.mark.parametrize("lang", LANGS)
def test_error_table_is_the_registry(lang):
    guide = text("agents", lang)
    table = [cells for cells in rows(guide) if len(cells) == 4]

    assert set(_ERROR_ADVICE) == set(ERROR_CODES)
    assert [cells[0] for cells in table[1:]] == [f"`{code}`" for code in ERROR_CODES]
    for cells, spec in zip(table[1:], ERROR_CODES.values(), strict=True):
        title = spec.title_en if lang == "en" else spec.title
        assert cells[1:3] == [title, str(spec.exit_code)]
        assert len(cells[3]) > 40  # says what to do, not just the code
    for spec in ERROR_CODES.values():
        assert f"`{spec.code}` ({spec.exit_code})" in text("llms", lang)


@pytest.mark.parametrize("lang", LANGS)
def test_envelope_and_error_document_fields_are_all_documented(lang):
    """A field added to the envelope or the error document must be added to the guide."""
    guide = text("agents", lang)
    envelope = run_command("commands list").to_dict()
    envelope["files"] = [FileRecord("/x", "00").to_dict()]
    envelope["notices"] = [Notice("info", "code", "text").to_dict()]
    error = error_document(NotFoundError("x"), "tc kirpich", lang)
    fields = {
        *envelope,
        *envelope["files"][0],
        *envelope["notices"][0],
        *error,
    }

    for field in fields:
        assert f'"{field}"' in guide, field


@pytest.mark.parametrize("format", GUIDES.values())
@pytest.mark.parametrize("lang", LANGS)
def test_schema_names_are_the_current_ones(format, lang):
    allowed = {RESULT_SCHEMA, ERROR_SCHEMA, COMMANDS_SCHEMA}

    mentioned = set(
        re.findall(r"hydrolog-(?:result|error|commands)/\d+", text(format, lang))
    )

    assert mentioned and mentioned <= allowed
    assert {RESULT_SCHEMA, ERROR_SCHEMA} <= mentioned


# --- the rules --------------------------------------------------------------------------


@pytest.mark.parametrize("lang", LANGS)
def test_both_guides_carry_every_rule_in_order(lang):
    rules = principles(lang)
    expected = "\n".join(f"{n}. {rule}" for n, rule in enumerate(rules, start=1))

    assert 5 <= len(rules) == len(_PRINCIPLES) <= 7
    for format in GUIDES.values():
        assert f"\n{expected}\n" in text(format, lang)


def test_the_rules_name_options_and_commands_of_the_catalog():
    """``{opt:...}`` and ``{cmd:...}`` are replaced by names that exist."""
    commands = data_commands()

    assert _checked("`{opt:input_file}` `{cmd:tc kirpich}`", commands) == (
        "`input_file` `tc kirpich`"
    )
    with pytest.raises(ValueError, match="option 'no_such_option'"):
        _checked("{opt:no_such_option}", commands)
    with pytest.raises(ValueError, match="command 'tc nope'"):
        _checked("{cmd:tc nope}", commands)
    for rule in principles("pl") + principles("en"):
        assert "{" not in rule


def test_unknown_language_is_a_validation_error():
    with pytest.raises(InvalidParameterError) as caught:
        principles("de")

    assert caught.value.details["option"] == "lang"


# --- the flows --------------------------------------------------------------------------

PATHS = {
    "/dane/hydrolog/zlewnia.json": FIXTURES / "watershed_example.json",
    "/dane/hydrolog/q_dobowe.csv": FIXTURES / "daily_flows_3y.csv",
}
COMMAND_STEPS = [
    pytest.param(
        flow_index, step_index, id=f"flow{flow_index + 1}-step{step_index + 1}"
    )
    for flow_index, flow in enumerate(_FLOWS)
    for step_index, step in enumerate(flow.steps)
    if step.command is not None
]


def real_paths(options, tmp_path):
    """``options`` with the example paths of a flow replaced by fixtures or scratch."""
    scratch = {
        "/dane/hydrolog/raport.md": tmp_path / "raport.md",
        "/dane/hydrolog/hsg.tif": tmp_path / "hsg.tif",
    }

    def real(value):
        if isinstance(value, str) and value.startswith("/dane/"):
            for kind in ("clay", "sand", "silt"):
                if f"global_soilgrids_{kind}_" in value:
                    return str(FIXTURES / f"hsg_{kind}.tif")
            return str({**PATHS, **scratch}[value])
        return value

    return {name: real(value) for name, value in options.items()}


def flow_lines(guide: str, lang: str = "pl") -> list[list[str]]:
    """The line of every step of every flow in the guide, flow by flow."""
    flows = section(guide, "Typical flows" if lang == "en" else "Typowe przepływy")
    return [
        re.findall(r"^\d+\. `([^`]+)`", part, re.MULTILINE)
        for part in flows.split("\n### ")[1:]
    ]


@pytest.mark.parametrize("lang", LANGS)
def test_every_flow_step_is_listed_with_a_cli_line_and_an_mcp_call(lang):
    guide = text("agents", lang)
    flows = section(guide, "Typical flows" if lang == "en" else "Typowe przepływy")

    lines = flow_lines(guide, lang)
    mcp = re.findall(r"^   - MCP: `([^`]+)`", flows, re.MULTILINE)

    assert [len(flow) for flow in lines] == [len(flow.steps) for flow in _FLOWS]
    steps = [step for flow in _FLOWS for step in flow.steps if step.command]
    assert len(mcp) == len(steps)
    for call, step in zip(mcp, steps, strict=True):
        tool, _, arguments = call.partition(" ")
        assert tool == get_command(step.command).operation_id
        assert json.loads(arguments) == json.loads(json.dumps(step.options))


@pytest.mark.parametrize(("flow_index", "step_index"), COMMAND_STEPS)
def test_the_cli_accepts_the_line_of_a_flow_step_and_means_the_same_options(
    flow_index, step_index
):
    step = _FLOWS[flow_index].steps[step_index]
    command = get_command(step.command)
    line = flow_lines(text("agents"))[flow_index][step_index]
    words = shlex.split(line)

    assert words[: 1 + len(command.name.split())] == ["hydrolog", *command.name.split()]
    parsed = parse_command_line(command, words[1 + len(command.name.split()) :])

    assert validate_command(command, parsed.options) == validate_command(
        command, step.options
    )


@pytest.mark.parametrize("number", range(1, len(_FLOWS) + 1))
def test_every_flow_runs_on_fixtures(number, tmp_path):
    """The commands of a flow, in order, with the example files replaced by fixtures."""
    results = {}
    for step in _FLOWS[number - 1].steps:
        if step.command is None:
            continue
        options = real_paths(step.options, tmp_path)
        try:
            results[step.command] = run_command(step.command, options).to_dict()
        except MissingDependencyError as exc:
            pytest.skip(f"optional extra not installed: {exc}")

    assert results
    assert all(envelope["status"] == "ok" for envelope in results.values())
    if number == 1:
        assert (tmp_path / "raport.md").stat().st_size > 0
        assert results["report generate"]["files"][0]["path"] == str(
            (tmp_path / "raport.md").resolve()
        )
    if number == 3:  # hsg-stats reads the raster that hsg wrote
        assert results["soil hsg-stats"]["inputs"]["hsg_path"] == str(
            (tmp_path / "hsg.tif").resolve()
        )


@pytest.mark.parametrize(
    ("command", "fields"),
    [
        (
            "hydrograph generate",
            (
                "peak_discharge_m3s",
                "time_to_peak_min",
                "total_volume_m3",
                "runoff_coefficient",
            ),
        ),
        ("tc watershed", ("tc_min",)),
        ("stats flood-frequency", ("best_distribution", "distributions", "quantiles")),
        ("soil hsg-stats", ("groups", "area_ha", "percent", "nodata")),
        ("cn weighted", ("cn",)),
    ],
)
def test_result_fields_named_in_the_flows_exist(command, fields, tmp_path):
    """The notes of the flows name fields of the result; they are really there."""
    notes = " ".join(
        step.note_pl
        for flow in _FLOWS
        for step in flow.steps
        if step.command == command
    )
    step = next(s for f in _FLOWS for s in f.steps if s.command == command)
    shutil.copy(
        FIXTURES / "hsg_result.tif", tmp_path / "hsg.tif"
    )  # stands in for soil hsg
    try:
        result = run_command(command, real_paths(step.options, tmp_path)).to_dict()[
            "result"
        ]
    except MissingDependencyError as exc:
        pytest.skip(f"optional extra not installed: {exc}")
    document = json.dumps(result)

    for field in fields:
        assert field in notes, f"the flow does not mention {field}"
        assert f'"{field}"' in document, f"the result has no {field}"


def test_weighted_cn_of_the_flow_uses_the_tr55_numbers_of_the_row_it_names():
    """``cn list`` -> ``cn weighted``: the parts are the CNs of meadow in good condition."""
    step = next(s for flow in _FLOWS for s in flow.steps if s.command == "cn weighted")
    expected = [
        run_command(
            "cn lookup", {"hsg": hsg, "land_cover": "meadow", "condition": "good"}
        ).to_dict()["result"]["cn"]
        for hsg in "ABCD"
    ]

    assert [part["cn"] for part in step.options["parts"]] == expected


def test_external_steps_are_lines_of_the_other_tools_with_the_documented_options():
    external = [s for f in _FLOWS for s in f.steps if s.external is not None]

    tools = [shlex.split(step.external)[:3] for step in external]
    assert tools == [["imgw", "series", "export"], ["kartograf", "soil", "download"]]
    imgw = shlex.split(external[0].external)
    assert imgw[imgw.index("--format") + 1] == "csv"
    assert imgw[imgw.index("--path") + 1] == "/dane/hydrolog/q_dobowe.csv"
    assert "{store}" in external[0].external and "{station}" in external[0].external
    # the IMGWTools symbols are named in the language of the guide
    assert "KOD_STACJI" in text("agents", "pl") and "STATION_CODE" in text(
        "agents", "en"
    )
    assert "{store}" not in text("agents", "pl") + text("agents", "en")


def test_the_series_of_the_imgwtools_flow_is_what_the_next_step_reads():
    """The exported file is the ``input_file`` of both Hydrolog steps of the flow."""
    flow = _FLOWS[1]
    exported = shlex.split(flow.steps[0].external)
    path = exported[exported.index("--path") + 1]

    assert [s.options["input_file"] for s in flow.steps[1:]] == [path, path]


def test_a_step_is_a_command_or_a_line_of_another_tool():
    with pytest.raises(ValueError, match="exactly one"):
        _Step("a", "b")
    with pytest.raises(ValueError, match="exactly one"):
        _Step("a", "b", command="tc kirpich", external="imgw x")


def test_a_stale_flow_stops_the_generator(monkeypatch):
    """A renamed option or command is an error at generation, not a stale example."""
    wrong_option = _Flow(
        "t",
        "t",
        "i",
        "i",
        (_Step("n", "n", "tc kirpich", {"length_km": 1, "slope": 1}),),
    )
    wrong_command = _Flow("t", "t", "i", "i", (_Step("n", "n", "tc nope", {}),))
    wrong_tool = _Flow("t", "t", "i", "i", (_Step("n", "n", external="curl x"),))

    for flow, error in (
        (wrong_option, InvalidParameterError),
        (wrong_command, NotFoundError),
        (wrong_tool, ValueError),
    ):
        monkeypatch.setattr(guide_module, "_FLOWS", (flow,))
        with pytest.raises(error):
            text("agents")


def test_an_error_code_without_a_description_stops_the_generator(monkeypatch):
    monkeypatch.setattr(guide_module, "_ERROR_ADVICE", {})

    with pytest.raises(ValueError, match="validation_error"):
        text("agents")


def test_a_group_without_a_title_is_shown_by_its_name(monkeypatch):
    """A new group must not break the guide; the test above requires its title."""
    monkeypatch.setattr(guide_module, "_GROUP_TITLES", {})

    guide = text("agents")

    assert "\n### `tc` — tc\n" in guide
    assert "- `tc` — tc: `faa`" in text("llms")


# --- links and names in the guide --------------------------------------------------------


@pytest.mark.parametrize("format", GUIDES.values())
@pytest.mark.parametrize("lang", LANGS)
def test_commands_named_in_the_guide_exist(format, lang):
    names = {command.name for command in COMMANDS}
    mentioned = set()
    for span in code_spans(text(format, lang)):
        words = span.split()
        if words[:1] == ["hydrolog"] and len(words) > 2 and words[1] in GROUPS:
            mentioned.add(f"{words[1]} {words[2]}")
        elif len(words) == 2 and words[0] in GROUPS:
            mentioned.add(span)

    assert mentioned - FOREIGN_COMMANDS <= names, sorted(mentioned - names)


@pytest.mark.parametrize("lang", LANGS)
def test_paths_and_modules_named_in_the_guide_exist(lang):
    guide = text("agents", lang)
    paths = {
        span
        for span in code_spans(guide)
        if re.fullmatch(r"(?:hydrolog|docs|tests)/[A-Za-z0-9_./-]+|CLAUDE\.md", span)
    }
    modules = {
        span
        for span in code_spans(guide)
        if re.fullmatch(r"hydrolog(?:\.[a-z_]+)+", span)
    }

    assert {
        "CLAUDE.md",
        "docs/DEVELOPMENT_STANDARDS.md",
        "hydrolog/agent_guide.py",
    } <= paths
    for path in paths:
        assert (REPOSITORY / path).exists(), path
    assert {"hydrolog.operations", "hydrolog.catalog"} <= modules
    for module in modules:
        assert find_spec(module) is not None, module


@pytest.mark.parametrize("lang", LANGS)
def test_llms_txt_has_the_llms_txt_structure(lang):
    lines = text("llms", lang).splitlines()
    headings = [n for n, line in enumerate(lines) if line.startswith("#")]

    assert len(lines) <= 150
    assert lines[0] == "# Hydrolog"
    assert next(line for line in lines[1:] if line).startswith("> ")
    assert all(lines[n].startswith("## ") for n in headings[1:])
    assert lines[headings[-1]] == "## Optional"
    for start, end in zip(headings[1:], [*headings[2:], len(lines)], strict=True):
        items = [line for line in lines[start + 1 : end] if line]
        assert items, lines[start]
        assert all(
            re.fullmatch(r"- \[[^\]]+\]\(https://[^)\s]+\)(: .+)?", item)
            for item in items
        ), items


@pytest.mark.parametrize("lang", LANGS)
def test_llms_txt_links_point_at_files_of_the_repository(lang):
    base = "https://raw.githubusercontent.com/Daldek/Hydrolog/main/"
    links = re.findall(r"\]\((https://[^)\s]+)\)", text("llms", lang))

    assert links
    for link in links:
        assert link.startswith(base), link
        assert (REPOSITORY / link.removeprefix(base)).is_file(), link
    assert base + "AGENTS.md" in links


# --- templates and the engine -------------------------------------------------------------


def test_render_replaces_markers_and_rejects_unknown_or_repeated_blocks():
    blocks = {"one": lambda: "1.0", "many": lambda: "a\nb"}

    assert _render("v<!-- hydrolog:one -->\n<!-- hydrolog:many -->\nend\n", blocks) == [
        "v1.0\n",
        "a\n",
        "b\n",
        "end\n",
    ]
    for template in (
        "<!-- hydrolog:nothing -->\n",
        "<!-- hydrolog:one -->\n<!-- hydrolog:one -->\n",
        "x <!-- hydrolog:many -->\n",
    ):
        with pytest.raises(ValueError):
            _render(template, blocks)


def test_templates_ship_as_package_data():
    """Every template file is matched by the ``package-data`` patterns of the package."""
    pyproject = tomllib.loads(
        (REPOSITORY / "pyproject.toml").read_text(encoding="utf-8")
    )
    patterns = pyproject["tool"]["setuptools"]["package-data"]["hydrolog"]
    templates = sorted(
        path.relative_to(REPOSITORY / "hydrolog").as_posix()
        for path in (REPOSITORY / "hydrolog" / "_data" / "agents").iterdir()
    )

    assert templates == sorted(
        f"_data/agents/{f}.{lang}.md" for f in GUIDES.values() for lang in LANGS
    )
    for template in templates:
        assert any(fnmatch(template, pattern) for pattern in patterns), template


# --- the guide API -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "option"), [(("html", "pl"), "format"), (("agents", "de"), "lang")]
)
def test_unknown_format_or_language_is_a_validation_error(arguments, option):
    with pytest.raises(InvalidParameterError) as caught:
        agent_guide(*arguments)

    assert caught.value.details["option"] == option
    assert caught.value.details["reason"] == "choice"


def test_language_only_changes_the_prose_not_the_identifiers():
    pl, en = (command_rows(text("agents", lang)) for lang in LANGS)

    assert [(c[0], c[1]) for c in pl] == [(c[0], c[1]) for c in en]
    assert [c[2] for c in pl] != [c[2] for c in en]
    assert text("agents", "pl") != text("agents", "en")


# --- commands guide ---------------------------------------------------------------------------


def test_declared_formats_are_the_guide_formats():
    command = get_command("commands guide")
    format_option = command.option("format")

    assert set(format_option.choices) == set(get_args(GuideFormat))
    assert command.writes and command.option("path").writes
    assert not command.option("path").required


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("format", GUIDES.values())
def test_commands_guide_without_path_returns_the_text_and_writes_nothing(
    format, lang, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    envelope = run_command("commands guide", {"format": format, "lang": lang})

    assert envelope.result == text(format, lang)
    assert envelope.inputs == {"format": format, "lang": lang}
    assert envelope.files == () and envelope.notices == ()
    assert list(tmp_path.iterdir()) == []


def test_commands_guide_defaults_to_the_polish_agents_guide():
    envelope = run_command("commands guide")

    assert envelope.inputs == {"format": "agents", "lang": "pl"}
    assert envelope.result == text("agents", "pl")


@pytest.mark.parametrize("existing", [False, True], ids=["new", "existing"])
def test_path_writes_the_guide_and_reports_the_file(existing, tmp_path):
    target = tmp_path / "przewodnik" / "AGENTS.md"
    target.parent.mkdir()
    if existing:
        target.write_text("stara treść\n", encoding="utf-8")

    envelope = run_command(
        "commands guide", {"format": "llms", "lang": "en", "path": str(target)}
    )

    assert target.read_bytes() == text("llms", "en").encode("utf-8")
    assert envelope.result == text("llms", "en")
    assert [(f.path, f.sha256, f.role) for f in envelope.files] == [
        (str(target.resolve()), sha256_file(target), "output")
    ]
    assert [p.name for p in target.parent.iterdir()] == [
        "AGENTS.md"
    ]  # no temporary file


def test_path_creates_missing_directories(tmp_path):
    target = tmp_path / "a" / "b" / "llms.txt"

    run_command("commands guide", {"format": "llms", "path": str(target)})

    assert target.read_bytes() == text("llms", "pl").encode("utf-8")


def test_two_writers_of_one_file_do_not_share_a_temporary_file(tmp_path, monkeypatch):
    """The MCP server runs calls in threads: both temporary files exist before either
    is renamed, and both calls must still succeed."""
    target = tmp_path / "AGENTS.md"
    meeting = threading.Barrier(2, timeout=20)
    rename = os.replace

    def meet_then_rename(source, destination):
        meeting.wait()
        return rename(source, destination)

    monkeypatch.setattr(os, "replace", meet_then_rename)
    errors = []

    def write():
        try:
            commands_guide(format="llms", path=target)
        except BaseException as exc:  # reported by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=write) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == []
    assert target.read_bytes() == text("llms", "pl").encode("utf-8")
    assert [p.name for p in tmp_path.iterdir()] == ["AGENTS.md"]


def test_a_directory_as_path_is_an_io_error_and_leaves_nothing_behind(tmp_path):
    with pytest.raises(OutputError) as caught:
        run_command("commands guide", {"format": "llms", "path": str(tmp_path)})

    assert caught.value.code == "io_error"
    assert caught.value.details["path"] == str(tmp_path.resolve())
    assert list(tmp_path.iterdir()) == []


def test_path_outside_the_allowed_directories_is_forbidden_and_nothing_is_written(
    tmp_path,
):
    allowed = tmp_path / "data"
    allowed.mkdir()
    outside = tmp_path / "AGENTS.md"

    with pytest.raises(ForbiddenPathError):
        run_command("commands guide", {"path": str(outside)}, allowed_dirs=[allowed])
    inside = run_command(
        "commands guide", {"path": str(allowed / "AGENTS.md")}, allowed_dirs=[allowed]
    )

    assert not outside.exists()
    assert inside.files[0].path == str((allowed / "AGENTS.md").resolve())
    # reading the guide needs no directory at all
    assert run_command("commands guide", {}, allowed_dirs=[]).result == text()


@pytest.mark.parametrize("lang", LANGS)
def test_cli_prints_the_guide_as_it_is(lang, capsys):
    code = main(["commands", "guide", "--format", "llms", "--lang", lang])
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    assert out == text("llms", lang)


def test_cli_without_language_flag_prints_polish(capsys):
    assert main(["commands", "guide", "--format", "llms"]) == 0

    assert capsys.readouterr().out == text("llms", "pl")
