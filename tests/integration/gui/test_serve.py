"""The standalone server (plan D3, D8): it answers, stops on a signal with exit 0,
and refuses a port in use, an unknown host and a missing extra."""

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

SERVE = (
    "import json\n"
    "from hydrolog.gui.server import serve\n"
    "print(json.dumps(serve(host='127.0.0.1', port=0, open_browser=False)))\n"
)
ANNOUNCED = re.compile(r"^Hydrolog GUI: (http://127\.0\.0\.1:\d+/)$")
TIMESTAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
START_TIMEOUT_S = 60

posix_signals = pytest.mark.skipif(
    sys.platform == "win32",
    reason="SIGINT and SIGTERM are POSIX signals; Windows stops a console with Ctrl+C",
)


def started(argv, tmp_path):
    """Start a server process; return it and the address it announced."""
    environment = {**os.environ, "TMPDIR": str(tmp_path)}
    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        cwd=tmp_path,
    )
    lines: queue.Queue = queue.Queue()

    def read():
        for line in process.stderr:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    seen = []
    while True:
        try:
            line = lines.get(timeout=START_TIMEOUT_S)
        except queue.Empty:
            process.kill()
            pytest.fail(f"the server did not announce itself: {seen}")
        if line is None:
            pytest.fail(f"the server ended: {seen}")
        seen.append(line)
        match = ANNOUNCED.match(line.strip())
        if match:
            return process, match.group(1)


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.status, response.headers, response.read()


@posix_signals
@pytest.mark.parametrize("stop", [signal.SIGTERM, signal.SIGINT])
def test_the_server_answers_and_a_signal_stops_it_with_exit_0(tmp_path, stop):
    process, url = started([sys.executable, "-c", SERVE], tmp_path)
    try:
        status, headers, body = get(url + "api/session")
        process.send_signal(stop)
        out, _ = process.communicate(timeout=60)
    finally:
        process.kill()

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
def test_hydrolog_gui_serve_answers_and_stops_with_exit_0(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    argv = [sys.executable, "-m", "hydrolog.cli", "gui", "serve", "--no-browser"]

    process, url = started([*argv, "--port", str(port), "--json"], tmp_path)
    try:
        status, _, _ = get(url + "api/commands")
        process.send_signal(signal.SIGTERM)
        out, _ = process.communicate(timeout=60)
    finally:
        process.kill()

    assert url == f"http://127.0.0.1:{port}/"
    assert status == 200
    assert process.returncode == 0
    envelope = json.loads(out)
    assert envelope["result"]["schema"] == "hydrolog-gui-serve/1"
    assert envelope["result"]["url"] == url


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
