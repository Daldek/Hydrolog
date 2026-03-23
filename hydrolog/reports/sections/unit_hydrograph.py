"""Unit hydrograph report section.

Generates the section documenting unit hydrograph model calculations
for SCS, Nash, Clark, and Snyder models.
"""

from typing import Any, Dict, Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.reports.formatters import FormulaRenderer, TableGenerator
from hydrolog.reports.templates import (
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
    UH_MODELS,
)


def generate_uh_section(
    model: str,
    area_km2: float,
    times_min: NDArray[np.float64],
    ordinates_m3s: NDArray[np.float64],
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Optional[Dict[str, Any]] = None,
    tc_min: Optional[float] = None,
    duration_min: Optional[float] = None,
    include_formulas: bool = True,
    include_table: bool = True,
    max_table_rows: int = 30,
) -> str:
    """
    Generate unit hydrograph section.

    Parameters
    ----------
    model : str
        Unit hydrograph model ("scs", "nash", "clark", "snyder").
    area_km2 : float
        Watershed area [km²].
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        UH ordinates [m³/s/mm].
    time_to_peak_min : float
        Time to peak [min].
    peak_discharge_m3s : float
        Peak discharge [m³/s/mm].
    model_params : dict, optional
        Model-specific parameters.
    tc_min : float, optional
        Time of concentration [min].
    duration_min : float, optional
        Rainfall duration [min].
    include_formulas : bool, optional
        Include detailed formulas, by default True.
    include_table : bool, optional
        Include ordinates table, by default True.
    max_table_rows : int, optional
        Maximum rows in table, by default 30.

    Returns
    -------
    str
        Markdown content for the section.
    """
    model = model.lower()
    model_params = model_params or {}

    lines = [
        SECTION_HEADERS["unit_hydrograph"],
        SECTION_INTROS["unit_hydrograph"],
        "",
        SUBSECTION_HEADERS["unit_hydrograph"]["model"],
        "",
        f"**{UH_MODELS.get(model, model)}**",
        "",
    ]

    # Model-specific content
    if model == "scs":
        lines.extend(
            _generate_scs_section(
                area_km2=area_km2,
                tc_min=tc_min,
                duration_min=duration_min,
                time_to_peak_min=time_to_peak_min,
                peak_discharge_m3s=peak_discharge_m3s,
                model_params=model_params,
                include_formulas=include_formulas,
            )
        )
    elif model == "nash":
        lines.extend(
            _generate_nash_section(
                area_km2=area_km2,
                time_to_peak_min=time_to_peak_min,
                peak_discharge_m3s=peak_discharge_m3s,
                model_params=model_params,
                include_formulas=include_formulas,
            )
        )
    elif model == "clark":
        lines.extend(
            _generate_clark_section(
                area_km2=area_km2,
                tc_min=tc_min,
                time_to_peak_min=time_to_peak_min,
                peak_discharge_m3s=peak_discharge_m3s,
                model_params=model_params,
                include_formulas=include_formulas,
            )
        )
    elif model == "snyder":
        lines.extend(
            _generate_snyder_section(
                area_km2=area_km2,
                time_to_peak_min=time_to_peak_min,
                peak_discharge_m3s=peak_discharge_m3s,
                model_params=model_params,
                include_formulas=include_formulas,
            )
        )

    # Ordinates table
    if include_table:
        lines.extend(
            [
                "",
                SUBSECTION_HEADERS["unit_hydrograph"]["ordinates"],
                "",
                TableGenerator.uh_ordinates_table(
                    times=times_min,
                    ordinates=ordinates_m3s,
                    max_rows=max_table_rows,
                ),
                "",
            ]
        )

    # Summary
    lines.extend(
        [
            "**Charakterystyki hydrogramu jednostkowego:**",
            "",
            f"| Parametr | Wartość |",
            f"|:---------|--------:|",
            f"| Czas do szczytu tp | {time_to_peak_min:.1f} min |",
            f"| Przepływ szczytowy qp | {peak_discharge_m3s:.4f} m³/s/mm |",
            f"| Powierzchnia zlewni A | {area_km2:.2f} km² |",
        ]
    )

    return "\n".join(lines)


def _generate_scs_section(
    area_km2: float,
    tc_min: Optional[float],
    duration_min: Optional[float],
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate SCS-specific content."""
    lines = []

    # Extract parameters
    tlag_min = model_params.get(
        "lag_time_min", time_to_peak_min * 0.6 if tc_min else None
    )
    tb_min = model_params.get("time_base_min")

    lines.extend(
        [
            SUBSECTION_HEADERS["unit_hydrograph"]["params"],
            "",
            f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
        ]
    )

    if tc_min:
        lines.append(f"- Czas koncentracji: tc = {tc_min:.1f} min")
    if duration_min:
        lines.append(f"- Czas trwania opadu: D = {duration_min:.1f} min")

    if include_formulas and tc_min and tlag_min:
        lines.extend(
            [
                "",
                SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
                "",
                "**Czas opóźnienia (lag time):**",
                "",
                FormulaRenderer.scs_uh_lag_time(tc_min, tlag_min),
                "",
                "**Czas do szczytu:**",
                "",
            ]
        )

        if duration_min:
            lines.append(
                FormulaRenderer.scs_uh_time_to_peak(
                    duration_min, tlag_min, time_to_peak_min
                )
            )
        else:
            lines.append(f"$$t_p = {time_to_peak_min:.1f} \\text{{ min}}$$")

        lines.extend(
            [
                "",
                "**Przepływ szczytowy jednostkowy:**",
                "",
                FormulaRenderer.scs_uh_peak_discharge(
                    area_km2, time_to_peak_min, peak_discharge_m3s
                ),
            ]
        )

        if tb_min:
            lines.extend(
                [
                    "",
                    "**Czas bazowy:**",
                    "",
                    f"$$t_b = 5 \\cdot t_p = 5 \\cdot {time_to_peak_min:.1f} = "
                    f"{tb_min:.1f} \\text{{ min}}$$",
                ]
            )

    return lines


def _generate_nash_section(
    area_km2: float,
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate Nash IUH-specific content.

    Supports three estimation methods via model_params["estimation_method"]:
    - "from_tc": parameters from time of concentration
    - "from_lutz": Lutz method for ungauged catchments
    - "from_urban_regression": urban regression (Rao, Delleur, Sarma 1972)
    - None / "direct": parameters given directly
    """
    lines = []

    n = model_params.get("n", 3.0)
    k_min = model_params.get("k_min", 30.0)
    k_h = k_min / 60
    estimation_method = model_params.get("estimation_method")

    # Check if Lutz calculation results are available
    lutz_params = model_params.get("lutz_params")

    if lutz_params:
        # Full Lutz method documentation
        lines.append(
            "Parametry modelu (n, K) wyznaczono **metodą Lutza (1984)** "
            "na podstawie charakterystyk fizjograficznych zlewni."
        )
        lines.append("")
        lines.append("### 5.2 Obliczenie parametrów metodą Lutza")
        lines.append("")
        lines.append("**Dane wejściowe:**")
        lines.append(f"- L = {lutz_params.L_km:.2f} km (długość cieku)")
        lines.append(
            f"- Lc = {lutz_params.Lc_km:.2f} km (odległość do środka ciężkości)"
        )
        lines.append(f"- Jg = {lutz_params.slope:.4f} (spadek cieku)")
        lines.append(f"- n_M = {lutz_params.manning_n:.3f} (współczynnik Manninga)")
        lines.append(f"- U = {lutz_params.urban_pct:.1f}% (powierzchnia uszczelniona)")
        lines.append(f"- W = {lutz_params.forest_pct:.1f}% (lesistość)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Krok 1: Współczynnik P₁**")
        lines.append("")
        lines.append(
            f"$$P_1 = 3.989 \\cdot n_M + 0.028 = "
            f"3.989 \\cdot {lutz_params.manning_n:.3f} + 0.028 = {lutz_params.P1:.4f}$$"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Krok 2: Czas do szczytu IUH (tp)**")
        lines.append("")
        lines.append(
            "$$t_p = P_1 \\cdot \\left(\\frac{L \\cdot L_c}{J_g^{1.5}}\\right)^{0.26} "
            "\\cdot e^{-0.016 \\cdot U} \\cdot e^{0.004 \\cdot W}$$"
        )
        lines.append("")
        lines.append(
            f"$$t_p = {lutz_params.P1:.4f} \\cdot "
            f"\\left(\\frac{{{lutz_params.L_km:.2f} \\cdot {lutz_params.Lc_km:.2f}}}"
            f"{{{lutz_params.slope:.4f}^{{1.5}}}}\\right)^{{0.26}} \\cdot "
            f"e^{{-0.016 \\cdot {lutz_params.urban_pct:.1f}}} \\cdot "
            f"e^{{0.004 \\cdot {lutz_params.forest_pct:.1f}}} = "
            f"{lutz_params.tp_hours:.3f} \\text{{ h}} = {lutz_params.tp_min:.1f} \\text{{ min}}$$"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Krok 3: Rzędna szczytowa IUH (up)**")
        lines.append("")
        lines.append(
            f"$$u_p = \\frac{{0.66}}{{t_p^{{1.04}}}} = "
            f"\\frac{{0.66}}{{{lutz_params.tp_hours:.3f}^{{1.04}}}} = "
            f"{lutz_params.up_per_hour:.3f} \\text{{ [1/h]}}$$"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Krok 4: Funkcja f(N)**")
        lines.append("")
        lines.append(
            f"$$f(N)_{{target}} = t_p \\cdot u_p = "
            f"{lutz_params.tp_hours:.3f} \\cdot {lutz_params.up_per_hour:.3f} = "
            f"{lutz_params.f_N_target:.3f}$$"
        )
        lines.append("")
        lines.append("Szukamy N spełniającego równanie:")
        lines.append("")
        lines.append(
            f"$$f(N) = \\frac{{(N-1)^N \\cdot e^{{-(N-1)}}}}{{\\Gamma(N)}} = "
            f"{lutz_params.f_N_target:.3f}$$"
        )
        lines.append("")
        lines.append(
            f"Rozwiązanie numeryczne (metoda Brenta): **N = {lutz_params.n:.3f}**"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Krok 5: Stała magazynowania K**")
        lines.append("")
        lines.append(
            f"$$K = \\frac{{t_p}}{{N - 1}} = "
            f"\\frac{{{lutz_params.tp_hours:.3f}}}{{{lutz_params.n:.3f} - 1}} = "
            f"\\frac{{{lutz_params.tp_hours:.3f}}}{{{lutz_params.n - 1:.3f}}} = "
            f"{lutz_params.k_hours:.3f} \\text{{ h}} = {lutz_params.k_min:.2f} \\text{{ min}}$$"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### 5.3 Podsumowanie parametrów Nasha")
        lines.append("")
        lines.append("| Parametr | Symbol | Wartość | Jednostka |")
        lines.append("|:---------|:------:|--------:|:---------:|")
        lines.append(f"| Liczba zbiorników | n | {n:.3f} | - |")
        lines.append(f"| Stała magazynowania | K | {k_min:.2f} | min |")
        lines.append(f"| Czas do szczytu IUH | tp | {(n-1)*k_min:.1f} | min |")
        lines.append(f"| Czas opóźnienia (lag) | tlag = n×K | {n*k_min:.1f} | min |")
        lines.append("")
        lines.append("**Referencje:**")
        lines.append(
            "- Lutz W. (1984): *Berechnung von Hochwasserabflüssen unter Anwendung von "
            "Gebietskenngrößen*. Universität Karlsruhe."
        )
        lines.append(
            "- KZGW (2017): *Aktualizacja metodyki obliczania przepływów "
            "i opadów maksymalnych*. Tabela C.2."
        )
        lines.append("")
        lines.append("### 5.4 Wzór IUH Nasha")
    else:
        # Standard Nash section without Lutz details
        lines.extend(
            [
                SUBSECTION_HEADERS["unit_hydrograph"]["params"],
                "",
                f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
                f"- Liczba zbiorników: n = {n:.2f}",
                f"- Stała zbiornika: K = {k_min:.1f} min = {k_h:.3f} h",
                f"- Czas opóźnienia: tlag = n × K = {n * k_min:.1f} min",
            ]
        )

    # Show estimation-specific input parameters
    if estimation_method == "from_lutz":
        lutz_inputs = [
            ("L_km", "Długość cieku L", "km", ".3f"),
            ("Lc_km", "Odległość do centroidu Lc", "km", ".3f"),
            ("slope", "Spadek cieku Jg", "", ".4f"),
            ("manning_n", "Współczynnik Manninga n", "", ".3f"),
        ]
        lines.append("")
        lines.append("**Dane wejściowe metody Lutza:**")
        lines.append("")
        for key, label, unit, fmt in lutz_inputs:
            val = model_params.get(key)
            if val is not None:
                suffix = f" {unit}" if unit else ""
                lines.append(f"- {label} = {val:{fmt}}{suffix}")
        urban_pct = model_params.get("urban_pct", 0.0)
        forest_pct = model_params.get("forest_pct", 0.0)
        lines.append(f"- Tereny zurbanizowane U = {urban_pct:.1f}%")
        lines.append(f"- Tereny leśne W = {forest_pct:.1f}%")

    if include_formulas:
        lines.extend(
            [
                "",
                "**Chwilowy hydrogram jednostkowy (IUH):**",
                "",
            ]
        )

        # Estimation method formulas (rendered BEFORE model formula)
        if estimation_method == "from_tc":
            tc_min = model_params.get("tc_min")
            lag_ratio = model_params.get("lag_ratio", 0.6)
            if tc_min is not None:
                lines.extend(
                    [
                        FormulaRenderer.nash_from_tc_formulas(
                            tc_min=tc_min,
                            n=n,
                            lag_ratio=lag_ratio,
                            k_min=k_min,
                        ),
                        "",
                    ]
                )

        elif estimation_method == "from_lutz":
            P1 = model_params.get("P1")
            tp_hours = model_params.get("tp_hours")
            up_per_hour = model_params.get("up_per_hour")
            f_N = model_params.get("f_N")
            L_km = model_params.get("L_km")
            Lc_km = model_params.get("Lc_km")
            slope = model_params.get("slope")
            manning_n = model_params.get("manning_n")
            if all(
                v is not None
                for v in (P1, tp_hours, up_per_hour, f_N, L_km, Lc_km, slope, manning_n)
            ):
                assert P1 is not None
                assert tp_hours is not None
                assert up_per_hour is not None
                assert f_N is not None
                assert L_km is not None
                assert Lc_km is not None
                assert slope is not None
                assert manning_n is not None
                lines.extend(
                    [
                        FormulaRenderer.nash_from_lutz_formulas(
                            L_km=L_km,
                            Lc_km=Lc_km,
                            slope=slope,
                            manning_n=manning_n,
                            urban_pct=model_params.get("urban_pct", 0.0),
                            forest_pct=model_params.get("forest_pct", 0.0),
                            P1=P1,
                            tp_hours=tp_hours,
                            up_per_hour=up_per_hour,
                            f_N=f_N,
                            n=n,
                            k_min=k_min,
                        ),
                        "",
                    ]
                )

        elif estimation_method == "from_urban_regression":
            ur_area = model_params.get("area_km2", area_km2)
            ur_urban = model_params.get("urban_fraction", 0.0)
            ur_precip = model_params.get("effective_precip_mm")
            ur_duration = model_params.get("duration_h")
            ur_tL = model_params.get("tL_h")
            ur_k = model_params.get("k_h", k_h)
            if ur_precip is not None and ur_duration is not None and ur_tL is not None:
                lines.extend(
                    [
                        FormulaRenderer.nash_urban_regression_formulas(
                            area_km2=ur_area,
                            urban_fraction=ur_urban,
                            effective_precip_mm=ur_precip,
                            duration_h=ur_duration,
                            tL_h=ur_tL,
                            k_h=ur_k,
                            N=n,
                        ),
                        "",
                    ]
                )

        # Model formula (always shown)
        if estimation_method:
            lines.extend(
                [
                    "**Wzór IUH Nasha (wyznaczone parametry):**",
                    "",
                ]
            )
        lines.append(FormulaRenderer.nash_iuh_formula(n, k_min))

        if n > 1:
            tp_theoretical = (n - 1) * k_min
            lines.extend(
                [
                    "",
                    "**Czas do szczytu IUH:**",
                    "",
                    f"$$t_p = (n - 1) \\cdot K = ({n:.2f} - 1) \\cdot {k_min:.1f} = "
                    f"{tp_theoretical:.1f} \\text{{ min}}$$",
                ]
            )

    return lines


def _generate_clark_section(
    area_km2: float,
    tc_min: Optional[float],
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate Clark IUH-specific content."""
    lines = []

    r_min = model_params.get("r_min", 30.0)
    tc = tc_min or model_params.get("tc_min", 60.0)
    estimation_method = model_params.get("estimation_method", "direct")
    r_tc_ratio = model_params.get("r_ratio")
    timestep_min = model_params.get("timestep_min")

    # Compute C1 routing coefficient when timestep is available
    c1: Optional[float] = None
    if timestep_min is not None and timestep_min > 0:
        c1 = timestep_min / (2.0 * r_min + timestep_min)

    lag_time_min = tc / 2.0 + r_min

    lines.extend(
        [
            SUBSECTION_HEADERS["unit_hydrograph"]["params"],
            "",
            f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
            f"- Czas koncentracji: Tc = {tc:.1f} min",
            f"- Stała zbiornika: R = {r_min:.1f} min",
        ]
    )

    # Show ratio when derived via from_tc_r_ratio
    if estimation_method == "from_tc_r_ratio" and r_tc_ratio is not None:
        lines.append(f"- Stosunek R/Tc = {r_tc_ratio:.3f} (metoda estymacji R/Tc)")

    lines.extend(
        [
            f"- Tc + R = {tc + r_min:.1f} min",
            f"- Czas opóźnienia (przybliżony): Tc/2 + R = {lag_time_min:.1f} min",
        ]
    )

    if timestep_min is not None:
        lines.append(f"- Krok czasowy obliczeń: Δt = {timestep_min:.1f} min")
    if c1 is not None:
        lines.append(f"- Współczynnik routingu: C1 = {c1:.4f}")

    if include_formulas:
        lines.extend(
            [
                "",
                SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
                "",
                FormulaRenderer.clark_iuh_formula(tc, r_min),
            ]
        )

        # Estimation method formulas
        if estimation_method == "from_tc_r_ratio" and r_tc_ratio is not None:
            lines.extend(
                [
                    "",
                    FormulaRenderer.clark_from_tc_r_ratio(tc, r_tc_ratio, r_min),
                ]
            )

        # Time-area histogram with substituted Tc
        lines.extend(
            [
                "",
                FormulaRenderer.clark_time_area_substituted(tc),
            ]
        )

        # Routing equation - general form first, then with numeric C1
        lines.extend(
            [
                "",
                "**Routing przez zbiornik liniowy (równanie Muskingum):**",
                "",
                "$$O_t = O_{t-1} + C_1 \\cdot (I_t + I_{t-1} - 2 \\cdot O_{t-1})$$",
                "",
            ]
        )

        if c1 is not None and timestep_min is not None:
            lines.append(
                FormulaRenderer.clark_routing_coefficient(timestep_min, r_min, c1)
            )
        else:
            lines.append(
                f"$$C_1 = \\frac{{\\Delta t}}{{2R + \\Delta t}} = "
                f"\\frac{{\\Delta t}}{{2 \\cdot {r_min:.1f} + \\Delta t}}$$"
            )

        # Lag time approximation
        lines.extend(
            [
                "",
                "**Przybliżony czas opóźnienia:**",
                "",
                f"$$t_{{lag}} \\approx \\frac{{T_c}}{{2}} + R = "
                f"\\frac{{{tc:.1f}}}{{2}} + {r_min:.1f} = {lag_time_min:.1f} \\text{{ min}}$$",
            ]
        )

    return lines


def _generate_snyder_section(
    area_km2: float,
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate Snyder UH-specific content.

    Reads the following keys from model_params (all optional with defaults):
    - L_km              : main stream length [km]
    - Lc_km             : length to centroid [km]
    - ct                : time coefficient Ct
    - cp                : peak coefficient Cp
    - lag_time_min      : basin lag time tL [min]
    - standard_duration_min : standard duration tD [min]  (computed if absent)
    - time_base_min     : time base tb [min]              (computed if absent)
    - duration_min      : actual rainfall duration used [min]
    - adjusted_lag_time_min : adjusted lag tLR [min]      (non-standard case)
    - adjusted_tp_min   : adjusted time to peak tpR [min] (non-standard case)
    - adjusted_qp_m3s   : adjusted peak discharge qpR [m³/s/mm] (non-standard)
    """
    lines = []

    L_km: float = model_params.get("L_km", 10.0)
    Lc_km: float = model_params.get("Lc_km", 5.0)
    ct: float = model_params.get("ct", 1.5)
    cp: float = model_params.get("cp", 0.6)
    tL_min: float = model_params.get("lag_time_min", 60.0)

    # Standard duration tD = tL / 5.5
    tD_min: float = model_params.get("standard_duration_min", tL_min / 5.5)

    # Time base tb = 0.556 * A / qp  (hours -> minutes)
    tb_min: float = model_params.get(
        "time_base_min",
        (0.556 * area_km2 / peak_discharge_m3s) * 60.0,
    )

    # Hydrograph widths at 50 % and 75 % of peak (metric constants)
    # W50 = 0.1783 / (qp/A)^1.08  [h],  W75 = 0.1019 / (qp/A)^1.08  [h]
    # where qp/A is in m³/s/km²/mm; constants derived from imperial W50=770,
    # W75=440 (cfs/mi²/inch) via conv = 25.4 / (0.028317 * 2.58999).
    qp_per_area = peak_discharge_m3s / area_km2
    w50_h: float = model_params.get("w50_h", 0.1783 / (qp_per_area**1.08))
    w75_h: float = model_params.get("w75_h", 0.1019 / (qp_per_area**1.08))

    # Non-standard duration parameters (present only when Δt ≠ tD)
    duration_min: Optional[float] = model_params.get("duration_min")
    tLR_min: Optional[float] = model_params.get("adjusted_lag_time_min")
    tpR_min: Optional[float] = model_params.get("adjusted_tp_min")
    qpR_m3s: Optional[float] = model_params.get("adjusted_qp_m3s")

    lines.extend(
        [
            SUBSECTION_HEADERS["unit_hydrograph"]["params"],
            "",
            f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
            f"- Długość cieku: L = {L_km:.2f} km",
            f"- Odległość do centroidu: Lc = {Lc_km:.2f} km",
            f"- Współczynnik czasowy: Ct = {ct:.2f}",
            f"- Współczynnik szczytowy: Cp = {cp:.2f}",
            f"- Czas opóźnienia zlewni: tL = {tL_min:.1f} min",
            f"- Standardowy czas trwania: tD = {tD_min:.1f} min",
        ]
    )

    if duration_min is not None:
        lines.append(f"- Użyty czas trwania opadu: Δt = {duration_min:.1f} min")

    lines.extend(
        [
            f"- Czas do szczytu: tp = {time_to_peak_min:.1f} min",
            f"- Przepływ szczytowy (standardowy): qp = {peak_discharge_m3s:.4f} m³/s/mm",
            f"- Czas bazowy: tb = {tb_min:.1f} min",
            f"- Szerokość W50 = {w50_h:.3f} h, W75 = {w75_h:.3f} h",
        ]
    )

    if include_formulas:
        lines.extend(
            [
                "",
                SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
                "",
                FormulaRenderer.snyder_uh_formulas(
                    L_km=L_km,
                    Lc_km=Lc_km,
                    ct=ct,
                    cp=cp,
                    tL_min=tL_min,
                    tD_min=tD_min,
                    tp_min=time_to_peak_min,
                    qp_m3s=peak_discharge_m3s,
                    area_km2=area_km2,
                    tb_min=tb_min,
                    w50_h=w50_h,
                    w75_h=w75_h,
                    duration_min=duration_min,
                    tLR_min=tLR_min,
                    tpR_min=tpR_min,
                    qpR_m3s=qpR_m3s,
                ),
            ]
        )

    return lines
