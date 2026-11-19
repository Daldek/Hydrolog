"""The handbook's fragments come from the formula specs (Nogat CMP-2.7, DEV-10.4).

``docs/podrecznik/`` shows the equations, constants and ranges of the formulas only in
fragments that ``scripts/generate_handbook.py`` generates from the specs: they are
fresh, each names a formula, table or index that exists and none is left empty, and the
Polish texts of every formula shown are complete and translate the spec as it is.
"""

import copy
import importlib.util
import math
import tomllib
from fractions import Fraction
from types import ModuleType
from typing import Any

import pytest

from hydrolog._formulas import specs, tier_b
from hydrolog.nogat_formulas import Range

from . import _nogat

HANDBOOK = _nogat.ROOT / "docs" / "podrecznik"


def _generator() -> ModuleType:
    found = importlib.util.spec_from_file_location(
        "generate_handbook", _nogat.ROOT / "scripts" / "generate_handbook.py"
    )
    assert found is not None and found.loader is not None
    module = importlib.util.module_from_spec(found)
    found.loader.exec_module(module)
    return module


GENERATOR = _generator()


def _polish() -> dict[str, Any]:
    return tomllib.loads((HANDBOOK / "_specs_pl.toml").read_text(encoding="utf-8"))


def _book(text: str, polish: dict[str, Any] | None = None) -> Any:
    """Return a handbook of one chapter with the project's specs and Polish texts."""
    return GENERATOR.Handbook(
        files={HANDBOOK / "01-proba.md": text},
        polish=_polish() if polish is None else polish,
        formulas={spec.name: spec for spec in specs()},
        rules={rule.name: rule for rule in tier_b()},
        commands=[],
    )


def _read_back(text: str) -> float | Fraction:
    """Return the value of a number as the handbook prints it."""
    plain = text.replace("\u2212", "-").replace("\u00a0", "").replace(",", ".")
    if plain.endswith("∞"):
        return -math.inf if plain.startswith("-") else math.inf
    if "/" in plain:
        return Fraction(plain)
    mantissa, _, power = plain.partition("·10")
    exponent = power.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-"))
    return float(f"{mantissa}e{exponent}" if exponent else mantissa)


def test_the_fragments_of_the_handbook_are_fresh():
    assert GENERATOR._stale() == []


def test_every_fragment_names_a_formula_table_or_index_and_is_well_marked():
    book = GENERATOR.handbook()

    assert book.marker_problems() == []
    assert book.name_problems() == []


def test_no_fragment_of_the_handbook_is_left_empty():
    book = GENERATOR.handbook()
    empty = []
    for fragment in book.all_fragments():
        lines = book.files[fragment.path].split("\n")
        if not "".join(lines[fragment.start + 1 : fragment.end]).strip():
            empty.append(fragment.where())

    assert book.all_fragments()
    assert empty == []


def test_the_polish_texts_are_complete_and_translate_the_specs_as_they_are():
    assert GENERATOR.handbook().polish_problems() == []


def test_every_number_a_frame_prints_reads_back_as_the_specs_value():
    values: list[float | Fraction] = []
    for spec in specs():
        for holder in (*spec.variables, *spec.outputs):
            for rng in (holder.physical, getattr(holder, "applicability", None)):
                if isinstance(rng, Range):
                    values += [rng.low, rng.high]
            typical = getattr(holder, "typical", None)
            if typical is not None:
                values += [typical.low, typical.high]
        values += [constant.value for constant in spec.constants]
    values += [c.value for rule in tier_b() for c in rule.constants]

    wrong = [v for v in values if _read_back(GENERATOR.number(v)) != v]

    assert wrong == []


def test_an_unknown_formula_stops_the_generator():
    book = _book("<!-- spec:no_such_formula -->\n<!-- /spec:no_such_formula -->\n")

    with pytest.raises(GENERATOR.HandbookError, match="no_such_formula"):
        book.documents()


def test_a_formula_without_polish_texts_stops_the_generator():
    polish = _polish()
    del polish["formulas"]["kirpich"]
    book = _book("<!-- spec:kirpich -->\n<!-- /spec:kirpich -->\n", polish)

    assert any("--template kirpich" in problem for problem in book.polish_problems())


def test_a_changed_spec_or_number_makes_its_polish_texts_stale():
    polish = _polish()
    stale = copy.deepcopy(polish)
    stale["formulas"]["kirpich"]["en_sha256"] = "0" * 64
    renumbered = copy.deepcopy(polish)
    conventions = renumbered["formulas"]["kirpich"]["conventions"]
    conventions[0] += " 7"
    text = "<!-- spec:kirpich -->\n<!-- /spec:kirpich -->\n"

    assert any("en_sha256" in p for p in _book(text, stale).polish_problems())
    assert any("adds 7" in p for p in _book(text, renumbered).polish_problems())


def test_markers_in_a_code_fence_are_text_and_broken_markers_are_refused():
    fenced = _book("```markdown\n<!-- spec:no_such_formula -->\n```\n")
    unclosed = _book("<!-- spec:kirpich -->\ntext\n")
    malformed = _book("<!-- spec: kirpich -->\n<!-- /spec: kirpich -->\n")

    assert fenced.problems() == [] and fenced.all_fragments() == []
    assert any("never closed" in p for p in unclosed.marker_problems())
    assert any("malformed" in p for p in malformed.marker_problems())


def test_a_filled_frame_is_refilled_from_the_spec():
    text = "a\n<!-- spec:scs_cn_retention -->\nold\n<!-- /spec:scs_cn_retention -->\nb"
    done = _book(text).documents()[HANDBOOK / "01-proba.md"]

    assert "\nold\n" not in done
    assert done.startswith("a\n<!-- spec:scs_cn_retention -->\n")
    assert done.endswith("<!-- /spec:scs_cn_retention -->\nb")
    assert _book(done).documents()[HANDBOOK / "01-proba.md"] == done


def _unit_key(unit: str) -> str:
    """Return a unit without its typesetting, to compare a printed one with a spec's."""
    for typeset, plain in (
        ("$", ""),
        ("\\mathrm", ""),
        ("\\text{ na }", "per"),
        (" na ", "per"),
        ("{,}", "."),
        ("\\,", ""),
        ("\\%", "%"),
        ("degC", "°C"),
        ("–", "-"),
    ):
        unit = unit.replace(typeset, plain)
    unit = unit.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-"))
    return "".join(c for c in unit if c not in " ^(){}")


def test_every_unit_a_frame_prints_reads_back_as_the_specs_unit():
    words = {u for u, entry in _polish()["units"].items() if "symbol" in entry}
    units = {
        item.unit
        for spec in specs()
        for item in (*spec.variables, *spec.outputs, *spec.constants)
    } | {c.unit for rule in tier_b() for c in rule.constants}

    wrong = [
        unit
        for unit in sorted(units - words)
        if _unit_key(GENERATOR.unit_symbol(unit)) != _unit_key(unit)
    ]

    assert wrong == []
