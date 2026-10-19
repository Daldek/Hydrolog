"""Unit tests for the reports module."""

import dataclasses
import warnings

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BetaHietogram
from hydrolog.reports import (
    FormulaRenderer,
    HydrologyReportGenerator,
    ReportConfig,
    TableGenerator,
)
from hydrolog.reports.sections.concentration import generate_tc_section
from hydrolog.reports.sections.convolution import generate_convolution_section
from hydrolog.reports.sections.hietogram import generate_hietogram_section
from hydrolog.reports.sections.scs_cn import generate_scs_cn_section
from hydrolog.reports.sections.unit_hydrograph import generate_uh_section
from hydrolog.reports.sections.water_balance import generate_water_balance_section
from hydrolog.reports.sections.watershed import generate_watershed_section
from hydrolog.reports.templates import SUBSECTION_HEADERS
from hydrolog.runoff import HydrographGenerator
from hydrolog.time import ConcentrationTime

# =============================================================================
# FormulaRenderer Tests
# =============================================================================


class TestFormulaRenderer:
    """Tests for FormulaRenderer class."""

    def test_scs_retention_typical_cn(self):
        """Test SCS retention formula for typical CN."""
        result = FormulaRenderer.scs_retention(cn=72)

        assert "25400" in result
        assert "72" in result
        assert "98.78" in result  # S = 25400/72 - 254 = 98.78
        assert "$$" in result  # LaTeX delimiters

    def test_scs_retention_cn_100(self):
        """Test SCS retention formula for CN=100 (no retention)."""
        result = FormulaRenderer.scs_retention(cn=100)

        assert "0.00" in result

    def test_scs_initial_abstraction(self):
        """Test SCS initial abstraction formula."""
        result = FormulaRenderer.scs_initial_abstraction(s_mm=98.89, ia_coef=0.2)

        assert "98.89" in result
        assert "0.2" in result
        assert "19.78" in result  # Ia = 0.2 * 98.89
        assert "$$" in result

    def test_scs_effective_precipitation_p_greater_than_ia(self):
        """Test SCS effective precipitation formula when P > Ia."""
        result = FormulaRenderer.scs_effective_precipitation(
            p_mm=50.0,
            ia_mm=19.78,
            s_mm=98.89,
            pe_mm=7.09,
        )

        assert "50.00" in result
        assert "19.78" in result
        assert "98.89" in result
        assert "7.09" in result
        assert "$$" in result

    def test_scs_effective_precipitation_p_less_than_ia(self):
        """Test SCS effective precipitation formula when P <= Ia."""
        result = FormulaRenderer.scs_effective_precipitation(
            p_mm=10.0,
            ia_mm=19.78,
            s_mm=98.89,
            pe_mm=0.0,
        )

        assert "P_e = 0" in result
        assert "nie przekracza" in result

    def test_scs_amc_adjustment_amc_i(self):
        """Test AMC adjustment formula for dry conditions."""
        result = FormulaRenderer.scs_amc_adjustment(cn_ii=72, cn_adjusted=53, amc="I")

        assert "CN_I" in result
        assert "72" in result
        assert "53" in result
        assert "2.281" in result  # Formula coefficient

    def test_scs_amc_adjustment_amc_iii(self):
        """Test AMC adjustment formula for wet conditions."""
        result = FormulaRenderer.scs_amc_adjustment(cn_ii=72, cn_adjusted=86, amc="III")

        assert "CN_{III}" in result
        assert "72" in result
        assert "86" in result
        assert "0.427" in result  # Formula coefficient

    def test_kirpich_tc(self):
        """Test Kirpich formula rendering."""
        result = FormulaRenderer.kirpich_tc(
            length_km=8.2,
            slope_m_per_m=0.023,
            tc_min=85.9,
        )

        assert "0.0663" in result
        assert "8.2" in result or "8.20" in result
        assert "0.023" in result
        assert "85.9" in result
        assert "Kirpich" in result or "min" in result

    def test_nrcs_tc(self):
        """Test NRCS formula rendering."""
        result = FormulaRenderer.nrcs_tc(
            length_km=5.0,
            slope_percent=2.5,
            cn=72,
            tc_min=200.0,
        )

        assert "0.01416" in result
        assert "72" in result
        assert "200" in result

    def test_giandotti_tc(self):
        """Test Giandotti formula rendering."""
        result = FormulaRenderer.giandotti_tc(
            area_km2=100.0,
            length_km=15.0,
            elevation_diff_m=500.0,
            tc_min=179.7,
        )

        assert "100" in result
        assert "15" in result
        assert "500" in result

    def test_scs_uh_lag_time(self):
        """Test SCS lag time formula."""
        result = FormulaRenderer.scs_uh_lag_time(tc_min=100.0, tlag_min=60.0)

        assert "0.6" in result
        assert "100" in result
        assert "60" in result

    def test_scs_uh_peak_discharge(self):
        """Test SCS peak discharge formula."""
        result = FormulaRenderer.scs_uh_peak_discharge(
            area_km2=45.0,
            tp_min=60.0,
            qp_m3s=9.36,
        )

        assert "0.208" in result
        assert "45" in result
        assert "9.36" in result

    def test_convolution_formula(self):
        """Test convolution formula rendering."""
        result = FormulaRenderer.convolution_formula()

        assert "Q(n)" in result
        assert "P_e" in result
        assert "UH" in result
        assert "sum" in result or "Σ" in result

    def test_runoff_coefficient(self):
        """Test runoff coefficient formula."""
        result = FormulaRenderer.runoff_coefficient(pe_mm=7.09, p_mm=50.0, c=0.142)

        assert "7.09" in result
        assert "50.00" in result
        assert "0.142" in result

    def test_faa_tc(self):
        """Test FAA formula rendering."""
        result = FormulaRenderer.faa_tc(
            length_km=0.15,
            slope_m_per_m=0.02,
            runoff_coeff=0.6,
            tc_min=15.8,
        )

        assert "22.213" in result
        assert "0.15" in result or "0.150" in result
        assert "0.02" in result or "0.0200" in result
        assert "0.60" in result
        assert "15.8" in result
        assert "min" in result

    def test_kerby_tc(self):
        """Test Kerby formula rendering."""
        result = FormulaRenderer.kerby_tc(
            length_km=0.10,
            slope_m_per_m=0.008,
            retardance=0.40,
            tc_min=24.9,
        )

        assert "36.37" in result
        assert "0.10" in result or "0.100" in result
        assert "0.008" in result or "0.0080" in result
        assert "0.40" in result
        assert "24.9" in result
        assert "min" in result

    def test_kerby_kirpich_tc(self):
        """Test Kerby-Kirpich composite formula rendering."""
        result = FormulaRenderer.kerby_kirpich_tc(
            ov_length_km=0.25,
            ov_slope_m_per_m=0.008,
            retardance=0.40,
            ch_length_km=5.0,
            ch_slope_m_per_m=0.005,
            tc_ov_min=40.0,
            tc_ch_min=104.0,
            tc_total_min=144.0,
        )

        assert "Kerby-Kirpich" in result
        assert "Kerby" in result
        assert "Kirpich" in result
        assert "40.0" in result
        assert "104.0" in result
        assert "144.0" in result
        assert "0.25" in result or "0.250" in result
        assert "5.0" in result or "5.00" in result

    def test_kerby_tc_substitutes_the_slope_the_formula_used(self):
        """Below 0.002 m/m the library adds 0.0005: the report shows what it used.

        With the raw 0.0010 the substitution would not reproduce the time shown.
        """
        tc = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.001, retardance=0.4
        )

        result = FormulaRenderer.kerby_tc(
            length_km=0.10, slope_m_per_m=0.001, retardance=0.40, tc_min=tc
        )

        assert "0.0015^{-0.2335}" in result
        assert "0.0010 + 0.0005 = 0.0015" in result
        assert 36.37 * (0.10 * 0.40) ** 0.467 * 0.0015 ** (-0.2335) == pytest.approx(tc)

    def test_kerby_tc_without_adjustment_has_no_note(self):
        result = FormulaRenderer.kerby_tc(
            length_km=0.10, slope_m_per_m=0.002, retardance=0.40, tc_min=30.0
        )

        assert "0.0020^{-0.2335}" in result
        assert "korekt" not in result

    def test_kerby_kirpich_tc_substitutes_the_slopes_the_formulas_used(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # the slopes are below the typical range
            tc_ov = ConcentrationTime.kerby(0.25, 0.001, 0.4)
            tc = ConcentrationTime.kerby_kirpich(0.25, 0.001, 0.4, 5.0, 0.0015)

        result = FormulaRenderer.kerby_kirpich_tc(
            ov_length_km=0.25,
            ov_slope_m_per_m=0.001,
            retardance=0.40,
            ch_length_km=5.0,
            ch_slope_m_per_m=0.0015,
            tc_ov_min=tc_ov,
            tc_ch_min=tc - tc_ov,
            tc_total_min=tc,
        )

        assert "0.0015^{-0.2335}" in result  # overland: 0.001 + 0.0005
        assert "0.0020^{-0.385}" in result  # channel: 0.0015 + 0.0005
        channel_min = tc - tc_ov
        channel_h = 0.0663 * 5.0**0.77 * 0.0020 ** (-0.385)
        assert channel_h * 60.0 == pytest.approx(channel_min, rel=2e-3)
        assert f"{channel_min / 60:.3f} \\text{{ h}} = {channel_min:.1f}" in result


# =============================================================================
# TableGenerator Tests
# =============================================================================


class TestTableGenerator:
    """Tests for TableGenerator class."""

    def test_parameters_table(self):
        """Test parameters table generation."""
        data = [
            ("Powierzchnia", "45.30", "km²"),
            ("CN", "72", "-"),
        ]
        result = TableGenerator.parameters_table(data)

        assert "| Parametr |" in result
        assert "Powierzchnia" in result
        assert "45.30" in result
        assert "km²" in result
        assert "|:---" in result  # Left alignment marker

    def test_time_series_table_short(self):
        """Test time series table for short series."""
        times = np.array([0.0, 5.0, 10.0, 15.0, 20.0])
        values = np.array([0.0, 1.0, 2.5, 1.5, 0.5])

        result = TableGenerator.time_series_table(
            times=times,
            values=values,
            time_header="Czas [min]",
            value_header="Q [m³/s]",
            max_rows=10,
        )

        assert "| Czas [min] |" in result
        assert "| Q [m³/s] |" in result
        assert "| 10.0 |" in result
        assert "..." not in result  # Should not be abbreviated

    def test_time_series_table_long_abbreviated(self):
        """Test time series table abbreviation for long series."""
        times = np.arange(0, 500, 5.0)
        values = np.zeros(100)

        result = TableGenerator.time_series_table(
            times=times,
            values=values,
            max_rows=20,
        )

        assert "..." in result
        assert "skrócona" in result.lower() or "100" in result

    def test_precipitation_table_with_effective(self):
        """Test precipitation table with effective precipitation."""
        times = np.array([10.0, 20.0, 30.0])
        precip = np.array([5.0, 10.0, 5.0])
        effective = np.array([0.0, 2.0, 3.0])

        result = TableGenerator.precipitation_table(
            times=times,
            precip_mm=precip,
            effective_mm=effective,
            max_rows=10,
        )

        assert "P [mm]" in result
        assert "Pe [mm]" in result
        assert "kum" in result  # cumulative

    def test_water_balance_table(self):
        """Test water balance table generation."""
        result = TableGenerator.water_balance_table(
            total_precip_mm=50.0,
            initial_abstraction_mm=19.78,
            retention_mm=98.89,
            effective_mm=7.09,
        )

        assert "Opad całkowity" in result
        assert "50.00" in result
        assert "100.0" in result  # 100% for total
        assert "7.09" in result

    def test_hydrograph_results_table(self):
        """Test hydrograph results table."""
        result = TableGenerator.hydrograph_results_table(
            peak_discharge=12.5,
            time_to_peak=90.0,
            volume=45000,
        )

        assert "Qmax" in result
        assert "12.5" in result or "12.50" in result
        assert "90" in result
        assert "45" in result  # 45,000 or 45000


# =============================================================================
# Section Generator Tests
# =============================================================================


class TestSectionGenerators:
    """Tests for section generator functions."""

    def test_generate_watershed_section(self):
        """Test watershed section generation."""
        result = generate_watershed_section(
            area_km2=45.3,
            perimeter_km=32.1,
            length_km=12.5,
            cn=72,
        )

        assert "## 1. Parametry Zlewni" in result
        assert "45.3" in result or "45.30" in result
        assert "72" in result

    def test_generate_tc_section_kirpich(self):
        """Test tc section with Kirpich method."""
        result = generate_tc_section(
            tc_min=85.9,
            method="kirpich",
            length_km=8.2,
            slope_m_per_m=0.023,
        )

        assert "## 2. Czas Koncentracji" in result
        assert "Kirpich" in result
        assert "85.9" in result

    def test_generate_tc_section_faa(self):
        """Test tc section with FAA method."""
        result = generate_tc_section(
            tc_min=15.8,
            method="faa",
            length_km=0.15,
            slope_m_per_m=0.02,
            runoff_coeff=0.6,
        )

        assert "## 2. Czas Koncentracji" in result
        assert "FAA" in result
        assert "15.8" in result

    def test_generate_tc_section_kerby(self):
        """Test tc section with Kerby method."""
        result = generate_tc_section(
            tc_min=24.9,
            method="kerby",
            length_km=0.10,
            slope_m_per_m=0.008,
            retardance=0.40,
        )

        assert "## 2. Czas Koncentracji" in result
        assert "Kerby" in result
        assert "24.9" in result

    def test_generate_tc_section_kerby_kirpich(self):
        """Test tc section with Kerby-Kirpich method."""
        result = generate_tc_section(
            tc_min=144.0,
            method="kerby_kirpich",
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            retardance=0.40,
            channel_length_km=5.0,
            channel_slope_m_per_m=0.005,
            tc_overland_min=40.0,
            tc_channel_min=104.0,
        )

        assert "## 2. Czas Koncentracji" in result
        assert "Kerby-Kirpich" in result
        assert "144.0" in result

    def test_generate_tc_section_faa_fallback(self):
        """Test tc section with FAA method when params are missing."""
        result = generate_tc_section(
            tc_min=15.8,
            method="faa",
        )

        assert "## 2. Czas Koncentracji" in result
        assert "FAA" in result
        assert "brak danych" in result
        assert "15.8" in result

    def test_generate_hietogram_section(self):
        """Test hietogram section generation."""
        times = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        intensities = np.array([5.0, 10.0, 15.0, 10.0, 5.0, 5.0])

        result = generate_hietogram_section(
            total_mm=50.0,
            duration_min=60.0,
            timestep_min=10.0,
            times_min=times,
            intensities_mm=intensities,
            distribution="beta",
        )

        assert "## 3. Hietogram" in result
        assert "50.0" in result or "50.00" in result
        assert "Beta" in result

    def test_generate_scs_cn_section(self):
        """Test SCS-CN section generation."""
        times = np.array([10.0, 20.0, 30.0])
        precip = np.array([10.0, 20.0, 20.0])
        effective = np.array([0.0, 5.0, 10.0])

        result = generate_scs_cn_section(
            total_precip_mm=50.0,
            cn_ii=72,
            cn_adjusted=72,
            amc="II",
            retention_mm=98.89,
            initial_abstraction_mm=19.78,
            total_effective_mm=7.09,
            times_min=times,
            precip_mm=precip,
            effective_mm=effective,
        )

        assert "## 4. Opad Efektywny" in result
        assert "SCS-CN" in result
        assert "72" in result
        assert "98.89" in result

    def test_generate_uh_section_scs(self):
        """Test UH section for SCS model."""
        times = np.linspace(0, 300, 31)
        ordinates = np.sin(np.pi * times / 300) * 0.5

        result = generate_uh_section(
            model="scs",
            area_km2=45.0,
            times_min=times,
            ordinates_m3s=ordinates,
            time_to_peak_min=60.0,
            peak_discharge_m3s=9.36,
            tc_min=100.0,
            duration_min=10.0,
        )

        assert "## 5. Hydrogram Jednostkowy" in result
        assert "SCS" in result
        assert "45" in result

    def test_generate_uh_section_nash(self):
        """Test UH section for Nash model."""
        times = np.linspace(0, 300, 31)
        ordinates = np.exp(-times / 100) * 0.5

        result = generate_uh_section(
            model="nash",
            area_km2=45.0,
            times_min=times,
            ordinates_m3s=ordinates,
            time_to_peak_min=60.0,
            peak_discharge_m3s=8.5,
            model_params={"n": 3.0, "k_min": 30.0},
        )

        assert "Nash" in result
        assert "zbiorników" in result or "n =" in result

    def test_generate_convolution_section(self):
        """Test convolution section generation."""
        result = generate_convolution_section(
            n_precip_steps=12,
            n_uh_steps=30,
            n_result_steps=41,
            timestep_min=10.0,
        )

        assert "## 6. Splot" in result
        assert "12" in result
        assert "30" in result
        assert "41" in result

    def test_generate_water_balance_section(self):
        """Test water balance section generation."""
        result = generate_water_balance_section(
            total_precip_mm=50.0,
            initial_abstraction_mm=19.78,
            retention_mm=98.89,
            total_effective_mm=7.09,
            runoff_coefficient=0.142,
            total_volume_m3=321000,
            area_km2=45.0,
        )

        assert "## 8. Bilans Wodny" in result
        assert "50.00" in result
        assert "7.09" in result
        assert "0.142" in result

    def test_generate_scs_cn_section_none_retention(self):
        """Test SCS-CN section handles None retention gracefully."""
        result = generate_scs_cn_section(
            total_precip_mm=50.0,
            cn_ii=72,
            cn_adjusted=72,
            amc="II",
            retention_mm=None,  # type: ignore[arg-type]
            initial_abstraction_mm=None,  # type: ignore[arg-type]
            total_effective_mm=7.09,
            include_formulas=True,
        )

        assert "## 4. Opad Efektywny" in result
        assert "brak danych" in result
        assert "7.09" in result

    def test_generate_scs_cn_section_none_retention_summary(self):
        """Test SCS-CN summary table shows fallback for None values."""
        result = generate_scs_cn_section(
            total_precip_mm=50.0,
            cn_ii=72,
            cn_adjusted=72,
            amc="II",
            retention_mm=None,  # type: ignore[arg-type]
            initial_abstraction_mm=None,  # type: ignore[arg-type]
            total_effective_mm=7.09,
            include_formulas=False,
        )

        assert "brak danych" in result


# =============================================================================
# ReportConfig Tests
# =============================================================================


class TestReportConfig:
    """Tests for ReportConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ReportConfig()

        assert config.tc_method == "kirpich"
        assert config.uh_model == "scs"
        assert config.hietogram_type == "beta"
        assert config.include_formulas is True
        assert config.include_tables is True
        assert config.max_table_rows == 50
        assert config.language == "pl"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ReportConfig(
            tc_method="nrcs",
            uh_model="nash",
            include_formulas=False,
            max_table_rows=30,
        )

        assert config.tc_method == "nrcs"
        assert config.uh_model == "nash"
        assert config.include_formulas is False
        assert config.max_table_rows == 30

    def test_invalid_hietogram_type_warns(self):
        """Test that invalid hietogram_type emits a warning."""
        import warnings

        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=10.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip)

        config = ReportConfig(hietogram_type="invalid_type")
        report = HydrologyReportGenerator(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            report.generate(
                result=result,
                hietogram=precip,
                watershed_name="Test",
            )
            hietogram_warnings = [x for x in w if "hietogram_type" in str(x.message)]
            assert len(hietogram_warnings) == 1
            assert "invalid_type" in str(hietogram_warnings[0].message)


# =============================================================================
# HydrologyReportGenerator Tests
# =============================================================================


class TestHydrologyReportGenerator:
    """Tests for HydrologyReportGenerator class."""

    @pytest.fixture
    def sample_result(self):
        """Create sample HydrographGeneratorResult."""
        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=10.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip)

        return result, precip

    def test_generate_basic(self, sample_result):
        """Test basic report generation."""
        result, precip = sample_result

        report = HydrologyReportGenerator()
        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Zlewnia Testowa",
        )

        # Check main sections are present
        assert "# Raport Hydrologiczny: Zlewnia Testowa" in content
        assert "## 3. Hietogram" in content
        assert "## 4. Opad Efektywny" in content
        assert "## 5. Hydrogram Jednostkowy" in content
        assert "## 7. Wyniki" in content
        assert "## 8. Bilans Wodny" in content

        # Check some key values
        assert "72" in content  # CN
        assert "Hydrolog" in content  # Version header

    def test_generate_with_tc(self, sample_result):
        """Test report generation with concentration time."""
        result, precip = sample_result

        report = HydrologyReportGenerator()
        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Test",
            tc_min=90.0,
            tc_method="kirpich",
        )

        assert "## 2. Czas Koncentracji" in content
        assert "Kirpich" in content
        assert "90" in content

    def test_generate_with_watershed_params(self, sample_result):
        """Test report generation with watershed parameters."""
        result, precip = sample_result

        watershed_params = {
            "perimeter_km": 32.1,
            "length_km": 12.5,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "channel_length_km": 10.2,
            "channel_slope_m_per_m": 0.025,
        }

        report = HydrologyReportGenerator()
        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Zlewnia z parametrami",
            watershed_params=watershed_params,
            tc_min=90.0,
        )

        assert "## 1. Parametry Zlewni" in content
        assert "32.1" in content or "32.10" in content
        assert "520" in content

    def test_generate_with_custom_config(self, sample_result):
        """Test report generation with custom configuration."""
        result, precip = sample_result

        config = ReportConfig(
            include_formulas=False,
            include_tables=False,
            max_table_rows=10,
        )

        report = HydrologyReportGenerator(config)
        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Test",
        )

        # Should still have section headers
        assert "## 4. Opad Efektywny" in content
        # But formulas might be simplified
        assert "Hydrolog" in content

    def test_generate_saves_to_file(self, sample_result, tmp_path):
        """Test that report saves to file correctly."""
        result, precip = sample_result

        output_path = tmp_path / "raport.md"

        report = HydrologyReportGenerator()
        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Test",
            output_path=output_path,
        )

        assert output_path.exists()
        saved_content = output_path.read_text(encoding="utf-8")
        assert saved_content == content
        assert "# Raport Hydrologiczny" in saved_content


# =============================================================================
# Integration Tests
# =============================================================================


class TestReportIntegration:
    """Integration tests for complete report generation workflow."""

    def test_full_workflow_scs_model(self):
        """Test full report workflow with SCS model."""
        # Generate precipitation
        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(
            total_mm=50.0, duration_min=120.0, timestep_min=10.0
        )

        # Generate hydrograph
        generator = HydrographGenerator(
            area_km2=45.3,
            cn=72,
            tc_min=90.0,
        )
        result = generator.generate(precip)

        # Generate report
        config = ReportConfig(
            tc_method="kirpich",
            uh_model="scs",
            hietogram_type="beta",
        )
        report = HydrologyReportGenerator(config)

        watershed_params = {
            "perimeter_km": 32.1,
            "length_km": 12.5,
            "channel_length_km": 10.2,
            "channel_slope_m_per_m": 0.025,
        }

        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Zlewnia Potoku",
            tc_min=90.0,
            tc_method="kirpich",
            watershed_params=watershed_params,
        )

        # Verify all sections
        assert "# Raport Hydrologiczny: Zlewnia Potoku" in content
        assert "## 1. Parametry Zlewni" in content
        assert "## 2. Czas Koncentracji" in content
        assert "## 3. Hietogram" in content
        assert "## 4. Opad Efektywny" in content
        assert "## 5. Hydrogram Jednostkowy" in content
        assert "## 6. Splot" in content
        assert "## 7. Wyniki" in content
        assert "## 8. Bilans Wodny" in content

        # Verify key calculations are documented
        assert "$$" in content  # LaTeX formulas
        assert "Qmax" in content or "przepływ szczytowy" in content.lower()

    def test_full_workflow_nash_model(self):
        """Test full report workflow with Nash model."""
        # Generate precipitation
        hietogram = BetaHietogram(alpha=2, beta=5)
        precip = hietogram.generate(
            total_mm=50.0, duration_min=120.0, timestep_min=10.0
        )

        # Generate hydrograph with Nash model
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            uh_params={"n": 3.0, "k": 0.8, "k_unit": "hours"},
        )
        result = generator.generate(precip)

        # Generate report
        config = ReportConfig(uh_model="nash")
        report = HydrologyReportGenerator(config)

        content = report.generate(
            result=result,
            hietogram=precip,
            watershed_name="Zlewnia Nash",
            uh_params={"n": 3.0, "k_min": 48.0},
        )

        assert "Nash" in content
        assert "zbiornik" in content.lower() or "n =" in content


# =============================================================================
# The report documents the computation that was performed
# =============================================================================

_UH_MODELS = {
    "scs": {"uh_model": "scs", "tc_min": 90.0},
    "nash": {
        "uh_model": "nash",
        "uh_params": {"n": 2.5, "k": 48.0, "k_unit": "min"},
    },
    "clark": {"uh_model": "clark", "tc_min": 90.0, "uh_params": {"r": 35.0}},
    "snyder": {
        "uh_model": "snyder",
        "uh_params": {"L_km": 15.0, "Lc_km": 7.5, "ct": 1.7, "cp": 0.65},
    },
}

# Watershed parameters of a catchment that all six tc methods can be applied to
_CATCHMENT = {
    "area_km2": 45.0,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "elevation_mean_m": 330.0,
    "mean_slope_m_per_m": 0.025,
    "channel_length_km": 10.8,
    "channel_slope_m_per_m": 0.018,
    "cn": 72,
    "runoff_coeff": 0.45,
    "retardance": 0.4,
    "overland_length_km": 0.25,
    "overland_slope_m_per_m": 0.008,
}


def _precipitation():
    return BetaHietogram(alpha=2, beta=5).generate(
        total_mm=50.0, duration_min=60.0, timestep_min=10.0
    )


def _computation(model="scs", cn=72, ia_coefficient=0.2):
    """Hydrograph of one model; returns ``(result, precipitation)``."""
    settings = dict(_UH_MODELS[model])
    precip = _precipitation()
    generator = HydrographGenerator(
        area_km2=45.0, cn=cn, ia_coefficient=ia_coefficient, **settings
    )
    return generator.generate(precip), precip


def _ordinate_rows(content):
    """The ``(time, ordinate)`` cells of the unit hydrograph table, as printed."""
    after = content.split(SUBSECTION_HEADERS["unit_hydrograph"]["ordinates"])[1]
    rows = []
    for line in after.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if line.startswith("| ") and cells[0].replace(".", "", 1).isdigit():
            rows.append((cells[0], cells[1]))
        elif rows and not line.startswith("|"):
            break
    return rows


def _section(content, number):
    """Text of the section ``## <number>.`` up to the next one."""
    start = content.index(f"## {number}.")
    end = content.find(f"## {number + 1}.", start)
    return content[start:] if end < 0 else content[start:end]


class TestReportShowsTheUnitHydrographThatWasUsed:
    """The unit hydrograph section is not a placeholder shape."""

    @pytest.mark.parametrize("model", list(_UH_MODELS))
    def test_the_ordinates_are_those_of_the_unit_hydrograph(self, model):
        result, precip = _computation(model)
        unit = result.unit_hydrograph_result

        content = HydrologyReportGenerator(
            ReportConfig(uh_model=model, max_table_rows=10_000)
        ).generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            tc_min=_UH_MODELS[model].get("tc_min"),
            uh_params=_UH_MODELS[model].get("uh_params") if model == "snyder" else None,
        )

        assert _ordinate_rows(content) == [
            (f"{t:.1f}", f"{q:.4f}") for t, q in zip(unit.times_min, unit.ordinates_m3s)
        ]

    @pytest.mark.parametrize("model", ["scs", "nash", "clark"])
    def test_the_summary_is_the_peak_of_the_unit_hydrograph(self, model):
        result, precip = _computation(model)
        unit = result.unit_hydrograph_result

        content = HydrologyReportGenerator(ReportConfig(uh_model=model)).generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            tc_min=_UH_MODELS[model].get("tc_min"),
        )

        section = _section(content, 5)
        assert f"| Czas do szczytu tp | {unit.time_to_peak_min:.1f} min |" in section
        assert (
            f"| Przepływ szczytowy qp | {unit.peak_discharge_m3s:.4f} m³/s/mm |"
            in section
        )

    def test_the_convolution_section_counts_the_ordinates_of_the_unit_hydrograph(
        self,
    ):
        result, precip = _computation("nash")

        content = HydrologyReportGenerator(ReportConfig(uh_model="nash")).generate(
            result=result, hietogram=precip, area_km2=45.0
        )

        n_ordinates = len(result.unit_hydrograph_result.ordinates_m3s)
        assert (
            f"| Liczba rzędnych hydrogramu jednostkowego (N) | {n_ordinates} |"
            in content
        )

    def test_model_parameters_are_those_of_the_model_not_defaults(self):
        """Nash n = 2.5, K = 48 min without ``uh_params``: no n = 3, K = 30 default."""
        result, precip = _computation("nash")

        content = HydrologyReportGenerator(ReportConfig(uh_model="nash")).generate(
            result=result, hietogram=precip, area_km2=45.0
        )

        assert "n = 2.50" in content
        assert "K = 48.0 min" in content
        assert "K = 30.0 min" not in content

    def test_clark_parameters_are_those_of_the_model(self):
        result, precip = _computation("clark")

        content = HydrologyReportGenerator(ReportConfig(uh_model="clark")).generate(
            result=result, hietogram=precip, area_km2=45.0
        )

        assert "Tc = 90.0 min" in content
        assert "R = 35.0 min" in content
        assert "Δt = 10.0 min" in content

    def test_snyder_formulas_use_the_coefficients_of_the_model(self):
        result, precip = _computation("snyder")
        unit = result.unit_hydrograph_result

        content = HydrologyReportGenerator(ReportConfig(uh_model="snyder")).generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            uh_params={"L_km": 15.0, "Lc_km": 7.5},
        )

        assert "Ct = 1.70" in content and "Cp = 0.65" in content
        assert "L = 15.00 km" in content and "Lc = 7.50 km" in content
        assert f"tL = {unit.lag_time_min:.1f} min" in content
        peak = 0.275 * 0.65 * 45.0 / (unit.lag_time_min / 60.0)
        assert f"qp = {peak:.4f} m³/s/mm" in content

    def test_unknown_stream_lengths_are_not_invented(self):
        """The result has no L and Lc: without ``uh_params`` they are left out."""
        result, precip = _computation("snyder")
        unit = result.unit_hydrograph_result

        content = HydrologyReportGenerator(ReportConfig(uh_model="snyder")).generate(
            result=result, hietogram=precip, area_km2=45.0
        )

        section = _section(content, 5)
        assert "Długość cieku" not in section
        assert "Odległość do centroidu" not in section
        assert "L = 10.00 km" not in section and "Lc = 5.00 km" not in section
        assert (
            f"t_L = {unit.lag_time_min / 60:.3f} \\text{{ h}} = "
            f"{unit.lag_time_min:.1f} \\text{{ min}}"
        ) in section
        assert "Ct = 1.70" in section

    def test_the_caller_dict_of_uh_params_is_not_modified(self):
        result, precip = _computation("snyder")
        uh_params = {"L_km": 15.0, "Lc_km": 7.5}

        HydrologyReportGenerator(ReportConfig(uh_model="snyder")).generate(
            result=result, hietogram=precip, area_km2=45.0, uh_params=uh_params
        )

        assert uh_params == {"L_km": 15.0, "Lc_km": 7.5}

    def test_a_result_without_a_unit_hydrograph_cannot_be_documented(self):
        result, precip = _computation("scs")
        bare = dataclasses.replace(result, unit_hydrograph_result=None)

        with pytest.raises(InvalidParameterError) as caught:
            HydrologyReportGenerator().generate(
                result=bare, hietogram=precip, area_km2=45.0
            )

        assert caught.value.details["reason"] == "no_unit_hydrograph"

    def test_the_model_of_the_result_wins_over_the_configured_one(self):
        result, precip = _computation("nash")

        with pytest.warns(UserWarning, match="uh_model='scs'.*'nash'"):
            content = HydrologyReportGenerator(ReportConfig(uh_model="scs")).generate(
                result=result, hietogram=precip, area_km2=45.0
            )

        assert "Model kaskady zbiorników Nasha" in content
        assert "Hydrogram jednostkowy SCS" not in content

    def test_a_matching_model_does_not_warn(self):
        result, precip = _computation("clark")

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            HydrologyReportGenerator(ReportConfig(uh_model="clark")).generate(
                result=result, hietogram=precip, area_km2=45.0
            )


class TestReportShowsTheInitialAbstractionCoefficient:
    """Ia = λ S is rendered with the λ of the computation, not always with 0.2."""

    @pytest.mark.parametrize("coefficient", [0.05, 0.1, 0.3])
    def test_lambda_is_read_back_from_the_result(self, coefficient):
        result, precip = _computation("scs", ia_coefficient=coefficient)

        content = HydrologyReportGenerator().generate(
            result=result, hietogram=precip, area_km2=45.0
        )

        assert (
            f"I_a = \\lambda \\cdot S = {coefficient} \\cdot "
            f"{result.retention_mm:.2f} = {result.initial_abstraction_mm:.2f}"
        ) in content

    def test_an_explicit_coefficient_is_used(self):
        """CN = 100 has S = 0: λ cannot be read back, so it is given."""
        result, precip = _computation("scs", cn=100, ia_coefficient=0.3)

        read_back = HydrologyReportGenerator().generate(
            result=result, hietogram=precip, area_km2=45.0
        )
        given = HydrologyReportGenerator().generate(
            result=result, hietogram=precip, area_km2=45.0, ia_coefficient=0.3
        )

        assert "\\lambda \\cdot S = 0.2 \\cdot 0.00" in read_back
        assert "\\lambda \\cdot S = 0.3 \\cdot 0.00" in given


class TestReportShowsTheInputsOfTheTimeOfConcentration:
    """Every method of ``calculate_tc`` shows the arguments it was fed with."""

    @staticmethod
    def _tc(method):
        params = WatershedParameters.from_dict(_CATCHMENT)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return params.calculate_tc(method=method)

    @staticmethod
    def _watershed_params():
        """The watershed dict of the report: rows of the section and tc inputs."""
        values = {
            key: value
            for key, value in _CATCHMENT.items()
            if key not in ("area_km2", "cn", "mean_slope_m_per_m")
        }
        values["mean_slope_percent"] = _CATCHMENT["mean_slope_m_per_m"] * 100.0
        return values

    def _tc_section(self, method, **extra):
        result, precip = _computation("scs")
        content = HydrologyReportGenerator(ReportConfig(tc_method=method)).generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            cn_ii=72,
            tc_min=self._tc(method),
            tc_method=method,
            watershed_params=self._watershed_params(),
            **extra,
        )
        return _section(content, 2)

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("kirpich", ["10.80^{0.77}", "0.0180^{-0.385}"]),
            ("nrcs", ["L = 10800 m", "Y = 1.80 %", "dla CN = 72"]),
            ("giandotti", ["\\sqrt{45.00}", "1.5 \\cdot 10.80", "\\sqrt{180.0}"]),
            ("faa", ["(1.1 - 0.45)", "10.800^{0.5}", "0.0180^{-1/3}"]),
            ("kerby", ["(10.800 \\cdot 0.40)^{0.467}", "0.0180^{-0.2335}"]),
            (
                "kerby_kirpich",
                ["(0.250 \\cdot 0.40)^{0.467}", "0.0080^{-0.2335}", "10.80^{0.77}"],
            ),
        ],
    )
    def test_the_formula_shows_the_inputs_of_the_computation(self, method, expected):
        section = self._tc_section(method)

        assert "brak danych" not in section
        for fragment in expected:
            assert fragment in section, fragment

    def test_the_composite_method_components_add_up_to_the_time_of_concentration(
        self,
    ):
        tc = self._tc("kerby_kirpich")
        overland = ConcentrationTime.kerby(0.25, 0.008, 0.4)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            channel = ConcentrationTime.kirpich(10.8, 0.018)
        assert tc == pytest.approx(overland + channel)

        section = self._tc_section("kerby_kirpich")

        assert f"t_c = {overland:.1f} + {channel:.1f} = {tc:.1f}" in section

    def test_inputs_given_as_tc_params_are_shown_as_given(self):
        section = self._tc_section(
            "kirpich", tc_params={"length_km": 3.0, "slope_m_per_m": 0.05}
        )

        assert "3.00^{0.77}" in section
        assert "0.0500^{-0.385}" in section

    def test_tc_params_may_be_given_without_any_watershed_params(self):
        result, precip = _computation("scs")

        content = HydrologyReportGenerator().generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            tc_min=90.0,
            tc_method="faa",
            tc_params={
                "length_km": 0.2,
                "slope_m_per_m": 0.02,
                "runoff_coeff": 0.6,
            },
        )

        section = _section(content, 2)
        assert "(1.1 - 0.60)" in section and "0.200^{0.5}" in section

    def test_the_inputs_that_are_no_watershed_rows_do_not_reach_that_section(self):
        result, precip = _computation("scs")

        content = HydrologyReportGenerator(ReportConfig(tc_method="kerby")).generate(
            result=result,
            hietogram=precip,
            area_km2=45.0,
            tc_min=self._tc("kerby"),
            tc_method="kerby",
            watershed_params=self._watershed_params(),
        )

        assert "## 1. Parametry Zlewni" in content
        assert "retardance" not in _section(content, 1)

    def test_the_slope_falls_back_to_the_mean_slope_and_to_the_relief(self):
        """The rules of ``calculate_tc``: channel slope, mean slope, relief/length."""
        no_channel = {
            key: value
            for key, value in self._watershed_params().items()
            if key not in ("channel_slope_m_per_m", "channel_length_km")
        }
        no_slopes = {
            key: value
            for key, value in no_channel.items()
            if key != "mean_slope_percent"
        }
        result, precip = _computation("scs")

        def kirpich_section(watershed_params):
            content = HydrologyReportGenerator().generate(
                result=result,
                hietogram=precip,
                area_km2=45.0,
                tc_min=90.0,
                tc_method="kirpich",
                watershed_params=watershed_params,
            )
            return _section(content, 2)

        assert "12.50^{0.77}" in kirpich_section(no_channel)
        assert "0.0250^{-0.385}" in kirpich_section(no_channel)
        relief_slope = (520.0 - 150.0) / (12.5 * 1000.0)
        assert f"{relief_slope:.4f}^{{-0.385}}" in kirpich_section(no_slopes)
