"""„Zgłoś uwagę” and its admin routes (Nogat plan 2026-11-03, D3 to D5) through
Starlette's TestClient.

``POST api/feedback`` stores a report of a GUI session in
``<data_dir>/hydrolog/feedback.sqlite3`` with Hydrograf's limits and answers;
``api/admin/feedback`` lists, marks and deletes the reports only for the key of
``HYDROLOG_ADMIN_API_KEY`` or ``HYDROLOG_ADMIN_API_KEY_FILE`` in ``X-Admin-Key``, and
refuses everything when the server has no key.
"""

import json
import re
import threading

import pytest

pytest.importorskip("starlette")

from starlette.testclient import TestClient

from hydrolog.gui import create_app
from tests.contract._nogat import validator

KEY = "klucz-administratora-0123"
ERROR = validator("error-1")
AGENT = "Mozilla/5.0 (X11; Linux x86_64) Testowa/1.0"
LIST = "/api/admin/feedback"
ROUTES = [("GET", LIST), ("PATCH", f"{LIST}/1"), ("DELETE", f"{LIST}/1")]
"""The admin routes, each with a report that exists in the tests that make one."""


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


def error(response, status, code, reason):
    """Check an error answer; return its document."""
    document = response.json()
    assert response.status_code == status, document
    ERROR.validate(document)
    assert document["code"] == code
    assert document["details"]["reason"] == reason, document
    return document


def report(client, body, **headers):
    return client.post("/api/feedback", json=body, headers=headers)


def listing(client, headers, query=""):
    response = client.get(f"{LIST}{query}", headers=headers)
    assert response.status_code == 200, response.json()
    return response.json()


def send(client, request, *, headers=None):
    method, path = request
    body = {"is_read": True} if method == "PATCH" else None
    return client.request(method, path, json=body, headers=headers or {})


# --- a report -------------------------------------------------------------------------


def test_a_report_is_stored_by_the_first_report_and_answered_with_its_id(
    client, admin, data_dir
):
    assert listing(client, admin) == {"items": [], "total": 0, "unread_count": 0}
    assert not database(data_dir).exists()  # reading creates nothing

    response = report(
        client, {"message": "Nie działa hydrogram"}, **{"User-Agent": AGENT}
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "status": "ok"}
    assert "hydrolog_gui=" in response.headers["set-cookie"]  # a GUI session
    assert database(data_dir).is_file()
    [item] = listing(client, admin)["items"]
    created = item.pop("created_at")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", created)
    assert item == {
        "id": 1,
        "message": "Nie działa hydrogram",
        "contact": None,
        "page_url": None,
        "user_agent": AGENT,
        "diagnostics": None,
        "is_read": False,
    }


def test_a_report_keeps_its_contact_page_and_diagnostics(client, admin):
    diagnostics = {
        "events": [{"t": "2026-11-03T10:15:00.000Z", "type": "api_call", "data": {}}],
        "workspace": {"section": "hydrogram", "context": "Kamiennik — Świerzawa"},
        "env": {"viewport": {"width": 1440, "height": 900}},
    }
    body = {
        "message": "Qmax wygląda dziwnie",
        "contact": "jan@example.com",
        "page_url": "http://127.0.0.1:8070/#hydrogram",
        "diagnostics": diagnostics,
        "is_read": True,  # not the report's to say: ignored
    }

    assert report(client, body).status_code == 200

    [item] = listing(client, admin)["items"]
    assert (item["contact"], item["page_url"]) == (body["contact"], body["page_url"])
    assert item["diagnostics"] == diagnostics
    assert item["is_read"] is False


@pytest.mark.parametrize(
    ("body", "parameter", "reason"),
    [
        ({}, "message", "required"),
        ({"message": None}, "message", "required"),
        ({"message": ""}, "message", "empty"),
        ({"message": 5}, "message", "type"),
        ({"message": "x" * 5001}, "message", "too_long"),
        ({"message": "x", "contact": "a" * 201}, "contact", "too_long"),
        ({"message": "x", "contact": ["jan"]}, "contact", "type"),
        ({"message": "x", "page_url": "u" * 501}, "page_url", "too_long"),
        ({"message": "x", "diagnostics": [1]}, "diagnostics", "type"),
        (
            {"message": "x", "diagnostics": {"events": ["e" * 100] * 1100}},
            "diagnostics",
            "too_large",
        ),
    ],
)
def test_a_report_beyond_hydrografs_limits_is_refused(
    client, admin, body, parameter, reason
):
    document = error(report(client, body), 400, "validation_error", reason)

    assert document["details"]["parameter"] == parameter
    assert listing(client, admin)["total"] == 0


def test_the_largest_report_within_the_limits_is_stored(client, admin):
    # 5000 characters of two UTF-8 bytes each: the limit counts characters
    body = {"message": "ż" * 5000, "contact": "k" * 200, "page_url": "u" * 500}
    # {"a":"…"} is 8 bytes of compact JSON around the text: 100 000 bytes in all
    largest = {"a": "d" * 99_992}

    assert report(client, {**body, "diagnostics": largest}).status_code == 200
    document = error(
        report(client, {**body, "diagnostics": {"a": "d" * 99_993}}),
        400,
        "validation_error",
        "too_large",
    )

    assert document["details"]["limit_bytes"] == 100_000
    [item] = listing(client, admin)["items"]
    assert (item["message"], item["contact"], item["page_url"]) == (
        body["message"],
        body["contact"],
        body["page_url"],
    )
    assert item["diagnostics"] == largest


@pytest.mark.parametrize(
    ("content", "content_type", "reason"),
    [
        (b'{"message": "x"}', "text/plain", "content_type"),
        (b'{"message": ', "application/json", "invalid_json"),
        (b'["message"]', "application/json", "type"),
        (
            json.dumps({"message": "x", "pad": "p" * 300_000}).encode(),
            "application/json",
            "too_large",
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
    content = b'{"message": "Qmax \\ud83d!", "diagnostics": {"stack": "\\udc00"}}'

    response = client.post(
        "/api/feedback", content=content, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200, response.json()
    [item] = listing(client, admin)["items"]
    assert item["message"] == "Qmax \ufffd!"
    assert item["diagnostics"] == {"stack": "\ufffd"}


def test_reports_go_to_the_data_dir_of_the_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HYDROLOG_DATA_DIR", str(tmp_path / "shared"))
    created = create_app(work_root=tmp_path / "work")
    try:
        response = report(TestClient(created), {"message": "x"})
    finally:
        created.state.gui.close()

    assert response.status_code == 200
    assert database(tmp_path / "shared").is_file()


def test_concurrent_reports_get_one_id_each(app, admin):
    numbers = []

    def post_ten():
        client = TestClient(app)
        for index in range(10):
            response = report(client, {"message": f"zgłoszenie {index}"})
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
    report(client, {"message": "x"})
    method, path = request_

    response = client.request(
        method,
        path,
        json={"message": "y", "is_read": True},
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
    report(client, {"message": "x"})

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
    report(client, {"message": "x"})

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
        report(client, {"message": message})
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
        report(client, {"message": f"zgłoszenie {index}"})

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
    report(client, {"message": "x"})

    marked = client.patch(f"{LIST}/1", json={"is_read": True}, headers=admin)
    read = listing(client, admin)
    unmarked = client.patch(f"{LIST}/1", json={"is_read": False}, headers=admin)

    assert (marked.status_code, marked.json()) == (200, {"status": "ok"})
    assert (read["items"][0]["is_read"], read["unread_count"]) == (True, 0)
    assert unmarked.json() == {"status": "ok"}
    assert listing(client, admin)["unread_count"] == 1


@pytest.mark.parametrize(
    ("body", "reason"),
    [({}, "required"), ({"is_read": "yes"}, "type"), ({"is_read": 1}, "type")],
)
def test_marking_takes_only_a_boolean_is_read(client, admin, body, reason):
    report(client, {"message": "x"})

    response = client.patch(f"{LIST}/1", json=body, headers=admin)

    document = error(response, 400, "validation_error", reason)
    assert document["details"]["parameter"] == "is_read"
    assert listing(client, admin)["unread_count"] == 1


def test_a_report_is_deleted_once(client, admin):
    report(client, {"message": "pierwsze"})
    report(client, {"message": "drugie"})

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
    report(client, {"message": "x"})

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
