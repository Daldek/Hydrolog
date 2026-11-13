"""The regulamin of a public GUI: the kit's template filled as Nogat's README says.

Nogat ``design/README.md`` (DEV-15.7): blocks first (a listed block keeps its lines
without its markers, any other goes with them), then fields (HTML-escaped; every one
needs a value, only ``processor_transfer``, ``processor_cookie`` and ``mail_transfer``
may be empty).
"""

import re
import tomllib
from pathlib import Path

import pytest

from hydrolog.gui._terms import (
    OPERATOR_FIELDS,
    OPTIONAL,
    PROJECT,
    TEMPLATE,
    TermsError,
    fill,
    load_terms,
)

ROOT = Path(__file__).resolve().parents[3]
SMALL = """<h1>{{service_name}}</h1>
<!-- block: imgw -->
<p>IMGW-PIB</p>
<!-- /block -->
<!-- block: pmaxtp -->
<p>PMAXTP</p>
<!-- /block -->
<!-- block: chmi -->
<p>CHMI</p>
<!-- /block -->
<!-- block: osm -->
<p>OSM</p>
<!-- /block -->



<p>{{processor_transfer}}</p>
"""
VALUES = {"service_name": "Hydrolog", "processor_transfer": "Bez transferu."}
OPERATOR_TOML = """
[nogat.operator]
name = "Jan Kowalski"
email = "operator@hydrolog.example"
terms_effective = 2026-11-20
processor = "Cloudflare, Inc."
processor_transfer = ""
processor_cookie = ""
mail_provider = "iCloud Mail (Apple)"
mail_transfer = ""
"""
SERVICE_URL = "https://hydrolog.example/"


def operator(**changes):
    """Return ``[nogat.operator]`` as ``tomllib`` reads it, with ``changes``."""
    table = tomllib.loads(OPERATOR_TOML)["nogat"]["operator"]
    table.update(changes)
    return table


# --- fill -----------------------------------------------------------------------------


def test_listed_blocks_stay_without_their_markers_and_the_others_go():
    page = fill(SMALL, VALUES, ["chmi"])

    assert "<p>CHMI</p>" in page
    for dropped in ("IMGW-PIB", "PMAXTP", "OSM"):
        assert dropped not in page
    assert "<!--" not in page


def test_the_values_are_html_escaped_and_trimmed():
    values = {**VALUES, "service_name": " <b>\"Hydro\" & 'log'</b> "}

    page = fill(SMALL, values, [])

    assert page.startswith(
        "<h1>&lt;b&gt;&quot;Hydro&quot; &amp; &#x27;log&#x27;&lt;/b&gt;</h1>\n"
    )


@pytest.mark.parametrize("value", ["", "   ", "\n"])
def test_an_empty_field_that_is_not_optional_is_refused_by_name(value):
    with pytest.raises(TermsError, match="service_name"):
        fill(SMALL, {**VALUES, "service_name": value}, [])


@pytest.mark.parametrize("missing", ["service_name", "processor_transfer"])
def test_a_missing_field_is_refused_by_name_even_an_optional_one(missing):
    values = {name: value for name, value in VALUES.items() if name != missing}

    with pytest.raises(TermsError, match=missing):
        fill(SMALL, values, [])


def test_every_missing_field_is_named():
    with pytest.raises(TermsError, match="processor_transfer, service_name"):
        fill(SMALL, {}, [])


def test_an_optional_field_may_be_empty():
    page = fill(SMALL, {**VALUES, "processor_transfer": ""}, [])

    assert page.endswith("<p></p>\n")


def test_a_value_that_leaves_a_placeholder_is_refused():
    with pytest.raises(TermsError):
        fill(SMALL, {**VALUES, "service_name": "{{service_url}}"}, [])


@pytest.mark.parametrize("listed", [[], ["imgw", "pmaxtp", "chmi"], ["osm"]])
def test_three_or_more_newlines_become_one_blank_line(listed):
    assert "\n\n\n" not in fill(SMALL, VALUES, listed)


# --- load_terms: the kit's template ---------------------------------------------------


def test_the_kits_template_is_filled_from_a_toml_operator():
    terms = load_terms(operator(), SERVICE_URL)

    page = terms.page.decode("utf-8")
    assert terms.operator_email == "operator@hydrolog.example"
    assert "obowiązuje od 2026-11-20" in page
    assert "Serwis prowadzi Jan Kowalski" in page
    assert f"pod adresem {SERVICE_URL}" in page
    assert "{{" not in page
    assert "<!--" not in page.split("</head>", 1)[1]
    assert "<h3>IMGW-PIB: dane publiczne</h3>" in page
    assert "<h3>ČHMÚ</h3>" in page
    assert "<h3>OpenStreetMap</h3>" not in page


@pytest.mark.parametrize(
    ("changes", "named"),
    [
        ({"email": 5}, "operator_email"),
        ({"terms_effective": 20261120}, "terms_effective"),
        (
            {"terms_effective": tomllib.loads("t = 2026-11-20T10:00:00")["t"]},
            "terms_effective",
        ),
        ({"processor": " "}, "processor"),
        ({"mail_provider": None}, "mail_provider"),
    ],
    ids=["email-number", "date-number", "date-time", "blank-processor", "no-mail"],
)
def test_an_unusable_operator_value_is_named(changes, named):
    with pytest.raises(TermsError, match=named):
        load_terms(operator(**changes), SERVICE_URL)


def test_a_date_as_text_is_used_as_written():
    page = load_terms(operator(terms_effective="2026-12-01"), SERVICE_URL).page

    assert "obowiązuje od 2026-12-01" in page.decode("utf-8")


@pytest.mark.parametrize("service_url", [None, "", "  "])
def test_without_the_gui_address_there_is_no_regulamin(service_url):
    with pytest.raises(TermsError, match="service_url"):
        load_terms(operator(), service_url)


def test_a_template_that_cannot_be_read_is_a_terms_error(tmp_path):
    with pytest.raises(TermsError):
        load_terms(operator(), SERVICE_URL, template=tmp_path / "absent.html")


def test_the_template_needs_exactly_the_fields_hydrolog_and_the_operator_give():
    """A kit update that adds or renames a field breaks here, not in production."""
    placeholders = set(
        re.findall(r"\{\{([a-z][a-z0-9_]*)\}\}", TEMPLATE.read_text(encoding="utf-8"))
    )

    assert placeholders == {*PROJECT, "service_url", *OPERATOR_FIELDS}
    assert set(OPTIONAL) <= set(OPERATOR_FIELDS)


def test_the_software_licence_is_the_license_of_pyproject():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    assert PROJECT["software_licence"] == project["license"]
