"""SCS-CN effective precipitation report section.

Generates the section documenting SCS Curve Number method calculations
including retention, initial abstraction, and effective precipitation.
"""

from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.reports.formatters import FormulaRenderer, TableGenerator
from hydrolog.reports.templates import (
    AMC_DESCRIPTIONS,
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
)


def generate_scs_cn_section(
    total_precip_mm: float,
    cn_ii: int,
    cn_adjusted: int,
    amc: str,
    retention_mm: float,
    initial_abstraction_mm: float,
    total_effective_mm: float,
    ia_coefficient: float = 0.2,
    times_min: Optional[NDArray[np.float64]] = None,
    precip_mm: Optional[NDArray[np.float64]] = None,
    effective_mm: Optional[NDArray[np.float64]] = None,
    include_formulas: bool = True,
    include_table: bool = True,
    max_table_rows: int = 30,
) -> str:
    """
    Generate SCS-CN effective precipitation section.

    Parameters
    ----------
    total_precip_mm : float
        Total precipitation [mm].
    cn_ii : int
        Curve Number for AMC-II conditions.
    cn_adjusted : int
        Adjusted CN for actual AMC.
    amc : str
        Antecedent Moisture Condition ("I", "II", or "III").
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    ia_coefficient : float, optional
        Initial abstraction coefficient, by default 0.2.
    times_min : NDArray[np.float64], optional
        Time values [min] for distribution table.
    precip_mm : NDArray[np.float64], optional
        Precipitation in each interval [mm].
    effective_mm : NDArray[np.float64], optional
        Effective precipitation in each interval [mm].
    include_formulas : bool, optional
        Include detailed formulas, by default True.
    include_table : bool, optional
        Include distribution table, by default True.
    max_table_rows : int, optional
        Maximum rows in distribution table, by default 30.

    Returns
    -------
    str
        Markdown content for the section.
    """
    lines = [
        SECTION_HEADERS["scs_cn"],
        SECTION_INTROS["scs_cn"],
        "",
        SUBSECTION_HEADERS["scs_cn"]["params"],
        "",
        f"- Curve Number dla AMC-II: **CN = {cn_ii}**",
        f"- Warunki wilgotnościowe: **AMC-{amc}** ({AMC_DESCRIPTIONS.get(amc, '')})",
    ]

    # AMC adjustment if needed
    if amc != "II" and cn_adjusted != cn_ii:
        lines.extend([
            "",
            "**Korekta CN dla warunków wilgotnościowych:**",
            "",
            FormulaRenderer.scs_amc_adjustment(cn_ii, cn_adjusted, amc),
            "",
            f"- CN skorygowany: **CN = {cn_adjusted}**",
        ])
    else:
        lines.append(f"- CN używany w obliczeniach: **CN = {cn_adjusted}**")

    if include_formulas:
        # Retention section
        lines.extend([
            "",
            SUBSECTION_HEADERS["scs_cn"]["retention"],
            "",
            "Retencja maksymalna S określa zdolność retencyjną zlewni:",
            "",
            FormulaRenderer.scs_retention(cn_adjusted),
            "",
        ])

        # Initial abstraction section
        lines.extend([
            SUBSECTION_HEADERS["scs_cn"]["ia"],
            "",
            "Abstrakcja początkowa obejmuje intercepcję, zwilżenie powierzchni "
            "i retencję w zagłębieniach terenu:",
            "",
            FormulaRenderer.scs_initial_abstraction(retention_mm, ia_coefficient),
            "",
        ])

        # Effective precipitation section
        lines.extend([
            SUBSECTION_HEADERS["scs_cn"]["pe"],
            "",
            f"Dla opadu całkowitego P = {total_precip_mm:.2f} mm:",
            "",
            FormulaRenderer.scs_effective_precipitation(
                p_mm=total_precip_mm,
                ia_mm=initial_abstraction_mm,
                s_mm=retention_mm,
                pe_mm=total_effective_mm,
            ),
            "",
        ])

    # Distribution table
    if include_table and times_min is not None and precip_mm is not None:
        lines.extend([
            SUBSECTION_HEADERS["scs_cn"]["distribution"],
            "",
            TableGenerator.precipitation_table(
                times=times_min,
                precip_mm=precip_mm,
                effective_mm=effective_mm,
                max_rows=max_table_rows,
            ),
            "",
        ])

    # Summary
    lines.extend([
        "**Podsumowanie:**",
        "",
        f"| Parametr | Wartość |",
        f"|:---------|--------:|",
        f"| Opad całkowity P | {total_precip_mm:.2f} mm |",
        f"| Retencja maksymalna S | {retention_mm:.2f} mm |",
        f"| Abstrakcja początkowa Ia | {initial_abstraction_mm:.2f} mm |",
        f"| **Opad efektywny Pe** | **{total_effective_mm:.2f} mm** |",
    ])

    return "\n".join(lines)
