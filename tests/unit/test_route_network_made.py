"""Tests of ``route network`` with subcatchments that make their own hydrograph.

The references are the generator (the node gives what ``HydrographGenerator`` gives for
its rain) and the front door of the other nodes: the document is checked in one place,
a file or an inline network says what is wrong with the same facts, and the notices and
the tables follow the rules of the command (a notice begins with the id of its node, a
table is the table that every ``route`` command reads).
"""

import warnings

import numpy as np
import pytest

from hydrolog.exceptions import InputDataError, InvalidParameterError
from hydrolog.operations import route_network
from hydrolog.operations._network_input import load_network
from hydrolog.precipitation import EulerIIHietogram
from hydrolog.routing import Hydrograph
from hydrolog.runoff import HydrographGenerator

from ._network_documents import document, junction, outlet, reach, source, written

WATERSHED = {
    "area_km2": 12.0,
    "perimeter_km": 18.0,
    "length_km": 6.0,
    "elevation_min_m": 210.0,
    "elevation_max_m": 330.0,
    "cn": 75,
}
RAIN = {
    "kind": "design",
    "hietogram_type": "euler_ii",
    "total_mm": 45,
    "duration_min": 60,
}
RUNOFF = {"model": "curve-number", "tc_min": 90.0}


def made(node_id, **fields):
    """A subcatchment that makes its hydrograph; ``fields`` replace or add."""
    return {
        "id": node_id,
        "type": "subcatchment",
        "watershed": WATERSHED,
        "runoff": RUNOFF,
        "rainfall": RAIN,
        **fields,
    }


def stream(**fields):
    """A made subcatchment, a reach by lag and the outlet."""
    return document(made("A", **fields), reach("R", "A", lag_min=30), outlet("R"))


def reference(step=5.0):
    """The hydrograph of the generator for the rain and the watershed above."""
    rain = EulerIIHietogram().generate(
        total_mm=45.0, duration_min=60.0, timestep_min=step
    )
    return HydrographGenerator(area_km2=12.0, cn=75, tc_min=90.0).generate(rain)


def refused(content, tmp_path):
    """The error of a network inline and of the same network in a file."""
    with pytest.raises(InvalidParameterError) as inline:
        load_network(network=content)
    with pytest.raises(InputDataError) as from_file:
        load_network(network_file=written(tmp_path, content))
    return inline.value, from_file.value


class TestTheSummary:
    def test_the_node_gives_what_the_generator_gives_and_says_what_it_used(self):
        output = route_network(network=stream(), nodes=["A"])

        result = output.result
        entry = {node["id"]: node for node in result.nodes}["A"]
        expected = reference().hydrograph
        assert result.timestep_min == 5.0
        np.testing.assert_array_equal(entry["discharge_m3s"], expected.discharge_m3s)
        np.testing.assert_array_equal(entry["times_min"], expected.times_min)
        assert entry["peak_m3s"] == expected.peak_discharge_m3s
        used = entry["parameters"]
        assert used["total_mm"] == 45.0 and used["area_km2"] == 12.0
        assert used["cn"] == 75 and used["tc_min"] == 90.0
        assert used["total_effective_mm"] == reference().total_effective_mm
        assert all(
            isinstance(value, int | float) and not isinstance(value, bool)
            for value in used.values()
        ), "numbers only: the names of the model and of the shape are in the document"
        assert "model" not in entry and "peak_attenuation_pct" not in entry

    def test_a_given_source_and_a_made_one_share_a_document_and_a_step(self):
        content = document(
            source("B", [0, 4, 12, 8, 3, 0, 0, 0]),
            made("A"),
            junction("J", "A", "B"),
            outlet("J"),
        )

        result = route_network(network=content).result

        by_id = {node["id"]: node for node in result.nodes}
        assert result.timestep_min == 10.0
        assert "parameters" in by_id["A"] and "parameters" not in by_id["B"]
        assert by_id["J"]["volume_m3"] == pytest.approx(
            by_id["A"]["volume_m3"] + by_id["B"]["volume_m3"]
        )

    def test_the_rain_of_the_document_is_the_default_of_the_nodes_without_one(self):
        own = {**RAIN, "total_mm": 20}
        content = document(
            made("A", rainfall=None),
            made("B", rainfall=own),
            junction("J", "A", "B"),
            outlet("J"),
            rainfall=RAIN,
            timestep_min=10,
        )

        result = route_network(network=content).result

        by_id = {node["id"]: node for node in result.nodes}
        assert result.timestep_min == 10.0
        assert by_id["A"]["parameters"]["total_mm"] == 45.0
        assert by_id["B"]["parameters"]["total_mm"] == 20.0
        assert by_id["A"]["parameters"]["timestep_min"] == 10.0


class TestTheNotices:
    def test_a_notice_begins_with_the_id_of_its_node(self):
        content = stream(rainfall={**RAIN, "duration_min": 62})

        notices = route_network(network=content).notices

        by_code = {notice.code: notice for notice in notices}
        assert by_code["duration_not_covered"].level == "warning"
        assert by_code["duration_not_covered"].message.startswith("A: ")
        assert by_code["tail_extended"].message.startswith("R: ")

    def test_a_warning_of_the_library_is_a_notice_and_is_not_printed(self):
        flat = {**WATERSHED, "length_km": 12.0, "elevation_max_m": 220.0}
        content = stream(watershed=flat, runoff={"model": "curve-number"})

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            notices = route_network(network=content).notices

        (warned,) = [notice for notice in notices if notice.code == "user_warning"]
        assert warned.level == "warning"
        assert (
            warned.message.startswith("A: ")
            and "outside typical range" in warned.message
        )


class TestTheTables:
    def test_the_table_of_a_made_node_is_the_hydrograph_of_the_generator(
        self, tmp_path
    ):
        directory = tmp_path / "out"

        output = route_network(network=stream(), output_dir=directory)

        expected = reference().hydrograph
        table = Hydrograph(expected.times_min, expected.discharge_m3s).to_table()
        assert (directory / "A.csv").read_text(encoding="utf-8") == table
        assert sorted(path.name for path in output.files) == [
            "A.csv",
            "OUT.csv",
            "R.csv",
        ]


class TestBadDocuments:
    @pytest.mark.parametrize(
        ("content", "reason", "facts"),
        [
            (
                stream(times_min=[0, 10], discharge_m3s=[0, 1]),
                "conflict",
                {"node_id": "A", "field": "times_min"},
            ),
            (
                stream(value_column="A"),
                "conflict",
                {"node_id": "A", "field": "value_column"},
            ),
            (
                stream(rainfall={**RAIN, "total_mm": -5}),
                "exclusive_minimum",
                {"node_id": "A", "field": "rainfall.total_mm"},
            ),
            (
                stream(rainfall={**RAIN, "kind": "radar"}),
                "unknown_kind",
                {"node_id": "A", "field": "rainfall.kind"},
            ),
            (
                stream(runoff={"model": "curve-number", "uh_model": "nash"}),
                "required",
                {"node_id": "A", "field": "runoff.nash_n"},
            ),
            (
                stream(watershed={**WATERSHED, "colour": "green"}),
                "unknown_field",
                {"node_id": "A", "field": "watershed.colour"},
            ),
            (
                stream(watershed={**WATERSHED, "cn": None}),
                "missing_field",
                {"node_id": "A", "field": "watershed.cn"},
            ),
            (
                stream(rainfall=None),
                "missing_field",
                {"node_id": "A", "field": "rainfall"},
            ),
            (
                {**stream(), "timestep_min": -1},
                "exclusive_minimum",
                {"field": "timestep_min"},
            ),
        ],
    )
    def test_what_is_wrong_names_the_node_and_the_field_whatever_the_source(
        self, content, reason, facts, tmp_path
    ):
        inline, from_file = refused(content, tmp_path)

        assert inline.details["option"] == "network"
        assert from_file.details["path"] == str(tmp_path / "network.json")
        for error in (inline, from_file):
            assert error.details["reason"] == reason
            assert {key: error.details.get(key) for key in facts} == facts
        assert inline.code == "validation_error" and from_file.code == "data_error"

    def test_a_step_that_the_sources_do_not_share_stays_a_validation_error(
        self, tmp_path
    ):
        series = {"kind": "series", "depths_mm": [0, 3, 8], "timestep_min": 15}
        content = document(
            made("A", rainfall=series),
            source("B"),
            junction("J", "A", "B"),
            outlet("J"),
        )

        for run in (
            lambda: load_network(network=content),
            lambda: load_network(network_file=written(tmp_path, content)),
        ):
            with pytest.raises(InvalidParameterError) as caught:
                run()
            assert caught.value.details["reason"] == "timestep_mismatch"
            assert caught.value.details["nodes"] == ["A", "B"]


class TestInflows:
    def test_an_inflows_file_that_no_source_reads_is_refused_when_all_make_theirs(
        self, tmp_path
    ):
        inflows = tmp_path / "inflows.csv"
        inflows.write_text("time_min,A\n0,0\n10,1\n", encoding="utf-8")

        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=stream(), inflows_file=inflows)

        assert caught.value.details == {"option": "inflows_file", "reason": "conflict"}

    def test_a_given_source_still_reads_its_column_next_to_a_made_one(self, tmp_path):
        inflows = tmp_path / "inflows.csv"
        flow = [0, 4, 12, 8, 3, 0, 0, 0]
        rows = ["time_min,B"] + [
            f"{time},{value}"
            for time, value in zip(range(0, 80, 10), flow, strict=True)
        ]
        inflows.write_text("\n".join(rows) + "\n", encoding="utf-8")
        content = document(
            made("A"),
            {"id": "B", "type": "subcatchment"},
            junction("J", "A", "B"),
            outlet("J"),
        )

        loaded = load_network(network=content, inflows_file=inflows)

        assert loaded.network.order == ("A", "B", "J", "OUT")
        assert loaded.network.timestep_min == 10.0
