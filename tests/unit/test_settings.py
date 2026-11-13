"""Tests for the shared settings (DEV-18.1): precedence, lenient values, the file,
``data_dir`` (DEV-18.2), the credential of the GUI's admin page (DEV-18.4), the
GUI addresses of the app menu (DEV-15.4), the request limit of a public GUI
(DEV-15.9) and its operator (DEV-15.7)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import platformdirs
import pytest

from hydrolog._settings import (
    DEFAULTS,
    KEYS,
    admin_api_key,
    config_path,
    credentials,
    gui_addresses,
    load_file,
    operator_table,
    resolve_setting,
)


def _toml(tmp_path, text: str):
    path = tmp_path / "nogat.toml"
    path.write_text(text, encoding="utf-8")
    return path


class TestPrecedence:
    """option > HYDROLOG_ > NOGAT_ > [hydrolog] > [nogat] > default."""

    FILE = {"hydrolog": {"lang": "en"}, "nogat": {"lang": "pl"}}

    def test_the_defaults_are_polish_warning_the_user_data_directory_and_300_in_60(
        self,
    ):
        assert DEFAULTS == {
            "lang": "pl",
            "log_level": "warning",
            "request_limit": "300",
            "request_window": "60",
        }
        expected = {**DEFAULTS, "data_dir": str(platformdirs.user_data_path("nogat"))}
        for key in KEYS:
            setting = resolve_setting(key, environ={}, file_data={})
            assert (setting.value, setting.source, setting.detail) == (
                expected[key],
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
            resolve_setting("cache_dir", environ={}, file_data={})

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
        assert config_path({"NOGAT_CONFIG": "/tmp/x/nogat.toml"}) == Path(
            "/tmp/x/nogat.toml"
        )

    def test_the_home_directory_is_expanded(self, home):
        assert config_path({"NOGAT_CONFIG": "~/n.toml"}) == home / "n.toml"

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


class TestDataDir:
    """``data_dir``: a path in the platform's notation, its case kept, ``~`` expanded.

    Windows writes ``/Dane/Nogat`` as ``\\Dane\\Nogat``.
    """

    @pytest.mark.parametrize(
        "environ",
        [
            {"HYDROLOG_DATA_DIR": "/Dane/Nogat", "NOGAT_DATA_DIR": "/x"},
            {"NOGAT_DATA_DIR": "/Dane/Nogat"},
        ],
    )
    def test_the_variables_give_a_path_as_written(self, environ):
        setting = resolve_setting("data_dir", environ=environ, file_data={})
        expected = str(Path("/Dane/Nogat"))
        assert (setting.value, setting.source) == (expected, "environment")

    def test_the_home_directory_is_expanded(self, home):
        setting = resolve_setting(
            "data_dir", environ={"HYDROLOG_DATA_DIR": " ~/Dane "}, file_data={}
        )
        assert setting.value == str(home / "Dane")

    def test_the_shared_section_of_the_file_gives_it(self):
        setting = resolve_setting(
            "data_dir", environ={}, file_data={"nogat": {"data_dir": "/srv/Nogat"}}
        )
        expected = str(Path("/srv/Nogat"))
        assert (setting.value, setting.detail) == (expected, "[nogat] data_dir")


class TestCredentials:
    """``HYDROLOG_ADMIN_API_KEY`` or the file ``HYDROLOG_ADMIN_API_KEY_FILE`` names."""

    def test_config_show_learns_only_whether_each_variable_is_set(self):
        environ = {
            "HYDROLOG_ADMIN_API_KEY": "sekret",
            "HYDROLOG_ADMIN_API_KEY_FILE": " ",
        }
        assert credentials(environ) == [
            {"name": "HYDROLOG_ADMIN_API_KEY", "present": True},
            {"name": "HYDROLOG_ADMIN_API_KEY_FILE", "present": False},
        ]

    def test_the_variable_gives_the_key_without_its_whitespace(self):
        assert admin_api_key({"HYDROLOG_ADMIN_API_KEY": " sekret\n"}) == "sekret"

    def test_without_the_variable_the_file_gives_it(self, tmp_path):
        path = tmp_path / "admin.key"
        path.write_text("z-pliku\n", encoding="utf-8")
        environ = {
            "HYDROLOG_ADMIN_API_KEY": " ",
            "HYDROLOG_ADMIN_API_KEY_FILE": str(path),
        }
        assert admin_api_key(environ) == "z-pliku"

    def test_the_variable_wins_over_the_file(self, tmp_path):
        path = tmp_path / "admin.key"
        path.write_text("z-pliku", encoding="utf-8")
        environ = {
            "HYDROLOG_ADMIN_API_KEY": "ze-zmiennej",
            "HYDROLOG_ADMIN_API_KEY_FILE": str(path),
        }
        assert admin_api_key(environ) == "ze-zmiennej"

    def test_the_home_directory_of_the_file_is_expanded(self, home):
        (home / "admin.key").write_text("domowy", encoding="utf-8")
        assert admin_api_key({"HYDROLOG_ADMIN_API_KEY_FILE": "~/admin.key"}) == "domowy"

    @pytest.mark.parametrize("content", [None, b"", b"  \n", b"\xff\xfe\xfa"])
    def test_a_file_without_a_usable_key_is_no_key(self, tmp_path, content):
        path = tmp_path / "admin.key"
        if content is not None:
            path.write_bytes(content)
        assert admin_api_key({"HYDROLOG_ADMIN_API_KEY_FILE": str(path)}) is None

    def test_no_variable_is_no_key(self):
        assert admin_api_key({}) is None

    def test_the_file_of_the_settings_never_gives_the_key(self, tmp_path):
        """DEV-18.4: a credential in nogat.toml is not read."""
        path = _toml(tmp_path, '[hydrolog]\nadmin_api_key = "z-pliku-ustawien"\n')
        assert admin_api_key({"NOGAT_CONFIG": str(path)}) is None


class TestGuiAddresses:
    """``[nogat] gui``: the deployment's GUIs for Nogat's app menu, no default."""

    def test_the_table_of_the_file(self, tmp_path):
        path = _toml(
            tmp_path,
            "[nogat]\n"
            'gui = { hydrolog = "http://127.0.0.1:8070/", hydrograf = "/h/" }\n',
        )
        assert gui_addresses({"NOGAT_CONFIG": str(path)}) == {
            "hydrolog": "http://127.0.0.1:8070/",
            "hydrograf": "/h/",
        }

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"nogat": {"lang": "pl"}},
            {"nogat": "gui"},
            {"nogat": {"gui": "http://127.0.0.1:8080/"}},
            {"hydrolog": {"gui": {"hydrograf": "http://127.0.0.1:8080/"}}},
        ],
    )
    def test_no_table_in_nogat_is_no_menu(self, data):
        assert gui_addresses({}, file_data=data) is None


class TestRequestLimit:
    """``request_limit`` (1 to 1 000 000) and ``request_window`` (1 to 86 400 s):
    whole numbers, a TOML integer or digits; anything else is ignored (DEV-15.9)."""

    @pytest.mark.parametrize(
        ("key", "environ", "detail"),
        [
            (
                "request_limit",
                {"HYDROLOG_REQUEST_LIMIT": "500"},
                "HYDROLOG_REQUEST_LIMIT",
            ),
            ("request_limit", {"NOGAT_REQUEST_LIMIT": "500"}, "NOGAT_REQUEST_LIMIT"),
            (
                "request_window",
                {"HYDROLOG_REQUEST_WINDOW": "500", "NOGAT_REQUEST_WINDOW": "9"},
                "HYDROLOG_REQUEST_WINDOW",
            ),
            (
                "request_window",
                {"NOGAT_REQUEST_WINDOW": " 500 "},
                "NOGAT_REQUEST_WINDOW",
            ),
        ],
    )
    def test_the_variables_give_it(self, key, environ, detail):
        setting = resolve_setting(
            key, environ=environ, file_data={"hydrolog": {key: 7}}
        )
        assert (setting.value, setting.source, setting.detail) == (
            "500",
            "environment",
            detail,
        )

    @pytest.mark.parametrize("key", ["request_limit", "request_window"])
    def test_the_tool_section_wins_over_the_shared_one(self, key):
        data = {"hydrolog": {key: 120}, "nogat": {key: 30}}
        setting = resolve_setting(key, environ={}, file_data=data)
        assert (setting.value, setting.detail) == ("120", f"[hydrolog] {key}")

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [(120, "120"), ("120", "120"), (" 120 ", "120"), ("0120", "120"), (1, "1")],
    )
    def test_an_integer_or_digits_are_a_count(self, raw, expected):
        setting = resolve_setting(
            "request_limit", environ={}, file_data={"nogat": {"request_limit": raw}}
        )
        assert (setting.value, setting.source) == (expected, "file")

    @pytest.mark.parametrize(
        ("key", "largest"),
        [("request_limit", 1_000_000), ("request_window", 86_400)],
    )
    def test_each_has_a_largest_value(self, key, largest):
        def value(raw):
            return resolve_setting(
                key, environ={}, file_data={"nogat": {key: raw}}
            ).value

        assert value(largest) == str(largest)
        assert value(largest + 1) == DEFAULTS[key]
        assert value(str(largest + 1)) == DEFAULTS[key]

    @pytest.mark.parametrize(
        "raw",
        [
            0,
            -5,
            True,
            False,
            1.5,
            60.0,
            "0",
            "-5",
            "+5",
            "1.5",
            "1e3",
            "abc",
            "",
            " ",
            "٣٠",
            None,
            [60],
        ],
    )
    @pytest.mark.parametrize("key", ["request_limit", "request_window"])
    def test_anything_else_is_ignored(self, key, raw):
        """The next source applies: here ``[nogat]``, after the variables."""
        environ = {f"HYDROLOG_{key.upper()}": raw} if isinstance(raw, str) else {}
        data = {"hydrolog": {key: raw}, "nogat": {key: 42}}
        setting = resolve_setting(key, environ=environ, file_data=data)
        assert (setting.value, setting.detail) == ("42", f"[nogat] {key}")


class TestOperatorTable:
    """``[nogat.operator]``: the operator of a public GUI, only from ``[nogat]``."""

    def test_the_table_of_the_file_as_toml_gives_it(self, tmp_path):
        path = _toml(
            tmp_path,
            '[nogat.operator]\nname = "Jan Kowalski"\nterms_effective = 2026-11-20\n',
        )
        assert operator_table({"NOGAT_CONFIG": str(path)}) == {
            "name": "Jan Kowalski",
            "terms_effective": date(2026, 11, 20),
        }

    def test_the_process_environment_names_the_file(self, tmp_path, monkeypatch):
        path = _toml(tmp_path, '[nogat.operator]\nemail = "a@example.org"\n')
        monkeypatch.setenv("NOGAT_CONFIG", str(path))
        assert operator_table() == {"email": "a@example.org"}

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"nogat": {"lang": "pl"}},
            {"nogat": "operator"},
            {"nogat": {"operator": "Jan Kowalski"}},
            {"hydrolog": {"operator": {"name": "Jan Kowalski"}}},
        ],
    )
    def test_no_table_in_nogat_is_no_operator(self, data):
        assert operator_table({}, file_data=data) is None

    def test_a_missing_file_is_no_operator(self, tmp_path):
        assert operator_table({"NOGAT_CONFIG": str(tmp_path / "absent.toml")}) is None
