"""Unit tests for hydrolog.soil.texture (USDA texture triangle, texture -> HSG).

Ported from the Kartograf 0.8.0 tests of ``kartograf.hydrology.hsg`` (ADR-025). The
class limits are tested against the definitions of the Soil Survey Manual (2017).
"""

from fractions import Fraction

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.soil.hsg import HSG_CODES
from hydrolog.soil.texture import (
    TEXTURE_CLASSES,
    TEXTURE_NAMES,
    TEXTURE_TO_HSG,
    classify_usda_texture,
    classify_usda_texture_array,
    texture_to_hsg,
    texture_to_hsg_array,
)

# Soil Science Division Staff (2017), Soil Survey Manual, USDA Agriculture Handbook
# No. 18, ch. 3, "Definitions of Soil Texture Classes and Subclasses", pp. 122-124
# (textural triangle Fig. 3-7, p. 125); "SSM 2017" below. Amounts in percent.

# One point inside each of the 12 classes, on none of the limits of its class.
CLASS_INTERIOR_POINTS = [
    # (clay, sand, silt, expected)
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

# Points on the limits of the SSM 2017 definitions, each limit from both sides:
# "X to less than Y percent" includes X and excludes Y, "more than X" excludes X,
# "X percent or more" and "X percent or less" include X. The class follows from the
# wording alone; the HSG is the one of TEXTURE_TO_HSG.
SSM2017_BOUNDARY_POINTS = [
    # (clay, sand, silt, texture, hsg)
    # p. 122: sands "silt plus 1.5 times the percentage of clay is less than 15",
    # loamy sands "15 or more"
    (0, 85, 15, "loamy_sand", "A"),
    (2, 86, 12, "loamy_sand", "A"),
    (0, 86, 14, "sand", "A"),
    (2, 87, 11, "sand", "A"),
    # pp. 122-123: loamy sands "silt plus twice the percentage of clay is less than
    # 30", sandy loams "30 or more"
    (0, 70, 30, "sandy_loam", "B"),
    (10, 80, 10, "sandy_loam", "B"),
    (0, 71, 29, "loamy_sand", "A"),
    (10, 81, 9, "loamy_sand", "A"),
    # pp. 123-124: sandy loams "7 to less than 20 percent clay", sandy clay loam
    # "20 to less than 35 percent clay"
    (20, 60, 20, "sandy_clay_loam", "C"),
    (20, 53, 27, "sandy_clay_loam", "C"),
    (19, 61, 20, "sandy_loam", "B"),
    (19, 54, 27, "sandy_loam", "B"),
    # pp. 123-124: sandy loams "more than 52 percent sand", loam "52 percent or less"
    (15, 52, 33, "loam", "B"),
    (15, 53, 32, "sandy_loam", "B"),
    # pp. 123-124: loam "7 to less than 27 percent clay", sandy loams "less than 7
    # percent clay and less than 50 percent silt", silt loam "50 to less than 80
    # percent silt and less than 12 percent clay"
    (7, 45, 48, "loam", "B"),
    (6, 45, 49, "sandy_loam", "B"),
    (6, 44, 50, "silt_loam", "B"),
    # p. 124: loam "7 to less than 27 percent clay", clay loam "27 to less than 40"
    (27, 38, 35, "clay_loam", "C"),
    (27, 45, 28, "clay_loam", "C"),
    (26, 38, 36, "loam", "B"),
    (26, 46, 28, "loam", "B"),
    # p. 124: loam "28 to less than 50 percent silt", sandy clay loam "less than 28
    # percent silt", silt loam "50 percent or more silt"
    (25, 47, 28, "loam", "B"),
    (25, 48, 27, "sandy_clay_loam", "C"),
    (10, 40, 50, "silt_loam", "B"),
    (10, 41, 49, "loam", "B"),
    # p. 124: silt loam "12 to less than 27 percent clay", clay loam and silty clay
    # loam "27 to less than 40 percent clay"
    (27, 22, 51, "clay_loam", "C"),
    (27, 15, 58, "silty_clay_loam", "C"),
    (26, 22, 52, "silt_loam", "B"),
    (26, 15, 59, "silt_loam", "B"),
    # p. 124: silt "80 percent or more silt and less than 12 percent clay"
    (5, 15, 80, "silt", "B"),
    (5, 16, 79, "silt_loam", "B"),
    (12, 8, 80, "silt_loam", "B"),
    (11, 9, 80, "silt", "B"),
    # p. 124: sandy clay loam "20 to less than 35 percent clay", sandy clay "35
    # percent or more clay"
    (35, 46, 19, "sandy_clay", "D"),
    (34, 46, 20, "sandy_clay_loam", "C"),
    # p. 124: sandy clay loam and sandy clay "more than 45 percent sand", clay loam
    # "more than 20 to 45 percent sand", silty clay loam "20 percent or less sand"
    (30, 45, 25, "clay_loam", "C"),
    (30, 46, 24, "sandy_clay_loam", "C"),
    (35, 45, 20, "clay_loam", "C"),
    (30, 21, 49, "clay_loam", "C"),
    (30, 20, 50, "silty_clay_loam", "C"),
    # p. 124: clay loam and silty clay loam "27 to less than 40 percent clay", clay
    # and silty clay "40 percent or more clay"
    (40, 30, 30, "clay", "D"),
    (39, 30, 31, "clay_loam", "C"),
    (40, 20, 40, "silty_clay", "D"),
    (39, 20, 41, "silty_clay_loam", "C"),
    # p. 124: clay "45 percent or less sand, and less than 40 percent silt", sandy
    # clay "more than 45 percent sand", silty clay "40 percent or more silt"
    (40, 45, 15, "clay", "D"),
    (40, 46, 14, "sandy_clay", "D"),
    (45, 15, 40, "silty_clay", "D"),
    (45, 16, 39, "clay", "D"),
]


def _ssm2017_classes(clay: int, sand: int, silt: int) -> list[str]:
    """The SSM 2017 definitions (pp. 122-124) that one composition satisfies.

    Transcribed from the wording, independently of the rules of the code, and
    evaluated in exact rational arithmetic on the shares in percent. All twelve
    definitions are evaluated; no rule order is involved.
    """
    total = Fraction(clay + sand + silt)
    c, s, si = (100 * Fraction(amount) / total for amount in (clay, sand, silt))
    silt_1_5_clay = si + Fraction(3, 2) * c  # "silt plus 1.5 times ... clay"
    silt_2_clay = si + 2 * c  # "silt plus twice the percentage of clay"
    definitions = {
        # "more than 85 percent sand, and ... less than 15"
        "sand": s > 85 and silt_1_5_clay < 15,
        # "between 70 and 90 percent sand, ... 15 or more, and ... less than 30"
        # (the two inequalities alone give 70 < sand <= 90)
        "loamy_sand": 70 <= s <= 90 and silt_1_5_clay >= 15 and silt_2_clay < 30,
        # "7 to less than 20 percent clay and more than 52 percent sand, and ... 30
        # or more; OR ... less than 7 percent clay and less than 50 percent silt,
        # and ... 30 or more"
        "sandy_loam": (7 <= c < 20 and s > 52 and silt_2_clay >= 30)
        or (c < 7 and si < 50 and silt_2_clay >= 30),
        # "7 to less than 27 percent clay, 28 to less than 50 percent silt, and 52
        # percent or less sand"
        "loam": 7 <= c < 27 and 28 <= si < 50 and s <= 52,
        # "50 percent or more silt and 12 to less than 27 percent clay; OR ... 50 to
        # less than 80 percent silt and less than 12 percent clay"
        "silt_loam": (si >= 50 and 12 <= c < 27) or (50 <= si < 80 and c < 12),
        # "80 percent or more silt and less than 12 percent clay"
        "silt": si >= 80 and c < 12,
        # "20 to less than 35 percent clay, less than 28 percent silt, and more than
        # 45 percent sand"
        "sandy_clay_loam": 20 <= c < 35 and si < 28 and s > 45,
        # "27 to less than 40 percent clay and more than 20 to 45 percent sand"
        "clay_loam": 27 <= c < 40 and 20 < s <= 45,
        # "27 to less than 40 percent clay and 20 percent or less sand"
        "silty_clay_loam": 27 <= c < 40 and s <= 20,
        # "35 percent or more clay and more than 45 percent sand"
        "sandy_clay": c >= 35 and s > 45,
        # "40 percent or more clay and 40 percent or more silt"
        "silty_clay": c >= 40 and si >= 40,
        # "40 percent or more clay, 45 percent or less sand, and less than 40
        # percent silt"
        "clay": c >= 40 and s <= 45 and si < 40,
    }
    return [name for name, holds in definitions.items() if holds]


def _simplex_points() -> list[tuple[int, int, int]]:
    """All points clay + sand + silt = 100 in 1 percent steps (5151 points)."""
    return [
        (clay, sand, 100 - clay - sand)
        for clay in range(0, 101)
        for sand in range(0, 101 - clay)
    ]


def _simplex_arrays(total: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Clay, sand and silt of all integer points with clay + sand + silt = total."""
    clay, sand = np.meshgrid(np.arange(total + 1.0), np.arange(total + 1.0))
    inside = clay + sand <= total
    clay, sand = clay[inside], sand[inside]
    return clay, sand, total - clay - sand


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
        ("clay", "sand", "silt", "expected"), CLASS_INTERIOR_POINTS
    )
    def test_a_point_inside_each_class(self, clay, sand, silt, expected):
        """Test one point inside each of the 12 classes of the USDA triangle."""
        assert classify_usda_texture(clay=clay, sand=sand, silt=silt) == expected

    @pytest.mark.parametrize("factor", [0.5, 2, 10, 1000])
    def test_unit_does_not_matter(self, factor):
        """Test that amounts are compared with their total, not with 100."""
        points = CLASS_INTERIOR_POINTS + [p[:4] for p in SSM2017_BOUNDARY_POINTS]
        for clay, sand, silt, expected in points:
            result = classify_usda_texture(
                clay=clay * factor, sand=sand * factor, silt=silt * factor
            )
            assert result == expected

    def test_g_per_kg_inputs(self):
        """Test SoilGrids-style integer g/kg amounts."""
        assert classify_usda_texture(clay=450, sand=200, silt=350) == "clay"
        assert classify_usda_texture(clay=200, sand=400, silt=400) == "loam"

    @pytest.mark.parametrize("name", ["clay", "sand", "silt"])
    def test_negative_amount_raises(self, name):
        """Test that a negative amount raises InvalidParameterError."""
        amounts = {"clay": 20.0, "sand": 40.0, "silt": 40.0}
        amounts[name] = -1.0
        with pytest.raises(InvalidParameterError) as caught:
            classify_usda_texture(**amounts)
        assert caught.value.details["option"] == name
        assert caught.value.details["reason"] == "outside_physical_range"

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
            (200, 600, 200, "sandy_clay_loam"),  # clay = 200 g/kg = 20 %
            (199, 601, 200, "sandy_loam"),
            (270, 330, 400, "clay_loam"),  # clay = 270 g/kg = 27 %
            (269, 331, 400, "loam"),
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


class TestSoilSurveyManualClassLimits:
    """Tests of the class limits against the Soil Survey Manual (2017) definitions."""

    @pytest.mark.parametrize(
        ("clay", "sand", "silt", "texture", "hsg"), SSM2017_BOUNDARY_POINTS
    )
    def test_point_on_a_limit_in_percent_and_g_per_kg(
        self, clay, sand, silt, texture, hsg
    ):
        """Test that a point on a class limit gets the class of the SSM wording."""
        assert classify_usda_texture(clay=clay, sand=sand, silt=silt) == texture
        assert (
            classify_usda_texture(clay=10 * clay, sand=10 * sand, silt=10 * silt)
            == texture
        )
        assert texture_to_hsg(texture) == hsg

    @pytest.mark.parametrize("dtype", [np.float64, np.float32, np.int16])
    @pytest.mark.parametrize("scale", [1, 10], ids=["percent", "g_per_kg"])
    def test_points_on_the_limits_as_arrays(self, scale, dtype):
        """Test the points on the limits as one array, with their HSG codes."""
        clay, sand, silt = (
            scale * np.array([point[axis] for point in SSM2017_BOUNDARY_POINTS], dtype)
            for axis in range(3)
        )

        codes = classify_usda_texture_array(clay, sand, silt)

        assert [TEXTURE_NAMES[int(code)] for code in codes] == [
            point[3] for point in SSM2017_BOUNDARY_POINTS
        ]
        assert texture_to_hsg_array(codes).tolist() == [
            HSG_CODES[point[4]] for point in SSM2017_BOUNDARY_POINTS
        ]

    def test_integer_percent_simplex_follows_the_ssm_definitions(self):
        """Test all 5151 integer compositions against the SSM 2017 transcription.

        Every point satisfies exactly one definition of :func:`_ssm2017_classes`
        (the definitions partition the triangle, with no ties), and the scalar and
        the array classifier both return that class.
        """
        points = _simplex_points()
        classes = [_ssm2017_classes(*point) for point in points]
        assert [
            p for p, hits in zip(points, classes, strict=True) if len(hits) != 1
        ] == []
        expected = [hits[0] for hits in classes]

        codes = classify_usda_texture_array(*np.array(points, dtype=np.float64).T)
        array = [TEXTURE_NAMES[int(code)] for code in codes]
        scalar = [classify_usda_texture(*point) for point in points]

        assert [
            (point, got, want)
            for point, got, want in zip(points, array, expected, strict=True)
            if got != want
        ] == []
        assert scalar == array
