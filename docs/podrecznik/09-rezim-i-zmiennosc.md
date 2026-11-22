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

<a id="spec-hydrological_year"></a>

> **Rok hydrologiczny daty** · wzór grupy B `hydrological_year` (Tier B, CMP-2.2)
>
> **Definicja:** Rok hydrologiczny daty: jej rok kalendarzowy, a dla listopada i grudnia rok następny. (źr. 1)
>
> **Konwencja:** Rok IMGW-PIB trwa od 1 listopada do 31 października i nosi nazwę roku kalendarzowego, w którym się kończy (2016 = 1.11.2015–31.10.2016); w ČHMÚ tak samo (Hydrologická ročenka České republiky 2010, wstęp).
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `first_month` | Pierwszy miesiąc roku hydrologicznego | 11 | mies. | (źr. 1) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/hydrologia_info_ogolne.txt>
>
> Funkcja `hydrolog.statistics._hydrological_year.hydrological_year`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-parde_coefficients"></a>

> **Współczynniki Pardégo: średni przepływ każdego miesiąca do średniego przepływu rocznego** · specyfikacja [`parde_coefficients`](../FORMULAS.md#parde_coefficients) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> K_m = \frac{\bar{Q}_m}{\bar{Q}},\quad \bar{Q}_m = \frac{1}{n_m}\sum_{d \in m} Q_d,\quad \bar{Q} = \frac{1}{N}\sum_{d} Q_d
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q_d$ | `values` (ciąg) | Średni przepływ dobowy, w m³/s lub dowolnej jednostce; NaN oznacza dzień bez wartości | m³/s | [0; ∞) | nie podano w źródłach | [1,24; 522] (źr. 4) |
> | $m_d$ | `month` (ciąg) | Miesiąc kalendarzowy każdego dnia, styczeń = 1 | – | [1; 12] | nie podano w źródłach | [1; 12] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\bar{Q}_m$ | `monthly_mean` (ciąg) | Średni przepływ każdego miesiąca, od listopada do października | m³/s | [0; ∞) |
> | $\bar{Q}$ | `annual_mean` | Średni przepływ ze wszystkich dni z wartością | m³/s | (0; ∞) |
> | $K_m$ | `parde` (ciąg) | Współczynnik Pardégo każdego miesiąca, od listopada do października | – | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jeden miesiąc na każdy dzień | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | każdy miesiąc jest liczbą całkowitą, miesiącem kalendarzowym od 1 do 12 | `whole_months` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | każdy miesiąc kalendarzowy ma dzień z wartością: istnieje dwanaście średnich | `every_month_has_a_value` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | 0 < Qbar < inf: któryś dzień ma dodatni przepływ, a float64 mieści średnią i jej sumę | `positive_mean` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - Qbar_m to średnia z dni z wartością miesiąca kalendarzowego m w całym okresie (dni tego miesiąca ze wszystkich lat łącznie), Qbar to średnia ze wszystkich dni z wartością, tak jak średnie miesięczne i roczne roku w IMGW-PIB: dwanaście współczynników ważonych liczbą dni ich miesięcy daje średnio jeden, a sumuje się do 12 tylko wtedy, gdy każdy miesiąc ma tyle samo dni (rok bez luk: około 11,96 przy silnym wezbraniu wiosennym); średnia z dwunastu średnich miesięcznych dawałaby sumę 12
> - dzień bez wartości (NaN) nie wchodzi do żadnej średniej; gdy luki skupiają się w niektórych miesiącach, Qbar przesuwa się ku miesiącom lepiej obserwowanym
> - miesiące wejściowe są kalendarzowe (styczeń = 1), wyniki są uporządkowane od listopada do października, według miesięcy roku hydrologicznego
> - przepływ w m³/s lub dowolnej jednostce (współczynniki są bezwymiarowe); tabele Wrzesińskiego podają je w % średniego przepływu rocznego
>
> **Założenia**
>
> - dni okresu reprezentują jego miesiące: okres kilku lat opisuje te lata, nie klimat (reżim rzek Polski określa się na podstawie 30–40 lat, Wrzesiński 2017)
>
> **Zgodność z obserwacjami według źródeł:** brak: współczynniki Pardégo opisują średni cykl roczny przepływu; ich źródła nie porównują ich z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff <http://wiki.baw.de/en/index.php/Parde_coefficient>
> 2. Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 254: Dynowska's (1997) types read from the monthly flow coefficients W (miesięczne współczynniki przepływu); Table 1, p. 260, in % of the mean annual flow <https://repozytorium.amu.edu.pl/server/api/core/bitstreams/2a303457-aae6-4476-a766-985a3a4ac0b6/content>
> 3. Pardé, M. (1933). Fleuves et rivières. Armand Colin, Paris, the monthly coefficient of discharge; not opened — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. IMGW-PIB, public hydrological data: the monthly characteristics of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997 (tests/fixtures/imgw_klodzko/imgw_150160180_mies_1971_2015.csv), the smallest monthly minimum 1.24 m3/s and the largest monthly maximum 522 m3/s of discharge, which bound its daily means <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 5. IMGW-PIB, MIES_publiczne_format.txt, the format of the public monthly files, the calendar month of a row, 1 to 12 <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
>
> Funkcja `hydrolog.statistics.regime.parde_coefficients`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:parde_coefficients -->

**Jak Hydrolog liczy średnie.** Średni przepływ miesiąca to średnia wszystkich dni tego miesiąca kalendarzowego we
wszystkich latach okresu. Średni przepływ z wielolecia to średnia wszystkich dni okresu, tak jak średni przepływ roku
u IMGW-PIB, a nie średnia dwunastu średnich miesięcznych. Dlatego suma dwunastu współczynników nie jest dokładnie
równa liczbie miesięcy: miesiące mają różną liczbę dni. Dzień bez wartości nie wchodzi do żadnej średniej, a gdy braki
skupiają się w kilku miesiącach, średnia z wielolecia przesuwa się ku miesiącom lepiej obserwowanym. Sposób, w jaki
polecenie `stats regime` układa szereg dobowy na kalendarzu, opisuje ramka:

<!-- spec:flow_regime_of_a_daily_series -->

<a id="spec-flow_regime_of_a_daily_series"></a>

> **Reżim odpływu szeregu dobowego** · wzór grupy B `flow_regime_of_a_daily_series` (Tier B, CMP-2.2)
>
> **Definicja:** Miesiąc kalendarzowy każdej daty; współczynniki Pardégo, udział wiosenny i typ reżimu szeregu według Dynowskiej (specyfikacje `parde_coefficients`, `spring_share`, `dynowska_regime_type`), wskaźnik Walsha i Lawlera objętości miesięcznych (średnie razy liczba dni miesiąca, luty 28,25 dnia) oraz pierwszy i ostatni rok hydrologiczny z wartością i liczba takich lat (źr. 1)
>
> **Konwencja:** miesiące kalendarza gregoriańskiego; listy od listopada do października; dzień bez wartości (NaN) jest pomijany; rok hydrologiczny trwa od listopada do października i nosi numer roku, w którym się kończy (IMGW-PIB)
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $d_{II}$ | `february_days` | Liczba dni lutego w roku średnim | 113/4 | d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), point 1: the result of stats regime
> 2. Hydrolog, ADR-0031 (2026), restated in ADR-0063, February of the mean year of 1901-2099, in which every fourth year is a leap year: 28 + 1/4 days, so the twelve months make 365.25 days; the other months have their days of a common year
>
> Funkcja `hydrolog.statistics.regime.flow_regime`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:flow_regime_of_a_daily_series -->

**Udział wiosenny.** Obok współczynników Hydrolog podaje udział marca i kwietnia w objętości odpływu przeciętnego
roku. To wskaźnik opisowy przyjęty w Hydrologu (ADR-0031), nie wielkość z literatury. Przydaje się przy porównywaniu
rzek z wyraźnym wezbraniem roztopowym.

<!-- spec:spring_share -->

<a id="spec-spring_share"></a>

> **Udział marca i kwietnia w rocznej objętości średnich przepływów miesięcznych** · specyfikacja [`spring_share`](../FORMULAS.md#spring_share) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> s = \frac{V_{III} + V_{IV}}{\sum_{m} V_m},\quad V_m = \bar{Q}_m\,d_m
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\bar{Q}_m$ | `monthly_mean` (ciąg) | Średni przepływ każdego miesiąca, od listopada do października | m³/s | [0; ∞) | nie podano w źródłach | [2,67; 58,9] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $s$ | `spring_share` | Udział marca i kwietnia w objętości rocznej, od 0 do 1 | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | 0 < sum(V_m) < inf: któryś miesiąc ma dodatnią średnią, a float64 mieści objętości | `positive_volume` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $d_{II}$ | `february_days` | Liczba dni lutego w roku średnim | 113/4 | d | (źr. 3) |
>
> **Konwencje**
>
> - objętości to wieloletnie średnie miesięczne pomnożone przez liczbę dni miesiąca, luty 28,25 dnia (rok średni 365,25 dnia), a nie przez dni lat okresu
> - dane wejściowe są uporządkowane od listopada do października, jak wyniki `parde_coefficients`; marzec i kwiecień są piątym i szóstym miesiącem
> - objętości w m³/s razy dni, jednostce, która w udziale się skraca
>
> **Zgodność z obserwacjami według źródeł:** brak: opisowy wskaźnik reżimu przyjęty w Hydrologu (ADR-0031)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: spring_share, the March-April share of the annual volume, the monthly means times the days of the month
> 2. IMGW-PIB, public hydrological data: the monthly characteristics of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997 (tests/fixtures/imgw_klodzko/imgw_150160180_mies_1971_2015.csv), the monthly means of discharge, 2.67 to 58.9 m3/s <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 3. Hydrolog, ADR-0031 (2026), restated in ADR-0063, February of the mean year of 1901-2099, in which every fourth year is a leap year: 28 + 1/4 days, so the twelve months make 365.25 days; the other months have their days of a common year
>
> Funkcja `hydrolog.statistics.regime.spring_share`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-dynowska_regime_type"></a>

> **Typ reżimu odpływu rzeki polskiej według Dynowskiej ze współczynników Pardégo** · specyfikacja [`dynowska_regime_type`](../FORMULAS.md#dynowska_regime_type) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> S = \max(K_{III}, K_{IV}),\ L = \max(K_{VI}, K_{VII}, K_{VIII});\ \text{typ} = \begin{cases} 5 & L \ge 0{,}95\,S \\ 4 & L \ge 1{,}00 \\ 1 & S \le 1{,}30 \\ 2 & S \le 1{,}80 \\ 3 & \text{w pozostałych przypadkach} \end{cases}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $K_m$ | `parde` (ciąg) | Współczynniki Pardégo miesięcy od listopada do października | – | [0; ∞) | nie podano w źródłach | [0,224; 2,819] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `code` (liczba całkowita) | 1 niwalny słabo wykształcony; 2 niwalny średnio wykształcony; 3 niwalny silnie wykształcony; 4 niwalno-pluwialny; 5 pluwialno-niwalny | – | [1; 5] |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $S_1$ | `weakly_nival` | Górna granica współczynnika miesiąca wiosennego w reżimie niwalnym słabo wykształconym | 13/10 | – | (źr. 1) |
> | $S_2$ | `moderately_nival` | Górna granica współczynnika miesiąca wiosennego w reżimie niwalnym średnio wykształconym | 9/5 | – | (źr. 1) |
> | $L_1$ | `summer_rise` | Najmniejszy współczynnik miesiąca letniego w reżimie niwalno-pluwialnym | 1 | – | (źr. 1) |
> | $r$ | `nearly_equal` | Najmniejszy stosunek współczynnika miesiąca letniego do wiosennego uznawany za „prawie równy” | 19/20 | – | (źr. 5) |
>
> **Konwencje**
>
> - współczynniki to współczynniki Pardégo miesięcy od listopada do października, np. 1,30 dla 130 % średniego przepływu rocznego
> - miesiąc wiosenny to większy z marca i kwietnia (Perz 2019, s. 79), miesiąc letni to największy z miesięcy od czerwca do sierpnia (interpretacja Hydrologa); przy równych współczynnikach wybiera się wcześniejszy miesiąc
> - typy są badane w kolejności 5, 4, potem od 1 do 3: „wyższy lub prawie równy” oznacza co najmniej 0,95 współczynnika wiosennego (interpretacja Hydrologa, żadne źródło nie podaje liczby); podane w źródłach „na ogół 130-180 %” dla typów 4 i 5 nie jest sprawdzane
> - granice domknięte tak, jak je formułują źródła: „co najwyżej 130 %” to typ 1, „powyżej 180 %” typ 3, więc 180 % to typ 2, „co najmniej 100 %” typ 4; granice porównuje się jako liczby zmiennoprzecinkowe 1,3, 1,8 i 1,0, a miesiąc letni z liczbą zmiennoprzecinkową 0,95 razy wiosenny, dzięki czemu każdy przypadek równości z granicą, drukowany z trzema miejscami po przecinku, pozostaje w swojej klasie
>
> **Założenia**
>
> - współczynniki opisują długi okres, w źródłach od 30 do 40 lat; typ z kilku lat lub ze współczynników bliskich granicy jest niepewny: czerwiec w Kłodzku w latach 1971-2015 leży 0,05 % powyżej 100 % (przypadek Perza)
> - dwie klasyfikacje Wrzesińskiego tych samych 516 posterunków z lat 1971-2010 liczą 24 (2017) i 33 (2018) rzeki o reżimie pluwialno-niwalnym: interpretacja „prawie równego” nie jest ustalona także w źródłach
>
> **Zgodność z obserwacjami według źródeł:** brak: typologia; Wrzesiński (2017, 2018) sklasyfikował według niej 516 posterunków z lat 1971-2010, a Perz (2019) rzeki Kotliny Kłodzkiej, bez miary zgodności
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 255: Dynowska's (1997) five types: the spring month's mean flow at most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a rule 130-180 % with a summer rise of at least 100 % (4); the summer month's mean flow higher than or nearly equal to the spring month's (5) <https://repozytorium.amu.edu.pl/server/api/core/bitstreams/2a303457-aae6-4476-a766-985a3a4ac0b6/content>
> 2. Wrzesiński, D. (2018). Typologia reżimu odpływu rzek w Polsce w różnych fazach oscylacji północnoatlantyckiej. Badania Fizjograficzne, Seria A, 9 (A69), 249-261. doi:10.14746/bfg.2018.9.19, p. 250: the five types in the words of Wrzesiński (2017, p. 255); Table 1, pp. 253-254: the mean coefficients of each type, 516 gauges, 1971-2010 <https://pressto.amu.edu.pl/index.php/bfg/article/download/24472/22684/50308>
> 3. Perz, A. (2019). Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania Fizjograficzne, Seria A, 10 (A70), 65-83. doi:10.14746/bfg.2019.10.6, p. 79: Dynowska's criteria, 130-180 % and at least 100 % of the mean annual flow, the spring month March or April (marzec-kwiecień) <https://pressto.amu.edu.pl/index.php/bfg/article/download/23873/22299/>
> 4. Dynowska, I. (1997). Reżim odpływu rzecznego. In: Atlas Rzeczypospolitej Polskiej. Główny Geodeta Kraju, Warszawa, the five types of the river regime; not opened: as Wrzesiński (2017, 2018) and Perz (2019) quote them — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: where the sources name no month and no number, the spring month is the larger of March and April, the summer month the largest of June to August and 'nearly equal' at least 0.95 of the spring coefficient (the mockup's REGIME_RULE)
> 6. Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, Table 1, p. 260: the smallest coefficient 22.4 % (February, type 5) and the largest 281.9 % (March, type 3) of 516 gauges, 1971-2010 <https://repozytorium.amu.edu.pl/server/api/core/bitstreams/2a303457-aae6-4476-a766-985a3a4ac0b6/content>
>
> Funkcja `hydrolog.statistics.regime.dynowska_regime_type`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
równomiernie w roku, do jedności, gdy wszystkie przypadają na ten sam dzień (Bayliss i Jones 1993; Burn 1997; Robson
i Reed 1999; Hall i Blöschl 2018).

<!-- spec:circular_mean -->

<a id="spec-circular_mean"></a>

> **Średni kierunek i koncentracja terminów na okręgach ich lat (Bayliss i Jones)** · specyfikacja [`circular_mean`](../FORMULAS.md#circular_mean) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> \theta_i = \frac{2\pi t_i}{L_i},\quad \bar{x} = \frac{1}{n}\sum_i \cos\theta_i,\quad \bar{y} = \frac{1}{n}\sum_i \sin\theta_i,\quad f = \frac{\operatorname{atan2}(\bar{y}, \bar{x}) \bmod 2\pi}{2\pi},\quad r = \sqrt{\bar{x}^2 + \bar{y}^2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $t_i$ | `elapsed_days` (ciąg) | Czas każdej daty od początku jej roku: dzień roku minus połowa, czyli środek dnia | d | [0; ∞) | nie podano w źródłach | [2,5; 336,5] (źr. 5) |
> | $L_i$ | `year_days` (ciąg) | Długość roku każdej daty, w jednostce terminów | d | (0; ∞) | nie podano w źródłach | [365; 366] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $f$ | `mean_fraction` | Kierunek średniego wektora jako ułamek roku | – | [0; 1] |
> | $r$ | `concentration` | Długość średniego wektora: 1 dla jednego terminu, bliska 0, gdy terminy rozkładają się na cały rok | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jedna długość roku na każdy termin | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 2) |
> | 0 <= t_i < L_i: każdy termin leży w swoim roku | `within_its_year` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 2) |
>
> **Konwencje**
>
> - terminy i długości ich lat w jednej jednostce czasu, w dniach dla dat; kąt 2 pi t / L terminu t liczonego od początku jego roku o długości L
> - dla dat t to dzień roku minus połowa, czyli środek dnia, a L to 365 lub 366 (ADJUST u Baylissa i Jonesa, w FEH nr dnia - 0,5); Hall i Blöschl (2018) przyjmują sam dzień, D 2 pi / m_i
> - średni kierunek atan2(ybar, xbar) sprowadzony do [0, 2 pi): Bayliss i Jones oraz FEH dodają pi lub 2 pi do arctan(ybar / xbar) zależnie od znaków, co daje ten sam kąt; przy xbar = ybar = 0 kierunek jest nieokreślony (Hall i Blöschl), a wzór daje 0, tak jak scipy.stats.circmean
> - w pobliżu r = 0 kierunek jest źle uwarunkowany: przesuwa go zaokrąglenie; średnią należy odczytywać razem z r (Bayliss i Jones, rozdz. 3.3; FEH)
>
> **Założenia**
>
> - terminy są datami niezależnych zdarzeń, jednego ekstremum rocznego na rok; Hall i Blöschl zachowują stacje, w których test Rayleigha odrzuca równomierny rozkład dat, czego Hydrolog nie oblicza
>
> **Zgodność z obserwacjami według źródeł:** brak: opis terminów wezbrań; Bayliss i Jones (1992) oraz FEH przedstawiają go na mapach dla rzek brytyjskich, Hall i Blöschl (2018) dla Europy
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bayliss, A.C. and Jones, R.C. (1992). The peaks-over-threshold database at the Institute of Hydrology. Report to MAFF, Institute of Hydrology, Wallingford, March 1992 (published as IH Report No. 121, 1993), section 3.2, pp. 18-19: theta_i = day 2 pi / LENYR - ADJUST with ADJUST = (1/2)(2 pi / 365) for the middle of the day, LENYR 365 or 366; xbar, ybar the means of cos and sin; tan(thetabar) = ybar / xbar with pi or 2 pi added by their signs; MPD = thetabar 365 / (2 pi) + 0.5; section 3.3, p. 21: r = sqrt(xbar^2 + ybar^2), MPD less meaningful when r is close to zero <https://nora.nerc.ac.uk/id/eprint/14407/>
> 2. Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1, pp. 177-179: theta = (day no. - 0.5) 2 pi / LENYR, LENYR 365 or 366, the 0.5 for the middle of the day; XFLOOD and YFLOOD the means of cos theta and sin theta; thetabar by their quadrant, r their length; when r is small the direction is less meaningful <https://www.ceh.ac.uk/sites/default/files/2021-11/Flood-Estimation-Handbook-3-Statistical-Procedures-For-Flood-Frequency-Estimation_Alice-Robson_Duncan-Reed.pdf>
> 3. Hall, J. and Blöschl, G. (2018). Spatial patterns and characteristics of flood seasonality in Europe. Hydrology and Earth System Sciences 22, 3883-3901, eqs. 1-5: theta_i = D_i 2 pi / m_i (D_i = 1 on 1 January, m_i 365 or 366); the mean date by the quadrant rules times m / (2 pi), m the mean number of days per year, undefined for xbar = ybar = 0; R = sqrt(xbar^2 + ybar^2) <https://hess.copernicus.org/articles/22/3883/2018/hess-22-3883-2018.pdf>
> 4. Burn, D.H. (1997). Catchment similarity for regional flood frequency analysis using seasonality measures. Journal of Hydrology 202, 212-230, the seasonality measures of flood dates; not opened — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. IMGW-PIB, public hydrological data: the half-year characteristics of discharge at station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997, the dates of the 44 annual maxima, the larger of the half-year maxima: days 3 to 337 of their calendar years <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 6. Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1: LENYR, 365 or 366 days <https://www.ceh.ac.uk/sites/default/files/2021-11/Flood-Estimation-Handbook-3-Statistical-Procedures-For-Flood-Frequency-Estimation_Alice-Robson_Duncan-Reed.pdf>
>
> Funkcja `hydrolog.statistics.seasonality.circular_mean`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:circular_mean -->

**Które daty.** Z szeregu dobowego Hydrolog bierze maksimum (albo minimum) każdego pełnego roku hydrologicznego,
datowane pierwszym dniem, w którym wystąpiło; rok z brakującym dniem pomija i wymienia w uwadze. Z pliku półrocznego
IMGW-PIB (`--half-year-file`) bierze opublikowane ekstrema półroczy, które IMGW-PIB wyznacza ze wszystkich obserwacji,
a nie z wartości dobowych. Kąt każdej daty liczy na roku kalendarzowym, do którego data należy, a udziały półroczy –
według półroczy roku hydrologicznego:

<!-- spec:extremes_of_complete_years -->

<a id="spec-extremes_of_complete_years"></a>

> **Ekstrema pełnych lat hydrologicznych szeregu dobowego** · wzór grupy B `extremes_of_complete_years` (Tier B, CMP-2.2)
>
> **Definicja:** Maksimum lub minimum każdego pełnego roku hydrologicznego szeregu dobowego, datowane pierwszym dniem jego wystąpienia (źr. 1)
>
> **Konwencja:** rok liczy się tylko wtedy, gdy ma wartość dla każdego dnia, tak jak IMGW-PIB nie podaje charakterystyki dla okresu z przerwą; ekstrema są z wartości dobowych, a nie ze wszystkich obserwacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of the public data, the winter half-year 1 November to 30 April, the summer one 1 May to 31 October; the hydrological year named after the year of its end; no characteristic for a period with a break in the observations <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
>
> Funkcja `hydrolog.statistics.seasonality.daily_extremes`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:extremes_of_complete_years -->

<!-- spec:circular_mean_of_dates -->

<a id="spec-circular_mean_of_dates"></a>

> **Średni termin i koncentracja dat** · wzór grupy B `circular_mean_of_dates` (Tier B, CMP-2.2)
>
> **Definicja:** Czas każdej daty, czyli jej dzień roku kalendarzowego (1 = 1 stycznia) minus połowa, i długość jej roku, 365 lub 366 dni; ich `circular_mean`; średni dzień 365,25 f + 0,5 i jego MM-DD w roku zwykłym 2001 (źr. 1)
>
> **Konwencja:** lata przestępne według reguły gregoriańskiej; kierunek przeliczany z powrotem na dzień w roku średnim 365,25 dnia (m u Halla i Blöschla; Bayliss i Jones przyjmują 365, co pod koniec roku daje termin wcześniejszy nawet o ćwierć dnia); data średniego dnia zaokrąglana funkcją round Pythona (połowa do dnia parzystego), dzień powyżej 365 przypada na 31 grudnia
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $m$ | `mean_year_days` | Średnia liczba dni w roku | 1461/4 | d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bayliss, A.C. and Jones, R.C. (1992). The peaks-over-threshold database at the Institute of Hydrology. Report to MAFF, Institute of Hydrology, Wallingford, March 1992 (published as IH Report No. 121, 1993), section 3.2, pp. 18-19: theta_i = day 2 pi / LENYR - ADJUST with ADJUST = (1/2)(2 pi / 365) for the middle of the day, LENYR 365 or 366; xbar, ybar the means of cos and sin; tan(thetabar) = ybar / xbar with pi or 2 pi added by their signs; MPD = thetabar 365 / (2 pi) + 0.5; section 3.3, p. 21: r = sqrt(xbar^2 + ybar^2), MPD less meaningful when r is close to zero <https://nora.nerc.ac.uk/id/eprint/14407/>
> 2. Hall, J. and Blöschl, G. (2018). Spatial patterns and characteristics of flood seasonality in Europe. Hydrology and Earth System Sciences 22, 3883-3901, eq. 2: m, the mean number of days per year, taken as 365.25, the mean of 1901-2099; Bayliss and Jones (1992, p. 19) take 365 <https://hess.copernicus.org/articles/22/3883/2018/hess-22-3883-2018.pdf>
>
> Funkcja `hydrolog.statistics.seasonality.circular_mean_date`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:circular_mean_of_dates -->

<!-- spec:seasonality_of_extremes -->

<a id="spec-seasonality_of_extremes"></a>

> **Sezonowość ekstremów rocznych** · wzór grupy B `seasonality_of_extremes` (Tier B, CMP-2.2)
>
> **Definicja:** Kołowy średni termin i koncentracja datowanych ekstremów rocznych oraz ich udziały w półroczu zimowym (listopad–kwiecień) i letnim (maj–październik) (źr. 1)
>
> **Konwencja:** półrocza IMGW-PIB według miesiąca kalendarzowego każdej daty
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of the public data, the winter half-year 1 November to 30 April, the summer one 1 May to 31 October; the hydrological year named after the year of its end; no characteristic for a period with a break in the observations <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
>
> Funkcja `hydrolog.statistics.seasonality.extreme_seasonality`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-harmonic_fit"></a>

> **Dopasowanie średniej i harmonik cyklu rocznego metodą najmniejszych kwadratów** · specyfikacja [`harmonic_fit`](../FORMULAS.md#harmonic_fit) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> x(t) = A_0 + \sum_{k=1}^{K}\left(a_k \cos\frac{2\pi k t}{P} + b_k \sin\frac{2\pi k t}{P}\right),\quad C_k = \sqrt{a_k^2 + b_k^2},\quad d_k = \frac{(\operatorname{atan2}(b_k, a_k) \bmod 2\pi)\,P}{2\pi k} + 1
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $d$ | `day_of_year` (ciąg) | Dzień roku hydrologicznego każdej wartości, 1 = 1 listopada | d | [1; 366] | nie podano w źródłach | [1; 366] (źr. 4) |
> | $x$ | `values` (ciąg) | Wartości dobowe w dowolnej jednostce, najczęściej temperatura wody lub powietrza; NaN oznacza dzień bez wartości | °C | (−∞; ∞) | nie podano w źródłach | [−22,2; 29,3] (źr. 5) |
> | $K$ | `n_harmonics` (liczba całkowita) | Liczba dopasowywanych harmonik | – | [1; 4] | nie podano w źródłach | [1; 4] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $A_0$ | `mean` | Średnia dopasowanego cyklu, w jednostce wartości | °C | (−∞; ∞) |
> | $C_k$ | `amplitudes` (ciąg) | Amplituda każdej harmoniki, w jednostce wartości | °C | [0; ∞) |
> | $d_k$ | `phase_days` (ciąg) | Dzień roku hydrologicznego pierwszego maksimum każdej harmoniki | d | [1; 366,25] |
> | – | `explained_variances` (ciąg) | Udział w wariancji, który każda harmonika dodaje do dopasowania harmonik poprzednich | – | [0; 1] |
> | $R^2$ | `r_squared` | Udział wariancji wyjaśnionej przez całe dopasowanie | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jeden dzień na każdą wartość | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | co najmniej 4 K + 2 wartości: dwukrotność liczby 2 K + 1 współczynników (reguła Hydrologa) | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | najdłuższa przerwa między dniami z wartością, na okręgu roku, jest krótsza niż P / (2 K): harmoniki są rozdzielone | `year_covered` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
> | 0 < sum((x - mean)^2) < inf: wartości nie są wszystkie równe, a float64 mieści ich wariancję, więc istnieją R² i fazy | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $P$ | `period_days` | Okres cyklu rocznego, długość roku średniego | 1461/4 | d | (źr. 8) |
>
> **Konwencje**
>
> - t to dzień roku hydrologicznego minus jeden (1 listopada = 0), P = 365,25 dnia: 31 października roku przestępnego to t = 365, więc na przełomie roku t przeskakuje o 1,25 dnia
> - dzień fazy to dzień roku hydrologicznego, w którego wartości harmonika osiąga maksimum: wartość dnia leży w t = dzień - 1, a dzień fazy to t + 1
> - udział harmoniki w wariancji to przyrost R² po dołączeniu jej do dopasowania metodą najmniejszych kwadratów harmonik poprzednich (dopasowania zagnieżdżone, dodatkowa suma kwadratów Drapera i Smitha); dla całkowitej liczby lat równo rozmieszczonych dni harmoniki są ortogonalne, a udział jest równy (n/2) C_k^2 / ((n - 1) s^2) Wilksa; Hydrolog 0.8 wycinał zamiast tego współczynniki z całego dopasowania, co w latach z lukami dawało ujemne udziały
> - R² = 1 - SSR / SST, gdzie SST to suma kwadratów odchyleń wartości od ich średniej
> - wartości w dowolnej jednostce (°C w dokumentach): średnia i amplitudy są w tej jednostce
>
> **Założenia**
>
> - cykl roczny jest okresowy o okresie roku średniego; trend lub zmiana reżimu w okresie rozkłada się na harmoniki
> - harmonika o zerowej amplitudzie nie ma fazy: jej dzień fazy jest wtedy szumem zaokrągleń, należy go odczytywać tylko razem z amplitudą
>
> **Zgodność z obserwacjami według źródeł:** brak: opis średniego cyklu rocznego; Wilks (2011) nie podaje miary jego zgodności z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd ed. Academic Press, Oxford, section 9.4: the harmonic functions of a periodic series, their amplitude, phase and share of the variance, fitted by regression; not opened — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Feichtinger, H.G., Gröchenig, K. and Strohmer, T. (1995). Efficient numerical methods in non-uniform sampling theory. Numerische Mathematik 69, 423-440, section 4, Propositions 1 and 2, pp. 429-430: a trigonometric polynomial of degree M on a period of 1 sampled with a largest gap delta < 1/(2M) (on the circle) is a stable sampling set, its condition number at most ((1 + 2 delta M) / (1 - 2 delta M))^2; for larger gaps no estimate is known (after Gröchenig 1992, Math. Comp. 59, 181-194) <http://www.math.ucdavis.edu/~strohmer/papers/1995/fgs0195.ps.gz>
> 3. Draper, N.R. and Smith, H. (1998). Applied Regression Analysis, 3rd ed. Wiley, New York, section 6.1: the extra sum of squares of terms added to a fitted model, which never increases the residual sum of squares; not opened — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. IMGW-PIB, hydrologia_info_ogolne.txt of the public hydrological data, the hydrological year from 1 November to 31 October: days 1 to 365, or 366 when it ends in a leap year <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/>
> 5. IMGW-PIB, synoptic station Warszawa-Okęcie (352200375), daily data 1991-2020 (tests/fixtures/warszawa_okecie_1991_2020.csv.gz), the daily mean air temperature, -22.2 to 29.3 degC <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/>
> 6. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: harmonics 1 to 4 (default 2: the annual and the half-year one), as the option of stats harmonics
> 7. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: too_few_values
> 8. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: the period P = 365.25 d, the mean year of 1901-2099, in which every fourth year is a leap year (the Julian year)
>
> Funkcja `hydrolog.statistics.harmonics.harmonic_fit`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:harmonic_fit -->

Dzień maksimum harmoniki Hydrolog podaje jako dzień roku hydrologicznego. Polecenie `stats harmonics` dopasowuje
harmoniki do średniego cyklu całego okresu i osobno do każdego roku hydrologicznego z wystarczającą liczbą wartości:

<!-- spec:annual_cycle_of_a_daily_series -->

<a id="spec-annual_cycle_of_a_daily_series"></a>

> **Cykl roczny szeregu dobowego** · wzór grupy B `annual_cycle_of_a_daily_series` (Tier B, CMP-2.2)
>
> **Definicja:** Dzień roku hydrologicznego każdej daty (1 = 1 listopada); `harmonic_fit` wszystkich dni okresu, czyli średni cykl roczny, oraz każdego roku hydrologicznego z co najmniej 300 dniami z wartością, który spełnia warunki wstępne dopasowania (źr. 1)
>
> **Konwencja:** rok hydrologiczny trwa od listopada do października i nosi numer roku, w którym się kończy (IMGW-PIB); rok, którego wartości dopasowanie odrzuca (wszystkie równe albo luka zbyt długa dla harmonik), nie ma własnego dopasowania
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `min_year_values` | Najmniejsza liczba wartości w roku hydrologicznym, który ma własne dopasowanie | 300 | d | (źr. 2) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: the result of stats harmonics
> 2. Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: each hydrological year with at least 300 values has a fit of its own
>
> Funkcja `hydrolog.statistics.harmonics.annual_cycle`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

Średnia okresu wynosi 9,04 °C (lata hydrologiczne 1992–2020, więc nieco inny okres niż norma 1991–2020 z rozdziału
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
zależność ta jest bliska funkcji potęgowej (WMO 2010, równ. 1.4; ISO 1100-2:2010).

<!-- spec:rating_curve -->

<a id="spec-rating_curve"></a>

> **Przepływ przy danym stanie wody z potęgowej krzywej natężenia przepływu** · specyfikacja [`rating_curve`](../FORMULAS.md#rating_curve) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> Q = \begin{cases} a\,(H - H_0)^{b} & H > H_0 \\ 0 & H \le H_0 \end{cases}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $H$ | `water_levels` (ciąg) | Stany wody H, przy których odczytuje się przepływ, w jednostce stanów krzywej | cm | (−∞; ∞) | nie podano w źródłach | [−10; 330] (źr. 3) |
> | $a$ | `a` | Przepływ przy wysokości H - H0 równej jednej jednostce H (C według WMO) | $\mathrm{m^{3}/s\text{ na }cm^{b}}$ | [0; ∞) | nie podano w źródłach | [0,003; 0,04] (źr. 4) |
> | $b$ | `b` | Wykładnik wysokości nad stanem przepływu zerowego (beta według WMO) | – | [0; ∞) | nie podano w źródłach | [1,2; 3,1] (źr. 4) |
> | $H_0$ | `h0` | Stan przepływu zerowego albo efektywnego przepływu zerowego (e według WMO) | cm | (−∞; ∞) | nie podano w źródłach | [−30; 55] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q$ | `discharge_m3s` (ciąg) | Przepływ przy każdym stanie | m³/s | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | a (max(H) - H0)**b < 1.8e308: przepływ przy każdym stanie jest liczbą float64 | `finite_discharge` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
>
> **Konwencje**
>
> - H i H0 w jednej jednostce stanów: cm, jak podaje je IMGW-PIB, albo m; a w m³/s na (jednostkę H)^b, więc ta sama krzywa ze stanami w m ma a 100^b razy większe i H0 100 razy mniejsze (symetria `levels_in_another_unit`); Q w m³/s
> - Q = 0 przy H0 i poniżej, czyli przy stanie przepływu zerowego (e według WMO): brak przepływu przez kontrolę, niezależnie od b
> - H0 to stan przepływu zerowego, a nie zero wodowskazu (poziom odniesienia łaty wodowskazowej)
>
> **Założenia**
>
> - jedna zależność stan–przepływ jednej kontroli (przekrojowej albo korytowej) w całym zakresie stanów: bez przesunięć krzywej, histerezy ani zmiennej cofki
>
> **Zgodność z obserwacjami według źródeł:** brak: WMO-No. 1044 przedstawia równanie jako krzywą natężenia przepływu dla kontroli przekrojowych i korytowych (rozdz. 1.3 oraz 1.5.4 do 1.5.6) i nie podaje żadnej miary jego zgodności z pomiarami przepływu; dopasowanie krzywej do jej pomiarów opisuje specyfikacja `rating_curve_fit`
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper <https://library.wmo.int/idurl/4/32726>
> 2. ISO 1100-2:2010. Hydrometry - Measurement of liquid flow in open channels - Part 2: Determination of the stage-discharge relationship, the power-law rating equation and its fit to gaugings — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070
> 4. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm
> 5. NumPy documentation, numpy.finfo, float64: the largest number 1.7976931348623157e+308 <https://numpy.org/doc/stable/reference/generated/numpy.finfo.html>
>
> Funkcja `hydrolog.hydrometrics.rating_curve.rating_discharge`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:rating_curve -->

**Znaczenie parametrów.** $H_0$ to stan, przy którym przepływ ustaje (stan przepływu zerowego, *gauge height of zero
flow*; dla nieregularnego przekroju – stan przepływu zerowego „efektywnego”). **To nie jest zero wodowskazu** (*gauge
datum*), czyli poziom odniesienia łaty wodowskazowej (rzędna „P.z.” w rocznikach IMGW-PIB); stany wody poniżej zera
wodowskazu są czymś zwyczajnym. Współczynnik $a$ to przepływ przy głębokości $H - H_0$ równej jednostce stanu, a jego
jednostka zależy od jednostki stanu: ta sama krzywa ze stanami w metrach ma inne $a$ niż ze stanami w centymetrach
(ramka). Wykładnik $b$ zależy od rodzaju kontroli przepływu: inny jest dla kontroli przekrojowej (próg, przelew,
przewężenie), inny dla kontroli korytowej, gdzie o przepływie decyduje opór całego odcinka koryta (WMO 2010,
s. II.1-2 i II.1-8).

**Dopasowanie.** Hydrolog dopasowuje krzywą metodą najmniejszych kwadratów na przepływach. WMO (2010, rozdz. 1.12.2)
opisuje metodę najmniejszych kwadratów na logarytmach, w której krzywa jest prostą na papierze logarytmicznym. Obie
metody dają różne krzywe z tych samych par (przykład w ramce): na przepływach większą wagę mają duże przepływy (błędy
bezwzględne), na logarytmach wszystkie pomiary ważą tyle samo względnie. WMO zaleca, by pomiarów było wiele i by
obejmowały cały zakres stanów (WMO 2010, s. II.1-3).

<!-- spec:rating_curve_fit -->

<a id="spec-rating_curve_fit"></a>

> **Krzywa natężenia przepływu Q = a (H - H0)^b dopasowana do par stan–przepływ metodą najmniejszych kwadratów na Q** · specyfikacja [`rating_curve_fit`](../FORMULAS.md#rating_curve_fit) · wersja wzoru 2 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> (\hat a, \hat b, \hat H_0) = \arg\min_{a \ge 0,\, 0 \le b < 100,\, \min H - 1024\,(\max H - \min H) < H_0 < \min H} \sum_{i=1}^{n} \left(Q_i - a\,(H_i - H_0)^{b}\right)^2,\quad R^2 = 1 - \frac{SS_{res}}{SS_{tot}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $H$ | `water_levels` (ciąg) | Stan wody H każdego pomiaru przepływu, w jednej jednostce stanów | cm | (−∞; ∞) | nie podano w źródłach | [−10; 330] (źr. 5) |
> | $Q$ | `discharges_m3s` (ciąg) | Przepływ zmierzony przy każdym stanie | m³/s | [0; ∞) | nie podano w źródłach | [0,5; 125] (źr. 6) |
> | $H_{0,start}$ | `h0_initial` | Punkt startowy poszukiwania H0, poniżej każdego stanu | cm | (−∞; ∞) | nie podano w źródłach | [−30; 60] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $a$ | `a` | Przepływ przy wysokości równej jednej jednostce H | $\mathrm{m^{3}/s\text{ na }cm^{b}}$ | [0; ∞) |
> | $b$ | `b` | Wykładnik wysokości nad stanem przepływu zerowego | – | [0; ∞) |
> | $H_0$ | `h0` | Stan przepływu zerowego, poniżej każdego stanu | cm | (−∞; ∞) |
> | $R^2$ | `r_squared` | Współczynnik determinacji krzywej na Q | – | (−∞; 1] |
> | $s$ | `std_residuals` | Odchylenie standardowe reszt Q - Q(H) | m³/s | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jeden przepływ na każdy stan | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 8) |
> | n >= 3: co najmniej trzy pary dla trzech parametrów a, b i H0 | `enough_pairs` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | min(H) < max(H): jednakowe stany nie wyznaczają ani b, ani H0 | `levels_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | min(Q) < max(Q): przepływ niezmienny ze stanem daje dopasowanie b = 0 przy dowolnym H0 | `discharges_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | h0_initial < min(H): poszukiwanie zaczyna się wewnątrz swojego ograniczenia, z H0 poniżej każdego stanu | `start_below_levels` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | suma kwadratów ma minimum przy b < 100 i H0 powyżej 1024 rozstępów stanów poniżej najniższego stanu, które poszukiwanie osiąga i w którym krzywa przy każdym stanie jest liczbą float64; pary, w których przepływ rośnie jak funkcja wykładnicza H, nie mają go, bo ich krzywa jest wklęsła na papierze logarytmicznym przy każdej wartości próbnej H0 | `least_squares_minimum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 3) |
> | n >= 12: co najmniej 12 do 15 pomiarów przepływu z okresu analizy | `enough_gaugings` | wynik z ostrzeżeniem: poza zakresem stosowalności | (źr. 8) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `least_gaugings` | Najmniejsza liczba pomiarów przepływu z okresu analizy | 12 | – | (źr. 8) |
>
> **Konwencje**
>
> - najmniejsze kwadraty na Q, reszty arytmetyczne wszystkich par z jednakową wagą; WMO-No. 1044 (rozdz. 1.12.2) dopasowuje prostą na papierze logarytmicznym, log Q względem log(H - H0), co daje inną krzywą (sześć pomiarów przepływu z katalogu: b = 1,640 na Q, 1,820 w logarytmach)
> - ograniczenia a >= 0, b od 0 do 100 (25 razy więcej niż największy wykładnik wiarygodnej krzywej, ADR-0041) i H0 od 1024 rozstępów stanów poniżej najniższego stanu do 2^-30 skali stanów poniżej niego (potęgi dwójki, która sprowadza największe \|H\| do [1/2, 1)), czyli około 5e-7 cm dla stanów rzędu kilku metrów; koniec poszukiwania odległy o mniej niż 10^-3 od ograniczenia b albo, względnie, o mniej niż 10^-3 od najgłębszego ograniczenia H0 nie jest minimum: najmniejsze kwadraty par, w których przepływ rośnie jak funkcja wykładnicza H (pary z dwóch krzywych, kontrola złożona), zmierzają do Q = C exp(k H), granicy krzywej, gdy H0 dąży do minus nieskończoności, a b do plus nieskończoności, i osiągają ograniczenia
> - poszukiwanie na stanach i przepływach podzielonych dokładnie przez potęgi dwójki sprowadzające ich największe wartości bezwzględne do [1/2, 1) (krzywa jest następnie przeskalowana z powrotem, więc stany w cm albo m i przepływy przeskalowane przez potęgę dwójki dają tę samą krzywą): wartości próbne H0 według WMO-No. 1044 (rozdz. 1.5.4), czyli ograniczenie, `h0_initial` oraz rozstęp stanów razy 2^j poniżej najniższego stanu dla j = -20 do 10; dla każdej z nich najlepsze b, przy a w postaci jawnej, na siatce od 0 do 8 co 0,25 i dalej z mnożnikiem 1,13 do 100, uściślone między sąsiadami najlepszego punktu przez `minimize_scalar` z SciPy (ograniczona metoda Brenta, xatol 1e-12); ln głębokości H0 uściślony tak samo między sąsiadami najlepszej wartości próbnej; następnie `curve_fit` z SciPy od tego końca, metoda trust region reflective w granicach ograniczeń z ftol, xtol i gtol równymi 1e-12 i co najwyżej 10 000 obliczeń funkcji, której koniec zachowuje się tam, gdzie nie jest wyższy
> - R2 = 1 - SS_res / SS_tot na Q; s to odchylenie standardowe reszt z dzielnikiem n - 1 (numpy.std, ddof 1)
> - H, H0 i `h0_initial` w jednej jednostce stanów (cm albo m); a w m³/s na (jednostkę H)^b; Q w m³/s
>
> **Założenia**
>
> - pary odpowiadają jednej zależności stan–przepływ jednej kontroli w całym okresie (bez przesunięć krzywej, histerezy ani zmiennej cofki); sprawdzenie ze specyfikacji `rating_curve_plausibility` wskazuje krzywe, dla których tak nie jest
> - błędy tylko w Q, niezależne i o jednakowej wariancji
>
> **Zgodność z obserwacjami według źródeł:** brak: metoda najmniejszych kwadratów daje krzywą najbliższą pomiarom przepływu w wartościach Q; WMO-No. 1044 (rozdz. 1.12.2) nie podaje żadnej miary zgodności takiego dopasowania, a w przeglądzie źródeł nie znaleziono otwartego przykładu obliczeniowego z pomiarami przepływu i dopasowanymi parametrami (WMO-No. 1044, Rantz 1982, Kennedy 1984)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper <https://library.wmo.int/idurl/4/32726>
> 2. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.12.2, p. II.1-20: the equation of the relation may be computed by the method of least squares, which assumes that the relation plots as a straight line on logarithmic paper <https://library.wmo.int/idurl/4/32726>
> 3. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, pp. II.1-7 to II.1-8: e of a channel control or a section control of irregular shape may be determined by successive approximations, adding or subtracting trial values of e until the rating plots as a straight line on logarithmic paper; with values of e smaller than the true one the rating is concave upward, with greater ones concave downward <https://library.wmo.int/idurl/4/32726>
> 4. ISO 1100-2:2010. Hydrometry - Measurement of liquid flow in open channels - Part 2: Determination of the stage-discharge relationship, the power-law rating equation and its fit to gaugings — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070
> 6. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, discharges of 0.5 (the catalog's example) to 122.3 m3/s (station_daily.csv)
> 7. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the starts of their fits: -23 (the catalog's example of stages below the gauge zero), 40 and 41.2 cm
> 8. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.1, p. II.1-3: at a minimum the list of discharge measurements should include at least 12 to 15 measurements, all made during the period of analysis <https://library.wmo.int/idurl/4/32726>
>
> Funkcja `hydrolog.hydrometrics.rating_curve.fit_rating_curve`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:rating_curve_fit -->

**Wiarygodność krzywej.** Krzywa dopasowana do par z dwóch różnych zależności (przeniesione zero wodowskazu, rozmyte
albo zamulone koryto) ma zwykle bardzo stromy wykładnik i $H_0$ daleko poniżej wszystkich stanów. Hydrolog oznacza
takie krzywe jako mało wiarygodne, ale ich nie odrzuca (ADR-0041). Reguła jest własną regułą Hydrologa bez źródła w
literaturze, dlatego wynik zawiera uwagę `unreferenced_formula`. Przykład z ADR-0041: krzywa wodowskazu IMGW-PIB
150170070 z lat 1981–1990 ma $b = 6{,}50$ i $H_0 = -88$ cm przy stanach od 45 do 161 cm.

<!-- spec:rating_curve_plausibility -->

<a id="spec-rating_curve_plausibility"></a>

> **Wiarygodność krzywej natężenia przepływu jako krzywej jednej zależności stan–przepływ (reguła Hydrologa z ADR-0041)** · specyfikacja [`rating_curve_plausibility`](../FORMULAS.md#rating_curve_plausibility) · wersja wzoru 1 · status: **bez przypadku referencyjnego i wyroczni** (`unreferenced`)
>
> $$
> b \notin [1, 4] \Rightarrow \text{b\_out\_of\_range},\quad \min H - H_0 > \max H - \min H \Rightarrow \text{h0\_too\_low}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $H$ | `water_levels` (ciąg) | Stany par, do których dopasowano krzywą | cm | (−∞; ∞) | nie podano w źródłach | [−10; 330] (źr. 4) |
> | $b$ | `b` | Wykładnik krzywej | – | [0; ∞) | nie podano w źródłach | [1,2; 3,1] (źr. 5) |
> | $H_0$ | `h0` | Stan przepływu zerowego krzywej | cm | (−∞; ∞) | nie podano w źródłach | [−30; 55] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | – | `exponent` (wybór) | Czy b leży w przedziale od 1 do 4 | – | jedna z: `plausible`, `b_out_of_range` |
> | – | `zero_flow_stage` (wybór) | Czy H0 leży poniżej najniższego stanu co najwyżej o rozstęp stanów | – | jedna z: `plausible`, `h0_too_low` |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `lowest_exponent` | Dolna granica wiarygodnego wykładnika b | 1 | – | (źr. 1) |
> | – | `highest_exponent` | Górna granica wiarygodnego wykładnika b | 4 | – | (źr. 1) |
>
> **Konwencje**
>
> - b od 1 do 4, z granicami włącznie: kontrole przekrojowe 1,5 do 2,5 oraz 2 lub więcej w korytach naturalnych, kontrole korytowe zwykle poniżej 2 (WMO-No. 1044, s. II.1-2 i II.1-8); przekroje złożone i przepływ pozakorytowy mieszczą się w zakresie; rzeczywista kontrola przekrojowa o nachyleniu 4,3 (rys. II.1.5) zostaje oznaczona
> - H0 poniżej najniższego stanu co najwyżej o rozstęp stanów, z granicą włącznie: własne ograniczenie Hydrologa; stany to stany par przekazanych do dopasowania, przed usunięciem wartości odstających
> - ocena, a nie odmowa: krzywa jest mimo to podawana (ADR-0041)
>
> **Założenia**
>
> - krzywa dopasowana do par z dwóch zależności (przesunięte zero wodowskazu, zmiana koryta w okresie) ma bardzo duże b i H0 daleko poniżej każdego stanu
>
> **Zgodność z obserwacjami według źródeł:** brak: heurystyka Hydrologa (ADR-0041), niesprawdzona na obserwacjach; WMO-No. 1044 pokazuje rzeczywistą kontrolę przekrojową, której krzywa ma nachylenie około 4,3 poniżej 1,4 m (rys. II.1.5, s. II.1-9), a reguła oznacza ją jako `b_out_of_range`
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0041 (2026). Implausible rating curves: flagged, not refused, docs/decisions/0041-implausible-rating-curves-flagged-not-refused.md, decision 1: b from 1 to 4, H0 below the lowest stage by at most the range of the stages; Hydrolog's own rule, published by no source
> 2. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.3, eq. 1.1, p. II.1-2: beta = 1.5 for a rectangular and 2.5 for a V-shaped section control; sect. 1.5.6, p. II.1-8: logarithmic ratings of section controls in natural channels almost always have a slope of 2 or greater, those of channel controls usually less than 2 <https://library.wmo.int/idurl/4/32726>
> 3. WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.6, fig. II.1.5, p. II.1-9: the rating of a real stream with section control throughout, e = 0.6 m, has a slope of about 4.3 below 1.4 m and 2.8 above 1.5 m <https://library.wmo.int/idurl/4/32726>
> 4. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070
> 5. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm
>
> Funkcja `hydrolog.hydrometrics.rating_curve.rating_curve_plausibility`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-water_level_frequency"></a>

> **Rozkład częstości i czasu trwania stanów wody** · wzór grupy B `water_level_frequency` (Tier B, CMP-2.2)
>
> **Definicja:** Klasy o szerokości `bin_width` od najniższego stanu zaokrąglonego w dół do pełnej jednostki aż do pierwszej granicy powyżej najwyższego stanu zaokrąglonego w górę; liczebność każdej klasy, jej częstość 100 n_i / n %, częstość skumulowana od najniższej klasy i czas trwania D_i = 100 - częstość skumulowana poniżej klasy i, czyli udział stanów równych dolnej granicy klasy lub wyższych. (źr. 1)
>
> **Konwencja:** Klasy [dolna, górna) jak w numpy.histogram, ostatnia domknięta; pierwsza granica to pełna jednostka stanów (cm albo m), więc klasy zależą od jednostki; czas trwania jako udział wartości osiągniętych lub przekroczonych.
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology: Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 2: the percent of time a value was equalled or exceeded; p. 6: class intervals barely including the extremes of the record <https://pubs.usgs.gov/wsp/1542a/report.pdf>
>
> Funkcja `hydrolog.hydrometrics.rating_curve.WaterLevelFrequency.frequency_distribution`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:water_level_frequency -->

<!-- spec:rybczynski_zones -->

<a id="spec-rybczynski_zones"></a>

> **Strefy niskiego, średniego i wysokiego tła wodnego według Rybczyńskiego (NTW, STW, WTW)** · specyfikacja [`rybczynski_zones`](../FORMULAS.md#rybczynski_zones) · wersja wzoru 1 · status: **bez przypadku referencyjnego i wyroczni** (`unreferenced`)
>
> $$
> H_{NTW} = c_{\arg\max_i f_i},\quad H_{STW} = c_{\min\{i:\, D_i < 50\%\}},\quad D_i = 100 - \sum_{j<i} f_j,\quad f_j = \frac{100\,n_j}{\sum n}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $e$ | `bin_edges` (ciąg) | Granice klas stanów, rosnące | cm | (−∞; ∞) | nie podano w źródłach | [−10; 340] (źr. 2) |
> | $n$ | `counts` (ciąg) | Liczba stanów w każdej klasie | – | [0; ∞) | nie podano w źródłach | [0; 820] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $H_{NTW}$ | `ntw_upper` | Górna granica niskiego tła wodnego (NTW) | cm | (−∞; ∞) |
> | $H_{STW}$ | `stw_upper` | Górna granica średniego tła wodnego (STW) | cm | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jedna liczebność na każdą klasę między dwiema granicami | `one_count_per_class` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | e[i+1] > e[i]: klasy o dodatniej szerokości, od najniższego stanu w górę | `edges_increasing` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | sum(n) > 0: częstości wymagają stanów | `some_levels` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `duration_limit_pct` | Graniczny czas trwania stanów wyznaczający górną granicę STW | 50 | % | (źr. 1) |
>
> **Konwencje**
>
> - granice są środkami klas: NTW kończy się w środku najliczniejszej klasy (pierwszej z równolicznych), STW w środku pierwszej klasy, na której dolnej granicy czas trwania (udział stanów równych tej granicy lub wyższych) jest mniejszy niż 50 %
> - gdy żadna klasa nie ma czasu trwania poniżej 50 % albo STW nie leżałaby powyżej NTW, STW kończy się w środku klasy następnej po najliczniejszej; gdy jest to ostatnia klasa, o jedną szerokość klasy powyżej NTW, poza najwyższą granicą (WTW biegnie wtedy wstecz)
> - klasy i liczebności ze specyfikacji `water_level_frequency` (Tier B), stany w cm albo m
>
> **Założenia**
>
> - stany z długiego szeregu, dobowe lub częstsze, przy jednym zerze wodowskazu
>
> **Zgodność z obserwacjami według źródeł:** brak: źródło Rybczyńskiego nie zostało sprawdzone
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070
> 3. Hydrolog's water level data: tests/fixtures/station_daily.csv and the classes of 5 to 20 cm of the catalog's and the tests' examples, 1,811 daily stages of 45 to 329 cm: classes of 10 cm hold up to 483 levels, of 20 cm up to 815
>
> Funkcja `hydrolog.hydrometrics.rating_curve.rybczynski_zones`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
