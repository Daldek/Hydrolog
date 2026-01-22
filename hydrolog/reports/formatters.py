"""Formatters for LaTeX formulas and Markdown tables.

This module provides utilities for rendering mathematical formulas
with substituted values and generating formatted Markdown tables.
"""

from typing import List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray


class FormulaRenderer:
    """
    Render mathematical formulas in LaTeX notation with substituted values.

    Each method returns a string containing both the general formula
    and the formula with substituted numerical values.

    Examples
    --------
    >>> FormulaRenderer.scs_retention(cn=72)
    '$$S = \\\\frac{25400}{CN} - 254 = \\\\frac{25400}{72} - 254 = 98.89 \\\\text{ mm}$$'
    """

    # =========================================================================
    # SCS-CN Formulas
    # =========================================================================

    @staticmethod
    def scs_retention(cn: int) -> str:
        """
        Render maximum retention formula: S = 25400/CN - 254.

        Parameters
        ----------
        cn : int
            Curve Number (1-100).

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        if cn == 100:
            s = 0.0
        else:
            s = (25400 / cn) - 254
        return (
            f"$$S = \\frac{{25400}}{{CN}} - 254 = "
            f"\\frac{{25400}}{{{cn}}} - 254 = {s:.2f} \\text{{ mm}}$$"
        )

    @staticmethod
    def scs_initial_abstraction(s_mm: float, ia_coef: float = 0.2) -> str:
        """
        Render initial abstraction formula: Ia = lambda * S.

        Parameters
        ----------
        s_mm : float
            Maximum retention [mm].
        ia_coef : float, optional
            Initial abstraction coefficient, by default 0.2.

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        ia = ia_coef * s_mm
        return (
            f"$$I_a = \\lambda \\cdot S = "
            f"{ia_coef} \\cdot {s_mm:.2f} = {ia:.2f} \\text{{ mm}}$$"
        )

    @staticmethod
    def scs_effective_precipitation(
        p_mm: float,
        ia_mm: float,
        s_mm: float,
        pe_mm: float,
    ) -> str:
        """
        Render effective precipitation formula: Pe = (P - Ia)^2 / (P - Ia + S).

        Parameters
        ----------
        p_mm : float
            Total precipitation [mm].
        ia_mm : float
            Initial abstraction [mm].
        s_mm : float
            Maximum retention [mm].
        pe_mm : float
            Effective precipitation [mm] (pre-calculated).

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        if p_mm <= ia_mm:
            return (
                f"$$P \\leq I_a \\Rightarrow P_e = 0 \\text{{ mm}}$$\n\n"
                f"(Opad całkowity P = {p_mm:.2f} mm nie przekracza "
                f"abstrakcji początkowej Ia = {ia_mm:.2f} mm)"
            )

        p_minus_ia = p_mm - ia_mm
        denominator = p_minus_ia + s_mm
        return (
            f"$$P_e = \\frac{{(P - I_a)^2}}{{P - I_a + S}} = "
            f"\\frac{{({p_mm:.2f} - {ia_mm:.2f})^2}}"
            f"{{{p_mm:.2f} - {ia_mm:.2f} + {s_mm:.2f}}} = "
            f"\\frac{{{p_minus_ia:.2f}^2}}{{{denominator:.2f}}} = "
            f"{pe_mm:.2f} \\text{{ mm}}$$"
        )

    @staticmethod
    def scs_amc_adjustment(cn_ii: int, cn_adjusted: int, amc: str) -> str:
        """
        Render AMC adjustment formula.

        Parameters
        ----------
        cn_ii : int
            Original CN for AMC-II.
        cn_adjusted : int
            Adjusted CN for target AMC.
        amc : str
            Target AMC condition ("I" or "III").

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        if amc == "I":
            formula = (
                f"$$CN_I = \\frac{{CN_{{II}}}}{{2.281 - 0.01281 \\cdot CN_{{II}}}} = "
                f"\\frac{{{cn_ii}}}{{2.281 - 0.01281 \\cdot {cn_ii}}} = {cn_adjusted}$$"
            )
        elif amc == "III":
            formula = (
                f"$$CN_{{III}} = \\frac{{CN_{{II}}}}{{0.427 + 0.00573 \\cdot CN_{{II}}}} = "
                f"\\frac{{{cn_ii}}}{{0.427 + 0.00573 \\cdot {cn_ii}}} = {cn_adjusted}$$"
            )
        else:
            formula = f"$$CN_{{II}} = {cn_ii}$$ (bez korekty)"
        return formula

    # =========================================================================
    # Time of Concentration Formulas
    # =========================================================================

    @staticmethod
    def kirpich_tc(length_km: float, slope_m_per_m: float, tc_min: float) -> str:
        """
        Render Kirpich formula: tc = 0.0663 * L^0.77 * S^(-0.385).

        Parameters
        ----------
        length_km : float
            Channel length [km].
        slope_m_per_m : float
            Channel slope [m/m].
        tc_min : float
            Calculated concentration time [min].

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        tc_h = tc_min / 60
        return (
            "**Wzór ogólny:**\n\n"
            "$$t_c = 0.0663 \\cdot L^{0.77} \\cdot S^{-0.385} \\text{ [h]}$$\n\n"
            "gdzie:\n"
            "- $L$ - długość cieku [km]\n"
            "- $S$ - spadek cieku [m/m]\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$t_c = 0.0663 \\cdot {length_km:.2f}^{{0.77}} \\cdot "
            f"{slope_m_per_m:.4f}^{{-0.385}} = {tc_h:.3f} \\text{{ h}} = "
            f"{tc_min:.1f} \\text{{ min}}$$"
        )

    @staticmethod
    def scs_lag_tc(
        length_km: float,
        slope_percent: float,
        cn: int,
        tc_min: float,
    ) -> str:
        """
        Render SCS Lag formula.

        Parameters
        ----------
        length_km : float
            Hydraulic length [km].
        slope_percent : float
            Average watershed slope [%].
        cn : int
            Curve Number.
        tc_min : float
            Calculated concentration time [min].

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        length_m = length_km * 1000
        s = (25400 / cn) - 254 if cn < 100 else 0
        lag_min = tc_min * 0.6
        return (
            "**Wzór ogólny:**\n\n"
            "$$t_{lag} = \\frac{L^{0.8} \\cdot (S + 25.4)^{0.7}}"
            "{7069 \\cdot Y^{0.5}} \\text{ [h]}$$\n\n"
            "$$t_c = \\frac{t_{lag}}{0.6}$$\n\n"
            "gdzie:\n"
            "- $L$ - długość hydrauliczna [m]\n"
            "- $S$ - retencja maksymalna [mm]\n"
            "- $Y$ - średni spadek zlewni [%]\n\n"
            "**Podstawienie wartości:**\n\n"
            f"- L = {length_m:.0f} m\n"
            f"- S = {s:.2f} mm (dla CN = {cn})\n"
            f"- Y = {slope_percent:.2f} %\n\n"
            f"$$t_{{lag}} = {lag_min:.1f} \\text{{ min}}$$\n\n"
            f"$$t_c = \\frac{{{lag_min:.1f}}}{{0.6}} = {tc_min:.1f} \\text{{ min}}$$"
        )

    @staticmethod
    def giandotti_tc(
        area_km2: float,
        length_km: float,
        elevation_diff_m: float,
        tc_min: float,
    ) -> str:
        """
        Render Giandotti formula.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        length_km : float
            Main channel length [km].
        elevation_diff_m : float
            Elevation difference [m].
        tc_min : float
            Calculated concentration time [min].

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        tc_h = tc_min / 60
        return (
            "**Wzór ogólny:**\n\n"
            "$$t_c = \\frac{4\\sqrt{A} + 1.5L}{0.8\\sqrt{H}} \\text{ [h]}$$\n\n"
            "gdzie:\n"
            "- $A$ - powierzchnia zlewni [km²]\n"
            "- $L$ - długość cieku głównego [km]\n"
            "- $H$ - różnica wysokości [m]\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$t_c = \\frac{{4\\sqrt{{{area_km2:.2f}}} + 1.5 \\cdot {length_km:.2f}}}"
            f"{{0.8\\sqrt{{{elevation_diff_m:.1f}}}}} = "
            f"{tc_h:.3f} \\text{{ h}} = {tc_min:.1f} \\text{{ min}}$$"
        )

    # =========================================================================
    # Unit Hydrograph Formulas
    # =========================================================================

    @staticmethod
    def scs_uh_lag_time(tc_min: float, tlag_min: float) -> str:
        """Render SCS lag time formula: tlag = 0.6 * tc."""
        return (
            "$$t_{lag} = 0.6 \\cdot t_c = "
            f"0.6 \\cdot {tc_min:.1f} = {tlag_min:.1f} \\text{{ min}}$$"
        )

    @staticmethod
    def scs_uh_time_to_peak(
        duration_min: float,
        tlag_min: float,
        tp_min: float,
    ) -> str:
        """Render SCS time to peak formula: tp = D/2 + tlag."""
        return (
            "$$t_p = \\frac{D}{2} + t_{lag} = "
            f"\\frac{{{duration_min:.1f}}}{{2}} + {tlag_min:.1f} = "
            f"{tp_min:.1f} \\text{{ min}}$$"
        )

    @staticmethod
    def scs_uh_peak_discharge(
        area_km2: float,
        tp_min: float,
        qp_m3s: float,
    ) -> str:
        """Render SCS peak discharge formula: qp = 0.208 * A / tp."""
        tp_h = tp_min / 60
        return (
            "$$q_p = \\frac{0.208 \\cdot A}{t_p} = "
            f"\\frac{{0.208 \\cdot {area_km2:.2f}}}{{{tp_h:.3f}}} = "
            f"{qp_m3s:.3f} \\text{{ m³/s/mm}}$$"
        )

    @staticmethod
    def nash_iuh_formula(n: float, k_min: float) -> str:
        """Render Nash IUH formula."""
        k_h = k_min / 60
        return (
            "**Wzór IUH Nasha:**\n\n"
            "$$u(t) = \\frac{1}{K \\cdot \\Gamma(n)} \\cdot "
            "\\left(\\frac{t}{K}\\right)^{n-1} \\cdot e^{-t/K}$$\n\n"
            "**Parametry modelu:**\n\n"
            f"- $n$ = {n:.2f} (liczba zbiorników)\n"
            f"- $K$ = {k_min:.1f} min = {k_h:.3f} h (stała zbiornika)\n"
            f"- $t_{{lag}}$ = n × K = {n * k_min:.1f} min"
        )

    @staticmethod
    def clark_iuh_formula(tc_min: float, r_min: float) -> str:
        """Render Clark IUH formula."""
        return (
            "**Model Clarka:**\n\n"
            "Translacja (histogram czas-powierzchnia) + routing przez zbiornik liniowy\n\n"
            "**Parametry modelu:**\n\n"
            f"- $T_c$ = {tc_min:.1f} min (czas koncentracji)\n"
            f"- $R$ = {r_min:.1f} min (stała zbiornika)\n"
            f"- $T_c + R$ = {tc_min + r_min:.1f} min"
        )

    @staticmethod
    def snyder_uh_formulas(
        L_km: float,
        Lc_km: float,
        ct: float,
        cp: float,
        tL_min: float,
        tp_min: float,
        qp_m3s: float,
        area_km2: float,
    ) -> str:
        """Render Snyder UH formulas."""
        tL_h = tL_min / 60
        tp_h = tp_min / 60
        return (
            "**Wzory Snydera:**\n\n"
            "$$t_L = C_t \\cdot (L \\cdot L_c)^{0.3} \\text{ [h]}$$\n\n"
            "$$q_p = \\frac{0.275 \\cdot C_p \\cdot A}{t_L} "
            "\\text{ [m³/s/mm]}$$\n\n"
            "**Parametry wejściowe:**\n\n"
            f"- $L$ = {L_km:.2f} km (długość cieku)\n"
            f"- $L_c$ = {Lc_km:.2f} km (odległość do centroidu)\n"
            f"- $C_t$ = {ct:.2f} (współczynnik czasowy)\n"
            f"- $C_p$ = {cp:.2f} (współczynnik szczytowy)\n"
            f"- $A$ = {area_km2:.2f} km²\n\n"
            "**Obliczenia:**\n\n"
            f"$$t_L = {ct:.2f} \\cdot ({L_km:.2f} \\cdot {Lc_km:.2f})^{{0.3}} = "
            f"{tL_h:.3f} \\text{{ h}} = {tL_min:.1f} \\text{{ min}}$$\n\n"
            f"$$t_p = t_L + D/2 = {tp_min:.1f} \\text{{ min}}$$\n\n"
            f"$$q_p = {qp_m3s:.3f} \\text{{ m³/s/mm}}$$"
        )

    # =========================================================================
    # Convolution Formula
    # =========================================================================

    @staticmethod
    def convolution_formula() -> str:
        """Render discrete convolution formula."""
        return (
            "**Splot dyskretny (konwolucja):**\n\n"
            "$$Q(n) = \\sum_{m=1}^{\\min(n,M)} P_e(m) \\cdot UH(n - m + 1)$$\n\n"
            "gdzie:\n"
            "- $Q(n)$ - przepływ w kroku czasowym n [m³/s]\n"
            "- $P_e(m)$ - opad efektywny w kroku m [mm]\n"
            "- $UH(k)$ - rzędna hydrogramu jednostkowego [m³/s/mm]\n"
            "- $M$ - liczba kroków opadu"
        )

    # =========================================================================
    # Water Balance
    # =========================================================================

    @staticmethod
    def runoff_coefficient(pe_mm: float, p_mm: float, c: float) -> str:
        """Render runoff coefficient formula."""
        return (
            "$$C = \\frac{P_e}{P} = "
            f"\\frac{{{pe_mm:.2f}}}{{{p_mm:.2f}}} = {c:.3f}$$"
        )


class TableGenerator:
    """
    Generate formatted Markdown tables.

    Examples
    --------
    >>> TableGenerator.parameters_table([
    ...     ("Powierzchnia", "45.30", "km²"),
    ...     ("CN", "72", "-"),
    ... ])
    '| Parametr | Wartość | Jednostka |\\n|:---------|--------:|:---------:|...'
    """

    @staticmethod
    def parameters_table(
        data: List[Tuple[str, str, str]],
        headers: Tuple[str, str, str] = ("Parametr", "Wartość", "Jednostka"),
    ) -> str:
        """
        Generate a parameters table with aligned columns.

        Parameters
        ----------
        data : list of tuple
            List of (parameter, value, unit) tuples.
        headers : tuple of str, optional
            Column headers.

        Returns
        -------
        str
            Formatted Markdown table.
        """
        lines = [
            f"| {headers[0]} | {headers[1]} | {headers[2]} |",
            "|:---------|--------:|:---------:|",
        ]
        for param, value, unit in data:
            lines.append(f"| {param} | {value} | {unit} |")
        return "\n".join(lines)

    @staticmethod
    def time_series_table(
        times: NDArray[np.float64],
        values: NDArray[np.float64],
        time_header: str = "Czas [min]",
        value_header: str = "Q [m³/s]",
        max_rows: int = 50,
        time_format: str = ".1f",
        value_format: str = ".3f",
    ) -> str:
        """
        Generate a time series table, abbreviated if too long.

        Parameters
        ----------
        times : NDArray[np.float64]
            Time values.
        values : NDArray[np.float64]
            Corresponding values.
        time_header : str, optional
            Header for time column.
        value_header : str, optional
            Header for value column.
        max_rows : int, optional
            Maximum rows before abbreviation.
        time_format : str, optional
            Format string for time values.
        value_format : str, optional
            Format string for values.

        Returns
        -------
        str
            Formatted Markdown table.
        """
        n = len(times)
        lines = [
            f"| {time_header} | {value_header} |",
            "|--------:|--------:|",
        ]

        if n <= max_rows:
            # Show all rows
            for t, v in zip(times, values):
                lines.append(f"| {t:{time_format}} | {v:{value_format}} |")
        else:
            # Show first rows, ..., last rows
            head_count = max_rows // 2
            tail_count = max_rows - head_count - 1

            for t, v in zip(times[:head_count], values[:head_count]):
                lines.append(f"| {t:{time_format}} | {v:{value_format}} |")

            lines.append("| ... | ... |")

            for t, v in zip(times[-tail_count:], values[-tail_count:]):
                lines.append(f"| {t:{time_format}} | {v:{value_format}} |")

            lines.append(f"\n*Tabela skrócona ({n} wierszy)*")

        return "\n".join(lines)

    @staticmethod
    def precipitation_table(
        times: NDArray[np.float64],
        precip_mm: NDArray[np.float64],
        effective_mm: Optional[NDArray[np.float64]] = None,
        max_rows: int = 30,
    ) -> str:
        """
        Generate precipitation distribution table.

        Parameters
        ----------
        times : NDArray[np.float64]
            Time values [min].
        precip_mm : NDArray[np.float64]
            Precipitation in each interval [mm].
        effective_mm : NDArray[np.float64], optional
            Effective precipitation [mm].
        max_rows : int, optional
            Maximum rows before abbreviation.

        Returns
        -------
        str
            Formatted Markdown table.
        """
        n = len(times)
        has_effective = effective_mm is not None

        # Calculate cumulative sums
        p_cumsum = np.cumsum(precip_mm)

        if has_effective:
            pe_cumsum = np.cumsum(effective_mm)
            headers = "| Czas [min] | P [mm] | P kum. [mm] | Pe [mm] | Pe kum. [mm] |"
            separator = "|--------:|------:|------:|------:|------:|"
        else:
            headers = "| Czas [min] | P [mm] | P kum. [mm] |"
            separator = "|--------:|------:|------:|"

        lines = [headers, separator]

        def add_row(i: int) -> None:
            t = times[i]
            p = precip_mm[i]
            pc = p_cumsum[i]
            if has_effective:
                pe = effective_mm[i]
                pec = pe_cumsum[i]
                lines.append(f"| {t:.1f} | {p:.2f} | {pc:.2f} | {pe:.2f} | {pec:.2f} |")
            else:
                lines.append(f"| {t:.1f} | {p:.2f} | {pc:.2f} |")

        if n <= max_rows:
            for i in range(n):
                add_row(i)
        else:
            head_count = max_rows // 2
            tail_count = max_rows - head_count - 1

            for i in range(head_count):
                add_row(i)

            if has_effective:
                lines.append("| ... | ... | ... | ... | ... |")
            else:
                lines.append("| ... | ... | ... |")

            for i in range(n - tail_count, n):
                add_row(i)

            lines.append(f"\n*Tabela skrócona ({n} wierszy)*")

        return "\n".join(lines)

    @staticmethod
    def water_balance_table(
        total_precip_mm: float,
        initial_abstraction_mm: float,
        retention_mm: float,
        effective_mm: float,
    ) -> str:
        """
        Generate water balance summary table.

        Parameters
        ----------
        total_precip_mm : float
            Total precipitation [mm].
        initial_abstraction_mm : float
            Initial abstraction [mm].
        retention_mm : float
            Maximum retention [mm].
        effective_mm : float
            Total effective precipitation [mm].

        Returns
        -------
        str
            Formatted Markdown table with percentages.
        """
        # Calculate infiltration (continuing abstraction)
        infiltration_mm = total_precip_mm - initial_abstraction_mm - effective_mm
        if infiltration_mm < 0:
            infiltration_mm = 0

        # Calculate percentages
        def pct(value: float) -> str:
            if total_precip_mm > 0:
                return f"{100 * value / total_precip_mm:.1f}"
            return "0.0"

        lines = [
            "| Składnik bilansu | Wartość [mm] | Udział [%] |",
            "|:-----------------|-------------:|-----------:|",
            f"| Opad całkowity P | {total_precip_mm:.2f} | 100.0 |",
            f"| Abstrakcja początkowa Ia | {initial_abstraction_mm:.2f} | {pct(initial_abstraction_mm)} |",
            f"| Infiltracja F | {infiltration_mm:.2f} | {pct(infiltration_mm)} |",
            f"| **Opad efektywny Pe** | **{effective_mm:.2f}** | **{pct(effective_mm)}** |",
        ]
        return "\n".join(lines)

    @staticmethod
    def uh_ordinates_table(
        times: NDArray[np.float64],
        ordinates: NDArray[np.float64],
        max_rows: int = 30,
    ) -> str:
        """
        Generate unit hydrograph ordinates table.

        Parameters
        ----------
        times : NDArray[np.float64]
            Time values [min].
        ordinates : NDArray[np.float64]
            UH ordinates [m³/s/mm].
        max_rows : int, optional
            Maximum rows.

        Returns
        -------
        str
            Formatted Markdown table.
        """
        return TableGenerator.time_series_table(
            times=times,
            values=ordinates,
            time_header="Czas [min]",
            value_header="q [m³/s/mm]",
            max_rows=max_rows,
            time_format=".1f",
            value_format=".4f",
        )

    @staticmethod
    def hydrograph_results_table(
        peak_discharge: float,
        time_to_peak: float,
        volume: float,
    ) -> str:
        """
        Generate hydrograph results summary table.

        Parameters
        ----------
        peak_discharge : float
            Peak discharge [m³/s].
        time_to_peak : float
            Time to peak [min].
        volume : float
            Total volume [m³].

        Returns
        -------
        str
            Formatted Markdown table.
        """
        lines = [
            "| Charakterystyka | Wartość | Jednostka |",
            "|:----------------|--------:|:---------:|",
            f"| Przepływ szczytowy Qmax | {peak_discharge:.2f} | m³/s |",
            f"| Czas do szczytu tp | {time_to_peak:.1f} | min |",
            f"| Objętość odpływu V | {volume:,.0f} | m³ |",
        ]
        return "\n".join(lines)

    @staticmethod
    def shape_indicators_table(
        form_factor: float,
        compactness: float,
        circularity: float,
        elongation: float,
    ) -> str:
        """
        Generate watershed shape indicators table.

        Parameters
        ----------
        form_factor : float
            Horton's form factor Cf.
        compactness : float
            Gravelius compactness coefficient Cz.
        circularity : float
            Miller's circularity ratio Ck.
        elongation : float
            Schumm's elongation ratio Ce.

        Returns
        -------
        str
            Formatted Markdown table with interpretation.
        """

        def interpret_cf(v: float) -> str:
            if v < 0.5:
                return "wydłużona"
            elif v > 0.75:
                return "zwarta"
            return "umiarkowana"

        def interpret_cz(v: float) -> str:
            if v < 1.25:
                return "zbliżona do koła"
            elif v > 1.5:
                return "wydłużona"
            return "umiarkowana"

        lines = [
            "| Wskaźnik | Symbol | Wartość | Interpretacja |",
            "|:---------|:------:|--------:|:--------------|",
            f"| Wskaźnik formy Hortona | Cf | {form_factor:.3f} | {interpret_cf(form_factor)} |",
            f"| Wsp. zwartości Graveliusa | Cz | {compactness:.3f} | {interpret_cz(compactness)} |",
            f"| Wsp. kolistości Millera | Ck | {circularity:.3f} | - |",
            f"| Wsp. wydłużenia Schumma | Ce | {elongation:.3f} | - |",
        ]
        return "\n".join(lines)
