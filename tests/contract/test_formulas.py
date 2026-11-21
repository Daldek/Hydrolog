"""The formulas keep the computation standard (Nogat CMP): specs, documents, tests.

Every Tier A formula is declared by a spec (``hydrolog._formulas.specs()``); its
function, docstring, evidence and reference cases keep the standard
(``spec_problems``, CMP-2.6, CMP-2.7, CMP-5.1, CMP-6.5); the documents generated from
the specs are fresh (CMP-2.6, DEV-10.4) and the cards follow Nogat's schema; the
tests of the formulas compare numbers with explicit tolerances (CMP-6.8).
"""

import importlib
import importlib.util
import json
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from hydrolog._formulas import constraint_ranges, specs
from hydrolog.nogat_formulas import FormulaSpec, card, spec_problems, tolerance_problems

from . import _nogat

FORMULA_TESTS = sorted((_nogat.ROOT / "tests").rglob("test_formulas_*.py"))
"""The test files of the formulas: the generated and reference-case tests of each
family (``tests/unit/test_formulas_<family>.py``)."""


def _generator() -> ModuleType:
    found = importlib.util.spec_from_file_location(
        "generate_formulas", _nogat.ROOT / "scripts" / "generate_formulas.py"
    )
    assert found is not None and found.loader is not None
    module = importlib.util.module_from_spec(found)
    found.loader.exec_module(module)
    return module


def _function(spec: FormulaSpec) -> Callable[..., object]:
    """Return the function a spec declares, by its import path."""
    parts = spec.function.split(".")
    for end in range(len(parts) - 1, 0, -1):
        try:
            found: Any = importlib.import_module(".".join(parts[:end]))
        except ModuleNotFoundError:
            continue
        for name in parts[end:]:
            found = getattr(found, name)
        return found  # type: ignore[no-any-return]
    raise AssertionError(f"{spec.function} cannot be imported")


def test_the_generated_documents_are_fresh():
    assert _generator()._stale() == []


@pytest.mark.parametrize("spec", specs(), ids=lambda spec: spec.name)
def test_the_spec_and_its_function_keep_the_standard(spec: FormulaSpec):
    assert spec_problems(spec, _function(spec), root=_nogat.ROOT) == []


@pytest.mark.parametrize("spec", specs(), ids=lambda spec: spec.name)
def test_the_card_follows_nogats_schema(spec: FormulaSpec):
    schema = json.loads(
        (_nogat.SCHEMAS / "card-1.schema.json").read_text(encoding="utf-8")
    )
    data = card(spec)
    committed = _nogat.ROOT / "formulas" / f"{spec.name}.toml"

    Draft202012Validator(schema).validate(data)
    assert tomllib.loads(committed.read_text(encoding="utf-8")) == data


def test_spec_names_are_unique():
    names = [spec.name for spec in specs()]

    assert len(names) == len(set(names))


def test_every_applicability_constraint_names_the_range_its_notice_gives():
    """A violated applicability constraint is issued as ``outside_applicability`` of
    the quantity it bounds, declared by ``hydrolog._formulas.constraint_range``."""
    declared = constraint_ranges()
    undeclared = [
        f"{spec.name}.{constraint.name}"
        for spec in specs()
        for constraint in spec.constraints
        if constraint.cls == "applicability"
        and (spec.name, constraint.name) not in declared
    ]

    assert undeclared == []


@pytest.mark.parametrize(
    "path", FORMULA_TESTS, ids=lambda path: str(path.relative_to(_nogat.ROOT))
)
def test_the_tests_of_a_formula_state_their_tolerances(path: Path):
    assert tolerance_problems(path.read_text(encoding="utf-8"), str(path)) == []
