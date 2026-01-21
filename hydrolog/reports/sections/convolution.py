"""Convolution (discrete convolution) report section.

Generates the section documenting the convolution process
that transforms effective precipitation into runoff hydrograph.
"""

from hydrolog.reports.formatters import FormulaRenderer
from hydrolog.reports.templates import (
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
)


def generate_convolution_section(
    n_precip_steps: int,
    n_uh_steps: int,
    n_result_steps: int,
    timestep_min: float,
    include_formulas: bool = True,
) -> str:
    """
    Generate convolution section.

    Parameters
    ----------
    n_precip_steps : int
        Number of effective precipitation time steps.
    n_uh_steps : int
        Number of unit hydrograph ordinates.
    n_result_steps : int
        Number of resulting hydrograph time steps.
    timestep_min : float
        Time step [min].
    include_formulas : bool, optional
        Include detailed formulas, by default True.

    Returns
    -------
    str
        Markdown content for the section.
    """
    lines = [
        SECTION_HEADERS["convolution"],
        SECTION_INTROS["convolution"],
        "",
    ]

    if include_formulas:
        lines.extend([
            SUBSECTION_HEADERS["convolution"]["formula"],
            "",
            FormulaRenderer.convolution_formula(),
            "",
        ])

    lines.extend([
        SUBSECTION_HEADERS["convolution"]["description"],
        "",
        "Procedura splotu dyskretnego:",
        "",
        "1. Opad efektywny Pe(t) dzielony jest na przyrosty w kolejnych krokach czasowych",
        "2. Każdy przyrost opadu generuje odpływ proporcjonalny do hydrogramu jednostkowego",
        "3. Odpływy cząstkowe są sumowane (superpozycja) dając wynikowy hydrogram",
        "",
        "**Parametry procedury:**",
        "",
        f"| Parametr | Wartość |",
        f"|:---------|--------:|",
        f"| Liczba kroków opadu efektywnego (M) | {n_precip_steps} |",
        f"| Liczba ordinat hydrogramu jednostkowego (N) | {n_uh_steps} |",
        f"| Liczba kroków wynikowego hydrogramu | {n_result_steps} |",
        f"| Krok czasowy Δt | {timestep_min:.1f} min |",
        f"| Całkowity czas trwania hydrogramu | {n_result_steps * timestep_min:.1f} min |",
        "",
        "**Uwaga:** Długość wynikowego hydrogramu = M + N - 1 kroków czasowych.",
    ])

    return "\n".join(lines)
