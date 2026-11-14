"""A public GUI (Nogat DEV-15.7 to DEV-15.11), through Starlette's TestClient.

A deployment whose ``nogat.toml`` has ``[nogat.operator]`` opens the GUI to anyone:
the app serves the filled regulamin, limits the requests of each client address and
counts its use in daily totals; given a ``ServerLog``, public or not, it logs every
request but static content without the address (Nogat DEV-12.4 to DEV-12.9). The
clients come from the documentation address ``203.0.113.7`` (RFC 5737), which must
never be written anywhere.
"""

import json
import logging
import re
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("starlette")

from hydrolog.gui import create_app
from hydrolog.gui.nogat_logging import ServerLog
from tests.contract._nogat import validator

FLOOD = (
    Path(__file__).resolve().parents[2] / "fixtures" / "flood_inflow.csv"
).read_bytes()
ADDRESS = "203.0.113.7"
OTHER_ADDRESS = "198.51.100.2"
SERVICE_URL = "https://hydrolog.example/"
SETTINGS = f"""
[nogat]
gui = {{ hydrolog = "{SERVICE_URL}" }}

[nogat.operator]
name = "Jan Kowalski, ul. Wodna 1, 00-001 Warszawa"
email = "operator@hydrolog.example"
terms_effective = 2026-11-20
processor = "Cloudflare, Inc."
processor_transfer = "Dane mogą być przekazywane do USA."
processor_cookie = ""
mail_provider = "iCloud Mail (Apple)"
mail_transfer = "Mogą być przetwarzane poza Europejskim Obszarem Gospodarczym."
"""
OPERATOR = tomllib.loads(SETTINGS)["nogat"]["operator"]
ERROR = validator("error-1")
RECORD = validator("record-1")
KIRPICH = {"length_km": 8.2, "slope_m_per_m": 0.023}
FLOOD_OPTIONS = {"input_file": "in/flood.csv", "lag_min": 20, "output": "out/o.csv"}
CATALOG = [
    "/api/commands",
    "/api/commands/uh/nash",
    "/api/schemas/hydrolog-network-1.schema.json",
]
STATIC = ["/nogat/tokens.css", "/src/main.js"]


def settings(*, operator=OPERATOR, service_url=SERVICE_URL, limit=300, window=60):
    """Return a parsed ``nogat.toml``; ``operator=None`` leaves the table out."""
    shared = {} if service_url is None else {"gui": {"hydrolog": service_url}}
    if operator is not None:
        shared["operator"] = dict(operator)
    return {
        "nogat": shared,
        "hydrolog": {"request_limit": limit, "request_window": window},
    }


@pytest.fixture
def make_app(web, tmp_path):
    """Yield ``make_app(config, data_dir=..., log=None)``: apps of one worker, closed
    at the end; their daily totals go to ``tmp_path / "data"`` by default."""
    made = []

    def make(config, *, data_dir=None, log=None):
        created = create_app(
            work_root=tmp_path / f"work{len(made)}",
            workers=1,
            data_dir=tmp_path / "data" if data_dir is None else data_dir,
            config=config,
            log=log,
        )
        made.append(created)
        return created

    yield make
    for created in made:
        created.state.gui.close()


@pytest.fixture
def visitor(page_client):
    """Return ``visitor(app, address=ADDRESS, user_agent=...)``: a page's client."""

    def make(app, address=ADDRESS, user_agent="Browser/1.0"):
        return page_client(
            app, client=(address, 50000), headers={"user-agent": user_agent}
        )

    return make


def assert_secure(response):
    """The security headers of every response (plan D8)."""
    assert response.headers["content-security-policy"].startswith("default-src 'self'")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def log_records(directory):
    """Return the records of every log file of ``directory``, by file then line."""
    return [
        json.loads(line)
        for path in sorted(directory.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def stats_lines(data_dir):
    path = data_dir / "hydrolog" / "stats.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --- the regulamin (DEV-15.7) ---------------------------------------------------------


def test_the_regulamin_is_the_kits_template_filled_for_the_deployment(
    make_app, visitor
):
    response = visitor(make_app(settings())).get("/regulamin.html")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert_secure(response)
    page = response.text
    for expected in (
        "<title>Regulamin serwisu Hydrolog</title>",
        "Jan Kowalski, ul. Wodna 1, 00-001 Warszawa",
        "mailto:operator@hydrolog.example",
        "obowiązuje od 2026-11-20",
        f'<a href="{SERVICE_URL}">Wróć do serwisu Hydrolog</a>',
        "Ruch do serwisu przechodzi przez Cloudflare, Inc.",
        "na licencji MIT",
        "https://github.com/Daldek/Hydrolog",
        "<h3>IMGW-PIB: opady maksymalne PMAXTP</h3>",
        "<h3>IMGW-PIB: dane publiczne</h3>",
        "https://danepubliczne.imgw.pl",
        "<h3>ČHMÚ</h3>",
    ):
        assert expected in page, expected
    for absent in (
        "Copernicus",
        "GUGiK",
        "OpenStreetMap",
        "Esri",
        "Wody Polskie",
        "ČÚZK",
        "SoilGrids",
        "IMGW-PIB: serwis hydrologiczny",
        "Warunki korzystania z danych IMGW-PIB",
        "{{",
        "<!-- block",
        "<!-- /block",
    ):
        assert absent not in page, absent
    assert re.findall(r'<link rel="stylesheet" href="([^"]*)">', page) == [
        "nogat/tokens.css",
        "nogat/nogat-terms.css",
    ]
    assert "<script" not in page


def test_the_values_of_the_regulamin_are_html_escaped(make_app, visitor):
    operator = {**OPERATOR, "name": "Firma <b>& Syn</b>"}

    page = visitor(make_app(settings(operator=operator))).get("/regulamin.html").text

    assert "Firma &lt;b&gt;&amp; Syn&lt;/b&gt;" in page
    assert "<b>" not in page


def test_a_public_deployment_names_its_regulamin_and_operator(make_app, visitor):
    client = visitor(make_app(settings()))
    expected = {
        "terms": "regulamin.html",
        "operator_email": "operator@hydrolog.example",
    }

    session = client.get("/api/session").json()
    terms = client.get("/api/terms")

    assert {key: session[key] for key in expected} == expected
    assert terms.status_code == 200
    assert terms.json() == expected


def test_a_gui_that_is_not_public_has_no_regulamin(make_app, visitor):
    client = visitor(make_app(settings(operator=None)))

    assert client.get("/regulamin.html").status_code == 404
    assert client.get("/api/terms").json() == {"terms": None, "operator_email": None}
    session = client.get("/api/session").json()
    assert (session["terms"], session["operator_email"]) == (None, None)


@pytest.mark.parametrize(
    "deployment",
    [
        {"operator": {k: v for k, v in OPERATOR.items() if k != "mail_provider"}},
        {"operator": {**OPERATOR, "processor": ""}},
        {"operator": {**OPERATOR, "terms_effective": "  "}},
        {"service_url": None},
        {"service_url": " "},
    ],
    ids=[
        "missing-key",
        "empty-processor",
        "blank-date",
        "no-gui-address",
        "blank-gui-address",
    ],
)
def test_an_incomplete_operator_gives_no_regulamin_and_no_link(
    make_app, visitor, deployment
):
    """DEV-15.7: with a field missing the GUI serves no page and no link; the
    operator's address still goes to „Zgłoś uwagę”."""
    client = visitor(make_app(settings(**deployment)))

    assert client.get("/regulamin.html").status_code == 404
    expected = {"terms": None, "operator_email": "operator@hydrolog.example"}
    assert client.get("/api/terms").json() == expected
    session = client.get("/api/session").json()
    assert (session["terms"], session["operator_email"]) == (
        None,
        "operator@hydrolog.example",
    )


def test_an_operator_email_that_is_not_text_is_not_named(make_app, visitor):
    client = visitor(make_app(settings(operator={**OPERATOR, "email": 5})))

    assert client.get("/api/terms").json() == {"terms": None, "operator_email": None}
    assert client.get("/regulamin.html").status_code == 404


# --- the request limit (DEV-15.9) -----------------------------------------------------


def test_requests_over_the_limit_get_429_with_retry_after(make_app, visitor):
    client = visitor(make_app(settings(limit=3, window=60)))
    assert [client.get("/api/terms").status_code for _ in range(3)] == [200] * 3

    api = client.get("/api/terms")
    page = client.get("/")

    assert api.status_code == 429
    document = api.json()
    ERROR.validate(document)
    assert document["code"] == "rate_limited"
    assert document["title"] == "Zbyt wiele żądań"
    wait = int(api.headers["retry-after"])
    assert 1 <= wait <= 60
    assert document["details"] == {"reason": "rate_limited", "retry_after_s": wait}
    assert api.headers["cache-control"] == "no-store"
    assert page.status_code == 429
    assert page.headers["content-type"] == "text/html; charset=utf-8"
    seconds = int(page.headers["retry-after"])
    assert 1 <= seconds <= 60
    assert f"Zbyt wiele żądań. Spróbuj ponownie za {seconds} s." in page.text
    for refused in (api, page):
        assert_secure(refused)


def test_a_refused_post_does_not_reach_the_app(make_app, visitor):
    app = make_app(settings(limit=1, window=60))
    client = visitor(app)
    client.get("/api/terms")

    refused = client.post(
        "/api/feedback", json={"message": "x", "context": {"view": "kalkulatory"}}
    )

    assert refused.status_code == 429
    assert app.state.gui.reports.listing(limit=10, offset=0)["total"] == 0


def test_static_files_and_the_catalog_are_not_counted(make_app, visitor):
    client = visitor(make_app(settings(limit=3, window=60)))

    for _ in range(5):
        for path in STATIC + CATALOG:
            assert client.get(path).status_code == 200, path

    assert [client.get("/api/terms").status_code for _ in range(3)] == [200] * 3
    assert client.get("/api/terms").status_code == 429
    for path in STATIC + CATALOG:  # still answered over the limit
        assert client.get(path).status_code == 200, path


def test_each_address_has_a_limit_of_its_own(make_app, visitor):
    app = make_app(settings(limit=2, window=60))
    first, second = visitor(app), visitor(app, address=OTHER_ADDRESS)
    first.get("/api/terms")
    first.get("/api/terms")

    assert first.get("/api/terms").status_code == 429
    assert [second.get("/api/terms").status_code for _ in range(2)] == [200, 200]
    assert second.get("/").status_code == 429


def test_requests_pass_again_after_the_window(make_app, visitor):
    client = visitor(make_app(settings(limit=2, window=1)))
    client.get("/api/terms")
    client.get("/api/terms")
    refused = client.get("/api/terms")
    assert refused.status_code == 429
    assert refused.headers["retry-after"] == "1"

    time.sleep(1.1)

    assert [client.get("/api/terms").status_code for _ in range(2)] == [200, 200]
    assert client.get("/api/terms").status_code == 429


# --- the access log (Nogat DEV-12.4 to DEV-12.9) --------------------------------------


def test_every_request_but_static_content_gives_one_record_without_the_address(
    make_app, visitor, tmp_path, caplog
):
    caplog.set_level(logging.DEBUG)
    logs = tmp_path / "logs"
    app = make_app(settings(limit=6, window=60), log=ServerLog("hydrolog", "1", logs))
    client = visitor(app, user_agent="Testowa/2.0")
    requests = [
        ("GET", "/?widok=siec&x=1", None),
        ("GET", "/src/main.js", None),  # a file of the page: not logged
        ("GET", "/api/commands", None),  # a catalog document: not logged
        ("GET", "/src/missing.js", None),  # not found: logged
        ("GET", "/api/session", None),
        ("POST", "/api/run/tc/kirpich?channel=kalkulatory&q=Kamienna", KIRPICH),
        ("POST", "/api/run/tc/nope", {}),
        ("GET", "/regulamin.html", None),
        ("GET", "/missing.html", None),
        ("GET", "/api/terms", None),  # the 7th counted: over the limit, logged too
    ]

    responses = [
        client.request(method, path, json=body) for method, path, body in requests
    ]

    assert [r.status_code for r in responses] == [
        200,
        200,
        200,
        404,
        200,
        200,
        404,
        200,
        404,
        429,
    ]
    logged = [
        (request, response)
        for request, response in zip(requests, responses, strict=True)
        if request[1] not in ("/src/main.js", "/api/commands")
    ]
    records = log_records(logs)
    assert len(records) == len(logged)
    for record, ((method, path, _), response) in zip(records, logged, strict=True):
        RECORD.validate(record)
        assert (record["kind"], record["app"]) == ("access", "hydrolog")
        assert (record["method"], record["status"], record["bytes"]) == (
            method,
            response.status_code,
            len(response.content),
        )
        assert record["path"] == path.replace("q=Kamienna", "q=")
        assert record["agent"] == "script"
        assert "x-request-id" not in response.headers
    assert len({record["request_id"] for record in records}) == len(records)
    text = "".join(p.read_text(encoding="utf-8") for p in logs.glob("*.jsonl"))
    assert ADDRESS not in text and "Testowa" not in text and "Kamienna" not in text
    for record in caplog.records:
        assert ADDRESS not in record.getMessage(), record.name
        assert ADDRESS not in repr(vars(record)), record.name


# --- the daily totals (DEV-15.11) -----------------------------------------------------


def test_the_daily_totals_count_visitors_pages_stations_runs_and_downloads(
    make_app, visitor, tmp_path
):
    data_dir = tmp_path / "data"
    app = make_app(settings())
    first = visitor(app, user_agent="Browser A")
    second = visitor(app, address=OTHER_ADDRESS, user_agent="Browser B")
    same_address = visitor(app, user_agent="Browser B")
    only_static = visitor(app, address="192.0.2.1")

    page = first.get("/")  # page view 1
    assert first.get(
        "/", headers={"if-none-match": page.headers["etag"]}
    ).status_code == (
        304  # page view 2: a revalidated page is served too
    )
    assert first.get("/regulamin.html").status_code == 200  # page view 3
    assert first.get("/admin/").status_code == 200  # not a public page
    assert first.get("/missing.html").status_code == 404  # not served
    first.put("/api/files/in/flood.csv", content=FLOOD)
    assert first.post("/api/run/tc/kirpich", json=KIRPICH).json()["status"] == "ok"
    checked = first.post("/api/run/route/lag?check=true", json=FLOOD_OPTIONS)
    assert checked.json()["status"] == "ok" and checked.json()["check"] is True
    assert first.post("/api/run/tc/kirpich", json={"length_km": -1}).status_code == 400
    assert second.get("/").status_code == 200  # page view 4
    assert second.post("/api/stats/station").status_code == 204
    assert second.post("/api/stats/download").status_code == 204
    assert second.post("/api/stats/download").status_code == 204
    assert same_address.get("/index.html").status_code == 200  # page view 5
    for path in STATIC + CATALOG:
        assert only_static.get(path).status_code == 200
    today = datetime.now(UTC).date().isoformat()

    app.state.gui.close()

    expected = {
        "date": today,
        "visitors": 3,
        "page_views": 5,
        "stations_opened": 1,
        "analyses_run": 1,
        "downloads": 2,
    }
    assert stats_lines(data_dir) == [expected]
    text = (data_dir / "hydrolog" / "stats.jsonl").read_text(encoding="utf-8")
    assert list(json.loads(text)) == list(expected)  # the order of DEV-15.11
    assert ADDRESS not in text and OTHER_ADDRESS not in text
    assert "Browser" not in text

    restarted = make_app(settings())
    visitor(restarted, user_agent="Browser A").get("/")
    restarted.state.gui.close()

    assert stats_lines(data_dir) == [{**expected, "visitors": 4, "page_views": 6}]


def test_an_unknown_event_is_not_a_total(make_app, visitor):
    response = visitor(make_app(settings())).post("/api/stats/visit")

    document = response.json()
    assert response.status_code == 404
    ERROR.validate(document)
    assert document["code"] == "not_found"
    assert document["details"]["reason"] == "no_total"
    assert document["details"]["allowed"] == ["station", "download"]


# --- a GUI that is not public ---------------------------------------------------------


def test_a_gui_that_is_not_public_counts_and_limits_nothing_but_logs_its_requests(
    make_app, visitor, tmp_path
):
    logs = tmp_path / "logs"
    app = make_app(
        settings(operator=None, limit=1, window=60),
        log=ServerLog("hydrolog", "1", logs),
    )
    client = visitor(app)

    responses = [
        client.post("/api/stats/station"),
        client.post("/api/stats/download"),
        client.get("/"),
        client.get("/api/terms"),
        client.get("/api/terms"),
    ]
    app.state.gui.close()

    assert [r.status_code for r in responses] == [204, 204, 200, 200, 200]
    records = log_records(logs)
    assert [(r["method"], r["path"], r["status"]) for r in records] == [
        ("POST", "/api/stats/station", 204),
        ("POST", "/api/stats/download", 204),
        ("GET", "/", 200),
        ("GET", "/api/terms", 200),
        ("GET", "/api/terms", 200),
    ]
    assert not (tmp_path / "data" / "hydrolog" / "stats.jsonl").exists()


def test_without_a_server_log_the_app_logs_no_request(make_app, visitor, tmp_path):
    client = visitor(make_app(settings()))

    assert client.get("/").status_code == 200
    assert not any(tmp_path.rglob("access-*.jsonl"))
