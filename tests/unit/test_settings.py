"""Tests for the shared settings (DEV-18.1): precedence, lenient values, the file."""

from __future__ import annotations

import pytest

from hydrolog._settings import (
    DEFAULTS,
    KEYS,
    config_path,
    load_file,
    resolve_setting,
)


def _toml(tmp_path, text: str):
    path = tmp_path / "nogat.toml"
    path.write_text(text, encoding="utf-8")
    return path


class TestPrecedence:
    """option > HYDROLOG_ > NOGAT_ > [hydrolog] > [nogat] > default."""

    FILE = {"hydrolog": {"lang": "en"}, "nogat": {"lang": "pl"}}

    def test_the_default_is_polish_and_warning(self):
        assert DEFAULTS == {"lang": "pl", "log_level": "warning"}
        for key in KEYS:
            setting = resolve_setting(key, environ={}, file_data={})
            assert (setting.value, setting.source, setting.detail) == (
                DEFAULTS[key],
                "default",
                None,
            )

    def test_the_option_wins_over_everything(self):
        setting = resolve_setting(
            "lang",
            explicit="en",
            environ={"HYDROLOG_LANG": "pl", "NOGAT_LANG": "pl"},
            file_data=self.FILE,
        )
        assert (setting.value, setting.source, setting.detail) == (
            "en",
            "option",
            "--lang",
        )

    def test_the_tool_variable_wins_over_the_shared_one(self):
        setting = resolve_setting(
            "lang",
            environ={"HYDROLOG_LANG": "en", "NOGAT_LANG": "pl"},
            file_data=self.FILE,
        )
        assert (setting.value, setting.source, setting.detail) == (
            "en",
            "environment",
            "HYDROLOG_LANG",
        )

    def test_the_shared_variable_wins_over_the_file(self):
        setting = resolve_setting(
            "lang", environ={"NOGAT_LANG": "en"}, file_data={"hydrolog": {"lang": "pl"}}
        )
        assert (setting.value, setting.detail) == ("en", "NOGAT_LANG")

    def test_the_tool_section_wins_over_the_shared_section(self):
        setting = resolve_setting("lang", environ={}, file_data=self.FILE)
        assert (setting.value, setting.source, setting.detail) == (
            "en",
            "file",
            "[hydrolog] lang",
        )

    def test_the_shared_section_applies_when_the_tool_section_lacks_the_key(self):
        setting = resolve_setting(
            "lang",
            environ={},
            file_data={"hydrolog": {"log_level": "info"}, "nogat": {"lang": "en"}},
        )
        assert (setting.value, setting.detail) == ("en", "[nogat] lang")

    def test_each_key_is_resolved_on_its_own(self):
        environ = {"HYDROLOG_LOG_LEVEL": "debug"}
        assert (
            resolve_setting("log_level", environ=environ, file_data={}).value == "debug"
        )
        assert (
            resolve_setting("lang", environ=environ, file_data={}).source == "default"
        )

    def test_an_unknown_key_is_refused(self):
        with pytest.raises(KeyError):
            resolve_setting("data_dir", environ={}, file_data={})

    def test_the_process_environment_is_used_by_default(self, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        assert resolve_setting("lang", file_data={}).detail == "HYDROLOG_LANG"


class TestLenientValues:
    """An ambient setting that cannot be used never stops a calculation."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("en", "en"),
            ("EN", "en"),
            ("  pl  ", "pl"),
            ("en_US.UTF-8", "en"),
            ("pl_PL", "pl"),
            ("en-GB", "en"),
            ("pl@euro", "pl"),
        ],
    )
    def test_locale_values_give_their_language(self, raw, expected):
        setting = resolve_setting("lang", environ={"HYDROLOG_LANG": raw}, file_data={})
        assert (setting.value, setting.source) == (expected, "environment")

    @pytest.mark.parametrize("raw", ["de", "C", "POSIX", "", "   ", "english"])
    def test_an_unsupported_language_is_ignored(self, raw):
        """The next source applies: here the lower-priority variable."""
        setting = resolve_setting(
            "lang",
            environ={"HYDROLOG_LANG": raw, "NOGAT_LANG": "en"},
            file_data={},
        )
        assert (setting.value, setting.detail) == ("en", "NOGAT_LANG")

    def test_an_unsupported_value_everywhere_gives_the_default(self):
        setting = resolve_setting(
            "lang", environ={"HYDROLOG_LANG": "de"}, file_data={"hydrolog": {"lang": 5}}
        )
        assert (setting.value, setting.source) == ("pl", "default")

    @pytest.mark.parametrize("raw", ["DEBUG", " Info ", "warning", "error"])
    def test_log_levels_are_case_insensitive(self, raw):
        setting = resolve_setting(
            "log_level", environ={"HYDROLOG_LOG_LEVEL": raw}, file_data={}
        )
        assert setting.value == raw.strip().lower()

    @pytest.mark.parametrize("raw", ["verbose", "critical", "10"])
    def test_an_unknown_log_level_is_ignored(self, raw):
        setting = resolve_setting(
            "log_level", environ={"HYDROLOG_LOG_LEVEL": raw}, file_data={}
        )
        assert (setting.value, setting.source) == ("warning", "default")

    @pytest.mark.parametrize("raw", [5, True, ["en"], {"a": 1}])
    def test_a_file_value_of_the_wrong_type_is_ignored(self, raw):
        setting = resolve_setting(
            "lang", environ={}, file_data={"hydrolog": {"lang": raw}}
        )
        assert setting.source == "default"

    def test_a_section_that_is_not_a_table_is_ignored(self):
        setting = resolve_setting(
            "lang", environ={}, file_data={"hydrolog": "en", "nogat": {"lang": "en"}}
        )
        assert setting.detail == "[nogat] lang"


class TestFile:
    """``nogat.toml``: read leniently."""

    def test_the_file_is_read(self, tmp_path, monkeypatch):
        path = _toml(tmp_path, '[hydrolog]\nlang = "en"\n')
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        setting = resolve_setting("lang")
        assert (setting.value, setting.source) == ("en", "file")

    def test_a_missing_file_is_an_empty_configuration(self, tmp_path):
        assert load_file(tmp_path / "absent.toml") == {}

    def test_a_broken_file_is_ignored(self, tmp_path, monkeypatch):
        path = _toml(tmp_path, "[hydrolog\nlang = ")
        assert load_file(path) == {}
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        assert resolve_setting("lang").source == "default"

    def test_a_directory_instead_of_a_file_is_ignored(self, tmp_path):
        assert load_file(tmp_path) == {}

    def test_a_file_with_non_utf8_bytes_is_ignored(self, tmp_path):
        path = tmp_path / "nogat.toml"
        path.write_bytes(b'[hydrolog]\nlang = "\xff\xfe"\n')
        assert load_file(path) == {}


class TestConfigPath:
    """Where ``nogat.toml`` is looked for."""

    def test_nogat_config_names_the_file(self):
        assert str(config_path({"NOGAT_CONFIG": "/tmp/x/nogat.toml"})) == (
            "/tmp/x/nogat.toml"
        )

    def test_the_home_directory_is_expanded(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", str(tmp_path))
        assert config_path({"NOGAT_CONFIG": "~/n.toml"}) == tmp_path / "n.toml"

    @pytest.mark.parametrize("value", ["", "   "])
    def test_a_blank_variable_falls_back_to_the_user_directory(self, value):
        path = config_path({"NOGAT_CONFIG": value})
        assert path.name == "nogat.toml"
        assert path == config_path({})

    def test_the_default_is_in_the_user_configuration_directory(self):
        import platformdirs

        assert config_path({}) == platformdirs.user_config_path("nogat") / "nogat.toml"

    def test_the_process_environment_is_the_default_source(self, tmp_path):
        """The autouse fixture points ``NOGAT_CONFIG`` at an absent file."""
        assert config_path() == tmp_path / "absent.toml"
