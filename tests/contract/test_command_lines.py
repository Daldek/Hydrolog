"""The example calls of the catalog are canonical lines that read back and run.

A consumer stores and passes on the lines of the catalog (Nogat ECO-054, the CLI line
of the GUI): :func:`hydrolog.parse_command` must read every one into a call that
:func:`hydrolog.format_command` writes as the same line, and that call must run.
"""

from pathlib import Path
from typing import Any

import pytest

from hydrolog import format_command, parse_command
from hydrolog.catalog import catalog_document, data_commands, run_command
from hydrolog.catalog.spec import Command
from hydrolog.exceptions import MissingDependencyError

from . import _nogat

COMMANDS = data_commands()
CALLS = {
    entry["name"]: [example["call"] for example in entry["examples"]]
    for entry in catalog_document(COMMANDS)["commands"]
}


def _examples() -> list[Any]:
    return [
        pytest.param(command, number, id=f"{command.name}#{number}")
        for command in COMMANDS
        for number in range(len(command.examples))
    ]


def _outputs_into(command: Command, options: dict, directory: Path) -> dict:
    moved = dict(options)
    for name, value in options.items():
        if command.option(name).path_role == "output":
            moved[name] = str(directory / Path(str(value)).name)
    return moved


@pytest.mark.parametrize(("command", "number"), _examples())
def test_the_example_call_is_the_canonical_line_of_its_options(command, number):
    call = CALLS[command.name][number]
    example = {k: v for k, v in command.examples[number].items() if v is not None}

    parsed = parse_command(call)

    assert call == format_command(command.name, example)
    assert parsed.command == command.name
    assert parsed.run == {}
    assert format_command(*parsed) == call


@pytest.mark.parametrize(("command", "number"), _examples())
def test_the_call_read_from_the_line_runs(command, number, tmp_path, monkeypatch):
    monkeypatch.chdir(_nogat.ROOT)  # examples name their inputs from the repository
    parsed = parse_command(CALLS[command.name][number])

    try:
        envelope = run_command(
            parsed.command, _outputs_into(command, parsed.options, tmp_path)
        ).to_dict()
    except MissingDependencyError:
        pytest.skip("an optional extra is not installed")

    assert envelope["status"] == "ok"
    assert envelope["command"] == command.name
