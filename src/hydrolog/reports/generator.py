"""Main report generator for hydrological calculations.

This module provides the HydrologyReportGenerator class that combines
all section generators to produce complete calculation reports.
"""

import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import hydrolog
from hydrolog.exceptions import InvalidParameterError
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
from hydrolog.runoff.clark_iuh import ClarkUHResult
from hydrolog.runoff.generator import HydrographGeneratorResult
from hydrolog.runoff.nash_iuh import NashUHResult
from hydrolog.runoff.snyder_uh import SnyderUHResult
from hydrolog.runoff.unit_hydrograph import UnitHydrographResult
from hydrolog.time import ConcentrationTime

_DEFAULT_IA_COEFFICIENT = 0.2

# Keys of ``watershed_params`` that are inputs of a time of concentration formula
# (FAA, Kerby, Kerby-Kirpich), not rows of the watershed section.
_TC_ONLY_PARAMS = frozenset(
    {"runoff_coeff", "retardance", "overland_length_km", "overland_slope_m_per_m"}
)


@dataclass
class ReportConfig:
    """
    Configuration for report generation.

    Parameters
    ----------
    tc_method : str, optional
        Time of concentration method ("kirpich", "nrcs", "giandotti",
        "faa", "kerby", "kerby_kirpich"), by default "kirpich".
    uh_model : str, optional
        Unit hydrograph model ("scs", "nash", "clark", "snyder"),
        by default "scs". The report documents the model of the unit
        hydrograph of the result; a warning is issued when that is another one.
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

    def __init__(self, config: ReportConfig | None = None) -> None:
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
        output_path: str | Path | None = None,
        area_km2: float | None = None,
        cn_ii: int | None = None,
        amc: str = "II",
        tc_min: float | None = None,
        tc_method: str | None = None,
        watershed_params: dict[str, Any] | None = None,
        uh_params: dict[str, Any] | None = None,
        figures_dir: str | None = None,
        ia_coefficient: float | None = None,
        tc_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate complete hydrological report.

        The report documents the computation that produced ``result``: the unit
        hydrograph section shows the unit hydrograph the result was computed
        with (``result.unit_hydrograph_result``: its model, parameters and
        ordinates), the initial abstraction formula uses the coefficient of the
        computation and the time of concentration section the inputs of the
        method.

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
            Watershed parameters. The keys of ``generate_watershed_section``
            fill the watershed section (the area and the CN are passed
            separately); ``runoff_coeff``, ``retardance``,
            ``overland_length_km`` and ``overland_slope_m_per_m`` are inputs of
            the FAA, Kerby and Kerby-Kirpich formulas of the time of
            concentration section.
        uh_params : dict, optional
            Details of the unit hydrograph model that its result does not
            carry: Snyder ``L_km`` and ``Lc_km``, Nash ``estimation_method`` and
            the inputs of that estimation. The parameters of the model itself
            (Nash n and K, Clark R and tc, Snyder Ct and Cp, the SCS lag time)
            are those of the unit hydrograph of ``result``.
        figures_dir : str, optional
            Directory containing figures to embed in report.
            Expected files: hietogram_beta.png, hydrogram_jednostkowy_nash.png,
            rainfall_runoff.png, bilans_wodny.png, generator_dashboard.png.
        ia_coefficient : float, optional
            Initial abstraction coefficient λ (Ia = λ·S) of the computation. If
            None, it is read back from ``result`` (Ia / S; 0.2 when the
            retention is zero).
        tc_params : dict, optional
            Inputs of the time of concentration formula exactly as the
            computation used them, under the names of the arguments of
            ``generate_tc_section`` (``length_km``, ``slope_m_per_m``,
            ``slope_percent``, ``area_km2``, ``elevation_diff_m``, ``cn``,
            ``runoff_coeff``, ``retardance``, ``overland_length_km``, ...). If
            None, they are extracted from ``watershed_params`` by the rules of
            ``WatershedParameters.calculate_tc``: length = channel length, else
            watershed length; slope = channel slope, else mean slope, else
            relief over length.

        Returns
        -------
        str
            Complete report content in Markdown format.

        Raises
        ------
        InvalidParameterError
            If ``result`` carries no unit hydrograph
            (``result.unit_hydrograph_result`` is None).

        Warns
        -----
        UserWarning
            If ``ReportConfig.hietogram_type`` is not a known type or
            ``ReportConfig.uh_model`` is not the model of the unit hydrograph
            of ``result``.
        """
        unit = result.unit_hydrograph_result
        if unit is None:
            raise InvalidParameterError(
                "result.unit_hydrograph_result is missing: the report documents "
                "the unit hydrograph the hydrograph was computed with",
                details={"option": "result", "reason": "no_unit_hydrograph"},
                hint="Pass the result of HydrographGenerator.generate().",
            )

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

        # Validate hietogram_type against known types
        _VALID_HIETOGRAM_TYPES = {"block", "triangular", "beta", "euler_ii"}
        if self.config.hietogram_type not in _VALID_HIETOGRAM_TYPES:
            warnings.warn(
                f"ReportConfig.hietogram_type='{self.config.hietogram_type}' "
                f"is not one of {sorted(_VALID_HIETOGRAM_TYPES)}. "
                f"Report may contain incorrect distribution labels.",
                UserWarning,
                stacklevel=2,
            )

        # The model is the one of the unit hydrograph that was actually used
        uh_model = _unit_hydrograph_model(unit, self.config.uh_model)
        if uh_model != self.config.uh_model:
            warnings.warn(
                f"ReportConfig.uh_model='{self.config.uh_model}' is not the model "
                f"of the unit hydrograph of the result ('{uh_model}'); the report "
                f"documents '{uh_model}'.",
                UserWarning,
                stacklevel=2,
            )

        # Build report sections
        sections = []

        # Header
        sections.append(self._build_header(watershed_name))

        # 1. Watershed parameters
        section_params = {
            key: value
            for key, value in (watershed_params or {}).items()
            if key not in _TC_ONLY_PARAMS
        }
        if section_params:
            sections.append(
                self._build_watershed_section(
                    area_km2=area_km2,
                    cn=cn_ii,
                    **section_params,
                )
            )

        # 2. Time of concentration
        if tc_min is not None:
            sections.append(
                self._build_tc_section(
                    tc_min=tc_min,
                    method=tc_method,
                    cn=cn_ii,
                    area_km2=area_km2,
                    watershed_params=watershed_params,
                    tc_params=tc_params,
                )
            )

        # 3. Hietogram
        sections.append(self._build_hietogram_section(hietogram))

        # 4. SCS-CN Effective Precipitation
        sections.append(
            self._build_scs_cn_section(
                result=result,
                hietogram=hietogram,
                cn_ii=cn_ii,
                amc=amc,
                ia_coefficient=self._initial_abstraction_coefficient(
                    result, ia_coefficient
                ),
            )
        )

        # 5. Unit Hydrograph
        sections.append(
            self._build_uh_section(
                result=result,
                unit=unit,
                model=uh_model,
                area_km2=area_km2,
                tc_min=tc_min,
                uh_params=uh_params,
            )
        )

        # 6. Convolution
        sections.append(
            self._build_convolution_section(
                result, hietogram, n_uh_steps=len(unit.ordinates_m3s)
            )
        )

        # 7. Hydrograph Results
        sections.append(self._build_hydrograph_section(result))

        # 8. Water Balance
        sections.append(
            generate_water_balance_section(
                total_precip_mm=result.total_precip_mm,
                initial_abstraction_mm=result.initial_abstraction_mm,
                retention_mm=result.retention_mm,
                total_effective_mm=result.total_effective_mm,
                runoff_coefficient=result.runoff_coefficient,
                total_volume_m3=result.total_volume_m3,
                area_km2=area_km2,
                include_formulas=self.config.include_formulas,
            )
        )

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
        cn: int | None = None,
        **kwargs: Any,
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
        ia_coefficient: float,
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
            ia_coefficient=ia_coefficient,
            times_min=hietogram.times_min,
            precip_mm=hietogram.intensities_mm,
            effective_mm=result.effective_precip_mm,
            include_formulas=self.config.include_formulas,
            include_table=self.config.include_tables,
            max_table_rows=self.config.max_table_rows,
        )

    @staticmethod
    def _initial_abstraction_coefficient(
        result: HydrographGeneratorResult, ia_coefficient: float | None
    ) -> float:
        """Coefficient λ of Ia = λ S: the given one, else read back from ``result``."""
        if ia_coefficient is not None:
            return ia_coefficient
        if result.retention_mm > 0:
            return round(result.initial_abstraction_mm / result.retention_mm, 10)
        return _DEFAULT_IA_COEFFICIENT

    def _build_uh_section(
        self,
        result: HydrographGeneratorResult,
        unit: Any,
        model: str,
        area_km2: float,
        tc_min: float | None,
        uh_params: dict[str, Any] | None,
    ) -> str:
        """Build unit hydrograph section from the unit hydrograph of the result.

        Ordinates, time to peak, peak discharge and the model parameters are
        those of ``unit`` (``result.unit_hydrograph_result``); ``uh_params`` only
        adds what that result does not carry.
        """
        timestep_min = result.hydrograph.timestep_min
        params: dict[str, Any] = dict(uh_params or {})
        section_tc_min = tc_min
        tp_min = unit.time_to_peak_min
        qp_m3s = unit.peak_discharge_m3s
        duration_min = getattr(unit, "duration_min", timestep_min)

        if isinstance(unit, UnitHydrographResult):
            params.update(
                lag_time_min=unit.lag_time_min, time_base_min=unit.time_base_min
            )
            duration_min = unit.timestep_min
        elif isinstance(unit, NashUHResult):
            params.update(n=unit.n, k_min=unit.k_min)
        elif isinstance(unit, ClarkUHResult):
            params.update(
                r_min=unit.r_min, tc_min=unit.tc_min, timestep_min=timestep_min
            )
            section_tc_min = unit.tc_min
        elif isinstance(unit, SnyderUHResult):
            # The section explains the standard-duration formulas; tpR and qpR are
            # the adjusted values for the duration that was used
            lag_h = unit.lag_time_min / 60.0
            adjusted_lag_h = unit.adjusted_lag_time_min / 60.0
            params.update(
                lag_time_min=unit.lag_time_min,
                standard_duration_min=unit.standard_duration_min,
                ct=unit.ct,
                cp=unit.cp,
                duration_min=unit.duration_min,
                adjusted_lag_time_min=unit.adjusted_lag_time_min,
                adjusted_tp_min=unit.time_to_peak_min,
                adjusted_qp_m3s=0.275 * unit.cp * unit.area_km2 / adjusted_lag_h,
            )
            tp_min = unit.lag_time_min + unit.standard_duration_min / 2.0
            qp_m3s = 0.275 * unit.cp * unit.area_km2 / lag_h

        return generate_uh_section(
            model=model,
            area_km2=area_km2,
            times_min=unit.times_min,
            ordinates_m3s=unit.ordinates_m3s,
            time_to_peak_min=tp_min,
            peak_discharge_m3s=qp_m3s,
            model_params=params,
            tc_min=section_tc_min,
            duration_min=duration_min,
            include_formulas=self.config.include_formulas,
            include_table=self.config.include_tables,
            max_table_rows=self.config.max_table_rows,
        )

    def _build_tc_section(
        self,
        tc_min: float,
        method: str,
        cn: int,
        area_km2: float,
        watershed_params: dict[str, Any] | None,
        tc_params: dict[str, Any] | None,
    ) -> str:
        """Build time of concentration section with the inputs of the method."""
        inputs = (
            dict(tc_params)
            if tc_params is not None
            else self._extract_tc_params(watershed_params, method, area_km2)
        )
        section_inputs: dict[str, Any] = {"cn": cn, **inputs}
        if method.lower() == "kerby_kirpich":
            self._add_kerby_kirpich_components(section_inputs, tc_min)
        return generate_tc_section(
            tc_min=tc_min,
            method=method,
            include_formulas=self.config.include_formulas,
            **section_inputs,
        )

    @staticmethod
    def _add_kerby_kirpich_components(inputs: dict[str, Any], tc_min: float) -> None:
        """Add the two components of the composite method when they are missing.

        ``tc = t_overland + t_channel``: the Kerby overland time follows from the
        inputs and the channel time is what is left of ``tc_min``, so the
        components always add up to the time of concentration of the report.
        """
        if "tc_overland_min" in inputs or "tc_channel_min" in inputs:
            return
        needed = ("overland_length_km", "overland_slope_m_per_m", "retardance")
        if any(inputs.get(name) is None for name in needed):
            return
        with warnings.catch_warnings():
            # the range warnings were issued by the computation itself
            warnings.simplefilter("ignore")
            overland_min = ConcentrationTime.kerby(
                length_km=inputs["overland_length_km"],
                slope_m_per_m=inputs["overland_slope_m_per_m"],
                retardance=inputs["retardance"],
            )
        inputs["tc_overland_min"] = overland_min
        inputs["tc_channel_min"] = tc_min - overland_min

    def _build_convolution_section(
        self,
        result: HydrographGeneratorResult,
        hietogram: HietogramResult,
        n_uh_steps: int,
    ) -> str:
        """Build convolution section."""
        n_precip = len(result.effective_precip_mm)
        n_result = len(result.hydrograph.times_min)

        return generate_convolution_section(
            n_precip_steps=n_precip,
            n_uh_steps=n_uh_steps,
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
            lines.extend(
                [
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
                ]
            )

        return "\n".join(lines)

    def _estimate_area(self, result: HydrographGeneratorResult) -> float:
        """Estimate watershed area from result data."""
        # V = Pe * A * 1000 (mm * km² * 1000 = m³)
        if result.total_effective_mm > 0:
            return result.total_volume_m3 / (result.total_effective_mm * 1000)
        return 1.0

    def _extract_tc_params(
        self,
        watershed_params: dict[str, Any] | None,
        method: str,
        area_km2: float,
    ) -> dict[str, Any]:
        """Derive inputs of the ``method`` formula from watershed parameters.

        Applies the rules of ``WatershedParameters.calculate_tc``: the length is
        the channel length, else the watershed length; the slope is the channel
        slope, else the mean slope, else the relief over the length (NRCS takes
        the mean slope of the watershed first: Y of TR-55 is the average land
        slope); FAA and Kerby time the overland flow, so they take
        ``overland_length_km`` and ``overland_slope_m_per_m``, never the channel.
        """
        if watershed_params is None:
            return {}
        values = watershed_params
        length_km = values.get("channel_length_km") or values.get("length_km")
        slope = _slope_m_per_m(values, length_km)

        if method == "kirpich":
            return _present(length_km=length_km, slope_m_per_m=slope)
        if method == "nrcs":
            land_slope = _slope_m_per_m(values, length_km, land_first=True)
            return _present(
                length_km=length_km,
                slope_percent=None if land_slope is None else land_slope * 100.0,
            )
        if method == "giandotti":
            return _present(
                area_km2=area_km2,
                length_km=length_km,
                elevation_diff_m=_mean_elevation_above_outlet_m(values),
            )
        if method == "faa":
            return _present(
                length_km=values.get("overland_length_km"),
                slope_m_per_m=values.get("overland_slope_m_per_m"),
                runoff_coeff=values.get("runoff_coeff"),
            )
        if method == "kerby":
            return _present(
                length_km=values.get("overland_length_km"),
                slope_m_per_m=values.get("overland_slope_m_per_m"),
                retardance=values.get("retardance"),
            )
        if method == "kerby_kirpich":
            return _present(
                overland_length_km=values.get("overland_length_km"),
                overland_slope_m_per_m=values.get("overland_slope_m_per_m"),
                retardance=values.get("retardance"),
                channel_length_km=values.get("channel_length_km"),
                channel_slope_m_per_m=values.get("channel_slope_m_per_m"),
            )
        return {}

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
                lines.extend(
                    [
                        f"### {description}",
                        "",
                        f"![{description}]({filename})",
                        "",
                    ]
                )

        return "\n".join(lines)

    def _save(self, content: str, path: str | Path) -> None:
        """Save report to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _unit_hydrograph_model(unit: Any, default: str) -> str:
    """Return the name of the model a unit hydrograph result belongs to.

    The name is ``default`` if the model is unknown.
    """
    if isinstance(unit, UnitHydrographResult):
        return "scs"
    if isinstance(unit, NashUHResult):
        return "nash"
    if isinstance(unit, ClarkUHResult):
        return "clark"
    if isinstance(unit, SnyderUHResult):
        return "snyder"
    return default


def _present(**values: Any) -> dict[str, Any]:
    """Return the given values that are not None."""
    return {name: value for name, value in values.items() if value is not None}


def _slope_m_per_m(
    values: dict[str, Any], length_km: float | None, land_first: bool = False
) -> float | None:
    """Slope a time of concentration method is fed with (``calculate_tc`` rule).

    The channel slope, else the mean slope, else the relief over the length; with
    ``land_first`` (NRCS) the mean slope of the watershed comes before the channel
    slope.
    """
    channel = values.get("channel_slope_m_per_m")
    mean = values.get("mean_slope_percent")
    mean = None if mean is None else float(mean) / 100.0
    for slope in (mean, channel) if land_first else (channel, mean):
        if slope is not None:
            return float(slope)
    relief_m = values.get("relief_m")
    if (
        relief_m is None
        and values.get("elevation_min_m") is not None
        and values.get("elevation_max_m") is not None
    ):
        relief_m = values["elevation_max_m"] - values["elevation_min_m"]
    if relief_m is not None and length_km:
        return float(relief_m) / (length_km * 1000.0)
    return None


def _mean_elevation_above_outlet_m(values: dict[str, Any]) -> float | None:
    """Elevation difference of the Giandotti formula (``calculate_tc`` rule).

    Mean elevation minus the outlet elevation; the mean elevation defaults to the
    middle of the elevation range.
    """
    outlet_m = values.get("elevation_min_m")
    if outlet_m is None:
        return None
    mean_m = values.get("elevation_mean_m")
    if mean_m is None:
        top_m = values.get("elevation_max_m")
        if top_m is None:
            return None
        mean_m = (outlet_m + top_m) / 2.0
    return float(mean_m - outlet_m)
