"""Tests for loading series, watershed parameters and stations (catalog inputs)."""

import json
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog.inputs import (
    Series,
    Table,
    load_records,
    load_series,
    load_stations,
    load_watershed,
    read_table,
)
from hydrolog.exceptions import InputDataError, InvalidParameterError, NotFoundError
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.precipitation.interpolation import Station

FIXTURES = Path(__file__).parents[1] / "fixtures"
IMGW_EXPORT = FIXTURES / "imgwtools_series_export.csv"

WATERSHED = {
    "area_km2": 45.3,
    "perimeter_km": 32.1,
    "length_km": 12.5,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "cn": 72,
    "name": "Testowa",
}


def write(directory: Path, name: str, content: str | bytes, encoding: str = "utf-8"):
    """Write a test file and return its path."""
    path = directory / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_bytes(content.encode(encoding))
    return path


def failure(call, exc_type=InputDataError):
    """Run ``call`` and return the expected error."""
    with pytest.raises(exc_type) as caught:
        call()
    return caught.value


# --- files ----------------------------------------------------------------------------


class TestReadTableCsv:
    """CSV dialects and damage."""

    def test_comma_separated_with_header(self, tmp_path):
        """Plain comma CSV: columns in file order, cells stripped."""
        path = write(tmp_path, "a.csv", "date, flow\n2020-01-01, 1.5\n2020-01-02,2\n")
        table = read_table(path)
        assert isinstance(table, Table)
        assert table.columns == ("date", "flow")
        assert table.n_rows == 2
        assert table.data["flow"] == ["1.5", "2"]
        assert table.source == path

    def test_semicolon_is_detected_from_the_header(self, tmp_path):
        """A semicolon header selects the semicolon, decimal commas stay in cells."""
        path = write(tmp_path, "a.csv", "date;flow\n2020-01-01;1,5\n2020-01-02;2,25\n")
        table = read_table(path)
        assert table.columns == ("date", "flow")
        assert table.data["flow"] == ["1,5", "2,25"]

    def test_quoted_fields_keep_delimiters_and_quotes(self, tmp_path):
        """Quoted cells may contain the delimiter and doubled quotes."""
        path = write(tmp_path, "a.csv", 'name,note\nA,"x, y"\nB,"say ""hi"""\n')
        assert read_table(path).data["note"] == ["x, y", 'say "hi"']

    def test_utf8_bom_is_ignored(self, tmp_path):
        """A BOM does not become part of the first column name."""
        path = write(tmp_path, "a.csv", b"\xef\xbb\xbfdate,flow\n2020-01-01,1\n")
        assert read_table(path).columns == ("date", "flow")

    def test_crlf_and_lf_and_blank_lines(self, tmp_path):
        """Line endings and blank lines do not matter."""
        crlf = write(tmp_path, "crlf.csv", "a,b\r\n1,2\r\n\r\n3,4\r\n\r\n")
        lf = write(tmp_path, "lf.csv", "\na,b\n1,2\n3,4\n")
        assert (
            read_table(crlf).data
            == read_table(lf).data
            == {"a": ["1", "3"], "b": ["2", "4"]}
        )

    def test_polish_text_is_read_as_utf8(self, tmp_path):
        """Non-ASCII text survives."""
        path = write(tmp_path, "a.csv", "stacja,uwagi\nŁódź,zażółć gęślą jaźń\n")
        assert read_table(path).data["uwagi"] == ["zażółć gęślą jaźń"]

    def test_header_only_file_has_no_rows(self, tmp_path):
        """A header without data is a valid, empty table."""
        table = read_table(write(tmp_path, "a.csv", "a,b\n"))
        assert (table.columns, table.n_rows) == (("a", "b"), 0)

    def test_trailing_delimiters_are_tolerated(self, tmp_path):
        """An empty trailing header cell is dropped; empty extra cells are ignored."""
        path = write(tmp_path, "a.csv", "a;b;\n1;2;\n3;4;\n")
        table = read_table(path)
        assert table.columns == ("a", "b")
        assert table.data == {"a": ["1", "3"], "b": ["2", "4"]}

    def test_ragged_row_is_reported_with_its_number(self, tmp_path):
        """A row with too few cells names the row."""
        path = write(tmp_path, "a.csv", "a,b,c\n1,2,3\n4,5\n")
        error = failure(lambda: read_table(path))
        assert error.code == "data_error"
        assert error.details["reason"] == "ragged_row"
        assert (
            error.details["row"],
            error.details["cells"],
            error.details["expected"],
        ) == (2, 2, 3)
        assert error.details["path"] == str(path)

    def test_row_with_extra_content_is_ragged(self, tmp_path):
        """Extra non-empty cells are an error, not silently dropped."""
        path = write(tmp_path, "a.csv", "a,b\n1,2,3\n")
        assert failure(lambda: read_table(path)).details["reason"] == "ragged_row"

    def test_duplicate_column_names(self, tmp_path):
        """Ambiguous headers are rejected up front."""
        path = write(tmp_path, "a.csv", "q,q,x\n1,2,3\n")
        error = failure(lambda: read_table(path))
        assert error.details["reason"] == "duplicate_column"
        assert error.details["columns"] == ["q"]

    def test_empty_file(self, tmp_path):
        """An empty file or one with only blank lines is ``empty``."""
        for content in ("", "\n\n  \n"):
            error = failure(
                lambda content=content: read_table(write(tmp_path, "e.csv", content))
            )
            assert error.details["reason"] == "empty"

    def test_not_utf8_is_an_encoding_error_with_a_hint(self, tmp_path):
        """A Windows-1250 file is reported as such, with advice."""
        path = write(tmp_path, "a.csv", "stacja;opad\nŁódź;1\n", encoding="cp1250")
        error = failure(lambda: read_table(path))
        assert error.details["reason"] == "encoding"
        assert "UTF-8" in error.hint

    def test_missing_file_is_not_found(self, tmp_path):
        """A file that does not exist is ``not_found`` with its path."""
        path = tmp_path / "nope.csv"
        error = failure(lambda: read_table(path), NotFoundError)
        assert error.code == "not_found"
        assert error.details == {"path": str(path)}

    def test_directory_is_not_a_file(self, tmp_path):
        """A directory is a data error, not a crash."""
        error = failure(lambda: read_table(tmp_path))
        assert error.details["reason"] == "not_a_file"

    def test_blank_path_is_a_validation_error(self):
        """An empty path is a wrong option value."""
        error = failure(lambda: read_table("  "), InvalidParameterError)
        assert error.details["reason"] == "empty"

    def test_oversized_cell_is_invalid_csv(self, tmp_path):
        """The csv module's field limit is reported as a data error."""
        path = write(tmp_path, "a.csv", "a,b\n1," + "x" * 200_000 + "\n")
        assert failure(lambda: read_table(path)).details["reason"] == "invalid_csv"

    def test_unreadable_file_is_a_data_error(self, tmp_path, monkeypatch):
        """A permission problem is ``data_error`` (unreadable), not a crash."""
        path = write(tmp_path, "a.csv", "a\n1\n")

        def deny(self, *args, **kwargs):
            raise PermissionError(13, "Permission denied", str(path))

        monkeypatch.setattr(Path, "open", deny)
        error = failure(lambda: read_table(path))
        assert error.code == "data_error"
        assert error.details == {"path": str(path), "reason": "unreadable"}


class TestReadTableJson:
    """JSON shapes."""

    def test_list_of_records(self, tmp_path):
        """Records become columns; missing keys become ``None``."""
        data = [{"d": "2020-01-01", "q": 1.5}, {"d": "2020-01-02"}]
        table = read_table(write(tmp_path, "a.json", json.dumps(data)))
        assert table.columns == ("d", "q")
        assert table.data == {"d": ["2020-01-01", "2020-01-02"], "q": [1.5, None]}

    def test_object_of_columns(self, tmp_path):
        """Equal-length lists are columns."""
        table = read_table(
            write(tmp_path, "a.json", '{"values": [1, 2], "dates": ["a", "b"]}')
        )
        assert table.columns == ("values", "dates")
        assert table.n_rows == 2

    def test_columns_of_different_length_are_rejected(self, tmp_path):
        """Ragged columns are a data error."""
        error = failure(
            lambda: read_table(write(tmp_path, "a.json", '{"a": [1], "b": [1, 2]}'))
        )
        assert error.details["reason"] == "ragged_columns"

    def test_plain_list_of_numbers_is_one_column_called_values(self, tmp_path):
        """The simplest series file."""
        table = read_table(write(tmp_path, "a.json", "[1, 2.5, null]"))
        assert table.columns == ("values",)
        assert table.data["values"] == [1, 2.5, None]

    @pytest.mark.parametrize(
        "content", ["[]", "{}", '"text"', "[true, false]", "[[1], [2]]", "3"]
    )
    def test_unsupported_shapes(self, tmp_path, content):
        """Anything else is a ``shape`` (or ``empty``) error."""
        error = failure(lambda: read_table(write(tmp_path, "a.json", content)))
        assert error.details["reason"] in ("shape", "empty")

    def test_invalid_json_reports_the_position(self, tmp_path):
        """Syntax errors carry line and column (as the ``json`` module counts them)."""
        path = write(tmp_path, "a.json", '{"a": [1,\n 2,]}')
        error = failure(lambda: read_table(path))
        assert error.details["reason"] == "invalid_json"
        assert error.details["line"] == 2
        # Python 3.13 points at the trailing comma (3), Python 3.12 at the bracket (4).
        assert error.details["column"] in (3, 4)

    def test_nan_literal_is_rejected(self, tmp_path):
        """``NaN`` is not JSON; a missing value is ``null``."""
        error = failure(lambda: read_table(write(tmp_path, "a.json", "[1, NaN]")))
        assert error.details["reason"] == "invalid_json"
        assert "null" in str(error)

    def test_json_bom_is_ignored(self, tmp_path):
        """Windows editors add a BOM to JSON files."""
        table = read_table(write(tmp_path, "a.json", b"\xef\xbb\xbf[1, 2]"))
        assert table.n_rows == 2

    def test_format_is_sniffed_for_other_suffixes(self, tmp_path):
        """Unknown suffixes are JSON when they start with ``[`` or ``{``, else CSV."""
        assert read_table(write(tmp_path, "a.dat", "[1, 2]")).columns == ("values",)
        assert read_table(write(tmp_path, "b.dat", "a,b\n1,2\n")).columns == ("a", "b")

    def test_json_suffix_wins_over_content(self, tmp_path):
        """A ``.json`` file that is not JSON is an error, never parsed as CSV."""
        error = failure(lambda: read_table(write(tmp_path, "a.json", "a,b\n1,2\n")))
        assert error.details["reason"] == "invalid_json"


class TestLoadRecords:
    """``load_records``."""

    def test_csv_records_are_strings(self, tmp_path):
        """CSV cells stay text; the consumer converts."""
        path = write(tmp_path, "a.csv", "name,x\nA,1.5\n")
        assert load_records(path) == [{"name": "A", "x": "1.5"}]

    def test_json_records_keep_types(self, tmp_path):
        """JSON values keep their types, nested lists included."""
        data = [{"segment_id": 3, "upstream_ids": [1, 2], "length_km": 2.0}]
        assert load_records(write(tmp_path, "a.json", json.dumps(data))) == data


class TestColumnResolution:
    """Column lookup rules."""

    @pytest.fixture
    def table(self):
        return read_table(IMGW_EXPORT)

    def test_exact_name(self, table):
        """The full header text always works."""
        assert table.resolve_column("Q [m3/s]") == "Q [m3/s]"

    def test_name_without_unit_suffix(self, table):
        """``Q`` finds ``Q [m3/s]`` but not ``Q_flag``."""
        assert table.resolve_column("Q") == "Q [m3/s]"
        assert table.resolve_column("H") == "H [cm]"

    def test_missing_column_lists_the_available_ones(self, table):
        """The error names the option, the column and what exists."""
        error = failure(lambda: table.resolve_column("Z", option="value_column"))
        assert error.code == "data_error"
        assert error.details["reason"] == "missing_column"
        assert error.details["column"] == "Z"
        assert error.details["option"] == "value_column"
        assert "Q [m3/s]" in error.details["available"]
        assert "Available columns" in error.hint

    def test_ambiguous_short_name(self, tmp_path):
        """Two columns that shorten to the same name need the full name."""
        path = write(tmp_path, "a.csv", "Q [m3/s],Q [l/s]\n1,2\n")
        error = failure(lambda: read_table(path).resolve_column("Q"))
        assert error.details["reason"] == "ambiguous_column"


class TestNumbers:
    """Number parsing of cells."""

    def test_decimal_comma_and_missing_tokens(self, tmp_path):
        """Polish decimals load; empty and NA-like cells are NaN."""
        rows = [
            "1,5",
            "2.5",
            "",
            "NaN",
            "na",
            "N/A",
            "null",
            "None",
            "1e3",
            " 7 ",
            "-0,25",
            ".5",
        ]
        path = write(
            tmp_path,
            "a.csv",
            "k,v\n" + "\n".join(f'{i},"{r}"' for i, r in enumerate(rows)) + "\n",
        )
        values = read_table(path).numbers("v")
        expected = [
            1.5,
            2.5,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            1000.0,
            7.0,
            -0.25,
            0.5,
        ]
        np.testing.assert_array_equal(values, np.array(expected))
        assert values.dtype == np.float64

    @pytest.mark.parametrize(
        "cell",
        [
            "abc",
            "1,234.5",
            "1 234",
            "12 mm",
            "inf",
            "-Infinity",
            "1e999",
            "0x10",
            "1_000",
        ],
    )
    def test_malformed_numbers_name_row_column_and_value(self, tmp_path, cell):
        """A bad cell is a data error pointing at it (1-based data row)."""
        path = write(tmp_path, "a.csv", f'd,v\nx,1\ny,2\nz,"{cell}"\n')
        error = failure(lambda: read_table(path).numbers("v"))
        assert error.details["reason"] == "bad_number"
        assert (error.details["column"], error.details["row"]) == ("v", 3)
        assert error.details["value"] == cell

    def test_json_cells(self, tmp_path):
        """JSON numbers, null and numeric text are accepted; booleans are not."""
        path = write(tmp_path, "a.json", '{"v": [1, 2.5, null, "3,5"]}')
        np.testing.assert_array_equal(
            read_table(path).numbers("v"), [1, 2.5, np.nan, 3.5]
        )
        path = write(tmp_path, "b.json", '{"v": [1, true]}')
        error = failure(lambda: read_table(path).numbers("v"))
        assert error.details["row"] == 2

    @pytest.mark.parametrize(
        "content",
        [
            '{"v": [1e999]}',
            '{"v": [1' + "0" * 400 + "]}",
            '{"v": [[1]]}',
            '{"v": [{"a": 1}]}',
        ],
    )
    def test_json_cells_that_are_not_finite_numbers(self, tmp_path, content):
        """Overflowing numbers and containers are bad cells, never crashes."""
        error = failure(
            lambda: read_table(write(tmp_path, "a.json", content)).numbers("v")
        )
        assert error.details["reason"] == "bad_number"
        assert error.details["row"] == 1


class TestDates:
    """ISO date parsing of cells."""

    def test_iso_dates(self, tmp_path):
        """ISO dates give ``datetime64[D]``; a midnight time part is ignored."""
        path = write(
            tmp_path,
            "a.csv",
            "d\n2024-02-29\n2024-03-01T00:00:00\n2024-03-02 00:00\n 2024-03-03 \n",
        )
        dates = read_table(path).dates("d")
        assert dates.dtype == np.dtype("datetime64[D]")
        assert list(dates.astype(str)) == [
            "2024-02-29",
            "2024-03-01",
            "2024-03-02",
            "2024-03-03",
        ]

    @pytest.mark.parametrize(
        "cell",
        [
            "29.02.2024",
            "2024-02-30",
            "2023-02-29",
            "2024-02",
            "2024",
            "2024-2-9",
            "2024-02-29T08:30:00",
            "2024-02-29T00:00:00+01:00",
            "yesterday",
            "",
            "20240229",
        ],
    )
    def test_non_iso_or_impossible_dates(self, tmp_path, cell):
        """Only real ``YYYY-MM-DD`` calendar dates (at most with a midnight time)."""
        path = write(tmp_path, "a.csv", f'k,d\n1,2024-01-01\n2,"{cell}"\n')
        error = failure(lambda: read_table(path).dates("d"))
        assert error.details["reason"] == "bad_date"
        assert (error.details["column"], error.details["row"]) == ("d", 2)
        assert error.details["value"] == cell
        assert "2024-02-29" in error.hint


# --- series ---------------------------------------------------------------------------


class TestLoadSeriesInline:
    """Inline values and dates."""

    def test_values_and_dates(self):
        """Inline lists become float and ``datetime64[D]`` arrays."""
        series = load_series(
            values=[1, 2.5, 3], dates=["2020-01-01", "2020-01-02", "2020-01-03"]
        )
        assert isinstance(series, Series)
        assert series.values.dtype == np.float64
        assert series.dates is not None and series.dates.dtype == np.dtype(
            "datetime64[D]"
        )
        np.testing.assert_array_equal(series.values, [1, 2.5, 3])
        assert str(series.dates[-1]) == "2020-01-03"
        assert series.source == "inline"
        assert len(series) == 3
        assert series.n_missing == 0

    def test_values_without_dates(self):
        """Dates are optional unless required."""
        series = load_series(values=[1, 2])
        assert series.dates is None
        error = failure(
            lambda: load_series(values=[1, 2], require_dates=True),
            InvalidParameterError,
        )
        assert error.details == {"option": "dates", "reason": "required"}

    def test_none_is_a_missing_value_and_can_be_dropped(self):
        """``None`` becomes NaN; ``without_missing`` keeps dates aligned."""
        series = load_series(
            values=[1, None, 3], dates=["2020-01-01", "2020-01-02", "2020-01-03"]
        )
        assert series.n_missing == 1
        clean = series.without_missing()
        np.testing.assert_array_equal(clean.values, [1, 3])
        assert list(clean.dates.astype(str)) == ["2020-01-01", "2020-01-03"]
        assert series.n_missing == 1  # the original is untouched

    def test_python_dates_and_numpy_arrays_are_accepted(self):
        """Library users may pass ``date`` objects or arrays."""
        import datetime as dt

        series = load_series(
            values=np.array([1.0, 2.0]),
            dates=[dt.date(2020, 1, 1), dt.date(2020, 1, 2)],
        )
        assert list(series.dates.astype(str)) == ["2020-01-01", "2020-01-02"]
        arr = np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[D]")
        assert load_series(values=[1, 2], dates=arr).dates is not None

    def test_length_mismatch(self):
        """One date per value."""
        error = failure(
            lambda: load_series(values=[1, 2, 3], dates=["2020-01-01", "2020-01-02"]),
            InvalidParameterError,
        )
        assert error.details["reason"] == "length_mismatch"
        assert (error.details["dates"], error.details["values"]) == (2, 3)

    @pytest.mark.parametrize(
        "dates", [["2020-01-02", "2020-01-01"], ["2020-01-01", "2020-01-01"]]
    )
    def test_dates_must_strictly_increase(self, dates):
        """Unsorted or duplicate dates would corrupt time-series statistics."""
        error = failure(
            lambda: load_series(values=[1, 2], dates=dates), InvalidParameterError
        )
        assert error.details["reason"] == "dates_not_increasing"
        assert error.details["row"] == 2

    def test_bad_values_name_their_index(self):
        """A non-numeric item is located."""
        error = failure(lambda: load_series(values=[1, "x", 3]), InvalidParameterError)
        assert error.details["option"] == "values"
        assert error.details["index"] == 1

    def test_empty_values(self):
        """A series needs at least one value."""
        error = failure(lambda: load_series(values=[]), InvalidParameterError)
        assert error.details["reason"] == "empty"

    def test_bad_inline_date(self):
        """An inline date that is not ISO names the option."""
        error = failure(
            lambda: load_series(values=[1], dates=["01.01.2020"]), InvalidParameterError
        )
        assert error.details["option"] == "dates"
        assert error.details["reason"] == "bad_date"

    def test_datetime_objects_must_be_midnight(self):
        """``datetime`` values are dates only when they have no time of day."""
        import datetime as dt

        series = load_series(
            values=[1, 2],
            dates=[dt.datetime(2020, 1, 1), np.datetime64("2020-01-02")],
        )
        assert list(series.dates.astype(str)) == ["2020-01-01", "2020-01-02"]
        error = failure(
            lambda: load_series(values=[1], dates=[dt.datetime(2020, 1, 1, 8)]),
            InvalidParameterError,
        )
        assert error.details["reason"] == "bad_date"

    def test_nat_in_a_datetime_array_is_rejected(self):
        """An array with a missing date is not a series index."""
        dates = np.array(["2020-01-01", "NaT"], dtype="datetime64[D]")
        error = failure(
            lambda: load_series(values=[1, 2], dates=dates), InvalidParameterError
        )
        assert (error.details["reason"], error.details["row"]) == ("bad_date", 2)

    def test_values_must_be_a_list_of_numbers(self):
        """Text and matrices are not value lists."""
        for values in ("1,2,3", np.zeros((2, 2)), 5):
            error = failure(
                lambda values=values: load_series(values=values), InvalidParameterError
            )
            assert error.details["option"] == "values"
            assert error.details["reason"] == "type"


class TestLoadSeriesFile:
    """Series from files, including the IMGWTools export."""

    def test_imgwtools_export_loads_without_preprocessing(self):
        """The CSV of ``imgwtools series export`` (units in headers, flags, CRLF)."""
        series = load_series(
            input_file=IMGW_EXPORT, value_column="Q [m3/s]", date_column="date"
        )
        expected = [
            2.5,
            2.7,
            3.0,
            3.6,
            4.8,
            7.1,
            11.4,
            np.nan,
            np.nan,
            7.9,
            5.6,
            4.4,
            3.5,
            3.0,
        ]
        np.testing.assert_array_equal(series.values, np.array(expected))
        assert series.n_missing == 2
        assert str(series.dates[0]) == "2023-11-01"
        assert str(series.dates[-1]) == "2023-11-14"
        assert series.source == str(IMGW_EXPORT)

    def test_short_column_names_work_for_the_export(self):
        """``Q`` and ``H`` stand for ``Q [m3/s]`` and ``H [cm]``."""
        q = load_series(input_file=IMGW_EXPORT, value_column="Q", date_column="date")
        h = load_series(input_file=IMGW_EXPORT, value_column="H", date_column="date")
        assert q.values[0] == 2.5
        assert h.values[0] == 150.0
        np.testing.assert_array_equal(q.dates, h.dates)

    def test_missing_days_can_be_dropped_with_aligned_dates(self):
        """Empty export cells (flag ``missing``) become NaN and can be removed."""
        series = load_series(
            input_file=IMGW_EXPORT, value_column="Q", date_column="date"
        )
        clean = series.without_missing()
        assert len(clean) == 12
        assert "2023-11-08" not in clean.dates.astype(str)
        assert "2023-11-09" not in clean.dates.astype(str)

    def test_export_without_date_column_has_no_dates(self):
        """Dates are loaded only when asked for."""
        series = load_series(input_file=IMGW_EXPORT, value_column="Q")
        assert series.dates is None

    def test_missing_value_column_lists_available(self):
        """A wrong column is a data error with the columns of the file."""
        error = failure(lambda: load_series(input_file=IMGW_EXPORT, value_column="Z"))
        assert error.details["reason"] == "missing_column"
        assert error.details["option"] == "value_column"
        assert "date" in error.details["available"]

    def test_missing_date_column(self):
        """The same for the date column."""
        error = failure(
            lambda: load_series(
                input_file=IMGW_EXPORT, value_column="Q", date_column="day"
            )
        )
        assert error.details["option"] == "date_column"

    def test_non_numeric_column_is_located(self):
        """Reading a text column as values points at the first bad cell."""
        error = failure(
            lambda: load_series(input_file=IMGW_EXPORT, value_column="Q_flag")
        )
        assert error.details["reason"] == "bad_number"
        assert error.details["row"] == 1
        assert error.details["value"] == "value"

    def test_missing_file(self, tmp_path):
        """A file that is not there is ``not_found``."""
        error = failure(
            lambda: load_series(input_file=tmp_path / "x.csv", value_column="Q"),
            NotFoundError,
        )
        assert error.code == "not_found"

    def test_semicolon_decimal_comma_bom_file(self, tmp_path):
        """A typical Polish Excel export loads."""
        content = (
            "\ufeffdata;przepływ [m3/s]\n2020-01-01;1,5\n2020-01-02;\n2020-01-03;2,5\n"
        )
        path = write(tmp_path, "pl.csv", content)
        series = load_series(
            input_file=path, value_column="przepływ", date_column="data"
        )
        np.testing.assert_array_equal(series.values, [1.5, np.nan, 2.5])
        assert str(series.dates[1]) == "2020-01-02"

    def test_single_column_file_needs_no_value_column(self, tmp_path):
        """With one column the name can be left out."""
        path = write(tmp_path, "one.csv", "flow\n1\n2\n3\n")
        np.testing.assert_array_equal(load_series(input_file=path).values, [1, 2, 3])

    def test_several_columns_require_value_column(self, tmp_path):
        """Guessing between columns would be dangerous."""
        path = write(tmp_path, "two.csv", "a,b\n1,2\n")
        error = failure(lambda: load_series(input_file=path), InvalidParameterError)
        assert error.details["option"] == "value_column"
        assert error.details["available"] == ["a", "b"]

    def test_require_dates_for_files(self):
        """Operations that need dates insist on ``date_column``."""
        error = failure(
            lambda: load_series(
                input_file=IMGW_EXPORT, value_column="Q", require_dates=True
            ),
            InvalidParameterError,
        )
        assert error.details == {"option": "date_column", "reason": "required"} | {
            k: v for k, v in error.details.items() if k not in ("option", "reason")
        }

    def test_file_dates_must_strictly_increase(self, tmp_path):
        """Unsorted files are rejected with the offending row."""
        path = write(tmp_path, "u.csv", "d,v\n2020-01-02,1\n2020-01-01,2\n")
        error = failure(
            lambda: load_series(input_file=path, value_column="v", date_column="d")
        )
        assert error.details["reason"] == "dates_not_increasing"
        assert error.details["row"] == 2
        assert error.details["path"] == str(path)

    def test_header_only_file_has_no_data(self, tmp_path):
        """No rows means no series."""
        path = write(tmp_path, "h.csv", "d,v\n")
        error = failure(
            lambda: load_series(input_file=path, value_column="v", date_column="d")
        )
        assert error.details["reason"] == "empty"

    def test_json_files(self, tmp_path):
        """Plain list, object of columns and list of records all load."""
        plain = write(tmp_path, "plain.json", "[1, 2, null]")
        np.testing.assert_array_equal(
            load_series(input_file=plain).values, [1, 2, np.nan]
        )
        columns = write(
            tmp_path, "cols.json", '{"q": [1, 2], "d": ["2020-01-01", "2020-01-02"]}'
        )
        series = load_series(input_file=columns, value_column="q", date_column="d")
        assert list(series.dates.astype(str)) == ["2020-01-01", "2020-01-02"]
        records = write(
            tmp_path,
            "rec.json",
            '[{"d": "2020-01-01", "q": 1}, {"d": "2020-01-02", "q": 2.5}]',
        )
        np.testing.assert_array_equal(
            load_series(input_file=records, value_column="q", date_column="d").values,
            [1, 2.5],
        )


class TestLoadSeriesArguments:
    """Combinations of inline and file arguments."""

    def test_nothing_given(self):
        """One source is required."""
        error = failure(lambda: load_series(), InvalidParameterError)
        assert error.details["reason"] == "one_of"
        assert error.details["groups"] == [
            ["values", "dates"],
            ["input_file", "value_column"],
        ]

    def test_both_sources_given(self):
        """Inline values and a file are ambiguous."""
        error = failure(
            lambda: load_series(values=[1], input_file=IMGW_EXPORT, value_column="Q"),
            InvalidParameterError,
        )
        assert error.details["reason"] == "one_of"

    def test_dates_alone_are_not_a_series(self):
        """Dates need values."""
        error = failure(
            lambda: load_series(dates=["2020-01-01"]), InvalidParameterError
        )
        assert error.details == {"option": "values", "reason": "required"}

    def test_file_options_conflict_with_inline_values(self):
        """``value_column`` makes no sense without a file."""
        for kwargs, option in (
            ({"value_column": "Q"}, "value_column"),
            ({"date_column": "d"}, "date_column"),
        ):
            error = failure(
                lambda kwargs=kwargs: load_series(values=[1], **kwargs),
                InvalidParameterError,
            )
            assert error.details == {"option": option, "reason": "conflict"}


# --- watershed ------------------------------------------------------------------------


class TestLoadWatershed:
    """``load_watershed``."""

    def test_inline_object(self):
        """An inline object becomes parameters; unknown keys are ignored."""
        params = load_watershed(watershed={**WATERSHED, "comment": "ignored"})
        assert isinstance(params, WatershedParameters)
        assert params.area_km2 == 45.3
        assert params.cn == 72
        assert params.name == "Testowa"
        assert params.relief_m == 370.0

    def test_file_in_to_json_format(self, tmp_path):
        """The ``WatershedParameters.to_json()`` file format round-trips."""
        original = WatershedParameters.from_dict(WATERSHED)
        path = write(tmp_path, "ws.json", original.to_json(indent=2))
        assert load_watershed(watershed_file=path) == original

    def test_exactly_one_source(self, tmp_path):
        """Both or neither source is a validation error."""
        path = write(tmp_path, "ws.json", json.dumps(WATERSHED))
        for kwargs in ({}, {"watershed": WATERSHED, "watershed_file": path}):
            error = failure(
                lambda kwargs=kwargs: load_watershed(**kwargs), InvalidParameterError
            )
            assert error.details["reason"] == "one_of"

    def test_missing_required_parameters_inline(self):
        """Missing keys are listed; for an inline object the error names the option."""
        data = {
            k: v for k, v in WATERSHED.items() if k not in ("area_km2", "length_km")
        }
        error = failure(lambda: load_watershed(watershed=data), InvalidParameterError)
        assert error.details["option"] == "watershed"
        assert error.details["reason"] == "missing_field"
        assert error.details["missing"] == ["area_km2", "length_km"]
        assert "area_km2, perimeter_km" in error.hint

    def test_missing_required_parameters_in_a_file(self, tmp_path):
        """The same problem in a file is a data error naming the file."""
        path = write(tmp_path, "ws.json", json.dumps({"area_km2": 1.0}))
        error = failure(lambda: load_watershed(watershed_file=path))
        assert error.code == "data_error"
        assert error.details["path"] == str(path)
        assert error.details["missing"] == [
            "perimeter_km",
            "length_km",
            "elevation_min_m",
            "elevation_max_m",
        ]

    def test_null_required_value_counts_as_missing(self):
        """``null`` for a required parameter is a missing parameter."""
        error = failure(
            lambda: load_watershed(watershed={**WATERSHED, "area_km2": None}),
            InvalidParameterError,
        )
        assert error.details["missing"] == ["area_km2"]

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("area_km2", "45"),
            ("cn", True),
            ("perimeter_km", [1]),
            ("name", 5),
            ("crs", 2180),
        ],
    )
    def test_wrong_types_name_the_field(self, field, value):
        """Strings where numbers belong (and vice versa) are named, not crashes."""
        error = failure(
            lambda: load_watershed(watershed={**WATERSHED, field: value}),
            InvalidParameterError,
        )
        assert error.details["reason"] == "type"
        assert error.details["field"] == field

    def test_non_finite_number_is_rejected(self):
        """NaN passes ``x <= 0`` checks silently, so it is rejected here."""
        error = failure(
            lambda: load_watershed(watershed={**WATERSHED, "area_km2": float("nan")}),
            InvalidParameterError,
        )
        assert error.details["field"] == "area_km2"

    def test_invalid_values_keep_the_library_message(self, tmp_path):
        """Range checks of ``WatershedParameters`` surface as validation/data errors."""
        error = failure(
            lambda: load_watershed(watershed={**WATERSHED, "area_km2": -1}),
            InvalidParameterError,
        )
        assert error.details == {"option": "watershed", "reason": "invalid_value"}
        assert "area_km2 must be positive" in str(error)
        path = write(tmp_path, "ws.json", json.dumps({**WATERSHED, "cn": 120}))
        error = failure(lambda: load_watershed(watershed_file=path))
        assert error.details["reason"] == "invalid_value"
        assert "cn must be 0-100" in str(error)

    def test_file_that_is_not_an_object(self, tmp_path):
        """A JSON list is not a watershed."""
        path = write(tmp_path, "ws.json", "[1, 2]")
        assert (
            failure(lambda: load_watershed(watershed_file=path)).details["reason"]
            == "shape"
        )

    def test_file_errors(self, tmp_path):
        """Missing and malformed files."""
        assert failure(
            lambda: load_watershed(watershed_file=tmp_path / "x.json"), NotFoundError
        )
        path = write(tmp_path, "bad.json", "{")
        assert (
            failure(lambda: load_watershed(watershed_file=path)).details["reason"]
            == "invalid_json"
        )

    def test_unexpected_library_value_error_becomes_a_data_error(
        self, tmp_path, monkeypatch
    ):
        """A ``ValueError`` from the library is reported as invalid parameters."""

        def boom(data):
            raise ValueError("odd combination")

        monkeypatch.setattr(WatershedParameters, "from_dict", staticmethod(boom))
        error = failure(
            lambda: load_watershed(watershed=WATERSHED), InvalidParameterError
        )
        assert error.details == {"option": "watershed", "reason": "invalid_value"}
        assert "odd combination" in str(error)


# --- stations -------------------------------------------------------------------------

STATION_ROWS = [
    {"name": "A", "x": 1.0, "y": 2.0, "precipitation_mm": 10.5},
    {"name": "B", "x": 3.0, "y": 4.0, "precipitation_mm": 12.0, "elevation_m": 250.0},
]


class TestLoadStations:
    """``load_stations``."""

    def test_inline_records(self):
        """Records become ``Station`` objects in order; elevation is optional."""
        stations = load_stations(stations=STATION_ROWS)
        assert stations == [
            Station("A", 1.0, 2.0, 10.5),
            Station("B", 3.0, 4.0, 12.0, elevation_m=250.0),
        ]

    def test_station_id_is_an_alias_of_name(self):
        """``asdict(Station)`` output loads as it is."""
        rows = [{"station_id": 7, "x": 1, "y": 2, "precipitation_mm": 3}]
        assert load_stations(stations=rows)[0].station_id == "7"

    def test_csv_file_with_semicolons_and_decimal_commas(self, tmp_path):
        """Polish CSV: ``name;x;y;precipitation_mm;elevation_m``."""
        content = (
            "name;x;y;precipitation_mm;elevation_m\n"
            "Kraków;1,5;2,5;10,25;220\n"
            "Łódź;3;4;11;\n"
        )
        path = write(tmp_path, "s.csv", content)
        assert load_stations(stations_file=path) == [
            Station("Kraków", 1.5, 2.5, 10.25, 220.0),
            Station("Łódź", 3.0, 4.0, 11.0, None),
        ]

    def test_json_file(self, tmp_path):
        """A JSON list of records."""
        path = write(tmp_path, "s.json", json.dumps(STATION_ROWS))
        assert [s.station_id for s in load_stations(stations_file=path)] == ["A", "B"]

    def test_missing_columns_are_listed(self, tmp_path):
        """A file without ``y`` and ``precipitation_mm`` says so."""
        path = write(tmp_path, "s.csv", "name,x\nA,1\n")
        error = failure(lambda: load_stations(stations_file=path))
        assert error.details["reason"] == "missing_column"
        assert error.details["missing"] == ["y", "precipitation_mm"]
        assert error.details["available"] == ["name", "x"]

    def test_missing_name_column(self, tmp_path):
        """The name column is required too."""
        path = write(tmp_path, "s.csv", "x,y,precipitation_mm\n1,2,3\n")
        assert failure(lambda: load_stations(stations_file=path)).details[
            "missing"
        ] == ["name"]

    def test_bad_number_names_row_and_field(self, tmp_path):
        """The first bad value is located."""
        path = write(
            tmp_path, "s.csv", "name,x,y,precipitation_mm\nA,1,2,3\nB,1,two,3\n"
        )
        error = failure(lambda: load_stations(stations_file=path))
        assert (
            error.details["reason"],
            error.details["row"],
            error.details["field"],
        ) == (
            "bad_number",
            2,
            "y",
        )

    def test_empty_required_value_is_missing(self, tmp_path):
        """An empty precipitation cell cannot be interpolated."""
        path = write(tmp_path, "s.csv", "name,x,y,precipitation_mm\nA,1,2,\n")
        error = failure(lambda: load_stations(stations_file=path))
        assert error.details["reason"] == "missing_field"
        assert error.details["missing"] == ["precipitation_mm"]

    def test_inline_errors_name_the_option(self):
        """Inline records report ``option='stations'``."""
        error = failure(
            lambda: load_stations(stations=[{"name": "A", "x": 1, "y": 2}]),
            InvalidParameterError,
        )
        assert error.details["option"] == "stations"
        assert error.details["missing"] == ["precipitation_mm"]
        error = failure(
            lambda: load_stations(stations=[{"x": 1}]), InvalidParameterError
        )
        assert error.details["missing"] == ["name"]
        error = failure(lambda: load_stations(stations=["A"]), InvalidParameterError)
        assert error.details["reason"] == "shape"

    def test_duplicate_station_names(self):
        """Station ids are unique (Thiessen areas are keyed by them)."""
        error = failure(
            lambda: load_stations(stations=[STATION_ROWS[0], dict(STATION_ROWS[0])]),
            InvalidParameterError,
        )
        assert error.details["reason"] == "duplicate_station"
        assert error.details["row"] == 2

    def test_no_stations(self):
        """An empty list is an error."""
        assert (
            failure(lambda: load_stations(stations=[]), InvalidParameterError).details[
                "reason"
            ]
            == "empty"
        )

    def test_exactly_one_source(self, tmp_path):
        """Both or neither source is a validation error."""
        path = write(tmp_path, "s.json", json.dumps(STATION_ROWS))
        for kwargs in ({}, {"stations": STATION_ROWS, "stations_file": path}):
            error = failure(
                lambda kwargs=kwargs: load_stations(**kwargs), InvalidParameterError
            )
            assert error.details["reason"] == "one_of"

    def test_stations_must_be_a_list(self):
        """A string or a mapping is not a list of stations."""
        for stations in ("A", {"name": "A"}):
            error = failure(
                lambda stations=stations: load_stations(stations=stations),
                InvalidParameterError,
            )
            assert error.details["reason"] == "type"

    def test_missing_file(self, tmp_path):
        """A missing file is ``not_found``."""
        assert failure(
            lambda: load_stations(stations_file=tmp_path / "x.csv"), NotFoundError
        )
