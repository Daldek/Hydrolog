"""Generic tests over *every* catalog command: the CLI against ``run_command``.

The tests are parametrized over :func:`hydrolog.catalog.data_commands`, so a command
added to the catalog is covered without touching this file. Conventions for examples
(shared with the authors of the groups): paths are relative to the repository root and
point to files that exist there (``tests/fixtures``); options that write a file
(``writes=True``) are redirected to a scratch directory; an example that needs an
optional extra that is not installed is skipped. The envelopes are compared in full;
the only field left out is the SHA-256 of a written file (a generated file may embed
the date or time), which is instead checked against the file on disk.
"""

import json
from pathlib import Path

import pytest

from hydrolog.catalog import (
    Command,
    command_schema,
    data_commands,
    run_command,
    validate_command,
)
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


@pytest.fixture(autouse=True)
def _repository_root(monkeypatch):
    """Examples use paths relative to the repository root; no ambient language."""
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.delenv("HYDROLOG_LANG", raising=False)
    monkeypatch.setenv("COLUMNS", "100")


def _scratch_outputs(command: Command, example, directory: Path) -> dict:
    """The example with every output path moved into ``directory``."""
    adjusted = dict(example)
    for option in command.options:
        if option.writes and option.name in adjusted:
            suffix = Path(str(adjusted[option.name])).suffix
            adjusted[option.name] = str(directory / f"{option.name}{suffix}")
    return adjusted


def _without_digests(envelope: dict) -> dict:
    """The envelope without the SHA-256 of written files (a file may embed a time)."""
    stripped = dict(envelope)
    stripped["files"] = [
        {key: value for key, value in record.items() if key != "sha256"}
        for record in envelope["files"]
    ]
    return stripped


def _run_or_skip(command: Command, example):
    try:
        return run_command(command, example)
    except MissingDependencyError as exc:
        pytest.skip(f"optional extra not installed: {exc}")


def test_the_catalog_is_not_empty():
    assert COMMANDS and EXAMPLES


@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_json_envelope_equals_run_command(command, index, capsys, tmp_path):
    example = _scratch_outputs(command, command.examples[index], tmp_path)
    expected = _run_or_skip(command, example).to_dict()

    argv = [*command.name.split(), *example_arguments(command, example), "--json"]
    code = main(argv)
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    assert out.count("\n") == 1, "the envelope is one line"
    envelope = json.loads(out)
    assert _without_digests(envelope) == _without_digests(expected)
    for record in envelope["files"]:
        assert sha256_file(record["path"]) == record["sha256"]


@pytest.mark.parametrize("lang", ["pl", "en"])
@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_human_summary_of_every_example(command, index, lang, capsys, tmp_path):
    example = _scratch_outputs(command, command.examples[index], tmp_path)
    has_lang_option = any(option.name == "lang" for option in command.options)
    if has_lang_option:
        example["lang"] = lang  # the texts of the result follow --lang
    result = _run_or_skip(command, example).to_dict()["result"]

    argv = [*command.name.split(), *example_arguments(command, example)]
    if not has_lang_option:
        argv += ["--lang", lang]
    code = main(argv)
    out, err = capsys.readouterr()

    assert (code, err) == (0, "")
    if isinstance(result, dict) and "schema" in result:
        # A versioned document is printed as the JSON it is, ready to be redirected.
        assert json.loads(out) == result
    elif isinstance(result, str) and "\n" in result:
        assert out == result.rstrip("\n") + "\n"
    else:
        assert out.splitlines()[0] == f"{command.name}: {command.summarize(lang)}"
        assert ("Result" if lang == "en" else "Wynik") in out


@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_example_survives_the_round_trip_through_the_command_line(command, index):
    example = command.examples[index]
    line = parse_command_line(command, example_arguments(command, example))
    carried = {k: v for k, v in example.items() if k != "lang" and v is not None}
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
    assert json.loads(err) == error_document(expected, command.name, "pl")


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.name)
def test_schema_flag_prints_the_command_schema(command, capsys):
    assert main([*command.name.split(), "--schema"]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert json.loads(out) == command_schema(command)


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
        if option.name == "lang":
            # The command's own language option *is* the general --lang.
            assert option.type == "choice"
            assert option.choices == ("pl", "en")
            continue
        flags = {option.flag}
        if option.type == "boolean":
            flags.add("--no-" + option.flag[2:])
        assert not flags & taken, f"{command.name}: {option.name} collides"
        taken |= flags
    build_command_parser(command)  # raises ValueError on a collision


def test_no_group_is_called_mcp():
    assert "mcp" not in {command.group for command in COMMANDS}
