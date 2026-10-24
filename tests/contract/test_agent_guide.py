"""Guide for AI agents (AGI section 8): AGENTS.md, llms.txt and the block.

``AGENTS.md`` and ``llms.txt`` in the repository root are derived files: the drift
tests compare their bytes with the generator. The rest checks the size budgets
(DOC-1.7), the structure rules of the files (DOC-4.2, DOC-5.1), that the guide says
what the catalog says (commands, errors, envelope), that its flows really run, and
that nothing in it points at a file, a command or an option that does not exist.
"""

import re
import shlex
import tomllib
from fnmatch import fnmatch
from importlib.util import find_spec
from pathlib import Path
from typing import get_args

import pytest

from hydrolog import agent_guide as guide_module
from hydrolog.agent_guide import (
    _COMPACT_GROUPS,
    _ERROR_ADVICE,
    _FLOWS,
    _GROUP_TITLES,
    _PRINCIPLES,
    BLOCK_BEGIN,
    BLOCK_END,
    GUIDE_FORMATS,
    GuideFormat,
    _checked,
    _Flow,
    _render,
    _Step,
    agent_guide,
    inject_block,
    principles,
)
from hydrolog.catalog import (
    data_commands,
    get_command,
    run_command,
    validate_command,
)
from hydrolog.catalog.envelope import FileRecord, Notice
from hydrolog.cli.parser import parse_command_line
from hydrolog.exceptions import (
    ERROR_CODES,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    error_document,
)

REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY / "tests" / "fixtures"
RAW = "https://raw.githubusercontent.com/Daldek/Hydrolog/main/"
GUIDES = {"AGENTS.md": "agents", "llms.txt": "llms"}
COMMANDS = data_commands()
GROUPS = list(dict.fromkeys(command.group for command in COMMANDS))
# Commands of other tools whose name looks like one of ours (group ``soil``).
FOREIGN_COMMANDS = {"soil download"}


def section(markdown: str, heading: str) -> str:
    """Text of the ``## heading`` section, up to the next ``## `` heading."""
    start = markdown.index(f"\n## {heading}\n")
    end = markdown.find("\n## ", start + 1)
    return markdown[start : None if end < 0 else end]


def code_spans(markdown: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", markdown)


def llms_link_lines(markdown: str) -> list[int]:
    """Indexes of the lines that open a link list: an item with a Markdown link."""
    return [
        n
        for n, line in enumerate(markdown.splitlines())
        if re.match(r"- \[[^\]]+\]\(", line)
    ]


# --- derived files of the repository
# ---------------------------------------------------


@pytest.mark.parametrize(("name", "format"), GUIDES.items())
def test_repository_guides_are_the_bytes_of_the_generator(name, format):
    expected = agent_guide(format).encode("utf-8")

    assert (REPOSITORY / name).read_bytes() == expected, (
        f"{name} differs from the generator; regenerate it: hydrolog commands guide "
        f"--format {format} --output {name} --force"
    )


@pytest.mark.parametrize(("name", "format"), GUIDES.items())
def test_the_documented_command_regenerates_the_repository_file(name, format, tmp_path):
    """``commands guide --format F --output FILE`` (the command in the guide)."""
    target = tmp_path / name

    run_command("commands guide", {"format": format, "output": str(target)})

    assert target.read_bytes() == (REPOSITORY / name).read_bytes()


@pytest.mark.parametrize("format", GUIDE_FORMATS)
def test_guide_is_plain_deterministic_english_text(format, tmp_path, monkeypatch):
    first = agent_guide(format)
    monkeypatch.chdir(tmp_path)

    again = agent_guide(format)

    assert again == first
    assert first.endswith("\n") and not first.endswith("\n\n")
    assert "\r" not in first
    assert all(line == line.rstrip() for line in first.splitlines())
    assert "<!-- hydrolog:" not in first
    # a surname may carry a diacritic; Polish prose would carry many
    assert len(re.findall(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", first)) <= 2
    assert str(tmp_path) not in first and str(REPOSITORY) not in first
    unlinked = re.sub(r"https://\S+", "", first)  # a link may carry a date
    assert not re.search(r"\b20\d\d-\d\d-\d\d\b", unlinked)  # no generation date


# --- budgets (DOC-1.7) and structure (DOC-4.2, DOC-5.1)
# ---------------------------------------------------


def test_agents_md_stays_within_its_budget():
    guide = agent_guide("agents")

    assert len(guide.splitlines()) <= 200
    assert len(guide.encode("utf-8")) <= 16 * 1024


def test_agents_md_ends_with_the_pointer_to_the_development_guide():
    assert agent_guide("agents").splitlines()[-1] == (
        "Developing this repository? Read CLAUDE.md."
    )


def test_llms_txt_text_before_the_first_link_list_stays_within_its_budget():
    guide = agent_guide("llms")
    first = llms_link_lines(guide)[0]

    assert len("\n".join(guide.splitlines()[:first])) <= 8000


def test_the_block_stays_within_its_budget():
    assert len(agent_guide("agents-md-block").splitlines()) <= 60


def test_llms_txt_has_the_llms_txt_structure():
    lines = agent_guide("llms").splitlines()
    headings = [n for n, line in enumerate(lines) if line.startswith("#")]

    assert lines[0] == "# Hydrolog"
    assert next(line for line in lines[1:] if line).startswith("> ")
    assert all(lines[n].startswith("## ") for n in headings[1:])
    # short paragraphs without headings between the summary and the first H2
    assert all(not line.startswith("#") for line in lines[1 : headings[1]])
    for start, end in zip(headings[1:], [*headings[2:], len(lines)], strict=True):
        items = [line for line in lines[start + 1 : end] if line]
        assert items, lines[start]
        assert all(
            re.fullmatch(r"- \[[^\]]+\]\(https://[^)\s]+\): \S.*", item)
            for item in items
        ), items


def test_llms_txt_links_point_at_files_of_the_repository():
    links = re.findall(r"\]\((https://[^)\s]+)\)", agent_guide("llms"))

    assert links
    for link in links:
        if link.startswith(RAW):
            assert (REPOSITORY / link.removeprefix(RAW)).is_file(), link
    assert RAW + "AGENTS.md" in links


def test_the_block_is_delimited_by_its_markers():
    block = agent_guide("agents-md-block")

    assert block.startswith(BLOCK_BEGIN + "\n")
    assert block.endswith("\n" + BLOCK_END + "\n")
    assert block.count(BLOCK_BEGIN) == block.count(BLOCK_END) == 1
    assert RAW + "AGENTS.md" in block
    assert "hydrolog commands guide --format agents-md-block --inject AGENTS.md" in (
        block
    )


def test_every_command_line_of_the_block_is_accepted_by_the_cli():
    block = agent_guide("agents-md-block")
    fence = re.search(r"```bash\n(.*?)\n```", block, re.DOTALL)
    assert fence is not None

    lines = fence.group(1).splitlines()
    assert 6 <= len(lines) <= 8
    for line in lines:
        words = shlex.split(line)
        assert words[0] == "hydrolog" and words[-1] == "--json"
        command = get_command(" ".join(words[1:3]))
        parse_command_line(command, [w for w in words[3:] if w != "--json"])


# --- the catalog in the guide
# ----------------------------------------------------------


def test_every_group_has_a_title_and_an_index_heading_linking_the_paths():
    index = section(agent_guide("agents"), "Command index")
    headings = re.findall(r"^### (.+)$", index, re.MULTILINE)

    assert set(_GROUP_TITLES) == set(GROUPS), "every group needs its title"
    assert len(headings) == len(GROUPS)
    reference = re.search(r"^\[(\w+)\]: (\S+)$", index, re.MULTILINE)
    assert reference is not None
    assert reference[2].endswith("/docs/COMPUTATION_PATHS.md")
    for group, heading in zip(GROUPS, headings, strict=True):
        assert heading.startswith(f"[{group}")
        assert heading.endswith(f"[{reference[1]}]")


def index_lines(index: str) -> dict[str, list[str]]:
    """The ``- `` lines of the command index under the heading of each group."""
    lines: dict[str, list[str]] = {}
    group = ""
    for line in index.splitlines():
        heading = re.match(r"### \[(\w+):", line)
        if heading:
            group = heading[1]
            lines[group] = []
        elif line.startswith("- "):
            lines[group].append(line)
    return lines


def test_the_index_names_every_command_once_in_catalog_order():
    """A line per command; a compact group has one line that names all of them."""
    index = section(agent_guide("agents"), "Command index")
    by_group = index_lines(index)

    assert list(by_group) == GROUPS
    for group in GROUPS:
        commands = [c for c in COMMANDS if c.group == group]
        if group in _COMPACT_GROUPS:
            assert len(by_group[group]) == 1, group
            names = re.findall(
                r"`(\w+ [\w-]+)`", by_group[group][0].split(" (tools")[0]
            )
            assert names == [c.name for c in commands], group
        else:
            lines = [
                re.fullmatch(r"- `([^`]+)` \(`([^`]+)`\): (.+)", line)
                for line in by_group[group]
            ]
            assert all(lines), group
            assert [m.groups() for m in lines if m] == [
                (c.name, c.operation_id, c.summary) for c in commands
            ]


def test_an_operation_id_is_the_tool_prefix_of_its_group_and_the_verb():
    """What the line of a compact group promises: ``hydrolog_<group>_<verb>``."""
    for command in COMMANDS:
        verb = command.subcommand.replace("-", "_")
        assert command.operation_id == f"hydrolog_{command.group}_{verb}"


def test_a_compact_group_has_one_index_line_for_all_its_commands(monkeypatch):
    plain = agent_guide("agents")
    normal = index_lines(section(plain, "Command index"))
    monkeypatch.setattr(
        guide_module, "_COMPACT_GROUPS", {"stats": "compute flow statistics"}
    )

    guide = agent_guide("agents")
    by_group = index_lines(section(guide, "Command index"))

    stats = [c for c in COMMANDS if c.group == "stats"]
    assert len(stats) > 1 and len(by_group["stats"]) == 1
    line = by_group["stats"][0]
    assert re.findall(r"`(stats [\w-]+)`", line.split(" (tools")[0]) == [
        c.name for c in stats
    ]
    assert "`hydrolog_stats_<verb>`" in line and "`commands list`" in line
    assert line.endswith(": compute flow statistics; summaries: `commands list`.")
    assert {k: v for k, v in by_group.items() if k != "stats"} == {
        k: v for k, v in normal.items() if k != "stats"
    }
    assert len(guide.encode("utf-8")) < len(plain.encode("utf-8"))


def test_error_table_is_the_registry():
    guide = agent_guide("agents")
    table = [
        re.split(r"(?<!\\) \| ", line[2:-2])
        for line in guide.splitlines()
        if line.startswith("| `")
    ]

    assert set(_ERROR_ADVICE) == set(ERROR_CODES)
    assert [(cells[0], cells[1]) for cells in table] == [
        (f"`{code}`", str(spec.exit_code)) for code, spec in ERROR_CODES.items()
    ]
    assert all(cells[2] for cells in table)
    assert "https://github.com/Daldek/Nogat/blob/main/standards/ERROR_REGISTRY.md" in (
        guide
    )
    for spec in ERROR_CODES.values():
        assert f"`{spec.code}` ({spec.exit_code})" in agent_guide("llms")


def test_envelope_and_error_document_fields_are_all_documented():
    """A field added to the envelope or the error document must be in the guide."""
    guide = agent_guide("agents")
    envelope = run_command("commands list").to_dict()
    record = FileRecord("/x", 1, "00").to_dict()
    notice = Notice("info", "code", "text").to_dict()
    error = error_document(NotFoundError("x", hint="h"), "tc kirpich")
    fields = {*envelope, *record, *notice, *error}

    for field in fields:
        assert f"`{field}`" in guide or f"`{field}," in guide or f"{field}," in guide, (
            field
        )


def test_schema_names_are_the_current_ones():
    from hydrolog.catalog.document import COMMANDS_SCHEMA
    from hydrolog.catalog.envelope import RESULT_SCHEMA
    from hydrolog.exceptions import ERROR_SCHEMA

    allowed = {RESULT_SCHEMA, ERROR_SCHEMA, COMMANDS_SCHEMA}

    for format in GUIDE_FORMATS:
        mentioned = set(
            re.findall(r"hydrolog-(?:result|error|commands)/\d+", agent_guide(format))
        )
        assert mentioned <= allowed
    assert {RESULT_SCHEMA, ERROR_SCHEMA} <= set(
        re.findall(r"hydrolog-(?:result|error)/\d+", agent_guide("agents"))
    )


# --- the rules
# --------------------------------------------------------------------------


def test_agents_md_carries_every_rule_in_order():
    rules = principles()
    expected = "\n".join(f"{n}. {rule}" for n, rule in enumerate(rules, start=1))

    assert len(rules) == len(_PRINCIPLES)
    assert f"\n{expected}\n" in agent_guide("agents")


def test_the_rules_name_options_and_commands_of_the_catalog():
    """``{opt:...}`` and ``{cmd:...}`` are replaced by names that exist."""
    assert _checked("`{opt:input_file}` `{cmd:tc kirpich}`", COMMANDS) == (
        "`input_file` `tc kirpich`"
    )
    with pytest.raises(ValueError, match="option 'no_such_option'"):
        _checked("{opt:no_such_option}", COMMANDS)
    with pytest.raises(ValueError, match="command 'tc nope'"):
        _checked("{cmd:tc nope}", COMMANDS)
    for rule in principles():
        assert "{" not in rule


# --- the flows
# --------------------------------------------------------------------------

PATHS = {
    "/data/hydrolog/watershed.json": FIXTURES / "watershed_example.json",
    "/data/hydrolog/q_daily.csv": FIXTURES / "daily_flows_3y.csv",
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
        "/data/hydrolog/report.md": tmp_path / "report.md",
        "/data/hydrolog/hsg.tif": tmp_path / "hsg.tif",
    }

    def real(value):
        if isinstance(value, str) and value.startswith("/data/"):
            for kind in ("clay", "sand", "silt"):
                if value == f"/data/kartograf/soil/{kind}.tif":
                    return str(FIXTURES / f"hsg_{kind}.tif")
            return str({**PATHS, **scratch}[value])
        return value

    return {name: real(value) for name, value in options.items()}


def flow_lines(guide: str) -> list[list[str]]:
    """The line of every step of every flow in the guide, flow by flow."""
    flows = section(guide, "Typical flows")
    return [
        re.findall(r"^\d+\. `([^`]+)`", part, re.MULTILINE)
        for part in flows.split("\n### ")[1:]
    ]


def test_every_flow_step_is_listed_with_its_line():
    lines = flow_lines(agent_guide("agents"))

    assert [len(flow) for flow in lines] == [len(flow.steps) for flow in _FLOWS]


@pytest.mark.parametrize(("flow_index", "step_index"), COMMAND_STEPS)
def test_the_cli_accepts_the_line_of_a_flow_step_and_means_the_same_options(
    flow_index, step_index
):
    step = _FLOWS[flow_index].steps[step_index]
    command = get_command(step.command)
    line = flow_lines(agent_guide("agents"))[flow_index][step_index]
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
        if step.options.get("check"):
            options["check"] = False  # the flow says: then run it for real
        try:
            results[step.command] = run_command(step.command, options).to_dict()
        except MissingDependencyError as exc:
            pytest.skip(f"optional extra not installed: {exc}")

    assert results
    assert all(envelope["status"] == "ok" for envelope in results.values())
    if number == 1:
        report = (tmp_path / "report.md").resolve()
        assert report.stat().st_size > 0
        files = results["report generate"]["result"]["files"]
        assert [item["path"] for item in files] == [str(report)]
    if number == 3:  # hsg-stats reads the raster that hsg wrote
        assert results["soil hsg-stats"]["inputs"]["hsg_path"] == str(
            (tmp_path / "hsg.tif").resolve()
        )


def test_the_check_step_of_a_flow_plans_and_writes_nothing(tmp_path):
    step = next(s for f in _FLOWS for s in f.steps if s.options.get("check"))

    envelope = run_command(step.command, real_paths(step.options, tmp_path)).to_dict()

    assert envelope["check"] is True
    assert not (tmp_path / "report.md").exists()
    assert envelope["result"]["targets"][0]["action"] == "write"


@pytest.mark.parametrize(
    ("command", "fields"),
    [
        (
            "hydrograph generate",
            ("peak_discharge_m3s", "time_to_peak_min", "total_volume_m3"),
        ),
        ("tc watershed", ("tc_min",)),
        ("stats flood-frequency", ("best_distribution", "distributions", "quantiles")),
        ("soil hsg-stats", ("groups", "area_ha", "nodata")),
        ("cn weighted", ("cn",)),
    ],
)
def test_result_fields_named_in_the_flows_exist(command, fields, tmp_path):
    """The notes of the flows name fields of the result; they are really there."""
    notes = " ".join(
        step.note for flow in _FLOWS for step in flow.steps if step.command == command
    )
    step = next(s for f in _FLOWS for s in f.steps if s.command == command)
    (tmp_path / "hsg.tif").write_bytes((FIXTURES / "hsg_result.tif").read_bytes())
    try:
        result = run_command(command, real_paths(step.options, tmp_path)).to_dict()[
            "result"
        ]
    except MissingDependencyError as exc:
        pytest.skip(f"optional extra not installed: {exc}")
    document = str(result)

    for field in fields:
        assert field in notes, f"the flow does not mention {field}"
        assert f"'{field}'" in document, f"the result has no {field}"


def test_external_steps_are_lines_of_the_other_tools_with_the_documented_options():
    external = [s for f in _FLOWS for s in f.steps if s.external is not None]

    tools = [shlex.split(step.external)[:3] for step in external]
    assert tools == [["imgw", "series", "export"], ["kartograf", "soil", "download"]]
    imgw = shlex.split(external[0].external)
    assert imgw[imgw.index("--format") + 1] == "csv"
    assert imgw[imgw.index("--output") + 1] == "/data/hydrolog/q_daily.csv"
    kartograf = shlex.split(external[1].external)
    assert "--output-dir" in kartograf and "--json" in kartograf


def test_the_series_of_the_imgwtools_flow_is_what_the_next_step_reads():
    """The exported file is the ``input_file`` of the Hydrolog step that follows."""
    flow = _FLOWS[1]
    exported = shlex.split(flow.steps[0].external)
    path = exported[exported.index("--output") + 1]

    assert [s.options["input_file"] for s in flow.steps[1:]] == [path]


def test_a_step_is_a_command_or_a_line_of_another_tool():
    with pytest.raises(ValueError, match="exactly one"):
        _Step("a")
    with pytest.raises(ValueError, match="exactly one"):
        _Step("a", command="tc kirpich", external="imgw x")


def test_a_stale_flow_stops_the_generator(monkeypatch):
    """A renamed option or command is an error at generation, not a stale example."""
    wrong_option = _Flow(
        "t", "i", (_Step("n", "tc kirpich", {"length_km": 1, "slope": 1}),)
    )
    wrong_command = _Flow("t", "i", (_Step("n", "tc nope", {}),))
    wrong_tool = _Flow("t", "i", (_Step("n", external="curl x"),))

    for flow, error in (
        (wrong_option, InvalidParameterError),
        (wrong_command, NotFoundError),
        (wrong_tool, ValueError),
    ):
        monkeypatch.setattr(guide_module, "_FLOWS", (flow,))
        with pytest.raises(error):
            agent_guide("agents")


def test_an_error_code_without_a_description_stops_the_generator(monkeypatch):
    monkeypatch.setattr(guide_module, "_ERROR_ADVICE", {})

    with pytest.raises(ValueError, match="internal_error"):
        agent_guide("agents")


def test_a_group_without_a_title_is_shown_by_its_name(monkeypatch):
    """A new group must not break the guide; the test above requires its title."""
    monkeypatch.setattr(guide_module, "_GROUP_TITLES", {})

    assert "\n### [tc: tc]" in agent_guide("agents")


# --- links and names in the guide
# --------------------------------------------------------


@pytest.mark.parametrize("format", GUIDE_FORMATS)
def test_commands_named_in_the_guide_exist(format):
    names = {command.name for command in COMMANDS}
    mentioned = set()
    for span in code_spans(agent_guide(format)):
        words = span.split()
        if words[:1] == ["hydrolog"] and len(words) > 2 and words[1] in GROUPS:
            mentioned.add(f"{words[1]} {words[2]}")
        elif len(words) == 2 and words[0] in GROUPS:
            mentioned.add(span)

    assert mentioned - FOREIGN_COMMANDS <= names, sorted(mentioned - names)


def test_paths_and_modules_named_in_the_guide_exist():
    guide = agent_guide("agents")
    paths = {
        span
        for span in code_spans(guide)
        if re.fullmatch(
            r"(?:src/hydrolog|docs|tests|scripts)/[A-Za-z0-9_./-]+|CLAUDE\.md", span
        )
    }
    modules = {
        span
        for span in code_spans(guide)
        if re.fullmatch(r"hydrolog(?:\.[a-z_]+)+", span)
    }

    assert {"scripts/gate.sh", "src/hydrolog/agent_guide.py"} <= paths
    for path in paths:
        assert (REPOSITORY / path).exists(), path
    assert not {
        p for p in paths if "DEVELOPMENT_STANDARDS" in p or "IMPLEMENTATION" in p
    }
    for module in modules:
        assert find_spec(module.rsplit(".", 1)[0]) is not None, module


# --- templates and the engine
# -------------------------------------------------------------


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
    """Every template file is matched by the ``package-data`` patterns."""
    pyproject = tomllib.loads(
        (REPOSITORY / "pyproject.toml").read_text(encoding="utf-8")
    )
    patterns = pyproject["tool"]["setuptools"]["package-data"]["hydrolog"]
    templates = sorted(
        path.relative_to(REPOSITORY / "src" / "hydrolog").as_posix()
        for path in (REPOSITORY / "src" / "hydrolog" / "_data" / "agents").iterdir()
    )

    assert templates == sorted(f"_data/agents/{f}.md" for f in GUIDE_FORMATS)
    for template in templates:
        assert any(fnmatch(template, pattern) for pattern in patterns), template


# --- the guide API
# -------------------------------------------------------------------------


def test_unknown_format_is_a_validation_error():
    with pytest.raises(InvalidParameterError) as caught:
        agent_guide("html")  # type: ignore[arg-type]

    assert caught.value.details["option"] == "format"
    assert caught.value.details["reason"] == "choice"


def test_declared_formats_are_the_guide_formats():
    format_option = get_command("commands guide").option("format")

    assert (
        set(format_option.choices) == set(get_args(GuideFormat)) == set(GUIDE_FORMATS)
    )


# --- inject_block (AGI-8.2)
# ---------------------------------------------------------------------


BLOCK = agent_guide("agents-md-block")


def test_a_block_is_appended_to_a_file_without_it():
    existing = "# Project\n\nOwn rules.\n"

    injected = inject_block(existing, BLOCK)

    assert injected.startswith(existing + "\n")
    assert injected.endswith(BLOCK)


def test_a_block_goes_into_an_empty_file_as_it_is():
    assert inject_block("", BLOCK) == BLOCK


def test_an_existing_block_is_replaced_and_the_text_around_it_stays():
    old = f"{BLOCK_BEGIN}\nstale\n{BLOCK_END}"
    existing = f"# Project\n\n{old}\n\n## Other\n\nText.\n"

    injected = inject_block(existing, BLOCK)

    assert "stale" not in injected
    assert injected == f"# Project\n\n{BLOCK.rstrip()}\n\n## Other\n\nText.\n"


@pytest.mark.parametrize(
    "existing",
    ["", "# Project\n", f"# P\n\n{BLOCK_BEGIN}\nold\n{BLOCK_END}\n\nTail\n"],
    ids=["empty", "without block", "with block"],
)
def test_injecting_twice_changes_nothing(existing):
    once = inject_block(existing, BLOCK)

    assert inject_block(once, BLOCK) == once
    assert once.count(BLOCK_BEGIN) == once.count(BLOCK_END) == 1
