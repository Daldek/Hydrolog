# 1. Zlewnia i jej charakterystyki

Każde obliczenie wezbrania w zlewni niekontrolowanej zaczyna się od liczb opisujących samą
zlewnię: jej powierzchni, długości, wysokości, spadków i sieci rzecznej. Wchodzą one do wzorów
na czas koncentracji (rozdział 4), do parametrów hydrogramów jednostkowych Snydera i Nasha
(rozdział 5) i do porównań między zlewniami. Ten rozdział wyjaśnia, co te charakterystyki
znaczą, jak je mierzyć i jak liczy je Hydrolog, a na końcu każdej części pokazuje je na
przykładzie przewodnim podręcznika: zlewni Kamiennika po przekrój w Świerzawie.

Kształt i rzeźba zlewni wpływają na przebieg wezbrania. W zlewni wydłużonej woda z różnych
części dopływa do przekroju zamykającego w różnym czasie, fala jest więc zwykle płaska, wezbranie
trwa dłużej, a kulminacja jest niższa niż w zlewni zwartej o tej samej powierzchni (Baścik 2006,
s. 21). Zlewnia stroma odprowadza wodę szybciej niż płaska, a gęsta sieć cieków skraca drogę,
którą woda przebywa po stoku. Liczby z tego rozdziału są jednak tylko opisem: żaden ze wskaźników
kształtu nie jest daną wejściową metody SCS-CN ani hydrogramu jednostkowego; kształt działa w tych
modelach przez długości, spadki i czas koncentracji.

> **Przykład przewodni.** Kamiennik w dorzeczu Kaczawy, po przekrój w Świerzawie
> (51,01544° N, 15,88984° E): 37,22 km². Powierzchnię, długości, wysokości i spadki zlewni
> wyznaczył Hydrograf z numerycznego modelu terenu (NMT) Głównego Urzędu Geodezji i Kartografii
> o oczkach 5 m; zapisano je w pliku `tests/fixtures/kamiennik.json` repozytorium Hydrologu, a
> profil podłużny najdłuższej drogi spływu w `tests/fixtures/kamiennik_flow_path_profile.json`.
> Dane NMT i sieci cieków użyte w przykładach tego rozdziału są w katalogu [`dane/`](dane/)
> podręcznika.
> Źródło: Główny Urząd Geodezji i Kartografii – GUGiK, NMT, BDOT10k; dane przetworzone.

## 1.1. Zlewnia, dział wodny, przekrój zamykający

**Zlewnia** (ang. *catchment*, *watershed*, *drainage basin*) to obszar, z którego woda spływa
do jednego punktu cieku, **przekroju zamykającego** (ang. *outlet*). Granicą zlewni jest **dział
wodny** (ang. *divide*): linia, po której obu stronach woda płynie do różnych cieków. W hydrologii
stosowanej mówi się o zlewni *po przekrój*: zlewnia Kamiennika po Świerzawę to część całej
zlewni Kamiennika, z której woda dopływa do przekroju w Świerzawie.

Dział wodny wyznacza się dziś zwykle z NMT: każdej komórce rastra przypisuje się kierunek
odpływu do jednej z ośmiu sąsiednich komórek (metoda D8), a zlewnia przekroju to wszystkie komórki,
których droga spływu prowadzi do komórki przekroju. Przed wyznaczeniem kierunków NMT przygotowuje
się hydrologicznie: wypełnia się zagłębienia bez odpływu, a koryta znanych cieków (np. z bazy
BDOT10k) wpala się w teren, aby spływ z NMT biegł korytami, także pod mostami i przez przepusty w
nasypach. Zlewnia **topograficzna** wyznaczona w ten sposób może się różnić od **podziemnej**, z
której dopływa woda gruntowa; w obliczeniach wezbrań opadowych przyjmuje się topograficzną.

Hydrolog nie wyznacza zlewni. Przyjmuje jej parametry jako obiekt `WatershedParameters`: z pliku
JSON (na przykład z przekazania Hydrografu), z formularza w GUI albo wpisane ręcznie z map.
Wszystkie wzory tego rozdziału działają więc na liczbach, które ktoś wcześniej zmierzył; wynik
zależy od tego, jak je zmierzono, i dlatego każda część rozdziału mówi, na co przy pomiarze
uważać.

## 1.2. Parametry zlewni w Hydrologu

Tabela zestawia pola `WatershedParameters`, z których korzysta ten rozdział, z wartościami dla
Kamiennika z pliku przykładu.

| Pole | Znaczenie | Jednostka | Kamiennik |
|---|---|---|---|
| `area_km2` | powierzchnia zlewni (rzut poziomy) $A$ | km² | 37,22 |
| `perimeter_km` | obwód zlewni, długość działu wodnego $P$ | km | 40,89 |
| `length_km` | długość zlewni $L$ (Hydrograf podaje najdłuższą drogę spływu) | km | 16,05 |
| `elevation_min_m` | wysokość najniższa, przekroju zamykającego $H_{min}$ | m n.p.m. | 257,3 |
| `elevation_max_m` | wysokość najwyższa $H_{max}$ | m n.p.m. | 475,1 |
| `elevation_mean_m` | wysokość średnia zlewni | m n.p.m. | 363,2 |
| `mean_slope_m_per_m` | średnie nachylenie stoków z NMT | m/m | 0,082 |
| `channel_length_km` | długość cieku głównego | km | 14,78 |
| `flow_path_length_km` | długość najdłuższej drogi spływu | km | 15,88 |
| `flow_path_slope_m_per_m` | spadek najdłuższej drogi spływu między jej końcami | m/m | 0,0114 |
| `flow_path_equal_area_slope_m_per_m` | spadek wyrównany profilu tej drogi (podrozdział 1.6) | m/m | 0,00848 |

Pozostałe pola pliku (`cn`, `Lc_km`, `manning_n`, `forest_pct`, `urban_pct` i parametry spływu po
stoku) należą do rozdziałów 3, 4 i 5.

## 1.3. Powierzchnia, obwód, długość i szerokość

**Powierzchnia** $A$ to powierzchnia rzutu poziomego zlewni, z mapy albo z liczby komórek NMT
pomnożonej przez powierzchnię komórki. W terenie górskim powierzchnia rzeczywista stoków jest
większa od rzutu (Baścik 2006, wzór 1.2.4), ale wszystkie wzory hydrologiczne tego podręcznika
używają rzutu.

**Obwód** $P$ (ang. *perimeter*) to długość działu wodnego. Ma on cechę, o której łatwo zapomnieć: dział wodny jest
nieregularny w każdej skali, więc jego zmierzona długość rośnie wraz ze szczegółowością mapy lub
NMT (Bendjoudi i Hubert 2002, s. 924–928). Ta sama zlewnia ma inny obwód na mapie 1:50 000, inny
na granicy złożonej ze schodków komórek NMT i jeszcze inny na granicy wygładzonej. Wskaźniki
zależne od obwodu wolno więc porównywać tylko między zlewniami wyznaczonymi tą samą metodą.

**Długość zlewni** $L$ (ang. *basin length*) ma w literaturze co najmniej trzy definicje:

| Długość | Definicja | Źródło |
|---|---|---|
| w linii prostej | największa odległość w linii prostej od przekroju zamykającego do najdalszego punktu działu wodnego | Baścik 2006, s. 21 |
| długość doliny $L_m$ | długość doliny rzeki głównej od ujścia do działu wodnego w przedłużeniu odcinka źródłowego | Baścik 2006, s. 21 |
| najdłuższa droga spływu | długość drogi spływu po kierunkach D8 od punktu najdalszego hydraulicznie do przekroju | Hydrograf (`length_km`) |

W literaturze anglojęzycznej Schumm (1956, cytowany za źródłami wtórnymi) mierzył długość
jako największy wymiar zlewni równoległy do głównej linii odpływu. Hydrolog opisuje `length_km`
jako odcinek prosty, a Hydrograf przekazuje w tym polu najdłuższą drogę spływu, która nie bywa
krótsza. Dla Kamiennika różnica jest duża: najdłuższa droga spływu ma 16,05 km, a odcinek prosty
od przekroju do najdalszego punktu działu wodnego 10,88 km (zmierzony na granicy zlewni z
Hydrografu). Którą długość przyjąć we wskaźnikach kształtu, pozostaje otwartym pytaniem ADR-0065
Hydrologu; zawsze trzeba podać, którą się przyjęło.

**Średnia szerokość** zlewni (ang. *mean width*) to szerokość prostokąta o powierzchni i długości zlewni. Hydrolog
podaje ją jako `width_km`; Baścik (2006, s. 21) dzieli przez długość doliny $L_m$.

<!-- spec:mean_width -->

<a id="spec-mean_width"></a>

> **Średnia szerokość zlewni** · wzór grupy B `mean_width` (Tier B, CMP-2.2)
>
> **Definicja:** W = A / L, średnia szerokość zlewni [km] (źr. 1)
>
> **Konwencja:** L jako `length_km` z `WatershedGeometry` (odcinek prosty albo najdłuższa droga spływu); B według Baścika dzieli powierzchnię przez długość doliny Lm
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: średnia szerokość zlewni B = A / Lm <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.morphometry.geometric.WatershedGeometry.width_km`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:mean_width -->

**Typowe błędy.** Mieszanie w jednym zestawieniu długości mierzonych różnymi metodami; liczenie
obwodu z poszarpanej granicy rastra i porównywanie go z obwodem z mapy; powierzchnia z komórek
NMT i obwód z granicy wygładzonej, czyli z dwóch różnych obrysów (Hydrolog odrzuca obwód krótszy
od obwodu koła o tej samej powierzchni, bo taki obrys nie istnieje).

## 1.4. Wskaźniki kształtu

Wskaźniki kształtu porównują zlewnię z figurą wzorcową: kwadratem, kołem albo pętlą lemniskaty.
Są bezwymiarowe i silnie ze sobą powiązane: wskaźnik formy, wskaźnik wydłużenia i wskaźnik
lemniskaty są funkcjami jednego stosunku, powierzchni do kwadratu długości, a wskaźnik kolistości
to odwrotność kwadratu wskaźnika zwartości. Pięć liczb niesie więc w istocie dwie informacje: jak
zlewnia jest wydłużona (zależy od $L$) i jak rozwinięty jest jej dział wodny (zależy od $P$).

### Wskaźnik formy Hortona

Wskaźnik formy (ang. *form factor*) to stosunek powierzchni zlewni do kwadratu jej długości,
czyli średniej szerokości do długości (Horton 1932, cytowany za Bendjoudi i Hubert 2002; Wartalska,
PWr). Im mniejszy, tym zlewnia bardziej wydłużona.

<!-- spec:form_factor -->

<a id="spec-form_factor"></a>

> **Wskaźnik formy zlewni według Hortona** · specyfikacja [`form_factor`](../FORMULAS.md#form_factor) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> C_f = \frac{A}{L^2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 3) |
> | $L$ | `length_km` | Długość zlewni: odcinek prosty od ujścia do najdalszego punktu działu wodnego albo najdłuższa droga spływu przekazana przez Hydrograf | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $C_f$ | `form_factor` | Wskaźnik formy: powierzchnia podzielona przez kwadrat długości; pi/4 dla koła o średnicy L | – | [0; 3,141592653589793] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | A <= pi L^2: zlewnia leży w kole o promieniu L wokół swojego ujścia, gdzie L to odcinek prosty do najdalszego punktu działu wodnego albo najdłuższa droga spływu, która nie jest krótsza | `within_reach` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
>
> **Konwencje**
>
> - L to odcinek prosty od ujścia do najdalszego punktu działu wodnego (Baścik 2006, s. 21), tak jak `WatershedGeometry` opisuje `length_km`; Hydrograf przekazuje najdłuższą drogę spływu, która nie jest krótsza, więc przy niej wskaźnik wydłużenia jest mniejszy (k większy) niż przy odcinku prostym; L Schumma (1956), czyli największy wymiar równoległy do głównej linii odpływu, oraz Lm Baścika, czyli długość doliny, to inne konwencje
> - to, że A mieści się w kole o promieniu L wokół ujścia, ogranicza Cf z góry przez pi; przy L równym największemu wymiarowi zlewni (nierówność izodiametryczna) — przez pi/4, wartość dla koła
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik geometryczny, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, p. 929: Horton's (1932) form factor, the area of the basin over the square of its length <https://doi.org/10.1080/02626660209493000>
> 2. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik formy Cf = A / L^2 = B / L <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km
> 5. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.morphometry.geometric.form_factor`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:form_factor -->

### Wskaźnik zwartości Graveliusa

Wskaźnik zwartości (ang. *compactness coefficient*), nazywany też wskaźnikiem rozwinięcia działu
wodnego, to stosunek obwodu zlewni do obwodu koła o tej samej powierzchni (Gravelius 1914,
cytowany za Bendjoudi i Hubert 2002, wzór 1). Koło ma najkrótszy obwód spośród figur o danej
powierzchni, więc wskaźnik nie spada poniżej wartości dla koła; im większy, tym dział wodny
bardziej rozwinięty. Bendjoudi i Hubert (2002) pokazali, że wskaźnik rośnie wraz ze
szczegółowością pomiaru obwodu, więc zależy nie tylko od kształtu zlewni, lecz także od
nieregularności jej granicy.

<!-- spec:compactness_coefficient -->

<a id="spec-compactness_coefficient"></a>

> **Wskaźnik zwartości zlewni według Graveliusa** · specyfikacja [`compactness_coefficient`](../FORMULAS.md#compactness_coefficient) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> C_z = \frac{P}{2\sqrt{\pi A}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 3) |
> | $P$ | `perimeter_km` | Obwód zlewni, czyli długość jej działu wodnego | km | (0; ∞) | nie podano w źródłach | [0,17; 90] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $C_z$ | `compactness_coefficient` | Wskaźnik zwartości: obwód zlewni podzielony przez obwód koła o tej samej powierzchni; 1 dla koła | – | [1; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | P^2 >= 4 pi A: żaden obwód nie jest krótszy od obwodu koła o tej samej powierzchni (nierówność izoperymetryczna); krótszy oznacza, że A i P zmierzono na różnych obrysach | `isoperimetric` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
> | P / (2 sqrt(pi A)) mieści się w zakresie float64: żadna zlewnia nie ma działu wodnego 10^150 razy dłuższego od swojej szerokości | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
>
> **Konwencje**
>
> - P to długość działu wodnego w wykreślonym przebiegu: rośnie wraz z rozdzielczością mapy lub NMT, ponieważ dział wodny jest nieregularny w każdej skali, a razem z nią rośnie wskaźnik (Bendjoudi i Hubert 2002, s. 924-928)
> - A i P z tego samego obrysu: Hydrograf bierze A z komórek, a P z wygładzonej granicy, więc wartość bliską 1 należy interpretować ostrożnie
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik geometryczny, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (1), p. 922: K = P / (2 sqrt(pi A)) = 0.28 P / sqrt(A) <https://doi.org/10.1080/02626660209493000>
> 2. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik zwartości (Graveliusa) K = Oz / (2 sqrt(pi A)) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: perimeters of 0.1756 to 84.46 km
> 5. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, pp. 921-922: the perimeter of any basin exceeds that of the circle of the same area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle <https://doi.org/10.1080/02626660209493000>
>
> Funkcja `hydrolog.morphometry.geometric.compactness_coefficient`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:compactness_coefficient -->

### Wskaźnik kolistości Millera

Wskaźnik kolistości (ang. *circularity ratio*) to stosunek powierzchni zlewni do powierzchni
koła o obwodzie równym obwodowi zlewni (Miller 1953, cytowany za Baścik 2006, wzór 1.2.3). Niesie
tę samą informację co wskaźnik Graveliusa (jest odwrotnością jego kwadratu), tylko w skali, w
której koło ma wartość największą.

<!-- spec:circularity_ratio -->

<a id="spec-circularity_ratio"></a>

> **Wskaźnik kolistości zlewni według Millera** · specyfikacja [`circularity_ratio`](../FORMULAS.md#circularity_ratio) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> C_k = \frac{4\pi A}{P^2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 4) |
> | $P$ | `perimeter_km` | Obwód zlewni, czyli długość jej działu wodnego | km | (0; ∞) | nie podano w źródłach | [0,17; 90] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $C_k$ | `circularity_ratio` | Wskaźnik kolistości: powierzchnia zlewni podzielona przez powierzchnię koła o tym samym obwodzie; 1 dla koła | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | P^2 >= 4 pi A: żaden obwód nie jest krótszy od obwodu koła o tej samej powierzchni (nierówność izoperymetryczna); krótszy oznacza, że A i P zmierzono na różnych obrysach | `isoperimetric` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 6) |
>
> **Konwencje**
>
> - P to długość działu wodnego w wykreślonym przebiegu: rośnie wraz z rozdzielczością mapy lub NMT, ponieważ dział wodny jest nieregularny w każdej skali, a razem z nią rośnie wskaźnik (Bendjoudi i Hubert 2002, s. 924-928)
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik geometryczny, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (2), p. 922: Miller's (1953) C = 4 pi A / P^2 <https://doi.org/10.1080/02626660209493000>
> 2. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.3): Ck = A / Ak = 4 pi A / P^2 <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 3. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik kolistości Ck = 4 pi A / Oz^2 <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: perimeters of 0.1756 to 84.46 km
> 6. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, pp. 921-922: the perimeter of any basin exceeds that of the circle of the same area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle <https://doi.org/10.1080/02626660209493000>
>
> Funkcja `hydrolog.morphometry.geometric.circularity_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:circularity_ratio -->

### Wskaźnik wydłużenia Schumma

Wskaźnik wydłużenia (ang. *elongation ratio*) to stosunek średnicy koła o powierzchni zlewni do
długości zlewni (Schumm 1956, za Baścik 2006, wzór 1.2.2, gdzie w mianowniku stoi długość doliny
$L_m$). Im mniejszy, tym zlewnia bardziej wydłużona.

<!-- spec:elongation_ratio -->

<a id="spec-elongation_ratio"></a>

> **Wskaźnik wydłużenia zlewni według Schumma** · specyfikacja [`elongation_ratio`](../FORMULAS.md#elongation_ratio) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> C_e = \frac{2}{L}\sqrt{\frac{A}{\pi}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 3) |
> | $L$ | `length_km` | Długość zlewni: odcinek prosty od ujścia do najdalszego punktu działu wodnego albo najdłuższa droga spływu przekazana przez Hydrograf | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $C_e$ | `elongation_ratio` | Wskaźnik wydłużenia: średnica koła o tej samej powierzchni podzielona przez długość zlewni; 1 dla koła o średnicy L | – | [0; 2] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | A <= pi L^2: zlewnia leży w kole o promieniu L wokół swojego ujścia, gdzie L to odcinek prosty do najdalszego punktu działu wodnego albo najdłuższa droga spływu, która nie jest krótsza | `within_reach` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
>
> **Konwencje**
>
> - L to odcinek prosty od ujścia do najdalszego punktu działu wodnego (Baścik 2006, s. 21), tak jak `WatershedGeometry` opisuje `length_km`; Hydrograf przekazuje najdłuższą drogę spływu, która nie jest krótsza, więc przy niej wskaźnik wydłużenia jest mniejszy (k większy) niż przy odcinku prostym; L Schumma (1956), czyli największy wymiar równoległy do głównej linii odpływu, oraz Lm Baścika, czyli długość doliny, to inne konwencje
> - to, że A mieści się w kole o promieniu L wokół ujścia, ogranicza Ce z góry przez 2; przy L równym największemu wymiarowi zlewni — przez 1, wartość dla koła
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik geometryczny, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.2): Cw = (2 / Lm) sqrt(A / pi), after Schumm (1956) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik wydłużenia Cw = (2 / L) (A / pi)^0.5 <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km
> 5. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.morphometry.geometric.elongation_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:elongation_ratio -->

### Wskaźnik lemniskaty Chorleya

Chorley, Malm i Pogorzelski (1957, cytowani za Bendjoudi i Hubert 2002, wzory 3–5) porównali
zlewnię z jedną pętlą lemniskaty (krzywej o kształcie płatka). Wskaźnik $k$ (ang. *lemniscate
ratio*) to stosunek powierzchni koła o średnicy $L$ do powierzchni zlewni: rośnie, gdy zlewnia
się wydłuża. W części literatury przeglądowej spotyka się wariant bez $\pi$, który daje wartości
$\pi$ razy mniejsze; nie jest to wskaźnik Chorleya. Hydrolog do wersji 0.8.1 włącznie liczył
właśnie ten wariant; wersja rozwojowa 0.9.0 liczy wskaźnik Chorleya, tak jak Hydrograf.

<!-- spec:lemniscate_ratio -->

<a id="spec-lemniscate_ratio"></a>

> **Wskaźnik lemniskaty k zlewni według Chorleya** · specyfikacja [`lemniscate_ratio`](../FORMULAS.md#lemniscate_ratio) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> k = \frac{\pi L^2}{4A}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 3) |
> | $L$ | `length_km` | Długość zlewni: odcinek prosty od ujścia do najdalszego punktu działu wodnego albo najdłuższa droga spływu przekazana przez Hydrograf | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `lemniscate_ratio` | Wskaźnik lemniskaty: powierzchnia koła o średnicy L podzielona przez powierzchnię zlewni; 1 dla tego koła, większy dla zlewni bardziej wydłużonych | – | [0,25; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | A <= pi L^2: zlewnia leży w kole o promieniu L wokół swojego ujścia, gdzie L to odcinek prosty do najdalszego punktu działu wodnego albo najdłuższa droga spływu, która nie jest krótsza | `within_reach` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
> | pi L^2 / (4A) mieści się w zakresie float64: żadna zlewnia nie jest 10^150 razy dłuższa niż szeroka | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - L to odcinek prosty od ujścia do najdalszego punktu działu wodnego (Baścik 2006, s. 21), tak jak `WatershedGeometry` opisuje `length_km`; Hydrograf przekazuje najdłuższą drogę spływu, która nie jest krótsza, więc przy niej wskaźnik wydłużenia jest mniejszy (k większy) niż przy odcinku prostym; L Schumma (1956), czyli największy wymiar równoległy do głównej linii odpływu, oraz Lm Baścika, czyli długość doliny, to inne konwencje
> - k Chorleya z pi (pętla lemniskaty), a nie wariant L^2 / (4A) z niektórych źródeł wtórnych, który Hydrolog obliczał do wersji 0.8.1
> - to, że A mieści się w kole o promieniu L wokół ujścia, ogranicza k z dołu przez 1/4; przy L równym największemu wymiarowi zlewni — przez 1, wartość dla koła
>
> **Zgodność z obserwacjami według źródeł:** brak: wskaźnik geometryczny, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eqs. (3)-(5), pp. 922-923: Chorley et al. (1957) compare the basin with one loop of the lemniscate rho = l cos(k theta), of area pi l^2 / (4k), so k = pi l^2 / (4A) <https://doi.org/10.1080/02626660209493000>
> 2. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik lemniskaty Cl = pi L^2 / (4A) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km
> 5. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 6. Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (5), p. 923 <https://doi.org/10.1080/02626660209493000>
>
> Funkcja `hydrolog.morphometry.geometric.lemniscate_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:lemniscate_ratio -->

### Jak czytać wskaźniki kształtu

- Wskaźniki opisują zlewnię, nie przewidują wezbrania. Dwie zlewnie o tym samym wskaźniku formy
  mogą mieć różne fale, jeśli różnią się spadkami, glebami czy siecią rzeczną.
- Słowne klasy („zlewnia zwarta”, „wydłużona”) i progi spotykane w materiałach dydaktycznych nie
  mają jednego źródła; traktuj je orientacyjnie.
- Wartość zależy od definicji $L$ i od sposobu pomiaru $P$. Zestawiając wskaźniki różnych
  zlewni, podaj obie.
- Hydrolog sprawdza, czy dane opisują możliwą zlewnię: odrzuca powierzchnię większą od koła o
  promieniu $L$ wokół przekroju i obwód krótszy od obwodu koła o tej samej powierzchni (warunki
  w ramkach).

### Przykład: wskaźniki kształtu Kamiennika

Wskaźniki geometryczne, kształtu i rzeźby z pliku zlewni liczy jedno polecenie:

```bash
hydrolog morphometry watershed --watershed-file tests/fixtures/kamiennik.json
```

Fragment wyniku:

```text
  geometry:
    area_km2:     37.22
    perimeter_km: 40.89
    length_km:    16.05
    width_km:     2.319
  shape_indicators:
    form_factor:             0.144486
    compactness_coefficient: 1.89071
    circularity_ratio:       0.279738
    elongation_ratio:        0.428912
    lemniscate_ratio:        5.4358
```

Zlewnia ma średnio 2,32 km szerokości przy 16,05 km długości: wskaźnik formy 0,144, wskaźnik
wydłużenia 0,429 i wskaźnik lemniskaty 5,44 opisują zlewnię silnie wydłużoną. Obwód jest 1,89
raza dłuższy od obwodu koła o tej samej powierzchni (wskaźnik kolistości 0,280).

Te same liczby zależą jednak od przyjętych definicji. Z długością w linii prostej (10,88 km):

```bash
hydrolog morphometry watershed --watershed '{"name":"Kamiennik — Świerzawa (L w linii prostej)","area_km2":37.22,"perimeter_km":40.89,"length_km":10.88,"elevation_min_m":257.3,"elevation_max_m":475.1}'
```

a z obwodem zmierzonym po schodkowej granicy komórek NMT (51,12 km zamiast 40,89 km wygładzonej
granicy Hydrografu):

```bash
hydrolog morphometry watershed --watershed '{"name":"Kamiennik — Świerzawa (obwód z komórek NMT)","area_km2":37.22,"perimeter_km":51.12,"length_km":16.05,"elevation_min_m":257.3,"elevation_max_m":475.1}'
```

| Wskaźnik | Plik przykładu | $L$ w linii prostej | $P$ z komórek NMT |
|---|---|---|---|
| wskaźnik formy $C_f$ | 0,1445 | 0,3144 | 0,1445 |
| wskaźnik zwartości $C_z$ | 1,891 | 1,891 | 2,364 |
| wskaźnik kolistości $C_k$ | 0,2797 | 0,2797 | 0,1790 |
| wskaźnik wydłużenia $C_e$ | 0,4289 | 0,6327 | 0,4289 |
| wskaźnik lemniskaty $k$ | 5,436 | 2,498 | 5,436 |

Zmiana definicji długości przesuwa wskaźnik formy ponad dwukrotnie, a wskaźnik lemniskaty z 5,4
na 2,5; obwód z granicy rastra zwiększa wskaźnik zwartości o jedną czwartą. Dwie ostatnie
kolumny nie mają w pliku wysokości średniej, więc Hydrolog przybliża ją średnią z wysokości
skrajnych i mówi o tym uwagą `mean_elevation_approximated` (podrozdział 1.5).

## 1.5. Wysokości, deniwelacja i wskaźnik rzeźby

**Wysokości charakterystyczne.** $H_{max}$ to najwyższy punkt zlewni, $H_{min}$ najniższy, zwykle
przekrój zamykający; w opracowaniach hydrologicznych za $H_{min}$ przyjmuje się też rzędną
zwierciadła wody w przekroju (Baścik 2006, s. 23). Ich różnica to **deniwelacja** (ang.
*relief*). **Wysokość średnią** najlepiej liczyć jako średnią ważoną powierzchnią z NMT albo z
krzywej hipsograficznej (podrozdział 1.7). Gdy jej nie podano, Hydrolog przyjmuje średnią z
wysokości najwyższej i najniższej i informuje o tym; to tylko przybliżenie (Baścik 2006,
wzór 1.2.5).

<!-- spec:midpoint_elevation -->

<a id="spec-midpoint_elevation"></a>

> **Średnia wysokość zlewni jako średnia wysokości skrajnych** · wzór grupy B `midpoint_elevation` (Tier B, CMP-2.2)
>
> **Definicja:** H_mean = (Hmin + Hmax) / 2, średnia wysokość przyjmowana przez `TerrainAnalysis`, gdy nie podano żadnej [m n.p.m.] (źr. 1)
>
> **Konwencja:** przybliżenie, z komunikatem `mean_elevation_approximated` tam, gdzie Hydrolog go zgłasza; należy preferować średnią z NMT ważoną powierzchnią (Baścik 2006, wzór 1.2.8, `HypsometricCurve.mean_elevation`)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.5): the mean elevation approximated by the mean of the highest and the lowest <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.morphometry.terrain.TerrainAnalysis`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:midpoint_elevation -->

**Wskaźnik rzeźby** (ang. *relief ratio*; Schumm 1956, „wskaźnik rzeźby” u Baścik 2006,
wzór 1.2.12) to deniwelacja zlewni podzielona przez jej długość: przeciętny spadek, jaki
miałaby zlewnia, gdyby opadała równomiernie od najwyższego punktu do przekroju. Hydrolog podaje
go bezwymiarowo (m/m), Baścik i Wartalska w m/km, czyli w promilach.

<!-- spec:relief_ratio -->

<a id="spec-relief_ratio"></a>

> **Wskaźnik rzeźby: deniwelacja zlewni podzielona przez długość (Schumm)** · specyfikacja [`relief_ratio`](../FORMULAS.md#relief_ratio) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> R_h = \frac{H_{max} - H_{min}}{L}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $H_{min}$ | `elevation_min_m` | Najniższa wysokość zlewni, czyli wysokość jej ujścia [m n.p.m.] | m | (−∞; ∞) | nie podano w źródłach | [100; 750] (źr. 3) |
> | $H_{max}$ | `elevation_max_m` | Najwyższa wysokość zlewni [m n.p.m.] | m | (−∞; ∞) | nie podano w źródłach | [100; 750] (źr. 3) |
> | $L$ | `length_km` | Długość zlewni: odcinek prosty od ujścia do najdalszego punktu działu wodnego albo najdłuższa droga spływu przekazana przez Hydrograf | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $R_h$ | `relief_ratio` | Wskaźnik rzeźby: deniwelacja podzielona przez długość zlewni | m/m | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | Hmax > Hmin: zlewnia odwadnia się do swojego ujścia, więc wznosi się ponad nie | `rises_above_outlet` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | (Hmax - Hmin) / L mieści się w zakresie float64: żadna deniwelacja nie jest 10^300 razy większa od długości | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $100$ | `percent` | Mnożnik przeliczający stosunek m/m na procenty | 100 | % na m/m | (źr. 5) |
>
> **Konwencje**
>
> - Rh w m/m (bezwymiarowy): deniwelacja w m podzielona przez L przeliczone z km na m według tabeli jednostek; Baścik (2006) i Wartalska podają go w m/km (w promilach)
> - deniwelacja całej zlewni, czyli jej najwyższy punkt minus ujście; Baścik (2006, s. 23) zauważa, że w praktyce hydrologicznej można przyjmować rzędną zwierciadła wody w ujściu
> - L to `length_km` zlewni we wskaźniku rzeźby (L Schumma to największy wymiar równoległy do głównej linii odpływu, Lm Baścika to długość doliny); `TerrainAnalysis` podaje ten sam stosunek jako spadek zlewni, który nie jest średnim spadkiem terenu, a w odniesieniu do długości cieku jako spadek cieku głównego, którego różnicą wysokości jest wtedy deniwelacja zlewni, a nie różnica między źródłem a ujściem cieku
>
> **Zgodność z obserwacjami według źródeł:** brak: stosunek wielkości mierzonych, którego źródła nie porównują z żadnymi obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.12): wskaźnik rzeźby Cs = (Hmax - Hmin) / Lm; eq. (1.2.15): the slope of a river, the drop from its source to its mouth over its length <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2.3: wskaźnik rzeźby zlewni Strahlera Jd = dH / L <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km
> 5. BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01; the slopes of TerrainAnalysis in percent <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>
>
> Funkcja `hydrolog.morphometry.terrain.relief_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:relief_ratio -->

Hydrolog nazywa ten sam stosunek **spadkiem zlewni** (`watershed_slope`), a deniwelację całej
zlewni podzieloną przez długość cieku głównego **spadkiem cieku** (`channel_slope`). Obie
nazwy wymagają ostrożności:

- **Spadek zlewni** z deniwelacji nie jest średnim nachyleniem stoków. To drugie liczy się z NMT
  jako średnią nachyleń komórek (dla Kamiennika Hydrograf podał 0,082 m/m, sześć razy więcej);
  Hydrolog go nie liczy, a podany w pliku tylko przekazuje metodom czasu koncentracji, które go
  potrzebują (rozdział 4), i mówi o tym uwagą `slopes_from_relief`.
- **Spadek cieku** z deniwelacji całej zlewni to górne oszacowanie. Spadek rzeki to różnica
  wysokości jej źródła i ujścia podzielona przez długość (Baścik 2006, wzór 1.2.15), a źródło
  leży zwykle niżej niż najwyższy punkt działu wodnego. Metody czasu koncentracji i hydrogramu
  jednostkowego biorą spadki z przeznaczonych dla nich pól zlewni (rozdziały 4 i 5), nie z tego
  wskaźnika.
- W Hydrografie klucz `relief_ratio` oznacza inny wskaźnik: deniwelację podzieloną przez
  pierwiastek z powierzchni (wskaźnik Meltona, ang. *Melton ruggedness ratio*; Wartalska, PWr,
  podaje go jako średni spadek zlewni). Nie myl go ze wskaźnikiem rzeźby.

<!-- TODO spec: Melton's ruggedness ratio, the relief over the square root of the area (Hydrograf's key relief_ratio; Wartalska, PWr); not computed by Hydrolog -->

**Przykład 1 (Baścik 2006, s. 33): Racławka.** Rzeka ma 16,3 km długości, źródła na 390 m n.p.m.
i ujście na 242 m n.p.m. Jej spadek to wskaźnik rzeźby z długością rzeki:

```python
from hydrolog.morphometry.terrain import relief_ratio

print(round(relief_ratio(elevation_min_m=242, elevation_max_m=390, length_km=16.3), 5))
# 0.00908
```

czyli 9,08 ‰, jak u Baścik (9,1 ‰). Tu źródło rzeki i najwyższy punkt są tym samym punktem, więc
wskaźnik rzeźby i spadek rzeki są równe.

**Przykład 2: Kamiennik.** Polecenie z podrozdziału 1.4 daje dla pliku przykładu:

```text
  elevation:
    elevation_min_m:  257.3
    elevation_max_m:  475.1
    elevation_mean_m: 363.2
    relief_m:         217.8
    relief_ratio:     0.0135701
  slopes:
    watershed_slope_percent: 1.35701
    watershed_slope_m_per_m: 0.0135701
    channel_slope_percent:   1.47361
    channel_slope_m_per_m:   0.0147361
```

Deniwelacja 217,8 m na 16,05 km daje wskaźnik rzeźby 0,0136 m/m (13,6 ‰). „Spadek cieku”
0,0147 m/m to ta sama deniwelacja na 14,78 km cieku głównego; najdłuższa droga spływu opada
jednak tylko o 181,44 m (od 440,16 do 258,72 m n.p.m.), bo zaczyna się niżej niż najwyższy punkt
zlewni, a jej spadek między końcami wynosi 0,0114 m/m.

## 1.6. Spadek wyrównany profilu podłużnego

Profil podłużny cieku jest zwykle wklęsły: stromy w górnym biegu, łagodny w dolnym. Spadek
liczony między końcami profilu przecenia wtedy spadek większej części cieku. **Spadek
wyrównany** (ang. *equal-area slope*) to spadek prostej poprowadzonej z najniższego punktu
profilu tak, aby pola między nią a profilem, leżące nad nią i pod nią, były równe (KZGW 2017,
zał. 2, s. 97, objaśnienie wzoru 6.17; Ministry of Works and Development 1980, aneks A). Trójkąt
pod tą prostą ma więc to samo pole co obszar pod profilem nad przekrojem. Takiego spadku $J_g$
wymaga metoda Lutza szacowania parametrów modelu Nasha (rozdział 5), opisana w metodyce KZGW
(2017).

<!-- spec:equal_area_slope -->

<a id="spec-equal_area_slope"></a>

> **Spadek uśredniony profilu podłużnego metodą równych pól (prosta przez przekrój z równymi polami nad nią i pod nią)** · specyfikacja [`equal_area_slope`](../FORMULAS.md#equal_area_slope) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> S = \frac{2A}{L^2},\quad A = \sum_{i} \frac{(x_{i+1} - x_i)\,(h_i + h_{i+1})}{2},\quad h_i = z_i - z_0,\quad L = x_n - x_0
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x$ | `distance_m` (ciąg) | Odległość wzdłuż profilu od przekroju (pierwszego punktu) w górę do każdego punktu; początek dowolny, bo liczą się tylko różnice | m | [0; ∞) | nie podano w źródłach | [0; 30 000] (źr. 4) |
> | $z$ | `elevation_m` (ciąg) | Wysokość każdego punktu profilu, dna lub wypełnionego NMT wzdłuż drogi spływu; pierwsza to wysokość przekroju | m | (−∞; ∞) | nie podano w źródłach | [100; 750] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $S$ | `slope_m_per_m` | Spadek prostej przez przekrój, przy którym pola profilu nad nią i pod nią są równe | m/m | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jedna wysokość dla każdej odległości | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 3) |
> | x[i+1] >= x[i]: profil biegnie od przekroju w górę; powtórzona odległość to pionowy uskok | `distance_not_decreasing` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 3) |
> | 0 < 2 A / L**2 < inf: profil jako całość leży powyżej przekroju (A > 0) na długości L > 0, a float64 mieści obie wartości | `positive_area` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
>
> **Konwencje**
>
> - profil jest uporządkowany od przekroju w górę: x to odległość wzdłuż drogi spływu w m od dowolnego początku, bo liczą się tylko różnice, z to wysokość w m; L to ostatnia odległość minus pierwsza
> - prosta przechodzi przez pierwszy punkt, czyli przekrój, na jego wysokości: TM61 prowadzi ją przez przekrój A, KZGW (2017, s. 97) z najniższego punktu profilu, którym jest przekrój drogi spływu na wypełnionym NMT; odcinek poniżej przekroju liczy się jako pole pod prostą, więc A to pole ze znakiem funkcji z - z[0]
> - A metodą trapezów, profil prostoliniowy między punktami (Barbosa Jr., wzór 17); trójkąt pod prostą, L (S L) / 2, ma pole równe A, więc pola profilu nad prostą i pod nią są równe (TM61, Sa = 2Ad/L^2)
> - S w m/m, nie w procentach ani promilach
> - Jg Lutza (KZGW 2017, s. 97) to właśnie ten spadek profilu podłużnego cieku głównego od działu wodnego do przekroju, czyli najdłuższej drogi spływu (`WatershedParameters.flow_path_equal_area_slope_m_per_m`); spadek między końcami tej drogi (`flow_path_slope_m_per_m`), S Kirpicha, jest na profilu wklęsłym większy i nie może go zastąpić
>
> **Założenia**
>
> - punktami są te miejsca jednej drogi spływu, w których znana jest wysokość: komórki drogi D8 na wypełnionym NMT lub punkty pomierzone; ciąg punktów o równej wysokości można przerzedzić do jego końców bez zmiany A
> - profil z wypełnionego NMT nie ma punktu poniżej przekroju; pomierzone dno może mieć poniżej niego przegłębienia, które zmniejszają A
>
> **Zgodność z obserwacjami według źródeł:** brak: spadek uśredniony metodą równych pól definiuje średni spadek profilu (TM61, załącznik A; KZGW 2017, s. 97); jego źródła nie porównują go z żadnymi obserwacjami, a TM61 (s. 12) zauważa, że w praktyce daje on wyniki w dużej mierze niezależne od osoby wykonującej obliczenia
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the legend of eq. 6.17: Jg, the averaged slope of the main stream, is the slope of the line from the lowest point of the longitudinal profile for which the areas between it and the profile, below and above it, are equal <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Ministry of Works and Development, Water and Soil Division (1980). A method for estimating design peak discharge, Technical Memorandum No. 61, Wellington, appendix A, pp. 12-13: the equal-area method, line AC through the outlet A with equal areas X and Y; the area under the profile Ad equals the triangle ABC, so Sa = 2Ad/L^2 <https://web.archive.org/web/20170228021947/http://docs.niwa.co.nz/library/public/TM61_1980.pdf>
> 3. Barbosa Jr., A.R. (2004). Hidrologia Aplicada CIV 226, Bacia Hidrográfica, Universidade Federal de Ouro Preto, lecture notes, section 3.4.4, eqs. 17-18, p. 14: the area under the profile Ap as a sum of trapezoids and S2 = 2Ap/L^2 - 2z_foz/L <https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/17403/material/Cap2%20-%20Bacia%20Hidrografica_UFOP.pdf>
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m
>
> Funkcja `hydrolog.morphometry.profile.equal_area_slope`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:equal_area_slope -->

Hydrolog liczy spadek wyrównany funkcją `hydrolog.morphometry.equal_area_slope` z punktów profilu
uporządkowanych od przekroju w górę (odległość wzdłuż drogi spływu i wysokość); w zlewni jest to
pole `flow_path_equal_area_slope_m_per_m`, które przekazuje Hydrograf. Pole pod profilem sumuje
się metodą trapezów (Barbosa Jr. 2004), więc profil może mieć dowolnie wiele punktów, także
nierówno rozmieszczonych.

**Typowe błędy.** Podstawianie spadku między końcami cieku w miejsce spadku wyrównanego (Hydrolog
nie robi tego za użytkownika: metoda Lutza bez pola spadku wyrównanego kończy się błędem
`missing_field`, ADR-0053); liczenie spadku z profilu innego niż profil najdłuższej drogi spływu;
profil z NMT nieprzygotowanego hydrologicznie, z zagłębieniami poniżej przekroju (zmniejszają pole
nad przekrojem, a więc i spadek).

**Przykład: Kamiennik.** Profil najdłuższej drogi spływu z NMT Hydrografu (wypełnionego) ma
15 878,29 m od przekroju (258,72 m n.p.m.) do punktu najdalszego hydraulicznie (440,16 m n.p.m.);
w pliku zostało 1593 z 2645 komórek, bo wnętrza odcinków o stałej wysokości nie zmieniają pola.

```python
import json

from hydrolog.morphometry import equal_area_slope

with open("tests/fixtures/kamiennik_flow_path_profile.json") as f:
    profil = json.load(f)
print(round(equal_area_slope(profil["distance_m"], profil["elevation_m"]), 5))
# 0.00848
```

Spadek wyrównany wynosi 0,00848 m/m (8,48 ‰), a spadek między końcami 0,0114 m/m: profil jest
wklęsły i spadek wyrównany stanowi 0,742 spadku między końcami. W metodzie Lutza mniejszy spadek
oznacza dłuższy czas do kulminacji i niższą falę (rozdział 5).

## 1.7. Krzywa hipsograficzna i całka hipsometryczna

**Krzywa hipsograficzna** (hipsometryczna, ang. *hypsometric curve*) pokazuje, jaka część
powierzchni zlewni leży powyżej danej wysokości. Strahler (1952) zapisał ją we współrzędnych
względnych: na jednej osi udział powierzchni $a/A$ leżącej nad daną wysokością, na drugiej
wysokość względna $h/H$, czyli wysokość nad najniższym punktem podzielona przez deniwelację.
Krzywe zlewni różnej wielkości i wysokości mieszczą się wtedy w kwadracie jednostkowym i można je
porównywać.

<!-- spec:hypsometric_curve -->

<a id="spec-hypsometric_curve"></a>

> **Krzywa hipsometryczna zlewni** · wzór grupy B `hypsometric_curve` (Tier B, CMP-2.2)
>
> **Definicja:** wysokości względne h/H = (t - min) / (max - min) na n równo rozmieszczonych progach t oraz względne powierzchnie a/A komórek położonych na wysokości każdego progu lub powyżej (źr. 1)
>
> **Konwencja:** przekroczenie (powierzchnia powyżej), czyli procentowa krzywa hipsometryczna Strahlera; pierwsza względna powierzchnia wynosi 1
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) <https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html>
>
> Funkcja `hydrolog.morphometry.hypsometry.HypsometricCurve.generate_curve`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hypsometric_curve -->

**Całka hipsometryczna** HI (ang. *hypsometric integral*) to pole pod krzywą w tym kwadracie:
jaka część „bryły” między najniższym a najwyższym punktem jest jeszcze wypełniona terenem. Jest
równa ilorazowi wysokości średniej nad najniższym punktem i deniwelacji (wskaźnik Pike'a i
Wilsona 1971, ang. *elevation-relief ratio*; równość wynika wprost z definicji krzywej). Hydrolog
całkuje krzywą metodą trapezów na równo rozmieszczonych wysokościach względnych; różnicę względem
wartości dokładnej i jej granicę podaje ramka. Czy liczyć wartość dokładną, pozostaje otwartym
pytaniem ADR-0065.

<!-- spec:hypsometric_integral -->

<a id="spec-hypsometric_integral"></a>

> **Całka hipsometryczna zlewni obliczana metodą trapezów z krzywej hipsometrycznej (Strahler)** · specyfikacja [`hypsometric_integral`](../FORMULAS.md#hypsometric_integral) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> HI = \sum_{i=0}^{n-2} \frac{a_i + a_{i+1}}{2\,(n-1)},\quad a_i = \frac{\sum_{z_j \ge t_i} A_j}{\sum_j A_j},\quad t_i = z_{min} + \frac{i}{n-1}(z_{max} - z_{min})
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $z$ | `elevations_m` (ciąg) | Wysokość każdej komórki NMT zlewni [m n.p.m.] | m | (−∞; ∞) | nie podano w źródłach | [100; 750] (źr. 3) |
> | $A_j$ | `cell_areas` (ciąg) | Powierzchnia każdej komórki w dowolnej jednej jednostce (liczą się tylko udziały) | – | (0; ∞) | nie podano w źródłach | [1; 1] (źr. 4) |
> | $n$ | `n_points` (liczba całkowita) | Liczba równo rozmieszczonych wysokości względnych krzywej | – | [2; ∞) | nie podano w źródłach | [101; 101] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $HI$ | `hypsometric_integral` | Pole pod procentową krzywą hipsometryczną w kwadracie jednostkowym | – | [0; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | jedna powierzchnia na każdą wysokość | `same_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | max(z) > min(z): wysokość względna h/H powstaje z dzielenia przez deniwelację | `positive_relief` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - krzywa względnej powierzchni a/A położonej na wysokości względnej h/H lub powyżej (przekroczenie), czyli procentowa krzywa hipsometryczna Strahlera, próbkowana na n równo rozmieszczonych wysokościach od najniższej do najwyższej komórki, h/H = 0 do 1
> - HI metodą trapezów na n punktach krzywej, domyślnie n = 101; dokładna całka schodkowej krzywej komórek wynosi (mean - min) / (max - min) (Pike i Wilson 1971), a wynik metody trapezów odbiega od niej co najwyżej o (a(0) - a(1)) / (2 (n - 1)), czyli 0,005 dla n = 101, najbardziej tam, gdzie duża część powierzchni leży na wysokości ujścia
> - stadia Strahlera (1952, tekst przy rys. 7): około 0,60 i więcej — stadium nierównowagi (młodości), od 0,35 do 0,60 — stadium równowagi (dojrzałości), poniżej 0,35 — faza monadnock (ostańców); Strahler podaje je jako przybliżone granice i zastępuje starość fazą monadnock
> - powierzchnie komórek w dowolnej jednej jednostce: liczą się tylko ich udziały
>
> **Zgodność z obserwacjami według źródeł:** brak: całka opisuje powierzchnię terenu; Strahler (1952) wiąże jej wartości ze stadiami erozji, a nie z obserwacjami jakiejś wielkości
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) <https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html>
> 2. Pike, R.J. & Wilson, S.E. (1971). Elevation-relief ratio, hypsometric integral, and geomorphic area-altitude analysis. Geological Society of America Bulletin 82: 1079-1084, the elevation-relief ratio E = (mean - min) / (max - min) equals the hypsometric integral (not opened; the identity of the exceedance integral, integral of P(h >= x) dx over [0, 1] = E[h], is exact)
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m
> 4. Hydrolog's HypsometricCurve: cells of equal area unless cell_areas is given, as in every example and test of the project, src/hydrolog/morphometry/hypsometry.py; examples/04_morfometria.ipynb
>
> Funkcja `hydrolog.morphometry.hypsometry.hypsometric_integral`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hypsometric_integral -->

Krzywa daje też wysokości charakterystyczne: **wysokość średnią** (ważoną powierzchnią) i
**wysokość środkową** (medianę), powyżej której leży połowa powierzchni.

<!-- spec:area_weighted_mean_elevation -->

<a id="spec-area_weighted_mean_elevation"></a>

> **Średnia wysokość zlewni ważona powierzchnią** · wzór grupy B `area_weighted_mean_elevation` (Tier B, CMP-2.2)
>
> **Definicja:** średnia wysokość komórek ważona ich powierzchniami [m n.p.m.] (źr. 1)
>
> **Konwencja:** `numpy.average` z powierzchniami komórek jako wagami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.8): the mean elevation weighted by the areas between contours <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.morphometry.hypsometry.HypsometricCurve.mean_elevation`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:area_weighted_mean_elevation -->

<!-- spec:elevation_above_share -->

<a id="spec-elevation_above_share"></a>

> **Wysokość, powyżej której leży zadany udział powierzchni zlewni** · wzór grupy B `elevation_above_share` (Tier B, CMP-2.2)
>
> **Definicja:** wysokość pierwszej komórki, licząc od najwyższej w dół, przy której skumulowany udział powierzchni osiąga zadany procent [m n.p.m.] (źr. 1)
>
> **Konwencja:** wysokość środkowa (mediana) to ta, powyżej której leży połowa powierzchni; bez interpolacji między komórkami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) <https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html>
>
> Funkcja `hydrolog.morphometry.hypsometry.HypsometricCurve.elevation_at_percentile`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:elevation_above_share -->

**Interpretacja.** Strahler (1952) wiązał kształt krzywej ze stadium rozwoju rzeźby: krzywa
wypukła i duża całka to stadium nierównowagi (młodość), krzywa esowata to stadium równowagi
(dojrzałość), a mała całka to faza ostańcowa (ang. *monadnock phase*), gdy nad zrównanym terenem
sterczą pojedyncze wzniesienia. Sam Strahler podawał progi tych stadiów jako przybliżone (ramka
całki hipsometrycznej); Hydrolog ich nie stosuje i zwraca tylko liczbę. Całka zależy od
rozdzielczości NMT, od tego, czy najniższym punktem jest najniższa komórka, czy zwierciadło wody w
przekroju, i od przygotowania NMT; zlewnia płaska (bez deniwelacji) nie ma krzywej, a Hydrolog
odmawia wtedy obliczeń.

**Przykład: Kamiennik.** Plik [`dane/kamiennik_hipsometria.csv`](dane/kamiennik_hipsometria.csv)
zawiera wysokości wszystkich 1 488 936 komórek NMT GUGiK (oczko 5 m, 37,22 km²) leżących wewnątrz
granicy zlewni wyznaczonej przez Hydrograf, zaokrąglone do 0,1 m, z liczbą komórek na każdej
wysokości (kolumny `elevation_m` i `cells`). Komórki mają równe powierzchnie, więc liczby komórek
są wagami:

```python
import csv

import numpy as np

from hydrolog.morphometry import HypsometricCurve

with open("docs/podrecznik/dane/kamiennik_hipsometria.csv") as f:
    rows = list(csv.DictReader(f))
z = np.array([float(r["elevation_m"]) for r in rows])
n = np.array([float(r["cells"]) for r in rows])
krzywa = HypsometricCurve(z, n)
wynik = krzywa.analyze()
print(round(wynik.hypsometric_integral, 4), round(wynik.elevation_mean_m, 2), wynik.elevation_median_m)
# 0.4817 363.26 367.6
print(krzywa.elevation_at_percentile(10), krzywa.elevation_at_percentile(90))
# 395.3 321.3
```

Punkty krzywej (co dziesiąty z wyniku `generate_curve`; wysokość bezwzględną odtworzono z
wysokości względnej, najniższej wysokości i deniwelacji):

| $h/H$ | wysokość [m n.p.m.] | $a/A$ |
|---|---|---|
| 0,0 | 259,3 | 1,0000 |
| 0,1 | 280,9 | 0,9895 |
| 0,2 | 302,5 | 0,9577 |
| 0,3 | 324,0 | 0,8872 |
| 0,4 | 345,6 | 0,7495 |
| 0,5 | 367,2 | 0,5068 |
| 0,6 | 388,8 | 0,1507 |
| 0,7 | 410,4 | 0,0546 |
| 0,8 | 431,9 | 0,0138 |
| 0,9 | 453,5 | 0,0033 |
| 1,0 | 475,1 | 0,0000 |

Całka hipsometryczna Kamiennika wynosi 0,4817 (wartość dokładna z wysokości średniej: 0,48174;
trapezy na domyślnej liczbie punktów odbiegają od niej dopiero na szóstym miejscu po przecinku,
bo przy samym przekroju leży niewiele komórek). Krzywa jest esowata: między 367 a 389 m n.p.m.
leży ponad jedna trzecia powierzchni zlewni, a ponad 410 m n.p.m. tylko jej 5,5 %. Według
przybliżonych progów Strahlera (ramka) to stadium równowagi. Wysokość średnia z NMT,
363,26 m n.p.m., jest bliska wysokości w pliku przykładu (363,2 m n.p.m.), a średnia z wysokości
skrajnych (367,2 m n.p.m.) zawyża ją o prawie 4 m.

W pliku przykładu $H_{min}$ wynosi 257,3 m n.p.m., a najniższa komórka surowego NMT 259,3 m
n.p.m.: Hydrograf brał wysokości z NMT przygotowanego hydrologicznie, w którym koryta cieków z
BDOT10k obniżył o 2 m. Krzywą hipsograficzną liczy się z NMT surowego, bo ma ona opisywać teren.

## 1.8. Sieć rzeczna

### Cieki, odcinki i rzędy

Sieć rzeczną opisuje się jako drzewo: **odcinki** (ang. *links*, *segments*) łączą **węzły** (ang. *nodes*)
(źródła, połączenia cieków i przekrój zamykający). **Ciek** w sensie Strahlera to ciąg odcinków
tego samego rzędu, od miejsca, w którym ten rząd powstał, do połączenia z ciekiem rzędu równego
lub wyższego.

**Rzędy Strahlera** (ang. *stream order*; Strahler 1957, za Baścik 2006, s. 28) zaczynają się od
cieków źródłowych, a rząd rośnie dopiero tam, gdzie łączą się cieki tego samego, najwyższego
rzędu; przy połączeniu cieków różnych rzędów ciek poniżej zachowuje rząd wyższego (reguła w
ramce). Dopływ niższego rzędu nie przerywa więc cieku: ciek rzędu 2, do którego wpada ciek rzędu
1, pozostaje jednym ciekiem rzędu 2, choć w programie GIS składa się z dwóch odcinków.

<!-- spec:strahler_order -->

<a id="spec-strahler_order"></a>

> **Rząd cieku poniżej węzła według Strahlera** · specyfikacja [`strahler_order`](../FORMULAS.md#strahler_order) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> u = \begin{cases} 1 & \text{brak cieków powyżej} \\ \max u_i + 1 & \text{co najmniej dwa } u_i = \max u_i \\ \max u_i & \text{w pozostałych przypadkach} \end{cases}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $u_i$ | `upstream_orders` (ciąg) | Rzędy według Strahlera cieków wpadających do danego cieku; lista pusta dla cieku źródłowego | – | [1; ∞) | nie podano w źródłach | [1; 3] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $u$ | `order` (liczba całkowita) | Rząd cieku poniżej węzła według Strahlera | – | [1; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | rzędy są liczbami całkowitymi | `whole_orders` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
>
> **Konwencje**
>
> - węzeł trzech lub więcej cieków podnosi rząd, gdy co najmniej dwa z nich mają rząd najwyższy
> - innym uporządkowaniem jest magnituda Shreve'a, czyli suma magnitud cieków powyżej węzła (specyfikacja `shreve_magnitude`)
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja cieków sieci rzecznej
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) <https://doi.org/10.1029/TR038i006p00913>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, orders 1 to 3
>
> Funkcja `hydrolog.network.stream_order.strahler_order`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:strahler_order -->

**Magnitudy Shreve'a** (ang. *magnitude*; Shreve 1966, cytowany za źródłami wtórnymi) liczą
źródła: odcinek źródłowy ma magnitudę 1, a w każdym węźle magnitudy odcinków dopływających się
sumują. Magnituda odcinka ujściowego to liczba wszystkich źródeł sieci. Hydrolog nadaje magnitudy
poleceniem `network stats --method shreve`.

<!-- spec:shreve_magnitude -->

<a id="spec-shreve_magnitude"></a>

> **Magnituda odcinka cieku poniżej węzła według Shreve'a** · specyfikacja [`shreve_magnitude`](../FORMULAS.md#shreve_magnitude) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> M = \begin{cases} 1 & \text{brak odcinka powyżej} \\ \sum_i M_i & \text{w pozostałych przypadkach} \end{cases}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $M_i$ | `upstream_magnitudes` (ciąg) | Magnitudy według Shreve'a odcinków wpadających do danego odcinka; lista pusta dla odcinka źródłowego | – | [1; ∞) | nie podano w źródłach | [1; 4] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $M$ | `magnitude` (liczba całkowita) | Magnituda odcinka poniżej węzła według Shreve'a, czyli liczba źródeł powyżej niego | – | [1; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | magnitudy są liczbami całkowitymi, liczbami źródeł | `whole_magnitudes` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 2) |
> | suma magnitud jest mniejsza niż 2^53, do której float64 przedstawia dokładnie każdą liczbę całkowitą | `sum_exact` | odmowa obliczeń: wzór jest nieokreślony | (źr. 4) |
>
> **Konwencje**
>
> - magnitudy odcinków, czyli fragmentów cieków między węzłami, takich jak odcinki `StreamNetwork`
> - `network stats --method shreve` liczy odcinki każdej magnitudy i nie podaje wskaźników Hortona, zdefiniowanych dla rzędów Strahlera
>
> **Zgodność z obserwacjami według źródeł:** brak: klasyfikacja odcinków sieci rzecznej
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Esri. How Stream Order works. ArcGIS Pro 3.8 documentation, Spatial Analyst, 'Shreve method': exterior links are of order 1 and the orders of interior links are additive, 1 and 1 give 2, 1 and 2 give 3, 2 and 3 give 5; the magnitude of a link is the number of upstream links (after Shreve 1966) <https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/how-stream-order-works.htm>
> 2. Shreve, R.L. (1966). Statistical law of stream numbers. Journal of Geology 74(1): 17-37, the magnitude of a link, the number of sources upstream of it: a source link is of magnitude 1 and the magnitudes add at every junction (not opened; the definition as Esri's documentation gives it) <https://doi.org/10.1086/627137>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, magnitudes 1 to 4 meet
> 4. IEEE 754 double precision (float64), 53-bit significand: whole numbers exact up to 2^53
>
> Funkcja `hydrolog.network.stream_order.shreve_magnitude`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:shreve_magnitude -->

### Prawa Hortona

Horton (1945) i Strahler (1957) zauważyli, że w wielu sieciach liczby cieków kolejnych rzędów
maleją, a ich średnie długości rosną w przybliżeniu w postępie geometrycznym (prawa Hortona,
cytowane za Baścik 2006, wzory 1.2.18–1.2.22). Opisują to dwa stosunki: **wskaźnik bifurkacji**
(ang. *bifurcation ratio*), stosunek liczb cieków dwóch kolejnych rzędów, i **wskaźnik długości
cieków** (ang. *length ratio*), stosunek ich średnich długości. Oba są określone tylko dla rzędów
Strahlera; dla magnitud Shreve'a Hydrolog ich nie podaje.

<!-- spec:streams_of_each_order -->

<a id="spec-streams_of_each_order"></a>

> **Liczba i długości cieków każdego rzędu** · wzór grupy B `streams_of_each_order` (Tier B, CMP-2.2)
>
> **Definicja:** liczba cieków każdego rzędu według Strahlera, ich łączne i średnie długości [km] oraz łączna długość sieci [km] (źr. 1)
>
> **Konwencja:** odcinek kontynuuje ciek odcinka położonego powyżej, jeśli ten ma ten sam rząd, a w przeciwnym razie zaczyna nowy ciek; średnia długość to łączna długość odcinków danego rzędu podzielona przez liczbę jego cieków
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.network.stream_order.StreamNetwork.get_statistics`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:streams_of_each_order -->

<!-- spec:bifurcation_ratio -->

<a id="spec-bifurcation_ratio"></a>

> **Wskaźnik bifurkacji Hortona dla cieków dwóch kolejnych rzędów** · specyfikacja [`bifurcation_ratio`](../FORMULAS.md#bifurcation_ratio) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> R_b = \frac{N_u}{N_{u+1}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $N_u$ | `n_lower` | Liczba cieków rzędu u według Strahlera | – | [2; ∞) | nie podano w źródłach | [2; 5] (źr. 3) |
> | $N_{u+1}$ | `n_higher` | Liczba cieków rzędu u + 1 według Strahlera | – | [1; ∞) | nie podano w źródłach | [1; 2] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $R_b$ | `bifurcation_ratio` | Wskaźnik bifurkacji rzędów u i u + 1 | – | [2; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | N_u i N_(u+1) to liczby cieków, czyli liczby całkowite | `whole_numbers` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | N_u >= 2 N_(u+1): każdy ciek rzędu u + 1 zaczyna się tam, gdzie kończą się co najmniej dwa cieki rzędu u, a każdy ciek kończy się tylko raz, więc Rb >= 2 | `two_streams_per_junction` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
>
> **Konwencje**
>
> - N_u liczy cieki według Strahlera — ciek rzędu u biegnie od miejsca, w którym zaczyna się ten rząd, do połączenia z ciekiem rzędu równego lub wyższego — a nie odcinki między węzłami (`StreamNetwork.get_statistics`)
> - wskaźniki Hortona są zdefiniowane tylko dla rzędów Strahlera: dla magnitud Shreve'a nie wyznacza się ich
>
> **Zgodność z obserwacjami według źródeł:** brak: prawo liczby cieków Hortona sprawia, że Rb jest prawie stały w kolejnych rzędach; źródła podają zakresy Rb, a nie jego zgodność z jakąś wielkością
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) <https://doi.org/10.1029/TR038i006p00913>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 5 and 2 streams of orders 1 and 2
> 4. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 2 and 1 streams of orders 2 and 3
> 5. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
>
> Funkcja `hydrolog.network.stream_order.bifurcation_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:bifurcation_ratio -->

<!-- spec:length_ratio -->

<a id="spec-length_ratio"></a>

> **Wskaźnik długości cieków Hortona dla dwóch kolejnych rzędów** · specyfikacja [`length_ratio`](../FORMULAS.md#length_ratio) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> R_l = \frac{\bar L_{u+1}}{\bar L_u}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\bar L_u$ | `mean_length_lower_km` | Średnia długość cieków rzędu u według Strahlera | km | (0; ∞) | nie podano w źródłach | [0,9; 5,2] (źr. 3) |
> | $\bar L_{u+1}$ | `mean_length_higher_km` | Średnia długość cieków rzędu u + 1 według Strahlera | km | [0; ∞) | nie podano w źródłach | [0,9; 5,2] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $R_l$ | `length_ratio` | Wskaźnik długości cieków rzędów u i u + 1 | – | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | średnia L_(u+1) / średnia L_u mieści się w zakresie float64 | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - średnie długości cieków według Strahlera: łączna długość odcinków danego rzędu podzielona przez liczbę jego cieków (`StreamNetwork.get_statistics`), km
> - Rl ze średnich długości, czyli wskaźnik Hortona; nie stosunek długości łącznych
>
> **Zgodność z obserwacjami według źródeł:** brak: prawo długości cieków Hortona sprawia, że Rl jest prawie stały w kolejnych rzędach; źródła nie podają jego zgodności z żadną wielkością
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) <https://doi.org/10.1029/TR038i006p00913>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, mean lengths of 0.92, 1.45 and 5.2 km of orders 1-3
>
> Funkcja `hydrolog.network.stream_order.length_ratio`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:length_ratio -->

Niski wskaźnik bifurkacji „świadczy o dużej koncentracji dopływów” (Baścik 2006, s. 28). Według
Strahlera (1964, cytowanego za artykułami przeglądowymi; oryginału nie otwierano) w zlewniach,
w których budowa geologiczna nie zaburza sieci, wskaźnik bifurkacji przyjmuje zwykle wartości od
3 do 5, a wyższe wskazują na kontrolę strukturalną. Wskaźnik liczony z jednego czy dwóch cieków
najwyższego rzędu jest jednak bardzo niepewny.

### Gęstość sieci i częstość cieków

**Gęstość sieci rzecznej** (ang. *drainage density*) to łączna długość cieków na jednostkę
powierzchni zlewni; **wskaźnik częstości cieków** (ang. *stream frequency*) to liczba cieków
Strahlera wszystkich rzędów na jednostkę powierzchni (Baścik 2006, wzory 1.2.18–1.2.22). Duża
gęstość sieci oznacza krótką drogę wody po stoku do koryta i zwykle szybszą reakcję zlewni.

<!-- spec:drainage_density -->

<a id="spec-drainage_density"></a>

> **Gęstość sieci rzecznej: długość cieków podzielona przez powierzchnię zlewni** · specyfikacja [`drainage_density`](../FORMULAS.md#drainage_density) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> D_d = \frac{\sum L}{A}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\sum L$ | `total_length_km` | Łączna długość cieków zlewni | km | [0; ∞) | nie podano w źródłach | [0,7; 12,7] (źr. 3) |
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $D_d$ | `drainage_density` | Gęstość sieci rzecznej | km/km² | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | sum(L) / A mieści się w zakresie float64 | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - długość wszystkich cieków sieci podzielona przez powierzchnię zlewni, km/km²; sieć z NMT zależy od progowej powierzchni zlewni cieku, a sieć z mapy od jej skali, więc wartości można porównywać tylko przy tej samej metodzie
>
> **Zgodność z obserwacjami według źródeł:** brak: stosunek wielkości mierzonych; Baścik (2006) zauważa, że silnie zależy on od skali mapy i od progu wydzielania cieku
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) <https://doi.org/10.1029/TR038i006p00913>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, segments of 0.7 to 3.0 km, 12.7 km in all
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
>
> Funkcja `hydrolog.network.stream_order.drainage_density`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:drainage_density -->

<!-- spec:stream_frequency -->

<a id="spec-stream_frequency"></a>

> **Wskaźnik częstości cieków: liczba cieków podzielona przez powierzchnię zlewni** · specyfikacja [`stream_frequency`](../FORMULAS.md#stream_frequency) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> F_s = \frac{\sum_u N_u}{A}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\sum N_u$ | `n_streams` (liczba całkowita) | Liczba cieków wszystkich rzędów według Strahlera | – | [0; ∞) | nie podano w źródłach | [1; 8] (źr. 3) |
> | $A$ | `area_km2` | Powierzchnia zlewni w rzucie poziomym | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $F_s$ | `stream_frequency` | Wskaźnik częstości cieków | 1/km² | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | sum(N_u) / A mieści się w zakresie float64 | `within_float64` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - cieki według Strahlera wszystkich rzędów (`StreamNetwork.n_streams`), a nie odcinki między węzłami; wskaźnik częstości cieków w Hydrografie liczy odcinki sieci BDOT10k i wyraźnie to zaznacza
>
> **Zgodność z obserwacjami według źródeł:** brak: stosunek wielkości zliczonych i zmierzonych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
> 2. Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) <https://doi.org/10.1029/TR038i006p00913>
> 3. Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 8 streams of orders 1-3
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
>
> Funkcja `hydrolog.network.stream_order.stream_frequency`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:stream_frequency -->

Gęstość sieci zależy silnie od tego, co uznano za ciek: na mapie od jej skali, w sieci z NMT od
progu powierzchni zlewni, od którego komórka staje się ciekiem (Baścik 2006). Wartości porównuje
się więc tylko przy tej samej metodzie; przykład niżej pokazuje, jak duża jest ta zależność.

**Typowe błędy.** Liczenie odcinków zamiast cieków: program GIS dzieli sieć w każdym węźle, a
liczba odcinków rzędu 2 i wyższych jest większa od liczby cieków, co zaniża wskaźnik bifurkacji i
średnie długości. Hydrolog do wersji 0.8.1 włącznie liczył właśnie odcinki; wersja rozwojowa
0.9.0 liczy cieki Strahlera i odrzuca liczby cieków, których żadna sieć nie może mieć (warunek
w ramce wskaźnika bifurkacji). Inne błędy: wskaźniki Hortona dla magnitud Shreve'a; porównywanie
gęstości sieci z map w różnych skalach albo z NMT przy różnych progach.

### Przykład: sieć Kamiennika z NMT i z mapy

Sieć z NMT zbudowano z kierunków odpływu D8 i akumulacji przepływu Hydrografu (przebieg z
17 listopada 2026 r. na NMT GUGiK o oczku 5 m): ciekiem jest każda komórka zlewni, do której
spływa woda z co najmniej progowej powierzchni. Odcinek biegnie od źródła albo od węzła do
komórki poprzedzającej następny węzeł; jego długość to suma kroków D8 (5 m wzdłuż boku komórki,
$5\sqrt{2}$ m po przekątnej). Dla dwóch progów, 1 km² i 0,1 km², odcinki zapisano w plikach CSV
w formacie polecenia `network stats` (kolumny `segment_id`, `upstream_ids`, `length_km`):
[`dane/kamiennik_siec_1km2.csv`](dane/kamiennik_siec_1km2.csv) (17 odcinków) i
[`dane/kamiennik_siec_0_1km2.csv`](dane/kamiennik_siec_0_1km2.csv) (209 odcinków).

```bash
hydrolog network stats --segments-file docs/podrecznik/dane/kamiennik_siec_1km2.csv --method strahler --area-km2 37.22
```

```text
  method:                   strahler
  n_segments:               17
  stream_frequency_per_km2: 0.322407
  statistics:
    max_order:              3
    segment_counts:
      1: 9
      2: 2
      3: 1
    total_lengths_km:
      1: 16.3304
      2: 8.0472
      3: 4.7777
    mean_lengths_km:
      1: 1.81449
      2: 4.0236
      3: 4.7777
    bifurcation_ratios:
      1: 4.5
      2: 2
    length_ratios:
      1: 2.21748
      2: 1.18742
    total_stream_length_km: 29.1553
    drainage_density:       0.783323
```

Siedemnaście odcinków tworzy dwanaście cieków Strahlera: dziewięć rzędu 1, dwa rzędu 2 i jeden
rzędu 3 (pole `segment_counts` wyniku podaje liczby cieków, nie odcinków). To samo polecenie z
plikiem `kamiennik_siec_0_1km2.csv` daje sieć rzędu 4. Zestawienie obu sieci:

| Wielkość | próg 1 km² | próg 0,1 km² |
|---|---|---|
| odcinki | 17 | 209 |
| cieki rzędów 1, 2, 3, 4 | 9, 2, 1, – | 105, 22, 4, 1 |
| średnie długości cieków rzędów 1–4 [km] | 1,814; 4,024; 4,778; – | 0,360; 0,847; 2,581; 11,213 |
| wskaźniki bifurkacji 1→2, 2→3, 3→4 | 4,5; 2,0; – | 4,77; 5,50; 4,00 |
| wskaźniki długości 1→2, 2→3, 3→4 | 2,217; 1,187; – | 2,350; 3,047; 4,345 |
| łączna długość cieków [km] | 29,155 | 78,017 |
| gęstość sieci [km/km²] | 0,783 | 2,096 |
| częstość cieków [1/km²] | 0,322 | 3,546 |

Ta sama zlewnia ma więc gęstość sieci 0,78 albo 2,10 km/km² zależnie od progu, a rząd ujścia 3
albo 4. Przy progu 1 km² wskaźnik bifurkacji rzędu 2→3 (2,0) liczono z trzech cieków, dlatego
wyraźnie odstaje; przy progu 0,1 km² wskaźniki bifurkacji 4,0–5,5 są zbliżone do siebie, jak
przewidują prawa Hortona.

Magnitudy Shreve'a tych samych sieci:

```bash
hydrolog network stats --segments-file docs/podrecznik/dane/kamiennik_siec_1km2.csv --method shreve --area-km2 37.22
```

Odcinek ujściowy ma magnitudę 9 przy progu 1 km² i 105 przy progu 0,1 km², czyli tyle, ile sieć
ma źródeł; wskaźników Hortona wynik nie zawiera.

Na mapie topograficznej baza BDOT10k (warstwa rzek i strumieni `OT_SWRS_L`) ma wewnątrz zlewni
28,9 km cieków: Kamiennik (12,7 km), Czerwieniec (9,7 km) i cieki bez nazwy (6,5 km). Rowy
melioracyjne (`OT_SWRM_L`) to dalsze 58,8 km.

```python
from hydrolog.network.stream_order import drainage_density

print(round(drainage_density(28.885, 37.22), 3), round(drainage_density(28.885 + 58.842, 37.22), 3))
# 0.776 2.357
```

Gęstość sieci rzek i strumieni z mapy (0,776 km/km²) jest bliska gęstości sieci z NMT przy
progu 1 km² (0,783 km/km²); z rowami rośnie do 2,357 km/km², więcej niż sieć z NMT przy progu
0,1 km². Która z tych liczb jest „gęstością sieci Kamiennika”, zależy od pytania: do porównań z
literaturą potrzebna jest ta sama mapa albo ten sam próg co w porównywanych pracach.

## 1.9. Karta zlewni Kamiennika

| Charakterystyka | Wartość | Skąd |
|---|---|---|
| powierzchnia | 37,22 km² | Hydrograf, plik przykładu |
| obwód | 40,89 km (granica wygładzona); 51,12 km (granica z komórek) | Hydrograf; granica zlewni |
| długość: najdłuższa droga spływu; w linii prostej | 16,05 km; 10,88 km | Hydrograf; granica zlewni |
| średnia szerokość | 2,32 km | `morphometry watershed` |
| wskaźnik formy; wydłużenia; lemniskaty | 0,1445; 0,4289; 5,436 | `morphometry watershed` |
| wskaźnik zwartości; kolistości | 1,891; 0,2797 | `morphometry watershed` |
| wysokości: najniższa, najwyższa, średnia | 257,3; 475,1; 363,2 m n.p.m. | Hydrograf, plik przykładu |
| deniwelacja; wskaźnik rzeźby | 217,8 m; 0,0136 m/m | `morphometry watershed` |
| spadek najdłuższej drogi spływu: między końcami; wyrównany | 0,0114 m/m; 0,00848 m/m | Hydrograf; `equal_area_slope` |
| całka hipsometryczna; wysokość środkowa | 0,4817; 367,6 m n.p.m. | `HypsometricCurve`, NMT GUGiK |
| gęstość sieci: NMT próg 1 km²; 0,1 km²; BDOT10k rzeki i strumienie | 0,783; 2,096; 0,776 km/km² | `network stats`, `drainage_density` |
| rząd Strahlera ujścia (NMT próg 1 km²; 0,1 km²) | 3; 4 | `network stats` |

## Źródła

- Baścik M. (2006). Parametry fizjograficzne. W: Pociask-Karteczka J. (red.), *Zlewnia.
  Właściwości i procesy*. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, s. 21–34.
  https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content
- Barbosa Jr. A.R. (2004). *Hidrologia Aplicada CIV 226. Bacia Hidrográfica*. Universidade
  Federal de Ouro Preto, notatki do wykładu, rozdz. 3.4.4.
  https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/17403/material/Cap2%20-%20Bacia%20Hidrografica_UFOP.pdf
- Bendjoudi H., Hubert P. (2002). Le coefficient de compacité de Gravelius : analyse critique
  d'un indice de forme des bassins versants. *Hydrological Sciences Journal* 47(6), 921–930.
  https://doi.org/10.1080/02626660209493000
- GUGiK. Numeryczny model terenu (oczko 5 m, PL-1992, EVRF2007) i Baza Danych Obiektów
  Topograficznych BDOT10k, zasób Głównego Urzędu Geodezji i Kartografii, pobrane przez Hydrograf
  w październiku i listopadzie 2026 r.; dane przetworzone.
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych*, załącznik 2
  do OPZ (wersja ujednolicona), s. 97.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Ministry of Works and Development, Water and Soil Division (1980). *A method for estimating
  design peak discharge*. Technical Memorandum No. 61, Wellington, aneks A, s. 12–13.
  https://web.archive.org/web/20170228021947/http://docs.niwa.co.nz/library/public/TM61_1980.pdf
- Strahler A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography.
  *Geological Society of America Bulletin* 63, 1117–1142 (kopia artykułu:
  https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html).
- Wartalska K. *Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące
  zlewnię*. Politechnika Wrocławska, materiały dydaktyczne.
- Hydrolog: ADR-0053 (spadek wyrównany jako $J_g$ metody Lutza), ADR-0065 (wskaźniki
  morfometryczne i sieci w specyfikacjach), `docs/decisions/` w repozytorium.

Cytowane za źródłami wtórnymi (oryginałów nie otwierano; nie wszystkie są w otwartym dostępie):
Chorley R.J., Malm D.E.G., Pogorzelski H.A. (1957), *American Journal of Science* 255, 138–141;
Gravelius H. (1914), *Flusskunde*; Horton R.E. (1932), *Transactions AGU* 13, 350–361; Horton R.E.
(1945), *GSA Bulletin* 56; Miller V.C. (1953), Columbia University, Technical Report 3;
Pike R.J., Wilson S.E. (1971), *GSA Bulletin* 82, 1079–1084; Schumm S.A. (1956), *GSA Bulletin*
67, 597–646; Shreve R.L. (1966), *Journal of Geology* 74; Strahler A.N. (1957),
*Transactions AGU* 38(6), 913–920; Strahler A.N. (1964), w: Chow V.T. (red.), *Handbook of
Applied Hydrology*, rozdz. 4-II.
