"""Pytest configuration and shared fixtures."""

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
