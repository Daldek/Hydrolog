"""Guide for AI agents generated from the command catalog (AGI section 8).

:func:`agent_guide` renders ``AGENTS.md`` (``format="agents"``), ``llms.txt``
(``format="llms"``) and the compact block for the ``AGENTS.md`` of a consumer
repository (``format="agents-md-block"``), always in English (AGI-9.2), from the
hand-written templates in ``src/hydrolog/_data/agents`` (``<format>.md``). Every marker
``<!-- hydrolog:<block> -->`` of a template is replaced by a block generated from the
command catalog (:func:`hydrolog.catalog.data_commands`), the error registry
(:data:`hydrolog.exceptions.ERROR_CODES`) and the data of this module: the principles
shared with the MCP server instructions (:func:`principles`) and the typical flows,
whose steps are catalog commands rendered as CLI lines. A marker that fills a whole
line takes a block of any number of lines, a marker inside a line a one-line block; an
unknown block or a block used twice is a program error (``ValueError``).

The flows are checked while they are rendered: every step names an existing command
and gives valid options (:func:`hydrolog.catalog.validate_command`), so a renamed
option or command stops the generator instead of leaving a stale example in the guide.
The principles name options and commands through ``{opt:...}`` and ``{cmd:...}``
placeholders that are checked against the catalog in the same way.

The output depends only on the installed package (no dates, no version, no local
paths), so ``AGENTS.md`` and ``llms.txt`` in the repository root are derived files
that the tests compare byte for byte with the generator. Regenerate them after any
change of the catalog, the error registry, the templates or this module::

    hydrolog commands guide --format agents --output AGENTS.md --force
    hydrolog commands guide --format llms --output llms.txt --force

The CLI lines of the flows are written by the example formatter of the command line
(:func:`hydrolog.cli.parser.format_example`), imported when a flow is rendered, so they
are exactly what the CLI parses.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Final, Literal, cast

from hydrolog.catalog import Command, data_commands, get_command, validate_command
from hydrolog.exceptions import ERROR_CODES

__all__ = [
    "BLOCK_BEGIN",
    "BLOCK_END",
    "GUIDE_FORMATS",
    "GuideFormat",
    "agent_guide",
    "inject_block",
    "principles",
]

GuideFormat = Literal["agents", "llms", "agents-md-block"]
GUIDE_FORMATS: Final[tuple[str, ...]] = ("agents", "llms", "agents-md-block")
"""Formats of :func:`agent_guide` (AGI-3.8)."""
BLOCK_BEGIN: Final = "<!-- BEGIN hydrolog -->"
BLOCK_END: Final = "<!-- END hydrolog -->"
"""Markers that delimit the block of ``agents-md-block`` (AGI-8.2)."""

_MARKER: Final = re.compile(r"<!--\s*hydrolog:(?P<name>[^\s>]*)\s*-->")
_PLACEHOLDER: Final = re.compile(r"\{(?P<kind>opt|cmd):(?P<name>[^{}]+)\}")
_TEMPLATES: Final = ("_data", "agents")
_COMPUTATION_PATHS: Final = (
    "https://github.com/Daldek/Hydrolog/blob/main/docs/COMPUTATION_PATHS.md"
)

# --- texts
# -----------------------------------------------------------------------------

# Titles of the command groups. A group of the catalog without a title here shows its
# bare name; a test requires a title for every group.
_GROUP_TITLES: Final[Mapping[str, str]] = {
    "tc": "Time of concentration",
    "cn": "Curve Number (TR-55)",
    "scs": "SCS-CN effective precipitation",
    "precip": "Precipitation: hyetographs and areal precipitation",
    "uh": "Unit hydrographs",
    "hydrograph": "Runoff hydrograph",
    "morphometry": "Watershed morphometry",
    "network": "River network",
    "stats": "Flow statistics",
    "hydrometrics": "Hydrometry",
    "soil": "Soil: texture and HSG",
    "report": "Calculation report",
    "config": "Effective settings",
    "commands": "The command catalog and this guide",
}
# Groups whose index entry is one line that names every command instead of one line per
# command (ADR-0009): group -> what its commands do, one clause. They are listed here
# only to keep AGENTS.md within its budget; ``commands list`` still gives each summary.
_COMPACT_GROUPS: Final[Mapping[str, str]] = {
    "route": (
        "route a hydrograph (`time_min`, `discharge_m3s`) through a reach, a "
        "reservoir or a river network"
    ),
}
# The rules of AGENTS.md, the block and the instructions of the MCP server.
# ``{opt:name}`` and ``{cmd:name}`` are checked against the catalog and replaced by the
# bare name.
_PRINCIPLES: Final[tuple[str, ...]] = (
    "**Discover, do not guess:** `{cmd:commands list}` lists the commands, "
    "`{cmd:commands schema}` (option `{opt:command}`) gives options, units, bounds "
    "and examples; in MCP use `tools/list`.",
    "**Files, not arrays:** give series, stations, segments and watersheds as a "
    "CSV/JSON file (`{opt:input_file}`, `{opt:watershed_file}`...), not long lists.",
    "**Units:** option descriptions give them (km, km2, m/m, mm, min, m3/s; slope in "
    "m/m, not %); do not convert silently or guess values the user did not give.",
    "**Check, then write:** a command that writes takes `{opt:output}`, `{opt:check}` "
    "and `{opt:force}`; run `check` first, an existing file is replaced only with "
    "`force`, written files are listed in `result.files`.",
    "**Errors by code:** decide by `code`, `details.option` and `details.reason` (or "
    "the exit code), fix the argument as `hint` says and call again; never present "
    "an error as a result.",
    "**Absolute paths in allowed directories:** MCP refuses (`forbidden`) files "
    "outside `--allow-dir`, and every path option without it.",
    "**Read `notices`:** non-fatal warnings (a short series, a value outside a "
    "formula's range); pass them on with the result.",
    "**No data downloads:** Hydrolog uses no network; series come from IMGWTools, "
    "soil rasters from Kartograf.",
)
# What each code of the error registry means for an agent.
_ERROR_ADVICE: Final[Mapping[str, str]] = {
    "validation_error": "wrong or missing option: fix `details.option` (`hint`)",
    "not_found": "unknown command (`details.suggestions`) or input file",
    "conflict": "output file exists: another `output` or `force`",
    "missing_dependency": "optional extra missing: install it (`hint`)",
    "data_error": "malformed input file: see `details.path`, `details.reason`",
    "io_error": "output cannot be written: check `details.path`",
    "forbidden": "path outside allowed directories (`details.allowed_dirs`)",
    "calculation_error": "valid input, no result: change the data",
    "cancelled": "interrupted (Ctrl+C): nothing half written, run again",
    "terminated": "ended by SIGTERM: nothing half written, run again",
    "internal_error": "bug in Hydrolog: report command, options, version",
}

# --- flows
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class _Step:
    """One step of a flow: a catalog command or a line of another tool.

    A step is either a catalog command (``command`` and its ``options``) or a line of
    another tool of the ecosystem (``external``). The note is Markdown.
    """

    note: str
    command: str | None = None
    options: Mapping[str, object] = field(default_factory=dict)
    external: str | None = None

    def __post_init__(self) -> None:
        if (self.command is None) == (self.external is None):
            raise ValueError("A flow step needs exactly one of command and external")


@dataclass(frozen=True)
class _Flow:
    """A typical task of an agent: a title, an introduction and its steps."""

    title: str
    intro: str
    steps: tuple[_Step, ...]


_WATERSHED: Final = "/data/hydrolog/watershed.json"
_SERIES: Final = "/data/hydrolog/q_daily.csv"
_REPORT: Final = "/data/hydrolog/report.md"
_HSG: Final = "/data/hydrolog/hsg.tif"
_SOILGRIDS: Final = "/data/kartograf/soil/{}.tif"
_DESIGN_STORM: Final = {"hietogram_type": "beta", "total_mm": 50, "duration_min": 60}
_HYDROGRAPH: Final = {
    "watershed_file": _WATERSHED,
    "tc_method": "kirpich",
    **_DESIGN_STORM,
}
_FLOWS: Final[tuple[_Flow, ...]] = (
    _Flow(
        "Design hydrograph of a watershed described by a JSON file",
        "The watershed file has the `WatershedParameters` format: `area_km2`, "
        "`perimeter_km`, `length_km`, `elevation_min_m` and `elevation_max_m` are "
        "required; `cn`, `channel_length_km`, `channel_slope_m_per_m` are optional.",
        (
            _Step(
                "geometric, shape and relief indicators; a bad file is a "
                "`data_error` with `details.path`.",
                "morphometry watershed",
                {"watershed_file": _WATERSHED},
            ),
            _Step(
                "time of concentration (`result.tc_min`); a field the method needs "
                "but the file lacks is a `validation_error` listing what is missing.",
                "tc watershed",
                {"watershed_file": _WATERSHED, "method": "kirpich"},
            ),
            _Step(
                "direct runoff (Beta hyetograph, SCS-CN with `cn` from the file, SCS "
                "unit hydrograph): `peak_discharge_m3s`, `time_to_peak_min`, "
                "`total_volume_m3`.",
                "hydrograph generate",
                _HYDROGRAPH,
            ),
            _Step(
                "plan of the Markdown report (action `write`, `replace` or "
                "`conflict`, nothing written); run it without `check` to write it "
                "(`result.files`).",
                "report generate",
                {**_HYDROGRAPH, "output": _REPORT, "check": True},
            ),
        ),
    ),
    _Flow(
        "Flood frequency from an IMGWTools CSV export",
        "IMGWTools exports the daily discharge series to a CSV file (`Q [m3/s]`, "
        "`date`) that Hydrolog loads without preprocessing.",
        (
            _Step(
                "IMGWTools (a separate tool): export one station (`CODE` from `imgw "
                "stations find`); reliable quantiles need at least 30 years.",
                external=(
                    "imgw series export --dataset pl.imgw.hydro_daily "
                    f"--station CODE --variables Q --format csv --output {_SERIES}"
                ),
            ),
            _Step(
                "annual maxima of hydrological years (Nov-Oct); `Q` finds the column "
                "`Q [m3/s]`; result: `best_distribution`, `distributions[].quantiles`; "
                "under 30 years adds a notice.",
                "stats flood-frequency",
                {
                    "input_file": _SERIES,
                    "value_column": "Q",
                    "date_column": "date",
                    "distribution": "all",
                    "return_periods": [10, 50, 100],
                },
            ),
        ),
    ),
    _Flow(
        "Hydrologic soil groups (HSG) from SoilGrids rasters and the weighted CN",
        "Kartograf downloads clay, sand and silt (g/kg); Hydrolog computes the HSG "
        "(extra `raster`).",
        (
            _Step(
                "Kartograf (a separate tool): repeat with `--property sand` and "
                "`--property silt`; the `files[].path` values of its `--json` result "
                "are the raster inputs of the next step.",
                external=(
                    "kartograf soil download --property clay --depth 0-5cm "
                    "--stat mean --bbox 626000,480000,628000,482000 "
                    "--bbox-crs EPSG:2180 --output-dir /data/kartograf --json"
                ),
            ),
            _Step(
                "HSG raster (GeoTIFF `uint8`: 0 no data, 1-4 are A-D) from three "
                "rasters with the same coordinate system, grid and size.",
                "soil hsg",
                {
                    "clay_path": _SOILGRIDS.format("clay"),
                    "sand_path": _SOILGRIDS.format("sand"),
                    "silt_path": _SOILGRIDS.format("silt"),
                    "output": _HSG,
                },
            ),
            _Step(
                "area (`area_ha`) and share of each group (`groups.A` ... `groups.D`) "
                "and the `nodata` cells.",
                "soil hsg-stats",
                {"hsg_path": _HSG},
            ),
            _Step(
                "area-weighted CN (`result.cn`): a part is a CN (`cn list`, `cn "
                "lookup`) and the `area_ha` of a group from `soil hsg-stats`; "
                "intersecting rasters with land cover happens outside Hydrolog.",
                "cn weighted",
                {
                    "parts": [
                        {"cn": 30, "area": 75.0},
                        {"cn": 58, "area": 75.0},
                        {"cn": 71, "area": 75.0},
                        {"cn": 78, "area": 68.75},
                    ]
                },
            ),
        ),
    ),
)
_EXAMPLE: Final = ("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
# Commands of the compact block: the discovery pair, then the commonest computations.
_BLOCK_COMMANDS: Final[tuple[tuple[str, Mapping[str, object]], ...]] = (
    ("commands list", {}),
    ("commands schema", {"command": "tc kirpich"}),
    _EXAMPLE,
    ("tc watershed", {"watershed_file": _WATERSHED, "method": "kirpich"}),
    ("hydrograph generate", _HYDROGRAPH),
    ("stats flood-frequency", {"input_file": _SERIES, "value_column": "Q"}),
    ("report generate", {**_HYDROGRAPH, "output": _REPORT, "check": True}),
    ("soil hsg-stats", {"hsg_path": _HSG}),
)
_EXTERNAL_TOOLS: Final = ("imgw", "kartograf")

# --- helpers
# ---------------------------------------------------------------------------


def _code(text: object) -> str:
    return f"`{text}`"


def _table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    def cell(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(cell(text) for text in header) + " |",
        "|" + "---|" * len(header),
    ]
    lines += ["| " + " | ".join(cell(text) for text in row) + " |" for row in rows]
    return "\n".join(lines)


def _groups(commands: Sequence[Command]) -> dict[str, list[Command]]:
    """Group the commands by group, in catalog order."""
    grouped: dict[str, list[Command]] = {}
    for command in commands:
        grouped.setdefault(command.group, []).append(command)
    return grouped


def _group_title(group: str) -> str:
    return _GROUP_TITLES.get(group, group)


def _checked(text: str, commands: Sequence[Command]) -> str:
    """``text`` with its ``{opt:...}``/``{cmd:...}`` placeholders checked and replaced.

    Raises
    ------
    ValueError
        If a placeholder names an option or a command that the catalog lacks.
    """
    options = {option.name for command in commands for option in command.options}
    names = {command.name for command in commands}

    def fill(match: re.Match[str]) -> str:
        known, kind = (
            (options, "option") if match["kind"] == "opt" else (names, "command")
        )
        if match["name"] not in known:
            raise ValueError(
                f"The guide names the {kind} {match['name']!r}, which the catalog "
                "does not have"
            )
        return match["name"]

    return _PLACEHOLDER.sub(fill, text)


# --- blocks
# ----------------------------------------------------------------------------


def principles() -> tuple[str, ...]:
    """Return the rules for an agent, shared by the guides and the MCP instructions.

    Returns
    -------
    tuple of str
        The rules as English Markdown (one string per rule, without numbering):
        discover before calling, files not arrays, units, check before writing,
        errors by code, absolute paths in allowed directories, read the notices, no
        data downloads. The options and commands they name exist in the catalog.
    """
    commands = data_commands()
    return tuple(_checked(rule, commands) for rule in _PRINCIPLES)


def _rules() -> str:
    return "\n".join(
        f"{number}. {rule}" for number, rule in enumerate(principles(), start=1)
    )


def _compact_entry(group: str, commands: Sequence[Command]) -> str:
    """Return the single index line of a compact group: commands, tools, purpose."""
    names = ", ".join(_code(command.name) for command in commands)
    return (
        f"- {names} (tools `hydrolog_{group}_<verb>`, `-` as `_`): "
        f"{_COMPACT_GROUPS[group]}; summaries: `commands list`."
    )


def _index() -> str:
    """One heading per group (linking the computation paths), a line per command.

    A group in :data:`_COMPACT_GROUPS` has one line for all its commands.
    """
    lines = []
    for group, commands in _groups(data_commands()).items():
        title = f"{group}: {_group_title(group)}"
        lines.append(f"### [{title}][paths]")
        if group in _COMPACT_GROUPS:
            lines.append(_compact_entry(group, commands))
            continue
        lines += [
            f"- {_code(command.name)} ({_code(command.operation_id)}): "
            f"{command.summary}"
            for command in commands
        ]
    lines += ["", f"[paths]: {_COMPUTATION_PATHS}"]
    return "\n".join(lines)


def _group_names() -> str:
    return ", ".join(_code(group) for group in _groups(data_commands()))


def _errors() -> str:
    rows = [
        (_code(spec.code), str(spec.exit_code), _error_advice(spec.code))
        for spec in ERROR_CODES.values()
    ]
    return _table(("Code", "Exit", "What to do"), rows)


def _error_advice(code: str) -> str:
    advice = _ERROR_ADVICE.get(code)
    if advice is None:
        raise ValueError(f"The guide has no description of the error code {code!r}")
    return advice


def _error_codes() -> str:
    return ", ".join(
        f"{_code(spec.code)} ({spec.exit_code})" for spec in ERROR_CODES.values()
    )


def _cli_line(command: Command, options: Mapping[str, object]) -> str:
    """Return the command line that gives ``command`` the ``options``.

    The line is written the way the CLI parses it.
    """
    from hydrolog.cli.parser import format_example

    return format_example(command, options)


def _python_call(command: Command, options: Mapping[str, object]) -> str:
    arguments = "".join(
        f", {name}={json.dumps(value)}" for name, value in options.items()
    )
    return f"hydrolog.run_command({json.dumps(command.name)}{arguments})"


def _python_example() -> str:
    name, options = _EXAMPLE
    command = get_command(name)
    validate_command(command, options)
    return _code(_python_call(command, options))


def _cli_example() -> str:
    name, options = _EXAMPLE
    command = get_command(name)
    validate_command(command, options)
    return _code(f"{_cli_line(command, options)} --json")


def _external_line(step: _Step) -> str:
    """Return the line of another tool, checked to start with a known tool."""
    assert step.external is not None
    words = shlex.split(step.external)  # unbalanced quotes are a program error
    if words[0] not in _EXTERNAL_TOOLS:
        raise ValueError(
            f"The flow step runs {words[0]!r}, an unknown tool: {step.external}"
        )
    return step.external


def _rendered_step(step: _Step) -> str:
    """Render the line of a step (CLI or of another tool), validated.

    Raises
    ------
    NotFoundError
        If the step names a command that the catalog lacks.
    InvalidParameterError
        If the options of the step are not valid for its command.
    """
    if step.external is not None:
        return _external_line(step)
    assert step.command is not None
    command = get_command(step.command)
    validate_command(command, step.options)
    return _cli_line(command, step.options)


def _flows() -> str:
    """Render the typical flows: a numbered CLI line with a note per step."""
    sections = []
    for number, flow in enumerate(_FLOWS, start=1):
        lines = [f"### {number}. {flow.title}", flow.intro]
        lines += [
            f"{index}. {_code(_rendered_step(step))} - {step.note}"
            for index, step in enumerate(flow.steps, start=1)
        ]
        sections.append("\n".join(lines))
    return "\n".join(sections)


def _block_commands() -> str:
    """Render the commands of the compact block as CLI lines in a fence."""
    lines = []
    for name, options in _BLOCK_COMMANDS:
        command = get_command(name)
        validate_command(command, options)
        lines.append(f"{_cli_line(command, options)} --json")
    return "\n".join(["```bash", *lines, "```"])


def _blocks() -> dict[str, Callable[[], str]]:
    """Build the generated blocks of the guide (rendered only when used)."""
    return {
        "rules": _rules,
        "python_example": _python_example,
        "cli_example": _cli_example,
        "index": _index,
        "group_names": _group_names,
        "errors": _errors,
        "error_codes": _error_codes,
        "flows": _flows,
        "block_commands": _block_commands,
    }


# --- templates
# -------------------------------------------------------------------------


def _render(template: str, blocks: Mapping[str, Callable[[], str]]) -> list[str]:
    """Lines of ``template``, each ending with a newline, with every marker replaced.

    Raises
    ------
    ValueError
        If a marker names an unknown block, a block is used twice or a multi-line
        block stands inside a line (program errors of a template).
    """
    used: set[str] = set()

    def block(name: str) -> str:
        if name not in blocks:
            raise ValueError(f"Unknown guide block {name!r} in a template")
        if name in used:
            raise ValueError(f"Guide block {name!r} is used twice in a template")
        used.add(name)
        return blocks[name]()

    def inline(match: re.Match[str]) -> str:
        text = block(match["name"])
        if "\n" in text:
            raise ValueError(
                f"Guide block {match['name']!r} has several lines but its marker "
                "stands inside a line of the template"
            )
        return text

    lines: list[str] = []
    for line in template.removesuffix("\n").split("\n"):
        whole = _MARKER.fullmatch(line.strip())
        if whole is not None:
            lines += block(whole["name"]).split("\n")
        else:
            lines.append(_MARKER.sub(inline, line))
    return [f"{line}\n" for line in lines]


def inject_block(existing: str, block: str) -> str:
    """Return ``existing`` with its Hydrolog block replaced by ``block``.

    The block runs from :data:`BLOCK_BEGIN` to :data:`BLOCK_END`; ``block`` carries
    both markers. A text without the block gets it appended after a blank line, so
    injecting the same block again returns the same text (AGI-8.2).

    Parameters
    ----------
    existing : str
        Current text of the consumer's ``AGENTS.md`` (may be empty).
    block : str
        The block to put in, markers included.

    Returns
    -------
    str
        The new text, ending with a newline.
    """
    start = existing.find(BLOCK_BEGIN)
    end = existing.find(BLOCK_END, start) if start >= 0 else -1
    wanted = block.strip("\n")
    if start >= 0 and end >= 0:
        tail = existing[end + len(BLOCK_END) :]
        return existing[:start] + wanted + (tail if tail.strip() else "\n")
    if not existing.strip():
        return wanted + "\n"
    return existing.rstrip("\n") + "\n\n" + wanted + "\n"


def _template(format: GuideFormat) -> str:
    resource = files("hydrolog").joinpath(*_TEMPLATES, f"{format}.md")
    return resource.read_text(encoding="utf-8")


def agent_guide(format: GuideFormat) -> str:
    r"""Generate the English guide for AI agents from the command catalog.

    ``format="agents"`` gives ``AGENTS.md`` (at most 200 lines and 16 KiB): purpose
    and scope, install, interfaces, the discover-check-run-read workflow, the result
    envelope, the error codes, the command index, typical flows and what not to do.
    ``format="llms"`` gives ``llms.txt`` in the llmstxt.org layout.
    ``format="agents-md-block"`` gives the compact block (at most 60 lines) between
    :data:`BLOCK_BEGIN` and :data:`BLOCK_END` for the ``AGENTS.md`` of a repository
    that uses Hydrolog (see :func:`inject_block`). The text depends only on the
    installed package (no dates, no version, no local paths), so the repository files
    ``AGENTS.md`` and ``llms.txt`` equal ``agent_guide(format)`` byte for byte.

    Parameters
    ----------
    format : {"agents", "llms", "agents-md-block"}
        Guide to generate.

    Returns
    -------
    str
        UTF-8 Markdown with ``"\n"`` line ends, ending with a newline.

    Raises
    ------
    InvalidParameterError
        If ``format`` is not allowed (``details.option`` names it).
    ValueError
        If a template or a flow is inconsistent with the catalog (a program error
        that the tests of the repository catch).

    Examples
    --------
    >>> agent_guide("llms").splitlines()[0]
    '# Hydrolog'
    """
    options = validate_command("commands guide", {"format": format})
    guide = cast(GuideFormat, options["format"])
    return "".join(_render(_template(guide), _blocks()))
