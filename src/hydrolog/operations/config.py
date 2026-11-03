"""Operations of the group ``config``: the effective settings (DEV-18.6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hydrolog._serialization import JsonResultMixin
from hydrolog._settings import KEYS, config_path, resolve_setting

__all__ = ["ConfigShow", "config_show"]


@dataclass
class ConfigShow(JsonResultMixin):
    """The settings of Hydrolog as ``config show`` reports them.

    Attributes
    ----------
    settings : list of dict
        Each setting with ``key``, ``value``, ``source`` (``option``, ``environment``,
        ``file`` or ``default``) and ``detail`` (the variable or section that gave
        the value).
    config_file : dict
        ``path`` of ``nogat.toml`` and whether it ``exists``.
    credentials : list of dict
        The credentials Hydrolog reads, each with ``name`` and ``present``; none.
    store : dict or None
        The store root with its source and size; ``None`` because Hydrolog writes
        no store.
    """

    settings: list[dict[str, Any]]
    config_file: dict[str, Any]
    credentials: list[dict[str, Any]] = field(default_factory=list)
    store: dict[str, Any] | None = None


def config_show() -> ConfigShow:
    """Show the effective settings of Hydrolog (``config show``).

    The command line options of a call (``--lang``) apply to that call only and are
    not part of this report: it shows what the environment and ``nogat.toml`` give.

    Returns
    -------
    ConfigShow
        ``settings`` (``lang``, ``log_level``), the settings file, ``credentials``
        (none) and ``store`` (``None``).

    Examples
    --------
    >>> report = config_show()
    >>> [item["key"] for item in report.settings]
    ['lang', 'log_level']
    """
    path = config_path()
    return ConfigShow(
        settings=[resolve_setting(key).to_dict() for key in KEYS],
        config_file={"path": str(path), "exists": path.is_file()},
    )
