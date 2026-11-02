"""The worker of the GUI server: one request, one document, no server paths."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from hydrolog.gui import _worker

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
KIRPICH = {"length_km": 8.2, "slope_m_per_m": 0.023}


@pytest.fixture
def session(tmp_path):
    root = tmp_path / "session"
    (root / "in").mkdir(parents=True)
    (root / "out").mkdir()
    return root.resolve()


def request(command, options, root, check=False):
    return {"command": command, "options": options, "root": str(root), "check": check}


def test_a_run_answers_its_envelope(session):
    reply = _worker.handle(request("tc kirpich", KIRPICH, session))

    assert reply["error"] is False
    assert reply["document"]["schema"] == "hydrolog-result/1"
    assert reply["document"]["status"] == "ok"
    assert reply["document"]["inputs"] == KIRPICH


def test_a_failure_answers_its_error_document_in_polish(session):
    reply = _worker.handle(request("tc kirpich", {"length_km": -1.0}, session))

    assert reply["error"] is True
    assert reply["document"]["code"] == "validation_error"
    assert reply["document"]["title"] == "Nieprawidłowe dane wejściowe"
    assert reply["document"]["command"] == "tc kirpich"


def test_paths_of_the_session_come_back_relative(session):
    flood = (FIXTURES / "flood_inflow.csv").read_bytes()
    (session / "in" / "flood.csv").write_bytes(flood)
    options = {
        "input_file": str(session / "in" / "flood.csv"),
        "lag_min": 20.0,
        "output": str(session / "out" / "outflow.csv"),
    }

    reply = _worker.handle(request("route lag", options, session))

    document = reply["document"]
    assert reply["error"] is False
    assert document["inputs"]["input_file"] == "in/flood.csv"
    assert document["inputs"]["output"] == "out/outflow.csv"
    assert [item["path"] for item in document["result"]["files"]] == ["out/outflow.csv"]
    assert str(session) not in json.dumps(document)
    assert (session / "out" / "outflow.csv").is_file()


def test_errors_name_no_server_path(session):
    options = {"input_file": str(session / "in" / "missing.csv"), "lag_min": 20.0}

    reply = _worker.handle(request("route lag", options, session))

    assert reply["error"] is True
    assert reply["document"]["code"] == "not_found"
    assert str(session) not in json.dumps(reply["document"])
    assert "in/missing.csv" in json.dumps(reply["document"])


def test_a_path_outside_the_session_is_forbidden_in_the_worker_too(session, tmp_path):
    outside = tmp_path / "outside.csv"
    outside.write_bytes((FIXTURES / "flood_inflow.csv").read_bytes())

    reply = _worker.handle(
        request("route lag", {"input_file": str(outside), "lag_min": 20.0}, session)
    )

    assert reply["error"] is True
    assert reply["document"]["code"] == "forbidden"
    assert reply["document"]["details"]["allowed_dirs"] == ["."]


def test_a_check_run_plans_without_writing(session):
    flood = (FIXTURES / "flood_inflow.csv").read_bytes()
    (session / "in" / "flood.csv").write_bytes(flood)
    options = {
        "input_file": str(session / "in" / "flood.csv"),
        "lag_min": 20.0,
        "output": str(session / "out" / "outflow.csv"),
    }

    reply = _worker.handle(request("route lag", options, session, check=True))

    assert reply["document"]["check"] is True
    assert reply["document"]["result"]["schema"] == "hydrolog-plan/1"
    assert reply["document"]["result"]["targets"][0]["path"] == "out/outflow.csv"
    assert not (session / "out" / "outflow.csv").exists()


def test_the_worker_process_speaks_its_protocol(session):
    process = subprocess.Popen(
        [sys.executable, "-m", "hydrolog.gui._worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    try:
        ready = json.loads(process.stdout.readline())
        line = json.dumps(request("tc kirpich", KIRPICH, session)) + "\n"
        process.stdin.write(line.encode("utf-8"))
        process.stdin.flush()
        reply = json.loads(process.stdout.readline())
        process.stdin.close()
        code = process.wait(timeout=30)
    finally:
        process.kill()
        process.wait()

    assert ready == {"ready": True, "pid": process.pid}
    assert reply["error"] is False
    assert reply["document"]["command"] == "tc kirpich"
    assert code == 0


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS is POSIX")
def test_a_worker_caps_its_address_space():
    script = (
        "import resource\n"
        "from hydrolog.gui._worker import _limit_memory\n"
        "_limit_memory()\n"
        "print(resource.getrlimit(resource.RLIMIT_AS)[0])\n"
    )
    shown = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout

    if sys.platform == "darwin" and int(shown) != _worker.MEMORY_LIMIT_BYTES:
        pytest.skip("macOS refused the cap (best effort there)")
    assert int(shown) == 2 * 2**30
