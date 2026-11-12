"""Shared user settings of the Nogat tools (DEV-18.1): file, environment, defaults.

A setting comes from the first of: the command-line option, the environment variable
(``HYDROLOG_<KEY>`` before ``NOGAT_<KEY>``), ``nogat.toml`` (section ``[hydrolog]``
before ``[nogat]``) and the built-in default. The file is ``nogat.toml`` in the user
configuration directory (``platformdirs.user_config_path("nogat")``) or the path in
``NOGAT_CONFIG``; it is read with ``tomllib`` and Hydrolog works without it.

Hydrolog has three settings: ``lang`` (language of human-readable output),
``log_level`` (verbosity of the CLI log on stderr) and ``data_dir`` (the shared data
directory, DEV-18.2: the web GUI keeps the reports of „Zgłoś uwagę” in
``<data_dir>/hydrolog/feedback.sqlite3``). It has no store and no cache, so
``cache_dir`` of the shared section is not used. Its one credential, the key of the
web GUI's admin page, comes from the environment only (DEV-18.4):
:func:`admin_api_key`. The web GUI's app menu lists the deployment's GUIs from the
shared table ``gui`` of ``[nogat]`` (DEV-15.4): :func:`gui_addresses`.
"""

from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

import platformdirs

__all__ = [
    "ADMIN_API_KEY",
    "ADMIN_API_KEY_FILE",
    "CREDENTIALS",
    "DEFAULTS",
    "KEYS",
    "Setting",
    "admin_api_key",
    "config_path",
    "credentials",
    "default_data_dir",
    "gui_addresses",
    "load_file",
    "resolve_setting",
]

TOOL: Final = "hydrolog"
KEYS: Final = ("lang", "log_level", "data_dir")
"""Names of the settings of Hydrolog."""
DEFAULTS: Final[Mapping[str, str]] = {"lang": "pl", "log_level": "warning"}
"""Built-in default of each setting but ``data_dir`` (:func:`default_data_dir`)."""
ADMIN_API_KEY: Final = "HYDROLOG_ADMIN_API_KEY"
"""The variable that holds the key of the web GUI's admin page (DEV-18.4)."""
ADMIN_API_KEY_FILE: Final = "HYDROLOG_ADMIN_API_KEY_FILE"
"""The variable that names a file holding that key (a secret file of a service)."""
CREDENTIALS: Final = (ADMIN_API_KEY, ADMIN_API_KEY_FILE)
"""The credential variables Hydrolog reads, in the order ``config show`` lists them."""

SettingSource = Literal["option", "environment", "file", "default"]


@dataclass(frozen=True)
class Setting:
    """One setting with its value and where the value comes from.

    Attributes
    ----------
    key : str
        Name of the setting.
    value : str
        Effective value.
    source : {"option", "environment", "file", "default"}
        Where the value comes from.
    detail : str or None
        The environment variable, the ``[section]`` of the file or the option that
        gave the value; ``None`` for the default.
    """

    key: str
    value: str
    source: SettingSource
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return ``{"key", "value", "source", "detail"}``."""
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "detail": self.detail,
        }


def config_path(environ: Mapping[str, str] | None = None) -> Path:
    """Return the path of ``nogat.toml`` (``NOGAT_CONFIG`` or the user config dir).

    Parameters
    ----------
    environ : Mapping, optional
        Environment to read; defaults to ``os.environ``.

    Returns
    -------
    pathlib.Path
        The path; the file need not exist.
    """
    source = os.environ if environ is None else environ
    given = source.get("NOGAT_CONFIG", "").strip()
    if given:
        return Path(given).expanduser()
    return Path(platformdirs.user_config_path("nogat")) / "nogat.toml"


def load_file(path: Path) -> dict[str, Any]:
    """Read ``nogat.toml``; a file that cannot be used is an empty configuration.

    Parameters
    ----------
    path : pathlib.Path
        The file.

    Returns
    -------
    dict
        The parsed TOML, or ``{}`` when the file is missing, unreadable, not UTF-8 or
        not valid TOML (a broken settings file must not stop a calculation).
    """
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}


def default_data_dir() -> str:
    """Return the default ``data_dir``: the user data directory of ``nogat`` (DEV-18.2).

    Returns
    -------
    str
        ``platformdirs.user_data_path("nogat")``, e.g. ``~/.local/share/nogat``.
    """
    return str(platformdirs.user_data_path("nogat"))


def _normalize(key: str, raw: object) -> str | None:
    """Return the value of ``key`` from ``raw``, or ``None`` when it is not usable."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    if key == "data_dir":
        return str(Path(raw.strip()).expanduser())
    value = raw.strip().lower()
    if key == "lang":
        language = re.split(r"[_.\-@]", value, maxsplit=1)[0]
        return language if language in ("pl", "en") else None
    if key == "log_level":
        return value if value in ("debug", "info", "warning", "error") else None
    return value


def resolve_setting(
    key: str,
    *,
    explicit: str | None = None,
    environ: Mapping[str, str] | None = None,
    file_data: Mapping[str, Any] | None = None,
) -> Setting:
    """Resolve one setting by the order of DEV-18.1.

    Parameters
    ----------
    key : str
        One of :data:`KEYS`.
    explicit : str, optional
        The value of the command-line option, already validated by the caller.
    environ : Mapping, optional
        Environment to read; defaults to ``os.environ``.
    file_data : Mapping, optional
        Parsed ``nogat.toml``; defaults to the file at :func:`config_path`.

    Returns
    -------
    Setting
        The effective value and its source. An environment variable or file value
        that is not valid for the key is ignored, as an ambient setting should not
        stop a calculation.
    """
    if key not in KEYS:
        raise KeyError(key)
    if explicit is not None:
        return Setting(key, explicit, "option", f"--{key.replace('_', '-')}")
    source = os.environ if environ is None else environ
    for prefix in (TOOL.upper(), "NOGAT"):
        name = f"{prefix}_{key.upper()}"
        value = _normalize(key, source.get(name))
        if value is not None:
            return Setting(key, value, "environment", name)
    data = load_file(config_path(source)) if file_data is None else file_data
    for section in (TOOL, "nogat"):
        table = data.get(section)
        if isinstance(table, Mapping):
            value = _normalize(key, table.get(key))
            if value is not None:
                return Setting(key, value, "file", f"[{section}] {key}")
    return Setting(
        key, default_data_dir() if key == "data_dir" else DEFAULTS[key], "default"
    )


def credentials(environ: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    """Return each credential variable and whether it is set (DEV-18.6).

    Parameters
    ----------
    environ : Mapping, optional
        Environment to read; defaults to ``os.environ``.

    Returns
    -------
    list of dict
        ``{"name", "present"}`` for each of :data:`CREDENTIALS`, ``present`` when the
        variable is set and not blank; never the value.
    """
    source = os.environ if environ is None else environ
    return [
        {"name": name, "present": bool(source.get(name, "").strip())}
        for name in CREDENTIALS
    ]


def admin_api_key(environ: Mapping[str, str] | None = None) -> str | None:
    """Return the key of the web GUI's admin page, or ``None`` when none is set.

    The key is ``HYDROLOG_ADMIN_API_KEY``; without it, the text of the file that
    ``HYDROLOG_ADMIN_API_KEY_FILE`` names (the secret file of a service or a
    container). Surrounding whitespace is dropped. It is never read from
    ``nogat.toml`` (DEV-18.4).

    Parameters
    ----------
    environ : Mapping, optional
        Environment to read; defaults to ``os.environ``.

    Returns
    -------
    str or None
        The key; ``None`` when both variables are unset or blank, or the file is
        missing, unreadable, not UTF-8 or blank.
    """
    source = os.environ if environ is None else environ
    key = source.get(ADMIN_API_KEY, "").strip()
    if key:
        return key
    path = source.get(ADMIN_API_KEY_FILE, "").strip()
    if not path:
        return None
    try:
        key = Path(path).expanduser().read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    return key or None


def gui_addresses(
    environ: Mapping[str, str] | None = None,
    file_data: Mapping[str, Any] | None = None,
) -> dict[str, str] | None:
    """Return the deployment's GUI addresses: the table ``gui`` of ``[nogat]``.

    The table names each GUI of the ecosystem by its registry name in lower case and
    gives its address, absolute or a path on the same origin (DEV-15.4, DEV-18.1),
    e.g. ``hydrograf = "http://127.0.0.1:8080/"``. The web GUI's app menu lists them;
    it has no default, so without the table the menu is not drawn. The table describes
    the deployment, so only ``[nogat]`` gives it: no environment variable and no
    ``[hydrolog]`` table.

    Parameters
    ----------
    environ : Mapping, optional
        Environment to read (``NOGAT_CONFIG``); defaults to ``os.environ``.
    file_data : Mapping, optional
        Parsed ``nogat.toml``; defaults to the file at :func:`config_path`.

    Returns
    -------
    dict or None
        Name -> address for each entry whose name and address are strings, the address
        not blank (surrounding whitespace dropped), in the file's order; ``None`` when
        the file is missing or unusable or gives no table ``gui`` in ``[nogat]``.
    """
    source = os.environ if environ is None else environ
    data = load_file(config_path(source)) if file_data is None else file_data
    shared = data.get("nogat")
    table = shared.get("gui") if isinstance(shared, Mapping) else None
    if not isinstance(table, Mapping):
        return None
    return {
        name: address.strip()
        for name, address in table.items()
        if isinstance(name, str) and isinstance(address, str) and address.strip()
    }
