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
    """The report of the settings, their sources, the credentials and the store."""

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
        import platformdirs

        result = _show()
        assert [item["key"] for item in result["settings"]] == [
            "lang",
            "log_level",
            "data_dir",
            "state_dir",
            "request_limit",
            "request_window",
        ]
        assert _settings(result) == {
            "lang": {"key": "lang", "value": "pl", "source": "default", "detail": None},
            "log_level": {
                "key": "log_level",
                "value": "warning",
                "source": "default",
                "detail": None,
            },
            "data_dir": {
                "key": "data_dir",
                "value": str(platformdirs.user_data_path("nogat")),
                "source": "default",
                "detail": None,
            },
            "state_dir": {
                "key": "state_dir",
                "value": str(platformdirs.user_state_path("nogat")),
                "source": "default",
                "detail": None,
            },
            "request_limit": {
                "key": "request_limit",
                "value": "300",
                "source": "default",
                "detail": None,
            },
            "request_window": {
                "key": "request_window",
                "value": "60",
                "source": "default",
                "detail": None,
            },
        }
        assert result["config_file"] == {
            "path": str(tmp_path / "absent.toml"),
            "exists": False,
        }

    def test_the_request_limit_is_reported_with_its_source(self, tmp_path, monkeypatch):
        path = tmp_path / "nogat.toml"
        path.write_text(
            "[nogat]\nrequest_limit = 0\n[hydrolog]\nrequest_limit = 120\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        monkeypatch.setenv("NOGAT_REQUEST_WINDOW", "30")
        settings = _settings(_show())
        assert settings["request_limit"] == {
            "key": "request_limit",
            "value": "120",
            "source": "file",
            "detail": "[hydrolog] request_limit",
        }
        assert settings["request_window"] == {
            "key": "request_window",
            "value": "30",
            "source": "environment",
            "detail": "NOGAT_REQUEST_WINDOW",
        }

    def test_hydrolog_has_no_store(self):
        """Hydrolog writes only the files named by the caller."""
        assert _show()["store"] is None

    def test_the_admin_key_is_reported_present_never_shown(self, monkeypatch):
        assert _show()["credentials"] == [
            {"name": "HYDROLOG_ADMIN_API_KEY", "present": False},
            {"name": "HYDROLOG_ADMIN_API_KEY_FILE", "present": False},
        ]
        monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", "sekretny-klucz")
        document = json.loads(run_command("config show").to_json())
        assert document["result"]["credentials"][0] == {
            "name": "HYDROLOG_ADMIN_API_KEY",
            "present": True,
        }
        assert "sekretny-klucz" not in json.dumps(document)

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
