"""Hydrolog's web GUI: a page and its server, alone or hosted by Nogat (extra ``gui``).

Plan 2026-11-02 (``docs/plans/2026-11-02-hydrolog-gui.md``). The page (``web/``, Preact
modules without a build) computes nothing: every hydrological value comes from the
catalog through the private API of the server (:func:`create_app`), which runs
:func:`~hydrolog.catalog.run_command` in warm worker processes, one work directory per
browser session.

* :func:`serve` -- the standalone server (``hydrolog gui serve``, ``127.0.0.1:8070``
  by default); it blocks until Ctrl+C or ``SIGTERM``.
* :func:`create_app` -- the ASGI app; a host mounts it at a prefix of its origin.
* :func:`gui_module` -- the description of the module that Nogat's GUI platform finds
  through the entry point group ``nogat.gui``.

Importing this package does not import Starlette or uvicorn; :func:`create_app` and
:func:`serve` raise :class:`~hydrolog.exceptions.MissingDependencyError`
(``pip install "hydrolog[gui]"``) when the extra is missing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from hydrolog.gui._extra import require_gui_extra
from hydrolog.gui.server import serve

if TYPE_CHECKING:
    from starlette.applications import Starlette

__all__ = ["SECTIONS", "WEB_DIR", "GuiModule", "create_app", "gui_module", "serve"]

WEB_DIR: Final = Path(__file__).resolve().parent / "web"
"""The page's directory (package data ``gui/web/**``)."""
SECTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("hydrogram", "Hydrogram zlewni"),
    ("siec", "Sieć i trasowanie"),
    ("statystyka", "Statystyka przepływów"),
    ("kalkulatory", "Kalkulatory"),
    ("polecenia", "Wszystkie polecenia"),
)
"""The sections of the page: the id of its address (``#hydrogram``) and its title."""


@dataclass(frozen=True)
class GuiModule:
    """A GUI module as Nogat's GUI platform hosts it (plan D4; a proposal to Nogat).

    Attributes
    ----------
    name : str
        Id of the module (``"hydrolog"``).
    title : str
        Title shown by the host.
    web : Path
        Directory of the page's static files.
    index : str
        The page, relative to ``web``.
    sections : tuple of (str, str)
        The sections: the fragment of the address and the Polish title.
    app : callable
        :func:`create_app`: ``app(work_root=...)`` returns the ASGI app that serves
        ``web`` and answers ``api/...`` relative to the page, at any prefix
        (``data_dir=`` places the reports of „Zgłoś uwagę”).
    """

    name: str
    title: str
    web: Path
    index: str
    sections: tuple[tuple[str, str], ...]
    app: Callable[..., Starlette]


def create_app(
    *,
    work_root: Path | None = None,
    workers: int = 2,
    run_timeout_s: float = 30.0,
    data_dir: Path | None = None,
) -> Starlette:
    """Create the ASGI app of the GUI: the page and the private API of plan D5.

    The worker processes start with the app's lifespan, or with the first run when a
    host does not run the lifespan of a mounted app; they and the session
    directories end with the lifespan, or when the app is collected or the
    interpreter exits.

    Parameters
    ----------
    work_root : Path, optional
        Directory for the session directories; ``None`` (default) creates one in
        the system's temporary directory and removes it at the end.
    workers : int, optional
        Number of worker processes (at least 1).
    run_timeout_s : float, optional
        Longest run [s]; a longer one kills its worker and ends ``cancelled``.
    data_dir : Path, optional
        The shared data directory (DEV-18.2): the reports of „Zgłoś uwagę” go to
        ``<data_dir>/hydrolog/feedback.sqlite3``, created by the first report;
        ``None`` (default) takes the setting ``data_dir`` (``HYDROLOG_DATA_DIR``,
        ``NOGAT_DATA_DIR``, ``nogat.toml``, else the user data directory of
        ``nogat``). The admin routes answer only the key of
        ``HYDROLOG_ADMIN_API_KEY`` or ``HYDROLOG_ADMIN_API_KEY_FILE``, read on every
        request.

    Returns
    -------
    starlette.applications.Starlette
        The app: the page at its root, the API under ``api/``.

    Raises
    ------
    MissingDependencyError
        If the ``gui`` extra (Starlette, uvicorn) is not installed.
    InvalidParameterError
        If ``workers`` is below 1 or ``run_timeout_s`` is not positive.
    """
    from hydrolog.exceptions import InvalidParameterError

    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise InvalidParameterError(
            f"workers must be an integer >= 1, got {workers!r}",
            details={"option": "workers", "reason": "minimum", "minimum": 1},
        )
    if not run_timeout_s > 0:
        raise InvalidParameterError(
            f"run_timeout_s must be > 0, got {run_timeout_s!r}",
            details={
                "option": "run_timeout_s",
                "reason": "exclusive_minimum",
                "exclusive_minimum": 0,
            },
        )
    require_gui_extra()
    from hydrolog._settings import resolve_setting
    from hydrolog.gui._app import build_app

    if data_dir is None:
        data_dir = Path(resolve_setting("data_dir").value)
    return build_app(
        work_root=work_root,
        workers=workers,
        run_timeout_s=run_timeout_s,
        data_dir=Path(data_dir),
    )


def gui_module() -> GuiModule:
    """Describe the GUI for Nogat's GUI platform (entry point ``nogat.gui``).

    Returns
    -------
    GuiModule
        ``name="hydrolog"``, ``title="Hydrolog"``, the page's directory and
        ``index.html``, the five sections and :func:`create_app`.
    """
    return GuiModule(
        name="hydrolog",
        title="Hydrolog",
        web=WEB_DIR,
        index="index.html",
        sections=SECTIONS,
        app=create_app,
    )
