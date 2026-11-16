"""Tests of the rainfall sources: design storms, series, their documents, registries.

The reference of a design storm is the generator of its shape: the storm cut at a step
is what ``generate`` gives for that step. A series is the depths it was made of, at the
step it was made at, and nothing is resampled. A document says what an object says, so
an object and its document are the same whether a default was written or not; a kind is
a registry entry, nothing else.
"""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    HietogramResult,
    TriangularHietogram,
)
from hydrolog.routing import (
    HIETOGRAMS,
    RAINFALL_KINDS,
    DesignStorm,
    RainfallSeries,
    RainfallSource,
)
from hydrolog.routing.rainfall import rainfall_from_document

from ._routing_extensions import Constant, Growing

SHAPES = {
    "block": BlockHietogram(),
    "triangular": TriangularHietogram(peak_position=0.4),
    "beta": BetaHietogram(alpha=3.0, beta=4.0),
    "euler_ii": EulerIIHietogram(),
}


def refused(build) -> InvalidParameterError:
    with pytest.raises(InvalidParameterError) as caught:
        build()
    return caught.value


class TestADesignStorm:
    @pytest.mark.parametrize("name", SHAPES)
    @pytest.mark.parametrize("step", [5.0, 10.0, 20.0])
    def test_it_is_cut_at_the_step_as_its_generator_cuts_it(self, name, step):
        shape = SHAPES[name]
        storm = DesignStorm(45.0, 60.0, shape)

        cut = storm.hyetograph(step)

        expected = shape.generate(total_mm=45.0, duration_min=60.0, timestep_min=step)
        np.testing.assert_array_equal(cut.intensities_mm, expected.intensities_mm)
        np.testing.assert_array_equal(cut.times_min, expected.times_min)
        assert (cut.total_mm, cut.duration_min, cut.timestep_min) == (45.0, 60.0, step)

    def test_it_takes_any_step_and_a_source_with_the_protocol_is_what_it_is(self):
        storm = DesignStorm(45.0, 60.0, BlockHietogram())

        assert storm.timestep_min is None
        assert isinstance(storm, RainfallSource)
        assert not isinstance(object(), RainfallSource)

    def test_it_lasts_what_it_lasts_and_is_not_stretched(self):
        storm = DesignStorm(45.0, 60.0, BlockHietogram())

        assert storm.hyetograph(10.0, duration_min=60.0).n_steps == 6
        error = refused(lambda: storm.hyetograph(10.0, duration_min=120.0))
        assert error.details["reason"] == "duration_mismatch"
        assert error.details["expected"] == 60.0 and error.details["value"] == 120.0

    def test_a_step_longer_than_the_storm_is_the_error_of_the_generator(self):
        storm = DesignStorm(45.0, 30.0, BlockHietogram())

        error = refused(lambda: storm.hyetograph(60.0))
        assert "cannot exceed" in str(error)

    @pytest.mark.parametrize(
        ("total", "duration", "shape", "option", "reason"),
        [
            (0.0, 60.0, BlockHietogram(), "total_mm", "exclusive_minimum"),
            (-3.0, 60.0, BlockHietogram(), "total_mm", "exclusive_minimum"),
            (45.0, 0.0, BlockHietogram(), "duration_min", "exclusive_minimum"),
            ("45", 60.0, BlockHietogram(), "total_mm", "type"),
            (float("inf"), 60.0, BlockHietogram(), "total_mm", "not_finite"),
            (45.0, 60.0, "euler_ii", "hietogram", "type"),
            (45.0, 60.0, EulerIIHietogram, "hietogram", "type"),
        ],
    )
    def test_a_value_that_is_not_valid_is_refused_by_its_option(
        self, total, duration, shape, option, reason
    ):
        error = refused(lambda: DesignStorm(total, duration, shape))

        assert error.details["option"] == option
        assert error.details["reason"] == reason

    def test_it_says_what_it_uses_and_where_each_value_came_from(self):
        storm = DesignStorm(45.0, 60.0, TriangularHietogram())
        listed = {p.name: p for p in storm.describe()}
        run = {p.name: p for p in storm.describe(storm.hyetograph(10.0))}

        assert [(p.name, p.value, p.unit, p.source) for p in listed.values()] == [
            ("total_mm", 45.0, "mm", "given"),
            ("duration_min", 60.0, "min", "given"),
            ("hietogram_type", "triangular", None, "given"),
            ("peak_position", 0.5, None, "default"),
        ]
        assert run["timestep_min"].value == 10.0
        assert (run["timestep_min"].unit, run["timestep_min"].source) == (
            "min",
            "computed",
        )
        shaped = DesignStorm(45.0, 60.0, TriangularHietogram(peak_position=0.4))
        assert {p.name: p.source for p in shaped.describe()}["peak_position"] == "given"


class TestASeries:
    def test_it_is_the_depths_at_the_step_it_was_made_at(self):
        record = RainfallSeries([0.0, 4.0, 11.0, 6.0, 1.0], timestep_min=10.0)

        cut = record.hyetograph(10.0)

        assert isinstance(cut, HietogramResult)
        np.testing.assert_array_equal(cut.intensities_mm, [0.0, 4.0, 11.0, 6.0, 1.0])
        np.testing.assert_array_equal(cut.times_min, [10.0, 20.0, 30.0, 40.0, 50.0])
        assert (cut.total_mm, cut.duration_min, cut.timestep_min) == (22.0, 50.0, 10.0)
        assert record.timestep_min == 10.0 and record.duration_min == 50.0

    def test_it_is_not_resampled(self):
        record = RainfallSeries([0.0, 4.0, 11.0], timestep_min=10.0)

        error = refused(lambda: record.hyetograph(5.0))
        assert error.details["reason"] == "timestep_mismatch"
        assert error.details["expected"] == 10.0 and error.details["value"] == 5.0
        assert "not resampled" in str(error.hint)
        assert refused(lambda: record.hyetograph(10.0, duration_min=40.0)).details[
            "reason"
        ] == ("duration_mismatch")

    def test_the_depths_cannot_be_changed_from_outside(self):
        depths = np.array([1.0, 2.0, 3.0])
        record = RainfallSeries(depths, timestep_min=5.0)

        depths[0] = 99.0
        with pytest.raises(ValueError):
            record.depths_mm[1] = 99.0
        assert record.depths_mm.tolist() == [1.0, 2.0, 3.0]
        cut = record.hyetograph(5.0)
        cut.intensities_mm[0] = 99.0
        assert record.depths_mm[0] == 1.0

    @pytest.mark.parametrize(
        ("depths", "reason", "index"),
        [
            ([], "too_short", None),
            ([[1.0, 2.0]], "too_short", None),
            ([1.0, -0.5, 2.0], "negative", 1),
            ([1.0, 2.0, float("nan")], "not_finite", 2),
            ([float("inf")], "not_finite", 0),
        ],
    )
    def test_a_depth_that_is_not_valid_is_refused_with_its_index(
        self, depths, reason, index
    ):
        error = refused(lambda: RainfallSeries(depths, timestep_min=5.0))

        assert error.details["option"] == "depths_mm"
        assert error.details["reason"] == reason
        assert error.details.get("index") == index

    def test_the_depths_must_be_numbers_and_the_step_positive(self):
        assert refused(lambda: RainfallSeries(["wet"], 5.0)).details["reason"] == "type"
        error = refused(lambda: RainfallSeries([1.0], timestep_min=0.0))
        assert error.details["option"] == "timestep_min"

    def test_it_says_what_it_uses(self):
        listed = RainfallSeries([2.0, 3.0], timestep_min=15.0).describe()

        assert [(p.name, p.value, p.unit, p.source) for p in listed] == [
            ("timestep_min", 15.0, "min", "given"),
            ("total_mm", 5.0, "mm", "computed"),
            ("duration_min", 30.0, "min", "computed"),
        ]


DESIGN = {
    "kind": "design",
    "hietogram_type": "euler_ii",
    "total_mm": 45.0,
    "duration_min": 60.0,
}
SERIES = {"kind": "series", "depths_mm": [0.0, 4.0, 11.0], "timestep_min": 10.0}


class TestTheDocument:
    @pytest.mark.parametrize("document", [DESIGN, SERIES])
    def test_a_canonical_document_is_read_and_written_back_as_it_is(self, document):
        source = rainfall_from_document(document)

        assert source.to_document() == document

    @pytest.mark.parametrize("name", SHAPES)
    def test_an_object_and_its_document_are_the_same_object(self, name):
        storm = DesignStorm(45.0, 60.0, SHAPES[name])

        again = rainfall_from_document(storm.to_document())

        assert again == storm
        assert again.hyetograph(10.0).intensities_mm.tolist() == (
            storm.hyetograph(10.0).intensities_mm.tolist()
        )

    def test_a_default_is_left_out_of_the_document_and_a_given_value_is_not(self):
        plain = DesignStorm(45.0, 60.0, EulerIIHietogram())
        peaked = DesignStorm(45.0, 60.0, EulerIIHietogram(peak_position=0.5))

        assert "peak_position" not in plain.to_document()
        assert peaked.to_document()["peak_position"] == 0.5
        assert rainfall_from_document({**DESIGN, "peak_position": 0.33}) == plain
        assert plain != peaked

    def test_the_series_of_two_objects_are_compared_by_depths_and_step(self):
        assert RainfallSeries([1.0, 2.0], 5.0) == RainfallSeries([1.0, 2.0], 5.0)
        assert RainfallSeries([1.0, 2.0], 5.0) != RainfallSeries([1.0, 2.5], 5.0)
        assert RainfallSeries([1.0, 2.0], 5.0) != RainfallSeries([1.0, 2.0], 10.0)

    @pytest.mark.parametrize(
        ("document", "reason", "facts"),
        [
            ([1, 2], "type", {}),
            ({}, "missing_field", {"field": "kind"}),
            (
                {"kind": "radar"},
                "unknown_kind",
                {"field": "kind", "value": "radar", "allowed": ["design", "series"]},
            ),
            (
                {**DESIGN, "hietogram_type": None},
                "missing_field",
                {"field": "hietogram_type"},
            ),
            (
                {**DESIGN, "hietogram_type": "gauss"},
                "unknown_hietogram_type",
                {"field": "hietogram_type", "value": "gauss"},
            ),
            (
                {**DESIGN, "alpha": 2.0},
                "unknown_field",
                {"field": "alpha"},
            ),
            (
                {**DESIGN, "hietogram_type": "beta", "peak_position": 0.3},
                "unknown_field",
                {"field": "peak_position"},
            ),
            (
                {k: v for k, v in DESIGN.items() if k != "total_mm"},
                "missing_field",
                {"field": "total_mm"},
            ),
            ({**DESIGN, "total_mm": -1}, "exclusive_minimum", {"option": "total_mm"}),
            (
                {**DESIGN, "hietogram_type": "beta", "alpha": -1},
                "invalid_value",
                {"field": "alpha"},
            ),
            ({**SERIES, "timestep": 10}, "unknown_field", {"field": "timestep"}),
            (
                {k: v for k, v in SERIES.items() if k != "depths_mm"},
                "missing_field",
                {"field": "depths_mm"},
            ),
            ({**SERIES, "depths_mm": [1, -1]}, "negative", {"option": "depths_mm"}),
        ],
    )
    def test_a_document_that_is_wrong_says_what_and_where(
        self, document, reason, facts
    ):
        error = refused(lambda: rainfall_from_document(document))

        assert error.details["reason"] == reason
        assert {key: error.details.get(key) for key in facts} == facts

    def test_the_kinds_and_the_shapes_are_what_the_package_has(self):
        assert RAINFALL_KINDS.names == ("design", "series")
        assert HIETOGRAMS.names == ("block", "triangular", "beta", "euler_ii")
        assert RAINFALL_KINDS["series"] is RainfallSeries
        assert HIETOGRAMS["euler_ii"] is EulerIIHietogram
        assert HIETOGRAMS.name_of(EulerIIHietogram()) == "euler_ii"


class TestExtending:
    def test_a_new_kind_of_rainfall_is_a_registry_entry_and_nothing_else(
        self, monkeypatch
    ):
        monkeypatch.setitem(RAINFALL_KINDS._classes, "constant", Constant)

        source = rainfall_from_document(
            {"kind": "constant", "depth_mm": 2.0, "steps": 4}
        )

        assert isinstance(source, Constant) and isinstance(source, RainfallSource)
        assert source.hyetograph(10.0).total_mm == 8.0
        assert rainfall_from_document(source.to_document()).steps == 4

    def test_a_class_that_cannot_be_read_and_written_is_not_registered(self):
        class Unreadable:
            kind = "unreadable"

        with pytest.raises(TypeError, match="no from_document, to_document"):
            RAINFALL_KINDS.register(Unreadable)
        assert "unreadable" not in RAINFALL_KINDS

    def test_a_new_shape_is_named_by_its_type_and_its_arguments(self, monkeypatch):
        monkeypatch.setitem(HIETOGRAMS._classes, "late", Growing)

        storm = rainfall_from_document(
            {**DESIGN, "hietogram_type": "late", "growth": 2.0}
        )

        assert isinstance(storm, DesignStorm)
        weights = np.arange(1, 7) ** 2.0
        np.testing.assert_allclose(
            storm.hyetograph(10.0).intensities_mm, 45.0 * weights / weights.sum()
        )
        assert storm.to_document()["growth"] == 2.0
        assert "growth" not in DesignStorm(45.0, 60.0, Growing()).to_document()
        names = {p.name: p.value for p in storm.describe()}
        assert names["hietogram_type"] == "late" and names["growth"] == 2.0

    def test_a_shape_that_is_not_registered_is_described_but_not_written(self):
        storm = DesignStorm(45.0, 60.0, Growing())

        assert {p.name: p.value for p in storm.describe()}["hietogram_type"] == (
            "Growing"
        )
        error = refused(storm.to_document)
        assert error.details["reason"] == "unregistered"
