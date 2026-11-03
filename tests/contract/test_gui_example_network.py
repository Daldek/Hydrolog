"""The example network of „Sieć i trasowanie” is Hydrolog's own (GUI plan D17, S4).

``web/examples/siec.json``, which a first visit of the section opens, is the network of
``hydrolog.testing.example_network_document()`` and a valid ``hydrolog-network/1``
document, so the GUI shows what the library tests.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from hydrolog.testing import example_network_document

ROOT = Path(__file__).resolve().parents[2] / "src" / "hydrolog"
EXAMPLE = ROOT / "gui" / "web" / "examples" / "siec.json"
SCHEMA = ROOT / "schemas" / "hydrolog-network-1.schema.json"


def test_the_shipped_example_is_the_testing_modules_network() -> None:
    shipped = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    assert shipped == example_network_document()


def test_the_shipped_example_is_a_valid_network_document() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    shipped = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    assert [
        error.message for error in Draft202012Validator(schema).iter_errors(shipped)
    ] == []
