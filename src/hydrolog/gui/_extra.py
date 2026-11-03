"""The ``gui`` extra: Starlette and uvicorn, imported only when the GUI is served."""

from __future__ import annotations

import importlib
from typing import Final

from hydrolog.exceptions import MissingDependencyError

REQUIREMENTS: Final = ("starlette>=1.10,<2", "uvicorn>=0.54,<1")
"""Requirements of the extra; ``pyproject.toml`` says the same."""
INSTALL_HINT: Final = 'pip install "hydrolog[gui]"'
"""Command that installs the extra, as shown in the ``missing_dependency`` error."""
_MODULES: Final = ("starlette", "uvicorn")


def require_gui_extra() -> None:
    """Raise :class:`MissingDependencyError` unless Starlette and uvicorn import.

    Raises
    ------
    MissingDependencyError
        If a package of the ``gui`` extra is missing; ``hint`` says how to install it.
    """
    for module in _MODULES:
        try:
            importlib.import_module(module)
        except ImportError as exc:
            raise MissingDependencyError(
                f"The GUI needs the 'gui' extra ({', '.join(REQUIREMENTS)}): "
                f"cannot import {module!r} ({exc})",
                hint=INSTALL_HINT,
                details={"extra": "gui", "module": module},
            ) from exc
