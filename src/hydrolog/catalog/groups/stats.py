"""Group ``stats``: statistics of hydrological series.

Characteristic values, events beyond a level, duration curves, runoff volumes, daily
and monthly statistics, flood frequency, low-flow frequency and sequences, the
Mann-Kendall trend test and the homogeneity tests. The operations are in
:mod:`hydrolog.operations.stats`.
"""

from __future__ import annotations

from dataclasses import replace

from hydrolog.catalog.groups._attribution import ATTRIBUTION
from hydrolog.catalog.groups._series import (
    DATE_COLUMN,
    DATED_ONE_OF,
    DATED_OPTIONS,
    DATES,
    HALF_YEAR_FILE,
    INPUT_FILE,
    PERIOD_OPTIONS,
    VALUE_COLUMN,
    VALUES,
)
from hydrolog.catalog.spec import Command, Option, RangeCheck

_FIXTURES = "tests/fixtures"
_OBSERWATOR_EXPORT = f"{_FIXTURES}/obserwator_series_export.csv"
_DAILY_FLOWS = f"{_FIXTURES}/daily_flows_3y.csv"
_ANNUAL_MAXIMA = f"{_FIXTURES}/annual_maxima.csv"
_STATION_DAILY = f"{_FIXTURES}/station_daily.csv"
_STATION_HALF_YEARS = f"{_FIXTURES}/station_half_years.csv"

# Errors of the commands that read a dated daily series.
_STATION_ERRORS = (
    "validation_error",
    "not_found",
    "data_error",
    "calculation_error",
    "forbidden",
)

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

# The variable of IMGW-PIB's half-year file in the frequency commands (plan D9).
_HALF_YEAR_PARAMETER = Option(
    name="parameter",
    type="choice",
    description_pl=(
        "Zmienna pliku `half_year_file`: wskazuje jego kolumny; szeregu dobowego ani "
        "wartości nie zmienia."
    ),
    description=(
        "The variable of `half_year_file`: it picks its columns; it does not change a "
        "daily series or values."
    ),
    choices=("Q", "H"),
    meanings={
        "Q": "Discharge: the columns Q_min, Q_max.",
        "H": "Stage: the columns H_min, H_max.",
    },
    meanings_pl={
        "Q": "Przepływ: kolumny Q_min, Q_max.",
        "H": "Stan wody: kolumny H_min, H_max.",
    },
    default="Q",
)
# The annual extremes of a frequency command: values, a daily series or the half-years.
_ANNUAL_ONE_OF = (("values",), ("input_file", "value_column"), ("half_year_file",))

# Series whose values are not dated: annual maxima or a series ordered in time.
_UNDATED_ONE_OF = (("values",), ("input_file", "value_column"))

# The series of annual maxima: the maxima themselves, or a daily series whose complete
# hydrological years give them.
_ANNUAL_VALUES = replace(
    VALUES,
    description_pl=(
        "Szereg w kolejności czasowej: maksima roczne (bez `dates`) albo wartości "
        "dobowe (z `dates`; maksima roczne są wtedy wybierane dla kompletnych lat "
        "hydrologicznych XI–X). Długie szeregi podawaj w pliku (`input_file`)."
    ),
    description=(
        "Series in time order: annual maxima (without `dates`) or daily values (with "
        "`dates`; the annual maxima are then taken for the complete hydrological years "
        "Nov–Oct). Give long series in a file (`input_file`)."
    ),
)
_ANNUAL_DATES = replace(
    DATES,
    description_pl=(
        "Daty wartości dobowych w formacie ISO `RRRR-MM-DD`, ściśle rosnące, tyle samo "
        "co `values`; pomiń, gdy `values` to maksima roczne."
    ),
    description=(
        "Dates of daily values in ISO format `YYYY-MM-DD`, strictly increasing, as "
        "many as `values`; omit when `values` are annual maxima."
    ),
)
_ANNUAL_DATE_COLUMN = replace(
    DATE_COLUMN,
    description_pl=(
        "Nazwa kolumny z datami ISO w `input_file` (np. `date`); podaj dla szeregu "
        "dobowego, pomiń dla maksimów rocznych."
    ),
    description=(
        "Name of the column with ISO dates in `input_file` (e.g. `date`); give it for "
        "a daily series, omit it for annual maxima."
    ),
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="stats characteristic",
        operation_id="hydrolog_stats_characteristic",
        summary_pl=(
            "Oblicz wartości charakterystyczne I i II stopnia (WQ…NQ, WWQ…NNQ, WWW…NNW)"
        ),
        summary=(
            "Compute first- and second-degree characteristic values (WQ…NQ, WWQ…NNQ)"
        ),
        description_pl=(
            "Wg IMGW-PIB: minimum, średnia i maksimum każdego roku hydrologicznego "
            "(XI–X) i półrocza (I stopień) oraz w okresie ich największa, średnia, "
            "mediana i najmniejsza (II stopień: WWQ…NNQ, WWW…NNW). Z szeregu dobowego "
            "albo pliku półroczy IMGW-PIB; kwantyle wezbrań: `stats flood-frequency`."
        ),
        description=(
            "Per IMGW-PIB: the minimum, mean and maximum of each hydrological year "
            "(Nov–Oct) and half-year (first degree) and, over the period, their "
            "highest, mean, median and lowest (second degree: WWQ…NNQ, WWW…NNW). From "
            "a daily series or IMGW-PIB's half-year file; flood quantiles: `stats "
            "flood-frequency`."
        ),
        result_schema="hydrolog-stats-characteristic/1",
        cardinality="bounded",
        rules=(
            "Give a daily series with dates or `half_year_file`.",
            "The period is the whole record unless `first_year`/`last_year` are given.",
            "Read `notices` and `labels`; results are in the unit of the series.",
        ),
        rules_pl=(
            "Podaj szereg dobowy z datami albo `half_year_file`.",
            "Okres to całe wielolecie, chyba że podasz `first_year`/`last_year`.",
            "Czytaj `notices` i `labels`; wyniki są w jednostce szeregu.",
        ),
        errors=_STATION_ERRORS,
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
            {
                "wwx": 329.0,
                "swx": 260.25,
                "nnx": 45.0,
                "period_years": 4,
                "first_year": 2020,
                "last_year": 2023,
                "labels": {"wwx": "WWW", "snx": "SNW"},
                "incomplete_years": [2021, 2022],
                "years": [
                    {
                        "year": 2020,
                        "annual": {
                            "max": 329.0,
                            "max_date": "2020-06-24",
                            "days_with_data": 366,
                        },
                    }
                ],
            },
            {
                "source": "half_years",
                "wwx": 132.13,
                "swx": 84.924,
                "snx": 1.014,
                "nnx": 0.52,
                "period_years": 5,
                "years": [
                    {
                        "year": 2019,
                        "annual": {
                            "max": 72.18,
                            "max_date": "2019-05-22",
                            "mean": 5.51,
                        },
                    }
                ],
            },
        ),
        function="hydrolog.operations.stats_characteristic",
        options=(
            *DATED_OPTIONS,
            HALF_YEAR_FILE,
            Option(
                name="parameter",
                type="choice",
                description_pl=(
                    "Zmienna szeregu: nazywa wartości (`labels`) i wskazuje kolumny "
                    "`half_year_file`."
                ),
                description=(
                    "The variable of the series: it names the values (`labels`) and "
                    "picks the columns of `half_year_file`."
                ),
                choices=("Q", "H", "T"),
                meanings={
                    "Q": "Discharge (WQ…NQ, WWQ…NNQ).",
                    "H": "Stage (WW…NW, WWW…NNW).",
                    "T": "Water temperature (WT…NT, WWT…NNT).",
                },
                meanings_pl={
                    "Q": "Przepływ (WQ…NQ, WWQ…NNQ).",
                    "H": "Stan wody (WW…NW, WWW…NNW).",
                    "T": "Temperatura wody (WT…NT, WWT…NNT).",
                },
                default="Q",
            ),
            *PERIOD_OPTIONS,
            ATTRIBUTION,
        ),
        one_of=(*DATED_ONE_OF, ("half_year_file",)),
        examples=(
            {
                "input_file": _OBSERWATOR_EXPORT,
                "value_column": "Q",
                "date_column": "date",
                "parameter": "Q",
            },
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
            },
            {
                "input_file": _STATION_DAILY,
                "value_column": "H",
                "date_column": "date",
                "parameter": "H",
                "first_year": 2020,
                "last_year": 2023,
            },
            {"half_year_file": _STATION_HALF_YEARS, "parameter": "Q"},
        ),
    ),
    Command(
        name="stats threshold-events",
        operation_id="hydrolog_stats_threshold_events",
        summary_pl=(
            "Znajdź epizody i dni powyżej albo poniżej poziomu w szeregu dobowym"
        ),
        summary="Find the events and days above or below a level in a daily series",
        description_pl=(
            "Ciągi dni z wartością na poziomie `level` lub wyższą (albo niższą) z "
            "początkiem, końcem, czasem trwania i kulminacją oraz dni poza poziomem w "
            "każdym roku hydrologicznym (XI–X). Do stanów ostrzegawczych i "
            "charakterystycznych; niedobory ciągów niżówkowych: `stats "
            "low-flow-sequences`. Dzień "
            "bez danych kończy epizod, chyba że `max_gap_days` go łączy."
        ),
        description=(
            "Runs of days with a value at or above `level` (or below it) with start, "
            "end, duration and peak, and the days beyond the level in each "
            "hydrological year (Nov–Oct). Use for warning and characteristic levels; "
            "for low-flow deficits use `stats low-flow-sequences`. A day without a "
            "value ends an event unless `max_gap_days` bridges it."
        ),
        result_schema="hydrolog-stats-threshold-events/1",
        cardinality="bounded",
        rules=(
            "Give `level` in the unit of the series.",
            "`above` counts values >= level, `below` values < level.",
            "An event counts in the year in which it starts.",
        ),
        rules_pl=(
            "Podaj `level` w jednostce szeregu.",
            "`above` liczy wartości >= level, `below` wartości < level.",
            "Epizod liczy się w roku, w którym się zaczyna.",
        ),
        errors=_STATION_ERRORS,
        example_results=(
            {
                "level": 180.0,
                "direction": "above",
                "days_beyond": 24,
                "n_events": 8,
                "max_duration_days": 6,
                "events": [
                    {
                        "start_date": "2019-03-14",
                        "end_date": "2019-03-15",
                        "peak": 192.0,
                    }
                ],
                "years": [{"year": 2019, "days_beyond": 5, "n_events": 2}],
            },
            {
                "direction": "below",
                "first_year": 2021,
                "last_year": 2022,
                "days_beyond": 59,
                "n_events": 24,
                "max_duration_days": 15,
            },
        ),
        function="hydrolog.operations.stats_threshold_events",
        options=(
            *DATED_OPTIONS,
            Option(
                name="level",
                type="number",
                description_pl="Poziom w jednostce szeregu (np. stan [cm], Q [m³/s]).",
                description="The level, in the unit of the series (H [cm], Q [m³/s]).",
                required=True,
            ),
            Option(
                name="direction",
                type="choice",
                description_pl="Dni na poziomie lub powyżej albo poniżej poziomu.",
                description="Days at or above the level, or below it.",
                choices=("above", "below"),
                meanings={
                    "above": "A day with a value >= level is beyond it.",
                    "below": "A day with a value < level is beyond it.",
                },
                meanings_pl={
                    "above": "Dzień z wartością >= level jest poza poziomem.",
                    "below": "Dzień z wartością < level jest poza poziomem.",
                },
                default="above",
            ),
            Option(
                name="min_duration_days",
                type="integer",
                description_pl="Najkrótszy raportowany epizod w dobach, co najmniej 1.",
                description="Shortest event reported, in days, at least 1.",
                default=1,
                minimum=1,
                unit="d",
            ),
            Option(
                name="max_gap_days",
                type="integer",
                description_pl=(
                    "Epizody rozdzielone mniejszą liczbą dób (bez danych albo nie poza "
                    "poziomem) łączą się w jeden; 0 nie łączy."
                ),
                description=(
                    "Events parted by fewer days (without a value or not beyond the "
                    "level) merge into one; 0 merges none."
                ),
                default=0,
                minimum=0,
                unit="d",
            ),
            *PERIOD_OPTIONS,
            ATTRIBUTION,
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _STATION_DAILY,
                "value_column": "H",
                "date_column": "date",
                "level": 180,
            },
            {
                "input_file": _STATION_DAILY,
                "value_column": "T",
                "date_column": "date",
                "level": 1.0,
                "direction": "below",
                "first_year": 2021,
                "last_year": 2022,
            },
        ),
    ),
    Command(
        name="stats duration-curve",
        operation_id="hydrolog_stats_duration_curve",
        summary_pl=(
            "Oblicz krzywą czasu trwania szeregu dobowego z liczebnościami klas i "
            "klasą modalną"
        ),
        summary=(
            "Compute the duration curve of a daily series with class counts and the "
            "modal class"
        ),
        description_pl=(
            "Wartość osiągana lub przekraczana przez p % dni (pozycje Weibulla "
            "m/(n+1)) w okresie albo jednym miesiącu oraz dni każdej klasy (o równej "
            "szerokości albo logarytmicznej) z sumami „z wyższymi” i „z niższymi” i "
            "podziałem na miesiące hydrologiczne. Do krzywych czasu trwania H i Q; "
            "strefy Rybczyńskiego: `hydrometrics water-level-zones`."
        ),
        description=(
            "The value equalled or exceeded on p % of the days (Weibull positions "
            "m/(n+1)) over the period or one month, and the days of each class (equal "
            "width or logarithmic) with the cumulative days including higher and "
            "lower, split by hydrological month. Use for H and Q duration curves; for "
            "Rybczyński zones use `hydrometrics water-level-zones`."
        ),
        result_schema="hydrolog-stats-duration-curve/1",
        cardinality="bounded",
        rules=(
            "Use `class_width` 10 (cm) for H and `class_method` log for Q.",
            "`percents` are exceedance percentages; classes run from the highest.",
        ),
        rules_pl=(
            "Użyj `class_width` 10 (cm) dla H i `class_method` log dla Q.",
            "`percents` to procenty przekroczenia; klasy idą od najwyższej.",
        ),
        errors=_STATION_ERRORS,
        example_results=(
            {
                "n_values": 1811,
                "median": 75.0,
                "percents": [1.0, 5.0, 10.0],
                "values": [189.88, 115.4, 90.0],
                "modal_class": {"lower": 80.0, "upper": 90.0, "days": 529},
                "classes": [
                    {
                        "lower": 320.0,
                        "upper": 330.0,
                        "days": 1,
                        "days_with_higher": 1,
                        "days_with_lower": 1811,
                    }
                ],
            },
            {
                "month": 9,
                "n_values": 150,
                "class_method": "log",
                "values": [1.335, 0.61, 0.58],
                "modal_class": {"lower": 0.54, "days": 60},
            },
        ),
        function="hydrolog.operations.stats_duration_curve",
        options=(
            *DATED_OPTIONS,
            *PERIOD_OPTIONS,
            Option(
                name="month",
                type="integer",
                description_pl=(
                    "Tylko dni tego miesiąca kalendarzowego (1–12, 11 = listopad); "
                    "domyślnie wszystkie dni."
                ),
                description=(
                    "Only the days of this calendar month (1–12, 11 = November); by "
                    "default every day."
                ),
                minimum=1,
                maximum=12,
            ),
            Option(
                name="percents",
                type="number_list",
                description_pl=(
                    "Procenty przekroczenia tabeli, każdy z przedziału (0, 100); "
                    "domyślnie 1, 5, 10, 30, 50, 70, 90, 95, 99."
                ),
                description=(
                    "Exceedance percentages of the table, each in (0, 100); default "
                    "1, 5, 10, 30, 50, 70, 90, 95, 99."
                ),
                default=(1.0, 5.0, 10.0, 30.0, 50.0, 70.0, 90.0, 95.0, 99.0),
                exclusive_minimum=0,
                maximum=100,
            ),
            Option(
                name="class_method",
                type="choice",
                description_pl="Sposób podziału wartości na klasy.",
                description="How the values are divided into classes.",
                choices=("width", "log"),
                meanings={
                    "width": "Classes of `class_width` from a multiple of it.",
                    "log": "`class_count` logarithmic classes (for discharge).",
                },
                meanings_pl={
                    "width": "Klasy o szerokości `class_width` od jej wielokrotności.",
                    "log": "`class_count` klas logarytmicznych (dla przepływów).",
                },
                default="width",
            ),
            Option(
                name="class_width",
                type="number",
                description_pl=(
                    "Szerokość klasy w jednostce szeregu (np. 10 cm), dodatnia."
                ),
                description="Width of a class, in the unit of the series (10 cm).",
                default=10.0,
                exclusive_minimum=0,
            ),
            Option(
                name="class_count",
                type="integer",
                description_pl=(
                    "Liczba klas logarytmicznych między najmniejszą dodatnią a "
                    "największą wartością, co najmniej 2."
                ),
                description=(
                    "Number of logarithmic classes between the smallest positive and "
                    "the largest value, at least 2."
                ),
                default=40,
                minimum=2,
            ),
            ATTRIBUTION,
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _STATION_DAILY,
                "value_column": "H",
                "date_column": "date",
                "class_width": 10,
            },
            {
                "input_file": _STATION_DAILY,
                "value_column": "Q",
                "date_column": "date",
                "month": 9,
                "percents": [50, 70, 90],
                "class_method": "log",
                "class_count": 20,
            },
        ),
    ),
    Command(
        name="stats runoff-volume",
        operation_id="hydrolog_stats_runoff_volume",
        summary_pl=(
            "Oblicz roczne i miesięczne objętości odpływu oraz krzywą sumową roku"
        ),
        summary=(
            "Compute annual and monthly runoff volumes and the cumulative volume of a "
            "year"
        ),
        description_pl=(
            "Objętość V = ΣQ·86 400 s [m³] każdego roku hydrologicznego (XI–X) i jego "
            "miesięcy, ich średnie z pełnych lat i miesięcy okresu oraz objętość "
            "narastająca jednego roku obok średniej. Wymaga dobowych przepływów w m³/s "
            "z datami; dzień bez danych nic nie dodaje i czyni rok niepełnym."
        ),
        description=(
            "Volumes V = ΣQ·86,400 s [m³] of each hydrological year (Nov–Oct) and its "
            "months, their means over the complete years and months of the period, and "
            "the cumulative volume of one year beside the mean one. Needs daily "
            "discharge in m³/s with dates; a day without a value adds nothing and "
            "makes its year incomplete."
        ),
        result_schema="hydrolog-stats-runoff-volume/1",
        cardinality="bounded",
        rules=(
            "Give daily discharge in m³/s with dates.",
            "Means use complete years and months only; volumes are in m³.",
        ),
        rules_pl=(
            "Podaj dobowe przepływy w m³/s z datami.",
            "Średnie liczą tylko pełne lata i miesiące; objętości są w m³.",
        ),
        errors=_STATION_ERRORS,
        example_results=(
            {
                "n_complete_years": 3,
                "mean_annual_volume_m3": 181315872.0,
                "cumulative_year": 2022,
                "years": [
                    {
                        "year": 2019,
                        "volume_m3": 173741760.0,
                        "complete": True,
                        "months": [{"month": 11, "volume_m3": 5818176.0}],
                    }
                ],
            },
        ),
        function="hydrolog.operations.stats_runoff_volume",
        options=(
            *DATED_OPTIONS,
            *PERIOD_OPTIONS,
            Option(
                name="cumulative_year",
                type="integer",
                description_pl=(
                    "Rok hydrologiczny krzywej sumowej; domyślnie ostatni pełny rok "
                    "okresu."
                ),
                description=(
                    "Hydrological year of the cumulative volume; by default the last "
                    "complete year of the period."
                ),
                minimum=1,
            ),
            ATTRIBUTION,
        ),
        one_of=DATED_ONE_OF,
        examples=(
            {
                "input_file": _STATION_DAILY,
                "value_column": "Q",
                "date_column": "date",
                "cumulative_year": 2022,
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
        options=(*DATED_OPTIONS, ATTRIBUTION),
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
            ATTRIBUTION,
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
            "maksimów rocznych (domyślnie L-momenty; największa wiarygodność, "
            "momenty, najmniejsze kwadraty albo wszystkie metody naraz) i podaje "
            "kwantyle z miarami zgodności (KS, A², AIC). Do przepływów miarodajnych; "
            "niżówki: `stats low-flow`."
        ),
        description=(
            "Fits log-normal, GEV, Pearson III and Weibull distributions to annual "
            "maxima (L-moments by default; maximum likelihood, moments, least squares "
            "or all at once) and gives quantiles with goodness-of-fit (KS, A², AIC). "
            "Use for design discharges; for low flows use `stats low-flow`."
        ),
        result_schema="hydrolog-stats-flood-frequency/1",
        cardinality="bounded",
        rules=(
            (
                "Pass annual maxima without dates, a daily series with dates or "
                "`half_year_file`."
            ),
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
            (
                "Podaj maksima roczne bez dat, szereg dobowy z datami albo "
                "`half_year_file`."
            ),
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
            {"n_years": 35, "best_distribution": "log_normal", "source": "values"},
            {
                "n_years": 3,
                "annual_maxima": [21.12, 13.99, 24.93],
                "hydrological_years": [2022, 2023, 2024],
                "best_distribution": "gev",
                "source": "daily",
            },
            {
                "n_years": 5,
                "annual_maxima": [72.18, 132.13, 102.57, 41.19, 76.55],
                "hydrological_years": [2019, 2020, 2021, 2022, 2023],
                "incomplete_years": [],
                "source": "half_years",
            },
        ),
        function="hydrolog.operations.stats_flood_frequency",
        options=(
            _ANNUAL_VALUES,
            _ANNUAL_DATES,
            INPUT_FILE,
            VALUE_COLUMN,
            _ANNUAL_DATE_COLUMN,
            HALF_YEAR_FILE,
            _HALF_YEAR_PARAMETER,
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
            Option(
                name="fit_method",
                type="choice",
                description_pl="Metoda estymacji parametrów rozkładów.",
                description="Method that estimates the distribution parameters.",
                choices=("mle", "moments", "l_moments", "least_squares", "all"),
                meanings={
                    "mle": "Maximum likelihood.",
                    "moments": "Method of moments: mean, variance, skewness.",
                    "l_moments": "Method of L-moments (Hosking and Wallis 1997).",
                    "least_squares": "Least squares of quantiles at plotting points.",
                    "all": "Each distribution by each method, sorted by AIC.",
                },
                meanings_pl={
                    "mle": "Największa wiarygodność.",
                    "moments": "Metoda momentów: średnia, wariancja, skośność.",
                    "l_moments": "Metoda L-momentów (Hosking i Wallis 1997).",
                    "least_squares": "Najmniejsze kwadraty kwantyli w pozycjach "
                    "empirycznych.",
                    "all": "Każdy rozkład każdą metodą, posortowane wg AIC.",
                },
                default="l_moments",
            ),
            _RETURN_PERIODS,
            *PERIOD_OPTIONS,
            ATTRIBUTION,
        ),
        one_of=_ANNUAL_ONE_OF,
        typical_ranges=(RangeCheck("flood_frequency", "years", result="n_years"),),
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
            {"half_year_file": _STATION_HALF_YEARS, "return_periods": [10, 100]},
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
            "zdarzenia suszy: `stats low-flow-sequences`. Wymaga dat albo "
            "`half_year_file`."
        ),
        description=(
            "Fits the Fisher–Tippett (GEV for minima) distribution to annual minima"
            " and gives low-flow quantiles (flow reached or undercut once in T "
            "years). Use for low-flow frequency; for floods use `stats "
            "flood-frequency`, for drought events `stats low-flow-sequences`. Needs"
            " dates or `half_year_file`."
        ),
        result_schema="hydrolog-stats-low-flow/1",
        cardinality="bounded",
        rules=(
            (
                "Give a daily series with dates or `half_year_file`; years with a "
                "missing day are skipped."
            ),
            (
                "Check `notices` for `incomplete_years` and samples shorter than 10 "
                "years."
            ),
            "At least 3 complete hydrological years are required.",
        ),
        rules_pl=(
            (
                "Podaj szereg dobowy z datami albo `half_year_file`; lata z "
                "brakującym dniem są pomijane."
            ),
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
                "source": "daily",
            },
            {
                "n_years": 5,
                "hydrological_years": [2019, 2020, 2021, 2022, 2023],
                "annual_minima": [0.54, 1.54, 1.48, 0.52, 0.99],
                "source": "half_years",
            },
        ),
        function="hydrolog.operations.stats_low_flow",
        options=(
            *DATED_OPTIONS,
            HALF_YEAR_FILE,
            _HALF_YEAR_PARAMETER,
            _RETURN_PERIODS,
            *PERIOD_OPTIONS,
            ATTRIBUTION,
        ),
        one_of=(*DATED_ONE_OF, ("half_year_file",)),
        examples=(
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
                "return_periods": [2, 10, 50],
            },
            {"half_year_file": _STATION_HALF_YEARS, "return_periods": [2, 10]},
        ),
    ),
    Command(
        name="stats low-flow-sequences",
        operation_id="hydrolog_stats_low_flow_sequences",
        summary_pl=("Wykryj ciągi niżówkowe (susze) poniżej progu"),
        summary=("Detect low-flow (drought) sequences below a threshold"),
        description_pl=(
            "Metoda poziomu progowego: ciągi dób poniżej progu (podanego, SNQ okresu "
            "albo przepływu przekraczanego przez p % dni), łączone przez krótkie "
            "przerwy, z datami, czasem trwania, minimum, średnią, niedoborem i "
            "podsumowaniem lat hydrologicznych. Luki w danych są dozwolone. Częstość "
            "minimów rocznych: `stats low-flow`."
        ),
        description=(
            "Threshold level method: runs of days below the threshold (given, SNQ of "
            "the period, or the flow exceeded on p % of days), merged across short "
            "gaps, with dates, duration, minimum, mean, deficit and a summary per "
            "hydrological year. Gaps in the record are allowed. For annual minima "
            "frequency use `stats low-flow`."
        ),
        result_schema="hydrolog-stats-low-flow-sequences/1",
        cardinality="bounded",
        rules=(
            "Give `threshold` (unit of the series) or another `threshold_method`.",
            "Deficit is in series unit × day; `deficit_volume_m3` for Q in m³/s.",
            "A sequence counts in the year in which it starts.",
        ),
        rules_pl=(
            "Podaj `threshold` (w jednostce szeregu) albo inną `threshold_method`.",
            "Niedobór jest w jednostce szeregu × doba; `deficit_volume_m3` dla Q.",
            "Ciąg liczy się w roku, w którym się zaczyna.",
        ),
        errors=_STATION_ERRORS,
        example_results=(
            {
                "threshold": 2.2,
                "n_days": 1096,
                "n_events": 7,
                "total_deficit": 23.78,
                "max_duration_days": 48,
            },
            {
                "threshold_method": "mean_annual_minimum",
                "threshold": 1.014,
                "n_events": 2,
                "total_deficit": 42.75,
                "total_deficit_volume_m3": 3693600.0,
                "max_duration_days": 67,
                "n_missing_days": 15,
                "sequences": [
                    {
                        "start_date": "2019-08-20",
                        "end_date": "2019-10-13",
                        "duration_days": 55,
                        "deficit_volume_m3": 1613952.0,
                    }
                ],
            },
        ),
        function="hydrolog.operations.stats_low_flow_sequences",
        options=(
            *DATED_OPTIONS,
            Option(
                name="threshold",
                type="number",
                description_pl=(
                    "Próg niżówkowy w jednostce szeregu (np. m³/s), dodatni; dni z "
                    "wartością poniżej progu tworzą niżówkę. Tylko z "
                    "`threshold_method` value."
                ),
                description=(
                    "Low-flow threshold in the unit of the series (e.g. m³/s), "
                    "positive; days with a value below it make up a low-flow event. "
                    "Only with `threshold_method` value."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="threshold_method",
                type="choice",
                description_pl="Skąd pochodzi próg.",
                description="Where the threshold comes from.",
                choices=("value", "mean_annual_minimum", "exceedance"),
                meanings={
                    "value": "The given `threshold`.",
                    "mean_annual_minimum": "SNQ (SNW): mean of the annual minima.",
                    "exceedance": "The flow exceeded on `exceedance_percent` % of "
                    "days.",
                },
                meanings_pl={
                    "value": "Podany `threshold`.",
                    "mean_annual_minimum": "SNQ (SNW): średnia z minimów rocznych.",
                    "exceedance": "Przepływ przekraczany przez `exceedance_percent` % "
                    "dni.",
                },
                default="value",
            ),
            Option(
                name="exceedance_percent",
                type="number",
                description_pl=(
                    "Procent dni przekroczenia dla `exceedance`, z przedziału "
                    "(0, 100): 70 daje Q70, 90 daje Q90."
                ),
                description=(
                    "Exceedance percentage of `exceedance`, in (0, 100): 70 gives Q70, "
                    "90 gives Q90."
                ),
                default=70.0,
                exclusive_minimum=0,
                maximum=100,
            ),
            Option(
                name="parameter",
                type="choice",
                description_pl="Zmienna szeregu.",
                description="The variable of the series.",
                choices=("Q", "H"),
                meanings={
                    "Q": "Discharge in m³/s: the deficits are also volumes in m³.",
                    "H": "Stage: low-stage periods, without volumes.",
                },
                meanings_pl={
                    "Q": "Przepływ w m³/s: niedobory także jako objętości w m³.",
                    "H": "Stan wody: okresy niskich stanów, bez objętości.",
                },
                default="Q",
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
                    "Przerwy krótsze niż ta liczba dób (bez danych albo powyżej progu) "
                    "między dwoma ciągami poniżej progu łączą je w jeden ciąg; 0 "
                    "wyłącza łączenie."
                ),
                description=(
                    "Gaps shorter than this number of days (without a value or above "
                    "the threshold) between two runs below the threshold merge them "
                    "into one sequence; 0 disables merging."
                ),
                default=4,
                minimum=0,
                unit="d",
            ),
            *PERIOD_OPTIONS,
            ATTRIBUTION,
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
            {
                "input_file": _STATION_DAILY,
                "value_column": "Q",
                "date_column": "date",
                "threshold_method": "mean_annual_minimum",
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
            ATTRIBUTION,
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
    Command(
        name="stats homogeneity",
        operation_id="hydrolog_stats_homogeneity",
        summary_pl=(
            "Zbadaj jednorodność maksimów rocznych testami Manna-Whitneya, "
            "Kołmogorowa-Smirnowa i Pettitta"
        ),
        summary=(
            "Test annual maxima for homogeneity (Mann-Whitney U, Kolmogorov-Smirnov, "
            "Pettitt)"
        ),
        description_pl=(
            "Porównuje maksima roczne sprzed i od roku `split_year` (domyślnie połowy "
            "ciągu) dwustronnymi testami Manna-Whitneya U i Kołmogorowa-Smirnowa dla "
            "dwóch prób; test Pettitta wskazuje najbardziej prawdopodobny punkt "
            "zmiany. Do sprawdzenia ciągu przed `stats flood-frequency`. Lata z "
            "brakami dni są pomijane."
        ),
        description=(
            "Compares the annual maxima before and after `split_year` (default: the "
            "halves) by the two-sided Mann-Whitney U and two-sample "
            "Kolmogorov-Smirnov tests; Pettitt's test finds the most probable change "
            "point. Use before `stats flood-frequency`."
        ),
        result_schema="hydrolog-stats-homogeneity/1",
        rules=(
            (
                "Pass annual maxima (`years`/`year_column` for `split_year`), a daily "
                "series with dates or `half_year_file`."
            ),
            (
                "A test rejects homogeneity when `homogeneous` is false (`p_value` "
                "below `alpha`)."
            ),
            (
                "`split_year` and Pettitt's `change_point_year` are the first year of "
                "the second part."
            ),
        ),
        rules_pl=(
            (
                "Podaj maksima roczne (z `years` albo `year_column`, by użyć "
                "`split_year`), szereg dobowy z datami albo `half_year_file`."
            ),
            (
                "Test odrzuca jednorodność, gdy `homogeneous` jest fałszem (`p_value` "
                "mniejsze niż `alpha`)."
            ),
            (
                "`split_year` i `change_point_year` testu Pettitta to pierwszy rok "
                "drugiej części."
            ),
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
                "n_years": 35,
                "split_index": 11,
                "split_year": 2000,
                "mann_whitney": {"statistic": 124.0, "homogeneous": True},
                "pettitt": {"change_point_year": 2020, "homogeneous": True},
                "source": "values",
            },
            {"n_years": 3, "split_index": 1, "split_year": 2023, "source": "daily"},
            {
                "n_years": 10,
                "split_index": 5,
                "split_year": None,
                "mann_whitney": {"statistic": 0.0, "homogeneous": False},
                "kolmogorov_smirnov": {"statistic": 1.0, "homogeneous": False},
                "pettitt": {"change_point_index": 5, "homogeneous": True},
            },
            {
                "n_years": 5,
                "split_year": 2021,
                "source": "half_years",
                "hydrological_years": [2019, 2020, 2021, 2022, 2023],
            },
        ),
        function="hydrolog.operations.stats_homogeneity",
        options=(
            _ANNUAL_VALUES,
            _ANNUAL_DATES,
            Option(
                name="years",
                type="number_list",
                description_pl=(
                    "Lata maksimów rocznych z `values`: liczby całkowite, ściśle "
                    "rosnące (mogą mieć luki), tyle samo co `values`; potrzebne do "
                    "`split_year`. Nie z `dates`."
                ),
                description=(
                    "Years of the annual maxima in `values`: whole numbers, strictly "
                    "increasing (gaps allowed), as many as `values`; needed for "
                    "`split_year`. Not with `dates`."
                ),
            ),
            replace(
                INPUT_FILE,
                description_pl=(
                    "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON z "
                    "szeregiem. Kolumny wskazują `value_column` oraz `date_column` "
                    "albo `year_column`."
                ),
                description=(
                    "CSV file (comma or semicolon, header row) or JSON file with the "
                    "series. The columns are named by `value_column` and "
                    "`date_column` or `year_column`."
                ),
            ),
            VALUE_COLUMN,
            _ANNUAL_DATE_COLUMN,
            Option(
                name="year_column",
                type="string",
                description_pl=(
                    "Nazwa kolumny z latami maksimów rocznych w `input_file` (np. "
                    "`year`); potrzebna do `split_year`. Nie z `date_column`."
                ),
                description=(
                    "Name of the column with the years of the annual maxima in "
                    "`input_file` (e.g. `year`); needed for `split_year`. Not with "
                    "`date_column`."
                ),
            ),
            HALF_YEAR_FILE,
            _HALF_YEAR_PARAMETER,
            Option(
                name="split_year",
                type="integer",
                description_pl=(
                    "Pierwszy rok drugiej części: maksima wcześniejszych lat tworzą "
                    "pierwszą część. Wymaga lat (`years`, `year_column` albo dat); "
                    "domyślnie pierwszą część tworzy pierwsza połowa wartości (n // 2)."
                ),
                description=(
                    "First year of the second part: the annual maxima of earlier years "
                    "form the first part. Needs years (`years`, `year_column` or "
                    "dates); by default the first half of the values (n // 2) is the "
                    "first part."
                ),
            ),
            Option(
                name="alpha",
                type="number",
                description_pl=(
                    "Poziom istotności testów z przedziału otwartego (0, 1), np. 0,05."
                ),
                description=(
                    "Significance level of the tests, in the open interval (0, 1), "
                    "e.g. 0.05."
                ),
                default=0.05,
                exclusive_minimum=0,
                maximum=1,
            ),
            *PERIOD_OPTIONS,
            ATTRIBUTION,
        ),
        one_of=_ANNUAL_ONE_OF,
        examples=(
            {
                "input_file": _ANNUAL_MAXIMA,
                "value_column": "Qmax",
                "year_column": "year",
                "split_year": 2000,
            },
            {
                "input_file": _DAILY_FLOWS,
                "value_column": "Q",
                "date_column": "date",
            },
            {
                "values": [52.0, 48.0, 55.0, 50.0, 47.0, 81.0, 86.0, 79.0, 90.0, 84.0],
            },
            {"half_year_file": _STATION_HALF_YEARS, "parameter": "H"},
        ),
    ),
)
