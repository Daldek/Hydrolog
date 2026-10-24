"""Executable examples of the user documentation (DOC-2.6, DEV-10.4).

``README.md`` and ``docs/USAGE.md`` hold fenced code blocks. This module runs them, so
an example that stops working fails the gate. A document that does not exist yet is
skipped. Each block is one test, named ``README.md:L42`` after the line of its opening
fence. Blocks are independent (a fresh directory and namespace each): a sequence of
steps, such as ``--check``, a run and a rerun with ``--force``, belongs in one block.

The info string, the text after the opening backticks, selects what happens:

``bash``
    Executed. A line that starts with ``hydrolog `` runs in-process as
    ``hydrolog.cli.main.main(shlex.split(line)[1:])`` and must exit with 0. Empty and
    comment lines are skipped, a trailing ``\\`` continues the line on the next one and
    a trailing ``# comment`` is dropped. There are no pipes, redirections, variables or
    other shell syntax. Lines that do not start with ``hydrolog `` (``pip install ...``)
    are ignored; a block without any ``hydrolog `` line is not a test. The server
    (``hydrolog mcp``) is never started: show it in an ``sh`` block.
``python``
    Executed with ``exec`` in a fresh namespace.
``json``
    Not executed; it must parse as JSON. A block with a line that is only ``...`` (an
    ellipsis) is skipped.
``json output``
    The output of the block it directly follows (the previous fenced block of the
    document, which must run: ``bash`` or ``python``). That block runs again and its
    stdout, which must be one JSON document, has to contain this one. For ``bash`` it
    is the stdout of the last ``hydrolog`` command (give it ``--json``); for ``python``
    the whole stdout. The match is a recursive subset: object keys may be left out;
    scalars are equal (floats to a relative 1e-9, so copy the full value); the string
    ``"..."`` as a value matches anything; lists have the same length, unless the last
    element is ``"..."``, which leaves the rest of the list free. The block itself has
    to parse as JSON, so it holds no ellipsis line.

Any other info string (``sh``, ``console``, ``text``, ``toml``, ``yaml``,
``bash no-run``...) is not executed.

Every block runs in a fresh temporary working directory that holds a copy of
``tests/fixtures`` as ``tests/fixtures`` (a document may use ``--input-file
tests/fixtures/daily_flows_3y.csv``), with ``HYDROLOG_LANG``, ``NOGAT_LANG``,
``HYDROLOG_LOG_LEVEL`` and ``NOGAT_LOG_LEVEL`` unset and ``NOGAT_CONFIG`` pointing at a
file that does not exist. A block that needs an optional extra that is not installed
(a command that ends with ``missing_dependency``, a ``MissingDependencyError`` or the
import of a module of an extra) is skipped.

Three more checks keep the documentation in step with the code. The README Capabilities
table lists every catalog command with its CLI name, MCP tool and Python function
(AGI-1.1), the README MCP section names every tool family, and ``.env.example`` and the
README list every environment variable that the settings read (DEV-18.3).
"""

from __future__ import annotations

import json
import math
import re
import shlex
import shutil
import tomllib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from hydrolog import _settings
from hydrolog.catalog import data_commands
from hydrolog.cli.main import main
from hydrolog.exceptions import MissingDependencyError

REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY / "tests" / "fixtures"
DOCUMENTS = ("README.md", "docs/USAGE.md")
UNSET = ("HYDROLOG_LANG", "NOGAT_LANG", "HYDROLOG_LOG_LEVEL", "NOGAT_LOG_LEVEL")
WILDCARD = "..."
ELLIPSIS_LINES = {"...", "…"}
FENCE = re.compile(r"^(?P<indent>\s*)(?P<ticks>`{3,})(?P<info>[^`]*)$")


def optional_modules() -> set[str]:
    """Names of the modules that the extras of ``pyproject.toml`` bring."""
    project = tomllib.loads((REPOSITORY / "pyproject.toml").read_text("utf-8"))
    extras = project["project"]["optional-dependencies"]
    return {
        re.split(r"[\[<>=!~;\s]", requirement, maxsplit=1)[0].lower().replace("-", "_")
        for requirements in extras.values()
        for requirement in requirements
    }


OPTIONAL_MODULES = optional_modules()


@dataclass(frozen=True)
class Block:
    """A fenced code block of a document."""

    document: str
    line: int
    info: str
    code: str
    previous: Block | None

    @property
    def name(self) -> str:
        """Test id: the document and the line of the opening fence."""
        return f"{self.document}:L{self.line}"


def closes(line: str, ticks: str) -> bool:
    """Whether ``line`` closes a fence opened with ``ticks``."""
    text = line.strip()
    return len(text) >= len(ticks) and set(text) == {"`"}


def parse_blocks(document: str, text: str) -> list[Block]:
    """Return the fenced blocks of ``text`` in order; ``previous`` links them."""
    lines = text.splitlines()
    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        opening = FENCE.match(lines[index])
        if opening is None:
            index += 1
            continue
        start = index
        body: list[str] = []
        index += 1
        while index < len(lines) and not closes(lines[index], opening["ticks"]):
            body.append(lines[index].removeprefix(opening["indent"]))
            index += 1
        if index == len(lines):
            raise ValueError(f"{document}:L{start + 1}: the code fence is not closed")
        index += 1
        info = " ".join(opening["info"].split())
        previous = blocks[-1] if blocks else None
        blocks.append(
            Block(document, start + 1, info, "\n".join(body) + "\n", previous)
        )
    return blocks


def commands_of(code: str) -> list[str]:
    """The ``hydrolog`` command lines of a ``bash`` block, continuations joined."""
    commands: list[str] = []
    line = ""
    for raw in code.splitlines():
        text = raw.strip()
        if not line and (not text or text.startswith("#")):
            continue
        if text.endswith("\\"):
            line += text[:-1].strip() + " "
            continue
        line = (line + text).strip()
        if line == "hydrolog" or line.startswith("hydrolog "):
            commands.append(line)
        line = ""
    return commands


def runs(block: Block) -> bool:
    """Whether the block is executed: ``python``, or ``bash`` with a command."""
    return block.info == "python" or (
        block.info == "bash" and bool(commands_of(block.code))
    )


def collect() -> list[Any]:
    """One test parameter per block that is executed or checked."""
    parameters: list[Any] = []
    for document in DOCUMENTS:
        path = REPOSITORY / document
        if not path.is_file():
            parameters.append(
                pytest.param(
                    None,
                    id=f"{document}:missing",
                    marks=pytest.mark.skip(reason=f"{document} does not exist yet"),
                )
            )
            continue
        for block in parse_blocks(document, path.read_text(encoding="utf-8")):
            if runs(block) or block.info in ("json", "json output"):
                parameters.append(pytest.param(block, id=block.name))
    return parameters


def needs_extra(error: BaseException) -> bool:
    """Whether ``error`` says that an optional extra is not installed."""
    if isinstance(error, MissingDependencyError):
        return True
    return (
        isinstance(error, ModuleNotFoundError)
        and (error.name or "").partition(".")[0] in OPTIONAL_MODULES
    )


def error_code(stderr: str) -> str | None:
    """``code`` of the error document on the last line of ``stderr``, if any."""
    lines = stderr.strip().splitlines()
    try:
        document = json.loads(lines[-1])
    except (IndexError, ValueError):
        return None
    code = document.get("code") if isinstance(document, dict) else None
    return code if isinstance(code, str) else None


def run_line(block: Block, line: str, capsys: pytest.CaptureFixture[str]) -> str:
    """Run one ``hydrolog`` line in-process; return its stdout."""
    words = shlex.split(line, comments=True)
    if words[1:2] == ["mcp"] and not {"-h", "--help"} & set(words):
        pytest.fail(f"{block.name}: `{line}` starts the server; fence it as `sh`")
    capsys.readouterr()
    status = main(words[1:])
    captured = capsys.readouterr()
    if status == 0:
        return captured.out
    if error_code(captured.err) == "missing_dependency":
        pytest.skip(f"`{line}` needs an optional extra that is not installed")
    pytest.fail(f"{block.name}: `{line}` exited with {status}\n{captured.err}")


def run_python(block: Block, capsys: pytest.CaptureFixture[str]) -> str:
    """Execute a ``python`` block in a fresh namespace; return its stdout."""
    capsys.readouterr()
    namespace: dict[str, Any] = {"__name__": "__documentation__"}
    try:
        exec(compile(block.code, block.name, "exec"), namespace)
    except (MissingDependencyError, ModuleNotFoundError) as error:
        if not needs_extra(error):
            raise
        pytest.skip(f"{block.name} needs an optional extra that is not installed")
    return capsys.readouterr().out


def execute(block: Block, capsys: pytest.CaptureFixture[str]) -> str:
    """Run a block; return the stdout that a ``json output`` block shows."""
    if block.info == "python":
        return run_python(block, capsys)
    output = ""
    for line in commands_of(block.code):
        output = run_line(block, line, capsys)
    return output


def mismatches(expected: Any, actual: Any, path: str = "$") -> list[str]:
    """Where ``expected`` is not contained in ``actual`` (rules: module docstring)."""
    if isinstance(expected, str) and expected == WILDCARD:
        return []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected an object, found {actual!r}"]
        problems: list[str] = []
        for key, value in expected.items():
            if key in actual:
                problems += mismatches(value, actual[key], f"{path}.{key}")
            else:
                problems.append(f"{path}.{key}: missing")
        return problems
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected a list, found {actual!r}"]
        open_ended = bool(expected) and expected[-1] == WILDCARD
        shown = expected[:-1] if open_ended else expected
        if len(actual) < len(shown) or (not open_ended and len(actual) > len(shown)):
            more = "or more " if open_ended else ""
            return [f"{path}: expected {len(shown)} {more}items, found {len(actual)}"]
        return [
            problem
            for index, value in enumerate(shown)
            for problem in mismatches(value, actual[index], f"{path}[{index}]")
        ]
    return (
        []
        if same_scalar(expected, actual)
        else [f"{path}: expected {expected!r}, found {actual!r}"]
    )


def same_scalar(expected: Any, actual: Any) -> bool:
    """Equality of JSON scalars: ``True`` is not ``1``; floats to a relative 1e-9."""
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    numbers = (int, float)
    if isinstance(expected, numbers) and isinstance(actual, numbers):
        if isinstance(expected, int) and isinstance(actual, int):
            return expected == actual
        return math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-12)
    return bool(expected == actual)


def check_json(block: Block) -> None:
    """A ``json`` block parses, unless it holds an ellipsis line."""
    lines = {line.strip().rstrip(",") for line in block.code.splitlines()}
    if lines & ELLIPSIS_LINES:
        pytest.skip(f"{block.name} holds an ellipsis line")
    try:
        json.loads(block.code)
    except ValueError as error:
        pytest.fail(f"{block.name} is not valid JSON: {error}")


def check_output(block: Block, capsys: pytest.CaptureFixture[str]) -> None:
    """A ``json output`` block is contained in the stdout of the block before it."""
    source = block.previous
    if source is None or not runs(source):
        pytest.fail(
            f"{block.name}: `json output` must directly follow a block that runs"
        )
    try:
        expected = json.loads(block.code)
    except ValueError as error:
        pytest.fail(
            f"{block.name} is not valid JSON ('...' is a value, not a line): {error}"
        )
    output = execute(source, capsys)
    try:
        actual = json.loads(output)
    except ValueError:
        pytest.fail(
            f"{block.name}: the stdout of {source.name} is not one JSON document "
            f"(use --json, print only JSON): {output[:200]!r}"
        )
    problems = mismatches(expected, actual)
    assert not problems, f"{block.name} differs from the output of {source.name}:\n" + (
        "\n".join(problems)
    )


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fresh working directory with the fixtures and a clean environment."""
    shutil.copytree(FIXTURES, tmp_path / "tests" / "fixtures")
    for name in UNSET:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NOGAT_CONFIG", str(tmp_path / "absent.toml"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize("block", collect())
def test_documented_example_works(
    block: Block | None, workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert block is not None
    if block.info == "json":
        check_json(block)
    elif block.info == "json output":
        check_output(block, capsys)
    else:
        execute(block, capsys)


def test_output_match_is_a_subset_with_wildcards() -> None:
    actual = {"a": 1, "b": {"c": [1, 2, 3], "d": 0.30000000000000004}, "e": None}
    shown = {"a": 1, "b": {"c": [1, "..."], "d": 0.3}, "e": None}
    assert mismatches(shown, actual) == []
    assert mismatches({"a": "...", "b": {"c": [1, 2, 3]}}, actual) == []
    wrong = [{"a": 2}, {"x": 1}, {"b": {"c": [1, 2]}}, {"b": {"c": [1, 2, 4]}}]
    wrong += [{"b": {"c": []}}, {"e": 0}, {"a": True}, {"b": {"d": 0.31}}]
    for document in wrong:
        assert mismatches(document, actual), document


def test_fences_and_commands_are_found_in_a_document() -> None:
    text = (
        "intro\n```bash\nhydrolog cn list\n```\n\n- item\n\n"
        "  ````text\n  ```\n  ````\n  ```json output\n  {}\n  ```\n"
    )
    blocks = parse_blocks("x.md", text)
    assert [(block.line, block.info) for block in blocks] == [
        (2, "bash"),
        (8, "text"),
        (11, "json output"),
    ]
    assert blocks[1].code == "```\n"
    assert blocks[2].previous is blocks[1]
    code = (
        "pip install x\n# note\nhydrolog tc kirpich \\\n  --length-km 8.2\n\n"
        "hydrolog cn list\n"
    )
    assert commands_of(code) == [
        "hydrolog tc kirpich --length-km 8.2",
        "hydrolog cn list",
    ]


def section(text: str, heading: str) -> str:
    """The text of the ``## heading`` section, up to the next ``## `` heading."""
    start = text.index(f"\n## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : None if end < 0 else end]


def test_readme_capabilities_table_lists_the_catalog() -> None:
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    table = section(readme, "Capabilities")
    lines = [line for line in table.splitlines() if line.startswith("|")]
    rows = [re.findall(r"`([^`]+)`", line) for line in lines]
    listed = [
        (cli, tool, f"hydrolog.operations.{function}")
        for cli, tool, function in (row for row in rows if len(row) == 3)
    ]
    commands = data_commands()
    assert listed == [(c.name, c.operation_id, c.function) for c in commands]
    assert (
        f"{len(commands)} commands in {len({c.group for c in commands})} groups"
        in table
    )


def test_readme_mcp_section_names_the_tool_families() -> None:
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    mcp = section(readme, "MCP server")
    commands = data_commands()
    families = {c.group for c in commands} | {c.name for c in commands if c.core}
    assert not {name for name in families if f"`{name}`" not in mcp}


class ReadVariables(Mapping[str, str]):
    """An empty environment that records the variables asked for."""

    def __init__(self) -> None:
        self.read: set[str] = set()

    def __getitem__(self, key: str) -> str:
        self.read.add(key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0


def test_env_example_and_readme_list_every_variable_the_settings_read() -> None:
    environment = ReadVariables()
    for key in _settings.KEYS:
        _settings.resolve_setting(key, environ=environment, file_data={})
    _settings.config_path(environment)
    example = (REPOSITORY / ".env.example").read_text(encoding="utf-8")
    declared = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", example, re.MULTILINE))
    assert declared == environment.read
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    assert not {name for name in declared if f"`{name}`" not in readme}
