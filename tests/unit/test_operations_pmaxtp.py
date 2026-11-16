"""``precip pmaxtp``: the PMAXTP depth of IMGW-PIB through Obserwator (ADR-0018).

Obserwator's fetch is the recorded table of Warsaw (``tests/conftest.py``) unless a
test replaces it; the ``live`` test asks IMGW-PIB itself (``pytest -m live``).
"""

import json
import sys
from typing import Any

import obserwator
import pytest

from hydrolog import _attribution, _pmaxtp
from hydrolog.catalog import get_command, run_command
from hydrolog.cli.main import main
from hydrolog.exceptions import (
    HydrologError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
)
from tests.conftest import recorded_pmaxtp

WARSAW = {"latitude": 52.23, "longitude": 21.01}
"""The point of the recorded table."""


def _cell(duration: str, probability: str) -> float:
    """Return a depth of the recorded table [mm]."""
    depth: float = recorded_pmaxtp()["data"]["ks"][duration][probability]
    return depth


def _calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record the calls of Obserwator's fetch (the recorded table still answers)."""
    calls: list[dict[str, Any]] = []
    answer = obserwator.fetch_pmaxtp

    def fetch(latitude: float, longitude: float, **options: Any) -> Any:
        calls.append({"latitude": latitude, "longitude": longitude, **options})
        return answer(latitude, longitude, **options)

    monkeypatch.setattr(obserwator, "fetch_pmaxtp", fetch)
    return calls


def _failing(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    """Make Obserwator's fetch raise ``error``."""

    def fetch(latitude: float, longitude: float, **options: Any) -> Any:
        raise error

    monkeypatch.setattr(obserwator, "fetch_pmaxtp", fetch)


def _run(**options: Any) -> dict[str, Any]:
    envelope: dict[str, Any] = run_command(
        "precip pmaxtp", {**WARSAW, **options}
    ).to_dict()
    return envelope


class TestDepth:
    """The depth is the cell of the duration and the probability."""

    def test_the_depth_is_the_cell_of_the_duration_and_the_probability(self):
        envelope = _run(duration_min=60, probability_percent=1)

        result = envelope["result"]
        assert result["depth_mm"] == _cell("60", "1") == 39.16
        assert (result["latitude"], result["longitude"]) == (52.23, 21.01)
        assert (result["method"], result["duration_min"]) == ("POT", 60.0)
        assert result["probability_percent"] == 1.0
        assert result["attribution"] == _attribution.PMAXTP_SOURCE

    def test_the_envelope_carries_the_lines_of_pmaxtps_terms(self):
        """PS, PP and the monograph M, then the link to PMAXTP's terms (DEV §20)."""
        envelope = _run(duration_min=60, probability_percent=1)

        assert envelope["attribution"] == [
            _attribution.PMAXTP_SOURCE,
            _attribution.PMAXTP_PROCESSED,
            _attribution.PMAXTP_MONOGRAPH,
        ]
        assert envelope["terms_notice"] == [
            "Regulamin danych PMAXTP: https://klimat.imgw.pl/opady-maksymalne"
        ]
        assert list(envelope)[6:9] == ["result", "attribution", "terms_notice"]

    @pytest.mark.parametrize(
        ("duration", "probability", "key"),
        [(720, 0.5, "0.5"), (720, 50, "50"), (5, 99.9, "99.9"), (4320, 0.01, "0.01")],
    )
    def test_a_fractional_probability_is_not_its_whole_neighbour(
        self, duration, probability, key
    ):
        """0.5 % and 50 % are different cells; so are the ends of both lists."""
        result = _run(duration_min=duration, probability_percent=probability)["result"]

        assert result["depth_mm"] == _cell(str(duration), key)

    def test_a_whole_duration_given_as_a_float_finds_its_row(self):
        result = _run(duration_min=720.0, probability_percent=1.0)["result"]

        assert result["depth_mm"] == _cell("720", "1")

    def test_the_method_and_a_timeout_below_the_guis_go_to_obserwator(
        self, monkeypatch
    ):
        calls = _calls(monkeypatch)

        result = _run(duration_min=60, probability_percent=1, method="AMP")["result"]

        assert result["method"] == "AMP"
        assert calls == [{**WARSAW, "method": "AMP", "timeout": _pmaxtp.TIMEOUT_S}]
        assert _pmaxtp.TIMEOUT_S < 30

    def test_the_notice_points_to_the_lines_and_pmaxtps_terms(self):
        (notice,) = _run(duration_min=60, probability_percent=1)["notices"]

        assert (notice["level"], notice["code"]) == ("info", "pmaxtp_attribution")
        assert notice["details"] == {
            "attribution": _attribution.PMAXTP_SOURCE,
            "terms_url": "https://klimat.imgw.pl/opady-maksymalne",
        }

    def test_the_command_is_the_one_that_uses_the_network(self):
        effects = get_command("precip pmaxtp").effects

        assert effects.network is True
        assert (effects.read_only, effects.destructive) == (True, False)


class TestValuesOfTheAtlas:
    """A duration or probability the tables lack fails before anything is fetched."""

    @pytest.mark.parametrize(
        ("option", "value", "allowed"),
        [
            ("duration_min", 61, _pmaxtp.DURATIONS_MIN),
            ("duration_min", 25, _pmaxtp.DURATIONS_MIN),
            ("probability_percent", 1.5, _pmaxtp.PROBABILITIES_PERCENT),
            ("probability_percent", 0.04, _pmaxtp.PROBABILITIES_PERCENT),
        ],
    )
    def test_it_is_a_validation_error_listing_the_allowed_values(
        self, monkeypatch, option, value, allowed
    ):
        calls = _calls(monkeypatch)
        options = {"duration_min": 60, "probability_percent": 1, option: value}

        with pytest.raises(InvalidParameterError) as caught:
            _run(**options)

        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == "choice"
        assert caught.value.details["allowed"] == list(allowed)
        assert calls == []

    def test_the_tables_hold_every_value_the_command_allows(self):
        """The published lists are those of the recorded answer of IMGW-PIB."""
        table = recorded_pmaxtp()["data"]["ks"]

        probabilities = {f"{value:g}" for value in _pmaxtp.PROBABILITIES_PERCENT}
        assert set(table) == {str(value) for value in _pmaxtp.DURATIONS_MIN}
        for row in table.values():
            assert set(row) == probabilities

    def test_a_point_outside_the_box_of_poland_is_refused_by_the_catalog(
        self, monkeypatch
    ):
        calls = _calls(monkeypatch)

        with pytest.raises(InvalidParameterError) as caught:
            _run(latitude=60.0, duration_min=60, probability_percent=1)

        assert caught.value.details["option"] == "latitude"
        assert caught.value.details["reason"] == "maximum"
        assert calls == []


class TestErrorsOfObserwator:
    """Obserwator's errors become Hydrolog's registry codes."""

    def test_a_point_outside_the_grid_is_an_error_of_the_latitude(self, monkeypatch):
        """In the box but outside the atlas (the Baltic): Obserwator names no option."""
        _failing(
            monkeypatch,
            obserwator.ObserwatorValidationError("outside the PMAXTP grid"),
        )

        with pytest.raises(InvalidParameterError) as caught:
            _run(latitude=54.7, longitude=20.5, duration_min=60, probability_percent=1)

        assert caught.value.code == "validation_error"
        assert caught.value.details["option"] == "latitude"
        assert caught.value.details["reason"] == "outside_pmaxtp"
        assert "PMAXTP covers Poland" in (caught.value.hint or "")

    def test_the_coordinate_obserwator_names_is_kept(self, monkeypatch):
        _failing(
            monkeypatch,
            obserwator.ObserwatorValidationError(
                "outside Poland", details={"option": "longitude", "value": 30.0}
            ),
        )

        with pytest.raises(InvalidParameterError) as caught:
            _pmaxtp.fetch_depth(52.0, 30.0, 60, 1)

        assert caught.value.details["option"] == "longitude"

    def test_an_unreachable_server_is_source_unavailable(self, monkeypatch):
        _failing(
            monkeypatch,
            obserwator.ObserwatorConnectionError(
                "timeout", details={"url": "https://imgw.example/", "reason": "timeout"}
            ),
        )

        with pytest.raises(HydrologError) as caught:
            _run(duration_min=60, probability_percent=1)

        assert caught.value.code == "source_unavailable"
        assert caught.value.exit_code == 5
        assert caught.value.details["source"] == "imgw-pmaxtp"
        assert caught.value.details["reason"] == "timeout"

    def test_an_answer_that_cannot_be_read_is_a_data_error(self, monkeypatch):
        _failing(monkeypatch, obserwator.ObserwatorDataError("no table ks"))

        with pytest.raises(InputDataError) as caught:
            _run(duration_min=60, probability_percent=1)

        assert caught.value.code == "data_error"

    def test_a_table_without_the_cell_is_a_data_error(self, monkeypatch):
        recorded = recorded_pmaxtp()
        table = {key: dict(row) for key, row in recorded["data"]["ks"].items()}
        del table["60"]["1"]

        def fetch(latitude: float, longitude: float, **options: Any) -> Any:
            answer = {**recorded, "data": {**recorded["data"], "ks": table}}
            return obserwator.PMaXTPResult.model_validate(answer)

        monkeypatch.setattr(obserwator, "fetch_pmaxtp", fetch)

        with pytest.raises(InputDataError) as caught:
            _run(duration_min=60, probability_percent=1)

        assert caught.value.details["duration_min"] == 60
        assert caught.value.details["probability_percent"] == 1.0

    def test_without_obserwator_it_names_the_extra(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "obserwator", None)

        with pytest.raises(MissingDependencyError) as caught:
            _run(duration_min=60, probability_percent=1)

        assert caught.value.details == {"extra": "pmaxtp", "module": "obserwator"}
        assert caught.value.hint == 'pip install "hydrolog[pmaxtp]"'


class TestCommandLine:
    """The CLI line of the author's smoke test."""

    LINE = (
        "precip",
        "pmaxtp",
        "--latitude",
        "52.23",
        "--longitude",
        "21.01",
        "--duration-min",
        "60",
        "--probability-percent",
        "1",
    )

    def test_json_prints_the_depth(self, capsys):
        code = main([*self.LINE, "--json"])

        envelope = json.loads(capsys.readouterr().out)
        assert code == 0
        assert envelope["result"]["depth_mm"] == 39.16
        assert envelope["notices"][0]["code"] == "pmaxtp_attribution"

    def test_an_unreachable_server_exits_with_5(self, monkeypatch, capsys):
        _failing(monkeypatch, obserwator.ObserwatorConnectionError("down"))

        code = main([*self.LINE, "--json"])

        error = json.loads(capsys.readouterr().err.splitlines()[-1])
        assert (code, error["code"]) == (5, "source_unavailable")


@pytest.mark.live
def test_imgw_pib_answers_with_a_depth_for_warsaw():
    """The real PMAXTP of IMGW-PIB (``pytest -m live``); the atlas may change values."""
    result = run_command(
        "precip pmaxtp", {**WARSAW, "duration_min": 60, "probability_percent": 1}
    ).to_dict()["result"]

    assert 10 < result["depth_mm"] < 200
