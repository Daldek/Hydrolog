"""Tests of ``route network``: the summary, the tables of the nodes and their plan.

The references are the elements themselves: a network with one reach writes the table
that the single command writes, every method reached through a document equals the
element it makes, and the order of the nodes in the document changes nothing. The files
follow the plain mode of DEV section 19: one table per node in one directory, planned
before anything is computed, written through a staging directory, never over an input.
"""

import errno
import json
import os
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import check_command, run_command
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_hydrograph
from hydrolog.cli.main import main
from hydrolog.exceptions import (
    CalculationError,
    ConflictError,
    InputDataError,
    InvalidParameterError,
    OutputError,
)
from hydrolog.operations import (
    NetworkRouteResult,
    route_lag,
    route_muskingum,
    route_network,
)
from hydrolog.operations._network_input import load_network
from hydrolog.routing import (
    CascadeReach,
    Hydrograph,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    RoutingNetwork,
)

from ._network_documents import (
    FLOOD,
    SMALL,
    TIMES,
    confluence,
    document,
    junction,
    outlet,
    reach,
    source,
    stream,
    written,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"
FIXTURE_NETWORK = FIXTURES / "network_flood.json"
FIXTURE_INFLOWS = FIXTURES / "network_inflows.csv"
FIXTURE_NODES = ["A", "B", "R1", "J1", "D", "OUT"]
POND_TABLE = "storage_m3,outflow_m3s\n0,0\n30000,10\n90000,40\n180000,100\n"
STAGING = ".hydrolog-incoming"


def fixture(**options) -> OperationOutput:
    """Route the fixture network, which needs its files."""
    return route_network(
        network_file=FIXTURE_NETWORK, inflows_file=FIXTURE_INFLOWS, **options
    )


def tables_of(directory: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(directory.iterdir())
    }


@pytest.fixture(autouse=True)
def _stable_environment(monkeypatch):
    monkeypatch.setenv("COLUMNS", "100")


class TestTheSummary:
    def test_every_node_has_its_peak_and_volume_in_the_order_of_evaluation(self):
        output = route_network(network=confluence())

        result = output.result
        assert isinstance(result, NetworkRouteResult)
        assert result.name is None and result.outlet == "OUT"
        assert result.timestep_min == 10.0
        assert result.order == ["A", "B", "R", "J", "OUT"]
        assert [node["id"] for node in result.nodes] == result.order
        by_id = {node["id"]: node for node in result.nodes}
        assert by_id["A"]["type"] == "subcatchment" and by_id["A"]["from"] == []
        assert (by_id["A"]["peak_m3s"], by_id["A"]["time_to_peak_min"]) == (90.0, 30.0)
        assert by_id["A"]["volume_m3"] == pytest.approx(144000.0)
        assert by_id["B"]["peak_m3s"] == 12.0
        assert by_id["J"]["from"] == ["R", "B"]
        assert (by_id["J"]["peak_m3s"], by_id["J"]["time_to_peak_min"]) == (75.0, 60.0)
        assert by_id["J"]["volume_m3"] == pytest.approx(144000.0 + 16200.0)
        assert by_id["OUT"]["type"] == "outlet"
        assert by_id["OUT"]["peak_m3s"] == by_id["J"]["peak_m3s"]

    def test_a_reach_reports_what_its_command_reports(self):
        by_id = {n["id"]: n for n in route_network(network=confluence()).result.nodes}

        entry = by_id["R"]
        assert entry["model"] == "lag"
        assert entry["parameters"] == {"lag_min": 25.0, "lag_steps": 2.5}
        assert entry["peak_m3s"] == 75.0
        assert entry["peak_attenuation_pct"] == pytest.approx(100.0 * 15.0 / 90.0)
        assert entry["peak_delay_min"] == 30.0
        assert abs(entry["balance_error_m3"]) < 1e-6
        for other in ("A", "B", "J", "OUT"):
            assert not {"model", "parameters", "balance_error_m3"} & set(by_id[other])

    def test_a_reservoir_reports_its_peak_storage(self):
        by_id = {n["id"]: n for n in fixture().result.nodes}

        pond = by_id["D"]
        assert pond["model"] == "level-pool"
        assert pond["parameters"]["storage_peak_m3"] == pytest.approx(183635.078)
        assert pond["parameters"]["stage_peak_m"] == pytest.approx(102.40553)
        assert pond["peak_m3s"] == pytest.approx(13.86388, rel=1e-6)
        assert pond["peak_delay_min"] == 50.0

    def test_the_name_of_the_document_is_in_the_result(self):
        result = fixture().result

        assert result.name == "Pond catchment"
        assert result.timestep_min == 10.0
        assert result.order == FIXTURE_NODES

    def test_the_notices_of_the_reaches_name_their_node(self):
        notices = route_network(network=confluence()).notices

        assert all(isinstance(notice, Notice) for notice in notices)
        assert [(n.level, n.code) for n in notices] == [
            ("info", "lag_interpolated"),
            ("info", "tail_extended"),
        ]
        assert all(notice.message.startswith("R: ") for notice in notices)

    def test_each_reach_of_the_fixture_gives_its_own_notices(self):
        notices = fixture().notices

        assert [(n.code, n.message.split(":")[0]) for n in notices] == [
            ("timestep_refined", "R1"),
            ("tail_extended", "R1"),
            ("tail_extended", "D"),
        ]

    @staticmethod
    def long_network(steps: int) -> dict:
        times = [10 * step for step in range(steps)]
        wave = [
            round(50 * np.sin(np.pi * step / steps) ** 2, 1) for step in range(steps)
        ]
        return document(
            source("A", wave, times_min=times),
            source("B", wave, times_min=times),
            reach("R", "A"),
            junction("J", "R", "B"),
            outlet("J"),
        )

    def test_a_result_over_a_page_says_how_to_make_it_smaller(self):
        output = route_network(network=self.long_network(400))

        large = [n for n in output.notices if n.code == "large_result"]
        assert [n.level for n in large] == ["warning"]
        assert "`nodes`" in large[0].message and "`output_dir`" in large[0].message
        size = len(output.result.to_json())  # type: ignore[union-attr]
        assert f"{size:,}" in large[0].message
        assert size > 20_000

    def test_a_result_within_a_page_has_no_such_notice(self):
        everything = route_network(network=self.long_network(20))
        one_node = route_network(network=self.long_network(400), nodes=["OUT"])

        assert not [n for n in everything.notices if n.code == "large_result"]
        assert not [n for n in one_node.notices if n.code == "large_result"]

    def test_a_directory_keeps_the_series_out_of_the_result_and_the_notice_away(
        self, tmp_path
    ):
        output = route_network(
            network=self.long_network(400), output_dir=tmp_path / "out"
        )

        assert not [n for n in output.notices if n.code == "large_result"]

    def test_the_series_of_the_selected_nodes_are_in_the_result_without_a_directory(
        self,
    ):
        output = route_network(network=confluence(), nodes=["OUT", "B"])

        by_id = {node["id"]: node for node in output.result.nodes}
        assert [node["id"] for node in output.result.nodes] == [
            "A",
            "B",
            "R",
            "J",
            "OUT",
        ]
        assert set(by_id["OUT"]) >= {"times_min", "discharge_m3s"}
        assert set(by_id["B"]) >= {"times_min", "discharge_m3s"}
        assert not {"times_min", "discharge_m3s"} & set(by_id["R"])
        np.testing.assert_array_equal(by_id["B"]["discharge_m3s"], SMALL)
        expected = RoutingNetwork(load_network(network=confluence()).network.nodes)
        np.testing.assert_array_equal(
            by_id["OUT"]["discharge_m3s"],
            expected.route().hydrographs["OUT"].discharge_m3s,
        )
        assert by_id["OUT"]["times_min"][:3].tolist() == [0.0, 10.0, 20.0]
        assert output.files == ()

    def test_without_nodes_every_series_is_in_the_result_without_a_directory(self):
        nodes = route_network(network=confluence()).result.nodes

        assert all({"times_min", "discharge_m3s"} <= set(node) for node in nodes)

    def test_the_result_is_json_with_the_series_as_lists(self):
        output = route_network(network=confluence(), nodes=["OUT"])

        document_ = output.result.to_dict()  # type: ignore[union-attr]
        json.dumps(document_)
        assert document_["nodes"][-1]["discharge_m3s"][:3] == [0.0, 4.0, 12.0]

    def test_a_check_without_a_directory_computes(self):
        output = route_network(network=confluence(), check=True)

        assert output.check is False
        assert isinstance(output.result, NetworkRouteResult)


class TestTheTables:
    def test_there_is_one_table_per_node_named_by_its_id(self, tmp_path):
        out = tmp_path / "out"

        output = fixture(output_dir=out)

        assert [Path(p).name for p in output.files] == [
            f"{i}.csv" for i in FIXTURE_NODES
        ]
        assert all(Path(p).parent == out for p in output.files)
        assert tables_of(out).keys() == {f"{i}.csv" for i in FIXTURE_NODES}
        assert output.replaced == () and output.check is False
        expected = (
            load_network(network_file=FIXTURE_NETWORK, inflows_file=FIXTURE_INFLOWS)
            .network.route()
            .hydrographs
        )
        for node_id, hydrograph in expected.items():
            text = (out / f"{node_id}.csv").read_text(encoding="utf-8")
            assert text == hydrograph.to_table()
        assert not any(
            "times_min" in node
            for node in output.result.nodes  # type: ignore[union-attr]
        ), "the series are in the files, not in the result"

    def test_nothing_else_is_left_in_the_directory(self, tmp_path):
        out = tmp_path / "out"

        fixture(output_dir=out)

        assert sorted(os.listdir(out)) == sorted(f"{i}.csv" for i in FIXTURE_NODES)
        assert os.listdir(tmp_path) == ["out"]

    def test_a_network_with_one_reach_writes_the_table_of_the_single_command(
        self, tmp_path
    ):
        out = tmp_path / "out"
        single = tmp_path / "lag.csv"

        route_network(network=stream(), output_dir=out)
        route_lag(lag_min=25.0, times_min=TIMES, discharge_m3s=FLOOD, output=single)

        assert (out / "OUT.csv").read_bytes() == single.read_bytes()
        assert (out / "R.csv").read_bytes() == single.read_bytes()

    def test_the_tables_are_the_input_of_every_route_command(self, tmp_path):
        out = tmp_path / "out"
        fixture(output_dir=out)

        again = route_lag(lag_min=30.0, input_file=out / "R1.csv")
        hydrograph = load_hydrograph(input_file=out / "J1.csv")

        assert again.result.inflow_peak_m3s == pytest.approx(22.2318891877)
        assert hydrograph.peak_discharge_m3s == pytest.approx(25.4718891877)

    def test_the_directory_is_made_with_its_parents(self, tmp_path):
        out = tmp_path / "a" / "b" / "c"

        route_network(network=stream(), output_dir=out)

        assert (out / "OUT.csv").is_file()

    def test_a_relative_directory_given_as_a_path_object(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        output = route_network(network=stream(), output_dir=Path("tables"))

        assert (tmp_path / "tables" / "R.csv").is_file()
        assert Path(output.files[0]).name == "A.csv"

    def test_nodes_select_the_tables_and_their_order(self, tmp_path):
        out = tmp_path / "out"

        output = fixture(output_dir=out, nodes=["OUT", "J1"])

        assert [Path(p).name for p in output.files] == ["OUT.csv", "J1.csv"]
        assert sorted(os.listdir(out)) == ["J1.csv", "OUT.csv"]
        assert len(output.result.nodes) == 6  # type: ignore[union-attr]

    def test_an_unknown_node_is_a_validation_error_and_nothing_is_written(
        self, tmp_path
    ):
        out = tmp_path / "out"

        with pytest.raises(InvalidParameterError) as caught:
            fixture(output_dir=out, nodes=["OUT", "X"])

        details = caught.value.details
        assert details["option"] == "nodes" and details["reason"] == "unknown_node"
        assert details["node_id"] == "X"
        assert "A, B, R1" in caught.value.hint
        assert not out.exists()

    @pytest.mark.parametrize(
        ("nodes", "reason"), [("OUT", "type"), ([], "empty"), ([1], "type")]
    )
    def test_nodes_must_be_a_list_of_ids(self, nodes, reason):
        with pytest.raises(InvalidParameterError) as caught:
            route_network(network=stream(), nodes=nodes)

        assert caught.value.details == {
            "option": "nodes",
            "reason": reason,
            **({"expected": "array of strings"} if reason == "type" else {}),
        }

    def test_a_node_named_twice_is_a_conflict(self, tmp_path):
        out = tmp_path / "out"

        with pytest.raises(ConflictError) as caught:
            route_network(network=stream(), output_dir=out, nodes=["A", "OUT", "A"])

        assert caught.value.details["reason"] == "duplicate_output_name"
        assert caught.value.details["paths"] == [str(out / "A.csv")]
        assert not out.exists()

    def test_the_order_of_the_nodes_in_the_document_changes_nothing(self, tmp_path):
        content = json.loads(FIXTURE_NETWORK.read_text(encoding="utf-8"))
        runs = []
        for number, order in enumerate(
            (
                content["nodes"],
                content["nodes"][::-1],
                content["nodes"][2:] + content["nodes"][:2],
            )
        ):
            folder = tmp_path / f"run{number}"
            folder.mkdir()
            (folder / "pond_rating.csv").write_bytes(
                (FIXTURES / "pond_rating.csv").read_bytes()
            )
            network = written(folder, {**content, "nodes": order})
            output = route_network(
                network_file=network,
                inflows_file=FIXTURE_INFLOWS,
                output_dir=folder / "out",
            )
            runs.append((output.result.order, tables_of(folder / "out")))  # type: ignore[union-attr]

        assert runs[0][0] == FIXTURE_NODES
        assert runs[1] == runs[0] and runs[2] == runs[0]

    @pytest.mark.parametrize(
        ("method", "fields", "element"),
        [
            ("lag", {"lag_min": 25}, LagReach(lag_min=25.0)),
            ("muskingum", {"k_min": 40, "x": 0.2}, MuskingumReach(k_min=40.0, x=0.2)),
            (
                "muskingum-cunge",
                {
                    "length_km": 8,
                    "slope_m_per_m": 0.001,
                    "celerity_m_per_s": 1.2,
                    "top_width_m": 25,
                    "reference_discharge_m3s": 10,
                },
                MuskingumCungeReach(
                    length_km=8.0,
                    slope_m_per_m=0.001,
                    celerity_m_per_s=1.2,
                    top_width_m=25.0,
                    reference_discharge_m3s=10.0,
                ),
            ),
            ("cascade", {"n": 3, "k_min": 20}, CascadeReach(n=3.0, k_min=20.0)),
            (
                "level-pool",
                {"rating_file": "pond.csv"},
                LevelPoolReach(
                    storage_m3=[0, 30000, 90000, 180000],
                    outflow_m3s=[0, 10, 40, 100],
                ),
            ),
        ],
    )
    def test_every_method_through_a_document_equals_its_element(
        self, method, fields, element, tmp_path
    ):
        (tmp_path / "pond.csv").write_text(POND_TABLE, encoding="utf-8")
        node = {"id": "R", "type": "reach", "from": ["A"], "method": method, **fields}
        network = written(tmp_path, document(source("A"), node, outlet("R")))

        route_network(network_file=network, output_dir=tmp_path / "out")

        expected = element.route(Hydrograph(TIMES, FLOOD)).outflow.to_table()
        assert (tmp_path / "out" / "OUT.csv").read_text(encoding="utf-8") == expected

    def test_a_reservoir_equals_a_reach_by_level_pool(self, tmp_path):
        (tmp_path / "pond.csv").write_text(POND_TABLE, encoding="utf-8")
        pool = {"from": ["A"], "rating_file": "pond.csv", "subreaches": 2}
        reservoir = {"id": "R", "type": "reservoir", **pool}
        as_reach = {"id": "R", "type": "reach", "method": "level-pool", **pool}
        results = []
        for number, node in enumerate((reservoir, as_reach)):
            folder = tmp_path / str(number)
            folder.mkdir()
            (folder / "pond.csv").write_text(POND_TABLE, encoding="utf-8")
            network = written(folder, document(source("A"), node, outlet("R")))
            route_network(network_file=network, output_dir=folder / "out")
            results.append(tables_of(folder / "out"))

        assert results[0] == results[1]

    def test_the_run_options_of_a_node_reach_its_element(self, tmp_path):
        out = tmp_path / "out"
        content = document(
            source("A"),
            reach("R", "A", initial_outflow_m3s=5.0, extend_min=0),
            outlet("R"),
        )

        route_network(network=content, output_dir=out)

        direct = LagReach(lag_min=25.0).route(
            Hydrograph(TIMES, FLOOD), initial_outflow_m3s=5.0, extend_min=0.0
        )
        assert (out / "R.csv").read_text(encoding="utf-8") == direct.outflow.to_table()
        assert len((out / "R.csv").read_text(encoding="utf-8").splitlines()) == 9

    def test_reaches_in_series_equal_the_sub_reaches_of_one(self):
        # Muskingum with N sub-reaches is N reaches of K / N in series; a fixed
        # extension keeps the cut of the settling tail out of the comparison
        single = route_muskingum(
            k_min=60.0,
            x=0.2,
            subreaches=3,
            times_min=TIMES,
            discharge_m3s=FLOOD,
            extend_min=600,
        ).result

        def link(number: int, upstream: str) -> dict:
            return {
                "id": f"R{number}",
                "type": "reach",
                "from": [upstream],
                "method": "muskingum",
                "k_min": 20.0,
                "x": 0.2,
                "subreaches": 1,
                "extend_min": 600,
            }

        chain = document(
            source("A"), link(1, "A"), link(2, "R1"), link(3, "R2"), outlet("R3")
        )

        routed = route_network(network=chain, nodes=["OUT"]).result.nodes[-1]

        series = np.asarray(routed["discharge_m3s"])
        assert len(single.outflow_m3s) == 68 and len(series) == 188
        np.testing.assert_allclose(
            series[: len(single.outflow_m3s)], single.outflow_m3s, atol=1e-12
        )


class TestExistingTables:
    def planted(self, tmp_path, *names) -> Path:
        out = tmp_path / "out"
        out.mkdir()
        for name in (*names, "notes.txt"):
            (out / name).write_text("mine", encoding="utf-8")
        return out

    def test_existing_tables_are_a_conflict_that_lists_every_path(self, tmp_path):
        out = self.planted(tmp_path, "A.csv", "OUT.csv")
        before = tables_of(out)

        with pytest.raises(ConflictError) as caught:
            fixture(output_dir=out)

        assert caught.value.details == {
            "reason": "output_exists",
            "paths": [str(out / "A.csv"), str(out / "OUT.csv")],
        }
        assert "--force" in caught.value.hint
        assert tables_of(out) == before, "nothing was written"

    def test_force_replaces_the_tables_and_nothing_else(self, tmp_path):
        out = self.planted(tmp_path, "A.csv", "OUT.csv")

        output = fixture(output_dir=out, force=True)

        assert set(output.replaced) == {str(out / "A.csv"), str(out / "OUT.csv")}
        assert (out / "notes.txt").read_text(encoding="utf-8") == "mine"
        assert (out / "A.csv").read_text(encoding="utf-8").startswith("time_min,")
        assert sorted(os.listdir(out)) == sorted(
            [*(f"{i}.csv" for i in FIXTURE_NODES), "notes.txt"]
        )

    def test_the_envelope_says_which_tables_were_replaced(self, tmp_path):
        out = self.planted(tmp_path, "B.csv")
        options = {
            "network_file": str(FIXTURE_NETWORK),
            "inflows_file": str(FIXTURE_INFLOWS),
            "output_dir": str(out),
            "force": True,
        }

        files = run_command("route network", options).to_dict()["result"]["files"]

        assert {Path(f["path"]).name: f["status"] for f in files} == {
            "A.csv": "written",
            "B.csv": "replaced",
            "R1.csv": "written",
            "J1.csv": "written",
            "D.csv": "written",
            "OUT.csv": "written",
        }

    def test_check_plans_every_table_and_writes_nothing(self, tmp_path):
        out = tmp_path / "out"

        output = fixture(output_dir=out, check=True)

        assert output.check is True
        assert not out.exists()
        document_ = output.result
        assert document_["schema"] == "hydrolog-plan/1"  # type: ignore[index]
        assert [
            (Path(t["path"]).name, t["option"], t["action"])
            for t in document_["targets"]  # type: ignore[index]
        ] == [(f"{i}.csv", "output_dir", "write") for i in FIXTURE_NODES]

    def test_a_check_shows_the_conflicts_and_the_replacements(self, tmp_path):
        out = self.planted(tmp_path, "D.csv")

        taken = fixture(output_dir=out, check=True).result["targets"]  # type: ignore[index]
        forced = fixture(output_dir=out, check=True, force=True).result["targets"]  # type: ignore[index]

        assert {
            t["action"]: t.get("reason") for t in taken if t["action"] != "write"
        } == {"conflict": "output_exists"}
        assert [t["action"] for t in forced].count("replace") == 1
        assert not (out / "A.csv").exists()

    def test_a_check_needs_a_valid_network(self, tmp_path):
        with pytest.raises(InvalidParameterError) as caught:
            route_network(
                network=stream(lag_min=-1), output_dir=tmp_path / "out", check=True
            )

        assert caught.value.details["field"] == "lag_min"

    def test_a_table_that_appears_during_the_computation_is_not_replaced(
        self, tmp_path, monkeypatch
    ):
        out = tmp_path / "out"
        out.mkdir()
        route = RoutingNetwork.route

        def late(self):
            (out / "R.csv").write_text("mine", encoding="utf-8")
            return route(self)

        monkeypatch.setattr(RoutingNetwork, "route", late)

        with pytest.raises(ConflictError) as caught:
            route_network(network=stream(), output_dir=out)

        assert caught.value.details["paths"] == [str(out / "R.csv")]
        assert tables_of(out) == {"R.csv": "mine"}, "no table and no staging is left"

    @pytest.mark.parametrize(
        ("marker", "inside"),
        [
            ("kartograf-store.json", ""),
            ("imgw-store.json", ""),
            ("kartograf-store.json", "plain/tables"),
        ],
    )
    def test_a_store_of_another_tool_is_refused(self, marker, inside, tmp_path):
        store = tmp_path / "store"
        store.mkdir()
        (store / marker).write_text("{}", encoding="utf-8")
        out = store / inside if inside else store
        before = sorted(os.listdir(store))

        with pytest.raises(ConflictError) as caught:
            route_network(network=stream(), output_dir=out)

        details = caught.value.details
        assert details["reason"] == "output_in_store"
        assert details["store"] == str(store)
        assert details["paths"] == [str(out / f"{i}.csv") for i in ("A", "R", "OUT")]
        assert "--root" in caught.value.hint
        assert sorted(os.listdir(store)) == before, "nothing was written"

    def test_a_check_of_a_store_is_a_plan_with_conflicts(self, tmp_path):
        (tmp_path / "kartograf-store.json").write_text("{}", encoding="utf-8")

        output = route_network(network=stream(), output_dir=tmp_path, check=True)

        assert {
            (t["action"], t["reason"])
            for t in output.result["targets"]  # type: ignore[index]
        } == {("conflict", "output_in_store")}


class TestTheInputsAreSafe:
    @pytest.mark.parametrize("victim", ["rating_file", "inflows_file", "network_file"])
    @pytest.mark.parametrize("check", [False, True])
    def test_a_table_never_replaces_a_file_the_network_is_read_from(
        self, victim, check, tmp_path
    ):
        folder = tmp_path / "net"
        folder.mkdir()
        rating = folder / ("D.csv" if victim == "rating_file" else "pond.csv")
        inflows = folder / ("A.csv" if victim == "inflows_file" else "inflows.csv")
        rating.write_text(POND_TABLE, encoding="utf-8")
        inflows.write_text(
            "time_min,A\n"
            + "\n".join(f"{t},{q}" for t, q in zip(TIMES, FLOOD, strict=True)),
            encoding="utf-8",
        )
        content = document(
            {"id": "A", "type": "subcatchment"},
            {"id": "D", "type": "reservoir", "from": ["A"], "rating_file": rating.name},
            outlet("D"),
        )
        network = written(
            folder, content, "OUT.csv" if victim == "network_file" else "network.json"
        )
        before = tables_of(folder)

        with pytest.raises(InvalidParameterError) as caught:
            route_network(
                network_file=network,
                inflows_file=inflows,
                output_dir=folder,
                force=True,
                check=check,
            )

        details = caught.value.details
        assert details["option"] == "output_dir" and details["reason"] == "conflict"
        assert details["input"].startswith(victim)
        assert "would overwrite the input file" in str(caught.value)
        assert tables_of(folder) == before


class TestFailures:
    OVERFLOWING = document(
        source("A", [0, 400, 800, 400, 0, 0, 0, 0]),
        {
            "id": "D",
            "type": "reservoir",
            "from": ["A"],
            "storage_m3": [0, 1000, 2000],
            "outflow_m3s": [0, 1, 2],
        },
        outlet("D"),
    )

    def test_nothing_is_written_when_a_reservoir_fills_beyond_its_table(self, tmp_path):
        out = tmp_path / "out"

        with pytest.raises(CalculationError) as caught:
            route_network(network=self.OVERFLOWING, output_dir=out)

        assert caught.value.details["reason"] == "table_exceeded"
        assert caught.value.details["node_id"] == "D"
        assert "Node 'D'" in str(caught.value)
        assert not out.exists()

    def test_an_existing_directory_stays_empty_when_the_routing_fails(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()

        with pytest.raises(CalculationError):
            route_network(network=self.OVERFLOWING, output_dir=out)

        assert os.listdir(out) == [], "no table and no staging directory"

    def test_a_reach_that_cannot_be_routed_names_its_node(self, tmp_path):
        content = stream(
            method="muskingum", lag_min=None, k_min=20, x=0.2, subreaches=50
        )
        del content["nodes"][1]["lag_min"]

        with pytest.raises(InvalidParameterError) as caught:
            route_network(network=content, output_dir=tmp_path / "out")

        assert caught.value.details["reason"] == "unstable_timestep"
        assert caught.value.details["node_id"] == "R"
        assert not (tmp_path / "out").exists()

    def test_a_failure_while_moving_names_what_was_already_written(
        self, tmp_path, monkeypatch
    ):
        out = tmp_path / "out"
        replace = os.replace
        calls = []

        def flaky(source, target):
            calls.append(target)
            if len(calls) == 3:
                raise OSError(errno.EIO, "disk error")
            replace(source, target)

        monkeypatch.setattr(os, "replace", flaky)

        with pytest.raises(OutputError) as caught:
            route_network(network=stream(), output_dir=out)

        details = caught.value.details
        assert details["reason"] == "output_unwritable"
        assert details["path"] == str(out)
        assert details["written"] == [str(out / "A.csv"), str(out / "R.csv")]
        assert "details.written" in caught.value.hint
        assert sorted(os.listdir(out)) == ["A.csv", "R.csv"], "staging is removed"

    def test_a_directory_that_cannot_be_made_is_an_output_error(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed", encoding="utf-8")

        with pytest.raises(OutputError) as caught:
            route_network(network=stream(), output_dir=blocker / "out")

        assert caught.value.details == {
            "path": str(blocker / "out"),
            "reason": "output_unwritable",
        }
        assert caught.value.hint is None
        assert os.listdir(tmp_path) == ["blocker"]

    def test_a_broken_network_file_writes_nothing(self, tmp_path):
        network = written(tmp_path, stream(lag_min=0))

        with pytest.raises(InputDataError) as caught:
            route_network(network_file=network, output_dir=tmp_path / "out")

        assert caught.value.details["path"] == str(network)
        assert not (tmp_path / "out").exists()


class TestTheCommand:
    def test_the_envelope_lists_the_files_and_echoes_the_options(self, tmp_path):
        out = tmp_path / "out"

        envelope = run_command(
            "route network",
            {
                "network_file": str(FIXTURE_NETWORK),
                "inflows_file": str(FIXTURE_INFLOWS),
                "output_dir": str(out),
            },
        ).to_dict()

        assert envelope["result"]["schema"] == "hydrolog-route-network/1"
        assert [Path(f["path"]).name for f in envelope["result"]["files"]] == [
            f"{i}.csv" for i in FIXTURE_NODES
        ]
        assert envelope["inputs"]["output_dir"] == str(out)
        assert envelope["inputs"]["force"] is False
        assert envelope["notices"][0]["message"].startswith("R1: ")

    def test_check_command_gives_the_plan_of_the_directory(self, tmp_path):
        envelope = check_command(
            "route network",
            {"network": stream(), "output_dir": str(tmp_path / "out")},
        ).to_dict()

        assert envelope["check"] is True
        assert envelope["result"]["schema"] == "hydrolog-plan/1"
        assert len(envelope["result"]["targets"]) == 3

    def test_both_sources_or_none_are_refused_by_the_catalog(self):
        for options in ({}, {"network": stream(), "network_file": "x.json"}):
            with pytest.raises(InvalidParameterError) as caught:
                run_command("route network", options)
            assert caught.value.details["reason"] == "one_of"


def _json_run(capsys, *argv):
    code = main([*argv, "--json"])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestOnTheCommandLine:
    BASE = (
        "route",
        "network",
        "--network-file",
        str(FIXTURE_NETWORK),
        "--inflows-file",
        str(FIXTURE_INFLOWS),
    )

    def test_the_short_flag_and_nodes_write_the_selected_tables(self, capsys, tmp_path):
        out = tmp_path / "out"

        code, stdout, stderr = _json_run(
            capsys, *self.BASE, "-o", str(out), "--nodes", "OUT,D"
        )

        assert (code, stderr) == (0, "")
        files = json.loads(stdout)["result"]["files"]
        assert [Path(f["path"]).name for f in files] == ["OUT.csv", "D.csv"]
        assert sorted(os.listdir(out)) == ["D.csv", "OUT.csv"]

    def test_the_long_flag_is_the_same_option(self, capsys, tmp_path):
        out = tmp_path / "out"

        code, _, stderr = _json_run(capsys, *self.BASE, "--output-dir", str(out))

        assert (code, stderr) == (0, "")
        assert len(os.listdir(out)) == len(FIXTURE_NODES)

    def test_check_prints_the_plan_and_creates_nothing(self, capsys, tmp_path):
        out = tmp_path / "out"

        code, stdout, _ = _json_run(capsys, *self.BASE, "-o", str(out), "--check")

        document_ = json.loads(stdout)
        assert code == 0 and document_["check"] is True
        assert len(document_["result"]["targets"]) == len(FIXTURE_NODES)
        assert not out.exists()

    def test_existing_tables_are_a_conflict_with_the_exit_code_4(
        self, capsys, tmp_path
    ):
        out = tmp_path / "out"
        main([*self.BASE, "-o", str(out), "--json"])
        capsys.readouterr()

        code = main([*self.BASE, "-o", str(out), "--lang", "en"])
        err = capsys.readouterr().err

        assert code == 4
        lines = err.splitlines()
        assert lines[0] == "Error (conflict): State conflict"
        assert "already exists" in lines[1]
        assert f"    {out / 'A.csv'}" in lines
        assert len([line for line in lines if line.startswith("    ")]) == 6
        assert json.loads(lines[-1])["details"]["reason"] == "output_exists"

    def test_a_store_is_refused_in_both_languages(self, capsys, tmp_path):
        (tmp_path / "imgw-store.json").write_text("{}", encoding="utf-8")
        out = tmp_path / "tables"

        code = main([*self.BASE, "-o", str(out), "--nodes", "OUT", "--lang", "en"])
        english = capsys.readouterr().err
        main([*self.BASE, "-o", str(out), "--nodes", "OUT", "--lang", "pl"])
        polish = capsys.readouterr().err

        assert code == 4
        assert "The output directory lies in the store of another tool" in english
        assert f"    {out / 'OUT.csv'}" in english.splitlines()
        assert "own --root" in english
        assert "Katalog wyjściowy leży w magazynie innego narzędzia" in polish
        assert "--root" in polish.splitlines()[-2]
        assert not out.exists()

    def test_the_plan_of_a_store_is_readable(self, capsys, tmp_path):
        (tmp_path / "kartograf-store.json").write_text("{}", encoding="utf-8")

        code = main([*self.BASE, "-o", str(tmp_path), "--check", "--lang", "en"])
        stdout = capsys.readouterr().out

        assert code == 0
        assert "the directory is in the store of" in stdout, "the note wraps in a cell"
        assert "another tool" in stdout
        assert "Running without --check would fail" in stdout

    def test_a_broken_network_file_has_the_exit_code_7(self, capsys, tmp_path):
        network = written(tmp_path, stream(lag_min=0))

        code, _, err = _json_run(
            capsys, "route", "network", "--network-file", str(network)
        )

        document_ = json.loads(err.splitlines()[-1])
        assert code == 7 and document_["code"] == "data_error"
        assert document_["details"]["path"] == str(network)

    def test_an_inline_network_is_json_text_and_a_broken_one_has_the_exit_code_2(
        self, capsys
    ):
        good = json.dumps(stream())
        code, stdout, _ = _json_run(capsys, "route", "network", "--network", good)
        assert code == 0
        assert json.loads(stdout)["result"]["outlet"] == "OUT"

        cycle = json.dumps(
            document(source("A"), junction("J", "A", "R"), reach("R", "J"), outlet("R"))
        )
        code, _, err = _json_run(capsys, "route", "network", "--network", cycle)

        document_ = json.loads(err.splitlines()[-1])
        assert code == 2 and document_["details"]["reason"] == "cycle"
        assert document_["details"]["option"] == "network"

    def test_the_summary_in_words_lists_the_nodes_and_the_files(self, capsys, tmp_path):
        out = tmp_path / "out"

        code = main([*self.BASE, "-o", str(out), "--lang", "en"])
        stdout = capsys.readouterr().out

        assert code == 0
        assert stdout.splitlines()[0].startswith("route network: Route hydrographs")
        assert "nodes (6):" in stdout and "model:" in stdout
        assert f"Files:\n  {out / 'A.csv'}  (written," in stdout
