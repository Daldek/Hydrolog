"""Group ``meteo``: statistics of a meteorological station's daily series.

Precipitation (sums and normals, maxima, days, intensity, heavy precipitation,
seasonality), dry and wet spells, the standardized precipitation index, air
temperature, snow cover and Sielianinov's hydrothermal coefficient (plan 2026-11-13,
D12). The operations are in :mod:`hydrolog.operations.meteo`.
"""

from __future__ import annotations

from dataclasses import replace

from hydrolog.catalog.groups._attribution import ATTRIBUTION
from hydrolog.catalog.groups._series import DATES, FIRST_YEAR, INPUT_FILE, LAST_YEAR
from hydrolog.catalog.spec import Command, Option

_METEO_DAILY = "tests/fixtures/meteo_daily.csv"

# Errors of the commands that read a daily series.
_ERRORS = (
    "validation_error",
    "not_found",
    "data_error",
    "calculation_error",
    "forbidden",
)

_DATES = replace(
    DATES,
    description_pl=(
        "Daty wartości dobowych podanych w treści, ISO `RRRR-MM-DD`, ściśle rosnące; "
        "tyle samo co każda lista wartości. Długie szeregi podawaj w pliku."
    ),
    description=(
        "Dates of the inline daily values, ISO `YYYY-MM-DD`, strictly increasing; as "
        "many as each list of values. Give long series in a file."
    ),
)
_INPUT_FILE = replace(
    INPUT_FILE,
    description_pl=(
        "Plik CSV albo JSON z szeregiem dobowym stacji, np. eksport Obserwatora "
        "(`obserwator series export`): kolumny `date`, `P [mm]`, `P_flag`, "
        "`Tmax [degC]`, `Tmin [degC]`, `Tmean [degC]`, `snow_cover [cm]`, "
        "`fresh_snow [cm]`, znajdowane przez opcje `*_column`."
    ),
    description=(
        "CSV or JSON file with the station's daily series, e.g. Obserwator's export "
        "(`obserwator series export`): the columns `date`, `P [mm]`, `P_flag`, "
        "`Tmax [degC]`, `Tmin [degC]`, `Tmean [degC]`, `snow_cover [cm]`, "
        "`fresh_snow [cm]`, found by the `*_column` options."
    ),
)
_DATE_COLUMN = Option(
    name="date_column",
    type="string",
    description_pl="Kolumna dat ISO w `input_file`; domyślnie `date`.",
    description="Column of the ISO dates in `input_file`; default `date`.",
)
_YEAR_TYPE = Option(
    name="year_type",
    type="choice",
    description_pl="Rodzaj roku wyników i okresu.",
    description="The kind of year of the results and of the period.",
    choices=("calendar", "hydrological"),
    meanings={
        "calendar": "Calendar years, January to December.",
        "hydrological": "Hydrological years, November to October, named after the end.",
    },
    meanings_pl={
        "calendar": "Lata kalendarzowe, styczeń–grudzień.",
        "hydrological": "Lata hydrologiczne XI–X, nazwane rokiem, w którym się kończą.",
    },
    default="calendar",
)
_FIRST_YEAR = replace(
    FIRST_YEAR,
    description_pl=(
        "Pierwszy rok okresu (rodzaju `year_type`); domyślnie pierwszy rok z danymi. "
        "Zalecany okres to co najmniej 30 lat."
    ),
    description=(
        "First year of the period (of `year_type`); by default the first year with a "
        "value. At least 30 years are recommended."
    ),
)
_LAST_YEAR = replace(
    LAST_YEAR,
    description_pl="Ostatni rok okresu (rodzaju `year_type`); domyślnie ostatni.",
    description=(
        "Last year of the period (of `year_type`); by default the last year with a "
        "value."
    ),
)
_CALENDAR_FIRST_YEAR = replace(
    FIRST_YEAR,
    description_pl=(
        "Pierwszy rok kalendarzowy okresu; domyślnie pierwszy rok z danymi. Zalecany "
        "okres to co najmniej 30 lat."
    ),
    description=(
        "First calendar year of the period; by default the first year with a value. "
        "At least 30 years are recommended."
    ),
)
_CALENDAR_LAST_YEAR = replace(
    LAST_YEAR,
    description_pl="Ostatni rok kalendarzowy okresu; domyślnie ostatni z danymi.",
    description="Last calendar year of the period; by default the last with a value.",
)
_WINTER_FIRST_YEAR = replace(
    FIRST_YEAR,
    description_pl=(
        "Pierwsza zima okresu (sezon VIII–VII nazwany rokiem, w którym się kończy); "
        "domyślnie pierwsza z danymi. Zalecane co najmniej 30 zim."
    ),
    description=(
        "First winter of the period (the season August–July named after the year in "
        "which it ends); by default the first with a value. At least 30 are "
        "recommended."
    ),
)
_WINTER_LAST_YEAR = replace(
    LAST_YEAR,
    description_pl="Ostatnia zima okresu; domyślnie ostatnia z danymi.",
    description="Last winter of the period; by default the last with a value.",
)

_PRECIPITATION_MM = Option(
    name="precipitation_mm",
    type="number_list",
    description_pl="Dobowe sumy opadu [mm] podane w treści, po jednej na datę.",
    description="Inline daily precipitation [mm], one per date.",
    minimum=0,
    unit="mm",
)
_PRECIPITATION_COLUMN = Option(
    name="precipitation_column",
    type="string",
    description_pl=(
        "Kolumna dobowego opadu [mm] w `input_file`; domyślnie `P` (znajduje `P [mm]`)."
    ),
    description=(
        "Column of the daily precipitation [mm] in `input_file`; default `P` (finds "
        "`P [mm]`)."
    ),
)
_PRECIPITATION_FLAG_COLUMN = Option(
    name="precipitation_flag_column",
    type="string",
    description_pl=(
        "Kolumna flag opadu; wartość z flagą `accumulated` to suma dni bez pomiaru "
        "przed nią: w sumach miesięcznych zastępuje te dni (WMO-No. 1203), w "
        "statystykach dobowych jest brakiem. Domyślnie `P_flag`, gdy plik ją ma."
    ),
    description=(
        "Column of the precipitation flags; a value flagged `accumulated` is the total "
        "of the missing days before it: it stands for them in monthly sums (WMO-No. "
        "1203) and is missing for daily statistics. Default `P_flag` when the file has "
        "it."
    ),
)
_TMEAN_C = Option(
    name="tmean_c",
    type="number_list",
    description_pl="Średnia dobowa temperatura [°C] w treści, po jednej na datę.",
    description="Inline daily mean air temperature [°C], one per date.",
    unit="°C",
)
_TMAX_C = Option(
    name="tmax_c",
    type="number_list",
    description_pl="Maksymalna dobowa temperatura powietrza [°C] w treści.",
    description="Inline daily maximum air temperature [°C], one per date.",
    unit="°C",
)
_TMIN_C = Option(
    name="tmin_c",
    type="number_list",
    description_pl="Minimalna dobowa temperatura powietrza [°C] w treści.",
    description="Inline daily minimum air temperature [°C], one per date.",
    unit="°C",
)
_TMEAN_COLUMN = Option(
    name="tmean_column",
    type="string",
    description_pl="Kolumna średniej dobowej temperatury [°C]; domyślnie `Tmean`.",
    description="Column of the daily mean temperature [°C]; default `Tmean`.",
)
_TMAX_COLUMN = Option(
    name="tmax_column",
    type="string",
    description_pl="Kolumna maksymalnej temperatury [°C]; domyślnie `Tmax`.",
    description="Column of the daily maximum temperature [°C]; default `Tmax`.",
)
_TMIN_COLUMN = Option(
    name="tmin_column",
    type="string",
    description_pl="Kolumna minimalnej temperatury [°C]; domyślnie `Tmin`.",
    description="Column of the daily minimum temperature [°C]; default `Tmin`.",
)

_PRECIPITATION_SERIES = (
    _DATES,
    _PRECIPITATION_MM,
    _INPUT_FILE,
    _DATE_COLUMN,
    _PRECIPITATION_COLUMN,
    _PRECIPITATION_FLAG_COLUMN,
)
_PRECIPITATION_ONE_OF = (("dates", "precipitation_mm"), ("input_file",))
_PERIOD = (_YEAR_TYPE, _FIRST_YEAR, _LAST_YEAR)


def _celsius(name: str, default: float, text: str, text_pl: str) -> Option:
    """Declare a temperature threshold or base of ``meteo temperature`` [°C]."""
    return Option(
        name=name,
        type="number",
        description_pl=text_pl,
        description=text,
        default=default,
        unit="°C",
    )


COMMANDS: tuple[Command, ...] = (
    Command(
        name="meteo precipitation",
        operation_id="hydrolog_meteo_precipitation",
        summary_pl=(
            "Oblicz statystyki opadu: sumy i normalne, maksima, dni z opadem, "
            "natężenie, opady duże, reżim"
        ),
        summary=(
            "Compute precipitation statistics: sums and normals, maxima, days, "
            "intensity, heavy, regime"
        ),
        description_pl=(
            "Jeden wskaźnik `index` na wywołanie: `sums` (miesiące, półrocza, pory "
            "roku, lata, normalne okresu i % normalnej), `maxima` (największe sumy 1 "
            "i n dni z datami), `days` (dni z P ≥ `thresholds_mm`), `intensity` "
            "(SDII), `heavy` (R95pTOT, R99pTOT), `seasonality` (reżim, PCI, SI). Braki "
            "wg WMO-No. 1203; wskaźniki ETCCDI."
        ),
        description=(
            "One `index` per call: `sums` (months, half-years, seasons, years, the "
            "normals of the period and % of them), `maxima` (largest 1- and n-day sums "
            "with dates), `days` (days with P ≥ `thresholds_mm`), `intensity` (SDII), "
            "`heavy` (R95pTOT, R99pTOT), `seasonality` (regime, PCI, SI). Missing days "
            "by WMO-No. 1203; ETCCDI indices."
        ),
        result_schema="hydrolog-meteo-precipitation/1",
        cardinality="bounded",
        rules=(
            "Give daily P [mm]; Obserwator's export (`date`, `P`, `P_flag`) loads.",
            "For quantiles of `maxima` run `stats flood-frequency` on their values.",
        ),
        rules_pl=(
            (
                "Podaj dobowy opad [mm]; eksport Obserwatora (`date`, `P`, `P_flag`) "
                "wczytuje się wprost."
            ),
            "Kwantyle `maxima`: `stats flood-frequency` na ich wartościach.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "index": "sums",
                "first_year": 2019,
                "last_year": 2023,
                "period": {"normal_mm": 683.35, "normal_years": 4},
            },
            {
                "index": "maxima",
                "durations_days": [1, 2, 5],
                "period": {"n_years": 3, "incomplete_years": [2019, 2022]},
            },
            {"index": "days", "thresholds_mm": [0.1, 1.0, 10.0, 20.0]},
            {"index": "intensity", "year_type": "hydrological", "period_years": 4},
            {"index": "heavy", "period": {"wet_days": 601, "n_years": 3}},
            {"index": "seasonality", "period_years": 5},
        ),
        function="hydrolog.operations.meteo_precipitation",
        options=(
            Option(
                name="index",
                type="choice",
                description_pl="Obliczany wskaźnik.",
                description="The statistic to compute.",
                choices=(
                    "sums",
                    "maxima",
                    "days",
                    "intensity",
                    "heavy",
                    "seasonality",
                ),
                meanings={
                    "sums": "Sums of months, half-years, seasons, years; normals, %.",
                    "maxima": "Largest daily and n-day sums of years and months.",
                    "days": "Days with P at or above each of `thresholds_mm`.",
                    "intensity": "Mean annual sum and mean P of a wet day (SDII).",
                    "heavy": "Sums above percentiles of wet days (R95pTOT).",
                    "seasonality": "Regime of the normals, PCI and SI.",
                },
                meanings_pl={
                    "sums": "Sumy miesięcy, półroczy, pór roku, lat; normalne, %.",
                    "maxima": "Największe sumy dobowe i n-dniowe lat i miesięcy.",
                    "days": "Dni z P co najmniej każdego z `thresholds_mm`.",
                    "intensity": "Średnia suma roczna i opad dnia mokrego (SDII).",
                    "heavy": "Sumy powyżej percentyli dni mokrych (R95pTOT).",
                    "seasonality": "Reżim normalnych, PCI i SI.",
                },
                required=True,
            ),
            *_PRECIPITATION_SERIES,
            *_PERIOD,
            Option(
                name="durations_days",
                type="number_list",
                description_pl=(
                    "Dla `maxima`: długości sum wielodniowych [doby], całkowite od 1; "
                    "domyślnie 2, 3, 5, 10 (suma 1 doby jest zawsze)."
                ),
                description=(
                    "For `maxima`: durations of the multi-day sums [days], whole "
                    "numbers from 1; default 2, 3, 5, 10 (1 day is always given)."
                ),
                default=(2, 3, 5, 10),
                minimum=1,
                unit="d",
            ),
            Option(
                name="thresholds_mm",
                type="number_list",
                description_pl=(
                    "Dla `days`: progi opadu dobowego [mm], dodatnie; domyślnie 0,1, "
                    "1, 10, 20 (R10mm, R20mm ETCCDI)."
                ),
                description=(
                    "For `days`: thresholds of daily precipitation [mm], positive; "
                    "default 0.1, 1, 10, 20 (R10mm, R20mm of the ETCCDI)."
                ),
                default=(0.1, 1.0, 10.0, 20.0),
                exclusive_minimum=0,
                unit="mm",
            ),
            Option(
                name="wet_day_mm",
                type="number",
                description_pl=(
                    "Dla `intensity` i `heavy`: dzień mokry ma co najmniej tyle opadu "
                    "[mm]; domyślnie 1 (ETCCDI)."
                ),
                description=(
                    "For `intensity` and `heavy`: a wet day has at least this "
                    "precipitation [mm]; default 1 (ETCCDI)."
                ),
                default=1.0,
                exclusive_minimum=0,
                unit="mm",
            ),
            Option(
                name="percentiles",
                type="number_list",
                description_pl=(
                    "Dla `heavy`: percentyle opadu dni mokrych okresu, w (0, 100); "
                    "domyślnie 95 i 99."
                ),
                description=(
                    "For `heavy`: percentiles of the precipitation of the wet days of "
                    "the period, in (0, 100); default 95 and 99."
                ),
                default=(95.0, 99.0),
                exclusive_minimum=0,
                maximum=100,
            ),
            ATTRIBUTION,
        ),
        one_of=_PRECIPITATION_ONE_OF,
        examples=(
            {"index": "sums", "input_file": _METEO_DAILY},
            {
                "index": "maxima",
                "input_file": _METEO_DAILY,
                "durations_days": [2, 5],
            },
            {"index": "days", "input_file": _METEO_DAILY},
            {
                "index": "intensity",
                "input_file": _METEO_DAILY,
                "year_type": "hydrological",
                "first_year": 2020,
                "last_year": 2023,
            },
            {"index": "heavy", "input_file": _METEO_DAILY},
            {"index": "seasonality", "input_file": _METEO_DAILY},
        ),
    ),
    Command(
        name="meteo spells",
        operation_id="hydrolog_meteo_spells",
        summary_pl=(
            "Znajdź ciągi dni bezopadowych albo opadowych z najdłuższym ciągiem i "
            "liczebnościami lat"
        ),
        summary=(
            "Find the dry or wet spells of daily precipitation, the longest and the "
            "counts of each year"
        ),
        description_pl=(
            "Ciągi dni z P poniżej `threshold_mm` (`dry`) albo co najmniej progu "
            "(`wet`; CDD i CWD ETCCDI dla 1 mm) wg logiki ciągów `stats "
            "threshold-events`: każdy ciąg, w każdym roku najdłuższy i liczba ciągów "
            "co najmniej 10, 15 i 20 dni, rozkład długości. Dzień bez danych kończy "
            "ciąg (otwarty)."
        ),
        description=(
            "Runs of days with P below `threshold_mm` (`dry`) or at least it (`wet`; "
            "CDD "
            "and CWD of the ETCCDI for 1 mm) by the run logic of `stats "
            "threshold-events`: each spell, per year the longest and the spells of at "
            "least 10, 15 and 20 days, and the distribution of lengths. A day without "
            "a value ends a spell (open)."
        ),
        result_schema="hydrolog-meteo-spells/1",
        cardinality="bounded",
        rules=(
            "A spell counts in the year in which it starts.",
            "Yearly counts need every day of the year.",
        ),
        rules_pl=(
            "Ciąg liczy się w roku, w którym się zaczyna.",
            "Liczebności roku wymagają danych z każdego dnia.",
        ),
        errors=_ERRORS,
        example_results=(
            {"kind": "dry", "n_spells": 333, "max_length_days": 21},
            {"kind": "wet", "threshold_mm": 0.1, "n_spells": 317},
        ),
        function="hydrolog.operations.meteo_spells",
        options=(
            Option(
                name="kind",
                type="choice",
                description_pl="Ciągi dni bezopadowych albo opadowych.",
                description="Dry or wet spells.",
                choices=("dry", "wet"),
                meanings={
                    "dry": "Days with P below `threshold_mm`.",
                    "wet": "Days with P at or above `threshold_mm`.",
                },
                meanings_pl={
                    "dry": "Dni z P poniżej `threshold_mm`.",
                    "wet": "Dni z P co najmniej `threshold_mm`.",
                },
                default="dry",
            ),
            Option(
                name="threshold_mm",
                type="number",
                description_pl="Próg opadu dobowego [mm], dodatni; domyślnie 1.",
                description="Threshold of daily precipitation [mm]; default 1.",
                default=1.0,
                exclusive_minimum=0,
                unit="mm",
            ),
            *_PRECIPITATION_SERIES,
            *_PERIOD,
            ATTRIBUTION,
        ),
        one_of=_PRECIPITATION_ONE_OF,
        examples=(
            {"input_file": _METEO_DAILY},
            {"input_file": _METEO_DAILY, "kind": "wet", "threshold_mm": 0.1},
        ),
    ),
    Command(
        name="meteo spi",
        operation_id="hydrolog_meteo_spi",
        summary_pl=(
            "Oblicz SPI 1–12 miesięcy oraz opad względny i jego klasy w miesiącach i "
            "latach"
        ),
        summary=(
            "Compute the SPI of several scales and the relative precipitation of "
            "months and years"
        ),
        description_pl=(
            "SPI każdego miesiąca dla `scales_months` (rozkład gamma z "
            "prawdopodobieństwem zera dla każdego miesiąca kalendarzowego, metoda "
            "Thoma; McKee i in., 1993; WMO-No. 1090) oraz opad w % normalnej z klasą: "
            "lata wg Kaczorowskiej (1962), miesiące wg progów miesięcznych "
            "(Tomaszewska, 1994)."
        ),
        description=(
            "The SPI of each month for `scales_months` (a gamma distribution with the "
            "probability of zero per calendar month, Thom's fit; McKee et al., 1993; "
            "WMO-No. 1090) and the precipitation in % of its normal with its class: "
            "years by Kaczorowska (1962), months by the monthly limits (Tomaszewska, "
            "1994)."
        ),
        result_schema="hydrolog-meteo-spi/1",
        cardinality="bounded",
        rules=("A fit needs sums in 80 % of the years; 30 or more years are advised.",),
        rules_pl=("Dopasowanie wymaga sum w 80 % lat; zalecane co najmniej 30 lat.",),
        errors=_ERRORS,
        example_results=(
            {"scales_months": [1, 3, 6, 12], "period": {"normal_mm": 683.35}},
            {"scales_months": [1, 3], "year_type": "hydrological"},
        ),
        function="hydrolog.operations.meteo_spi",
        options=(
            Option(
                name="scales_months",
                type="number_list",
                description_pl=(
                    "Skale SPI [miesiące], całkowite od 1 do 48; domyślnie 1, 3, 6, 12."
                ),
                description=(
                    "Scales of the SPI [months], whole numbers 1 to 48; default 1, "
                    "3, 6, 12."
                ),
                default=(1, 3, 6, 12),
                minimum=1,
                maximum=48,
            ),
            *_PRECIPITATION_SERIES,
            *_PERIOD,
            ATTRIBUTION,
        ),
        one_of=_PRECIPITATION_ONE_OF,
        examples=(
            {"input_file": _METEO_DAILY},
            {
                "input_file": _METEO_DAILY,
                "scales_months": [1, 3],
                "year_type": "hydrological",
            },
        ),
    ),
    Command(
        name="meteo temperature",
        operation_id="hydrolog_meteo_temperature",
        summary_pl=(
            "Oblicz statystyki temperatury powietrza: średnie i normalne, dni "
            "charakterystyczne, stopniodni"
        ),
        summary=(
            "Compute air temperature statistics: means and normals, characteristic "
            "days, degree days, range"
        ),
        description_pl=(
            "Jeden wskaźnik `index` na wywołanie: `means` (średnie miesięczne i roczne "
            "Tśr, Tmax, Tmin, normalna i anomalia, ekstrema), `days` (dni z "
            "przymrozkiem, mroźne, gorące, upalne, noce tropikalne; ETCCDI), "
            "`degree_days` (stopniodni wzrostu > 5 °C, grzania 18 − Tśr gdy Tśr ≤ "
            "15 °C, Eurostat), `range` (średnia amplituda dobowa). Braki wg WMO-No. "
            "1203."
        ),
        description=(
            "One `index` per call: `means` (monthly and annual Tmean, Tmax, Tmin, the "
            "normal and anomaly, extremes), `days` (frost, ice, summer, hot days, "
            "tropical nights; ETCCDI), `degree_days` (growing above 5 °C; heating "
            "18 − Tmean when Tmean ≤ 15 °C, Eurostat), `range` (mean daily range). "
            "Missing days by WMO-No. 1203."
        ),
        result_schema="hydrolog-meteo-temperature/1",
        cardinality="bounded",
        rules=(
            "Give °C: `means` and `degree_days` need Tmean, `range` Tmax and Tmin.",
        ),
        rules_pl=(
            "Podaj °C: `means` i `degree_days` wymagają Tśr, `range` Tmax i Tmin.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "index": "means",
                "period": {"normal_years": 4, "max_c": 34.0, "max_date": "2021-07-16"},
            },
            {"index": "days", "period": {"hot_days": 1.75, "tropical_nights": 1.75}},
            {"index": "degree_days", "year_type": "hydrological", "first_year": 2020},
            {"index": "range", "last_year": 2021, "period": {"n_years": 3}},
        ),
        function="hydrolog.operations.meteo_temperature",
        options=(
            Option(
                name="index",
                type="choice",
                description_pl="Obliczany wskaźnik.",
                description="The statistic to compute.",
                choices=("means", "days", "degree_days", "range"),
                meanings={
                    "means": "Monthly and annual means, normal, anomaly, extremes.",
                    "days": "Frost, ice, summer and hot days, tropical nights.",
                    "degree_days": "Growing and heating degree days.",
                    "range": "Mean daily range Tmax - Tmin.",
                },
                meanings_pl={
                    "means": "Średnie, normalna, anomalia, ekstrema.",
                    "days": "Dni z przymrozkiem, mroźne, gorące, upalne, noce tropik.",
                    "degree_days": "Stopniodni wzrostu i grzania.",
                    "range": "Średnia amplituda dobowa Tmax - Tmin.",
                },
                required=True,
            ),
            _DATES,
            _TMEAN_C,
            _TMAX_C,
            _TMIN_C,
            _INPUT_FILE,
            _DATE_COLUMN,
            _TMEAN_COLUMN,
            _TMAX_COLUMN,
            _TMIN_COLUMN,
            *_PERIOD,
            _celsius(
                "frost_tmin_c",
                0.0,
                "For `days`: a frost day has Tmin below this [°C]; default 0 (FD).",
                "Dla `days`: dzień z przymrozkiem ma Tmin poniżej [°C]; domyślnie 0.",
            ),
            _celsius(
                "ice_tmax_c",
                0.0,
                "For `days`: an ice day has Tmax below this [°C]; default 0 (ID).",
                "Dla `days`: dzień mroźny ma Tmax poniżej [°C]; domyślnie 0.",
            ),
            _celsius(
                "summer_tmax_c",
                25.0,
                "For `days`: a summer day has Tmax above this [°C]; default 25 (SU).",
                "Dla `days`: dzień gorący ma Tmax powyżej [°C]; domyślnie 25.",
            ),
            _celsius(
                "hot_tmax_c",
                30.0,
                "For `days`: a hot day has Tmax above this [°C]; default 30.",
                "Dla `days`: dzień upalny ma Tmax powyżej [°C]; domyślnie 30.",
            ),
            _celsius(
                "tropical_tmin_c",
                20.0,
                "For `days`: a tropical night has Tmin above this [°C]; default 20.",
                "Dla `days`: noc tropikalna ma Tmin powyżej [°C]; domyślnie 20.",
            ),
            _celsius(
                "growing_base_c",
                5.0,
                "For `degree_days`: base of the growing degree days [°C]; default 5.",
                "Dla `degree_days`: próg stopniodni wzrostu [°C]; domyślnie 5.",
            ),
            _celsius(
                "heating_base_c",
                18.0,
                "For `degree_days`: base of the heating degree days [°C]; default 18.",
                "Dla `degree_days`: baza stopniodni grzania [°C]; domyślnie 18.",
            ),
            _celsius(
                "heating_limit_c",
                15.0,
                "For `degree_days`: a day heats when Tmean is at most this [°C]; "
                "default 15.",
                "Dla `degree_days`: dzień grzewczy ma Tśr co najwyżej [°C]; dom. 15.",
            ),
            ATTRIBUTION,
        ),
        one_of=(("dates",), ("input_file",)),
        examples=(
            {"index": "means", "input_file": _METEO_DAILY},
            {"index": "days", "input_file": _METEO_DAILY},
            {
                "index": "degree_days",
                "input_file": _METEO_DAILY,
                "year_type": "hydrological",
                "first_year": 2020,
            },
            {"index": "range", "input_file": _METEO_DAILY, "last_year": 2021},
        ),
    ),
    Command(
        name="meteo snow",
        operation_id="hydrolog_meteo_snow",
        summary_pl=(
            "Oblicz pokrywę śnieżną każdej zimy: dni, największa grubość, pierwszy i "
            "ostatni dzień"
        ),
        summary=(
            "Compute the snow cover of each winter: days, largest depth, first and "
            "last day, fresh snow"
        ),
        description_pl=(
            "Każda zima to sezon VIII–VII nazwany rokiem hydrologicznym, w którym się "
            "kończy: dni z pokrywą ≥ 1 cm (skalowane w miesiącach wg WMO-No. 1203), "
            "największa grubość z datą, pierwszy i ostatni dzień z pokrywą, suma "
            "śniegu świeżego. Zima wymaga dość danych w miesiącach X–V."
        ),
        description=(
            "Each winter is a season August–July named after the hydrological year it "
            "ends in: days with snow cover ≥ 1 cm (scaled per month by WMO-No. 1203), "
            "the largest depth with its day, the first and the last day with cover and "
            "the sum of fresh snow. A winter needs enough days in October–May."
        ),
        result_schema="hydrolog-meteo-snow/1",
        cardinality="bounded",
        rules=("Give depths in cm; 0 means no snow cover.",),
        rules_pl=("Podaj grubości w cm; 0 oznacza brak pokrywy.",),
        errors=_ERRORS,
        example_results=(
            {
                "first_year": 2019,
                "period": {
                    "n_years": 3,
                    "max_depth_cm": 68.0,
                    "earliest_first_date": "2020-10-27",
                },
            },
        ),
        function="hydrolog.operations.meteo_snow",
        options=(
            _DATES,
            Option(
                name="snow_cover_cm",
                type="number_list",
                description_pl="Grubość pokrywy śnieżnej [cm] w treści, na datę.",
                description="Inline depth of the snow cover [cm], one per date.",
                minimum=0,
                unit="cm",
            ),
            Option(
                name="fresh_snow_cm",
                type="number_list",
                description_pl="Grubość śniegu świeżego [cm] w treści, na datę.",
                description="Inline depth of fresh snow [cm], one per date.",
                minimum=0,
                unit="cm",
            ),
            _INPUT_FILE,
            _DATE_COLUMN,
            Option(
                name="snow_cover_column",
                type="string",
                description_pl="Kolumna grubości pokrywy [cm]; domyślnie `snow_cover`.",
                description="Column of the snow depth [cm]; default `snow_cover`.",
            ),
            Option(
                name="fresh_snow_column",
                type="string",
                description_pl=(
                    "Kolumna śniegu świeżego [cm]; domyślnie `fresh_snow`, gdy plik ją "
                    "ma."
                ),
                description=(
                    "Column of fresh snow [cm]; default `fresh_snow` when the file has "
                    "it."
                ),
            ),
            _WINTER_FIRST_YEAR,
            _WINTER_LAST_YEAR,
            ATTRIBUTION,
        ),
        one_of=(("dates", "snow_cover_cm"), ("input_file",)),
        examples=({"input_file": _METEO_DAILY},),
    ),
    Command(
        name="meteo hydrothermal",
        operation_id="hydrolog_meteo_hydrothermal",
        summary_pl=(
            "Oblicz współczynnik hydrotermiczny Sielianinowa miesięcy IV–IX i okresu "
            "Tśr > 10 °C"
        ),
        summary=(
            "Compute Sielianinov's hydrothermal coefficient of the months IV–IX and "
            "of the warm season"
        ),
        description_pl=(
            "k = P/(0,1 Σt) każdego miesiąca IV–IX (Σt to średnia miesięczna "
            "temperatura razy liczba dni; Skowera i Puła, 2004) i dni z Tśr > 10 °C "
            "każdego roku kalendarzowego (Sielianinow, 1928), z 9 klasami Skowery i "
            "Puły. Wymaga dobowego opadu [mm] i Tśr [°C]."
        ),
        description=(
            "k = P/(0.1 Σt) of each month April–September (Σt the monthly mean "
            "temperature times its days; Skowera and Puła, 2004) and of the days with "
            "Tmean > 10 °C of each calendar year (Selyaninov, 1928), with the nine "
            "classes of Skowera and Puła. Needs daily P [mm] and Tmean [°C]."
        ),
        result_schema="hydrolog-meteo-hydrothermal/1",
        cardinality="bounded",
        rules=("The season needs both values on every day of the year.",),
        rules_pl=("Okres wymaga obu wartości w każdym dniu roku.",),
        errors=_ERRORS,
        example_results=(
            {"first_year": 2019, "period": {"mean_season_class": "optimal"}},
        ),
        function="hydrolog.operations.meteo_hydrothermal",
        options=(
            _DATES,
            _PRECIPITATION_MM,
            _TMEAN_C,
            _INPUT_FILE,
            _DATE_COLUMN,
            _PRECIPITATION_COLUMN,
            _PRECIPITATION_FLAG_COLUMN,
            _TMEAN_COLUMN,
            _CALENDAR_FIRST_YEAR,
            _CALENDAR_LAST_YEAR,
            ATTRIBUTION,
        ),
        one_of=(("dates", "precipitation_mm", "tmean_c"), ("input_file",)),
        examples=({"input_file": _METEO_DAILY},),
    ),
)
