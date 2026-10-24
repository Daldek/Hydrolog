"""Tests for ``config show`` (DEV-18.6): the effective settings, run as a command."""

from __future__ import annotations

import json

import pytest

from hydrolog.catalog import run_command


def _show() -> dict:
    document = json.loads(run_command("config show").to_json())
    assert document["status"] == "ok"
    return document["result"]


def _settings(result: dict) -> dict[str, dict]:
    return {item["key"]: item for item in result["settings"]}


class TestConfigShow:
    """The report of the settings, their sources and the (absent) store."""

    def test_the_document_keys(self):
        result = _show()
        assert result["schema"] == "hydrolog-config/1"
        assert set(result) == {
            "schema",
            "settings",
            "config_file",
            "credentials",
            "store",
        }

    def test_the_defaults_without_environment_or_file(self, tmp_path):
        result = _show()
        assert _settings(result) == {
            "lang": {"key": "lang", "value": "pl", "source": "default", "detail": None},
            "log_level": {
                "key": "log_level",
                "value": "warning",
                "source": "default",
                "detail": None,
            },
        }
        assert result["config_file"] == {
            "path": str(tmp_path / "absent.toml"),
            "exists": False,
        }

    def test_hydrolog_has_no_store_and_no_credentials(self):
        """Hydrolog writes only the files named by the caller."""
        result = _show()
        assert result["store"] is None
        assert result["credentials"] == []

    def test_the_environment_is_reported_with_its_variable(self, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        monkeypatch.setenv("NOGAT_LOG_LEVEL", "debug")
        settings = _settings(_show())
        assert settings["lang"] == {
            "key": "lang",
            "value": "en",
            "source": "environment",
            "detail": "HYDROLOG_LANG",
        }
        assert settings["log_level"]["value"] == "debug"
        assert settings["log_level"]["detail"] == "NOGAT_LOG_LEVEL"

    def test_the_file_is_reported_with_its_section(self, tmp_path, monkeypatch):
        path = tmp_path / "nogat.toml"
        path.write_text('[nogat]\nlog_level = "info"\n', encoding="utf-8")
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        result = _show()
        assert result["config_file"] == {"path": str(path), "exists": True}
        assert _settings(result)["log_level"] == {
            "key": "log_level",
            "value": "info",
            "source": "file",
            "detail": "[nogat] log_level",
        }

    def test_a_broken_file_still_exists_but_gives_the_defaults(
        self, tmp_path, monkeypatch
    ):
        path = tmp_path / "nogat.toml"
        path.write_text("not = [toml", encoding="utf-8")
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        result = _show()
        assert result["config_file"]["exists"] is True
        assert {s["source"] for s in result["settings"]} == {"default"}

    def test_a_command_line_option_is_not_part_of_the_report(self):
        """``--lang`` applies to a call only; the command takes no such option."""
        with pytest.raises(Exception, match="Unknown option 'lang'"):
            run_command("config show", {"lang": "en"})

    def test_the_command_reads_only(self):
        from hydrolog.catalog import get_command

        command = get_command("config show")
        assert command.effects.read_only is True
        assert command.check is None
