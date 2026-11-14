"""The file of the reports of „Zgłoś uwagę” (``hydrolog.gui._feedback``).

The first report makes the file, private to its owner; reading makes nothing; two
writers on one file lose nothing; a file that cannot be used fails without its path;
the table itself refuses what the limits refuse. A file of version 1 (the form with a
contact, the page's address, the browser and diagnostics) is copied whole beside it and
moved to version 2, which keeps the reports and drops everything else from the file.
"""

import json
import logging
import os
import re
import sqlite3
import sys
import threading
from contextlib import closing

import pytest

from hydrolog.exceptions import HydrologError
from hydrolog.gui._feedback import FeedbackStore, Report

CONTEXT: dict[str, object] = {
    "view": "hydrogram",
    "station": None,
    "parameters": {},
    "app_version": "1",
}

V1_SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(message) BETWEEN 1 AND 5000),
    contact TEXT CHECK (length(contact) <= 200),
    page_url TEXT CHECK (length(page_url) <= 500),
    user_agent TEXT CHECK (length(user_agent) <= 500),
    diagnostics TEXT CHECK (
        json_valid(diagnostics)
        AND length(CAST(diagnostics AS BLOB)) <= 100000
    ),
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback (created_at DESC);
PRAGMA user_version = 1;
"""
"""The schema of a file of version 1, as the previous Hydrolog made it."""
V1_COLUMNS = (
    "id",
    "created_at",
    "message",
    "contact",
    "page_url",
    "user_agent",
    "diagnostics",
    "is_read",
)
CONTACT = "jan.kowalski.migracja@example.com"
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) StaraPrzegladarka/7.7"
V1_ROWS = [
    (
        1,
        "2026-10-01T08:00:00Z",
        "Qmax wygląda dziwnie",
        CONTACT,
        "http://x/#statystyka",
        BROWSER,
        json.dumps(
            {
                "workspace": {
                    "section": "hydrogram",
                    "path": ["scs", "jednostkowy"],
                    "inputs": {"area_km2": 12.5, "cn": 72},
                },
                "env": {"viewport": {"width": 1440, "height": 900}},
            }
        ),
        1,
    ),
    (
        2,
        "2026-10-02T09:30:00Z",
        "Brak stacji",
        CONTACT,
        "http://x/#statystyka",
        BROWSER,
        None,
        0,
    ),
    (4, "2026-10-03T10:45:00Z", "Bez niczego", None, None, None, None, 0),
]
"""Reports of version 1: id 3 was deleted before the move."""


def make(message="x", context=None):
    return Report(message=message, context=json.dumps(context or CONTEXT))


@pytest.fixture
def path(tmp_path):
    return tmp_path / "data" / "hydrolog" / "feedback.sqlite3"


def checkpoint(path):
    """Move the write-ahead log into the file and empty it; return the file's bytes."""
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    return b"".join(
        (path.parent / name).read_bytes()
        for name in os.listdir(path.parent)
        if name.startswith(path.name)
    )


def write_v1(path):
    """Write a file of version 1 with ``V1_ROWS``, in WAL mode as it was served."""
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(V1_SCHEMA)
        marks = ", ".join("?" * len(V1_COLUMNS))
        db.executemany(
            f"INSERT INTO feedback ({', '.join(V1_COLUMNS)}) VALUES ({marks})", V1_ROWS
        )


def test_reading_an_absent_file_makes_nothing(path):
    store = FeedbackStore(path)

    assert store.listing(limit=50, offset=0) == {
        "items": [],
        "total": 0,
        "unread_count": 0,
    }
    assert store.set_read(1, is_read=True) is None
    assert store.delete(1) is False
    assert not path.parent.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_the_first_report_makes_a_private_directory_and_file(path):
    assert FeedbackStore(path).add(make()) == 1

    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert path.stat().st_mode & 0o777 == 0o600


def test_the_file_is_in_wal_mode_with_the_schema_version(path):
    FeedbackStore(path).add(make())

    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2


def test_a_report_is_listed_with_its_context_as_an_object(path):
    context = {
        "view": "statystyka/przeplywy",
        "station": "Kamiennik — Świerzawa",
        "parameters": {"area_km2": 12.5, "methods": ["scs"]},
        "app_version": "1.0.0",
    }
    store = FeedbackStore(path)

    store.add(make("Qmax wygląda dziwnie", context))

    [item] = store.listing(limit=50, offset=0)["items"]
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", item.pop("created_at"))
    assert item == {
        "id": 1,
        "message": "Qmax wygląda dziwnie",
        "context": context,
        "is_read": False,
    }


def test_two_writers_on_one_file_lose_no_report(path):
    """Two stores stand for two processes on one data directory."""
    stores = [FeedbackStore(path), FeedbackStore(path)]
    stores[0].add(make("pierwsze"))
    numbers = []

    def write(store):
        for index in range(25):
            numbers.append(store.add(make(f"zgłoszenie {index}")))

    threads = [threading.Thread(target=write, args=(stores[i % 2],)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(numbers) == list(range(2, 102))
    assert stores[1].listing(limit=1, offset=0)["total"] == 101


def test_a_file_removed_while_serving_is_made_again(path):
    store = FeedbackStore(path)
    store.add(make())
    for name in os.listdir(path.parent):
        os.remove(path.parent / name)

    store.add(make("po usunięciu"))

    assert store.listing(limit=50, offset=0)["items"][0]["message"] == "po usunięciu"


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda store: store.add(make()), "feedback_store_failed"),
        (lambda store: store.listing(limit=50, offset=0), "feedback_list_failed"),
        (lambda store: store.set_read(1, is_read=True), "feedback_update_failed"),
        (lambda store: store.delete(1), "feedback_delete_failed"),
    ],
)
def test_a_file_that_is_not_a_database_fails_without_its_path(path, call, reason):
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not a database, " * 100)

    with pytest.raises(HydrologError) as caught:
        call(FeedbackStore(path))

    assert caught.value.code == "io_error"
    assert caught.value.details == {"reason": reason}
    assert str(path) not in str(caught.value)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("message", ""),
        ("message", "x" * 5001),
        ("context", None),
        ("context", "{not json"),
        ("context", "[1]"),
        # An id of its own: pytest puts the test's id into an environment variable,
        # which Windows limits to 32 767 characters
        pytest.param("context", '{"a":"' + "d" * 99_993 + '"}', id="context-too_large"),
        ("is_read", 2),
    ],
)
def test_the_table_refuses_what_the_limits_refuse(path, column, value):
    """Another writer of the file (sqlite3 by hand) meets the same limits."""
    FeedbackStore(path).add(make())
    row = {"created_at": "2026-11-03T10:15:00Z", "message": "x", "context": "{}"}
    statement = "INSERT INTO feedback ({}) VALUES ({})"

    with closing(sqlite3.connect(path)) as db:
        db.execute(
            statement.format(", ".join(row), ", ".join("?" * len(row))),
            (*row.values(),),
        )
        row[column] = value
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                statement.format(", ".join(row), ", ".join("?" * len(row))),
                (*row.values(),),
            )


def test_a_file_has_no_column_for_a_contact_an_address_or_a_browser(path):
    FeedbackStore(path).add(make())

    with closing(sqlite3.connect(path)) as db:
        columns = [row[1] for row in db.execute("PRAGMA table_info(feedback)")]

    assert columns == ["id", "created_at", "message", "context", "is_read"]


# --- a file of version 1 --------------------------------------------------------------


def test_a_file_of_version_1_is_moved_to_version_2_keeping_its_reports(path):
    write_v1(path)
    store = FeedbackStore(path)

    page = store.listing(limit=50, offset=0)

    assert page["items"] == [
        {
            "id": 4,
            "created_at": "2026-10-03T10:45:00Z",
            "message": "Bez niczego",
            "context": {
                "view": "",
                "station": None,
                "parameters": {},
                "app_version": None,
            },
            "is_read": False,
        },
        {
            "id": 2,
            "created_at": "2026-10-02T09:30:00Z",
            "message": "Brak stacji",
            "context": {  # no diagnostics: the view is the address's fragment
                "view": "statystyka",
                "station": None,
                "parameters": {},
                "app_version": None,
            },
            "is_read": False,
        },
        {
            "id": 1,
            "created_at": "2026-10-01T08:00:00Z",
            "message": "Qmax wygląda dziwnie",
            "context": {  # the diagnostics' section and route win over the address
                "view": "hydrogram/scs/jednostkowy",
                "station": None,
                "parameters": {"area_km2": 12.5, "cn": 72},
                "app_version": None,
            },
            "is_read": True,
        },
    ]
    assert (page["total"], page["unread_count"]) == (3, 2)
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        columns = [row[1] for row in db.execute("PRAGMA table_info(feedback)")]
    assert columns == ["id", "created_at", "message", "context", "is_read"]


def test_a_file_of_version_1_is_copied_whole_beside_it_before_the_move(path):
    write_v1(path)

    FeedbackStore(path).listing(limit=50, offset=0)

    [copy] = [p for p in path.parent.iterdir() if p.name.startswith("feedback-v1-")]
    assert re.fullmatch(r"feedback-v1-\d{8}T\d{6}Z\.sqlite3", copy.name)
    if sys.platform != "win32":
        assert copy.stat().st_mode & 0o777 == 0o600
    with closing(sqlite3.connect(copy)) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        rows = db.execute(
            f"SELECT {', '.join(V1_COLUMNS)} FROM feedback ORDER BY id"
        ).fetchall()
    assert rows == V1_ROWS


def test_the_moved_file_keeps_no_contact_address_or_browser(path):
    """``VACUUM``: no page of the old table stays in the live file."""
    write_v1(path)
    assert CONTACT.encode() in checkpoint(path)  # the test sees text when it is there

    FeedbackStore(path).listing(limit=50, offset=0)

    content = checkpoint(path)
    for text in (CONTACT, BROWSER, "http://x/", "viewport"):
        assert text.encode() not in content, text


def test_the_move_is_logged_with_the_name_of_the_copy(path, caplog):
    write_v1(path)

    with caplog.at_level(logging.WARNING, logger="hydrolog.gui._feedback"):
        FeedbackStore(path).listing(limit=50, offset=0)

    [copy] = [
        p.name for p in path.parent.iterdir() if p.name.startswith("feedback-v1-")
    ]
    [record] = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert copy in record.getMessage()


def test_after_the_move_no_id_is_given_twice_and_no_second_copy_is_made(path):
    """An id given in version 1, even of a report deleted since, is never given
    again (``AUTOINCREMENT``), so an id names one report for good."""
    write_v1(path)
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        for number in (5, 6, 7):
            db.execute(
                "INSERT INTO feedback (id, created_at, message) VALUES (?, ?, ?)",
                (number, "2026-10-04T00:00:00Z", "usunięte"),
            )
        db.execute("DELETE FROM feedback WHERE id > 4")
    FeedbackStore(path).listing(limit=50, offset=0)

    store = FeedbackStore(path)  # a restart: the file is of version 2 now
    number = store.add(make("po przeniesieniu"))

    assert number == 8
    assert store.listing(limit=50, offset=0)["total"] == 4
    copies = [p for p in path.parent.iterdir() if p.name.startswith("feedback-v1-")]
    assert len(copies) == 1
