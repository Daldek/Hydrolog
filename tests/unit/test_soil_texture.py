"""Unit tests for hydrolog.soil.texture (USDA texture triangle, texture -> HSG).

Ported from the Kartograf 0.8.0 tests of ``kartograf.hydrology.hsg`` (ADR-025).
"""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.soil.hsg import HSG_CODES
from hydrolog.soil.texture import (
    _USDA_RULES,
    TEXTURE_CLASSES,
    TEXTURE_NAMES,
    TEXTURE_TO_HSG,
    classify_usda_texture,
    classify_usda_texture_array,
    texture_to_hsg,
    texture_to_hsg_array,
)

# Control points of the canonical USDA triangle (Soil Survey Manual):
# 4 points from the Kartograf audit (A4-4), the 2 boundary ties of ADR-025 and the
# centres of all 12 classes.
CANONICAL_CONTROL_POINTS = [
    # (clay, sand, silt, expected)
    (0, 70, 30, "sandy_loam"),  # silt + 2*clay = 30 >= 30
    (20, 45, 35, "loam"),  # sand <= 52, silt 28-50
    (35, 45, 20, "clay_loam"),  # sand <= 45 => not sandy_clay
    (12, 75, 13, "sandy_loam"),  # silt + 2*clay = 37 >= 30
    (20, 60, 20, "sandy_loam"),  # tie: also sandy_clay_loam, sandy_loam comes first
    (27, 30, 43, "loam"),  # tie: also clay_loam, loam comes first
    (5, 90, 5, "sand"),
    (5, 80, 15, "loamy_sand"),
    (10, 65, 25, "sandy_loam"),
    (20, 40, 40, "loam"),
    (15, 20, 65, "silt_loam"),
    (5, 5, 90, "silt"),
    (27, 60, 13, "sandy_clay_loam"),
    (33, 33, 34, "clay_loam"),
    (33, 10, 57, "silty_clay_loam"),
    (42, 52, 6, "sandy_clay"),
    (47, 6, 47, "silty_clay"),
    (60, 20, 20, "clay"),
]


def _simplex_points() -> list[tuple[int, int, int]]:
    """All points clay + sand + silt = 100 in 1 percent steps (5151 points)."""
    return [
        (clay, sand, 100 - clay - sand)
        for clay in range(0, 101)
        for sand in range(0, 101 - clay)
    ]


# Class counts of the integer g/kg simplex (clay + sand + silt = 1000, 501 501 points)
# computed with Kartograf 0.8.0 ``classify_usda_texture_array`` (ADR-025).
G_PER_KG_SIMPLEX_CLASS_COUNTS = {
    "sand": 7600,
    "loamy_sand": 15050,
    "sandy_loam": 57545,
    "loam": 35705,
    "silt_loam": 81975,
    "silt": 16980,
    "sandy_clay_loam": 38560,
    "clay_loam": 32280,
    "silty_clay_loam": 26130,
    "sandy_clay": 20100,
    "silty_clay": 20301,
    "clay": 149275,
}


class TestTextureClasses:
    """Tests for the texture class tables."""

    def test_twelve_classes_with_codes_one_to_twelve(self):
        """Test that the 12 USDA classes carry the codes 1-12, each once."""
        assert sorted(TEXTURE_CLASSES.values()) == list(range(1, 13))
        assert set(TEXTURE_CLASSES) == {
            "sand",
            "loamy_sand",
            "sandy_loam",
            "loam",
            "silt_loam",
            "silt",
            "sandy_clay_loam",
            "clay_loam",
            "silty_clay_loam",
            "sandy_clay",
            "silty_clay",
            "clay",
        }

    def test_names_are_the_reverse_mapping(self):
        """Test that TEXTURE_NAMES maps every code back to its class."""
        assert len(TEXTURE_NAMES) == 12
        for name, code in TEXTURE_CLASSES.items():
            assert TEXTURE_NAMES[code] == name

    def test_every_class_has_an_hsg(self):
        """Test that the texture -> HSG table covers exactly the 12 classes."""
        assert set(TEXTURE_TO_HSG) == set(TEXTURE_CLASSES)
        assert set(TEXTURE_TO_HSG.values()) == set(HSG_CODES)


class TestClassifyUsdaTexture:
    """Tests for the scalar USDA texture classification."""

    def test_sand(self):
        """Test sand classification."""
        assert classify_usda_texture(clay=5, sand=90, silt=5) == "sand"
        # canonical USDA: silt + 1.5*clay = 14.0 < 15
        assert classify_usda_texture(clay=8, sand=90, silt=2) == "sand"

    def test_loamy_sand(self):
        """Test loamy sand classification."""
        assert classify_usda_texture(clay=5, sand=80, silt=15) == "loamy_sand"
        # canonical USDA: silt + 1.5*clay = 17 >= 15, silt + 2*clay = 21 < 30
        assert classify_usda_texture(clay=8, sand=87, silt=5) == "loamy_sand"

    def test_sandy_loam(self):
        """Test sandy loam classification."""
        assert classify_usda_texture(clay=15, sand=60, silt=25) == "sandy_loam"
        assert classify_usda_texture(clay=10, sand=65, silt=25) == "sandy_loam"
        # canonical USDA: silt + 2*clay = 30 >= 30
        assert classify_usda_texture(clay=10, sand=80, silt=10) == "sandy_loam"
        # canonical USDA: silt + 2*clay = 37 >= 30
        assert classify_usda_texture(clay=12, sand=75, silt=13) == "sandy_loam"

    def test_loam(self):
        """Test loam classification."""
        assert classify_usda_texture(clay=20, sand=40, silt=40) == "loam"
        assert classify_usda_texture(clay=15, sand=35, silt=50) == "silt_loam"

    def test_silt_loam(self):
        """Test silt loam classification."""
        assert classify_usda_texture(clay=15, sand=20, silt=65) == "silt_loam"
        assert classify_usda_texture(clay=20, sand=15, silt=65) == "silt_loam"

    def test_silt(self):
        """Test silt classification."""
        assert classify_usda_texture(clay=5, sand=10, silt=85) == "silt"
        assert classify_usda_texture(clay=8, sand=8, silt=84) == "silt"

    def test_sandy_clay_loam(self):
        """Test sandy clay loam classification."""
        assert classify_usda_texture(clay=25, sand=55, silt=20) == "sandy_clay_loam"
        assert classify_usda_texture(clay=30, sand=50, silt=20) == "sandy_clay_loam"

    def test_clay_loam(self):
        """Test clay loam classification."""
        assert classify_usda_texture(clay=35, sand=30, silt=35) == "clay_loam"
        assert classify_usda_texture(clay=30, sand=35, silt=35) == "clay_loam"

    def test_silty_clay_loam(self):
        """Test silty clay loam classification."""
        assert classify_usda_texture(clay=35, sand=10, silt=55) == "silty_clay_loam"
        assert classify_usda_texture(clay=30, sand=15, silt=55) == "silty_clay_loam"

    def test_sandy_clay(self):
        """Test sandy clay classification."""
        assert classify_usda_texture(clay=40, sand=50, silt=10) == "sandy_clay"
        assert classify_usda_texture(clay=45, sand=48, silt=7) == "sandy_clay"

    def test_silty_clay(self):
        """Test silty clay classification."""
        assert classify_usda_texture(clay=45, sand=5, silt=50) == "silty_clay"
        assert classify_usda_texture(clay=50, sand=10, silt=40) == "silty_clay"

    def test_clay(self):
        """Test clay classification."""
        assert classify_usda_texture(clay=55, sand=25, silt=20) == "clay"
        assert classify_usda_texture(clay=60, sand=20, silt=20) == "clay"

    @pytest.mark.parametrize(
        ("clay", "sand", "silt", "expected"), CANONICAL_CONTROL_POINTS
    )
    def test_canonical_control_points(self, clay, sand, silt, expected):
        """Test the canonical control points of the USDA triangle."""
        assert classify_usda_texture(clay=clay, sand=sand, silt=silt) == expected

    @pytest.mark.parametrize("factor", [0.5, 2, 10, 1000])
    def test_unit_does_not_matter(self, factor):
        """Test that amounts are compared with their total, not with 100."""
        for clay, sand, silt, expected in CANONICAL_CONTROL_POINTS:
            result = classify_usda_texture(
                clay=clay * factor, sand=sand * factor, silt=silt * factor
            )
            assert result == expected

    def test_g_per_kg_inputs(self):
        """Test SoilGrids-style integer g/kg amounts."""
        assert classify_usda_texture(clay=450, sand=200, silt=350) == "clay"
        assert classify_usda_texture(clay=200, sand=400, silt=400) == "loam"

    def test_zero_sum_returns_loam(self):
        """Test that amounts summing to 0 (no data) are loam, not the sand rule."""
        assert classify_usda_texture(clay=0, sand=0, silt=0) == "loam"

    @pytest.mark.parametrize("name", ["clay", "sand", "silt"])
    def test_negative_amount_raises(self, name):
        """Test that a negative amount raises InvalidParameterError."""
        amounts = {"clay": 20.0, "sand": 40.0, "silt": 40.0}
        amounts[name] = -1.0
        with pytest.raises(InvalidParameterError, match=f"{name} must be") as caught:
            classify_usda_texture(**amounts)
        assert caught.value.details["option"] == name

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), "loam", None])
    def test_non_finite_or_non_numeric_amount_raises(self, bad):
        """Test that NaN, Inf and non-numbers raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            classify_usda_texture(clay=bad, sand=40, silt=40)


class TestTextureToHsg:
    """Tests for the texture class -> HSG mapping (Kartograf ADR-025)."""

    @pytest.mark.parametrize("texture", ["sand", "loamy_sand"])
    def test_group_a(self, texture):
        """Test textures that map to HSG A."""
        assert texture_to_hsg(texture) == "A"

    @pytest.mark.parametrize("texture", ["sandy_loam", "loam", "silt_loam", "silt"])
    def test_group_b(self, texture):
        """Test textures that map to HSG B (sandy_loam deviates from TR-55)."""
        assert texture_to_hsg(texture) == "B"

    @pytest.mark.parametrize(
        "texture", ["sandy_clay_loam", "clay_loam", "silty_clay_loam"]
    )
    def test_group_c(self, texture):
        """Test textures that map to HSG C (clay_loam, silty_clay_loam: not D)."""
        assert texture_to_hsg(texture) == "C"

    @pytest.mark.parametrize("texture", ["sandy_clay", "silty_clay", "clay"])
    def test_group_d(self, texture):
        """Test textures that map to HSG D."""
        assert texture_to_hsg(texture) == "D"

    def test_unknown_texture_raises(self):
        """Test that an unknown class raises instead of defaulting to a group."""
        with pytest.raises(InvalidParameterError, match="Unknown texture class"):
            texture_to_hsg("unknown")


class TestTextureToHsgArray:
    """Tests for the vectorised texture code -> HSG code mapping."""

    def test_agrees_with_table_for_every_class(self):
        """Test that every class code maps to the code of its TEXTURE_TO_HSG group."""
        codes = np.arange(1, 13, dtype=np.uint8)
        expected = [HSG_CODES[TEXTURE_TO_HSG[TEXTURE_NAMES[c]]] for c in range(1, 13)]
        result = texture_to_hsg_array(codes)
        assert result.tolist() == expected
        assert result.dtype == np.uint8

    def test_group_codes(self):
        """Test sand -> A, loam -> B, clay_loam -> C, clay -> D."""
        texture = [TEXTURE_CLASSES[n] for n in ("sand", "loam", "clay_loam", "clay")]
        assert texture_to_hsg_array(texture).tolist() == [1, 2, 3, 4]

    def test_zero_is_no_data(self):
        """Test that texture code 0 (no data) stays 0."""
        texture = np.array([0, TEXTURE_CLASSES["sand"], 0])
        assert texture_to_hsg_array(texture).tolist() == [0, 1, 0]

    def test_keeps_shape(self):
        """Test that a 2-D array keeps its shape."""
        texture = np.array([[1, 12], [4, 0]], dtype=np.uint8)
        assert texture_to_hsg_array(texture).tolist() == [[1, 4], [2, 0]]

    @pytest.mark.parametrize("bad", [[13], [-1, 4]])
    def test_code_out_of_range_raises(self, bad):
        """Test that codes outside 0-12 raise (a negative index must not wrap)."""
        with pytest.raises(InvalidParameterError, match="0-12"):
            texture_to_hsg_array(bad)

    def test_non_integer_codes_raise(self):
        """Test that float codes raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="integers"):
            texture_to_hsg_array(np.array([1.0, 2.0]))


class TestClassifyUsdaTextureArray:
    """Tests for the vectorised USDA texture classification."""

    def test_basic(self):
        """Test classification of a few cells."""
        clay = np.array([5, 20, 35, 55])
        sand = np.array([90, 40, 30, 20])
        silt = np.array([5, 40, 35, 25])

        result = classify_usda_texture_array(clay, sand, silt)

        assert result.dtype == np.uint8
        assert result[0] == TEXTURE_CLASSES["sand"]
        assert result[1] == TEXTURE_CLASSES["loam"]
        assert result[2] == TEXTURE_CLASSES["clay_loam"]
        assert result[3] == TEXTURE_CLASSES["clay"]

    def test_keeps_shape(self):
        """Test that a 2-D input gives a 2-D output."""
        clay = np.array([[5.0, 55.0], [20.0, 33.0]])
        sand = np.array([[90.0, 25.0], [40.0, 33.0]])
        silt = np.array([[5.0, 20.0], [40.0, 34.0]])

        result = classify_usda_texture_array(clay, sand, silt)

        assert [[TEXTURE_NAMES[int(c)] for c in row] for row in result] == [
            ["sand", "clay"],
            ["loam", "clay_loam"],
        ]

    def test_scalar_and_array_agree_on_whole_simplex(self):
        """Test that scalar and vector classifiers agree on 5151 simplex points."""
        points = _simplex_points()
        assert len(points) == 5151

        clay = np.array([p[0] for p in points], dtype=np.float64)
        sand = np.array([p[1] for p in points], dtype=np.float64)
        silt = np.array([p[2] for p in points], dtype=np.float64)

        codes = classify_usda_texture_array(clay, sand, silt)
        expected = np.array(
            [TEXTURE_CLASSES[classify_usda_texture(c, s, si)] for c, s, si in points],
            dtype=np.uint8,
        )

        assert np.array_equal(codes, expected)
        assert (codes >= 1).all() and (codes <= 12).all()

    def test_rules_cover_the_whole_simplex(self):
        """Test that every simplex point matches at least one rule.

        ``np.select`` falls back to loam for an unmatched point, which the 1-12
        range check cannot tell from a real loam: the rules themselves are checked.
        """
        points = np.array(_simplex_points(), dtype=np.float64)
        clay, sand, silt = points[:, 0], points[:, 1], points[:, 2]
        total = clay + sand + silt

        matched = np.zeros(len(points), dtype=bool)
        for _, rule in _USDA_RULES:
            matched |= rule(100 * clay, 100 * sand, 100 * silt, total)

        assert matched.all()

    def test_class_counts_on_the_g_per_kg_simplex_match_kartograf(self):
        """Test every class count of the whole g/kg simplex (501 501 points).

        Reference: ``classify_usda_texture_array`` of Kartograf 0.8.0 (ADR-025). All
        boundaries of the triangle lie on whole g/kg, so a changed ``<`` / ``<=``
        or threshold in any rule moves points between classes and fails here. It
        also proves that all 12 classes are reachable.
        """
        clay, sand = np.meshgrid(np.arange(1001.0), np.arange(1001.0))
        inside = clay + sand <= 1000
        clay, sand = clay[inside], sand[inside]
        silt = 1000 - clay - sand

        codes = classify_usda_texture_array(clay, sand, silt)

        counts = np.bincount(codes, minlength=13)
        assert {TEXTURE_NAMES[code]: int(counts[code]) for code in range(1, 13)} == (
            G_PER_KG_SIMPLEX_CLASS_COUNTS
        )

    def test_unit_invariance_on_random_integer_amounts(self):
        """Test that scaling all amounts by a factor never changes the class."""
        rng = np.random.default_rng(42)
        amounts = rng.integers(0, 1000, size=(3, 5000)).astype(np.float64)

        base = classify_usda_texture_array(*amounts)
        scaled = classify_usda_texture_array(*(10 * amounts))

        assert np.array_equal(base, scaled)

    def test_float32_input_boundary_clay_15(self):
        """Test that float32 at the clay = 15 % boundary agrees with the scalar."""
        # as in a raster pipeline: g/kg (float32) / 10 -> percent
        clay = np.array([np.float32(150)], dtype=np.float32) / np.float32(10)
        sand = np.array([np.float32(750)], dtype=np.float32) / np.float32(10)
        silt = np.array([np.float32(100)], dtype=np.float32) / np.float32(10)

        code = int(classify_usda_texture_array(clay, sand, silt)[0])
        scalar = classify_usda_texture(15.0, 75.0, 10.0)

        assert TEXTURE_NAMES[code] == scalar == "sandy_loam"

    @pytest.mark.parametrize(
        ("clay", "sand", "silt", "expected"),
        [
            (100, 900, 0, "loamy_sand"),  # silt + 1.5*clay = 150 = 15 % of 1000
            (99, 901, 0, "sand"),
            (150, 850, 0, "sandy_loam"),  # silt + 2*clay = 300 = 30 % of 1000
            (149, 851, 0, "loamy_sand"),
            (270, 330, 400, "loam"),  # clay = 270 g/kg = 27 %, tie with clay_loam
            (271, 329, 400, "clay_loam"),
        ],
    )
    def test_integer_g_per_kg_on_the_boundaries_is_exact(
        self, clay, sand, silt, expected
    ):
        """Test float32 g/kg amounts exactly on a boundary (no rounding of shares)."""
        codes = classify_usda_texture_array(
            np.array([clay], dtype=np.float32),
            np.array([sand], dtype=np.float32),
            np.array([silt], dtype=np.float32),
        )

        assert TEXTURE_NAMES[int(codes[0])] == expected

    def test_zero_sum_returns_loam(self):
        """Test that a zero total gives loam (explicit guard, not the sand rule)."""
        clay = np.array([0.0, 5.0])
        sand = np.array([0.0, 90.0])
        silt = np.array([0.0, 5.0])

        result = classify_usda_texture_array(clay, sand, silt)

        assert result[0] == TEXTURE_CLASSES["loam"]
        assert result[1] == TEXTURE_CLASSES["sand"]

    def test_nan_total_returns_loam_without_warning(self, recwarn):
        """Test that NaN amounts are tolerated (loam) and raise no warning."""
        nan = float("nan")

        result = classify_usda_texture_array([nan, 5.0], [90.0, nan], [5.0, 5.0])

        assert result.tolist() == [TEXTURE_CLASSES["loam"]] * 2
        assert len(recwarn) == 0

    @pytest.mark.parametrize("name", ["clay", "sand", "silt"])
    def test_negative_amount_raises(self, name):
        """Test that a negative amount anywhere in an array raises."""
        amounts = {
            "clay": np.array([20.0, 20.0]),
            "sand": np.array([40.0, 40.0]),
            "silt": np.array([40.0, 40.0]),
        }
        amounts[name][1] = -0.5
        with pytest.raises(InvalidParameterError, match=f"{name} must not be") as e:
            classify_usda_texture_array(**amounts)
        assert e.value.details["option"] == name

    def test_shape_mismatch_raises(self):
        """Test that inputs of different shapes raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="same shape"):
            classify_usda_texture_array([1.0, 2.0], [1.0, 2.0], [1.0, 2.0, 3.0])

    def test_non_numeric_raises(self):
        """Test that non-numeric values raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="clay"):
            classify_usda_texture_array(["a"], [1.0], [1.0])
