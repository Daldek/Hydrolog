"""Hietogram report section.

Generates the section documenting precipitation temporal distribution.
"""

from typing import Optional

import numpy as np
from numpy.typing import NDArray

from hydrolog.reports.formatters import TableGenerator
from hydrolog.reports.templates import (
    HIETOGRAM_TYPES,
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
)


def generate_hietogram_section(
    total_mm: float,
    duration_min: float,
    timestep_min: float,
    times_min: NDArray[np.float64],
    intensities_mm: NDArray[np.float64],
    distribution: str = "beta",
    distribution_params: Optional[str] = None,
    include_table: bool = True,
    max_table_rows: int = 30,
) -> str:
    """
    Generate hietogram section.

    Parameters
    ----------
    total_mm : float
        Total precipitation [mm].
    duration_min : float
        Total duration [min].
    timestep_min : float
        Time step [min].
    times_min : NDArray[np.float64]
        Time values at end of each interval [min].
    intensities_mm : NDArray[np.float64]
        Precipitation depth in each interval [mm].
    distribution : str, optional
        Distribution type ("beta", "block", "triangular", "euler_ii").
    distribution_params : str, optional
        Distribution parameters description (e.g., "α=2, β=5").
    include_table : bool, optional
        Include distribution table, by default True.
    max_table_rows : int, optional
        Maximum rows in table, by default 30.

    Returns
    -------
    str
        Markdown content for the section.
    """
    distribution = distribution.lower()

    lines = [
        SECTION_HEADERS["hietogram"],
        SECTION_INTROS["hietogram"],
        "",
        SUBSECTION_HEADERS["hietogram"]["params"],
        "",
    ]

    # Parameters table
    avg_intensity_mm_h = (total_mm / duration_min) * 60
    peak_intensity_mm = float(np.max(intensities_mm))
    peak_intensity_mm_h = (peak_intensity_mm / timestep_min) * 60
    peak_time_idx = int(np.argmax(intensities_mm))
    peak_time_min = times_min[peak_time_idx]

    params_data = [
        ("Opad całkowity P", f"{total_mm:.2f}", "mm"),
        ("Czas trwania", f"{duration_min:.1f}", "min"),
        ("Krok czasowy", f"{timestep_min:.1f}", "min"),
        ("Liczba kroków", str(len(times_min)), "-"),
        ("Średnia intensywność", f"{avg_intensity_mm_h:.2f}", "mm/h"),
        ("Intensywność szczytowa", f"{peak_intensity_mm_h:.2f}", "mm/h"),
        ("Czas szczytu", f"{peak_time_min:.1f}", "min"),
    ]

    lines.append(TableGenerator.parameters_table(params_data))

    # Distribution type
    dist_name = HIETOGRAM_TYPES.get(distribution, distribution)
    if distribution_params:
        dist_name = f"{dist_name} ({distribution_params})"

    lines.extend([
        "",
        f"**Typ rozkładu:** {dist_name}",
    ])

    # Distribution table
    if include_table:
        lines.extend([
            "",
            SUBSECTION_HEADERS["hietogram"]["distribution"],
            "",
        ])

        # Calculate cumulative
        cumsum = np.cumsum(intensities_mm)

        n = len(times_min)
        if n <= max_table_rows:
            # Full table
            table_lines = [
                "| Czas [min] | P [mm] | P kum. [mm] | Intensywność [mm/h] |",
                "|--------:|------:|------:|------:|",
            ]
            for i in range(n):
                t = times_min[i]
                p = intensities_mm[i]
                pc = cumsum[i]
                intensity_h = (p / timestep_min) * 60
                table_lines.append(f"| {t:.1f} | {p:.2f} | {pc:.2f} | {intensity_h:.2f} |")

            lines.append("\n".join(table_lines))
        else:
            # Abbreviated table
            head_count = max_table_rows // 2
            tail_count = max_table_rows - head_count - 1

            table_lines = [
                "| Czas [min] | P [mm] | P kum. [mm] | Intensywność [mm/h] |",
                "|--------:|------:|------:|------:|",
            ]

            for i in range(head_count):
                t = times_min[i]
                p = intensities_mm[i]
                pc = cumsum[i]
                intensity_h = (p / timestep_min) * 60
                table_lines.append(f"| {t:.1f} | {p:.2f} | {pc:.2f} | {intensity_h:.2f} |")

            table_lines.append("| ... | ... | ... | ... |")

            for i in range(n - tail_count, n):
                t = times_min[i]
                p = intensities_mm[i]
                pc = cumsum[i]
                intensity_h = (p / timestep_min) * 60
                table_lines.append(f"| {t:.1f} | {p:.2f} | {pc:.2f} | {intensity_h:.2f} |")

            table_lines.append(f"\n*Tabela skrócona ({n} wierszy)*")
            lines.append("\n".join(table_lines))

    return "\n".join(lines)
