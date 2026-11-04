"""Pytest configuration and shared fixtures."""

import json
import os
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any

import pytest

PMAXTP_TABLE = Path(__file__).parent / "fixtures" / "pmaxtp_warszawa_pot.json"
"""IMGW-PIB's PMAXTP answer for Warsaw (52.23, 21.01, POT), recorded on 2026-11-04 as
Obserwator returns it (``PMaXTPResult``: 16 durations, 27 probabilities)."""


@pytest.fixture
def sample_watershed_params() -> dict:
    """Sample watershed parameters for testing."""
    return {
        "area_km2": 45.3,
        "cn": 72,
        "tc_min": 68.5,
        "length_km": 8.2,
        "slope_percent": 2.3,
    }


@pytest.fixture
def sample_precipitation_mm() -> float:
    """Sample precipitation depth for testing."""
    return 38.5


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate every test from the settings of the developer's machine."""
    for name in list(os.environ):
        if name.startswith(("HYDROLOG_", "NOGAT_")):
            monkeypatch.delenv(name)
    monkeypatch.setenv("NOGAT_CONFIG", str(tmp_path / "absent.toml"))


@cache
def recorded_pmaxtp(path: Path = PMAXTP_TABLE) -> dict[str, Any]:
    """Return a recorded answer of IMGW-PIB (default :data:`PMAXTP_TABLE`)."""
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def recorded_fetch(path: Path = PMAXTP_TABLE) -> Callable[..., Any]:
    """Return a stand-in of ``obserwator.fetch_pmaxtp`` that answers from a recording.

    Every point and method get the table recorded at ``path`` with their own
    coordinates and method, as Obserwator returns it (``PMaXTPResult``), and Hydrolog's
    real code reads it.
    """
    import obserwator

    def fetch_pmaxtp(
        latitude: float,
        longitude: float,
        *,
        method: str = "POT",
        timeout: float = 30.0,
        validate_coords: bool = True,
    ) -> obserwator.PMaXTPResult:
        answer = {
            **recorded_pmaxtp(path),
            "method": method,
            "latitude": latitude,
            "longitude": longitude,
        }
        return obserwator.PMaXTPResult.model_validate(answer)

    return fetch_pmaxtp


@pytest.fixture(autouse=True)
def _pmaxtp_offline(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Answer Obserwator's PMAXTP fetch with the recorded table, outside ``live`` tests.

    ``precip pmaxtp`` is the only command that uses the network (ADR-0018); the gate
    runs offline, so every point and method get the table of :data:`PMAXTP_TABLE`
    (:func:`recorded_fetch`). A test that needs another answer, or an error of
    Obserwator, patches ``obserwator.fetch_pmaxtp`` itself; the browser tests answer
    the page's requests from Kamiennik's table (``tests/e2e/conftest.py``).
    """
    if request.node.get_closest_marker("live") is not None:
        return
    try:
        import obserwator
    except ImportError:
        return
    monkeypatch.setattr(obserwator, "fetch_pmaxtp", recorded_fetch())
