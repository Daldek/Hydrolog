"""Generic tests over *every* catalog command: the CLI against ``run_command``.

The tests are parametrized over :func:`hydrolog.catalog.data_commands`, so a command
added to the catalog is covered without touching this file. Conventions for examples
(shared with the authors of the groups): paths are relative to the repository root and
point to files that exist there (``tests/fixtures``); options that write a file
(``path_role="output"``) are redirected to a scratch directory; an example that needs
an optional extra that is not installed is skipped. The envelopes are compared in full;
the only field left out is the SHA-256 of a written file (``result.files``; a generated
file may embed the date or time), which is instead checked against the file on disk.
"""

import json
import os
from pathlib import Path

import pytest

from hydrolog.catalog import (
    Command,
    check_command,
    command_schema,
    data_commands,
    run_command,
    validate_command,
)
from hydrolog.catalog.document import COMMAND_LIST_SCHEMA, COMMANDS_SCHEMA
from hydrolog.catalog.envelope import sha256_file
from hydrolog.cli.main import main
from hydrolog.cli.parser import (
    GLOBAL_FLAGS,
    build_command_parser,
    example_arguments,
    format_example,
    parse_command_line,
)
from hydrolog.exceptions import (
    InvalidParameterError,
    MissingDependencyError,
    error_document,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = data_commands()
EXAMPLES = [
    pytest.param(command, index, id=f"{command.name}#{index}")
    for command in COMMANDS
    for index in range(len(command.examples))
]
CHECKED_EXAMPLES = [
    pytest.param(command, index, id=f"{command.name}#{index}")
    for command in COMMANDS
    if command.check is not None
    for index in range(len(command.examples))
]


@pytest.fixture(autouse=True)
def _repository_root(monkeypatch, tmp_path):
    """Examples use paths relative to the repository root; no ambient settings."""
    monkeypatch.chdir(REPO_ROOT)
    for name in (
        "HYDROLOG_LANG",
        "NOGAT_LANG",
        "HYDROLOG_LOG_LEVEL",
        "NOGAT_LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NOGAT_CONFIG", str(tmp_path / "no-nogat.toml"))
    monkeypatch.setenv("COLUMNS", "100")


def _scratch_outputs(command: Command, example, directory: Path) -> dict:
    """The example with every output path moved into ``directory``."""
    adjusted = dict(example)
    for option in command.options:
        if option.writes and option.name in adjusted:
            suffix = Path(str(adjusted[option.name])).suffix
            adjusted[option.name] = str(directory / f"{option.name}{suffix}")
    return adjusted


def _written(envelope: dict) -> list[dict]:
    """The ``files`` of an envelope: ``result.files``, absent from most results."""
    result = envelope["result"]
    return result.get("files", []) if isinstance(result, dict) else []


def _without_digests(envelope: dict) -> dict:
    """The envelope without the SHA-256 of written files (a file may embed a time)."""
    stripped = json.loads(json.dumps(envelope))
    for record in _written(stripped):
        del record["sha256"]
    return stripped


def _api_envelope(command: Command, example) -> dict:
    """The envelope of ``run_command``, with the files it wrote removed again.

    The CLI refuses to replace a file without ``--force``, so it has to start from
    the state ``run_command`` started from.
    """
    try:
        envelope = run_command(command, example).to_dict()
    except MissingDependencyError as exc:
        pytest.skip(f"optional extra not installed: {exc}")
    for record in _written(envelope):
        os.remove(record["path"])
    return envelope


def test_the_catalog_is_not_empty():
    assert COMMANDS and EXAMPLES and CHECKED_EXAMPLES


@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_json_envelope_equals_run_command(command, index, capsys, tmp_path):
    example = _scratch_outputs(command, command.examples[index], tmp_path)
    expected = _api_envelope(command, example)

    argv = [*command.name.split(), *example_arguments(command, example), "--json"]
    code = main(argv)
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    assert out.count("\n") == 1, "the envelope is one line"
    envelope = json.loads(out)
    assert _without_digests(envelope) == _without_digests(expected)
    for record in _written(envelope):
        assert sha256_file(record["path"]) == record["sha256"]


@pytest.mark.parametrize("lang", ["pl", "en"])
@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_human_summary_of_every_example(command, index, lang, capsys, tmp_path):
    example = _scratch_outputs(command, command.examples[index], tmp_path)
    result = _api_envelope(command, example)["result"]

    code = main(
        [*command.name.split(), *example_arguments(command, example), "--lang", lang]
    )
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    assert out.endswith("\n") and not out.endswith("\n\n")
    lines = out.splitlines()
    schema = result.get("schema") if isinstance(result, dict) else None
    if schema == COMMANDS_SCHEMA:
        # The description of commands has no title line: it starts with a command.
        assert lines[0].startswith(f"{result['commands'][0]['name']} (hydrolog_")
    elif schema == "hydrolog-guide/1" and "text" in result:
        # The guide is the text itself, ready to be redirected into a file.
        assert out == result["text"].rstrip("\n") + "\n"
    else:
        assert lines[0] == f"{command.name}: {command.summarize(lang)}"
    if schema is None:
        assert ("Result" if lang == "en" else "Wynik") in out
    if schema == COMMAND_LIST_SCHEMA:
        assert all(entry["name"] in out for entry in result["commands"])


@pytest.mark.parametrize(("command", "index"), CHECKED_EXAMPLES)
def test_check_flag_prints_the_plan_of_check_command(command, index, capsys, tmp_path):
    example = _scratch_outputs(command, command.examples[index], tmp_path)
    expected = check_command(command, example).to_dict()

    argv = [*command.name.split(), *example_arguments(command, example)]
    code = main([*argv, "--check", "--json"])
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    assert json.loads(out) == expected
    # a route command without `output` has no file to plan and computes (ADR-0008)
    plans = command.group != "route" or any(command.option(n).writes for n in example)
    assert expected["check"] is plans
    assert list(tmp_path.iterdir()) == [], "a plan writes nothing"


@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_example_survives_the_round_trip_through_the_command_line(command, index):
    example = command.examples[index]
    line = parse_command_line(command, example_arguments(command, example))
    carried = {k: v for k, v in example.items() if v is not None}
    assert validate_command(command, line.options) == validate_command(command, carried)


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.name)
def test_missing_options_fail_like_run_command(command, capsys):
    try:
        run_command(command, {})
    except InvalidParameterError as exc:
        expected = exc
    else:
        pytest.skip("the command needs no options")

    code = main(["--json", *command.name.split()])
    out, err = capsys.readouterr()

    assert out == ""
    assert code == expected.exit_code == 2
    # The last line of stderr is the English document (AGI-3.3).
    assert json.loads(err.splitlines()[-1]) == error_document(
        expected, command.name, "en"
    )


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.name)
def test_schema_flag_prints_the_command_schema(command, capsys):
    assert main([*command.name.split(), "--schema"]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert json.loads(out) == command_schema(command).to_dict()


@pytest.mark.parametrize("lang", ["pl", "en"])
@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.name)
def test_help_names_every_option_and_example(command, lang, capsys):
    assert main([*command.name.split(), "--help", "--lang", lang]) == 0
    out, _ = capsys.readouterr()
    for option in command.options:
        assert option.flag in out, option.name
        if option.type == "boolean":
            assert "--no-" + option.flag[2:] in out
    for example in command.examples[:3]:
        assert format_example(command, example) in out
    assert command.summarize(lang) in out.replace("\n", " ")


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.name)
def test_no_option_collides_with_the_general_flags(command):
    taken = set(GLOBAL_FLAGS)
    for option in command.options:
        flags = {option.flag}
        if option.type == "boolean":
            flags.add("--no-" + option.flag[2:])
        assert not flags & taken, f"{command.name}: {option.name} collides"
        taken |= flags
    build_command_parser(command)  # raises ValueError on a collision


def test_no_group_is_called_mcp():
    assert "mcp" not in {command.group for command in COMMANDS}
