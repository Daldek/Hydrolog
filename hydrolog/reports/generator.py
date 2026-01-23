"""Main report generator for hydrological calculations.

This module provides the HydrologyReportGenerator class that combines
all section generators to produce complete calculation reports.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
from numpy.typing import NDArray

import hydrolog
from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.reports.formatters import TableGenerator
from hydrolog.reports.sections.concentration import generate_tc_section
from hydrolog.reports.sections.convolution import generate_convolution_section
from hydrolog.reports.sections.hietogram import generate_hietogram_section
from hydrolog.reports.sections.scs_cn import generate_scs_cn_section
from hydrolog.reports.sections.unit_hydrograph import generate_uh_section
from hydrolog.reports.sections.water_balance import generate_water_balance_section
from hydrolog.reports.sections.watershed import generate_watershed_section
from hydrolog.reports.templates import REPORT_HEADER_TEMPLATE, SECTION_HEADERS
from hydrolog.runoff.generator import HydrographGeneratorResult


@dataclass
class ReportConfig:
    """
    Configuration for report generation.

    Parameters
    ----------
    tc_method : str, optional
        Time of concentration method ("kirpich", "nrcs", "giandotti"),
        by default "kirpich".
    uh_model : str, optional
        Unit hydrograph model ("scs", "nash", "clark", "snyder"),
        by default "scs".
    hietogram_type : str, optional
        Hietogram distribution type ("beta", "block", "triangular", "euler_ii"),
        by default "beta".
    include_formulas : bool, optional
        Include detailed formulas in the report, by default True.
    include_tables : bool, optional
        Include data tables in the report, by default True.
    max_table_rows : int, optional
        Maximum rows in tables before abbreviation, by default 50.
    language : str, optional
        Report language (currently only "pl" supported), by default "pl".
    """

    tc_method: str = "kirpich"
    uh_model: str = "scs"
    hietogram_type: str = "beta"
    include_formulas: bool = True
    include_tables: bool = True
    max_table_rows: int = 50
    language: str = "pl"


class HydrologyReportGenerator:
    """
    Generate comprehensive hydrological calculation reports.

    This class combines all section generators to produce complete
    Markdown reports documenting the entire calculation procedure
    from watershed parameters to final hydrograph.

    Parameters
    ----------
    config : ReportConfig, optional
        Report configuration. If not provided, uses defaults.

    Examples
    --------
    >>> from hydrolog.reports import HydrologyReportGenerator
    >>> from hydrolog.runoff import HydrographGenerator
    >>> from hydrolog.precipitation import BetaHietogram
    >>>
    >>> # Generate hydrograph
    >>> hietogram = BetaHietogram(alpha=2, beta=5)
    >>> precip = hietogram.generate(total_mm=50, duration_min=120, timestep_min=10)
    >>> generator = HydrographGenerator(area_km2=45, cn=72, tc_min=90)
    >>> result = generator.generate(precip)
    >>>
    >>> # Generate report
    >>> report = HydrologyReportGenerator()
    >>> content = report.generate(
    ...     result=result,
    ...     hietogram=precip,
    ...     watershed_name="Zlewnia Testowa",
    ...     output_path="raport.md"
    ... )
    """

    def __init__(self, config: Optional[ReportConfig] = None) -> None:
        """
        Initialize report generator.

        Parameters
        ----------
        config : ReportConfig, optional
            Report configuration.
        """
        self.config = config or ReportConfig()

    def generate(
        self,
        result: HydrographGeneratorResult,
        hietogram: HietogramResult,
        watershed_name: str = "Zlewnia",
        output_path: Optional[Union[str, Path]] = None,
        area_km2: Optional[float] = None,
        cn_ii: Optional[int] = None,
        amc: str = "II",
        tc_min: Optional[float] = None,
        tc_method: Optional[str] = None,
        watershed_params: Optional[Dict[str, Any]] = None,
        uh_params: Optional[Dict[str, Any]] = None,
        figures_dir: Optional[str] = None,
    ) -> str:
        """
        Generate complete hydrological report.

        Parameters
        ----------
        result : HydrographGeneratorResult
            Result from HydrographGenerator.generate().
        hietogram : HietogramResult
            Precipitation hietogram.
        watershed_name : str, optional
            Name of the watershed, by default "Zlewnia".
        output_path : str or Path, optional
            Path to save the report. If None, only returns content.
        area_km2 : float, optional
            Watershed area [km²]. If None, inferred from result.
        cn_ii : int, optional
            Original CN for AMC-II. If None, uses result.cn_used.
        amc : str, optional
            AMC condition used ("I", "II", "III"), by default "II".
        tc_min : float, optional
            Time of concentration [min].
        tc_method : str, optional
            Concentration time method used.
        watershed_params : dict, optional
            Additional watershed parameters for detailed section.
        uh_params : dict, optional
            Unit hydrograph model parameters.
        figures_dir : str, optional
            Directory containing figures to embed in report.
            Expected files: hietogram_beta.png, hydrogram_jednostkowy_nash.png,
            rainfall_runoff.png, bilans_wodny.png, generator_dashboard.png.

        Returns
        -------
        str
            Complete report content in Markdown format.
        """
        # Determine area
        if area_km2 is None:
            # Try to estimate from hydrograph volume
            area_km2 = self._estimate_area(result)

        # Determine CN
        if cn_ii is None:
            cn_ii = result.cn_used

        # Use config defaults if not specified
        if tc_method is None:
            tc_method = self.config.tc_method

        # Build report sections
        sections = []

        # Header
        sections.append(self._build_header(watershed_name))

        # 1. Watershed parameters
        if watershed_params:
            sections.append(self._build_watershed_section(
                area_km2=area_km2,
                cn=cn_ii,
                **watershed_params,
            ))

        # 2. Time of concentration
        if tc_min is not None:
            tc_params = self._extract_tc_params(watershed_params, tc_method)
            sections.append(generate_tc_section(
                tc_min=tc_min,
                method=tc_method,
                cn=cn_ii,
                include_formulas=self.config.include_formulas,
                **tc_params,
            ))

        # 3. Hietogram
        sections.append(self._build_hietogram_section(hietogram))

        # 4. SCS-CN Effective Precipitation
        sections.append(self._build_scs_cn_section(
            result=result,
            hietogram=hietogram,
            cn_ii=cn_ii,
            amc=amc,
        ))

        # 5. Unit Hydrograph
        sections.append(self._build_uh_section(
            result=result,
            area_km2=area_km2,
            tc_min=tc_min,
            hietogram=hietogram,
            uh_params=uh_params,
        ))

        # 6. Convolution
        sections.append(self._build_convolution_section(result, hietogram))

        # 7. Hydrograph Results
        sections.append(self._build_hydrograph_section(result))

        # 8. Water Balance
        sections.append(generate_water_balance_section(
            total_precip_mm=result.total_precip_mm,
            initial_abstraction_mm=result.initial_abstraction_mm,
            retention_mm=result.retention_mm,
            total_effective_mm=result.total_effective_mm,
            runoff_coefficient=result.runoff_coefficient,
            total_volume_m3=result.total_volume_m3,
            area_km2=area_km2,
            include_formulas=self.config.include_formulas,
        ))

        # 9. Figures (if directory provided)
        if figures_dir:
            sections.append(self._build_figures_section(figures_dir))

        # Combine sections
        content = "\n\n".join(sections)

        # Save if path provided
        if output_path is not None:
            self._save(content, output_path)

        return content

    def _build_header(self, watershed_name: str) -> str:
        """Build report header."""
        return REPORT_HEADER_TEMPLATE.format(
            name=watershed_name,
            date=date.today().isoformat(),
            version=hydrolog.__version__,
        )

    def _build_watershed_section(
        self,
        area_km2: float,
        cn: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Build watershed parameters section."""
        return generate_watershed_section(
            area_km2=area_km2,
            cn=cn,
            include_shape_indicators=self.config.include_tables,
            **kwargs,
        )

    def _build_hietogram_section(self, hietogram: HietogramResult) -> str:
        """Build hietogram section."""
        return generate_hietogram_section(
            total_mm=hietogram.total_mm,
            duration_min=hietogram.duration_min,
            timestep_min=hietogram.timestep_min,
            times_min=hietogram.times_min,
            intensities_mm=hietogram.intensities_mm,
            distribution=self.config.hietogram_type,
            include_table=self.config.include_tables,
            max_table_rows=self.config.max_table_rows,
        )

    def _build_scs_cn_section(
        self,
        result: HydrographGeneratorResult,
        hietogram: HietogramResult,
        cn_ii: int,
        amc: str,
    ) -> str:
        """Build SCS-CN section."""
        return generate_scs_cn_section(
            total_precip_mm=result.total_precip_mm,
            cn_ii=cn_ii,
            cn_adjusted=result.cn_used,
            amc=amc,
            retention_mm=result.retention_mm,
            initial_abstraction_mm=result.initial_abstraction_mm,
            total_effective_mm=result.total_effective_mm,
            times_min=hietogram.times_min,
            precip_mm=hietogram.intensities_mm,
            effective_mm=result.effective_precip_mm,
            include_formulas=self.config.include_formulas,
            include_table=self.config.include_tables,
            max_table_rows=self.config.max_table_rows,
        )

    def _build_uh_section(
        self,
        result: HydrographGeneratorResult,
        area_km2: float,
        tc_min: Optional[float],
        hietogram: HietogramResult,
        uh_params: Optional[Dict[str, Any]],
    ) -> str:
        """Build unit hydrograph section."""
        # Extract UH characteristics from result
        hydrograph = result.hydrograph
        timestep = hydrograph.timestep_min

        # Generate UH ordinates (simplified - in real case would need access to UH)
        # For now, we'll use placeholder values
        n_steps = int(result.hydrograph.time_to_peak_min / timestep * 3)
        times = np.arange(0, n_steps * timestep, timestep)

        # Estimate UH parameters based on model
        model = self.config.uh_model
        model_params = uh_params or {}

        # For SCS model, estimate peak discharge
        if model == "scs" and tc_min:
            tlag = 0.6 * tc_min
            tp = hietogram.timestep_min / 2 + tlag
            tp_h = tp / 60
            qp = 0.208 * area_km2 / tp_h
            model_params.setdefault("lag_time_min", tlag)
            model_params.setdefault("time_base_min", 5 * tp)
        elif model == "nash":
            model_params.setdefault("n", 3.0)
            model_params.setdefault("k_min", 30.0)
        elif model == "clark":
            model_params.setdefault("r_min", 30.0)
            model_params.setdefault("tc_min", tc_min or 60.0)
        elif model == "snyder":
            model_params.setdefault("L_km", 10.0)
            model_params.setdefault("Lc_km", 5.0)
            model_params.setdefault("ct", 1.5)
            model_params.setdefault("cp", 0.6)

        # Create placeholder ordinates (triangular shape)
        # In real implementation, these would come from the actual UH generation
        n_ord = max(20, int(n_steps / 2))
        uh_times = np.linspace(0, n_ord * timestep, n_ord)

        # Estimate peak parameters
        if model == "scs" and tc_min:
            tp_min = hietogram.timestep_min / 2 + 0.6 * tc_min
            tp_h = tp_min / 60
            qp_m3s = 0.208 * area_km2 / tp_h
        else:
            tp_min = result.hydrograph.time_to_peak_min * 0.7
            qp_m3s = result.hydrograph.peak_discharge_m3s / max(result.effective_precip_mm)

        # Generate simplified UH shape
        uh_ordinates = self._generate_uh_shape(uh_times, tp_min, qp_m3s)

        return generate_uh_section(
            model=model,
            area_km2=area_km2,
            times_min=uh_times,
            ordinates_m3s=uh_ordinates,
            time_to_peak_min=tp_min,
            peak_discharge_m3s=qp_m3s,
            model_params=model_params,
            tc_min=tc_min,
            duration_min=hietogram.timestep_min,
            include_formulas=self.config.include_formulas,
            include_table=self.config.include_tables,
            max_table_rows=self.config.max_table_rows,
        )

    def _build_convolution_section(
        self,
        result: HydrographGeneratorResult,
        hietogram: HietogramResult,
    ) -> str:
        """Build convolution section."""
        n_precip = len(result.effective_precip_mm)
        n_result = len(result.hydrograph.times_min)
        # Estimate UH length: result = precip + uh - 1
        n_uh = n_result - n_precip + 1

        return generate_convolution_section(
            n_precip_steps=n_precip,
            n_uh_steps=max(n_uh, 1),
            n_result_steps=n_result,
            timestep_min=hietogram.timestep_min,
            include_formulas=self.config.include_formulas,
        )

    def _build_hydrograph_section(self, result: HydrographGeneratorResult) -> str:
        """Build hydrograph results section."""
        hydrograph = result.hydrograph

        lines = [
            SECTION_HEADERS["hydrograph"],
            "",
            "Poniżej przedstawiono charakterystyki obliczonego hydrogramu "
            "odpływu bezpośredniego.",
            "",
            "### 7.1 Charakterystyki",
            "",
            TableGenerator.hydrograph_results_table(
                peak_discharge=hydrograph.peak_discharge_m3s,
                time_to_peak=hydrograph.time_to_peak_min,
                volume=hydrograph.total_volume_m3,
            ),
        ]

        if self.config.include_tables:
            lines.extend([
                "",
                "### 7.2 Szereg czasowy",
                "",
                TableGenerator.time_series_table(
                    times=hydrograph.times_min,
                    values=hydrograph.discharge_m3s,
                    time_header="Czas [min]",
                    value_header="Q [m³/s]",
                    max_rows=self.config.max_table_rows,
                ),
            ])

        return "\n".join(lines)

    def _estimate_area(self, result: HydrographGeneratorResult) -> float:
        """Estimate watershed area from result data."""
        # V = Pe * A * 1000 (mm * km² * 1000 = m³)
        if result.total_effective_mm > 0:
            return result.total_volume_m3 / (result.total_effective_mm * 1000)
        return 1.0

    def _extract_tc_params(
        self,
        watershed_params: Optional[Dict[str, Any]],
        method: str,
    ) -> Dict[str, Any]:
        """Extract parameters needed for tc calculation."""
        params = {}
        if watershed_params is None:
            return params

        if method == "kirpich":
            if "channel_length_km" in watershed_params:
                params["length_km"] = watershed_params["channel_length_km"]
            elif "length_km" in watershed_params:
                params["length_km"] = watershed_params["length_km"]
            if "channel_slope_m_per_m" in watershed_params:
                params["slope_m_per_m"] = watershed_params["channel_slope_m_per_m"]

        elif method == "nrcs":
            if "channel_length_km" in watershed_params:
                params["length_km"] = watershed_params["channel_length_km"]
            if "mean_slope_percent" in watershed_params:
                params["slope_percent"] = watershed_params["mean_slope_percent"]

        elif method == "giandotti":
            if "area_km2" in watershed_params:
                params["area_km2"] = watershed_params["area_km2"]
            if "channel_length_km" in watershed_params:
                params["length_km"] = watershed_params["channel_length_km"]
            elif "length_km" in watershed_params:
                params["length_km"] = watershed_params["length_km"]
            if "elevation_max_m" in watershed_params and "elevation_min_m" in watershed_params:
                params["elevation_diff_m"] = (
                    watershed_params["elevation_max_m"] - watershed_params["elevation_min_m"]
                )

        return params

    def _generate_uh_shape(
        self,
        times: NDArray[np.float64],
        tp_min: float,
        qp_m3s: float,
    ) -> NDArray[np.float64]:
        """Generate simplified triangular UH shape."""
        ordinates = np.zeros_like(times)
        for i, t in enumerate(times):
            if t <= tp_min:
                ordinates[i] = qp_m3s * t / tp_min
            else:
                # Recession
                tb = 5 * tp_min  # Time base
                if t < tb:
                    ordinates[i] = qp_m3s * (1 - (t - tp_min) / (tb - tp_min))
                else:
                    ordinates[i] = 0
        return ordinates

    def _build_figures_section(self, figures_dir: str) -> str:
        """Build figures section with embedded images."""
        figures_path = Path(figures_dir)

        # Define expected figures with Polish descriptions
        figures = [
            ("hietogram_beta.png", "Hietogram opadu"),
            ("hydrogram_jednostkowy_nash.png", "Hydrogram jednostkowy Nasha"),
            ("rainfall_runoff.png", "Transformacja opad-odpływ"),
            ("bilans_wodny.png", "Bilans wodny SCS-CN"),
            ("generator_dashboard.png", "Podsumowanie analizy hydrologicznej"),
        ]

        lines = [
            "## 9. Wykresy",
            "",
            "Poniżej przedstawiono wykresy dokumentujące przebieg obliczeń.",
            "",
        ]

        for filename, description in figures:
            filepath = figures_path / filename
            if filepath.exists():
                lines.extend([
                    f"### {description}",
                    "",
                    f"![{description}]({filename})",
                    "",
                ])

        return "\n".join(lines)

    def _save(self, content: str, path: Union[str, Path]) -> None:
        """Save report to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
