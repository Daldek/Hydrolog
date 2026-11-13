"""Fixtures of the GUI server's tests: a page directory, apps and clients.

The page of the package (``src/hydrolog/gui/web``) belongs to the frontend; these
tests serve a small page of their own (with a stylesheet of the kit and an admin
page), so they test the server alone. Clients do not run the lifespan: the workers
start with the first run, as in a host that mounts the app without running its
lifespan, and the fixtures stop them. A client keeps its session as the page does:
it sends back the ``X-Hydrolog-Session`` that an answer gives.

Starlette is imported inside the fixtures: without the ``gui`` extra the test modules
skip themselves (``pytest.importorskip``).
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PAGE = "<!doctype html><title>Hydrolog</title><script type=module src=src/main.js>"
MAIN_JS = 'import "./app.js";\n'
ADMIN = "<!doctype html><title>Zgłoszenia</title>"
TOKENS = ":root { --nogat-space: 4px; }\n"
SESSION_HEADER = "X-Hydrolog-Session"


@pytest.fixture(scope="package")
def web(tmp_path_factory):
    """Serve a small page of the tests instead of the package's ``web/``."""
    from hydrolog.gui import _app

    directory = tmp_path_factory.mktemp("web")
    (directory / "index.html").write_text(PAGE, encoding="utf-8")
    (directory / "src").mkdir()
    (directory / "src" / "main.js").write_text(MAIN_JS, encoding="utf-8")
    (directory / "admin").mkdir()
    (directory / "admin" / "index.html").write_text(ADMIN, encoding="utf-8")
    (directory / "nogat").mkdir()
    (directory / "nogat" / "tokens.css").write_text(TOKENS, encoding="utf-8")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(_app, "WEB_DIR", directory)
        yield directory


@pytest.fixture(scope="package")
def app(web, tmp_path_factory):
    """Yield one app (two workers) for the tests of the package; reports go to a
    data directory of the tests."""
    from hydrolog.gui import create_app

    created = create_app(
        work_root=tmp_path_factory.mktemp("work"),
        data_dir=tmp_path_factory.mktemp("data"),
    )
    yield created
    created.state.gui.close()


@pytest.fixture
def page_client():
    """Return ``page_client(app, **options)``: a TestClient that keeps its session as
    the page does, sending back the ``X-Hydrolog-Session`` an answer gives."""
    from starlette.testclient import TestClient

    def make(app, **options):
        made = TestClient(app, **options)

        def adopt(response):
            session = response.headers.get(SESSION_HEADER)
            if session:
                made.headers[SESSION_HEADER] = session

        made.event_hooks["response"].append(adopt)
        return made

    return make


@pytest.fixture
def client(app, page_client):
    """Return a client of ``app`` that has no session yet and keeps the one it gets."""
    return page_client(app)


@pytest.fixture
def slow_app(web, monkeypatch, tmp_path):
    """Yield ``slow_app(workers=1, run_timeout_s=30)``: apps whose ``tc kirpich``
    sleeps ``length_km`` seconds (``tests.integration.gui._slow_worker``)."""
    from hydrolog.gui import create_app

    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    monkeypatch.setattr(
        "hydrolog.gui._runner.WORKER_MODULE", "tests.integration.gui._slow_worker"
    )
    made = []

    def make(*, workers=1, run_timeout_s=30.0):
        created = create_app(
            work_root=tmp_path / f"work{len(made)}",
            workers=workers,
            run_timeout_s=run_timeout_s,
        )
        made.append(created)
        return created

    yield make
    for created in made:
        created.state.gui.close()
