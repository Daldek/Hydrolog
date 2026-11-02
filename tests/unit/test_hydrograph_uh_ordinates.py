"""The ordinates of the unit hydrograph in the result of ``hydrograph generate``."""

from __future__ import annotations

import numpy as np
import pytest

from hydrolog.catalog import run_command

RAIN = {
    "area_km2": 37.2,
    "cn": 72,
    "hietogram_type": "beta",
    "total_mm": 60.0,
    "duration_min": 120.0,
    "alpha": 2.0,
    "beta": 5.0,
}
MODELS = {
    "scs": {"tc_min": 95.0},
    "nash": {"nash_n": 3.0, "nash_k_min": 30.0},
    "clark": {"tc_min": 95.0, "clark_r_min": 60.0},
    "snyder": {"snyder_length_km": 14.0, "snyder_centroid_length_km": 7.0},
}
ANALYTIC_PEAK = {"scs", "snyder"}
"""Models whose peak is computed analytically, so it may fall between ordinates."""


def _generate(model: str, timestep_min: float) -> dict[str, object]:
    options = {**RAIN, **MODELS[model], "uh_model": model}
    options["timestep_min"] = timestep_min
    result: dict[str, object] = run_command("hydrograph generate", options).to_dict()[
        "result"
    ]
    return result


@pytest.mark.parametrize("timestep_min", [10.0, 7.0])
@pytest.mark.parametrize("model", MODELS)
class TestTheConvolvedUnitHydrograph:
    def test_its_convolution_with_the_effective_rain_is_the_hydrograph(
        self, model, timestep_min
    ):
        result = _generate(model, timestep_min)
        discharge = np.asarray(result["discharge_m3s"])

        convolved = np.convolve(
            np.asarray(result["effective_precipitation_mm"]),
            np.asarray(result["uh_discharge_m3s_per_mm"]),
        )

        assert discharge.max() > 0
        np.testing.assert_allclose(
            convolved[: len(discharge)], discharge, rtol=1e-9, atol=0.0
        )

    def test_its_times_are_the_grid_of_the_time_step_from_zero(
        self, model, timestep_min
    ):
        result = _generate(model, timestep_min)
        times = np.asarray(result["uh_times_min"])

        assert len(times) == len(result["uh_discharge_m3s_per_mm"])  # type: ignore[arg-type]
        np.testing.assert_allclose(times, np.arange(len(times)) * timestep_min)

    def test_its_peak_is_the_peak_that_the_result_reports(self, model, timestep_min):
        result = _generate(model, timestep_min)
        ordinates = np.asarray(result["uh_discharge_m3s_per_mm"])
        times = np.asarray(result["uh_times_min"])
        peak = result["uh_peak_discharge_m3s_per_mm"]
        time_to_peak = result["uh_time_to_peak_min"]
        largest = int(np.argmax(ordinates))

        if model in ANALYTIC_PEAK:
            assert ordinates[largest] <= peak * (1 + 1e-9)  # type: ignore[operator]
            assert abs(times[largest] - time_to_peak) < timestep_min  # type: ignore[operator]
        else:
            assert ordinates[largest] == pytest.approx(peak, rel=1e-12)
            assert times[largest] == pytest.approx(time_to_peak, rel=1e-12)
