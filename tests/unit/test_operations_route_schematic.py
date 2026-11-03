"""``route schematic``: the schematic of a network without routing it (ADR-0013)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hydrolog.catalog import get_command, run_command
from hydrolog.catalog.groups.route import _TWO_SOURCES
from hydrolog.exceptions import InputDataError, InvalidParameterError
from hydrolog.operations import RouteSchematicResult, route_schematic
from hydrolog.operations._network_input import load_network

FIXTURES = Path(__file__).parents[1] / "fixtures"
FIXTURE_NETWORK = FIXTURES / "network_flood.json"
FIXTURE_INFLOWS = FIXTURES / "network_inflows.csv"
SCHEMA = "hydrolog-network-schematic/1"


def _result(options: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = run_command("route schematic", options).to_dict()[
        "result"
    ]
    return result


class TestTheDocument:
    def test_an_inline_network_gives_the_schematic_of_the_library(self):
        expected = load_network(network=_TWO_SOURCES).network.schematic()

        result = _result({"network": _TWO_SOURCES})

        assert result == {"schema": SCHEMA, **expected}
        assert list(result)[0] == "schema"
        assert result["has_result"] is False

    def test_a_network_file_with_its_inflows_gives_the_schematic_of_the_library(self):
        loaded = load_network(
            network_file=FIXTURE_NETWORK, inflows_file=FIXTURE_INFLOWS
        )

        result = _result(
            {
                "network_file": str(FIXTURE_NETWORK),
                "inflows_file": str(FIXTURE_INFLOWS),
            }
        )

        assert result == {"schema": SCHEMA, **loaded.network.schematic()}
        assert result["name"] == "Pond catchment"

    def test_the_function_returns_the_document_itself(self):
        result = route_schematic(network=_TWO_SOURCES)
        expected = load_network(network=_TWO_SOURCES).network.schematic()

        assert isinstance(result, RouteSchematicResult)
        assert result.to_dict() == expected
        assert type(result.to_dict()) is dict

    def test_a_network_without_its_inflows_is_refused(self):
        with pytest.raises(InputDataError) as caught:
            route_schematic(network_file=FIXTURE_NETWORK)

        assert caught.value.details["reason"] == "missing_field"


class TestTheMainStem:
    def test_a_declared_main_stem_is_the_first_line(self):
        graph = load_network(network=_TWO_SOURCES).network

        result = _result({"network": _TWO_SOURCES, "main_stem": ["B"]})

        assert result == {"schema": SCHEMA, **graph.schematic(main_stem=["B"])}
        assert result["lines"][0]["nodes"] == ["B", "J1", "OUT"]  # type: ignore[index]

    @pytest.mark.parametrize(
        ("main_stem", "reason", "node"),
        [
            (["nothing"], "unknown_node", "nothing"),
            (["A", "B"], "main_stem_not_a_path", "B"),
        ],
    )
    def test_a_main_stem_that_is_not_a_path_is_refused_as_the_option(
        self, main_stem, reason, node
    ):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "route schematic", {"network": _TWO_SOURCES, "main_stem": main_stem}
            )

        assert caught.value.details["option"] == "main_stem"
        assert caught.value.details["reason"] == reason
        assert caught.value.details["node_id"] == node


class TestNoEffects:
    def test_nothing_is_written_beside_the_files_it_reads(self, tmp_path):
        network = shutil.copy(FIXTURE_NETWORK, tmp_path / "network.json")
        inflows = shutil.copy(FIXTURE_INFLOWS, tmp_path / "inflows.csv")
        shutil.copy(FIXTURES / "pond_rating.csv", tmp_path / "pond_rating.csv")
        before = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*")}

        envelope = run_command(
            "route schematic", {"network_file": network, "inflows_file": inflows}
        ).to_dict()

        assert {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*")} == before
        assert "files" not in envelope["result"]

    def test_the_command_is_read_only_and_has_no_check(self):
        command = get_command("route schematic")

        assert command.effects.read_only is True
        assert command.effects.destructive is False
        assert command.check is None
        assert "check" not in {option.name for option in command.options}
