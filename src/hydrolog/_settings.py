"""Shared user settings of the Nogat tools (DEV-18.1): file, environment, defaults.

A setting comes from the first of: the command-line option, the environment variable
(``HYDROLOG_<KEY>`` before ``NOGAT_<KEY>``), ``nogat.toml`` (section ``[hydrolog]``
before ``[nogat]``) and the built-in default. The file is ``nogat.toml`` in the user
configuration directory (``platformdirs.user_config_path("nogat")``) or the path in
``NOGAT_CONFIG``; it is read with ``tomllib`` and Hydrolog works without it.

Hydrolog has two settings, ``lang`` (language of human-readable output) and
``log_level`` (verbosity of the CLI log on stderr). It reads no credentials and has no
store or cache, so ``data_dir`` and ``cache_dir`` of the shared section are not used.
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
    "DEFAULTS",
    "KEYS",
    "Setting",
    "config_path",
    "load_file",
    "resolve_setting",
]

TOOL: Final = "hydrolog"
KEYS: Final = ("lang", "log_level")
"""Names of the settings of Hydrolog."""
DEFAULTS: Final[Mapping[str, str]] = {"lang": "pl", "log_level": "warning"}
"""Built-in default of each setting."""

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


def _normalize(key: str, raw: object) -> str | None:
    """Return the value of ``key`` from ``raw``, or ``None`` when it is not usable."""
    if not isinstance(raw, str) or not raw.strip():
        return None
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
    return Setting(key, DEFAULTS[key], "default")
