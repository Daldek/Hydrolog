"""``gui serve``: the plan of ``check``, the guard of the extra and the result."""

import logging
import socket
import sys
import types

import pytest

import hydrolog
from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError, MissingDependencyError
from hydrolog.operations import gui as gui_module


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class TestCheck:
    """``check`` plans without serving: the address and whether the port is free."""

    def test_the_plan_of_the_default_call(self):
        envelope = hydrolog.check_command("gui serve").to_dict()

        assert envelope["check"] is True
        assert envelope["result"]["schema"] == "hydrolog-plan/1"
        assert envelope["result"]["targets"] == []
        assert envelope["result"]["url"] == "http://127.0.0.1:8070/"
        assert isinstance(envelope["result"]["port_free"], bool)
        assert envelope["notices"] == []

    def test_a_free_port_and_a_taken_one(self):
        port = _free_port()
        free = run_command("gui serve", {"port": port, "check": True}).to_dict()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            taken = server.getsockname()[1]
            busy = run_command("gui serve", {"port": taken, "check": True}).to_dict()

        assert free["result"]["port_free"] is True
        assert busy["result"]["port_free"] is False

    def test_an_address_beyond_this_computer_warns_that_there_is_no_sign_in(self):
        port = _free_port()
        envelope = run_command(
            "gui serve", {"host": "0.0.0.0", "port": port, "check": True}
        ).to_dict()

        url = f"http://0.0.0.0:{port}/"
        assert envelope["result"]["url"] == url
        [notice] = envelope["notices"]
        assert (notice["level"], notice["code"]) == ("warning", "exposed_without_auth")
        assert notice["details"] == {"host": "0.0.0.0", "url": url}

    @pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.2", "localhost", "::1"])
    def test_a_loopback_address_has_no_notice(self, host):
        if host == "::1" and not socket.has_ipv6:
            pytest.skip("no IPv6 on this computer")
        try:
            envelope = run_command(
                "gui serve", {"host": host, "port": _free_port(), "check": True}
            ).to_dict()
        except InvalidParameterError:
            pytest.skip(f"{host} is not an address of this computer")
        assert envelope["notices"] == []

    def test_an_ipv6_address_is_written_in_brackets(self):
        assert gui_module._url("::1", 8070) == "http://[::1]:8070/"

    def test_an_unresolvable_host_is_refused_by_its_reason(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command("gui serve", {"host": "no-such-host.invalid", "check": True})
        assert caught.value.details == {
            "option": "host",
            "reason": "invalid_host",
            "value": "no-such-host.invalid",
        }

    @pytest.mark.parametrize("port", [0, 65536])
    def test_the_port_is_bounded(self, port):
        with pytest.raises(InvalidParameterError) as caught:
            run_command("gui serve", {"port": port, "check": True})
        assert caught.value.details["option"] == "port"


def test_without_the_extra_it_is_a_missing_dependency(monkeypatch):
    real = gui_module.find_spec
    monkeypatch.setattr(
        gui_module,
        "find_spec",
        lambda name: None if name == "uvicorn" else real(name),
    )

    with pytest.raises(MissingDependencyError) as caught:
        run_command("gui serve", {"check": True})

    assert caught.value.details == {"extra": "gui", "module": "uvicorn"}
    assert caught.value.hint == 'pip install "hydrolog[gui]"'


def test_serving_returns_where_and_when_it_served(monkeypatch, caplog):
    """The server of the extra blocks until it is stopped; the result follows."""
    calls = []

    def serve(*, host, port, open_browser):
        calls.append((host, port, open_browser))
        return {
            "url": f"http://{host}:{port}/",
            "started_at": "2026-11-02T10:15:00Z",
            "stopped_at": "2026-11-02T11:00:00Z",
        }

    server = types.ModuleType("hydrolog.gui.server")
    server.serve = serve  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "hydrolog.gui.server", server)

    with caplog.at_level(logging.WARNING, logger="hydrolog"):
        envelope = run_command(
            "gui serve", {"host": "0.0.0.0", "port": 8099, "no_browser": True}
        ).to_dict()

    assert calls == [("0.0.0.0", 8099, False)]
    assert envelope["check"] is False
    assert envelope["result"] == {
        "schema": "hydrolog-gui-serve/1",
        "url": "http://0.0.0.0:8099/",
        "started_at": "2026-11-02T10:15:00Z",
        "stopped_at": "2026-11-02T11:00:00Z",
    }
    assert [n["code"] for n in envelope["notices"]] == ["exposed_without_auth"]
    assert "no sign-in" in caplog.text, "the warning is shown when serving starts"
