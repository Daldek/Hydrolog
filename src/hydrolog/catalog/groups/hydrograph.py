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
        description=(
            "Parametry zlewni jako obiekt WatershedParameters (`area_km2`, "
            "`perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`, "
            "opcjonalnie `cn`, `mean_slope_m_per_m`, `channel_length_km`, "
            "`runoff_coeff`, `retardance`...). Dostarcza powierzchnię, CN i dane "
            "do czasu koncentracji; parametry modeli Nash, Clark (R) i Snyder "
            "podaje się jawnie."
        ),
        description_en=(
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
        description=(
            "Plik JSON z parametrami zlewni (format "
            "`WatershedParameters.to_json()`); alternatywa dla `watershed` i "
            "`area_km2` + `cn`."
        ),
        description_en=(
            "JSON file with the watershed parameters (the "
            "`WatershedParameters.to_json()` format); alternative to "
            "`watershed` and `area_km2` + `cn`."
        ),
    ),
    Option(
        name="area_km2",
        type="number",
        description=(
            "Powierzchnia zlewni [km²]; > 0. Razem z `cn`, zamiast zlewni "
            "(`watershed`, `watershed_file`)."
        ),
        description_en=(
            "Catchment area [km2]; > 0. Together with `cn`, instead of a "
            "watershed (`watershed`, `watershed_file`)."
        ),
        exclusive_minimum=0,
        unit="km2",
    ),
    Option(
        name="cn",
        type="number",
        description=(
            "Liczba krzywej CN dla AMC II, 1–100 (może być ułamkowa, np. z `cn "
            "weighted`). Wymagana z `area_km2`; obok zlewni nadpisuje jej `cn` w "
            "całym obliczeniu, także w czasie koncentracji metodą nrcs (a gdy "
            "zlewnia nie ma `cn`, jest wymagana)."
        ),
        description_en=(
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
        description=(
            "Czas koncentracji [min]; > 0. Potrzebny modelom scs i clark; "
            "pominięty — liczony dla zlewni metodą `tc_method`. Modele nash i "
            "snyder go nie używają."
        ),
        description_en=(
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
        description=(
            "Metoda liczenia tc ze zlewni, gdy nie podano `tc_min`; domyślnie "
            "kirpich. Pola zlewni wymagane przez metodę: patrz `tc watershed`."
        ),
        description_en=(
            "Method for computing tc from a watershed when `tc_min` is not "
            "given; default kirpich. The watershed fields a method needs: see "
            "`tc watershed`."
        ),
        choices=_TC_METHODS,
    ),
    Option(
        name="ia_coefficient",
        type="number",
        description=(
            "Współczynnik strat początkowych λ (Ia = λ·S), 0 < λ ≤ 1; domyślnie "
            "0,2 (standard, dla którego skalibrowano tablice CN)."
        ),
        description_en=(
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
        description=(
            "Wilgotność poprzedzająca (AMC): I — sucho, II — przeciętnie, III — "
            "mokro; domyślnie II."
        ),
        description_en=(
            "Antecedent moisture condition (AMC): I - dry, II - normal, III - "
            "wet; default II."
        ),
        choices=("I", "II", "III"),
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
        description=(
            "Szereg opadu zamiast hietogramu projektowego: wysokości opadu w "
            "kolejnych krokach `timestep_min` [mm]; każda ≥ 0."
        ),
        description_en=(
            "A precipitation series instead of a design hyetograph: precipitation "
            "depths in consecutive steps of `timestep_min` [mm]; each >= 0."
        ),
        minimum=0,
        unit="mm",
    ),
    Option(
        name="input_file",
        type="path",
        description=(
            "Plik CSV lub JSON z wysokościami opadu w krokach [mm] (zamiast `values`)."
        ),
        description_en=(
            "CSV or JSON file with the precipitation depths per step [mm] "
            "(instead of `values`)."
        ),
    ),
    Option(
        name="value_column",
        type="string",
        description=(
            "Kolumna pliku z wysokościami opadu; pomijana dla pliku jednokolumnowego."
        ),
        description_en=(
            "File column with the precipitation depths; may be omitted for a "
            "one-column file."
        ),
    ),
    Option(
        name="timestep_min",
        type="number",
        description=(
            "Krok czasowy [min]; > 0; domyślnie 5. Krok hietogramu "
            "projektowego, szeregu opadu, hydrogramu jednostkowego i wyniku."
        ),
        description_en=(
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
        description=(
            "Model hydrogramu jednostkowego: scs (wymaga tc), nash (`nash_n`, "
            "`nash_k_min`), clark (tc oraz `clark_r_min` albo `clark_r_tc_ratio`), "
            "snyder (`snyder_length_km`, `snyder_centroid_length_km`; bez tc). "
            "Domyślnie scs."
        ),
        description_en=(
            "Unit hydrograph model: scs (needs tc), nash (`nash_n`, "
            "`nash_k_min`), clark (tc and `clark_r_min` or `clark_r_tc_ratio`), "
            "snyder (`snyder_length_km`, `snyder_centroid_length_km`; no tc). "
            "Default scs."
        ),
        choices=_UH_MODELS,
        default="scs",
    ),
    Option(
        name="nash_n",
        type="number",
        description=(
            "Nash: liczba zbiorników n (> 0, typowo 1–10); razem z "
            "`nash_k_min`. Parametry z metody Lutza daje `uh nash`."
        ),
        description_en=(
            "Nash: number of reservoirs n (> 0, typically 1-10); together with "
            "`nash_k_min`. `uh nash` derives parameters by the Lutz method."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="nash_k_min",
        type="number",
        description=(
            "Nash: stała magazynowania K [min] (> 0, typowo 10–200); razem z `nash_n`."
        ),
        description_en=(
            "Nash: storage constant K [min] (> 0, typically 10-200); together "
            "with `nash_n`."
        ),
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="clark_r_min",
        type="number",
        description=(
            "Clark: stała retencji R [min] (> 0); alternatywa dla `clark_r_tc_ratio`."
        ),
        description_en=(
            "Clark: storage constant R [min] (> 0); alternative to `clark_r_tc_ratio`."
        ),
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="clark_r_tc_ratio",
        type="number",
        description=(
            "Clark: stosunek R/tc (> 0, typowo 0,2–1,5), R = stosunek · tc; "
            "alternatywa dla `clark_r_min`."
        ),
        description_en=(
            "Clark: ratio R/tc (> 0, typically 0.2-1.5), R = ratio · tc; "
            "alternative to `clark_r_min`."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="snyder_length_km",
        type="number",
        description=(
            "Snyder: długość cieku głównego L [km] (> 0); razem z "
            "`snyder_centroid_length_km`."
        ),
        description_en=(
            "Snyder: main stream length L [km] (> 0); together with "
            "`snyder_centroid_length_km`."
        ),
        exclusive_minimum=0,
        unit="km",
    ),
    Option(
        name="snyder_centroid_length_km",
        type="number",
        description=(
            "Snyder: długość od przekroju zamykającego do środka ciężkości "
            "zlewni Lc [km] (> 0)."
        ),
        description_en=(
            "Snyder: length from the outlet to the catchment centroid Lc [km] (> 0)."
        ),
        exclusive_minimum=0,
        unit="km",
    ),
    Option(
        name="snyder_ct",
        type="number",
        description="Snyder: współczynnik czasowy Ct (> 0); domyślnie 1,5.",
        description_en="Snyder: time coefficient Ct (> 0); default 1.5.",
        exclusive_minimum=0,
    ),
    Option(
        name="snyder_cp",
        type="number",
        description="Snyder: współczynnik szczytowy Cp (> 0); domyślnie 0,6.",
        description_en="Snyder: peak coefficient Cp (> 0); default 0.6.",
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
        operation_id="hydrograph_generate",
        summary=(
            "Hydrogram odpływu bezpośredniego zlewni: opad → SCS-CN → hydrogram "
            "jednostkowy → splot."
        ),
        summary_en=(
            "Direct runoff hydrograph of a catchment: precipitation -> SCS-CN "
            "-> unit hydrograph -> convolution."
        ),
        description=(
            "Projektowy hydrogram odpływu bezpośredniego zlewni (HydrographGenerator): "
            "(1) opad — hietogram projektowy z `hietogram_type`, `total_mm`, "
            "`duration_min` (typy i parametry jak w `precip hietogram`) albo "
            "szereg wysokości opadu w krokach (`values` albo `input_file` + "
            "`value_column`), zawsze z krokiem `timestep_min`; (2) opad "
            "efektywny metodą SCS-CN z `cn` (AMC II), korektą `amc` i `ia_"
            "coefficient` (patrz `scs effective`); (3) hydrogram jednostkowy "
            "modelu `uh_model` — scs (wymaga tc), nash (`nash_n`, `nash_k_min`), "
            "clark (tc oraz `clark_r_min` albo `clark_r_tc_ratio`), snyder "
            "(`snyder_length_km`, `snyder_centroid_length_km`, opcjonalnie "
            "`snyder_ct`, `snyder_cp`; bez tc) — modele opisują komendy `uh ...`; "
            "(4) dyskretny splot opadu efektywnego z hydrogramem jednostkowym. "
            "Zlewnia: `watershed`/`watershed_file` (WatershedParameters: "
            "powierzchnia, CN, dane do tc) albo `area_km2` + `cn`; `cn` podane "
            "obok zlewni nadpisuje jej wartość w całym obliczeniu, także w czasie "
            "koncentracji metodą nrcs. Czas koncentracji (scs, clark): "
            "`tc_min` albo, dla zlewni, liczony metodą `tc_method` (domyślnie "
            "kirpich; pola zlewni: patrz `tc watershed`). Opcje spoza wybranego "
            "wariantu (typu hietogramu, modelu) są odrzucane. Model snyder ma "
            "własne równanie lagu — `tc_min` nie jest do niego używany, a jego "
            "hydrogram jednostkowy jest liczony dla czasu trwania opadu równego "
            "krokowi `timestep_min` (tLR, tpR i qpR wg Snydera), bo splot traktuje "
            "go jako odpowiedź na 1 mm opadu efektywnego w jednym kroku. Wynik: "
            "szczyt Q [m³/s], czas do szczytu [min], objętość odpływu [m³], "
            "współczynnik odpływu, bilans (opad, opad efektywny, S, Ia, CN po "
            "korekcie AMC), parametry hydrogramu jednostkowego oraz pełne "
            "szeregi: czas, przepływ, opad i opad efektywny w krokach. "
            "Informacje: ostrzeżenia o parametrach poza typowym zakresem wzorów "
            "tc, λ ≠ 0,2, duration_min niepodzielne przez krok. Literatura: "
            "USDA-NRCS (1986), TR-55; NEH Part 630 (rozdz. 10, 15, 16); Snyder, "
            "F.F. (1938), Synthetic unit-graphs, Trans. AGU 19, 447–454."
        ),
        description_en=(
            "Design direct-runoff hydrograph of a catchment (HydrographGenerator): "
            "(1) precipitation - a design hyetograph from `hietogram_type`, "
            "`total_mm`, `duration_min` (types and parameters as in `precip "
            "hietogram`) or a series of precipitation depths per step (`values` "
            "or `input_file` + `value_column`), always with the step "
            "`timestep_min`; (2) effective precipitation by SCS-CN from `cn` (AMC "
            "II), the adjustment `amc` and `ia_coefficient` (see `scs "
            "effective`); (3) the unit hydrograph of the `uh_model` - scs (needs "
            "tc), nash (`nash_n`, `nash_k_min`), clark (tc and `clark_r_min` or "
            "`clark_r_tc_ratio`), snyder (`snyder_length_km`, "
            "`snyder_centroid_length_km`, optionally `snyder_ct`, `snyder_cp`; no "
            "tc) - the models are described by the `uh ...` commands; (4) the "
            "discrete convolution of the effective precipitation with the unit "
            "hydrograph. Catchment: `watershed`/`watershed_file` "
            "(WatershedParameters: area, CN, data for tc) or `area_km2` + `cn`; "
            "a `cn` given next to a watershed overrides its value in the whole "
            "computation, also in the time of concentration by nrcs. Time of "
            "concentration (scs, clark): `tc_min` or, for a watershed, computed "
            "by `tc_method` (default kirpich; watershed fields: see `tc "
            "watershed`). Options outside the chosen variant (hyetograph type, "
            "model) are rejected. The snyder model has its own lag equation - "
            "`tc_min` is not used by it, and its unit hydrograph is computed for "
            "a rainfall duration equal to the step `timestep_min` (Snyder's tLR, "
            "tpR and qpR), because the convolution takes it as the response to "
            "1 mm of effective precipitation in one step. Result: peak Q [m3/s], "
            "time to peak "
            "[min], runoff volume [m3], runoff coefficient, the balance "
            "(precipitation, effective precipitation, S, Ia, CN after the AMC "
            "adjustment), the unit hydrograph parameters and the full series: "
            "time, discharge, precipitation and effective precipitation per "
            "step. Notices: warnings about parameters outside the typical range "
            "of the tc formulas, λ != 0.2, a duration not divisible by the step. "
            "Reference: USDA-NRCS (1986), TR-55; NEH Part 630 (chapters 10, 15, "
            "16); Snyder, F.F. (1938), Synthetic unit-graphs, Trans. AGU 19, "
            "447-454."
        ),
        function="hydrolog.operations:hydrograph_generate",
        options=GENERATE_OPTIONS,
        one_of=GENERATE_ONE_OF,
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
