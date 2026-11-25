# 8. Przepływy charakterystyczne i niżówki

Rozdział opisuje statystyki, którymi charakteryzuje się reżim ilościowy przekroju wodowskazowego na co
dzień, a nie tylko w czasie wezbrań: przepływy charakterystyczne pierwszego i drugiego stopnia, krzywą
sum czasów trwania przepływów, niżówki z ich czasem trwania i deficytem odpływu, rozkład minimów
rocznych, przepływ podstawowy i recesję oraz sygnatury hydrologiczne zbiorów CAMELS. Wszystkie te
wielkości liczy się z szeregu przepływów dobowych (albo z charakterystyk półrocznych IMGW-PIB)
w ustalonym okresie odniesienia, zwykle 30-letnim.

Przykłady dotyczą lat hydrologicznych 1991–2020 wodowskazu IMGW-PIB Świerzawa na Kaczawie (151150170),
w miejscowości, w której zamyka się zlewnia Kamiennika, oraz wodowskazu Bukowna na Czarnej Wodzie
(151160040) w dorzeczu Kaczawy. Pliki danych i warunki korzystania z nich opisuje
`docs/podrecznik/dane/README.md`. Rok hydrologiczny (XI–X) i sposób wyznaczania maksimów rocznych
omawia rozdział 7.

## 8.1. Przepływy charakterystyczne

### Pierwszy i drugi stopień

Przepływy charakterystyczne (ang. *characteristic discharges*) pierwszego stopnia to największy ($WQ$),
średni ($SQ$) i najmniejszy ($NQ$) przepływ miesiąca, półrocza (zimowego XI–IV, letniego V–X) albo roku
hydrologicznego (IMGW-PIB 2023). Drugi stopień opisuje wielolecie: pierwsza litera to statystyka
z wartości rocznych, druga — rodzaj wartości rocznej. $WWQ$ jest największym z maksimów rocznych,
$SWQ$ średnią maksimów rocznych, $SSQ$ średnią z przepływów średnich rocznych, $SNQ$ średnią minimów
rocznych, a $NNQ$ najmniejszym z minimów. Hydrolog podaje wszystkie dwanaście kombinacji, także
z medianą (litera Z, np. $ZNQ$) i pary mieszane ($WNQ$ — największe z minimów rocznych, $NWQ$ —
najmniejsze z maksimów). Dla stanu wody te same symbole kończą się literą W ($WWW$ … $NNW$), dla
temperatury wody literą T.

<!-- spec:characteristic_first_degree -->

<a id="spec-characteristic_first_degree"></a>

> **Wartości charakterystyczne I stopnia** · wzór grupy B `characteristic_first_degree` (Tier B, CMP-2.2)
>
> **Definicja:** Wartości I stopnia każdego roku hydrologicznego i jego półroczy z szeregu dobowego: minimum, średnia i maksimum z dni, które mają wartość; każde ekstremum jest datowane pierwszym dniem, w którym wystąpiło. (źr. 1)
>
> **Konwencja:** Zima XI–IV, lato V–X, rok XI–X. Ekstrema są ekstremami wartości dobowych, z reguły łagodniejszymi niż ekstrema IMGW-PIB ze wszystkich obserwacji (Kłodzko 2010: WQ 96,0 wobec 145 m³/s); rok z dniami bez wartości pozostaje, z tymi dniami, które ma, i jest wymieniony w `incomplete_years`, podczas gdy IMGW-PIB nie publikuje dla takiego okresu charakterystyk.
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `summer_first_month` | Pierwszy miesiąc półrocza letniego | 5 | mies. | (źr. 1) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7) <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/Rocznik%20hydrologiczny/Rocznik%20Hydrologiczny%202022.pdf>
>
> Funkcja `hydrolog.statistics.characteristic.calculate_characteristic_values`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:characteristic_first_degree -->

<!-- spec:characteristic_second_degree -->

<a id="spec-characteristic_second_degree"></a>

> **Wartości charakterystyczne II stopnia** · wzór grupy B `characteristic_second_degree` (Tier B, CMP-2.2)
>
> **Definicja:** Wartości II stopnia roku i każdego półrocza: największa (W), średnia (S), mediana (Z) i najmniejsza (N) z wielolecia spośród maksimów, średnich i minimów I stopnia (WWQ ... NNQ), każda z tych lat, które daną wartość mają. (źr. 1)
>
> **Konwencja:** SWQ to średnia z maksimów rocznych, nigdy z połączonych maksimów półroczy; mediany (ZWQ, ZSQ, ZNQ) oraz WSQ, NSQ, WNQ, NWQ tworzy się według schematu Byczkowskiego (1996, źródło dostarczone przez autora); W, S, N stanu wody to WWW ... NNW, a temperatury wody WWT ... NNT.
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7) <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/Rocznik%20hydrologiczny/Rocznik%20Hydrologiczny%202022.pdf>
>
> Funkcja `hydrolog.statistics.characteristic.calculate_characteristic_values`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:characteristic_second_degree -->

Przepływ średni niski $SNQ$ (ang. *mean annual minimum flow*) ma także definicję prawną: to średnia
arytmetyczna z minimalnych rocznych przepływów z wielolecia (Dz.U. 2026 poz. 692, § 4 pkt 10). Jest
podstawą opłat za pobór wód powierzchniowych według Prawa wodnego, które wymaga ciągu co najmniej
dwudziestoletniego; zespół IMGW-PIB zaleca 30-lecie jednakowe dla całej Polski, przesuwane co rok
o jeden rok (Ozga-Zieliński i Walczykiewicz red. 2022).

### Szereg dobowy a charakterystyki IMGW-PIB

IMGW-PIB wyznacza ekstrema ze wszystkich dostępnych pomiarów i obserwacji (IMGW-PIB 2023), a nie
z przepływów średnich dobowych, i nie publikuje charakterystyk okresu z przerwą w obserwacjach.
Polecenie `hydrolog stats characteristic` liczy więc dwie różne rzeczy, zależnie od danych:

- z szeregu dobowego (`--input-file` z `--date-column`) — ekstrema średnich dobowych, z reguły
  łagodniejsze od ekstremów IMGW-PIB (maksima niższe, minima wyższe); rok z brakami zostaje w obliczeniu
  z dniami, które ma, i jest wymieniony w uwadze `years_with_missing_days`;
- z charakterystyk półrocznych IMGW-PIB (`--half-year-file`) — opublikowane wartości półroczy,
  a z nich maksimum i minimum roku:

<!-- spec:characteristic_from_half_years -->

<a id="spec-characteristic_from_half_years"></a>

> **Wartości charakterystyczne z opublikowanych charakterystyk półroczy** · wzór grupy B `characteristic_from_half_years` (Tier B, CMP-2.2)
>
> **Definicja:** Wartości I stopnia z charakterystyk półroczy publikowanych przez IMGW-PIB: półrocza zachowują swoje minimum, średnią i maksimum z datami; maksimum roczne to większe z maksimów półroczy, a minimum roczne mniejsze z minimów, z datą z tego półrocza; średnia roczna to wartość opublikowana. (źr. 1)
>
> **Konwencja:** Przy równości przyjmuje się wartość zimową; ekstremum roczne przy brakującym półroczu (przerwa w obserwacjach) jest nieznane; rok bez żadnej wartości jest pomijany; wartości II stopnia jak z szeregu dobowego.
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), PLWSKP 13 winter half-year XI-IV, 14 summer half-year V-X, 15 year; PLWSKEX 1 minimum, 2 mean, 3 maximum; a value 99999.999 or NULL is a break in observations <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/polroczne_i_roczne/POLR_publiczne_format.txt>
>
> Funkcja `hydrolog.statistics.characteristic.characteristic_values_from_half_years`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:characteristic_from_half_years -->

Typowe błędy: porównywanie ekstremów dobowych z ekstremami IMGW-PIB bez zaznaczenia różnicy; liczenie
$SWQ$ ze wszystkich maksimów półroczy zamiast z maksimów rocznych; pozostawienie w wieloleciu roku
z brakami bez sprawdzenia, czy brak nie objął wezbrania albo niżówki; okres odniesienia krótszy niż
30 lat bez zaznaczenia (Hydrolog dołącza wtedy uwagę `short_reference_period`).

### Przykład 8.1: Kaczawa — Świerzawa, 1991–2020

Charakterystyki z przepływów średnich dobowych:

```sh
hydrolog stats characteristic --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020
```

i z charakterystyk półrocznych IMGW-PIB:

```sh
hydrolog stats characteristic --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv --first-year 1991 --last-year 2020
```

| Przepływ [m³/s] | z przepływów dobowych | z charakterystyk IMGW-PIB |
|---|---|---|
| $WWQ$ | 92,7 (20.07.1997) | 152 (20.07.1997) |
| $SWQ$ | 18,69 | 31,38 |
| $ZWQ$ | 11,7 | 15,0 |
| $NWQ$ | 4,71 | 7,18 |
| $WSQ$ | 2,01 | 2,01 |
| $SSQ$ | 1,162 | 1,161 |
| $ZSQ$ | 1,119 | 1,12 |
| $NSQ$ | 0,612 | 0,61 |
| $WNQ$ | 0,63 | 0,58 |
| $SNQ$ | 0,323 | 0,292 |
| $ZNQ$ | 0,28 | 0,25 |
| $NNQ$ | 0,10 (27.07.1993) | 0,08 (3.08.1993) |

Przepływy średnie obu źródeł są prawie równe, ekstrema nie: kulminacja z lipca 1997 r. wynosiła 152 m³/s,
a największa średnia dobowa 92,7 m³/s; $SWQ$ z kulminacji jest o dwie trzecie większe niż z dobowych.
Minima IMGW-PIB są niższe od minimów dobowych, więc $SNQ$ z charakterystyk IMGW-PIB jest o 10 % mniejszy.
Do porównań z publikacjami IMGW-PIB i do celów prawnych właściwe są charakterystyki IMGW-PIB.

Charakterystyki półroczy pokazują reżim: średnia maksimów letnich (dobowe: $SWQ$ = 15,9 m³/s) jest
prawie dwukrotnie większa niż zimowych (8,75 m³/s), a $SNQ$ lata (0,343 m³/s) mniejszy niż zimy
(0,441 m³/s). Największe wezbrania i najgłębsze niżówki zdarzają się tu latem.

## 8.2. Krzywa sum czasów trwania przepływów

Krzywa sum czasów trwania przepływów wraz z wyższymi (ang. *flow duration curve*) podaje, przez jaki
procent dni przepływ był równy danej wartości lub od niej wyższy. $Q_{90\%}$ to przepływ osiągany lub
przekraczany przez 90 % dni okresu. Krzywa jest opisem okresu obserwacji, a nie rozkładem
prawdopodobieństwa: dni nie są niezależne, a sezonowość i susze kilku lat decydują o jej dolnej części.

<!-- spec:exceedance_values -->

<a id="spec-exceedance_values"></a>

> **Wartości krzywej sum czasów trwania osiągane lub przekraczane przez p % dni (pozycje Weibulla, interpolacja liniowa)** · specyfikacja [`exceedance_values`](../FORMULAS.md#exceedance_values) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_p = q_{(i)} + \theta\,\bigl(q_{(i+1)} - q_{(i)}\bigr),\quad i = \left\lfloor \tfrac{(n+1)\,p}{100} \right\rfloor,\quad \theta = \tfrac{(n+1)\,p}{100} - i,\quad q_{(1)} \ge \dots \ge q_{(n)}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $q$ | `values` (ciąg) | Wartości dobowe szeregu, w dowolnej kolejności; NaN w dniu bez wartości, który jest pomijany | m³/s | (−∞; ∞) | nie podano w źródłach | [1,24; 522] (źr. 3) |
> | $p$ | `exceedance_percent` (ciąg) | Procenty dni, w których wartość jest osiągana lub przekraczana | % | (0; 100) | nie podano w źródłach | [0,1; 99,9] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_p$ | `exceedance_values` (ciąg) | Wartość osiągana lub przekraczana w każdym z podanych procentów dni, w jednostce szeregu | m³/s | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 1: co najmniej jeden dzień z wartością | `has_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
>
> **Konwencje**
>
> - p to procent przewyższenia: udział dni z wartością, w których wartość jest osiągana lub przekraczana (krzywa sum czasów trwania wraz z wyższymi); Q_p to (100 - p)-ty percentyl wartości
> - pozycja wykreślna Weibulla m / (n + 1) wartości o randze m liczonej od największej, z interpolacją liniową między pozycjami: Q_p,2 Vogela i Fennesseya (1994, wzór 3), metoda R6 Hyndmana i Fana (NIST e-Handbook 7.2.6.2), metoda 'weibull' w numpy i typ 6 funkcji quantile w R
> - poza skrajnymi pozycjami 100 / (n + 1) i 100 n / (n + 1) % przyjmuje się wartości skrajne, tak jak R6 przypisuje k = 0 minimum, a k >= N maksimum; Vogel i Fennessey nie definiują Q_p,2 przed pierwszą pozycją i zalecają interpolację do q(n+1) = 0 za ostatnią, czego Hydrolog nie robi
> - nie jest to metoda klas Searcy'ego (1959) i WMO-No. 1029 (§ 6.1), w której udział klasy wynosi i / N, ani Qxx z pakietu lfstat (typ 7 funkcji quantile w R)
> - wartości równe (wiązane) zachowują każda swoją pozycję, a zera są wartościami; dzień bez wartości (NaN) jest pomijany, n liczy dni z wartością
> - szereg w dowolnej jednostce: wartości krzywej w tej samej jednostce (m³/s w dokumentach, cm dla stanów wody)
> - interpolację wykonuje się na wartościach podzielonych przez potęgę dwójki, tak aby różnica dwóch wartości bliskich największej liczbie zmiennoprzecinkowej nie powodowała przepełnienia
>
> **Założenia**
>
> - wartości pochodzą z jednej stacji i jednego okresu: krzywa opisuje ten okres (krzywa z całego okresu obserwacji według Vogela i Fennesseya), a nie klimat
> - niezależność dni nie jest wymagana: krzywa ma charakter opisowy i nie ma przedziału ufności; ma go stojąca obok niej medianowa krzywa roczna, której lata uznaje się za niezależne (specyfikacja duration_curve_annual_median_interval)
>
> **Zgodność z obserwacjami według źródeł:** brak: estymacja nieparametryczna z samego obserwowanego szeregu; Vogel i Fennessey (1994) porównują jej własności próbkowe, a nie zgodność z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Vogel, R.M. and Fennessey, N.M. (1994). Flow-duration curves. I: New interpretation and confidence intervals. Journal of Water Resources Planning and Management 120(4), 485-504 (the authors' copy), pp. 488-489, eqs. (2a) and (3): Q_p,2 = (1 - theta) q(i) + theta q(i+1) with i = [(n + 1) p] and theta = (n + 1) p - i, the ordered observations q(i) plotted at the Weibull position p_i = i / (n + 1) <https://sites.tufts.edu/richardvogel/files/2019/04/flowDuration1.pdf>
> 2. NIST/SEMATECH (2012). e-Handbook of Statistical Methods, section 7.2.6.2, Percentiles, p (N + 1) = k + d: Y(p) = Y[k] + d (Y[k+1] - Y[k]) for 0 < k < N, Y[1] for k = 0 and Y[N] for k >= N, method R6 of Hyndman and Fan (1996); the example of twelve resistivities, 90th percentile 95.1981 ohm.cm <https://www.itl.nist.gov/div898/handbook/prc/section2/prc262.htm>
> 3. IMGW-PIB, public hydrological data: the half-yearly characteristic flows (polr_Q) of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 (1997 absent), the lowest flow NNQ 1.24 m3/s (2015) and the highest WWQ 522 m3/s (2006), between which its daily mean flows lie <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 4. Hydrolog's duration curve: CURVE_PERCENTS of hydrolog.statistics.duration, the percentages of every drawn curve, and the table's DEFAULT_PERCENTS; the thresholds Q70, Q90 and Q95 of Polish low-flow studies (Tokarczyk 2010, p. 32; Tomaszewski 2012, p. 68) lie between, 0.1 to 99.9 %
>
> Funkcja `hydrolog.statistics.duration.exceedance_values`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:exceedance_values -->

Hydrolog liczy wartości krzywej metodą pozycji (Vogel i Fennessey 1994): $n$ wartości dobowych
uporządkowanych malejąco dostaje pozycje Weibulla, a wartość dla dowolnego procentu interpoluje się
liniowo między sąsiednimi pozycjami. Klasyczna metoda klas (Searcy 1959; WMO 2008, § 6.1) dzieli wartości
na przedziały i sumuje dni od klasy najwyższej; Hydrolog podaje ją obok, jako tabelę klas z sumami dni
„wraz z wyższymi” i „wraz z niższymi” oraz klasą modalną (najczęstszą). Dla długich szeregów obie metody
dają prawie te same wartości; różnią się w skrajnych procentach i w krótkich szeregach.

<!-- spec:duration_curve_days -->

<a id="spec-duration_curve_days"></a>

> **Dni ujęte w krzywej sum czasów trwania** · wzór grupy B `duration_curve_days` (Tier B, CMP-2.2)
>
> **Definicja:** dni, z których liczy się krzywą i klasy: wszystkie dni z wartością albo tylko dni jednego miesiąca kalendarzowego (`month`); ich liczba `n_values`, minimum, maksimum, średnia i mediana, krzywa w punktach `CURVE_PERCENTS` i tabela dla `exceedance_percents` (specyfikacja `exceedance_values`) oraz lata hydrologiczne tych dni (1 listopada – 31 października, nazwane rokiem ich końca): `first_year`, `last_year` i `period_years` (źr. 1)
>
> **Konwencja:** krzywa z całego okresu, ze wszystkich dni zapisu (Searcy 1959, s. 3; WMO-No. 1029, § 6.1); dzień, którego wartość jest NaN lub nie jest liczbą skończoną, nie ma wartości i jest pomijany, a nie uzupełniany; krzywa miesiąca obejmuje ten miesiąc kalendarzowy z każdego roku; daty ściśle rosną, jedna wartość na dobę
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology, Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 3: the total-period method, the days of each class cumulated from the highest class; figs. 4-5 (form 9-217c), p. 9: the days equal to or greater than a class limit and less than the next <https://pubs.usgs.gov/wsp/1542a/report.pdf>
>
> Funkcja `hydrolog.statistics.duration.duration_curve`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:duration_curve_days -->

<!-- spec:duration_classes -->

<a id="spec-duration_classes"></a>

> **Klasy wartości i liczby dni w klasach krzywej sum czasów trwania** · wzór grupy B `duration_classes` (Tier B, CMP-2.2)
>
> **Definicja:** klasy o równej szerokości w, [k w, (k + 1) w), od wielokrotności w równej najmniejszej wartości lub leżącej poniżej niej do klasy wartości największej, albo `bin_count` klas o równych krokach log10 między najmniejszą wartością dodatnią a największą, których skrajnymi granicami są te wartości i które liczą tylko wartości dodatnie; wartość v należy do klasy, dla której lower <= v < upper, przy czym klasa najwyższa obejmuje też swoją górną granicę; dla każdej klasy, od najwyższej w dół: jej dni, ich udział w liczonych dniach [%], dni tej klasy i wszystkich wyższych (wraz z wyższymi) oraz tej klasy i wszystkich niższych (wraz z niższymi), a także jej dni w poszczególnych miesiącach hydrologicznych, od listopada do października; klasa modalna ma najwięcej dni, a przy równych liczebnościach jest nią najniższa z nich (źr. 1)
>
> **Konwencja:** dni liczone od klasy najwyższej w dół, przy czym klasa obejmuje dni równe jej dolnej granicy lub większe od niej i mniejsze od granicy następnej (Searcy 1959, rys. 4–5); granice klas o równej szerokości oblicza się w arytmetyce dziesiętnej na najkrótszych zapisach dziesiętnych wartości i szerokości, tak że wartość zapisana na granicy klasy rozpoczyna swoją klasę (0,3 przy szerokości 0,1 należy do [0,3; 0,4); ADR-0048); granicami są liczby zmiennoprzecinkowe najbliższe tym granicom
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology, Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 3: the total-period method, the days of each class cumulated from the highest class; figs. 4-5 (form 9-217c), p. 9: the days equal to or greater than a class limit and less than the next <https://pubs.usgs.gov/wsp/1542a/report.pdf>
>
> Funkcja `hydrolog.statistics.duration.duration_curve`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:duration_classes -->

Klasy o równej szerokości nadają się do stanów wody (np. co 10 cm). Rozkład przepływów jest silnie
skośny, więc klasy równej szerokości wrzucają prawie wszystkie dni do najniższej klasy; dla przepływów
należy wybrać klasy logarytmiczne (`--bin-method log`). Krzywą jednego miesiąca kalendarzowego
z wszystkich lat daje opcja `--month`.

Zastosowania: przepływy niskie i średnie z krzywej ($Q_{70\%}$, $Q_{90\%}$, $Q_{95\%}$) jako progi
niżówek (p. 8.3) i wskaźniki zasobów, porównanie zlewni (krzywa stroma — reżim zmienny, płaska — wyrównany
przez retencję), ocena, przez ile dni w roku dostępny jest przepływ potrzebny do poboru wody.

### Medianowa krzywa roczna i jej przedział ufności

Krzywa z całego okresu nie ma przedziału ufności, bo dni nie są niezależne. Vogel i Fennessey (1994)
stawiają obok niej interpretację roczną: krzywą każdego pełnego roku hydrologicznego, liczoną z dni tego
roku, i dla każdego procentu medianę $N$ wartości rocznych, czyli medianową krzywą roczną, krzywą
typowego roku. Lata, w przeciwieństwie do dni, można uznać za niezależne, więc mediana ma przedział
ufności ze statystyk pozycyjnych (Helsel i Hirsch 2002, § 3.3.1): $k$-tą najmniejszą i $k$-tą
największą z $N$ wartości rocznych, z największym $k$, przy którym prawdopodobieństwo dwumianowe objęcia
mediany wynosi co najmniej $c$. Przedział nie zależy od rozkładu wartości rocznych. Wymaga co najmniej
6 pełnych lat przy poziomie 0,95 i 3 przy 0,68; przy mniejszej liczbie lat wynik ma uwagę
`interval_not_computed` (przyczyna `too_few_complete_years`). Polecenie `stats duration-curve` podaje
medianową krzywą roczną w polu `annual_median_values`, a jej przedział w `intervals` (`ci_method`
`order_statistics`), oba w punktach `curve_exceedance_percents`; poziomy wybiera `--confidence-level`
(domyślnie 0,95, także lista, np. `0.95,0.68`).

Nie jest to wzór (10) Vogela i Fennesseya: jego granice, kwantyle samych wartości rocznych, opisują
rozrzut wartości jednego roku, a nie niepewność mediany, i nie zwężają się wraz z liczbą lat.

<!-- spec:duration_curve_annual_median_interval -->

<a id="spec-duration_curve_annual_median_interval"></a>

> **Medianowa roczna krzywa sum czasów trwania i jej przedział ufności ze statystyk pozycyjnych (pokrycie dwumianowe, lata niezależne)** · specyfikacja [`duration_curve_annual_median_interval`](../FORMULAS.md#duration_curve_annual_median_interval) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_{p,0{,}5} = \tfrac{1}{2}\bigl(Q_{p,(\lfloor (N+1)/2 \rfloor)} + Q_{p,(\lceil (N+1)/2 \rceil)}\bigr),\quad \bigl[Q_{p,(k)},\ Q_{p,(N+1-k)}\bigr],\quad k = \max\Bigl\{k \ge 1 : 1 - 2\sum_{j=0}^{k-1}\binom{N}{j}\,2^{-N} \ge c\Bigr\}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_p(i)$ | `annual_values` (tablica) | Wartości krzywych rocznych: wiersz na każdy pełny rok hydrologiczny i, w dowolnej kolejności, kolumna na każdy procent przewyższenia p (Q_p(i) Vogela i Fennesseya, każda z dni swojego roku) | m³/s | (−∞; ∞) | nie podano w źródłach | [1,24; 522] (źr. 3) |
> | $c$ | `confidence_levels` (ciąg) | Poziomy ufności, różne: każdy przedział jest dwustronny i centralny, każdy ogon najwyżej (1 - c) / 2 | – | (0; 1) | nie podano w źródłach | [0,68; 0,95] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_{p,0{,}5}$ | `median` (ciąg) | Medianowa krzywa roczna: dla każdego procentu mediana N wartości rocznych, w jednostce szeregu | m³/s | (−∞; ∞) |
> | $Q_{p,(k)}$ | `lower` (ciąg) | Dolna granica każdej mediany, wiersz na poziom w podanej kolejności: k-ta najmniejsza wartość roczna; luka tam, gdzie N lat nie osiąga poziomu | m³/s | (−∞; ∞) |
> | $Q_{p,(N+1-k)}$ | `upper` (ciąg) | Górna granica: k-ta największa wartość roczna; luka jak w dolnej | m³/s | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | poziomy ufności są różne | `distinct_levels` | odmowa obliczeń: wzór jest nieokreślony | (źr. 4) |
>
> **Konwencje**
>
> - dwustronny i centralny przy każdym poziomie ufności c: statystyki pozycyjne Q_p(k) i Q_p(N + 1 - k) N wartości rocznych danego procentu, k-ta od każdego końca, z największym k >= 1, którego pokrycie 1 - 2 F(k - 1) wynosi co najmniej c, F to dystrybuanta rozkładu dwumianowego N prób z prawdopodobieństwem 1/2 (lata poniżej prawdziwej mediany): każdy ogon najwyżej (1 - c) / 2 (Helsel i Hirsch 2002, wzory 3.2–3.3)
> - statystyki pozycyjne, niezależne od rozkładu: pokrycie jest dokładne dla ciągłego rozkładu wartości rocznych; nie jest to wzór (10) Vogela i Fennesseya (1994, s. 497), którego granice, kwantyle alfa/2 i 1 - alfa/2 Q_p,2 n wartości rocznych, obejmują wartość jednego roku, a nie medianę, i nie zwężają się wraz ze wzrostem n
> - pokrycie porównuje się z c dokładnie, w liczbach całkowitych: poziom równy pokryciu przyjmuje jego parę (c = 0,75 przy N = 3: wartość najmniejsza i największa); Helsel i Hirsch (2002, s. 71) biorą ogon najbliższy (1 - c) / 2, co może zostawić pokrycie poniżej c
> - poziom, którego nie osiąga nawet k = 1, 1 - 2^(1 - N) < c (mniej niż 6 lat przy c = 0,95, 5 przy 0,90, 3 przy 0,68), nie ma granic: jego wiersze lower i upper są lukami, a duration_curve podaje jego przedział jako niewyznaczony, z komunikatem interval_not_computed (too_few_complete_years)
> - mediana nieparzystej liczby wartości to wartość środkowa, parzystej — średnia dwóch środkowych, liczona jako suma ich połówek, tak aby wartości bliskie największej liczbie zmiennoprzecinkowej nie powodowały przepełnienia: Q_0.5,2 ze wzoru (3) Vogela i Fennesseya i numpy.median
> - wartości równe: równe wartości roczne zachowują każda swoją rangę; przy wartościach równych pokrycie wynosi co najmniej dwumianowe, bo P(Q < M) <= 1/2 <= P(Q <= M) w medianie M
> - luki: brak; wartości roczne to krzywe pełnych lat hydrologicznych (Tier B annual_duration_curves), a luka jest odrzucana
> - wartości w dowolnej jednostce: mediana i granice w tej samej jednostce (m3/s w dokumentach, cm dla stanów wody)
> - wszystkie poziomy jednego wywołania z jednego sortowania wartości każdego procentu; wiersze lower i upper następują w podanej kolejności poziomów
>
> **Założenia**
>
> - N wartości rocznych danego procentu jest niezależnych i ma jednakowy rozkład: lata uznaje się za niezależne, tak jak Vogel i Fennessey (1994, s. 496) traktują n wartości Q_p(i) jako próbę losową; autokorelacja kolejnych lat, np. przy suszach trwających kilka lat, obniżyłaby pokrycie poniżej c
> - przedział dotyczy medianowej krzywej rocznej, krzywej typowego roku (Vogel i Fennessey 1994, s. 496), a nie krzywej z całego okresu (specyfikacja exceedance_values), która przedziału nie ma
>
> **Zgodność z obserwacjami według źródeł:** brak: przedział estymatora; jego pokrycie, symulowane z wartości rocznych o rozkładzie logarytmiczno-normalnym przy 30 i 60 latach, podaje się pod wzorem (CMP-6.11)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Vogel, R.M. and Fennessey, N.M. (1994). Flow-duration curves. I: New interpretation and confidence intervals. Journal of Water Resources Planning and Management 120(4), 485-504 (the authors' copy), pp. 494-497: 'Annual Interpretation of Flow-Duration Curves', the FDC of each of the n years from its own daily flows by Q_p,2 and, per exceedance probability, the median of the n annual values, the median annual FDC (p. 494), the distribution of daily flow in a typical year (p. 496); 'Confidence Intervals for Quantiles of Flow-Duration Curves', the n values Q_p(i) treated as a random sample (p. 496) and their interval, eqs. (10a)-(10b) (p. 497) <https://sites.tufts.edu/richardvogel/files/2019/04/flowDuration1.pdf>
> 2. Helsel, D.R. and Hirsch, R.M. (2002). Statistical Methods in Water Resources. Techniques of Water-Resources Investigations of the U.S. Geological Survey, book 4, chapter A3 (superseded by Techniques and Methods 4-A3, 2020), sect. 3.3.1, pp. 70-72, eqs. 3.2-3.3: the nonparametric interval of the median between the R_l-th observations from each end, R_l = x' + 1 and R_u = n - x', x' the critical value of the binomial distribution with p = 0.5 at alpha/2 (table B5); example 2, 25 arsenic concentrations: 4.8 <= C_0.5 <= 110 at alpha = 0.044 <https://pubs.usgs.gov/twri/twri4a3/twri4a3.pdf>
> 3. IMGW-PIB, public hydrological data: the half-yearly characteristic flows (polr_Q) of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 (1997 absent), the lowest flow NNQ 1.24 m3/s (2015) and the highest WWQ 522 m3/s (2006), between which its daily mean flows lie <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 4. Nogat (2026). Decisions of the ecosystem, ECO-091: Intervals beside point estimates, computed by Hydrolog, shown by Obserwator, two-sided and central at each confidence_level asked; Obserwator stores 0.95 and 0.68 <https://github.com/Daldek/Nogat/blob/main/standards/DECISIONS.md>
>
> Funkcja `hydrolog.statistics.duration.annual_median_interval`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:duration_curve_annual_median_interval -->

### Przykład 8.2: krzywa czasu trwania, Świerzawa 1991–2020

```sh
hydrolog stats duration-curve --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020 --bin-method log
```

| $p$ [% dni] | 1 | 5 | 10 | 30 | 50 | 70 | 90 | 95 | 99 |
|---|---|---|---|---|---|---|---|---|---|
| $Q_{p\%}$ [m³/s] | 8,26 | 3,12 | 2,10 | 1,06 | 0,70 | 0,55 | 0,32 | 0,26 | 0,18 |

Krzywa obejmuje 10 958 dni. Mediana przepływu (0,70 m³/s) jest znacznie niższa od średniej (1,162 m³/s),
a średnia jest przekraczana przez mniej niż 30 % dni: kilka wezbrań w roku przenosi dużą część odpływu.
$Q_{70\%}$ = 0,55 m³/s posłuży jako próg niżówki w p. 8.3. Najliczniejsza z 40 klas logarytmicznych
obejmuje przepływy od 0,655 do 0,776 m³/s (1356 dni, 12,4 %). To samo polecenie bez `--bin-method log`
tworzy klasy szerokości 10 m³/s, z których najniższa obejmuje 99,3 % dni — tabela klas jest wtedy
bezużyteczna, choć wartości krzywej są te same.

Medianowa krzywa roczna tych 30 lat (to samo polecenie z `--confidence-level 0.95,0.68`; pola
`annual_median_values` i `intervals`, odczytane w procentach tabeli):

| $p$ [% dni] | 1 | 5 | 10 | 30 | 50 | 70 | 90 | 95 | 99 |
|---|---|---|---|---|---|---|---|---|---|
| mediana roczna [m³/s] | 8,31 | 2,92 | 2,06 | 1,10 | 0,70 | 0,53 | 0,40 | 0,35 | 0,31 |
| przedział 95 % [m³/s] | 5,15–10,20 | 2,56–3,38 | 1,66–2,33 | 0,92–1,20 | 0,61–0,79 | 0,40–0,63 | 0,31–0,53 | 0,26–0,50 | 0,23–0,46 |

W środkowym zakresie (10–70 %) medianowa krzywa roczna prawie pokrywa się z krzywą z całego okresu;
w niskich przepływach jest wyraźnie wyższa ($Q_{95\%}$ typowego roku 0,35 m³/s wobec 0,26 m³/s), bo krzywa
z całego okresu zbiera dni najsuchszych lat, których typowy rok nie ma. Przy 30 latach granicami
przedziału 95 % są 10. i 21. wartość roczna (pokrycie 0,957), a przedziału 68 % 12. i 19. (pokrycie 0,800).

## 8.3. Niżówki: metoda progowa, czas trwania i deficyt

Niżówka (ang. *low-flow event*, *streamflow drought*) to okres, w którym przepływ jest niższy od
przyjętego przepływu granicznego (IMGW-PIB, Słownik dla mediów). Metoda progowa (ang. *threshold level
method*; WMO 2008, rozdz. 8; Tallaksen i van Lanen 2004) opisuje każde zdarzenie początkiem, końcem,
czasem trwania, przepływem najniższym i deficytem (niedoborem) odpływu (ang. *deficit volume*), czyli
objętością wody, której zabrakło do progu. Dwa zdarzenia rozdzielone krótką przerwą (kilka dni
z przepływem powyżej progu) są zwykle jednym zjawiskiem, dlatego się je łączy (ang. *pooling*), a bardzo
krótkie zdarzenia pomija.

<!-- spec:threshold_runs -->

<a id="spec-threshold_runs"></a>

> **Ciągi dni poza progiem i ich łączenie** · wzór grupy B `threshold_runs` (Tier B, CMP-2.2)
>
> **Definicja:** ciągi kolejnych dni oznaczonych jako leżące poza progiem; dwa ciągi rozdzielone mniej niż `max_gap_days` dniami (bez wartości lub nieleżącymi poza progiem) łączy się w jeden, razem z dniami między nimi; ciągi krótsze niż `min_duration_days`, liczone z dołączonymi dniami, są odrzucane; każdy ciąg to pozycje jego pierwszego i ostatniego dnia, włącznie, w porządku czasowym (źr. 1)
>
> **Konwencja:** łączenie metodą czasu między zdarzeniami (inter-event time): ciągi łączy się, gdy przerwa jest krótsza niż t_min = `max_gap_days` dni (WMO-No. 1029, s. 72; `pool_it` z pakietu lfstat, 'inter-event time is less than tmin'), podczas gdy Fleig i in. (2006) piszą tau_i <= t_c we wzorze, wbrew „mniej niż” w tekście; `max_gap_days` 4 łączy przerwy od 1 do 3 dni, tak jak program NIŻÓWKA łączy niżówki przedzielone 3 dniami (Tokarczyk 2010, s. 34), a Tomaszewski (2012, s. 68–69) przerwy co najwyżej 3-dniowe; czas trwania połączonego ciągu obejmuje przerwę, jak pełny czas trwania suszy u Fleiga i in. (2006, wzór 1) i duration w lfstat, natomiast WMO-No. 1029 (wzór 8.1(a)), NIŻÓWKA (Tokarczyk 2010, s. 34) i Tomaszewski (2012, rys. 14) sumują czasy trwania ciągów bez przerwy (rzeczywisty czas trwania, `days_beyond` w `threshold_events`); minimalny czas trwania stosuje się do pełnego czasu trwania po połączeniu (Fleig i in. stosują d_min do rzeczywistego); 0 nie łączy niczego
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.), sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the threshold and ends as soon as it returns above it, with its duration, volume, minimum flow and time of occurrence; the IT method pools deficits that occur less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 (eqs. 8.1) <https://library.wmo.int/idurl/4/32176>
>
> Funkcja `hydrolog.statistics.events.threshold_runs`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:threshold_runs -->

<!-- spec:low_flow_sequences -->

<a id="spec-low_flow_sequences"></a>

> **Niżówki wyznaczane metodą progową** · wzór grupy B `low_flow_sequences` (Tier B, CMP-2.2)
>
> **Definicja:** przepływy umieszczone w kalendarzu ich dat; ciągi dni z wartością poniżej progu T, Q < T (`threshold_runs`, domyślnie `min_duration_days` 5 i `max_gap_days` 4); dla każdej niżówki: czas trwania w dniach kalendarzowych (łącznie z dniami przerw), minimum i średnia z jej dni z wartością, niedobór (deficyt) sum(max(T - Q, 0)) po jej dniach z wartością w jednostce szeregu pomnożonej przez dobę, jej dni bez wartości oraz to, czy dzień przed nią (po niej) nie ma wartości; suma niedoborów, najdłuższy czas trwania i liczba niżówek (źr. 1)
>
> **Konwencja:** poniżej oznacza Q < T, jak podają WMO-No. 1029 (s. 71) i słownik IMGW-PIB (hasło 29, „niższe od”), a nie Q <= T według Yevjevicha u Tokarczyka (2010, s. 33) ani według lfstat; niedobór połączonej niżówki jest sumą niedoborów jej ciągów, bez odejmowania nadwyżki dni między nimi (Fleig i in. 2006, wzór 2; WMO-No. 1029, wzór 8.1(b); vbt w lfstat, podczas gdy volume w lfstat ją odejmuje); dzień bez wartości nie dodaje niedoboru i jest dniem przerwy; wartości domyślne to minimum 5 dni programu NIŻÓWKA i łączenie przez 3 dni (Tokarczyk 2010, s. 34); dowolny skończony próg, a więc także stan wody poniżej zera wodowskazu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Fleig, A.K., Tallaksen, L.M., Hisdal, H. and Demuth, S. (2006). A global evaluation of streamflow drought characteristics. Hydrology and Earth System Sciences 10, 535-552, sect. 2.1, p. 539, eqs. (1) and (2): the full duration of a pooled drought runs from the first day of the first event to the last day of the last, the excess periods included, and its deficit volume is the sum of the pooled deficits <https://hess.copernicus.org/articles/10/535/2006/hess-10-535-2006.pdf>
>
> Funkcja `hydrolog.statistics.low_flows.LowFlowAnalysis.detect_sequences`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:low_flow_sequences -->

<!-- spec:low_flow_deficit_volumes -->

<a id="spec-low_flow_deficit_volumes"></a>

> **Objętość niedoboru odpływu w niżówkach** · wzór grupy B `low_flow_deficit_volumes` (Tier B, CMP-2.2)
>
> **Definicja:** niedobór szeregu przepływów w m³/s wyrażony jako objętość, `deficit_volume_m3` = deficit x 86 400 s/d [m³], dla każdej niżówki, każdego roku hydrologicznego i całego okresu; None dla stanów wody (parametr H); niżówka liczy się w roku hydrologicznym swojego pierwszego dnia, z całym czasem trwania i niedoborem (źr. 1)
>
> **Konwencja:** doba trwająca 86 400 s (jednostka spoza SI akceptowana do użytku z SI, BIPM 2019, tab. 8, z tabeli jednostek `nogat_formulas`): dobowe niedobory [m³/s] pomnożone przez dni dają m³, objętość niedoboru według WMO-No. 1029 (§ 8.3 (c)(iii), „suma dobowych przepływów niedoboru pomnożona przez czas trwania w dniach”); Tokarczyk (2010, s. 34, wzór 1) sumuje (Q0 - Q_t) Δt, gdzie Δt to doba
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $\Delta t$ | `day` | Liczba sekund w dobie | 86 400 | s/d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.), sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the threshold and ends as soon as it returns above it, with its duration, volume, minimum flow and time of occurrence; the IT method pools deficits that occur less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 (eqs. 8.1) <https://library.wmo.int/idurl/4/32176>
> 2. BIPM (2019), The International System of Units (SI), 9th edition, version 4.01, Table 8, non-SI units accepted for use with the SI <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>
>
> Funkcja `hydrolog.operations.stats.stats_low_flow_sequences`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:low_flow_deficit_volumes -->

Wybór progu decyduje o wyniku. W polskich badaniach niżówek najczęściej przyjmuje się przepływ z krzywej
czasu trwania: $Q_{70\%}$ dla niżówek i $Q_{95\%}$ dla niżówek głębokich (Tokarczyk 2010; Tomaszewski
2012); w praktyce gospodarki wodnej także $SNQ$. Hydrolog przyjmuje próg podany wprost
(`--threshold`), $SNQ$ okresu (`--threshold-method mean_annual_minimum`) albo wartość krzywej czasu
trwania (`--threshold-method exceedance --exceedance-percent 70`). Reguły łączenia i minimalny czas
trwania podaje ramka `threshold_runs`; domyślne odpowiadają programowi NIŻÓWKA (Tokarczyk 2010), a inne
prace przyjmują inne (Tomaszewski 2012). Liczby niżówek, ich czasy trwania i deficyty można porównywać
tylko przy tym samym progu, tych samych regułach i z tego samego okresu.

Czas trwania zdarzenia połączonego obejmuje dni przerwy (pełny czas trwania według Fleig i in. 2006),
a deficyt sumuje tylko dni poniżej progu. Niżówka jest zaliczana do roku hydrologicznego, w którym się
zaczęła, nawet gdy trwa do następnego.

### Przykład 8.3: niżówki Kaczawy w Świerzawie, 1991–2020

Próg $SNQ$ okresu (z przepływów dobowych 0,323 m³/s, por. przykład 8.1):

```sh
hydrolog stats low-flow-sequences --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --threshold-method mean_annual_minimum --first-year 1991 --last-year 2020
```

Wynik (domyślne `min_duration_days` = 5 i `max_gap_days` = 4): 37 niżówek w 15 z 30 lat, łączny deficyt
75,95 m³/s·d, czyli 6,56 mln m³. Największe zdarzenia:

| Początek | Koniec | Czas trwania [d] | $Q_{min}$ [m³/s] | Deficyt [mln m³] |
|---|---|---|---|---|
| 25.05.2018 | 3.12.2018 | 193 | 0,15 | 1,419 |
| 25.06.2019 | 8.11.2019 | 137 | 0,19 | 0,941 |
| 11.05.1993 | 10.07.1993 | 61 | 0,14 | 0,732 |
| 22.07.1993 | 31.08.1993 | 41 | 0,10 | 0,593 |
| 2.07.2015 | 14.10.2015 | 105 | 0,23 | 0,529 |

Najdłuższa niżówka (2018) nie dała największego rocznego deficytu: w roku 1993 pięć niżówek (razem
163 dni, w tym dwie letnie z tabeli i trzy zimowe) dało 1,456 mln m³, więcej niż jedna niżówka roku
2018 (1,419 mln m³).

Próg $Q_{70\%}$ (0,55 m³/s, przykład 8.2):

```sh
hydrolog stats low-flow-sequences --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --threshold-method exceedance --exceedance-percent 70 --first-year 1991 --last-year 2020
```

daje 82 niżówki w 27 z 30 lat i łączny deficyt 48,8 mln m³. Najdłuższa trwała 247 dni, od 10.07.1992 do
13.03.1993, i jest zaliczona do roku 1992; największy deficyt jednego zdarzenia, 5,70 mln m³, miała
niżówka od 21.04 do 21.12.2018 (245 dni). Przy wyższym progu niżówki są częstsze, dłuższe i zlewają się
w zdarzenia wielomiesięczne; o tym, który próg jest właściwy, decyduje cel analizy.

## 8.4. Minima roczne: rozkład Fishera–Tippetta

### Rozkład minimów i umowa okresu powtarzalności

Minimum roczne (ang. *annual minimum*) jest najmniejszą z wielu wartości dobowych, więc jego rozkład
przybliża się rozkładem wartości ekstremalnych dla minimów. Dla niżówek okres powtarzalności $T$ odnosi
się do prawdopodobieństwa nieprzewyższenia (ang. *non-exceedance*): przepływ o okresie 10 lat jest
osiągany lub niższy średnio raz na 10 lat (WMO 2008, wzór 7.14). Pozycje empiryczne minimów liczy się
więc od najmniejszego:

<!-- spec:non_exceedance_positions -->

<a id="spec-non_exceedance_positions"></a>

> **Pozycje wykreślne minimów rocznych: prawdopodobieństwa nieprzewyższenia i okresy powtarzalności** · specyfikacja [`non_exceedance_positions`](../FORMULAS.md#non_exceedance_positions) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> p_i = \frac{i - a}{n + 1 - 2a},\qquad T_i = \frac{1}{p_i}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_{(i)}$ | `values` (ciąg) | Próba: minima roczne przepływu lub stanu wody | m³/s | (−∞; ∞) | nie podano w źródłach | [0; 78] (źr. 3) |
> | $a$ | `method` (wybór) | Formuła pozycji wykreślnej: Weibulla, Hazena lub Cunnane'a | – | jedna z: `weibull`, `hazen`, `cunnane` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $x_{(i)}$ | `values_ascending` (ciąg) | Wartości uporządkowane rosnąco | m³/s | (−∞; ∞) |
> | $F_i$ | `non_exceedance_probabilities` (ciąg) | Prawdopodobieństwo nieprzewyższenia każdej wartości | – | (0; 1) |
> | $T_i$ | `return_periods` (ciąg) | Okres powtarzalności każdej wartości, od której wartość niższa występuje raz na T lat | lata | (1; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $a$ | `a_weibull` | Parametr a formuły pozycji wykreślnej Weibulla | 0 | – | (źr. 2) |
> | $a$ | `a_hazen` | Parametr a formuły pozycji wykreślnej Hazena | 1/2 | – | (źr. 2) |
> | $a$ | `a_cunnane` | Parametr a formuły pozycji wykreślnej Cunnane'a | 2/5 | – | (źr. 2) |
>
> **Konwencje**
>
> - prawdopodobieństwo nieprzewyższenia i-tej od najmniejszej wartości, ranga 1 to wartość najmniejsza (WMO-No. 1029, wzór 7.3 i § 7.8, krok I); okres powtarzalności T = 1 / F przepływu niskiego, od którego niższy przepływ występuje raz na T lat (WMO-No. 1029, wzór 7.14), jak dla kwantyli `fisher_tippett_minima`
> - postać ogólna (i - a) / (n + 1 - 2a) z WMO-No. 1029, wzór 7.3, z wartościami a z WMO-No. 168, § 5.6.1; bez wzoru Gringortena
> - wartości wiązane otrzymują kolejne rangi, każda z własną pozycją, tak jak w KZGW 2017, tab. 3.13, kolejne rangi mają dwie wartości 10,3 i dwie wartości 7,88 m³/s
> - próba w dowolnej jednostce: pozycje zależą tylko od rang
>
> **Zgodność z obserwacjami według źródeł:** brak: oszacowanie prawdopodobieństwa każdej wartości uporządkowanej próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.3, eq. 7.3, p. 59: P_i = (i - a) / (n + 1 - 2a), the non-exceedance probability of the ith smallest of n events; p. 60: the Weibull formula is a = 0; sect. 7.8, step I, p. 65: the AM(7) values ranked ascending, the smallest rank 1, and the Weibull formula <https://library.wmo.int/idurl/4/32176>
> 2. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 3. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, table 7.1, p. 64: the AM(7) annual minima of stations 223204 and 223207, 0 to 78 in the unit of the table <https://library.wmo.int/idurl/4/32176>
>
> Funkcja `hydrolog.statistics._types.compute_non_exceedance_positions`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:non_exceedance_positions -->

Hydrolog dopasowuje metodą największej wiarygodności uogólniony rozkład wartości ekstremalnych minimów,
obejmujący rozkład Gumbela dla minimów i trójparametrowy rozkład Weibulla (III typ Fishera–Tippetta):

<!-- spec:fisher_tippett_minima -->

<a id="spec-fisher_tippett_minima"></a>

> **Rozkład Fishera–Tippetta minimów rocznych metodą największej wiarygodności i jego kwantyle** · specyfikacja [`fisher_tippett_minima`](../FORMULAS.md#fisher_tippett_minima) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> F(x) = 1 - \exp\left\{-\left[1 + c\,\frac{x - \xi}{\alpha}\right]^{1/c}\right\},\quad Q_T = \xi + \frac{\alpha}{c}\left[\left(-\ln\left(1 - \frac{1}{T}\right)\right)^{c} - 1\right]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `minima` (ciąg) | Minima roczne przepływu lub stanu wody | m³/s | (−∞; ∞) | nie podano w źródłach | [0; 78] (źr. 3) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: wartość niższa od kwantyla T-letniego występuje z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 1000] (źr. 4) |
> | $v$ | `variable` (wybór) | Rodzaj minimów: przepływ, nigdy poniżej 0, lub stan wody, którego 0 jest zerem wodowskazu | – | jedna z: `discharge`, `stage` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $c$ | `shape` | Parametr kształtu c funkcji genextreme biblioteki scipy dla zanegowanych minimów: dolne ograniczenie minimów loc - scale / c dla c > 0 | – | (−∞; ∞) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) |
> | $Q_T$ | `quantiles` (ciąg) | Minima o danych okresach powtarzalności; luka tam, gdzie przepływ byłby ujemny | m³/s | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 4 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | min(x) >= 0 dla przepływu | `discharges_not_negative` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 7) |
> | wiarygodność rozkładu GEV zanegowanych minimów ma maksimum, na którym poszukiwanie się stabilizuje (warunek wstępny `likelihood_has_a_maximum` wzoru `fit_maximum_likelihood`) | `likelihood_has_a_maximum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Konwencje**
>
> - min(x) = -max(-x): rozkład Fishera–Tippetta minimów to rozkład GEV zanegowanych minimów, F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)}, z parametrem kształtu c funkcji genextreme biblioteki scipy i parametrem położenia -loc zanegowanej próby
> - kwantyl T-letni przy prawdopodobieństwie nieprzewyższenia 1/T (WMO-No. 1029, wzór 7.14), z odwrotnej funkcji przeżycia zanegowanej próby
> - kwantyl przepływu poniżej 0 jest luką (NaN, null w JSON) z komunikatem `negative_quantiles`; ujemny kwantyl stanu wody zostaje zachowany
> - poszukiwanie jak w `fit_maximum_likelihood`: rozkłady GEV mające średnią, -1 < c < 1
>
> **Założenia**
>
> - minima roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: dopasowanie rozkładu minimów metodą największej wiarygodności
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, p. 62: if X is EV III distributed, -X is Weibull distributed; eq. 7.14, p. 64: T of the event X <= x_p <https://library.wmo.int/idurl/4/32176>
> 2. Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer, sect. 3.1.4: min(X) = -max(-X), the GEV of minima — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, table 7.1, p. 64: the AM(7) annual minima of stations 223204 and 223207, 0 to 78 in the unit of the table <https://library.wmo.int/idurl/4/32176>
> 4. Hydrolog (2026). stats low-flow and Obserwator's low_flow.Q, the default return periods, 2 to 1000 years <https://github.com/Daldek/Hydrolog>
> 5. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, n values fit n parameters exactly, where the likelihood has no maximum: one value more than the three parameters — *źródło niedostępne publicznie (dostarczone przez autora)*
> 6. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5: a distribution of the minima needs their spread <https://library.wmo.int/idurl/4/32176>
> 7. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, p. 62: the lower bound of the minima of a flow is 0 or above <https://library.wmo.int/idurl/4/32176>
> 8. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the bound placed at the closest value makes the likelihood grow without limit — *źródło niedostępne publicznie (dostarczone przez autora)*
>
> Funkcja `hydrolog.statistics.low_flows.fisher_tippett_minima`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fisher_tippett_minima -->

Dodatni parametr kształtu $c$ oznacza, że minima mają dolne ograniczenie (rozkład Weibulla); kwantyle
długich okresów zbliżają się wtedy do tego ograniczenia. WMO (2008, § 7.5) zaleca rozkład Weibulla
z dolnym ograniczeniem nieujemnym i odradza rozkład Gumbela dla minimów, który nie ma dolnej granicy.
W polskiej praktyce do minimów stosowano metodę Gumbela opartą na III typie rozkładu wartości najmniejszych
(Wałęga i in. 2014); urzędowo zalecanego rozkładu minimów rocznych w przeglądzie literatury do tego
podręcznika nie znaleziono.

### Przedział ufności kwantyli minimów

Polecenie `hydrolog stats low-flow` podaje przedział ufności kwantyli $NQ_T$ (pole
`fisher_tippett.intervals`, opcja `--confidence-level`, domyślnie 0,95). Liczy go metoda delta
z informacji obserwowanej rozkładu GEV zanegowanych minimów, tak jak dla dopasowania GEV metodą
największej wiarygodności w rozdziale 7 (ramka `quantile_interval_delta` z `extremes` `minima`, p. 7.8);
granice zanegowanej próby neguje się i zamienia miejscami. Granica przepływu poniżej zera jest pusta
(`null`, uwaga `interval_not_computed`, przyczyna `below_physical_range`), tak jak kwantyl
(`negative_quantiles`). Metoda delta wymaga regularnej wiarygodności: przy $c \ge 0{,}5$, czyli przy
minimach z wyraźnym dolnym ograniczeniem, przedziału nie ma (przyczyna `nonregular_fit`). Tak jest
w obu przykładach tego podrozdziału.

### Puste kwantyle

Hydrolog nie wymusza nieujemnego dolnego ograniczenia: dopasowany rozkład może sięgać poniżej zera,
gdy kształt jest niedodatni albo gdy ograniczenie wypada poniżej zera. Ujemny przepływ jest fizycznie
niemożliwy, więc taki kwantyl jest pusty: `null` w JSON (NaN w bibliotece), z uwagą
`negative_quantiles`, której pola podają okresy pominiętych kwantyli (`return_periods`) i okres
powtarzalności, przy którym dopasowany rozkład osiąga zero (`zero_return_period`). Pusty kwantyl nie
jest błędem programu, lecz informacją, że dopasowany rozkład nie opisuje rzadkich niżówek tej rzeki.
Stan wody (z zerem wodowskazu, a nie zerem fizycznym) zachowuje wszystkie kwantyle. Polecenie
`hydrolog stats low-flow` wymaga minimów z co najmniej kilku pełnych lat (warunek `enough_values`
w ramce); z krótszym ciągiem kończy się błędem `calculation_error`. Test Kołmogorowa–Smirnowa ma tu, jak
w rozdziale 7, tylko znaczenie orientacyjne (`ks_valid: false`).

<!-- TODO spec: test Kołmogorowa–Smirnowa rozkładu minimów (scipy.stats.kstest, obliczenie delegowane, CMP-1.2) -->

### Przykład 8.4: minima roczne Kaczawy w Świerzawie, 1991–2020

Najpierw trend minimów (rozdział 10):

```sh
hydrolog stats mann-kendall --values 0.28,0.18,0.1,0.22,0.13,0.31,0.42,0.56,0.6,0.43,0.43,0.63,0.28,0.21,0.32,0.21,0.34,0.24,0.24,0.42,0.51,0.38,0.45,0.48,0.23,0.27,0.28,0.15,0.19,0.21 --years 1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020
```

$S = -6$, $p = 0{,}929$: brak trendu. Dopasowanie:

```sh
hydrolog stats low-flow --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020
```

Parametry: $c = 0{,}566$, położenie 0,3527 m³/s, skala 0,1527 m³/s; kształt dodatni, więc minima mają
dolne ograniczenie. Kształt przekracza 0,5, więc wynik nie ma przedziału ufności (uwaga
`interval_not_computed`, przyczyna `nonregular_fit`); to samo dotyczy całego zapisu 1961–2025
($c = 0{,}595$) i charakterystyk półrocznych z lat 1991–2020 ($c = 0{,}540$).

| $T$ [lata] | 2 | 5 | 10 | 20 | 50 | 100 | 500 | 1000 |
|---|---|---|---|---|---|---|---|---|
| $Q_T$ [m³/s] | 0,302 | 0,198 | 0,158 | 0,133 | 0,113 | 0,103 | 0,091 | 0,089 |

Najgłębsze minimum okresu, 0,10 m³/s w 1993 r., ma prawdopodobieństwo empiryczne 1/31 i okres
powtarzalności 31 lat (blok `empirical`). Kwantyle powyżej 100 lat zmieniają się już niewiele, bo
zbliżają się do dolnego ograniczenia rozkładu. Z charakterystyk półrocznych IMGW-PIB (`--half-year-file`,
te same lata) minima są niższe i $Q_{100}$ wynosi 0,084 m³/s.

### Przykład 8.5: puste kwantyle, Czarna Woda — Bukowna

Charakterystyki półroczne IMGW-PIB wodowskazu Bukowna na Czarnej Wodzie w latach 1991–2020 (dane
publiczne nie mają lat 1992–1994, zostaje 27 lat):

```sh
hydrolog stats low-flow --half-year-file docs/podrecznik/dane/czarna_woda_bukowna_Q_polroczne_1973_2025.csv --first-year 1991 --last-year 2020
```

| $T$ [lata] | 2 | 5 | 10 | 20 | 50 | 100 | 500 | 1000 |
|---|---|---|---|---|---|---|---|---|
| $Q_T$ [m³/s] | 0,217 | 0,109 | 0,064 | 0,035 | 0,0095 | `null` | `null` | `null` |

Uwaga `negative_quantiles` podaje, że dopasowany rozkład osiąga przepływ 0 średnio raz na 82,6 roku, więc
kwantyle 100, 500 i 1000 lat byłyby ujemne i zostały pominięte. Najniższe minima roczne okresu są
bardzo bliskie zera: 0,004 m³/s w 2018 r. i 0,023 m³/s w 2006 r. Kształt $c = 0{,}501$ leży tuż powyżej
0,5, więc przedziału ufności nie ma (`nonregular_fit`).

Cały zapis 1973–2025 (50 lat):

```sh
hydrolog stats low-flow --half-year-file docs/podrecznik/dane/czarna_woda_bukowna_Q_polroczne_1973_2025.csv
```

daje $Q_{100} = 0{,}0089$ m³/s, a puste są tylko kwantyle 500 i 1000 lat (zero raz na 348,7 roku), znów bez
przedziału ufności ($c = 0{,}641$). Wynik zależy więc mocno od okresu. Przyczynę pokazuje test trendu
minimów całego zapisu:

```sh
hydrolog stats mann-kendall --values 0.82,0.4,0.18,0.27,0.43,0.35,0.21,0.78,0.28,0.22,0.1,0.47,0.25,0.32,0.62,0.51,0.18,0.26,0.48,0.2,0.35,0.25,0.25,0.2,0.25,0.56,0.23,0.05,0.2,0.31,0.023,0.21,0.15,0.22,0.33,0.44,0.38,0.28,0.24,0.07,0.38,0.13,0.004,0.06,0.07,0.18,0.03,0.021,0.16,0.14 --years 1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025
```

$S = -453$, $Z = -3{,}78$, $p = 0{,}00015$: istotny trend malejący, według nachylenia Sena
−0,0051 m³/s na rok (przedział ufności 95 % od −0,0081 do −0,0026 m³/s na rok). Minima nie mają więc
jednego rozkładu w czasie, a założenie analizy częstości (niezależne minima o jednakowym rozkładzie)
nie jest spełnione. Puste kwantyle i silna zależność wyniku od okresu są tu objawami tej
niestacjonarności: zanim poda się „przepływ minimalny stuletni”, trzeba wyjaśnić przyczynę trendu (np.
zmiany klimatu, pobory wody, zmiany w zlewni czy w przekroju) i wybrać okres, który opisuje obecne
warunki. Rozdział 10 omawia testy trendu; przyczyny test nie wskaże.

## 8.5. Przepływ podstawowy: filtr Lyne’a–Hollicka i wskaźnik BFI

Przepływ rzeki dzieli się na przepływ szybki (ang. *quickflow*: spływ powierzchniowy i podpowierzchniowy
po opadzie lub roztopach) i przepływ podstawowy (ang. *baseflow*: zasilanie podziemne, wolno zmienne).
Cyfrowy filtr rekurencyjny Lyne’a i Hollicka (1979) traktuje szybkie zmiany hydrogramu jak składową
o wysokiej częstotliwości i odcina ją od powolnej reszty. Ladson i in. (2013) opisali jego standardowe
użycie dla danych dobowych (odbicie lustrzane końców, liczba i kierunki przejść, warunki początkowe)
i opublikowali kod i arkusz z przykładem; Hydrolog odtwarza ich wyniki.

<!-- spec:lyne_hollick -->

<a id="spec-lyne_hollick"></a>

> **Przepływ podstawowy szeregu dobowego z filtru Lyne'a i Hollicka (standard Ladsona i in. 2013)** · specyfikacja [`lyne_hollick`](../FORMULAS.md#lyne_hollick) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> q_t = \alpha\,q_{t-1} + \frac{1 + \alpha}{2}\,(Q_t - Q_{t-1}),\quad b_t = \begin{cases} Q_t - q_t & q_t > 0 \\ Q_t & q_t \le 0 \end{cases}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy, znany dla każdego dnia, w porządku czasowym | m³/s | [0; ∞) | nie podano w źródłach | [0,5; 125] (źr. 5) |
> | $\alpha$ | `alpha` | Parametr filtru | – | (0; 1) | [0,9; 0,98] (źr. 6) | [0,925; 0,98] (źr. 7) |
> | $N$ | `passes` (liczba całkowita) | Przejścia filtru, na przemian naprzód i wstecz | – | [1; ∞) | nie podano w źródłach | [3; 3] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $b_t$ | `baseflow` (ciąg) | Przepływ podstawowy każdego dnia, w jednostce szeregu | m³/s | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n > 30 | `longer_than_reflection` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | passes nieparzyste i passes >= 3 | `odd_passes` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $30$ | `reflected_values` | Liczba wartości odbitych lustrzanie na każdym końcu szeregu | 30 | d | (źr. 10) |
>
> **Konwencje**
>
> - standard w postaci, w jakiej Ladson i in. opracowali go w swoim arkuszu, tab. 4 i BFI.R: przepływ szybki jest zachowywany bez obcinania, także ujemny, jako stan następnego dnia (tab. 4, przypisy d–f), a nie ustawiany na 0, jak wynikałoby z drukowanego wzoru 1 („q_f = 0 otherwise”) i wzoru 7 Murphy'ego i in. (2009) („subject to q_f(i) >= 0”)
> - 30 wartości odbitych lustrzanie na każdym końcu bez powtarzania wartości końcowej: Q_31, ..., Q_2 przed szeregiem i Q_(n-1), ..., Q_(n-30) po nim (rozdz. 2.1)
> - przepływ szybki każdego przejścia zaczyna się od pierwszej wartości jego danych wejściowych: Q_31 w pierwszym przejściu, ostatniej wartości przepływu podstawowego z poprzedniego przejścia w przejściu wstecz i pierwszej w przejściu naprzód (rozdz. 2.2)
> - nieparzysta liczba przejść, na przemian naprzód i wstecz, tak aby ostatnie biegło naprzód (rozdz. 2.3: trzy dla danych dobowych, dziewięć dla godzinowych)
> - przepływ podstawowy poniżej 0 jest po ostatnim przejściu zastępowany przez 0, a wartości odbite są odrzucane (BFI.R, BFI.calc)
> - szereg w dowolnej jednostce, przepływ podstawowy w tej samej (rozdz. 2: „In general the units of flow are not important”)
> - dane dobowe bez luk: luka jest odrzucana; `baseflow_separation` filtruje osobno każdy odcinek bez luk szeregu z lukami (Tier B `baseflow_spans`)
>
> **Założenia**
>
> - przepływ szybki jest składową hydrogramu o wysokiej częstotliwości, a przepływ podstawowy pozostałością o niskiej częstotliwości; filtr nie ma podstaw fizycznych (Ladson i in., rozdz. 1)
> - początek każdego przejścia jest efektem brzegowym, który odbicie tłumi, ale nie usuwa: stały szereg o wartości 10 otrzymuje pierwszego dnia przepływ podstawowy 6,78, a BFI z 400 dni wynosi 0,983; Ladson i in. (rozdz. 2.1) uznali wpływ odbicia na BFI za pomijalny od około 300 dni
>
> **Zgodność z obserwacjami według źródeł:** Ladson i in. (2013, rozdz. 2.5, tab. 2, rys. 2): w 9 zlewniach australijskich BFI przy alfa 0,98 lepiej niż przy 0,925 zgadzał się z oszacowaniami opartymi na znacznikach chemicznych, przy dużym rozrzucie; Nathan i McMahon (1990) uznali alfa od 0,9 do 0,95 za zadowalające w porównaniu z ręcznym rozdzieleniem hydrogramu w 122 zlewniach o powierzchni od 4,2 do 210 km² (według Ladsona i in.)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, eqs. 1 and 2 (the filter); sect. 2.1 to 2.3 (reflection, initial values, passes); sect. 3, Tables 3 and 4 (the worked example) <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 2. Ladson, A.R. (2013). BFI.R and BFI_example.R, the code of Ladson et al. (2013), github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646 (2014-02-12), copied into tests/oracles/baseflow/, BFI.R: FirstPass, BackwardPass, ForwardPass and BFI.calc <https://github.com/TonyLadson/BaseflowSeparation_LyneHollick>
> 3. Nathan, R.J. and McMahon, T.A. (1990). Evaluation of automated techniques for base flow and recession analyses. Water Resources Research 26(7), 1465-1473, the filter with three passes and alpha 0.925 for daily flows, as quoted by Ladson et al. (2013), sect. 1.1 and 2.5, and by Murphy et al. (2009), p. 16 <https://doi.org/10.1029/WR026i007p01465> — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Murphy, R., Graszkiewicz, Z., Hill, P., Neal, B., Nathan, R. and Ladson, T. (2009). Australian Rainfall and Runoff Revision Project 7: Baseflow for Catchment Simulation, Stage 1 report, P7/S1/004, Engineers Australia, p. 15, eq. 7 (the filter); p. 16 (three passes, forward, backward and forward; alpha 0.925 of Nathan and McMahon 1990 for daily data) <https://www.arr-software.org/pdfs/ARR_Project07_Stage1_Final%20Report.pdf>
> 5. IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 6. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.5, pp. 9-10: Nathan and McMahon (1990) found 0.9, 0.925 and 0.95 satisfactory against manual separation, and 0.98 matched chemical tracers better than 0.925 in 9 catchments; sect. 3.1, p. 16: alpha 'anywhere in the range 0.9 to 0.98' <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 7. Hydrolog's catalog and tests: the defaults of stats baseflow (alpha 0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification, src/hydrolog/catalog/groups/stats.py (stats baseflow); tests/unit/test_station_regime.py (TestBaseflow)
> 8. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.1, p. 7: 'the data set must be longer than the amount of reflection'; BFI.R, l. 297 <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 9. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.2 and 2.3, pp. 8-9: three passes for daily data, in order forward, backward, forward; BFI.R, l. 290: 'passes must be odd and greater than 2' <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 10. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.1, pp. 6-7; BFI.R, n.reflect = 30 <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
>
> Funkcja `hydrolog.statistics.baseflow.lyne_hollick_filter`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:lyne_hollick -->

Filtr nie jest modelem fizycznym (Ladson i in. 2013): jego wynik zależy od parametru $\alpha$
i liczby przejść. Domyślne $\alpha$ Hydrologa pochodzi od Nathana i McMahona (1990), którzy uznali je za
zadowalające przy porównaniu z rozdziałem ręcznym; Ladson i in. (2013) uzyskali dla większego $\alpha$
lepszą zgodność z metodami znacznikowymi. Zakres sprawdzonych wartości podaje ramka; wartość spoza niego
daje uwagę. Wynik zawsze trzeba podawać z $\alpha$ i porównywać tylko indeksy liczone tym samym filtrem.

Szereg z lukami filtruje się odcinkami bez luk, a wskaźnik roczny tylko dla roku z dostatecznie wieloma
dniami; obie reguły są własnymi regułami Hydrologa (ADR-0031), bez źródła publikowanego:

<!-- spec:baseflow_spans -->

<a id="spec-baseflow_spans"></a>

> **Przepływ podstawowy szeregu dobowego z lukami, filtrowany odcinkami** · wzór grupy B `baseflow_spans` (Tier B, CMP-2.2)
>
> **Definicja:** szereg dobowy umieszcza się w kalendarzu kolejnych dni (brakująca data to dzień bez wartości); każdy odcinek bez luk o długości co najmniej 60 dni jest filtrowany osobno (specyfikacja `lyne_hollick`), z odbiciem na obu jego końcach; dzień krótszego odcinka nie ma przepływu podstawowego; `series_baseflow` to przepływ podstawowy każdego dnia roku `series_year`, domyślnie ostatniego pełnego roku hydrologicznego (źr. 1)
>
> **Konwencja:** odcinki co najmniej 60-dniowe są własną regułą Hydrologa; Ladson i in. (2013, rozdz. 2.4) filtrują każdy odcinek wartości niebrakujących, a ich BFI.R każdy dłuższy niż 30 wartości odbitych
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $60$ | `min_span_days` | Najmniejsza długość odcinka bez luk filtrowanego osobno | 60 | d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.4, p. 9: 'Flow data should be divided into segments of non-missing values ... data should be reflected at each end of each segment' <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 2. Hydrolog's own rules, ADR-0031: Regime, seasonality, harmonics, Sen's slope and baseflow of a station, point 5: the filter on each gapless span of at least 60 days, a year's index from 300 days with a baseflow (no published source; Ladson et al. 2013 filter every segment longer than the 30 reflected values, sect. 2.1 and 2.4) <docs/decisions/0031-regime-seasonality-harmonics-sens-slope-and-baseflow.md>
>
> Funkcja `hydrolog.statistics.baseflow.baseflow_separation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:baseflow_spans -->

Wskaźnik przepływu podstawowego BFI (ang. *baseflow index*) to stosunek objętości przepływu podstawowego
do objętości całego przepływu w okresie albo w roku (WMO 2008, § 5.2):

<!-- spec:baseflow_index -->

<a id="spec-baseflow_index"></a>

> **Wskaźnik odpływu podziemnego BFI: objętość przepływu podstawowego do objętości przepływu** · specyfikacja [`baseflow_index`](../FORMULAS.md#baseflow_index) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{BFI} = \frac{\sum_t b_t}{\sum_t Q_t}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy; luka (NaN) oznacza dzień bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0,5; 125] (źr. 4) |
> | $b_t$ | `baseflow` (ciąg) | Przepływ podstawowy tych samych dni; luka oznacza dzień bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0,5; 125] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $BFI$ | `bfi` | Udział przepływu podstawowego w objętości przepływu | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | b_t <= Q_t w każdym dniu z obiema wartościami | `baseflow_not_above_flow` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
> | len(b) = len(Q) | `same_days` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | sum(Q_t) > 0 | `positive_flow_volume` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
>
> **Konwencje**
>
> - objętości są sumami wartości dobowych (każdy dzień tej samej długości), sumowanymi z jednym zaokrągleniem (math.fsum)
> - dzień liczy się, gdy ma zarówno przepływ, jak i przepływ podstawowy; przy lukach wskaźnik jest ilorazem sum z dni z wartościami (Ladson i in., rozdz. 2.4), a nie średnią wskaźników odcinków ważoną ich długościami, którą oblicza BFI.R
> - szereg w dowolnej jednostce: wskaźnik jest bezwymiarowy
>
> **Zgodność z obserwacjami według źródeł:** brak: definicja wskaźnika
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, p. 5: 'the ratio of the baseflow volume (calculated from q_b) to the volume of streamflow (q) over a specified period'; sect. 2.4, p. 9: 'the sum of baseflow divided by the sum of total flow over the period of available raw data segments' <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 2. Ladson, A.R. (2013). BFI.R and BFI_example.R, the code of Ladson et al. (2013), github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646 (2014-02-12), copied into tests/oracles/baseflow/, BFI.R, BFI.calc: BFI.value <- sum(Qbase)/sum(Qin) <https://github.com/TonyLadson/BaseflowSeparation_LyneHollick>
> 3. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.2, pp. 43-44: 'BFI = V_baseflow/V_total'; annual BFI from the volumes of each year <https://library.wmo.int/idurl/4/32176>
> 4. IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 5. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, eq. 2: q_b = q - q_f with q_f >= 0 <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 6. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.4, p. 9: baseflow statistics 'only from time steps in which raw data were available' <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
> 7. Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, p. 5: a ratio to the volume of streamflow, undefined without flow <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
>
> Funkcja `hydrolog.statistics.baseflow.baseflow_index`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:baseflow_index -->

<!-- spec:baseflow_index_by_year -->

<a id="spec-baseflow_index_by_year"></a>

> **Wskaźnik odpływu podziemnego BFI okresu i poszczególnych lat hydrologicznych** · wzór grupy B `baseflow_index_by_year` (Tier B, CMP-2.2)
>
> **Definicja:** wskaźnik odpływu podziemnego okresu i każdego roku hydrologicznego (1 listopada – 31 października, nazywanego od roku jego końca) jest wskaźnikiem (specyfikacja `baseflow_index`) ich dni z przepływem podstawowym; rok potrzebuje 300 takich dni, aby mieć własny wskaźnik, a rok bez przepływu w tych dniach go nie ma (null); okres bez przepływu w tych dniach jest odrzucany (źr. 1)
>
> **Konwencja:** iloraz objętości z dni z przepływem podstawowym (Ladson i in., rozdz. 2.4; WMO-No. 1029, rozdz. 5.2), a nie średnia wskaźników odcinków ważona ich długościami z BFI.R; 300 dni w roku to własna reguła Hydrologa
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $300$ | `min_year_days` | Najmniejsza liczba dni z przepływem podstawowym w roku, dla którego podaje się własny wskaźnik | 300 | d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.2, p. 44: 'Annual BFI values can be determined by summing up the base-flow and total-flow volume separately for each year' <https://library.wmo.int/idurl/4/32176>
> 2. Hydrolog's own rules, ADR-0031: Regime, seasonality, harmonics, Sen's slope and baseflow of a station, point 5: the filter on each gapless span of at least 60 days, a year's index from 300 days with a baseflow (no published source; Ladson et al. 2013 filter every segment longer than the 30 reflected values, sect. 2.1 and 2.4) <docs/decisions/0031-regime-seasonality-harmonics-sens-slope-and-baseflow.md>
>
> Funkcja `hydrolog.statistics.baseflow.baseflow_separation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:baseflow_index_by_year -->

BFI bliskie 1 oznacza rzekę zasilaną głównie wodami podziemnymi, o wyrównanym przepływie; małe BFI —
rzekę „nerwową”, w której większość odpływu przychodzi z wezbraniami. W suchych latach BFI rośnie, bo
przepływu szybkiego jest mało; w latach wezbrań maleje.

### Przykład 8.6: przepływ podstawowy Kaczawy w Świerzawie, 1991–2020

```sh
hydrolog stats baseflow --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020
```

Z domyślnym filtrem ($\alpha$ = 0,925, trzy przejścia; jeden odcinek bez luk, 10 958 dni) BFI okresu
wynosi 0,604: ok. 60 % objętości odpływu przypada na składową wolną. Wskaźniki roczne wahają się od 0,411
w roku 1997 (powódź lipcowa) do 0,782 w suchym roku 2018. Ten sam okres z $\alpha$ = 0,98:

```sh
hydrolog stats baseflow --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020 --alpha 0.98
```

daje BFI 0,529. Różnica 0,074 wynika tylko z parametru filtru; dlatego wartość $\alpha$ jest częścią
wyniku. Pole `series_baseflow` zawiera przepływ podstawowy każdego dnia ostatniego roku okresu (tu 2020;
inny rok wybiera `--series-year`), do wykresu na tle hydrogramu.

## 8.6. Recesja i stała recesji

W okresach bez zasilania opadowego przepływ maleje w przybliżeniu wykładniczo, a stosunek przepływu dnia
następnego do dnia bieżącego, stała recesji $k$ (ang. *recession constant*), jest w przybliżeniu stały
(WMO 2008, § 5.3). Czas połowicznego spadku przepływu (ang. *half-life*) to liczba dni, po których
przepływ maleje o połowę.

<!-- spec:recession_constant -->

<a id="spec-recession_constant"></a>

> **Stała recesji przepływu całkowitego: mediana dobowych ilorazów w ciągach malejącego przepływu** · specyfikacja [`recession_constant`](../FORMULAS.md#recession_constant) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> k = \operatorname{median}\left\{\frac{Q_{t+1}}{Q_t}\right\},\quad T_{1/2} = \frac{\ln 2}{-\ln k}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy w kolejnych dniach; luka (NaN) oznacza dzień bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0,5; 125] (źr. 2) |
> | $m$ | `min_days` (liczba całkowita) | Najkrótszy odcinek recesji: liczba spadków z rzędu | d | [1; ∞) | nie podano w źródłach | [5; 5] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `k` | Dobowa stała recesji przepływu całkowitego | – | [0; 1) |
> | $T_{1/2}$ | `half_life_days` | Liczba dni, w ciągu których taka recesja zmniejsza przepływ o połowę | d | [0; ∞) |
> | – | `n_segments` (liczba całkowita) | Liczba znalezionych odcinków recesji | – | [1; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | ciąg co najmniej min_days dni z 0 < Q_(t+1) / Q_t < 1 | `recession_segment` | odmowa obliczeń: wzór jest nieokreślony | (źr. 4) |
>
> **Konwencje**
>
> - k jest dobowym ilorazem Q_(t+1) / Q_t ze wzoru 5.2 WMO-No. 1029, a czas połowicznego spadku ln 2 / (-ln k) to C ln 2 z jego wzoru 5.3
> - odcinki według własnej reguły Hydrologa: każdy ciąg co najmniej min_days spadków, od pierwszego dnia po kulminacji, bez progu (WMO zaczyna poniżej Q70 i dwa dni po kulminacji, na odcinkach siedmiodniowych, i dopasowuje je regresją)
> - mediana wszystkich ilorazów wszystkich odcinków łącznie, a nie regresja przez początek układu (główna krzywa recesji WMO) ani średnia stałych poszczególnych odcinków (pojedyncze odcinki recesji WMO)
> - spadek jest ostry: dzień o przepływie równym poprzedniemu (wartości wiązane) kończy ciąg, tak jak wzrost
> - dzień bez wartości lub dzień bez przepływu (Q_t = 0) kończy ciąg; spadek do 0 jest ostatnim ilorazem swojego ciągu, więc k = 0 i czas połowicznego spadku 0 tylko przy min_days równym 1
>
> **Założenia**
>
> - recesja jest wykładnicza w obrębie każdego odcinka (WMO-No. 1029, wzór 5.1)
> - szereg jest dobowy: k odnosi się do doby, a czas połowicznego spadku jest w dobach
>
> **Zgodność z obserwacjami według źródeł:** brak: mediana ilorazów przepływu całkowitego jest własnym estymatorem Hydrologa; w przykładzie rzeki Ngaruroro z WMO-No. 1029 (1963-1989) daje k = 0,932, podczas gdy główna krzywa recesji WMO daje 0,9602, a MRC pakietu lfstat 0,954 (analiza z 2026-11-18): jego odcinki obejmują przepływ szybki po kulminacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45, eqs. 5.1 to 5.3: Q_t = Q_0 exp(-t/C), k = Q_t/Q_(t-1), C = -dt/ln(k); 'A minimum length in the order of five to seven days is, however, commonly used' <https://library.wmo.int/idurl/4/32176>
> 2. IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 3. Hydrolog's catalog and tests: the defaults of stats baseflow (alpha 0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification, src/hydrolog/catalog/groups/stats.py (stats baseflow); tests/unit/test_station_regime.py (TestBaseflow)
> 4. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45: the recession is analysed on segments of a minimum length <https://library.wmo.int/idurl/4/32176>
>
> Funkcja `hydrolog.statistics.baseflow.recession_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:recession_constant -->

<!-- spec:recession_without_segment -->

<a id="spec-recession_without_segment"></a>

> **Stała recesji szeregu bez odcinka recesji** · wzór grupy B `recession_without_segment` (Tier B, CMP-2.2)
>
> **Definicja:** stała recesji szeregu (specyfikacja `recession_constant`), z k i czasem połowicznego spadku równymi null i bez odcinków, gdy szereg nie ma żadnego odcinka recesji (źr. 1)
>
> **Konwencja:** recesja w `baseflow_separation` jest liczona dla całego kalendarza dobowego szeregu, a luki są w nim końcami odcinków
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45 <https://library.wmo.int/idurl/4/32176>
>
> Funkcja `hydrolog.statistics.baseflow.recession_constant`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:recession_without_segment -->

Hydrolog szacuje $k$ własną metodą: medianą stosunków dobowych ze wszystkich odcinków nieprzerwanego
spadku przepływu, od pierwszego dnia po kulminacji, bez progu. WMO (2008) zaleca analizę recesji
przepływu podstawowego: odcinki poniżej $Q_{70\%}$, zaczynające się kilka dni po kulminacji, stałej
długości, z krzywą główną recesji (ang. *master recession curve*). Odcinki Hydrologu obejmują więc także
opadanie przepływu szybkiego zaraz po wezbraniu, a jego $k$ opisuje recesję przepływu całkowitego i jest
mniejsze (recesja szybsza) niż stała recesji przepływu podstawowego według WMO; porównanie na przykładzie
WMO podaje ramka. Wartości $k$ z Hydrologu i z metody WMO nie są zamienne.

### Przykład 8.7: recesja Kaczawy w Świerzawie, 1991–2020

Polecenie `stats baseflow` z przykładu 8.6 podaje też stałą recesji (blok `recession`): $k = 0{,}9125$
z 282 odcinków spadku, czyli czas połowicznego spadku przepływu 7,57 doby. Ze względu na metodę jest to
recesja przepływu całkowitego po wezbraniach; recesja przepływu podstawowego w długich okresach bez opadu
jest wolniejsza.

## 8.7. Sygnatury hydrologiczne i CAMELS-PL

Sygnatura hydrologiczna (ang. *hydrological signature*) to jedna liczba, która streszcza szereg
przepływów dobowych tak, aby można było porównywać zlewnie (Sawicz i in. 2011; Westerberg i McMillan
2015). Zbiory CAMELS publikują dla każdego wodowskazu ten sam zestaw sygnatur: CAMELS dla 671 zlewni
w USA (Addor i in. 2017), CAMELS-DE dla Niemiec i CAMELS-PL dla 869 zlewni w Polsce (Brzezińska i in.
2026). Hydrolog liczy pięć z nich wzorami ze specyfikacjami; dwie kolejne to wielkości z poprzednich
podrozdziałów: kwantyle $Q_5$ i $Q_{95}$ zbiorów CAMELS to wartości krzywej sum czasów trwania
osiągane lub przekraczane w 95 i 5 % dni (podrozdział 8.2), a `baseflow_index` to BFI z podrozdziału
8.5. Sygnatury są funkcjami biblioteki `hydrolog.statistics` (nie mają polecenia): przyjmują próbę,
czyli kolejne dni zapisu z luką NaN, a nie kalendarz; który okres i które lata wejdą do próby,
decyduje wywołujący.

Nachylenie krzywej sum czasów trwania mierzy, jak szybko przepływ maleje między przepływami średnimi
i niskimi: duże nachylenie ma rzeka „nerwowa”, małe — rzeka zasilana równomiernie, np. z wód
podziemnych lub jezior (Sawicz i in. 2011).

<!-- spec:fdc_slope -->

<a id="spec-fdc_slope"></a>

> **Nachylenie krzywej sum czasów trwania między dwoma procentami przewyższenia w skali logarytmicznej** · specyfikacja [`fdc_slope`](../FORMULAS.md#fdc_slope) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> S = \frac{\ln Q(p_1) - \ln Q(p_2)}{(p_2 - p_1)/100},\quad p_1 < p_2
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Wartości dobowe szeregu, w dowolnej kolejności; NaN w dniu bez wartości, który jest pomijany | m³/s | [0; ∞) | nie podano w źródłach | [0; 6430] (źr. 4) |
> | $p_1$ | `from_percent` | Procent przewyższenia pierwszego, wyższego punktu krzywej | % | (0; 100) | nie podano w źródłach | [33; 34] (źr. 5) |
> | $p_2$ | `to_percent` | Procent przewyższenia drugiego, niższego punktu krzywej | % | (0; 100) | nie podano w źródłach | [66; 67] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $S$ | `slope` | Spadek krzywej w skali logarytmicznej na jednostkę prawdopodobieństwa przewyższenia | – | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 1: co najmniej jeden dzień z wartością | `has_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | p_1 < p_2 | `ordered_percents` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | Q(p_2) > 0 | `flow_at_both_points` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
>
> **Konwencje**
>
> - Q(p) to krzywa sum czasów trwania Hydrologa (specyfikacja exceedance_values): wartość osiągana lub przekraczana w p % dni z wartością, pozycje Weibulla m / (n + 1) i interpolacja liniowa; Sawicz i in. (2011) odczytują przepływy przekraczane w 33 i 66 % dni, czyli wartości domyślne
> - Addor i in. (2017) oraz kody CAMELS-DE i CAMELS-PL biorą kwantyle nieprzekroczenia 0,33 i 0,66, czyli przepływy przekraczane w 67 i 34 % dni („slightly different”, jak zaznacza kod CAMELS-US): from_percent 34 i to_percent 67 dają ich nachylenie
> - zera są wartościami krzywej, jak u Sawicza i in. i w kodzie CAMELS-US: krzywa równa 0 w p_2 jest odrzucana (warunek flow_at_both_points); kody CAMELS-DE i CAMELS-PL najpierw pomijają dni bez przepływu, co wywołujący uzyskuje, podając tylko przepływy większe od 0
> - krzywa jest liczona na wartościach podzielonych przez potęgę dwójki, która sprowadza największą do [1/2, 1), a ln Q(p_1) - ln Q(p_2) z ich mantys i wykładników: nachylenie nie zależy od jednostki szeregu i nie powoduje przepełnienia
> - Q(p_2) jest ograniczane do co najwyżej Q(p_1): zaokrąglenie interpolacji mogłoby inaczej dać wartość o jednostkę ostatniego miejsca większą od wyższej
> - dzień bez wartości (NaN) jest pomijany, n liczy dni z wartością
>
> **Założenia**
>
> - wartości pochodzą z jednej stacji i jednego okresu: nachylenie opisuje krzywą tego okresu
> - krzywa między dwoma punktami jest w skali logarytmicznej prawie prosta, dlatego Sawicz i in. wybrali 33 i 66 %; inne punkty dają nachylenie swojej części krzywej
>
> **Zgodność z obserwacjami według źródeł:** brak: statystyka opisowa obserwowanego szeregu; Sawicz i in. (2011) oraz Addor i in. (2017) wiążą ją z cechami zlewni, a nie z obserwacją tej samej wielkości
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Sawicz, K., Wagener, T., Sivapalan, M., Troch, P.A. and Carrillo, G. (2011). Catchment classification: empirical analysis of hydrologic similarity based on catchment function in the eastern USA. Hydrology and Earth System Sciences 15, 2895-2911, sect. 3.2, eq. 3, p. 2898: S_FDC = [ln(Q33%) - ln(Q66%)] / (0.66 - 0.33), on the flow duration curve, 'the distribution of probabilities of streamflow being greater than or equal to a specified magnitude' <https://doi.org/10.5194/hess-15-2895-2011>
> 2. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, sect. 5.1, p. 5298: 'the slope of the flow duration curve ... between the log-transformed 33rd and 66th streamflow percentiles', undefined where the flow is 0 on more than a third of the days; Table 3, p. 5300, slope_fdc <https://doi.org/10.5194/hess-21-5293-2017>
> 3. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, comp_s_fdc: sfdc_sawicz_2011 on the exceedance percentages 33 and 66, sfdc_addor_2017 on the quantiles 0.33 and 0.66, NA when q66 = 0 <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 4. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to 193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and five more) to 6430 m3/s (the Wisła at Tczew) <https://doi.org/10.5281/zenodo.23275336>
> 5. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, CAMELS_PL_Data_Description.pdf, Table 7, slope_fdc between the 33rd and 66th percentiles, the flows exceeded on 67 and 34 % of the days; Sawicz et al. (2011, eq. 3) take the flows exceeded on 33 and 66 % <https://doi.org/10.5281/zenodo.23275336>
> 6. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, find_avail_data_array: a signature needs the days with a value, NA without <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 7. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, sect. 5.1, p. 5298: 'In intermittent streams, the frequency of days with no flow can be greater than 33 % ... Since the logarithm cannot be extracted, the slope of the flow duration curve is undefined' <https://doi.org/10.5194/hess-21-5293-2017>
>
> Funkcja `hydrolog.statistics.signatures.fdc_slope`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fdc_slope -->

Dni przepływów wysokich i niskich liczą, jak często przepływ wychodzi poza próg odniesiony do
przepływu typowego zlewni (mediany albo średniej), i jak długo trwają ciągi takich dni. Częstość jest
liczbą dni na rok (jednostka d/rok), a nie udziałem:

<!-- spec:high_flow_days -->

<a id="spec-high_flow_days"></a>

> **Dni przepływów wysokich: ich częstość i średni czas trwania ich ciągów** · specyfikacja [`high_flow_days`](../FORMULAS.md#high_flow_days) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_t > 9\,\tilde{Q},\quad F = 365{,}25\,\frac{N_h}{n},\quad D = \frac{N_h}{E}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy w porządku czasowym; NaN w dniu bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0; 6430] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $F_h$ | `days_per_year` | Liczba dni poza progiem na rok dni z wartością | d/rok | [0; 365,25] |
> | $D_h$ | `mean_duration_days` | Średnia długość ciągów takich dni, 0 bez żadnego | d | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 1: co najmniej jeden dzień z wartością | `has_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $9$ | `high_flow_multiple` | Krotność mediany przepływu dobowego, powyżej której dzień jest dniem przepływu wysokiego | 9 | – | (źr. 7) |
> | $365{,}25$ | `days_per_year` | Liczba dni roku, na który przelicza się częstość | 1461/4 | d | (źr. 8) |
>
> **Konwencje**
>
> - dzień przepływu wysokiego ma przepływ ściśle większy od 9-krotności mediany dni z wartością (Addor i in. 2017, tab. 3; Westerberg i McMillan 2015, tab. 2); mediana parzystej liczby wartości to średnia dwóch środkowych
> - gdy mediana wynosi 0, każdy dzień z przepływem jest dniem przepływu wysokiego (zaznacza to kod CAMELS-US)
> - częstość liczy się na dzień z wartością, razy 365,25 dnia: kod Addora i in. (sum(hf) / sum(avail_data) * 365.25); kody CAMELS-DE i CAMELS-PL dzielą przez wszystkie dni swojej ramki, także dni bez wartości
> - zdarzenie to ciąg kolejnych dni poza progiem, a dzień bez wartości go kończy, jak w kodzie CAMELS-DE; kod Addora i in. pomija takie dni i łączy ciągi po obu ich stronach
> - średni czas trwania to liczba dni poza progiem przez liczbę zdarzeń; szereg bez takiego dnia ma częstość 0 i czas trwania 0, tak jak w kodach CAMELS-US, CAMELS-DE i CAMELS-PL
> - porównania wykonuje się na wartościach podzielonych przez potęgę dwójki, która sprowadza największą do [1/2, 1): te same liczby dla szeregu w dowolnej jednostce
>
> **Założenia**
>
> - zapis jest dość długi, aby jego mediana była medianą reżimu: częstość z krótkiego lub niepełnego zapisu mówi niewiele
>
> **Zgodność z obserwacjami według źródeł:** brak: statystyka opisowa obserwowanego szeregu; Westerberg i McMillan (2015) szacują jej niepewność z niepewności danych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: high_q_freq and high_q_dur <https://doi.org/10.5194/hess-21-5293-2017>
> 2. Westerberg, I.K. and McMillan, H.K. (2015). Uncertainty in hydrological signatures. Hydrology and Earth System Sciences 19, 3951-3968, Table 2, p. 3956: QHF and QHD, the frequency and the duration of daily flows higher than 9 times the median daily flow (Clausen and Biggs 2000); QLF and QLD, of daily flows lower than 0.2 times the mean daily flow (Olden and Poff 2003, who used a 5 % threshold) <https://doi.org/10.5194/hess-19-3951-2015>
> 3. Clausen, B. and Biggs, B.J.F. (2000). Flow variables for ecological studies in temperate streams: groupings based on covariance. Journal of Hydrology 237, 184-197, the frequency of high flows above a multiple of the median flow, as Westerberg and McMillan (2015, Table 2) and Addor et al. (2017, Table 3) cite it <https://doi.org/10.1016/S0022-1694(00)00306-1> — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_hf_freq_dur: hf <- q > 9 * median(q) <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 5. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to 193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and five more) to 6430 m3/s (the Wisła at Tczew) <https://doi.org/10.5281/zenodo.23275336>
> 6. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, find_avail_data_array: a signature needs the days with a value, NA without <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 7. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: high_q_freq, the frequency of high-flow days (> 9 times the median daily flow); confirmed by Westerberg and McMillan (2015), Table 2, p. 3956, QHF <https://doi.org/10.5194/hess-21-5293-2017>
> 8. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_hf_freq_dur and compute_lf_freq_dur: hf_freq <- sum(hf) / sum(avail_data) * 365.25; the same in the code of CAMELS-DE (08_hydrologic_attributes.ipynb): high_q_freq = hf.sum() / len(df) * 365.25 <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
>
> Funkcja `hydrolog.statistics.signatures.high_flow_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:high_flow_days -->

<!-- spec:low_flow_days -->

<a id="spec-low_flow_days"></a>

> **Dni przepływów niskich: ich częstość i średni czas trwania ich ciągów** · specyfikacja [`low_flow_days`](../FORMULAS.md#low_flow_days) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_t < 0{,}2\,\bar{Q},\quad F = 365{,}25\,\frac{N_l}{n},\quad D = \frac{N_l}{E}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy w porządku czasowym; NaN w dniu bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0; 6430] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $F_l$ | `days_per_year` | Liczba dni poza progiem na rok dni z wartością | d/rok | [0; 365,25] |
> | $D_l$ | `mean_duration_days` | Średnia długość ciągów takich dni, 0 bez żadnego | d | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 1: co najmniej jeden dzień z wartością | `has_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}2$ | `low_flow_multiple` | Krotność średniego przepływu dobowego, poniżej której dzień jest dniem przepływu niskiego | 1/5 | – | (źr. 7) |
> | $365{,}25$ | `days_per_year` | Liczba dni roku, na który przelicza się częstość | 1461/4 | d | (źr. 8) |
>
> **Konwencje**
>
> - dzień przepływu niskiego ma przepływ ściśle mniejszy od 0,2 średniej dni z wartością (Addor i in. 2017, tab. 3, oraz kody CAMELS-DE i CAMELS-PL; Westerberg i McMillan 2015, tab. 2: „lower than”); kod CAMELS-US przyjmuje <=
> - średnia to suma dni z wartością, zaokrąglona dokładnie raz (math.fsum), przez ich liczbę
> - częstość liczy się na dzień z wartością, razy 365,25 dnia: kod Addora i in. (sum(hf) / sum(avail_data) * 365.25); kody CAMELS-DE i CAMELS-PL dzielą przez wszystkie dni swojej ramki, także dni bez wartości
> - zdarzenie to ciąg kolejnych dni poza progiem, a dzień bez wartości go kończy, jak w kodzie CAMELS-DE; kod Addora i in. pomija takie dni i łączy ciągi po obu ich stronach
> - średni czas trwania to liczba dni poza progiem przez liczbę zdarzeń; szereg bez takiego dnia ma częstość 0 i czas trwania 0, tak jak w kodach CAMELS-US, CAMELS-DE i CAMELS-PL
> - porównania wykonuje się na wartościach podzielonych przez potęgę dwójki, która sprowadza największą do [1/2, 1): te same liczby dla szeregu w dowolnej jednostce
>
> **Założenia**
>
> - zapis jest dość długi, aby jego średnia była średnią reżimu: częstość z krótkiego lub niepełnego zapisu mówi niewiele
>
> **Zgodność z obserwacjami według źródeł:** brak: statystyka opisowa obserwowanego szeregu; Westerberg i McMillan (2015) szacują jej niepewność z niepewności danych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: low_q_freq and low_q_dur <https://doi.org/10.5194/hess-21-5293-2017>
> 2. Westerberg, I.K. and McMillan, H.K. (2015). Uncertainty in hydrological signatures. Hydrology and Earth System Sciences 19, 3951-3968, Table 2, p. 3956: QHF and QHD, the frequency and the duration of daily flows higher than 9 times the median daily flow (Clausen and Biggs 2000); QLF and QLD, of daily flows lower than 0.2 times the mean daily flow (Olden and Poff 2003, who used a 5 % threshold) <https://doi.org/10.5194/hess-19-3951-2015>
> 3. Olden, J.D. and Poff, N.L. (2003). Redundancy and the choice of hydrologic indices for characterizing streamflow regimes. River Research and Applications 19, 101-121, the frequency and duration of low flows, as Westerberg and McMillan (2015, Table 2) and Addor et al. (2017, Table 3) cite it, with a threshold of 5 % of the mean, which they raise to 0.2 times the mean <https://doi.org/10.1002/rra.700>
> 4. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_lf_freq_dur: lf <- q <= 0.2 * mean(q) <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 5. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to 193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and five more) to 6430 m3/s (the Wisła at Tczew) <https://doi.org/10.5281/zenodo.23275336>
> 6. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, find_avail_data_array: a signature needs the days with a value, NA without <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 7. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: low_q_freq, the frequency of low-flow days (< 0.2 times the mean daily flow); confirmed by Westerberg and McMillan (2015), Table 2, p. 3956, QLF <https://doi.org/10.5194/hess-21-5293-2017>
> 8. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_hf_freq_dur and compute_lf_freq_dur: hf_freq <- sum(hf) / sum(avail_data) * 365.25; the same in the code of CAMELS-DE (08_hydrologic_attributes.ipynb): high_q_freq = hf.sum() / len(df) * 365.25 <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
>
> Funkcja `hydrolog.statistics.signatures.low_flow_days`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:low_flow_days -->

Udział dni bez przepływu odróżnia rzeki okresowo wysychające od stałych:

<!-- spec:zero_flow_fraction -->

<a id="spec-zero_flow_fraction"></a>

> **Udział dni bez przepływu** · specyfikacja [`zero_flow_fraction`](../FORMULAS.md#zero_flow_fraction) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> f_0 = \frac{N_0}{n}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy; NaN w dniu bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0; 6430] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $f_0$ | `fraction` | Udział dni bez przepływu wśród dni z wartością | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 1: co najmniej jeden dzień z wartością | `has_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 4) |
>
> **Konwencje**
>
> - dzień bez przepływu ma przepływ równy dokładnie 0 w zaokrągleniu danych: przepływ mniejszy od połowy ostatniej drukowanej jednostki to 0 (CAMELS-PL liczy dni, w których przepływ jednostkowy, drukowany z dokładnością 0,001 mm/d, wynosi 0)
> - udział w dniach z wartością (kod CAMELS-US); kody CAMELS-DE i CAMELS-PL dzielą przez wszystkie dni swojej ramki, także dni bez wartości
> - ułamek, a nie procent (Addor i in. 2017, tab. 3, podają %, pliki CAMELS-US, CAMELS-DE i CAMELS-PL ułamki)
>
> **Zgodność z obserwacjami według źródeł:** brak: liczba dni obserwowanego szeregu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: zero_q_freq, the frequency of days with Q = 0 <https://doi.org/10.5194/hess-21-5293-2017>
> 2. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_no_flow: sum(q[avail_data] <= thres) / length(...) <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 3. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to 193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and five more) to 6430 m3/s (the Wisła at Tczew) <https://doi.org/10.5281/zenodo.23275336>
> 4. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, find_avail_data_array: a signature needs the days with a value, NA without <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
>
> Funkcja `hydrolog.statistics.signatures.zero_flow_fraction`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:zero_flow_fraction -->

Data połowy odpływu (Court 1962) mówi, kiedy w roku przepływa połowa jego odpływu: wcześnie w rzece
o wezbraniach roztopowych, później w rzece zasilanej latem. Liczy się ją dla każdego roku osobno,
a sygnaturą zapisu jest średnia dat jego lat:

<!-- spec:half_flow_date -->

<a id="spec-half_flow_date"></a>

> **Data połowy odpływu: dzień, w którym upłynęła połowa odpływu roku** · specyfikacja [`half_flow_date`](../FORMULAS.md#half_flow_date) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> d = \min\Bigl\{k : 2\sum_{t=1}^{k} Q_t > \sum_{t=1}^{n} Q_t\Bigr\}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_t$ | `values` (ciąg) | Przepływ dobowy jednego roku od jego pierwszego dnia; NaN w dniu bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [0; 6430] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $d$ | `day` (liczba całkowita) | Dzień roku, licząc od 1, w którym przepływ zsumowany od pierwszego dnia po raz pierwszy przekracza połowę sumy roku | d | [1; 366] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | sum(Q_t) > 0 | `positive_flow_volume` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - wartości to kolejne dni jednego roku, dzień 1 jest jego pierwszym: rok hydrologiczny IMGW-PIB od 1 listopada (CAMELS-PL), rok CAMELS-US od 1 października; średnia data połowy odpływu zapisu to średnia dat jego lat
> - datą jest pierwszy dzień, w którym przepływ zsumowany od początku roku przekracza połowę sumy roku (ściśle, jak w kodach CAMELS-US i CAMELS-DE; tab. 3 Addora i in. mówi „reaches”)
> - dzień bez wartości (NaN) nie dodaje nic do żadnej z sum, więc nigdy nie jest datą (kod CAMELS-US go pomija i zachowuje numery dni)
> - sumy są dokładne dla podanych wartości dwójkowych, całkowitych wielokrotności ich najmniejszej potęgi dwójki: o dacie nie decyduje żadne zaokrąglenie, a suma równa połowie sumy roku (remis) nie jest jej przekroczeniem; wartości równe w drukowanych cyfrach dziesiętnych mogą dawać remis w zapisie dziesiętnym, a w dwójkowym nie
>
> **Założenia**
>
> - dni bez wartości jest mało: każdy zabiera swój przepływ z roku i może przesunąć datę
>
> **Zgodność z obserwacjami według źródeł:** brak: statystyka terminu w obserwowanym szeregu; Court (1962) i Addor i in. (2017) porównują nią terminy odpływu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Court, A. (1962). Measures of streamflow timing. Journal of Geophysical Research 67(11), 4335-4339, the half-flow date, as Addor et al. (2017, Table 3) cite it — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Addor, N., Newman, A.J., Mizukami, N. and Clark, M.P. (2017). The CAMELS data set: catchment attributes and meteorology for large-sample studies. Hydrology and Earth System Sciences 21, 5293-5313, Table 3, p. 5300: hfd_mean, the mean half-flow date, the 'date on which the cumulative discharge since 1 October reaches half of the annual discharge' <https://doi.org/10.5194/hess-21-5293-2017>
> 3. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_hfd_mean_sd: which(cumsum(hy_q) > 0.5 * sum(hy_q))[1], the number of days since the beginning of the hydrological year <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
> 4. Dolich, A. (2024). 08_hydrologic_attributes.ipynb, the code of the hydrologic attributes of CAMELS-DE version 1 (Loritz et al. 2024, ESSD 16, 5625-5642), github.com/CAMELS-DE/camels_de, hfd_mean: the first day whose cumulative discharge since the start of the year exceeds half of the year's, counted from 1 <https://github.com/CAMELS-DE/camels_de/blob/main/version1/scripts/08_hydrologic_attributes.ipynb>
> 5. Brzezińska, W., Marcinkowski, P., Dolich, A., Perz, A. E., Maharjan, A., Piniewski, M., Kardel, I., Loritz, R. and Wrzesiński, D. (2026). CAMELS-PL: hydro-meteorological time series and landscape attributes for 869 catchments in Poland, version 2.1.0 [dataset], Zenodo record 23275336, CC BY 4.0, discharge_vol_obs of the 13 gauges of tests/fixtures/camels_pl/ (5.93 to 193,728 km2): 0 m3/s on days without flow (Brynica, Czarna, Gardęga, Noteć and five more) to 6430 m3/s (the Wisła at Tczew) <https://doi.org/10.5281/zenodo.23275336>
> 6. Addor, N. (2017). hydro_signatures.R, the code of the hydrological signatures of CAMELS (Addor et al. 2017), github.com/naddor/camels, compute_hfd_mean_sd: 'hfd can't be computed if annual discharge is 0' <https://github.com/naddor/camels/blob/master/hydro/hydro_signatures.R>
>
> Funkcja `hydrolog.statistics.signatures.half_flow_date`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:half_flow_date -->

### Porównanie z CAMELS-PL

CAMELS-PL 2.1.0 publikuje sygnatury każdego wodowskazu obok jego przepływu dobowego, z którego je
policzono, ale bez kodu. Ich sposób obliczenia odtworzono na wszystkich 869 wodowskazach: to kod
CAMELS-DE (`08_hydrologic_attributes.ipynb`) z czterema zmianami. Rok hydrologiczny zaczyna się
1 listopada, kwantyle $Q_5$, $Q_{95}$ i punkty nachylenia to najbliższe statystyki pozycyjne (metoda
`nearest` numpy), nachylenie liczy się tylko z dodatnich przepływów pełnych lat, a częstość i czas
trwania niżówek bez żadnego zdarzenia wynoszą 0. Do próby wchodzą lata hydrologiczne, w których brakuje
najwyżej 5 % dni, a częstości dzieli się przez wszystkie dni tych lat, także dni bez wartości.
Z tymi regułami $Q_5$, $Q_{95}$, nachylenie, częstości i czasy trwania przepływów wysokich i niskich
oraz udział dni bez przepływu zgadzają się na 869 z 869 wodowskazów, a data połowy odpływu na 828;
pozostałe 41 różnią się tylko w latach, w których suma przepływów wypada dokładnie na połowie sumy roku
w drukowanych cyfrach dziesiętnych.

Sygnatury trzynastu wodowskazów, od 6 do 193 728 km² (od Kamiennej w Jakuszycach po Wisłę w Tczewie,
w tym cztery z dniami bez przepływu), są przypadkami referencyjnymi wzorów Hydrologa
(`tests/fixtures/formulas/camels-pl-cases.json`, ADR-0073). Każdy przypadek podaje próbę, na której
CAMELS-PL liczył sygnaturę, i każdy krok, w którym jego obliczenie różni się od obliczenia Hydrologa:
$Q_5$ i $Q_{95}$ to u CAMELS-PL najbliższa statystyka pozycyjna, a u Hydrologa interpolacja w pozycji
Weibulla, nachylenie CAMELS-PL ma punkty 34 i 67 % (kwantyle nieprzekroczenia 0,33 i 0,66), a częstość
Hydrologa przelicza się na mianownik CAMELS-PL. Wszystkie sygnatury poza BFI zgadzają się w tolerancji,
którą przypadek uzasadnia. Przypadki wskazują wydanie zbioru: rekord Zenodo 23275336, wersję 2.1.0,
DOI i skrót SHA-256 każdego czytanego pliku (Nogat CMP-6.10); nowsze wydanie zmienia je tylko świadomą
zmianą testów, bo wydanie może poprawiać wartości poprzedniego.

**BFI się nie zgadza, i to z powodu definicji, a nie arytmetyki.** CAMELS-PL filtruje szereg filtrem
Lyne’a–Hollicka ($\alpha$ = 0,925) dwukrotnie, naprzód i wstecz, z przepływem podstawowym nie większym
niż przepływ danego przejścia (czyli z przepływem szybkim obciętym do 0, jak w drukowanym wzorze 1
Ladsona i in. 2013), od $b = Q$ pierwszego dnia, tak jak metoda LH pakietu `baseflow` (Xie i in.
2020), na danych do 31 grudnia 2023 r. z pominiętymi lukami. Hydrolog stosuje standard Ladsona i in.
(2013) z podrozdziału 8.5: trzy przejścia, przepływ szybki nieobcinany i 30 wartości odbitych na każdym
końcu. Dwuprzejściowy filtr odtwarza BFI CAMELS-PL na wszystkich 139 wodowskazach bez brakujących dni
i na 824 z 869; BFI Hydrologa różni się od niego na trzynastu wodowskazach o −0,045 do +0,027, a od
wartości CAMELS-PL na wszystkich 869 wodowskazach nawet o 0,19:

| Wodowskaz | CAMELS-PL | Filtr dwuprzejściowy | Hydrolog |
|---|---|---|---|
| Jakuszyce (Kamienna) | 0,52 | 0,5182 | 0,5369 |
| Wisła (Wisła) | 0,45 | 0,4518 | 0,4790 |
| Nowy Sącz (Łubinka) | 0,44 | 0,4426 | 0,4649 |
| Brynica (Brynica) | 0,54 | 0,5415 | 0,5654 |
| Struga (Czarna) | 0,52 | 0,5214 | 0,5297 |
| Szembruk (Gardęga) | 0,73 | 0,7338 | 0,6889 |
| Łysek (Noteć) | 0,78 | 0,7778 | 0,7405 |
| Ciecholewy (Brda) | 0,93 | 0,9252 | 0,9203 |
| Konojad (Mogilnica) | 0,67 | 0,6673 | 0,6372 |
| Kłodzko (Nysa Kłodzka) | 0,65 | 0,6504 | 0,6606 |
| Osowiec (Biebrza) | 0,79 | 0,7907 | 0,7557 |
| Gozdowice (Odra) | 0,85 | 0,8520 | 0,8359 |
| Tczew (Wisła) | 0,78 | 0,7847 | 0,7919 |

Przypadki BFI są więc zapisane jako rozbieżność (Nogat CMP-5.2) z jej przyczyną, sprawdzoną drugim
źródłem, a nie ukryte. Zgodnie z podrozdziałem 8.5 porównuje się tylko BFI liczone tym samym filtrem:
BFI z CAMELS-PL i z Hydrologa nie są zamienne.

### Przykład 8.8: sygnatury Nysy Kłodzkiej w Kłodzku, 1952–2025

Wodowskaz Kłodzko (150160180, 1083 km²) ma w CAMELS-PL 2.1.0 pełny zapis bez brakujących dni, więc
próbą CAMELS-PL są wszystkie dni 74 lat hydrologicznych 1952–2025 (rok 1951 nie ma listopada i grudnia).
Przepływ jednostkowy [mm/d] tego wodowskazu z CAMELS-PL jest w pliku
`tests/fixtures/camels_pl/camels_pl_150160180.csv.gz` (opis i atrybucja:
`tests/fixtures/camels_pl/CAMELS_PL_ATTRIBUTION.txt`):

```python
import csv, gzip
import numpy as np
from hydrolog.statistics import (exceedance_values, fdc_slope, half_flow_date,
                                 high_flow_days, low_flow_days, zero_flow_fraction)

with gzip.open("tests/fixtures/camels_pl/camels_pl_150160180.csv.gz", "rt") as plik:
    wiersze = [w for w in csv.DictReader(plik) if w["date"] >= "1951-11-01"]
q = np.array([float(w["discharge_spec_obs"]) for w in wiersze])     # 27 029 dni, mm/d
rok = np.array([int(w["date"][:4]) + (w["date"][5:7] in ("11", "12")) for w in wiersze])

print(exceedance_values(q, [95.0, 5.0]))          # [0.265 2.672]
print(fdc_slope(q[q > 0], 34, 67))                # 1.788204805673388
print(high_flow_days(q))                          # 1.554 d/rok, 1.620 d (115 dni, 71 zdarzeń)
print(low_flow_days(q))                           # 3.486 d/rok, 3.686 d (258 dni, 70 zdarzeń)
print(zero_flow_fraction(q))                      # 0.0
print(np.mean([half_flow_date(q[rok == r]) for r in np.unique(rok)]))   # 174.2027...
```

| Sygnatura CAMELS-PL | CAMELS-PL 2.1.0 | Hydrolog |
|---|---|---|
| `Q5` [mm/d] | 0,27 | 0,265 |
| `Q95` [mm/d] | 2,67 | 2,672 |
| `slope_fdc` | 1,79 | 1,788 |
| `high_q_freq` [d/rok] / `high_q_dur` [d] | 1,55 / 1,62 | 1,554 / 1,620 |
| `low_q_freq` [d/rok] / `low_q_dur` [d] | 3,49 / 3,69 | 3,486 / 3,686 |
| `zero_q_freq` | 0,0 | 0 |
| `hfd_mean` [dzień roku] | 174,2 | 174,20 |
| `baseflow_index` | 0,65 | 0,661 |

Bez luk mianowniki częstości są te same, a statystyki pozycyjne wokół pozycji Weibulla i najbliższej
są równe, więc sygnatury zgadzają się co do ostatniej drukowanej cyfry. Połowa odpływu przypada średnio
na 174. dzień roku hydrologicznego, czyli około 23 kwietnia: wezbrania roztopowe z Sudetów przesuwają
ją na wiosnę. BFI Hydrologa (`baseflow_index(okno, lyne_hollick_filter(okno))` na 26 663 dniach od
1951-01-01 do 2023-12-31, oknie CAMELS-PL) wynosi 0,661 wobec 0,65 z CAMELS-PL; filtr dwuprzejściowy
daje 0,650.

## 8.8. Podsumowanie

- Charakterystyki z szeregu dobowego i z danych IMGW-PIB to różne wielkości: średnie się zgadzają,
  ekstrema nie. Do celów prawnych ($SNQ$) i porównań z publikacjami IMGW-PIB używaj charakterystyk
  IMGW-PIB z co najmniej 20, a najlepiej 30 lat.
- Krzywa czasu trwania opisuje okres, a nie prawdopodobieństwo; dla przepływów stosuj klasy logarytmiczne.
  Przedział ufności ma medianowa krzywa roczna (lata niezależne), nie krzywa z całego okresu.
- Liczby i deficyty niżówek zależą od progu i reguł łączenia; podawaj je razem z wynikiem.
- Rozkład minimów zakłada brak trendu; puste kwantyle i trend minimów są sygnałem, że analiza częstości
  nie opisuje obecnych warunków.
- BFI i stała recesji zależą od metody (parametr filtru, definicja odcinków recesji); porównuj tylko
  wartości liczone tak samo.
- Sygnatura zależy od próby (okres, lata z lukami, mianownik częstości) i od konwencji jej obliczenia;
  porównując ją z CAMELS-PL, odtwórz jego próbę, a BFI z CAMELS-PL porównuj tylko z filtrem
  dwuprzejściowym.

## Źródła

- Addor N., Newman A.J., Mizukami N., Clark M.P. (2017). The CAMELS data set: catchment attributes and
  meteorology for large-sample studies. *Hydrology and Earth System Sciences* 21, 5293–5313.
  https://hess.copernicus.org/articles/21/5293/2017/ ; kod sygnatur: https://github.com/naddor/camels
- Brzezińska W., Marcinkowski P., Dolich A., Perz A.E., Maharjan A., Piniewski M., Kardel I., Loritz R.,
  Wrzesiński D. (2026). *CAMELS-PL: hydro-meteorological time series and landscape attributes for 869
  catchments in Poland*, wersja 2.1.0 [zbiór danych]. Zenodo, rekord 23275336, CC BY 4.0.
  https://doi.org/10.5281/zenodo.23275336
- Court A. (1962). Measures of streamflow timing. *Journal of Geophysical Research* 67(11), 4335–4339.
  Niedostępne w otwartym dostępie.
- Fleig A.K., Tallaksen L.M., Hisdal H., Demuth S. (2006). A global evaluation of streamflow drought
  characteristics. *Hydrology and Earth System Sciences* 10, 535–552.
  https://hess.copernicus.org/articles/10/535/2006/
- Helsel D.R., Hirsch R.M. (2002). *Statistical Methods in Water Resources*. Techniques of
  Water-Resources Investigations of the U.S. Geological Survey, book 4, chapter A3.
  https://pubs.usgs.gov/twri/twri4a3/twri4a3.pdf
- IMGW-PIB (2023). *Rocznik hydrologiczny 2022*. Instytut Meteorologii i Gospodarki Wodnej – Państwowy
  Instytut Badawczy, Warszawa (definicje przepływów charakterystycznych, s. 5–8).
- IMGW-PIB. *Słownik dla mediów — najważniejsze pojęcia i zwroty w hydrologii*.
  https://www.imgw.pl/sites/default/files/inline-files/slownik-dla-mediow_chok.pdf
- Ladson A.R., Brown R., Neal B., Nathan R. (2013). A standard approach to baseflow separation using the
  Lyne and Hollick filter. *Australasian Journal of Water Resources* 17(1), 25–34. Rękopis autorski, kod
  i arkusz: https://github.com/TonyLadson/BaseflowSeparation_LyneHollick
- Loritz R., Dolich A., Acuña Espinoza E. i in. (2024). CAMELS-DE: hydro-meteorological time series and
  attributes for 1582 catchments in Germany. *Earth System Science Data* 16, 5625–5642.
  https://essd.copernicus.org/articles/16/5625/2024/ ; kod sygnatur `08_hydrologic_attributes.ipynb`:
  https://github.com/CAMELS-DE/camels_de
- Lyne V., Hollick M. (1979). Stochastic time-variable rainfall-runoff modelling. Hydrology and Water
  Resources Symposium, Institution of Engineers Australia, Perth. Niedostępne w otwartym dostępie.
- Nathan R.J., McMahon T.A. (1990). Evaluation of automated techniques for base flow and recession
  analyses. *Water Resources Research* 26(7), 1465–1473. Niedostępne w otwartym dostępie.
- Ozga-Zieliński B., Walczykiewicz T. (red.) (2022). *Metody obliczania przepływu średniego niskiego
  SNQ*. IMGW-PIB, Warszawa.
  https://www.imgw.pl/sites/default/files/2022-01/imgw-pib-monografia-2022.01-metody-obliczania-przeplywu-sredniego-niskiego-sqn-calosc-min.pdf
- Rozporządzenie Ministra Infrastruktury z dnia 4 maja 2026 r. w sprawie warunków technicznych, jakim
  powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2026 poz. 692), § 4 pkt 10.
  https://dziennikustaw.gov.pl/D2026000069201.pdf
- Sawicz K., Wagener T., Sivapalan M., Troch P.A., Carrillo G. (2011). Catchment classification:
  empirical analysis of hydrologic similarity based on catchment function in the eastern USA. *Hydrology
  and Earth System Sciences* 15, 2895–2911. https://hess.copernicus.org/articles/15/2895/2011/
- Searcy J.K. (1959). *Flow-duration curves*. Manual of Hydrology, Part 2, Low-flow techniques. U.S.
  Geological Survey Water-Supply Paper 1542-A. https://pubs.usgs.gov/wsp/1542a/report.pdf
- Tallaksen L.M., van Lanen H.A.J. (red.) (2004). *Hydrological Drought: Processes and Estimation Methods
  for Streamflow and Groundwater*. Elsevier, Amsterdam. Niedostępne w otwartym dostępie.
- Tokarczyk T. (2010). *Niżówka jako wskaźnik suszy hydrologicznej*. Monografie IMGW, Warszawa.
  https://bibliotekanauki.pl/books/2080712.pdf
- Tomaszewski E. (2012). *Wieloletnia i sezonowa dynamika niżówek w rzekach środkowej Polski*.
  Wydawnictwo Uniwersytetu Łódzkiego, Łódź.
  https://dspace.uni.lodz.pl/xmlui/bitstream/handle/11089/41804/Tomaszewski_Wieloletnia.pdf?sequence=1
- Vogel R.M., Fennessey N.M. (1994). Flow-duration curves. I: New interpretation and confidence
  intervals. *Journal of Water Resources Planning and Management* 120(4), 485–504. Kopia autorska:
  https://sites.tufts.edu/richardvogel/files/2019/04/flowDuration1.pdf
- Wałęga A., Młyński D., Kokoszka R. (2014). Weryfikacja wybranych metod empirycznych do obliczania
  przepływów minimalnych i średnich w zlewniach dorzecza Dunajca. *Infrastruktura i Ekologia Terenów
  Wiejskich* II/3, 825–837.
- Westerberg I.K., McMillan H.K. (2015). Uncertainty in hydrological signatures. *Hydrology and Earth
  System Sciences* 19, 3951–3968. https://hess.copernicus.org/articles/19/3951/2015/
- WMO (2008). *Manual on Low-flow Estimation and Prediction* (red. A. Gustard, S. Demuth), Operational
  Hydrology Report No. 50, WMO-No. 1029. Genewa. https://library.wmo.int/idurl/4/32176
- Xie J., Liu X., Wang K., Yang T., Liang K., Liu C. (2020). Evaluation of typical methods for baseflow
  separation in the contiguous United States. *Journal of Hydrology* 583, 124628. Niedostępne
  w otwartym dostępie; pakiet `baseflow`: https://github.com/xiejx5/baseflow

Dane przykładów: źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy
Instytut Badawczy; dane IMGW-PIB zostały przetworzone (regulamin:
https://danepubliczne.imgw.pl/regulations).

Dane przykładu 8.8 (CAMELS-PL 2.1.0, wybór wierszy i kolumn):

- Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy
- Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone
- Źródło danych: CAMELS-PL 2.1.0 (Brzezińska i in., 2026), https://doi.org/10.5281/zenodo.23275336, licencja CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- Dane CAMELS-PL zostały przetworzone
