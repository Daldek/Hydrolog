"""The admin panel's page, statistics and status (Nogat DEV-15.13) through TestClient.

``admin`` answers ``308`` to ``admin/``; no answer of the panel, its page or its API, is
stored. ``api/admin/stats`` gives the days of ``stats.jsonl`` in a period of UTC days
(by default the last 30) and their totals; ``api/admin/status`` gives the server, its
disk and the checks ``data_dir`` and ``feedback_db``. The refusals of a missing, wrong
or unconfigured key are in ``test_feedback.py``, for every admin route.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("starlette")

from starlette.testclient import TestClient

import hydrolog
from hydrolog.gui import create_app
from tests.contract._nogat import validator

KEY = "klucz-administratora-0123"
ERROR = validator("error-1")
STATS = "/api/admin/stats"
STATUS = "/api/admin/status"
KEYS = ["visitors", "page_views", "stations_opened", "analyses_run", "downloads"]


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def make_app(web, tmp_path):
    """Yield ``make_app(data_dir)``: apps that are not public, closed at the end."""
    made = []

    def make(data_dir):
        created = create_app(work_root=tmp_path / f"work{len(made)}", data_dir=data_dir)
        made.append(created)
        return created

    yield make
    for created in made:
        created.state.gui.close()


@pytest.fixture
def client(make_app, data_dir, monkeypatch):
    """A client of an app with the admin key, which it sends."""
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", KEY)
    return TestClient(make_app(data_dir), headers={"X-Admin-Key": KEY})


def day(offset):
    """Return the UTC day ``offset`` days from today, ``YYYY-MM-DD``."""
    return (datetime.now(UTC).date() + timedelta(days=offset)).isoformat()


def line(date, *values):
    return {"date": date, **dict(zip(KEYS, values, strict=True))}


def write_stats(data_dir, *entries):
    path = data_dir / "hydrolog" / "stats.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        entry if isinstance(entry, str) else json.dumps(entry) + "\n"
        for entry in entries
    )
    path.write_text(text, encoding="utf-8")


def error(response, status, code, reason):
    document = response.json()
    assert response.status_code == status, document
    ERROR.validate(document)
    assert (document["code"], document["details"]["reason"]) == (code, reason)
    return document


# --- the page -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "target"), [("/admin", "admin/"), ("/admin?x=1", "admin/?x=1")]
)
def test_the_admin_path_without_its_slash_answers_308_to_the_page(
    make_app, data_dir, path, target
):
    client = TestClient(make_app(data_dir), follow_redirects=False)

    response = client.get(path)

    assert (response.status_code, response.headers["location"]) == (308, target)
    assert response.headers["cache-control"] == "no-store"


def test_under_a_hosts_prefix_the_308_leads_to_the_page_under_it(make_app, data_dir):
    from starlette.applications import Starlette
    from starlette.routing import Mount

    host = Starlette(routes=[Mount("/hydrolog", app=make_app(data_dir))])

    response = TestClient(host).get("/hydrolog/admin")

    assert response.status_code == 200
    assert str(response.url).endswith("/hydrolog/admin/")


@pytest.mark.parametrize("path", ["/admin/", "/admin/index.html", "/api/admin/stats"])
def test_no_answer_of_the_panel_is_stored(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_the_apps_page_is_revalidated_not_refused_to_the_cache(client):
    assert client.get("/").headers["cache-control"] == "no-cache"


# --- the statistics -------------------------------------------------------------------


def test_the_stats_give_the_last_30_days_of_the_file_and_their_totals(client, data_dir):
    write_stats(
        data_dir,
        line(day(-30), 9, 9, 9, 9, 9),  # a day before the period
        line(day(-29), 2, 5, 1, 3, 0),
        "not json\n",
        line(day(-3), 4, 7, 0, 1, 2),
    )

    document = client.get(STATS).json()

    assert document == {
        "days": [line(day(-29), 2, 5, 1, 3, 0), line(day(-3), 4, 7, 0, 1, 2)],
        "totals": {
            "page_views": 12,
            "stations_opened": 1,
            "analyses_run": 4,
            "downloads": 2,
        },
    }


def test_the_stats_take_both_days_of_the_period_and_a_missing_total_is_0(
    client, data_dir
):
    write_stats(
        data_dir,
        {"date": "2026-01-01", "visitors": 1, "page_views": True},
        line("2026-01-02", 1, 2, 3, 4, 5),
        line("2026-01-03", 1, 1, 1, 1, 1),
        {"date": "2026-1-2", "visitors": 7},  # not a day: left out
    )

    document = client.get(f"{STATS}?from=2026-01-01&to=2026-01-02").json()

    assert document["days"] == [
        line("2026-01-01", 1, 0, 0, 0, 0),
        line("2026-01-02", 1, 2, 3, 4, 5),
    ]
    assert document["totals"]["page_views"] == 2
    assert "visitors" not in document["totals"]


def test_a_period_ending_on_to_starts_29_days_before_it(client, data_dir):
    write_stats(data_dir, line("2026-01-01", *[1] * 5), line("2026-01-31", *[2] * 5))

    def dates(query):
        return [entry["date"] for entry in client.get(STATS + query).json()["days"]]

    assert dates("?to=2026-01-30") == ["2026-01-01"]
    assert dates("?to=2026-01-31") == ["2026-01-31"]
    assert dates("?from=2026-01-31&to=2026-01-31") == ["2026-01-31"]


def test_without_a_file_the_stats_have_no_days(client):
    assert client.get(STATS).json() == {
        "days": [],
        "totals": dict.fromkeys(KEYS[1:], 0),
    }


@pytest.mark.parametrize(
    ("query", "parameter", "reason"),
    [
        ("?from=2026-13-01", "from", "format"),
        ("?to=1.01.2026", "to", "format"),
        ("?from=2026-1-1", "from", "format"),
        ("?from=2026-02-02&to=2026-02-01", "from", "maximum"),
    ],
)
def test_the_days_of_the_stats_are_checked(client, query, parameter, reason):
    document = error(client.get(f"{STATS}{query}"), 400, "validation_error", reason)

    assert document["details"]["parameter"] == parameter


# --- the status -----------------------------------------------------------------------


def test_the_status_names_the_server_its_disk_and_its_checks(client, data_dir):
    document = client.get(STATUS).json()

    assert document["app"] == "Hydrolog"
    assert document["version"] == hydrolog.__version__
    started = datetime.strptime(document["started_at"], "%Y-%m-%dT%H:%M:%SZ")
    assert abs(datetime.now(UTC).replace(tzinfo=None) - started) < timedelta(minutes=1)
    assert isinstance(document["uptime_s"], int) and document["uptime_s"] >= 0
    assert document["data_dir"] == str(data_dir / "hydrolog")
    disk = document["disk"]
    assert 0 < disk["free_bytes"] <= disk["total_bytes"]
    assert [(c["name"], c["status"]) for c in document["checks"]] == [
        ("data_dir", "ok"),
        ("feedback_db", "ok"),
    ]
    assert not (data_dir / "hydrolog").exists()  # asking makes nothing


def test_the_status_counts_the_reports_and_leaves_no_probe(client, data_dir):
    for _ in range(2):
        client.post("/api/feedback", json={"message": "x", "context": {"view": "a"}})
    client.patch("/api/admin/feedback/1", json={"is_read": True})

    checks = client.get(STATUS).json()["checks"]

    assert checks[1] == {
        "name": "feedback_db",
        "status": "ok",
        "detail": "Zgłoszenia: 2, nieprzeczytane: 1.",
    }
    assert checks[0] == {
        "name": "data_dir",
        "status": "ok",
        "detail": "Katalog danych jest zapisywalny.",
    }
    probes = [p for p in (data_dir / "hydrolog").iterdir() if "check" in p.name]
    assert probes == []


def test_a_data_dir_that_cannot_be_written_and_a_broken_file_fail(
    make_app, tmp_path, monkeypatch
):
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", KEY)
    blocked = tmp_path / "plik"
    blocked.write_text("not a directory", encoding="utf-8")
    client = TestClient(make_app(blocked / "data"), headers={"X-Admin-Key": KEY})

    checks = client.get(STATUS).json()["checks"]

    assert [(c["name"], c["status"]) for c in checks] == [
        ("data_dir", "failed"),
        ("feedback_db", "ok"),
    ]

    data_dir = tmp_path / "data"
    (data_dir / "hydrolog").mkdir(parents=True)
    (data_dir / "hydrolog" / "feedback.sqlite3").write_bytes(b"not a database" * 100)
    client = TestClient(make_app(data_dir), headers={"X-Admin-Key": KEY})

    checks = client.get(STATUS).json()["checks"]

    assert [(c["name"], c["status"]) for c in checks] == [
        ("data_dir", "ok"),
        ("feedback_db", "failed"),
    ]
    assert str(data_dir) not in json.dumps(checks)
