"""Water balance report section.

Generates the section documenting the water balance summary
including precipitation, abstraction, and runoff components.
"""

from hydrolog.reports.formatters import FormulaRenderer, TableGenerator
from hydrolog.reports.templates import (
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
)


def generate_water_balance_section(
    total_precip_mm: float,
    initial_abstraction_mm: float,
    retention_mm: float,
    total_effective_mm: float,
    runoff_coefficient: float,
    total_volume_m3: float,
    area_km2: float,
    include_formulas: bool = True,
) -> str:
    """
    Generate water balance section.

    Parameters
    ----------
    total_precip_mm : float
        Total precipitation [mm].
    initial_abstraction_mm : float
        Initial abstraction [mm].
    retention_mm : float
        Maximum retention [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    runoff_coefficient : float
        Runoff coefficient C [-].
    total_volume_m3 : float
        Total runoff volume [m³].
    area_km2 : float
        Watershed area [km²].
    include_formulas : bool, optional
        Include formulas, by default True.

    Returns
    -------
    str
        Markdown content for the section.
    """
    lines = [
        SECTION_HEADERS["water_balance"],
        SECTION_INTROS["water_balance"],
        "",
        SUBSECTION_HEADERS["water_balance"]["summary"],
        "",
    ]

    # Water balance table
    lines.append(TableGenerator.water_balance_table(
        total_precip_mm=total_precip_mm,
        initial_abstraction_mm=initial_abstraction_mm,
        retention_mm=retention_mm,
        effective_mm=total_effective_mm,
    ))

    # Runoff coefficient section
    lines.extend([
        "",
        SUBSECTION_HEADERS["water_balance"]["coefficient"],
        "",
    ])

    if include_formulas:
        lines.append(FormulaRenderer.runoff_coefficient(
            pe_mm=total_effective_mm,
            p_mm=total_precip_mm,
            c=runoff_coefficient,
        ))
    else:
        lines.append(f"**Współczynnik odpływu:** C = {runoff_coefficient:.3f}")

    # Volume verification
    expected_volume_m3 = total_effective_mm * area_km2 * 1000  # mm * km² * 1000 = m³

    lines.extend([
        "",
        "**Weryfikacja objętościowa:**",
        "",
        f"- Objętość opadu efektywnego: $V_{{Pe}}$ = Pe × A = "
        f"{total_effective_mm:.2f} mm × {area_km2:.2f} km² = "
        f"{expected_volume_m3:,.0f} m³",
        f"- Objętość z hydrogramu: $V_Q$ = {total_volume_m3:,.0f} m³",
    ])

    # Check balance
    if expected_volume_m3 > 0:
        balance_error = abs(total_volume_m3 - expected_volume_m3) / expected_volume_m3 * 100
        if balance_error < 1:
            lines.append(f"- Bilans: ✓ zgodność ({balance_error:.2f}% różnicy)")
        else:
            lines.append(f"- Bilans: różnica {balance_error:.2f}%")

    # Summary box
    lines.extend([
        "",
        "---",
        "",
        "**Podsumowanie bilansu wodnego:**",
        "",
        f"| | Wartość |",
        f"|:--|--------:|",
        f"| Opad całkowity P | {total_precip_mm:.2f} mm |",
        f"| Opad efektywny Pe | {total_effective_mm:.2f} mm |",
        f"| Straty (Ia + F) | {total_precip_mm - total_effective_mm:.2f} mm |",
        f"| Współczynnik odpływu C | {runoff_coefficient:.3f} ({runoff_coefficient*100:.1f}%) |",
        f"| Objętość odpływu V | {total_volume_m3:,.0f} m³ |",
    ])

    return "\n".join(lines)
