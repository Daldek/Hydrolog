"""Group ``stats``: statistics of hydrological series.

Characteristic values, daily and monthly statistics, flood frequency, low-flow
frequency and sequences, and the Mann-Kendall trend test. The operations are in
:mod:`hydrolog.operations.stats`.
"""

from __future__ import annotations

from dataclasses import replace

from hydrolog.catalog.groups._series import (
    DATE_COLUMN,
    DATED_ONE_OF,
    DATED_OPTIONS,
    DATES,
    INPUT_FILE,
    VALUE_COLUMN,
    VALUES,
)
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"
_IMGW_EXPORT = f"{_FIXTURES}/imgwtools_series_export.csv"
_DAILY_FLOWS = f"{_FIXTURES}/daily_flows_3y.csv"
_ANNUAL_MAXIMA = f"{_FIXTURES}/annual_maxima.csv"

_RETURN_PERIODS = Option(
    name="return_periods",
    type="number_list",
    description_pl=(
        "Okresy powtarzalności T [lata], każdy większy od 1; domyślnie 2, 5, 10, 20, "
        "50, 100, 500, 1000."
    ),
    description=(
        "Return periods T [years], each greater than 1; default 2, 5, 10, 20, 50, "
        "100, 500, 1000."
    ),
    default=(2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0),
    exclusive_minimum=1,
)

# Series whose values are not dated: annual maxima or a series ordered in time.
_UNDATED_ONE_OF = (("values",), ("input_file", "value_column"))

COMMANDS: tuple[Command, ...] = (
    Command(
        name="stats characteristic",
        operation_id="hydrolog_stats_characteristic",
        summary_pl=(
            "Oblicz wartości charakterystyczne II stopnia (WWQ…NNQ) z szeregu dobowego"
        ),
        summary=(
            "Compute second-degree characteristic values (WWQ…NNQ) of a daily series"
        ),
        description_pl=(
            "Wartości charakterystyczne szeregu dobowego przepływów Q albo stanów H"
            " wg IMGW-PIB, po latach hydrologicznych (XI–X): największa, średnia, "
            "mediana i najmniejsza z maksimów, średnich i minimów rocznych. Do "
            "tabel WWQ…NNQ; kwantyle wezbrań daje `stats flood-frequency`. Wymaga "
            "dat; NaN jest pomijane."
        ),
        description=(
            "Characteristic values of a daily discharge Q or stage H series per "
            "IMGW-PIB, by hydrological year (Nov–Oct): highest, mean, median and "
            "lowest of the annual maxima, means and minima. Use for WWQ…NNQ tables;"
            " for flood quantiles use `stats flood-frequency`. Needs dates; NaN is "
            "skipped."
        ),
        result_schema="hydrolog-stats-characteristic/1",
        rules=(
            "Give dates with the values, or a file with a date column.",
            "Check `notices` for skipped missing values.",
            (
                "Results are in the unit of the series; `period_years` counts partial "
                "years."
            ),
        ),
        rules_pl=(
            "Podaj daty z wartościami albo plik z kolumną dat.",
            "Sprawdź `notices` pod kątem pominiętych braków danych.",
            ("Wyniki są w jednostce szeregu; `period_years` liczy też lata niepełne."),
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "wwx": 11.4,
                "wsx": 4.95833,
                "wnx": 2.5,
                "period_years": 1,
                "parameter": "Q",
            },
            {
                "wwx": 24.93,
                "swx": 20.0133,
                "nwx": 13.99,
                "period_years": 3,
                "parameter": "Q",
            },
        ),
        function="hydrolog.operations.stats_characteristic",
        options=(
            *DATED_OPTIONS,
            Option(
                name="parameter",
                type="choice",
                description_pl=(
                    "Etykieta szeregu; nie wpływa na obliczenia, tylko na opis wyniku."
                ),
                description=(
                    "Series label; it does not affect the computation, only the "
                    "label of the result."
                ),
                choices=("Q", "H"),
                meanings={
                    "Q": "Discharge series (values WWQ…NNQ).",
                    "H": "Stage series (values WWH…NNH).",
                },
                meanings_pl={
                    "Q": "Szereg przepływów (wartości WWQ…NNQ).",
                    "H": "Szereg stanów wody (wartości WWH…NNH).",
                },
                default="Q",
            ),
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _IMGW_EXPORT,
                "value_column": "Q",
                "date_column": "date",
                "parameter": "Q",
            },
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
            },
        ),
    ),
    Command(
        name="stats daily",
        operation_id="hydrolog_stats_daily",
        summary_pl=("Oblicz statystyki dobowe z wielolecia szeregu dobowego"),
        summary=("Compute day-of-year statistics over all years of a daily series"),
        description_pl=(
            "Maksimum, średnia, mediana, minimum i liczba obserwacji dla każdej "
            "doby roku hydrologicznego (1 = 1 XI, do 366) ze wszystkich lat. Do "
            "krzywych reżimu dobowego; wartości miesięczne daje `stats monthly`. "
            "Wymaga dat; NaN jest pomijane. Wynik to tablice o jednakowej długości."
        ),
        description=(
            "Maximum, mean, median, minimum and count for each day of the "
            "hydrological year (1 = 1 Nov, up to 366) over all years. Use for daily"
            " regime curves; for monthly values use `stats monthly`. Needs dates; "
            "NaN is skipped. The result is arrays of equal length."
        ),
        result_schema="hydrolog-stats-daily/1",
        cardinality="bounded",
        rules=(
            "Give dates with the values, or a file with a date column.",
            "Check `notices` for skipped missing values.",
            "Days without observations are absent from the arrays.",
        ),
        rules_pl=(
            "Podaj daty z wartościami albo plik z kolumną dat.",
            "Sprawdź `notices` pod kątem pominiętych braków danych.",
            "Doby bez obserwacji nie występują w tablicach.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "day_of_year": [1.0, 2.0, 3.0],
                "max_values": [2.88, 2.67, 7.7],
                "min_values": [2.57, 2.58, 2.64],
                "count": [3.0, 3.0, 3.0],
            },
        ),
        function="hydrolog.operations.stats_daily",
        options=DATED_OPTIONS,
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
            },
        ),
    ),
    Command(
        name="stats monthly",
        operation_id="hydrolog_stats_monthly",
        summary_pl=(
            "Oblicz statystyki miesięczne z przedziałem ufności średniej (t-Studenta)"
        ),
        summary=(
            "Compute monthly statistics with a t-Student confidence interval of the"
            " mean"
        ),
        description_pl=(
            "Dla miesięcy 1–12: maksimum, średnia, mediana, minimum, odchylenie "
            "standardowe, współczynnik zmienności, skośność i przedział ufności "
            "średniej. Do tabel reżimu miesięcznego; wartości dobowe daje `stats "
            "daily`. Wymaga dat i wartości we wszystkich 12 miesiącach."
        ),
        description=(
            "For months 1–12: maximum, mean, median, minimum, standard deviation, "
            "variation coefficient, skewness and the confidence interval of the "
            "mean. Use for monthly regime tables; for daily values use `stats "
            "daily`. Needs dates and values in all 12 months."
        ),
        result_schema="hydrolog-stats-monthly/1",
        cardinality="bounded",
        rules=(
            (
                "Give values for all 12 months, otherwise a calculation_error is "
                "returned."
            ),
            (
                "Check `notices` for `single_value_month`: such a month has null spread"
                " values."
            ),
            "Results are in the unit of the series.",
        ),
        rules_pl=(
            (
                "Podaj wartości ze wszystkich 12 miesięcy, inaczej wystąpi "
                "calculation_error."
            ),
            (
                "Sprawdź `notices` (`single_value_month`): taki miesiąc ma `null` w "
                "miarach rozrzutu."
            ),
            "Wyniki są w jednostce szeregu.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "months": [1.0, 2.0, 3.0],
                "mean_values": [6.09946, 6.86659, 7.22269],
                "ci_lower": [5.98154, 6.71963, 7.10644],
                "confidence_level": 0.9,
            },
        ),
        function="hydrolog.operations.stats_monthly",
        options=(
            *DATED_OPTIONS,
            Option(
                name="confidence_level",
                type="number",
                description_pl=(
                    "Poziom ufności przedziału średniej, z przedziału otwartego "
                    "(0, 1), np. 0,95."
                ),
                description=(
                    "Confidence level of the interval of the mean, in the open "
                    "interval (0, 1), e.g. 0.95."
                ),
                default=0.95,
                exclusive_minimum=0,
                maximum=1,
            ),
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
                "confidence_level": 0.9,
            },
        ),
    ),
    Command(
        name="stats flood-frequency",
        operation_id="hydrolog_stats_flood_frequency",
        summary_pl=(
            "Oblicz kwantyle wezbrań dla okresów powtarzalności z maksimów rocznych"
        ),
        summary=("Compute flood quantiles for return periods from annual maxima"),
        description_pl=(
            "Dopasowuje rozkłady log-normalny, GEV, Pearsona III i Weibulla do "
            "maksimów rocznych (największa wiarygodność) i podaje kwantyle z "
            "miarami zgodności (KS, A², AIC). Do przepływów miarodajnych z maksimów"
            " rocznych albo szeregu dobowego; niżówki: `stats low-flow`. Lata z "
            "brakami dni są pomijane."
        ),
        description=(
            "Fits log-normal, GEV, Pearson III and Weibull distributions to annual "
            "maxima (maximum likelihood) and gives quantiles with goodness-of-fit "
            "(KS, A², AIC). Use for design discharges from annual maxima or a daily"
            " series; for low flows use `stats low-flow`."
        ),
        result_schema="hydrolog-stats-flood-frequency/1",
        cardinality="bounded",
        rules=(
            ("Pass annual maxima without dates, or a daily series with dates."),
            (
                "Check `notices` for `incomplete_years` and samples shorter than 30 "
                "years."
            ),
            (
                "Rank distributions by `aic`; `ks_valid=false` means the KS p-value is "
                "indicative."
            ),
        ),
        rules_pl=(
            "Podaj maksima roczne bez dat albo szereg dobowy z datami.",
            ("Sprawdź `notices`: `incomplete_years` i próby krótsze niż 30 lat."),
            (
                "Porządkuj rozkłady wg `aic`; `ks_valid=false` oznacza orientacyjne "
                "p-value KS."
            ),
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        core=True,
        example_results=(
            {"n_years": 35, "best_distribution": "log_normal"},
            {
                "n_years": 3,
                "annual_maxima": [21.12, 13.99, 24.93],
                "hydrological_years": [2022, 2023, 2024],
                "best_distribution": "gev",
            },
        ),
        function="hydrolog.operations.stats_flood_frequency",
        options=(
            replace(
                VALUES,
                description_pl=(
                    "Szereg w kolejności czasowej: maksima roczne (bez `dates`) albo "
                    "wartości dobowe (z `dates`; maksima roczne są wtedy wybierane dla "
                    "kompletnych lat hydrologicznych XI–X). Długie szeregi podawaj w "
                    "pliku (`input_file`)."
                ),
                description=(
                    "Series in time order: annual maxima (without `dates`) or daily "
                    "values (with `dates`; the annual maxima are then taken for the "
                    "complete hydrological years Nov–Oct). Give long series in a file "
                    "(`input_file`)."
                ),
            ),
            replace(
                DATES,
                description_pl=(
                    "Daty wartości dobowych w formacie ISO `RRRR-MM-DD`, ściśle "
                    "rosnące, tyle samo co `values`; pomiń, gdy `values` to maksima "
                    "roczne."
                ),
                description=(
                    "Dates of daily values in ISO format `YYYY-MM-DD`, strictly "
                    "increasing, as many as `values`; omit when `values` are annual "
                    "maxima."
                ),
            ),
            INPUT_FILE,
            VALUE_COLUMN,
            replace(
                DATE_COLUMN,
                description_pl=(
                    "Nazwa kolumny z datami ISO w `input_file` (np. `date`); podaj "
                    "dla szeregu dobowego, pomiń dla maksimów rocznych."
                ),
                description=(
                    "Name of the column with ISO dates in `input_file` (e.g. `date`); "
                    "give it for a daily series, omit it for annual maxima."
                ),
            ),
            Option(
                name="distribution",
                type="choice",
                description_pl=("Rozkład do dopasowania."),
                description=("Distribution to fit."),
                choices=("all", "log_normal", "gev", "pearson3", "weibull"),
                meanings={
                    "all": "Fit the four distributions, sorted by AIC.",
                    "log_normal": "Log-normal, 2 parameters, location 0.",
                    "gev": "Generalized extreme value.",
                    "pearson3": "Pearson type III.",
                    "weibull": "Weibull.",
                },
                meanings_pl={
                    "all": "Dopasuj cztery rozkłady, posortowane wg AIC.",
                    "log_normal": "Log-normalny, 2 parametry, położenie 0.",
                    "gev": "Uogólniony rozkład wartości ekstremalnych (GEV).",
                    "pearson3": "Pearsona typu III.",
                    "weibull": "Weibulla.",
                },
                default="all",
            ),
            _RETURN_PERIODS,
        ),
        one_of=_UNDATED_ONE_OF,
        examples=(
            {
                "input_file": _ANNUAL_MAXIMA,
                "value_column": "Qmax",
                "distribution": "all",
                "return_periods": [10, 50, 100],
            },
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
                "distribution": "gev",
            },
        ),
    ),
    Command(
        name="stats low-flow",
        operation_id="hydrolog_stats_low_flow",
        summary_pl=(
            "Oblicz kwantyle niżówek dla okresów powtarzalności z minimów rocznych"
        ),
        summary=("Compute low-flow quantiles for return periods from annual minima"),
        description_pl=(
            "Dopasowuje rozkład Fishera–Tippetta (GEV dla minimów) do minimów "
            "rocznych i podaje kwantyle niskich przepływów (osiągane lub niższe raz"
            " na T lat). Do częstości niżówek; wezbrania: `stats flood-frequency`, "
            "zdarzenia suszy: `stats low-flow-sequences`. Wymaga dat."
        ),
        description=(
            "Fits the Fisher–Tippett (GEV for minima) distribution to annual minima"
            " and gives low-flow quantiles (flow reached or undercut once in T "
            "years). Use for low-flow frequency; for floods use `stats "
            "flood-frequency`, for drought events `stats low-flow-sequences`. Needs"
            " dates."
        ),
        result_schema="hydrolog-stats-low-flow/1",
        cardinality="bounded",
        rules=(
            ("Give a daily series with dates; years with a missing day are skipped."),
            (
                "Check `notices` for `incomplete_years` and samples shorter than 10 "
                "years."
            ),
            "At least 3 complete hydrological years are required.",
        ),
        rules_pl=(
            ("Podaj szereg dobowy z datami; lata z brakującym dniem są pomijane."),
            ("Sprawdź `notices`: `incomplete_years` i próby krótsze niż 10 lat."),
            "Wymagane są co najmniej 3 kompletne lata hydrologiczne.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "n_years": 3,
                "hydrological_years": [2022, 2023, 2024],
                "annual_minima": [1.79, 1.88, 1.66],
                "incomplete_years": [],
            },
        ),
        function="hydrolog.operations.stats_low_flow",
        options=(*DATED_OPTIONS, _RETURN_PERIODS),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
                "return_periods": [2, 10, 50],
            },
        ),
    ),
    Command(
        name="stats low-flow-sequences",
        operation_id="hydrolog_stats_low_flow_sequences",
        summary_pl=("Wykryj ciągi niżówkowe (susze) poniżej progu"),
        summary=("Detect low-flow (drought) sequences below a threshold"),
        description_pl=(
            "Metoda poziomu progowego: ciągi dób poniżej `threshold`, łączone przez"
            " krótkie przerwy, z datami początku i końca, czasem trwania, minimum, "
            "średnią i niedoborem. Do zdarzeń suszy; częstość minimów rocznych: "
            "`stats low-flow`. Wymaga kompletnego szeregu dobowego bez NaN."
        ),
        description=(
            "Threshold level method: runs of days below `threshold`, merged across "
            "short gaps, with start and end dates, duration, minimum, mean and "
            "deficit. Use for drought events; for frequency of annual minima use "
            "`stats low-flow`. Needs a complete daily series without NaN."
        ),
        result_schema="hydrolog-stats-low-flow-sequences/1",
        cardinality="bounded",
        rules=(
            "Pass consecutive daily dates without gaps and without NaN.",
            "Give `threshold` in the unit of the series.",
            "Deficit is in series unit × day.",
        ),
        rules_pl=(
            "Podaj kolejne daty dobowe bez luk i bez NaN.",
            "Podaj `threshold` w jednostce szeregu.",
            "Niedobór jest w jednostce szeregu × doba.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "threshold": 2.2,
                "n_days": 1096,
                "n_events": 7,
                "total_deficit": 23.78,
                "max_duration_days": 48,
            },
        ),
        function="hydrolog.operations.stats_low_flow_sequences",
        options=(
            VALUES,
            replace(
                DATES,
                description_pl=(
                    "Daty kolejnych dób w formacie ISO `RRRR-MM-DD`: kolejne dni, bez "
                    "luk; tyle samo co `values`."
                ),
                description=(
                    "Dates of consecutive days in ISO format `YYYY-MM-DD`: successive "
                    "days without gaps; as many as `values`."
                ),
            ),
            INPUT_FILE,
            VALUE_COLUMN,
            replace(
                DATE_COLUMN,
                description_pl=(
                    "Nazwa kolumny z datami ISO w `input_file` (np. `date`); daty "
                    "muszą być kolejnymi dniami, bez luk."
                ),
                description=(
                    "Name of the column with ISO dates in `input_file` (e.g. "
                    "`date`); the dates must be consecutive days without gaps."
                ),
            ),
            Option(
                name="threshold",
                type="number",
                description_pl=(
                    "Próg niżówkowy w jednostce szeregu (np. m³/s), dodatni; dni z "
                    "wartością poniżej progu tworzą niżówkę."
                ),
                description=(
                    "Low-flow threshold in the unit of the series (e.g. m³/s), "
                    "positive; days with a value below it make up a low-flow event."
                ),
                required=True,
                exclusive_minimum=0,
            ),
            Option(
                name="min_duration_days",
                type="integer",
                description_pl=(
                    "Najkrótszy raportowany ciąg niżówkowy w dobach, co najmniej 1."
                ),
                description=(
                    "Shortest low-flow sequence reported, in days, at least 1."
                ),
                default=5,
                minimum=1,
                unit="d",
            ),
            Option(
                name="max_gap_days",
                type="integer",
                description_pl=(
                    "Przerwy krótsze niż ta liczba dób między dwoma ciągami poniżej "
                    "progu łączą je w jeden ciąg; 0 wyłącza łączenie."
                ),
                description=(
                    "Gaps shorter than this number of days between two runs below the "
                    "threshold merge them into one sequence; 0 disables merging."
                ),
                default=4,
                minimum=0,
                unit="d",
            ),
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
                "threshold": 2.2,
                "min_duration_days": 5,
                "max_gap_days": 4,
            },
        ),
    ),
    Command(
        name="stats mann-kendall",
        operation_id="hydrolog_stats_mann_kendall",
        summary_pl=(
            "Zbadaj istnienie monotonicznego trendu w szeregu testem Manna–Kendalla"
        ),
        summary=("Test a series for a monotonic trend with the Mann–Kendall test"),
        description_pl=(
            "Nieparametryczny test Manna–Kendalla: statystyka S, Z, dwustronne "
            "p-value i kierunek trendu. Do oceny stacjonarności maksimów rocznych "
            "przed `stats flood-frequency`. Wymaga co najmniej 3 wartości w "
            "kolejności czasowej; NaN jest pomijane. Wariancja bez poprawki na "
            "powtórzenia (test nieco zachowawczy)."
        ),
        description=(
            "Non-parametric Mann–Kendall test: S statistic, Z, two-sided p-value "
            "and trend direction. Use to check stationarity of annual maxima before"
            " `stats flood-frequency`. Needs 3 or more values in time order; NaN is"
            " skipped. Variance has no tie correction (slightly conservative)."
        ),
        result_schema="hydrolog-stats-mann-kendall/1",
        rules=(
            "Pass values in time order, at least 3.",
            "A trend is detected when `p_value` is below `alpha`.",
            "Check `notices` for skipped missing values.",
        ),
        rules_pl=(
            "Podaj wartości w kolejności czasowej, co najmniej 3.",
            "Trend jest wykryty, gdy `p_value` jest mniejsze niż `alpha`.",
            "Sprawdź `notices` pod kątem pominiętych braków danych.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "s_statistic": -6.0,
                "p_value": 0.943392,
                "trend_detected": False,
                "trend_direction": "none",
                "significance_level": 0.05,
            },
            {
                "s_statistic": 29.0,
                "p_value": 0.0122661,
                "trend_detected": True,
                "trend_direction": "increasing",
                "significance_level": 0.05,
            },
        ),
        function="hydrolog.operations.stats_mann_kendall",
        options=(
            replace(
                VALUES,
                description_pl=(
                    "Szereg w kolejności czasowej, np. maksima roczne (co najmniej 3 "
                    "wartości). Długie szeregi podawaj w pliku (`input_file`)."
                ),
                description=(
                    "Series in time order, e.g. annual maxima (at least 3 values). "
                    "Give long series in a file (`input_file`)."
                ),
            ),
            replace(
                INPUT_FILE,
                description_pl=(
                    "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON z "
                    "szeregiem; wiersze w kolejności czasowej. Kolumnę wskazuje "
                    "`value_column`."
                ),
                description=(
                    "CSV file (comma or semicolon, header row) or JSON file with the "
                    "series; rows in time order. The column is named by "
                    "`value_column`."
                ),
            ),
            VALUE_COLUMN,
            Option(
                name="alpha",
                type="number",
                description_pl=(
                    "Poziom istotności testu z przedziału otwartego (0, 1), np. 0,05."
                ),
                description=(
                    "Significance level of the test, in the open interval (0, 1), "
                    "e.g. 0.05."
                ),
                default=0.05,
                exclusive_minimum=0,
                maximum=1,
            ),
        ),
        one_of=_UNDATED_ONE_OF,
        examples=(
            {
                "input_file": _ANNUAL_MAXIMA,
                "value_column": "Qmax",
                "alpha": 0.05,
            },
            {
                "values": [
                    312.0,
                    287.5,
                    401.2,
                    355.9,
                    298.4,
                    420.7,
                    389.1,
                    450.3,
                    433.8,
                    470.2,
                ],
            },
        ),
    ),
)
