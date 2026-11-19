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
<!-- /spec:years_of_a_series -->

**Braki danych.** Hydrolog stosuje zasady WMO-No. 1203 (WMO 2017, rozdz. 4.4.1). Średnia miesięczna i liczba dni ze
zjawiskiem znoszą kilka rozproszonych braków, ale nie dłuższą przerwę; liczbę dni ze zjawiskiem w miesiącu z brakami
przelicza się na pełny miesiąc. Suma miesięczna wymaga kompletu dni, chyba że brakujące dni obejmuje suma zbiorcza
(*accumulated total*: opad zmierzony po kilku dniach bez pomiaru i zapisany pod ostatnim dniem). Ekstremum miesiąca
liczy się z tylu dni, ile jest. Progi tych reguł podają ramki:

<!-- spec:wmo_monthly_mean -->
<!-- /spec:wmo_monthly_mean -->

<!-- spec:wmo_monthly_count -->
<!-- /spec:wmo_monthly_count -->

<!-- spec:wmo_monthly_sum -->
<!-- /spec:wmo_monthly_sum -->

<!-- spec:accumulated_totals -->
<!-- /spec:accumulated_totals -->

<!-- spec:block_extreme -->
<!-- /spec:block_extreme -->

Wartość roczna wymaga wszystkich dwunastu miesięcy, a maksima roczne, sumy opadów bardzo dużych, ciągi dni i sezon
hydrotermiczny – wszystkich dni roku. Programy wskaźników ETCCDI (np. climdex.pcic) przyjmują inne tolerancje braków,
więc przy danych z lukami ich wyniki mogą się różnić od wyników Hydrologa. Sumy opadu Hydrolog zaokrągla, żeby sumy
równe w zapisie dziesiętnym były równymi liczbami (ważne dla wartości równych w teście Manna–Kendalla, rozdział 10):

<!-- spec:rounded_sums -->
<!-- /spec:rounded_sums -->

**Typowy błąd.** Liczenie sumy miesięcznej z miesiąca, w którym brakuje kilku dni, „bo to tylko dwa dni”: jedna burza
może zmienić sumę miesiąca o połowę.

## 11.2. Normy klimatyczne

**Idea.** Norma klimatyczna (*climate normal*) to średnia z wielolecia, z którą porównuje się pojedyncze lata i
miesiące. Standardowa norma WMO obejmuje ostatnie pełne trzydziestolecie kończące się rokiem z zerem na końcu (obecnie
1991–2020), a okres 1961–1990 pozostaje stałym punktem odniesienia do badania zmian klimatu (WMO 2017, rozdz. 2 i 5.1).
Normę miesiąca liczy się tylko wtedy, gdy wystarczająco wiele lat okresu ma wartość tego miesiąca:

<!-- spec:wmo_normal -->
<!-- /spec:wmo_normal -->

Normę roczną, półroczną i sezonową WMO każe liczyć z norm miesięcznych – jako sumę norm miesięcznych dla sum i liczb
dni, jako ich średnią dla średnich – a nie z wartości rocznych (WMO 2017, rozdz. 4.3.3). Przy kompletnych danych oba
sposoby dają to samo, ale gdy w różnych latach brakuje pojedynczych miesięcy, tylko reguła WMO daje normę roczną.
Hydrolog stosuje ją od wersji 0.9.0 (ADR-0044).

<!-- spec:multimonth_normal -->
<!-- /spec:multimonth_normal -->

Okres normy wybierają opcje `--reference-first-year` i `--reference-last-year`; domyślnie jest nim analizowany okres.
Lata analizy zachowują własne wartości, a z okresu normy pochodzą tylko punkty odniesienia: normy, opad względny,
anomalie i klasy (ADR-0033).

<!-- spec:precipitation_normals -->
<!-- /spec:precipitation_normals -->

<!-- spec:temperature_normals_and_anomalies -->
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
<!-- /spec:precipitation_sums -->

<!-- spec:relative_precipitation -->
<!-- /spec:relative_precipitation -->

**Klasy roczne Kaczorowskiej.** Kaczorowska (1962, s. 72) zdefiniowała siedem klas dla lat i pór roku, nie dla
miesięcy. Granice klas to pełne procenty, a źródło nie mówi, jak zaokrąglać. Hydrolog zaokrągla procent normy do
pełnego procentu, połówkę w górę (ADR-0059), tak jak roczniki IMGW-PIB drukują pełne procenty. Łabędzki i Bąk (2004)
czytają te same klasy z granicami dziesiętnymi, więc rok bliski granicy klasy bywa u nich w innej klasie; przy
granicy podawaj zawsze procent z jednym miejscem po przecinku.

<!-- spec:kaczorowska_class -->
<!-- /spec:kaczorowska_class -->

**Klasy miesięczne.** Sumy miesięczne są dużo bardziej zmienne niż roczne, dlatego klasa „normalny” jest dla nich
szersza. Hydrolog stosuje klasy z tab. 1 Gąsiorek i Musiał (2011), za Tomaszewską (1994):

<!-- spec:month_precipitation_class -->
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
<!-- /spec:precipitation_days -->

<!-- spec:sdii -->
<!-- /spec:sdii -->

<!-- spec:precipitation_intensity -->
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
<!-- /spec:wet_day_percentile -->

<!-- spec:heavy_precipitation_share -->
<!-- /spec:heavy_precipitation_share -->

<!-- spec:heavy_precipitation_thresholds -->
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
<!-- /spec:precipitation_concentration_index -->

<!-- spec:pci_class -->
<!-- /spec:pci_class -->

<!-- spec:seasonality_index -->
<!-- /spec:seasonality_index -->

<!-- spec:si_class -->
<!-- /spec:si_class -->

Klasy źródeł mają przerwy między granicami (Oliver – pełne liczby, Walsh i Lawler – dwa miejsca po przecinku);
Hydrolog przydziela wartość z przerwy do klasy wyższej (ADR-0059).

<!-- spec:precipitation_regime -->
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
<!-- /spec:spell_lengths -->

**Do którego roku należy ciąg?** Ciąg przechodzący przez 1 stycznia można przypisać na trzy sposoby: przeciąć granicą
roku (dosłowne brzmienie definicji ETCCDI), przypisać w całości rokowi, w którym się kończy (programy ETCCDI i ECA&D;
ECA&D 2021, s. 20), albo rokowi, w którym się zaczyna. Hydrolog do wersji 0.8.1 przypisywał ciąg rokowi początku, a od
wersji 0.9.0 przypisuje go rokowi końca, jak ECA&D (ADR-0044). Porównując wyniki z literaturą, sprawdzaj tę
konwencję.

<!-- spec:spell_year -->
<!-- /spec:spell_year -->

<!-- spec:spell_summaries -->
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
<!-- /spec:spi_k_month_sums -->

<!-- spec:spi_gamma_fit -->
<!-- /spec:spi_gamma_fit -->

<!-- spec:spi -->
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
<!-- /spec:temperature_monthly_means -->

<!-- spec:temperature_extremes -->
<!-- /spec:temperature_extremes -->

<!-- spec:daily_temperature_range -->
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
<!-- /spec:threshold_days -->

<!-- spec:temperature_day_counts -->
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
<!-- /spec:degree_days -->

<!-- spec:degree_day_sums -->
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
<!-- /spec:snow_cover_day -->

**Zima.** Hydrolog liczy zimy jako sezony od lata do lata, nazwane rokiem, w którym się kończą, tak jak Urban (2015);
dzięki temu śnieg z października należy do zimy, którą zaczyna. W literaturze spotyka się też sezony od
października do maja, od listopada do marca i od grudnia do lutego, więc porównując wyniki, sprawdź, jaki sezon
przyjęto. Normy IMGW-PIB liczą dni z pokrywą w latach kalendarzowych.

<!-- spec:snow_season -->
<!-- /spec:snow_season -->

<!-- spec:snow_season_extremes -->
<!-- /spec:snow_season_extremes -->

<!-- spec:snow_season_medians -->
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
<!-- /spec:sielianinov_coefficient -->

<!-- spec:sielianinov_class -->
<!-- /spec:sielianinov_class -->

**Miesiące i sezon w Hydrologu.** Hydrolog liczy współczynnik każdego miesiąca od kwietnia do września oraz
współczynnik sezonu: dni tych miesięcy ze średnią temperaturą powyżej progu, jak Miś (2026) i Chmist-Sikorska i in.
(2022). Klasycznego okresu Sielianinowa, między wiosennym a jesiennym trwałym przejściem temperatury przez próg,
Hydrolog nie liczy, bo żadne otwarte polskie źródło nie ustala reguły wyznaczania tych przejść (ADR-0044). Inni autorzy
(Chmist-Sikorska i in. 2022; Miś 2026) stosują też inne granice klas niż Skowera i Puła; podawaj, czyją klasyfikację
stosujesz.

<!-- spec:hydrothermal_months -->
<!-- /spec:hydrothermal_months -->

<!-- spec:hydrothermal_season -->
<!-- /spec:hydrothermal_season -->

<!-- spec:hydrothermal_period -->
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
