"""Tests for the analysis operations and their catalog declarations.

Groups: ``morphometry``, ``network``, ``stats``, ``hydrometrics``, ``soil`` (and
``report``, see the end of the module). Every operation is compared with the direct use
of the library class it composes, run through ``run_command`` where the envelope
(notices, files, JSON) matters, and driven with the file fixtures of
``tests/fixtures``.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import Command, run_command
from hydrolog.catalog.envelope import sha256_file
from hydrolog.catalog.groups import collect_commands
from hydrolog.catalog.groups.hydrograph import GENERATE_ONE_OF, GENERATE_OPTIONS
from hydrolog.catalog.inputs import load_series, read_table
from hydrolog.exceptions import (
    CalculationError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
)
from hydrolog.hydrometrics import RatingCurve, WaterLevelFrequency
from hydrolog.morphometry import WatershedParameters
from hydrolog.network import (
    NetworkStatistics,
    OrderingMethod,
    StreamNetwork,
    StreamSegment,
)
from hydrolog.operations import (
    hydrometrics,
    network,
    report,
    soil,
    stats,
    tc,
)
from hydrolog.operations.hydrograph import compute_hydrograph
from hydrolog.soil import classify_usda_texture, texture_to_hsg
from hydrolog.statistics import (
    FloodFrequencyAnalysis,
    LowFlowAnalysis,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
    mann_kendall_test,
)
from hydrolog.time import ConcentrationTime

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
IMGW_EXPORT = FIXTURES / "imgwtools_series_export.csv"
DAILY_FLOWS = FIXTURES / "daily_flows_3y.csv"
ANNUAL_MAXIMA = FIXTURES / "annual_maxima.csv"
NETWORK_SEGMENTS = FIXTURES / "network_segments.csv"
RATING_PAIRS = FIXTURES / "rating_curve_pairs.csv"
WATERSHED_FILE = FIXTURES / "watershed_example.json"

GROUPS = ("morphometry", "network", "stats", "hydrometrics", "soil", "report")


def _declared(name: str) -> Command:
    """Declaration of a command, bound to its operation module.

    The ``function`` path is pointed at ``hydrolog.operations.<group>`` so these tests
    do not depend on how ``hydrolog.operations`` re-exports the functions.
    """
    group = name.split(" ", 1)[0]
    module = importlib.import_module(f"hydrolog.catalog.groups.{group}")
    command = next(item for item in module.COMMANDS if item.name == name)
    function = command.function.replace(
        "hydrolog.operations:", f"hydrolog.operations.{group}:"
    )
    return dataclasses.replace(command, function=function)


def run(name: str, **options):
    """Run a catalog command by name and return its ``CommandResult``."""
    return run_command(_declared(name), options)


def _daily(path: Path = DAILY_FLOWS):
    """The daily series of a fixture file (values and dates)."""
    return load_series(input_file=path, value_column="Q", date_column="date")


def _json_roundtrip(result) -> dict:
    """A result as the plain JSON document a client receives."""
    return json.loads(result.to_json())


def _boundary_series():
    """Four hydrological years of daily values with peaks on the 31 Oct / 1 Nov edge.

    Baseline 5.0 from 2019-11-01 to 2023-10-31. Peaks (high) and dips (low) sit on the
    last day of one hydrological year and the first day of the next, so the annual
    extremes tell the Nov-Oct hydrological year from the calendar year.
    """
    dates = np.arange(
        np.datetime64("2019-11-01"), np.datetime64("2023-11-01"), dtype="datetime64[D]"
    )
    values = np.full(len(dates), 5.0)

    def put(day: str, value: float) -> None:
        values[int(np.flatnonzero(dates == np.datetime64(day))[0])] = value

    for day, value in (
        ("2020-10-31", 10.0),  # last day of HY 2020
        ("2020-11-01", 8.0),  # first day of HY 2021
        ("2021-10-31", 6.0),  # last day of HY 2021 (below the 8.0 of the same year)
        ("2021-11-01", 9.0),  # first day of HY 2022
        ("2022-06-15", 7.0),
        ("2022-11-01", 5.5),  # first day of HY 2023
        ("2023-03-01", 5.2),
        ("2020-10-30", 1.0),  # lowest day of HY 2020
        ("2020-11-02", 0.5),  # lowest day of HY 2021
        ("2022-10-31", 0.8),  # lowest day of HY 2022
        ("2022-11-02", 0.9),  # lowest day of HY 2023
    ):
        put(day, value)
    return values.tolist(), [str(day) for day in dates]


# --- declarations of the analysis groups ----------------------------------------------


def _commands_of_groups() -> tuple[Command, ...]:
    return collect_commands(list(GROUPS))


@pytest.mark.parametrize("command", _commands_of_groups(), ids=lambda c: c.name)
class TestDeclarations:
    """The declarations agree with the operations they describe."""

    def test_declared_defaults_equal_the_python_defaults(self, command):
        """An option default is the default of the operation parameter."""
        module, _, attribute = command.function.partition(":")
        group = command.group
        function = getattr(importlib.import_module(f"{module}.{group}"), attribute)
        parameters = inspect.signature(function).parameters
        for option in command.options:
            if option.default is None:
                continue
            python_default = parameters[option.name].default
            assert option.normalize(option.default) == option.normalize(python_default)

    def test_options_without_default_are_optional_or_required_in_python(self, command):
        """Required options are parameters without default; the others have one."""
        module, _, attribute = command.function.partition(":")
        function = getattr(
            importlib.import_module(f"{module}.{command.group}"), attribute
        )
        parameters = inspect.signature(function).parameters
        for option in command.options:
            has_default = parameters[option.name].default is not inspect.Parameter.empty
            assert has_default != option.required, option.name

    def test_examples_run_and_serialize(self, command, tmp_path, monkeypatch):
        """Every example is a valid call that produces a JSON envelope."""
        monkeypatch.chdir(REPO_ROOT)
        bound = _declared(command.name)
        for example in command.examples:
            options = dict(example)
            for option in command.options:
                if option.writes:
                    options[option.name] = str(tmp_path / f"{command.operation_id}.out")
            try:
                result = run_command(bound, options)
            except MissingDependencyError:
                pytest.skip("optional extra [raster] is not installed")
            document = json.loads(result.to_json())
            assert document["status"] == "ok"
            assert document["command"] == command.name
            for record in document["files"]:
                assert record["sha256"] == sha256_file(record["path"])


# --- morphometry ----------------------------------------------------------------------

WATERSHED = {
    "name": "Zlewnia testowa",
    "area_km2": 45.3,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "elevation_mean_m": 310.0,
    "channel_length_km": 14.2,
}


class TestMorphometryWatershed:
    """``morphometry watershed``."""

    def test_indicators_equal_the_classes_of_the_library(self):
        parameters = WatershedParameters.from_dict(WATERSHED)
        geometry = parameters.to_geometry()
        terrain = parameters.to_terrain()
        result = run("morphometry watershed", watershed=WATERSHED).result
        assert result.name == "Zlewnia testowa"
        assert result.geometry == geometry.get_parameters()
        assert result.shape_indicators == geometry.get_shape_indicators()
        assert result.elevation == terrain.get_elevation_parameters()
        assert result.slopes == terrain.get_slope_parameters()

    def test_the_known_values_of_the_shape_indicators(self):
        """Hand-computed Horton, Gravelius and Miller indicators of a 4 x 1 km box."""
        box = {
            "area_km2": 4.0,
            "perimeter_km": 10.0,
            "length_km": 4.0,
            "elevation_min_m": 100.0,
            "elevation_max_m": 140.0,
        }
        result = run("morphometry watershed", watershed=box).result
        assert result.geometry.width_km == pytest.approx(1.0)
        assert result.shape_indicators.form_factor == pytest.approx(0.25)
        assert result.shape_indicators.compactness_coefficient == pytest.approx(
            10.0 / (2.0 * np.sqrt(np.pi * 4.0))
        )
        assert result.shape_indicators.circularity_ratio == pytest.approx(
            4.0 * np.pi * 4.0 / 100.0
        )
        assert result.elevation.relief_m == pytest.approx(40.0)
        assert result.slopes.watershed_slope_m_per_m == pytest.approx(40.0 / 4000.0)

    def test_file_and_inline_object_give_the_same_result(self):
        from_file = run("morphometry watershed", watershed_file=str(WATERSHED_FILE))
        inline = json.loads(WATERSHED_FILE.read_text(encoding="utf-8"))
        from_object = run("morphometry watershed", watershed=inline)
        assert from_file.result == from_object.result
        assert from_file.result.name == "Zlewnia Przykładowa"

    def test_result_is_json(self):
        document = _json_roundtrip(run("morphometry watershed", watershed=WATERSHED))
        assert document["result"]["shape_indicators"]["form_factor"] == pytest.approx(
            45.3 / 12.5**2
        )
        assert document["result"]["elevation"]["relief_m"] == 370.0

    def test_notices_tell_what_was_approximated(self):
        minimal = {
            key: WATERSHED[key]
            for key in (
                "area_km2",
                "perimeter_km",
                "length_km",
                "elevation_min_m",
                "elevation_max_m",
            )
        }
        approximated = run("morphometry watershed", watershed=minimal)
        assert {n.code for n in approximated.notices} == {
            "mean_elevation_approximated",
            "channel_length_defaulted",
        }
        assert approximated.result.elevation.elevation_mean_m == 335.0
        assert approximated.result.slopes.channel_slope_m_per_m == pytest.approx(
            370.0 / 12500.0
        )
        assert run("morphometry watershed", watershed=WATERSHED).notices == ()

    def test_mean_elevation_outside_the_range_is_rejected(self):
        with pytest.raises(InvalidParameterError, match="elevation_mean_m"):
            run(
                "morphometry watershed",
                watershed={**WATERSHED, "elevation_mean_m": 900},
            )

    def test_missing_file_is_not_found(self, tmp_path):
        with pytest.raises(NotFoundError):
            run("morphometry watershed", watershed_file=str(tmp_path / "none.json"))

    def test_absurd_magnitudes_are_a_calculation_error_not_a_crash(self):
        absurd = {
            "area_km2": 1e300,
            "perimeter_km": 1e300,
            "length_km": 1e-300,
            "elevation_min_m": 0,
            "elevation_max_m": 1,
        }
        with pytest.raises(CalculationError) as caught:
            run("morphometry watershed", watershed=absurd)
        assert caught.value.code == "calculation_error"

    def test_incomplete_file_is_a_data_error(self, tmp_path):
        broken = tmp_path / "broken.json"
        broken.write_text(json.dumps({"area_km2": 10.0}), encoding="utf-8")
        with pytest.raises(InputDataError) as caught:
            run("morphometry watershed", watershed_file=str(broken))
        assert caught.value.details["reason"] == "missing_field"


# --- network --------------------------------------------------------------------------


def _segments(table):
    """Library segments of ``(id, upstream, length)`` rows."""
    return [StreamSegment(i, list(up), length_km=length) for i, up, length in table]


FIXTURE_NETWORK = [
    (1, [], 1.2),
    (2, [], 0.8),
    (3, [1, 2], 1.5),
    (4, [], 1.0),
    (5, [], 0.9),
    (6, [4, 5], 1.4),
    (7, [3, 6], 2.2),
    (8, [], 0.7),
    (9, [7, 8], 3.0),
]


def _inline(table):
    return [
        {"segment_id": i, "upstream_ids": list(up), "length_km": length}
        for i, up, length in table
    ]


class TestNetworkStats:
    """``network stats``."""

    @pytest.mark.parametrize("method", ["strahler", "shreve"])
    def test_statistics_equal_the_stream_network_class(self, method):
        direct = StreamNetwork(_segments(FIXTURE_NETWORK), area_km2=12.0)
        direct.classify(OrderingMethod(method))
        result = run(
            "network stats",
            segments=_inline(FIXTURE_NETWORK),
            method=method,
            area_km2=12.0,
        ).result
        assert result.statistics == direct.get_statistics()
        assert result.method == method
        assert result.n_segments == 9
        assert result.stream_frequency_per_km2 == pytest.approx(9 / 12.0)

    def test_known_strahler_orders_and_ratios(self):
        """Hand-computed orders of the fixture network (5 + 2 + 2 segments)."""
        statistics = run(
            "network stats", segments_file=str(NETWORK_SEGMENTS)
        ).result.statistics
        assert statistics.max_order == 3
        assert statistics.segment_counts == {1: 5, 2: 2, 3: 2}
        assert statistics.total_lengths_km[1] == pytest.approx(
            1.2 + 0.8 + 1.0 + 0.9 + 0.7
        )
        assert statistics.bifurcation_ratios == {
            1: pytest.approx(2.5),
            2: pytest.approx(1.0),
        }
        assert statistics.total_stream_length_km == pytest.approx(12.7)
        assert statistics.drainage_density is None

    def test_drainage_density_needs_the_area(self):
        with_area = run(
            "network stats", segments_file=str(NETWORK_SEGMENTS), area_km2=10.0
        ).result
        assert with_area.statistics.drainage_density == pytest.approx(1.27)
        assert with_area.stream_frequency_per_km2 == pytest.approx(0.9)

    def test_shreve_with_missing_magnitudes_has_ratios_only_between_present_ones(self):
        """Regression: Shreve magnitudes 1, 2, 4, 5 (no 3) raised ``KeyError``."""
        result = run(
            "network stats", segments_file=str(NETWORK_SEGMENTS), method="shreve"
        ).result.statistics
        assert result.segment_counts == {1: 5, 2: 2, 4: 1, 5: 1}
        assert result.max_order == 5
        # pairs (1, 2) and (4, 5) exist; the gaps 2-3 and 3-4 have no ratio
        assert set(result.bifurcation_ratios) == {1, 4}
        assert result.bifurcation_ratios[1] == pytest.approx(5 / 2)
        assert result.bifurcation_ratios[4] == pytest.approx(1.0)
        assert set(result.length_ratios) == {1, 4}

    def test_library_statistics_survive_non_contiguous_magnitudes(self):
        """Regression of ``StreamNetwork.get_statistics`` itself."""
        direct = StreamNetwork(_segments(FIXTURE_NETWORK))
        direct.classify(OrderingMethod.SHREVE)
        statistics = direct.get_statistics()
        assert isinstance(statistics, NetworkStatistics)
        assert sorted(statistics.segment_counts) == [1, 2, 4, 5]

    def test_csv_json_and_inline_agree(self, tmp_path):
        records = _inline(FIXTURE_NETWORK)
        as_json = tmp_path / "segments.json"
        as_json.write_text(json.dumps(records), encoding="utf-8")
        from_csv = run("network stats", segments_file=str(NETWORK_SEGMENTS)).result
        from_json = run("network stats", segments_file=str(as_json)).result
        from_inline = run("network stats", segments=records).result
        assert from_csv == from_json == from_inline

    @pytest.mark.parametrize(
        ("delimiter", "ids"),
        [(",", '"1;2"'), (",", '"1|2"'), (",", '"1, 2"'), (";", "1 2"), (";", "1;2")],
    )
    def test_upstream_ids_formats_of_a_csv(self, tmp_path, delimiter, ids):
        quoted = ids if delimiter == "," else f'"{ids}"'
        text = "\n".join(
            [
                delimiter.join(["segment_id", "upstream_ids", "length_km"]),
                delimiter.join(["1", "", "1,5" if delimiter == ";" else "1.5"]),
                delimiter.join(["2", "", "1.0"]),
                delimiter.join(["3", quoted, "2.0"]),
            ]
        )
        path = tmp_path / "segments.csv"
        path.write_text(text + "\n", encoding="utf-8")
        result = run("network stats", segments_file=str(path)).result
        assert result.statistics.segment_counts == {1: 2, 2: 1}
        assert result.statistics.total_stream_length_km == pytest.approx(4.5)

    def test_numbers_in_a_json_file_may_be_strings_or_integral_floats(self, tmp_path):
        path = tmp_path / "segments.json"
        path.write_text(
            json.dumps(
                [
                    {"segment_id": "1", "upstream_ids": None, "length_km": "1.5"},
                    {"segment_id": 2.0, "length_km": 1},
                    {"segment_id": 3, "upstream_ids": "1;2", "length_km": 0},
                ]
            ),
            encoding="utf-8",
        )
        result = run("network stats", segments_file=str(path)).result
        assert result.statistics.segment_counts == {1: 2, 2: 1}

    @pytest.mark.parametrize(
        ("records", "reason"),
        [
            (
                [
                    {"segment_id": 1, "upstream_ids": [2], "length_km": 1.0},
                    {"segment_id": 2, "upstream_ids": [1], "length_km": 1.0},
                ],
                "cycle",
            ),
            ([{"segment_id": 1, "upstream_ids": [1], "length_km": 1.0}], "cycle"),
            (
                [{"segment_id": 1, "upstream_ids": [7], "length_km": 1.0}],
                "unknown_upstream",
            ),
            (
                [
                    {"segment_id": 1, "length_km": 1.0},
                    {"segment_id": 1, "length_km": 2.0},
                ],
                "duplicate_segment",
            ),
            (
                [
                    {"segment_id": 1, "length_km": 1.0},
                    {"segment_id": 2, "length_km": 1.0},
                    {"segment_id": 3, "upstream_ids": [1, 1], "length_km": 1.0},
                ],
                "duplicate_upstream",
            ),
            ([{"segment_id": 1, "length_km": -1.0}], "bad_number"),
            ([{"segment_id": 1.5, "length_km": 1.0}], "bad_number"),
            ([{"segment_id": True, "length_km": 1.0}], "bad_number"),
            ([{"segment_id": 1}], "missing_field"),
            ([{"length_km": 1.0}], "missing_field"),
            (["segment"], "shape"),
        ],
    )
    def test_invalid_inline_segments_are_parameter_errors(self, records, reason):
        with pytest.raises(InvalidParameterError) as caught:
            network.network_stats(segments=records)
        assert caught.value.details["option"] == "segments"
        assert caught.value.details["reason"] == reason

    def test_a_cycle_downstream_of_a_headwater_is_rejected_not_looped(self):
        """The library rejects the cycle (it used to loop forever)."""
        records = [
            {"segment_id": 1, "upstream_ids": [], "length_km": 1.0},
            {"segment_id": 2, "upstream_ids": [1, 3], "length_km": 1.0},
            {"segment_id": 3, "upstream_ids": [2], "length_km": 1.0},
        ]
        with pytest.raises(InvalidParameterError) as caught:
            network.network_stats(segments=records)
        assert caught.value.details["segments"] == [2, 3]

    def test_file_errors_are_data_errors_with_the_row(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_text(
            "segment_id,upstream_ids,length_km\n1,,1.0\n2,9,1.0\n", encoding="utf-8"
        )
        with pytest.raises(InputDataError) as caught:
            run("network stats", segments_file=str(path))
        assert caught.value.details["reason"] == "unknown_upstream"
        assert caught.value.details["row"] == 2
        assert caught.value.details["path"] == str(path)

    def test_a_file_needs_the_three_columns(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_text("segment_id,length_km\n1,1.0\n", encoding="utf-8")
        with pytest.raises(InputDataError) as caught:
            run("network stats", segments_file=str(path))
        assert caught.value.details["column"] == "upstream_ids"

    def test_exactly_one_source_and_a_known_method(self):
        with pytest.raises(InvalidParameterError):
            network.network_stats()
        with pytest.raises(InvalidParameterError):
            network.network_stats(
                segments=_inline(FIXTURE_NETWORK), segments_file=str(NETWORK_SEGMENTS)
            )
        with pytest.raises(InvalidParameterError) as caught:
            network.network_stats(segments=_inline(FIXTURE_NETWORK), method="horton")
        assert caught.value.details["reason"] == "choice"

    def test_result_keys_are_json_strings(self):
        document = _json_roundtrip(
            run("network stats", segments_file=str(NETWORK_SEGMENTS), area_km2=12.0)
        )
        assert document["result"]["statistics"]["segment_counts"] == {
            "1": 5,
            "2": 2,
            "3": 2,
        }


# --- stats: series input --------------------------------------------------------------


class TestImgwToolsExport:
    """The IMGWTools ``export_series`` CSV loads and runs without preprocessing."""

    # 14 days from 2023-11-01 (hydrological year 2024); 2023-11-08 and -09 are missing.
    VALID_Q = [2.5, 2.7, 3.0, 3.6, 4.8, 7.1, 11.4, 7.9, 5.6, 4.4, 3.5, 3.0]

    def test_characteristic_values(self):
        result = run(
            "stats characteristic",
            input_file=str(IMGW_EXPORT),
            value_column="Q",
            date_column="date",
        )
        values = result.result
        assert values.period_years == 1
        assert values.parameter == "Q"
        assert values.wwx == values.nwx == 11.4
        assert values.nnx == 2.5
        assert values.ssx == pytest.approx(np.mean(self.VALID_Q))
        assert [n.code for n in result.notices] == ["missing_values_removed"]
        assert "2 of 14" in result.notices[0].text
        assert "2023-11-08" in result.notices[0].text

    def test_the_column_name_may_carry_its_unit(self):
        plain = run(
            "stats characteristic",
            input_file=str(IMGW_EXPORT),
            value_column="Q",
            date_column="date",
        )
        full = run(
            "stats characteristic",
            input_file=str(IMGW_EXPORT),
            value_column="Q [m3/s]",
            date_column="date",
            parameter="Q",
        )
        assert plain.result == full.result

    def test_stage_column_with_the_stage_label(self):
        result = run(
            "stats characteristic",
            input_file=str(IMGW_EXPORT),
            value_column="H",
            date_column="date",
            parameter="H",
        ).result
        assert result.parameter == "H"
        assert result.wwx == 203.0
        assert result.nnx == 150.0

    def test_daily_statistics(self):
        result = run(
            "stats daily",
            input_file=str(IMGW_EXPORT),
            value_column="Q",
            date_column="date",
        ).result
        # November days only: hydrological days 1-14 without 8 and 9
        assert result.day_of_year.tolist() == [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14]
        assert result.count.tolist() == [1.0] * 12
        assert result.max_values.tolist() == self.VALID_Q

    def test_trend_test_on_the_valid_values(self):
        result = run(
            "stats mann-kendall", input_file=str(IMGW_EXPORT), value_column="Q"
        )
        assert result.result == mann_kendall_test(np.array(self.VALID_Q))
        assert result.notices[0].code == "missing_values_removed"

    def test_a_single_year_is_too_short_for_flood_frequency(self):
        with pytest.raises(CalculationError) as caught:
            run(
                "stats flood-frequency",
                input_file=str(IMGW_EXPORT),
                value_column="Q",
                date_column="date",
            )
        assert caught.value.details == {"count": 1, "minimum": 3}

    def test_months_without_data_stop_the_monthly_statistics(self):
        with pytest.raises(CalculationError) as caught:
            run(
                "stats monthly",
                input_file=str(IMGW_EXPORT),
                value_column="Q",
                date_column="date",
            )
        assert caught.value.details["missing_months"] == [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            12,
        ]

    def test_missing_days_stop_the_sequence_detection(self):
        with pytest.raises(CalculationError) as caught:
            run(
                "stats low-flow-sequences",
                input_file=str(IMGW_EXPORT),
                value_column="Q",
                date_column="date",
                threshold=4.0,
            )
        assert caught.value.details == {
            "reason": "missing_values",
            "n_missing": 2,
            "first_missing_date": "2023-11-08",
        }

    def test_water_level_zones_of_the_stage_column(self):
        result = run(
            "hydrometrics water-level-zones",
            input_file=str(IMGW_EXPORT),
            value_column="H",
            bin_width=10,
        )
        assert result.result.n_observations == 12
        assert result.result.frequency.counts.sum() == 12
        assert result.notices[0].code == "missing_values_removed"


class TestSeriesInput:
    """Inline values and files give the same series; bad inputs are told apart."""

    def test_inline_and_file_are_the_same_series(self, tmp_path):
        series = _daily()
        inline = run(
            "stats characteristic",
            values=series.values.tolist(),
            dates=[str(day) for day in series.dates],
        )
        from_file = run(
            "stats characteristic",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
        )
        assert inline.result == from_file.result

    def test_semicolon_csv_with_decimal_comma(self, tmp_path):
        path = tmp_path / "flows.csv"
        path.write_text(
            "Data;Przepływ\n2022-01-01;1,5\n2022-01-02;2,5\n2022-01-03;4,0\n",
            encoding="utf-8",
        )
        result = run(
            "stats characteristic",
            input_file=str(path),
            value_column="Przepływ",
            date_column="Data",
        ).result
        assert result.wwx == 4.0
        assert result.nnx == 1.5
        assert result.ssx == pytest.approx(8.0 / 3.0)

    def test_dates_are_required_for_dated_statistics(self):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_characteristic(values=[1.0, 2.0, 3.0])
        assert caught.value.details["option"] == "dates"

    def test_missing_value_column_is_a_data_error(self):
        with pytest.raises(InputDataError) as caught:
            run(
                "stats characteristic",
                input_file=str(DAILY_FLOWS),
                value_column="Qmax",
                date_column="date",
            )
        assert caught.value.details["reason"] == "missing_column"

    def test_a_column_without_numbers_is_a_calculation_error(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("date,Q\n2022-01-01,\n2022-01-02,NA\n", encoding="utf-8")
        with pytest.raises(CalculationError, match="All 2 values"):
            run(
                "stats characteristic",
                input_file=str(path),
                value_column="Q",
                date_column="date",
            )


# --- stats: characteristic, daily, monthly --------------------------------------------


class TestCharacteristicDailyMonthly:
    """``stats characteristic``, ``stats daily`` and ``stats monthly``."""

    def test_characteristic_values_equal_the_library(self):
        series = _daily()
        direct = calculate_characteristic_values(series.values, series.dates, "Q")
        result = run(
            "stats characteristic",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
        )
        assert result.result == direct
        assert result.notices == ()
        assert direct.period_years == 3

    def test_daily_statistics_equal_the_library(self):
        series = _daily()
        direct = calculate_daily_statistics(series.values, series.dates)
        result = run(
            "stats daily",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
        ).result
        for field in dataclasses.fields(direct):
            np.testing.assert_array_equal(
                getattr(result, field.name), getattr(direct, field.name)
            )
        assert len(result.day_of_year) == 366

    def test_monthly_statistics_equal_the_library(self):
        series = _daily()
        direct = calculate_monthly_statistics(series.values, series.dates, 0.9)
        result = run(
            "stats monthly",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
            confidence_level=0.9,
        )
        for field in dataclasses.fields(direct):
            np.testing.assert_array_equal(
                getattr(result.result, field.name), getattr(direct, field.name)
            )
        assert result.result.confidence_level == 0.9
        assert result.notices == ()

    def test_a_month_with_one_value_has_undefined_dispersion_and_a_notice(self):
        dates = [f"2022-{month:02d}-15" for month in range(1, 13)]
        values = [float(month) for month in range(1, 13)]
        result = run("stats monthly", values=values, dates=dates)
        document = _json_roundtrip(result)["result"]
        assert document["mean_values"] == values
        for field in (
            "std_values",
            "cv_values",
            "skewness_values",
            "ci_lower",
            "ci_upper",
        ):
            assert document[field] == [None] * 12, field
        assert [n.code for n in result.notices] == ["single_value_month"]
        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12" in result.notices[0].text

    def test_only_the_months_with_one_value_are_named_in_the_notice(self):
        dates = [f"2022-{month:02d}-15" for month in range(1, 13)]
        dates += [f"2023-{month:02d}-15" for month in range(1, 12)]  # not December
        values = [float(month) for month in range(1, 13)] + [
            float(month) + 2.0 for month in range(1, 12)
        ]
        result = run("stats monthly", values=values, dates=dates)
        document = _json_roundtrip(result)["result"]
        assert document["std_values"][:11] != [None] * 11
        assert document["std_values"][11] is None
        assert [n.code for n in result.notices] == ["single_value_month"]
        assert result.notices[0].text.startswith("Month(s) 12 hold a single value")

    @pytest.mark.parametrize("level", [0.0, 1.0, -0.2, 1.5])
    def test_confidence_level_must_be_inside_zero_one(self, level):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_monthly(
                values=[1.0] * 12,
                dates=[f"2022-{m:02d}-01" for m in range(1, 13)],
                confidence_level=level,
            )
        assert caught.value.details["option"] == "confidence_level"

    def test_unknown_parameter_label(self):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_characteristic(
                values=[1.0], dates=["2022-01-01"], parameter="V"
            )
        assert caught.value.details["reason"] == "choice"


# --- stats: flood frequency -----------------------------------------------------------


def _annual_maxima() -> np.ndarray:
    return load_series(input_file=ANNUAL_MAXIMA, value_column="Qmax").values


class TestFloodFrequency:
    """``stats flood-frequency``."""

    def test_all_distributions_equal_fit_all(self):
        maxima = _annual_maxima()
        periods = np.array([10.0, 50.0, 100.0])
        direct = FloodFrequencyAnalysis(maxima, periods)
        expected = direct.fit_all()
        result = run(
            "stats flood-frequency",
            input_file=str(ANNUAL_MAXIMA),
            value_column="Qmax",
            return_periods=[10, 50, 100],
        ).result
        assert [d.distribution_name for d in result.distributions] == list(expected)
        for fitted, reference in zip(result.distributions, expected.values()):
            assert fitted.to_dict() == reference.to_dict()
        assert result.best_distribution == next(iter(expected))
        assert result.n_years == 35
        assert result.annual_maxima == maxima.tolist()
        assert result.hydrological_years is None
        assert result.empirical.to_dict() == direct.empirical_frequency().to_dict()

    @pytest.mark.parametrize(
        ("name", "method"),
        [
            ("log_normal", "fit_log_normal"),
            ("gev", "fit_gev"),
            ("pearson3", "fit_pearson3"),
            ("weibull", "fit_weibull"),
        ],
    )
    def test_a_single_distribution_equals_its_fit(self, name, method):
        maxima = _annual_maxima()
        reference = getattr(FloodFrequencyAnalysis(maxima), method)()
        result = run(
            "stats flood-frequency",
            input_file=str(ANNUAL_MAXIMA),
            value_column="Qmax",
            distribution=name,
        ).result
        assert len(result.distributions) == 1
        assert result.best_distribution == name
        assert result.distributions[0].to_dict() == reference.to_dict()
        assert result.distributions[0].return_periods.tolist() == [
            2.0,
            5.0,
            10.0,
            20.0,
            50.0,
            100.0,
            500.0,
            1000.0,
        ]

    def test_quantiles_grow_with_the_return_period(self):
        result = run(
            "stats flood-frequency",
            input_file=str(ANNUAL_MAXIMA),
            value_column="Qmax",
            distribution="gev",
        ).result
        quantiles = result.distributions[0].quantiles
        assert np.all(np.diff(quantiles) > 0)

    def test_a_daily_series_is_reduced_to_annual_maxima_of_hydrological_years(self):
        values, dates = _boundary_series()
        result = run(
            "stats flood-frequency", values=values, dates=dates, distribution="gev"
        )
        assert result.result.hydrological_years == [2020, 2021, 2022, 2023]
        # 10.0 on 31 Oct 2020 belongs to HY 2020 and 8.0 on 1 Nov 2020 to HY 2021
        assert result.result.annual_maxima == [10.0, 8.0, 9.0, 5.5]
        assert result.result.n_years == 4

    def test_annual_maxima_agree_with_the_characteristic_values(self):
        series = _daily()
        result = run(
            "stats flood-frequency",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
            distribution="log_normal",
        ).result
        characteristic = calculate_characteristic_values(series.values, series.dates)
        assert result.hydrological_years == [2022, 2023, 2024]
        assert max(result.annual_maxima) == characteristic.wwx
        assert np.mean(result.annual_maxima) == pytest.approx(characteristic.swx)
        assert float(np.median(result.annual_maxima)) == characteristic.zwx
        assert min(result.annual_maxima) == characteristic.nwx

    def test_short_samples_are_reported_as_notices(self):
        few = run(
            "stats flood-frequency", values=[100, 120, 90, 150, 130], distribution="gev"
        )
        texts = " | ".join(n.text for n in few.notices)
        assert "Sample size < 10" in texts
        assert {n.code for n in few.notices} == {"user_warning"}
        twenty = run(
            "stats flood-frequency", values=list(range(100, 120)), distribution="gev"
        )
        assert any("KZGW (2017)" in n.text for n in twenty.notices)

    def test_missing_annual_maxima_are_dropped_with_a_notice(self, tmp_path):
        path = tmp_path / "maxima.csv"
        path.write_text(
            "year,Qmax\n2000,100\n2001,\n2002,150\n2003,120\n2004,130\n",
            encoding="utf-8",
        )
        result = run(
            "stats flood-frequency",
            input_file=str(path),
            value_column="Qmax",
            distribution="gev",
        )
        assert result.result.annual_maxima == [100.0, 150.0, 120.0, 130.0]
        assert result.notices[0].code == "missing_values_removed"

    @pytest.mark.parametrize("periods", [[1], [0.5, 10], [0, 10], [10, float("nan")]])
    def test_return_periods_must_exceed_one_year(self, periods):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_flood_frequency(
                values=[1.0, 2.0, 3.0, 4.0], return_periods=periods
            )
        assert caught.value.details["option"] == "return_periods"

    def test_fewer_than_three_maxima_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            stats.stats_flood_frequency(values=[10.0, 20.0])
        assert caught.value.code == "calculation_error"
        assert caught.value.details == {"count": 2, "minimum": 3}

    def test_unknown_distribution(self):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_flood_frequency(values=[1.0, 2.0, 3.0], distribution="gumbel")
        assert caught.value.details["allowed"][0] == "all"

    def test_dates_and_values_must_match(self):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_flood_frequency(
                values=[1.0, 2.0, 3.0], dates=["2020-01-01", "2020-01-02"]
            )
        assert caught.value.details["reason"] == "length_mismatch"

    def test_result_is_json(self):
        document = _json_roundtrip(
            run(
                "stats flood-frequency",
                input_file=str(ANNUAL_MAXIMA),
                value_column="Qmax",
                distribution="gev",
            )
        )
        assert document["result"]["distributions"][0]["distribution_name"] == "gev"
        assert document["result"]["hydrological_years"] is None
        assert document["notices"][0]["code"] == "user_warning"


# --- stats: low flows -----------------------------------------------------------------


class TestLowFlow:
    """``stats low-flow``."""

    def test_fisher_tippett_equals_the_library(self):
        series = _daily()
        direct = LowFlowAnalysis(
            series.values, series.dates, np.array([2.0, 10.0, 50.0])
        )
        result = run(
            "stats low-flow",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
            return_periods=[2, 10, 50],
        )
        assert (
            result.result.fisher_tippett.to_dict()
            == direct.fit_fisher_tippett().to_dict()
        )
        assert result.result.annual_minima == direct.annual_minima().tolist()
        assert (
            result.result.empirical.to_dict() == direct.empirical_frequency().to_dict()
        )
        assert result.result.n_years == 3
        assert result.result.hydrological_years == [2022, 2023, 2024]
        assert [n.code for n in result.notices] == ["user_warning"]
        assert "Only 3 year(s)" in result.notices[0].text

    def test_annual_minima_follow_the_hydrological_year(self):
        values, dates = _boundary_series()
        result = run("stats low-flow", values=values, dates=dates).result
        # 1.0 on 30 Oct 2020 (HY 2020), 0.5 on 2 Nov 2020 (HY 2021), 0.8 and 0.9
        assert result.hydrological_years == [2020, 2021, 2022, 2023]
        assert result.annual_minima == [1.0, 0.5, 0.8, 0.9]

    def test_low_flow_quantiles_fall_with_the_return_period(self):
        quantiles = run(
            "stats low-flow",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
            return_periods=[2, 10, 50],
        ).result.fisher_tippett.quantiles
        assert np.all(np.diff(quantiles) < 0)

    def test_fewer_than_three_years_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            run(
                "stats low-flow",
                input_file=str(IMGW_EXPORT),
                value_column="Q",
                date_column="date",
            )
        assert caught.value.details == {"count": 1, "minimum": 3}

    def test_return_periods_are_checked(self):
        with pytest.raises(InvalidParameterError):
            stats.stats_low_flow(
                values=[1.0], dates=["2022-01-01"], return_periods=[1.0]
            )


class TestFitErrorClassification:
    """A numerical failure of a fit is a calculation error, a Hydrolog error is not."""

    def test_a_numerical_failure_is_a_calculation_error(self):
        def failing():
            raise FloatingPointError("overflow")

        with pytest.raises(CalculationError) as caught:
            stats._fit("the test distribution", failing)
        assert caught.value.code == "calculation_error"
        assert caught.value.details == {"fit": "the test distribution"}

    def test_an_invalid_parameter_error_keeps_its_code(self):
        """It is also a ``ValueError``, which must not read as a numerical failure."""

        def invalid():
            raise InvalidParameterError("bad input", details={"option": "x"})

        with pytest.raises(InvalidParameterError) as caught:
            stats._fit("the test distribution", invalid)
        assert caught.value.code == "validation_error"
        assert caught.value.details == {"option": "x"}


def _sequence_series():
    """30 days of 5.0 with two runs below 3.0 two days apart and a longer one later."""
    values = [5.0] * 30
    for index in (2, 3, 4):
        values[index] = 1.0
    for index in (7, 8):
        values[index] = 2.0
    for index in range(20, 26):
        values[index] = 0.5
    dates = [
        str(day)
        for day in np.arange(
            np.datetime64("2023-01-01"),
            np.datetime64("2023-01-31"),
            dtype="datetime64[D]",
        )
    ]
    return values, dates


class TestLowFlowSequences:
    """``stats low-flow-sequences``."""

    def test_sequences_equal_detect_sequences(self):
        series = _daily()
        direct = LowFlowAnalysis(series.values, series.dates).detect_sequences(
            2.2, 5, 4
        )
        result = run(
            "stats low-flow-sequences",
            input_file=str(DAILY_FLOWS),
            value_column="Q",
            date_column="date",
            threshold=2.2,
        ).result
        assert result.n_events == direct.n_events == 7
        assert result.total_deficit == direct.total_deficit
        assert result.max_duration_days == direct.max_duration_days
        assert result.n_days == 1096
        for event, reference in zip(result.sequences, direct.sequences):
            assert event.start_index == reference.start_index
            assert event.end_index == reference.end_index
            assert event.duration_days == reference.duration_days
            assert event.min_flow == reference.min_flow
            assert event.mean_flow == reference.mean_flow
            assert event.deficit_volume == reference.deficit_volume
            assert event.start_date == str(series.dates[reference.start_index])
            assert event.end_date == str(series.dates[reference.end_index])

    def test_close_runs_are_merged_and_the_deficit_is_hand_computed(self):
        values, dates = _sequence_series()
        result = run(
            "stats low-flow-sequences",
            values=values,
            dates=dates,
            threshold=3.0,
            min_duration_days=3,
            max_gap_days=4,
        ).result
        first, second = result.sequences
        # runs 2-4 and 7-8 are two days apart (< 4): one event of 7 days
        assert (first.start_date, first.end_date) == ("2023-01-03", "2023-01-09")
        assert first.duration_days == 7
        assert first.min_flow == 1.0
        assert first.mean_flow == pytest.approx((1 + 1 + 1 + 5 + 5 + 2 + 2) / 7)
        assert first.deficit_volume == pytest.approx(2 * 3 + 0 + 0 + 1 * 2)
        assert (second.start_date, second.end_date) == ("2023-01-21", "2023-01-26")
        assert second.deficit_volume == pytest.approx(2.5 * 6)
        assert result.total_deficit == pytest.approx(8.0 + 15.0)
        assert result.max_duration_days == 7
        assert result.n_events == 2

    def test_a_gap_of_max_gap_days_is_not_bridged(self):
        values, dates = _sequence_series()
        result = run(
            "stats low-flow-sequences",
            values=values,
            dates=dates,
            threshold=3.0,
            min_duration_days=3,
            max_gap_days=2,
        ).result
        # the gap has 2 days: 2 < 2 is false, so 2-4 and 7-8 stay apart and 7-8 is
        # shorter than 3 days
        assert [(e.start_index, e.end_index) for e in result.sequences] == [
            (2, 4),
            (20, 25),
        ]

    def test_no_sequence_below_a_low_threshold(self):
        values, dates = _sequence_series()
        result = run(
            "stats low-flow-sequences", values=values, dates=dates, threshold=0.1
        ).result
        assert result.n_events == 0
        assert result.sequences == []
        assert result.max_duration_days == 0

    def test_dates_must_be_consecutive_days(self):
        values, dates = _sequence_series()
        del values[10], dates[10]
        with pytest.raises(CalculationError) as caught:
            run("stats low-flow-sequences", values=values, dates=dates, threshold=3.0)
        assert caught.value.details["reason"] == "date_gap"
        assert caught.value.details["after"] == "2023-01-10"
        assert caught.value.details["next"] == "2023-01-12"

    @pytest.mark.parametrize(
        ("options", "option"),
        [({"threshold": 0.0}, "threshold"), ({"threshold": -1.0}, "threshold")],
    )
    def test_the_threshold_must_be_positive(self, options, option):
        values, dates = _sequence_series()
        with pytest.raises(InvalidParameterError, match="threshold"):
            stats.stats_low_flow_sequences(values=values, dates=dates, **options)

    def test_the_minimum_duration_must_be_at_least_one_day(self):
        values, dates = _sequence_series()
        with pytest.raises(InvalidParameterError, match="min_duration_days"):
            stats.stats_low_flow_sequences(
                values=values, dates=dates, threshold=3.0, min_duration_days=0
            )

    def test_result_is_json(self):
        values, dates = _sequence_series()
        document = _json_roundtrip(
            run(
                "stats low-flow-sequences",
                values=values,
                dates=dates,
                threshold=3.0,
                min_duration_days=3,
            )
        )
        assert document["result"]["sequences"][0]["start_date"] == "2023-01-03"
        assert document["inputs"]["max_gap_days"] == 4


# --- stats: trend ---------------------------------------------------------------------


class TestMannKendall:
    """``stats mann-kendall``."""

    @pytest.mark.parametrize(
        ("values", "direction"),
        [
            (list(np.arange(1.0, 21.0)), "increasing"),
            (list(np.arange(20.0, 0.0, -1.0)), "decreasing"),
            ([3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0], "none"),
        ],
    )
    def test_equals_the_library_test(self, values, direction):
        result = run("stats mann-kendall", values=values, alpha=0.05)
        assert result.result == mann_kendall_test(np.array(values), alpha=0.05)
        assert result.result.trend_direction == direction

    def test_a_monotonic_series_has_the_maximum_s_statistic(self):
        result = run("stats mann-kendall", values=list(np.arange(1.0, 21.0))).result
        assert result.s_statistic == 20 * 19 / 2
        assert result.trend_detected

    def test_alpha_decides_the_detection(self):
        values = [1.0, 2.0, 1.5, 3.0, 2.5, 4.0, 3.5, 5.0]
        strict = run("stats mann-kendall", values=values, alpha=0.001).result
        loose = run("stats mann-kendall", values=values, alpha=0.2).result
        assert strict.p_value == loose.p_value
        assert not strict.trend_detected
        assert loose.trend_detected
        assert loose.significance_level == 0.2

    def test_file_input_of_the_annual_maxima(self):
        result = run(
            "stats mann-kendall", input_file=str(ANNUAL_MAXIMA), value_column="Qmax"
        )
        assert result.result == mann_kendall_test(_annual_maxima())

    @pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1, 2.0])
    def test_alpha_must_be_inside_zero_one(self, alpha):
        with pytest.raises(InvalidParameterError) as caught:
            stats.stats_mann_kendall(values=[1.0, 2.0, 3.0], alpha=alpha)
        assert caught.value.details["option"] == "alpha"

    def test_fewer_than_three_values_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            stats.stats_mann_kendall(values=[1.0, 2.0])
        assert caught.value.details == {"count": 2, "minimum": 3}


# --- hydrometrics ---------------------------------------------------------------------


def _rating_pairs():
    table = read_table(RATING_PAIRS)
    return table.numbers("H"), table.numbers("Q")


class TestRatingCurve:
    """``hydrometrics rating-curve``."""

    def test_file_fit_equals_the_library_fit(self):
        levels, flows = _rating_pairs()
        direct = RatingCurve(levels, flows).fit(h0_initial=40.0, remove_outliers=True)
        result = run(
            "hydrometrics rating-curve",
            input_file=str(RATING_PAIRS),
            level_column="H",
            discharge_column="Q",
            h0_initial=40.0,
            remove_outliers=True,
        )
        assert result.result == direct
        assert result.notices == ()

    def test_inline_pairs_equal_the_file(self):
        levels, flows = _rating_pairs()
        inline = run(
            "hydrometrics rating-curve",
            water_levels=levels.tolist(),
            discharges=flows.tolist(),
            h0_initial=40.0,
        )
        from_file = run(
            "hydrometrics rating-curve",
            input_file=str(RATING_PAIRS),
            level_column="H [cm]",
            discharge_column="Q [m3/s]",
            h0_initial=40.0,
        )
        assert inline.result == from_file.result

    def test_removing_the_outlier_recovers_the_generating_law(self):
        """The fixture: Q = 0.01 (H - 40)^1.5 with noise and one gauging 35 % high."""
        kept = run(
            "hydrometrics rating-curve",
            input_file=str(RATING_PAIRS),
            level_column="H",
            discharge_column="Q",
            h0_initial=40.0,
        ).result
        cleaned = run(
            "hydrometrics rating-curve",
            input_file=str(RATING_PAIRS),
            level_column="H",
            discharge_column="Q",
            h0_initial=40.0,
            remove_outliers=True,
        ).result
        assert (kept.n_points, kept.n_outliers_removed) == (15, 0)
        assert (cleaned.n_points, cleaned.n_outliers_removed) == (14, 1)
        assert cleaned.r_squared > kept.r_squared
        assert cleaned.b == pytest.approx(1.5, abs=0.05)
        assert cleaned.h0 == pytest.approx(40.0, abs=2.0)
        assert cleaned.std_residuals < kept.std_residuals

    def test_the_outlier_threshold_reaches_the_fit(self):
        """A threshold of 10 sigma keeps every pair, as the library does."""
        levels, flows = _rating_pairs()
        direct = RatingCurve(levels, flows).fit(
            h0_initial=40.0, remove_outliers=True, outlier_std=10.0
        )
        result = run(
            "hydrometrics rating-curve",
            input_file=str(RATING_PAIRS),
            level_column="H",
            discharge_column="Q",
            h0_initial=40.0,
            remove_outliers=True,
            outlier_std=10.0,
        ).result
        assert result == direct
        assert result.n_outliers_removed == 0
        assert result.n_points == 15

    def test_pairs_with_a_missing_value_are_dropped_with_a_notice(self, tmp_path):
        levels, flows = _rating_pairs()
        lines = ["H,Q"]
        for index, (level, flow) in enumerate(zip(levels, flows)):
            if index == 3:
                lines.append(f"{level},")
            elif index == 6:
                lines.append(f",{flow}")
            else:
                lines.append(f"{level},{flow}")
        path = tmp_path / "pairs.csv"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = run(
            "hydrometrics rating-curve",
            input_file=str(path),
            level_column="H",
            discharge_column="Q",
            h0_initial=40.0,
        )
        keep = np.ones(len(levels), dtype=bool)
        keep[[3, 6]] = False
        assert result.result == RatingCurve(levels[keep], flows[keep]).fit(
            h0_initial=40.0
        )
        assert result.result.n_points == 13
        assert [n.code for n in result.notices] == ["missing_values_removed"]
        assert "2 of 15" in result.notices[0].text

    def test_lengths_must_match(self):
        with pytest.raises(InvalidParameterError) as caught:
            hydrometrics.hydrometrics_rating_curve(
                water_levels=[1.0, 2.0, 3.0, 4.0], discharges=[1.0, 2.0, 3.0]
            )
        assert caught.value.details["reason"] == "length_mismatch"

    def test_too_few_pairs_are_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            hydrometrics.hydrometrics_rating_curve(
                water_levels=[100.0, 120.0], discharges=[5.0, 9.0], h0_initial=50.0
            )
        assert caught.value.details == {"count": 2, "minimum": 3}

    @pytest.mark.parametrize("h0", [62.0, 70.0, 1000.0])
    def test_the_initial_zero_level_must_be_below_every_level(self, h0):
        with pytest.raises(InvalidParameterError) as caught:
            run(
                "hydrometrics rating-curve",
                input_file=str(RATING_PAIRS),
                level_column="H",
                discharge_column="Q",
                h0_initial=h0,
            )
        assert caught.value.details["option"] == "h0_initial"
        assert caught.value.details["maximum"] == 62.0

    def test_the_default_initial_level_fails_for_negative_levels_with_a_hint(self):
        with pytest.raises(InvalidParameterError) as caught:
            hydrometrics.hydrometrics_rating_curve(
                water_levels=[-20.0, 10.0, 40.0, 80.0],
                discharges=[0.5, 2.0, 6.0, 15.0],
            )
        assert "lower than every water level" in caught.value.hint

    def test_a_numerically_failing_fit_is_a_calculation_error(self):
        """Levels so large that the power law overflows: no fit, exit code 4."""
        with pytest.raises(CalculationError) as caught:
            hydrometrics.hydrometrics_rating_curve(
                water_levels=[1e250, 2e250, 3e250, 4e250],
                discharges=[1.0, 2.0, 3.0, 4.0],
            )
        assert caught.value.code == "calculation_error"
        assert caught.value.exit_code == 4

    @pytest.mark.parametrize("threshold", [0.0, -1.0, float("nan")])
    def test_outlier_threshold_must_be_positive(self, threshold):
        with pytest.raises(InvalidParameterError) as caught:
            hydrometrics.hydrometrics_rating_curve(
                water_levels=[1.0, 2.0, 3.0],
                discharges=[1.0, 2.0, 3.0],
                outlier_std=threshold,
            )
        assert caught.value.details["option"] == "outlier_std"

    @pytest.mark.parametrize(
        "options",
        [
            {"water_levels": [1.0, 2.0, 3.0]},
            {"discharges": [1.0, 2.0, 3.0]},
            {"input_file": "pairs.csv"},
            {"input_file": "pairs.csv", "level_column": "H"},
            {
                "input_file": "pairs.csv",
                "level_column": "H",
                "discharge_column": "Q",
                "water_levels": [1.0, 2.0, 3.0],
            },
            {
                "water_levels": [1.0, 2.0, 3.0],
                "discharges": [1.0, 2.0, 3.0],
                "level_column": "H",
            },
            {},
        ],
    )
    def test_the_pairs_come_from_one_source(self, options):
        with pytest.raises(InvalidParameterError):
            hydrometrics.hydrometrics_rating_curve(**options)

    def test_missing_column_is_a_data_error(self):
        with pytest.raises(InputDataError) as caught:
            run(
                "hydrometrics rating-curve",
                input_file=str(RATING_PAIRS),
                level_column="level",
                discharge_column="Q",
            )
        assert caught.value.details["column"] == "level"


class TestWaterLevelZones:
    """``hydrometrics water-level-zones``."""

    # 25 levels in classes [100,110) ... [150,160): counts 2, 3, 10, 5, 3, 2
    LEVELS = [100] * 2 + [110] * 3 + [120] * 10 + [130] * 5 + [140] * 3 + [150] * 2

    def test_zones_of_a_known_histogram(self):
        result = run(
            "hydrometrics water-level-zones", values=self.LEVELS, bin_width=10
        ).result
        assert result.n_observations == 25
        assert result.frequency.counts.tolist() == [2, 3, 10, 5, 3, 2]
        assert result.frequency.duration_pct.tolist() == pytest.approx(
            [100, 92, 80, 40, 20, 8]
        )
        # NTW ends at the centre of the modal class, STW where the duration < 50 %
        assert result.zones.ntw_upper == 125.0
        assert result.zones.stw_upper == 135.0
        assert result.zones.ntw_range == (100.0, 125.0)
        assert result.zones.stw_range == (125.0, 135.0)
        assert result.zones.wtw_range == (135.0, 160.0)

    def test_equals_the_library(self):
        levels = np.array(self.LEVELS, dtype=float) + np.linspace(0.0, 8.0, 25)
        direct = WaterLevelFrequency(levels, bin_width=5.0)
        result = run(
            "hydrometrics water-level-zones", values=levels.tolist(), bin_width=5
        ).result
        assert result.zones == direct.rybczynski_zones()
        assert result.frequency.to_dict() == direct.frequency_distribution().to_dict()
        assert result.bin_width == 5.0

    def test_default_class_width_is_ten(self):
        result = run("hydrometrics water-level-zones", values=self.LEVELS)
        assert result.inputs["bin_width"] == 10.0
        assert result.result.bin_width == 10.0

    def test_frequencies_add_up(self):
        result = run(
            "hydrometrics water-level-zones", values=self.LEVELS, bin_width=10
        ).result
        assert result.frequency.frequency_pct.sum() == pytest.approx(100.0)
        assert result.frequency.cumulative_frequency_pct[-1] == pytest.approx(100.0)

    def test_the_zones_are_ordered_for_a_real_series(self):
        series = _daily()
        result = run(
            "hydrometrics water-level-zones",
            values=(series.values * 30.0).tolist(),
            bin_width=20,
        ).result
        assert result.zones.ntw_upper < result.zones.stw_upper
        assert result.zones.ntw_range[1] == result.zones.stw_range[0]
        assert result.zones.stw_range[1] == result.zones.wtw_range[0]

    @pytest.mark.parametrize("width", [0.0, -5.0, float("inf")])
    def test_class_width_must_be_positive_and_finite(self, width):
        with pytest.raises(InvalidParameterError) as caught:
            hydrometrics.hydrometrics_water_level_zones(
                values=self.LEVELS, bin_width=width
            )
        assert caught.value.details["option"] == "bin_width"

    def test_a_tiny_class_width_is_refused_instead_of_allocating_the_histogram(self):
        with pytest.raises(InvalidParameterError) as caught:
            hydrometrics.hydrometrics_water_level_zones(
                values=self.LEVELS, bin_width=1e-6
            )
        assert caught.value.details["reason"] == "minimum"

    def test_result_is_json(self):
        document = _json_roundtrip(
            run("hydrometrics water-level-zones", values=self.LEVELS, bin_width=10)
        )
        assert document["result"]["zones"]["ntw_range"] == [100.0, 125.0]
        assert document["result"]["frequency"]["counts"] == [2, 3, 10, 5, 3, 2]


# --- soil -----------------------------------------------------------------------------


class TestSoilTexture:
    """``soil texture``."""

    @pytest.mark.parametrize(
        ("clay", "sand", "silt", "texture", "hsg"),
        [
            (5, 90, 5, "sand", "A"),
            (8, 82, 10, "loamy_sand", "A"),
            (10, 65, 25, "sandy_loam", "B"),
            (20, 40, 40, "loam", "B"),
            (15, 20, 65, "silt_loam", "B"),
            (5, 10, 85, "silt", "B"),
            (25, 60, 15, "sandy_clay_loam", "C"),
            (33, 33, 34, "clay_loam", "C"),
            (33, 10, 57, "silty_clay_loam", "C"),
            (40, 50, 10, "sandy_clay", "D"),
            (45, 5, 50, "silty_clay", "D"),
            (45, 20, 35, "clay", "D"),
        ],
    )
    def test_every_texture_class_and_its_group(self, clay, sand, silt, texture, hsg):
        result = run("soil texture", clay=clay, sand=sand, silt=silt).result
        assert (
            result.texture_class == classify_usda_texture(clay, sand, silt) == texture
        )
        assert result.hsg == texture_to_hsg(texture) == hsg
        assert result.hsg_code == "ABCD".index(hsg) + 1

    def test_codes_follow_the_class_order(self):
        assert run("soil texture", clay=20, sand=40, silt=40).result.texture_code == 4
        assert run("soil texture", clay=45, sand=20, silt=35).result.texture_code == 12

    def test_the_unit_does_not_matter(self):
        percent = run("soil texture", clay=20, sand=40, silt=40).result
        grams_per_kg = run("soil texture", clay=200, sand=400, silt=400).result
        assert percent == grams_per_kg

    def test_amounts_need_not_sum_to_one_hundred(self):
        assert (
            run("soil texture", clay=2, sand=4, silt=4).result.texture_class == "loam"
        )

    def test_result_is_json(self):
        document = _json_roundtrip(run("soil texture", clay=45, sand=20, silt=35))
        assert document["result"] == {
            "texture_class": "clay",
            "texture_code": 12,
            "hsg": "D",
            "hsg_code": 4,
        }

    def test_no_soil_data_is_an_error_not_loam(self):
        with pytest.raises(InvalidParameterError) as caught:
            soil.soil_texture(clay=0, sand=0, silt=0)
        assert caught.value.details["reason"] == "no_data"

    @pytest.mark.parametrize(
        "amounts",
        [(-1, 50, 50), (10, float("nan"), 50), (10, 50, float("inf")), (10, 50, "x")],
    )
    def test_invalid_amounts_are_parameter_errors(self, amounts):
        with pytest.raises(InvalidParameterError):
            soil.soil_texture(clay=amounts[0], sand=amounts[1], silt=amounts[2])


@pytest.fixture
def soil_rasters(tmp_path):
    """Clay, sand and silt rasters (g/kg, EPSG:2180, 100 m cells) of 2 x 3 cells.

    Cells: sand (A), loam (B), clay loam (C) / clay (D), nodata tag, all zero.
    """
    rasterio = pytest.importorskip("rasterio")
    pytest.importorskip("pyproj")
    from rasterio.transform import from_origin

    cells = [
        [(60, 880, 60), (200, 400, 400), (330, 330, 340)],
        [(500, 200, 300), (-32768, -32768, -32768), (0, 0, 0)],
    ]
    paths = {}
    for index, name in enumerate(("clay", "sand", "silt")):
        data = np.array(
            [[cell[index] for cell in row] for row in cells], dtype=np.int16
        )
        path = tmp_path / f"{name}.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            dtype="int16",
            count=1,
            width=3,
            height=2,
            crs="EPSG:2180",
            transform=from_origin(500000.0, 600000.0, 100.0, 100.0),
            nodata=-32768,
        ) as target:
            target.write(data, 1)
        paths[f"{name}_path"] = str(path)
    return paths


class TestSoilHsg:
    """``soil hsg`` and ``soil hsg-stats`` (extra ``[raster]``)."""

    def test_writes_the_hsg_geotiff_and_reports_the_file(self, soil_rasters, tmp_path):
        rasterio = pytest.importorskip("rasterio")
        output = tmp_path / "out" / "hsg.tif"
        result = run("soil hsg", output_path=str(output), **soil_rasters)
        assert result.result.counts == {"A": 1, "B": 1, "C": 1, "D": 1, "nodata": 2}
        assert result.result.shape == (2, 3)
        assert result.result.crs == "EPSG:2180"
        assert [record.path for record in result.files] == [str(output)]
        assert result.files[0].sha256 == sha256_file(output)
        assert result.files[0].role == "output"
        with rasterio.open(output) as raster:
            assert raster.read(1).tolist() == [[1, 2, 3], [4, 0, 0]]
            assert raster.nodata == 0

    def test_equals_the_library_function(self, soil_rasters, tmp_path):
        from hydrolog.soil import hsg_from_rasters

        direct = hsg_from_rasters(
            soil_rasters["clay_path"],
            soil_rasters["sand_path"],
            soil_rasters["silt_path"],
            tmp_path / "direct.tif",
        )
        result = run("soil hsg", output_path=str(tmp_path / "op.tif"), **soil_rasters)
        assert result.result.counts == direct.counts
        assert result.result.shape == direct.shape
        assert (tmp_path / "op.tif").read_bytes() == (
            tmp_path / "direct.tif"
        ).read_bytes()

    def test_the_envelope_is_json_with_the_file_record(self, soil_rasters, tmp_path):
        document = _json_roundtrip(
            run("soil hsg", output_path=str(tmp_path / "hsg.tif"), **soil_rasters)
        )
        assert document["result"]["output_path"] == (tmp_path / "hsg.tif").as_posix()
        assert document["files"][0]["path"] == str(tmp_path / "hsg.tif")
        assert len(document["files"][0]["sha256"]) == 64

    def test_a_missing_input_is_not_found_and_nothing_is_written(
        self, soil_rasters, tmp_path
    ):
        soil_rasters["silt_path"] = str(tmp_path / "none.tif")
        output = tmp_path / "hsg.tif"
        with pytest.raises(NotFoundError):
            run("soil hsg", output_path=str(output), **soil_rasters)
        assert not output.exists()

    def test_the_output_must_not_be_an_input(self, soil_rasters):
        with pytest.raises(InvalidParameterError):
            run(
                "soil hsg",
                output_path=soil_rasters["clay_path"],
                **{key: value for key, value in soil_rasters.items()},
            )

    def test_statistics_equal_the_library_function(self, soil_rasters, tmp_path):
        from hydrolog.soil import hsg_statistics

        output = tmp_path / "hsg.tif"
        run("soil hsg", output_path=str(output), **soil_rasters)
        direct = hsg_statistics(output)
        result = run("soil hsg-stats", hsg_path=str(output))
        assert result.result == direct
        assert result.notices == ()
        assert result.result.total_area_m2 == 6 * 100.0 * 100.0
        assert result.result.groups["A"].area_m2 == 10_000.0
        assert result.result.nodata.count == 2

    def test_statistics_in_a_bbox_count_cut_cells_by_their_share(
        self, soil_rasters, tmp_path
    ):
        output = tmp_path / "hsg.tif"
        run("soil hsg", output_path=str(output), **soil_rasters)
        # the left half of the first column and the whole second column of both rows
        bbox = [500050.0, 599800.0, 500200.0, 600000.0]
        result = run(
            "soil hsg-stats", hsg_path=str(output), bbox=bbox, bbox_crs="EPSG:2180"
        )
        assert result.result.total_area_m2 == pytest.approx(150.0 * 200.0)
        assert result.result.groups["A"].area_m2 == pytest.approx(50.0 * 100.0)
        assert result.result.groups["B"].area_m2 == pytest.approx(100.0 * 100.0)

    def test_a_bbox_outside_the_raster_gives_zero_areas_and_a_notice(
        self, soil_rasters, tmp_path
    ):
        output = tmp_path / "hsg.tif"
        run("soil hsg", output_path=str(output), **soil_rasters)
        result = run(
            "soil hsg-stats",
            hsg_path=str(output),
            bbox=[1.0, 1.0, 2.0, 2.0],
            bbox_crs="EPSG:2180",
        )
        assert result.result.total_area_m2 == 0.0
        assert [n.code for n in result.notices] == ["empty_area"]

    @pytest.mark.parametrize(
        "options",
        [
            {"bbox": [1.0, 2.0, 3.0]},
            {"bbox": [5.0, 5.0, 1.0, 1.0]},
            {"bbox_crs": "EPSG:2180"},
            {"bbox": [1.0, 1.0, 2.0, 2.0], "bbox_crs": "EPSG:00"},
        ],
    )
    def test_invalid_areas_are_parameter_errors(self, soil_rasters, tmp_path, options):
        output = tmp_path / "hsg.tif"
        run("soil hsg", output_path=str(output), **soil_rasters)
        with pytest.raises(InvalidParameterError):
            run("soil hsg-stats", hsg_path=str(output), **options)

    def test_a_file_that_is_not_a_raster_is_a_data_error(self, tmp_path):
        pytest.importorskip("rasterio")
        path = tmp_path / "fake.tif"
        path.write_text("not a raster", encoding="utf-8")
        with pytest.raises(InputDataError):
            run("soil hsg-stats", hsg_path=str(path))

    def test_without_the_raster_extra_the_error_is_missing_dependency(
        self, monkeypatch, tmp_path
    ):
        """The operations let ``MissingDependencyError`` through (exit code 6)."""
        monkeypatch.setitem(sys.modules, "rasterio", None)
        with pytest.raises(MissingDependencyError) as caught:
            run("soil hsg-stats", hsg_path=str(tmp_path / "hsg.tif"))
        assert caught.value.code == "missing_dependency"
        assert caught.value.exit_code == 6
        assert "hydrolog[raster]" in caught.value.hint
        with pytest.raises(MissingDependencyError):
            run(
                "soil hsg",
                clay_path=str(tmp_path / "a.tif"),
                sand_path=str(tmp_path / "b.tif"),
                silt_path=str(tmp_path / "c.tif"),
                output_path=str(tmp_path / "out.tif"),
            )


# --- report ---------------------------------------------------------------------------

_DESIGN = {
    "hietogram_type": "beta",
    "total_mm": 50.0,
    "duration_min": 60.0,
    "timestep_min": 5.0,
}
_SERIES = {"values": [5.0, 10.0, 15.0, 10.0, 5.0, 3.0], "timestep_min": 10.0}
_CATCHMENT = {"area_km2": 45.0, "cn": 72, "tc_min": 90.0}


def _report(tmp_path, name="raport.md", **options):
    """Run ``report generate``; return the envelope and the text of the report."""
    output = tmp_path / name
    result = run("report generate", output=str(output), **options)
    return result, output.read_text(encoding="utf-8")


# a watershed with the inputs of all six time of concentration methods
_FULL_WATERSHED = {
    "name": "Potok Młynówka",
    "area_km2": 45.3,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "elevation_mean_m": 330.0,
    "mean_slope_m_per_m": 0.025,
    "channel_length_km": 10.8,
    "channel_slope_m_per_m": 0.018,
    "cn": 72,
    "runoff_coeff": 0.45,
    "retardance": 0.4,
    "overland_length_km": 0.25,
    "overland_slope_m_per_m": 0.008,
}


def _section(text, number):
    """Text of the report section ``## <number>.`` up to the next section."""
    start = text.index(f"## {number}.")
    end = text.find(f"## {number + 1}.", start)
    return text[start:] if end < 0 else text[start:end]


def _ordinate_rows(text):
    """``(time, ordinate)`` of the unit hydrograph table of a report, as printed."""
    section = _section(text, 5).split("### 5.4")[1]
    rows = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if line.startswith("| ") and cells[0].replace(".", "", 1).isdigit():
            rows.append((cells[0], cells[1]))
    return rows


def _tc_formula_fragments(method, p):
    """Pieces of the substituted formula of a method for the arguments ``p``."""
    if method == "kirpich":
        return [
            f"{p['length_km']:.2f}^{{0.77}}",
            f"{p['slope_m_per_m']:.4f}^{{-0.385}}",
        ]
    if method == "nrcs":
        return [
            f"L = {p['length_km'] * 1000:.0f} m",
            f"Y = {p['slope_m_per_m'] * 100:.2f} %",
            f"dla CN = {int(p['cn'])}",
        ]
    if method == "giandotti":
        return [
            f"\\sqrt{{{p['area_km2']:.2f}}}",
            f"1.5 \\cdot {p['length_km']:.2f}",
            f"\\sqrt{{{p['elevation_diff_m']:.1f}}}",
        ]
    if method == "faa":
        return [
            f"(1.1 - {p['runoff_coeff']:.2f})",
            f"{p['length_km']:.3f}^{{0.5}}",
            f"{p['slope_m_per_m']:.4f}^{{-1/3}}",
        ]
    if method == "kerby":
        return [
            f"({p['length_km']:.3f} \\cdot {p['retardance']:.2f})^{{0.467}}",
            f"{p['slope_m_per_m']:.4f}^{{-0.2335}}",
        ]
    return [  # kerby_kirpich
        f"({p['overland_length_km']:.3f} \\cdot {p['retardance']:.2f})^{{0.467}}",
        f"{p['overland_slope_m_per_m']:.4f}^{{-0.2335}}",
        f"{p['channel_length_km']:.2f}^{{0.77}}",
        f"{p['channel_slope_m_per_m']:.4f}^{{-0.385}}",
    ]


# (method, fields the watershed lacks): the arguments of a method follow what is there
_TC_REPORT_CASES = [
    (method, dropped)
    for method in ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
    for dropped in (
        (),
        ("channel_length_km", "channel_slope_m_per_m"),
        ("channel_length_km", "channel_slope_m_per_m", "mean_slope_m_per_m"),
        ("elevation_mean_m",),
    )
    # the composite method cannot do without the channel
    if not (method == "kerby_kirpich" and "channel_length_km" in dropped)
]


class TestReportGenerate:
    """``report generate``: the report of the computation of ``hydrograph generate``."""

    def test_the_report_documents_the_numbers_of_the_computation(self, tmp_path):
        options = {
            "watershed_file": str(WATERSHED_FILE),
            "tc_method": "kirpich",
            **_DESIGN,
        }
        result, text = _report(tmp_path, **options)
        computed = compute_hydrograph(**options).result
        summary = result.result
        assert summary.peak_discharge_m3s == computed.peak_discharge_m3s
        assert summary.time_to_peak_min == computed.time_to_peak_min
        assert summary.total_volume_m3 == computed.total_volume_m3
        assert summary.total_precipitation_mm == 50.0
        assert summary.total_effective_mm == computed.total_effective_mm
        assert summary.runoff_coefficient == computed.runoff_coefficient
        assert summary.cn_used == computed.cn_used == 72
        # the same numbers, formatted, are in the Markdown
        assert f"| {computed.peak_discharge_m3s:.2f} | m³/s |" in text
        assert f"| {computed.total_volume_m3:,.0f} | m³ |" in text
        assert f"{computed.total_effective_mm:.2f} mm" in text
        assert "CN = 72" in text

    def test_sections_are_listed_in_order(self, tmp_path):
        result, text = _report(
            tmp_path, watershed_file=str(WATERSHED_FILE), tc_method="nrcs", **_DESIGN
        )
        headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
        assert result.result.sections == headings
        assert [title.split(".")[0] for title in headings] == [
            str(number) for number in range(1, 9)
        ]
        assert headings[0] == "1. Parametry Zlewni"
        assert headings[-1] == "8. Bilans Wodny"

    def test_without_a_watershed_there_is_no_watershed_section(self, tmp_path):
        result, text = _report(tmp_path, **_CATCHMENT, **_DESIGN)
        assert "Parametry Zlewni" not in text
        assert result.result.sections[0].startswith("2. Czas")

    def test_the_header_names_the_watershed(self, tmp_path):
        from_file, text = _report(
            tmp_path,
            "a.md",
            watershed_file=str(WATERSHED_FILE),
            tc_method="kirpich",
            **_DESIGN,
        )
        assert text.splitlines()[0] == "# Raport Hydrologiczny: Zlewnia Przykładowa"
        assert from_file.result.watershed_name == "Zlewnia Przykładowa"
        named, text = _report(
            tmp_path,
            "b.md",
            watershed_file=str(WATERSHED_FILE),
            tc_method="kirpich",
            watershed_name="Potok Testowy",
            **_DESIGN,
        )
        assert text.splitlines()[0] == "# Raport Hydrologiczny: Potok Testowy"
        default, text = _report(tmp_path, "c.md", **_CATCHMENT, **_DESIGN)
        assert text.splitlines()[0] == "# Raport Hydrologiczny: Zlewnia"
        assert default.result.watershed_name == "Zlewnia"

    def test_the_tc_method_of_the_computation_is_named_in_the_report(self, tmp_path):
        _, text = _report(
            tmp_path, watershed_file=str(WATERSHED_FILE), tc_method="kirpich", **_DESIGN
        )
        assert "Wzór Kirpicha (1940)" in text

    def test_a_given_tc_is_not_passed_off_as_the_default_method(self, tmp_path):
        _, text = _report(tmp_path, area_km2=45.0, cn=72, tc_min=95.0, **_DESIGN)
        assert "Metoda: wartość zadana" in text
        assert "Kirpicha" not in text
        assert "tc = 95.0 min" in text

    def test_a_model_without_tc_has_no_tc_section(self, tmp_path):
        result, text = _report(
            tmp_path,
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            nash_n=3.0,
            nash_k_min=48.0,
            **_DESIGN,
        )
        assert "Czas Koncentracji" not in text
        assert result.result.sections[0] == "3. Hietogram Opadu"

    def test_model_parameters_reach_the_report_not_the_generator_defaults(
        self, tmp_path
    ):
        _, nash = _report(
            tmp_path,
            "nash.md",
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            nash_n=2.5,
            nash_k_min=48.0,
            **_DESIGN,
        )
        assert "n = 2.50" in nash
        assert "K = 48.0 min" in nash
        assert "K = 30.0 min" not in nash  # the placeholder of the generator
        _, clark = _report(
            tmp_path,
            "clark.md",
            area_km2=45.0,
            cn=72,
            tc_min=90.0,
            uh_model="clark",
            clark_r_min=35.0,
            **_DESIGN,
        )
        assert "R = 35.0 min" in clark
        assert "Tc + R = 125.0 min" in clark
        _, snyder = _report(
            tmp_path,
            "snyder.md",
            area_km2=45.0,
            cn=72,
            uh_model="snyder",
            snyder_length_km=15.0,
            snyder_centroid_length_km=7.5,
            snyder_ct=1.7,
            snyder_cp=0.65,
            **_DESIGN,
        )
        assert "L = 15.00 km" in snyder
        assert "Lc = 7.50 km" in snyder
        assert "Ct = 1.70" in snyder
        assert "Cp = 0.65" in snyder

    def test_a_weighted_curve_number_and_the_amc_adjustment(self, tmp_path):
        result, text = _report(
            tmp_path, area_km2=45.0, cn=72.5, amc="III", tc_min=90.0, **_DESIGN
        )
        assert "Curve Number dla AMC-II: **CN = 72.5**" in text
        assert "AMC-III" in text
        assert "Korekta CN" in text
        computed = compute_hydrograph(
            area_km2=45.0, cn=72.5, amc="III", tc_min=90.0, **_DESIGN
        )
        assert result.result.cn_used == computed.result.cn_used

    def test_a_precipitation_series_is_labelled_and_raises_no_label_notice(
        self, tmp_path
    ):
        result, text = _report(tmp_path, **_CATCHMENT, **_SERIES)
        assert "**Typ rozkładu:** opad zadany szeregiem" in text
        assert result.result.total_precipitation_mm == pytest.approx(48.0)
        assert not any("hietogram_type" in notice.text for notice in result.notices)

    def test_a_designed_hyetograph_is_labelled_with_its_distribution(self, tmp_path):
        _, text = _report(tmp_path, **_CATCHMENT, **_DESIGN)
        assert "**Typ rozkładu:** Rozkład Beta" in text

    def test_formulas_and_tables_can_be_left_out(self, tmp_path):
        _, full = _report(tmp_path, "full.md", **_CATCHMENT, **_DESIGN)
        _, plain = _report(
            tmp_path,
            "plain.md",
            include_formulas=False,
            include_tables=False,
            **_CATCHMENT,
            **_DESIGN,
        )
        assert "$$" in full
        assert "Szereg czasowy" in full
        assert "$$" not in plain
        assert "Szereg czasowy" not in plain
        assert len(plain) < len(full)

    def test_long_tables_are_abbreviated_at_max_table_rows(self, tmp_path):
        _, short = _report(
            tmp_path, "short.md", max_table_rows=6, **_CATCHMENT, **_DESIGN
        )
        _, long = _report(
            tmp_path, "long.md", max_table_rows=500, **_CATCHMENT, **_DESIGN
        )
        assert "| ... | ... |" in short
        assert "| ... | ... |" not in long
        assert len(short) < len(long)

    def test_the_file_is_written_atomically_and_replaces_an_existing_one(
        self, tmp_path
    ):
        output = tmp_path / "nested" / "dir" / "raport.md"
        output.parent.mkdir(parents=True)
        output.write_text("old report", encoding="utf-8")
        result = run("report generate", output=str(output), **_CATCHMENT, **_DESIGN)
        text = output.read_text(encoding="utf-8")
        assert text.startswith("# Raport Hydrologiczny")
        assert [path.name for path in output.parent.iterdir()] == ["raport.md"]
        assert result.result.size_bytes == len(text.encode("utf-8"))

    def test_missing_directories_are_created(self, tmp_path):
        output = tmp_path / "a" / "b" / "raport.md"
        run("report generate", output=str(output), **_CATCHMENT, **_DESIGN)
        assert output.is_file()

    def test_the_envelope_lists_the_file_and_carries_the_notices(self, tmp_path):
        result, _ = _report(
            tmp_path,
            watershed_file=str(WATERSHED_FILE),
            tc_method="kirpich",
            hietogram_type="beta",
            total_mm=50.0,
            duration_min=62.0,  # not a multiple of the 5 min step
            timestep_min=5.0,
        )
        output = tmp_path / "raport.md"
        assert [record.path for record in result.files] == [str(output)]
        assert result.files[0].sha256 == sha256_file(output)
        assert [notice.code for notice in result.notices] == ["duration_not_covered"]
        document = _json_roundtrip(result)
        assert document["result"]["output_path"] == output.as_posix()
        assert document["result"]["size_bytes"] == output.stat().st_size

    def test_the_standard_ia_coefficient_is_accepted(self, tmp_path):
        result, _ = _report(tmp_path, ia_coefficient=0.2, **_CATCHMENT, **_DESIGN)
        assert result.inputs["ia_coefficient"] == 0.2

    @pytest.mark.parametrize("coefficient", [0.05, 0.25, 1.0])
    def test_another_ia_coefficient_is_computed_and_rendered(
        self, tmp_path, coefficient
    ):
        """λ = 0.05 / 0.25 / 1: the effective precipitation and the formula use it."""
        options = {**_CATCHMENT, **_DESIGN, "ia_coefficient": coefficient}
        result, text = _report(tmp_path, **options)
        computed = compute_hydrograph(**options).result
        standard = compute_hydrograph(**_CATCHMENT, **_DESIGN).result

        assert result.inputs["ia_coefficient"] == coefficient
        assert result.result.total_effective_mm == computed.total_effective_mm
        assert result.result.total_effective_mm != pytest.approx(
            standard.total_effective_mm
        )
        assert (
            f"I_a = \\lambda \\cdot S = {coefficient} \\cdot "
            f"{computed.retention_mm:.2f} = {computed.initial_abstraction_mm:.2f}"
        ) in text
        assert (
            f"| Abstrakcja początkowa Ia | {computed.initial_abstraction_mm:.2f} mm |"
            in text
        )

    @pytest.mark.parametrize(
        "model, options",
        [
            ("scs", {}),
            ("nash", {"nash_n": 2.5, "nash_k_min": 48.0}),
            ("clark", {"clark_r_min": 35.0}),
            ("clark", {"clark_r_tc_ratio": 0.5}),
            (
                "snyder",
                {
                    "snyder_length_km": 15.0,
                    "snyder_centroid_length_km": 7.5,
                    "snyder_ct": 1.7,
                    "snyder_cp": 0.65,
                },
            ),
        ],
    )
    def test_the_unit_hydrograph_section_lists_the_computed_ordinates(
        self, tmp_path, model, options
    ):
        """The table is the unit hydrograph the hydrograph was computed with."""
        inputs = {**_CATCHMENT, **_DESIGN, "uh_model": model, **options}
        _, text = _report(tmp_path, max_table_rows=10_000, **inputs)

        unit = compute_hydrograph(**inputs).result.unit_hydrograph_result
        assert _ordinate_rows(text) == [
            (f"{t:.1f}", f"{q:.4f}") for t, q in zip(unit.times_min, unit.ordinates_m3s)
        ]

    @pytest.mark.parametrize("method, dropped", _TC_REPORT_CASES, ids=str)
    def test_the_tc_section_shows_what_the_method_was_fed_with(
        self, tmp_path, method, dropped
    ):
        """Whatever the watershed gives, the formula shows the derived arguments."""
        watershed = {
            key: value for key, value in _FULL_WATERSHED.items() if key not in dropped
        }
        _, text = _report(tmp_path, watershed=watershed, tc_method=method, **_DESIGN)

        parameters = tc.tc_watershed(
            watershed=watershed, method=method
        ).result.parameters
        section = _section(text, 2)
        assert "brak danych" not in section
        for fragment in _tc_formula_fragments(method, parameters):
            assert fragment in section, fragment

    def test_the_composite_tc_components_add_up_to_the_reported_tc(self, tmp_path):
        _, text = _report(
            tmp_path, watershed=_FULL_WATERSHED, tc_method="kerby_kirpich", **_DESIGN
        )

        run_ = compute_hydrograph(
            watershed=_FULL_WATERSHED, tc_method="kerby_kirpich", **_DESIGN
        )
        overland = ConcentrationTime.kerby(0.25, 0.008, 0.4)
        assert (
            f"t_c = {overland:.1f} + {run_.tc_min - overland:.1f} = {run_.tc_min:.1f}"
        ) in _section(text, 2)

    def test_a_given_tc_has_no_formula_inputs_to_show(self, tmp_path):
        _, text = _report(
            tmp_path,
            watershed=_FULL_WATERSHED,
            tc_min=95.0,
            uh_model="nash",
            nash_n=3.0,
            nash_k_min=48.0,
            **_DESIGN,
        )

        section = _section(text, 2)
        assert "Metoda: wartość zadana" in section
        assert "95.0 min" in section

    def test_a_failing_computation_writes_nothing(self, tmp_path):
        output = tmp_path / "sub" / "raport.md"
        with pytest.raises(InvalidParameterError) as caught:
            run("report generate", output=str(output), area_km2=45.0, cn=72, **_DESIGN)
        assert caught.value.details["option"] == "tc_min"
        assert not output.parent.exists()

    def test_a_missing_input_file_writes_nothing(self, tmp_path):
        output = tmp_path / "raport.md"
        with pytest.raises(NotFoundError):
            run(
                "report generate",
                output=str(output),
                watershed_file=str(tmp_path / "none.json"),
                **_DESIGN,
            )
        assert not output.exists()

    @pytest.mark.parametrize("option", ["watershed_file", "input_file"])
    def test_the_report_must_not_overwrite_an_input_file(self, tmp_path, option):
        source = tmp_path / "input.json"
        if option == "watershed_file":
            source.write_text(
                WATERSHED_FILE.read_text(encoding="utf-8"), encoding="utf-8"
            )
            options = {"watershed_file": str(source), "tc_method": "kirpich", **_DESIGN}
        else:
            source.write_text("depth\n5\n10\n5\n", encoding="utf-8")
            options = {
                "input_file": str(source),
                "value_column": "depth",
                "area_km2": 45.0,
                "cn": 72,
                "tc_min": 90.0,
                "timestep_min": 10.0,
            }
        before = source.read_bytes()
        with pytest.raises(InvalidParameterError) as caught:
            run("report generate", output=str(source), **options)
        assert caught.value.details == {
            "option": "output",
            "reason": "conflict",
            "input": option,
        }
        assert source.read_bytes() == before

    def test_an_unwritable_output_is_an_io_error_without_leftovers(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file, not a directory", encoding="utf-8")
        with pytest.raises(OutputError) as caught:
            run(
                "report generate",
                output=str(blocker / "raport.md"),
                **_CATCHMENT,
                **_DESIGN,
            )
        assert caught.value.code == "io_error"
        assert caught.value.exit_code == 9
        assert [path.name for path in tmp_path.iterdir()] == ["blocker"]

    @pytest.mark.parametrize("rows", [0, -3])
    def test_max_table_rows_must_be_positive(self, rows):
        with pytest.raises(InvalidParameterError) as caught:
            report.report_generate(
                output="unused.md", max_table_rows=rows, **_CATCHMENT, **_DESIGN
            )
        assert caught.value.details["option"] == "max_table_rows"

    def test_inputs_are_those_of_hydrograph_generate(self):
        """``report generate`` accepts every input of ``hydrograph generate``, alike."""
        declared = _declared("report generate")
        hydrograph_options = {option.name: option for option in GENERATE_OPTIONS}
        report_options = {option.name: option for option in declared.options}
        assert set(hydrograph_options) < set(report_options)
        assert declared.one_of == GENERATE_ONE_OF
        for name, option in hydrograph_options.items():
            assert report_options[name].type == option.type
            assert report_options[name].default == option.default
            assert report_options[name].required == option.required
        parameters = inspect.signature(report.report_generate).parameters
        reference = inspect.signature(compute_hydrograph).parameters
        assert set(reference) <= set(parameters)
        for name, parameter in reference.items():
            assert parameters[name].default == parameter.default, name
