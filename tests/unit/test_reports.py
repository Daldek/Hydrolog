"""Unit tests for the reports module."""

import numpy as np
import pytest

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
from hydrolog.runoff import HydrographGenerator


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
        precip = hietogram.generate(total_mm=50.0, duration_min=120.0, timestep_min=10.0)

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
        precip = hietogram.generate(total_mm=50.0, duration_min=120.0, timestep_min=10.0)

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
