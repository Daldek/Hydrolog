# 9. Reżim odpływu i jego zmienność

Reżim rzeczny (*river regime*) to powtarzający się z roku na rok rytm zasilania i odpływu rzeki: kiedy rzeka niesie
najwięcej wody, kiedy najmniej i jak wyraźne są te pory. W Polsce rytm ten kształtują przede wszystkim roztopy
(zasilanie śnieżne, niwalne) i deszcze (zasilanie deszczowe, pluwialne). Rozdział opisuje miary, którymi Hydrolog
charakteryzuje reżim: współczynniki Pardégo, typ reżimu według Dynowskiej, wskaźnik sezonowości Walsha i Lawlera,
statystykę kołową terminów wezbrań i niżówek oraz analizę harmoniczną cyklu rocznego. Dwa ostatnie podrozdziały
dotyczą stanów wody: krzywej natężenia przepływu, która zamienia stany na przepływy, i stref stanów wody
Rybczyńskiego.

Wszystkie te miary opisują przeciętny rok wielolecia albo zbiór wartości z wielu lat. Same nie rozstrzygają, czy
reżim się zmienia; do tego służą testy trendu i jednorodności z rozdziału 10.

## Dane przykładów

Przykłady korzystają z dwóch szeregów stacji IMGW-PIB:

- **Nysa Kłodzka – Kłodzko** (150160180): dobowe stany wody i przepływy z lat hydrologicznych 1951–2025, wyeksportowane
  z Obserwatora do pliku `docs/podrecznik/dane/klodzko_1951_2025.csv.gz` (opis pliku, polecenie eksportu i atrybucja:
  `docs/podrecznik/dane/README.md`). W publicznych danych IMGW-PIB brakuje całego roku hydrologicznego 1997, czyli
  roku powodzi lipcowej. Hydrolog zgłasza to uwagą `missing_values_removed` i liczy z pozostałych dni.
- **Warszawa-Okęcie** (352200375): dobowe temperatury powietrza i opady z lat 1991–2020, plik testowy Hydrologa
  `tests/fixtures/warszawa_okecie_1991_2020.csv.gz`.

Hydrolog czyta pliki tekstowe, więc oba pliki trzeba najpierw rozpakować (polecenia uruchamiamy z katalogu głównego
repozytorium Hydrologa):

```bash
gzip -dk docs/podrecznik/dane/klodzko_1951_2025.csv.gz
gzip -dk tests/fixtures/warszawa_okecie_1991_2020.csv.gz
```

Każde polecenie z tego rozdziału wypisuje podsumowanie wyniku; z opcją `--json` wypisuje cały wynik jako dokument JSON.

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy. Dane
Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone. Regulamin danych
IMGW-PIB: https://danepubliczne.imgw.pl/regulations

## 9.1. Rok hydrologiczny

Statystyki przepływów w Polsce liczy się w latach hydrologicznych (*hydrological year*). Rok hydrologiczny IMGW-PIB
zaczyna się jesienią, gdy zasoby wody w zlewni (śnieg, wilgotność gleby, wody gruntowe) są najmniejsze i najbardziej
podobne z roku na rok. Dzięki temu opady zimy i wywołany nimi odpływ roztopowy należą do tego samego roku
(IMGW-PIB, opis danych hydrologicznych). Definicję, której używa Hydrolog, podaje ramka.

<!-- spec:hydrological_year -->
<!-- /spec:hydrological_year -->

W wynikach poleceń `stats` miesiące następują w kolejności roku hydrologicznego (pole `months`), a opcje
`--first-year` i `--last-year` wskazują lata hydrologiczne, nazwane tak jak u IMGW-PIB.

**Typowe błędy.** Liczenie średnich miesięcznych i ekstremów w latach kalendarzowych i porównywanie ich z rocznikami
IMGW-PIB: wezbranie roztopowe z przełomu roku trafia wtedy do innego roku niż w roczniku. Przypisanie jesiennych
miesięcy do roku kalendarzowego zamiast do następnego roku hydrologicznego.

## 9.2. Współczynniki Pardégo

**Idea.** Średni przepływ miesiąca zależy przede wszystkim od wielkości zlewni, więc liczby z różnych rzek trudno
porównać. Współczynnik Pardégo (*Pardé coefficient*) dzieli średni przepływ miesiąca w wieloleciu przez średni przepływ
z wielolecia (Pardé 1933; BAWiki; Wrzesiński 2017). Otrzymana liczba nie ma wymiaru i pokazuje kształt rocznego rytmu
odpływu niezależnie od wielkości rzeki: wartość większa od jedności oznacza miesiąc zasobniejszy w wodę od
przeciętnego, mniejsza – uboższy. Polskie prace podają te współczynniki w procentach średniego przepływu rocznego
(Wrzesiński 2017; Perz 2019).

<!-- spec:parde_coefficients -->
<!-- /spec:parde_coefficients -->

**Jak Hydrolog liczy średnie.** Średni przepływ miesiąca to średnia wszystkich dni tego miesiąca kalendarzowego we
wszystkich latach okresu. Średni przepływ z wielolecia to średnia wszystkich dni okresu, tak jak średni przepływ roku
u IMGW-PIB, a nie średnia dwunastu średnich miesięcznych. Dlatego suma dwunastu współczynników nie jest dokładnie
równa liczbie miesięcy: miesiące mają różną liczbę dni. Dzień bez wartości nie wchodzi do żadnej średniej, a gdy braki
skupiają się w kilku miesiącach, średnia z wielolecia przesuwa się ku miesiącom lepiej obserwowanym. Sposób, w jaki
polecenie `stats regime` układa szereg dobowy na kalendarzu, opisuje ramka:

<!-- spec:flow_regime_of_a_daily_series -->
<!-- /spec:flow_regime_of_a_daily_series -->

**Udział wiosenny.** Obok współczynników Hydrolog podaje udział marca i kwietnia w objętości odpływu przeciętnego
roku. To wskaźnik opisowy przyjęty w Hydrologu (ADR-0031), nie wielkość z literatury. Przydaje się przy porównywaniu
rzek z wyraźnym wezbraniem roztopowym.

<!-- spec:spring_share -->
<!-- /spec:spring_share -->

**Zakres stosowania.** Współczynniki opisują przeciętny rok wielolecia, więc mają sens dla okresu na tyle długiego,
by uśrednić lata mokre i suche; polskie opracowania liczą je z kilkudziesięciu lat (Wrzesiński 2017). Kilka lat
opisuje tylko te lata, a nie reżim rzeki. Polecenie `stats regime` wymaga wartości w każdym miesiącu kalendarzowym,
a dla okresu krótszego od zalecanego zgłasza uwagę `short_reference_period`.

**Typowe zastosowania.** Porównanie rzek i regionów (mapy typów reżimu), klasyfikacja typu reżimu (p. 9.3), ocena
zmian rytmu odpływu między okresami, wskazanie miesięcy krytycznych dla poboru wody, żeglugi czy energetyki wodnej.

**Typowe błędy.** Porównywanie współczynników z różnych okresów bez podania okresów. Mieszanie procentów i ułamków.
Porównywanie z publikacjami współczynników liczonych od średniej dwunastu miesięcy, a nie od średniej wszystkich dni.
Okres z długą przerwą w danych bez sprawdzenia, które miesiące ta przerwa objęła.

### Przykład: reżim Nysy Kłodzkiej w Kłodzku w czterech okresach

```bash
hydrolog stats regime --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --first-year 1951 --last-year 1980
hydrolog stats regime --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --first-year 1971 --last-year 2015
hydrolog stats regime --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020
hydrolog stats regime --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --first-year 1951 --last-year 2025
```

Współczynniki Pardégo (pole `parde`), średni przepływ z wielolecia (`annual_mean`), udział marca i kwietnia
(`spring_share`) i wskaźnik sezonowości (`seasonality_index`, p. 9.4):

| Okres | XI | XII | I | II | III | IV | V | VI | VII | VIII | IX | X | $\bar Q$ [m³/s] | udział III–IV | SI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1951–1980 | 0,744 | 0,920 | 0,767 | 0,841 | 1,178 | 1,599 | 1,371 | 1,059 | 1,213 | 0,968 | 0,708 | 0,621 | 12,77 | 0,231 | 0,242 |
| 1971–2015 | 0,739 | 0,933 | 1,015 | 0,936 | 1,457 | 1,569 | 1,138 | 1,000 | 0,992 | 0,829 | 0,749 | 0,639 | 12,77 | 0,253 | 0,206 |
| 1991–2020 | 0,698 | 0,812 | 1,046 | 1,093 | 1,636 | 1,611 | 1,106 | 0,986 | 0,854 | 0,660 | 0,787 | 0,722 | 12,50 | 0,271 | 0,243 |
| 1951–2025 | 0,735 | 0,901 | 0,938 | 0,996 | 1,374 | 1,563 | 1,212 | 1,004 | 0,978 | 0,829 | 0,806 | 0,666 | 12,44 | 0,245 | 0,196 |

Okresy 1971–2015, 1991–2020 i 1951–2025 obejmują rok 1997 bez danych, więc liczą 44, 29 i 74 lata; dla 29 lat
Hydrolog zgłasza uwagę `short_reference_period`.

**Jak czytać wynik.** W latach 1951–1980 najzasobniejszy w wodę był kwiecień, a lipiec miał drugie, letnie maksimum.
W latach 1991–2020 największy współczynnik ma marzec, wzrosły współczynniki stycznia i lutego, a lato jest uboższe w
wodę (lipiec 0,854, sierpień 0,660). Średni przepływ z wielolecia zmienił się niewiele (12,77 i 12,50 m³/s), więc
zmieniło się przede wszystkim rozłożenie odpływu w roku. Czy jest to trwała zmiana, czy wynik kilku nietypowych lat,
rozstrzygają testy z rozdziału 10. Przyczyn trzeba szukać w danych klimatycznych i w historii zlewni; współczynniki
ich nie wskazują.

## 9.3. Typy reżimu według Dynowskiej

**Idea i historia.** Dynowska (1997) podzieliła rzeki Polski na pięć typów reżimu według udziału zasilania śnieżnego
i deszczowego: trzy typy niwalne (słabo, średnio i silnie wykształcony), typ niwalno-pluwialny i typ
pluwialno-niwalny. Typy niwalne różnią się wielkością wezbrania roztopowego, czyli współczynnikiem Pardégo miesiąca
wiosennego. Typ niwalno-pluwialny ma ponadto wyraźny wzrost przepływu latem, a typ pluwialno-niwalny – miesiąc letni
co najmniej prawie tak zasobny jak wiosenny. Arkusza Atlasu Rzeczypospolitej Polskiej z tą klasyfikacją nie ma w
otwartym dostępie; jej kryteria przytaczają Wrzesiński (2017, s. 255; 2018, s. 250) i Perz (2019, s. 79). Nie należy
jej mylić ze starszą typologią Dynowskiej (1971), która wyróżnia trzy typy główne (reżim wyrównany, umiarkowany i
niewyrównany) i 13 podtypów według zmienności przepływu, rodzaju zasilania i pory wezbrań (Wrzesiński 2017,
s. 253–254).

<!-- spec:dynowska_regime_type -->
<!-- /spec:dynowska_regime_type -->

**Co Hydrolog dopowiada do źródeł.** Źródła nie mówią jednoznacznie, który miesiąc jest „wiosenny”, a który „letni”,
nie podają liczby dla słów „prawie równy” i nie ustalają kolejności sprawdzania kryteriów. Hydrolog przyjmuje własne
odczytanie (ADR-0031, ADR-0063), opisane w ramce: miesiąc wiosenny to większy z marca i kwietnia, miesiąc letni –
największy z czerwca, lipca i sierpnia, a kryteria są sprawdzane od typu pluwialno-niwalnego. Zastrzeżenia „na ogół”
w opisie typów niwalno-pluwialnego i pluwialno-niwalnego Hydrolog nie sprawdza. Pole `regime_type.criteria` wyniku
pokazuje, które miesiące i które współczynniki zdecydowały o typie. Gdyby arkusz Atlasu rozstrzygał te kwestie
inaczej, typ niektórych rzek się zmieni; to otwarta kwestia źródłowa.

**Interpretacja.** Typ jest skrótem współczynników. Podawaj go zawsze razem z nimi: gdy współczynnik leży blisko
progu klasyfikacji, typ zależy od zaokrągleń danych i od wyboru lat.

### Przykład: typ reżimu Nysy Kłodzkiej w Kłodzku

Te same cztery wywołania `stats regime` co w p. 9.2 (pole `regime_type`):

| Okres | Miesiąc wiosenny | Współczynnik | Miesiąc letni | Współczynnik | Typ |
|---|---|---|---|---|---|
| 1951–1980 | IV | 1,599 | VII | 1,213 | 4 – niwalno-pluwialny |
| 1971–2015 | IV | 1,569 | VI | 1,00013 | 4 – niwalno-pluwialny |
| 1991–2020 | III | 1,636 | VI | 0,986 | 2 – niwalny średnio wykształcony |
| 1951–2025 | IV | 1,563 | VI | 1,004 | 4 – niwalno-pluwialny |

Wynik dla lat 1971–2015 zgadza się z oceną Perza (2019, s. 79), który zalicza Nysę Kłodzką poniżej Międzylesia w tym
okresie do typu niwalno-pluwialnego. Czerwcowy współczynnik (1,00013) przekracza jednak próg wzrostu letniego
zaledwie o 0,00013 – znacznie mniej, niż wynosi dokładność przepływów dobowych (trzy cyfry znaczące). Przy minimalnie
mniejszym przepływie czerwca typ byłby niwalny średnio wykształcony, jak w latach 1991–2020. Zmiana typu między
okresami nie dowodzi więc sama zmiany reżimu: w tabeli z p. 9.2 widać, że kształt rocznego rytmu zmieniał się
stopniowo, a typ przeskoczył, gdy jeden współczynnik przekroczył próg.

## 9.4. Wskaźnik sezonowości Walsha i Lawlera

**Idea.** Wskaźnik sezonowości (*seasonality index*, SI) opisuje jedną liczbą, jak nierówno rozkłada się objętość
roczna na miesiące. Walsh i Lawler (1981) zaproponowali go dla opadów (rozdział 11); Hydrolog stosuje ten sam wzór do
miesięcznych objętości odpływu przeciętnego roku (ADR-0031). Wskaźnik jest najmniejszy, gdy wszystkie miesiące są
równe, a największy, gdy całość przypada na jeden miesiąc (zakres w ramce).

<!-- spec:seasonality_index -->
<!-- /spec:seasonality_index -->

**Jak czytać.** Klasy Walsha i Lawlera (`si_class`, rozdział 11) opisano dla opadów, dlatego dla odpływu Hydrolog
podaje tylko liczbę. Wskaźnik policzony z miesięcy przeciętnego roku jest mniejszy od średniej wskaźników
poszczególnych lat, bo uśrednianie wygładza różnice między latami (Sumner i in. 2001); `stats regime` podaje ten
pierwszy.

**Przykład.** Wskaźniki z tabeli w p. 9.2: 0,242 w latach 1951–1980 i 0,243 w latach 1991–2020. Liczby są prawie
równe, choć rytm odpływu w obu okresach jest inny: w pierwszym dwa maksima (kwiecień i lipiec), w drugim jedno,
marcowe. SI mówi, jak nierówny jest rozkład odpływu w roku, ale nie mówi, kiedy przypadają miesiące zasobne; czytaj go
razem ze współczynnikami Pardégo.

## 9.5. Sezonowość wezbrań i niżówek: statystyka kołowa

**Idea.** Kalendarz jest kołem: koniec grudnia sąsiaduje z początkiem stycznia. Zwykła średnia numerów dni zawodzi:
maksimum z 30 grudnia i maksimum z 2 stycznia dają „średni termin” na początku lipca. Statystyka kołowa (*circular
statistics*) zamienia każdą datę na kąt na okręgu roku i uśrednia wektory jednostkowe. Kierunek wektora średniego
wskazuje średni termin, a jego długość $r$ – koncentrację (skupienie) terminów: od zera, gdy terminy rozkładają się
równomiernie w roku, do jedności, gdy wszystkie przypadają na ten sam dzień (Bayliss i Jones 1993; Burn 1997; Hall i
Blöschl 2018).

<!-- spec:circular_mean -->
<!-- /spec:circular_mean -->

**Które daty.** Z szeregu dobowego Hydrolog bierze maksimum (albo minimum) każdego pełnego roku hydrologicznego,
datowane pierwszym dniem, w którym wystąpiło; rok z brakującym dniem pomija i wymienia w uwadze. Z pliku półrocznego
IMGW-PIB (`--half-year-file`) bierze opublikowane ekstrema półroczy, które IMGW-PIB wyznacza ze wszystkich obserwacji,
a nie z wartości dobowych. Kąt każdej daty liczy na roku kalendarzowym, do którego data należy, a udziały półroczy –
według półroczy roku hydrologicznego:

<!-- spec:extremes_of_complete_years -->
<!-- /spec:extremes_of_complete_years -->

<!-- spec:circular_mean_of_dates -->
<!-- /spec:circular_mean_of_dates -->

<!-- spec:seasonality_of_extremes -->
<!-- /spec:seasonality_of_extremes -->

**Założenia i zakres.** Jedno ekstremum na rok i niezależne zdarzenia. Przy małym $r$ średni termin traci sens:
gdy wezbrania mają dwie pory, średni kierunek może wskazać miesiąc, w którym wezbrań prawie nie ma. Hall i Blöschl
(2018) analizują tylko stacje, na których test Rayleigha odrzuca równomierny rozkład terminów; Hydrolog tego testu nie
liczy. Maksimum z przepływów dobowych (średnich z doby) jest zwykle niższe od maksimum IMGW-PIB wyznaczonego ze
wszystkich obserwacji i może wystąpić innego dnia (rozdział 8).

**Typowe błędy.** Średnia arytmetyczna numerów dni. Podawanie średniego terminu bez koncentracji $r$. Wybieranie
maksimów w latach kalendarzowych, gdy wezbrania zimowe przechodzą przez przełom roku.

### Przykład: terminy maksimów i minimów rocznych w Kłodzku

```bash
hydrolog stats seasonality --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --parameter Q --statistic max
hydrolog stats seasonality --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --parameter Q --statistic min
```

| Wielkość (pole wyniku) | Maksima roczne | Minima roczne |
|---|---|---|
| Liczba lat (`years`) | 74 | 74 |
| Średni termin (`mean_date`, `mean_day`) | 9 maja (dzień 129,4) | 11 października (dzień 283,9) |
| Koncentracja $r$ (`concentration`) | 0,213 | 0,478 |
| Udział półrocza zimowego (`winter_share`) | 0,459 | 0,419 |
| Udział półrocza letniego (`summer_share`) | 0,541 | 0,581 |

Liczba maksimów rocznych w poszczególnych miesiącach (policzona z listy `years` wyniku):

| I | II | III | IV | V | VI | VII | VIII | IX | X | XI | XII |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 12 | 2 | 8 | 8 | 10 | 8 | 4 | 2 | 2 | 3 |

**Jak czytać wynik.** Wezbrania w Kłodzku mają dwie pory: zimowo-wiosenną (roztopy i odwilże, styczeń–marzec) i
letnią (deszcze, maj–sierpień). Średni termin, 9 maja, wypada między nimi, a mała koncentracja ($r = 0{,}213$)
ostrzega, że nie jest to typowy termin wezbrania. Największe przepływy dobowe wielolecia to 707 m³/s
(15 września 2024 r.), 424 m³/s (27 czerwca 2009 r.) oraz po 298 m³/s (3 sierpnia 1977 r. i 23 lipca 1998 r.) –
wszystkie letnie; wezbrania z lipca 1997 r. w danych nie ma. Warto zauważyć, że kwiecień, najzasobniejszy w wodę
miesiąc reżimu (p. 9.2), ma tylko dwa maksima roczne: roztopy podnoszą przepływ na wiele tygodni, a deszcze letnie
dają krótkie, wysokie kulminacje. Reżim i sezonowość ekstremów to różne cechy rzeki.

Minima roczne są skupione silniej ($r = 0{,}478$): 55 z 74 przypada na lipiec–listopad, a druga, mniejsza grupa na
styczeń (10 lat) – to niżówki zimowe, gdy mróz zatrzymuje wodę w śniegu i lodzie.

## 9.6. Analiza harmoniczna cyklu rocznego

**Idea.** Cykl roczny wielkości, która zmienia się w roku płynnie i powtarzalnie (temperatura powietrza i wody), daje
się przybliżyć sumą średniej i kilku fal sinusoidalnych o okresach roku, pół roku itd. (harmonik, *harmonics*). Każda
harmonika ma amplitudę (połowę rozpiętości jej wahań), fazę (termin maksimum) i udział w wariancji szeregu.
Współczynniki dopasowuje się metodą najmniejszych kwadratów do wartości dobowych (Wilks 2011, rozdz. 9.4).

<!-- spec:harmonic_fit -->
<!-- /spec:harmonic_fit -->

Dzień maksimum harmoniki Hydrolog podaje jako dzień roku hydrologicznego. Polecenie `stats harmonics` dopasowuje
harmoniki do średniego cyklu całego okresu i osobno do każdego roku hydrologicznego z wystarczającą liczbą wartości:

<!-- spec:annual_cycle_of_a_daily_series -->
<!-- /spec:annual_cycle_of_a_daily_series -->

**Zakres stosowania.** Metoda zakłada cykl okresowy o długości przeciętnego roku. Opisuje dobrze przebieg temperatury;
przepływu – słabo, bo wezbrania są nieregularne. Trend w danych rozkłada się na harmoniki i zniekształca ich
amplitudy. Rok, którego luki nie pozwalają wyznaczyć cyklu, Hydrolog pomija i wymienia w uwadze `years_without_fit`.

**Typowe błędy.** Odczytywanie fazy harmoniki o pomijalnej amplitudzie (jej termin maksimum to szum zaokrągleń).
Dopasowanie harmonik do szeregu z wyraźnym trendem bez komentarza. Porównywanie dni maksimum liczonych od początku roku
hydrologicznego z dniami roku kalendarzowego.

### Przykład: cykl roczny temperatury powietrza w Warszawie

Dane zaczynają się 1 stycznia 1991 r., więc pierwszym pełnym rokiem hydrologicznym jest rok 1992:

```bash
hydrolog stats harmonics --input-file tests/fixtures/warszawa_okecie_1991_2020.csv --value-column Tmean --date-column date --first-year 1992 --last-year 2020
```

Wynik dla całego okresu (pole `period`, 10 593 dni; 29 lat, uwaga `short_reference_period`):

| Wielkość | Harmonika 1 (roczna) | Harmonika 2 (półroczna) |
|---|---|---|
| Amplituda | 10,86 °C | 0,07 °C |
| Dzień maksimum (roku hydrologicznego) | 258,9 (około 17 lipca) | 76,7 |
| Udział w wariancji | 0,782 | 0,00003 |

Średnia okresu wynosi 9,04 °C (lata hydrologiczne 1992–2020, więc nieco inny okres niż norma 1991–2020 z rozdziału
11), a obie harmoniki wyjaśniają razem 78,2% zmienności temperatur dobowych ($R^2 = 0{,}782$). Cykl jest prawie
sinusoidą: druga harmonika ma pomijalną amplitudę, więc jej termin nic nie znaczy. Maksimum cyklu przypada niespełna
cztery tygodnie po przesileniu letnim – to skutek bezwładności cieplnej podłoża i atmosfery. Pozostałe
22% zmienności to zmiany pogody z dnia na dzień, których cykl roczny nie opisuje. Pojedynczy rok jest mniej regularny:
dla roku hydrologicznego 1992 (pierwszy element listy `years`) amplituda pierwszej harmoniki wynosi 10,99 °C, drugiej
1,59 °C, a $R^2 = 0{,}862$.

Dla porównania przepływ Nysy Kłodzkiej:

```bash
hydrolog stats harmonics --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --first-year 1991 --last-year 2020
```

Pierwsza harmonika ma amplitudę 4,97 m³/s i maksimum na przełomie marca i kwietnia (dzień 151,6), ale obie harmoniki
wyjaśniają tylko 7,7% zmienności przepływów dobowych ($R^2 = 0{,}077$). Wezbrań nie da się opisać falą sinusoidalną; do
opisu rytmu odpływu służą współczynniki Pardégo (p. 9.2).

## 9.7. Krzywa natężenia przepływu

**Idea.** Stan wody (*water level, stage*) mierzy się codziennie albo co kilka minut, a przepływ tylko podczas
okresowych pomiarów hydrometrycznych. Przepływy dobowe IMGW-PIB oblicza ze stanów wody za pomocą krzywej natężenia
przepływu (krzywej przepływu, krzywej konsumcyjnej; *rating curve, stage–discharge relation*), a gdy krzywa się
zmienia, poprawia przepływy archiwalne (IMGW-PIB, Rocznik Hydrologiczny). Dla stabilnego profilu kontrolnego
zależność ta jest bliska funkcji potęgowej (WMO 2010, równ. 1.4).

<!-- spec:rating_curve -->
<!-- /spec:rating_curve -->

**Znaczenie parametrów.** $H_0$ to stan, przy którym przepływ ustaje (dla nieregularnego przekroju – stan przepływu
zerowego „efektywnego”). **To nie jest zero wodowskazu**, czyli poziom odniesienia łaty wodowskazowej (rzędna „P.z.”
w rocznikach IMGW-PIB); stany wody poniżej zera wodowskazu są czymś zwyczajnym. Współczynnik $a$ to przepływ przy
głębokości $H - H_0$ równej jednostce stanu, a jego jednostka zależy od jednostki stanu: ta sama krzywa ze stanami w
metrach ma inne $a$ niż ze stanami w centymetrach (ramka). Wykładnik $b$ zależy od rodzaju kontroli przepływu: inny
jest dla kontroli przekrojowej (próg, przelew, przewężenie), inny dla kontroli korytowej, gdzie o przepływie decyduje
opór całego odcinka koryta (WMO 2010, s. II.1-2 i II.1-8).

**Dopasowanie.** Hydrolog dopasowuje krzywą metodą najmniejszych kwadratów na przepływach. WMO (2010, rozdz. 1.12.2)
opisuje metodę najmniejszych kwadratów na logarytmach, w której krzywa jest prostą na papierze logarytmicznym. Obie
metody dają różne krzywe z tych samych par (przykład w ramce): na przepływach większą wagę mają duże przepływy (błędy
bezwzględne), na logarytmach wszystkie pomiary ważą tyle samo względnie. WMO zaleca, by pomiarów było wiele i by
obejmowały cały zakres stanów (WMO 2010, s. II.1-3).

<!-- spec:rating_curve_fit -->
<!-- /spec:rating_curve_fit -->

**Wiarygodność krzywej.** Krzywa dopasowana do par z dwóch różnych zależności (przeniesione zero wodowskazu, rozmyte
albo zamulone koryto) ma zwykle bardzo stromy wykładnik i $H_0$ daleko poniżej wszystkich stanów. Hydrolog oznacza
takie krzywe jako mało wiarygodne, ale ich nie odrzuca (ADR-0041). Reguła jest własną regułą Hydrologa bez źródła w
literaturze, dlatego wynik zawiera uwagę `unreferenced_formula`. Przykład z ADR-0041: krzywa wodowskazu IMGW-PIB
150170070 z lat 1981–1990 ma $b = 6{,}50$ i $H_0 = -88$ cm przy stanach od 45 do 161 cm.

<!-- spec:rating_curve_plausibility -->
<!-- /spec:rating_curve_plausibility -->

**Typowe błędy.** Podawanie $a$ bez jednostki stanu. Mylenie $H_0$ z zerem wodowskazu. Ekstrapolacja krzywej poza
zakres pomiarów, zwłaszcza na wezbrania. Jedna krzywa dla okresu, w którym zmieniło się koryto albo zero wodowskazu.
Traktowanie przepływów dobowych IMGW-PIB jak pomiarów.

### Przykład 1: krzywa jednego roku w Kłodzku

```bash
hydrolog hydrometrics rating-curve --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --level-column H --discharge-column Q --date-column date --first-year 2010 --last-year 2010
```

Z 365 par dobowych roku hydrologicznego 2010 (najniższy stan 96 cm):
$a = 0{,}000320$ m³/s na cm$^b$, $b = 2{,}49$, $H_0 = 44{,}6$ cm, $R^2 = 0{,}949$, odchylenie standardowe reszt
3,26 m³/s; krzywa jest wiarygodna według reguły Hydrologa (`plausible`).

**Zastrzeżenie.** Pary dobowe nie są pomiarami hydrometrycznymi: przepływy dobowe IMGW-PIB obliczono ze stanów wody
krzywą natężenia przepływu (z poprawkami w okresach zjawisk lodowych). Dopasowana krzywa odtwarza więc krzywą, której
IMGW-PIB użył w danym roku, a nie niezależny pomiar. Do tego jednak dobrze służy: pozwala śledzić, jak ta krzywa
zmieniała się w czasie.

### Przykład 2: przesuwanie się krzywej w ciągu 75 lat

```bash
hydrolog hydrometrics rating-curve --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --level-column H --discharge-column Q --date-column date --years-per-period 10
```

Hydrolog dopasowuje krzywą każdego dziesięciolecia (pole `periods`) i odczytuje ją przy medianach stanu (95 cm) i
przepływu (8,79 m³/s) wszystkich par:

| Okres | $b$ | $H_0$ [cm] | $R^2$ | $Q$ przy $H$ = 95 cm [m³/s] | $H$ przy $Q$ = 8,79 m³/s [cm] |
|---|---|---|---|---|---|
| 1951–1960 | 2,14 | 0,3 | 0,981 | 12,93 | 79,4 |
| 1961–1970 | 1,95 | 19,1 | 0,950 | 13,06 | 81,1 |
| 1971–1980 | 1,96 | 24,7 | 0,971 | 11,73 | 85,4 |
| 1981–1990 | 1,58 | 47,4 | 0,957 | 10,87 | 89,0 |
| 1991–2000 | 1,86 | 43,1 | 0,922 | 8,67 | 95,4 |
| 2001–2010 | 1,94 | 56,0 | 0,937 | 5,71 | 104,7 |
| 2011–2020 | 1,62 | 63,4 | 0,963 | 7,00 | 99,8 |
| 2021–2025 | 2,06 | 26,0 | 0,867 | 7,29 | 101,6 |

Wszystkie krzywe są wiarygodne według reguły Hydrologa, a jednak ten sam przepływ 8,79 m³/s odpowiadał w latach
1951–1960 stanowi 79 cm, a w latach 2001–2010 – stanowi 105 cm. Zależność stan–przepływ w Kłodzku przesunęła się o
ponad dwadzieścia centymetrów. Przyczyną może być zmiana koryta w profilu wodowskazowym, zmiana samego wodowskazu albo
kolejne korekty krzywej przez IMGW-PIB; z danych tego nie odczytamy. Krzywa całego wielolecia ma $R^2 = 0{,}880$, mniej
niż krzywa któregokolwiek dziesięciolecia, bo łączy kilka różnych zależności. W latach 2001–2010 (i dla całego
wielolecia) dopasowane $H_0$ leży tuż pod najniższym stanem okresu (56 cm; dla wielolecia 30 cm), czyli na granicy
dopuszczalnego obszaru: to sygnał, że jedna krzywa potęgowa słabo opisuje pary tego okresu.

Wniosek praktyczny: szereg stanów wody z wielu dziesięcioleci nie musi być jednorodny, nawet gdy szereg przepływów
jest. Przed analizą stanów (strefy stanów w p. 9.8, trendy stanów w rozdziale 10) sprawdź, czy zależność stan–przepływ
się nie zmieniła.

## 9.8. Strefy stanów wody Rybczyńskiego

**Idea.** Polska tradycja hydrometryczna dzieli zakres stanów wody wodowskazu na strefy niskich, średnich i wysokich
stanów: niskie, średnie i wysokie tło wodne (NTW, STW, WTW). Granice wyznacza się z histogramu stanów i krzywej czasu
trwania stanów (Rybczyński 1923, 1932). Oryginalnych prac Rybczyńskiego nie udało się sprawdzić w otwartym źródle,
więc ani nazwy stref, ani reguły ich granic nie są potwierdzone; Hydrolog stosuje własne odczytanie (ADR-0063) i
zgłasza uwagę `unreferenced_formula`. Traktuj wynik jako przybliżenie.

<!-- spec:water_level_frequency -->
<!-- /spec:water_level_frequency -->

<!-- spec:rybczynski_zones -->
<!-- /spec:rybczynski_zones -->

### Przykład: strefy stanów w Kłodzku

```bash
hydrolog hydrometrics water-level-zones --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column H
```

Z 27 029 stanów dobowych z lat 1951–2025 w klasach co 10 cm Hydrolog wyznacza: NTW do 95 cm, STW od 95 do 105 cm i
WTW powyżej 105 cm (do 670 cm). Najliczniejsza jest klasa 90–100 cm.

**Zastrzeżenie.** Polecenie bierze wszystkie stany pliku. Tymczasem w Kłodzku ten sam przepływ odpowiadał w latach
1951–1960 stanowi o ponad dwadzieścia centymetrów niższemu niż w latach 2001–2010 (p. 9.7), więc strefy całego
wielolecia mieszają stany z różnych warunków koryta. Do opisu współczesnych stref przygotuj plik ze stanami jednego,
jednorodnego okresu.

## Źródła

Źródła oznaczone „niedostępne” nie są w otwartym dostępie; ich treść znamy z cytowań w źródłach otwartych.

- Bayliss A.C., Jones R.C. (1993) Peaks-over-threshold flood database: summary statistics and seasonality. Institute
  of Hydrology, Wallingford, IH Report 121 (raport z 1992 r. dla MAFF). Niedostępne.
- BAWiki, Bundesanstalt für Wasserbau: hasło „Parde coefficient”. http://wiki.baw.de/en/index.php/Parde_coefficient
- Burn D.H. (1997) Catchment similarity for regional flood frequency analysis using seasonality measures. Journal of
  Hydrology 202, 212–230. Niedostępne.
- Dynowska I. (1971) Typy reżimów rzecznych w Polsce. Zeszyty Naukowe UJ, Prace Geograficzne 28. Niedostępne.
- Dynowska I. (1997) Reżim odpływu rzecznego. W: Atlas Rzeczypospolitej Polskiej. Główny Geodeta Kraju, Warszawa.
  Niedostępne.
- Hall J., Blöschl G. (2018) Spatial patterns and characteristics of flood seasonality in Europe. Hydrology and
  Earth System Sciences 22, 3883–3901. https://hess.copernicus.org/articles/22/3883/2018/
- Hydrolog, decyzje architektoniczne: ADR-0031 (reżim, sezonowość, harmoniki), ADR-0041 (mało wiarygodne krzywe
  przepływu), ADR-0063 (statystyki stacji według specyfikacji), katalog `docs/decisions/`.
- IMGW-PIB: dane publiczne i opisy formatów (`hydrologia_info_ogolne.txt`), Rocznik Hydrologiczny.
  https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/
- ISO 1100-2:2010 Hydrometry – Measurement of liquid flow in open channels – Part 2: Determination of the
  stage-discharge relationship. Niedostępne.
- Pardé M. (1933) Fleuves et rivières. Armand Colin, Paryż. Niedostępne.
- Perz A. (2019) Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania Fizjograficzne, Seria A – Geografia Fizyczna
  10 (A70), 65–83. doi:10.14746/bfg.2019.10.6
- Robson A., Reed D. (1999) Flood Estimation Handbook, t. 3: Statistical procedures for flood frequency estimation.
  Institute of Hydrology, Wallingford. Niedostępne.
- Rybczyński M. (1923) skrypt wykładów; (1932) Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa
  Geofizyków w Warszawie 4–5. Niedostępne.
- Sumner G., Homar V., Ramis C. (2001) Precipitation seasonality in eastern and southern coastal Spain. International
  Journal of Climatology 21, 219–247.
- Walsh R.P.D., Lawler D.M. (1981) Rainfall seasonality: description, spatial patterns and change through time.
  Weather 36(7), 201–208. Niedostępne.
- Wilks D.S. (2011) Statistical Methods in the Atmospheric Sciences, wyd. 3. Academic Press, Oxford. Niedostępne.
- WMO (2010) Manual on Stream Gauging, t. II: Computation of Discharge. WMO-No. 1044, Genewa.
  https://library.wmo.int/idurl/4/32726
- Wrzesiński D. (2017) Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania
  Fizjograficzne, Seria A – Geografia Fizyczna 8 (A68), 253–264. doi:10.14746/bfg.2017.8.19
- Wrzesiński D. (2018) Typologia reżimu odpływu rzek w Polsce w różnych fazach oscylacji północnoatlantyckiej. Badania
  Fizjograficzne, Seria A – Geografia Fizyczna 9 (A69), 249–261. doi:10.14746/bfg.2018.9.19
