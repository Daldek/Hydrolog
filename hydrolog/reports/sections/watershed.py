"""Watershed parameters report section.

Generates the section documenting watershed physical characteristics
including geometry, terrain, and shape indicators.
"""

from typing import Optional

from hydrolog.reports.formatters import TableGenerator
from hydrolog.reports.templates import (
    PARAMETER_LABELS,
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
    UNITS,
)


def generate_watershed_section(
    area_km2: float,
    perimeter_km: Optional[float] = None,
    length_km: Optional[float] = None,
    width_km: Optional[float] = None,
    elevation_min_m: Optional[float] = None,
    elevation_max_m: Optional[float] = None,
    elevation_mean_m: Optional[float] = None,
    relief_m: Optional[float] = None,
    mean_slope_percent: Optional[float] = None,
    channel_length_km: Optional[float] = None,
    channel_slope_m_per_m: Optional[float] = None,
    cn: Optional[int] = None,
    name: Optional[str] = None,
    form_factor: Optional[float] = None,
    compactness: Optional[float] = None,
    circularity: Optional[float] = None,
    elongation: Optional[float] = None,
    include_shape_indicators: bool = True,
) -> str:
    """
    Generate watershed parameters section.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    perimeter_km : float, optional
        Watershed perimeter [km].
    length_km : float, optional
        Watershed length [km].
    width_km : float, optional
        Watershed width [km].
    elevation_min_m : float, optional
        Minimum elevation [m a.s.l.].
    elevation_max_m : float, optional
        Maximum elevation [m a.s.l.].
    elevation_mean_m : float, optional
        Mean elevation [m a.s.l.].
    relief_m : float, optional
        Relief (elevation range) [m].
    mean_slope_percent : float, optional
        Mean watershed slope [%].
    channel_length_km : float, optional
        Main channel length [km].
    channel_slope_m_per_m : float, optional
        Main channel slope [m/m].
    cn : int, optional
        Curve Number.
    name : str, optional
        Watershed name.
    form_factor : float, optional
        Horton's form factor.
    compactness : float, optional
        Gravelius compactness coefficient.
    circularity : float, optional
        Miller's circularity ratio.
    elongation : float, optional
        Schumm's elongation ratio.
    include_shape_indicators : bool, optional
        Include shape indicators section, by default True.

    Returns
    -------
    str
        Markdown content for the section.
    """
    lines = [
        SECTION_HEADERS["watershed"],
        SECTION_INTROS["watershed"],
        "",
        SUBSECTION_HEADERS["watershed"]["input"],
        "",
    ]

    # Build parameters table
    params_data = []

    # Required parameter
    params_data.append((
        PARAMETER_LABELS["area_km2"],
        f"{area_km2:.2f}",
        UNITS["area_km2"],
    ))

    # Optional geometry parameters
    if perimeter_km is not None:
        params_data.append((
            PARAMETER_LABELS["perimeter_km"],
            f"{perimeter_km:.2f}",
            UNITS["perimeter_km"],
        ))

    if length_km is not None:
        params_data.append((
            PARAMETER_LABELS["length_km"],
            f"{length_km:.2f}",
            UNITS["length_km"],
        ))

    if width_km is not None:
        params_data.append((
            PARAMETER_LABELS["width_km"],
            f"{width_km:.2f}",
            UNITS["width_km"],
        ))

    # Elevation parameters
    if elevation_min_m is not None:
        params_data.append((
            PARAMETER_LABELS["elevation_min_m"],
            f"{elevation_min_m:.1f}",
            UNITS["elevation_m"],
        ))

    if elevation_max_m is not None:
        params_data.append((
            PARAMETER_LABELS["elevation_max_m"],
            f"{elevation_max_m:.1f}",
            UNITS["elevation_m"],
        ))

    if elevation_mean_m is not None:
        params_data.append((
            PARAMETER_LABELS["elevation_mean_m"],
            f"{elevation_mean_m:.1f}",
            UNITS["elevation_m"],
        ))

    if relief_m is not None:
        params_data.append((
            PARAMETER_LABELS["relief_m"],
            f"{relief_m:.1f}",
            UNITS["relief_m"],
        ))

    if mean_slope_percent is not None:
        params_data.append((
            PARAMETER_LABELS["mean_slope_percent"],
            f"{mean_slope_percent:.2f}",
            UNITS["slope_percent"],
        ))

    # Channel parameters
    if channel_length_km is not None:
        params_data.append((
            PARAMETER_LABELS["channel_length_km"],
            f"{channel_length_km:.2f}",
            UNITS["length_km"],
        ))

    if channel_slope_m_per_m is not None:
        params_data.append((
            PARAMETER_LABELS["channel_slope_m_per_m"],
            f"{channel_slope_m_per_m:.4f}",
            UNITS["slope_m_per_m"],
        ))

    # Curve Number
    if cn is not None:
        params_data.append((
            PARAMETER_LABELS["cn"],
            str(cn),
            UNITS["cn"],
        ))

    lines.append(TableGenerator.parameters_table(params_data))

    # Shape indicators section
    if include_shape_indicators and any([form_factor, compactness, circularity, elongation]):
        lines.extend([
            "",
            SUBSECTION_HEADERS["watershed"]["shape"],
            "",
            "Wskaźniki kształtu charakteryzują geometrię zlewni i wpływają na "
            "jej odpowiedź hydrologiczną:",
            "",
        ])

        if all([form_factor, compactness, circularity, elongation]):
            lines.append(TableGenerator.shape_indicators_table(
                form_factor=form_factor,
                compactness=compactness,
                circularity=circularity,
                elongation=elongation,
            ))
        else:
            # Partial indicators
            indicator_data = []
            if form_factor is not None:
                indicator_data.append(("Wskaźnik formy Hortona (Cf)", f"{form_factor:.3f}", "-"))
            if compactness is not None:
                indicator_data.append(("Wsp. zwartości Graveliusa (Cz)", f"{compactness:.3f}", "-"))
            if circularity is not None:
                indicator_data.append(("Wsp. kolistości Millera (Ck)", f"{circularity:.3f}", "-"))
            if elongation is not None:
                indicator_data.append(("Wsp. wydłużenia Schumma (Ce)", f"{elongation:.3f}", "-"))

            if indicator_data:
                lines.append(TableGenerator.parameters_table(
                    indicator_data,
                    headers=("Wskaźnik", "Wartość", "Jednostka"),
                ))

    return "\n".join(lines)
