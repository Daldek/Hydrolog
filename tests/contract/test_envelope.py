"""Contract tests of the ``hydrolog-result/1`` envelope and the error documents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import hydrolog
from hydrolog.catalog import CommandResult, run_command
from hydrolog.exceptions import (
    ConflictError,
    ForbiddenPathError,
    InvalidParameterError,
    NotFoundError,
    error_document,
)

from . import _nogat

ENVELOPE_KEYS = [
    "schema",
    "tool",
    "version",
    "command",
    "check",
    "status",
    "result",
    "notices",
    "inputs",
]


def _envelope(name: str, /, **options: Any) -> dict[str, Any]:
    return run_command(name, options).to_dict()


def _violations(name: str, document: dict[str, Any]) -> list[str]:
    return [e.message for e in _nogat.validator(name).iter_errors(document)]


class TestFields:
    """The keys and the types of every envelope."""

    def test_keys_and_types(self):
        envelope = _envelope("cn lookup", hsg="B", land_cover="forest")
        assert list(envelope) == ENVELOPE_KEYS
        assert envelope["schema"] == "hydrolog-result/1"
        assert envelope["tool"] == "hydrolog"
        assert envelope["version"] == hydrolog.__version__
        assert envelope["command"] == "cn lookup"
        assert envelope["check"] is False
        assert envelope["status"] == "ok"
        assert isinstance(envelope["result"], dict)
        assert isinstance(envelope["notices"], list)
        assert isinstance(envelope["inputs"], dict)

    def test_the_result_is_a_document_with_its_schema_first(self):
        envelope = _envelope("cn lookup", hsg="B", land_cover="forest")
        assert list(envelope["result"])[0] == "schema"
        assert envelope["result"]["schema"] == "hydrolog-cn-lookup/1"

    def test_the_old_keys_are_gone(self):
        envelope = _envelope("cn lookup", hsg="B", land_cover="forest")
        assert not {"hydrolog_version", "files"} & set(envelope)

    def test_inputs_hold_the_normalized_options_with_defaults(self):
        envelope = _envelope("cn lookup", hsg="B", land_cover="forest")
        assert envelope["inputs"] == {"hsg": "B", "land_cover": "forest"}
        pages = _envelope("commands list")
        assert pages["inputs"] == {"limit": 100}

    def test_notices_have_level_code_and_message(self):
        envelope = _envelope("cn lookup", hsg="B", land_cover="forest")
        assert envelope["notices"]
        for notice in envelope["notices"]:
            assert sorted(notice) == ["code", "level", "message"]
            assert notice["level"] in ("info", "warning")
        assert _violations("result-1", envelope) == []

    def test_the_json_text_is_the_dictionary(self):
        result = run_command("cn lookup", {"hsg": "B", "land_cover": "forest"})
        assert json.loads(result.to_json()) == result.to_dict()

    def test_a_result_that_is_not_a_mapping_raises_type_error(self):
        for value in (1, 2.5, "text", [1, 2], None):
            with pytest.raises(TypeError, match="document"):
                CommandResult("cn lookup", {}, value, "hydrolog-cn-lookup/1").to_dict()


class TestFiles:
    """Written files are listed inside ``result`` (DEV-19.19)."""

    @staticmethod
    def _guide(tmp_path: Path, **options: Any) -> dict[str, Any]:
        return _envelope(
            "commands guide",
            format="llms",
            output=str(tmp_path / "llms.txt"),
            **options,
        )

    def test_a_new_file_is_written(self, tmp_path):
        envelope = self._guide(tmp_path)
        target = tmp_path / "llms.txt"
        content = target.read_bytes()
        assert envelope["result"]["files"] == [
            {
                "path": str(target),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "status": "written",
            }
        ]
        assert "files" not in envelope
        assert _violations("result-1", envelope) == []

    def test_a_forced_overwrite_is_replaced(self, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("old", encoding="utf-8")
        envelope = self._guide(tmp_path, force=True)
        record = envelope["result"]["files"][0]
        assert record["status"] == "replaced"
        assert record["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
        assert _violations("result-1", envelope) == []

    def test_a_command_that_writes_nothing_has_no_files_key(self):
        assert "files" not in _envelope("commands guide", format="llms")["result"]

    def test_check_has_a_plan_and_no_files(self, tmp_path):
        envelope = self._guide(tmp_path, check=True)
        assert envelope["check"] is True
        assert envelope["result"]["schema"] == "hydrolog-plan/1"
        assert envelope["result"]["targets"][0]["action"] == "write"
        assert "files" not in envelope["result"]
        assert not (tmp_path / "llms.txt").exists()
        assert _violations("result-1", envelope) == []


class TestPage:
    """``page`` appears for paginated commands only."""

    def test_commands_list_is_paginated(self):
        envelope = _envelope("commands list", limit=3)
        page = envelope["page"]
        assert page["total"] > 3
        assert page["truncated"] is True
        assert isinstance(page["next_cursor"], str)
        assert len(envelope["result"]["commands"]) == 3
        assert _violations("result-1", envelope) == []

    def test_the_last_page_has_no_cursor(self):
        total = _envelope("commands list")["page"]["total"]
        envelope = _envelope("commands list", limit=total)
        assert envelope["page"] == {
            "total": total,
            "truncated": False,
            "next_cursor": None,
        }

    def test_the_whole_catalog_of_commands_schema_is_paginated(self):
        envelope = _envelope("commands schema", limit=2)
        assert len(envelope["result"]["commands"]) == 2
        assert envelope["page"]["truncated"] is True
        assert _violations("result-1", envelope) == []

    def test_the_schema_of_one_command_has_no_page(self):
        assert "page" not in _envelope("commands schema", command="tc kirpich")

    def test_other_commands_have_no_page(self):
        assert "page" not in _envelope("cn lookup", hsg="B", land_cover="forest")


FAILURES = [
    pytest.param(
        lambda: run_command("cn lookup", {"hsg": "Z", "land_cover": "forest"}),
        InvalidParameterError,
        id="validation",
    ),
    pytest.param(
        lambda: run_command("no such command"), NotFoundError, id="unknown command"
    ),
    pytest.param(
        lambda: run_command("commands guide", {"format": "llms", "output": __file__}),
        ConflictError,
        id="conflict",
    ),
    pytest.param(
        lambda: run_command("commands guide", {"output": "x.md"}, allowed_dirs=()),
        ForbiddenPathError,
        id="forbidden",
    ),
    pytest.param(
        lambda: run_command(
            "stats daily",
            {
                "input_file": "no/such/file.csv",
                "value_column": "Q",
                "date_column": "date",
            },
        ),
        NotFoundError,
        id="missing file",
    ),
]


class TestErrorDocuments:
    """Every failure of a command is a ``hydrolog-error/1`` document."""

    @pytest.mark.parametrize(("call", "kind"), FAILURES)
    def test_the_error_document_validates_against_error_1(self, call, kind):
        with pytest.raises(kind) as caught:
            call()
        document = error_document(caught.value, "some command")
        assert _violations("error-1", document) == []
        assert document["schema"] == "hydrolog-error/1"
        assert document["code"] == caught.value.code
        assert document["exit_code"] == caught.value.exit_code
        assert document["command"] == "some command"

    def test_the_conflict_names_its_paths(self):
        with pytest.raises(ConflictError) as caught:
            run_command("commands guide", {"format": "llms", "output": __file__})
        document = error_document(caught.value)
        assert document["code"] == "conflict"
        assert document["details"] == {
            "reason": "output_exists",
            "paths": [str(Path(__file__).resolve())],
        }
        assert "command" not in document

    def test_an_unexpected_exception_is_an_internal_error_document(self):
        document = error_document(RuntimeError("boom"), "cn lookup")
        assert document["code"] == "internal_error"
        assert _violations("error-1", document) == []

    def test_validation_details_name_the_option(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command("cn lookup", {"hsg": "Z", "land_cover": "forest"})
        error = caught.value
        assert error.details["option"] == "hsg"
        assert error.details["reason"] == "choice"
