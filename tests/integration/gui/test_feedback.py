"""„Zgłoś uwagę” and its admin routes (Nogat DEV-15.12, plan 2026-11-03, D3 to D5)
through Starlette's TestClient.

``POST api/feedback`` stores a report, its text and the context the page adds (view,
station, parameters and the server's version), in
``<data_dir>/hydrolog/feedback.sqlite3``, with no session and nothing else: a contact,
the page's address, diagnostics or any other field are refused and the request's
``User-Agent`` is not kept; a deleted report leaves no text in the file.
``api/admin/feedback`` lists, marks and deletes the reports only for the key of
``HYDROLOG_ADMIN_API_KEY`` or ``HYDROLOG_ADMIN_API_KEY_FILE`` in ``X-Admin-Key``, and
refuses everything when the server has no key.
"""

import json
import os
import re
import sqlite3
import threading
from contextlib import closing

import pytest

pytest.importorskip("starlette")

from starlette.testclient import TestClient

import hydrolog
from hydrolog.gui import create_app
from tests.contract._nogat import validator

KEY = "klucz-administratora-0123"
ERROR = validator("error-1")
AGENT = "Mozilla/5.0 (X11; Linux x86_64) TestowaPrzegladarka/9.8.7-unikalna"
LIST = "/api/admin/feedback"
ROUTES = [("GET", LIST), ("PATCH", f"{LIST}/1"), ("DELETE", f"{LIST}/1")]
"""The admin routes, each with a report that exists in the tests that make one."""
CONTEXT_FIELDS = [
    "context.app_version",
    "context.parameters",
    "context.station",
    "context.view",
]
"""The fields a context may have, as an ``unknown_field`` error lists them."""


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def app(tmp_path, data_dir):
    """An app of its own per test, so each test starts without reports."""
    created = create_app(work_root=tmp_path / "work", data_dir=data_dir)
    yield created
    created.state.gui.close()


@pytest.fixture
def admin(monkeypatch):
    """Set the admin key on the server; return the headers that carry it."""
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", KEY)
    return {"X-Admin-Key": KEY}


def database(data_dir):
    return data_dir / "hydrolog" / "feedback.sqlite3"


def file_bytes(data_dir):
    """Move the write-ahead log into the file and empty it; return the bytes of the
    file and of what SQLite keeps beside it."""
    path = database(data_dir)
    with closing(sqlite3.connect(path)) as db:
        busy = db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]
    assert busy == 0
    return b"".join(
        (path.parent / name).read_bytes()
        for name in os.listdir(path.parent)
        if name.startswith(path.name)
    )


def error(response, status, code, reason):
    """Check an error answer; return its document."""
    document = response.json()
    assert response.status_code == status, document
    ERROR.validate(document)
    assert document["code"] == code
    assert document["details"]["reason"] == reason, document
    return document


def body(message="x", **context):
    """Return the body the page sends: the text and its context."""
    return {"message": message, "context": {"view": "hydrogram", **context}}


def report(client, content, **headers):
    return client.post("/api/feedback", json=content, headers=headers)


def listing(client, headers, query=""):
    response = client.get(f"{LIST}{query}", headers=headers)
    assert response.status_code == 200, response.json()
    return response.json()


def send(client, request, *, headers=None):
    method, path = request
    content = {"is_read": True} if method == "PATCH" else None
    return client.request(method, path, json=content, headers=headers or {})


# --- a report -------------------------------------------------------------------------


def test_a_report_is_stored_by_the_first_report_and_answered_with_its_id(
    client, admin, data_dir
):
    assert listing(client, admin) == {"items": [], "total": 0, "unread_count": 0}
    assert not database(data_dir).exists()  # reading creates nothing

    response = report(client, body("Nie działa hydrogram"))

    assert response.status_code == 200
    assert response.json() == {"id": 1, "status": "ok"}
    # a report needs no session: none is started, no cookie is set
    assert "X-Hydrolog-Session" not in response.headers
    assert "set-cookie" not in response.headers
    assert database(data_dir).is_file()
    [item] = listing(client, admin)["items"]
    created = item.pop("created_at")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", created)
    assert item == {
        "id": 1,
        "message": "Nie działa hydrogram",
        "context": {
            "view": "hydrogram",
            "station": None,
            "parameters": {},
            "app_version": hydrolog.__version__,
        },
        "is_read": False,
    }


def test_a_report_keeps_its_view_station_and_parameters(client, admin):
    parameters = {"area_km2": 12.5, "methods": ["scs", "snyder"], "storm": {"p": 1}}
    content = body(
        "Qmax wygląda dziwnie",
        view="statystyka/przeplywy",
        station="Kamiennik — Świerzawa",
        parameters=parameters,
    )

    assert report(client, content).status_code == 200

    [item] = listing(client, admin)["items"]
    assert item["context"] == {
        "view": "statystyka/przeplywy",
        "station": "Kamiennik — Świerzawa",
        "parameters": parameters,
        "app_version": hydrolog.__version__,
    }
    assert item["is_read"] is False


@pytest.mark.parametrize(
    "sent",
    [{}, {"app_version": None}, {"app_version": ""}, {"app_version": "99.0.0-obca"}],
)
def test_the_context_has_the_servers_version_whatever_the_page_sends(
    client, admin, sent
):
    assert report(client, body(**sent)).status_code == 200

    [item] = listing(client, admin)["items"]
    assert item["context"]["app_version"] == hydrolog.__version__


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contact", "jan@example.com"),
        ("contact", None),  # even empty
        ("page_url", "http://127.0.0.1:8070/#hydrogram"),
        ("user_agent", AGENT),
        ("diagnostics", {"events": []}),
        ("is_read", True),  # not the report's to say
    ],
)
def test_a_field_outside_the_form_is_refused_and_nothing_stored(
    client, admin, data_dir, field, value
):
    response = report(client, {**body(), field: value})

    document = error(response, 400, "validation_error", "unknown_field")
    assert document["details"]["parameter"] == field
    assert document["details"]["allowed"] == ["context", "message"]
    assert listing(client, admin)["total"] == 0
    assert not database(data_dir).exists()


@pytest.mark.parametrize("field", ["url", "contact", "user_agent", "diagnostics"])
def test_a_field_outside_the_context_is_refused_and_nothing_stored(
    client, admin, data_dir, field
):
    response = report(client, body(**{field: "http://127.0.0.1:8070/#hydrogram"}))

    document = error(response, 400, "validation_error", "unknown_field")
    assert document["details"]["parameter"] == f"context.{field}"
    assert document["details"]["allowed"] == CONTEXT_FIELDS
    assert listing(client, admin)["total"] == 0
    assert not database(data_dir).exists()


@pytest.mark.parametrize(
    ("content", "parameter", "reason"),
    [
        ({"context": {"view": "v"}}, "message", "required"),
        ({**body(), "message": None}, "message", "required"),
        (body(""), "message", "empty"),
        (body(5), "message", "type"),
        (body("x" * 5001), "message", "too_long"),
        ({"message": "x"}, "context", "required"),
        ({"message": "x", "context": None}, "context", "required"),
        ({"message": "x", "context": ["hydrogram"]}, "context", "type"),
        ({"message": "x", "context": {}}, "context.view", "required"),
        (body(view=None), "context.view", "required"),
        (body(view=""), "context.view", "empty"),
        (body(view=["hydrogram"]), "context.view", "type"),
        (body(view="v" * 201), "context.view", "too_long"),
        (body(station=7), "context.station", "type"),
        (body(station="s" * 201), "context.station", "too_long"),
        (body(parameters=[1, 2]), "context.parameters", "type"),
        (body(parameters="area_km2=12"), "context.parameters", "type"),
        (body(app_version="9" * 51), "context.app_version", "too_long"),
    ],
)
def test_a_report_beyond_the_limits_is_refused(
    client, admin, data_dir, content, parameter, reason
):
    document = error(report(client, content), 400, "validation_error", reason)

    assert document["details"]["parameter"] == parameter
    assert listing(client, admin)["total"] == 0
    assert not database(data_dir).exists()


def test_the_largest_report_within_the_limits_is_stored(client, admin):
    """The message and the texts count characters; the context counts the bytes of
    its compact JSON in UTF-8, with the server's version in it."""
    view, station = "w" * 200, "ś" * 200
    stored = {
        "view": view,
        "station": station,
        "parameters": {"a": ""},
        "app_version": hydrolog.__version__,
    }
    compact = json.dumps(stored, ensure_ascii=False, separators=(",", ":"))
    pad = "d" * (100_000 - len(compact.encode()))

    def sent(text):
        return body("ż" * 5000, view=view, station=station, parameters={"a": text})

    assert report(client, sent(pad)).status_code == 200
    response = report(client, sent(pad + "d"))

    document = error(response, 400, "validation_error", "too_large")
    assert document["details"]["parameter"] == "context"
    assert document["details"]["limit_bytes"] == 100_000
    assert document["details"]["size_bytes"] == 100_001
    [item] = listing(client, admin)["items"]
    assert item["message"] == "ż" * 5000
    assert item["context"] == {**stored, "parameters": {"a": pad}}


@pytest.mark.parametrize(
    ("content", "content_type", "reason"),
    [
        (json.dumps(body()).encode(), "text/plain", "content_type"),
        (b'{"message": ', "application/json", "invalid_json"),
        (b'["message"]', "application/json", "type"),
        # An id of its own: pytest puts the test's id into an environment variable,
        # which Windows limits to 32 767 characters
        pytest.param(
            json.dumps(body(parameters={"pad": "p" * 300_000})).encode(),
            "application/json",
            "too_large",
            id="too_large",
        ),
    ],
)
def test_a_report_is_a_json_object_of_a_bounded_size(
    client, admin, content, content_type, reason
):
    response = client.post(
        "/api/feedback", content=content, headers={"Content-Type": content_type}
    )

    error(response, 400, "validation_error", reason)
    assert listing(client, admin)["total"] == 0


def test_lone_surrogates_are_stored_as_replacement_characters(client, admin):
    """A browser that cut an emoji in half sends half a surrogate pair."""
    content = (
        b'{"message": "Qmax \\ud83d!", "context": {"view": "hydrogram\\udc00",'
        b' "station": "\\ud83d", "parameters": {"stack": "\\udc00"}}}'
    )

    response = client.post(
        "/api/feedback", content=content, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200, response.json()
    [item] = listing(client, admin)["items"]
    assert item["message"] == "Qmax \ufffd!"
    assert item["context"] == {
        "view": "hydrogram\ufffd",
        "station": "\ufffd",
        "parameters": {"stack": "\ufffd"},
        "app_version": hydrolog.__version__,
    }


def test_the_stored_report_holds_no_user_agent_of_the_request(client, admin, data_dir):
    response = report(client, body("Nie działa"), **{"User-Agent": AGENT})
    assert response.status_code == 200

    assert AGENT not in json.dumps(listing(client, admin))
    content = file_bytes(data_dir)
    assert "Nie działa".encode() in content  # the bytes hold what was stored
    assert b"TestowaPrzegladarka" not in content


def test_a_deleted_report_leaves_no_text_in_the_file(client, admin, data_dir):
    """``secure_delete``: the text is overwritten, not only unlinked."""
    report(client, body("zostaje"))
    report(client, body("Tajne zgłoszenie 4f9c-kasowane", station="Stacja 4f9c"))
    assert b"4f9c-kasowane" in file_bytes(data_dir)  # the bytes hold what is stored

    assert client.delete(f"{LIST}/2", headers=admin).status_code == 200

    content = file_bytes(data_dir)
    assert b"4f9c" not in content
    assert b"zostaje" in content


def test_reports_go_to_the_data_dir_of_the_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HYDROLOG_DATA_DIR", str(tmp_path / "shared"))
    created = create_app(work_root=tmp_path / "work")
    try:
        response = report(TestClient(created), body())
    finally:
        created.state.gui.close()

    assert response.status_code == 200
    assert database(tmp_path / "shared").is_file()


def test_concurrent_reports_get_one_id_each(app, admin):
    numbers = []

    def post_ten():
        client = TestClient(app)
        for index in range(10):
            response = report(client, body(f"zgłoszenie {index}"))
            numbers.append(response.json()["id"])

    threads = [threading.Thread(target=post_ten) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(numbers) == list(range(1, 81))
    assert listing(TestClient(app), admin, "?limit=200")["total"] == 80


@pytest.mark.parametrize(
    "request_",
    [("POST", "/api/feedback"), ("PATCH", f"{LIST}/1"), ("DELETE", f"{LIST}/1")],
)
def test_writes_from_other_sites_are_refused(client, admin, request_):
    report(client, body())
    method, path = request_

    response = client.request(
        method,
        path,
        json={**body("y"), "is_read": True},
        headers={**admin, "Sec-Fetch-Site": "cross-site"},
    )

    error(response, 403, "forbidden", "cross_site")
    page = listing(client, admin)
    assert (page["total"], page["unread_count"]) == (1, 1)


# --- the admin key --------------------------------------------------------------------


@pytest.mark.parametrize("request_", ROUTES)
@pytest.mark.parametrize("headers", [{}, {"X-Admin-Key": KEY}])
def test_without_a_key_on_the_server_the_admin_routes_refuse_everything(
    client, request_, headers
):
    report(client, body())

    document = error(
        send(client, request_, headers=headers),
        401,
        "unauthorized",
        "admin_key_not_configured",
    )

    assert document["title"] == "Wymagane uwierzytelnienie"
    assert document["exit_code"] is None
    assert "HYDROLOG_ADMIN_API_KEY" in document["hint"]


@pytest.mark.parametrize("request_", ROUTES)
@pytest.mark.parametrize(
    ("headers", "reason"),
    [
        ({}, "admin_key_missing"),
        ({"X-Admin-Key": ""}, "admin_key_missing"),
        ({"X-Admin-Key": "zły klucz".encode()}, "admin_key_invalid"),
        ({"X-Admin-Key": KEY[:-1]}, "admin_key_invalid"),
        ({"X-Admin-Key": KEY + "4"}, "admin_key_invalid"),
    ],
)
def test_a_missing_or_wrong_key_is_refused_and_changes_nothing(
    client, admin, request_, headers, reason
):
    report(client, body())

    error(send(client, request_, headers=headers), 401, "unauthorized", reason)

    assert listing(client, admin)["items"][0]["is_read"] is False


def test_the_key_can_come_from_a_file_read_on_every_request(
    client, tmp_path, monkeypatch
):
    path = tmp_path / "admin.key"
    path.write_text(f"{KEY}\n", encoding="utf-8")
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY_FILE", str(path))

    assert client.get(LIST, headers={"X-Admin-Key": KEY}).status_code == 200

    path.write_text("nowy-klucz", encoding="utf-8")  # rotated without a restart
    error(
        client.get(LIST, headers={"X-Admin-Key": KEY}),
        401,
        "unauthorized",
        "admin_key_invalid",
    )
    assert client.get(LIST, headers={"X-Admin-Key": "nowy-klucz"}).status_code == 200


def test_the_key_variable_wins_over_the_key_file(client, admin, tmp_path, monkeypatch):
    path = tmp_path / "admin.key"
    path.write_text("klucz-z-pliku", encoding="utf-8")
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY_FILE", str(path))

    assert client.get(LIST, headers=admin).status_code == 200
    error(
        client.get(LIST, headers={"X-Admin-Key": "klucz-z-pliku"}),
        401,
        "unauthorized",
        "admin_key_invalid",
    )


def test_a_key_file_that_cannot_be_read_is_no_key(client, tmp_path, monkeypatch):
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY_FILE", str(tmp_path / "missing.key"))

    response = client.get(LIST, headers={"X-Admin-Key": ""})

    error(response, 401, "unauthorized", "admin_key_not_configured")


def test_a_key_beyond_ascii_is_compared_as_the_bytes_sent(client, monkeypatch):
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", "zażółć-gęślą-jaźń")

    response = client.get(LIST, headers={"X-Admin-Key": "zażółć-gęślą-jaźń".encode()})

    assert response.status_code == 200, response.json()


# --- the list, the read flag and deleting ---------------------------------------------


def test_the_list_is_newest_first_with_the_total_and_the_unread_count(client, admin):
    for message in ("pierwsze", "drugie", "trzecie"):
        report(client, body(message))
    client.patch(f"{LIST}/2", json={"is_read": True}, headers=admin)

    page = listing(client, admin)

    assert [
        (item["id"], item["message"], item["is_read"]) for item in page["items"]
    ] == [
        (3, "trzecie", False),
        (2, "drugie", True),
        (1, "pierwsze", False),
    ]
    assert (page["total"], page["unread_count"]) == (3, 2)


def test_the_list_pages_by_limit_and_offset(client, admin):
    for index in range(5):
        report(client, body(f"zgłoszenie {index}"))

    pages = [
        listing(client, admin, f"?limit=2&offset={offset}") for offset in (0, 2, 4, 6)
    ]

    assert [[item["id"] for item in page["items"]] for page in pages] == [
        [5, 4],
        [3, 2],
        [1],
        [],
    ]
    assert {page["total"] for page in pages} == {5}


@pytest.mark.parametrize(
    ("query", "parameter", "reason"),
    [
        ("?limit=0", "limit", "minimum"),
        ("?limit=201", "limit", "maximum"),
        ("?limit=dużo", "limit", "type"),
        ("?limit=1.5", "limit", "type"),
        ("?offset=-1", "offset", "minimum"),
    ],
)
def test_the_page_parameters_are_checked(client, admin, query, parameter, reason):
    document = error(
        client.get(f"{LIST}{query}", headers=admin), 400, "validation_error", reason
    )

    assert document["details"]["parameter"] == parameter


def test_a_report_is_marked_read_and_unread_again(client, admin):
    report(client, body())

    marked = client.patch(f"{LIST}/1", json={"is_read": True}, headers=admin)
    read = listing(client, admin)
    unmarked = client.patch(f"{LIST}/1", json={"is_read": False}, headers=admin)

    assert (marked.status_code, marked.json()) == (200, {"status": "ok"})
    assert (read["items"][0]["is_read"], read["unread_count"]) == (True, 0)
    assert unmarked.json() == {"status": "ok"}
    assert listing(client, admin)["unread_count"] == 1


@pytest.mark.parametrize(
    ("content", "reason"),
    [({}, "required"), ({"is_read": "yes"}, "type"), ({"is_read": 1}, "type")],
)
def test_marking_takes_only_a_boolean_is_read(client, admin, content, reason):
    report(client, body())

    response = client.patch(f"{LIST}/1", json=content, headers=admin)

    document = error(response, 400, "validation_error", reason)
    assert document["details"]["parameter"] == "is_read"
    assert listing(client, admin)["unread_count"] == 1


def test_a_report_is_deleted_once(client, admin):
    report(client, body("pierwsze"))
    report(client, body("drugie"))

    deleted = client.delete(f"{LIST}/1", headers=admin)
    again = client.delete(f"{LIST}/1", headers=admin)

    assert (deleted.status_code, deleted.json()) == (200, {"status": "deleted"})
    document = error(again, 404, "not_found", "feedback_not_found")
    assert document["details"]["feedback_id"] == 1
    page = listing(client, admin)
    assert ([item["id"] for item in page["items"]], page["total"]) == ([2], 1)


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
@pytest.mark.parametrize("number", [7, 2**63])
def test_reports_that_do_not_exist_are_not_found(client, admin, method, number):
    report(client, body())

    response = send(client, (method, f"{LIST}/{number}"), headers=admin)

    document = error(response, 404, "not_found", "feedback_not_found")
    assert document["details"]["feedback_id"] == number
    assert listing(client, admin)["total"] == 1


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
def test_without_a_first_report_nothing_is_found_and_nothing_made(
    client, admin, data_dir, method
):
    response = send(client, (method, f"{LIST}/1"), headers=admin)

    error(response, 404, "not_found", "feedback_not_found")
    assert not database(data_dir).exists()
