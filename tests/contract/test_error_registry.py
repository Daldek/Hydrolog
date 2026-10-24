"""The error module is generated from the vendored Nogat registry (ERR-3)."""

import importlib.util
import json
from types import ModuleType

import pytest
from jsonschema import Draft202012Validator

from hydrolog import _errors
from hydrolog.exceptions import (
    ERROR_CODES,
    CalculationError,
    ConflictError,
    ForbiddenPathError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
    error_document,
)

from . import _nogat

REGISTRY = _nogat.SCHEMAS / "error_registry.json"


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_errors", _nogat.ROOT / "scripts" / "generate_errors.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_error_module_equals_the_generator_output():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    generated = _generator().render(registry)

    module = _nogat.ROOT / "src" / "hydrolog" / "_errors.py"
    assert module.read_text(encoding="utf-8") == generated


def test_error_module_carries_every_code_and_outcome_of_the_registry():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert [c.code for c in _errors.CODES] == [e["code"] for e in registry["errors"]]
    assert {
        o["status"]: o["exit_code"] for o in registry["outcomes"]
    } == _errors.OUTCOMES


def test_codes_of_hydrolog_have_the_exit_codes_and_titles_of_the_registry():
    for code, spec in ERROR_CODES.items():
        entry = _errors.BY_CODE[code]

        assert spec.exit_code == entry.exit_code
        assert spec.title_en == entry.title
        assert spec.title == entry.title_pl


@pytest.mark.parametrize("name", _nogat.NAMES)
def test_vendored_schema_is_a_valid_json_schema(name):
    Draft202012Validator.check_schema(_nogat.load(name))


def test_vendored_error_schema_lists_the_registry_codes():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    schema = _nogat.load("error-1")

    assert schema["$defs"]["code"]["enum"] == [e["code"] for e in registry["errors"]]


@pytest.mark.parametrize(
    "exc",
    [
        InvalidParameterError("bad", details={"option": "cn", "reason": "maximum"}),
        InvalidParameterError("bad", hint="Use 0-100."),
        NotFoundError("missing", details={"path": "x.csv"}),
        ConflictError("exists", details={"reason": "output_exists", "paths": ["a"]}),
        MissingDependencyError("extra", hint="uv add 'hydrolog[raster]'"),
        InputDataError("malformed"),
        OutputError("not writable", details={"reason": "output_unwritable"}),
        ForbiddenPathError("outside"),
        CalculationError("no convergence"),
        RuntimeError("bug"),
        FileNotFoundError(2, "No such file", "x"),
    ],
)
@pytest.mark.parametrize("lang", ["en", "pl"])
def test_error_documents_validate_against_the_error_schema(exc, lang):
    document = error_document(exc, command="tc kirpich", lang=lang)

    _nogat.validator("error-1").validate(document)
    assert document["exit_code"] == _errors.BY_CODE[document["code"]].exit_code
