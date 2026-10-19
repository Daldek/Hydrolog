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
    description=(
        "Okresy powtarzalności T [lata], każdy większy od 1; domyślnie 2, 5, 10, 20, "
        "50, 100, 500, 1000."
    ),
    description_en=(
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
        operation_id="stats_characteristic",
        summary=(
            "Wartości charakterystyczne II stopnia (WWQ…NNQ) z szeregu dobowego, rok "
            "hydrologiczny XI–X."
        ),
        summary_en=(
            "Second-degree characteristic values (WWQ…NNQ) of a daily series, "
            "hydrological year Nov–Oct."
        ),
        description=(
            "Charakterystyki II stopnia wg metodyki IMGW-PIB z szeregu dobowego "
            "przepływów Q albo stanów H. Szereg jest dzielony na lata hydrologiczne "
            "(1 listopada – 31 października; rok nosi numer roku kalendarzowego, w "
            "którym się kończy), dla każdego roku liczone są maksimum, średnia i "
            "minimum, a z każdego z tych trzech szeregów rocznych wyznaczane są "
            "wartość największa (W), średnia (S), mediana (Z) i najmniejsza (N). "
            "Wynik: `wwx`, `swx`, `zwx`, `nwx` (z maksimów rocznych, czyli WWQ, SWQ, "
            "ZWQ, NWQ), `wsx`…`nsx` (ze średnich rocznych), `wnx`…`nnx` (z minimów "
            "rocznych), `period_years` (liczba lat hydrologicznych w szeregu, także "
            "niepełnych) i `parameter`; jednostką wyniku jest jednostka szeregu. "
            "Szereg wymaga dat; braki danych (NaN) są pomijane i zgłaszane w "
            "`notices`."
        ),
        description_en=(
            "Second-degree characteristic values following the IMGW-PIB methodology, "
            "from a daily discharge (Q) or stage (H) series. The series is split into "
            "hydrological years (1 November – 31 October; a year is named after the "
            "calendar year in which it ends); for each year the maximum, mean and "
            "minimum are taken, and from each of these three annual series the "
            "highest (W), mean (S), median (Z) and lowest (N) value. Result: `wwx`, "
            "`swx`, `zwx`, `nwx` (of the annual maxima: WWQ, SWQ, ZWQ, NWQ), "
            "`wsx`…`nsx` (of the annual means), `wnx`…`nnx` (of the annual minima), "
            "`period_years` (number of hydrological years in the series, partial "
            "years included) and `parameter`; the unit of the result is the unit of "
            "the series. The series needs dates; missing values (NaN) are skipped and "
            "reported in `notices`."
        ),
        function="hydrolog.operations:stats_characteristic",
        options=(
            *DATED_OPTIONS,
            Option(
                name="parameter",
                type="choice",
                description=(
                    "Etykieta szeregu: `Q` (przepływ, wartości WWQ…NNQ) albo `H` (stan "
                    "wody, WWH…NNH); nie wpływa na obliczenia, tylko na opis wyniku."
                ),
                description_en=(
                    "Series label: `Q` (discharge, values WWQ…NNQ) or `H` (stage, "
                    "WWH…NNH); it does not affect the computation, only the label of "
                    "the result."
                ),
                choices=("Q", "H"),
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
        operation_id="stats_daily",
        summary=(
            "Statystyki dobowe z wielolecia: maksimum, średnia, mediana i minimum dla "
            "każdej doby roku hydrologicznego."
        ),
        summary_en=(
            "Day-of-year statistics over all years: maximum, mean, median and minimum "
            "for each day of the hydrological year."
        ),
        description=(
            "Dla każdej doby roku hydrologicznego (1 = 1 listopada, do 366) liczy ze "
            "wszystkich lat szeregu maksimum, średnią, medianę, minimum i liczbę "
            "obserwacji. Wynik to tablice o jednakowej długości: `day_of_year`, "
            "`max_values`, `mean_values`, `median_values`, `min_values`, `count`; doby "
            "bez żadnej obserwacji nie występują. Szereg wymaga dat; braki danych "
            "(NaN) są pomijane i zgłaszane w `notices`."
        ),
        description_en=(
            "For each day of the hydrological year (1 = 1 November, up to 366) "
            "computes the maximum, mean, median, minimum and number of observations "
            "over all years of the series. The result is a set of arrays of equal "
            "length: `day_of_year`, `max_values`, `mean_values`, `median_values`, "
            "`min_values`, `count`; days without any observation are absent. The "
            "series needs dates; missing values (NaN) are skipped and reported in "
            "`notices`."
        ),
        function="hydrolog.operations:stats_daily",
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
        operation_id="stats_monthly",
        summary=(
            "Statystyki miesięczne z przedziałem ufności średniej (t-Studenta) dla "
            "miesięcy 1–12."
        ),
        summary_en=(
            "Monthly statistics with a t-Student confidence interval of the mean for "
            "months 1–12."
        ),
        description=(
            "Dla każdego miesiąca kalendarzowego (1–12) liczy ze wszystkich wartości "
            "szeregu maksimum, średnią, medianę, minimum, odchylenie standardowe "
            "(n − 1), współczynnik zmienności (odchylenie / średnia), skośność "
            "(współczynnik Fishera–Pearsona) oraz dwustronny przedział ufności "
            "średniej z rozkładu t-Studenta (dolna granica nie jest mniejsza od 0). "
            "Miesiąc z jedną wartością nie ma odchylenia standardowego, współczynnika "
            "zmienności, skośności ani przedziału ufności (w JSON `null`, ostrzeżenie "
            "`single_value_month` w `notices`). Szereg musi mieć wartości we "
            "wszystkich 12 miesiącach, inaczej `calculation_error`. Wynik: tablice "
            "`months`, `max_values`, `mean_values`, `median_values`, `min_values`, "
            "`std_values`, "
            "`cv_values`, `skewness_values`, `ci_lower`, `ci_upper` i "
            "`confidence_level`. Szereg wymaga dat; braki danych (NaN) są pomijane i "
            "zgłaszane w `notices`."
        ),
        description_en=(
            "For each calendar month (1–12) computes over all values of the series "
            "the maximum, mean, median, minimum, standard deviation (n − 1), "
            "coefficient of variation (deviation / mean), skewness (Fisher–Pearson "
            "coefficient) and the two-sided t-Student confidence interval of the "
            "mean (the lower limit is not below 0). A month with a single value has "
            "no standard deviation, coefficient of variation, skewness or confidence "
            "interval (`null` in JSON, warning `single_value_month` in `notices`). "
            "The series must hold values in all 12 months, otherwise "
            "`calculation_error`. Result: arrays `months`, `max_values`, "
            "`mean_values`, `median_values`, "
            "`min_values`, `std_values`, `cv_values`, `skewness_values`, `ci_lower`, "
            "`ci_upper` and `confidence_level`. The series needs dates; missing "
            "values (NaN) are skipped and reported in `notices`."
        ),
        function="hydrolog.operations:stats_monthly",
        options=(
            *DATED_OPTIONS,
            Option(
                name="confidence_level",
                type="number",
                description=(
                    "Poziom ufności przedziału średniej, z przedziału otwartego "
                    "(0, 1), np. 0,95."
                ),
                description_en=(
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
        operation_id="stats_flood_frequency",
        summary=(
            "Analiza częstości wezbrań: rozkłady log-normalny, GEV, Pearsona III, "
            "Weibulla; kwantyle dla okresów powtarzalności."
        ),
        summary_en=(
            "Flood frequency analysis: log-normal, GEV, Pearson III and Weibull "
            "distributions; quantiles for return periods."
        ),
        description=(
            "Dopasowuje do maksimów rocznych rozkłady: log-normalny (2 parametry, "
            "położenie = 0), GEV, Pearsona typu III i Weibulla (estymacja największej "
            "wiarygodności, `scipy.stats`) i podaje kwantyle x_T = F⁻¹(1 − 1/T) dla "
            "zadanych okresów powtarzalności T [lata] oraz miary zgodności: test "
            "Kołmogorowa–Smirnowa (statystyka i p-value; nieważny dla parametrów "
            "oszacowanych z tej samej próby, `ks_valid=false`), statystykę "
            "Andersona–Darlinga (A², przybliżone wartości krytyczne) i kryterium AIC. "
            "Szereg wejściowy to albo same maksima roczne (bez dat), albo szereg "
            "dobowy z datami — wtedy maksima są wybierane dla kompletnych lat "
            "hydrologicznych (1 XI – 31 X): rok jest kompletny, gdy ma wartość dla "
            "każdego dnia (365 albo 366 dni), a rok z brakującym dniem (nieobecna "
            "data albo NaN) jest pomijany, bo jego maksimum mogło nie zostać "
            "zarejestrowane (KZGW 2017 i WMO nr 1029, 2009 biorą do analizy pełne "
            "lata obserwacji); pominięte lata wymienia `incomplete_years` w wyniku "
            "i w `notices` (kod `incomplete_years`), więc eksport z lat "
            "kalendarzowych traci pierwszy i ostatni rok hydrologiczny. Metodyka "
            "KZGW (2017) zaleca co najmniej 30 lat danych (Coles 2001: podstawy "
            "teorii wartości ekstremalnych); dla próby krótszej niż 30 lat (a "
            "zwłaszcza niż 10) w `notices` pojawia się ostrzeżenie, a minimum "
            "obliczeniowe to 3 maksima (3 kompletne lata). Przy `distribution=all` "
            "rozkłady są posortowane wg AIC (najlepszy pierwszy). Wynik: `n_years`, "
            "`annual_maxima`, `hydrological_years`, `incomplete_years`, "
            "`best_distribution`, `distributions` (parametry, `quantiles`, "
            "`exceedance_probabilities`, miary zgodności) i `empirical` (częstość "
            "empiryczna, pozycje plotowania Weibulla: wartości malejąco z "
            "prawdopodobieństwem przewyższenia)."
        ),
        description_en=(
            "Fits the log-normal (2 parameters, location = 0), GEV, Pearson type III "
            "and Weibull distributions to annual maxima (maximum likelihood, "
            "`scipy.stats`) and gives the quantiles x_T = F⁻¹(1 − 1/T) for the "
            "requested return periods T [years] together with goodness-of-fit "
            "measures: the Kolmogorov–Smirnov test (statistic and p-value; not valid "
            "for parameters estimated from the same sample, `ks_valid=false`), the "
            "Anderson–Darling statistic (A², approximate critical values) and AIC. "
            "The input series is either the annual maxima themselves (no dates) or a "
            "daily series with dates, from which the maxima of the complete "
            "hydrological years (1 Nov – 31 Oct) are taken: a year is complete when "
            "it has a value for every day (365 or 366 days), and a year with a "
            "missing day (an absent date or a NaN) is skipped because its maximum "
            "may have gone unrecorded (KZGW 2017 and WMO No. 1029, 2009 analyse "
            "whole years of observations); the skipped years are listed in "
            "`incomplete_years` of the result and in `notices` (code "
            "`incomplete_years`), so a calendar-year export loses its first and last "
            "hydrological year. The KZGW (2017) methodology recommends at least 30 "
            "years of data (Coles 2001: foundations of extreme value theory); a "
            "sample shorter than 30 years (especially than 10) raises a warning in "
            "`notices`, and the computational minimum is 3 maxima (3 complete "
            "years). With `distribution=all` the distributions are sorted by AIC "
            "(best first). Result: `n_years`, `annual_maxima`, `hydrological_years`, "
            "`incomplete_years`, `best_distribution`, `distributions` (parameters, "
            "`quantiles`, `exceedance_probabilities`, goodness of fit) and "
            "`empirical` (empirical frequency, Weibull plotting positions: values "
            "descending with exceedance probabilities)."
        ),
        function="hydrolog.operations:stats_flood_frequency",
        options=(
            replace(
                VALUES,
                description=(
                    "Szereg w kolejności czasowej: maksima roczne (bez `dates`) albo "
                    "wartości dobowe (z `dates`; maksima roczne są wtedy wybierane dla "
                    "kompletnych lat hydrologicznych XI–X). Długie szeregi podawaj w "
                    "pliku (`input_file`)."
                ),
                description_en=(
                    "Series in time order: annual maxima (without `dates`) or daily "
                    "values (with `dates`; the annual maxima are then taken for the "
                    "complete hydrological years Nov–Oct). Give long series in a file "
                    "(`input_file`)."
                ),
            ),
            replace(
                DATES,
                description=(
                    "Daty wartości dobowych w formacie ISO `RRRR-MM-DD`, ściśle "
                    "rosnące, tyle samo co `values`; pomiń, gdy `values` to maksima "
                    "roczne."
                ),
                description_en=(
                    "Dates of daily values in ISO format `YYYY-MM-DD`, strictly "
                    "increasing, as many as `values`; omit when `values` are annual "
                    "maxima."
                ),
            ),
            INPUT_FILE,
            VALUE_COLUMN,
            replace(
                DATE_COLUMN,
                description=(
                    "Nazwa kolumny z datami ISO w `input_file` (np. `date`); podaj "
                    "dla szeregu dobowego, pomiń dla maksimów rocznych."
                ),
                description_en=(
                    "Name of the column with ISO dates in `input_file` (e.g. `date`); "
                    "give it for a daily series, omit it for annual maxima."
                ),
            ),
            Option(
                name="distribution",
                type="choice",
                description=(
                    "Rozkład do dopasowania: `all` (cztery rozkłady posortowane wg "
                    "AIC), `log_normal`, `gev`, `pearson3` albo `weibull`."
                ),
                description_en=(
                    "Distribution to fit: `all` (the four distributions sorted by "
                    "AIC), `log_normal`, `gev`, `pearson3` or `weibull`."
                ),
                choices=("all", "log_normal", "gev", "pearson3", "weibull"),
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
        operation_id="stats_low_flow",
        summary=(
            "Analiza częstości niżówek: rozkład Fishera–Tippetta (GEV) dla minimów "
            "rocznych, kwantyle niskich przepływów."
        ),
        summary_en=(
            "Low-flow frequency analysis: Fisher–Tippett (GEV) distribution of annual "
            "minima, low-flow quantiles."
        ),
        description=(
            "Z szeregu dobowego wybiera minima roczne dla kompletnych lat "
            "hydrologicznych (1 XI – 31 X): rok jest kompletny, gdy ma wartość dla "
            "każdego dnia (365 albo 366 dni), a rok z brakującym dniem (nieobecna "
            "data albo NaN) jest pomijany, bo jego minimum mogło nie zostać "
            "zarejestrowane (WMO nr 1029, 2009 i KZGW 2017 biorą do analizy pełne "
            "lata obserwacji); pominięte lata wymienia `incomplete_years` w wyniku "
            "i w `notices` (kod `incomplete_years`), więc eksport z lat "
            "kalendarzowych traci pierwszy i ostatni rok hydrologiczny. Do minimów "
            "dopasowuje rozkład Fishera–Tippetta wartości najmniejszych (GEV dla "
            "minimów, czyli GEV maksimów dopasowany do ujemnych minimów, "
            "`scipy.stats.genextreme`): F(x) = 1 − exp(−(1 + "
            "shape·(x − loc)/scale)^(1/shape)); shape → 0 daje rozkład Gumbela, "
            "shape > 0 rozkład Weibulla z dolną granicą loc − scale/shape, `loc` i "
            "`scale` są w jednostce szeregu. Podaje kwantyle niskich przepływów "
            "q_T rzędu p = 1/T dla okresów powtarzalności "
            "T [lata]: przepływ, który raz na T lat jest osiągany lub niższy "
            "(prawdopodobieństwo nieprzekroczenia p = 1/T; WMO nr 1029, 2009; "
            "Tallaksen i van Lanen, 2004). Podaje też statystykę Kołmogorowa–"
            "Smirnowa (`ks_valid=false`: parametry oszacowano z tej samej próby) i "
            "częstość empiryczną minimów `empirical` w tej samej konwencji co "
            "kwantyle: `values_ascending` (minima rosnąco), "
            "`non_exceedance_probabilities` F = m/(n+1) (pozycje plotowania "
            "Weibulla, m = 1 dla najmniejszego minimum) i `return_periods` "
            "T = 1/F; najgłębsza niżówka ma najmniejsze F i najdłuższy okres "
            "T = n + 1. Minimum obliczeniowe to 3 kompletne lata hydrologiczne; "
            "poniżej 10 lat w `notices` pojawia się ostrzeżenie o niskiej "
            "wiarygodności. Wynik: `n_years`, `hydrological_years`, "
            "`annual_minima`, `incomplete_years`, `fisher_tippett` (`parameters`, "
            "`quantiles`, `non_exceedance_probabilities`, `ks_statistic`, "
            "`ks_p_value`) i `empirical`. Szereg wymaga dat; braki danych (NaN) są "
            "pomijane i zgłaszane w `notices` (dzień bez wartości kosztuje cały rok "
            "hydrologiczny)."
        ),
        description_en=(
            "Takes the annual minima of a daily series for the complete "
            "hydrological years (1 Nov – 31 Oct): a year is complete when it has a "
            "value for every day (365 or 366 days), and a year with a missing day "
            "(an absent date or a NaN) is skipped because its minimum may have gone "
            "unrecorded (WMO No. 1029, 2009 and KZGW 2017 analyse whole years of "
            "observations); the skipped years are listed in `incomplete_years` of "
            "the result and in `notices` (code `incomplete_years`), so a "
            "calendar-year export loses its first and last hydrological year. It "
            "fits to the minima the Fisher–Tippett distribution of smallest values "
            "(GEV for minima, i.e. the maxima GEV fitted to the negated minima, "
            "`scipy.stats.genextreme`): F(x) = 1 − exp(−(1 + "
            "shape·(x − loc)/scale)^(1/shape)); shape → 0 gives the Gumbel "
            "distribution, shape > 0 the Weibull distribution with the lower bound "
            "loc − scale/shape, `loc` and `scale` are in the unit of the series. "
            "It gives the low-flow quantiles q_T of order p = 1/T for the return "
            "periods T [years]: "
            "the flow reached or undercut once in T years (non-exceedance probability "
            "p = 1/T; WMO No. 1029, 2009; Tallaksen and van Lanen, 2004). It also "
            "gives the Kolmogorov–Smirnov statistic (`ks_valid=false`: the parameters "
            "are estimated from the same sample) and the empirical frequency of the "
            "minima `empirical` in the same convention as the quantiles: "
            "`values_ascending` (the minima, smallest first), "
            "`non_exceedance_probabilities` F = m/(n+1) (Weibull plotting positions, "
            "m = 1 for the smallest minimum) and `return_periods` T = 1/F; the "
            "deepest low flow has the smallest F and the longest period T = n + 1. "
            "The computational minimum is 3 complete hydrological years; fewer than "
            "10 years raise a reliability warning in `notices`. Result: `n_years`, "
            "`hydrological_years`, `annual_minima`, `incomplete_years`, "
            "`fisher_tippett` (`parameters`, `quantiles`, "
            "`non_exceedance_probabilities`, `ks_statistic`, `ks_p_value`) and "
            "`empirical`. The series needs dates; missing values (NaN) are skipped "
            "and reported in `notices` (a day without a value costs the whole "
            "hydrological year)."
        ),
        function="hydrolog.operations:stats_low_flow",
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
        operation_id="stats_low_flow_sequences",
        summary=(
            "Ciągi niżówkowe (susze hydrologiczne) metodą progową: terminy, czas "
            "trwania, niedobór."
        ),
        summary_en=(
            "Low-flow (drought) sequences by the threshold level method: dates, "
            "duration, deficit."
        ),
        description=(
            "Wykrywa niżówki metodą poziomu progowego (threshold level method; "
            "Tallaksen i van Lanen, 2004): niżówka to ciąg dób z wartością poniżej "
            "`threshold`; dwa ciągi rozdzielone przerwą krótszą niż `max_gap_days` dób "
            "są łączone, a zachowywane są tylko ciągi trwające co najmniej "
            "`min_duration_days` dób. Dla każdego ciągu wynik podaje daty początku i "
            "końca (włącznie), czas trwania [doby], minimum i średnią oraz niedobór "
            "`deficit_volume` = Σ(próg − wartość) po dobach poniżej progu "
            "[jednostka szeregu × doba; × 86400 daje m³ dla m³/s]. Szereg musi być "
            "kompletnym szeregiem dobowym (kolejne dni, bez luk i bez NaN), inaczej "
            "`calculation_error`. Wynik: `threshold`, `min_duration_days`, "
            "`max_gap_days`, `n_days`, `n_events`, `total_deficit`, "
            "`max_duration_days` i `sequences`."
        ),
        description_en=(
            "Detects low flows with the threshold level method (Tallaksen and van "
            "Lanen, 2004): a low-flow event is a run of days with a value below "
            "`threshold`; two runs separated by a gap shorter than `max_gap_days` "
            "days are merged, and only sequences lasting at least `min_duration_days` "
            "days are kept. For each sequence the result gives the start and end "
            "dates (inclusive), the duration [days], the minimum and mean, and the "
            "deficit `deficit_volume` = Σ(threshold − value) over the days below the "
            "threshold [series unit × day; × 86400 gives m³ for m³/s]. The series "
            "must be a complete daily series (consecutive days, no gaps, no NaN), "
            "otherwise `calculation_error`. Result: `threshold`, "
            "`min_duration_days`, `max_gap_days`, `n_days`, `n_events`, "
            "`total_deficit`, `max_duration_days` and `sequences`."
        ),
        function="hydrolog.operations:stats_low_flow_sequences",
        options=(
            VALUES,
            replace(
                DATES,
                description=(
                    "Daty kolejnych dób w formacie ISO `RRRR-MM-DD`: kolejne dni, bez "
                    "luk; tyle samo co `values`."
                ),
                description_en=(
                    "Dates of consecutive days in ISO format `YYYY-MM-DD`: successive "
                    "days without gaps; as many as `values`."
                ),
            ),
            INPUT_FILE,
            VALUE_COLUMN,
            replace(
                DATE_COLUMN,
                description=(
                    "Nazwa kolumny z datami ISO w `input_file` (np. `date`); daty "
                    "muszą być kolejnymi dniami, bez luk."
                ),
                description_en=(
                    "Name of the column with ISO dates in `input_file` (e.g. "
                    "`date`); the dates must be consecutive days without gaps."
                ),
            ),
            Option(
                name="threshold",
                type="number",
                description=(
                    "Próg niżówkowy w jednostce szeregu (np. m³/s), dodatni; dni z "
                    "wartością poniżej progu tworzą niżówkę."
                ),
                description_en=(
                    "Low-flow threshold in the unit of the series (e.g. m³/s), "
                    "positive; days with a value below it make up a low-flow event."
                ),
                required=True,
                exclusive_minimum=0,
            ),
            Option(
                name="min_duration_days",
                type="integer",
                description=(
                    "Najkrótszy raportowany ciąg niżówkowy w dobach, co najmniej 1."
                ),
                description_en=(
                    "Shortest low-flow sequence reported, in days, at least 1."
                ),
                default=5,
                minimum=1,
                unit="d",
            ),
            Option(
                name="max_gap_days",
                type="integer",
                description=(
                    "Przerwy krótsze niż ta liczba dób między dwoma ciągami poniżej "
                    "progu łączą je w jeden ciąg; 0 wyłącza łączenie."
                ),
                description_en=(
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
        operation_id="stats_mann_kendall",
        summary=(
            "Test trendu Manna–Kendalla szeregu (stacjonarność): statystyka, p-value, "
            "kierunek trendu."
        ),
        summary_en=(
            "Mann–Kendall trend test of a series (stationarity): statistic, p-value, "
            "trend direction."
        ),
        description=(
            "Nieparametryczny test istnienia monotonicznego trendu w szeregu "
            "uporządkowanym w czasie (Mann 1945; Kendall 1975), stosowany m.in. do "
            "oceny stacjonarności maksimów rocznych przed analizą częstości (KZGW). "
            "Liczy statystykę S (suma znaków różnic wszystkich par obserwacji), jej "
            "wariancję wzorem bez poprawki na powtórzenia (test nieco zachowawczy), "
            "statystykę Z z poprawką na ciągłość i dwustronne p-value; trend jest "
            "wykryty, gdy p < `alpha`, a jego kierunek (`increasing`, `decreasing`, "
            "`none`) wynika ze znaku S. Wymaga co najmniej 3 wartości; braki danych "
            "(NaN) są pomijane i zgłaszane w `notices`. Wynik: `s_statistic`, "
            "`var_s`, `z_score`, `p_value`, `trend_detected`, `trend_direction`, "
            "`significance_level`."
        ),
        description_en=(
            "Non-parametric test for a monotonic trend in a series ordered in time "
            "(Mann 1945; Kendall 1975), used among others to assess the stationarity "
            "of annual maxima before frequency analysis (KZGW). It computes the S "
            "statistic (sum of the signs of the differences of all pairs of "
            "observations), its variance by the formula without the correction for "
            "ties (the test is slightly conservative), the continuity-corrected Z "
            "statistic and the two-sided p-value; a trend is detected when p < "
            "`alpha`, and its direction (`increasing`, `decreasing`, `none`) follows "
            "the sign of S. At least 3 values are required; missing values (NaN) are "
            "skipped and reported in `notices`. Result: `s_statistic`, `var_s`, "
            "`z_score`, `p_value`, `trend_detected`, `trend_direction`, "
            "`significance_level`."
        ),
        function="hydrolog.operations:stats_mann_kendall",
        options=(
            replace(
                VALUES,
                description=(
                    "Szereg w kolejności czasowej, np. maksima roczne (co najmniej 3 "
                    "wartości). Długie szeregi podawaj w pliku (`input_file`)."
                ),
                description_en=(
                    "Series in time order, e.g. annual maxima (at least 3 values). "
                    "Give long series in a file (`input_file`)."
                ),
            ),
            replace(
                INPUT_FILE,
                description=(
                    "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON z "
                    "szeregiem; wiersze w kolejności czasowej. Kolumnę wskazuje "
                    "`value_column`."
                ),
                description_en=(
                    "CSV file (comma or semicolon, header row) or JSON file with the "
                    "series; rows in time order. The column is named by "
                    "`value_column`."
                ),
            ),
            VALUE_COLUMN,
            Option(
                name="alpha",
                type="number",
                description=(
                    "Poziom istotności testu z przedziału otwartego (0, 1), np. 0,05."
                ),
                description_en=(
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
