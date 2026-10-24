"""Group ``tc``: time of concentration.

One command per empirical formula of :class:`~hydrolog.time.ConcentrationTime`
(``tc kirpich``, ``tc nrcs``, ``tc giandotti``, ``tc faa``, ``tc kerby``,
``tc kerby-kirpich``) and ``tc watershed``, which applies one of the methods to a
:class:`~hydrolog.morphometry.WatershedParameters` file. All results are given in
minutes and hours.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")

_KERBY_TABLE_PL = (
    "Typowe wartości N: 0,02 gładka nawierzchnia nieprzepuszczalna; 0,10 gładka "
    "twarda gleba; 0,20 słaba trawa, uprawy rzędowe; 0,40 pastwisko, przeciętna "
    "trawa; 0,60 las liściasty; 0,80 gęsta trawa, las iglasty."
)
_KERBY_TABLE_EN = (
    "Typical N: 0.02 smooth impervious surface; 0.10 smooth bare packed soil; "
    "0.20 poor grass, row crops; 0.40 pasture, average grass; 0.60 deciduous "
    "forest; 0.80 dense grass, coniferous forest."
)

_CN = Option(
    name="cn",
    type="number",
    description=(
        "Liczba krzywej CN dla AMC II, 1–100 (zalecany zakres metody: 50–95); "
        "może być ułamkowa (np. średnia ważona z `cn weighted`)."
    ),
    description_en=(
        "Curve Number CN for AMC II, 1-100 (recommended range of the method: "
        "50-95); may be fractional (e.g. a weighted mean from `cn weighted`)."
    ),
    required=True,
    minimum=1,
    maximum=100,
)

_RETARDANCE = Option(
    name="retardance",
    type="number",
    description=(
        "Współczynnik retardacji (szorstkości) Kerby'ego N, > 0; zwykle "
        f"0,02–0,80. {_KERBY_TABLE_PL}"
    ),
    description_en=(
        "Kerby retardance (roughness) coefficient N, > 0; usually 0.02-0.80. "
        f"{_KERBY_TABLE_EN}"
    ),
    required=True,
    exclusive_minimum=0,
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="tc kirpich",
        operation_id="tc_kirpich",
        summary="Czas koncentracji wzorem Kirpicha z długości i spadku cieku głównego.",
        summary_en=(
            "Time of concentration by the Kirpich formula (channel length, slope)."
        ),
        description=(
            "Czas koncentracji tc wzorem Kirpicha (1940): tc [min] = 3,981 · L^0,77 · "
            "S^(−0,385), gdzie L to długość cieku głównego od działu wodnego do "
            "przekroju zamykającego [km], a S to średni spadek cieku [m/m] "
            "(bezwymiarowy, nie w procentach). Wzór opracowano dla małych zlewni "
            "rolniczych (0,004–0,45 km², spadki 3–10%); dla L > 80 km lub S poza "
            "0,002–0,15 wynik zawiera ostrzeżenie. Wynik: tc w minutach i godzinach "
            "oraz użyte parametry. Literatura: Kirpich, Z.P. (1940), Time of "
            "concentration of small agricultural watersheds, Civil Engineering "
            "10(6), 362."
        ),
        description_en=(
            "Time of concentration tc by the Kirpich (1940) formula: tc [min] = "
            "3.981 · L^0.77 · S^(-0.385), where L is the main channel length from "
            "the watershed divide to the outlet [km] and S the mean channel slope "
            "[m/m] (dimensionless, not percent). The formula was derived for small "
            "agricultural watersheds (0.004-0.45 km2, slopes 3-10%); a warning is "
            "reported for L > 80 km or S outside 0.002-0.15. Result: tc in minutes "
            "and hours and the parameters used. Reference: Kirpich, Z.P. (1940), "
            "Time of concentration of small agricultural watersheds, Civil "
            "Engineering 10(6), 362."
        ),
        function="hydrolog.operations:tc_kirpich",
        options=(
            Option(
                name="length_km",
                type="number",
                description=(
                    "Długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego [km]; > 0 (typowo ≤ 80)."
                ),
                description_en=(
                    "Main channel length from the watershed divide to the outlet "
                    "[km]; > 0 (typically <= 80)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description=(
                    "Średni spadek cieku głównego [m/m] (nie w procentach); > 0 "
                    "(typowo 0,002–0,15)."
                ),
                description_en=(
                    "Mean slope of the main channel [m/m] (not percent); > 0 "
                    "(typically 0.002-0.15)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
        ),
        examples=({"length_km": 8.2, "slope_m_per_m": 0.023},),
    ),
    Command(
        name="tc nrcs",
        operation_id="tc_nrcs",
        summary=(
            "Czas koncentracji metodą NRCS (TR-55, czas opóźnienia) z L, spadku i CN."
        ),
        summary_en=(
            "Time of concentration by the NRCS (TR-55 lag) method from L, slope, CN."
        ),
        description=(
            "Czas koncentracji tc metodą NRCS (TR-55): najpierw czas opóźnienia "
            "tlag [h] = L^0,8 · (S_r + 25,4)^0,7 / (7069 · Y^0,5), gdzie L to długość "
            "drogi hydraulicznej [m], S_r = 25400/CN − 254 to maksymalna retencja "
            "[mm], a Y to średni spadek zlewni [%]; następnie tc = tlag / 0,6. "
            "Wejście w jednostkach metrycznych: L [km], spadek [m/m] (przeliczany "
            "wewnętrznie na %), CN 1–100 (zalecany zakres metody 50–95). Zwraca tc, "
            "nie tlag (tlag = 0,6 · tc). Dla parametrów poza typowym zakresem "
            "(L 0,03–30 km, spadek 0,001–0,15) wynik zawiera ostrzeżenie. "
            "Literatura: USDA-NRCS (1986), Urban Hydrology for Small Watersheds, "
            "TR-55, rozdz. 3."
        ),
        description_en=(
            "Time of concentration tc by the NRCS (TR-55) method: first the lag "
            "time tlag [h] = L^0.8 · (S_r + 25.4)^0.7 / (7069 · Y^0.5), where L is "
            "the hydraulic length [m], S_r = 25400/CN - 254 the maximum retention "
            "[mm] and Y the mean watershed slope [%]; then tc = tlag / 0.6. Metric "
            "input: L [km], slope [m/m] (converted to % internally), CN 1-100 "
            "(recommended range of the method 50-95). Returns tc, not tlag (tlag = "
            "0.6 · tc). A warning is reported for parameters outside the typical "
            "range (L 0.03-30 km, slope 0.001-0.15). Reference: USDA-NRCS (1986), "
            "Urban Hydrology for Small Watersheds, TR-55, chapter 3."
        ),
        function="hydrolog.operations:tc_nrcs",
        options=(
            Option(
                name="length_km",
                type="number",
                description=(
                    "Długość drogi hydraulicznej zlewni (najdłuższej ścieżki "
                    "spływu) [km]; > 0 (typowo 0,03–30)."
                ),
                description_en=(
                    "Hydraulic length of the watershed (longest flow path) [km]; "
                    "> 0 (typically 0.03-30)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description=(
                    "Średni spadek zlewni [m/m] (nie w procentach); > 0 (typowo "
                    "0,001–0,15)."
                ),
                description_en=(
                    "Mean watershed slope [m/m] (not percent); > 0 (typically "
                    "0.001-0.15)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _CN,
        ),
        examples=({"length_km": 8.2, "slope_m_per_m": 0.023, "cn": 72},),
    ),
    Command(
        name="tc giandotti",
        operation_id="tc_giandotti",
        summary=(
            "Czas koncentracji wzorem Giandottiego z powierzchni, długości i spadku."
        ),
        summary_en=(
            "Time of concentration by the Giandotti formula (area, length, relief)."
        ),
        description=(
            "Czas koncentracji tc wzorem Giandottiego (1934): tc [h] = (4·√A + "
            "1,5·L) / (0,8·√H), gdzie A to powierzchnia zlewni [km²], L długość "
            "cieku głównego [km], H różnica wysokości między średnią wysokością "
            "zlewni a przekrojem zamykającym [m]. Wzór opracowano dla większych "
            "zlewni górskich we Włoszech (> 170 km²); dla A poza 100–10 000 km², "
            "L poza 1–300 km lub H poza 20–3000 m wynik zawiera ostrzeżenie. "
            "Wynik jest przeliczony na minuty. Literatura: Giandotti, M. (1934), "
            "Previsione delle piene e delle magre dei corsi d'acqua, Memorie e "
            "Studi Idrografici 8; Grimaldi, S. i in. (2012), Hydrological Sciences "
            "Journal 57(2), 217–228."
        ),
        description_en=(
            "Time of concentration tc by the Giandotti (1934) formula: tc [h] = "
            "(4·sqrt(A) + 1.5·L) / (0.8·sqrt(H)), where A is the watershed area "
            "[km2], L the main channel length [km] and H the difference between "
            "the mean watershed elevation and the outlet [m]. The formula was "
            "derived for larger Italian mountain watersheds (> 170 km2); a warning "
            "is reported for A outside 100-10,000 km2, L outside 1-300 km or H "
            "outside 20-3000 m. The result is converted to minutes. References: "
            "Giandotti, M. (1934), Previsione delle piene e delle magre dei corsi "
            "d'acqua, Memorie e Studi Idrografici 8; Grimaldi, S. et al. (2012), "
            "Hydrological Sciences Journal 57(2), 217-228."
        ),
        function="hydrolog.operations:tc_giandotti",
        options=(
            Option(
                name="area_km2",
                type="number",
                description="Powierzchnia zlewni [km²]; > 0 (typowo 100–10 000).",
                description_en="Watershed area [km2]; > 0 (typically 100-10,000).",
                required=True,
                exclusive_minimum=0,
                unit="km2",
            ),
            Option(
                name="length_km",
                type="number",
                description="Długość cieku głównego [km]; > 0 (typowo 1–300).",
                description_en="Main channel length [km]; > 0 (typically 1-300).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="elevation_diff_m",
                type="number",
                description=(
                    "Różnica wysokości między średnią wysokością zlewni a "
                    "przekrojem zamykającym [m]; > 0 (typowo 20–3000)."
                ),
                description_en=(
                    "Difference between the mean watershed elevation and the "
                    "outlet [m]; > 0 (typically 20-3000)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m",
            ),
        ),
        examples=({"area_km2": 145.0, "length_km": 21.5, "elevation_diff_m": 320.0},),
    ),
    Command(
        name="tc faa",
        operation_id="tc_faa",
        summary=(
            "Czas koncentracji metodą FAA dla spływu powierzchniowego (L, spadek, C)."
        ),
        summary_en=(
            "Time of concentration by the FAA method for overland flow (L, slope, C)."
        ),
        description=(
            "Czas koncentracji tc metodą FAA (Federal Aviation Agency) dla spływu "
            "powierzchniowego na krótkich, płaskich drogach: tc [min] = 22,213 · "
            "(1,1 − C) · L^0,5 / S^(1/3) (wersja metryczna wzoru 1,8·(1,1−C)·"
            "L[ft]^0,5 / S[%]^(1/3)). L to długość spływu powierzchniowego [km], "
            "S średni spadek terenu [m/m], C współczynnik odpływu metody "
            "wymiernej (0 < C ≤ 1). Typowy zakres: L 0,015–3 km, S 0,005–0,10, "
            "C 0,10–0,95 (poza nim wynik zawiera ostrzeżenie). To czas spływu "
            "powierzchniowego, nie czas koncentracji zlewni z korytem (do tego "
            "`tc kerby-kirpich` albo `tc kirpich`). Literatura: Federal Aviation "
            "Agency (1966), Airport Drainage, AC 150/5320-5A; FAA (2013), Airport "
            "Drainage Design, AC 150/5320-5D."
        ),
        description_en=(
            "Time of concentration tc by the FAA (Federal Aviation Agency) method "
            "for overland flow on short, flat paths: tc [min] = 22.213 · (1.1 - C) "
            "· L^0.5 / S^(1/3) (metric form of 1.8·(1.1-C)·L[ft]^0.5 / "
            "S[%]^(1/3)). L is the overland flow length [km], S the mean ground "
            "slope [m/m], C the rational-method runoff coefficient (0 < C <= 1). "
            "Typical range: L 0.015-3 km, S 0.005-0.10, C 0.10-0.95 (a warning is "
            "reported outside it). It is the overland flow time, not the time of "
            "concentration of a watershed with a channel (use `tc kerby-kirpich` "
            "or `tc kirpich` for that). References: Federal Aviation Agency "
            "(1966), Airport Drainage, AC 150/5320-5A; FAA (2013), Airport "
            "Drainage Design, AC 150/5320-5D."
        ),
        function="hydrolog.operations:tc_faa",
        options=(
            Option(
                name="length_km",
                type="number",
                description=(
                    "Długość spływu powierzchniowego [km]; > 0 (typowo 0,015–3)."
                ),
                description_en="Overland flow length [km]; > 0 (typically 0.015-3).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description=(
                    "Średni spadek terenu [m/m] (nie w procentach); > 0 (typowo "
                    "0,005–0,10)."
                ),
                description_en=(
                    "Mean ground slope [m/m] (not percent); > 0 (typically 0.005-0.10)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="runoff_coeff",
                type="number",
                description=(
                    "Współczynnik odpływu C metody wymiernej, 0 < C ≤ 1 (typowo "
                    "0,10–0,95)."
                ),
                description_en=(
                    "Rational-method runoff coefficient C, 0 < C <= 1 (typically "
                    "0.10-0.95)."
                ),
                required=True,
                exclusive_minimum=0,
                maximum=1,
            ),
        ),
        examples=({"length_km": 0.15, "slope_m_per_m": 0.02, "runoff_coeff": 0.6},),
    ),
    Command(
        name="tc kerby",
        operation_id="tc_kerby",
        summary=(
            "Czas spływu powierzchniowego wzorem Kerby'ego (L, spadek, retardancja N)."
        ),
        summary_en=(
            "Overland flow time of concentration by the Kerby formula (L, slope, N)."
        ),
        description=(
            "Czas koncentracji tc dla spływu warstwowego wzorem Kerby'ego (1959) w "
            "wersji metrycznej: tc [min] = 36,37 · (L·N)^0,467 · S^(−0,2335), gdzie "
            "L to długość spływu powierzchniowego [km], S średni spadek terenu "
            "[m/m], a N współczynnik retardacji. Dla S < 0,002 stosowana jest "
            "poprawka niskiego spadku (Cleveland i in., 2012): S + 0,0005. "
            "Wzór dotyczy krótkich dróg spływu (typowo L ≤ 0,366 km, S "
            "0,001–0,01, N 0,02–0,80; poza tym zakresem wynik zawiera "
            "ostrzeżenie); to czas spływu powierzchniowego, nie czas koncentracji "
            "zlewni z korytem (do tego `tc kerby-kirpich` albo `tc kirpich`). "
            "Literatura: Kerby, W.S. (1959), Civil Engineering "
            "29(3), 174; Roussel, M.C. i in. (2005), TxDOT Report 0-4696-2; "
            "Cleveland, T.G. i in. (2012), TxDOT Report 0-6544-1."
        ),
        description_en=(
            "Time of concentration tc for sheet flow by the Kerby (1959) formula in "
            "metric form: tc [min] = 36.37 · (L·N)^0.467 · S^(-0.2335), where L is "
            "the overland flow length [km], S the mean ground slope [m/m] and N the "
            "retardance coefficient. For S < 0.002 the low-slope adjustment "
            "(Cleveland et al., 2012) S + 0.0005 is applied. The formula is meant "
            "for short flow paths (typically L <= 0.366 km, S 0.001-0.01, N "
            "0.02-0.80; a warning is reported outside that range); it is the "
            "overland flow time, not the time of concentration of a watershed with "
            "a channel (use `tc kerby-kirpich` or `tc kirpich` for that). "
            "References: Kerby, W.S. (1959), Civil Engineering 29(3), 174; "
            "Roussel, M.C. et al. (2005), TxDOT Report 0-4696-2; Cleveland, T.G. "
            "et al. (2012), TxDOT Report 0-6544-1."
        ),
        function="hydrolog.operations:tc_kerby",
        options=(
            Option(
                name="length_km",
                type="number",
                description=(
                    "Długość spływu powierzchniowego [km]; > 0 (typowo ≤ 0,366)."
                ),
                description_en="Overland flow length [km]; > 0 (typically <= 0.366).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description=(
                    "Średni spadek terenu [m/m] (nie w procentach); > 0 (typowo "
                    "0,001–0,01)."
                ),
                description_en=(
                    "Mean ground slope [m/m] (not percent); > 0 (typically 0.001-0.01)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _RETARDANCE,
        ),
        examples=({"length_km": 0.10, "slope_m_per_m": 0.008, "retardance": 0.4},),
    ),
    Command(
        name="tc kerby-kirpich",
        operation_id="tc_kerby_kirpich",
        summary=(
            "Czas koncentracji złożoną metodą Kerby–Kirpich (spływ "
            "powierzchniowy + koryto)."
        ),
        summary_en=(
            "Time of concentration by the composite Kerby-Kirpich method "
            "(overland + channel)."
        ),
        description=(
            "Czas koncentracji tc złożoną metodą Kerby–Kirpich: droga spływu dzieli "
            "się na odcinek powierzchniowy (wzór Kerby'ego) i korytowy (wzór "
            "Kirpicha), a tc = t_powierzchniowy + t_korytowy [min]. Poprawka "
            "niskiego spadku (Cleveland i in., 2012; S < 0,002 → S + 0,0005) jest "
            "stosowana osobno do obu odcinków. Metoda zweryfikowana przez Roussel "
            "i in. (2005) na 92 zlewniach Teksasu o powierzchni 0,65–388 km². "
            "Ostrzeżenia, gdy odcinek powierzchniowy wykracza poza zakres wzoru "
            "Kerby'ego (L ≤ 0,366 km, S 0,001–0,01, N 0,02–0,80) lub korytowy poza "
            "zakres Kirpicha (L ≤ 80 km, S 0,002–0,15). Literatura: Kerby (1959); "
            "Kirpich (1940); Roussel, M.C. i in. (2005), TxDOT Report 0-4696-2; "
            "Cleveland, T.G. i in. (2012), TxDOT Report 0-6544-1."
        ),
        description_en=(
            "Time of concentration tc by the composite Kerby-Kirpich method: the "
            "flow path is split into an overland segment (Kerby formula) and a "
            "channel segment (Kirpich formula), and tc = t_overland + t_channel "
            "[min]. The low-slope adjustment (Cleveland et al., 2012; S < 0.002 -> "
            "S + 0.0005) is applied to both segments independently. The method was "
            "validated by Roussel et al. (2005) on 92 Texas watersheds of "
            "0.65-388 km2. Warnings are reported when the overland segment is "
            "outside the Kerby range (L <= 0.366 km, S 0.001-0.01, N 0.02-0.80) or "
            "the channel segment outside the Kirpich range (L <= 80 km, S "
            "0.002-0.15). References: Kerby (1959); Kirpich (1940); Roussel, M.C. "
            "et al. (2005), TxDOT Report 0-4696-2; Cleveland, T.G. et al. (2012), "
            "TxDOT Report 0-6544-1."
        ),
        function="hydrolog.operations:tc_kerby_kirpich",
        options=(
            Option(
                name="overland_length_km",
                type="number",
                description=(
                    "Długość spływu powierzchniowego od najdalszego punktu do "
                    "początku wyraźnego cieku [km]; > 0 (typowo ≤ 0,366)."
                ),
                description_en=(
                    "Overland flow length from the most distant point to the start "
                    "of a defined channel [km]; > 0 (typically <= 0.366)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="overland_slope_m_per_m",
                type="number",
                description=(
                    "Średni spadek spływu powierzchniowego [m/m]; > 0 (typowo "
                    "0,001–0,01)."
                ),
                description_en=(
                    "Mean overland slope [m/m]; > 0 (typically 0.001-0.01)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _RETARDANCE,
            Option(
                name="channel_length_km",
                type="number",
                description=(
                    "Długość cieku od początku wyraźnego koryta do przekroju "
                    "zamykającego [km]; > 0 (typowo ≤ 80)."
                ),
                description_en=(
                    "Channel length from the start of the defined channel to the "
                    "outlet [km]; > 0 (typically <= 80)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="channel_slope_m_per_m",
                type="number",
                description=("Średni spadek koryta [m/m]; > 0 (typowo 0,002–0,15)."),
                description_en="Mean channel slope [m/m]; > 0 (typically 0.002-0.15).",
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
        ),
        examples=(
            {
                "overland_length_km": 0.25,
                "overland_slope_m_per_m": 0.008,
                "retardance": 0.4,
                "channel_length_km": 5.0,
                "channel_slope_m_per_m": 0.005,
            },
        ),
    ),
    Command(
        name="tc watershed",
        operation_id="tc_watershed",
        summary=(
            "Czas koncentracji wybraną metodą z parametrów zlewni "
            "(WatershedParameters)."
        ),
        summary_en=(
            "Time of concentration by a chosen method from watershed parameters."
        ),
        description=(
            "Czas koncentracji tc wybraną metodą (kirpich, nrcs, giandotti, faa, "
            "kerby, kerby_kirpich) z parametrów zlewni w formacie "
            "WatershedParameters (plik JSON `watershed_file` z Hydrografa albo "
            "obiekt `watershed`). Długość: `channel_length_km`, a gdy jej brak — "
            "`length_km`; spadek: `channel_slope_m_per_m`, potem "
            "`mean_slope_m_per_m`, w ostateczności relief/(L·1000); metoda nrcs "
            "bierze spadek w odwrotnej kolejności, najpierw `mean_slope_m_per_m` "
            "(w TR-55 Y to średni spadek terenu zlewni, nie koryta). Metody faa i "
            "kerby to wzory na czas spływu powierzchniowego: zamiast długości i "
            "spadku koryta biorą `overland_length_km` i `overland_slope_m_per_m` "
            "(wynik to czas spływu powierzchniowego; dla zlewni z korytem użyj "
            "kerby_kirpich). Pola wymagane przez metodę: nrcs — `cn`; faa — "
            "`runoff_coeff`, `overland_length_km`, `overland_slope_m_per_m`; "
            "kerby — `retardance`, `overland_length_km`, "
            "`overland_slope_m_per_m`; kerby_kirpich — `retardance`, "
            "`overland_length_km`, `overland_slope_m_per_m`, `channel_length_km`, "
            "`channel_slope_m_per_m`; giandotti używa `elevation_mean_m` (gdy "
            "brak — średniej z min i max) minus `elevation_min_m`. Braki "
            "kończą się błędem walidacji z listą brakujących pól. Wynik: tc "
            "[min] i [h], nazwa metody i faktycznie użyte parametry wzoru (wzory "
            "i literatura: opisy komend `tc kirpich`, `tc nrcs`, `tc giandotti`, "
            "`tc faa`, `tc kerby`, `tc kerby-kirpich`)."
        ),
        description_en=(
            "Time of concentration tc by a chosen method (kirpich, nrcs, "
            "giandotti, faa, kerby, kerby_kirpich) from watershed parameters in "
            "the WatershedParameters format (a JSON `watershed_file` from "
            "Hydrograf or an inline `watershed` object). Length: "
            "`channel_length_km`, else `length_km`; slope: "
            "`channel_slope_m_per_m`, then `mean_slope_m_per_m`, finally "
            "relief/(L·1000); the nrcs method takes the slope in the opposite "
            "order, `mean_slope_m_per_m` first (Y of TR-55 is the average land "
            "slope of the watershed, not of the channel). The faa and kerby "
            "methods are overland flow formulas: instead of the channel length "
            "and slope they take `overland_length_km` and "
            "`overland_slope_m_per_m` (the result is the overland flow time; use "
            "kerby_kirpich for a watershed with a channel). Fields required by "
            "the method: nrcs - `cn`; faa - `runoff_coeff`, `overland_length_km`, "
            "`overland_slope_m_per_m`; kerby - `retardance`, "
            "`overland_length_km`, `overland_slope_m_per_m`; kerby_kirpich - "
            "`retardance`, `overland_length_km`, `overland_slope_m_per_m`, "
            "`channel_length_km`, `channel_slope_m_per_m`; giandotti uses "
            "`elevation_mean_m` (the midpoint of min and max when absent) minus "
            "`elevation_min_m`. Missing fields end in a validation error listing "
            "them. Result: tc [min] and [h], the method name and the formula "
            "parameters actually used (formulas and references: the descriptions "
            "of `tc kirpich`, `tc nrcs`, `tc giandotti`, `tc faa`, `tc kerby`, "
            "`tc kerby-kirpich`)."
        ),
        function="hydrolog.operations:tc_watershed",
        options=(
            Option(
                name="watershed",
                type="object",
                description=(
                    "Parametry zlewni jako obiekt WatershedParameters (m.in. "
                    "`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, "
                    "`elevation_max_m`, opcjonalnie `cn`, `mean_slope_m_per_m`, "
                    "`channel_length_km`, `channel_slope_m_per_m`, `runoff_coeff`, "
                    "`retardance`, `overland_length_km`, "
                    "`overland_slope_m_per_m`...)."
                ),
                description_en=(
                    "Watershed parameters as a WatershedParameters object "
                    "(`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, "
                    "`elevation_max_m`, optionally `cn`, `mean_slope_m_per_m`, "
                    "`channel_length_km`, `channel_slope_m_per_m`, `runoff_coeff`, "
                    "`retardance`, `overland_length_km`, "
                    "`overland_slope_m_per_m`...)."
                ),
            ),
            Option(
                name="watershed_file",
                type="path",
                description=(
                    "Plik JSON z parametrami zlewni (format "
                    "`WatershedParameters.to_json()`)."
                ),
                description_en=(
                    "JSON file with the watershed parameters (the "
                    "`WatershedParameters.to_json()` format)."
                ),
            ),
            Option(
                name="method",
                type="choice",
                description=(
                    "Metoda obliczenia tc; domyślnie kirpich. Pola zlewni "
                    "wymagane przez metodę są wymienione w opisie komendy."
                ),
                description_en=(
                    "Method of computing tc; default kirpich. The watershed "
                    "fields a method needs are listed in the command description."
                ),
                choices=_METHODS,
                default="kirpich",
            ),
        ),
        one_of=(("watershed",), ("watershed_file",)),
        examples=(
            {
                "watershed": {
                    "name": "Potok Młynówka",
                    "area_km2": 45.3,
                    "perimeter_km": 32.1,
                    "length_km": 12.5,
                    "elevation_min_m": 150.0,
                    "elevation_max_m": 520.0,
                    "mean_slope_m_per_m": 0.025,
                    "cn": 72,
                },
                "method": "nrcs",
            },
        ),
    ),
)
