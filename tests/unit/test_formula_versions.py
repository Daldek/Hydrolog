"""The versions of the formulas behind a result (Nogat CMP-2.8)."""

from hydrolog._formula_versions import record, recording
from hydrolog.catalog.envelope import CommandResult


def test_a_formula_is_recorded_in_every_block_around_it():
    with recording() as outer:
        record("kirpich", 1)
        with recording() as inner:
            record("nrcs", 2)

    assert inner == {"nrcs": 2}
    assert outer == {"kirpich": 1, "nrcs": 2}


def test_nothing_is_recorded_outside_a_block():
    record("kirpich", 1)

    with recording() as found:
        pass

    assert found == {}


def test_the_envelope_carries_the_versions_sorted_and_only_when_a_formula_ran():
    plain = CommandResult(
        command="tc kirpich", inputs={}, result={}, result_schema="hydrolog-x/1"
    )
    versioned = CommandResult(
        command="tc kirpich",
        inputs={},
        result={},
        result_schema="hydrolog-x/1",
        formula_versions={"nrcs": 2, "kirpich": 1},
    )

    assert "formula_versions" not in plain.to_dict()
    assert list(versioned.to_dict()["formula_versions"].items()) == [
        ("kirpich", 1),
        ("nrcs", 2),
    ]
