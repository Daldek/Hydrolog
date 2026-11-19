# 8. Przepływy charakterystyczne i niżówki

Rozdział opisuje statystyki, którymi charakteryzuje się reżim ilościowy przekroju wodowskazowego na co
dzień, a nie tylko w czasie wezbrań: przepływy charakterystyczne pierwszego i drugiego stopnia, krzywą
sum czasów trwania przepływów, niżówki z ich czasem trwania i deficytem odpływu, rozkład minimów
rocznych, przepływ podstawowy i recesję. Wszystkie te wielkości liczy się z szeregu przepływów dobowych
(albo z charakterystyk półrocznych IMGW-PIB) w ustalonym okresie odniesienia, zwykle 30-letnim.

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
<!-- /spec:characteristic_first_degree -->

<!-- spec:characteristic_second_degree -->
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
<!-- /spec:exceedance_values -->

Hydrolog liczy wartości krzywej metodą pozycji (Vogel i Fennessey 1994): $n$ wartości dobowych
uporządkowanych malejąco dostaje pozycje Weibulla, a wartość dla dowolnego procentu interpoluje się
liniowo między sąsiednimi pozycjami. Klasyczna metoda klas (Searcy 1959; WMO 2008, § 6.1) dzieli wartości
na przedziały i sumuje dni od klasy najwyższej; Hydrolog podaje ją obok, jako tabelę klas z sumami dni
„wraz z wyższymi” i „wraz z niższymi” oraz klasą modalną (najczęstszą). Dla długich szeregów obie metody
dają prawie te same wartości; różnią się w skrajnych procentach i w krótkich szeregach.

<!-- spec:duration_curve_days -->
<!-- /spec:duration_curve_days -->

<!-- spec:duration_classes -->
<!-- /spec:duration_classes -->

Klasy o równej szerokości nadają się do stanów wody (np. co 10 cm). Rozkład przepływów jest silnie
skośny, więc klasy równej szerokości wrzucają prawie wszystkie dni do najniższej klasy; dla przepływów
należy wybrać klasy logarytmiczne (`--bin-method log`). Krzywą jednego miesiąca kalendarzowego
z wszystkich lat daje opcja `--month`.

Zastosowania: przepływy niskie i średnie z krzywej ($Q_{70\%}$, $Q_{90\%}$, $Q_{95\%}$) jako progi
niżówek (p. 8.3) i wskaźniki zasobów, porównanie zlewni (krzywa stroma — reżim zmienny, płaska — wyrównany
przez retencję), ocena, przez ile dni w roku dostępny jest przepływ potrzebny do poboru wody.

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

## 8.3. Niżówki: metoda progowa, czas trwania i deficyt

Niżówka (ang. *low-flow event*, *streamflow drought*) to okres, w którym przepływ jest niższy od
przyjętego przepływu granicznego (IMGW-PIB, Słownik dla mediów). Metoda progowa (ang. *threshold level
method*; WMO 2008, rozdz. 8; Tallaksen i van Lanen 2004) opisuje każde zdarzenie początkiem, końcem,
czasem trwania, przepływem najniższym i deficytem (niedoborem) odpływu (ang. *deficit volume*), czyli
objętością wody, której zabrakło do progu. Dwa zdarzenia rozdzielone krótką przerwą (kilka dni
z przepływem powyżej progu) są zwykle jednym zjawiskiem, dlatego się je łączy (ang. *pooling*), a bardzo
krótkie zdarzenia pomija.

<!-- spec:threshold_runs -->
<!-- /spec:threshold_runs -->

<!-- spec:low_flow_sequences -->
<!-- /spec:low_flow_sequences -->

<!-- spec:low_flow_deficit_volumes -->
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
<!-- /spec:non_exceedance_positions -->

Hydrolog dopasowuje metodą największej wiarygodności uogólniony rozkład wartości ekstremalnych minimów,
obejmujący rozkład Gumbela dla minimów i trójparametrowy rozkład Weibulla (III typ Fishera–Tippetta):

<!-- spec:fisher_tippett_minima -->
<!-- /spec:fisher_tippett_minima -->

Dodatni parametr kształtu $c$ oznacza, że minima mają dolne ograniczenie (rozkład Weibulla); kwantyle
długich okresów zbliżają się wtedy do tego ograniczenia. WMO (2008, § 7.5) zaleca rozkład Weibulla
z dolnym ograniczeniem nieujemnym i odradza rozkład Gumbela dla minimów, który nie ma dolnej granicy.
W polskiej praktyce do minimów stosowano metodę Gumbela opartą na III typie rozkładu wartości najmniejszych
(Wałęga i in. 2014); urzędowo zalecanego rozkładu minimów rocznych w przeglądzie literatury do tego
podręcznika nie znaleziono.

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

Parametry: $c = 0{,}566$, położenie 0,3527 m³/s, skala 0,1527 m³/s; kształt dodatni, więc minima mają
dolne ograniczenie.

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
kwantyle 100, 500 i 1000 lat byłyby ujemne i zostały pominięte. Najniższe minima roczne okresu są
bardzo bliskie zera: 0,004 m³/s w 2018 r. i 0,023 m³/s w 2006 r.

Cały zapis 1973–2025 (50 lat):

```sh
hydrolog stats low-flow --half-year-file docs/podrecznik/dane/czarna_woda_bukowna_Q_polroczne_1973_2025.csv
```

daje $Q_{100} = 0{,}0089$ m³/s, a puste są tylko kwantyle 500 i 1000 lat (zero raz na 348,7 roku). Wynik
zależy więc mocno od okresu. Przyczynę pokazuje test trendu minimów całego zapisu:

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
<!-- /spec:lyne_hollick -->

Filtr nie jest modelem fizycznym (Ladson i in. 2013): jego wynik zależy od parametru $\alpha$
i liczby przejść. Domyślne $\alpha$ Hydrologa pochodzi od Nathana i McMahona (1990), którzy uznali je za
zadowalające przy porównaniu z rozdziałem ręcznym; Ladson i in. (2013) uzyskali dla większego $\alpha$
lepszą zgodność z metodami znacznikowymi. Zakres sprawdzonych wartości podaje ramka; wartość spoza niego
daje uwagę. Wynik zawsze trzeba podawać z $\alpha$ i porównywać tylko indeksy liczone tym samym filtrem.

Szereg z lukami filtruje się odcinkami bez luk, a wskaźnik roczny tylko dla roku z dostatecznie wieloma
dniami; obie reguły są własnymi regułami Hydrologa (ADR-0031), bez źródła publikowanego:

<!-- spec:baseflow_spans -->
<!-- /spec:baseflow_spans -->

Wskaźnik przepływu podstawowego BFI (ang. *baseflow index*) to stosunek objętości przepływu podstawowego
do objętości całego przepływu w okresie albo w roku (WMO 2008, § 5.2):

<!-- spec:baseflow_index -->
<!-- /spec:baseflow_index -->

<!-- spec:baseflow_index_by_year -->
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
<!-- /spec:recession_constant -->

<!-- spec:recession_without_segment -->
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

## 8.7. Podsumowanie

- Charakterystyki z szeregu dobowego i z danych IMGW-PIB to różne wielkości: średnie się zgadzają,
  ekstrema nie. Do celów prawnych ($SNQ$) i porównań z publikacjami IMGW-PIB używaj charakterystyk
  IMGW-PIB z co najmniej 20, a najlepiej 30 lat.
- Krzywa czasu trwania opisuje okres, a nie prawdopodobieństwo; dla przepływów stosuj klasy logarytmiczne.
- Liczby i deficyty niżówek zależą od progu i reguł łączenia; podawaj je razem z wynikiem.
- Rozkład minimów zakłada brak trendu; puste kwantyle i trend minimów są sygnałem, że analiza częstości
  nie opisuje obecnych warunków.
- BFI i stała recesji zależą od metody (parametr filtru, definicja odcinków recesji); porównuj tylko
  wartości liczone tak samo.

## Źródła

- Fleig A.K., Tallaksen L.M., Hisdal H., Demuth S. (2006). A global evaluation of streamflow drought
  characteristics. *Hydrology and Earth System Sciences* 10, 535–552.
  https://hess.copernicus.org/articles/10/535/2006/
- IMGW-PIB (2023). *Rocznik hydrologiczny 2022*. Instytut Meteorologii i Gospodarki Wodnej – Państwowy
  Instytut Badawczy, Warszawa (definicje przepływów charakterystycznych, s. 5–8).
- IMGW-PIB. *Słownik dla mediów — najważniejsze pojęcia i zwroty w hydrologii*.
  https://www.imgw.pl/sites/default/files/inline-files/slownik-dla-mediow_chok.pdf
- Ladson A.R., Brown R., Neal B., Nathan R. (2013). A standard approach to baseflow separation using the
  Lyne and Hollick filter. *Australasian Journal of Water Resources* 17(1), 25–34. Rękopis autorski, kod
  i arkusz: https://github.com/TonyLadson/BaseflowSeparation_LyneHollick
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
- WMO (2008). *Manual on Low-flow Estimation and Prediction* (red. A. Gustard, S. Demuth), Operational
  Hydrology Report No. 50, WMO-No. 1029. Genewa. https://library.wmo.int/idurl/4/32176

Dane przykładów: źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy
Instytut Badawczy; dane IMGW-PIB zostały przetworzone (regulamin:
https://danepubliczne.imgw.pl/regulations).
