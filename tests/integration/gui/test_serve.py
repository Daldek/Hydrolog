"""The standalone server (plan D3, D8): it answers, stops on a signal with exit 0,
keeps Nogat's logs (DEV-12.4 to DEV-12.9), and refuses a port in use, an unknown host
and a missing extra."""

import contextlib
import json
import os
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import urllib.request

import pytest

pytest.importorskip("uvicorn")

from hydrolog.exceptions import (
    ConflictError,
    InvalidParameterError,
    MissingDependencyError,
)
from hydrolog.gui import create_app
from hydrolog.gui.server import serve, url_of
from tests.contract._nogat import validator

SERVE = (
    "import json\n"
    "from hydrolog.gui.server import serve\n"
    "print(json.dumps(serve(host='127.0.0.1', port=0, open_browser=False)))\n"
)
TIMESTAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
START_TIMEOUT_S = 60
RECORD = validator("record-1")

posix_signals = pytest.mark.skipif(
    sys.platform == "win32",
    reason="SIGINT and SIGTERM are POSIX signals; Windows stops a console with Ctrl+C",
)


@pytest.fixture
def state_dir(tmp_path_factory):
    """The server's ``state_dir``, outside its working and temporary directory."""
    return tmp_path_factory.mktemp("state")


class Started:
    """A server process, the address of its record ``start`` and its standard error."""

    def __init__(self, argv, tmp_path, state_dir):
        environment = {
            **os.environ,
            "TMPDIR": str(tmp_path),
            "HYDROLOG_STATE_DIR": str(state_dir),
        }
        self.process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
            cwd=tmp_path,
        )
        self.stderr: list[str] = []
        lines: queue.Queue = queue.Queue()

        def read():
            for line in self.process.stderr:
                self.stderr.append(line)
                lines.put(line)
            lines.put(None)

        self._reader = threading.Thread(target=read, daemon=True)
        self._reader.start()
        while True:
            try:
                line = lines.get(timeout=START_TIMEOUT_S)
            except queue.Empty:
                self.process.kill()
                pytest.fail(f"the server did not announce itself: {self.stderr}")
            if line is None:
                pytest.fail(f"the server ended: {self.stderr}")
            with contextlib.suppress(ValueError):
                record = json.loads(line)
                if record.get("event") == "start":
                    self.url = record["settings"]["url"]
                    return

    def stop(self, number):
        """Send the signal; return standard output once the process has ended."""
        try:
            self.process.send_signal(number)
            self.process.wait(timeout=60)
            out = self.process.stdout.read()
            self._reader.join(timeout=60)
        finally:
            self.process.kill()
        return out


def log_records(state_dir, kind):
    """Return the records of ``<state_dir>/hydrolog/logs/<kind>-*.jsonl``, in order."""
    return [
        json.loads(line)
        for path in sorted((state_dir / "hydrolog" / "logs").glob(f"{kind}-*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.status, response.headers, response.read()


@posix_signals
@pytest.mark.parametrize("stop", [signal.SIGTERM, signal.SIGINT])
def test_the_server_answers_and_a_signal_stops_it_with_exit_0(
    tmp_path, state_dir, stop
):
    server = Started([sys.executable, "-c", SERVE], tmp_path, state_dir)
    process, url = server.process, server.url
    try:
        status, headers, body = get(url + "api/session")
    finally:
        out = server.stop(stop)

    assert status == 200
    assert json.loads(body)["schema"] == "hydrolog-gui-session/1"
    assert headers["Content-Security-Policy"].startswith("default-src 'self';")
    assert process.returncode == 0
    times = json.loads(out)
    assert times["url"] == url
    assert TIMESTAMP.match(times["started_at"])
    assert TIMESTAMP.match(times["stopped_at"])
    assert list(tmp_path.iterdir()) == []  # the work root went with the server


@posix_signals
def test_hydrolog_gui_serve_logs_to_files_and_prints_only_its_lifecycle(
    tmp_path, state_dir
):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    argv = [sys.executable, "-m", "hydrolog.cli", "gui", "serve", "--no-browser"]

    server = Started([*argv, "--port", str(port), "--json"], tmp_path, state_dir)
    process, url = server.process, server.url
    try:
        status, headers, _ = get(url + "api/session?email=jan@example.pl&x=1")
        static, _, _ = get(url + "css/app.css")
    finally:
        out = server.stop(signal.SIGTERM)

    assert url == f"http://127.0.0.1:{port}/"
    assert (status, static) == (200, 200)
    assert "x-request-id" not in {name.lower() for name in headers}
    assert process.returncode == 0
    envelope = json.loads(out)
    assert envelope["result"]["schema"] == "hydrolog-gui-serve/1"
    assert envelope["result"]["url"] == url
    printed = [json.loads(line) for line in server.stderr]
    assert [(r["kind"], r["event"]) for r in printed] == [
        ("lifecycle", "start"),
        ("lifecycle", "stop"),
    ]
    assert printed[0]["settings"] == {"url": url, "public": False}
    assert log_records(state_dir, "lifecycle") == printed
    [access] = log_records(state_dir, "access")  # the page's file is not logged
    for record in [*printed, access]:
        RECORD.validate(record)
    assert (access["method"], access["path"], access["status"]) == (
        "GET",
        "/api/session?email=&x=1",
        200,
    )
    assert access["agent"] == "script"


def test_a_port_in_use_is_a_conflict():
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]

        with pytest.raises(ConflictError) as raised:
            serve(host="127.0.0.1", port=port, open_browser=False)

    assert raised.value.details == {
        "reason": "port_in_use",
        "host": "127.0.0.1",
        "port": port,
    }


def test_a_host_that_does_not_resolve_is_a_validation_error():
    with pytest.raises(InvalidParameterError) as raised:
        serve(host="no-such-host.invalid", port=0, open_browser=False)

    assert raised.value.details["option"] == "host"
    assert raised.value.details["reason"] == "invalid_host"


@pytest.mark.parametrize("module", ["starlette", "uvicorn"])
def test_without_the_extra_the_gui_says_how_to_install_it(monkeypatch, module):
    monkeypatch.setitem(sys.modules, module, None)

    for start in (
        lambda: serve(host="127.0.0.1", port=0, open_browser=False),
        lambda: create_app(),
    ):
        with pytest.raises(MissingDependencyError) as raised:
            start()
        assert raised.value.hint == 'pip install "hydrolog[gui]"'
        assert raised.value.details == {"extra": "gui", "module": module}


@pytest.mark.parametrize(
    ("host", "url"),
    [
        ("127.0.0.1", "http://127.0.0.1:8070/"),
        ("localhost", "http://localhost:8070/"),
        ("::1", "http://[::1]:8070/"),
    ],
)
def test_the_address_of_the_page(host, url):
    assert url_of(host, 8070) == url
