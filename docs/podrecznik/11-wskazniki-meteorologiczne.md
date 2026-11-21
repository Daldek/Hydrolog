# 11. Wskaźniki meteorologiczne stacji

Hydrolog opisuje klimat zlewni wskaźnikami liczonymi z dobowych serii stacji meteorologicznej: opadu, temperatury
powietrza i pokrywy śnieżnej. Służą one do oceny, czy rok, sezon albo miesiąc był suchy czy wilgotny, ciepły czy
chłodny, do opisu susz i opadów ekstremalnych oraz jako tło analiz odpływu (rozdziały 8–10). Rozdział omawia polecenia
grupy `meteo`: `meteo precipitation` (sumy, normy, maksima, dni z opadem, natężenie, opady bardzo duże, sezonowość),
`meteo spells` (ciągi dni suchych i mokrych), `meteo spi` (standaryzowany wskaźnik opadu i opad względny),
`meteo temperature` (średnie, dni charakterystyczne, stopniodni, amplituda dobowa), `meteo snow` (pokrywa śnieżna) i
`meteo hydrothermal` (współczynnik hydrotermiczny Sielianinowa).

## Dane przykładów

- Dobowe temperatury (maksymalna, minimalna, średnia) i opady stacji synoptycznej IMGW-PIB Warszawa-Okęcie (352200375)
  z lat 1991–2020, bez braków danych: plik testowy Hydrologa `tests/fixtures/warszawa_okecie_1991_2020.csv.gz`
  (rozpakowanie: rozdział 9).
- Dobowa grubość pokrywy śnieżnej tej samej stacji z zim 1991–2020, wyeksportowana z Obserwatora do pliku
  `docs/podrecznik/dane/warszawa_okecie_snieg_1991_2020.csv` (opis i atrybucja: `docs/podrecznik/dane/README.md`).

Lata 1991–2020 to obecny okres normalny Światowej Organizacji Meteorologicznej (WMO), więc wyniki można porównać z
normami klimatycznymi IMGW-PIB dla stacji Warszawa.

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy. Dane
Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone. Regulamin danych
IMGW-PIB: https://danepubliczne.imgw.pl/regulations

## 11.1. Doba, rok i braki danych

**Doba pomiarowa.** Dobowa suma opadu w danych IMGW-PIB to opad doby opadowej, która zaczyna się rano danego dnia i
kończy rano dnia następnego (od 06.01 do 06.00 UTC); data w pliku to dzień jej rozpoczęcia. Temperatura maksymalna i
minimalna dotyczą doby termicznej kończącej się wieczorem danego dnia (od 18.01 UTC dnia poprzedniego do 18.00 UTC),
a grubość pokrywy śnieżnej mierzy się rano (IMGW-PIB, Rocznik Meteorologiczny). Hydrolog przyjmuje daty takie, jakie
ma plik, i niczego nie przesuwa. W rocznikach IMGW-PIB „0,0” oznacza ślad opadu (*trace*: opad, który wystąpił, ale był
za mały do zmierzenia), a „–” brak opadu; dzień ze śladem opadu nie jest dniem z opadem mierzalnym (WMO 2023, rozdz. 6).

**Rok.** Polecenia `meteo precipitation`, `meteo spells`, `meteo spi` i `meteo temperature` liczą lata kalendarzowe
albo – z opcją `--year-type hydrological` – lata hydrologiczne. `meteo snow` liczy zimy, a `meteo hydrothermal` lata
kalendarzowe:

<!-- spec:years_of_a_series -->

<a id="spec-years_of_a_series"></a>

> **Rok kalendarzowy, rok hydrologiczny i sezon śnieżny serii** · wzór grupy B `years_of_a_series` (Tier B, CMP-2.2)
>
> **Definicja:** rok kalendarzowy (styczeń–grudzień), polski rok hydrologiczny (listopad–październik) nazwany od roku, w którym się kończy, albo sezon śnieżny (sierpień–lipiec) nazwany od roku, w którym się kończy (źr. 1)
>
> **Konwencja:** rok nakłada się na siatkę dat w całości, a jego dni bez wartości są brakami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, chapter 2: normals of calendar months <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.year_of`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:years_of_a_series -->

**Braki danych.** Hydrolog stosuje zasady WMO-No. 1203 (WMO 2017, rozdz. 4.4.1). Średnia miesięczna i liczba dni ze
zjawiskiem znoszą kilka rozproszonych braków, ale nie dłuższą przerwę; liczbę dni ze zjawiskiem w miesiącu z brakami
przelicza się na pełny miesiąc. Suma miesięczna wymaga kompletu dni, chyba że brakujące dni obejmuje suma zbiorcza
(*accumulated total*: opad zmierzony po kilku dniach bez pomiaru i zapisany pod ostatnim dniem). Ekstremum miesiąca
liczy się z tylu dni, ile jest. Progi tych reguł podają ramki:

<!-- spec:wmo_monthly_mean -->

<a id="spec-wmo_monthly_mean"></a>

> **Średnia miesięczna według reguły WMO** · wzór grupy B `wmo_monthly_mean` (Tier B, CMP-2.2)
>
> **Definicja:** średnia wartości dobowych miesiąca, w którym brakuje mniej niż 11 dni i mniej niż 5 kolejnych, a co najmniej jedna wartość istnieje (źr. 1)
>
> **Konwencja:** dzień siatki dat bez rekordu z tą datą liczy się jako brakujący
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $11$ | `missing_days` | Liczba brakujących dni, od której nie liczy się średniej miesięcznej | 11 | d | (źr. 1) |
> | $5$ | `missing_run` | Liczba kolejnych brakujących dni, od której nie liczy się średniej miesięcznej | 5 | d | (źr. 1) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and footnote 4, p. 7: a mean is not calculated when 11 or more days are missing or 5 or more consecutive days <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.monthly_means`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:wmo_monthly_mean -->

<!-- spec:wmo_monthly_count -->

<a id="spec-wmo_monthly_count"></a>

> **Liczba dni ze zjawiskiem w miesiącu według WMO** · wzór grupy B `wmo_monthly_count` (Tier B, CMP-2.2)
>
> **Definicja:** liczba dni ze zjawiskiem w miesiącu, dla którego można było obliczyć średnią, przeliczona na liczbę dni miesiąca: liczba dni ze zjawiskiem podzielona przez liczbę dni z wartością i pomnożona przez liczbę dni miesiąca (źr. 1)
>
> **Konwencja:** przeliczenie dotyczy każdego takiego miesiąca (WMO-No. 1203 podaje ten stosunek dla norm); liczba nie jest wtedy liczbą całkowitą
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (d) and 4.4.1 (d), pp. 5-8 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.monthly_counts`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:wmo_monthly_count -->

<!-- spec:wmo_monthly_sum -->

<a id="spec-wmo_monthly_sum"></a>

> **Suma miesięczna z kompletu dni** · wzór grupy B `wmo_monthly_sum` (Tier B, CMP-2.2)
>
> **Definicja:** suma wartości dobowych miesiąca z kompletem dni (źr. 1)
>
> **Konwencja:** miesiąc z brakującym dniem nie ma sumy
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (c) and 4.4.1 (c), pp. 5-8 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.monthly_totals`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:wmo_monthly_sum -->

<!-- spec:accumulated_totals -->

<a id="spec-accumulated_totals"></a>

> **Opady zbiorcze w sumach miesięcznych** · wzór grupy B `accumulated_totals` (Tier B, CMP-2.2)
>
> **Definicja:** suma oznaczona jako opad zbiorczy zastępuje brakujące dni bezpośrednio ją poprzedzające, gdy wraz z jej własnym dniem jest ich mniej niż 5; suma miesięczna uwzględnia takie opady zbiorcze, gdy obejmują mniej niż 11 dni miesiąca (źr. 1)
>
> **Konwencja:** blok obejmujący początek miesiąca ocenia się według całej jego długości; opad zbiorczy wlicza się do miesiąca swojego dnia
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (c), pp. 7-8: accumulated observations that cover the full period of missing data, not 11 or more days nor 5 or more in a row <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.monthly_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:accumulated_totals -->

<!-- spec:block_extreme -->

<a id="spec-block_extreme"></a>

> **Ekstremum miesięczne i data jego wystąpienia** · wzór grupy B `block_extreme` (Tier B, CMP-2.2)
>
> **Definicja:** ekstremum miesiąca z dni, które mają wartość, wraz z pierwszą datą jego wystąpienia (źr. 1)
>
> **Konwencja:** funkcja dla serii wyznacza ekstremum roczne statystyki wymagającej kompletu dni tylko z pełnych lat
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b), p. 7: extremes regardless of missing data <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.block_extreme`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:block_extreme -->

Wartość roczna wymaga wszystkich dwunastu miesięcy, a maksima roczne, sumy opadów bardzo dużych, ciągi dni i sezon
hydrotermiczny – wszystkich dni roku. Programy wskaźników ETCCDI (np. climdex.pcic) przyjmują inne tolerancje braków,
więc przy danych z lukami ich wyniki mogą się różnić od wyników Hydrologa. Sumy opadu Hydrolog zaokrągla, żeby sumy
równe w zapisie dziesiętnym były równymi liczbami (ważne dla wartości równych w teście Manna–Kendalla, rozdział 10):

<!-- spec:rounded_sums -->

<a id="spec-rounded_sums"></a>

> **Zaokrąglanie sum opadu dobowego** · wzór grupy B `rounded_sums` (Tier B, CMP-2.2)
>
> **Definicja:** każda suma opadu dobowego zaokrąglona do 1e-6 mm (źr. 1)
>
> **Konwencja:** dane z dokładnością 0,1 mm sumowane w arytmetyce binarnej zależą od kolejności dodawania; po zaokrągleniu sumy równe w zapisie dziesiętnym są równymi liczbami (wartości wiązane w teście Manna–Kendalla, pierwsze z równych okien); najwyżej 5e-7 mm na sumę
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a station, the group meteo, the sums of daily precipitation <https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/0032-meteorological-statistics-of-a-station-the-group-meteo.md>
>
> Funkcja `hydrolog.statistics._climate.round_sums`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:rounded_sums -->

**Typowy błąd.** Liczenie sumy miesięcznej z miesiąca, w którym brakuje kilku dni, „bo to tylko dwa dni”: jedna burza
może zmienić sumę miesiąca o połowę.

## 11.2. Normy klimatyczne

**Idea.** Norma klimatyczna (*climate normal*) to średnia z wielolecia, z którą porównuje się pojedyncze lata i
miesiące. Standardowa norma WMO obejmuje ostatnie pełne trzydziestolecie kończące się rokiem z zerem na końcu (obecnie
1991–2020), a okres 1961–1990 pozostaje stałym punktem odniesienia do badania zmian klimatu (WMO 2017, rozdz. 2 i 5.1).
Normę miesiąca liczy się tylko wtedy, gdy wystarczająco wiele lat okresu ma wartość tego miesiąca:

<!-- spec:wmo_normal -->

<a id="spec-wmo_normal"></a>

> **Norma miesięczna według WMO** · wzór grupy B `wmo_normal` (Tier B, CMP-2.2)
>
> **Definicja:** norma miesiąca kalendarzowego: średnia jego wartości z lat okresu odniesienia, w których wartość istnieje, o ile stanowią one co najmniej 80 % lat okresu (źr. 1)
>
> **Konwencja:** liczy się każdy rok okresu odniesienia, także lata bez danych; bez kryterium kolejnych lat
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $80 %$ | `normal_share` | Najmniejszy udział lat okresu odniesienia z wartością | 4/5 | – | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9 <https://library.wmo.int/idurl/4/55797>
> 2. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: 24 or more of 30 years <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.normal`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:wmo_normal -->

Normę roczną, półroczną i sezonową WMO każe liczyć z norm miesięcznych – jako sumę norm miesięcznych dla sum i liczb
dni, jako ich średnią dla średnich – a nie z wartości rocznych (WMO 2017, rozdz. 4.3.3). Przy kompletnych danych oba
sposoby dają to samo, ale gdy w różnych latach brakuje pojedynczych miesięcy, tylko reguła WMO daje normę roczną.
Hydrolog stosuje ją od wersji 0.9.0 (ADR-0044).

<!-- spec:multimonth_normal -->

<a id="spec-multimonth_normal"></a>

> **Norma roczna, półroczna i sezonowa z norm miesięcznych** · wzór grupy B `multimonth_normal` (Tier B, CMP-2.2)
>
> **Definicja:** norma roku, półrocza lub pory roku: suma norm miesięcy, które obejmuje, dla sumy lub liczby dni, a ich średnia dla średniej (źr. 1)
>
> **Konwencja:** z norm miesięcznych, nie z wartości rocznych (WMO-No. 1203, 4.3.3: wyniki identyczne, gdy nie brakuje miesięcy)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.3, p. 6 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics._climate.multimonth_normal`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:multimonth_normal -->

Okres normy wybierają opcje `--reference-first-year` i `--reference-last-year`; domyślnie jest nim analizowany okres.
Lata analizy zachowują własne wartości, a z okresu normy pochodzą tylko punkty odniesienia: normy, opad względny,
anomalie i klasy (ADR-0033).

<!-- spec:precipitation_normals -->

<a id="spec-precipitation_normals"></a>

> **Normy opadu miesięczne, półroczne, sezonowe i roczne** · wzór grupy B `precipitation_normals` (Tier B, CMP-2.2)
>
> **Definicja:** norma miesiąca kalendarzowego: średnia jego sum z lat okresu odniesienia, w których suma istnieje, o ile stanowią one co najmniej 80 % lat okresu; norma półrocza, pory roku lub roku: suma norm miesięcy, które obejmuje (źr. 1)
>
> **Konwencja:** okresem odniesienia są domyślnie lata analizy; jego lata bez danych liczą się do jego lat
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $80 %$ | `normal_share` | Najmniejszy udział lat okresu odniesienia z wartością | 4/5 | – | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: values in at least 80 % of the years; section 4.3.3, p. 6: the normal of several months from the monthly normals <https://library.wmo.int/idurl/4/55797>
> 2. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_sums`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_normals -->

<!-- spec:temperature_normals_and_anomalies -->

<a id="spec-temperature_normals_and_anomalies"></a>

> **Normy i anomalie temperatury powietrza** · wzór grupy B `temperature_normals_and_anomalies` (Tier B, CMP-2.2)
>
> **Definicja:** norma Tmean miesiąca kalendarzowego: średnia z jego średnich miesięcznych w tych latach okresu odniesienia, w których one istnieją, o ile stanowią co najmniej 80 % jego lat; norma roczna – średnia z dwunastu norm miesięcznych; anomalia – średnia pomniejszona o swoją normę (źr. 1)
>
> **Konwencja:** okresem odniesienia są domyślnie analizowane lata; jego lata bez danych wliczają się do jego lat
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9; section 4.3.3 (a), p. 6 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_temperature.temperature_means`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:temperature_normals_and_anomalies -->

**Typowe błędy.** Porównywanie z normą innego okresu bez podania okresu (1991–2020 czy 1961–1990). Liczenie normy
rocznej z lat, które mają komplet miesięcy, gdy WMO każe sumować normy miesięczne.

### Przykład: normy opadu i temperatury w Warszawie, 1991–2020

```bash
hydrolog meteo precipitation --index sums --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
hydrolog meteo temperature --index means --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Normy miesięczne opadu (pole `period.months[].normal_mm`) [mm]:

| I | II | III | IV | V | VI | VII | VIII | IX | X | XI | XII | rok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31,04 | 29,78 | 28,98 | 35,14 | 55,45 | 63,85 | 82,19 | 60,60 | 50,36 | 40,21 | 36,01 | 36,13 | 549,73 |

Zaokrąglone do 0,1 mm są to dokładnie normy IMGW-PIB 1991–2020 dla stacji Warszawa (norma roczna 549,7 mm; IMGW-PIB,
Normy klimatyczne 1991–2020). Norma średniej temperatury rocznej (`period.normal_c`) wynosi 8,97 °C, a IMGW-PIB podaje
9,0 °C. Normy zgadzają się, bo dane są kompletne i pochodzą z tej samej stacji.

## 11.3. Sumy opadu, opad względny i jego klasy

**Idea.** Sumę opadu miesiąca, półrocza, pory roku albo roku porównuje się z normą tego samego okresu i wyraża w
procentach normy (opad względny, wskaźnik względnego opadu, *relative precipitation index*, RPI; Gąsiorek i Musiał
2011). Procent normy dzieli się na klasy od skrajnie suchego do skrajnie wilgotnego.

<!-- spec:precipitation_sums -->

<a id="spec-precipitation_sums"></a>

> **Sumy opadu miesięczne, półroczne, sezonowe i roczne** · wzór grupy B `precipitation_sums` (Tier B, CMP-2.2)
>
> **Definicja:** suma opadu dobowego miesiąca, wymagająca kompletu dni albo opadów zbiorczych obejmujących brakujące dni; suma półrocza (XI–IV, V–X), pory roku (DJF z poprzedzającym grudniem, MAM, JJA, SON) i roku jako suma sum miesięcznych wchodzących w ich skład, wymagająca każdej z nich; suma w % swojej normy, 100 P / N (źr. 1)
>
> **Konwencja:** każda suma opadu dobowego zaokrąglona do 1e-6 mm (`round_sums`); brak odsetka, gdy brak normy lub norma wynosi 0
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.1 (c) and 4.4.1 (c), pp. 5-8: a sum needs complete data or accumulated observations covering the missing days <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_sums`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_sums -->

<!-- spec:relative_precipitation -->

<a id="spec-relative_precipitation"></a>

> **Opad względny w procentach normy** · wzór grupy B `relative_precipitation` (Tier B, CMP-2.2)
>
> **Definicja:** 100 P / N: suma miesięczna w % normy swojego miesiąca kalendarzowego, suma roczna w % sumy dwunastu norm miesięcznych (klasyfikowane przez `month_precipitation_class` i `kaczorowska_class`) (źr. 1)
>
> **Konwencja:** normy z okresu odniesienia; brak odsetka, gdy brak normy lub norma wynosi 0
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), eq. 1, p. 109: RPI = P / P-bar 100 % <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
>
> Funkcja `hydrolog.statistics.meteo_spi.standardized_precipitation_index`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:relative_precipitation -->

**Klasy roczne Kaczorowskiej.** Kaczorowska (1962, s. 72) zdefiniowała siedem klas dla lat i pór roku, nie dla
miesięcy. Granice klas to pełne procenty, a źródło nie mówi, jak zaokrąglać. Hydrolog zaokrągla procent normy do
pełnego procentu, połówkę w górę (ADR-0059), tak jak roczniki IMGW-PIB drukują pełne procenty. Łabędzki i Bąk (2004)
czytają te same klasy z granicami dziesiętnymi, więc rok bliski granicy klasy bywa u nich w innej klasie; przy
granicy podawaj zawsze procent z jednym miejscem po przecinku.

<!-- spec:kaczorowska_class -->

<a id="spec-kaczorowska_class"></a>

> **Klasa opadu rocznego według Kaczorowskiej (opad w % normy)** · specyfikacja [`kaczorowska_class`](../FORMULAS.md#kaczorowska_class) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> r = \left\lfloor \frac{100\,P}{N} + \frac{1}{2} \right\rfloor:\ r < 50,\ 50 \le r \le 74,\ 75 \le r \le 89,\ 90 \le r \le 110,\ 111 \le r \le 125,\ 126 \le r \le 150,\ r > 150
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P/N$ | `percent_of_normal` | Opad w % normy | % | [0; ∞) | nie podano w źródłach | [71; 145,2] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `precipitation_class` (wybór) | Klasa, od najsuchszej | – | jedna z: `extremely_dry`, `very_dry`, `dry`, `normal`, `wet`, `very_wet`, `extremely_wet` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $50$ | `very_dry_from` | Najmniejszy pełny procent klasy bardzo suchej (`very_dry`) | 50 | % | (źr. 4) |
> | $75$ | `dry_from` | Najmniejszy pełny procent klasy suchej (`dry`) | 75 | % | (źr. 5) |
> | $90$ | `normal_from` | Najmniejszy pełny procent klasy normalnej (`normal`) | 90 | % | (źr. 6) |
> | $111$ | `wet_from` | Najmniejszy pełny procent klasy wilgotnej (`wet`) | 111 | % | (źr. 7) |
> | $126$ | `very_wet_from` | Najmniejszy pełny procent klasy bardzo wilgotnej (`very_wet`) | 126 | % | (źr. 8) |
> | $151$ | `extremely_wet_from` | Najmniejszy pełny procent klasy skrajnie wilgotnej (`extremely_wet`) | 151 | % | (źr. 9) |
> | $1/2$ | `rounding_half` | Połowa procenta w regule zaokrąglania odsetka | 0,5 | % | (źr. 10) |
>
> **Konwencje**
>
> - odsetek należy do klasy swojego zaokrąglenia do liczby całkowitej, z połową zaokrąglaną w górę: 74,5 % to rok suchy, 110,5 % – wilgotny, 150,5 % – skrajnie wilgotny (zaokrąglanie połowy do liczby parzystej w Pythonie, stosowane do wersji 0.8.1, dawało w tych przypadkach rok bardzo suchy, normalny i bardzo wilgotny)
> - Łabędzki i Bąk (2004, Acta Agrophysica 3(1), tab. 2) podają klasy z granicami dziesiętnymi (75,0–89,9 – rok suchy): 89,6 % daje tu rok normalny, a tam suchy
> - norma z okresu odniesienia, domyślnie z analizowanych lat
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the classes of a year (or a season) in % of the normal <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 2. IMGW-PIB (2023). Rocznik Meteorologiczny 2022, Tab. 5, p. 14 (the same classes, „normalny” for „przeciętny”) and Tab. 9, p. 22 (annual sums in % of the normal 1991-2020, whole percents) <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/Rocznik%20meteorologiczny/Rocznik%20Meteorologiczny%202022.pdf>
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the annual sums of 1991-2020 in % of their normal: 71.0 to 145.2 %
> 4. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class very_dry <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 5. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class dry <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 6. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class normal <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 7. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class wet <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 8. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class very_wet <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 9. Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class extremely_wet <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
> 10. Hydrolog ADR-0059 (2026-11-19): the meteorological indices declared by specs, the classes are ranges of whole percents: a percentage counts in the class of its rounding, a half up <https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/0059-the-meteorological-indices-by-specs.md>
>
> Funkcja `hydrolog.statistics.meteo_spi.year_precipitation_class`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:kaczorowska_class -->

**Klasy miesięczne.** Sumy miesięczne są dużo bardziej zmienne niż roczne, dlatego klasa „normalny” jest dla nich
szersza. Hydrolog stosuje klasy z tab. 1 Gąsiorek i Musiał (2011), za Tomaszewską (1994):

<!-- spec:month_precipitation_class -->

<a id="spec-month_precipitation_class"></a>

> **Klasa opadu miesięcznego (opad w % normy)** · specyfikacja [`month_precipitation_class`](../FORMULAS.md#month_precipitation_class) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \frac{100\,P}{N} < 25,\ [25, 50),\ [50, 75),\ [75, 125],\ (125, 150],\ (150, 200],\ > 200
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P/N$ | `percent_of_normal` | Opad w % normy | % | [0; ∞) | nie podano w źródłach | [1,1; 358,9] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `precipitation_class` (wybór) | Klasa, od najsuchszej | – | jedna z: `extremely_dry`, `very_dry`, `dry`, `normal`, `wet`, `very_wet`, `extremely_wet` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $25$ | `extremely_dry_below` | Otwarta górna granica klasy skrajnie suchej (`extremely_dry`) | 25 | % | (źr. 3) |
> | $50$ | `very_dry_below` | Otwarta górna granica klasy bardzo suchej (`very_dry`) | 50 | % | (źr. 4) |
> | $75$ | `dry_below` | Otwarta górna granica klasy suchej (`dry`) | 75 | % | (źr. 5) |
> | $125$ | `normal_to` | Górna granica klasy normalnej (`normal`) | 125 | % | (źr. 6) |
> | $150$ | `wet_to` | Górna granica klasy wilgotnej (`wet`) | 150 | % | (źr. 7) |
> | $200$ | `very_wet_to` | Górna granica klasy bardzo wilgotnej (`very_wet`) | 200 | % | (źr. 8) |
>
> **Konwencje**
>
> - domknięcia przedziałów jak w tab. 1 źródła: trzy niższe klasy domknięte od dołu, wyższe domknięte od góry
> - Kaczorowska (1962) klasyfikuje tylko lata i pory roku; monitoring IMGW-PIB opisuje tę tabelę miesięczną jej nazwiskiem, czego nie robi podpis źródła u Gąsiorek i Musiał (2011)
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the classes of the relative precipitation index of a month (source line: Tomaszewska 1994); eq. 1, p. 109 (RPI = 100 P / N) <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 2. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020 in % of their normals: 1.1 to 358.9 %
> 3. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class extremely_dry <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 4. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class very_dry <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 5. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class dry <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 6. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class normal <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 7. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class wet <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
> 8. Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class very_wet <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>
>
> Funkcja `hydrolog.statistics.meteo_spi.month_precipitation_class`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:month_precipitation_class -->

**Typowe błędy.** Stosowanie klas rocznych Kaczorowskiej do miesięcy. Porównywanie z normą innego okresu. Mieszanie
lat kalendarzowych i hydrologicznych.

### Przykład: lata suche i wilgotne w Warszawie

Procent normy i klasy podaje polecenie `meteo spi` (pola `years[]` i `months[]`; same sumy podaje także
`meteo precipitation --index sums`):

```bash
hydrolog meteo spi --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

| Rok | Suma [mm] | % normy | Klasa Kaczorowskiej |
|---|---|---|---|
| 2010 | 798,1 | 145,2 | bardzo wilgotny |
| 2011 | 604,4 | 109,9 | normalny (przeciętny) |
| 2015 | 403,5 | 73,4 | bardzo suchy |
| 2017 | 705,1 | 128,3 | bardzo wilgotny |
| 2018 | 433,4 | 78,8 | suchy |
| 2019 | 390,2 | 71,0 | bardzo suchy |

Miesiące skrajne: sierpień 2015 r. – 8,4 mm, czyli 13,9% normy (skrajnie suchy); maj 2010 r. – 116,4 mm, 209,9% normy
(skrajnie wilgotny); listopad 2011 r. – 0,4 mm, 1,1% normy (skrajnie suchy). Rok 2011 był przeciętny, choć jego
listopad – skrajnie suchy: klasa roku nie mówi nic o rozkładzie opadu w roku.

## 11.4. Największe opady dobowe i wielodniowe

**Idea.** Największa dobowa suma opadu w roku (Rx1day) i największa suma z kilku kolejnych dni (Rx5day dla pięciu dni)
to wskaźniki ETCCDI opisujące opady ekstremalne (ETCCDI 2009). Ich maksima roczne są wejściem analizy częstości
(rozdział 7). Hydrolog liczy też sumy innych liczb dni (opcja `--durations-days`).

<!-- spec:precipitation_maxima -->

<a id="spec-precipitation_maxima"></a>

> **Największe sumy opadu dobowe i wielodniowe** · wzór grupy B `precipitation_maxima` (Tier B, CMP-2.2)
>
> **Definicja:** Rx1day i największe sumy n-dniowe (Rx5day dla 5): suma n-dniowa danego dnia to suma n dni kończących się tym dniem, przypisana do roku jej ostatniego dnia i brakująca, jeśli nie są znane wszystkie n dni; maksimum miesiąca liczy się z dni, które ma, a maksimum roku wymaga kompletu dni roku (źr. 1)
>
> **Konwencja:** pierwsze z równych maksimów, wraz z jego datami; climdex.pcic 1.1-11 przypisuje okno 5-dniowe do jego środkowego dnia, a brakujący dzień przyjmuje jako 0
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, Rx1day, the largest daily precipitation of a period; Rx5day, the largest precipitation of 5 consecutive days (the interval ending on a day) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_maxima`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_maxima -->

**Konwencje.** Suma wielodniowa należy do roku swojego ostatniego dnia i wymaga kompletu dni; maksimum roczne wymaga
kompletu dni roku. Inne programy (np. climdex.pcic) dopuszczają braki, przypisują okno środkowemu dniu albo zastępują
brakujące dni zerem, więc ich maksima mogą się różnić.

**Typowe błędy.** Porównywanie dobowej sumy ze stacji (stała doba opadowa) z opadem o czasie trwania 24 godzin z PMAXTP
(okno ruchome; rozdział 2): stała doba dzieli ulewę między dwa dni i daje mniejsze wartości.

### Przykład: maksima opadu w Warszawie

```bash
hydrolog meteo precipitation --index maxima --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

| Wielkość (pole `period.durations[]`) | 1 dzień (Rx1day) | 2 dni | 5 dni (Rx5day) |
|---|---|---|---|
| Średnie maksimum roczne [mm] | 37,35 | 46,99 | 62,75 |
| Mediana maksimów rocznych [mm] | 36,0 | 43,6 | 60,3 |
| Największe w latach 1991–2020 [mm] | 75,8 | 102,4 | 118,8 |
| Kiedy | 31.07.2011 | 5–6.08.2002 | 2–6.08.2002 |

Opad z 5 i 6 sierpnia 2002 r. (102,4 mm w dwa dni) to więcej niż norma lipca, najbardziej deszczowego miesiąca.

## 11.5. Dni z opadem i natężenie opadu

**Idea.** Liczba dni z opadem co najmniej danej wysokości opisuje częstość opadów (wskaźniki ETCCDI R10mm i R20mm dla
dni z opadem dużym i bardzo dużym). Dzień mokry (*wet day*) to w ETCCDI dzień z opadem co najmniej progu dnia mokrego,
PRCPTOT – suma opadu dni mokrych, a wskaźnik intensywności opadu SDII (*simple daily intensity index*) – średni opad
dnia mokrego (ETCCDI 2009).

<!-- spec:precipitation_days -->

<a id="spec-precipitation_days"></a>

> **Liczba dni z opadem nie mniejszym od progu** · wzór grupy B `precipitation_days` (Tier B, CMP-2.2)
>
> **Definicja:** dni z P równym progowi lub większym, dla każdego progu (R10mm i R20mm dla 10 i 20 mm); liczba w miesiącu przeliczona na wszystkie jego dni, gdy brakuje mniej niż 11 dni i mniej niż 5 kolejnych; liczba w roku jako suma jego dwunastu miesięcy (źr. 1)
>
> **Konwencja:** P >= próg; przy lukach liczba w miesiącu nie jest liczbą całkowitą (climdex.pcic liczy dni, które ma)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, R10mm and R20mm: the annual count of days with RR >= 10 mm and >= 20 mm <https://etccdi.pacificclimate.org/list_27_indices.shtml>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_days -->

<!-- spec:sdii -->

<a id="spec-sdii"></a>

> **Wskaźnik intensywności opadu SDII: średni opad dnia z opadem** · specyfikacja [`sdii`](../FORMULAS.md#sdii) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> W = \#\{i : P_i \ge P_w\},\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,\quad \mathrm{SDII} = \frac{\mathrm{PRCPTOT}}{W}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_i$ | `precipitation_mm` (ciąg) | Opad dobowy dni okresu; NaN w dniu z brakiem danych, który jest pomijany | mm | [0; ∞) | nie podano w źródłach | [0; 75,8] (źr. 2) |
> | $P_w$ | `wet_day_mm` | Najmniejszy opad dnia z opadem | mm | (0; ∞) | nie podano w źródłach | [1; 1] (źr. 1) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{SDII}$ | `sdii_mm` | Średni opad dnia z opadem | mm | (0; ∞) |
> | $W$ | `wet_days` (liczba całkowita) | Liczba dni z opadem | d | [1; ∞) |
> | $\mathrm{PRCPTOT}$ | `wet_day_total_mm` | Suma opadu dni z opadem | mm | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | co najmniej jeden dzień ma P >= P_w | `a_wet_day` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - dzień z opadem ma P >= Pw (RR >= 1 mm według ETCCDI); dzień z brakiem danych (NaN) jest pomijany
> - funkcja dla serii bierze dni pełnego miesiąca lub roku albo łącznie pełne miesiące danego miesiąca kalendarzowego i zaokrągla PRCPTOT do 1e-6 mm; okres bez dnia z opadem nie ma SDII (climdex.pcic podaje 0)
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik opadu dobowego
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 <https://etccdi.pacificclimate.org/list_27_indices.shtml>
> 2. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm
>
> Funkcja `hydrolog.statistics.meteo_precipitation.wet_day_intensity`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:sdii -->

<!-- spec:precipitation_intensity -->

<a id="spec-precipitation_intensity"></a>

> **Intensywność opadu dni z opadem (SDII) miesięcy i lat** · wzór grupy B `precipitation_intensity` (Tier B, CMP-2.2)
>
> **Definicja:** `sdii` każdego miesiąca i roku z kompletem dni oraz każdego miesiąca kalendarzowego z tych miesięcy okresu łącznie; średnia suma roczna i średni SDII lat, które go mają (źr. 1)
>
> **Konwencja:** opad zbiorczy jest dla `sdii` dniem z brakiem danych i wlicza się do sumy rocznej; PRCPTOT zaokrąglony do 1e-6 mm; miesiąc lub rok bez dnia z opadem ma W = 0 i nie ma SDII
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 <https://etccdi.pacificclimate.org/list_27_indices.shtml>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_intensity`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_intensity -->

### Przykład: dni z opadem i natężenie opadu w Warszawie

```bash
hydrolog meteo precipitation --index days --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
hydrolog meteo precipitation --index intensity --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Średnia liczba dni w roku, 1991–2020 (pole `period.days` dla progów `thresholds_mm` = 0,1, 1, 10 i 20 mm):

| P ≥ 0,1 mm | P ≥ 1 mm | P ≥ 10 mm (R10mm) | P ≥ 20 mm (R20mm) |
|---|---|---|---|
| 155,1 | 98,6 | 12,9 | 3,2 |

Średni SDII lat 1991–2020 (`period.mean_sdii_mm`) wynosi 5,35 mm na dzień mokry. W styczniu dzień mokry przynosi
średnio 3,35 mm, w lipcu 8,57 mm (`period.months[].sdii_mm`). Dni z jakimkolwiek opadem jest w lipcu mniej niż w
styczniu (średnio 12,5 i 16,2, `period.months[].days`), ale letni dzień mokry przynosi znacznie więcej wody.

## 11.6. Opady bardzo duże: percentyle dni mokrych

**Idea.** Próg „opadu bardzo dużego” nie jest stałą liczbą milimetrów, tylko percentylem opadu dni mokrych w okresie
bazowym danej stacji, dzięki czemu wskaźnik jest porównywalny między klimatami (ETCCDI 2009). R95p to suma opadu dni
powyżej 95. percentyla, a R95pTOT – jej udział w PRCPTOT; R99p i R99pTOT analogicznie dla 99. percentyla.

<!-- spec:wet_day_percentile -->

<a id="spec-wet_day_percentile"></a>

> **Percentyl opadu dni z opadem (kwantyl typu 8)** · specyfikacja [`wet_day_percentile`](../FORMULAS.md#wet_day_percentile) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> h = \left(n + \tfrac{1}{3}\right)\frac{p}{100} + \tfrac{1}{3},\quad Q = x_{(k)} + (h - k)\left(x_{(k+1)} - x_{(k)}\right),\quad k = \lfloor h \rfloor
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_i$ | `precipitation_mm` (ciąg) | Opad dobowy dni okresu; NaN w dniu z brakiem danych, który jest pomijany | mm | [0; ∞) | nie podano w źródłach | [0; 75,8] (źr. 5) |
> | $P_w$ | `wet_day_mm` | Najmniejszy opad dnia z opadem | mm | (0; ∞) | nie podano w źródłach | [1; 1] (źr. 4) |
> | $p$ | `percentile` | Percentyl | % | (0; 100) | nie podano w źródłach | [95; 99] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q$ | `percentile_mm` | Percentyl opadu dni z opadem | mm | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | co najmniej jeden dzień ma P >= P_w | `a_wet_day` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - kwantyl typu 8 według Hyndmana i Fana (1996), nieobciążony względem mediany, jak w climdex.pcic 1.1-11 (kwantyl typu 8) i w metodzie `median_unbiased` biblioteki NumPy
> - dni z opadem (P >= Pw) podanego okresu; dzień z brakiem danych (NaN) jest pomijany
> - funkcja dla serii podaje dni z opadem okresu odniesienia i wymaga co najmniej 100 takich dni (`too_few_wet_days`, minimum przyjęte w Hydrologu, ADR-0032)
>
> **Zgodność z obserwacjami według źródeł:** brak: kwantyl z próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hyndman, R. J. and Fan, Y. (1996). Sample quantiles in statistical packages. The American Statistician 50(4), 361-365, definition 8: Q(p) = x(k) + (h - k) (x(k + 1) - x(k)), h = (n + 1/3) p + 1/3 and k its whole part, x(k) the k-th smallest of n values — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. NumPy 2 documentation, numpy.percentile, method 'median_unbiased': definition 8 of Hyndman and Fan (1996), virtual index n p + 1/3 + p / 3 - 1 counted from 0 <https://numpy.org/doc/stable/reference/generated/numpy.percentile.html>
> 3. Bronaugh, D. (2020). climdex.pcic 1.1-11: PCIC implementation of Climdex routines, R package, R/climdex.r: the percentiles of the wet days (not NA, at least 1 mm) of the base period by quantile type 8 <https://cran.r-project.org/src/contrib/Archive/climdex.pcic/>
> 4. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 <https://etccdi.pacificclimate.org/list_27_indices.shtml>
> 5. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm
>
> Funkcja `hydrolog.statistics.meteo_precipitation.wet_day_percentile`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:wet_day_percentile -->

<!-- spec:heavy_precipitation_share -->

<a id="spec-heavy_precipitation_share"></a>

> **Opad dni powyżej progu i jego udział w opadzie dni z opadem** · specyfikacja [`heavy_precipitation_share`](../FORMULAS.md#heavy_precipitation_share) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> R = \sum_{P_i > P_t} P_i,\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,\quad s = \frac{100\,R}{\mathrm{PRCPTOT}},\quad P_t \ge P_w
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_i$ | `precipitation_mm` (ciąg) | Opad dobowy dni okresu; NaN w dniu z brakiem danych, który jest pomijany | mm | [0; ∞) | nie podano w źródłach | [0; 75,8] (źr. 3) |
> | $P_w$ | `wet_day_mm` | Najmniejszy opad dnia z opadem | mm | (0; ∞) | nie podano w źródłach | [1; 1] (źr. 1) |
> | $P_t$ | `threshold_mm` | Próg: percentyl opadu dni z opadem okresu odniesienia | mm | (0; ∞) | nie podano w źródłach | [16,8; 29,43] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $R$ | `heavy_mm` | Opad dni powyżej progu (R95p) | mm | [0; ∞) |
> | $D$ | `heavy_days` (liczba całkowita) | Liczba dni powyżej progu | d | [0; ∞) |
> | $\mathrm{PRCPTOT}$ | `wet_day_total_mm` | Suma opadu dni z opadem | mm | (0; ∞) |
> | $s$ | `share_percent` | R w % PRCPTOT (R95pTOT według ClimPACT) | % | [0; 100] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | co najmniej jeden dzień ma P >= P_w | `a_wet_day` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | Pt >= Pw: dzień powyżej progu jest dniem z opadem | `threshold_of_a_wet_day` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - dzień liczy się jako dzień powyżej progu, gdy P > Pt (ostra nierówność), a jako dzień z opadem, gdy P >= Pw; dzień z brakiem danych (NaN) jest pomijany
> - R to R95p według ClimPACT i listy ETCCDI (suma w mm), a udział to R95pTOT według ClimPACT (100 R / PRCPTOT); R95pTOT według ECA&D dzieli przez opad wszystkich dni
> - funkcja dla serii bierze dni pełnego roku i próg z `wet_day_percentile` oraz zaokrągla R i PRCPTOT do 1e-6 mm; rok bez dnia z opadem nie ma udziału
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik opadu dobowego
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 <https://etccdi.pacificclimate.org/list_27_indices.shtml>
> 2. ClimPACT2, the indices of the Expert Team on Sector-specific Climate Indices (ET-SCI), climate.indices.csv: R95p, the annual sum of the precipitation of the days above the 95th percentile of the wet days; R95pTOT = 100 R95p / PRCPTOT <https://github.com/ARCCSS-extremes/climpact>
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm
> 4. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the 95th and 99th percentiles of the wet days of 1991-2020: 16.8 and 29.43 mm
>
> Funkcja `hydrolog.statistics.meteo_precipitation.heavy_precipitation_share`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:heavy_precipitation_share -->

<!-- spec:heavy_precipitation_thresholds -->

<a id="spec-heavy_precipitation_thresholds"></a>

> **Progi opadu bardzo dużego i udział opadu powyżej progu** · wzór grupy B `heavy_precipitation_thresholds` (Tier B, CMP-2.2)
>
> **Definicja:** progi: `wet_day_percentile` dni z opadem okresu odniesienia dla każdego percentyla, z co najmniej 100 dni z opadem; dla każdego roku z kompletem dni: `heavy_precipitation_share` dla każdego progu oraz średni udział z tych lat (źr. 1)
>
> **Konwencja:** okresem odniesienia są domyślnie lata analizy (okres bazowy ETCCDI to 1961-1990); minimum 100 dni z opadem przyjął Hydrolog (ADR-0032), żadne źródło go nie podaje
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bronaugh, D. (2020). climdex.pcic 1.1-11: PCIC implementation of Climdex routines, R package, R/climdex.r: the percentiles of the wet days (not NA, at least 1 mm) of the base period by quantile type 8 <https://cran.r-project.org/src/contrib/Archive/climdex.pcic/>
>
> Funkcja `hydrolog.statistics.meteo_precipitation.heavy_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:heavy_precipitation_thresholds -->

**Uwaga na nazwy.** Na liście 27 wskaźników ETCCDI „R95pTOT” oznacza sumę w milimetrach; w ClimPACT R95p to suma, a
R95pTOT udział w PRCPTOT; w ECA&D R95pTOT dzieli się przez opad wszystkich dni, a nie tylko mokrych. Hydrolog podaje
sumę, udział w PRCPTOT i liczbę dni. Percentyl liczy metodą typu 8 Hyndmana i Fana (1996), jak program climdex.pcic;
arkusz kalkulacyjny domyślnie stosuje inną metodę i da inny próg. Podawaj zawsze metodę i okres bazowy.

### Przykład: opady bardzo duże w Warszawie

```bash
hydrolog meteo precipitation --index heavy --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Z 2958 dni mokrych lat 1991–2020 (okres bazowy = okres analizy) progi wynoszą 16,8 mm (95. percentyl) i 29,43 mm
(99. percentyl). Średnio opady powyżej pierwszego progu dają 22,6% opadu dni mokrych roku, a powyżej drugiego 6,9%
(`period.mean_shares_percent`). W 1991 r. pięć dni powyżej 95. percentyla przyniosło 133,2 mm, czyli 29,0% PRCPTOT
tego roku.

## 11.7. Koncentracja i sezonowość opadu

**Idea.** Dwa wskaźniki opisują jedną liczbą, jak nierówno opad rozkłada się na miesiące: wskaźnik koncentracji opadów
PCI Olivera (*precipitation concentration index*; Oliver 1980, za de Luis i in. 2011) i wskaźnik sezonowości SI Walsha
i Lawlera (1981, za Sumner i in. 2001), ten sam co dla odpływu w p. 9.4. Oba są najmniejsze przy równych miesiącach i
największe, gdy cały opad przypada na jeden miesiąc (zakresy w ramkach).

<!-- spec:precipitation_concentration_index -->

<a id="spec-precipitation_concentration_index"></a>

> **Wskaźnik koncentracji opadów Olivera z dwunastu sum miesięcznych** · specyfikacja [`precipitation_concentration_index`](../FORMULAS.md#precipitation_concentration_index) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{PCI} = 100\,\frac{\sum_{i=1}^{12} p_i^2}{\left(\sum_{i=1}^{12} p_i\right)^2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $p_i$ | `monthly_mm` (ciąg) | Dwanaście sum miesięcznych roku albo dwanaście norm miesięcznych, w dowolnej kolejności | mm | [0; ∞) | nie podano w źródłach | [0,4; 295] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{PCI}$ | `pci` | Wskaźnik: 100/12 przy równych miesiącach, 100 przy jednym miesiącu z opadem | – | [8,333333333333334; 100] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | suma dwunastu miesięcy jest dodatnia | `a_positive_total` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
>
> **Konwencje**
>
> - liczony z udziałów p_i / sum p, co daje to samo co równanie, ale bez podnoszenia sumy do kwadratu (bez przepełnienia i niedomiaru kwadratów)
> - funkcja dla serii podaje dwanaście norm miesięcznych okresu odniesienia albo dwanaście sum miesięcznych roku, który ma je wszystkie; suma równa 0 nie ma wskaźnika
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik sum miesięcznych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, eq. 1, p. 1260: PCI = 100 sum p_i^2 / (sum p_i)^2 of the twelve monthly totals; 8.3 for equal months, 100 for all in one month <https://nhess.copernicus.org/articles/11/1259/2011/>
> 2. Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300-309, the index and its classes; not opened here: as de Luis et al. (2011) print them — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020: 0.4 to 295.0 mm
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_concentration_index`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_concentration_index -->

<!-- spec:pci_class -->

<a id="spec-pci_class"></a>

> **Klasa wskaźnika koncentracji opadów według Olivera** · specyfikacja [`pci_class`](../FORMULAS.md#pci_class) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{PCI} \le 10,\ (10, 15],\ (15, 20],\ > 20
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\mathrm{PCI}$ | `pci` | Wskaźnik koncentracji opadów | – | [8,333333333333334; 100] | nie podano w źródłach | [9,4; 27,3] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `index_class` (wybór) | Klasa, od najbardziej równomiernej | – | jedna z: `uniform`, `moderate`, `irregular`, `strongly_irregular` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $10$ | `uniform_to` | Górna granica klasy rozkładu równomiernego | 10 | – | (źr. 1) |
> | $15$ | `moderate_to` | Górna granica klasy umiarkowanej koncentracji | 15 | – | (źr. 1) |
> | $20$ | `irregular_to` | Górna granica klasy rozkładu nieregularnego | 20 | – | (źr. 1) |
>
> **Konwencje**
>
> - klasy w źródle są określone liczbami całkowitymi (poniżej 10, 11-15, 16-20, powyżej 20); luki między nimi należą do klasy wyższej: 10 to rozkład równomierny, 10,5 umiarkowana koncentracja, 15 umiarkowana koncentracja, a 15,5 rozkład nieregularny
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate concentration, 16-20 irregular, above 20 strong irregularity <https://nhess.copernicus.org/articles/11/1259/2011/>
> 2. Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300-309, the index and its classes; not opened here: as de Luis et al. (2011) print them — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the yearly PCI of 1991-2020: 9.4 to 27.3
>
> Funkcja `hydrolog.statistics.meteo_precipitation.pci_class`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:pci_class -->

<!-- spec:seasonality_index -->

<a id="spec-seasonality_index"></a>

> **Wskaźnik sezonowości Walsha i Lawlera z dwunastu sum miesięcznych** · specyfikacja [`seasonality_index`](../FORMULAS.md#seasonality_index) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{SI} = \frac{1}{R}\sum_{n=1}^{12}\left|x_n - \frac{R}{12}\right|,\quad R = \sum_{n=1}^{12} x_n
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_n$ | `monthly_mm` (ciąg) | Dwanaście sum miesięcznych w dowolnej kolejności: opadu lub objętości odpływu w dowolnej jednostce (wskaźnik jest bezwymiarowy) | mm | [0; ∞) | nie podano w źródłach | [0,4; 295] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{SI}$ | `si` | Wskaźnik: 0 dla równych miesięcy, 11/6 dla jednego miesiąca z opadem | – | [0; 1,8333333333333333] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | suma dwunastu miesięcy jest dodatnia | `a_positive_total` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - obliczany jako suma \|x_n / R - 1/12\|, równa wartości wzoru bez R/12, które dla subnormalnego R ulega niedomiarowi
> - `precipitation_seasonality` podaje dwanaście norm miesięcznych okresu odniesienia albo dwanaście sum miesięcznych roku, w którym wszystkie są znane, `flow_regime` objętości miesięczne szeregu przepływów; suma równa 0 nie ma wskaźnika
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik sum miesięcznych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, eq. 1, p. 225: SI = (1/R) sum \|x_n - R/12\|, R the annual total; 0 when every month has the same total, 1.83 when one month has all of it
> 2. Zambrano-Bigiarini, M. hydroTSM: time series management and analysis for hydrological modelling, R package (CRAN), si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83 <https://cran.r-project.org/package=hydroTSM>
> 3. Walsh, R. P. D. and Lawler, D. M. (1981). Rainfall seasonality: description, spatial patterns and change through time. Weather 36(7), 201-208, the index; not opened here: as Sumner et al. (2001) and hydroTSM print it — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020: 0.4 to 295.0 mm
>
> Funkcja `hydrolog.statistics.regime.seasonality_index`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:seasonality_index -->

<!-- spec:si_class -->

<a id="spec-si_class"></a>

> **Klasa wskaźnika sezonowości według Walsha i Lawlera** · specyfikacja [`si_class`](../FORMULAS.md#si_class) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{SI} < 0{,}2,\ [0{,}2, 0{,}4),\ [0{,}4, 0{,}6),\ [0{,}6, 0{,}8),\ [0{,}8, 1{,}0),\ [1{,}0, 1{,}2),\ \ge 1{,}2
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\mathrm{SI}$ | `si` | Wskaźnik sezonowości | – | [0; 1,8333333333333333] | nie podano w źródłach | [0,31; 0,85] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `index_class` (wybór) | Klasa, od najbardziej wyrównanej | – | jedna z: `very_equable`, `equable_wetter_season`, `rather_seasonal`, `seasonal`, `markedly_seasonal`, `most_in_three_months`, `extreme` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}2$ | `very_equable_below` | Granica, poniżej której opad jest bardzo wyrównany | 0,2 | – | (źr. 1) |
> | $0{,}4$ | `equable_wetter_season_below` | Granica, poniżej której opad jest wyrównany z wyraźną porą wilgotniejszą | 0,4 | – | (źr. 1) |
> | $0{,}6$ | `rather_seasonal_below` | Granica, poniżej której opad jest dość sezonowy z krótką porą suchszą | 0,6 | – | (źr. 1) |
> | $0{,}8$ | `seasonal_below` | Granica, poniżej której opad jest sezonowy | 0,8 | – | (źr. 1) |
> | $1$ | `markedly_seasonal_below` | Granica, poniżej której opad jest wyraźnie sezonowy z długą porą suchszą | 1 | – | (źr. 1) |
> | $1{,}2$ | `most_in_three_months_below` | Granica, poniżej której większość opadu przypada na trzy miesiące lub mniej | 1,2 | – | (źr. 1) |
>
> **Konwencje**
>
> - klasy w tabeli są podane z dokładnością do dwóch miejsc po przecinku (<= 0,19, 0,20-0,39 ... >= 1,20); każda klasa sięga do następnej granicy: 0,199 to klasa bardzo wyrównana, 0,2 wyrównana z porą wilgotniejszą, 1,2 skrajna
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme
> 2. Zambrano-Bigiarini, M. hydroTSM: time series management and analysis for hydrological modelling, R package (CRAN), si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83, and its seven classes <https://cran.r-project.org/package=hydroTSM>
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the yearly SI of 1991-2020: 0.31 to 0.85
>
> Funkcja `hydrolog.statistics.meteo_precipitation.si_class`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:si_class -->

Klasy źródeł mają przerwy między granicami (Oliver – pełne liczby, Walsh i Lawler – dwa miejsca po przecinku);
Hydrolog przydziela wartość z przerwy do klasy wyższej (ADR-0059).

<!-- spec:precipitation_regime -->

<a id="spec-precipitation_regime"></a>

> **Reżim opadowy: udziały miesięcy, koncentracja i sezonowość opadu** · wzór grupy B `precipitation_regime` (Tier B, CMP-2.2)
>
> **Definicja:** każda norma miesięczna okresu odniesienia w % ich sumy i w stosunku do ich średniej; `precipitation_concentration_index` i `seasonality_index` wraz z klasami dla dwunastu norm i dla każdego roku z kompletem dwunastu sum miesięcznych oraz średnie wskaźników rocznych (źr. 1)
>
> **Konwencja:** wskaźniki norm i średnie wskaźników rocznych różnią się i podaje się oba (Sumner i in. 2001); suma równa 0 nie ma wskaźnika
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, p. 225: the SI of the mean monthly totals and the mean of the yearly SI
>
> Funkcja `hydrolog.statistics.meteo_precipitation.precipitation_seasonality`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:precipitation_regime -->

**Ważne rozróżnienie.** Wskaźnik policzony z norm miesięcznych (przeciętny reżim) jest mniejszy niż średnia wskaźników
poszczególnych lat, bo uśrednianie wygładza różnice między latami (Sumner i in. 2001). Hydrolog podaje oba.

### Przykład: sezonowość opadu w Warszawie

```bash
hydrolog meteo precipitation --index seasonality --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

| Wskaźnik | Z norm 1991–2020 | Średnia z lat 1991–2020 |
|---|---|---|
| PCI | 9,35 – rozkład równomierny | 12,35 – umiarkowana koncentracja |
| SI | 0,303 – wyrównany z porą wilgotniejszą | 0,494 – dość sezonowy |

W Warszawie najwięcej pada latem (norma lipca 82,19 mm, lutego i marca poniżej 30 mm), ale żaden miesiąc nie jest
suchy, dlatego wskaźniki przeciętnego roku są niskie. Pojedyncze lata są bardziej nieregularne: na przykład rok 1991
ma PCI 11,65 (umiarkowana koncentracja) i SI 0,467 (dość sezonowy; pole `years[]`).

## 11.8. Ciągi dni suchych i mokrych

**Idea.** CDD (*consecutive dry days*) to najdłuższy w roku ciąg kolejnych dni suchych (*dry spell*), a CWD
(*consecutive wet days*) – najdłuższy ciąg dni mokrych (ETCCDI 2009). Długi ciąg suchy wiosną lub latem zapowiada
suszę rolniczą; zimą, przy małym parowaniu, ma mniejsze znaczenie. Dzień bez pomiaru przerywa ciąg, a Hydrolog
oznacza taki ciąg jako otwarty (mógł być dłuższy).

<!-- spec:spell_lengths -->

<a id="spec-spell_lengths"></a>

> **Długość ciągu dni bezopadowych lub z opadem kończącego się w danym dniu** · specyfikacja [`spell_lengths`](../FORMULAS.md#spell_lengths) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> L_t = \begin{cases} t - s + 1 & d_s = \dots = d_t = 1,\ d_{s-1} = d_{t+1} = 0 \\ 0 & \text{w pozostałych przypadkach} \end{cases},\quad d_t = [P_t < P_0]\ (\text{dzień bezopadowy}),\ [P_t \ge P_0]\ (\text{dzień z opadem})
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_t$ | `precipitation_mm` (ciąg) | Dobowy opad z kolejnych dni; NaN w dniu z brakiem danych | mm | [0; ∞) | nie podano w źródłach | [0; 75,8] (źr. 3) |
> | $P_0$ | `threshold_mm` | Najmniejszy opad dnia z opadem | mm | (0; ∞) | nie podano w źródłach | [1; 1] (źr. 1) |
> | $\text{rodzaj}$ | `kind` (wybór) | Ciągi dni bezopadowych (poniżej progu) albo ciągi dni z opadem (na progu lub powyżej) | – | jedna z: `dry`, `wet` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $L_t$ | `spell_days` (ciąg) | Liczba dni ciągu kończącego się w danym dniu, 0 w każdym innym dniu | d | [0; ∞) |
>
> **Konwencje**
>
> - dzień suchy (bezopadowy) ma P < P0, a dzień z opadem P >= P0 (RR < 1 mm i RR >= 1 mm w ETCCDI): dzień na progu jest dniem z opadem
> - dzień z brakiem danych (NaN) nie jest ani suchy, ani z opadem: kończy ciąg i ma L = 0; funkcja dla serii oznacza taki ciąg jako otwarty
> - długość ciągu zapisuje się w jego ostatnim dniu, aby funkcja dla serii przypisywała każdy ciąg w całości do roku jego zakończenia (Tier B `spell_year`)
>
> **Zgodność z obserwacjami według źródeł:** brak: liczba dni
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
> 2. ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20: a spell can continue into the next year and is counted against the year in which the spell ends <https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf>
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm
>
> Funkcja `hydrolog.statistics.meteo_spells.spell_lengths`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spell_lengths -->

**Do którego roku należy ciąg?** Ciąg przechodzący przez 1 stycznia można przypisać na trzy sposoby: przeciąć granicą
roku (dosłowne brzmienie definicji ETCCDI), przypisać w całości rokowi, w którym się kończy (programy ETCCDI i ECA&D;
ECA&D 2021, s. 20), albo rokowi, w którym się zaczyna. Hydrolog do wersji 0.8.1 przypisywał ciąg rokowi początku, a od
wersji 0.9.0 przypisuje go rokowi końca, jak ECA&D (ADR-0044). Porównując wyniki z literaturą, sprawdzaj tę
konwencję.

<!-- spec:spell_year -->

<a id="spec-spell_year"></a>

> **Przypisanie ciągu dni do roku** · wzór grupy B `spell_year` (Tier B, CMP-2.2)
>
> **Definicja:** ciąg (`spell_lengths`) liczy się w całości w roku swojego ostatniego dnia: ciąg obejmujący początek roku nie jest dzielony, a rok leżący w całości wewnątrz ciągu, który kończy się później, nie ma najdłuższego ciągu (źr. 1)
>
> **Konwencja:** rok zakończenia ciągu, jak w climdex.pcic 1.1-11 (domyślnie spells.can.span.years = TRUE) i ECA&D; definicja ETCCDI czytana dosłownie dzieli ciąg na początku roku (ADR-0044)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20: a spell can continue into the next year and is counted against the year in which the spell ends <https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf>
>
> Funkcja `hydrolog.statistics.meteo_spells.precipitation_spells`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spell_year -->

<!-- spec:spell_summaries -->

<a id="spec-spell_summaries"></a>

> **Podsumowania ciągów dni bezopadowych i z opadem** · wzór grupy B `spell_summaries` (Tier B, CMP-2.2)
>
> **Definicja:** dla każdego roku z wartością w każdym dniu: ciągi, które się w nim kończą, najdłuższy z nich (CDD, CWD) z jego dniami oraz ciągi trwające co najmniej 10, 15 i 20 dni; dla okresu: ich średnie z tych lat oraz rozkład długości tych ich ciągów, które nie są otwarte, w przeliczeniu na rok (źr. 1)
>
> **Konwencja:** rok wymaga każdego dnia (climdex.pcic dopuszcza do 15 brakujących dni); ciąg otwarty, przylegający do dnia z brakiem danych lub do końca serii, pomija się tylko w rozkładzie długości; `min_duration_days` skraca listę ciągów, a nie podsumowania
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
>
> Funkcja `hydrolog.statistics.meteo_spells.precipitation_spells`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spell_summaries -->

### Przykład: ciągi suche i mokre w Warszawie

```bash
hydrolog meteo spells --kind dry --min-duration-days 20 --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
hydrolog meteo spells --kind wet --min-duration-days 10 --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Opcja `--min-duration-days` skraca tylko listę ciągów (`spells`); podsumowania lat i okresu liczą każdy ciąg.
W latach 1991–2020 CDD wynosił średnio 25,8 dnia, a CWD 6,2 dnia (`period.mean_max_duration_days`). Najdłuższy ciąg
suchy trwał 59 dni, od 15 grudnia 1996 r. do 11 lutego 1997 r., i liczy się w roku 1997; w roku 1996 najdłuższy ciąg
to 25 dni (9 stycznia – 2 lutego). Gdyby przypisać ciąg rokowi początku, rok 1996 miałby CDD 59 dni, a rok 1997 –
znacznie krótszy. Jedyny ciąg mokry dłuższy niż 10 dni trwał 12 dni, od 12 do 23 maja 2019 r.

## 11.9. Standaryzowany wskaźnik opadu SPI

**Idea.** Standaryzowany wskaźnik opadu (*standardized precipitation index*, SPI) mówi, jak nietypowa była suma opadu
z ostatnich $k$ miesięcy w porównaniu z sumami tych samych miesięcy w wieloleciu, w jednostkach odchylenia
standardowego rozkładu normalnego (McKee i in. 1993; WMO 2012). Skala $k$ odpowiada różnym zasobom wody: kilka miesięcy
– wilgotności gleby i suszy rolniczej, kilka do kilkunastu – przepływom rzek i retencji, dłuższe – wodom podziemnym
(WMO 2012).

**Procedura.** Dla każdej skali i każdego miesiąca kalendarzowego osobno: sumy $k$-miesięczne kończące się w tym
miesiącu w latach okresu odniesienia, rozkład gamma dopasowany do sum dodatnich (przybliżenie Thoma, 1958),
uwzględnienie sum zerowych i przeliczenie prawdopodobieństwa na zmienną standardową rozkładu normalnego (Edwards i
McKee 1997; Naresh Kumar i in. 2009).

<!-- spec:spi_k_month_sums -->

<a id="spec-spi_k_month_sums"></a>

> **SPI k-miesięcznych sum opadu** · wzór grupy B `spi_k_month_sums` (Tier B, CMP-2.2)
>
> **Definicja:** k-miesięczna suma danego miesiąca to suma sum miesięcznych k miesięcy, które się w nim kończą; jest brakiem, jeśli nie wszystkie k sum są znane; sumy każdego miesiąca kalendarzowego z okresu odniesienia są dopasowywane (`spi_gamma_fit`), gdy są znane w co najmniej 80 % jego lat, wliczając lata bez danych (źr. 1)
>
> **Konwencja:** k-miesięczne sumy okresu odniesienia pozostają w obrębie jego lat (climate_indices 3.2.0 pozwala sumom jego pierwszych k - 1 miesięcy sięgać przed ten okres); każdy analizowany miesiąc otrzymuje SPI własnej sumy według dopasowania dla swojego miesiąca kalendarzowego; miesiąc, którego sum dopasowanie nie przyjmuje, nie ma SPI (komunikat `spi_not_fitted`)
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $80 %$ | `normal_share` | Najmniejszy udział lat okresu odniesienia z wartością | 4/5 | – | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) <https://library.wmo.int/idurl/4/39629>
> 2. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: values in at least 80 % of the years of the period; section 4.3.3, p. 6: the normal of several months from the monthly normals <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_spi.standardized_precipitation_index`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spi_k_month_sums -->

<!-- spec:spi_gamma_fit -->

<a id="spec-spi_gamma_fit"></a>

> **Rozkład gamma sum opadu według przybliżenia Thoma** · specyfikacja [`spi_gamma_fit`](../FORMULAS.md#spi_gamma_fit) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> A = \ln\bar{x} - \overline{\ln x},\quad \hat{\alpha} = \frac{1 + \sqrt{1 + 4A/3}}{4A},\quad \hat{\beta} = \frac{\bar{x}}{\hat{\alpha}},\quad q = \frac{m}{n}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `sums_mm` (ciąg) | Sumy opadu jednego miesiąca kalendarzowego i jednej skali czasowej, po jednej na każdy rok okresu odniesienia | mm | [0; ∞) | nie podano w źródłach | [0; 872,3] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\hat{\alpha}$ | `alpha` | Parametr kształtu rozkładu gamma sum dodatnich | – | (0; ∞) |
> | $\hat{\beta}$ | `beta_mm` | Parametr skali tego rozkładu | mm | (0; ∞) |
> | $q$ | `zero_probability` | Udział sum zerowych | – | [0; 1) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | co najmniej trzy sumy są dodatnie | `three_positive_sums` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | sumy dodatnie nie są wszystkie równe (A > 0) | `positive_sums_differ` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $4/3$ | `thom_ratio` | Współczynnik przy A pod pierwiastkiem w przybliżeniu Thoma | 4/3 | – | (źr. 2) |
> | $4$ | `thom_denominator` | Mnożnik A w mianowniku przybliżenia Thoma | 4 | – | (źr. 2) |
>
> **Konwencje**
>
> - sumy jednego miesiąca kalendarzowego i jednej skali czasowej z lat okresu odniesienia; wywołujący pomija lata bez sumy
> - q = m / n, udział sum zerowych wśród wszystkich n sum (Edwards i McKee 1997, w ujęciu Naresha Kumara i in. 2009, wzór A9); parametry kształtu i skali tylko z sum dodatnich
> - przybliżenie Thoma, a nie dokładny estymator największej wiarygodności, jak w climate_indices 3.2.0 i xclim 1.0.0 (metoda APP)
> - A liczone jako średnia z d - ln(1 + d), gdzie d = x / (średnia x) - 1, co jest równe ln(średnia x) - średnia(ln x), lecz bez utraty dokładności przy odejmowaniu (ln x - ln(średnia x) dla sumy mniejszej od połowy średniej)
>
> **Zgodność z obserwacjami według źródeł:** Estymator Thoma przybliża estymator największej wiarygodności parametru kształtu: jego błąd względny wynosi 1e-4 przy A = 0,1 (alpha bliskie 5), 2e-3 przy A = 0,3 i 2,7 % przy A = 1 (alpha 0,62) w porównaniu z dokładnym rozwiązaniem równania ln(alpha) - digamma(alpha) = A (audyt z 2026-11-18); źródła nie podają testu dopasowania do obserwacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Thom, H. C. S. (1958). A note on the gamma distribution. Monthly Weather Review 86(4), 117, the approximation of the maximum likelihood estimate of the shape; not opened here: its equations as McSweeney (2007) and Naresh Kumar et al. (2009) print them — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. McSweeney, C. F. (2007). Daily rainfall variability at point and areal scales: evaluating simulations of present and future climate. PhD thesis, University of East Anglia, Norwich, chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum likelihood estimate of the shape <https://crudata.uea.ac.uk/cru/pubs/thesis/2007-mcsweeney/4.Gamma.pdf>
> 3. Naresh Kumar, M., Murthy, C. S., Sesha Sai, M. V. R. and Roy, P. S. (2009). On the use of Standardized Precipitation Index (SPI) for drought intensity assessment. Meteorological Applications 16(3), 381-389; open preprint arXiv:1509.04808, appendix, eqs. A4-A8 (Thom's estimates) and A9 (q = m / n) <https://arxiv.org/pdf/1509.04808>
> 4. WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) <https://library.wmo.int/idurl/4/39629>
> 5. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the k-month sums of the default scales 1, 3, 6 and 12: 0.4 to 872.3 mm (a month without precipitation gives 0)
> 6. Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a station, the group meteo, point 5: a calendar month is fitted when 3 of its sums are positive <https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/0032-meteorological-statistics-of-a-station-the-group-meteo.md>
>
> Funkcja `hydrolog.statistics.meteo_spi.fit_gamma`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spi_gamma_fit -->

<!-- spec:spi -->

<a id="spec-spi"></a>

> **Standaryzowany wskaźnik opadu (SPI) dla sum opadu** · specyfikacja [`spi`](../FORMULAS.md#spi) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> H(x) = q + (1 - q)\,P\!\left(\alpha, \frac{x}{\beta}\right),\quad H(0) = q,\quad \mathrm{SPI} = \max\!\left(-3{,}09, \min\!\left(3{,}09, \Phi^{-1}(H(x))\right)\right)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x$ | `sums_mm` (ciąg) | Sumy opadu z miesiąca kalendarzowego i skali czasowej rozkładu; NaN pozostaje NaN | mm | [0; ∞) | nie podano w źródłach | [0; 872,3] (źr. 4) |
> | $\alpha$ | `alpha` | Parametr kształtu rozkładu gamma (`spi_gamma_fit`) | – | (0; ∞) | nie podano w źródłach | [1,7; 42,6] (źr. 5) |
> | $\beta$ | `beta_mm` | Parametr skali rozkładu gamma (`spi_gamma_fit`) | mm | (0; ∞) | nie podano w źródłach | [5,8; 31,7] (źr. 6) |
> | $q$ | `zero_probability` | Prawdopodobieństwo sumy zerowej (`spi_gamma_fit`) | – | [0; 1) | nie podano w źródłach | [0; 0] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{SPI}$ | `spi` (ciąg) | SPI każdej sumy | – | [−3,09; 3,09] |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $3{,}09$ | `spi_limit` | Graniczna wartość bezwzględna SPI | 3,09 | – | (źr. 3) |
>
> **Konwencje**
>
> - klasyczne traktowanie sum zerowych, H(0) = q (Edwards i McKee 1997; climate_indices, `zero_handling` 'classic'); środek masy zer, Phi^-1(q / 2), nie jest stosowany
> - wartości ograniczone do przedziału od -3,09 do 3,09, czyli kwantyli rzędu 0,001 i 0,999, jak w climate_indices; WMO-No. 1090 i xclim nie wprowadzają ograniczenia
> - górny ogon liczony z 1 - H = (1 - q) Q(alpha, x / beta), gdzie Q to regularyzowana górna niekompletna funkcja gamma, tam gdzie H > 0,5
> - SPI nie jest przypisywany do klas (WMO-No. 1090, tab. 1 podaje klasy od -2 do 2)
>
> **Zgodność z obserwacjami według źródeł:** brak: SPI jest przekształceniem dopasowanego rozkładu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) <https://library.wmo.int/idurl/4/39629>
> 2. Naresh Kumar, M., Murthy, C. S., Sesha Sai, M. V. R. and Roy, P. S. (2009). On the use of Standardized Precipitation Index (SPI) for drought intensity assessment. Meteorological Applications 16(3), 381-389; open preprint arXiv:1509.04808, appendix, eq. A9 (H(x) = q + (1 - q) G(x), after Edwards and McKee 1997) and eqs. A10-A12 (the normal quantile) <https://arxiv.org/pdf/1509.04808>
> 3. climate_indices 3.2.0 (J. Adams), Python package of climate indices, indices.spi: Thom's estimates, zero_handling 'classic' (H(0) = q), the SPI held within the valid range of a fitted index, -3.09 to 3.09 <https://pypi.org/project/climate-indices/3.2.0/>
> 4. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the k-month sums of the default scales 1, 3, 6 and 12: 0.4 to 872.3 mm (a month without precipitation gives 0)
> 5. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the fits of the default scales 1, 3, 6 and 12: shapes 1.72 to 42.60
> 6. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the fits of the default scales 1, 3, 6 and 12: scales 5.81 to 31.71 mm
> 7. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, no month without precipitation in 1991-2020: q = 0 in every fit of the default scales
>
> Funkcja `hydrolog.statistics.meteo_spi.spi_values`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:spi -->

**Konwencje i różnice między programami.**

- **Metoda dopasowania.** Hydrolog stosuje przybliżenie Thoma, jak pakiety climate_indices i xclim; dokładna metoda
  największej wiarygodności i L-momenty dają nieco inne parametry, a pakiet R SPEI domyślnie stosuje jeszcze inną metodę
  (ważone momenty prawdopodobieństwa). Copernicus EDO dopasowuje rozkład L-momentami (EDO 2025).
- **Okres odniesienia.** Sumy $k$-miesięczne okresu odniesienia Hydrolog bierze tylko z jego lat: suma dwunastomiesięczna
  kończąca się w sierpniu pierwszego roku sięga roku poprzedniego, więc nie wchodzi do dopasowania. Inne programy mogą
  ją uwzględniać, a wtedy SPI dłuższych skal się różni. Zmiana okresu odniesienia zmienia SPI każdego miesiąca: zawsze
  go podawaj.
- **Ograniczenie wartości.** Hydrolog ogranicza SPI do przedziału podanego w ramce, jak climate_indices; wartość na
  granicy przedziału znaczy „co najmniej tak skrajnie”.
- **Klasy.** Hydrolog nie klasyfikuje SPI. WMO (2012, tab. 1) podaje klasy od „ekstremalnie wilgotno” do „ekstremalnie
  sucho” co pół odchylenia standardowego poza przedziałem wartości przeciętnych; w Polsce stosuje się też klasy
  Łabędzkiego (2006, za Gąsiorek i Musiał 2011, tab. 2), z węższym przedziałem wartości normalnych. Podawaj, czyje klasy
  stosujesz.

**Zakres stosowania.** WMO (2012) zaleca co najmniej 30 lat danych miesięcznych. Przy kilkunastu latach parametry
rozkładu są bardzo niepewne. Gdy w okresie odniesienia brakuje sum w zbyt wielu latach albo jest za mało sum dodatnich,
Hydrolog nie dopasowuje rozkładu i zgłasza uwagę `spi_not_fitted`. Sprawdzian: Hydrolog odtwarza opublikowany przykład
Naresha Kumara i in. (2009) – parametry rozkładu gamma i wartości SPI lipcowych sum opadu w dystrykcie Anantapur –
z dokładnością do 0,001 (dodatek D).

### Przykład: susza 2015 r. w Warszawie

```bash
hydrolog meteo spi --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Domyślne skale to 1, 3, 6 i 12 miesięcy (`scales_months`), a okres odniesienia – lata 1991–2020. Rozkład gamma
sierpniowych sum jednomiesięcznych (`period.scales[].fits[]`) ma parametr kształtu $\alpha = 3{,}23$ i parametr skali
$\beta = 18{,}77$ mm. Wartości SPI wybranych miesięcy (`months[].spi`):

| Miesiąc | Suma [mm] | % normy | SPI-1 | SPI-3 | SPI-6 | SPI-12 |
|---|---|---|---|---|---|---|
| maj 2010 | 116,4 | 209,9 | 2,27 | 1,55 | 1,27 | 1,84 |
| listopad 2011 | 0,4 | 1,1 | −3,09 | −3,09 | 1,11 | 0,63 |
| sierpień 2015 | 8,4 | 13,9 | −2,48 | −2,07 | −2,01 | −2,45 |

Sierpień 2015 r. był skrajnie suchy we wszystkich skalach: niedobór opadu obejmował nie tylko ten miesiąc, ale całe
lato, półrocze i rok kończące się w sierpniu. Listopad 2011 r. pokazuje, że skale mówią różne rzeczy: jeden miesiąc
prawie bez opadu daje SPI-1 i SPI-3 na granicy przedziału (wartość ograniczona), ale półrocze i rok kończące się w
listopadzie były wilgotniejsze od przeciętnych. Dwunastomiesięczne dopasowanie dla sierpnia ma 29 sum, nie 30
(`n_values`): suma kończąca się w sierpniu 1991 r. sięga roku 1990, spoza okresu.

## 11.10. Temperatura powietrza: średnie, anomalie, ekstrema, amplituda dobowa

**Idea.** Średnia miesięczna temperatura to średnia temperatur dobowych miesiąca, a średnia roczna – średnia dwunastu
średnich miesięcznych, bez ważenia liczbą dni (WMO 2017, rozdz. 4.3.3). Anomalia (*anomaly*) to różnica między
wartością a normą. Dobowa amplituda temperatury (DTR, *daily temperature range*) to różnica temperatury maksymalnej i
minimalnej doby, uśredniona w miesiącu (ETCCDI 2009).

<!-- spec:temperature_monthly_means -->

<a id="spec-temperature_monthly_means"></a>

> **Średnie miesięczne i roczne temperatury powietrza** · wzór grupy B `temperature_monthly_means` (Tier B, CMP-2.2)
>
> **Definicja:** średnia z dobowych Tmean, Tmax i Tmin miesiąca, w którym brakuje mniej niż 11 dni i mniej niż 5 dni z rzędu; dla roku – średnia z jego dwunastu średnich miesięcznych, wymagająca każdej z nich (źr. 1)
>
> **Konwencja:** dwanaście miesięcy ma jednakową wagę (WMO-No. 1203, 4.3.3 a, przypis 1: ważenie liczbą dni nie jest zalecane)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (a) and 4.4.1 (a), pp. 5-7; 4.3.3 (a), p. 6 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_temperature.temperature_means`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:temperature_monthly_means -->

<!-- spec:temperature_extremes -->

<a id="spec-temperature_extremes"></a>

> **Ekstremalne temperatury powietrza z datami wystąpienia** · wzór grupy B `temperature_extremes` (Tier B, CMP-2.2)
>
> **Definicja:** najwyższa Tmax i najniższa Tmin miesiąca, roku i całego okresu wraz z datami, z dni, które mają wartość (źr. 1)
>
> **Konwencja:** ekstremum wyznacza się z tylu dni, ile jest dostępnych (WMO-No. 1203, 4.4.1 b); przy równych ekstremach – pierwsze z nich i jego data
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b), p. 7 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_temperature.temperature_means`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:temperature_extremes -->

<!-- spec:daily_temperature_range -->

<a id="spec-daily_temperature_range"></a>

> **Dobowa amplituda temperatury powietrza** · wzór grupy B `daily_temperature_range` (Tier B, CMP-2.2)
>
> **Definicja:** DTR: Tmax - Tmin każdego dnia z obiema wartościami, jej średnia w miesiącu, w którym brakuje mniej niż 11 dni i mniej niż 5 dni z rzędu, a dla roku – średnia z jego dwunastu średnich miesięcznych (źr. 1)
>
> **Konwencja:** dzień z Tmax niższą od Tmin przyjmuje się bez zmian (bez kontroli; kwestia otwarta audytu z 2026-11-18)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN <https://etccdi.pacificclimate.org/list_27_indices.shtml>
>
> Funkcja `hydrolog.statistics.meteo_temperature.temperature_range`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:daily_temperature_range -->

**Średnia dobowa IMGW-PIB.** Średnią dobową IMGW-PIB liczy z pomiarów terminowych według wzorów zależnych od rodzaju
stacji i okresu: stacje synoptyczne od 1966 r. z ośmiu terminów, stacje klimatologiczne z mniejszej liczby terminów
(IMGW-PIB, Jednolite serie danych). Nie jest to średnia temperatury maksymalnej i minimalnej. Szereg sklejony ze stacji
różnych typów może więc mieć skok wynikający ze zmiany wzoru, który test jednorodności (rozdział 10) weźmie za zmianę
klimatu. Hydrolog nie sprawdza też, czy temperatura maksymalna doby nie jest mniejsza od minimalnej: błędny dzień
zaniży średnią amplitudę bez ostrzeżenia, więc dane trzeba sprawdzić wcześniej.

### Przykład: temperatura w Warszawie

```bash
hydrolog meteo temperature --index means --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
hydrolog meteo temperature --index range --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Norma średniej temperatury 1991–2020 wynosi 8,97 °C. Najcieplejszy był rok 2019: 10,89 °C, anomalia +1,92 °C;
najzimniejszy rok 1996: 6,83 °C. Najwyższa temperatura okresu to 37,0 °C (8 sierpnia 2013 r.), najniższa −27,1 °C
(24 stycznia 2006 r.). Średnia dobowa amplituda temperatury lat 1991–2020 wynosi 8,36 °C.

## 11.11. Dni charakterystyczne

**Idea.** Dni charakterystyczne liczą dni, w których temperatura przekroczyła próg: dni z przymrozkiem (*frost days*,
FD), mroźne (*ice days*, ID), gorące (*summer days*, SU), upalne (*hot days*) i noce tropikalne (*tropical nights*,
TR). Hydrolog stosuje domyślnie definicje ETCCDI z ostrymi nierównościami (ETCCDI 2009); każdy próg można zmienić
opcją.

<!-- spec:threshold_days -->

<a id="spec-threshold_days"></a>

> **Dzień FD, przymrozkowy, mroźny, gorący i upalny oraz noc tropikalna dla jednej doby** · specyfikacja [`threshold_days`](../FORMULAS.md#threshold_days) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{FD} = [T_{n} < T_f],\ \mathrm{FT} = [T_{n} < T_f][T_{x} > T_i],\ \mathrm{ID} = [T_{x} < T_i],\ \mathrm{SU} = [T_{x} > T_s],\ \mathrm{HD} = [T_{x} > T_h],\ \mathrm{TR} = [T_{n} > T_t]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $T_x$ | `tmax_c` (ciąg) | Maksymalna dobowa temperatura powietrza; NaN w dniu z brakiem danych | °C | [−273,15; ∞) | nie podano w źródłach | [−16,7; 37] (źr. 4) |
> | $T_n$ | `tmin_c` (ciąg) | Minimalna dobowa temperatura powietrza z tych samych dni; NaN w dniu z brakiem danych | °C | [−273,15; ∞) | nie podano w źródłach | [−27,1; 22,8] (źr. 5) |
> | $T_f$ | `frost_tmin_c` | Próg: dzień FD ma Tmin poniżej tej wartości | °C | [−273,15; ∞) | nie podano w źródłach | [0; 0] (źr. 1) |
> | $T_i$ | `ice_tmax_c` | Próg: dzień mroźny ma Tmax poniżej tej wartości, a dzień przymrozkowy powyżej niej | °C | [−273,15; ∞) | nie podano w źródłach | [0; 0] (źr. 1) |
> | $T_s$ | `summer_tmax_c` | Próg: dzień gorący ma Tmax powyżej tej wartości | °C | [−273,15; ∞) | nie podano w źródłach | [25; 25] (źr. 1) |
> | $T_h$ | `hot_tmax_c` | Próg: dzień upalny ma Tmax powyżej tej wartości | °C | [−273,15; ∞) | nie podano w źródłach | [30; 30] (źr. 2) |
> | $T_t$ | `tropical_tmin_c` | Próg: noc tropikalna ma Tmin powyżej tej wartości | °C | [−273,15; ∞) | nie podano w źródłach | [20; 20] (źr. 1) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `frost` (ciąg) | 1 w dniu FD | – | [0; 1] |
> | – | `freeze_thaw` (ciąg) | 1 w dniu przymrozkowym; NaN, gdy brakuje którejkolwiek z obu temperatur | – | [0; 1] |
> | – | `ice` (ciąg) | 1 w dniu mroźnym | – | [0; 1] |
> | – | `summer` (ciąg) | 1 w dniu gorącym | – | [0; 1] |
> | – | `hot` (ciąg) | 1 w dniu upalnym | – | [0; 1] |
> | – | `tropical` (ciąg) | 1 w przypadku nocy tropikalnej | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | `tmax_c` i `tmin_c` obejmują te same dni, po jednej wartości każdej z nich na dzień | `the_same_days` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - nierówności ostre jak w ETCCDI: dzień dokładnie na progu nie jest żadnym z tych dni; roczniki IMGW-PIB liczą Tmin <= 0 oraz Tmax >= 25 lub 30 °C
> - dzień przymrozkowy (ang. freeze-thaw day) to „dzień przymrozkowy” w rozumieniu Słownika meteorologicznego i norm IMGW-PIB (PRZYMROZKI); dzień z ujemną temperaturą minimalną (ang. frost day) to FD
> - wskaźnik ma wartość brakującą (NaN) tam, gdzie brakuje potrzebnej mu temperatury; funkcja dla serii zwraca serię samych braków dla wskaźnika, którego temperatury nie ma
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja doby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN <https://etccdi.pacificclimate.org/list_27_indices.shtml>
> 2. Kossowska-Cezak, U. (2014). Zmiany wieloletnie liczby termicznych dni charakterystycznych w Warszawie (1951-2010). Prace Geograficzne 136, 9-30, p. 14, after the Słownik meteorologiczny (2003): a hot day („upalny”) has tmax > 30 °C, a freeze-thaw day („przymrozkowy”) tmin < 0 °C and tmax > 0 °C
> 3. IMGW-PIB: Normy klimatyczne 1991-2020, product PRZYMROZKI, „Liczba dni przymrozkowych (TMAX>0 & TMIN<0)” <https://klimat.imgw.pl>
> 4. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily maximum temperature: -16.7 to 37.0 °C
> 5. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily minimum temperature: -27.1 to 22.8 °C
>
> Funkcja `hydrolog.statistics.meteo_temperature.threshold_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:threshold_days -->

<!-- spec:temperature_day_counts -->

<a id="spec-temperature_day_counts"></a>

> **Liczby dni charakterystycznych temperatury** · wzór grupy B `temperature_day_counts` (Tier B, CMP-2.2)
>
> **Definicja:** liczba dni każdego rodzaju z `threshold_days` w miesiącu, w którym brakuje mniej niż 11 dni i mniej niż 5 dni z rzędu, przeskalowana do liczby dni miesiąca; dla roku – suma jego dwunastu miesięcy, wymagająca każdego z nich (źr. 1)
>
> **Konwencja:** przy lukach liczba dni w miesiącu nie jest liczbą całkowitą (climdex.pcic liczy te dni, które ma)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.1 (d) and 4.4.1 (d), pp. 5-8 <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_temperature.temperature_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:temperature_day_counts -->

**Polska terminologia nie jest jednolita** („nie ma jednolitych kryteriów wyróżniania dni charakterystycznych o tej
samej nazwie” – Kossowska-Cezak 2014). Najważniejsza różnica dotyczy dni przymrozkowych:

- *Słownik meteorologiczny* (2003), IMGW-PIB (normy 1991–2020, serwis agrometeorologiczny): **dzień przymrozkowy** to
  dzień z przymrozkiem, w którym temperatura maksymalna przekracza próg dnia mroźnego, czyli dzień z odwilżą w ciągu
  doby. Dni przymrozkowe i mroźne są wtedy rozłączne. W Hydrologu to pole `freeze_thaw_days`.
- *Atlas klimatu Polski* (2005) i KLIMADA 2.0 (Strużewska i in. 2020): dniem przymrozkowym nazywa się każdy dzień z przymrozkiem (FD
  ETCCDI). W Hydrologu to pole `frost_days`, w polskich etykietach „dni z przymrozkiem” (ADR-0044).

Roczniki IMGW-PIB liczą dni z nierównościami nieostrymi (temperatura „nie wyższa niż” albo „nie niższa niż” próg).
Temperatury podaje się z dokładnością 0,1 °C, więc dni dokładnie na progu nie są rzadkie. Żeby odtworzyć liczby IMGW-PIB
z ostrymi nierównościami Hydrologa, przesuń próg o pół dokładności danych (przykład niżej). Gdy podajesz liczbę dni
przymrozkowych, zawsze dopisz warunek.

### Przykład: dni charakterystyczne w Warszawie

```bash
hydrolog meteo temperature --index days --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
hydrolog meteo temperature --index days --input-file tests/fixtures/warszawa_okecie_1991_2020.csv --summer-tmax-c 24.95 --hot-tmax-c 29.95
```

Średnia liczba dni w roku, 1991–2020 (pole `period`), i normy IMGW-PIB 1991–2020 dla stacji Warszawa:

| Wskaźnik (pole) | Hydrolog, progi domyślne | Hydrolog, progi przesunięte | Normy IMGW-PIB |
|---|---|---|---|
| dni z przymrozkiem, FD (`frost_days`) | 97,9 | 97,9 | 97,9 |
| dni przymrozkowe (`freeze_thaw_days`) | 64,0 | 64,0 | 64,0 |
| dni mroźne, ID (`ice_days`) | 32,7 | 32,7 | 32,6 |
| dni gorące, SU (`summer_days`) | 48,5 | 49,7 | 49,8 |
| dni upalne (`hot_days`) | 9,0 | 9,5 | 9,6 |
| noce tropikalne, TR (`tropical_nights`) | 1,4 | 1,4 | – |

Normy IMGW-PIB dni gorących i upalnych liczą dni z temperaturą maksymalną nie niższą niż próg; z progami przesuniętymi
o 0,05 °C Hydrolog odtwarza je z dokładnością 0,1 dnia. Różnica między FD (97,9) a dniami przymrozkowymi w sensie
IMGW-PIB (64,0) to dni mroźne (32,7) i dni z temperaturą maksymalną dokładnie na progu dnia mroźnego (1,1 dnia).

## 11.12. Stopniodni

**Idea.** Stopniodni wzrostu (*growing degree days*, GDD) sumują nadwyżki średniej temperatury dobowej ponad
temperaturę bazową i opisują ciepło dostępne dla roślin (Wypych i in. 2017). Stopniodni grzania (*heating degree days*,
HDD) według Eurostatu sumują niedobór temperatury względem temperatury odniesienia w dniach chłodniejszych od
temperatury granicznej i opisują zapotrzebowanie na ogrzewanie (Eurostat 2024; dyrektywa Komisji (UE) 2015/1127).

<!-- spec:degree_days -->

<a id="spec-degree_days"></a>

> **Stopniodni wzrostu i grzania dla każdej doby** · specyfikacja [`degree_days`](../FORMULAS.md#degree_days) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{GDD} = \max(T_m - T_b, 0),\quad \mathrm{HDD} = \begin{cases} T_r - T_m & T_m \le T_l \\ 0 & T_m > T_l \end{cases},\quad T_l \le T_r
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $T_m$ | `tmean_c` (ciąg) | Średnia dobowa temperatura powietrza; NaN w dniu z brakiem danych | °C | [−273,15; ∞) | nie podano w źródłach | [−22,2; 29,3] (źr. 3) |
> | $T_b$ | `growing_base_c` | Temperatura bazowa stopniodni wzrostu | °C | [−273,15; ∞) | nie podano w źródłach | [0; 10] (źr. 2) |
> | $T_r$ | `heating_base_c` | Temperatura odniesienia stopniodni grzania (polska „temperatura bazowa”) | °C | [−273,15; ∞) | nie podano w źródłach | [18; 18] (źr. 1) |
> | $T_l$ | `heating_limit_c` | Próg grzania: doba jest dniem grzewczym, gdy Tm nie przekracza tej wartości (angielska „base temperature” Eurostatu, polska „temperatura graniczna”) | °C | [−273,15; ∞) | nie podano w źródłach | [15; 15] (źr. 1) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{GDD}$ | `growing_degree_days` (ciąg) | Stopniodni wzrostu każdej doby | °C·d | [0; ∞) |
> | $\mathrm{HDD}$ | `heating_degree_days` (ciąg) | Stopniodni grzania każdej doby | °C·d | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | `heating_limit_c <= heating_base_c`: dzień grzewczy leży poniżej temperatury odniesienia, więc jego stopniodni nie są ujemne | `heating_limit_not_above_base` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - Tm to podana średnia dobowa; dyrektywa, na której opiera się Eurostat, przyjmuje Tm = (Tmin + Tmax) / 2 (w Warszawie-Okęciu w latach 1991–2020 HDD 3407 wobec 3365 °C·d)
> - doba jest dniem grzewczym przy Tm <= Tl (włącznie), a stopniodni wzrostu daje przy Tm > Tb
> - funkcja dla serii sumuje dni pełnych miesięcy i dwanaście miesięcy roku: nie wydziela się okresu wegetacyjnego ani sezonu grzewczego
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik średniej dobowej temperatury
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) <https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm>
> 2. Wypych, A., Sulikowska, A., Ustrnul, Z. and Czekierda, D. (2017). Variability of growing degree days in Poland in response to ongoing climate changes in Europe. International Journal of Biometeorology 61, 49-59, eq. 1, p. 50: GDD = sum of (T - Tbase) over the days with T > Tbase; the bases 0, 5 and 10 °C
> 3. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily mean temperature: -22.2 to 29.3 °C
>
> Funkcja `hydrolog.statistics.meteo_temperature.daily_degree_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:degree_days -->

<!-- spec:degree_day_sums -->

<a id="spec-degree_day_sums"></a>

> **Miesięczne i roczne sumy stopniodni** · wzór grupy B `degree_day_sums` (Tier B, CMP-2.2)
>
> **Definicja:** suma `degree_days` wszystkich dni miesiąca, wymagająca każdego dnia; dla roku – suma jego dwunastu miesięcy, wymagająca każdego z nich (źr. 1)
>
> **Konwencja:** nie wydziela się okresu wegetacyjnego ani sezonu grzewczego (Eurostat: liczone dla każdej doby i sumowane do roku)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) <https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm>
>
> Funkcja `hydrolog.statistics.meteo_temperature.degree_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:degree_day_sums -->

**Nazwy temperatur.** W polskim opisie metody Eurostatu (Dopke 2010) temperaturą bazową nazywa się temperaturę
odniesienia, od której odejmuje się temperaturę dnia, a temperaturą graniczną – niższy próg, od którego dzień liczy się
jako dzień grzewczy. Angielski tekst Eurostatu nazywa „base temperature” właśnie ten niższy próg. Wartości obu – w
ramce.

**Średnia dobowa.** Dyrektywa liczy średnią dobową jako średnią temperatury minimalnej i maksymalnej, a Hydrolog bierze
średnią dobową podaną w danych (w Warszawie: średnią IMGW-PIB z ośmiu terminów). W latach 1991–2020 daje to w Warszawie
HDD 3407 °C·d zamiast 3365 °C·d według wzoru dyrektywy, o 1,25% więcej (ADR-0044).

**Typowy błąd.** Liczenie HDD jako sumy różnic temperatury odniesienia i temperatury dnia po wszystkich dniach roku:
latem różnice są ujemne i wynik nie odpowiada statystyce Eurostatu.

### Przykład: stopniodni w Warszawie

```bash
hydrolog meteo temperature --index degree_days --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

Średnio w latach 1991–2020: GDD 2179 °C·d, HDD 3407 °C·d (pole `period`). Obie sumy obejmują wszystkie dni roku;
Hydrolog nie wycina okresu wegetacyjnego ani sezonu grzewczego.

## 11.13. Pokrywa śnieżna

**Idea.** Pokrywa śnieżna (*snow cover*) według IMGW-PIB to warstwa śniegu zalegająca na ponad połowie terenu wokół
stacji; jej grubość mierzy się codziennie rano (IMGW-PIB, Rocznik Meteorologiczny). Liczba dni z pokrywą, jej
największa grubość oraz pierwszy i ostatni dzień z pokrywą opisują zimę i zasoby wody w śniegu, ważne dla wezbrań
roztopowych.

<!-- spec:snow_cover_day -->

<a id="spec-snow_cover_day"></a>

> **Dzień z pokrywą śnieżną** · wzór grupy B `snow_cover_day` (Tier B, CMP-2.2)
>
> **Definicja:** dzień z pokrywą śnieżną to dzień, w którym jej grubość wynosi co najmniej 1 cm; liczbę takich dni w miesiącu przeskalowuje się do liczby jego dni, gdy brakuje mniej niż 11 dni i mniej niż 5 dni z rzędu; liczba dni w zimie to suma z jej miesięcy (źr. 1)
>
> **Konwencja:** co najmniej 1 cm, jak w rocznikach IMGW-PIB i we wskaźniku SD1 ECA&D; normy IMGW-PIB liczą dni z pokrywą > 0 cm (SNIEG_0, to samo przy pełnych centymetrach) i > 1 cm (SNIEG_1)
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1 cm$ | `snow_cover_cm` | Najmniejsza grubość pokrywy śnieżnej w dniu z pokrywą | 1 | cm | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB (2023). Rocznik Meteorologiczny 2022, p. 5: snow cover, a layer of at least 1 cm covering more than half of the terrain around the station, measured at 06 UTC <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/Rocznik%20meteorologiczny/Rocznik%20Meteorologiczny%202022.pdf>
> 2. ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.3.9: SD1, snow days (SD >= 1 cm) <https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf>
>
> Funkcja `hydrolog.statistics.meteo_snow.snow_cover`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snow_cover_day -->

**Zima.** Hydrolog liczy zimy jako sezony od lata do lata, nazwane rokiem, w którym się kończą, tak jak Urban (2015);
dzięki temu śnieg z października należy do zimy, którą zaczyna. W literaturze spotyka się też sezony od
października do maja, od listopada do marca i od grudnia do lutego, więc porównując wyniki, sprawdź, jaki sezon
przyjęto. Normy IMGW-PIB liczą dni z pokrywą w latach kalendarzowych.

<!-- spec:snow_season -->

<a id="spec-snow_season"></a>

> **Sezon pokrywy śnieżnej (zima)** · wzór grupy B `snow_season` (Tier B, CMP-2.2)
>
> **Definicja:** zima to sezon pokrywy śnieżnej od 1 sierpnia do 31 lipca, nazwany rokiem, w którym się kończy; jest kompletna, gdy każdy miesiąc od października do maja ma dostatecznie wiele dni z danymi (źr. 1)
>
> **Konwencja:** cała chłodna pora roku łącznie: śnieg z końca października rozpoczyna swoją zimę (w badaniach polskich stosuje się też sezony X–V, XI–III lub XII–II)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Urban, G. (2015). Przegląd Geograficzny 87(3), pp. 498-499: the snow season from 1 August to 31 July, after Falarz — *źródło niedostępne publicznie (dostarczone przez autora)*
>
> Funkcja `hydrolog.statistics.meteo_snow.snow_cover`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snow_season -->

<!-- spec:snow_season_extremes -->

<a id="spec-snow_season_extremes"></a>

> **Charakterystyki skrajne pokrywy śnieżnej zimy** · wzór grupy B `snow_season_extremes` (Tier B, CMP-2.2)
>
> **Definicja:** największa grubość pokrywy z dniem jej wystąpienia, pierwszy i ostatni dzień z pokrywą śnieżną oraz suma grubości śniegu świeżego w zimie, z tych dni, które są dostępne (źr. 1)
>
> **Konwencja:** pierwsza z równych największych grubości
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b) and (d), pp. 7-8: extremes from whatever days, counts of months whose mean could be calculated <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_snow.snow_cover`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snow_season_extremes -->

<!-- spec:snow_season_medians -->

<a id="spec-snow_season_medians"></a>

> **Mediany dat pierwszego i ostatniego dnia z pokrywą śnieżną** · wzór grupy B `snow_season_medians` (Tier B, CMP-2.2)
>
> **Definicja:** mediana pierwszego i ostatniego dnia z pokrywą śnieżną z kompletnych zim: każda data jako numer dnia sezonu w kalendarzu bez 29 lutego, a mediana tych numerów z powrotem zamieniona na datę (źr. 1)
>
> **Konwencja:** 29 lutego liczy się jako 28 lutego, więc data jest tym samym dniem w każdej zimie; mediana wypadająca między dwoma dniami jest zaokrąglana do parzystego numeru dnia
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Urban, G. (2015). Przegląd Geograficzny 87(3), pp. 498-499: the snow season from 1 August to 31 July, after Falarz — *źródło niedostępne publicznie (dostarczone przez autora)*
>
> Funkcja `hydrolog.statistics.meteo_snow.snow_cover`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snow_season_medians -->

### Przykład: zimy w Warszawie, 1991–2020

```bash
hydrolog meteo snow --input-file docs/podrecznik/dane/warszawa_okecie_snieg_1991_2020.csv
```

Z 30 pełnych zim 1991–2020 (pole `period`):

| Wielkość | Wartość |
|---|---|
| Średnia liczba dni z pokrywą (`mean_cover_days`) | 48,5 |
| Średnia największa grubość zimy (`mean_max_depth_cm`) | 18,7 cm |
| Największa grubość wielolecia (`max_depth_cm`, `max_date`) | 53 cm, 16 lutego 2010 r. |
| Mediana pierwszego dnia z pokrywą (`median_first_day`) | 25 listopada |
| Mediana ostatniego dnia z pokrywą (`median_last_day`) | 26 marca |
| Najwcześniejszy pierwszy dzień (`earliest_first_date`) | 15 października 2009 r. |
| Najpóźniejszy ostatni dzień (`latest_last_date`) | 20 kwietnia 1999 r. |
| Zimy bez pokrywy (`years_without_cover`) | 1 (zima 2019/2020) |

Zimy różnią się bardzo: zima 2005/2006 miała 111 dni z pokrywą, zima 2009/2010 – 81 dni i największą grubość
wielolecia, a zima 2019/2020 – ani jednego dnia z pokrywą. Normy IMGW-PIB 1991–2020 podają dla Warszawy średnio 48,0
dnia z pokrywą w roku kalendarzowym; drobna różnica wynika z innego podziału na lata. Plik nie ma grubości śniegu
świeżego, więc pola `mean_fresh_snow_cm` i `fresh_snow_cm` są puste.

## 11.14. Współczynnik hydrotermiczny Sielianinowa

**Idea.** Współczynnik hydrotermiczny Sielianinowa (*Selyaninov hydrothermal coefficient*, HTC) porównuje opad z sumą
temperatur, która zastępuje parowanie: mały współczynnik oznacza niedobór wody dla roślin. Sielianinow (1928) liczył
go dla okresu, w którym średnia temperatura dobowa trwale przekracza próg aktywnej wegetacji; w Polsce stosuje się
głównie wersję miesięczną dla miesięcy okresu wegetacyjnego (Skowera i Puła 2004; Skowera 2014). Wzór i klasy
Skowery i Puły podają ramki:

<!-- spec:sielianinov_coefficient -->

<a id="spec-sielianinov_coefficient"></a>

> **Współczynnik hydrotermiczny Sielianinowa dla miesiąca lub sezonu** · specyfikacja [`sielianinov_coefficient`](../FORMULAS.md#sielianinov_coefficient) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> k = \frac{P}{0{,}1\,\sum t}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P$ | `precipitation_mm` | Opad miesiąca lub sezonu | mm | [0; ∞) | nie podano w źródłach | [3,2; 535,2] (źr. 4) |
> | $\sum t$ | `temperature_sum_c_days` | Suma średnich dobowych temperatur z tych samych dni: średnia miesięczna pomnożona przez liczbę dni miesiąca albo suma z dni sezonu | °C·d | (−∞; ∞) | nie podano w źródłach | [150,8; 3297] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `coefficient` | Współczynnik hydrotermiczny | – | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | sum t > 0: miesiąc ze średnią powyżej 0 °C, sezon z ciepłym dniem | `a_positive_temperature_sum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | P / (0,1 sum t) jest liczbą skończoną: sum t nie jest znikomo mała w porównaniu z P | `a_finite_coefficient` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}1$ | `tenth` | Mnożnik sumy temperatur w mianowniku | 1/10 | mm/(°C·d) | (źr. 1) |
>
> **Konwencje**
>
> - liczony jako 10 P / sum t, z dokładnym czynnikiem 1 / 0,1
> - funkcja dla serii podaje sumę opadu miesiąca i średnią temperaturę pomnożoną przez liczbę jego dni (od kwietnia do września, średnia powyżej 0 °C) albo sumy z dni od kwietnia do września ze średnią powyżej 10 °C (Miś 2026; Tier B `hydrothermal_season`)
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik opadu i temperatury
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the monthly sum of the air temperatures above 0 °C, the monthly mean times the days <http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf>
> 2. Kulik, M., Baryła, R., Czarnecki, Z. and Bochniak, A. (2016). Warunki hydrotermiczne w centralnej części rejonu kanału Wieprz-Krzna w 50-leciu (1966-2015). Agronomy Science 71(3), 1-12, p. 2: the coefficient; Table 1, pp. 5-6: P, the mean temperature and k of April-September at Sosnowica <https://doi.org/10.24326/as.2016.3.1>
> 3. Selyaninov, G. T. (1928). O sel'skokhozyaystvennoy otsenke klimata. Trudy po sel'skokhozyaystvennoy meteorologii 20, 165-177, the coefficient; not opened here: as Skowera and Puła (2004) print it — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the precipitation of the months April to September and of the seasons of 1991-2020: 3.2 to 535.2 mm
> 5. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the sums of the months April to September and of the seasons of 1991-2020: 150.8 to 3297.0 °C·d
>
> Funkcja `hydrolog.statistics.meteo_hydrothermal.sielianinov_coefficient`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:sielianinov_coefficient -->

<!-- spec:sielianinov_class -->

<a id="spec-sielianinov_class"></a>

> **Klasa współczynnika hydrotermicznego Sielianinowa (Skowera i Puła)** · specyfikacja [`sielianinov_class`](../FORMULAS.md#sielianinov_class) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> k \le 0{,}4,\ (0{,}4, 0{,}7],\ (0{,}7, 1{,}0],\ (1{,}0, 1{,}3],\ (1{,}3, 1{,}6],\ (1{,}6, 2{,}0],\ (2{,}0, 2{,}5],\ (2{,}5, 3{,}0],\ > 3{,}0
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $k$ | `coefficient` | Współczynnik hydrotermiczny | – | [0; ∞) | nie podano w źródłach | [0,1; 5,27] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `sielianinov_class` (wybór) | Klasa, od najsuchszej | – | jedna z: `extremely_dry`, `very_dry`, `dry`, `fairly_dry`, `optimal`, `fairly_wet`, `wet`, `very_wet`, `extremely_wet` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}4$ | `extremely_dry_to` | Górna granica klasy skrajnie suchej | 0,4 | – | (źr. 1) |
> | $0{,}7$ | `very_dry_to` | Górna granica klasy bardzo suchej | 0,7 | – | (źr. 1) |
> | $1$ | `dry_to` | Górna granica klasy suchej | 1 | – | (źr. 1) |
> | $1{,}3$ | `fairly_dry_to` | Górna granica klasy dość suchej | 1,3 | – | (źr. 1) |
> | $1{,}6$ | `optimal_to` | Górna granica klasy optymalnej | 1,6 | – | (źr. 1) |
> | $2$ | `fairly_wet_to` | Górna granica klasy dość wilgotnej | 2 | – | (źr. 1) |
> | $2{,}5$ | `wet_to` | Górna granica klasy wilgotnej | 2,5 | – | (źr. 1) |
> | $3$ | `very_wet_to` | Górna granica klasy bardzo wilgotnej | 3 | – | (źr. 1) |
>
> **Konwencje**
>
> - każda granica należy do klasy poniżej niej, jak podaje źródło (k <= 0,4 – skrajnie sucho); tekst źródła mówi o dziesięciu klasach, a wymienia dziewięć
> - Miś (2026) oraz Chmist-Sikorska i in. (2022) stosują inne granice
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet <http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf>
> 2. Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the coefficients of the months April to September of 1991-2020: 0.10 to 5.27
>
> Funkcja `hydrolog.statistics.meteo_hydrothermal.sielianinov_class`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:sielianinov_class -->

**Miesiące i sezon w Hydrologu.** Hydrolog liczy współczynnik każdego miesiąca od kwietnia do września oraz
współczynnik sezonu: dni tych miesięcy ze średnią temperaturą powyżej progu, jak Miś (2026) i Chmist-Sikorska i in.
(2022). Klasycznego okresu Sielianinowa, między wiosennym a jesiennym trwałym przejściem temperatury przez próg,
Hydrolog nie liczy, bo żadne otwarte polskie źródło nie ustala reguły wyznaczania tych przejść (ADR-0044). Inni autorzy
(Chmist-Sikorska i in. 2022; Miś 2026) stosują też inne granice klas niż Skowera i Puła; podawaj, czyją klasyfikację
stosujesz.

<!-- spec:hydrothermal_months -->

<a id="spec-hydrothermal_months"></a>

> **Miesięczne współczynniki hydrotermiczne Sielianinowa** · wzór grupy B `hydrothermal_months` (Tier B, CMP-2.2)
>
> **Definicja:** `sielianinov_coefficient` każdego miesiąca od kwietnia do września: P – jego suma opadu, sum t – jego średnia dobowa temperatura pomnożona przez liczbę jego dni, dla miesiąca z obiema wartościami i średnią powyżej 0 °C (źr. 1)
>
> **Konwencja:** miesiące od kwietnia do września (Radzka 2014); sumy opadu zaokrąglane do 1e-6 mm
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and (c), pp. 7-8: a monthly mean needs fewer than 11 missing days and fewer than 5 in a row, a monthly sum every day or accumulated totals covering the missing days <https://library.wmo.int/idurl/4/55797>
>
> Funkcja `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hydrothermal_months -->

<!-- spec:hydrothermal_season -->

<a id="spec-hydrothermal_season"></a>

> **Sezonowy współczynnik hydrotermiczny Sielianinowa** · wzór grupy B `hydrothermal_season` (Tier B, CMP-2.2)
>
> **Definicja:** `sielianinov_coefficient` z dni od kwietnia do września ze średnią temperaturą powyżej 10 °C: P i sum t sumowane po tych dniach, w roku, w którym każdy dzień od kwietnia do września ma obie wartości (źr. 1)
>
> **Konwencja:** filtr dni z praktyki polskiej (Miś 2026), a nie okres między trwałymi przejściami temperatury przez 10 °C z praktyki rosyjskiej; opad zbiorczy liczy się jako dzień brakujący w sezonie
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Miś, F. (2026). Spatiotemporal variability of atmospheric drought during the growing season in Poland: a multi-index analysis based on SPEI, VPD, and HTC (1980-2024). Theoretical and Applied Climatology 157(12), 790, section 2, eq. 4: the days with a mean temperature above 10 °C, calculated for the April-September period
>
> Funkcja `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hydrothermal_season -->

<!-- spec:hydrothermal_period -->

<a id="spec-hydrothermal_period"></a>

> **Współczynniki hydrotermiczne Sielianinowa z wielolecia** · wzór grupy B `hydrothermal_period` (Tier B, CMP-2.2)
>
> **Definicja:** dla każdego miesiąca od kwietnia do września: średni współczynnik z lat, w których on istnieje, i liczba przypadków każdej klasy; średni współczynnik sezonowy i jego klasa (źr. 1)
>
> **Konwencja:** klasa średniej, a nie najczęstsza klasa
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet <http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf>
>
> Funkcja `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hydrothermal_period -->

**Typowy błąd.** Liczenie współczynnika dla miesięcy chłodnych: przy średniej temperaturze miesiąca bliskiej zera
nawet przeciętny opad daje ogromny współczynnik, który nie ma sensu agrometeorologicznego.

### Przykład: rok 2015 w Warszawie

```bash
hydrolog meteo hydrothermal --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

| Miesiąc 2015 r. | IV | V | VI | VII | VIII | IX | sezon (164 dni) |
|---|---|---|---|---|---|---|---|
| Współczynnik | 1,37 | 0,93 | 0,36 | 0,95 | 0,12 | 1,26 | 0,70 |
| Klasa | optymalny | suchy | skrajnie suchy | suchy | skrajnie suchy | dość suchy | suchy |

Czerwiec i sierpień 2015 r. były według tego wskaźnika skrajnie suche, a sierpień także według SPI (p. 11.9). Średni
współczynnik sezonu w latach 1991–2020 wynosi 1,15 (`period.mean_season_coefficient`, klasa dość sucha).

## Źródła

Źródła oznaczone „niedostępne” nie są w otwartym dostępie; ich treść znamy z cytowań w źródłach otwartych.

- Atlas klimatu Polski (2005), red. H. Lorenc. IMGW, Warszawa. Nie otwierano; definicję dnia przymrozkowego podaje
  ADR-0044.
- Bronaugh D. (2020) climdex.pcic 1.1-11: PCIC implementation of Climdex routines, pakiet R. https://cran.r-project.org/package=climdex.pcic
- Chmist-Sikorska J., Kępińska-Kasprzak M., Struzik P. (2022) Agricultural drought assessment on the base of
  Hydro-thermal Coefficient of Selyaninov in Poland. Italian Journal of Agrometeorology (1), 3–12.
- ClimPACT2: wskaźniki Expert Team on Sector-specific Climate Indices (ET-SCI). https://github.com/ARCCSS-extremes/climpact
- de Luis M., González-Hidalgo J.C., Brunetti M., Longares L.A. (2011) Precipitation concentration changes in Spain
  1946–2005. Natural Hazards and Earth System Sciences 11, 1259–1265.
- Dopke J. (2010) Obliczanie liczby stopniodni grzania według metody Eurostat.
  https://www.cire.pl/pliki/2/Dopke273blstometoeurostat1963129496.pdf
- ECA&D (2021) European Climate Assessment & Dataset, Algorithm Theoretical Basis Document, wersja 11. KNMI, De Bilt.
  https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf
- EDO (2025) Copernicus European Drought Observatory, Factsheet: Standardized Precipitation Index (SPI).
  https://drought.emergency.copernicus.eu/data/factsheets/factsheet_spi.pdf
- Edwards D.C., McKee T.B. (1997) Characteristics of 20th century drought in the United States at multiple time scales.
  Colorado State University, Climatology Report 97-2. Niedostępne; cytowane za Naresh Kumar i in. (2009).
- ETCCDI (2009) Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and
  Indices. https://etccdi.pacificclimate.org/list_27_indices.shtml
- Eurostat (2024) Energy statistics – cooling and heating degree days (nrg_chdd), metadane z 25 października 2024 r.;
  dyrektywa Komisji (UE) 2015/1127, załącznik. https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm
- Gąsiorek E., Musiał E. (2011) Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego
  opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107–119.
- Hydrolog, decyzje architektoniczne: ADR-0032 (grupa `meteo`), ADR-0033 (okres odniesienia norm), ADR-0044 (normy
  wielomiesięczne, ciągi, dni przymrozkowe, sezon hydrotermiczny), ADR-0059 (wskaźniki meteorologiczne według
  specyfikacji), katalog `docs/decisions/`.
- Hyndman R.J., Fan Y. (1996) Sample quantiles in statistical packages. The American Statistician 50(4), 361–365.
  Niedostępne.
- IMGW-PIB: Normy klimatyczne 1991–2020. https://klimat.imgw.pl
- IMGW-PIB: Jednolite serie danych (portal Klimat). https://klimat.imgw.pl
- IMGW-PIB (2023) Rocznik Meteorologiczny 2022 oraz opisy danych meteorologicznych w serwisie danych publicznych.
  https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/
- Kaczorowska Z. (1962) Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33.
  https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf
- Kossowska-Cezak U. (2014) Zmiany wieloletnie liczby termicznych dni charakterystycznych w Warszawie (1951–2010).
  Prace Geograficzne 136, 9–30.
- Łabędzki L. (2006): klasy SPI stosowane w Polsce; cytowane za Gąsiorek i Musiał (2011, tab. 2), pracy nie
  otwierano.
- Łabędzki L., Bąk B. (2004) Standaryzowany klimatyczny bilans wodny jako wskaźnik suszy. Acta Agrophysica 3(1),
  117–124.
- McKee T.B., Doesken N.J., Kleist J. (1993) The relationship of drought frequency and duration to time scales. 8th
  Conference on Applied Climatology, Anaheim, 179–184.
- Miś F. (2026) Spatiotemporal variability of atmospheric drought during the growing season in Poland: a multi-index
  analysis based on SPEI, VPD, and HTC (1980–2024). Theoretical and Applied Climatology 157(12), 790.
- Naresh Kumar M., Murthy C.S., Sesha Sai M.V.R., Roy P.S. (2009) On the use of Standardized Precipitation Index (SPI)
  for drought intensity assessment. Meteorological Applications 16(3), 381–389; wersja otwarta arXiv:1509.04808.
- Oliver J.E. (1980) Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300–309.
  Niedostępne.
- Selyaninov (Sielianinow) G.T. (1928) O sel'skokhozyaystvennoy otsenke klimata. Trudy po sel'skokhozyaystvennoy
  meteorologii 20, 165–177. Niedostępne.
- Skowera B. (2014) Zmiany warunków hydrotermicznych na obszarze Polski (1971–2010). Fragmenta Agronomica 31(2), 74–87.
- Skowera B., Puła J. (2004) Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach
  1971–2000. Acta Agrophysica 3(1), 171–177.
- Słownik meteorologiczny (2003). Nie otwierano; cytowany za Kossowska-Cezak (2014, s. 14).
- Strużewska J. i in. (2020) Raport skrócony: Zmiany temperatury i opadu na obszarze Polski w warunkach przyszłego
  klimatu do roku 2100 (KLIMADA 2.0). IOŚ-PIB, Warszawa.
- Sumner G., Homar V., Ramis C. (2001) Precipitation seasonality in eastern and southern coastal Spain. International
  Journal of Climatology 21, 219–247.
- Thom H.C.S. (1958) A note on the gamma distribution. Monthly Weather Review 86(4), 117. Niedostępne.
- Tomaszewska (1994): klasy miesięcznego opadu względnego; cytowane za Gąsiorek i Musiał (2011, tab. 1), pracy nie
  otwierano.
- Urban G. (2015) Zaleganie pokrywy śnieżnej i jego zmienność w polskiej części Sudetów i na ich przedpolu. Przegląd
  Geograficzny 87(3), 497–516.
- Walsh R.P.D., Lawler D.M. (1981) Rainfall seasonality: description, spatial patterns and change through time.
  Weather 36(7), 201–208. Niedostępne.
- WMO (2012) Standardized Precipitation Index User Guide. WMO-No. 1090, Genewa.
- WMO (2017) WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Genewa.
  https://library.wmo.int/idurl/4/55797
- WMO (2023) Guide to Instruments and Methods of Observation, t. I. WMO-No. 8, Genewa.
- Wypych A., Sulikowska A., Ustrnul Z., Czekierda D. (2017) Variability of growing degree days in Poland in response
  to ongoing climate changes in Europe. International Journal of Biometeorology 61, 49–59.
