"""Tests for JSON serialization of Hydrolog result dataclasses."""

import dataclasses
import json
from enum import Enum
from pathlib import Path, PurePosixPath

import numpy as np
import pytest

from hydrolog._serialization import JsonResultMixin, to_jsonable
from hydrolog.hydrometrics.rating_curve import (
    RatingCurve,
    WaterLevelFrequency,
)
from hydrolog.morphometry import (
    HypsometricCurve,
    TerrainAnalysis,
    WatershedGeometry,
    WatershedParameters,
)
from hydrolog.network import OrderingMethod, StreamNetwork, StreamSegment
from hydrolog.precipitation import (
    BlockHietogram,
    HietogramResult,
    Station,
    arithmetic_mean,
    inverse_distance_weighting,
    isohyet_method,
    thiessen_polygons,
)
from hydrolog.runoff import (
    AMC,
    SCSCN,
    ClarkIUH,
    HydrographGenerator,
    HydrologicCondition,
    LandCover,
    NashIUH,
    SCSUnitHydrograph,
    SnyderUH,
    convolve_discrete,
    lookup_cn,
)
from hydrolog.statistics import (
    FloodFrequencyAnalysis,
    LowFlowAnalysis,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
    mann_kendall_test,
)


class Color(Enum):
    RED = "red"


class IntColor(int, Enum):
    ONE = 1


@dataclasses.dataclass
class _Inner:
    x: float
    tag: Color


@dataclasses.dataclass
class _Outer(JsonResultMixin):
    b: int
    a: np.ndarray
    inner: _Inner
    mapping: dict


class TestToJsonable:
    """Edge cases of the recursive converter."""

    def test_nan_and_inf_become_none(self):
        assert to_jsonable(float("nan")) is None
        assert to_jsonable(float("inf")) is None
        assert to_jsonable(-np.inf) is None
        assert to_jsonable(np.float32("nan")) is None

    def test_array_non_finite_values_become_none(self):
        arr = np.array([1.0, np.nan, np.inf, -np.inf, 2.5])
        assert to_jsonable(arr) == [1.0, None, None, None, 2.5]

    def test_nested_2d_array(self):
        arr = np.array([[1.0, np.nan], [3.0, 4.0]])
        assert to_jsonable(arr) == [[1.0, None], [3.0, 4.0]]

    def test_integer_and_bool_arrays_keep_type(self):
        ints = to_jsonable(np.array([1, 2, 3]))
        assert ints == [1, 2, 3]
        assert all(type(v) is int for v in ints)
        assert to_jsonable(np.array([True, False])) == [True, False]

    def test_numpy_scalars_become_python_scalars(self):
        assert type(to_jsonable(np.int64(5))) is int
        assert type(to_jsonable(np.float64(1.5))) is float
        assert type(to_jsonable(np.float32(0.5))) is float
        assert to_jsonable(np.bool_(True)) is True

    def test_python_scalars_unchanged(self):
        assert to_jsonable(None) is None
        assert to_jsonable(True) is True
        assert to_jsonable(3) == 3
        assert to_jsonable("zażółć") == "zażółć"

    def test_enum_becomes_value(self):
        assert to_jsonable(Color.RED) == "red"
        assert to_jsonable(AMC.III) == AMC.III.value
        assert to_jsonable(IntColor.ONE) == 1
        assert type(to_jsonable(IntColor.ONE)) is int

    def test_tuple_becomes_list(self):
        assert to_jsonable((1, (2.0, np.nan))) == [1, [2.0, None]]

    def test_dict_keys_become_strings(self):
        data = {1: "a", np.int64(2): "b", "k": "c", Color.RED: "d", 1.5: "e"}
        assert to_jsonable(data) == {
            "1": "a",
            "2": "b",
            "k": "c",
            "red": "d",
            "1.5": "e",
        }

    def test_dict_with_unsupported_key_raises(self):
        with pytest.raises(TypeError):
            to_jsonable({(1, 2): "x"})

    def test_paths_become_posix_strings(self):
        assert to_jsonable(PurePosixPath("/a/b.json")) == "/a/b.json"
        assert to_jsonable(Path("dir") / "f.csv") == "dir/f.csv"

    def test_dataclass_fields_in_declaration_order(self):
        obj = _Outer(
            b=1, a=np.array([0.5, np.nan]), inner=_Inner(2.0, Color.RED), mapping={3: 4}
        )
        data = to_jsonable(obj)
        assert list(data) == ["b", "a", "inner", "mapping"]
        assert data == {
            "b": 1,
            "a": [0.5, None],
            "inner": {"x": 2.0, "tag": "red"},
            "mapping": {"3": 4},
        }

    @pytest.mark.parametrize(
        "value",
        [object(), {1, 2}, b"bytes", 1 + 2j, np.datetime64("2020-01-01"), _Inner],
    )
    def test_unknown_types_raise_type_error(self, value):
        with pytest.raises(TypeError):
            to_jsonable(value)

    def test_unknown_nested_type_raises(self):
        with pytest.raises(TypeError):
            to_jsonable({"ok": [1, 2, {"bad": object()}]})


class TestJsonResultMixin:
    """Behaviour of the mixin methods."""

    def _obj(self) -> _Outer:
        return _Outer(
            b=1, a=np.array([1.0, np.inf]), inner=_Inner(0.0, Color.RED), mapping={}
        )

    def test_to_dict_matches_to_jsonable(self):
        obj = self._obj()
        assert obj.to_dict() == to_jsonable(obj)

    def test_to_json_roundtrip_with_null(self):
        obj = self._obj()
        assert json.loads(obj.to_json())["a"] == [1.0, None]
        assert "NaN" not in obj.to_json()
        assert "Infinity" not in obj.to_json()

    def test_to_json_indent(self):
        text = self._obj().to_json(indent=2)
        assert text.startswith('{\n  "b": 1')

    def test_to_json_does_not_escape_unicode(self):
        obj = _Outer(
            b=1,
            a=np.array([]),
            inner=_Inner(1.0, Color.RED),
            mapping={"zażółć": 1},
        )
        assert "zażółć" in obj.to_json()

    def test_unsupported_field_raises(self):
        obj = _Outer(b=1, a=np.array([]), inner=_Inner(1.0, Color.RED), mapping={})
        obj.mapping = {"x": object()}
        with pytest.raises(TypeError):
            obj.to_json()


# ---------------------------------------------------------------------------
# Real result objects built through the public API
# ---------------------------------------------------------------------------


def _dates(years: int = 31) -> np.ndarray:
    return np.arange(
        np.datetime64("1990-11-01"),
        np.datetime64("1990-11-01") + np.timedelta64(365 * years, "D"),
        dtype="datetime64[D]",
    )


def _daily_flows(dates: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(42)
    day = np.arange(len(dates))
    return (
        20.0 + 10.0 * np.sin(2 * np.pi * day / 365.25) + rng.uniform(0, 5, len(dates))
    )


def _annual_maxima() -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.gumbel(loc=100.0, scale=25.0, size=40)


_STATIONS = [
    Station("A", 0.0, 0.0, 10.0, elevation_m=100.0),
    Station("B", 10.0, 0.0, 20.0),
    Station("C", 0.0, 10.0, 30.0),
]


def _generator_result():
    hyeto = BlockHietogram().generate(
        total_mm=40.0, duration_min=60.0, timestep_min=10.0
    )
    return HydrographGenerator(area_km2=25.0, cn=75, tc_min=90.0).generate(
        hyeto, timestep_min=10.0
    )


def _rating_curve():
    h = np.linspace(110.0, 300.0, 25)
    q = 0.05 * (h - 100.0) ** 1.6
    return RatingCurve(h, q).fit(h0_initial=100.0)


def _flow_stats_nan():
    return mann_kendall_test(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 7.0, 8.0]))


def _low_flow_frequency():
    dates = _dates()
    return LowFlowAnalysis(_daily_flows(dates), dates).fit_fisher_tippett()


def _low_flow_analysis():
    dates = _dates(3)
    flows = _daily_flows(dates)
    flows[100:130] = 1.0
    return LowFlowAnalysis(flows, dates).detect_sequences(threshold=5.0)


def _iuh_from_lutz():
    return NashIUH.from_lutz(
        L_km=12.0, Lc_km=6.0, slope=0.01, manning_n=0.035, urban_pct=10.0
    )


# (id, factory, expected key values keyed by dotted path)
CASES = [
    (
        "EffectivePrecipitationResult",
        lambda: SCSCN(cn=75).effective_precipitation(np.array([10.0, 30.0, 60.0])),
        {"retention_mm": 84.66666666666667, "cn_adjusted": 75},
    ),
    (
        "HydrographResult",
        lambda: convolve_discrete(
            np.array([1.0, 2.0]), np.array([0.5, 1.0, 0.5]), timestep_min=10.0
        ),
        {"discharge_m3s": [0.5, 2.0, 2.5, 1.0], "timestep_min": 10.0},
    ),
    (
        "HydrographGeneratorResult",
        _generator_result,
        {"cn_used": 75, "hydrograph.timestep_min": 10.0},
    ),
    (
        "UnitHydrographResult",
        lambda: SCSUnitHydrograph(area_km2=50.0, tc_min=120.0).generate(
            timestep_min=10.0
        ),
        {"timestep_min": 10.0},
    ),
    (
        "IUHResult",
        lambda: NashIUH(n=3.0, k_min=20.0).generate(timestep_min=10.0),
        {"n": 3.0, "k_min": 20.0},
    ),
    (
        "NashUHResult",
        lambda: NashIUH(n=3.0, k_min=20.0, area_km2=40.0).generate(timestep_min=10.0),
        {"n": 3.0, "k_min": 20.0},
    ),
    (
        "LutzCalculationResult",
        lambda: _iuh_from_lutz().lutz_params,
        {"manning_n": 0.035, "urban_pct": 10.0},
    ),
    (
        "ClarkIUHResult",
        lambda: ClarkIUH(tc_min=60.0, r_min=30.0).generate(timestep_min=10.0),
        {"tc_min": 60.0, "r_min": 30.0},
    ),
    (
        "ClarkUHResult",
        lambda: ClarkIUH(tc_min=60.0, r_min=30.0, area_km2=20.0).generate(
            timestep_min=10.0
        ),
        {"tc_min": 60.0, "r_min": 30.0},
    ),
    (
        "SnyderUHResult",
        lambda: SnyderUH(area_km2=100.0, L_km=20.0, Lc_km=10.0).generate(
            timestep_min=30.0
        ),
        {"ct": 1.5, "cp": 0.6},
    ),
    (
        "CNLookupResult",
        lambda: lookup_cn("B", LandCover.FOREST, HydrologicCondition.GOOD),
        {"hsg": "B", "land_cover": LandCover.FOREST.value, "cn": 55},
    ),
    (
        "HietogramResult",
        lambda: BlockHietogram().generate(
            total_mm=30.0, duration_min=30.0, timestep_min=10.0
        ),
        {"intensities_mm": [10.0, 10.0, 10.0], "total_mm": 30.0},
    ),
    (
        "Station",
        lambda: _STATIONS[0],
        {"station_id": "A", "precipitation_mm": 10.0, "elevation_m": 100.0},
    ),
    (
        "ThiessenResult",
        lambda: thiessen_polygons(_STATIONS, {"A": 5.0, "B": 3.0, "C": 2.0}),
        {
            "areal_precipitation_mm": 17.0,
            "station_weights": {"A": 0.5, "B": 0.3, "C": 0.2},
        },
    ),
    (
        "IDWResult",
        lambda: inverse_distance_weighting(_STATIONS, 0.0, 0.0, power=2.0),
        {"areal_precipitation_mm": 10.0, "power": 2.0},
    ),
    (
        "IsohyetResult",
        lambda: isohyet_method(np.array([10.0, 20.0, 30.0]), np.array([0.25, 0.75])),
        {"areal_precipitation_mm": 22.5, "area_fractions": [0.25, 0.75]},
    ),
    (
        "StreamSegment",
        lambda: StreamSegment(3, [1, 2], length_km=2.0, order=2),
        {"segment_id": 3, "upstream_ids": [1, 2], "order": 2},
    ),
    (
        "NetworkStatistics",
        lambda: _network_statistics(),
        {"max_order": 2, "segment_counts": {"1": 2, "2": 1}, "drainage_density": 0.38},
    ),
    (
        "ShapeIndicators",
        lambda: WatershedGeometry(45.0, 32.0, 12.0).get_shape_indicators(),
        {"form_factor": 45.0 / 12.0**2},
    ),
    (
        "GeometricParameters",
        lambda: WatershedGeometry(45.0, 32.0, 12.0).get_parameters(),
        {"area_km2": 45.0, "width_km": 3.75},
    ),
    (
        "ElevationParameters",
        lambda: TerrainAnalysis(
            150.0, 520.0, 12.0, elevation_mean_m=340.0
        ).get_elevation_parameters(),
        {"relief_m": 370.0, "elevation_mean_m": 340.0},
    ),
    (
        "SlopeParameters",
        lambda: TerrainAnalysis(
            150.0, 520.0, 12.0, channel_length_km=15.0
        ).get_slope_parameters(),
        {"channel_slope_m_per_m": 370.0 / 15000.0},
    ),
    (
        "HypsometricResult",
        lambda: HypsometricCurve(np.linspace(100.0, 500.0, 200)).analyze(n_points=11),
        {"elevation_mean_m": 300.0},
    ),
    (
        "CharacteristicValues",
        lambda: calculate_characteristic_values(_daily_flows(_dates()), _dates()),
        {"period_years": 31, "parameter": "Q"},
    ),
    (
        "DailyStatistics",
        lambda: calculate_daily_statistics(_daily_flows(_dates(3)), _dates(3)),
        {},
    ),
    (
        "MonthlyStatistics",
        lambda: calculate_monthly_statistics(_daily_flows(_dates(3)), _dates(3)),
        {"confidence_level": 0.95, "months": list(range(1, 13))},
    ),
    (
        "FrequencyAnalysisResult",
        lambda: FloodFrequencyAnalysis(_annual_maxima()).fit_gev(),
        {"distribution_name": "gev"},
    ),
    (
        "EmpiricalFrequency",
        lambda: FloodFrequencyAnalysis(_annual_maxima()).empirical_frequency(),
        {},
    ),
    (
        "MannKendallResult",
        _flow_stats_nan,
        {"trend_direction": "increasing"},
    ),
    (
        "LowFlowFrequencyResult",
        _low_flow_frequency,
        {},
    ),
    (
        "LowFlowSequence",
        lambda: _low_flow_analysis().sequences[0],
        {"min_flow": 1.0, "duration_days": 30},
    ),
    (
        "LowFlowAnalysisResult",
        _low_flow_analysis,
        {"threshold": 5.0, "n_events": 1},
    ),
    (
        "RatingCurveResult",
        _rating_curve,
        {"n_points": 25},
    ),
    (
        "WaterLevelZones",
        lambda: WaterLevelFrequency(
            np.linspace(100.0, 300.0, 400), bin_width=20.0
        ).rybczynski_zones(),
        {},
    ),
    (
        "FrequencyDistributionResult",
        lambda: WaterLevelFrequency(
            np.linspace(100.0, 300.0, 400), bin_width=20.0
        ).frequency_distribution(),
        {},
    ),
]


def _network_statistics():
    network = StreamNetwork(
        [
            StreamSegment(1, [], length_km=1.0),
            StreamSegment(2, [], length_km=0.8),
            StreamSegment(3, [1, 2], length_km=2.0),
        ],
        area_km2=10.0,
    )
    network.classify(OrderingMethod.STRAHLER)
    return network.get_statistics()


def _lookup(payload, path):
    value = payload
    for part in path.split("."):
        value = value[part]
    return value


def _approx(expected):
    if isinstance(expected, float):
        return pytest.approx(expected, rel=1e-6)
    if isinstance(expected, list):
        return pytest.approx(expected, rel=1e-6)
    if isinstance(expected, dict):
        return pytest.approx(expected, rel=1e-6)
    return expected


@pytest.mark.parametrize("name,factory,expected", CASES, ids=[c[0] for c in CASES])
def test_result_types_serialize_to_json(name, factory, expected):
    """Every public result type round-trips through json with its values."""
    obj = factory()

    assert type(obj).__name__ == name
    assert isinstance(obj, JsonResultMixin)

    payload = json.loads(obj.to_json())

    # Same keys, same order as the dataclass declaration.
    assert list(payload) == [f.name for f in dataclasses.fields(obj)]

    # Strict JSON (no NaN/Infinity tokens) and dict export is equivalent.
    assert obj.to_dict() == payload
    for token in ("NaN", "Infinity"):
        assert token not in obj.to_json()

    for path, value in expected.items():
        assert _lookup(payload, path) == _approx(value), path

    # Every numpy array field is exported element-wise.
    for f in dataclasses.fields(obj):
        attr = getattr(obj, f.name)
        if isinstance(attr, np.ndarray) and attr.dtype.kind == "f":
            np.testing.assert_allclose(
                np.array(payload[f.name], dtype=float), attr, rtol=1e-12
            )


def test_all_dataclasses_in_scope_have_mixin():
    """No public result dataclass in the serialized packages is left out."""
    import importlib
    import inspect
    import pkgutil

    import hydrolog

    missing = []
    for pkg in (
        "runoff",
        "precipitation",
        "morphometry",
        "network",
        "statistics",
        "hydrometrics",
    ):
        package = importlib.import_module(f"hydrolog.{pkg}")
        for info in pkgutil.walk_packages(package.__path__, f"hydrolog.{pkg}."):
            module = importlib.import_module(info.name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    dataclasses.is_dataclass(cls)
                    and cls.__module__ == module.__name__
                    and not issubclass(cls, JsonResultMixin)
                ):
                    missing.append(f"{cls.__module__}.{cls.__name__}")

    assert hydrolog.__name__ == "hydrolog"
    # WatershedParameters is an input type with its own (file-format) exporter.
    assert missing == ["hydrolog.morphometry.watershed_params.WatershedParameters"]


class TestSpecialCases:
    """Serialization behaviour with non-finite values and Any-typed fields."""

    def test_generator_result_nests_hydrograph_and_unit_hydrograph(self):
        result = _generator_result()
        payload = result.to_dict()

        assert isinstance(payload["hydrograph"], dict)
        assert isinstance(payload["unit_hydrograph_result"], dict)
        np.testing.assert_allclose(
            payload["hydrograph"]["discharge_m3s"], result.hydrograph.discharge_m3s
        )
        # only declared fields are exported, computed properties are not added
        assert "n_steps" not in payload["hydrograph"]
        assert list(payload["hydrograph"]) == [
            f.name for f in dataclasses.fields(result.hydrograph)
        ]

    def test_enum_values_in_cn_lookup(self):
        payload = lookup_cn("A", LandCover.FOREST, HydrologicCondition.GOOD).to_dict()
        assert payload["land_cover"] == "forest"
        assert payload["condition"] == "good"

    def test_nan_in_result_array_becomes_null(self):
        result = HietogramResult(
            times_min=np.array([10.0, 20.0]),
            intensities_mm=np.array([5.0, np.nan]),
            total_mm=float("inf"),
            duration_min=20.0,
            timestep_min=10.0,
        )
        payload = json.loads(result.to_json())
        assert payload["intensities_mm"] == [5.0, None]
        assert payload["total_mm"] is None

    def test_scalar_effective_precipitation(self):
        result = SCSCN(cn=80).effective_precipitation(50.0)
        payload = json.loads(result.to_json())
        assert payload["effective_mm"] == pytest.approx(float(result.effective_mm))
        assert payload["cn_adjusted"] == 80

    def test_arithmetic_mean_unaffected(self):
        assert arithmetic_mean(_STATIONS) == pytest.approx(20.0)


class TestWatershedParametersSchemaKey:
    """WatershedParameters keeps its format and tolerates a schema marker."""

    def test_from_dict_ignores_schema_key(self):
        data = {
            "schema": "hydrolog-catchment/1",
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }
        params = WatershedParameters.from_dict(data)
        assert params.area_km2 == 45.0
        assert "schema" not in params.to_dict()

    def test_to_dict_excludes_none_values(self):
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
        )
        assert params.to_dict() == {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }
