"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import pytest


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
