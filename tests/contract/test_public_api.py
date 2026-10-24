"""Contract tests of the public Python API (AGI-7.1, AGI-7.3)."""

from __future__ import annotations

import importlib
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import hydrolog
from hydrolog.exceptions import InvalidParameterError

CONSUMER = """
import hydrolog

result = hydrolog.run_command('cn lookup', hsg='B', land_cover='forest').to_dict()
plan = hydrolog.check_command('report generate', output='r.md').to_dict()
options = hydrolog.validate_command('cn lookup', hsg='B', land_cover='forest')
listing = hydrolog.list_commands().to_json()
schema = hydrolog.command_schema('tc kirpich').to_dict()
page = hydrolog.list_commands(limit=3).to_dict()
reveal_type(result)
reveal_type(options)
reveal_type(listing)
reveal_type(schema)
"""


class TestAll:
    """``hydrolog.__all__`` is the public API."""

    @pytest.mark.parametrize("name", hydrolog.__all__)
    def test_every_name_is_importable(self, name):
        module = importlib.import_module("hydrolog")
        assert getattr(module, name) is not None

    def test_the_five_functions_of_the_interface_are_exported(self):
        assert {
            "list_commands",
            "command_schema",
            "validate_command",
            "check_command",
            "run_command",
        } <= set(hydrolog.__all__)

    def test_the_error_classes_and_the_registry_are_exported(self):
        assert issubclass(hydrolog.InvalidParameterError, hydrolog.HydrologError)
        assert "validation_error" in hydrolog.ERROR_CODES

    def test_there_are_no_duplicates(self):
        assert len(set(hydrolog.__all__)) == len(hydrolog.__all__)


class TestImport:
    """Importing the package is cheap: no numerical library, no file, no network."""

    HEAVY = ("numpy", "scipy", "rasterio", "matplotlib")

    def test_import_hydrolog_loads_no_numerical_library(self):
        code = textwrap.dedent(
            f"""
            import sys
            import hydrolog
            loaded = [m for m in {self.HEAVY!r} if m in sys.modules]
            assert not loaded, loaded
            """
        )
        done = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=False
        )
        assert done.returncode == 0, done.stderr

    def test_calling_a_function_loads_the_catalog_lazily(self):
        code = textwrap.dedent(
            """
            import sys
            import hydrolog
            assert "hydrolog.catalog" not in sys.modules
            hydrolog.list_commands()
            assert "hydrolog.catalog" in sys.modules
            """
        )
        done = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=False
        )
        assert done.returncode == 0, done.stderr


class TestTypes:
    """A consumer that calls the five functions type-checks under ``--strict``."""

    def test_consumer_snippet_passes_mypy_strict(self, tmp_path):
        from mypy import api

        snippet = tmp_path / "consumer.py"
        snippet.write_text(textwrap.dedent(CONSUMER), encoding="utf-8")
        stdout, stderr, status = api.run(
            [
                "--strict",
                "--no-incremental",
                "--cache-dir",
                str(tmp_path / "mypy-cache"),
                "--config-file",
                "",
                str(snippet),
            ]
        )
        errors = [line for line in stdout.splitlines() if ": error:" in line]
        assert errors == [], stdout + stderr
        revealed = [line for line in stdout.splitlines() if "Revealed type" in line]
        assert [line.split('"')[1] for line in revealed] == [
            "dict[str, Any]",
            "dict[str, Any]",
            "str",
            "dict[str, Any]",
        ]
        assert status == 0

    def test_a_wrong_call_is_rejected_by_mypy(self, tmp_path):
        """The check is real: misuse of the API is a type error."""
        from mypy import api

        snippet = tmp_path / "wrong.py"
        snippet.write_text(
            "import hydrolog\n"
            "hydrolog.command_schema(3)\n"
            "hydrolog.list_commands(limit='x')\n",
            encoding="utf-8",
        )
        stdout, _, status = api.run(
            [
                "--strict",
                "--no-incremental",
                "--cache-dir",
                str(tmp_path / "mypy-cache"),
                "--config-file",
                "",
                str(snippet),
            ]
        )
        assert status == 1
        assert stdout.count("error:") == 2


class TestBehaviour:
    """The five functions at work."""

    def test_run_command_takes_the_options_as_keywords(self):
        document = hydrolog.run_command("cn lookup", hsg="B", land_cover="forest")
        assert document.to_dict()["result"]["cn"] == 60

    def test_validate_command_applies_the_defaults_and_does_not_run(self):
        assert hydrolog.validate_command("commands list") == {"limit": 100}

    def test_validate_command_refuses_an_unknown_option(self):
        with pytest.raises(InvalidParameterError) as caught:
            hydrolog.validate_command("cn lookup", hsg="B", nonsense=1)
        assert caught.value.details["reason"] == "unknown_option"

    def test_list_commands_and_command_schema_return_documents(self):
        listing = hydrolog.list_commands(limit=2)
        assert listing.to_dict()["page"]["total"] == len(
            hydrolog.list_commands().to_dict()["commands"]
        )
        schema = hydrolog.command_schema("tc kirpich").to_dict()
        assert schema["commands"][0]["name"] == "tc kirpich"

    def test_check_command_of_a_writing_command_returns_the_plan(self, tmp_path):
        target = tmp_path / "guide.md"
        plan = hydrolog.check_command(
            "commands guide", format="llms", output=str(target)
        ).to_dict()
        assert plan["check"] is True
        assert plan["result"]["targets"][0]["action"] == "write"
        assert not Path(target).exists()

    def test_check_command_of_a_read_only_command_is_a_validation_error(self):
        with pytest.raises(InvalidParameterError) as caught:
            hydrolog.check_command("cn lookup", hsg="B", land_cover="forest")
        assert caught.value.code == "validation_error"
        assert caught.value.details["reason"] == "no_check"
