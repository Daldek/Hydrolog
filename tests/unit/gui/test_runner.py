"""The runner of the GUI server: its queue, the newest run of a channel, timeouts.

The workers here are ``tests.unit.gui._fake_worker`` processes, which speak the
protocol of ``hydrolog.gui._worker`` and start in milliseconds; the tests of the app
(``tests/integration/gui``) run the real worker.
"""

import json
import os
import sys
import time
from pathlib import Path

import pytest

from hydrolog.gui._runner import Job, Runner

ROOT = Path(__file__).resolve().parents[3]
FAKE = "tests.unit.gui._fake_worker"
WAIT_S = 30.0


@pytest.fixture
def runner(monkeypatch, tmp_path):
    """Yield ``runner(workers=1, timeout_s=30)``: runners of fake workers."""
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    made: list[Runner] = []

    def make(*, workers=1, timeout_s=30.0):
        created = Runner(
            workers=workers, timeout_s=timeout_s, cwd=tmp_path, worker_module=FAKE
        )
        made.append(created)
        return created

    yield make
    for created in made:
        created.close()


def job(command, **options):
    return Job(command, options, "/nowhere")


def result(future):
    outcome = future.result(timeout=WAIT_S)
    assert not outcome.error, outcome.document
    return outcome.document


def ended(pid):
    """Tell whether the process ``pid`` has ended (POSIX; Windows is not asked:
    ``os.kill`` would terminate the process there)."""
    if sys.platform == "win32":
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def wait_until(condition):
    deadline = time.monotonic() + WAIT_S
    while not condition():
        assert time.monotonic() < deadline, "the condition did not come true"
        time.sleep(0.01)


def test_a_run_ends_with_the_document_of_its_worker(runner):
    document = result(runner().submit(job("echo", value=1.5)))

    assert document["status"] == "ok"
    assert document["result"]["options"] == {"value": 1.5}


def test_workers_get_one_thread_of_numerical_code(runner):
    document = result(runner().submit(job("echo")))

    assert document["result"]["environment"] == {
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }


def test_a_newer_run_of_a_channel_ends_its_queued_older_run(runner, tmp_path):
    running = runner()
    release = tmp_path / "release"
    busy = running.submit(job("wait", release=str(release)))
    older = running.submit(job("echo", n=1), channel=("session", "hydrogram"))

    newer = running.submit(job("echo", n=2), channel=("session", "hydrogram"))

    replaced = older.result(timeout=WAIT_S)
    assert replaced.document["status"] == "cancelled"
    assert replaced.document["result"] is None
    assert replaced.document["command"] == "echo"
    assert replaced.document["notices"] == [
        {
            "level": "info",
            "code": "superseded",
            "message": "A newer run of the same channel replaced this one.",
        }
    ]
    assert not newer.done()
    release.touch()
    assert result(busy)["status"] == "ok"
    assert result(newer)["result"]["options"] == {"n": 2}


def test_channels_are_separate(runner, tmp_path):
    running = runner()
    release = tmp_path / "release"
    busy = running.submit(job("wait", release=str(release)))
    first = running.submit(job("echo"), channel=("session", "hydrogram"))
    other_channel = running.submit(job("echo"), channel=("session", "siec"))
    other_session = running.submit(job("echo"), channel=("other", "hydrogram"))
    release.touch()

    for future in (busy, first, other_channel, other_session):
        assert result(future)["status"] == "ok"


def test_a_running_run_finishes_when_a_newer_one_of_its_channel_comes(runner, tmp_path):
    running = runner()
    release = tmp_path / "release"
    older = running.submit(
        job("wait", release=str(release)), channel=("session", "hydrogram")
    )
    wait_until(older.running)

    newer = running.submit(job("echo"), channel=("session", "hydrogram"))
    release.touch()

    assert result(older)["status"] == "ok"
    assert result(newer)["status"] == "ok"


def test_a_run_over_the_timeout_kills_its_worker_and_a_new_worker_takes_over(
    runner,
):
    running = runner(timeout_s=0.5)
    before = result(running.submit(job("echo")))["result"]["pid"]
    started = time.monotonic()

    stopped = running.submit(job("sleep", seconds=60)).result(timeout=WAIT_S)

    assert time.monotonic() - started < 10
    assert stopped.document["status"] == "cancelled"
    assert stopped.document["notices"] == [
        {
            "level": "warning",
            "code": "timeout",
            "message": "The run took longer than 0.5 s and was stopped.",
            "details": {"timeout_s": 0.5},
        }
    ]
    after = result(running.submit(job("echo")))["result"]["pid"]
    assert after != before
    assert ended(before)


def test_a_worker_that_dies_during_a_run_is_replaced(runner):
    running = runner()

    crashed = running.submit(job("exit", code=3)).result(timeout=WAIT_S)

    assert crashed.error
    assert crashed.document["code"] == "internal_error"
    assert crashed.document["details"] == {"exit_code": 3}
    assert crashed.document["command"] == "exit"
    assert result(running.submit(job("echo")))["status"] == "ok"


def test_a_cancelled_queued_run_is_not_run(runner, monkeypatch, tmp_path):
    log = tmp_path / "requests.log"
    monkeypatch.setenv("FAKE_WORKER_LOG", str(log))
    running = runner()
    release = tmp_path / "release"
    busy = running.submit(job("wait", release=str(release)))
    dropped = running.submit(job("echo", n="dropped"))

    assert dropped.cancel()
    release.touch()
    result(busy)
    result(running.submit(job("echo", n="after")))

    requests = [json.loads(line) for line in log.read_text("utf-8").splitlines()]
    assert [r["options"].get("n") for r in requests] == [None, "after"]


def test_closing_ends_queued_and_running_runs_and_stops_the_workers(runner, tmp_path):
    running = runner()
    pid = result(running.submit(job("echo")))["result"]["pid"]
    busy = running.submit(job("wait", release=str(tmp_path / "never")))
    queued = running.submit(job("echo"))
    wait_until(busy.running)

    running.close()

    for future in (busy, queued):
        outcome = future.result(timeout=WAIT_S)
        assert outcome.error
        assert outcome.document["code"] == "terminated"
    late = running.submit(job("echo")).result(timeout=WAIT_S)
    assert late.document["code"] == "terminated"
    assert ended(pid)


def test_runs_fail_when_no_worker_can_start(runner, monkeypatch):
    monkeypatch.setenv("FAKE_WORKER_BROKEN", "1")

    outcome = runner().submit(job("echo")).result(timeout=WAIT_S)

    assert outcome.error
    assert outcome.document["code"] == "internal_error"
    assert "did not start" in outcome.document["message"]


def test_a_check_run_reaches_the_worker_as_a_check(runner):
    document = result(runner().submit(Job("echo", {}, "/nowhere", check=True)))

    assert document["check"] is True
