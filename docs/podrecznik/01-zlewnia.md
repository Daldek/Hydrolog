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

**Obwód** $P$ to długość działu wodnego. Ma on cechę, o której łatwo zapomnieć: dział wodny jest
nieregularny w każdej skali, więc jego zmierzona długość rośnie wraz ze szczegółowością mapy lub
NMT (Bendjoudi i Hubert 2002, s. 924–928). Ta sama zlewnia ma inny obwód na mapie 1:50 000, inny
na granicy złożonej ze schodków komórek NMT i jeszcze inny na granicy wygładzonej. Wskaźniki
zależne od obwodu wolno więc porównywać tylko między zlewniami wyznaczonymi tą samą metodą.

**Długość zlewni** $L$ ma w literaturze co najmniej trzy definicje:

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

**Średnia szerokość** zlewni to szerokość prostokąta o powierzchni i długości zlewni. Hydrolog
podaje ją jako `width_km`; Baścik (2006, s. 21) dzieli przez długość doliny $L_m$.

<!-- spec:mean_width -->
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
<!-- /spec:compactness_coefficient -->

### Wskaźnik kolistości Millera

Wskaźnik kolistości (ang. *circularity ratio*) to stosunek powierzchni zlewni do powierzchni
koła o obwodzie równym obwodowi zlewni (Miller 1953, cytowany za Baścik 2006, wzór 1.2.3). Niesie
tę samą informację co wskaźnik Graveliusa (jest odwrotnością jego kwadratu), tylko w skali, w
której koło ma wartość największą.

<!-- spec:circularity_ratio -->
<!-- /spec:circularity_ratio -->

### Wskaźnik wydłużenia Schumma

Wskaźnik wydłużenia (ang. *elongation ratio*) to stosunek średnicy koła o powierzchni zlewni do
długości zlewni (Schumm 1956, za Baścik 2006, wzór 1.2.2, gdzie w mianowniku stoi długość doliny
$L_m$). Im mniejszy, tym zlewnia bardziej wydłużona.

<!-- spec:elongation_ratio -->
<!-- /spec:elongation_ratio -->

### Wskaźnik lemniskaty Chorleya

Chorley, Malm i Pogorzelski (1957, cytowani za Bendjoudi i Hubert 2002, wzory 3–5) porównali
zlewnię z jedną pętlą lemniskaty (krzywej o kształcie płatka). Wskaźnik $k$ (ang. *lemniscate
ratio*) to stosunek powierzchni koła o średnicy $L$ do powierzchni zlewni: rośnie, gdy zlewnia
się wydłuża. W części literatury przeglądowej spotyka się wariant bez $\pi$, który daje wartości
$\pi$ razy mniejsze; nie jest to wskaźnik Chorleya. Hydrolog do wersji 0.8.1 włącznie liczył
właśnie ten wariant; wersja rozwojowa 0.9.0 liczy wskaźnik Chorleya, tak jak Hydrograf.

<!-- spec:lemniscate_ratio -->
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
<!-- /spec:midpoint_elevation -->

**Wskaźnik rzeźby** (ang. *relief ratio*; Schumm 1956, „wskaźnik rzeźby” u Baścik 2006,
wzór 1.2.12) to deniwelacja zlewni podzielona przez jej długość: przeciętny spadek, jaki
miałaby zlewnia, gdyby opadała równomiernie od najwyższego punktu do przekroju. Hydrolog podaje
go bezwymiarowo (m/m), Baścik i Wartalska w m/km, czyli w promilach.

<!-- spec:relief_ratio -->
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
<!-- /spec:hypsometric_curve -->

**Całka hipsometryczna** HI (ang. *hypsometric integral*) to pole pod krzywą w tym kwadracie:
jaka część „bryły” między najniższym a najwyższym punktem jest jeszcze wypełniona terenem. Jest
równa ilorazowi wysokości średniej nad najniższym punktem i deniwelacji (wskaźnik Pike'a i
Wilsona 1971, ang. *elevation-relief ratio*; równość wynika wprost z definicji krzywej). Hydrolog
całkuje krzywą metodą trapezów na równo rozmieszczonych wysokościach względnych; różnicę względem
wartości dokładnej i jej granicę podaje ramka. Czy liczyć wartość dokładną, pozostaje otwartym
pytaniem ADR-0065.

<!-- spec:hypsometric_integral -->
<!-- /spec:hypsometric_integral -->

Krzywa daje też wysokości charakterystyczne: **wysokość średnią** (ważoną powierzchnią) i
**wysokość środkową** (medianę), powyżej której leży połowa powierzchni.

<!-- spec:area_weighted_mean_elevation -->
<!-- /spec:area_weighted_mean_elevation -->

<!-- spec:elevation_above_share -->
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

Sieć rzeczną opisuje się jako drzewo: **odcinki** (ang. *links*, *segments*) łączą **węzły**
(źródła, połączenia cieków i przekrój zamykający). **Ciek** w sensie Strahlera to ciąg odcinków
tego samego rzędu, od miejsca, w którym ten rząd powstał, do połączenia z ciekiem rzędu równego
lub wyższego.

**Rzędy Strahlera** (ang. *stream order*; Strahler 1957, za Baścik 2006, s. 28) zaczynają się od
cieków źródłowych, a rząd rośnie dopiero tam, gdzie łączą się cieki tego samego, najwyższego
rzędu; przy połączeniu cieków różnych rzędów ciek poniżej zachowuje rząd wyższego (reguła w
ramce). Dopływ niższego rzędu nie przerywa więc cieku: ciek rzędu 2, do którego wpada ciek rzędu
1, pozostaje jednym ciekiem rzędu 2, choć w programie GIS składa się z dwóch odcinków.

<!-- spec:strahler_order -->
<!-- /spec:strahler_order -->

**Magnitudy Shreve'a** (ang. *magnitude*; Shreve 1966, cytowany za źródłami wtórnymi) liczą
źródła: odcinek źródłowy ma magnitudę 1, a w każdym węźle magnitudy odcinków dopływających się
sumują. Magnituda odcinka ujściowego to liczba wszystkich źródeł sieci. Hydrolog nadaje magnitudy
poleceniem `network stats --method shreve`.

<!-- TODO spec: Shreve's magnitude of a link, the sum of the magnitudes of the links that join at its upper node, a source link having the smallest (Shreve 1966, after secondary sources); computed by network stats --method shreve -->

### Prawa Hortona

Horton (1945) i Strahler (1957) zauważyli, że w wielu sieciach liczby cieków kolejnych rzędów
maleją, a ich średnie długości rosną w przybliżeniu w postępie geometrycznym (prawa Hortona,
cytowane za Baścik 2006, wzory 1.2.18–1.2.22). Opisują to dwa stosunki: **wskaźnik bifurkacji**
(ang. *bifurcation ratio*), stosunek liczb cieków dwóch kolejnych rzędów, i **wskaźnik długości
cieków** (ang. *length ratio*), stosunek ich średnich długości. Oba są określone tylko dla rzędów
Strahlera; dla magnitud Shreve'a Hydrolog ich nie podaje.

<!-- spec:streams_of_each_order -->
<!-- /spec:streams_of_each_order -->

<!-- spec:bifurcation_ratio -->
<!-- /spec:bifurcation_ratio -->

<!-- spec:length_ratio -->
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
<!-- /spec:drainage_density -->

<!-- spec:stream_frequency -->
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
