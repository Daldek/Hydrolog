"""The page and the private API of the GUI server, through Starlette's TestClient.

Plan 2026-11-02, D5 to D8: every route, limit, header, refused path and error status;
the newest run of a channel and the timeout with a new worker; the app mounted under
a prefix of a host. The runs use the real worker and catalog.
"""

import asyncio
import hashlib
import json
import threading
import time
from concurrent.futures import Future
from importlib import resources
from pathlib import Path

import pytest

pytest.importorskip("starlette")

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

import hydrolog
from hydrolog import catalog
from hydrolog._attribution import provider_lines
from hydrolog.catalog import command_schema, data_commands
from hydrolog.exceptions import ERROR_CODES, InvalidParameterError
from hydrolog.gui import create_app
from hydrolog.gui._app import _outcome
from hydrolog.testing import example_network_document
from tests.contract._nogat import validator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
FLOOD = (FIXTURES / "flood_inflow.csv").read_bytes()
KIRPICH = {"length_km": 8.2, "slope_m_per_m": 0.023}
MIB = 2**20
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS = {
    "content-security-policy": CSP,
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}
EXCLUDED = ("gui serve", "config show", "commands guide", "commands batch")
RESULT = validator("result-1")
ERROR = validator("error-1")
TITLES_PL = {code: spec.title for code, spec in ERROR_CODES.items()}
TITLES_PL["method_not_allowed"] = "Niedozwolona metoda"


def error(response, status, code, reason=None):
    """Check an error answer; return its document."""
    document = response.json()
    assert response.status_code == status, document
    ERROR.validate(document)
    assert document["code"] == code
    assert document["title"] == TITLES_PL[code]
    if reason is not None:
        assert document["details"]["reason"] == reason, document
    return document


def ok(response):
    """Check a successful run; return its envelope."""
    document = response.json()
    assert response.status_code == 200, document
    RESULT.validate(document)
    return document


def upload(client, name, data, **headers):
    return client.put(f"/api/files/in/{name}", content=data, headers=headers)


def run(client, command, options, query=""):
    return client.post(f"/api/run/{command.replace(' ', '/')}{query}", json=options)


def session_cookie(response):
    cookies = response.headers.get_list("set-cookie")
    assert len(cookies) == 1, cookies
    return cookies[0]


# --- the session ----------------------------------------------------------------------


def test_a_first_request_starts_a_session_with_its_cookie(client):
    response = client.get("/api/session")

    assert response.status_code == 200
    assert response.json() == {
        "schema": "hydrolog-gui-session/1",
        "version": hydrolog.__version__,
        "limits": {
            "file_bytes": 20 * MIB,
            "session_bytes": 100 * MIB,
            "session_files": 200,
            "request_bytes": 5 * MIB,
            "sessions": 64,
            "idle_s": 43200.0,
            "name_pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$",
            "run_timeout_s": 30.0,
        },
        "used_bytes": 0,
        "files": [],
        "gui": None,
        "attribution": provider_lines(),
    }
    cookie = session_cookie(response)
    name, _, attributes = cookie.partition(";")
    assert name.startswith("hydrolog_gui=")
    assert {part.strip().lower() for part in attributes.split(";")} == {
        "httponly",
        "path=/",
        "samesite=strict",
    }


def test_the_cookie_keeps_the_session_and_its_files(client):
    upload(client, "flood.csv", FLOOD)

    response = client.get("/api/session")

    assert "set-cookie" not in response.headers
    assert response.json()["files"] == [
        {
            "path": "in/flood.csv",
            "size_bytes": len(FLOOD),
            "sha256": hashlib.sha256(FLOOD).hexdigest(),
        }
    ]
    assert response.json()["used_bytes"] == len(FLOOD)


def test_the_session_gives_the_gui_addresses_of_nogat_toml(
    client, tmp_path, monkeypatch
):
    """``[nogat] gui`` for Nogat's app menu (DEV-15.4), read at every request."""
    settings = tmp_path / "nogat.toml"
    settings.write_text(
        "[nogat]\n"
        'gui = { hydrograf = " https://hydrograf.example/ ", archiwista = "/a/",'
        ' kartograf = 8060, obserwator = "" }\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("NOGAT_CONFIG", str(settings))

    assert client.get("/api/session").json()["gui"] == {
        "hydrograf": "https://hydrograf.example/",
        "archiwista": "/a/",
    }
    settings.write_text('[nogat]\nlang = "pl"\n', encoding="utf-8")
    assert client.get("/api/session").json()["gui"] is None


def test_an_unknown_cookie_gets_a_new_session(client):
    response = client.get(
        "/api/session", headers={"cookie": "hydrolog_gui=" + "A" * 43}
    )

    cookie = session_cookie(response)
    assert cookie.startswith("hydrolog_gui=")
    assert not cookie.startswith("hydrolog_gui=" + "A" * 43)


# --- the catalog ----------------------------------------------------------------------


def test_the_command_list_leaves_out_the_excluded_commands(client):
    response = client.get("/api/commands")

    assert response.status_code == 200
    document = response.json()
    assert document["schema"] == "hydrolog-command-list/1"
    names = [entry["name"] for entry in document["commands"]]
    assert names == [c.name for c in data_commands() if c.name not in EXCLUDED]


def test_a_command_is_its_catalog_document(client):
    response = client.get("/api/commands/uh/nash")

    assert response.status_code == 200
    assert response.json() == command_schema("uh nash").to_dict()


@pytest.mark.parametrize("name", EXCLUDED)
def test_the_excluded_commands_are_not_found(client, name):
    path = name.replace(" ", "/")

    error(client.get(f"/api/commands/{path}"), 404, "not_found")
    error(client.post(f"/api/run/{path}", json={}), 404, "not_found")
    error(client.post(f"/api/format/{path}", json={}), 404, "not_found")


def test_an_unknown_command_is_not_found(client):
    document = error(client.post("/api/run/tc/nope", json={}), 404, "not_found")

    assert document["command"] == "tc nope"


def test_the_schemas_of_the_package_are_served(client):
    response = client.get("/api/schemas/hydrolog-network-1.schema.json")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    package = resources.files("hydrolog") / "schemas" / "hydrolog-network-1.schema.json"
    assert response.content == package.read_bytes()


@pytest.mark.parametrize(
    "name", ["hydrolog-nope-1.schema.json", "__init__.py", "commands-1.schema.json"]
)
def test_other_schemas_are_not_found(client, name):
    error(client.get(f"/api/schemas/{name}"), 404, "not_found")


# --- runs -----------------------------------------------------------------------------


def test_a_run_answers_its_envelope(client):
    document = ok(run(client, "tc kirpich", KIRPICH, "?channel=kalkulatory"))

    assert document["command"] == "tc kirpich"
    assert document["status"] == "ok"
    assert document["inputs"] == KIRPICH
    assert document["result"]["schema"] == "hydrolog-tc-kirpich/1"


def test_a_check_plans_without_writing(client):
    upload(client, "flood.csv", FLOOD)
    options = {"input_file": "in/flood.csv", "lag_min": 20, "output": "out/o.csv"}

    document = ok(run(client, "route lag", options, "?check=true"))

    assert document["check"] is True
    assert document["result"]["targets"][0]["path"] == "out/o.csv"
    error(client.get("/api/files/out/o.csv"), 404, "not_found")


def test_a_check_of_a_read_only_command_is_refused(client):
    response = run(client, "tc kirpich", KIRPICH, "?check=true")

    error(response, 400, "validation_error", "no_check")


def test_invalid_options_are_a_validation_error_worded_by_the_catalog(client):
    response = run(client, "tc kirpich", {"length_km": -1, "slope_m_per_m": 0.02})

    document = error(response, 400, "validation_error", "exclusive_minimum")
    assert document["details"]["option"] == "length_km"
    assert document["command"] == "tc kirpich"


def test_a_result_that_cannot_be_computed_is_a_calculation_error(client):
    response = run(client, "stats flood-frequency", {"values": [1.0, 2.0]})

    error(response, 422, "calculation_error")


def test_a_malformed_input_file_is_a_data_error_without_server_paths(client, app):
    upload(client, "maxima.csv", b"year;Q\nx;y\n")
    options = {"input_file": "in/maxima.csv", "value_column": "Q"}

    response = run(client, "stats flood-frequency", options)

    error(response, 500, "data_error")
    assert str(app.state.gui.sessions.root) not in response.text


def test_outputs_are_files_of_the_session(client, app):
    upload(client, "flood.csv", FLOOD)
    options = {"input_file": "in/flood.csv", "lag_min": 20, "output": "out/o.csv"}

    document = ok(run(client, "route lag", options))

    assert document["inputs"]["input_file"] == "in/flood.csv"
    assert document["inputs"]["output"] == "out/o.csv"
    assert [f["path"] for f in document["result"]["files"]] == ["out/o.csv"]
    assert str(app.state.gui.sessions.root) not in json.dumps(document)
    download = client.get("/api/files/out/o.csv")
    assert download.status_code == 200
    assert (
        hashlib.sha256(download.content).hexdigest()
        == (document["result"]["files"][0]["sha256"])
    )
    error(run(client, "route lag", options), 409, "conflict", "output_exists")
    assert ok(run(client, "route lag", {**options, "force": True}))["status"] == "ok"


def test_outputs_written_into_a_directory_can_be_downloaded_and_removed(client):
    options = {"network": example_network_document(), "output_dir": "out/net"}

    document = ok(run(client, "route network", options))

    paths = [f["path"] for f in document["result"]["files"]]
    assert paths and all(path.startswith("out/net/") for path in paths)
    listed = [f["path"] for f in client.get("/api/session").json()["files"]]
    assert listed == sorted(paths)
    assert client.get(f"/api/files/{paths[0]}").status_code == 200
    assert client.delete("/api/files/out/net").status_code == 204
    assert client.get("/api/session").json()["files"] == []


@pytest.mark.parametrize(
    ("query", "parameter", "reason"),
    [("?channel=two%20words", "channel", "pattern"), ("?check=yes", "check", "choice")],
)
def test_the_query_parameters_are_checked(client, query, parameter, reason):
    document = error(run(client, "tc kirpich", KIRPICH, query), 400, "validation_error")

    assert document["details"]["parameter"] == parameter
    assert document["details"]["reason"] == reason


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("text/plain", json.dumps(KIRPICH)),
        ("application/x-www-form-urlencoded", "length_km=8.2"),
        (None, json.dumps(KIRPICH)),
    ],
)
@pytest.mark.parametrize("route", ["run", "format"])
def test_run_and_format_take_only_json(client, route, content_type, body):
    headers = {} if content_type is None else {"content-type": content_type}

    response = client.post(f"/api/{route}/tc/kirpich", content=body, headers=headers)

    error(response, 400, "validation_error", "content_type")


@pytest.mark.parametrize(
    ("body", "reason"),
    [("{", "invalid_json"), ('{"cn": NaN}', "invalid_json"), ("[1, 2]", "type")],
)
def test_a_body_must_be_a_json_object(client, body, reason):
    response = client.post(
        "/api/run/tc/kirpich",
        content=body,
        headers={"content-type": "application/json"},
    )

    error(response, 400, "validation_error", reason)


# --- paths ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "/etc/passwd",
        "../flood.csv",
        "in/../flood.csv",
        "flood.csv",
        "in/d/x.csv",
        "C:\\x",
    ],
)
def test_paths_outside_the_session_are_forbidden_before_the_run(client, value):
    response = run(client, "route lag", {"input_file": value, "lag_min": 20})

    document = error(response, 403, "forbidden", "outside_session")
    assert document["details"]["option"] == "input_file"


def test_a_command_writes_only_into_out(client):
    upload(client, "flood.csv", FLOOD)
    options = {"input_file": "in/flood.csv", "lag_min": 20, "output": "in/x.csv"}

    error(run(client, "route lag", options), 403, "forbidden", "output_area")


@pytest.mark.parametrize("name", ["%2E%2E", ".hidden", "CON", "a%5Cb", "x" * 129])
def test_uploads_need_a_file_name_of_the_rule(client, name):
    error(upload(client, name, b"x"), 403, "forbidden", "outside_session")


def test_uploads_go_only_into_in(client):
    error(client.put("/api/files/out/x.csv", content=b"x"), 405, "method_not_allowed")


@pytest.mark.parametrize(
    "path", ["in/..%2F..%2Fetc%2Fpasswd", "tmp/x.csv", "in/.hidden", "in/"]
)
def test_downloads_outside_the_session_are_forbidden(client, path):
    upload(client, "x.csv", b"x")

    error(client.get(f"/api/files/{path}"), 403, "forbidden", "outside_session")
    error(client.delete(f"/api/files/{path}"), 403, "forbidden", "outside_session")


def test_files_that_do_not_exist_are_not_found(client):
    error(client.get("/api/files/in/x.csv"), 404, "not_found", "no_file")  # no session
    upload(client, "y.csv", b"y")
    error(client.get("/api/files/in/x.csv"), 404, "not_found", "no_file")
    error(client.delete("/api/files/in/x.csv"), 404, "not_found", "no_file")


def test_a_file_uploads_downloads_and_goes(client):
    data = "rok,Q [m3/s]\n2023,307,3\nżółw\n".encode()

    created = upload(client, "maksima roczne.csv", data)

    assert created.status_code == 201
    assert created.json() == {
        "schema": "hydrolog-gui-file/1",
        "path": "in/maksima roczne.csv",
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    download = client.get("/api/files/in/maksima roczne.csv")
    assert download.content == data
    assert download.headers["content-disposition"].startswith("attachment;")
    assert upload(client, "maksima roczne.csv", b"new").status_code == 201
    assert client.get("/api/files/in/maksima roczne.csv").content == b"new"
    assert client.delete("/api/files/in/maksima roczne.csv").status_code == 204
    assert client.get("/api/session").json()["files"] == []


# --- limits ---------------------------------------------------------------------------


def test_a_json_body_over_5_mib_is_refused(client):
    body = json.dumps({"pad": "x" * (5 * MIB)}).encode()

    declared = client.post(
        "/api/run/tc/kirpich",
        content=body,
        headers={"content-type": "application/json"},
    )
    streamed = client.post(
        "/api/run/tc/kirpich",
        content=iter([body[:MIB], body[MIB:]]),
        headers={"content-type": "application/json"},
    )

    for response in (declared, streamed):
        document = error(response, 400, "validation_error", "too_large")
        assert document["details"]["limit_bytes"] == 5 * MIB


def test_a_file_over_20_mib_is_refused(client):
    exact = upload(client, "exact.bin", b"\0" * (20 * MIB))
    declared = upload(client, "over.bin", b"\0" * (20 * MIB + 1))
    streamed = client.put(
        "/api/files/in/streamed.bin", content=iter([b"\0" * (20 * MIB), b"\0"])
    )

    assert exact.status_code == 201
    for response in (declared, streamed):
        document = error(response, 400, "validation_error", "too_large")
        assert document["details"]["limit_bytes"] == 20 * MIB
    files = [f["path"] for f in client.get("/api/session").json()["files"]]
    assert files == ["in/exact.bin"]


def test_a_session_holds_at_most_200_files(client):
    for number in range(200):
        assert upload(client, f"f{number:03}.csv", b"1").status_code == 201

    document = error(upload(client, "one-more.csv", b"1"), 409, "conflict")

    assert document["details"]["reason"] == "session_full"
    assert document["details"]["limit_files"] == 200
    assert upload(client, "f000.csv", b"2").status_code == 201  # a replacement fits
    assert client.delete("/api/files/in/f001.csv").status_code == 204
    assert upload(client, "one-more.csv", b"1").status_code == 201


def test_a_full_session_takes_no_upload_and_no_writing_run(client, app):
    upload(client, "flood.csv", FLOOD)
    session = app.state.gui.sessions.get(client.cookies.get("hydrolog_gui"))
    with (session.directory / "in" / "big.bin").open("wb") as stream:
        stream.truncate(100 * MIB - len(FLOOD))  # sparse: the session is full

    refused = upload(client, "x.csv", b"1")
    writing = run(
        client,
        "route lag",
        {"input_file": "in/flood.csv", "lag_min": 20, "output": "out/o.csv"},
    )
    reading = run(client, "route lag", {"input_file": "in/flood.csv", "lag_min": 20})

    assert error(refused, 409, "conflict")["details"]["limit_bytes"] == 100 * MIB
    assert error(writing, 409, "conflict")["details"]["reason"] == "session_full"
    assert ok(reading)["status"] == "ok"
    assert client.delete("/api/files/in/big.bin").status_code == 204
    assert upload(client, "x.csv", b"1").status_code == 201


def test_a_65th_session_replaces_the_least_recently_used_idle_one(app):
    first = TestClient(app)
    upload(first, "x.csv", b"x")
    for _ in range(64):
        TestClient(app).get("/api/session")

    error(first.get("/api/files/in/x.csv"), 404, "not_found")
    assert "hydrolog_gui=" in session_cookie(first.get("/api/session"))


# --- headers and cross-site requests --------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "cache"),
    [
        ("GET", "/", "no-cache"),
        ("GET", "/index.html", "no-cache"),
        ("GET", "/src/main.js", "no-cache"),
        ("GET", "/missing.js", "no-cache"),
        ("GET", "/api/session", "no-store"),
        ("GET", "/api/commands", "no-store"),
        ("GET", "/api/nope", "no-store"),
        ("POST", "/api/session", "no-store"),
        ("POST", "/api/run/tc/kirpich", "no-store"),
    ],
)
def test_every_response_has_the_security_headers(client, method, path, cache):
    response = client.request(method, path, json={})

    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value, name
    assert response.headers["cache-control"] == cache


def test_the_page_is_served_and_revalidated(client, web):
    page = client.get("/")

    assert page.status_code == 200
    assert page.text == (web / "index.html").read_text(encoding="utf-8")
    script = client.get("/src/main.js")
    assert script.headers["content-type"].startswith("text/javascript")
    again = client.get("/", headers={"if-none-match": page.headers["etag"]})
    assert again.status_code == 304
    assert again.headers["content-security-policy"] == CSP


def test_unknown_api_routes_and_methods_are_error_documents(client):
    error(client.get("/api/nope"), 404, "not_found", "no_route")
    document = error(client.post("/api/session"), 405, "method_not_allowed", "method")
    assert document["exit_code"] is None


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/run/tc/kirpich"),
        ("POST", "/api/format/tc/kirpich"),
        ("PUT", "/api/files/in/x.csv"),
        ("DELETE", "/api/files/in/x.csv"),
    ],
)
def test_writes_from_other_sites_are_refused(client, method, path, site):
    upload(client, "x.csv", b"x")

    response = client.request(
        method, path, json=KIRPICH, headers={"sec-fetch-site": site}
    )

    document = error(response, 403, "forbidden", "cross_site")
    assert document["details"]["sec_fetch_site"] == site
    assert client.get("/api/files/in/x.csv").content == b"x"


@pytest.mark.parametrize("site", ["same-origin", "none"])
def test_writes_from_the_page_itself_are_allowed(client, site):
    response = client.post(
        "/api/run/tc/kirpich", json=KIRPICH, headers={"sec-fetch-site": site}
    )

    assert ok(response)["status"] == "ok"


def test_reads_from_other_sites_are_answered(client):
    response = client.get("/api/commands", headers={"sec-fetch-site": "cross-site"})

    assert response.status_code == 200


# --- the newest run, the timeout ------------------------------------------------------


def test_a_newer_run_of_a_channel_replaces_the_queued_older_one(slow_app):
    app = slow_app(workers=1)
    cookie = TestClient(app).get("/api/session").cookies["hydrolog_gui"]
    answers = {}

    def post(key, length_km, channel):
        client = TestClient(app, cookies={"hydrolog_gui": cookie})
        started = time.monotonic()
        options = {"length_km": length_km, "slope_m_per_m": 0.02}
        answers[key] = (run(client, "tc kirpich", options, f"?channel={channel}"),)
        answers[key] += (time.monotonic() - started,)

    threads = [
        threading.Thread(target=post, args=("busy", 3.0, "siec")),
        threading.Thread(target=post, args=("older", 0.1, "hydrogram")),
        threading.Thread(target=post, args=("newer", 0.2, "hydrogram")),
    ]
    for thread in threads:
        thread.start()
        time.sleep(0.5)
    for thread in threads:
        thread.join(timeout=60)

    replaced, waited = answers["older"]
    assert ok(replaced)["status"] == "cancelled"
    assert replaced.json()["notices"][0]["code"] == "superseded"
    assert waited < 2.0  # answered when the newer run came, not after the busy one
    assert ok(answers["newer"][0])["inputs"]["length_km"] == 0.2
    assert ok(answers["busy"][0])["status"] == "ok"


def test_a_run_over_the_timeout_ends_cancelled_and_a_new_worker_runs_on(slow_app):
    client = TestClient(slow_app(run_timeout_s=1.0))
    started = time.monotonic()

    stopped = ok(run(client, "tc kirpich", {"length_km": 60, "slope_m_per_m": 0.02}))

    assert time.monotonic() - started < 30
    assert stopped["status"] == "cancelled"
    assert stopped["result"] is None
    assert stopped["notices"] == [
        {
            "level": "warning",
            "code": "timeout",
            "message": "The run took longer than 1 s and was stopped.",
            "details": {"timeout_s": 1.0},
        }
    ]
    after = ok(run(client, "tc kirpich", {"length_km": 0.01, "slope_m_per_m": 0.02}))
    assert after["status"] == "ok"


def test_a_client_that_goes_away_drops_its_queued_run():
    async def gone():
        return {"type": "http.disconnect"}

    request = Request({"type": "http", "method": "POST", "headers": []}, gone)
    future = Future()

    outcome = asyncio.run(_outcome(request, future))

    assert outcome is None
    assert future.cancelled()


# --- the CLI line ---------------------------------------------------------------------


def test_the_cli_line_of_options_comes_from_the_catalog(client):
    response = client.post("/api/format/tc/kirpich", json=KIRPICH)

    assert response.status_code == 200
    assert response.json() == {
        "schema": "hydrolog-gui-line/1",
        "line": catalog.format_command("tc kirpich", KIRPICH),
    }


def test_the_cli_line_shows_files_by_their_names(client):
    options = {"input_file": "in/flood.csv", "lag_min": 20, "output": "out/o.csv"}

    line = client.post("/api/format/route/lag", json=options).json()["line"]

    shown = {"input_file": "flood.csv", "lag_min": 20, "output": "o.csv"}
    assert line == catalog.format_command("route lag", shown)


# --- the app in a host, its lifespan --------------------------------------------------


def test_a_host_serves_the_page_and_the_api_under_its_prefix(web, tmp_path):
    gui = create_app(work_root=tmp_path / "work", workers=1)
    host = Starlette(
        routes=[
            Route("/", lambda request: PlainTextResponse("host")),
            Mount("/m/hydrolog", app=gui),
        ]
    )
    client = TestClient(host)
    try:
        page = client.get("/m/hydrolog/")
        script = client.get("/m/hydrolog/src/main.js")
        session = client.get("/m/hydrolog/api/session")
        uploaded = client.put("/m/hydrolog/api/files/in/flood.csv", content=FLOOD)
        downloaded = client.get("/m/hydrolog/api/files/in/flood.csv")
        computed = client.post("/m/hydrolog/api/run/tc/kirpich", json=KIRPICH)
        missing = client.get("/m/hydrolog/api/nope")
        own = client.get("/")
    finally:
        gui.state.gui.close()

    assert page.text == (web / "index.html").read_text(encoding="utf-8")
    assert page.headers["content-security-policy"] == CSP
    assert script.status_code == 200
    assert "path=/m/hydrolog/" in session_cookie(session).lower()
    assert uploaded.status_code == 201
    assert downloaded.content == FLOOD
    assert ok(computed)["status"] == "ok"
    error(missing, 404, "not_found")
    assert missing.headers["cache-control"] == "no-store"
    assert own.text == "host"
    assert "content-security-policy" not in own.headers


def test_the_lifespan_starts_the_workers_and_removes_the_sessions(web, tmp_path):
    work = tmp_path / "work"
    app = create_app(work_root=work, workers=1)

    with TestClient(app) as client:
        assert ok(run(client, "tc kirpich", KIRPICH))["status"] == "ok"
        assert len(list(work.iterdir())) == 1

    assert work.is_dir()
    assert list(work.iterdir()) == []


def test_a_work_root_of_its_own_is_removed_with_the_app(web):
    app = create_app(workers=1)
    root = app.state.gui.sessions.root

    with TestClient(app) as client:
        client.get("/api/session")
        assert root.is_dir()

    assert not root.exists()


@pytest.mark.parametrize(
    "arguments", [{"workers": 0}, {"workers": 1.5}, {"run_timeout_s": 0}]
)
def test_the_app_needs_a_worker_and_a_positive_timeout(arguments):
    with pytest.raises(InvalidParameterError):
        create_app(**arguments)
