"""The file of the reports of „Zgłoś uwagę” (``hydrolog.gui._feedback``).

The first report makes the file, private to its owner; reading makes nothing; two
writers on one file lose nothing; a file that cannot be used fails without its path;
the table itself refuses what the limits refuse.
"""

import os
import sqlite3
import sys
import threading
from contextlib import closing

import pytest

from hydrolog.exceptions import HydrologError
from hydrolog.gui._feedback import FeedbackStore, Report


def make(message="x", diagnostics=None):
    return Report(message=message, contact=None, page_url=None, diagnostics=diagnostics)


@pytest.fixture
def path(tmp_path):
    return tmp_path / "data" / "hydrolog" / "feedback.sqlite3"


def test_reading_an_absent_file_makes_nothing(path):
    store = FeedbackStore(path)

    assert store.listing(limit=50, offset=0) == {
        "items": [],
        "total": 0,
        "unread_count": 0,
    }
    assert store.set_read(1, is_read=True) is False
    assert store.delete(1) is False
    assert not path.parent.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_the_first_report_makes_a_private_directory_and_file(path):
    assert FeedbackStore(path).add(make(), user_agent="UA") == 1

    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert path.stat().st_mode & 0o777 == 0o600


def test_the_file_is_in_wal_mode_with_the_schema_version(path):
    FeedbackStore(path).add(make(), user_agent="UA")

    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1


def test_two_writers_on_one_file_lose_no_report(path):
    """Two stores stand for two processes on one data directory."""
    stores = [FeedbackStore(path), FeedbackStore(path)]
    stores[0].add(make("pierwsze"), user_agent="UA")
    numbers = []

    def write(store):
        for index in range(25):
            numbers.append(store.add(make(f"zgłoszenie {index}"), user_agent="UA"))

    threads = [threading.Thread(target=write, args=(stores[i % 2],)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(numbers) == list(range(2, 102))
    assert stores[1].listing(limit=1, offset=0)["total"] == 101


def test_a_file_removed_while_serving_is_made_again(path):
    store = FeedbackStore(path)
    store.add(make(), user_agent="UA")
    for name in os.listdir(path.parent):
        os.remove(path.parent / name)

    store.add(make("po usunięciu"), user_agent="UA")

    assert store.listing(limit=50, offset=0)["items"][0]["message"] == "po usunięciu"


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda store: store.add(make(), user_agent="UA"), "feedback_store_failed"),
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
        ("contact", "k" * 201),
        ("page_url", "u" * 501),
        ("user_agent", "a" * 501),
        ("diagnostics", "{not json"),
        # An id of its own: pytest puts the test's id into an environment variable,
        # which Windows limits to 32 767 characters
        pytest.param(
            "diagnostics", '{"a":"' + "d" * 99_993 + '"}', id="diagnostics-too_large"
        ),
        ("is_read", 2),
    ],
)
def test_the_table_refuses_what_the_limits_refuse(path, column, value):
    """Another writer of the file (sqlite3 by hand) meets the same limits."""
    FeedbackStore(path).add(make(), user_agent="UA")
    row = {"created_at": "2026-11-03T10:15:00Z", "message": "x", column: value}
    columns = ", ".join(row)
    marks = ", ".join("?" * len(row))

    with closing(sqlite3.connect(path)) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute(
            f"INSERT INTO feedback ({columns}) VALUES ({marks})", tuple(row.values())
        )
