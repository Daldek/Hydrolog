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
    def nrcs_tc(
        length_km: float,
        slope_percent: float,
        cn: int,
        tc_min: float,
    ) -> str:
        """
        Render NRCS formula.

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
        return (
            "**Wzór ogólny:**\n\n"
            "$$t_c = 0.01416 \\cdot L^{0.8} \\cdot (S + 25.4)^{0.7}"
            " \\cdot Y^{-0.5} \\text{ [min]}$$\n\n"
            "gdzie:\n"
            "- $L$ - długość hydrauliczna [m]\n"
            "- $S$ - retencja maksymalna [mm]\n"
            "- $Y$ - średni spadek zlewni [%]\n\n"
            "**Podstawienie wartości:**\n\n"
            f"- L = {length_m:.0f} m\n"
            f"- S = {s:.2f} mm (dla CN = {cn})\n"
            f"- Y = {slope_percent:.2f} %\n\n"
            f"$$t_c = {tc_min:.1f} \\text{{ min}}$$"
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
    def nash_from_tc_formulas(
        tc_min: float,
        n: float,
        lag_ratio: float,
        k_min: float,
    ) -> str:
        """
        Render Nash IUH parameter estimation from time of concentration.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        n : float
            Number of reservoirs.
        lag_ratio : float
            Ratio of lag time to tc (SCS default: 0.6).
        k_min : float
            Storage coefficient K [min].

        Returns
        -------
        str
            LaTeX formulas with substituted values.
        """
        tlag_min = lag_ratio * tc_min
        return (
            "**Metoda estymacji parametrów (z czasu koncentracji):**\n\n"
            "**Czas opóźnienia:**\n\n"
            "$$t_{lag} = \\lambda \\cdot t_c$$\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$t_{{lag}} = {lag_ratio} \\cdot {tc_min:.1f} = "
            f"{tlag_min:.1f} \\text{{ min}}$$\n\n"
            "**Stała zbiornika:**\n\n"
            "$$K = \\frac{t_{lag}}{n}$$\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$K = \\frac{{{tlag_min:.1f}}}{{{n:.2f}}} = "
            f"{k_min:.1f} \\text{{ min}}$$\n\n"
            f"- $\\lambda$ = {lag_ratio} (stosunek czasu opóźnienia do tc)\n"
            f"- $t_c$ = {tc_min:.1f} min (czas koncentracji)\n"
            f"- $t_{{lag}}$ = {tlag_min:.1f} min (czas opóźnienia)\n"
            f"- $n$ = {n:.2f} (liczba zbiorników)\n"
            f"- $K$ = {k_min:.1f} min (stała zbiornika)"
        )

    @staticmethod
    def nash_from_lutz_formulas(
        L_km: float,
        Lc_km: float,
        slope: float,
        manning_n: float,
        urban_pct: float,
        forest_pct: float,
        P1: float,
        tp_hours: float,
        up_per_hour: float,
        f_N: float,
        n: float,
        k_min: float,
    ) -> str:
        """
        Render all Lutz parameter estimation steps for Nash IUH.

        Parameters
        ----------
        L_km : float
            Main stream length [km].
        Lc_km : float
            Length to catchment centroid along stream [km].
        slope : float
            Average main stream slope [-].
        manning_n : float
            Manning's roughness coefficient [-].
        urban_pct : float
            Urbanized area [%].
        forest_pct : float
            Forested area [%].
        P1 : float
            Lutz P1 coefficient.
        tp_hours : float
            Time to peak [hours].
        up_per_hour : float
            Peak IUH ordinate [1/hour].
        f_N : float
            Shape function value tp * up.
        n : float
            Estimated number of reservoirs.
        k_min : float
            Storage coefficient [min].

        Returns
        -------
        str
            LaTeX formulas with substituted values for all six steps.
        """
        k_h = k_min / 60
        tp_min = tp_hours * 60
        slope_pct = slope * 100

        return (
            "**Metoda Lutza — wyznaczanie parametrów n i K:**\n\n"
            "**Krok 1: Współczynnik P1**\n\n"
            "$$P_1 = 3{,}989 \\cdot n_{Man} + 0{,}028$$\n\n"
            f"$$P_1 = 3{{,}}989 \\cdot {manning_n:.3f} + 0{{,}}028 = {P1:.4f}$$\n\n"
            "**Krok 2: Czas do szczytu tp**\n\n"
            "$$t_p = P_1 \\cdot \\left(\\frac{L \\cdot L_c}{J_g^{1{,}5}}\\right)^{0{,}26}"
            " \\cdot e^{-0{,}016 U} \\cdot e^{0{,}004 W} \\quad [\\text{h}]$$\n\n"
            "gdzie:\n"
            f"- $L$ = {L_km:.3f} km (długość cieku)\n"
            f"- $L_c$ = {Lc_km:.3f} km (odległość do centroidu zlewni)\n"
            f"- $J_g$ = {slope:.4f} (spadek cieku, {slope_pct:.2f}%)\n"
            f"- $U$ = {urban_pct:.1f}% (tereny zurbanizowane)\n"
            f"- $W$ = {forest_pct:.1f}% (tereny leśne)\n\n"
            f"$$t_p = {P1:.4f} \\cdot \\left(\\frac{{{L_km:.3f} \\cdot {Lc_km:.3f}}}"
            f"{{{slope:.4f}^{{1{{,}}5}}}}\\right)^{{0{{,}}26}}"
            f" \\cdot e^{{-0{{,}}016 \\cdot {urban_pct:.1f}}}"
            f" \\cdot e^{{0{{,}}004 \\cdot {forest_pct:.1f}}}"
            f" = {tp_hours:.4f} \\text{{ h}} = {tp_min:.1f} \\text{{ min}}$$\n\n"
            "**Krok 3: Szczytowa rzędna IUH**\n\n"
            "$$u_p = \\frac{0{,}66}{t_p^{1{,}04}} \\quad [\\text{h}^{-1}]$$\n\n"
            f"$$u_p = \\frac{{0{{,}}66}}{{{tp_hours:.4f}^{{1{{,}}04}}}}"
            f" = {up_per_hour:.4f} \\text{{ h}}^{{-1}}$$\n\n"
            "**Krok 4: Funkcja kształtu f(N)**\n\n"
            "$$f(N) = t_p \\cdot u_p$$\n\n"
            f"$$f(N) = {tp_hours:.4f} \\cdot {up_per_hour:.4f} = {f_N:.4f}$$\n\n"
            "**Krok 5: Wyznaczenie parametru n**\n\n"
            "Rozwiązanie równania:\n\n"
            "$$f(N) = \\frac{(N-1)^N \\cdot e^{-(N-1)}}{\\Gamma(N)}$$\n\n"
            f"Dla $f(N) = {f_N:.4f}$ otrzymano: $n = {n:.3f}$\n\n"
            "**Krok 6: Stała zbiornika K**\n\n"
            "$$K = \\frac{t_p}{n - 1} \\quad [\\text{h}]$$\n\n"
            f"$$K = \\frac{{{tp_hours:.4f}}}{{{n:.3f} - 1}}"
            f" = {k_h:.4f} \\text{{ h}} = {k_min:.1f} \\text{{ min}}$$\n\n"
            "*Źródło: Lutz, W. (1984). Berechnung von Hochwasserabflüssen "
            "unter Anwendung von Gebietskenngrößen. Universität Karlsruhe.*"
        )

    @staticmethod
    def nash_urban_regression_formulas(
        area_km2: float,
        urban_fraction: float,
        effective_precip_mm: float,
        duration_h: float,
        tL_h: float,
        k_h: float,
        N: float,
    ) -> str:
        """
        Render Nash IUH parameter estimation via urban regression.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        urban_fraction : float
            Urbanization index [-] (0 = natural).
        effective_precip_mm : float
            Total effective precipitation depth [mm].
        duration_h : float
            Effective rainfall duration [h].
        tL_h : float
            Calculated lag time [h].
        k_h : float
            Calculated storage coefficient [h].
        N : float
            Calculated number of reservoirs [-].

        Returns
        -------
        str
            LaTeX formulas with substituted values.
        """
        k_min = k_h * 60.0
        one_plus_u = 1.0 + urban_fraction

        return (
            "**Metoda estymacji parametrów: regresja dla zlewni zurbanizowanych "
            "(Rao, Delleur, Sarma 1972)**\n\n"
            "**Parametry wejściowe:**\n\n"
            "| Parametr | Wartość | Jednostka |\n"
            "|:---------|--------:|:---------:|\n"
            f"| Powierzchnia zlewni A | {area_km2:.3f} | km² |\n"
            f"| Wskaźnik urbanizacji U | {urban_fraction:.3f} | - |\n"
            f"| Opad efektywny H | {effective_precip_mm:.3f} | mm |\n"
            f"| Czas trwania opadu D | {duration_h:.4f} | h |\n\n"
            "**Krok 1: Czas opóźnienia $t_L$**\n\n"
            "$$t_L = 1{,}28 \\cdot A^{0{,}46} \\cdot (1+U)^{-1{,}66} "
            "\\cdot H^{-0{,}27} \\cdot D^{0{,}37} \\text{ [h]}$$\n\n"
            f"$$t_L = 1{{,}}28 \\cdot {area_km2:.3f}^{{0{{,}}46}} "
            f"\\cdot {one_plus_u:.3f}^{{-1{{,}}66}} "
            f"\\cdot {effective_precip_mm:.3f}^{{-0{{,}}27}} "
            f"\\cdot {duration_h:.4f}^{{0{{,}}37}} "
            f"= {tL_h:.4f} \\text{{ h}}$$\n\n"
            "**Krok 2: Stała zbiornika $k$**\n\n"
            "$$k = 0{,}56 \\cdot A^{0{,}39} \\cdot (1+U)^{-0{,}62} "
            "\\cdot H^{-0{,}11} \\cdot D^{0{,}22} \\text{ [h]}$$\n\n"
            f"$$k = 0{{,}}56 \\cdot {area_km2:.3f}^{{0{{,}}39}} "
            f"\\cdot {one_plus_u:.3f}^{{-0{{,}}62}} "
            f"\\cdot {effective_precip_mm:.3f}^{{-0{{,}}11}} "
            f"\\cdot {duration_h:.4f}^{{0{{,}}22}} "
            f"= {k_h:.4f} \\text{{ h}} = {k_min:.2f} \\text{{ min}}$$\n\n"
            "**Krok 3: Liczba zbiorników $N$**\n\n"
            "$$N = \\frac{t_L}{k}$$\n\n"
            f"$$N = \\frac{{{tL_h:.4f}}}{{{k_h:.4f}}} = {N:.3f}$$\n\n"
            "*Źródło: Rao, R.A.; Delleur, J.W.; Sarma, B.S.P. (1972). "
            "Conceptual Hydrologic Models for Urbanizing Basins. "
            "Journal of the Hydraulics Division, ASCE, 98(HY7), 1205–1220.*"
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
    def clark_from_tc_r_ratio(tc_min: float, r_tc_ratio: float, r_min: float) -> str:
        """
        Render Clark R estimation from R/Tc ratio with substituted values.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        r_tc_ratio : float
            Ratio R/Tc used to derive the storage coefficient.
        r_min : float
            Derived storage coefficient [min].

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        return (
            "**Estymacja stałej zbiornika R (metoda R/Tc):**\n\n"
            "$$R = \\frac{R}{T_c} \\cdot T_c$$\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$R = {r_tc_ratio:.3f} \\cdot {tc_min:.1f} = {r_min:.1f} \\text{{ min}}$$"
        )

    @staticmethod
    def clark_routing_coefficient(timestep_min: float, r_min: float, c1: float) -> str:
        """
        Render Clark routing coefficient C1 with substituted values.

        Parameters
        ----------
        timestep_min : float
            Computational time step [min].
        r_min : float
            Storage coefficient [min].
        c1 : float
            Routing coefficient (pre-calculated).

        Returns
        -------
        str
            LaTeX formula with substituted values.
        """
        denom = 2.0 * r_min + timestep_min
        return (
            "**Współczynnik routingu C1:**\n\n"
            "$$C_1 = \\frac{\\Delta t}{2R + \\Delta t}$$\n\n"
            "**Podstawienie wartości:**\n\n"
            f"$$C_1 = \\frac{{{timestep_min:.1f}}}{{2 \\cdot {r_min:.1f} + {timestep_min:.1f}}} = "
            f"\\frac{{{timestep_min:.1f}}}{{{denom:.1f}}} = {c1:.4f}$$"
        )

    @staticmethod
    def clark_time_area_substituted(tc_min: float) -> str:
        """
        Render Clark time-area histogram formula with substituted Tc.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].

        Returns
        -------
        str
            LaTeX formula with substituted Tc value.
        """
        half_tc = tc_min / 2.0
        return (
            "**Skumulowany histogram czas-powierzchnia (zlewnia eliptyczna, standard HEC-HMS):**\n\n"
            "$$A_{cum}(t) = \\begin{cases}\n"
            "1.414 \\cdot \\left(\\frac{t}{T_c}\\right)^{1.5} & 0 \\leq t \\leq T_c/2 \\\\\n"
            "1 - 1.414 \\cdot \\left(1 - \\frac{t}{T_c}\\right)^{1.5} & T_c/2 < t \\leq T_c\n"
            "\\end{cases}$$\n\n"
            "**Podstawienie wartości** ($T_c$ = "
            f"{tc_min:.1f}"
            " min):\n\n"
            "$$A_{cum}(t) = \\begin{cases}\n"
            f"1.414 \\cdot \\left(\\dfrac{{t}}{{{tc_min:.1f}}}\\right)^{{1.5}} & 0 \\leq t \\leq {half_tc:.1f} \\text{{ min}} \\\\\n"
            f"1 - 1.414 \\cdot \\left(1 - \\dfrac{{t}}{{{tc_min:.1f}}}\\right)^{{1.5}} & {half_tc:.1f} \\text{{ min}} < t \\leq {tc_min:.1f} \\text{{ min}}\n"
            "\\end{cases}$$"
        )

    @staticmethod
    def snyder_uh_formulas(
        L_km: float,
        Lc_km: float,
        ct: float,
        cp: float,
        tL_min: float,
        tD_min: float,
        tp_min: float,
        qp_m3s: float,
        area_km2: float,
        tb_min: float,
        w50_h: float,
        w75_h: float,
        duration_min: Optional[float] = None,
        tLR_min: Optional[float] = None,
        tpR_min: Optional[float] = None,
        qpR_m3s: Optional[float] = None,
    ) -> str:
        """
        Render Snyder UH formulas with substituted values.

        Renders all key Snyder formulas: tL, tD, tp, qp, tb, W50, W75.
        When a non-standard duration is provided (duration_min != tD_min),
        also renders the adjusted parameters tLR, tpR, qpR.

        Parameters
        ----------
        L_km : float
            Main stream length [km].
        Lc_km : float
            Length to watershed centroid [km].
        ct : float
            Time coefficient Ct.
        cp : float
            Peak coefficient Cp.
        tL_min : float
            Basin lag time tL [min].
        tD_min : float
            Standard rainfall duration tD = tL/5.5 [min].
        tp_min : float
            Time to peak for standard duration [min].
        qp_m3s : float
            Peak discharge for standard duration [m³/s/mm].
        area_km2 : float
            Watershed area [km²].
        tb_min : float
            Time base tb [min].
        w50_h : float
            Hydrograph width at 50 % of peak [h].
        w75_h : float
            Hydrograph width at 75 % of peak [h].
        duration_min : float, optional
            Actual rainfall duration used (if non-standard).
        tLR_min : float, optional
            Adjusted lag time tLR [min] (for non-standard duration).
        tpR_min : float, optional
            Adjusted time to peak tpR [min] (for non-standard duration).
        qpR_m3s : float, optional
            Adjusted peak discharge qpR [m³/s/mm] (for non-standard duration).

        Returns
        -------
        str
            Markdown text with LaTeX formulas and substituted values.
        """
        tL_h = tL_min / 60
        tD_h = tD_min / 60
        tp_h = tp_min / 60
        tb_h = tb_min / 60
        qp_per_area = qp_m3s / area_km2

        is_non_standard = (
            duration_min is not None
            and tLR_min is not None
            and tpR_min is not None
            and qpR_m3s is not None
            and abs(duration_min - tD_min) > 0.5
        )

        parts: list = [
            "**Wzory Snydera:**\n\n"
            "$$t_L = C_t \\cdot (L \\cdot L_c)^{0.3} \\text{ [h]}$$\n\n"
            "$$t_D = \\frac{t_L}{5{,}5} \\text{ [h]}$$\n\n"
            "$$t_p = t_L + \\frac{t_D}{2} \\text{ [h]}$$\n\n"
            "$$q_p = \\frac{0{,}275 \\cdot C_p \\cdot A}{t_L} \\text{ [m³/s/mm]}$$\n\n"
            "$$t_b = \\frac{0{,}556 \\cdot A}{q_p} \\text{ [h]}$$\n\n"
            "$$W_{50} = \\frac{0{,}1783}{(q_p/A)^{1{,}08}} \\text{ [h]}, "
            "\\quad W_{75} = \\frac{0{,}1019}{(q_p/A)^{1{,}08}} \\text{ [h]}$$",
            "**Parametry wejściowe:**\n\n"
            f"- $L$ = {L_km:.2f} km (długość cieku)\n"
            f"- $L_c$ = {Lc_km:.2f} km (odległość do centroidu)\n"
            f"- $C_t$ = {ct:.2f} (współczynnik czasowy)\n"
            f"- $C_p$ = {cp:.2f} (współczynnik szczytowy)\n"
            f"- $A$ = {area_km2:.2f} km²",
            "**Obliczenia (standardowy czas trwania):**\n\n"
            f"$$t_L = {ct:.2f} \\cdot ({L_km:.2f} \\cdot {Lc_km:.2f})^{{0.3}} = "
            f"{tL_h:.3f} \\text{{ h}} = {tL_min:.1f} \\text{{ min}}$$\n\n"
            f"$$t_D = \\frac{{{tL_h:.3f}}}{{5{{,}}5}} = "
            f"{tD_h:.3f} \\text{{ h}} = {tD_min:.1f} \\text{{ min}}$$\n\n"
            f"$$t_p = {tL_h:.3f} + \\frac{{{tD_h:.3f}}}{{2}} = "
            f"{tp_h:.3f} \\text{{ h}} = {tp_min:.1f} \\text{{ min}}$$\n\n"
            f"$$q_p = \\frac{{0{{,}}275 \\cdot {cp:.2f} \\cdot {area_km2:.2f}}}{{{tL_h:.3f}}} = "
            f"{qp_m3s:.4f} \\text{{ m³/s/mm}}$$\n\n"
            f"$$t_b = \\frac{{0{{,}}556 \\cdot {area_km2:.2f}}}{{{qp_m3s:.4f}}} = "
            f"{tb_h:.3f} \\text{{ h}} = {tb_min:.1f} \\text{{ min}}$$\n\n"
            f"$$W_{{50}} = \\frac{{0{{,}}1783}}{{{qp_per_area:.5f}^{{1{{,}}08}}}} = "
            f"{w50_h:.3f} \\text{{ h}}, \\quad "
            f"W_{{75}} = \\frac{{0{{,}}1019}}{{{qp_per_area:.5f}^{{1{{,}}08}}}} = "
            f"{w75_h:.3f} \\text{{ h}}$$",
        ]

        if is_non_standard:
            assert duration_min is not None
            assert tLR_min is not None
            assert tpR_min is not None
            assert qpR_m3s is not None
            dt_h = duration_min / 60
            tLR_h = tLR_min / 60
            tpR_h = tpR_min / 60
            delta_h = (duration_min - tD_min) / 60

            parts.append(
                f"**Korekta dla niestandardowego czasu trwania "
                f"($\\Delta t$ = {duration_min:.1f} min "
                f"$\\neq$ $t_D$ = {tD_min:.1f} min):**\n\n"
                "$$t_{LR} = t_L + 0{,}25 \\cdot (\\Delta t - t_D) \\text{ [h]}$$\n\n"
                "$$t_{pR} = t_{LR} + \\frac{\\Delta t}{2} \\text{ [h]}$$\n\n"
                "$$q_{pR} = \\frac{0{,}275 \\cdot C_p \\cdot A}{t_{LR}} "
                "\\text{ [m³/s/mm]}$$\n\n"
                "**Obliczenia (niestandardowy czas trwania):**\n\n"
                f"$$t_{{LR}} = {tL_h:.3f} + 0{{,}}25 \\cdot "
                f"({dt_h:.3f} - {tD_h:.3f}) = "
                f"{tL_h:.3f} + 0{{,}}25 \\cdot ({delta_h:+.3f}) = "
                f"{tLR_h:.3f} \\text{{ h}} = {tLR_min:.1f} \\text{{ min}}$$\n\n"
                f"$$t_{{pR}} = {tLR_h:.3f} + \\frac{{{dt_h:.3f}}}{{2}} = "
                f"{tpR_h:.3f} \\text{{ h}} = {tpR_min:.1f} \\text{{ min}}$$\n\n"
                f"$$q_{{pR}} = \\frac{{0{{,}}275 \\cdot {cp:.2f} \\cdot "
                f"{area_km2:.2f}}}{{{tLR_h:.3f}}} = "
                f"{qpR_m3s:.4f} \\text{{ m³/s/mm}}$$"
            )

        return "\n\n".join(parts)

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
            "$$C = \\frac{P_e}{P} = " f"\\frac{{{pe_mm:.2f}}}{{{p_mm:.2f}}} = {c:.3f}$$"
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
