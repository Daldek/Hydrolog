"""Tests of ``route network --schematic``: the SVG file and the document (ADR-0013).

The file follows the rules of every file that a command writes: planned before anything
is computed, never over an input file or another output, replaced only with ``force``,
written through a temporary file. The result carries the document that the drawing is
made of, with the values of the run, and a main stem can be declared.
"""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from hydrolog.catalog import check_command, run_command
from hydrolog.cli.main import main
from hydrolog.exceptions import (
    CalculationError,
    ConflictError,
    InvalidParameterError,
    OutputError,
)
from hydrolog.operations import route_network
from hydrolog.routing import RoutingNetwork
from hydrolog.routing.schematic import schematic_svg

from ._network_documents import confluence, document, outlet, source, written
from ._schematic_checks import random_tree
from ._schematic_networks import network_of

FIXTURES = Path(__file__).parents[1] / "fixtures"
FIXTURE_NETWORK = FIXTURES / "network_flood.json"
FIXTURE_INFLOWS = FIXTURES / "network_inflows.csv"
SVG = "{http://www.w3.org/2000/svg}"


def files_of(output) -> list[str]:
    return sorted(Path(item).name for item in output.files)


class TestTheFileAndTheDocument:
    def test_the_drawing_is_the_svg_of_the_document_the_result_returns(self, tmp_path):
        target = tmp_path / "net.svg"

        output = route_network(network=confluence(), schematic=target)

        drawn = output.result.schematic  # type: ignore[union-attr]
        text = target.read_text(encoding="utf-8")
        assert text == schematic_svg(drawn)
        assert ET.fromstring(text).tag == f"{SVG}svg"
        assert [Path(item) for item in output.files] == [target]
        assert drawn["schema"] == "hydrolog-network-schematic/1"
        assert drawn["has_result"] is True

    def test_the_values_of_the_document_are_those_of_the_summary(self, tmp_path):
        output = route_network(network=confluence(), schematic=tmp_path / "net.svg")

        result = output.result
        nodes = {entry["id"]: entry for entry in result.nodes}  # type: ignore[union-attr]
        for node in result.schematic["nodes"]:  # type: ignore[union-attr]
            assert node["peak_m3s"] == nodes[node["id"]]["peak_m3s"]
            assert node["time_to_peak_min"] == nodes[node["id"]]["time_to_peak_min"]
            assert node["volume_m3"] == nodes[node["id"]]["volume_m3"]

    def test_the_document_is_that_of_the_network_that_was_routed(self, tmp_path):
        output = route_network(network=confluence(), schematic=tmp_path / "net.svg")

        network = RoutingNetwork.from_document(confluence())
        assert output.result.schematic == network.schematic(  # type: ignore[union-attr]
            network.route()
        )

    def test_without_a_schematic_the_result_has_none_and_nothing_is_written(
        self, tmp_path
    ):
        output = route_network(network=confluence())

        assert output.result.schematic is None  # type: ignore[union-attr]
        assert output.files == ()

    def test_the_schematic_shows_every_node_whatever_nodes_says(self, tmp_path):
        output = route_network(
            network=confluence(), nodes=["OUT"], schematic=tmp_path / "net.svg"
        )

        shown = [n["id"] for n in output.result.schematic["nodes"]]  # type: ignore[union-attr]
        assert sorted(shown) == ["A", "B", "J", "OUT", "R"]

    def test_the_directory_and_the_schematic_are_written_together(self, tmp_path):
        out = tmp_path / "out"

        output = route_network(
            network=confluence(), output_dir=out, schematic=tmp_path / "net.svg"
        )

        tables = ["A.csv", "B.csv", "J.csv", "OUT.csv", "R.csv"]
        assert files_of(output) == [*tables, "net.svg"]
        assert sorted(os.listdir(out)) == tables
        assert (tmp_path / "net.svg").is_file()

    def test_the_schematic_of_the_fixture_network_draws_its_reservoir(self, tmp_path):
        target = tmp_path / "pond.svg"

        output = route_network(
            network_file=FIXTURE_NETWORK, inflows_file=FIXTURE_INFLOWS, schematic=target
        )

        drawn = output.result.schematic  # type: ignore[union-attr]
        assert {n["id"]: n["type"] for n in drawn["nodes"]}["D"] == "reservoir"
        assert drawn["name"] == "Pond catchment"
        text = target.read_text(encoding="utf-8")
        assert "D (reservoir)" in text
        assert '<title id="title">Pond catchment</title>' in text

    def test_a_large_network_does_not_make_its_schematic_a_large_result(self, tmp_path):
        root, inflows = random_tree(60, 4, fan_in=3, deep=0.3)
        inline = network_of(root, inflows).to_document()

        output = route_network(
            network=inline, nodes=["END"], schematic=tmp_path / "net.svg"
        )

        size = len(output.result.to_json())  # type: ignore[union-attr]
        assert size > 20_000, "the schematic makes the result longer than a page"
        assert not [n for n in output.notices if n.code == "large_result"]


class TestTheMainStem:
    def test_a_declared_main_stem_is_drawn(self, tmp_path):
        default = route_network(network=confluence(), schematic=tmp_path / "a.svg")
        declared = route_network(
            network=confluence(), schematic=tmp_path / "b.svg", main_stem=["B"]
        )

        assert default.result.schematic["lines"][0]["nodes"] == [  # type: ignore[union-attr]
            "A",
            "R",
            "J",
            "OUT",
        ]
        assert declared.result.schematic["lines"][0]["nodes"] == ["B", "J", "OUT"]  # type: ignore[union-attr]

    def test_a_main_stem_without_a_schematic_is_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            route_network(network=confluence(), main_stem=["A"])

        assert caught.value.details == {"option": "main_stem", "reason": "conflict"}

    @pytest.mark.parametrize(
        ("main_stem", "reason", "node"),
        [
            (["nothing"], "unknown_node", "nothing"),
            (["A", "B"], "main_stem_not_a_path", "B"),
        ],
    )
    def test_nodes_that_are_not_a_path_are_refused_before_anything_is_written(
        self, tmp_path, main_stem, reason, node
    ):
        out = tmp_path / "out"

        with pytest.raises(InvalidParameterError) as caught:
            route_network(
                network=confluence(),
                output_dir=out,
                schematic=tmp_path / "net.svg",
                main_stem=main_stem,
            )

        assert caught.value.details["option"] == "main_stem"
        assert caught.value.details["reason"] == reason
        assert caught.value.details["node_id"] == node
        assert not out.exists() and not (tmp_path / "net.svg").exists()

    def test_a_check_refuses_the_same_main_stem(self, tmp_path):
        with pytest.raises(InvalidParameterError) as caught:
            route_network(
                network=confluence(),
                schematic=tmp_path / "net.svg",
                main_stem=["nothing"],
                check=True,
            )

        assert caught.value.details["reason"] == "unknown_node"


class TestThePlan:
    def test_an_existing_file_is_a_conflict_and_force_replaces_it(self, tmp_path):
        target = tmp_path / "net.svg"
        target.write_text("old", encoding="utf-8")

        with pytest.raises(ConflictError) as caught:
            route_network(network=confluence(), schematic=target)
        assert caught.value.details == {
            "reason": "output_exists",
            "paths": [str(target)],
        }
        assert target.read_text(encoding="utf-8") == "old"

        output = route_network(network=confluence(), schematic=target, force=True)
        assert output.replaced == (str(target),)
        assert target.read_text(encoding="utf-8").startswith("<svg")

    def test_a_check_plans_the_file_and_creates_nothing(self, tmp_path):
        target = tmp_path / "net.svg"

        plan = route_network(network=confluence(), schematic=target, check=True)

        assert plan.check is True
        assert plan.result == {
            "schema": "hydrolog-plan/1",
            "targets": [
                {"option": "schematic", "path": str(target), "action": "write"}
            ],
        }
        assert not target.exists()

    def test_a_check_plans_the_tables_and_the_file_together(self, tmp_path):
        out = tmp_path / "out"
        target = tmp_path / "net.svg"
        target.write_text("old", encoding="utf-8")

        plan = route_network(
            network=confluence(), output_dir=out, schematic=target, check=True
        )

        targets = plan.result["targets"]  # type: ignore[index]
        assert [item["option"] for item in targets] == ["output_dir"] * 5 + [
            "schematic"
        ]
        assert targets[-1] == {
            "option": "schematic",
            "path": str(target),
            "action": "conflict",
            "reason": "output_exists",
        }
        assert not out.exists()

    def test_a_file_that_is_one_of_the_tables_is_a_conflict(self, tmp_path):
        out = tmp_path / "out"

        plan = route_network(
            network=confluence(), output_dir=out, schematic=out / "A.csv", check=True
        )
        with pytest.raises(ConflictError) as caught:
            route_network(network=confluence(), output_dir=out, schematic=out / "A.csv")

        targets = plan.result["targets"]  # type: ignore[index]
        assert targets[-1]["reason"] == "duplicate_output_name"
        assert caught.value.details["reason"] == "duplicate_output_name"
        assert caught.value.details["paths"] == [str(out / "A.csv")]
        assert not out.exists()

    def test_the_schematic_never_replaces_a_file_the_network_is_read_from(
        self, tmp_path
    ):
        network_file = written(tmp_path, confluence())

        with pytest.raises(InvalidParameterError) as caught:
            route_network(network_file=network_file, schematic=network_file, force=True)

        assert caught.value.details["option"] == "schematic"
        assert json.loads(network_file.read_text(encoding="utf-8"))["schema"]

    def test_a_check_without_a_file_to_write_computes_as_before(self):
        output = route_network(network=confluence(), check=True)

        assert output.check is False
        assert output.result.schematic is None  # type: ignore[union-attr]

    def test_nothing_is_written_when_the_routing_fails(self, tmp_path):
        target = tmp_path / "net.svg"
        out = tmp_path / "out"
        overflowing = document(
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

        with pytest.raises(CalculationError):
            route_network(network=overflowing, output_dir=out, schematic=target)

        assert not target.exists() and not out.exists()

    def test_a_file_that_cannot_be_written_names_the_tables_that_were(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed", encoding="utf-8")
        out = tmp_path / "out"

        with pytest.raises(OutputError) as caught:
            route_network(
                network=confluence(), output_dir=out, schematic=blocker / "net.svg"
            )

        details = caught.value.details
        assert details["reason"] == "output_unwritable"
        assert details["path"] == str(blocker / "net.svg")
        assert sorted(Path(item).name for item in details["written"]) == [
            "A.csv",
            "B.csv",
            "J.csv",
            "OUT.csv",
            "R.csv",
        ]
        assert "details.written" in caught.value.hint

    def test_a_file_that_cannot_be_made_alone_is_an_output_error_without_a_hint(
        self, tmp_path
    ):
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")

        with pytest.raises(OutputError) as caught:
            route_network(network=confluence(), schematic=blocker / "net.svg")

        assert "written" not in caught.value.details
        assert caught.value.hint is None


class TestTheEnvelopeAndTheCommandLine:
    BASE = (
        "route",
        "network",
        "--network-file",
        str(FIXTURE_NETWORK),
        "--inflows-file",
        str(FIXTURE_INFLOWS),
    )

    def test_the_envelope_lists_the_file_and_carries_the_document(self, tmp_path):
        target = tmp_path / "net.svg"

        envelope = run_command(
            "route network",
            {
                "network_file": str(FIXTURE_NETWORK),
                "inflows_file": str(FIXTURE_INFLOWS),
                "schematic": str(target),
            },
        ).to_dict()

        result = envelope["result"]
        assert [Path(item["path"]) for item in result["files"]] == [target]
        assert result["files"][0]["status"] == "written"
        assert result["schematic"]["schema"] == "hydrolog-network-schematic/1"
        assert envelope["inputs"]["schematic"] == str(target)

    def test_check_command_plans_the_file(self, tmp_path):
        plan = check_command(
            "route network",
            {
                "network_file": str(FIXTURE_NETWORK),
                "inflows_file": str(FIXTURE_INFLOWS),
                "schematic": str(tmp_path / "net.svg"),
            },
        ).to_dict()["result"]

        assert [item["option"] for item in plan["targets"]] == ["schematic"]

    def test_the_flags_write_the_drawing_and_json_returns_the_document(
        self, capsys, tmp_path
    ):
        target = tmp_path / "net.svg"

        code = main(
            [*self.BASE, "--schematic", str(target), "--main-stem", "B", "--json"]
        )

        out = capsys.readouterr()
        assert (code, out.err) == (0, "")
        envelope = json.loads(out.out)
        assert envelope["result"]["schematic"]["lines"][0]["nodes"] == [
            "B",
            "J1",
            "D",
            "OUT",
        ]
        assert target.read_text(encoding="utf-8") == schematic_svg(
            envelope["result"]["schematic"]
        )

    @pytest.mark.parametrize(
        ("lang", "summary"),
        [
            ("en", "nodes: 6, lines: 2, grid 4 x 1 (document: --json)"),
            ("pl", "węzły: 6, linie: 2, siatka 4 × 1 (dokument: --json)"),
        ],
    )
    def test_the_summary_names_the_size_of_the_schematic_and_the_file(
        self, capsys, tmp_path, lang, summary
    ):
        target = tmp_path / "net.svg"

        code = main(
            [*self.BASE, "--schematic", str(target), "--nodes", "OUT", "--lang", lang]
        )

        text = capsys.readouterr().out
        assert code == 0
        assert summary in text
        assert str(target) in text
        assert "hydrolog-network-schematic" not in text, "the document is not dumped"
        assert "label" not in text

    def test_an_existing_drawing_is_a_conflict_with_the_exit_code_4(
        self, capsys, tmp_path
    ):
        target = tmp_path / "net.svg"
        main([*self.BASE, "--schematic", str(target), "--json"])
        capsys.readouterr()

        code = main([*self.BASE, "--schematic", str(target), "--lang", "en"])

        assert code == 4
        assert str(target) in capsys.readouterr().err

    def test_check_prints_the_plan_of_the_drawing(self, capsys, tmp_path):
        target = tmp_path / "net.svg"

        code = main([*self.BASE, "--schematic", str(target), "--check", "--lang", "en"])

        assert code == 0
        assert "schematic" in capsys.readouterr().out
        assert not target.exists()

    def test_a_main_stem_without_a_drawing_has_the_exit_code_2(self, capsys):
        code = main([*self.BASE, "--main-stem", "B", "--lang", "en"])

        assert code == 2
        assert "'main_stem'" in capsys.readouterr().err
