# 2. Opad

Obliczenie wezbrania metodą opad–odpływ zaczyna się od trzech pytań o opad: ile go spadnie (wysokość o danym
czasie trwania i prawdopodobieństwie przewyższenia), jak rozłoży się na zlewni (opad obszarowy) i jak rozłoży
się w czasie (hietogram). Rozdział odpowiada na nie w tej kolejności: omawia opad obszarowy z posterunków,
atlas PMAXTP Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego (IMGW-PIB) oraz
cztery hietogramy projektowe Hydrologa. Kończy się deszczem projektowym zlewni Kamiennika po Świerzawę, z
którego korzystają dalsze rozdziały.

Równanie, zmienne z jednostkami, stałe i zakresy każdej metody stoją w ramce generowanej ze specyfikacji
formuły w kodzie Hydrologa (zob. „Jak czytać” w [README](README.md) i [dodatek D](D-weryfikacja.md)). Tekst
ich nie powtarza: opisuje konstrukcję słowami, podaje źródła, zastosowania i sposób czytania wyniku.

## 2.1 Pojęcia podstawowe

**Wysokość opadu** $P$ [mm] to warstwa wody, jaką opad utworzyłby na poziomej powierzchni; **natężenie**
$i$ [mm/h] to wysokość na jednostkę czasu. **Czas trwania** $D$ [min] to długość deszczu, a **krok**
$\Delta t$ [min] — długość przedziałów, na które się go dzieli. **Hietogram** (ang. *hyetograph*) to ciąg
wysokości opadu w kolejnych krokach; natężenie w kroku to jego wysokość podzielona przez długość kroku.

**Krzywa wysokość–czas trwania** (ang. *depth–duration–frequency*, DDF) podaje dla ustalonego
prawdopodobieństwa największą wysokość opadu $h(D)$ o czasie trwania $D$. Jej odpowiednikiem w natężeniach
jest krzywa natężenie–czas trwania–częstość (IDF). Wysokość rośnie z czasem trwania, a natężenie średnie
maleje: krótkie deszcze są intensywniejsze.

**Prawdopodobieństwo przewyższenia** $p$ [%] (ang. *exceedance probability*) to prawdopodobieństwo, że w
danym roku wartość zostanie osiągnięta lub przekroczona. W praktyce projektowej utożsamia się je z
odwrotnością **okresu powtarzalności** $T$ (ang. *return period*): $p$ = 1 % to „opad stuletni”. W
projektowaniu kanalizacji mówi się też o **częstości** deszczu $C$ w latach.

**Doba opadowa** IMGW-PIB trwa od 06.01 UTC jednego dnia do 06.00 UTC dnia następnego, a suma dobowa jest
zapisana pod datą dnia, w którym doba się zaczyna: opad z datą 13 września spadł od 13 września 06 UTC do
14 września 06 UTC (IMGW-PIB, Rocznik Meteorologiczny 2025, rozdz. 1.1; Rocznik podaje tę definicję dla
stacji synoptycznych, a według biuletynów IMGW-PIB posterunki opadowe mierzą o tej samej porze). Suma z doby stałej jest nie większa od
największej sumy 24-godzinnej w oknie ruchomym, dlatego dobowych maksimów ze stacji nie należy porównywać
wprost z wartościami PMAXTP dla 1440 min.

**Opad punktowy i obszarowy.** Deszczomierz i atlas PMAXTP podają opad w punkcie. Dla zlewni potrzebny
jest opad średni na jej powierzchni (p. 2.2). Według DVWK (1984), za metodyką KZGW (2017, s. 105), wysokości z
analizy danych jednej stacji są reprezentatywne tylko dla bardzo małych zlewni, do ok. 10 km²; dla
większych należy je zredukować, przy czym dla zlewni od 10 do 100 km² redukcja nie przekracza 10 %.
Współczynnik redukcji obszarowej (ang. *areal reduction factor*, ARF) rośnie z czasem trwania deszczu i
maleje z powierzchnią zlewni. Ani PMAXTP, ani Hydrolog takiego współczynnika nie podają; zlewnia Kamiennika
(37,22 km²) leży w przedziale, w którym redukcja może sięgać 10 %, a przykłady podręcznika używają wartości
punktowej, czyli liczą po stronie bezpiecznej.

**Założenie metodyki.** Polska metodyka hydrogramów projektowych jest „oparta na założeniu o równości
prawdopodobieństwa wystąpienia deszczu i wywołanego nim wezbrania” (KZGW 2017, s. 103). To uproszczenie:
deszcz stuletni nie zawsze wywołuje wezbranie stuletnie, bo wezbranie zależy też od stanu zlewni przed
deszczem (rozdz. 3) i od rozkładu deszczu w czasie (p. 2.4).

## 2.2 Opad obszarowy

Opad średni w zlewni liczy się z wysokości zmierzonych na posterunkach w zlewni i w jej sąsiedztwie. Metodyka
KZGW (2017, s. 15–17) wymienia jako najczęściej stosowane metodę wieloboków równego opadu (Thiessena) i metodę
izohiet, a „w uzasadnionych przypadkach” inne, np. kriging. Hydrolog liczy cztery metody poleceniem
`precip areal`: średnią arytmetyczną, wieloboki Thiessena, odwrotne odległości (IDW) i izohiety. Współrzędne
posterunków muszą być w układzie metrycznym (w Polsce zwykle PL-1992, EPSG:2180); wynik metod
odległościowych nie zależy od jednostki odległości, ale od układu — w stopniach geograficznych odległości
są zniekształcone.

### Średnia arytmetyczna

Każdy posterunek ma tę samą wagę. Metoda wystarcza, gdy posterunki są rozmieszczone równomiernie, a teren
jest płaski; nie bierze pod uwagę ani położenia posterunków względem zlewni, ani rzeźby terenu.

<!-- spec:areal_mean_precipitation -->

<a id="spec-areal_mean_precipitation"></a>

> **Opad obszarowy jako średnia arytmetyczna z posterunków** · specyfikacja [`areal_mean_precipitation`](../FORMULAS.md#areal_mean_precipitation) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \bar{P} = \frac{1}{n}\sum_{i=1}^{n} P_i
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_i$ | `precipitation_mm` (ciąg) | Wysokość opadu na każdym posterunku | mm | [0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\bar{P}$ | `areal_precipitation_mm` | Średni opad w zlewni | mm | [0; ∞) |
>
> **Konwencje**
>
> - wysokości w mm; podaje się tylko posterunki leżące w zlewni (Chow i in. 1988 pomijają posterunki poza nią)
> - sumę liczy `math.fsum`, z poprawnym zaokrągleniem
>
> **Zgodność z obserwacjami według źródeł:** Chow i in. (1988, s. 78) uznają metodę za zadowalającą, gdy posterunki są rozmieszczone równomiernie na terenie płaskim; brak statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 3.4, Fig. 3.4.3(a), p. 78: the arithmetic mean of the gauges within the watershed <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 2. Hydrograf's areal PMAXTP depth (Thiessen cells of the PMAXTP grid points of a catchment) over the depths of Hydrolog's PMAXTP fixtures for Kamiennik and Warsaw (POT, recorded in November 2026), tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm
>
> Funkcja `hydrolog.precipitation.interpolation.areal_mean_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:areal_mean_precipitation -->

### Wieloboki Thiessena

Każdy punkt zlewni przypisuje się najbliższemu posterunkowi. Granice obszarów (wieloboków równego opadu,
ang. *Thiessen polygons*) to symetralne odcinków łączących sąsiednie posterunki; opad średni to średnia
wysokości z posterunków ważona polami ich wieloboków w zlewni (KZGW 2017, s. 15, rys. 2.1). Hydrolog nie
wyznacza wieloboków: pola wieloboków w zlewni liczy się w GIS i podaje w opcji `--polygon-areas-km2`.
Metoda nie uwzględnia orografii: jeden posterunek górski może reprezentować dużą część zlewni. IMGW-PIB
zrezygnował z niej przy mapach PMAXTP, bo wiele punktów pomiarowych leży w terenie podgórskim i górskim
(Ozga-Zieliński red. 2022, s. 9).

<!-- spec:thiessen_precipitation -->

<a id="spec-thiessen_precipitation"></a>

> **Opad obszarowy metodą wieloboków Thiessena** · specyfikacja [`thiessen_precipitation`](../FORMULAS.md#thiessen_precipitation) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \bar{P} = \frac{\sum_i A_i P_i}{\sum_i A_i},\quad w_i = \frac{A_i}{\sum_j A_j}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_i$ | `precipitation_mm` (ciąg) | Wysokość opadu na każdym posterunku | mm | [0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 4) |
> | $A_i$ | `polygon_areas_km2` (ciąg) | Powierzchnia wieloboku każdego posterunku w granicach zlewni | km² | [0; ∞) | nie podano w źródłach | [0,22; 4,02] (źr. 1) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\bar{P}$ | `areal_precipitation_mm` | Średni opad w zlewni | mm | [0; ∞) |
> | $w_i$ | `weights` (ciąg) | Waga każdego posterunku; wagi sumują się do jedności | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jedna powierzchnia wieloboku na każdy posterunek | `gauge_count` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | sum(A_i) > 0: wieloboki pokrywają choć część zlewni | `area_positive` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - wysokości w mm, powierzchnie w km² (każda jedna jednostka daje tę samą średnią)
> - wagi to powierzchnie podzielone przez ich sumę: KZGW (2017, wzór 2.1) dzieli przez powierzchnię zlewni, co daje to samo, gdy wieloboki pokrywają zlewnię
> - wieloboki są dane; ich wyznaczenie nie należy do wzoru
>
> **Zgodność z obserwacjami według źródeł:** brak: Chow i in. (1988, s. 78) opisują metodę jako dokładniejszą od średniej arytmetycznej, gdy posterunki są rozmieszczone nierównomiernie, ale nie podają statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 3.4, eq. 3.4.1 and Fig. 3.4.3(b), pp. 78-79: the polygons of the example, 0.22 to 4.02 km2 <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), ch. II.1, eq. 2.1, pp. 15-16: metoda wieloboków równego opadu (after Byczkowski 1996) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 3. Thiessen, A.H. (1911). Precipitation averages for large areas. Monthly Weather Review 39(7), 1082-1084 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Hydrograf's areal PMAXTP depth (Thiessen cells of the PMAXTP grid points of a catchment) over the depths of Hydrolog's PMAXTP fixtures for Kamiennik and Warsaw (POT, recorded in November 2026), tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm
>
> Funkcja `hydrolog.precipitation.interpolation.thiessen_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:thiessen_precipitation -->

### Odwrotne odległości (IDW)

Wartość w punkcie to średnia wysokości z posterunków z wagami malejącymi z potęgą odległości (ang. *inverse
distance weighting*; Chow, Maidment i Mays 1988, s. 79, za Wei i McGuinnessem 1973). Im większy wykładnik
potęgi, tym silniej liczą się posterunki bliskie. Opad średni w zlewni otrzymuje się, licząc IDW w węzłach
siatki pokrywającej zlewnię i uśredniając; Hydrolog przyjmuje taką siatkę w opcjach `--grid-x` i `--grid-y`,
a pojedynczy punkt w `--target-x` i `--target-y`.

<!-- spec:idw_precipitation -->

<a id="spec-idw_precipitation"></a>

> **Opad w punkcie metodą odwrotnych odległości (IDW) z posterunków** · specyfikacja [`idw_precipitation`](../FORMULAS.md#idw_precipitation) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> P = \sum_i w_i P_i,\quad w_i = \frac{d_i^{-p}}{\sum_j d_j^{-p}},\quad d_i = \sqrt{(x_i - x)^2 + (y_i - y)^2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `station_x_m` (ciąg) | Współrzędna wschodnia (easting) każdego posterunku | m | (−∞; ∞) | nie podano w źródłach | [545 900; 562 900] (źr. 5) |
> | $y_i$ | `station_y_m` (ciąg) | Współrzędna północna (northing) każdego posterunku | m | (−∞; ∞) | nie podano w źródłach | [229 400; 249 700] (źr. 5) |
> | $P_i$ | `precipitation_mm` (ciąg) | Wysokość opadu na każdym posterunku | mm | [0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 6) |
> | $x$ | `target_x_m` | Współrzędna wschodnia punktu | m | (−∞; ∞) | nie podano w źródłach | [545 900; 562 900] (źr. 5) |
> | $y$ | `target_y_m` | Współrzędna północna punktu | m | (−∞; ∞) | nie podano w źródłach | [229 400; 249 700] (źr. 5) |
> | $p$ | `power` | Wykładnik potęgi odległości | – | (0; ∞) | nie podano w źródłach | [2; 2] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $P$ | `point_precipitation_mm` | Opad w punkcie | mm | [0; ∞) |
> | $w_i$ | `weights` (ciąg) | Waga każdego posterunku; wagi sumują się do jedności | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | dwie współrzędne i wysokość opadu dla każdego posterunku | `station_count` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - współrzędne w metrach jednego układu odwzorowania (w Polsce EPSG:2180); wagi zależą tylko od stosunków odległości, więc każda jedna jednostka daje to samo oszacowanie, z wyjątkiem progu, poniżej którego posterunek leży w punkcie, 1e-10 jednostki
> - używa się każdego podanego posterunku: najbliższy posterunek w każdej ćwiartce i największa odległość z HEC-HMS to wybory wywołującego; posterunki leżące w punkcie dzielą go między siebie po równo
> - wagi liczy się z ln d względem najbliższego posterunku, więc d**-p ani nie przekracza zakresu float, ani nie zanika do sumy zerowej
>
> **Zgodność z obserwacjami według źródeł:** brak: źródła podają metodę bez statystyki błędu; HEC-HMS stosuje ją w prognozach w czasie rzeczywistym
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Indian Institute of Technology Roorkee, NPTEL course Hydrology (105107129), module 3, lecture 4, 3.6 Estimation of missing data, eq. 3.12 (the distance power method, weights 1/D^2) and Example 3.7 <https://archive.nptel.ac.in/content/storage2/courses/105107129/module3/lecture4/lecture4.pdf>
> 2. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual: Inverse distance gage weighting, the weight of a gage, 1/d^2 over the sum of 1/d^2 of the gages <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/meteorology/precipitation/inverse-distance-gage-weighting>
> 3. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, p. 79: the reciprocal-distance-squared method (Wei and McGuinness 1973); HEC-HMS's inverse distance gage weighting and Hydrolog's default use p = 2 <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 4. Shepard, D. (1968). A two-dimensional interpolation function for irregularly-spaced data. Proceedings of the 1968 23rd ACM National Conference, 517-524 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. Hydrolog's catalog example of precip areal: three gauges near Kraków in EPSG:2180, src/hydrolog/catalog/groups/precip.py, the examples of precip areal: x 545,900 to 562,900 m, y 229,400 to 249,700 m
> 6. Hydrograf's areal PMAXTP depth (Thiessen cells of the PMAXTP grid points of a catchment) over the depths of Hydrolog's PMAXTP fixtures for Kamiennik and Warsaw (POT, recorded in November 2026), tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm
>
> Funkcja `hydrolog.precipitation.interpolation.idw_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:idw_precipitation -->

<!-- spec:idw_grid_mean -->

<a id="spec-idw_grid_mean"></a>

> **Opad obszarowy jako średnia oszacowań IDW w węzłach siatki** · wzór grupy B `idw_grid_mean` (Tier B, CMP-2.2)
>
> **Definicja:** opad obszarowy zlewni jako średnia arytmetyczna oszacowań IDW (`idw_precipitation`) w punktach siatki (źr. 1)
>
> **Konwencja:** średnia z punktów jest średnią w zlewni tylko dla regularnej siatki punktów leżących w jej granicach; w każdym punkcie używa się każdego posterunku
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 3.4, p. 79: an areal mean from values interpolated at grid points by the reciprocal-distance-squared method <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
>
> Funkcja `hydrolog.precipitation.interpolation.areal_precipitation_idw`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:idw_grid_mean -->

### Izohiety

Izohiety (linie równego opadu, ang. *isohyets*) kreśli się, interpolując między posterunkami, w górach
zgodnie z rzeźbą terenu (KZGW 2017, s. 16–17). Opad średni to średnia z pasów między kolejnymi izohietami
ważona ich udziałem w powierzchni zlewni; za opad pasa przyjmuje się zwykle średnią jego granic. Pasy
skrajne, ograniczone jedną izohietą i granicą zlewni, wymagają oszacowania. Hydrolog przyjmuje wartości
izohiet (`--isohyet-values-mm`) i udziały pasów (`--area-fractions`); pas skrajny zapisuje się granicą
umowną, dla której średnia granic równa się oszacowanemu opadowi pasa (ADR-0046, za Chow i in. 1988).

<!-- spec:isohyet_precipitation -->

<a id="spec-isohyet_precipitation"></a>

> **Opad obszarowy metodą izohiet** · specyfikacja [`isohyet_precipitation`](../FORMULAS.md#isohyet_precipitation) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \bar{P} = \frac{\sum_i A_i \frac{v_i + v_{i+1}}{2}}{\sum_i A_i}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $v_i$ | `isohyet_values_mm` (ciąg) | Wartości kolejnych izohiet ograniczających pasy | mm | [0; ∞) | nie podano w źródłach | [10; 50] (źr. 1) |
> | $A_i$ | `zone_areas_km2` (ciąg) | Powierzchnia każdego pasa między dwiema kolejnymi izohietami | km² | [0; ∞) | nie podano w źródłach | [0,2; 3,01] (źr. 1) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\bar{P}$ | `areal_precipitation_mm` | Średni opad w zlewni | mm | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n izohiet ogranicza n - 1 pasów | `zone_count` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | sum(A_i) > 0: pasy pokrywają choć część zlewni | `area_positive` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - wysokości w mm, powierzchnie w km² (każda jedna jednostka daje tę samą średnią, więc także udziały w powierzchni zlewni)
> - opad pasa to średnia jego dwóch izohiet (KZGW 2017, wzór 2.2); pas skrajny dostaje granicę umowną, dla której ta średnia równa się oszacowanemu dla niego opadowi (Chow i in. 1988, rys. 3.4.3c: granice 0 i 56 mm dla 5 i 53 mm)
> - powierzchnie dzieli się przez ich sumę, czyli powierzchnię zlewni, gdy pasy ją pokrywają
>
> **Zgodność z obserwacjami według źródeł:** brak: Chow i in. (1988, s. 80) nazywają metodę najdokładniejszą z trzech, gdy izohiety kreśli się zgodnie z rzeźbą terenu; brak statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 3.4, Fig. 3.4.3(c), p. 80: the isohyets 10 to 50 mm and the zones of 0.20 to 3.01 km2 of the example <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), ch. II.1, eq. 2.2, pp. 16-17: metoda izohiet, the mean between neighbouring isohyets times the area between them (after Byczkowski 1996) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
>
> Funkcja `hydrolog.precipitation.interpolation.isohyet_precipitation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:isohyet_precipitation -->

Krigingu (metody geostatystycznej) Hydrolog nie liczy.

### Przykład 2.1. Kamiennik, doba opadowa 13 września 2024 r.

W połowie września 2024 r. niż genueński „Boris” przyniósł na Dolny Śląsk wielodniowe ulewy. Doba opadowa
z datą 13 września (od 13 IX 06 UTC do 14 IX 06 UTC) dała na posterunkach wokół zlewni Kamiennika wysokości
z tabeli. Posterunek Świerzawa leży przy przekroju zamykającym; pozostałe — 9–15 km od granicy zlewni.
Posterunek Kaczorów nie ma wartości z tej doby i nie wchodzi do obliczeń.

| Posterunek lub stacja (kod IMGW-PIB) | x [m] | y [m] | $P$ [mm] |
|---|---|---|---|
| Świerzawa (251150360) | 281 862 | 354 619 | 105,5 |
| Bolków (250160030) | 296 162 | 343 800 | 87,4 |
| Jawor (251160290) | 302 720 | 358 943 | 85,0 |
| Twardocice (251150280) | 272 312 | 363 228 | 78,6 |
| Ciechanowice (250150130) | 287 372 | 337 721 | 84,8 |
| Jelenia Góra, stacja synoptyczna (350150500) | 274 287 | 341 954 | 81,3 |

Współrzędne są w układzie PL-1992 (x — na wschód, y — na północ). Plik
[`dane/kamiennik_opad_2024-09-13.csv`](dane/kamiennik_opad_2024-09-13.csv) zawiera te wartości w formacie
polecenia `precip areal`; jego pochodzenie opisuje [`dane/README.md`](dane/README.md). Polecenia uruchamia się
z katalogu głównego repozytorium Hydrologa.

**Średnia arytmetyczna** sześciu posterunków:

```sh
hydrolog precip areal --method arithmetic --stations-file docs/podrecznik/dane/kamiennik_opad_2024-09-13.csv
```

daje 87,10 mm.

**Wieloboki Thiessena.** Pola wieloboków w zlewni policzono w GIS z granicy zlewni wyznaczonej przez
Hydrograf (37,2234 km²): wielobok Świerzawy obejmuje 37,0004 km², Jaworu 0,2161 km², Bolkowa 0,0069 km²,
pozostałe posterunki leżą za daleko, by ich wieloboki sięgały zlewni.

```sh
hydrolog precip areal --method thiessen --stations-file docs/podrecznik/dane/kamiennik_opad_2024-09-13.csv --polygon-areas-km2 '{"Świerzawa":37.0004,"Jawor":0.2161,"Bolków":0.0069,"Twardocice":0,"Ciechanowice":0,"Jelenia Góra":0}'
```

Wynik: 105,38 mm; waga Świerzawy wynosi 99,4 %, Jaworu 0,6 %.

**IDW na siatce.** Środki 39 kwadratów siatki kilometrowej układu PL-1992 leżące w zlewni, wykładnik
domyślny (ramka):

```sh
hydrolog precip areal --method idw --stations-file docs/podrecznik/dane/kamiennik_opad_2024-09-13.csv --grid-x 290500,287500,288500,289500,290500,284500,285500,286500,287500,288500,289500,290500,282500,283500,284500,285500,286500,287500,288500,289500,290500,291500,292500,283500,284500,285500,286500,287500,288500,289500,290500,291500,292500,283500,284500,285500,286500,292500,284500 --grid-y 351500,352500,352500,352500,352500,353500,353500,353500,353500,353500,353500,353500,354500,354500,354500,354500,354500,354500,354500,354500,354500,354500,354500,355500,355500,355500,355500,355500,355500,355500,355500,355500,355500,356500,356500,356500,356500,356500,357500
```

Wynik: 97,14 mm. Z wykładnikiem 1 (`--power 1`) ten sam rachunek daje 92,21 mm, z wykładnikiem 4 —
101,70 mm. W samym środku ciężkości zlewni (x = 287 695 m, y = 354 663 m):

```sh
hydrolog precip areal --method idw --stations-file docs/podrecznik/dane/kamiennik_opad_2024-09-13.csv --target-x 287695 --target-y 354663
```

IDW daje 97,05 mm, a Świerzawa ma w nim wagę 60,7 %.

**Jak czytać wyniki.** Trzy metody dały dla tej samej doby od 87,10 do 105,38 mm, czyli różnią się o 21 %.
Rozrzut nie mówi, która metoda jest lepsza, tylko jak rzadka jest sieć: jedyny posterunek przy zlewni stoi w
jej najniższym punkcie, a pozostałe leżą poza nią. Wieloboki Thiessena oddają całą zlewnię Świerzawie,
średnia arytmetyczna równo traktuje posterunki odległe o kilkanaście kilometrów, a IDW leży między nimi i
zależy od wykładnika. Opadu w górnej części zlewni, wyżej położonej, żadna z metod nie zna. Taką niepewność
zmniejszają dopiero dane radarowe, dodatkowe posterunki albo — w obliczeniach projektowych — atlas PMAXTP,
który podaje wartości dla każdego punktu kraju (p. 2.3).

Dla porównania z wartościami projektowymi: dobowa suma w Świerzawie (105,5 mm) leży w PMAXTP (metoda POT,
punkt przekroju Kamiennika, 1440 min) między wartością dla 3 % (104,27 mm) a dla 2 % (113,32 mm):

```sh
hydrolog precip pmaxtp --latitude 51.01544 --longitude 15.88984 --duration-min 1440 --probability-percent 3
hydrolog precip pmaxtp --latitude 51.01544 --longitude 15.88984 --duration-min 1440 --probability-percent 2
```

Ponieważ doba stała obejmuje nie więcej opadu niż najbardziej deszczowe 24 godziny tego zdarzenia, jego
największa suma 24-godzinna była zapewne rzadsza.

### Przykład 2.2. Izohiety (Chow, Maidment i Mays 1988, rys. 3.4.3c)

Podręcznik Chowa i in. pokazuje zlewnię o powierzchni 9,14 km² z pasami między izohietami o polach 0,88;
1,59; 2,24; 3,01; 1,22 i 0,20 km² i średnich 5, 15, 25, 35, 45 i 53 mm, z których skrajne (5 i 53 mm)
oszacowano. W zapisie Hydrologa pasy skrajne mają granice umowne 0 i 56 mm, bo (0 + 10)/2 = 5 i
(50 + 56)/2 = 53, a udziały pasów to ich pola podzielone przez 9,14 km²:

```sh
hydrolog precip areal --method isohyet --isohyet-values-mm 0,10,20,30,40,50,56 --area-fractions 0.0963,0.174,0.2451,0.3293,0.1335,0.0219
```

Hydrolog daje 27,91 mm; podręcznik — 27,9 mm.

### Typowe błędy

- **Współrzędne w stopniach** zamiast w układzie metrycznym: odległości IDW i wieloboki Thiessena są wtedy
  zniekształcone (stopień długości geograficznej jest w Polsce o ok. 35–40 % krótszy od stopnia szerokości).
- **Brak wartości wzięty za zero**: posterunek bez pomiaru (Kaczorów w przykładzie 2.1) trzeba pominąć i
  przeliczyć wieloboki bez niego, a nie wpisywać 0 mm.
- **Pola wieloboków, które nie sumują się do pola zlewni**, np. z pominiętym wielobokiem posterunku spoza
  zlewni. Hydrolog dzieli przez sumę podanych pól, więc pominięty wielobok po cichu zmienia wagi pozostałych.
- **Posterunek górski reprezentujący dużą część zlewni** bez sprawdzenia, czy opad zależy od wysokości.
- **Opad obszarowy z jednego posterunku** nazwany „średnim w zlewni” bez słowa o reprezentatywności (p. 2.1).

## 2.3 PMAXTP: opady maksymalne o określonym czasie trwania i prawdopodobieństwie przewyższenia

### Czym jest PMAXTP

PMAXTP (*Precipitation MAXimum Time (duration) Probability*) to opracowanie IMGW-PIB z 2022 r., które dla
każdego punktu Polski podaje wysokości opadów maksymalnych dla 16 czasów trwania, od 5 min do 72 h, i
27 prawdopodobieństw przewyższenia, od 99,9 % do 0,01 % (Ozga-Zieliński red. 2022, s. 10). Podstawą są
30-letnie ciągi (1986–2015) ze stu deszczomierzy w miarę równomiernie rozłożonych na obszarze Polski, z bazy
danych opadowych o wysokiej rozdzielczości, sprawdzonej m.in. z obrazami radarowymi systemu POLRAD (s. 8–9).
W każdym punkcie pomiarowym dopasowano metodą największej wiarygodności kilka rozkładów (Pearsona typu III,
logarytmiczno-normalny, Weibulla, log-gamma i Gumbela), wybrano najlepiej dopasowany i najbardziej
wiarygodny i wyznaczono przedział ufności kwantyli (s. 9–10). Kwantyle skorygowano tak, by rosły z czasem
trwania (rozdz. 3.5, s. 32 i nast.). Wartości między punktami pomiarowymi interpolowano krigingiem resztowym;
wieloboki Thiessena odrzucono, bo wiele punktów leży w górach i na pogórzu (s. 9 i 43). Tablica punktu
podaje kwantyl `ks` (wartość projektową), błąd estymacji `rb` i górną granicę przedziału ufności
`sg` = `ks` + `rb` (słowniczek aplikacji https://klimat.imgw.pl/opady-maksymalne/).

**AMP i POT.** Atlas ma dwie wersje, liczone z dwóch rodzajów ciągów (s. 13): **AMP** (ang. *annual
maximum precipitation*, metoda maksimów rocznych) — jeden największy opad z każdego roku; **POT** (ang.
*peaks over threshold*, metoda przewyższeń) — wszystkie opady wyższe od progu rosnącego z czasem trwania,
w PMAXTP 30 największych z 30 lat. Wadą AMP jest pominięcie wysokich opadów, które w danym roku nie były
największe. Obie metody dają bardzo różne kwantyle dla prawdopodobieństw bliskich 100 %. Dlatego IMGW-PIB
zaleca dla prawdopodobieństw 50 % i większych, np. przy projektowaniu i modelowaniu hydrodynamicznym
odwodnień, modele z ciągów POT, bo wtedy wynik „leży po tzw. bezpiecznej stronie”, a dla prawdopodobieństw
mniejszych od 50 % uznaje obie metody za „równorzędne – zastępowalne” (s. 23). Nie jest to więc zalecenie
POT bez zastrzeżeń.

**Czym PMAXTP nie jest.** PMAXTP to nie **opad maksymalny prawdopodobny** (ang. *probable maximum
precipitation*, PMP), czyli największa wysokość opadu o danym czasie trwania, jaka jest meteorologicznie
możliwa nad daną zlewnią w danym miejscu i porze roku, bez uwzględnienia długookresowych zmian klimatu (WMO
2009). Pomyłkę ułatwia język: w polskiej tradycji „przepływ maksymalny prawdopodobny” oznacza kwantyl
(rozdz. 7), a podobnie bywają nazywane opady o zadanym prawdopodobieństwie, także w samej monografii PMAXTP
(s. 9). Polski termin jest jednak dosłownym tłumaczeniem *probable maximum precipitation*, dlatego podręcznik
rezerwuje nazwę „opad maksymalny prawdopodobny” dla PMP, a wartości PMAXTP nazywa opadami maksymalnymi o
określonym czasie trwania i prawdopodobieństwie przewyższenia. Różnica jest zasadnicza: PMAXTP to kwantyle
rozkładu częstości; wartość dla 1 % zostanie kiedyś przekroczona, a PMP z założenia nie powinien być.
PMAXTP nie podaje też rozkładu opadu w czasie (hietogramu) ani współczynnika redukcji obszarowej: jego
wartości dotyczą opadu w punkcie, nie średniego opadu zlewni.

**Poprzednik.** Przed PMAXTP stosowano model IMGW Bogdanowicz i Stachý (1998), oparty na danych
pluwiograficznych z 20 stacji z lat 1960–1990, z regionalizacją Polski z wyłączeniem gór; formuła nie
obejmuje Karpat i Sudetów, więc i zlewni Kamiennika (KZGW 2017, s. 103–104). Według monografii PMAXTP
regionalizacja okazała się „zbyt generalna”, a charakterystyki różniły się znacząco od modeli lokalnych
(s. 8). Hydrolog jej nie liczy.

**Zastosowanie.** Barszcz, Kaznowska i Wasilewicz (2024) sprawdzili modelem SWMM kanalizację deszczową
Lotniska Chopina w Warszawie opadem o prawdopodobieństwie przewyższenia 20 % i czasie trwania 15 min:
kwantyl PMAXTP dla stacji Warszawa-Okęcie wyniósł 16,32 mm, formuła Bogdanowicz–Stachý dała 19,00 mm, a
dawny model Błaszczyka 11,88 mm. Autorzy zalecają zaprzestać projektowania kanalizacji modelem Błaszczyka na
rzecz PMAXTP.

### PMAXTP w Hydrologu

Polecenie `precip pmaxtp` pobiera z IMGW-PIB (przez dodatek `pmaxtp` Obserwatora) wysokość opadu dla punktu,
czasu trwania i prawdopodobieństwa, metodą POT albo AMP, oraz wysokości wszystkich 16 czasów trwania przy tym
prawdopodobieństwie (`depth_duration_mm`) — krzywą potrzebną deszczowi Eulera typu II (p. 2.4). To jedyne
polecenie Hydrologa, które korzysta z sieci ([ADR-0018](../decisions/0018-pmaxtp-through-obserwator.md),
[ADR-0042](../decisions/0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md)). Wynik podaje kwantyl
`ks`; błędu estymacji i granicy przedziału ufności nie podaje. Wynik niesie też wiersze przypisania, które
regulamin danych PMAXTP każe umieścić w każdym produkcie: źródło danych, informację o ich przetworzeniu i
monografię; trzeba je przenieść do obliczeń, w których wysokość zostanie użyta (opcja `--attribution`).

<!-- spec:pmaxtp_depth -->

<a id="spec-pmaxtp_depth"></a>

> **Wysokość opadu z tablic PMAXTP** · wzór grupy B `pmaxtp_depth` (Tier B, CMP-2.2)
>
> **Definicja:** wysokość z tablicy PMAXTP IMGW-PIB dla punktu, czasu trwania i prawdopodobieństwa przewyższenia z tablic, metodą POT albo AMP, wraz z wysokościami 16 czasów trwania przy tym prawdopodobieństwie: krzywa wysokość–czas trwania dla `euler_ii_hyetograph`; nic nie jest liczone ani interpolowane (źr. 1)
>
> **Konwencja:** p to prawdopodobieństwo przewyższenia w procentach (w praktyce odczytuje się T = 100 / p lat; IMGW-PIB nie dokumentuje przeliczenia POT na prawdopodobieństwa roczne); wysokość zwracana jest tak, jak podaje ją IMGW-PIB (0,01 mm); tylko czasy trwania i prawdopodobieństwa z tablic; domyślnie POT, które IMGW-PIB zaleca dla p >= 50 % i poniżej uznaje za równoważne AMP (s. 23). Wiersz jest zadeklarowany tutaj: hydrolog._pmaxtp nie importuje żadnej biblioteki numerycznej
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa, p. 10 (16 durations of 5 min to 72 h, 27 probabilities of 0.01 to 99.9 %), p. 23 (POT and AMP) <https://klimat.imgw.pl/opady-maksymalne/>
>
> Funkcja `hydrolog._pmaxtp.fetch_depth`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:pmaxtp_depth -->

### Przykład 2.3. Opady projektowe w przekroju Kamiennika

Punkt przekroju zamykającego (51,01544° N, 15,88984° E), czas trwania 720 min, $p$ = 1 %, metoda POT:

```sh
hydrolog precip pmaxtp --latitude 51.01544 --longitude 15.88984 --duration-min 720 --probability-percent 1
```

Hydrolog daje 101,82 mm. Ta sama wartość jest w tablicy IMGW-PIB zapisanej w repozytorium Hydrologa w
listopadzie 2026 r. (`tests/fixtures/pmaxtp_kamiennik_pot.json`); błąd estymacji `rb` wynosi w niej
28,08 mm, a górna granica `sg` — 129,90 mm. Wartość projektowa jest więc obarczona niepewnością rzędu
jednej czwartej. IMGW-PIB może przeliczać atlas, więc pobrana dziś wartość może się nieznacznie różnić.

Pozostałe wartości tabeli to `depth_mm` i `depth_duration_mm` z tego samego polecenia z innymi
prawdopodobieństwami i metodą (`--probability-percent 50`, `--probability-percent 99`, `--method AMP`):

| $p$ | Metoda | 15 min | 60 min | 180 min | 720 min | 1440 min |
|---|---|---|---|---|---|---|
| 99 % | POT | 9,67 | 14,57 | 20,24 | 30,67 | 37,68 |
| 99 % | AMP | 4,33 | 6,52 | 9,79 | 16,30 | 20,29 |
| 50 % | POT | 12,65 | 18,55 | 26,04 | 39,92 | 49,53 |
| 50 % | AMP | 10,07 | 15,94 | 22,70 | 35,93 | 44,86 |
| 1 % | POT | 29,80 | 46,28 | 65,58 | 101,82 | 128,58 |
| 1 % | AMP | 28,50 | 43,99 | 63,04 | 99,10 | 124,27 |

**Jak czytać tabelę.** Przy $p$ = 1 % metody różnią się o kilka procent (720 min: 101,82 i 99,10 mm), przy
50 % — o 10–20 %, a przy 99 % wartości AMP są mniej więcej o połowę mniejsze. Wynika to z budowy ciągów: ciąg AMP ma
jedną wartość z każdego roku, także z lat bez dużych opadów, więc jego dolny ogon schodzi nisko; ciąg POT
zbiera wszystkie duże opady. Dla prawdopodobieństw bliskich 100 % (opady występujące prawie co roku) różnica
jest więc największa, co tłumaczy zalecenie IMGW-PIB. Stosunek $h(5)/h(60)$ dla $p$ = 1 % wynosi tu
21,02/46,28 = 0,45: pięciominutowy fragment deszczu godzinnego niesie prawie połowę jego sumy, co ma
znaczenie dla deszczu Eulera typu II.

Dane PMAXTP: „Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut
Badawczy, dane pochodzą ze strony https://klimat.imgw.pl/opady-maksymalne”; „Dane Instytutu Meteorologii i
Gospodarki Wodnej – Państwowego Instytutu Badawczego pochodzące ze strony
https://klimat.imgw.pl/opady-maksymalne zostały przetworzone”; „Modele probabilistyczne opadów maksymalnych o
określonym czasie trwania i prawdopodobieństwie przewyższenia – Projekt PMAXTP”, red. Bogdan Ozga-Zieliński,
Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy, Warszawa 2022. Regulamin danych
PMAXTP: https://klimat.imgw.pl/opady-maksymalne.

### Typowe błędy

- **PMAXTP nazwany opadem maksymalnym prawdopodobnym (PMP).** To różne pojęcia (wyżej).
- **Pomylone wiersze tablicy:** 0,5 % z 5 % albo 99 % z 1 % (99 % to opad przekraczany prawie co roku).
- **Suma z innego czasu trwania niż czas trwania hietogramu**, np. suma 60-minutowa rozłożona na 120 min.
- **Wartości AMP i POT w jednym obliczeniu**, np. krzywa $h(D)$ złożona z obu metod.
- **Wartość punktowa wzięta za średnią dużej zlewni** bez rozważenia redukcji obszarowej (p. 2.1).
- **Maksima dobowe ze stacji porównane wprost z wartościami dla 1440 min** (doba stała a okno ruchome, p. 2.1).

## 2.4 Hietogramy projektowe

### Zasady wspólne

Hietogram projektowy dzieli wysokość opadu (np. z PMAXTP) na kroki. W Hydrologu (polecenie
`precip hietogram`, a w obliczeniu hydrogramu opcje `hydrograph generate`) każdy hietogram składa się z
**całych kroków**: czas trwania musi być całkowitą wielokrotnością kroku, deszcz trwa cały czas trwania i
zawiera całą sumę
([ADR-0046](../decisions/0046-design-hyetographs-of-whole-steps-and-exact-blocks.md)). Czas trwania 45 min z
krokiem 10 min zostanie odrzucony:

```sh
hydrolog precip hietogram --hietogram-type block --total-mm 36.58 --duration-min 45 --timestep-min 10
```

kończy się błędem `validation_error` z powodem `not_multiple`. Do wersji 0.8.1 Hydrolog mieścił wtedy całą
sumę w czterech krokach (40 min), więc natężenie średnie było o 12,5 % większe niż deszczu 45-minutowego o
tym prawdopodobieństwie. Dla PMAXTP dobiera się krok, który dzieli czas trwania (5 min dzieli wszystkie
czasy trwania atlasu).

**Kształt ma znaczenie.** Opad efektywny metodą SCS-CN liczy się z sumy narastającej (rozdz. 3): początek
deszczu pokrywa straty początkowe, a ten sam blok opadu daje więcej odpływu, gdy spada później. Przy tej samej
sumie i tym samym czasie trwania kształt hietogramu zmienia wysokość i czas kulminacji (niżej: porównanie
kształtów na Kamienniku). W zlewni Sidzinki w Krakowie, dla czterech kształtów deszczu, dwóch sposobów
liczenia czasu koncentracji i dwóch wartości CN, „różnica między najmniejszą i największą wartością
przepływu w kulminacji wyniosła 54%” (Wachulec, Wałęga i Młyński 2016, s. 77).

### Hietogram blokowy

Stałe natężenie przez cały czas trwania. To najprostszy deszcz miarodajny, w Polsce „najczęściej przyjmowany
przez projektantów systemu odwodnienia” (Wachulec i in. 2016, s. 74). Blok zaniża krótkotrwałe szczyty
natężenia: maksimum pięciominutowe jest równe średniej, więc w małych, szybko reagujących zlewniach daje
zwykle niższe kulminacje niż deszcze ze szczytem.

<!-- spec:block_hyetograph -->

<a id="spec-block_hyetograph"></a>

> **Blokowy hietogram projektowy (o stałym natężeniu)** · specyfikacja [`block_hyetograph`](../FORMULAS.md#block_hyetograph) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> P_j = \frac{P}{n},\quad n = \frac{T_d}{\Delta t},\quad t_j = j\,\Delta t
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P$ | `total_mm` | Całkowita wysokość deszczu | mm | (0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 3) |
> | $T_d$ | `duration_min` | Czas trwania deszczu, całkowita liczba kroków | min | (0; ∞) | nie podano w źródłach | [5; 4320] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy: długość każdego bloku deszczu | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $P_j$ | `intensities_mm` (ciąg) | Wysokość opadu w każdym kroku (pole zachowuje nazwę z wcześniejszych wersji; natężenie podaje pole wyniku intensity_mm_per_h) | mm | [0; ∞) |
> | $t_j$ | `times_min` (ciąg) | Koniec każdego kroku liczony od początku deszczu | min | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | dt <= Td: deszcz obejmuje co najmniej jeden krok | `step_within_duration` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
> | Td / dt <= 1 000 000: najwyżej milion kroków | `steps_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | Td = n dt dla całkowitego n, z dokładnością do 1e-9 Td: deszcz składa się z całych kroków | `whole_steps` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
>
> **Konwencje**
>
> - wysokości w mm na krok; t_j to koniec kroku j, krok j obejmuje ((j - 1) dt, j dt]
> - deszcz składa się z całych kroków: Td = n dt (ADR-0046)
>
> **Zgodność z obserwacjami według źródeł:** brak: deszcz blokowy jest konwencją projektową, nie modelem deszczy obserwowanych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Wachulec, K., Licznar, P., Zaleski, J. and Wójcik, R. (2016). Przegląd Naukowy Inżynieria i Kształtowanie Środowiska 71, p. 74: the block rain of constant intensity, the design rain most often taken by designers of drainage systems
> 2. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 14.4, p. 466: a design hyetograph gives the depth of n successive intervals of duration dt over the total duration Td = n dt <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 3. Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 %
> 4. Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa, ISBN 978-83-64979-48-4, p. 10: the tables give 16 durations, 5 min to 72 h <https://klimat.imgw.pl/opady-maksymalne/>
> 5. The steps of the design storms of the sources: 5 min (DWD, Malitz 2009, slide 17; the shortest duration of the PMAXTP tables) to 1 h (KZGW 2017, example 6.1, p. 92), Malitz 2009 slide 17; KZGW 2017 p. 92
> 6. Hydrolog, ADR-0067: the precipitation formulas by specs, docs/decisions/0067-the-precipitation-formulas-by-specs.md, point 3
>
> Funkcja `hydrolog.precipitation.hietogram.block_hyetograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:block_hyetograph -->

**Przykład.** Deszcz projektowy Kamiennika (101,82 mm, 720 min) z krokiem 10 min:

```sh
hydrolog precip hietogram --hietogram-type block --total-mm 101.82 --duration-min 720 --timestep-min 10
```

daje 72 kroki po 1,4142 mm, czyli 8,485 mm/h.

### Hietogram trójkątny (Yen i Chow)

Natężenie rośnie liniowo od zera do maksimum, a potem liniowo maleje do zera (Yen i Chow 1980; Chow,
Maidment i Mays 1988, rozdz. 14.3). Położenie maksimum opisuje **współczynnik wyprzedzenia burzy** $r$ (ang.
*storm advancement coefficient*), czyli czas do maksimum jako ułamek czasu trwania: $r$ = 0,5 to maksimum w
środku, mniejsze $r$ — wcześniej. Analizy deszczy w miastach USA, Indii i Kanady dały wartości mniejsze od
0,5 (Chow i in. 1988, tab. 14.3.2). W Hydrologu (`--peak-position`) każdy krok dostaje dokładną całkę
trójkąta po swoim przedziale ([ADR-0046](../decisions/0046-design-hyetographs-of-whole-steps-and-exact-blocks.md));
do wersji 0.8.1 wagi kroków liczono z wartości trójkąta na ich końcach, przez co przy trzech krokach wynosiły
zawsze 1/2, 1 i 1/2, niezależnie od $r$.

<!-- spec:triangular_hyetograph -->

<a id="spec-triangular_hyetograph"></a>

> **Trójkątny hietogram projektowy Yena i Chowa: całki trójkąta w blokach** · specyfikacja [`triangular_hyetograph`](../FORMULAS.md#triangular_hyetograph) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> h = \frac{2P}{T_d},\quad t_a = r\,T_d,\quad F(u) = \begin{cases} u^2/r & u \le r \\ 1 - (1-u)^2/(1-r) & u > r \end{cases},\quad P_j = P\left[F\left(\tfrac{j}{n}\right) - F\left(\tfrac{j-1}{n}\right)\right]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P$ | `total_mm` | Całkowita wysokość deszczu | mm | (0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 3) |
> | $T_d$ | `duration_min` | Czas trwania deszczu, całkowita liczba kroków | min | (0; ∞) | nie podano w źródłach | [5; 4320] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy: długość każdego bloku deszczu | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 5) |
> | $r$ | `peak_position` | Współczynnik wyprzedzenia burzy: czas do szczytu jako ułamek czasu trwania | – | (0; 1) | nie podano w źródłach | [0,294; 0,5] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $P_j$ | `intensities_mm` (ciąg) | Wysokość opadu w każdym kroku (pole zachowuje nazwę z wcześniejszych wersji; natężenie podaje pole wyniku intensity_mm_per_h) | mm | [0; ∞) |
> | $t_j$ | `times_min` (ciąg) | Koniec każdego kroku liczony od początku deszczu | min | (0; ∞) |
> | $h$ | `peak_intensity_mm_per_h` | Natężenie w szczycie trójkąta | mm/h | [0; ∞) |
> | $t_a$ | `peak_time_min` | Chwila szczytu liczona od początku deszczu | min | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | dt <= Td: deszcz obejmuje co najmniej jeden krok | `step_within_duration` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | Td / dt <= 1 000 000: najwyżej milion kroków | `steps_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | Td = n dt dla całkowitego n, z dokładnością do 1e-9 Td: deszcz składa się z całych kroków | `whole_steps` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | 2 P / Td jest skończonym natężeniem w float64 (deszcz trwający ułamek sekundy, o wysokości 1e-300 mm lub większej, przekracza ten zakres) | `peak_intensity_finite` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Konwencje**
>
> - wysokości w mm na krok; t_j to koniec kroku j; h w mm/h według tabeli jednostek
> - każdy krok zawiera wysokość, jaką przypisuje mu ciągły trójkąt, czyli różnicę udziału skumulowanego na jego końcach (ADR-0046); trójkąta się nie próbkuje
> - deszcz składa się z całych kroków: Td = n dt (ADR-0046)
>
> **Zgodność z obserwacjami według źródeł:** Chow i in. (1988, s. 464) podają w tabeli r dopasowane do deszczy w miastach USA, Indii i Kanady; sam trójkąt jest kształtem projektowym, a źródła nie podają dla niego statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 14.3 Triangular hyetograph method, eqs. 14.3.1 to 14.3.3, Example 14.3.1, pp. 462-465 (after Yen and Chow 1980) <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 2. Yen, B.C. and Chow, V.T. (1980). Design hyetographs for small drainage structures. Journal of the Hydraulics Division, ASCE 106(HY6), 1055-1076 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 %
> 4. Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa, ISBN 978-83-64979-48-4, p. 10: the tables give 16 durations, 5 min to 72 h <https://klimat.imgw.pl/opady-maksymalne/>
> 5. The steps of the design storms of the sources: 5 min (DWD, Malitz 2009, slide 17; the shortest duration of the PMAXTP tables) to 1 h (KZGW 2017, example 6.1, p. 92), Malitz 2009 slide 17; KZGW 2017 p. 92
> 6. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, Table 14.3.2, p. 464: storm advancement coefficients r of 0.294 to 0.480 for cities of the USA, India and Canada; Hydrolog's default 0.5 puts the peak at the centre <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 7. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 14.4, p. 466: a design hyetograph gives the depth of n successive intervals of duration dt over the total duration Td = n dt <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 8. Hydrolog, ADR-0067: the precipitation formulas by specs, docs/decisions/0067-the-precipitation-formulas-by-specs.md, point 3
>
> Funkcja `hydrolog.precipitation.hietogram.triangular_hyetograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:triangular_hyetograph -->

**Przykład (Chow i in. 1988, przykład 14.3.1).** Urbana w stanie Illinois, deszcz 15-minutowy o okresie
powtarzalności 5 lat, 1,07 in = 27,178 mm, $r$ = 0,38, krok 5 min:

```sh
hydrolog precip hietogram --hietogram-type triangular --total-mm 27.178 --duration-min 15 --timestep-min 5 --peak-position 0.38
```

Kroki zawierają 7,95; 14,36 i 4,87 mm. Największe natężenie średnie w kroku wynosi 172,33 mm/h — mniej niż
maksimum chwilowe trójkąta, bo krok uśrednia natężenie wokół szczytu.

### Hietogram Beta

Udział kroku w sumie jest proporcjonalny do gęstości rozkładu beta: dwa parametry kształtu ($\alpha$,
$\beta$) dają maksimum wczesne, środkowe albo późne. Polska metodyka używa rozkładu beta do podziału
dobowej sumy opadu na przedziały obliczeniowe (KZGW 2017, rozdz. II.3, s. 25–27, za Węglarczykiem 1993) i
pokazuje typowe kształty, od maksimum na początku doby po maksimum pod jej koniec (rys. 2.7). Parametry
„można określić metodami optymalizacyjnymi”: tak, by kulminacja z modelu opad–odpływ dla opadu o danym
prawdopodobieństwie była równa przepływowi maksymalnemu rocznemu o tym samym prawdopodobieństwie.

Hydrolog daje każdemu krokowi dokładną całkę gęstości rozkładu beta po jego przedziale (różnicę dystrybuanty
na jego końcach). KZGW (2017) liczy gęstość na końcach przedziałów, co przesuwa deszcz o pół kroku; to
odstępstwo od polskiego źródła jest świadome
([ADR-0046](../decisions/0046-design-hyetographs-of-whole-steps-and-exact-blocks.md)): całki są dokładne dla
każdego kroku i zbiegają do gęstości, gdy krok maleje. Parametry (2; 5), domyślne w Hydrologu, dają
maksimum w jednej piątej czasu trwania. To tylko kształt: nazywanie go „deszczem konwekcyjnym” bez kalibracji
nie ma źródła.

<!-- spec:beta_hyetograph -->

<a id="spec-beta_hyetograph"></a>

> **Hietogram projektowy Beta: całki gęstości rozkładu beta w blokach** · specyfikacja [`beta_hyetograph`](../FORMULAS.md#beta_hyetograph) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> P_j = P\left[I_{j/n}(\alpha, \beta) - I_{(j-1)/n}(\alpha, \beta)\right],\quad I_u(\alpha, \beta) = \frac{1}{B(\alpha, \beta)}\int_0^u s^{\alpha - 1}(1 - s)^{\beta - 1}\,ds
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P$ | `total_mm` | Całkowita wysokość deszczu | mm | (0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 3) |
> | $T_d$ | `duration_min` | Czas trwania deszczu, całkowita liczba kroków | min | (0; ∞) | nie podano w źródłach | [5; 4320] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy: długość każdego bloku deszczu | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 5) |
> | $\alpha$ | `alpha` | Pierwszy parametr kształtu (r w KZGW): narastanie deszczu | – | (0; ∞) | nie podano w źródłach | [1; 10] (źr. 6) |
> | $\beta$ | `beta` | Drugi parametr kształtu (s w KZGW): zanikanie deszczu | – | (0; ∞) | nie podano w źródłach | [2; 10] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $P_j$ | `intensities_mm` (ciąg) | Wysokość opadu w każdym kroku (pole zachowuje nazwę z wcześniejszych wersji; natężenie podaje pole wyniku intensity_mm_per_h) | mm | [0; ∞) |
> | $t_j$ | `times_min` (ciąg) | Koniec każdego kroku liczony od początku deszczu | min | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | dt <= Td: deszcz obejmuje co najmniej jeden krok | `step_within_duration` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | Td / dt <= 1 000 000: najwyżej milion kroków | `steps_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | Td = n dt dla całkowitego n, z dokładnością do 1e-9 Td: deszcz składa się z całych kroków | `whole_steps` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
>
> **Konwencje**
>
> - wysokości w mm na krok; t_j to koniec kroku j
> - każdy krok zawiera całkę gęstości po swoim przedziale (ADR-0046); KZGW (2017, wzór 2.20) liczy gęstość na końcach kroków, co przesuwa deszcz o pół kroku, i tego Hydrolog nie naśladuje
> - deszcz składa się z całych kroków: Td = n dt (ADR-0046)
>
> **Założenia**
>
> - KZGW (2017) dzieli sumę dobową na kroki godzinowe hipotetycznego wezbrania; Hydrolog przyjmuje dowolny czas trwania i krok
>
> **Zgodność z obserwacjami według źródeł:** KZGW (2017, s. 26) dobiera alfa i beta tak, by kulminacja hydrogramu z tego deszczu była równa przepływowi o tym samym prawdopodobieństwie; źródła nie podają statystyki błędu kształtu względem deszczy obserwowanych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), ch. II.3, eqs. 2.20-2.22, p. 25 (after Węglarczyk 1993); Fig. 2.7, p. 26 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Węglarczyk, S. (1993), as cited by KZGW (2017) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 %
> 4. Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa, ISBN 978-83-64979-48-4, p. 10: the tables give 16 durations, 5 min to 72 h <https://klimat.imgw.pl/opady-maksymalne/>
> 5. The steps of the design storms of the sources: 5 min (DWD, Malitz 2009, slide 17; the shortest duration of the PMAXTP tables) to 1 h (KZGW 2017, example 6.1, p. 92), Malitz 2009 slide 17; KZGW 2017 p. 92
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), Fig. 2.7, p. 26: typical Beta shapes (1, 10), (2, 10), (6, 6) and (10, 2); Hydrolog's default (2, 5) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 14.4, p. 466: a design hyetograph gives the depth of n successive intervals of duration dt over the total duration Td = n dt <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 8. Hydrolog, ADR-0067: the precipitation formulas by specs, docs/decisions/0067-the-precipitation-formulas-by-specs.md, point 3
>
> Funkcja `hydrolog.precipitation.hietogram.beta_hyetograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:beta_hyetograph -->

**Przykład.** Deszcz projektowy Kamiennika:

```sh
hydrolog precip hietogram --hietogram-type beta --total-mm 101.82 --duration-min 720 --timestep-min 10 --alpha 2 --beta 5
```

Największy krok (140–150 min) zawiera 3,47 mm, czyli 20,85 mm/h; po 12 godzinach ostatnie kroki są
praktycznie zerowe.

### Deszcz Eulera typu II (ATV-DVWK-A 118)

**Idea.** Deszcz Eulera typu II (niem. *Modellregen nach Euler, Typ II*) to deszcz modelowy niemieckich
wytycznych kanalizacyjnych ATV-DVWK-A 118 (cytowanych za Thewesem 2005, s. 10, i Kaźmierczakiem i Kotowskim
2012, s. 31–32). Bloki nie mają ustalonych wag: są przyrostami krzywej wysokość–czas trwania $h(D)$ dla
jednego prawdopodobieństwa, ułożonymi tak, by dla każdego czasu trwania $d$ deszcz zawierał okno o długości
$d$ z wysokością $h(d)$. Dlatego uważa się go za miarodajny dla każdej sieci lub zlewni, której czas reakcji
mieści się w jego czasie trwania. Ta własność dotyczy jednak opadu, nie opadu efektywnego: po stratach
SCS-CN inny kształt może dać wyższą kulminację (porównanie kształtów na końcu punktu).

**Konstrukcja.** Z krzywej $h(D)$ jednego prawdopodobieństwa liczy się przyrosty $h$ w kolejnych krokach.
Pierwszy przyrost, czyli $h(\Delta t)$, dla typowej krzywej największy, trafia do przedziału, który zaczyna się
po upływie ustalonego ułamka czasu trwania, zaokrąglonego w dół do wielokrotności kroku (ramka). Następne
przyrosty wypełniają czas przed nim, wstecz do początku deszczu, a pozostałe stoją po nim. Hydrolog układa
przyrosty w kolejności ich czasów trwania i ich nie sortuje: gdy interpolacja między punktami tablicy
sprawia, że przyrost rośnie, okna kończące się szczytem nadal zawierają dokładnie $h(d)$
([ADR-0042](../decisions/0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md)). Między punktami
krzywej Hydrolog interpoluje liniowo względem $\ln D$; tak odtwarza wydruki programu itwh KOSTRA-DWD, a
polskiej normy rozstrzygającej ten wybór nie znaleziono. Sposób interpolacji między punktami PMAXTP (5, 10,
15, 30, 45, 60 … min) pozostaje pytaniem otwartym w dokumentacji Hydrologa.

<!-- spec:euler_ii_hyetograph -->

<a id="spec-euler_ii_hyetograph"></a>

> **Deszcz modelowy Eulera typu II według ATV-DVWK-A 118 z krzywej wysokość–czas trwania** · specyfikacja [`euler_ii_hyetograph`](../FORMULAS.md#euler_ii_hyetograph) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \Delta h_j = h(j\,\Delta t) - h((j-1)\,\Delta t),\quad k = \lfloor 0{,}3\,n \rfloor,\quad P_{k-i} = \Delta h_{i+1}\ (i = 0..k),\quad P_{i-1} = \Delta h_i\ (i = k+2..n)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $D_i$ | `durations_min` (ciąg) | Czasy trwania punktów krzywej wysokość–czas trwania, rosnące | min | (0; ∞) | nie podano w źródłach | [5; 4320] (źr. 4) |
> | $h_i$ | `depths_mm` (ciąg) | Wysokości krzywej dla tych czasów trwania, jednego prawdopodobieństwa | mm | [0; ∞) | nie podano w źródłach | [6,96; 341,27] (źr. 5) |
> | $T_d$ | `duration_min` | Czas trwania deszczu, całkowita liczba kroków | min | (0; ∞) | nie podano w źródłach | [5; 4320] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy: długość każdego bloku deszczu | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $P_j$ | `intensities_mm` (ciąg) | Wysokość opadu w każdym kroku (pole zachowuje nazwę z wcześniejszych wersji; natężenie podaje pole wyniku intensity_mm_per_h) | mm | [0; ∞) |
> | $t_j$ | `times_min` (ciąg) | Koniec każdego kroku liczony od początku deszczu | min | (0; ∞) |
> | $h(T_d)$ | `total_mm` | Całkowita wysokość deszczu, wysokość krzywej dla Td | mm | [0; ∞) |
> | $k\,\Delta t$ | `peak_start_min` | Początek przedziału szczytu liczony od początku deszczu | min | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | h_(i+1) >= h_i: wysokość dla dłuższego czasu trwania nigdy nie jest mniejsza | `depths_not_decreasing` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 2) |
> | jedna wysokość dla każdego czasu trwania krzywej | `curve_lengths` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | D_(i+1) > D_i: każdy czas trwania krzywej raz, w kolejności rosnącej | `durations_increasing` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | dt <= Td: deszcz obejmuje co najmniej jeden krok | `step_within_duration` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | Td / dt <= 1 000 000: najwyżej milion kroków | `steps_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | Td = n dt dla całkowitego n, z dokładnością do 1e-9 Td: deszcz składa się z całych kroków | `whole_steps` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | D_1 <= dt i D_m >= Td: krzywa sięga od kroku do czasu trwania deszczu, niczego się nie ekstrapoluje | `curve_covers` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}3$ | `peak_start_share` | Ułamek czasu trwania, od którego zaczyna się przedział największego natężenia | 3/10 | – | (źr. 1) |
>
> **Konwencje**
>
> - wysokości w mm na krok; t_j to koniec kroku j
> - przyrosty zachowują kolejność swoich czasów trwania i nie są sortowane, więc m kroków kończących się szczytem zawiera h(m dt) także tam, gdzie interpolacja sprawia, że przyrost rośnie (ADR-0042, jak program itwh); dla krzywej o malejących przyrostach jest to posortowany układ z A 118 i DWD
> - szczyt zaczyna się w 0,3 Td zaokrąglonym w dół do całego kroku (A 118 w cytowanej postaci: do wielokrotności 5 min); program itwh umieszcza szczyt deszczu 15-minutowego w drugim kroku, a Kaźmierczak i Kotowski (2012) kończą go w Td / 3, krok później dla Td równego 165 i 180 min
> - suma to h(Td) krzywej; krzywa dotyczy jednego prawdopodobieństwa
> - deszcz składa się z całych kroków: Td = n dt (ADR-0046)
>
> **Założenia**
>
> - A 118 wymaga czasu trwania co najmniej dwukrotnie dłuższego od najdłuższego czasu przepływu; polskie deszcze modelowe Wartalskiej i Kotowskiego (2020) obejmują od 30 do 180 min; źródła nie podają zakresu danych wejściowych wzoru, więc żadna dana nie wywołuje uwagi
>
> **Zgodność z obserwacjami według źródeł:** brak: deszcz projektowy do wymiarowania odwodnienia (A 118); Licznar i Szeląg (2014, streszczenie) stwierdzają, że jego kształt odbiega od deszczy obserwowanych powyżej 180 min
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. ATV-DVWK (2001). Arbeitsblatt ATV-DVWK-A 118, Kap. 5.2.2.1, as quoted by Thewes, K. (2005). Diplomarbeit, Fachhochschule Trier, p. 10: the interval of the highest intensity begins at 0.3 of the duration rounded down to a multiple of 5 min; the next lower intervals follow to the left back to t = 0, the others to the right <https://www.hochschule-trier.de/fileadmin/Hauptcampus/Fachbereich_BL/BI/Personen/Erzmann/Abschlussarbeiten/DA-Thewes.pdf>
> 2. Malitz, G. (2009). Stark- und Extremniederschlag im Kurzzeitbereich. Deutscher Wetterdienst, Hydrometeorologie; slides of the 2. Trierer Workshop zur Niederschlag-Abfluss-Modellierung, slide 17: the highest 5-min value at position 4, the three next higher to its left, the rest decreasing to its right, the sum of the three largest the depth of 15 min; slides 18 and 19: two storms of 60 min <https://www.uni-trier.de/fileadmin/fb6/prof/PHY/PDF-Dateien/AG_ModSim/N-A-Workshop_2009/Malitz.pdf>
> 3. Kaźmierczak, B. and Kotowski, A. (2012). Weryfikacja przepustowości kanalizacji deszczowej w modelowaniu hydrodynamicznym. Oficyna Wydawnicza Politechniki Wrocławskiej, Wrocław, pp. 31-32 (the construction); Tab. 4.6, pp. 65-66 (eight storms of 75 to 180 min) <https://www.dbc.wroc.pl/Content/19608/PDF/kazmierczak_weryfikacja.pdf>
> 4. Ozga-Zieliński, B. (ed.) (2022). Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia - projekt PMAXTP. IMGW-PIB, Warszawa, ISBN 978-83-64979-48-4, p. 10: the tables give 16 durations, 5 min to 72 h <https://klimat.imgw.pl/opady-maksymalne/>
> 5. Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 %
> 6. The steps of the design storms of the sources: 5 min (DWD, Malitz 2009, slide 17; the shortest duration of the PMAXTP tables) to 1 h (KZGW 2017, example 6.1, p. 92), Malitz 2009 slide 17; KZGW 2017 p. 92
> 7. Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, New York, sec. 14.4, p. 466: a design hyetograph gives the depth of n successive intervals of duration dt over the total duration Td = n dt <https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf>
> 8. Hydrolog, ADR-0067: the precipitation formulas by specs, docs/decisions/0067-the-precipitation-formulas-by-specs.md, point 3
>
> Funkcja `hydrolog.precipitation.hietogram.euler_ii_hyetograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:euler_ii_hyetograph -->

<!-- spec:depth_duration_interpolation -->

<a id="spec-depth_duration_interpolation"></a>

> **Interpolacja krzywej wysokość–czas trwania** · wzór grupy B `depth_duration_interpolation` (Tier B, CMP-2.2)
>
> **Definicja:** wysokość krzywej wysokość–czas trwania dla czasu trwania między dwoma jej punktami D_i <= D <= D_(i+1): h = h_i + (h_(i+1) - h_i) ln(D / D_i) / ln(D_(i+1) / D_i); czas trwania odległy od punktu o mniej niż 1e-9 przyjmuje jego wysokość; poza krzywą wartości nie ma (źr. 1)
>
> **Konwencja:** liniowo względem ln D (ADR-0042): tak odtwarza się wydruki itwh KOSTRA-DWD 2010R dla Göllheim z dokładnością 0,07 mm z wysokości drukowanych z dokładnością 0,1 mm, a interpolacja liniowa względem D chybia o 0,16 mm; narzędzie DWA MDMS interpoluje liniowo względem D, a HEC-HMS w skali log-log; niczego się nie ekstrapoluje
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. itwh KOSTRA-DWD 2010R 3.2.3, model rains of Göllheim (T = 5 a), Anhang III of a planning procedure of Rhineland-Palatinate, pp. 2-5 (storms of 15 to 90 min) against p. 6 (depths hN) <https://upload.open.rlp.de/dataset/2420cfcf-294f-400f-8b82-93f2537feef6/resource/f7ac269a-d9c3-40ce-b926-ee7cafa9a4ab/download/merged-anhang-iii.pdf>
>
> Funkcja `hydrolog.precipitation.hietogram.EulerIIHietogram.depth_mm`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:depth_duration_interpolation -->

**Zastosowanie.** „Najczęściej używane w modelowaniu hydrodynamicznym sieci kanalizacyjnych w Polsce opady
modelowe” to rozkłady Eulera typu II i DVWK (Licznar 2021). Krzywą $h(D)$ bierze się z PMAXTP, z atlasu
PANDa albo z lokalnych wzorów. Wartalska i Kotowski (2020, s. 28) zauważają, że deszcz Eulera typu II „ma
zastosowanie dla małych zlewni miejskich, gdzie czasy trwania opadów miarodajnych, ograniczone czasem
przepływu w kanałach, nie przekraczają zwykle 2 godzin”, a porównanie z opadami z warszawskich
deszczomierzy (Licznar i Szeląg 2014, za tamże) wykazało rozbieżności zwłaszcza dla czasów trwania ponad
180 min. Dla zlewni rzecznej i deszczu kilkunastogodzinnego jest to więc użycie poza praktyką, z której
deszcz pochodzi.

**Do wersji 0.8.1** typ `euler_ii` Hydrologa nie był deszczem Eulera typu II: rozkładał samą sumę stałymi
wagami, niezależnie od miejsca, prawdopodobieństwa i czasu trwania, a jego blok szczytowy był 1,3–2,9 raza
niższy niż w opublikowanych deszczach Eulera II
([ADR-0042](../decisions/0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md)). Wyniki obliczone nim
wcześniej trzeba policzyć ponownie, z krzywą $h(D)$ ich prawdopodobieństwa.

**Przykład 2.4. Wrocław (Kaźmierczak i Kotowski 2012, tab. 4.6, s. 65).** Monografia podaje krzywą $h(d)$ z
modelu probabilistycznego dla Wrocławia przy częstości $C$ = 3 lata co 5 min i buduje z niej deszcze Eulera
typu II o czasie trwania 75–180 min, z blokiem szczytowym 101,71 mm/h. Deszcz 60-minutowy z tej samej krzywej:

```sh
hydrolog precip hietogram --hietogram-type euler_ii --duration-min 60 --timestep-min 5 --depth-duration-mm '{"5":8.48,"10":12.16,"15":14.49,"20":16.23,"25":17.64,"30":18.82,"35":19.85,"40":20.76,"45":21.58,"50":22.33,"55":23.02,"60":23.66}'
```

Bloki [mm]: 1,74; 2,33; 3,68; **8,48**; 1,41; 1,18; 1,03; 0,91; 0,82; 0,75; 0,69; 0,64. Blok szczytowy
(15–20 min) to $h(5)$ = 8,48 mm, czyli 101,76 mm/h; monografia liczy natężenie z niezaokrągloną wysokością i
podaje 101,71 mm/h. Przyrosty krzywej (kolumna Δh tabeli 4.6) są te same.

**Przykład 2.5. Kamiennik, 60 min, $p$ = 1 %.** Krzywa z PMAXTP (przykład 2.3) do 60 min:

```sh
hydrolog precip hietogram --hietogram-type euler_ii --duration-min 60 --timestep-min 5 --depth-duration-mm '{"5":21.02,"10":26.19,"15":29.8,"30":37.13,"45":42.24,"60":46.28}'
```

| Krok [min] | 0–5 | 5–10 | 10–15 | **15–20** | 20–25 | 25–30 | 30–35 | 35–40 | 40–45 | 45–50 | 50–55 | 55–60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $P_j$ [mm] | 3,04 | 3,61 | 5,17 | **21,02** | 2,36 | 1,93 | 1,94 | 1,68 | 1,48 | 1,48 | 1,34 | 1,22 |

Suma to $h(60)$ = 46,28 mm, blok szczytowy to $h(5)$ = 21,02 mm (252,24 mm/h), a trzy bloki kończące się
szczytem zawierają $h(15)$ = 29,80 mm. Blok 30–35 min jest nieco większy od bloku 25–30 min: na granicy
punktów tablicy (30 min) zmienia się nachylenie interpolowanej krzywej, a Hydrolog nie sortuje przyrostów.
Krzywą można też podać plikiem: `--depth-duration-file` przyjmuje wynik `precip pmaxtp --json` razem z jego
wierszami przypisania.

### Inne rozkłady

Metodyka KZGW (2017, s. 106) przyjmuje za DVWK (1984) deszcz z maksymalnym natężeniem w środku: w pierwszych
30 % czasu trwania spada 20 % sumy, do połowy czasu trwania — 70 %, a w drugiej połowie pozostałe 30 %.
Hydrolog nie ma tego rozkładu. Maksimum w środku dają hietogram trójkątny z $r$ = 0,5 i rozkład beta z
równymi parametrami, ale ich krzywe sumowe są inne (symetryczny trójkąt ma do połowy czasu trwania połowę
sumy). Hydrolog nie ma też metody bloków naprzemiennych (Chow i in. 1988, rozdz. 14.4), w której kolejne
bloki stoją na przemian po obu stronach szczytu — w deszczu Eulera typu II wszystkie większe przyrosty stoją
przed szczytem.

### Porównanie kształtów na Kamienniku

Ten sam deszcz (101,82 mm, 720 min, krok 10 min), czas koncentracji metodą Kerby'ego–Kirpicha (208,63 min,
rozdz. 4), straty SCS-CN dla CN 65 (rozdz. 3) i hydrogram jednostkowy SCS (rozdz. 5):

```sh
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type beta --total-mm 101.82 --duration-min 720 --alpha 2 --beta 5 --timestep-min 10
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type block --total-mm 101.82 --duration-min 720 --timestep-min 10
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type triangular --total-mm 101.82 --duration-min 720 --peak-position 0.5 --timestep-min 10
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type euler_ii --duration-min 720 --depth-duration-mm '{"5":21.02,"10":26.19,"15":29.8,"30":37.13,"45":42.24,"60":46.28,"90":52.64,"120":57.68,"180":65.58,"360":81.5,"720":101.82}' --timestep-min 10
```

| Hietogram | $Q_{max}$ [m³/s] | Czas do kulminacji [h:min] |
|---|---|---|
| Beta (2; 5) | 52,36 | 6:50 |
| trójkątny, $r$ = 0,5 | 48,34 | 10:10 |
| Euler typu II | 45,62 | 5:50 |
| blokowy | 42,21 | 12:40 |

Opad efektywny (26,25 mm) i objętość odpływu bezpośredniego (ok. 977 tys. m³) są te same: przy stratach
SCS-CN zależą od sumy, nie od kształtu. Kulminacja zmienia się o ok. 24 % (od 42,21 do 52,36 m³/s), a czas
do niej — o prawie siedem godzin. Deszcz blokowy rozkłada opad równo na 12 godzin i daje najniższą,
najpóźniejszą falę. Deszcz Eulera typu II ma najwyższe natężenie, ale w jednym kroku (koło czwartej
godziny), po którym zostają już tylko małe bloki; zlewnia o czasie koncentracji ok. 3,5 h rozkłada tak
krótki impuls na kilka godzin. Beta (2; 5) daje przez kilka godzin natężenia bliskie maksimum i przy
stratach SCS-CN to ona tworzy tu najwyższą falę.

## 2.5 Krytyczny czas trwania deszczu na Kamienniku

Krytyczny czas trwania to ten, który daje największą kulminację (rozdz. 4, p. 4.1). Metodyka KZGW (2017,
s. 105) podaje za DVWK (1984) przedział od $t_c$ do $2\,t_c$, co dla Kamiennika (Kerby–Kirpich, 208,63 min)
oznacza ok. 3,5–7 h. Ten przedział zakłada jednak stały współczynnik odpływu. Przy stratach SCS-CN trzeba go
sprawdzić obliczeniem: hydrogram dla kolejnych czasów trwania PMAXTP przy $p$ = 1 % (POT, przykład 2.3),
z tym samym kształtem Beta (2; 5) i krokiem 10 min, np.

```sh
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type beta --total-mm 81.5 --duration-min 360 --alpha 2 --beta 5 --timestep-min 10
```

(z `--total-mm` i `--duration-min` z kolejnych wierszy tabeli):

| $D$ [min] | $P$ [mm] | Opad efektywny [mm] | $Q_{max}$ [m³/s] | Czas do kulminacji [h:min] |
|---|---|---|---|---|
| 60 | 46,28 | 2,30 | 8,16 | 2:40 |
| 90 | 52,64 | 3,95 | 13,92 | 2:50 |
| 120 | 57,68 | 5,50 | 19,22 | 3:00 |
| 180 | 65,58 | 8,35 | 28,23 | 3:30 |
| 360 | 81,50 | 15,36 | 44,37 | 4:40 |
| 720 | 101,82 | 26,25 | 52,36 | 6:50 |
| 1080 | 116,56 | 35,22 | 51,97 | 8:50 |
| 1440 | 128,58 | 43,05 | 49,86 | 10:40 |

Największą kulminację daje deszcz 720-minutowy, a 1080-minutowy niewiele mniejszą. Przyczyną są straty
początkowe metody SCS-CN (rozdz. 3): przy CN 65 pierwsze 27,35 mm deszczu nie daje odpływu, więc deszcz
godzinny o wysokości 46,28 mm daje tylko 2,30 mm opadu efektywnego. Dłuższy deszcz ma większą sumę i
większą jej część ponad stratami. Dopóki opad efektywny rośnie szybciej, niż rozciąga się w czasie,
kulminacja rośnie; powyżej ok. 12 h przeważa rozciągnięcie deszczu i kulminacja maleje. Przedział DVWK jest
więc punktem wyjścia, nie wynikiem: krytyczny czas trwania trzeba sprawdzić w tym samym modelu, w którym
liczy się wezbranie.

**Deszcz projektowy dalszych rozdziałów** to zatem: PMAXTP, metoda POT, punkt przekroju Kamiennika,
$p$ = 1 %, czas trwania 720 min, 101,82 mm, hietogram Beta (2; 5) z krokiem 10 min, bez redukcji obszarowej.
To ten sam deszcz, którego używa przykład z instrukcji Hydrologa.

Dane PMAXTP: jak w przykładzie 2.3.

## Źródła

Źródła otwarte (dostępne w sieci w chwili pisania):

- Barszcz M.P., Kaznowska E., Wasilewicz M. (2024). Analiza wysokości opadów maksymalnych z modelu PMAXTP i
  ich zastosowanie do weryfikacji działania miejskiego systemu odwodnienia. *Przegląd Geograficzny* 96(4),
  473–494. https://doi.org/10.7163/PrzG.2024.4.4
- Chow V.T., Maidment D.R., Mays L.W. (1988). *Applied Hydrology*. McGraw-Hill, New York; s. 78–80 (opad
  obszarowy, rys. 3.4.3), rozdz. 14.3–14.4 (hietogramy). Kopia udostępniona przez V.M. Ponce (SDSU):
  https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf
- Kaźmierczak B., Kotowski A. (2012). *Weryfikacja przepustowości kanalizacji deszczowej w modelowaniu
  hydrodynamicznym*. Oficyna Wydawnicza Politechniki Wrocławskiej, Wrocław.
  https://www.dbc.wroc.pl/Content/19608/PDF/kazmierczak_weryfikacja.pdf
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych oraz identyfikacji
  modeli transformacji opadu w odpływ* (Banasik K., Wałęga A., Węglarczyk S., Więzik B.), zał. 2 do OPZ,
  Krajowy Zarząd Gospodarki Wodnej; s. 15–17, 25–27, 103–106.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Licznar P. (2021). Cyfrowe projektowanie systemów odwodnień. *Inżynier Budownictwa*.
  https://inzynierbudownictwa.pl/cyfrowe-projektowanie-systemow-odwodnien/
- Ozga-Zieliński B. (red.) (2022). *Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i
  prawdopodobieństwie przewyższenia – Projekt PMAXTP*. Seria Publikacji Naukowo-Badawczych IMGW-PIB, Instytut
  Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy, Warszawa, ISBN 978-83-64979-48-4, licencja
  CC BY 4.0; s. 8–10, 13, 23, 32, 43. Monografia (PDF), aplikacja, słowniczek i regulamin danych:
  https://klimat.imgw.pl/opady-maksymalne/
- Thewes K. (2005). Praca dyplomowa, Hochschule Trier (cytat ATV-DVWK-A 118, s. 10–11).
  https://www.hochschule-trier.de/fileadmin/Hauptcampus/Fachbereich_BL/BI/Personen/Erzmann/Abschlussarbeiten/DA-Thewes.pdf
- Wachulec K., Wałęga A., Młyński D. (2016). Wpływ czasu koncentracji i charakterystyk opadu na kształtowanie
  się hydrogramu odpływu w małej zlewni niekontrolowanej. *Przegląd Naukowy – Inżynieria i Kształtowanie
  Środowiska* 25, 1(71), 72–82. http://iks.pn.sggw.pl/PN71/A8/art8.pdf
- Wartalska K.E., Kotowski A. (2020). *Metodyka tworzenia wzorców opadów do modelowania odwodnień terenów*.
  Oficyna Wydawnicza Politechniki Wrocławskiej, Wrocław.
  https://dbc.wroc.pl/Content/75958/metodyka_tworzenia_wzorcow.pdf
- WMO (2009). *Manual on Estimation of Probable Maximum Precipitation (PMP)*. WMO-No. 1045, Geneva.
  https://library.wmo.int/viewer/35708

Dane: IMGW-PIB, dobowe sumy opadu posterunków opadowych i stacji synoptycznej Jelenia Góra (publiczne dane
IMGW-PIB, przez magazyn Obserwatora; [dane/README.md](dane/README.md)); IMGW-PIB, Rocznik Meteorologiczny
2025, rozdz. 1.1 (doba opadowa; plik PDF w katalogu „Roczniki” serwisu https://danepubliczne.imgw.pl);
PMAXTP (wyżej).

Dokumenty Hydrologa: [ADR-0018](../decisions/0018-pmaxtp-through-obserwator.md) (PMAXTP przez Obserwatora),
[ADR-0042](../decisions/0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md) (deszcz Eulera typu II),
[ADR-0046](../decisions/0046-design-hyetographs-of-whole-steps-and-exact-blocks.md) (całe kroki, dokładne
bloki trójkąta i rozkładu beta, izohiety), [COMPUTATION_PATHS](../COMPUTATION_PATHS.md), p. 3.15–3.16.

Źródła niedostępne w otwartym dostępie, cytowane za źródłami powyżej: ATV-DVWK-A 118 (DWA-A 118) (za Thewes
2005 i Kaźmierczak i Kotowski 2012); DVWK (1984) (za KZGW 2017); Bogdanowicz E., Stachý J. (1998) *Maksymalne
opady deszczu w Polsce. Charakterystyki projektowe* (za KZGW 2017); Węglarczyk S. (1993) (za KZGW 2017); Yen
B.C., Chow V.T. (1980) (za Chow i in. 1988); Wei T.C., McGuinness J.L. (1973) (za Chow i in. 1988); Licznar
P., Szeląg B. (2014) (za Wartalska i Kotowski 2020).
