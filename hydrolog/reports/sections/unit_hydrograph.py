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
        lines.extend(_generate_scs_section(
            area_km2=area_km2,
            tc_min=tc_min,
            duration_min=duration_min,
            time_to_peak_min=time_to_peak_min,
            peak_discharge_m3s=peak_discharge_m3s,
            model_params=model_params,
            include_formulas=include_formulas,
        ))
    elif model == "nash":
        lines.extend(_generate_nash_section(
            area_km2=area_km2,
            time_to_peak_min=time_to_peak_min,
            peak_discharge_m3s=peak_discharge_m3s,
            model_params=model_params,
            include_formulas=include_formulas,
        ))
    elif model == "clark":
        lines.extend(_generate_clark_section(
            area_km2=area_km2,
            tc_min=tc_min,
            time_to_peak_min=time_to_peak_min,
            peak_discharge_m3s=peak_discharge_m3s,
            model_params=model_params,
            include_formulas=include_formulas,
        ))
    elif model == "snyder":
        lines.extend(_generate_snyder_section(
            area_km2=area_km2,
            time_to_peak_min=time_to_peak_min,
            peak_discharge_m3s=peak_discharge_m3s,
            model_params=model_params,
            include_formulas=include_formulas,
        ))

    # Ordinates table
    if include_table:
        lines.extend([
            "",
            SUBSECTION_HEADERS["unit_hydrograph"]["ordinates"],
            "",
            TableGenerator.uh_ordinates_table(
                times=times_min,
                ordinates=ordinates_m3s,
                max_rows=max_table_rows,
            ),
            "",
        ])

    # Summary
    lines.extend([
        "**Charakterystyki hydrogramu jednostkowego:**",
        "",
        f"| Parametr | Wartość |",
        f"|:---------|--------:|",
        f"| Czas do szczytu tp | {time_to_peak_min:.1f} min |",
        f"| Przepływ szczytowy qp | {peak_discharge_m3s:.4f} m³/s/mm |",
        f"| Powierzchnia zlewni A | {area_km2:.2f} km² |",
    ])

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
    tlag_min = model_params.get("lag_time_min", time_to_peak_min * 0.6 if tc_min else None)
    tb_min = model_params.get("time_base_min")

    lines.extend([
        SUBSECTION_HEADERS["unit_hydrograph"]["params"],
        "",
        f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
    ])

    if tc_min:
        lines.append(f"- Czas koncentracji: tc = {tc_min:.1f} min")
    if duration_min:
        lines.append(f"- Czas trwania opadu: D = {duration_min:.1f} min")

    if include_formulas and tc_min and tlag_min:
        lines.extend([
            "",
            SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
            "",
            "**Czas opóźnienia (lag time):**",
            "",
            FormulaRenderer.scs_uh_lag_time(tc_min, tlag_min),
            "",
            "**Czas do szczytu:**",
            "",
        ])

        if duration_min:
            lines.append(FormulaRenderer.scs_uh_time_to_peak(
                duration_min, tlag_min, time_to_peak_min
            ))
        else:
            lines.append(f"$$t_p = {time_to_peak_min:.1f} \\text{{ min}}$$")

        lines.extend([
            "",
            "**Przepływ szczytowy jednostkowy:**",
            "",
            FormulaRenderer.scs_uh_peak_discharge(
                area_km2, time_to_peak_min, peak_discharge_m3s
            ),
        ])

        if tb_min:
            lines.extend([
                "",
                "**Czas bazowy:**",
                "",
                f"$$t_b = 5 \\cdot t_p = 5 \\cdot {time_to_peak_min:.1f} = "
                f"{tb_min:.1f} \\text{{ min}}$$",
            ])

    return lines


def _generate_nash_section(
    area_km2: float,
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate Nash IUH-specific content."""
    lines = []

    n = model_params.get("n", 3.0)
    k_min = model_params.get("k_min", 30.0)
    k_h = k_min / 60

    lines.extend([
        SUBSECTION_HEADERS["unit_hydrograph"]["params"],
        "",
        f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
        f"- Liczba zbiorników: n = {n:.2f}",
        f"- Stała zbiornika: K = {k_min:.1f} min = {k_h:.3f} h",
        f"- Czas opóźnienia: tlag = n × K = {n * k_min:.1f} min",
    ])

    if include_formulas:
        lines.extend([
            "",
            SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
            "",
            FormulaRenderer.nash_iuh_formula(n, k_min),
        ])

        if n > 1:
            tp_theoretical = (n - 1) * k_min
            lines.extend([
                "",
                "**Czas do szczytu IUH:**",
                "",
                f"$$t_p = (n - 1) \\cdot K = ({n:.2f} - 1) \\cdot {k_min:.1f} = "
                f"{tp_theoretical:.1f} \\text{{ min}}$$",
            ])

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

    lines.extend([
        SUBSECTION_HEADERS["unit_hydrograph"]["params"],
        "",
        f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
        f"- Czas koncentracji: Tc = {tc:.1f} min",
        f"- Stała zbiornika: R = {r_min:.1f} min",
        f"- Tc + R = {tc + r_min:.1f} min",
    ])

    if include_formulas:
        lines.extend([
            "",
            SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
            "",
            FormulaRenderer.clark_iuh_formula(tc, r_min),
            "",
            "**Histogram czas-powierzchnia (zlewnia eliptyczna):**",
            "",
            "$$A_{cum}(t) = 1.414 \\cdot \\left(\\frac{t}{T_c}\\right)^{0.5} - "
            "0.414 \\cdot \\left(\\frac{t}{T_c}\\right)^{1.5}$$",
            "",
            "**Routing przez zbiornik liniowy:**",
            "",
            "$$O_t = O_{t-1} + C_1 \\cdot (I_t + I_{t-1} - 2 \\cdot O_{t-1})$$",
            "",
            f"gdzie: $C_1 = \\frac{{\\Delta t}}{{2R + \\Delta t}}$",
        ])

    return lines


def _generate_snyder_section(
    area_km2: float,
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    model_params: Dict[str, Any],
    include_formulas: bool,
) -> list:
    """Generate Snyder UH-specific content."""
    lines = []

    L_km = model_params.get("L_km", 10.0)
    Lc_km = model_params.get("Lc_km", 5.0)
    ct = model_params.get("ct", 1.5)
    cp = model_params.get("cp", 0.6)
    tL_min = model_params.get("lag_time_min", 60.0)

    lines.extend([
        SUBSECTION_HEADERS["unit_hydrograph"]["params"],
        "",
        f"- Powierzchnia zlewni: A = {area_km2:.2f} km²",
        f"- Długość cieku: L = {L_km:.2f} km",
        f"- Odległość do centroidu: Lc = {Lc_km:.2f} km",
        f"- Współczynnik czasowy: Ct = {ct:.2f}",
        f"- Współczynnik szczytowy: Cp = {cp:.2f}",
    ])

    if include_formulas:
        lines.extend([
            "",
            SUBSECTION_HEADERS["unit_hydrograph"]["formulas"],
            "",
            FormulaRenderer.snyder_uh_formulas(
                L_km=L_km,
                Lc_km=Lc_km,
                ct=ct,
                cp=cp,
                tL_min=tL_min,
                tp_min=time_to_peak_min,
                qp_m3s=peak_discharge_m3s,
                area_km2=area_km2,
            ),
        ])

    return lines
