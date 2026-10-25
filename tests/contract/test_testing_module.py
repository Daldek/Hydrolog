"""``hydrolog.testing`` builds what the ``hydrolog`` program writes (DEV-10.6).

Every builder is compared with the real command run as a program: the tables with the
files of ``route network --output-dir`` and ``route lag --output``, the envelope with
the line that ``precip hietogram --json`` prints, and the documents with the shipped
JSON Schema and the command that reads them. A consumer that tests against the builders
then breaks when a format changes, at Hydrolog's release and not at its users.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import hydrolog
from hydrolog import testing
from hydrolog.exceptions import InvalidParameterError

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "src" / "hydrolog" / "schemas"


def program(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run ``hydrolog`` as a program; the process must end with 0."""
    done = subprocess.run(
        [sys.executable, "-m", "hydrolog.cli", *arguments, "--lang", "en"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return done


def tables(directory: Path) -> dict[str, bytes]:
    """Name to bytes of every file of ``directory``."""
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


def lag_network() -> dict[str, Any]:
    """Inline sources A and B, a lag reach below A, a junction and the outlet."""
    times = [0, 10, 20, 30, 40, 50]
    return testing.network_document(
        testing.subcatchment(
            "A", times_min=times, discharge_m3s=[0, 10, 40, 90, 60, 30]
        ),
        testing.subcatchment("B", times_min=times, discharge_m3s=[0, 4, 12, 8, 3, 0]),
        testing.reach("R", "A", method="lag", lag_min=25),
        testing.junction("J", "R", "B"),
        testing.outlet("J"),
        name="Inline",
    )


def test_the_fixture_tables_are_the_files_that_route_network_writes_from_its_files(
    tmp_path: Path,
) -> None:
    case = testing.build_network_fixture(tmp_path / "case")

    program(
        "route",
        "network",
        "--network-file",
        str(case.network_file),
        "--inflows-file",
        str(case.inflows_file),
        "--output-dir",
        str(tmp_path / "real"),
        "--json",
    )

    assert tables(case.output_dir) == tables(tmp_path / "real")
    assert sorted(tables(case.output_dir)) == sorted(f"{n}.csv" for n in case.nodes)


def test_the_tables_of_an_inline_network_are_the_files_that_route_network_writes(
    tmp_path: Path,
) -> None:
    document = lag_network()
    network_file = testing.write_network_document(tmp_path / "network.json", document)

    program(
        "route",
        "network",
        "--network-file",
        str(network_file),
        "--output-dir",
        str(tmp_path / "real"),
        "--json",
    )

    written = testing.write_network_tables(tmp_path / "built", document)
    assert {p.name: p.read_bytes() for p in written} == tables(tmp_path / "real")
    assert {n: t.encode() for n, t in testing.network_tables(document).items()} == (
        tables(tmp_path / "real")
    )


def test_a_hydrograph_table_is_the_file_that_route_lag_writes(tmp_path: Path) -> None:
    source = tmp_path / "in.csv"
    source.write_text(testing.hydrograph_table([0, 5, 10], [0, 1.5, 0]), "utf-8")

    program(
        "route",
        "lag",
        "--input-file",
        str(source),
        "--lag-min",
        "7",
        "--output",
        str(tmp_path / "out.csv"),
        "--json",
    )

    written = (tmp_path / "out.csv").read_bytes()
    header, *rows = written.decode("utf-8").splitlines()
    times, flows = zip(*(map(float, row.split(",")) for row in rows), strict=True)
    assert header == "time_min,discharge_m3s"
    assert testing.hydrograph_table(times, flows).encode("utf-8") == written
    assert b"\r" not in written
    assert written.endswith(b"\n")


def test_a_table_that_is_not_a_hydrograph_is_refused() -> None:
    with pytest.raises(InvalidParameterError):
        testing.hydrograph_table([0, 5, 11], [0, 1, 0])


def test_the_envelope_is_the_line_that_precip_hietogram_prints(tmp_path: Path) -> None:
    options: dict[str, Any] = {
        "hietogram_type": "beta",
        "total_mm": 25.5,
        "duration_min": 90.0,
        "timestep_min": 15.0,
        "alpha": 2.5,
    }

    printed = program(
        "precip",
        "hietogram",
        *(f"--{name.replace('_', '-')}={value}" for name, value in options.items()),
        "--json",
    ).stdout

    file = testing.write_hietogram_envelope(tmp_path / "rain" / "h.json", **options)
    assert file.read_text("utf-8") == printed
    assert testing.hietogram_envelope(**options) == json.loads(printed)
    assert printed.count("\n") == 1


def test_the_default_envelope_is_the_euler_ii_design_of_40_mm_in_an_hour() -> None:
    envelope = testing.hietogram_envelope()

    assert envelope["schema"] == "hydrolog-result/1"
    assert envelope["command"] == "precip hietogram"
    assert envelope["version"] == hydrolog.__version__
    result = envelope["result"]
    assert result["schema"] == "hydrolog-precip-hietogram/1"
    assert (result["hietogram_type"], result["n_steps"]) == ("euler_ii", 6)
    assert sum(result["depths_mm"]) == pytest.approx(40.0)


def test_an_option_that_does_not_apply_to_the_type_is_refused() -> None:
    with pytest.raises(InvalidParameterError):
        testing.hietogram_envelope(hietogram_type="block", alpha=2.0)


def test_the_documents_validate_against_the_shipped_schema_and_the_command_reads_them(
    tmp_path: Path,
) -> None:
    schema = json.loads((SCHEMAS / "hydrolog-network-1.schema.json").read_text("utf-8"))
    case = testing.build_network_fixture(tmp_path / "case")
    documents = [
        json.loads(case.network_file.read_text("utf-8")),
        lag_network(),
    ]

    for document in documents:
        Draft202012Validator(schema).validate(document)
        assert document["schema"] == testing.NETWORK_SCHEMA
    network_file = testing.write_network_document(tmp_path / "lag.json", documents[1])
    printed = program("route", "network", "--network-file", str(network_file), "--json")
    assert json.loads(printed.stdout)["result"]["outlet"] == "OUT"


def test_a_network_that_the_command_would_refuse_is_refused_when_it_is_built() -> None:
    with pytest.raises(InvalidParameterError) as unknown:
        testing.network_document(
            testing.subcatchment("A"),
            testing.reach("R", "NOWHERE", method="lag", lag_min=5),
            testing.outlet("R"),
        )
    with pytest.raises(InvalidParameterError) as nothing:
        testing.network_document(testing.subcatchment("A"))

    assert unknown.value.details["reason"] == "unknown_upstream"
    assert nothing.value.details["reason"] == "no_outlet"


def test_two_builds_are_the_same_bytes(tmp_path: Path) -> None:
    first = testing.build_network_fixture(tmp_path / "first")
    second = testing.build_network_fixture(tmp_path / "second")

    assert tables(first.output_dir) == tables(second.output_dir)
    assert first.network_file.read_bytes() == second.network_file.read_bytes()
    assert first.inflows_file.read_bytes() == second.inflows_file.read_bytes()
    assert testing.hietogram_envelope() == testing.hietogram_envelope()
    assert testing.network_tables(lag_network()) == testing.network_tables(
        lag_network()
    )
