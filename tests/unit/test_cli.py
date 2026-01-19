"""Tests for CLI interface."""

import json

import pytest

from hydrolog.cli.main import main


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_no_args_shows_help(self, capsys):
        """Test that no arguments shows help."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "Hydrolog" in captured.out
        assert "commands" in captured.out

    def test_version(self, capsys):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_help(self, capsys):
        """Test --help flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


class TestCLITc:
    """Tests for 'tc' command."""

    def test_tc_no_method_shows_help(self, capsys):
        """Test tc with no method shows help."""
        result = main(["tc"])
        assert result == 0
        captured = capsys.readouterr()
        assert "kirpich" in captured.out
        assert "scs-lag" in captured.out
        assert "giandotti" in captured.out

    def test_tc_kirpich(self, capsys):
        """Test tc kirpich calculation."""
        result = main(["tc", "kirpich", "--length", "2.5", "--slope", "0.02"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Kirpich" in captured.out
        assert "Tc =" in captured.out

    def test_tc_kirpich_missing_args(self, capsys):
        """Test tc kirpich with missing arguments."""
        with pytest.raises(SystemExit) as exc_info:
            main(["tc", "kirpich", "--length", "2.5"])
        assert exc_info.value.code != 0

    def test_tc_scs_lag(self, capsys):
        """Test tc scs-lag calculation."""
        result = main(["tc", "scs-lag", "--length", "5.0", "--slope", "0.01", "--cn", "72"])
        assert result == 0
        captured = capsys.readouterr()
        assert "SCS Lag" in captured.out
        assert "Curve Number" in captured.out

    def test_tc_giandotti(self, capsys):
        """Test tc giandotti calculation."""
        result = main(["tc", "giandotti", "--area", "100", "--length", "15", "--elevation", "500"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Giandotti" in captured.out
        assert "Watershed area" in captured.out


class TestCLICN:
    """Tests for 'cn' command."""

    def test_cn_no_subcommand_shows_help(self, capsys):
        """Test cn with no subcommand shows help."""
        result = main(["cn"])
        assert result == 0
        captured = capsys.readouterr()
        assert "lookup" in captured.out
        assert "list" in captured.out

    def test_cn_lookup(self, capsys):
        """Test cn lookup."""
        result = main(["cn", "lookup", "--hsg", "B", "--cover", "forest", "--condition", "good"])
        assert result == 0
        captured = capsys.readouterr()
        assert "CN = 55" in captured.out

    def test_cn_lookup_no_condition(self, capsys):
        """Test cn lookup without condition."""
        result = main(["cn", "lookup", "--hsg", "A", "--cover", "paved"])
        assert result == 0
        captured = capsys.readouterr()
        assert "CN = 98" in captured.out

    def test_cn_list(self, capsys):
        """Test cn list."""
        result = main(["cn", "list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "forest" in captured.out
        assert "pasture" in captured.out
        assert "paved" in captured.out

    def test_cn_range(self, capsys):
        """Test cn range."""
        result = main(["cn", "range", "--cover", "forest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "HSG" in captured.out
        assert "Min" in captured.out


class TestCLISCS:
    """Tests for 'scs' command."""

    def test_scs_basic(self, capsys):
        """Test basic SCS-CN calculation."""
        result = main(["scs", "--cn", "72", "--precipitation", "50"])
        assert result == 0
        captured = capsys.readouterr()
        assert "SCS-CN Runoff" in captured.out
        assert "Effective precip" in captured.out
        assert "7.09" in captured.out  # Expected Pe value

    def test_scs_with_amc(self, capsys):
        """Test SCS-CN with AMC-III."""
        result = main(["scs", "--cn", "72", "--precipitation", "50", "--amc", "III"])
        assert result == 0
        captured = capsys.readouterr()
        assert "AMC" in captured.out
        assert "wet" in captured.out

    def test_scs_with_custom_ia(self, capsys):
        """Test SCS-CN with custom Ia coefficient."""
        result = main(["scs", "--cn", "72", "--precipitation", "50", "--ia", "0.1"])
        assert result == 0
        captured = capsys.readouterr()
        assert "0.1" in captured.out

    def test_scs_no_runoff(self, capsys):
        """Test SCS-CN when P < Ia (no runoff)."""
        result = main(["scs", "--cn", "50", "--precipitation", "10"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No runoff" in captured.out


class TestCLIUH:
    """Tests for 'uh' command."""

    def test_uh_no_method_shows_help(self, capsys):
        """Test uh with no method shows help."""
        result = main(["uh"])
        assert result == 0
        captured = capsys.readouterr()
        assert "scs" in captured.out
        assert "nash" in captured.out
        assert "clark" in captured.out
        assert "snyder" in captured.out

    def test_uh_scs(self, capsys):
        """Test SCS unit hydrograph generation."""
        result = main(["uh", "scs", "--area", "45", "--tc", "90", "--timestep", "10"])
        assert result == 0
        captured = capsys.readouterr()
        assert "SCS" in captured.out
        assert "Peak" in captured.out

    def test_uh_nash(self, capsys):
        """Test Nash unit hydrograph generation."""
        result = main(["uh", "nash", "--area", "45", "--n", "3", "--k", "30", "--timestep", "10"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Nash" in captured.out
        assert "Peak" in captured.out

    def test_uh_clark(self, capsys):
        """Test Clark unit hydrograph generation."""
        result = main(["uh", "clark", "--area", "45", "--tc", "60", "--r", "30", "--timestep", "10"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Clark" in captured.out
        assert "Peak" in captured.out

    def test_uh_snyder(self, capsys):
        """Test Snyder unit hydrograph generation."""
        result = main(["uh", "snyder", "--area", "100", "--L", "15", "--Lc", "8", "--timestep", "30"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Snyder" in captured.out
        assert "Peak" in captured.out

    def test_uh_csv_output(self, capsys):
        """Test CSV output format."""
        result = main(["uh", "scs", "--area", "45", "--tc", "90", "--timestep", "10", "--csv"])
        assert result == 0
        captured = capsys.readouterr()
        assert "time_min,discharge_m3s_per_mm" in captured.out
        lines = captured.out.strip().split("\n")
        assert len(lines) > 5

    def test_uh_json_output(self, capsys):
        """Test JSON output format."""
        result = main(["uh", "scs", "--area", "45", "--tc", "90", "--timestep", "10", "--json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "method" in data
        assert data["method"] == "SCS"
        assert "hydrograph" in data
        assert "times_min" in data["hydrograph"]


class TestCLIErrors:
    """Tests for CLI error handling."""

    def test_invalid_cn(self, capsys):
        """Test error with invalid CN value."""
        result = main(["scs", "--cn", "150", "--precipitation", "50"])
        assert result != 0

    def test_invalid_hsg(self, capsys):
        """Test error with invalid HSG (argparse catches this)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["cn", "lookup", "--hsg", "E", "--cover", "forest"])
        assert exc_info.value.code != 0

    def test_invalid_cover(self, capsys):
        """Test error with invalid land cover."""
        result = main(["cn", "lookup", "--hsg", "B", "--cover", "invalid_cover"])
        assert result != 0
