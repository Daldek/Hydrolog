"""Contract tests of the notice codes of the catalog examples (plan D16).

Every example of every command runs offline from the repository root, as in
``test_catalog.py``, and each notice of its envelope has a code of ``NOTICES`` with
the level of the registry, never the catch-all code of a warning of another library,
and the details and message that the registry promises: exactly the detail keys of
the code, and the template filled with them as the message. ``route network`` adds
``details.node_id`` to the notice of a node and starts its message with the id; a
routing model, and a library warning that the network caught, give no other details
there (their notice keeps the text of its emitter).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from hydrolog._warnings import render
from hydrolog.catalog import Command, data_commands, run_command
from hydrolog.catalog.notices import NOTICES
from hydrolog.exceptions import MissingDependencyError

from . import _nogat

COMMANDS = data_commands()
CATCH_ALL = frozenset({"user_warning", "runtime_warning"})


def _examples() -> list[Any]:
    return [
        pytest.param(command, number, id=f"{command.name}#{number}")
        for command in COMMANDS
        for number in range(len(command.examples))
    ]


def _notices(command: Command, number: int, tmp_path: Path) -> list[dict[str, Any]]:
    """The notices of an example, its outputs moved into ``tmp_path``."""
    options = dict(command.examples[number])
    for name, value in command.examples[number].items():
        if command.option(name).path_role == "output":
            options[name] = str(tmp_path / Path(str(value)).name)
    try:
        envelope = run_command(command, options).to_dict()
    except MissingDependencyError:
        pytest.skip("an optional extra is not installed")
    notices: list[dict[str, Any]] = envelope["notices"]
    return notices


def _problems(command: str, notice: dict[str, Any]) -> list[str]:
    """List what is wrong with one notice of an example (empty when nothing)."""
    code = notice["code"]
    spec = NOTICES.get(code)
    if spec is None:
        return [f"{code}: not in NOTICES"]
    problems = []
    if notice["level"] != spec.level:
        problems.append(f"{code}: level {notice['level']}, registered {spec.level}")
    if code in CATCH_ALL:
        problems.append(f"{code}: a warning without a code of its own")
    details = dict(notice.get("details", {}))
    message = notice["message"]
    if command == "route network" and "node_id" in details:
        node_id = details.pop("node_id")
        if not message.startswith(f"{node_id}: "):
            problems.append(f"{code}: the message does not start with {node_id!r}")
        message = message.removeprefix(f"{node_id}: ")
        if not details:  # the text of a routing model or of a caught warning
            return problems
    if spec.own_text:
        if details:
            problems.append(f"{code}: carries the details {sorted(details)}")
        return problems
    if set(details) != set(spec.details):
        problems.append(f"{code}: details {sorted(details)}, registered {spec.details}")
    elif message != render(spec.template, details):
        problems.append(f"{code}: {message!r} is not the template filled")
    return problems


@pytest.fixture
def repository_root(monkeypatch):
    """Run from the repository root: examples name their input files relative to it."""
    monkeypatch.chdir(_nogat.ROOT)


@pytest.mark.usefixtures("repository_root")
class TestTheNoticesOfTheExamples:
    @pytest.mark.parametrize(("command", "number"), _examples())
    def test_every_notice_has_a_registered_code_details_and_message(
        self, command, number, tmp_path
    ):
        notices = _notices(command, number, tmp_path)
        problems = [
            problem for notice in notices for problem in _problems(command.name, notice)
        ]
        assert problems == []
