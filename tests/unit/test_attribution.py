"""The providers' lines in every product (Nogat DEV §20, ADR-0028).

The lines are legal texts that must stay byte for byte as the providers' terms and
Nogat's standard give them, so the first tests quote them in full.
"""

import json
from pathlib import Path

import pytest

import hydrolog
from hydrolog._attribution import (
    CHMI_PROCESSED,
    CHMI_SOURCE,
    IMGW_HYDRO,
    IMGW_PROCESSED,
    IMGW_SOURCE,
    IMGW_TERMS,
    PMAXTP_MONOGRAPH,
    PMAXTP_PROCESSED,
    PMAXTP_SOURCE,
    TERMS_DANEPUBLICZNE,
    TERMS_HYDRO,
    TERMS_PMAXTP,
    Attribution,
    attribution_text,
    csv_with_attribution,
    provider_lines,
)
from hydrolog.catalog.inputs import read_table
from hydrolog.cli.main import main
from hydrolog.exceptions import InvalidParameterError
from hydrolog.testing import example_network_document

FIXTURES = Path(__file__).parents[1] / "fixtures"
OBSERWATOR_CHMI_PROCESSED = (
    "Dane ČHMÚ zostały przetworzone (normalizacja i zmiana formatu)"
)
"""What Obserwator writes it did with ČHMÚ's data."""


class TestTheLines:
    """The lines are those of DEV §20, byte for byte."""

    def test_imgw_pib(self):
        assert IMGW_SOURCE == (
            "Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej "
            "– Państwowy Instytut Badawczy"
        )
        assert IMGW_PROCESSED == (
            "Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu "
            "Badawczego zostały przetworzone"
        )
        assert IMGW_HYDRO == (
            "Dane pochodzą z serwisu hydrologicznego IMGW-PIB https://hydro.imgw.pl"
        )

    def test_pmaxtp(self):
        assert PMAXTP_SOURCE == (
            "Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej "
            "– Państwowy Instytut Badawczy, dane pochodzą ze strony "
            "https://klimat.imgw.pl/opady-maksymalne"
        )
        assert PMAXTP_PROCESSED == (
            "Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu "
            "Badawczego pochodzące ze strony https://klimat.imgw.pl/opady-maksymalne "
            "zostały przetworzone"
        )
        assert PMAXTP_MONOGRAPH == (
            "„Modele probabilistyczne opadów maksymalnych o określonym czasie trwania "
            "i prawdopodobieństwie przewyższenia – Projekt PMAXTP”, red. Bogdan "
            "Ozga-Zieliński, Instytut Meteorologii i Gospodarki Wodnej – Państwowy "
            "Instytut Badawczy, Warszawa 2022"
        )

    def test_chmi(self):
        assert CHMI_SOURCE == (
            "Źródło danych: Český hydrometeorologický ústav (ČHMÚ), "
            "https://opendata.chmi.cz, licencja CC BY 4.0 "
            "(https://creativecommons.org/licenses/by/4.0/)"
        )
        assert CHMI_PROCESSED.startswith("Dane ČHMÚ zostały przetworzone (")

    def test_the_terms_notice(self):
        assert IMGW_TERMS == (
            "Dane IMGW-PIB można wykorzystywać nieodpłatnie do celów prywatnych "
            "(niezarobkowych). Wykorzystanie w działalności gospodarczej, na stronach "
            "z reklamami lub do celów wymienionych w regulaminie (m.in. planowanie w "
            "gospodarowaniu wodami, art. 317 Prawa wodnego) wymaga umowy z IMGW-PIB."
        )
        assert TERMS_DANEPUBLICZNE == (
            "Regulamin: https://danepubliczne.imgw.pl/regulations"
        )
        assert TERMS_HYDRO == "Regulamin: https://hydro.imgw.pl/#/regulamin"
        assert TERMS_PMAXTP == "Regulamin: https://klimat.imgw.pl/opady-maksymalne"


class TestRecognition:
    """An input's lines become the complete lines of their providers."""

    def test_a_source_line_brings_the_processed_line_and_the_terms(self):
        attribution = Attribution.from_lines([IMGW_SOURCE])

        assert attribution.lines == (IMGW_SOURCE, IMGW_PROCESSED)
        assert attribution.terms_notice == (IMGW_TERMS, TERMS_DANEPUBLICZNE)

    def test_pmaxtps_source_line_brings_its_own_lines_not_imgws(self):
        attribution = Attribution.from_lines([PMAXTP_SOURCE])

        assert attribution.lines == (PMAXTP_SOURCE, PMAXTP_PROCESSED, PMAXTP_MONOGRAPH)
        assert attribution.terms_notice == (IMGW_TERMS, TERMS_PMAXTP)

    def test_hydro_imgw_pl_adds_its_line_and_its_terms(self):
        attribution = Attribution.of("imgw_hydro")

        assert attribution.lines == (IMGW_SOURCE, IMGW_PROCESSED, IMGW_HYDRO)
        assert attribution.terms_notice == (IMGW_TERMS, TERMS_HYDRO)

    def test_a_final_full_stop_and_blanks_do_not_hide_a_line(self):
        attribution = Attribution.from_lines([f"  {IMGW_SOURCE}. "])

        assert attribution.lines == (IMGW_SOURCE, IMGW_PROCESSED)

    def test_an_older_chmi_credit_becomes_the_complete_one(self):
        """Obserwator's credit without the licence's link; its CP stays before ours."""
        older = (
            "Źródło danych: Český hydrometeorologický ústav (ČHMÚ), "
            "https://opendata.chmi.cz, licencja CC BY 4.0"
        )
        attribution = Attribution.from_lines([older, OBSERWATOR_CHMI_PROCESSED])

        assert attribution.lines == (
            CHMI_SOURCE,
            OBSERWATOR_CHMI_PROCESSED,
            CHMI_PROCESSED,
        )
        assert attribution.terms_notice == ()

    def test_lines_of_several_providers_take_the_order_of_dev_20_4(self):
        attribution = (
            Attribution.of("chmi")
            | Attribution.from_lines(["Inny dostawca danych"])
            | Attribution.of("pmaxtp")
            | Attribution.from_lines([IMGW_PROCESSED])
        )

        assert attribution.lines == (
            IMGW_SOURCE,
            IMGW_PROCESSED,
            PMAXTP_SOURCE,
            PMAXTP_PROCESSED,
            PMAXTP_MONOGRAPH,
            CHMI_SOURCE,
            CHMI_PROCESSED,
            "Inny dostawca danych",
        )
        assert attribution.terms_notice == (
            IMGW_TERMS,
            TERMS_DANEPUBLICZNE,
            TERMS_PMAXTP,
        )

    def test_terms_lines_given_with_the_lines_are_sorted_out(self):
        """The option takes both kinds mixed; an unknown address stays a terms line."""
        attribution = Attribution.from_lines(
            [TERMS_PMAXTP, "Regulamin: https://example.org/terms", PMAXTP_SOURCE]
        )

        assert attribution.lines == (PMAXTP_SOURCE, PMAXTP_PROCESSED, PMAXTP_MONOGRAPH)
        assert attribution.terms_notice == (
            IMGW_TERMS,
            TERMS_PMAXTP,
            "Regulamin: https://example.org/terms",
        )

    def test_no_line_is_no_attribution(self):
        attribution = Attribution.from_lines(["", "   ", None])

        assert not attribution
        assert attribution.to_dict() == {}

    def test_every_provider_has_its_complete_lines_for_the_gui(self):
        lines = provider_lines()

        assert lines["imgw"] == {
            "attribution": [IMGW_SOURCE, IMGW_PROCESSED],
            "terms_notice": [IMGW_TERMS, TERMS_DANEPUBLICZNE],
        }
        assert lines["pmaxtp"]["attribution"][2] == PMAXTP_MONOGRAPH
        assert lines["chmi"] == {
            "attribution": [CHMI_SOURCE, CHMI_PROCESSED],
            "terms_notice": [],
        }


class TestFiles:
    """The CSV columns and ``ATTRIBUTION.txt`` of DEV-20.5."""

    TABLE = "time_min,discharge_m3s\n0,0.5\n10,2.5\n20,1.0\n"

    def test_a_line_per_cell_from_the_first_data_row_down(self):
        text = csv_with_attribution(self.TABLE, Attribution.of("imgw"))

        assert text.splitlines() == [
            "time_min,discharge_m3s,attribution,terms_notice",
            f'0,0.5,{IMGW_SOURCE},"{IMGW_TERMS}"',
            f"10,2.5,{IMGW_PROCESSED},{TERMS_DANEPUBLICZNE}",
            "20,1.0,,",
        ]

    def test_a_short_table_joins_the_rest_into_its_last_cell(self, tmp_path):
        two_rows = "time_min,discharge_m3s\n0,0.5\n10,2.5\n"
        path = tmp_path / "short.csv"
        path.write_text(
            csv_with_attribution(two_rows, Attribution.of("pmaxtp")), encoding="utf-8"
        )

        table = read_table(path)

        assert table.data["discharge_m3s"] == ["0.5", "2.5"]
        assert table.attribution.to_dict() == Attribution.of("pmaxtp").to_dict()

    def test_a_table_without_lines_is_unchanged(self):
        assert csv_with_attribution(self.TABLE, Attribution()) == self.TABLE

    def test_the_attribution_columns_are_not_data(self, tmp_path):
        path = tmp_path / "with-lines.csv"
        path.write_text(
            csv_with_attribution(self.TABLE, Attribution.of("imgw")), encoding="utf-8"
        )

        table = read_table(path)

        assert table.columns == ("time_min", "discharge_m3s")
        assert table.attribution.lines == (IMGW_SOURCE, IMGW_PROCESSED)

    def test_attribution_txt_merges_with_the_file_already_there(self):
        first = attribution_text(Attribution.of("pmaxtp"))
        merged = attribution_text(Attribution.of("imgw"), first)

        assert first.splitlines() == [
            PMAXTP_SOURCE,
            PMAXTP_PROCESSED,
            PMAXTP_MONOGRAPH,
            IMGW_TERMS,
            TERMS_PMAXTP,
        ]
        assert merged.splitlines() == [
            IMGW_SOURCE,
            IMGW_PROCESSED,
            PMAXTP_SOURCE,
            PMAXTP_PROCESSED,
            PMAXTP_MONOGRAPH,
            IMGW_TERMS,
            TERMS_DANEPUBLICZNE,
            TERMS_PMAXTP,
        ]
        assert attribution_text(Attribution.of("imgw"), merged) == merged


def _observer_export(path: Path, *, lines: list[str], terms: list[str]) -> Path:
    """Write a daily series as Obserwator's ``series export`` does, with its lines.

    The values are ``daily_flows_3y.csv`` (three hydrological years); the columns
    ``attribution_source`` and ``attribution_processed`` hold the first two lines in
    the first row, ``attribution`` and ``terms_notice`` one line per row (DEV-20.5).
    """
    rows = (FIXTURES / "daily_flows_3y.csv").read_text(encoding="utf-8").splitlines()
    out = [
        "date,year,Q [m3/s],Q_flag,attribution_source,attribution_processed,"
        "attribution,terms_notice"
    ]
    for number, row in enumerate(rows[1:]):
        date, value = row.split(",")
        year = int(date[:4]) + (1 if date[5:7] in ("11", "12") else 0)
        pair = lines[:2] if number == 0 else ["", ""]
        line = lines[number] if number < len(lines) else ""
        term = terms[number] if number < len(terms) else ""
        cells = [date, str(year), value, "value", *pair, line, term]
        out.append(",".join(f'"{cell}"' if "," in cell else cell for cell in cells))
    path.write_text("\r\n".join(out) + "\r\n", encoding="utf-8")
    return path


class TestResults:
    """The envelope of a run carries the lines of its data (ADR-0028)."""

    def test_flood_frequency_of_an_obserwator_export_carries_s_and_p(self, tmp_path):
        export = _observer_export(
            tmp_path / "q_daily.csv",
            lines=[IMGW_SOURCE, IMGW_PROCESSED],
            terms=[IMGW_TERMS, TERMS_DANEPUBLICZNE],
        )

        envelope = hydrolog.run_command(
            "stats flood-frequency",
            input_file=str(export),
            value_column="Q",
            date_column="date",
        ).to_dict()

        assert envelope["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]
        assert envelope["result"]["n_years"] == 3

    def test_an_export_with_obserwators_two_columns_only_gets_the_terms(self):
        """An export made before the columns of DEV-20.5: S and P, the terms added."""
        envelope = hydrolog.run_command(
            "stats daily",
            input_file=str(FIXTURES / "obserwator_series_export.csv"),
            value_column="Q",
            date_column="date",
        ).to_dict()

        assert envelope["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]

    def test_a_chmi_export_carries_its_credit_and_both_modifications(self, tmp_path):
        export = _observer_export(
            tmp_path / "chmi.csv",
            lines=[CHMI_SOURCE, OBSERWATOR_CHMI_PROCESSED],
            terms=[],
        )

        envelope = hydrolog.run_command(
            "stats mann-kendall", input_file=str(export), value_column="Q"
        ).to_dict()

        assert envelope["attribution"] == [
            CHMI_SOURCE,
            OBSERWATOR_CHMI_PROCESSED,
            CHMI_PROCESSED,
        ]
        assert "terms_notice" not in envelope

    def test_values_without_a_source_carry_nothing(self):
        envelope = hydrolog.run_command(
            "stats mann-kendall", values=[3.0, 5.0, 4.0, 6.0, 8.0, 7.0]
        ).to_dict()

        assert "attribution" not in envelope
        assert "terms_notice" not in envelope

    def test_lines_given_with_a_depth_go_into_the_hydrograph(self):
        """The GUI and an agent pass the lines of ``precip pmaxtp`` with its depth."""
        envelope = hydrolog.run_command(
            "hydrograph generate",
            area_km2=37.22,
            cn=65,
            tc_min=180,
            hietogram_type="beta",
            total_mm=101.82,
            duration_min=720,
            attribution=[PMAXTP_SOURCE, PMAXTP_PROCESSED, PMAXTP_MONOGRAPH],
        ).to_dict()

        assert envelope["attribution"] == [
            PMAXTP_SOURCE,
            PMAXTP_PROCESSED,
            PMAXTP_MONOGRAPH,
        ]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_PMAXTP]

    def test_the_command_line_takes_the_lines_as_a_json_array(self, capsys):
        code = main(
            [
                "precip",
                "hietogram",
                "--hietogram-type",
                "block",
                "--total-mm",
                "40",
                "--duration-min",
                "60",
                "--attribution",
                json.dumps([PMAXTP_SOURCE], ensure_ascii=False),
                "--json",
            ]
        )

        envelope = json.loads(capsys.readouterr().out)
        assert code == 0
        assert envelope["attribution"][0] == PMAXTP_SOURCE
        assert envelope["inputs"]["attribution"] == [PMAXTP_SOURCE]

    def test_the_human_output_prints_the_lines_before_the_notices(self, capsys):
        code = main(
            [
                "stats",
                "daily",
                "--input-file",
                str(FIXTURES / "obserwator_series_export.csv"),
                "--value-column",
                "Q",
                "--date-column",
                "date",
                "--lang",
                "en",
            ]
        )

        out = capsys.readouterr().out
        assert code == 0
        sources = out.index("Data sources:")
        assert out.index(f"  {IMGW_SOURCE}\n") > sources
        assert out.index(f"  {TERMS_DANEPUBLICZNE}") > out.index(f"  {IMGW_TERMS}")
        assert "Notices:" not in out or out.index("Notices:") > sources


STATION_ANALYSES = [
    pytest.param("stats threshold-events", {"level": 7.0}, id="threshold-events"),
    pytest.param("stats duration-curve", {}, id="duration-curve"),
    pytest.param("stats runoff-volume", {}, id="runoff-volume"),
]
"""The commands of the station analyses (plan 2026-11-13) and their own options."""


class TestStationAnalyses:
    """The station analyses carry the lines of the series they read (ADR-0028)."""

    @pytest.mark.parametrize(("command", "options"), STATION_ANALYSES)
    def test_an_obserwator_export_gives_its_lines(self, tmp_path, command, options):
        export = _observer_export(
            tmp_path / "q_daily.csv",
            lines=[IMGW_SOURCE, IMGW_PROCESSED],
            terms=[IMGW_TERMS, TERMS_DANEPUBLICZNE],
        )

        envelope = hydrolog.run_command(
            command,
            input_file=str(export),
            value_column="Q",
            date_column="date",
            **options,
        ).to_dict()

        assert envelope["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]

    @pytest.mark.parametrize(("command", "options"), STATION_ANALYSES)
    def test_a_series_given_inline_takes_the_option(self, command, options):
        """A handed-off series has no file: its source line comes as `attribution`."""
        rows = (FIXTURES / "daily_flows_3y.csv").read_text("utf-8").splitlines()[1:]
        dates, values = zip(*(row.split(",") for row in rows), strict=True)

        envelope = hydrolog.run_command(
            command,
            values=[float(value) for value in values],
            dates=list(dates),
            attribution=[IMGW_SOURCE],
            **options,
        ).to_dict()

        assert envelope["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]

    def test_a_batch_line_has_its_own_calls_lines_the_batch_all(self, tmp_path):
        """A line carries the lines of its own call only; the batch's envelope all."""
        _observer_export(
            tmp_path / "q_daily.csv",
            lines=[IMGW_SOURCE, IMGW_PROCESSED],
            terms=[IMGW_TERMS, TERMS_DANEPUBLICZNE],
        )
        calls = [
            {
                "command": "tc kirpich",
                "options": {"length_km": 8.2, "slope_m_per_m": 0.02},
            },
            {
                "command": "stats runoff-volume",
                "options": {
                    "input_file": "q_daily.csv",
                    "value_column": "Q",
                    "date_column": "date",
                },
            },
            {
                "command": "tc kirpich",
                "options": {"length_km": 4.1, "slope_m_per_m": 0.01},
            },
        ]
        batch = tmp_path / "calls.jsonl"
        batch.write_text("".join(json.dumps(c) + "\n" for c in calls), "utf-8")

        envelope = hydrolog.run_command(
            "commands batch", input_file=str(batch), output=str(tmp_path / "out.jsonl")
        ).to_dict()

        lines = [
            json.loads(line)
            for line in (tmp_path / "out.jsonl").read_text("utf-8").splitlines()
        ]
        assert "attribution" not in lines[0]
        assert lines[1]["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert lines[1]["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]
        assert "attribution" not in lines[2]
        assert envelope["attribution"] == [IMGW_SOURCE, IMGW_PROCESSED]
        assert envelope["terms_notice"] == [IMGW_TERMS, TERMS_DANEPUBLICZNE]


class TestFilesOfCommands:
    """Files Hydrolog writes carry the lines of their data (DEV-20.5)."""

    def test_a_routed_table_carries_the_lines_and_reads_back(self, tmp_path):
        inflow = tmp_path / "inflow.csv"
        inflow.write_text(
            csv_with_attribution(
                "time_min,discharge_m3s\n0,0\n10,5\n20,12\n30,6\n40,2\n50,0\n",
                Attribution.of("pmaxtp"),
            ),
            encoding="utf-8",
        )

        first = hydrolog.run_command(
            "route lag",
            input_file=str(inflow),
            lag_min=10,
            output=str(tmp_path / "lagged.csv"),
        )
        again = hydrolog.run_command(
            "route lag", input_file=str(tmp_path / "lagged.csv"), lag_min=10
        )

        written = read_table(tmp_path / "lagged.csv")
        assert written.attribution.to_dict() == Attribution.of("pmaxtp").to_dict()
        assert first.attribution == again.attribution == Attribution.of("pmaxtp").lines

    def test_a_report_ends_with_the_sources(self, tmp_path):
        report = tmp_path / "raport.md"

        envelope = hydrolog.run_command(
            "report generate",
            output=str(report),
            area_km2=12.0,
            cn=72,
            tc_min=90,
            hietogram_type="beta",
            total_mm=50,
            duration_min=60,
            attribution=[PMAXTP_SOURCE],
        )

        text = report.read_text(encoding="utf-8")
        assert text.endswith(
            "## Źródła danych\n\n"
            f"- {PMAXTP_SOURCE}\n- {PMAXTP_PROCESSED}\n- {PMAXTP_MONOGRAPH}\n\n"
            f"- {IMGW_TERMS}\n- {TERMS_PMAXTP}\n"
        )
        assert envelope.result.sections[-1] == "Źródła danych"

    def test_a_report_without_a_providers_data_has_no_sources(self, tmp_path):
        report = tmp_path / "raport.md"

        hydrolog.run_command(
            "report generate",
            output=str(report),
            area_km2=12.0,
            cn=72,
            tc_min=90,
            hietogram_type="beta",
            total_mm=50,
            duration_min=60,
        )

        assert "Źródła danych" not in report.read_text(encoding="utf-8")

    def test_a_network_document_carries_its_lines_into_every_file(self, tmp_path):
        document = {
            **example_network_document(),
            "attribution": [PMAXTP_SOURCE],
        }
        out = tmp_path / "out"
        (out).mkdir()
        (out / "ATTRIBUTION.txt").write_text(f"{IMGW_SOURCE}\n", encoding="utf-8")

        envelope = hydrolog.run_command(
            "route network",
            network=document,
            output_dir=str(out),
            schematic=str(tmp_path / "siec.svg"),
            force=True,
        ).to_dict()

        files = {Path(item["path"]).name: item for item in envelope["result"]["files"]}
        assert files["ATTRIBUTION.txt"]["status"] == "replaced"
        assert (out / "ATTRIBUTION.txt").read_text(encoding="utf-8").splitlines() == [
            IMGW_SOURCE,
            IMGW_PROCESSED,
            PMAXTP_SOURCE,
            PMAXTP_PROCESSED,
            PMAXTP_MONOGRAPH,
            IMGW_TERMS,
            TERMS_DANEPUBLICZNE,
            TERMS_PMAXTP,
        ]
        outlet = read_table(out / f"{envelope['result']['outlet']}.csv")
        assert outlet.attribution.to_dict() == Attribution.of("pmaxtp").to_dict()
        svg = (tmp_path / "siec.svg").read_text(encoding="utf-8")
        assert ">Regulamin: https://klimat.imgw.pl/opady-maksymalne</text>" in svg
        assert envelope["attribution"][0] == PMAXTP_SOURCE

    def test_a_network_without_a_providers_data_writes_no_attribution_file(
        self, tmp_path
    ):
        out = tmp_path / "out"

        hydrolog.run_command(
            "route network",
            network=example_network_document(),
            output_dir=str(out),
        )

        assert not (out / "ATTRIBUTION.txt").exists()
        assert "attribution" not in (out / "OUT.csv").read_text(encoding="utf-8")

    def test_lines_of_a_network_must_be_strings(self):
        document = {
            **example_network_document(),
            "attribution": [IMGW_SOURCE, 7],
        }

        with pytest.raises(InvalidParameterError) as caught:
            hydrolog.run_command("route network", network=document)

        assert caught.value.details["reason"] == "type"
        assert caught.value.details["field"] == "attribution"
