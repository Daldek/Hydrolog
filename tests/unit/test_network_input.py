"""Tests of the network document ``hydrolog-network/1`` and of reading it.

A document is read into a :class:`~hydrolog.routing.RoutingNetwork`; what is wrong with
it is an error of the source it came from (a data error for a file, a validation error
for the inline option) with the same reason, the node and the field. The structure
rules are the ones of the library and are tested there: here they must arrive through
the document with their reasons.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from hydrolog.exceptions import InputDataError, InvalidParameterError, NotFoundError
from hydrolog.operations._network_input import SCHEMA, LoadedNetwork, load_network
from hydrolog.routing import (
    CascadeReach,
    Hydrograph,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
)

from ._network_documents import (
    FLOOD,
    SMALL,
    TIMES,
    document,
    outlet,
    reach,
    source,
    stream,
    written,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"


def refused(
    content, tmp_path, **options
) -> tuple[InvalidParameterError, InputDataError]:
    """The two errors that a document gives: inline, and from a file."""
    with pytest.raises(InvalidParameterError) as inline:
        load_network(network=content, **options)
    with pytest.raises(InputDataError) as from_file:
        load_network(network_file=written(tmp_path, content), **options)
    return inline.value, from_file.value


class TestTheFixture:
    def test_the_fixture_network_is_read_with_its_files(self):
        loaded = load_network(
            network_file=FIXTURES / "network_flood.json",
            inflows_file=FIXTURES / "network_inflows.csv",
        )

        assert isinstance(loaded, LoadedNetwork)
        network = loaded.network
        assert network.name == "Pond catchment"
        assert network.order == ("A", "B", "R1", "J1", "D", "OUT")
        assert network.outlet == "OUT"
        assert network.timestep_min == 10.0
        assert [n.kind for n in network.nodes] == [
            "subcatchment",
            "subcatchment",
            "reach",
            "junction",
            "reservoir",
            "outlet",
        ]
        assert isinstance(network.node("R1").reach, MuskingumCungeReach)
        assert isinstance(network.node("D").reach, LevelPoolReach)
        assert loaded.rating_files == {"D": (FIXTURES / "pond_rating.csv").resolve()}

    def test_a_source_reads_the_column_of_its_id_or_its_value_column(self):
        network = load_network(
            network_file=FIXTURES / "network_flood.json",
            inflows_file=FIXTURES / "network_inflows.csv",
        ).network

        by_id = network.node("A").hydrograph
        by_column = network.node("B").hydrograph
        assert by_id is not None and by_column is not None
        assert by_id.discharge_m3s[:3].tolist() == [1.2, 2.48, 7.44]
        assert by_column.discharge_m3s[:3].tolist() == [0.8, 3.98, 5.75]
        assert by_id.timestep_min == 10.0 and len(by_id) == 31


class TestAnInlineNetwork:
    def test_it_gives_the_network_that_is_built_by_hand(self):
        loaded = load_network(
            network=document(
                source("A"),
                source("B", SMALL),
                reach("R", "A"),
                {"id": "J", "type": "junction", "from": ["R", "B"]},
                outlet("J"),
                name="two",
            )
        )

        network = loaded.network
        assert network.name == "two" and loaded.rating_files == {}
        assert network.order == ("A", "B", "R", "J", "OUT")
        result = network.route()
        lagged = LagReach(lag_min=25).route(Hydrograph(TIMES, FLOOD))
        expected = lagged.outflow.discharge_m3s.copy()
        expected[: len(SMALL)] += SMALL
        np.testing.assert_allclose(result.hydrographs["J"].discharge_m3s, expected)

    def test_the_schema_is_required_and_must_be_the_one_this_reads(self, tmp_path):
        assert (
            load_network(network={**stream(), "schema": SCHEMA}).network.outlet == "OUT"
        )

        without = {key: value for key, value in stream().items() if key != "schema"}
        inline, from_file = refused(without, tmp_path)
        for error in (inline, from_file):
            assert error.details["reason"] == "missing_field"
            assert error.details["field"] == "schema"

        for wrong in ("hydrolog-network/2", None):
            inline, from_file = refused({**stream(), "schema": wrong}, tmp_path)
            for error in (inline, from_file):
                assert error.details["reason"] == "unknown_schema"
                assert error.details["expected"] == SCHEMA

    @pytest.mark.parametrize(
        ("method", "fields", "expected"),
        [
            ("lag", {"lag_min": 25}, LagReach),
            ("muskingum", {"k_min": 40, "x": 0.2, "subreaches": 2}, MuskingumReach),
            (
                "muskingum-cunge",
                {
                    "length_km": 8,
                    "slope_m_per_m": 0.001,
                    "celerity_m_per_s": 1.2,
                    "top_width_m": 25,
                    "reference_discharge_m3s": 10,
                },
                MuskingumCungeReach,
            ),
            ("cascade", {"n": 3, "k_min": 20}, CascadeReach),
            (
                "level-pool",
                {"storage_m3": [0, 30000, 90000], "outflow_m3s": [0, 10, 40]},
                LevelPoolReach,
            ),
        ],
    )
    def test_every_method_makes_its_element(self, method, fields, expected):
        node = {"id": "R", "type": "reach", "from": ["A"], "method": method, **fields}

        element = (
            load_network(network=document(source("A"), node, outlet("R")))
            .network.node("R")
            .reach
        )

        assert type(element) is expected

    def test_a_reservoir_takes_a_table_inline(self):
        node = {
            "id": "D",
            "type": "reservoir",
            "from": ["A"],
            "storage_m3": [0, 30000, 90000, 180000],
            "outflow_m3s": [0, 10, 40, 100],
            "stage_m": [0, 0.8, 1.9, 3.4],
            "subreaches": 2,
            "initial_outflow_m3s": 1.5,
            "extend_min": 0,
        }

        network = load_network(network=document(source("A"), node, outlet("D"))).network

        pool = network.node("D")
        assert isinstance(pool.reach, LevelPoolReach)
        assert pool.reach.subreaches == 2
        assert pool.reach.stage_m is not None
        assert (pool.initial_outflow_m3s, pool.extend_min) == (1.5, 0.0)

    def test_the_run_options_of_a_reach_reach_its_node(self):
        node = load_network(
            network=stream(initial_outflow_m3s=2.5, extend_min=30)
        ).network.node("R")

        assert (node.initial_outflow_m3s, node.extend_min) == (2.5, 30.0)

    def test_a_null_is_a_field_that_is_not_given(self):
        network = load_network(
            network={
                **stream(initial_outflow_m3s=None, extend_min=None),
                "name": None,
            }
        ).network

        assert network.node("R").initial_outflow_m3s is None
        assert network.name is None

    def test_the_order_of_the_nodes_changes_nothing(self):
        nodes = [source("A"), source("B", SMALL), reach("R", "A")]
        nodes += [{"id": "J", "type": "junction", "from": ["R", "B"]}, outlet("J")]
        forward = load_network(network=document(*nodes)).network
        backward = load_network(network=document(*reversed(nodes))).network

        assert forward.order == backward.order == ("A", "B", "R", "J", "OUT")
        np.testing.assert_array_equal(
            forward.route().hydrographs["OUT"].discharge_m3s,
            backward.route().hydrographs["OUT"].discharge_m3s,
        )


class TestBadDocuments:
    @pytest.mark.parametrize(
        ("content", "reason", "facts"),
        [
            ([1, 2], "shape", {}),
            (
                {"nodes": [source("A")], "color": "blue"},
                "unknown_field",
                {"field": "color"},
            ),
            ({"schema": SCHEMA, "name": "x"}, "missing_field", {"field": "nodes"}),
            ({"schema": SCHEMA, "nodes": {"A": 1}}, "type", {"field": "nodes"}),
            ({**stream(), "name": ""}, "type", {"field": "name"}),
            ({"schema": SCHEMA, "nodes": [5]}, "shape", {"index": 0}),
            (document({"type": "outlet"}), "missing_field", {"field": "id"}),
            (document({"id": 7, "type": "outlet"}), "invalid_id", {"index": 0}),
            (
                document({"id": "x y", "type": "outlet", "from": ["a"]}),
                "invalid_id",
                {},
            ),
            (
                document({"id": "Nul", "type": "outlet", "from": ["a"]}),
                "reserved_name",
                {"node_id": "Nul"},
            ),
            (document({"id": "A"}), "missing_field", {"node_id": "A", "field": "type"}),
            (
                document({"id": "A", "type": "river"}),
                "unknown_type",
                {"node_id": "A", "value": "river"},
            ),
            (
                document(source("A", lag_min=5)),
                "unknown_field",
                {"node_id": "A", "field": "lag_min"},
            ),
            (
                document(source("A"), {**outlet("A"), "lag_min": 5}),
                "unknown_field",
                {"node_id": "OUT", "field": "lag_min"},
            ),
            (
                document(source("A"), {**reach("R", "A"), "k_min": 5}),
                "unknown_field",
                {"node_id": "R", "field": "k_min"},
            ),
            (
                document(source("A"), {**reach("R", "A"), "times_min": [0, 10]}),
                "unknown_field",
                {"node_id": "R", "field": "times_min"},
            ),
            (
                document(source("A"), {**reach("R", "A"), "method": None}),
                "missing_field",
                {"node_id": "R", "field": "method"},
            ),
            (
                document(source("A"), reach("R", "A", method="kinematic")),
                "unknown_method",
                {"node_id": "R", "value": "kinematic"},
            ),
            (
                document(source("A"), {**reach("R", "A"), "lag_min": None}),
                "missing_field",
                {"node_id": "R", "field": "lag_min"},
            ),
            (stream(lag_min="long"), "type", {"node_id": "R", "field": "lag_min"}),
            (
                stream(lag_min=0),
                "exclusive_minimum",
                {"node_id": "R", "field": "lag_min"},
            ),
            (stream(extend_min=-1), "minimum", {"node_id": "R", "field": "extend_min"}),
            (
                stream(**{"from": "A"}),
                "type",
                {"node_id": "R", "field": "from"},
            ),
            (
                document(source("A", discharge=None), reach("R", "A"), outlet("R")),
                "missing_field",
                {"node_id": "A", "field": "discharge_m3s"},
            ),
            (
                document(
                    source("A", discharge=[1, -2, 3, 4, 5, 6, 7, 8]),
                    reach("R", "A"),
                    outlet("R"),
                ),
                "minimum",
                {"node_id": "A", "field": "discharge_m3s"},
            ),
            (
                document(source("A", value_column="A"), reach("R", "A"), outlet("R")),
                "conflict",
                {"node_id": "A", "field": "value_column"},
            ),
        ],
    )
    def test_a_field_that_is_wrong_names_the_node_and_the_field(
        self, content, reason, facts, tmp_path
    ):
        inline, from_file = refused(content, tmp_path)

        assert inline.details["option"] == "network"
        assert from_file.details["path"] == str(tmp_path / "network.json")
        for error in (inline, from_file):
            assert error.details["reason"] == reason
            assert {key: error.details.get(key) for key in facts} == facts
        assert inline.code == "validation_error" and from_file.code == "data_error"
        assert str(tmp_path / "network.json") in str(from_file)
        assert str(inline).count("Option 'network'") == 1, "the source is named once"
        assert str(from_file).count(str(tmp_path / "network.json")) == 1

    def test_a_node_that_is_wrong_is_named_in_the_message(self, tmp_path):
        inline, from_file = refused(stream(lag_min=0), tmp_path)

        assert "Node 'R'" in str(inline) and "Node 'R'" in str(from_file)
        assert "lag_min" in str(inline)

    @pytest.mark.parametrize(
        ("nodes", "reason", "facts"),
        [
            ([], "empty", {}),
            (
                [source("A"), reach("R", "A", **{"from": ["X"]}), outlet("R")],
                "unknown_upstream",
                {"node_id": "R", "upstream_id": "X"},
            ),
            (
                [
                    source("A"),
                    {"id": "J", "type": "junction", "from": ["A", "R"]},
                    reach("R", "J"),
                    outlet("R"),
                ],
                "cycle",
                {"nodes": ["J", "R"]},
            ),
            (
                [
                    source("A"),
                    reach("R1", "A"),
                    reach("R2", "A"),
                    {"id": "J", "type": "junction", "from": ["R1", "R2"]},
                    outlet("J"),
                ],
                "several_downstream",
                {"node_id": "A", "downstream": ["R1", "R2"]},
            ),
            ([source("A"), reach("R", "A")], "no_outlet", {}),
            (
                [
                    source("A"),
                    reach("R", "A"),
                    outlet("R"),
                    source("B"),
                    outlet("B", "END"),
                ],
                "several_outlets",
                {"nodes": ["END", "OUT"]},
            ),
            (
                [source("A"), reach("R", "A"), outlet("R"), reach("S", "OUT")],
                "outlet_has_downstream",
                {"node_id": "OUT", "downstream": ["S"]},
            ),
            (
                [source("A"), source("B"), reach("R", "A"), outlet("R")],
                "disconnected_node",
                {"node_id": "B"},
            ),
            (
                [source("A"), source("a"), reach("R", "A"), outlet("R")],
                "duplicate_node",
                {"node_id": "a", "other_id": "A"},
            ),
            (
                [source("A"), reach("R", "A", **{"from": ["A", "A"]}), outlet("R")],
                "upstream_count",
                {"node_id": "R", "found": 2},
            ),
            (
                [
                    source("A"),
                    {"id": "J", "type": "junction", "from": ["A", "A"]},
                    outlet("J"),
                ],
                "duplicate_upstream",
                {"node_id": "J"},
            ),
            (
                [{**source("A"), "from": ["A"]}, outlet("A")],
                "upstream_count",
                {"node_id": "A"},
            ),
        ],
    )
    def test_the_structure_rules_of_the_library_arrive_with_their_reasons(
        self, nodes, reason, facts, tmp_path
    ):
        inline, from_file = refused(document(*nodes), tmp_path)

        for error in (inline, from_file):
            assert error.details["reason"] == reason
            for key, value in facts.items():
                assert error.details[key] == value, key
        assert inline.details["option"] == "network"
        assert from_file.details["path"] == str(tmp_path / "network.json")

    def test_sources_with_different_axes_stay_a_validation_error_from_a_file(
        self, tmp_path
    ):
        steps = document(
            source("A"),
            {**source("B"), "times_min": [0, 5, 10, 15, 20, 25, 30, 35]},
            {"id": "J", "type": "junction", "from": ["A", "B"]},
            outlet("J"),
        )
        starts = document(
            source("A"),
            {**source("B"), "times_min": [10, 20, 30, 40, 50, 60, 70, 80]},
            {"id": "J", "type": "junction", "from": ["A", "B"]},
            outlet("J"),
        )

        with pytest.raises(InvalidParameterError) as step:
            load_network(network_file=written(tmp_path, steps))
        with pytest.raises(InvalidParameterError) as start:
            load_network(network_file=written(tmp_path, starts, "other.json"))

        assert step.value.details["reason"] == "timestep_mismatch"
        assert start.value.details["reason"] == "start_mismatch"
        assert step.value.code == start.value.code == "validation_error"


class TestTheSourceOfTheDocument:
    def test_exactly_one_of_the_two_sources(self, tmp_path):
        path = written(tmp_path, stream())
        for options in ({}, {"network": stream(), "network_file": path}):
            with pytest.raises(InvalidParameterError) as caught:
                load_network(**options)
            assert caught.value.details["reason"] == "one_of"

    def test_a_missing_file_is_not_found(self, tmp_path):
        with pytest.raises(NotFoundError):
            load_network(network_file=tmp_path / "absent.json")

    def test_a_file_that_is_not_json_is_a_data_error(self, tmp_path):
        path = written(tmp_path, "{not json")

        with pytest.raises(InputDataError) as caught:
            load_network(network_file=path)

        assert caught.value.details["reason"] == "invalid_json"
        assert caught.value.details["path"] == str(path)

    def test_an_inline_document_must_be_json_native(self):
        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=document({"id": "A", "type": object()}))

        assert caught.value.details["option"] == "network"

    def test_a_network_that_is_not_a_mapping_is_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=[1, 2])  # type: ignore[arg-type]

        assert caught.value.details["option"] == "network"
        assert caught.value.details["reason"] == "shape"


class TestInflows:
    def stream_of_columns(self) -> dict:
        return document(
            {"id": "A", "type": "subcatchment"},
            {"id": "B", "type": "subcatchment", "value_column": "tributary"},
            {"id": "J", "type": "junction", "from": ["A", "B"]},
            outlet("J"),
        )

    def inflows(self, tmp_path, header="time_min,A,tributary", name="inflows.csv"):
        rows = ["0,1,2", "10,3,4", "20,5,6"]
        path = tmp_path / name
        path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
        return path

    def test_the_columns_are_read_by_the_id_and_by_the_value_column(self, tmp_path):
        network = load_network(
            network=self.stream_of_columns(), inflows_file=self.inflows(tmp_path)
        ).network

        assert network.node("A").hydrograph.discharge_m3s.tolist() == [1, 3, 5]
        assert network.node("B").hydrograph.discharge_m3s.tolist() == [2, 4, 6]
        assert network.node("A").hydrograph.times_min.tolist() == [0, 10, 20]

    def test_the_time_column_is_named_by_an_option(self, tmp_path):
        inflows = self.inflows(tmp_path, header="minutes,A,tributary")

        network = load_network(
            network=self.stream_of_columns(),
            inflows_file=inflows,
            time_column="minutes",
        ).network

        assert network.node("A").hydrograph.times_min.tolist() == [0, 10, 20]

    def test_a_json_table_of_columns_is_read_too(self, tmp_path):
        path = tmp_path / "inflows.json"
        path.write_text(
            json.dumps(
                {"time_min": [0, 10, 20], "A": [1, 3, 5], "tributary": [2, 4, 6]}
            ),
            encoding="utf-8",
        )

        network = load_network(
            network=self.stream_of_columns(), inflows_file=path
        ).network

        assert network.node("B").hydrograph.discharge_m3s.tolist() == [2, 4, 6]

    def test_a_column_with_a_unit_is_found_by_its_name(self, tmp_path):
        inflows = self.inflows(tmp_path, header="time_min,A [m3/s],tributary")

        network = load_network(
            network=self.stream_of_columns(), inflows_file=inflows
        ).network

        assert network.node("A").hydrograph.discharge_m3s.tolist() == [1, 3, 5]

    def test_a_missing_column_names_the_node_and_the_file(self, tmp_path):
        inflows = self.inflows(tmp_path, header="time_min,A,other")

        with pytest.raises(InputDataError) as caught:
            load_network(network=self.stream_of_columns(), inflows_file=inflows)

        details = caught.value.details
        assert details["reason"] == "missing_column"
        assert details["node_id"] == "B" and details["column"] == "tributary"
        assert details["path"] == str(inflows)
        assert "Node 'B'" in str(caught.value)

    def test_a_table_that_breaks_a_rule_names_the_node_and_the_row(self, tmp_path):
        path = tmp_path / "inflows.csv"
        path.write_text(
            "time_min,A,tributary\n0,1,2\n10,-3,4\n20,5,6\n", encoding="utf-8"
        )

        with pytest.raises(InputDataError) as caught:
            load_network(network=self.stream_of_columns(), inflows_file=path)

        assert caught.value.details["reason"] == "negative"
        assert (caught.value.details["node_id"], caught.value.details["row"]) == (
            "A",
            2,
        )

    def test_a_missing_inflows_file_is_not_found(self, tmp_path):
        with pytest.raises(NotFoundError):
            load_network(
                network=self.stream_of_columns(), inflows_file=tmp_path / "none.csv"
            )

    def test_a_source_without_discharges_needs_the_inflows_file(self):
        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=self.stream_of_columns())

        assert caught.value.details["reason"] == "missing_field"
        assert caught.value.details["node_id"] == "A"
        assert "inflows_file" in caught.value.hint

    def test_an_inflows_file_that_no_source_reads_is_refused(self, tmp_path):
        inflows = self.inflows(tmp_path)

        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=stream(), inflows_file=inflows)

        assert caught.value.details == {"option": "inflows_file", "reason": "conflict"}

    def test_a_time_column_without_an_inflows_file_is_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=stream(), time_column="minutes")

        assert caught.value.details == {"option": "time_column", "reason": "conflict"}

    def test_inline_and_file_sources_mix(self, tmp_path):
        mixed = document(
            source("A"),
            {"id": "B", "type": "subcatchment", "value_column": "tributary"},
            {"id": "J", "type": "junction", "from": ["A", "B"]},
            outlet("J"),
        )
        inflows = tmp_path / "inflows.csv"
        rows = zip(TIMES, SMALL, strict=True)
        lines = ["time_min,tributary"] + [f"{t},{q}" for t, q in rows]
        inflows.write_text("\n".join(lines) + "\n", encoding="utf-8")

        network = load_network(network=mixed, inflows_file=inflows).network

        assert network.node("B").hydrograph.discharge_m3s.tolist() == SMALL
        assert network.node("A").hydrograph.discharge_m3s.tolist() == FLOOD


class TestRatingFiles:
    TABLE = "storage_m3,outflow_m3s\n0,0\n30000,10\n90000,40\n180000,100\n"

    def pond(self, **fields) -> dict:
        return document(
            source("A"),
            {"id": "D", "type": "reservoir", "from": ["A"], **fields},
            outlet("D"),
        )

    def test_a_rating_file_is_relative_to_the_directory_of_the_network_file(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "ratings").mkdir()
        rating = tmp_path / "ratings" / "pond.csv"
        rating.write_text(self.TABLE, encoding="utf-8")
        path = written(tmp_path, self.pond(rating_file="ratings/pond.csv"))
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)  # the working directory does not matter

        loaded = load_network(network_file=path)

        reservoir = loaded.network.node("D").reach
        assert isinstance(reservoir, LevelPoolReach)
        assert reservoir.storage_m3.tolist() == [0, 30000, 90000, 180000]
        assert loaded.rating_files == {"D": rating.resolve()}

    def test_a_rating_file_of_a_reach_by_level_pool_is_read_too(self, tmp_path):
        (tmp_path / "pond.csv").write_text(self.TABLE, encoding="utf-8")
        node = {
            "id": "R",
            "type": "reach",
            "from": ["A"],
            "method": "level-pool",
            "rating_file": "pond.csv",
        }

        loaded = load_network(
            network_file=written(tmp_path, document(source("A"), node, outlet("R")))
        )

        assert isinstance(loaded.network.node("R").reach, LevelPoolReach)
        assert set(loaded.rating_files) == {"R"}

    @pytest.mark.parametrize(
        "name", ["../pond.csv", "sub/../../pond.csv", "/etc/passwd"]
    )
    def test_a_rating_file_outside_the_directory_is_refused(self, name, tmp_path):
        directory = tmp_path / "net"
        directory.mkdir()
        (tmp_path / "pond.csv").write_text(self.TABLE, encoding="utf-8")

        with pytest.raises(InputDataError) as caught:
            load_network(network_file=written(directory, self.pond(rating_file=name)))

        details = caught.value.details
        assert details["reason"] == "path_outside"
        assert (details["node_id"], details["field"]) == ("D", "rating_file")
        assert details["value"] == name
        assert "directory of the network file" in str(caught.value)

    def test_a_link_that_leads_out_of_the_directory_is_refused(self, tmp_path):
        directory = tmp_path / "net"
        directory.mkdir()
        outside = tmp_path / "secret"
        outside.mkdir()
        (outside / "pond.csv").write_text(self.TABLE, encoding="utf-8")
        (directory / "linked").symlink_to(outside, target_is_directory=True)
        (directory / "pond.csv").symlink_to(outside / "pond.csv")

        for name in ("linked/pond.csv", "pond.csv"):
            with pytest.raises(InputDataError) as caught:
                load_network(
                    network_file=written(directory, self.pond(rating_file=name))
                )
            assert caught.value.details["reason"] == "path_outside", name

    def test_an_absolute_path_inside_the_directory_is_fine(self, tmp_path):
        rating = tmp_path / "pond.csv"
        rating.write_text(self.TABLE, encoding="utf-8")

        loaded = load_network(
            network_file=written(tmp_path, self.pond(rating_file=str(rating)))
        )

        assert loaded.rating_files == {"D": rating.resolve()}

    def test_an_inline_network_cannot_name_a_file(self, tmp_path):
        (tmp_path / "pond.csv").write_text(self.TABLE, encoding="utf-8")

        with pytest.raises(InvalidParameterError) as caught:
            load_network(network=self.pond(rating_file=str(tmp_path / "pond.csv")))

        details = caught.value.details
        assert details["reason"] == "inline_file" and details["node_id"] == "D"
        assert details["option"] == "network"
        assert "network_file" in caught.value.hint

    def test_a_missing_rating_file_names_the_node(self, tmp_path):
        with pytest.raises(NotFoundError) as caught:
            load_network(
                network_file=written(tmp_path, self.pond(rating_file="absent.csv"))
            )

        assert caught.value.details["node_id"] == "D"
        assert "absent.csv" in caught.value.details["path"]
        assert "Node 'D'" in str(caught.value)

    def test_a_rating_table_that_breaks_a_rule_names_the_node_and_the_row(
        self, tmp_path
    ):
        (tmp_path / "pond.csv").write_text(
            "storage_m3,outflow_m3s\n0,0\n30000,10\n20000,40\n", encoding="utf-8"
        )

        with pytest.raises(InputDataError) as caught:
            load_network(
                network_file=written(tmp_path, self.pond(rating_file="pond.csv"))
            )

        details = caught.value.details
        assert details["node_id"] == "D" and details["row"] == 3
        assert details["path"] == str(tmp_path / "pond.csv")

    def test_a_table_and_a_file_together_are_refused(self, tmp_path):
        (tmp_path / "pond.csv").write_text(self.TABLE, encoding="utf-8")
        both = self.pond(rating_file="pond.csv", storage_m3=[0, 1], outflow_m3s=[0, 1])

        with pytest.raises(InputDataError) as caught:
            load_network(network_file=written(tmp_path, both))

        assert caught.value.details["reason"] == "one_of"
        assert caught.value.details["node_id"] == "D"

    def test_a_stage_with_a_rating_file_is_a_conflict(self, tmp_path):
        (tmp_path / "pond.csv").write_text(self.TABLE, encoding="utf-8")

        with pytest.raises(InputDataError) as caught:
            load_network(
                network_file=written(
                    tmp_path, self.pond(rating_file="pond.csv", stage_m=[0, 1])
                )
            )

        assert caught.value.details["reason"] == "conflict"
        assert caught.value.details["field"] == "stage_m"

    def test_a_broken_inline_table_is_the_error_of_the_option(self):
        with pytest.raises(InvalidParameterError) as caught:
            load_network(
                network=self.pond(storage_m3=[0, 100, 50], outflow_m3s=[0, 1, 2])
            )

        details = caught.value.details
        assert details["option"] == "network" and details["node_id"] == "D"
        assert details["field"] == "storage_m3"
