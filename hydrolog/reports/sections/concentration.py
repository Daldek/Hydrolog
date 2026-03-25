"""Time of concentration report section.

Generates the section documenting concentration time calculations
using Kirpich, NRCS, Giandotti, FAA, Kerby, or Kerby-Kirpich methods.
"""

from typing import Optional

from hydrolog.reports.formatters import FormulaRenderer
from hydrolog.reports.templates import (
    SECTION_HEADERS,
    SECTION_INTROS,
    SUBSECTION_HEADERS,
    TC_METHODS,
)


def generate_tc_section(
    tc_min: float,
    method: str,
    length_km: Optional[float] = None,
    slope_m_per_m: Optional[float] = None,
    slope_percent: Optional[float] = None,
    area_km2: Optional[float] = None,
    elevation_diff_m: Optional[float] = None,
    cn: Optional[int] = None,
    runoff_coeff: Optional[float] = None,
    retardance: Optional[float] = None,
    overland_length_km: Optional[float] = None,
    overland_slope_m_per_m: Optional[float] = None,
    channel_length_km: Optional[float] = None,
    channel_slope_m_per_m: Optional[float] = None,
    tc_overland_min: Optional[float] = None,
    tc_channel_min: Optional[float] = None,
    include_formulas: bool = True,
) -> str:
    """
    Generate time of concentration section.

    Parameters
    ----------
    tc_min : float
        Calculated time of concentration [min].
    method : str
        Method used ("kirpich", "nrcs", "giandotti", "faa", "kerby",
        "kerby_kirpich").
    length_km : float, optional
        Channel/hydraulic length [km].
    slope_m_per_m : float, optional
        Channel slope [m/m].
    slope_percent : float, optional
        Watershed slope [%].
    area_km2 : float, optional
        Watershed area [km²].
    elevation_diff_m : float, optional
        Elevation difference [m].
    cn : int, optional
        Curve Number (for NRCS).
    runoff_coeff : float, optional
        Rational method runoff coefficient (for FAA).
    retardance : float, optional
        Kerby retardance roughness coefficient (for Kerby/Kerby-Kirpich).
    overland_length_km : float, optional
        Overland flow length [km] (for Kerby-Kirpich).
    overland_slope_m_per_m : float, optional
        Average overland slope [m/m] (for Kerby-Kirpich).
    channel_length_km : float, optional
        Channel flow length [km] (for Kerby-Kirpich).
    channel_slope_m_per_m : float, optional
        Average channel slope [m/m] (for Kerby-Kirpich).
    tc_overland_min : float, optional
        Overland flow component [min] (for Kerby-Kirpich).
    tc_channel_min : float, optional
        Channel flow component [min] (for Kerby-Kirpich).
    include_formulas : bool, optional
        Include detailed formulas, by default True.

    Returns
    -------
    str
        Markdown content for the section.
    """
    method = method.lower()

    lines = [
        SECTION_HEADERS["concentration"],
        SECTION_INTROS["concentration"],
        "",
        SUBSECTION_HEADERS["concentration"]["method"],
        "",
        f"**{TC_METHODS.get(method, method)}**",
        "",
    ]

    if include_formulas:
        lines.append(SUBSECTION_HEADERS["concentration"]["calculation"])
        lines.append("")

        if method == "kirpich":
            if length_km is not None and slope_m_per_m is not None:
                lines.append(
                    FormulaRenderer.kirpich_tc(
                        length_km=length_km,
                        slope_m_per_m=slope_m_per_m,
                        tc_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Długość cieku: L = {length_km:.2f} km"
                            if length_km
                            else "- Długość cieku: brak danych"
                        ),
                        (
                            f"- Spadek cieku: S = {slope_m_per_m:.4f} m/m"
                            if slope_m_per_m
                            else "- Spadek cieku: brak danych"
                        ),
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        elif method == "nrcs":
            if length_km is not None and slope_percent is not None and cn is not None:
                lines.append(
                    FormulaRenderer.nrcs_tc(
                        length_km=length_km,
                        slope_percent=slope_percent,
                        cn=cn,
                        tc_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Długość hydrauliczna: L = {length_km:.2f} km"
                            if length_km
                            else "- Długość: brak danych"
                        ),
                        (
                            f"- Spadek zlewni: Y = {slope_percent:.2f} %"
                            if slope_percent
                            else "- Spadek: brak danych"
                        ),
                        f"- Curve Number: CN = {cn}" if cn else "- CN: brak danych",
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        elif method == "giandotti":
            if (
                area_km2 is not None
                and length_km is not None
                and elevation_diff_m is not None
            ):
                lines.append(
                    FormulaRenderer.giandotti_tc(
                        area_km2=area_km2,
                        length_km=length_km,
                        elevation_diff_m=elevation_diff_m,
                        tc_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Powierzchnia: A = {area_km2:.2f} km²"
                            if area_km2
                            else "- Powierzchnia: brak danych"
                        ),
                        (
                            f"- Długość cieku: L = {length_km:.2f} km"
                            if length_km
                            else "- Długość: brak danych"
                        ),
                        (
                            f"- Różnica wysokości: H = {elevation_diff_m:.1f} m"
                            if elevation_diff_m
                            else "- Deniwelacja: brak danych"
                        ),
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        elif method == "faa":
            if (
                length_km is not None
                and slope_m_per_m is not None
                and runoff_coeff is not None
            ):
                lines.append(
                    FormulaRenderer.faa_tc(
                        length_km=length_km,
                        slope_m_per_m=slope_m_per_m,
                        runoff_coeff=runoff_coeff,
                        tc_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Długość spływu: L = {length_km:.3f} km"
                            if length_km
                            else "- Długość spływu: brak danych"
                        ),
                        (
                            f"- Spadek: S = {slope_m_per_m:.4f} m/m"
                            if slope_m_per_m
                            else "- Spadek: brak danych"
                        ),
                        (
                            f"- Współczynnik spływu: C = {runoff_coeff:.2f}"
                            if runoff_coeff
                            else "- Współczynnik spływu: brak danych"
                        ),
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        elif method == "kerby":
            if (
                length_km is not None
                and slope_m_per_m is not None
                and retardance is not None
            ):
                lines.append(
                    FormulaRenderer.kerby_tc(
                        length_km=length_km,
                        slope_m_per_m=slope_m_per_m,
                        retardance=retardance,
                        tc_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Długość spływu: L = {length_km:.3f} km"
                            if length_km
                            else "- Długość spływu: brak danych"
                        ),
                        (
                            f"- Spadek: S = {slope_m_per_m:.4f} m/m"
                            if slope_m_per_m
                            else "- Spadek: brak danych"
                        ),
                        (
                            f"- Współczynnik opóźnienia: N = {retardance:.2f}"
                            if retardance
                            else "- Współczynnik opóźnienia: brak danych"
                        ),
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        elif method == "kerby_kirpich":
            if (
                overland_length_km is not None
                and overland_slope_m_per_m is not None
                and retardance is not None
                and channel_length_km is not None
                and channel_slope_m_per_m is not None
                and tc_overland_min is not None
                and tc_channel_min is not None
            ):
                lines.append(
                    FormulaRenderer.kerby_kirpich_tc(
                        ov_length_km=overland_length_km,
                        ov_slope_m_per_m=overland_slope_m_per_m,
                        retardance=retardance,
                        ch_length_km=channel_length_km,
                        ch_slope_m_per_m=channel_slope_m_per_m,
                        tc_ov_min=tc_overland_min,
                        tc_ch_min=tc_channel_min,
                        tc_total_min=tc_min,
                    )
                )
            else:
                lines.extend(
                    [
                        "**Dane wejściowe:**",
                        "",
                        (
                            f"- Długość spływu pow.: L_ov = "
                            f"{overland_length_km:.3f} km"
                            if overland_length_km
                            else "- Długość spływu pow.: brak danych"
                        ),
                        (
                            f"- Spadek pow.: S_ov = "
                            f"{overland_slope_m_per_m:.4f} m/m"
                            if overland_slope_m_per_m
                            else "- Spadek pow.: brak danych"
                        ),
                        (
                            f"- Współczynnik opóźnienia: N = {retardance:.2f}"
                            if retardance
                            else "- Współczynnik opóźnienia: brak danych"
                        ),
                        (
                            f"- Długość koryta: L_ch = " f"{channel_length_km:.2f} km"
                            if channel_length_km
                            else "- Długość koryta: brak danych"
                        ),
                        (
                            f"- Spadek koryta: S_ch = "
                            f"{channel_slope_m_per_m:.4f} m/m"
                            if channel_slope_m_per_m
                            else "- Spadek koryta: brak danych"
                        ),
                        "",
                        f"**Wynik:** $t_c$ = {tc_min:.1f} min",
                    ]
                )

        else:
            lines.append(f"Metoda: {method}")
            lines.append("")
            lines.append(f"**Wynik:** $t_c$ = {tc_min:.1f} min")

    else:
        # Just show the result
        lines.extend(
            [
                f"Obliczony czas koncentracji: **tc = {tc_min:.1f} min** ({tc_min/60:.2f} h)",
            ]
        )

    # Summary
    lines.extend(
        [
            "",
            "---",
            "",
            f"**Przyjęty czas koncentracji:** $t_c$ = **{tc_min:.1f} min** = {tc_min/60:.2f} h",
        ]
    )

    return "\n".join(lines)
