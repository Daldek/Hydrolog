# 7. Przepływy maksymalne prawdopodobne

Rozdział opisuje statystyczną analizę częstości wezbrań (ang. *flood frequency analysis*): jak z ciągu
maksimów rocznych zmierzonych na wodowskazie wyznaczyć przepływ, który w każdym roku jest przewyższany
z zadanym prawdopodobieństwem. W polskiej praktyce taki przepływ nazywa się przepływem maksymalnym
prawdopodobnym albo, dokładniej, przepływem maksymalnym rocznym o określonym prawdopodobieństwie
przewyższenia $Q_{p\%}$ (np. $Q_{1\%}$). Jest to kwantyl rozkładu maksimów rocznych. Nie należy go mylić
z wezbraniem maksymalnym możliwym (ang. *probable maximum flood*, PMF), które jest górną granicą
fizyczną, a nie kwantylem — tak samo jak opady PMAXTP z rozdziału 2 nie są opadem maksymalnym
prawdopodobnym PMP.

Metoda wymaga długiego ciągu obserwacji przepływu w przekroju. Zlewnia Kamiennika, przykład przewodni
podręcznika, nie ma wodowskazu: jej hydrogram projektowy wyznacza się z opadu (rozdziały 2–6). Ten
rozdział pokazuje drugą drogę na danych dwóch wodowskazów: Polany na Czarnej (przykład metodyki KZGW
2017) i Świerzawy na Kaczawie — wodowskazu IMGW-PIB w tej samej miejscowości, w której zamyka się
zlewnia Kamiennika. Przepływy niskie i minima roczne omawia rozdział 8, testy trendu i jednorodności
rozdział 10.

## 7.1. Idea: maksimum roczne jako zmienna losowa

Największy przepływ roku hydrologicznego, $WQ$ (ang. *annual maximum flow*), traktuje się jak zmienną
losową. Jej dystrybuanta $F(x)$ podaje prawdopodobieństwo, że maksimum roku nie przekroczy wartości $x$
(prawdopodobieństwo nieprzewyższenia, ang. *non-exceedance probability*). W projektowaniu używa się
prawdopodobieństwa przewyższenia $p$ (ang. *exceedance probability*), czyli dopełnienia dystrybuanty
do jedności, zapisywanego w procentach. Okres powtarzalności $T$ (ang. *return period*) to odwrotność
prawdopodobieństwa przewyższenia: średni odstęp w latach między latami, w których przepływ $Q_{p\%}$
jest przekroczony. „Woda stuletnia” $Q_{1\%}$ nie zdarza się więc raz na sto lat jak w kalendarzu:
w każdym roku jest przewyższana z prawdopodobieństwem 1 %, niezależnie od tego, kiedy wystąpiła
ostatnio. Prawdopodobieństwo, że w ciągu wielu lat przepływ ten zostanie przewyższony choć raz, rośnie
z liczbą lat i dla okresu użytkowania budowli porównywalnego z $T$ jest znaczne; dlatego okres
powtarzalności nie jest gwarancją bezpieczeństwa na $T$ lat.

Analiza opiera się na trzech założeniach. Maksima kolejnych lat są niezależne (jedna wartość na rok
hydrologiczny), pochodzą z jednego rozkładu (ciąg jednorodny, ang. *homogeneous*: bez zbiornika,
regulacji czy przeniesienia wodowskazu w trakcie obserwacji) i ten rozkład nie zmienia się w czasie
(stacjonarność, ang. *stationarity*: brak trendu). Ramki specyfikacji poniżej podają je jako założenie
niezależności i jednakowego rozkładu maksimów rocznych.
Czwarta, ukryta trudność to ekstrapolacja: przepływy o okresie powtarzalności 100–1000 lat wyznacza się
z ciągów 30–70-letnich, więc o wyniku decyduje w dużej mierze przyjęty kształt rozkładu.

## 7.2. Dane: szereg maksimów rocznych

### Rok hydrologiczny i maksimum roku

Maksima liczy się w latach hydrologicznych, nie kalendarzowych: wezbranie roztopowe z przełomu zimy
i wiosny należy wtedy w całości do jednego roku.

<!-- spec:hydrological_year -->
<!-- /spec:hydrological_year -->

IMGW-PIB publikuje przepływy charakterystyczne półroczy (zimowego XI–IV i letniego V–X) wyznaczone ze
wszystkich obserwacji i pomiarów, a więc maksima bliskie kulminacji chwilowej. Hydrolog przyjmuje za
maksimum roczne większe z maksimów obu półroczy, a rok z jednym półroczem pomija i wymienia, bo brakujące
półrocze mogło zawierać wezbranie:

<!-- spec:half_year_annual_extremes -->
<!-- /spec:half_year_annual_extremes -->

Z szeregu dobowego (np. eksportu Obserwatora) maksimum roku jest największym średnim przepływem dobowym,
i to tylko z lat, w których każdy dzień ma wartość:

<!-- spec:complete_year_extremes -->
<!-- /spec:complete_year_extremes -->

Średnia dobowa spłaszcza kulminację, tym bardziej, im szybciej reaguje zlewnia. Polska metodyka
(KZGW 2017) definiuje przepływ maksymalny roczny jako najwyższą w roku wartość przepływu chwilowego lub
dobowego, a w praktyce posługuje się kulminacjami. W małych zlewniach różnica jest duża: na Kaczawie
w Świerzawie kwantyl stuletni z maksimów dobowych jest o ponad jedną trzecią mniejszy niż z maksimów IMGW-PIB
(przykład 7.10). Polecenia Hydrologa czytają oba rodzaje danych: `--half-year-file` (charakterystyki
półroczne IMGW-PIB w eksporcie Obserwatora), `--input-file` z `--date-column` (szereg dobowy) albo
`--values` (gotowe maksima roczne).

### Długość, jednorodność i trend

Metodyka KZGW (2017) wymaga ciągu co najmniej 30-letniego; krótszy należy najpierw przedłużyć, np.
korelacją z sąsiednim wodowskazem. Hydrolog liczy także krótsze ciągi, ale dołącza do wyniku uwagę
`short_record`, a przy bardzo krótkich `small_sample`. Przed dopasowaniem rozkładu trzeba sprawdzić, czy
ciąg jest jednorodny i bez trendu: KZGW (2017) wymaga testu Manna–Kendalla na poziomie istotności 0,05.
W Hydrologu służą do tego `hydrolog stats mann-kendall` i `hydrolog stats homogeneity` (testy
Manna–Whitneya, Kołmogorowa–Smirnowa i Pettitta); ich teorię i interpretację podaje rozdział 10. Wynik
„brak trendu” znaczy tylko, że test go nie wykrył: krótki ciąg rzadko daje odrzucenie hipotezy.

Najczęstsze błędy danych:

- maksima lat kalendarzowych zamiast hydrologicznych;
- łączenie w jednym ciągu kulminacji chwilowych i maksimów średnich dobowych;
- ciąg z luką w roku największego wezbrania. Publiczne dane IMGW-PIB nie mają np. roku hydrologicznego
  1997 dla wodowskazu Kłodzko na Nysie Kłodzkiej, czyli roku powodzi lipcowej; analiza częstości takiego
  ciągu bez uzupełnienia luki zaniża kwantyle rzadkich przepływów;
- rok z brakami pozostawiony w ciągu maksimów: Hydrolog pomija rok niepełny (uwaga `incomplete_years`),
  bo jego maksimum mogło wypaść w dniu bez danych.

## 7.3. Prawdopodobieństwo empiryczne: pozycje wykreślne

Uporządkowane maksima dostają prawdopodobieństwa empiryczne (pozycje wykreślne, ang. *plotting
positions*), które pozwalają nanieść próbę na siatkę prawdopodobieństwa obok dopasowanego rozkładu.
Hydrolog daje je w bloku `empirical` wyniku `stats flood-frequency`.

<!-- spec:plotting_positions -->
<!-- /spec:plotting_positions -->

Domyślny wzór Weibulla jest wzorem polskiej metodyki (KZGW 2017). Wzory Hazena i Cunnane’a różnią się
głównie w ogonach próby; WMO (2009) wymienia wszystkie trzy. Wzór Weibulla nigdy nie przypisuje
wartości prawdopodobieństwa 0 ani 1, ale też nie mówi, jak rzadkie było największe wezbranie: największe
z $N$ maksimów stoi zawsze przy okresie powtarzalności o rok dłuższym od długości ciągu, choćby było
wezbraniem tysiącletnim. Częsty błąd przy odczycie z siatki to pomylenie prawdopodobieństwa przewyższenia
z prawdopodobieństwem nieprzewyższenia; blok `empirical` Hydrologu podaje prawdopodobieństwo
przewyższenia (`exceedance_prob`) i okres powtarzalności (`return_periods`) każdego maksimum.

## 7.4. Charakterystyki próby: momenty i L-momenty

Rozkład dopasowuje się do kilku liczb opisujących próbę. Momenty zwykłe (ang. *product moments*) to
średnia, odchylenie standardowe i współczynnik skośności:

<!-- spec:sample_moments -->
<!-- /spec:sample_moments -->

L-momenty (ang. *L-moments*; Hosking 1990) są liniowymi kombinacjami uporządkowanych wartości. Pierwszy
jest średnią, drugi miarą rozrzutu w jednostce przepływu, a ich iloraz z trzecim — L-skośność $\tau_3$,
bez jednostki:

<!-- spec:sample_l_moments -->
<!-- /spec:sample_l_moments -->

Ponieważ wartości wchodzą do L-momentów liniowo, a nie w drugiej i trzeciej potędze, pojedyncze duże
wezbranie waży w nich znacznie mniej niż w odchyleniu standardowym i skośności. WMO (2009, § 5.5.1)
zauważa, że L-współczynnik zmienności i L-skośność są prawie nieobciążone, podczas gdy zwykłe $C_v$
i $C_s$ krótkich prób są silnie obciążone i bardzo zmienne. W obu przykładach tego rozdziału skośność
maksimów jest dodatnia i duża: kilka wielkich wezbrań na tle wielu umiarkowanych.

## 7.5. Rozkłady prawdopodobieństwa maksimów rocznych

Hydrolog dopasowuje cztery rozkłady. Każda ramka podaje wzór kwantyla dla okresu powtarzalności $T$
i umowy dotyczące parametrów. Kwantyl liczy się z odwrotności funkcji przeżycia w punkcie $1/T$, co
zachowuje dokładność także dla bardzo długich okresów.

### Uogólniony rozkład wartości ekstremalnych (GEV)

Rozkład GEV (ang. *generalized extreme value*) wynika z teorii wartości ekstremalnych: jest granicznym
rozkładem maksimów z dużej liczby zdarzeń (Coles 2001). Jego parametr kształtu decyduje o górnym ogonie.

<!-- spec:gev_quantiles -->
<!-- /spec:gev_quantiles -->

Uwaga na znak parametru kształtu. Hydrolog używa parametru $c$ biblioteki SciPy, równego $k$ Hoskinga
i $\kappa$ WMO (2009). Coles (2001) i wiele programów (np. pakiety R `evd`, `extRemes`) używają
$\xi = -c$. Ujemne $c$ (dodatnie $\xi$) oznacza ciężki górny ogon: kwantyle rosną z $T$ szybciej niż
w rozkładzie Gumbela, który odpowiada $c = 0$. Dodatnie $c$ daje rozkład ograniczony od góry. Rozkładu
GEV nie ma w metodyce KZGW (2017); jest w programie PrzepływyMax2011 IMGW-PIB (Węglarczyk red. 2013).

### Rozkład logarytmiczno-normalny

Rozkład logarytmiczno-normalny (ang. *log-normal*): logarytm przepływu pomniejszonego o dolne
ograniczenie $\epsilon$ ma rozkład normalny.

<!-- spec:log_normal_quantiles -->
<!-- /spec:log_normal_quantiles -->

Analiza częstości w Hydrologu (`stats flood-frequency`) dopasowuje wersję dwuparametrową, z dolnym
ograniczeniem równym zeru, więc wszystkie maksima muszą być dodatnie. Metodyka KZGW (2017) stosuje
wersję trójparametrową, z dolnym ograniczeniem szacowanym ze skrajnych wartości i mediany próby; tego
wariantu Hydrolog nie dopasowuje i jego wyniki rozkładu logarytmiczno-normalnego nie są wynikami KZGW.

### Rozkład Pearsona typu III

Trójparametrowy rozkład gamma (ang. *Pearson type III*) jest podstawowym rozkładem polskiej metodyki
(KZGW 2017) i amerykańskiego Bulletin 17B (IACWD 1982, tam dla logarytmów przepływów).

<!-- spec:pearson3_quantiles -->
<!-- /spec:pearson3_quantiles -->

Hydrolog parametryzuje go średnią, odchyleniem standardowym i skośnością; ramka podaje przeliczenie na
parametry KZGW (dolne ograniczenie $\epsilon$, skala $\alpha$, kształt $\lambda$). Przy dodatniej
skośności rozkład ma dolne ograniczenie. Gdy skośność przekracza wartość, przy której gęstość staje się
nieskończona na tej granicy, metoda największej wiarygodności przestaje działać (p. 7.6).

### Trójparametrowy rozkład Weibulla

Rozkład Weibulla ograniczony od dołu stosuje KZGW (2017) „w uzasadnionych przypadkach”.

<!-- spec:weibull_quantiles -->
<!-- /spec:weibull_quantiles -->

W Hydrologu kształt to $\beta_W$ KZGW, położenie to dolne ograniczenie $\epsilon$, a skala to odwrotność
$\alpha_W$. Metody momentów i L-momentów traktują rozkład Weibulla jak GEV próby o przeciwnym znaku
(ramki p. 7.6), co zawęża zakres możliwej skośności próby.

## 7.6. Estymacja parametrów

Każda metoda szacowania daje parametry tych samych czterech rozkładów; kwantyle, testy i AIC liczy się
z nich jednakowo. Opcja `--fit-method` wybiera metodę (`l_moments` domyślnie, `moments`, `mle`,
`least_squares`), a wartość `all` dopasowuje każdy rozkład każdą metodą i szereguje wszystkie
kombinacje według AIC. Próbę, której metoda nie potrafi dopasować, Hydrolog odrzuca z nazwą
niespełnionego warunku (ramki: `enough_values`, `values_not_all_equal`, `positive_values`,
`l_moments_within_distribution`, `skewness_within_distribution`, `likelihood_has_a_maximum`,
`squares_have_a_minimum`); przy wielu kombinacjach pomija tylko tę jedną z uwagą
`distribution_left_out`.

### Metoda L-momentów (domyślna)

Parametry dobiera się tak, by L-momenty rozkładu były równe L-momentom próby (Hosking i Wallis 1997).

<!-- spec:fit_l_moments -->
<!-- /spec:fit_l_moments -->

Metoda jest odporna na pojedyncze skrajne wartości i stabilna w krótkich ciągach, dlatego jest domyślna.
Nie występuje w metodyce KZGW (2017). Jej słabość: dopasowany rozkład z dolnym ograniczeniem (Pearson III,
Weibull) może zostawić najmniejsze maksima poza nośnikiem (ang. *support*), czyli przypisać im zerową
gęstość; Hydrolog sygnalizuje to uwagą `outside_support` (p. 7.7).

### Metoda momentów

W metodzie momentów (ang. *method of moments*) średnia, odchylenie standardowe i skośność rozkładu są
równe tym z próby.

<!-- spec:fit_moments -->
<!-- /spec:fit_moments -->

Dla rozkładu Pearsona III to wprost trzy momenty próby. Skośność próby jest silnie obciążona
w krótkich ciągach (p. 7.4), a WMO (2009, § 5.3.3) ostrzega, że momenty mogą dać granicę rozkładu
sprzeczną z obserwacjami.

### Metoda największej wiarygodności (MNW)

Parametry maksymalizują logarytm funkcji wiarygodności (ang. *maximum likelihood*).

<!-- spec:fit_maximum_likelihood -->
<!-- /spec:fit_maximum_likelihood -->

Dla rozkładów trójparametrowych z ograniczonym nośnikiem wiarygodność może rosnąć bez końca, gdy granica
nośnika zbliża się do najbliższej obserwacji, a gęstość na granicy jest nieskończona (Smith 1985). Tak
jest dla GEV, Pearsona III i Weibulla przy kształtach podanych w warunku `likelihood_has_a_maximum`.
Program, który mimo to zwraca „maksimum”, podaje punkt przy osobliwości: dolne ograniczenie równe
najmniejszemu maksimum, często z najmniejszym AIC ze wszystkich dopasowań. Hydrolog takiego dopasowania
nie zwraca (błąd `precondition_failed` albo uwaga `distribution_left_out` z przyczyną
`unbounded_likelihood`). W wersjach do 0.8.1 włącznie metoda `mle` korzystała z domyślnej optymalizacji
SciPy, która dla maksimów rzędu setek m³/s często zatrzymywała się daleko od maksimum wiarygodności
i dawała absurdalnie duże kwantyle rzadkich przepływów; wyniki tej metody z tamtych wersji należy
przeliczyć.

Metodyka KZGW (2017) szacuje rozkład Pearsona III warunkową MNW: dolne ograniczenie odczytuje się
graficznie z krzywej empirycznej, a pozostałe dwa parametry oblicza ze wzorów przybliżonych. Tego
wariantu, podobnie jak historycznej metody kwantyli (decyli) instrukcji CUGW z 1968 r., którą KZGW
dopuszcza w uzasadnionych przypadkach, Hydrolog nie ma.

### Metoda najmniejszych kwadratów (MNK)

Metoda najmniejszych kwadratów (ang. *least squares*) dobiera parametry tak, by suma kwadratów różnic
między uporządkowanymi maksimami a kwantylami rozkładu w pozycjach Weibulla była najmniejsza.

<!-- spec:fit_least_squares -->
<!-- /spec:fit_least_squares -->

Różnice są w m³/s, a największe maksima leżą najdalej od siebie, więc to one decydują o dopasowaniu.
Kwantyle rzadkich przepływów z MNK bywają przez to wyraźnie wyższe niż z innych metod (przykład 7.9).

## 7.7. Ocena dopasowania i wybór rozkładu

### Statystyka Andersona–Darlinga $A^2$

Statystyka $A^2$ (ang. *Anderson–Darling*) mierzy odległość dystrybuanty dopasowanej od empirycznej,
z większą wagą w ogonach niż test Kołmogorowa–Smirnowa.

<!-- spec:anderson_darling -->
<!-- /spec:anderson_darling -->

Tablicowe wartości krytyczne $A^2$ (Stephens 1974) dotyczą rozkładu znanego z góry. Gdy parametry
oszacowano z tej samej próby, rozkład dopasowuje się do niej i $A^2$ jest znacznie mniejsze: test
z wartościami tablicowymi prawie nigdy nie odrzuca. Hydrolog nadaje więc każdemu dopasowaniu metodą
L-momentów własne wartości krytyczne z parametrycznego bootstrapu (ang. *parametric bootstrap*; Stute,
González Manteiga i Presedo Quindimil 1993): losuje wiele prób o liczności badanej próby z dopasowanego
rozkładu, każdą dopasowuje ponownie tą samą metodą i za wartości krytyczne bierze kwantyle otrzymanych
$A^2$ (pole `ad_critical_values`, poziomy 15, 10, 5, 2,5 i 1 %). Liczbę prób i ziarno losowania podaje
ramka; wynik jest powtarzalny. Dopasowania innymi metodami wymagają iteracyjnej optymalizacji, więc nie
mają wartości krytycznych (`null`), a ich $A^2$ służy tylko do porównań. Interpretacja: $A^2$ większe od
wartości krytycznej na poziomie 5 % oznacza, że rozkład źle opisuje próbę; $A^2$ mniejsze nie dowodzi, że
rozkład jest właściwy. Gdy próbka bootstrapu wypada poza nośnik swojego dopasowania, jej $A^2$ jest
bardzo duże; dlatego wartości krytyczne rozkładów ograniczonych od dołu (Pearson III, Weibull) bywają
wysokie i test słabo je różnicuje.

### Test Kołmogorowa–Smirnowa

<!-- TODO spec: test Kołmogorowa–Smirnowa rozkładu dopasowanego (scipy.stats.kstest, obliczenie delegowane, CMP-1.2) -->

Hydrolog podaje też statystykę Kołmogorowa–Smirnowa i jej poziom krytyczny (`ks_statistic`,
`ks_p_value`), liczone przez SciPy dla rozkładu o parametrach z próby. Z tego samego powodu co wyżej
poziom krytyczny jest zawyżony, dlatego wynik ma `ks_valid: false` i uwagę `ks_test_approximate`; służy
tylko do orientacji. Test λ-Kołmogorowa z metodyki KZGW (2017) jest inną statystyką (różnice
dystrybuant w pozycjach Weibulla) z inną wartością krytyczną; Hydrolog go nie liczy.

### Kryterium informacyjne Akaikego (AIC)

<!-- spec:akaike_information_criterion -->
<!-- /spec:akaike_information_criterion -->

AIC (ang. *Akaike information criterion*) nagradza wiarygodność i karze liczbę parametrów; mniejsze
znaczy lepsze. Znaczenie mają różnice, nie wartości: różnica rzędu 2 i mniejsza nie rozstrzyga
(Burnham i Anderson 2002). Hydrolog liczy AIC w punkcie parametrów danej metody, więc MNW zwykle daje
swojemu rozkładowi najmniejsze AIC spośród metod. Pole `best_distribution` wskazuje dopasowanie
z najmniejszym AIC. Dopasowanie, które zostawia maksimum poza nośnikiem, ma nieskończony logarytm
wiarygodności: jego AIC jest `null`, trafia na koniec rankingu, a uwaga `outside_support` wymienia te
maksima (kwantyle, $A^2$ i statystyka K–S zostają podane).

WMO (2009, § 5.6.3) przestrzega, że samo kryterium Akaikego nie wystarcza do wyboru modelu. W polskiej
praktyce II cyklu planistycznego wybierano nim rozkład spośród dopasowań MNW niesprzecznych z testem
zgodności (IMGW-PIB i in. 2022). Rozsądna kolejność: najpierw odrzucić rozkłady z $A^2$ powyżej wartości
krytycznej i dopasowania z maksimami poza nośnikiem, potem porównać AIC pozostałych, a na końcu
sprawdzić, czy kwantyle rzadkich przepływów są fizycznie wiarygodne.

## 7.8. Przepływ miarodajny i kontrolny, niepewność

Rozporządzenie Ministra Infrastruktury z dnia 4 maja 2026 r. w sprawie warunków technicznych, jakim
powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2026 poz. 692), które zastąpiło
rozporządzenie Ministra Środowiska z 2007 r. (Dz.U. 2007 nr 86 poz. 579), określa w załączniku nr 3
prawdopodobieństwo przewyższenia przepływów miarodajnych $Q_m$ (ang. *design flood*; projektowanie)
i kontrolnych $Q_k$ (ang. *check flood*; sprawdzenie bezpieczeństwa w wyjątkowym układzie obciążeń) dla
stałych budowli hydrotechnicznych:

| Rodzaj budowli | Przepływ | Klasa I | Klasa II | Klasa III | Klasa IV |
|---|---|---|---|---|---|
| posadowione na podłożu łatwo rozmywalnym oraz budowle ziemne (bez wałów przeciwpowodziowych) | $Q_m$ | 0,1 % | 0,3 % | 0,5 % | 1,0 % |
| | $Q_k$ | 0,02 % | 0,05 % | 0,2 % | 0,5 % |
| pozostałe, w tym wały przeciwpowodziowe | $Q_m$ | 0,5 % | 1,0 % | 2,0 % | 3,0 % |
| | $Q_k$ | 0,1 % | 0,3 % | 0,5 % | 1,0 % |

Dla rzek i potoków górskich i podgórskich do przepływu kontrolnego dodaje się średni błąd jego
oszacowania $\delta$ przy poziomie ufności 0,84 i do wymiarowania przyjmuje $(1 + \delta)Q_k$
(objaśnienie 3 załącznika). Metodyka KZGW (2017) podaje w tym celu górną granicę jednostronnego przedziału
ufności kwantyla. **Hydrolog tej poprawki ani przedziału ufności nie liczy**; jeżeli projekt ich wymaga,
trzeba je wyznaczyć osobno, procedurą KZGW.

Prawdopodobieństwa z tabeli odpowiadają okresom powtarzalności od kilkudziesięciu do kilku tysięcy lat,
daleko poza długością obserwacji. W tym zakresie różnice między rozkładami i metodami są największe,
a próba prawie nic o nich nie mówi (przykłady 7.9 i 7.10). Kwantyl $Q_{0{,}1\%}$ z 34 lat danych jest
ekstrapolacją kształtu rozkładu, nie pomiarem.

## 7.9. Przykład: Czarna — Polana (metodyka KZGW 2017, przykład 3.2)

**Dane.** KZGW (2017, przykład 3.2, tab. 3.5) podaje 34 maksima roczne przepływu Czarnej w przekroju
wodowskazu Polana (zlewnia 94,17 km²) z lat hydrologicznych 1972–2005, w m³/s. W poleceniach
podaje się je wprost opcją `--values`, w kolejności lat.

**Trend.** Najpierw test Manna–Kendalla (rozdział 10):

```sh
hydrolog stats mann-kendall --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --years 1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005
```

Statystyka $S = 86$, $Z = 1{,}260$, poziom krytyczny $p = 0{,}208$: brak istotnego trendu na poziomie
0,05 (nachylenie Sena 0,60 m³/s na rok, przedział ufności od −0,30 do 1,35 m³/s na rok obejmuje
zero). KZGW (2017) drukuje $S = 85$; różnica wynika z innego liczenia par wartości równych (rozdział 10).

**Dopasowanie metodą L-momentów** (domyślną), dla prawdopodobieństw przewyższenia z tablicy KZGW:

```sh
hydrolog stats flood-frequency --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --return-periods 2,10,20,50,100,200,1000
```

| Rozkład (L-momenty) | $Q_{50\%}$ [m³/s] | $Q_{10\%}$ [m³/s] | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | $A^2$ | $A^2$ krytyczne 5 % | AIC |
|---|---|---|---|---|---|---|---|
| logarytmiczno-normalny | 25,4 | 67,2 | 148,6 | 265,3 | 0,362 | 0,922 | 303,0 |
| Weibulla | 26,4 | 69,8 | 126,5 | 180,3 | 0,290 | 5,37 | 303,8 |
| Pearsona III | 26,5 | 69,5 | 127,7 | 184,6 | 0,301 | 5,65 | 304,4 |
| GEV | 27,1 | 66,4 | 138,9 | 247,6 | 0,463 | 0,576 | 308,4 |

Żaden rozkład nie jest odrzucony testem $A^2$ na poziomie 5 %. GEV jest najbliżej granicy: jego $A^2$
przekracza wartość krytyczną poziomu 15 % (0,439), ale nie 10 % (0,497). Parametr kształtu GEV,
$c = -0{,}18$, oznacza ciężki ogon. Hydrolog wskazuje jako najlepszy rozkład logarytmiczno-normalny
(najmniejsze AIC, 303,0), lecz trzy pierwsze rozkłady dzielą mniej niż 1,4 jednostki AIC, czyli AIC ich
nie rozróżnia. Kwantyle bliskie środka próby ($Q_{50\%}$, $Q_{10\%}$) zgadzają się w granicach kilku
procent; $Q_{1\%}$ różnią się o 17 %, a $Q_{0{,}1\%}$ o 47 %. Największe maksimum próby, 111 m³/s,
ma prawdopodobieństwo empiryczne 0,0286, czyli okres powtarzalności 35 lat (pole `empirical`).

**Wszystkie metody naraz** (`--fit-method all`, 16 kombinacji w jednym rankingu AIC):

```sh
hydrolog stats flood-frequency --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --fit-method all --return-periods 2,10,20,50,100,200,1000
```

| Rozkład | Metoda | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | AIC |
|---|---|---|---|---|
| Pearsona III | momenty | 117,0 | 162,2 | 309,3 |
| Pearsona III | L-momenty | 127,7 | 184,6 | 304,4 |
| Pearsona III | MNW | 131,3 | 192,0 | 303,0 |
| Pearsona III | MNK | 140,9 | 207,3 | 303,3 |
| GEV | momenty | 117,3 | 169,5 | 311,7 |
| GEV | L-momenty | 138,9 | 247,6 | 308,4 |
| GEV | MNW | 204,2 | 543,1 | 306,7 |
| GEV | MNK | 158,4 | 296,3 | 309,3 |
| logarytmiczno-normalny | MNW | 152,4 | 273,4 | 303,0 |
| Weibulla | MNW | 126,8 | 181,8 | 302,8 |

Najmniejsze AIC całego rankingu ma rozkład Weibulla z MNW (302,8), ale dziewięć kombinacji mieści się
w 2 jednostkach od niego. Ta sama próba daje $Q_{1\%}$ od ok. 117 do 204 m³/s, a $Q_{0{,}1\%}$ od ok. 159
do 543 m³/s (pełny wynik polecenia). Skrajna jest GEV z MNW: parametr kształtu $c = -0{,}41$ (bardzo
ciężki ogon) daje $Q_{0{,}1\%}$ prawie trzy razy większe niż Pearson III, choć różnica AIC jest
niewielka. Momenty dają kwantyle najniższe, MNK — wysokie, zgodnie z p. 7.6.

**Porównanie z metodyką KZGW.** KZGW (2017, tab. 3.9) dopasowuje rozkład Pearsona III warunkową MNW
z dolnym ograniczeniem odczytanym graficznie i otrzymuje $Q_{1\%} = 123{,}2$ m³/s oraz
$Q_{0{,}1\%} = 177{,}1$ m³/s. Rozkład Pearsona III z L-momentów daje w Hydrologu kwantyle o ok. 4 %
wyższe, z pełnej MNW o 6,5 % ($Q_{1\%}$) i 8,4 % ($Q_{0{,}1\%}$) wyższe, a domyślny „najlepszy” rozkład
według AIC (logarytmiczno-normalny z L-momentów) $Q_{1\%}$ wyższe o 21 %. Jeżeli projekt ma być zgodny
z metodyką KZGW, trzeba zastosować jej procedurę, łącznie z górną granicą przedziału ufności (p. 7.8);
Hydrolog daje wtedy niezależne oszacowanie do porównania.

## 7.10. Przykład: Kaczawa — Świerzawa (IMGW-PIB 151150170), lata 1961–2025

**Dane.** Plik `docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv` zawiera
charakterystyki półroczne przepływu IMGW-PIB wodowskazu Świerzawa na Kaczawie, a plik
`kaczawa_swierzawa_Q_dobowe_1961_2025.csv` przepływy średnie dobowe; oba pochodzą z eksportu
Obserwatora (opis i warunki korzystania: `docs/podrecznik/dane/README.md`). Wszystkie 65 lat
hydrologicznych 1961–2025 są kompletne, łącznie z rokiem 1997.

**Jednorodność i trend** (rozdział 10):

```sh
hydrolog stats homogeneity --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv
```

Ciąg 65 maksimów rocznych podzielony na połowy (1961–1992 i 1993–2025) nie wykazuje różnic: test
Manna–Whitneya $p = 0{,}203$, Kołmogorowa–Smirnowa $p = 0{,}230$; test Pettitta wskazuje najbardziej
prawdopodobną zmianę przed rokiem 1994, ale z $p = 0{,}654$, czyli nieistotną. Test Manna–Kendalla na tych
samych maksimach z latami:

```sh
hydrolog stats mann-kendall --values 17.2,21.5,17.9,114,52.3,11.4,27.5,59.6,15.1,5.96,52.8,16.2,9.58,19.3,18.6,13.8,116,9.06,12.9,15.7,57,13,11.8,10.3,8.61,11.5,16,11.5,7.15,2.32,8.05,7.75,11.2,28.2,13,13.8,152,11.5,31,11.5,106,41,10.4,11.2,31,35,11.4,10,38,24,18.4,115,57.7,36.8,10,14.5,9.3,7.18,15.5,51,30.7,10.7,19,80.5,12.2 --years 1961,1962,1963,1964,1965,1966,1967,1968,1969,1970,1971,1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025
```

daje $S = -38$, $p = 0{,}834$: brak trendu. Ciąg można analizować jako jednorodny.

**Próba.** Maksima roczne IMGW-PIB wynoszą od 2,32 m³/s (1990) do 152 m³/s (1997); kolejne największe to
116 m³/s (1977), 115 m³/s (2012), 114 m³/s (1964) i 106 m³/s (2001). Momenty próby, odczytane
z dopasowania rozkładu Pearsona III metodą momentów (ramka `fit_moments`: parametry to średnia,
odchylenie i skośność próby), to średnia 28,8 m³/s, odchylenie standardowe 31,4 m³/s i skośność 2,24:
kilka wielkich wezbrań na tle wielu małych.

**Dopasowanie metodą L-momentów** (domyślne okresy powtarzalności):

```sh
hydrolog stats flood-frequency --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv
```

| Rozkład (L-momenty) | $Q_{50\%}$ [m³/s] | $Q_{10\%}$ [m³/s] | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | $A^2$ | $A^2$ krytyczne 5 % | AIC |
|---|---|---|---|---|---|---|---|
| GEV | 17,9 | 54,7 | 184,9 | 578,2 | 1,19 | 0,868 | 548,0 |
| logarytmiczno-normalny | 18,5 | 61,7 | 164,3 | 336,4 | 1,74 | 1,04 | 552,1 |
| Pearsona III | 15,2 | 66,8 | 166,6 | 276,2 | 11,8 | 70,3 | `null` |
| Weibulla | 16,0 | 64,1 | 175,4 | 324,7 | 5,47 | 31,0 | `null` |

Ten wynik wymaga ostrożności:

- Rozkłady Pearsona III i Weibulla z L-momentów mają dolne ograniczenie powyżej najmniejszych maksimów
  (uwaga `outside_support`: cztery najmniejsze maksima, od 2,32 do 7,18 m³/s, dla rozkładu Weibulla
  i sześć, do 8,05 m³/s, dla rozkładu Pearsona III), więc ich AIC jest `null` i trafiają na koniec
  rankingu.
- GEV ma najmniejsze AIC, ale jego $A^2 = 1{,}19$ przekracza wartość krytyczną poziomu 5 % (0,868) z jego
  własnego bootstrapu; rozkład logarytmiczno-normalny przekracza nawet wartość poziomu 1 % (1,46). Żaden
  z czterech rozkładów nie opisuje tej próby dobrze. Przy takim wyniku warto sprawdzić, czy maksima nie
  pochodzą z wezbrań o różnej genezie (np. roztopowych i opadowych), które należałoby analizować osobno.
- Kształt GEV $c = -0{,}48$ oznacza bardzo ciężki ogon: $Q_{0{,}1\%}$ jest trzykrotnie większe od $Q_{1\%}$
  i ponad dwukrotnie większe niż z rozkładu Pearsona III.

Pełny ranking (`--fit-method all`) dodaje dwie lekcje:

```sh
hydrolog stats flood-frequency --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv --fit-method all --return-periods 2,10,100,1000
```

Najmniejsze AIC (546,7) ma GEV z MNW, z $Q_{1\%} = 212{,}0$ m³/s i $Q_{0{,}1\%} = 759{,}3$ m³/s. Rozkład
Weibulla z MNW został pominięty (uwaga `distribution_left_out`, przyczyna `unbounded_likelihood`): jego
wiarygodność rośnie bez końca, gdy kształt spada do granicy podanej w ramce `fit_maximum_likelihood`,
a dolne ograniczenie zbliża się do najmniejszego maksimum (Smith 1985), więc maksimum nie istnieje.
Rozkład Pearsona III z MNW ma skośność 1,96, tuż poniżej granicy, i daje $Q_{1\%}$ tylko 121,8 m³/s
przy znacznie gorszym AIC (561,8).

**Maksima dobowe zamiast kulminacji.** To samo dopasowanie z maksimów średnich dobowych:

```sh
hydrolog stats flood-frequency --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date
```

daje GEV z $Q_{1\%} = 118{,}4$ m³/s zamiast 184,9 m³/s, czyli o 36 % mniej, a największe maksimum dobowe
roku 1997 wynosi 92,7 m³/s wobec 152 m³/s kulminacji. Kwantyle ze średnich dobowych nie zastąpią
kwantyli przepływów kulminacyjnych w małej zlewni. W trzech latach (1992, 1993 i 1995) maksimum półrocza
w danych IMGW-PIB jest nieco mniejsze od największego przepływu dobowego tego roku w danych dobowych —
publiczne dane różnych rodzajów nie zawsze są ze sobą uzgodnione, warto je porównać przed analizą.

**Związek z Kamiennikiem.** Zlewnia Kamiennika (37,22 km²) nie ma wodowskazu, więc jej przepływ
miarodajny wyznacza się z opadu (rozdziały 2–6). Analiza z tego przykładu pokazuje rząd wielkości
i rozrzut kwantyli w tej samej okolicy oraz to, jak mocno kulminacje małej zlewni przewyższają średnie
dobowe.

## 7.11. Podsumowanie: jak czytać wynik

- Sprawdź dane: rok hydrologiczny, kompletność lat, rodzaj maksimów (kulminacje czy średnie dobowe),
  długość ciągu, jednorodność i trend.
- Porównaj kilka rozkładów i metod, nie tylko pole `best_distribution`. Odrzuć dopasowania z $A^2$
  powyżej wartości krytycznej i z maksimami poza nośnikiem.
- Kwantyle dla $T$ wielokrotnie dłuższych od ciągu zależą bardziej od przyjętego rozkładu niż od danych;
  podawaj je z rozkładem, metodą i liczbą lat.
- Hydrolog nie realizuje procedury KZGW 2017 w całości (graficzne dolne ograniczenie, metoda decyli,
  trójparametrowy rozkład logarytmiczno-normalny, górna granica przedziału ufności); wynik zgodny
  z metodyką trzeba policzyć jej procedurą.

## Źródła

- Akaike H. (1974). A new look at the statistical model identification. *IEEE Transactions on Automatic
  Control* 19(6), 716–723. Niedostępne w otwartym dostępie.
- Burnham K.P., Anderson D.R. (2002). *Model Selection and Multimodel Inference: A Practical
  Information-Theoretic Approach*, wyd. 2. Springer, Nowy Jork. Niedostępne w otwartym dostępie.
- Coles S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer, Londyn.
  Niedostępne w otwartym dostępie.
- Hosking J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of
  order statistics. *Journal of the Royal Statistical Society, Series B* 52(1), 105–124. Niedostępne
  w otwartym dostępie.
- Hosking J.R.M., Wallis J.R. (1997). *Regional Frequency Analysis: An Approach Based on L-Moments*.
  Cambridge University Press. Niedostępne w otwartym dostępie.
- Hosking J.R.M. *lmom: L-moments*, pakiet R, wersja 3.3. https://cran.r-project.org/package=lmom
- IACWD — Interagency Advisory Committee on Water Data (1982). *Guidelines for Determining Flood Flow
  Frequency, Bulletin 17B*. U.S. Geological Survey, Reston.
  https://pubs.usgs.gov/unnumbered/70275162/report.pdf
- IMGW-PIB, Arcadis, Multiconsult (2022). *Raport z opracowania danych hydrologicznych na potrzeby
  modelowania hydraulicznego*, zał. 4 do raportu z przeglądu i aktualizacji map zagrożenia powodziowego
  i map ryzyka powodziowego, wersja 2.00.
  https://powodz.gov.pl/wp-content/uploads/2026/10/aMZPiMRP-Zal4-Raport-HYDROLOGIA-20220907-v2.00-pub.pdf
- IMGW-PIB. Dane publiczne, dane hydrologiczne, opis `hydrologia_info_ogolne.txt` (rok hydrologiczny
  i półrocza). https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych oraz identyfikacji
  modeli transformacji opadu w odpływ* (oprac. K. Banasik, A. Wałęga, S. Węglarczyk, B. Więzik,
  Stowarzyszenie Hydrologów Polskich), załącznik 2 do OPZ, wersja ujednolicona. Krajowy Zarząd Gospodarki
  Wodnej, Warszawa.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- NIST/SEMATECH (2012). *e-Handbook of Statistical Methods*, rozdz. 1.3.5.14 (test Andersona–Darlinga).
  https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm
- Rozporządzenie Ministra Infrastruktury z dnia 4 maja 2026 r. w sprawie warunków technicznych, jakim
  powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2026 poz. 692), załącznik nr 3.
  https://dziennikustaw.gov.pl/D2026000069201.pdf
- Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim
  powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579), uchylone.
- Smith R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. *Biometrika* 72(1),
  67–90. Niedostępne w otwartym dostępie.
- Stephens M.A. (1974). EDF statistics for goodness of fit and some comparisons. *Journal of the American
  Statistical Association* 69(347), 730–737. Niedostępne w otwartym dostępie.
- Stute W., González Manteiga W., Presedo Quindimil M. (1993). Bootstrap based goodness-of-fit-tests.
  *Metrika* 40, 243–256. Skan w bibliotece EuDML: https://eudml.org/doc/176470
- Virtanen P. i in. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python.
  *Nature Methods* 17, 261–272 (`scipy.stats`). https://docs.scipy.org/doc/scipy/reference/stats.html
- Węglarczyk S. (red.) (2013). *Problemy obliczania przepływów ekstremalnych w zlewniach kontrolowanych
  i niekontrolowanych*. Monografie Komitetu Gospodarki Wodnej PAN 35, Warszawa.
  https://kgw.pan.pl/files/35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf
- WMO (2009). *Guide to Hydrological Practices*, wyd. 6, t. II: *Management of Water Resources and
  Application of Hydrological Practices*, WMO-No. 168, rozdz. 5. Genewa.
  https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf

Dane przykładu 7.10: źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej –
Państwowy Instytut Badawczy; dane IMGW-PIB zostały przetworzone (regulamin:
https://danepubliczne.imgw.pl/regulations).
