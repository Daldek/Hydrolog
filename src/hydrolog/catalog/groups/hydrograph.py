"""Group ``hydrograph``: design runoff hydrograph (precipitation -> discharge).

``hydrograph generate`` composes the effective precipitation of SCS-CN, a unit
hydrograph model and the discrete convolution of
:class:`~hydrolog.runoff.HydrographGenerator`. The options and the ``one_of`` groups
are public constants (:data:`GENERATE_OPTIONS`, :data:`GENERATE_ONE_OF`) because
``report generate`` builds on the same inputs. The module imports only the catalog
declarations, so reading the catalog stays cheap.
"""

from __future__ import annotations

import dataclasses

from hydrolog.catalog.groups.precip import HIETOGRAM_OPTIONS
from hydrolog.catalog.spec import Command, Option

_TC_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")
_UH_MODELS = ("scs", "nash", "clark", "snyder")

_SHAPE = {option.name: option for option in HIETOGRAM_OPTIONS}


def _optional(option: Option) -> Option:
    """Return the option, no longer required (the series alternative needs none)."""
    return dataclasses.replace(option, required=False)


GENERATE_OPTIONS: tuple[Option, ...] = (
    Option(
        name="watershed",
        type="object",
        description_pl=(
            "Parametry zlewni jako obiekt WatershedParameters (`area_km2`, "
            "`perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`, "
            "opcjonalnie `cn`, `mean_slope_m_per_m`, `channel_length_km`, "
            "`runoff_coeff`, `retardance`...). Dostarcza powierzchnię, CN i dane "
            "do czasu koncentracji; parametry modeli Nash, Clark (R) i Snyder "
            "podaje się jawnie."
        ),
        description=(
            "Watershed parameters as a WatershedParameters object (`area_km2`, "
            "`perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`, "
            "optionally `cn`, `mean_slope_m_per_m`, `channel_length_km`, "
            "`runoff_coeff`, `retardance`...). It supplies the area, the CN and "
            "the data for the time of concentration; the parameters of the Nash, "
            "Clark (R) and Snyder models are given explicitly."
        ),
    ),
    Option(
        name="watershed_file",
        type="path",
        path_role="input",
        description_pl=(
            "Plik JSON z parametrami zlewni (format "
            "`WatershedParameters.to_json()`); alternatywa dla `watershed` i "
            "`area_km2` + `cn`."
        ),
        description=(
            "JSON file with the watershed parameters (the "
            "`WatershedParameters.to_json()` format); alternative to "
            "`watershed` and `area_km2` + `cn`."
        ),
    ),
    Option(
        name="area_km2",
        type="number",
        description_pl=(
            "Powierzchnia zlewni [km²]; > 0. Razem z `cn`, zamiast zlewni "
            "(`watershed`, `watershed_file`)."
        ),
        description=(
            "Catchment area [km2]; > 0. Together with `cn`, instead of a "
            "watershed (`watershed`, `watershed_file`)."
        ),
        exclusive_minimum=0,
        unit="km2",
    ),
    Option(
        name="cn",
        type="number",
        description_pl=(
            "Liczba krzywej CN dla AMC II, 1–100 (może być ułamkowa, np. z `cn "
            "weighted`). Wymagana z `area_km2`; obok zlewni nadpisuje jej `cn` w "
            "całym obliczeniu, także w czasie koncentracji metodą nrcs (a gdy "
            "zlewnia nie ma `cn`, jest wymagana)."
        ),
        description=(
            "Curve Number CN for AMC II, 1-100 (may be fractional, e.g. from "
            "`cn weighted`). Required with `area_km2`; next to a watershed it "
            "overrides its `cn` in the whole computation, also in the time of "
            "concentration by nrcs (and is required when the watershed has none)."
        ),
        minimum=1,
        maximum=100,
    ),
    Option(
        name="tc_min",
        type="number",
        description_pl=(
            "Czas koncentracji [min]; > 0. Potrzebny modelom scs i clark; "
            "pominięty — liczony dla zlewni metodą `tc_method`. Modele nash i "
            "snyder go nie używają."
        ),
        description=(
            "Time of concentration [min]; > 0. Needed by the scs and clark "
            "models; when omitted it is computed for a watershed by `tc_method`. "
            "The nash and snyder models do not use it."
        ),
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="tc_method",
        type="choice",
        description_pl=(
            "Metoda liczenia tc ze zlewni, gdy nie podano `tc_min`; domyślnie "
            "kirpich. Pola zlewni wymagane przez metodę: patrz `tc watershed`."
        ),
        description=(
            "Method for computing tc from a watershed when `tc_min` is not "
            "given; default kirpich. The watershed fields a method needs: see "
            "`tc watershed`."
        ),
        choices=_TC_METHODS,
        meanings={
            "kirpich": "Kirpich formula (default).",
            "nrcs": "NRCS lag method (uses the CN).",
            "giandotti": "Giandotti formula.",
            "faa": "FAA formula.",
            "kerby": "Kerby formula for overland flow.",
            "kerby_kirpich": "Kerby overland flow plus Kirpich channel flow.",
        },
        meanings_pl={
            "kirpich": "Wzór Kirpicha (domyślny).",
            "nrcs": "Metoda lagu NRCS (używa CN).",
            "giandotti": "Wzór Giandottiego.",
            "faa": "Wzór FAA.",
            "kerby": "Wzór Kerby'ego dla spływu powierzchniowego.",
            "kerby_kirpich": "Kerby (spływ powierzchniowy) plus Kirpich (koryto).",
        },
    ),
    Option(
        name="ia_coefficient",
        type="number",
        description_pl=(
            "Współczynnik strat początkowych λ (Ia = λ·S), 0 < λ ≤ 1; domyślnie "
            "0,2 (standard, dla którego skalibrowano tablice CN)."
        ),
        description=(
            "Initial abstraction ratio λ (Ia = λ·S), 0 < λ <= 1; default 0.2 "
            "(the standard the CN tables are calibrated for)."
        ),
        exclusive_minimum=0,
        maximum=1,
        default=0.2,
    ),
    Option(
        name="amc",
        type="choice",
        description_pl=("Wilgotność poprzedzająca (AMC); domyślnie II."),
        description=("Antecedent moisture condition (AMC); default II."),
        choices=("I", "II", "III"),
        meanings={
            "I": "Dry antecedent moisture; CN lowered.",
            "II": "Normal antecedent moisture; CN as given.",
            "III": "Wet antecedent moisture; CN raised.",
        },
        meanings_pl={
            "I": "Sucho przed opadem; CN obniżone.",
            "II": "Przeciętna wilgotność; CN bez zmian.",
            "III": "Mokro przed opadem; CN podwyższone.",
        },
        default="II",
    ),
    _optional(_SHAPE["hietogram_type"]),
    _optional(_SHAPE["total_mm"]),
    _optional(_SHAPE["duration_min"]),
    _SHAPE["alpha"],
    _SHAPE["beta"],
    _SHAPE["peak_position"],
    Option(
        name="values",
        type="number_list",
        description_pl=(
            "Szereg opadu zamiast hietogramu projektowego: wysokości opadu w "
            "kolejnych krokach `timestep_min` [mm]; każda ≥ 0."
        ),
        description=(
            "A precipitation series instead of a design hyetograph: precipitation "
            "depths in consecutive steps of `timestep_min` [mm]; each >= 0."
        ),
        minimum=0,
        unit="mm",
    ),
    Option(
        name="input_file",
        type="path",
        path_role="input",
        description_pl=(
            "Plik CSV lub JSON z wysokościami opadu w krokach [mm] (zamiast `values`)."
        ),
        description=(
            "CSV or JSON file with the precipitation depths per step [mm] "
            "(instead of `values`)."
        ),
    ),
    Option(
        name="value_column",
        type="string",
        description_pl=(
            "Kolumna pliku z wysokościami opadu; pomijana dla pliku jednokolumnowego."
        ),
        description=(
            "File column with the precipitation depths; may be omitted for a "
            "one-column file."
        ),
    ),
    Option(
        name="timestep_min",
        type="number",
        description_pl=(
            "Krok czasowy [min]; > 0; domyślnie 5. Krok hietogramu "
            "projektowego, szeregu opadu, hydrogramu jednostkowego i wyniku."
        ),
        description=(
            "Time step [min]; > 0; default 5. The step of the design "
            "hyetograph, the precipitation series, the unit hydrograph and the "
            "result."
        ),
        exclusive_minimum=0,
        unit="min",
        default=5.0,
    ),
    Option(
        name="uh_model",
        type="choice",
        description_pl=(
            "Model hydrogramu jednostkowego; domyślnie scs. Opcje modelu: "
            "`nash_*`, `clark_*`, `snyder_*`."
        ),
        description=(
            "Unit hydrograph model; default scs. Model options: `nash_*`, "
            "`clark_*`, `snyder_*`."
        ),
        choices=_UH_MODELS,
        meanings={
            "scs": "SCS dimensionless unit hydrograph; needs tc.",
            "nash": "Nash cascade; needs `nash_n` and `nash_k_min`.",
            "clark": "Clark; needs tc and `clark_r_min` or `clark_r_tc_ratio`.",
            "snyder": "Snyder; needs `snyder_length_km` and "
            "`snyder_centroid_length_km`, no tc.",
        },
        meanings_pl={
            "scs": "Bezwymiarowy hydrogram SCS; wymaga tc.",
            "nash": "Kaskada Nasha; wymaga `nash_n` i `nash_k_min`.",
            "clark": "Clark; wymaga tc oraz `clark_r_min` lub `clark_r_tc_ratio`.",
            "snyder": "Snyder; wymaga `snyder_length_km` i "
            "`snyder_centroid_length_km`, bez tc.",
        },
        default="scs",
    ),
    Option(
        name="nash_n",
        type="number",
        description_pl=(
            "Nash: liczba zbiorników n (> 0, typowo 1–10); razem z "
            "`nash_k_min`. Parametry z metody Lutza daje `uh nash`."
        ),
        description=(
            "Nash: number of reservoirs n (> 0, typically 1-10); together with "
            "`nash_k_min`. `uh nash` derives parameters by the Lutz method."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="nash_k_min",
        type="number",
        description_pl=(
            "Nash: stała magazynowania K [min] (> 0, typowo 10–200); razem z `nash_n`."
        ),
        description=(
            "Nash: storage constant K [min] (> 0, typically 10-200); together "
            "with `nash_n`."
        ),
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="clark_r_min",
        type="number",
        description_pl=(
            "Clark: stała retencji R [min] (> 0); alternatywa dla `clark_r_tc_ratio`."
        ),
        description=(
            "Clark: storage constant R [min] (> 0); alternative to `clark_r_tc_ratio`."
        ),
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="clark_r_tc_ratio",
        type="number",
        description_pl=(
            "Clark: stosunek R/tc (> 0, typowo 0,2–1,5), R = stosunek · tc; "
            "alternatywa dla `clark_r_min`."
        ),
        description=(
            "Clark: ratio R/tc (> 0, typically 0.2-1.5), R = ratio · tc; "
            "alternative to `clark_r_min`."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="snyder_length_km",
        type="number",
        description_pl=(
            "Snyder: długość cieku głównego L [km] (> 0); razem z "
            "`snyder_centroid_length_km`."
        ),
        description=(
            "Snyder: main stream length L [km] (> 0); together with "
            "`snyder_centroid_length_km`."
        ),
        exclusive_minimum=0,
        unit="km",
    ),
    Option(
        name="snyder_centroid_length_km",
        type="number",
        description_pl=(
            "Snyder: długość od przekroju zamykającego do środka ciężkości "
            "zlewni Lc [km] (> 0)."
        ),
        description=(
            "Snyder: length from the outlet to the catchment centroid Lc [km] (> 0)."
        ),
        exclusive_minimum=0,
        unit="km",
    ),
    Option(
        name="snyder_ct",
        type="number",
        description_pl="Snyder: współczynnik czasowy Ct (> 0); domyślnie 1,5.",
        description="Snyder: time coefficient Ct (> 0); default 1.5.",
        exclusive_minimum=0,
    ),
    Option(
        name="snyder_cp",
        type="number",
        description_pl="Snyder: współczynnik szczytowy Cp (> 0); domyślnie 0,6.",
        description="Snyder: peak coefficient Cp (> 0); default 0.6.",
        exclusive_minimum=0,
    ),
)
"""Options of ``hydrograph generate`` (shared with ``report generate``)."""

GENERATE_ONE_OF: tuple[tuple[str, ...], ...] = (
    ("watershed",),
    ("watershed_file",),
    ("area_km2", "cn"),
)
"""Alternative sources of the catchment: a watershed or ``area_km2`` + ``cn``."""

_WATERSHED_EXAMPLE = {
    "name": "Potok Młynówka",
    "area_km2": 45.3,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "mean_slope_m_per_m": 0.025,
    "cn": 72,
}

COMMANDS: tuple[Command, ...] = (
    Command(
        name="hydrograph generate",
        operation_id="hydrolog_hydrograph_generate",
        summary_pl=(
            "Oblicz projektowy hydrogram odpływu bezpośredniego: opad, SCS-CN, "
            "hydrogram jednostkowy, splot."
        ),
        summary=(
            "Compute the design direct-runoff hydrograph: rainfall, SCS-CN, unit "
            "hydrograph, convolution."
        ),
        description_pl=(
            "Projektowy hydrogram z hietogramu lub szeregu opadu, SCS-CN i hydrogramu "
            "jednostkowego (`uh_model`). Zlewnia: `watershed` lub `area_km2` + `cn`. "
            "Nie do szeregów obserwowanych (IMGWTools) ani samych strat (`scs "
            "effective`). Zwraca szczyt, objętość, bilans, szeregi."
        ),
        description=(
            "Design hydrograph from a hyetograph or rainfall series, SCS-CN and a unit"
            " hydrograph (`uh_model`). Catchment: a watershed or `area_km2` + `cn`. "
            "Not for observed series (IMGWTools) or losses only (`scs effective`). "
            "Returns peak, volume, balance, series."
        ),
        function="hydrolog.operations.hydrograph_generate",
        options=GENERATE_OPTIONS,
        one_of=GENERATE_ONE_OF,
        result_schema="hydrolog-hydrograph-generate/1",
        cardinality="bounded",
        rules=(
            (
                "Give one catchment source and one rainfall source (hyetograph or "
                "series)."
            ),
            "scs and clark need tc: pass tc_min or a watershed.",
            "Check `notices` for parameters outside typical ranges.",
        ),
        rules_pl=(
            "Podaj jedno źródło zlewni i jedno źródło opadu (hietogram lub szereg).",
            "scs i clark wymagają tc: podaj tc_min lub zlewnię.",
            "Sprawdź `notices`: parametry poza typowym zakresem.",
        ),
        errors=("validation_error", "not_found", "data_error", "forbidden"),
        core=True,
        example_results=(
            {
                "peak_discharge_m3s": 54.9222,
                "time_to_peak_min": 95.0,
                "total_volume_m3": 321295.0,
                "runoff_coefficient": 0.141794,
                "uh_model": "scs",
            },
            {
                "peak_discharge_m3s": 210.709,
                "time_to_peak_min": 110.0,
                "total_volume_m3": 1376330.0,
                "runoff_coefficient": 0.489735,
                "uh_model": "scs",
            },
            {
                "peak_discharge_m3s": 26.245,
                "time_to_peak_min": 140.0,
                "total_volume_m3": 282608.0,
                "runoff_coefficient": 0.130841,
                "uh_model": "nash",
            },
            {
                "peak_discharge_m3s": 40.8926,
                "time_to_peak_min": 120.0,
                "total_volume_m3": 321163.0,
                "runoff_coefficient": 0.141794,
                "uh_model": "clark",
            },
            {
                "peak_discharge_m3s": 20.6618,
                "time_to_peak_min": 390.0,
                "total_volume_m3": 708968.0,
                "runoff_coefficient": 0.141794,
                "uh_model": "snyder",
            },
        ),
        examples=(
            {
                "watershed": _WATERSHED_EXAMPLE,
                "tc_method": "kirpich",
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
                "timestep_min": 5.0,
                "uh_model": "scs",
            },
            {
                "area_km2": 45.3,
                "cn": 72,
                "tc_min": 90.0,
                "hietogram_type": "euler_ii",
                "total_mm": 62.0,
                "duration_min": 120.0,
                "amc": "III",
            },
            {
                "area_km2": 45.0,
                "cn": 72,
                "values": [5.0, 10.0, 15.0, 10.0, 5.0, 3.0],
                "timestep_min": 10.0,
                "uh_model": "nash",
                "nash_n": 3.0,
                "nash_k_min": 48.0,
            },
            {
                "area_km2": 45.3,
                "cn": 72,
                "tc_min": 120.0,
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
                "timestep_min": 10.0,
                "uh_model": "clark",
                "clark_r_tc_ratio": 0.5,
            },
            {
                "area_km2": 100.0,
                "cn": 72,
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
                "timestep_min": 10.0,
                "uh_model": "snyder",
                "snyder_length_km": 15.0,
                "snyder_centroid_length_km": 8.0,
            },
        ),
    ),
)
