"""The rules of a public GUI: what is counted, the request limit, the daily totals.

Nogat DEV-15.9 (a window per client address, static files not counted, ``Retry-After``
in whole seconds, the address in memory for its window only) and DEV-15.11 (visitors as
salted hashes of the address and the User-Agent, one line per UTC day of
``stats.jsonl`` in date order, added to after a restart).
"""

import json
import stat
import sys
from datetime import UTC, datetime, timedelta, timezone

import pytest

pytest.importorskip("starlette")

from hydrolog.gui._public import (
    FLUSH_S,
    STATS_KEYS,
    DailyStats,
    RateLimiter,
    is_admin,
    is_counted,
    is_page,
)

posix_modes = pytest.mark.skipif(
    sys.platform == "win32", reason="Windows has no POSIX file modes"
)
TOTALS = ("page_views", "stations_opened", "analyses_run", "downloads")


class Clock:
    """A clock the test moves: monotonic seconds or an aware time."""

    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


def line(date, visitors=0, **totals):
    """Return a line of ``stats.jsonl``: every total, 0 unless given."""
    return {"date": date, "visitors": visitors, **dict.fromkeys(TOTALS, 0), **totals}


def read_lines(path):
    return [json.loads(text) for text in path.read_text(encoding="utf-8").splitlines()]


# --- what is counted ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "route", "counted", "page"),
    [
        ("GET", "/", True, True),
        ("HEAD", "/", True, True),
        ("GET", "/index.html", True, True),
        ("GET", "/regulamin.html", True, True),
        ("GET", "/instrukcja/", True, True),
        ("GET", "/instrukcja", True, True),
        ("GET", "/admin/", True, False),
        ("GET", "/admin", True, False),
        ("GET", "/admin/index.html", True, False),
        ("POST", "/", True, False),
        ("GET", "/src/main.js", False, False),
        ("GET", "/nogat/tokens.css", False, False),
        ("GET", "/instrukcja/img/start.png", False, False),
        ("GET", "/favicon.ico", False, False),
        ("GET", "/api/session", True, False),
        ("DELETE", "/api/session", True, False),
        ("POST", "/api/run/tc/kirpich", True, False),
        ("GET", "/api/files/out/wynik.csv", True, False),
        ("POST", "/api/stats/station", True, False),
        ("GET", "/api/commands", False, False),
        ("HEAD", "/api/commands", False, False),
        ("GET", "/api/commands/uh/nash", False, False),
        ("GET", "/api/schemas/hydrolog-network-1.schema.json", False, False),
        ("POST", "/api/commands", True, False),
    ],
)
def test_what_the_limit_counts_and_what_is_a_page_view(method, route, counted, page):
    """Static files and reads of the catalog are not counted (DEV-15.9); a page view
    is a read of a public page, not of the admin page or the API."""
    assert is_counted(method, route) is counted
    assert is_page(method, route) is page


@pytest.mark.parametrize(
    ("route", "admin"),
    [
        ("/admin", True),
        ("/admin/", True),
        ("/admin/index.html", True),
        ("/api/admin/feedback/3", True),
        ("/api/admin/stats", True),
        ("/administracja", False),
        ("/api/administracja", False),
        ("/api/feedback", False),
        ("/instrukcja/admin/", False),
    ],
)
def test_the_admin_panel_is_its_three_paths(route, admin):
    """``/admin``, ``/admin/…`` and ``/api/admin/…`` (DEV-15.13), which no total
    counts (DEV-15.11)."""
    assert is_admin(route) is admin


# --- the request limit ----------------------------------------------------------------


def test_the_limit_refuses_the_request_after_the_last_allowed_one():
    limiter = RateLimiter(3, 60, clock=Clock(100.0))

    assert [limiter.hit("a") for _ in range(3)] == [None, None, None]
    assert limiter.hit("a") == 60
    assert limiter.hit("a") == 60


@pytest.mark.parametrize(
    ("elapsed", "retry_after"),
    [(0.0, 60), (0.4, 60), (10.2, 50), (59.0, 1), (59.5, 1), (59.999, 1)],
)
def test_retry_after_is_the_rest_of_the_window_in_whole_seconds(elapsed, retry_after):
    """Rounded up, at least 1 s: a client that waits that long is answered."""
    clock = Clock(100.0)
    limiter = RateLimiter(1, 60, clock=clock)
    limiter.hit("a")
    clock.now += elapsed

    assert limiter.hit("a") == retry_after


def test_each_address_has_a_window_of_its_own():
    clock = Clock(0.0)
    limiter = RateLimiter(2, 60, clock=clock)
    limiter.hit("a")
    limiter.hit("a")
    clock.now = 30.0

    assert limiter.hit("a") == 30
    assert [limiter.hit("b"), limiter.hit("b"), limiter.hit("b")] == [
        None,
        None,
        30 + 30,
    ]


def test_a_new_window_starts_when_the_old_one_ends():
    """Refused requests do not extend the window."""
    clock = Clock(0.0)
    limiter = RateLimiter(2, 60, clock=clock)
    limiter.hit("a")
    limiter.hit("a")
    clock.now = 59.9
    assert limiter.hit("a") == 1

    clock.now = 60.0
    assert [limiter.hit("a"), limiter.hit("a"), limiter.hit("a")] == [None, None, 60]


def test_addresses_are_forgotten_as_their_windows_end():
    """An address stays in memory for its window only (DEV-15.9)."""
    clock = Clock(0.0)
    limiter = RateLimiter(5, 60, clock=clock)
    limiter.hit("a")
    clock.now = 30.0
    limiter.hit("b")
    limiter.hit("a")
    assert len(limiter) == 2

    clock.now = 60.0
    limiter.purge()
    assert len(limiter) == 1

    clock.now = 90.0
    limiter.purge()
    assert len(limiter) == 0


def test_a_hit_forgets_the_ended_windows_of_other_addresses():
    clock = Clock(0.0)
    limiter = RateLimiter(5, 60, clock=clock)
    for address in ("a", "b", "c"):
        limiter.hit(address)
    clock.now = 61.0

    limiter.hit("d")

    assert len(limiter) == 1


# --- the daily totals -----------------------------------------------------------------


@pytest.fixture
def clock():
    return Clock(datetime(2026, 11, 13, 12, 0, tzinfo=UTC))


@pytest.fixture
def path(tmp_path):
    return tmp_path / "hydrolog" / "stats.jsonl"


def test_a_visitor_is_an_address_with_a_user_agent_counted_once_a_day(path, clock):
    stats = DailyStats(path, clock)

    stats.visit("203.0.113.7", "Firefox")
    stats.visit("203.0.113.7", "Firefox")
    stats.visit("203.0.113.7", "Chrome")
    stats.visit("198.51.100.2", "Firefox")
    stats.visit("198.51.100.2", "Firefox")

    assert stats.snapshot()["visitors"] == 3


def test_the_totals_are_one_line_in_the_order_of_the_standard(path, clock):
    stats = DailyStats(path, clock)
    stats.visit("203.0.113.7", "Firefox")
    for key in ("page_views", "page_views", "analyses_run", "downloads"):
        stats.count(key)

    stats.flush()

    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n") and text.count("\n") == 1
    document = json.loads(text)
    assert list(document) == ["date", *STATS_KEYS]
    assert document == line("2026-11-13", 1, page_views=2, analyses_run=1, downloads=1)
    assert "203.0.113.7" not in text and "Firefox" not in text


@pytest.mark.parametrize("key", ["visitors", "page_view", "date", ""])
def test_only_the_totals_other_than_visitors_can_be_counted(path, clock, key):
    stats = DailyStats(path, clock)

    with pytest.raises(KeyError):
        stats.count(key)
    assert stats.snapshot() == line("2026-11-13")


def test_nothing_is_written_while_nothing_was_counted(path, clock):
    DailyStats(path, clock).flush()

    assert not path.exists()


def test_a_new_utc_day_starts_at_midnight_with_a_new_salt(path, clock):
    """The same visitor is counted again the next day; the old day's line is final,
    both days are written, in date order."""
    clock.now = datetime(2026, 11, 13, 23, 59, 59, tzinfo=UTC)
    stats = DailyStats(path, clock)
    stats.visit("203.0.113.7", "Firefox")
    stats.count("page_views")

    clock.now = datetime(2026, 11, 14, 0, 0, 1, tzinfo=UTC)
    stats.visit("203.0.113.7", "Firefox")
    stats.flush()

    assert read_lines(path) == [
        line("2026-11-13", 1, page_views=1),
        line("2026-11-14", 1),
    ]
    assert stats.snapshot() == line("2026-11-14", 1)


def test_the_day_is_the_utc_day_whatever_the_clocks_zone(path, clock):
    warsaw = timezone(timedelta(hours=1))
    clock.now = datetime(2026, 11, 14, 0, 30, tzinfo=warsaw)  # 23:30 UTC, the 13th

    assert DailyStats(path, clock).snapshot()["date"] == "2026-11-13"


def test_the_lines_of_other_days_are_kept_in_date_order(path, clock):
    path.parent.mkdir()
    path.write_text(
        json.dumps(line("2026-11-15", 2)) + "\n" + json.dumps(line("2026-11-10", 7)),
        encoding="utf-8",
    )
    stats = DailyStats(path, clock)
    stats.count("downloads")

    stats.flush()

    assert [entry["date"] for entry in read_lines(path)] == [
        "2026-11-10",
        "2026-11-13",
        "2026-11-15",
    ]
    assert read_lines(path)[0] == line("2026-11-10", 7)


def test_a_restart_adds_to_the_days_stored_line(path, clock):
    first = DailyStats(path, clock)
    first.visit("203.0.113.7", "Firefox")
    for key in TOTALS:
        first.count(key)
    first.flush()

    second = DailyStats(path, clock)
    second.visit("203.0.113.7", "Firefox")  # a new salt: a new visitor
    second.count("page_views")
    second.flush()

    assert read_lines(path) == [
        line(
            "2026-11-13",
            2,
            page_views=2,
            stations_opened=1,
            analyses_run=1,
            downloads=1,
        )
    ]


def test_unusable_lines_of_the_file_are_skipped(path, clock):
    path.parent.mkdir()
    stored = line("2026-11-12", 4, page_views=9)
    path.write_text(
        "\n".join(
            [
                "not json",
                "[1, 2]",
                '{"date": 5, "visitors": 1}',
                "",
                json.dumps(stored),
                (
                    '{"date": "2026-11-13", "visitors": "many", "page_views": true,'
                    ' "downloads": 3}'
                ),
                "{",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stats = DailyStats(path, clock)
    stats.count("page_views")

    stats.flush()

    assert read_lines(path) == [stored, line("2026-11-13", page_views=1, downloads=3)]


def test_a_file_that_is_not_utf8_is_no_stored_totals(path, clock):
    path.parent.mkdir()
    path.write_bytes(b"\xff\xfe{")
    stats = DailyStats(path, clock)
    stats.count("downloads")

    stats.flush()

    assert read_lines(path) == [line("2026-11-13", downloads=1)]


@posix_modes
def test_the_file_is_private_and_replaced_whole(path, clock):
    stats = DailyStats(path, clock)
    stats.count("page_views")
    stats.flush()
    stats.count("page_views")
    stats.flush()

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert [entry.name for entry in path.parent.iterdir()] == ["stats.jsonl"]
    assert read_lines(path) == [line("2026-11-13", page_views=2)]


def test_a_failed_write_keeps_the_totals_for_the_next_try(tmp_path, clock, caplog):
    blocker = tmp_path / "hydrolog"
    blocker.write_text("a file where the directory should be", encoding="utf-8")
    path = blocker / "stats.jsonl"
    stats = DailyStats(path, clock)
    stats.count("downloads")

    stats.flush()

    assert "could not be written" in caplog.text
    blocker.unlink()
    stats.flush()
    assert read_lines(path) == [line("2026-11-13", downloads=1)]


def test_a_flush_is_due_after_five_minutes_of_changes(path, clock):
    stats = DailyStats(path, clock)
    assert not stats.due(0.0, 10 * FLUSH_S)  # nothing changed

    stats.count("page_views")
    assert not stats.due(0.0, FLUSH_S - 0.1)
    assert stats.due(0.0, FLUSH_S)

    stats.flush()
    assert not stats.due(0.0, 10 * FLUSH_S)


def test_a_flush_is_due_ten_seconds_after_the_last_one_when_a_day_ends(path, clock):
    stats = DailyStats(path, clock)
    clock.now += timedelta(days=1)

    assert not stats.due(100.0, 109.9)
    assert stats.due(100.0, 110.0)

    stats.flush()
    assert not stats.due(100.0, 110.0)
