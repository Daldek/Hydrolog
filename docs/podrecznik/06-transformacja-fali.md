# 6. Transformacja fali wezbraniowej

Rozdział 5 kończy się hydrogramem w przekroju zamykającym zlewnię. Ten rozdział opisuje, jak
wezbranie zmienia się, gdy płynie dalej korytem albo przechodzi przez zbiornik, oraz jak Hydrolog
łączy hydrogramy wielu zlewni w sieci rzecznej. **Transformacja fali wezbraniowej** (ang. *flood
routing*; w literaturze także trasowanie fali) to obliczenie hydrogramu odpływu z odcinka koryta lub
ze zbiornika na podstawie hydrogramu dopływu.

Hydrolog stosuje metody **hydrologiczne** (ang. *hydrologic routing*): łączą one równanie ciągłości
z zależnością retencji od przepływu i liczą tylko przepływ. Metody **hydrauliczne** rozwiązują
równania Saint-Venanta i dają także stany wody; służą do tego programy takie jak HEC-RAS (w
ekosystemie Nogat — Hydraulik). Żadna z metod tego rozdziału nie opisuje **cofki** (ang.
*backwater*), czyli wpływu wody poniżej odcinka (zbiornika, ujścia, zwężenia) na odpływ.

## 6.1. Retencja, spłaszczenie i opóźnienie

Podstawą wszystkich metod jest **równanie ciągłości**: zmiana objętości wody zgromadzonej w odcinku
lub zbiorniku (**retencji**, ang. *storage*) w czasie równa się różnicy dopływu i odpływu. W kroku
czasowym $\Delta t$ Hydrolog zapisuje je wzorem trapezów: średni dopływ w kroku minus średni odpływ
w kroku, razy $\Delta t$, to przyrost retencji (USDA-NRCS 2014, rozdz. 17). Metody różnią się tym,
jak wiążą retencję z dopływem i odpływem; wzory podają ramki kolejnych punktów.

Przejście przez odcinek lub zbiornik zmienia falę na dwa sposoby:

- **spłaszczenie** (tłumienie, ang. *attenuation*) — kulminacja maleje, a fala się wydłuża;
- **opóźnienie** (przesunięcie, translacja, ang. *translation*) — kulminacja przychodzi później.

Objętość fali się nie zmienia: metody nie uwzględniają strat (parowania, infiltracji w korycie) ani
dopływu bocznego, który dodaje się osobno jako zlewnię cząstkową (p. 6.8).

**Wspólne zasady Hydrologa** (ADR-0008). Hydrogram to tabela `time_min`, `discharge_m3s` o stałym
kroku, bez braków; Hydrolog niczego nie przepróbkowuje, a tabelę nieregularną odrzuca. Jednostki:
minuty, m³/s, m³ i km. Na początku odcinek jest w stanie ustalonym:

<!-- spec:routing_initial_state -->
<!-- /spec:routing_initial_state -->

Odpływ trwa dłużej niż dopływ, więc Hydrolog wydłuża oś czasu, utrzymując ostatnią wartość dopływu,
dopóki odpływ się nie ustali (uwaga `tail_extended`; gdy to się nie udaje — `tail_truncated`):

<!-- spec:routing_tail -->
<!-- /spec:routing_tail -->

Każdy wynik podaje objętość dopływu i odpływu, retencję na początku i na końcu oraz błąd bilansu:

<!-- spec:routing_volume_balance -->
<!-- /spec:routing_volume_balance -->

Błąd bilansu jest zerowy z dokładnością do zaokrągleń, chyba że schemat liczono na krokach
pośrednich albo jądrem dokładnym (kaskada, p. 6.6); wtedy jest to błąd całkowania metodą trapezów,
pomijalnie mały, gdy fala zaczyna się i kończy w spoczynku. Ostrzeżenia o dokładności są uwagami
wyniku, nigdy błędami.

### Przykład 6.1. Dopływ: hydrogram projektowy Kamiennika

Przykłady tego rozdziału przeprowadzają przez odcinek koryta i zbiornik hydrogram projektowy
Kamiennika w Świerzawie z rozdz. 5 (model SCS, czas koncentracji Kerby’ego–Kirpicha, maksymalny
opad o czasie trwania 12 h i prawdopodobieństwie przewyższenia 1 % z PMAXTP, 101,82 mm, hietogram
Beta, krok 10 min). Polecenie `route network` z siecią złożoną z jednej zlewni zapisuje ten
hydrogram w pliku `kamiennik/KAMIENNIK.csv`, który czytają wszystkie polecenia `route`:

```sh
hydrolog route network --network '{"schema":"hydrolog-network/1","name":"Kamiennik — Świerzawa, p = 1 %","timestep_min":10,"rainfall":{"kind":"design","hietogram_type":"beta","total_mm":101.82,"duration_min":720},"nodes":[{"id":"KAMIENNIK","type":"subcatchment","watershed":{"name":"Kamiennik — Świerzawa","area_km2":37.22,"cn":65,"flow_path_length_km":15.88,"flow_path_slope_m_per_m":0.0114,"overland_length_km":0.3,"overland_slope_m_per_m":0.082,"retardance":0.4},"runoff":{"model":"curve-number","tc_method":"kerby_kirpich","uh_model":"scs"}},{"id":"OUT","type":"outlet","from":["KAMIENNIK"]}]}' --nodes KAMIENNIK --output-dir kamiennik
```

Zlewnia sieci liczy hydrogram tą samą drogą co `hydrograph generate` (ADR-0012): kulminacja
52,36 m³/s po 410 min, objętość 977 269 m³, 138 rzędnych od 0 do 1370 min. Hydrogram zaczyna się od
zera, więc stan początkowy każdego odcinka to brak przepływu. Wysokość opadu pochodzi z PMAXTP:
„Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut
Badawczy. Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały
przetworzone”.

## 6.2. Przesunięcie w czasie

**Idea.** Najprostszy model: fala przechodzi przez odcinek bez zmiany kształtu, tylko później, o
czas $\tau$ (ang. *lag*). Retencja odcinka to woda „w drodze”.

<!-- spec:lag -->
<!-- /spec:lag -->

**Zastosowanie.** Krótkie odcinki o znanym czasie przepływu, na których spłaszczenie jest pomijalne
(HEC-HMS, model *Lag*). Gdy $\tau$ nie jest całkowitą wielokrotnością kroku, Hydrolog interpoluje
rzędne liniowo, co lekko ścina ostre kulminacje (uwaga `lag_interpolated`) — to spłaszczenie
numeryczne, nie fizyczne. **Odstępstwo od HEC-HMS** (ADR-0062): przed pierwszą rzędną Hydrolog
przyjmuje dopływ równy odpływowi początkowemu (stan ustalony), a HEC-HMS — bieżący dopływ.

### Przykład 6.2. Kamiennik na odcinku Kaczawy

Kamiennik uchodzi do Kaczawy w Świerzawie. Odcinek R8 sieci Hydrografa (p. 6.8) prowadzi Kaczawą od
ujścia Kamiennika (węzeł J7) do ujścia Wilczy (J8): 11,6591 km, spadek 4,258 ‰ z NMT. Aby pokazać
samą transformację, przepuszczamy przez ten odcinek wyłącznie falę Kamiennika. Czas przepływu fali
$L/c$ = 11 659 m / 3,351 m/s ≈ 58 min (prędkość fali z przykładu 6.5):

```sh
hydrolog route lag --lag-min 58 --input-file kamiennik/KAMIENNIK.csv
```

Kulminacja 52,345 m³/s przychodzi po 470 min, o 60 min później. Jest o 0,02 % niższa od kulminacji
dopływu tylko dlatego, że opóźnienie 58 min to 5,8 kroku i rzędne zostały zinterpolowane.

## 6.3. Metoda Muskingum

**Idea.** McCarthy (1938) opisał retencję odcinka jako sumę **retencji pryzmowej** (ang. *prism
storage*), proporcjonalnej do odpływu, i **retencji klinowej** (ang. *wedge storage*), dodatniej,
gdy fala narasta (dopływ większy od odpływu), i ujemnej, gdy opada. Parametrami są **stała retencji**
$K$ (ang. *storage constant*), w przybliżeniu czas przepływu fali przez odcinek, i **współczynnik
wagowy** $X$ (ang. *weighting factor*). Wstawienie tej retencji do równania ciągłości zapisanego
wzorem trapezów daje rekurencję o trzech wagach:

<!-- spec:muskingum -->
<!-- /spec:muskingum -->

Wagi sumują się do jedności, więc stan ustalony się utrzymuje. $X = 0$ to zbiornik liniowy
(największe spłaszczenie przy danym $K$), $X$ na górnej granicy zakresu — fala nietłumiona. Nazwy
wag różnią się w literaturze (ramka, konwencje): przed użyciem cudzych tabel trzeba sprawdzić, która
waga mnoży który przepływ.

**Pododcinki.** Długi odcinek dzieli się na $N$ jednakowych pododcinków (ang. *subreaches*) o stałej
$K/N$ i tym samym $X$, tak aby fala przechodziła przez pododcinek mniej więcej w jednym kroku
(HEC-HMS). Średnie opóźnienie odpowiedzi odcinka jest równe $K$ niezależnie od $N$, a rozrzut maleje
z $N$: więcej pododcinków — mniejsze spłaszczenie. Hydrolog dobiera $N$ tak:

<!-- spec:muskingum_subreaches -->
<!-- /spec:muskingum_subreaches -->

**Parametry.** $K$ i $X$ kalibruje się na parach zarejestrowanych hydrogramów dopływu i odpływu
albo szacuje: $K$ jako długość odcinka podzieloną przez prędkość fali (p. 6.4). USACE (1994) zaleca
$X$ bliższe zera dla rzek nizinnych z rozległą terasą zalewową, a bliższe górnej granicy dla rzek o
dobrze wykształconym korycie. Parametry skalibrowane na jednym wezbraniu nie muszą pasować do
innego, bo prędkość fali zależy od przepływu: Baláž i in. (2010) dla 34,76 km dolnej Morawy uzyskali
średni współczynnik Nasha–Sutcliffe’a 0,9735 przy $K$ i $X$ kalibrowanych osobno dla każdej z sześciu
fal i 0,9582 przy parametrach uśrednionych. Spłaszczenie zależy od $K$, $X$ **i** $N$: te same $K$ i
$X$ przy innej liczbie pododcinków dają inny wynik.

### Przykład 6.3. Muskingum na odcinku R8

$K$ = 58 min ($L/c$), $X$ = 0,2 — wartość często przyjmowana dla rzek naturalnych, gdy brak
kalibracji (Baláž i in. 2010):

```sh
hydrolog route muskingum --k-min 58 --x 0.2 --input-file kamiennik/KAMIENNIK.csv
```

Hydrolog przyjmuje $N$ = 6 pododcinków (dopuszczalne 3–9), wagi pododcinka 0,2408 (dopływ bieżący),
0,5445 (dopływ poprzedni) i 0,2147 (odpływ poprzedni). Kulminacja odpływu wynosi 51,82 m³/s po
470 min, o 1,04 % mniej niż dopływu. Dla $X$ = 0 (polecenie z `--x 0`) — 51,44 m³/s (−1,75 %).
Przykład 6.5 pokazuje, że na tym odcinku oba wyniki zawyżają spłaszczenie.

## 6.4. Przekrój koryta, wzór Manninga i prędkość fali

Metoda Muskingum–Cunge potrzebuje **prędkości fali** $c$ (ang. *celerity*) i **szerokości
zwierciadła** $T$ (ang. *top width*) przy przepływie odniesienia. Dla koryta pryzmatycznego
(prostokąt, trapez, trójkąt) Hydrolog liczy je ze wzoru Manninga przy **głębokości normalnej**
(ang. *normal depth*), w ruchu jednostajnym:

<!-- spec:manning_normal_flow -->
<!-- /spec:manning_normal_flow -->

Prędkość fali to prędkość, z jaką wzdłuż koryta przesuwa się dany przepływ; jest większa od średniej
prędkości wody $V = Q/A$. **Odstępstwo od NEH 630** (ADR-0062): Hydrolog liczy lokalną pochodną
$dQ/dA$ przekroju (HEC-HMS), a NEH dla tabeli z HEC-RAS — wykładnik krzywej natężenia uśredniony
z wagą przepływu; w przykładzie 17-4 NEH różnica wynosi 2 %. Współczynnik szorstkości $n$ dobiera
się z tablic i fotografii koryt wzorcowych (Arcement i Schneider 1989).

**Typowe błędy.** Przekrój samego koryta przy przepływie pozakorytowym: po wyjściu wody na terasę
zalewową prędkość fali spada, więc $c$ z przekroju koryta głównego jest wtedy zawyżona — $c$ i $T$
trzeba wziąć z modelu hydraulicznego (polecenie przyjmuje je wprost). Pomylenie wzoru anglosaskiego,
który zawiera czynnik przeliczeniowy (ramka, konwencje), z wzorem w jednostkach SI.

### Przykład 6.4. Przekrój odcinka R8

Hydrograf podaje długość i spadek odcinka, ale nie jego przekrój. Do przykładów przyjęto trapez o
szerokości dna 10 m, skarpach 1:1,5 i $n$ = 0,035. Przy przepływie 52,36 m³/s funkcja `normal_flow`
biblioteki (polecenie `route muskingum-cunge` podaje z niej $c$ i $T$) daje:

```python
from hydrolog.routing.formulas.manning import normal_flow

print(normal_flow(52.356786579415235, 0.004258, 10.0, 1.5, 0.035))
# NormalFlow(depth_m=1.78776..., area_m2=22.6717..., top_width_m=15.3632..., velocity_m_per_s=2.30933..., celerity_m_per_s=3.35079...)
```

Głębokość normalna wynosi 1,79 m, pole przekroju 22,67 m², szerokość zwierciadła 15,36 m, prędkość
wody 2,31 m/s, a prędkość fali 3,35 m/s — 1,45 raza większa.

## 6.5. Metoda Muskingum–Cunge

**Idea.** Cunge (1969) zauważył, że schemat Muskingum jest przybliżeniem równania fali
kinematycznej, a spłaszczenie, które daje, to **dyfuzja numeryczna** (ang. *numerical diffusion*)
schematu. Dobierając $K$ i $X$ tak, aby dyfuzja numeryczna była równa fizycznej dyfuzji fali
(równanie fali dyfuzyjnej), otrzymuje się parametry z danych o korycie, bez kalibracji. Długość
$D$ w ramce to **długość dyfuzji** (charakterystyczna) odcinka: im dłuższa wobec kroku drogi, tym
silniej fala się rozmywa. $X$ może tu być ujemne — w tej metodzie to nie „waga”, tylko parametr
dopasowania dyfuzji.

<!-- spec:muskingum_cunge -->
<!-- /spec:muskingum_cunge -->

**Siatka.** Odcinek dzieli się na $N$ równych **kroków drogi** (ang. *distance steps*) $\Delta x$;
NRCS podaje krok drogi zależny od $c\,\Delta t$ i $D$ (USDA-NRCS 2014, wzór 17-21). Hydrolog bierze
liczbę kroków NRCS albo najbliższą, przy której wszystkie wagi są nieujemne (uwaga
`subreaches_adjusted`):

<!-- spec:muskingum_cunge_grid -->
<!-- /spec:muskingum_cunge_grid -->

NEH 630 wymaga też odpowiedniej liczby kroków czasowych na wznoszącej gałęzi hydrogramu; krótszą
gałąź Hydrolog zagęszcza krokami pośrednimi (uwaga `timestep_refined`):

<!-- spec:muskingum_cunge_rise -->
<!-- /spec:muskingum_cunge_rise -->

**Liczby bezwymiarowe.** Wynik podaje **liczbę Couranta** $C_g$ (ang. *Courant number*) i
**siatkową liczbę Reynoldsa** $D_g$ (ang. *grid Reynolds number*) oraz granicę dokładności NRCS,
wyznaczoną empirycznie na 140 testowych obliczeniach (USDA-NRCS 2014, dodatek 17B). Każda siatka o
nieujemnych wagach mieści się w tej granicy (ADR-0008), więc uwaga `accuracy_limit` oznacza tylko,
że Hydrolog zastąpił siatkę NRCS inną.

**Przepływ odniesienia** to domyślnie kulminacja dopływu (NRCS); USACE (1994) zaleca przepływ
bazowy plus połowę przyrostu do kulminacji, bo kulminacja zawyża prędkość fali, a przepływ bazowy ją
zaniża. Można go podać opcją `--reference-discharge-m3s`.

**Odstępstwa od NEH 630** (ADR-0062, konwencje ramki): Hydrolog liczy tylko na siatkach o
nieujemnych wagach, choć NEH dopuszcza ujemną wagę (przykład 17-5; tam wynik Hydrologu leży między
wynikiem NEH a rozwiązaniem nieustalonym HEC-RAS), przyjmuje jeden przepływ odniesienia dla
wszystkich kroków drogi, a współczynniki są stałe przez całą falę.

**Zakres stosowania.** Fale dyfuzyjne bez cofki, w korycie pryzmatycznym o jednym spadku (założenia
ramki). Według USACE (1994) metoda odbiega od rozwiązania pełnego dla fal bardzo szybko
narastających na odcinkach o bardzo małym spadku; Ponce (online, wykłady CIVE 445) podaje
kryterium fali dyfuzyjnej zależne od czasu wznoszenia, spadku i głębokości. Hydrolog nie wydaje
dziś uwagi o tym kryterium — to otwarte pytanie autora (ADR-0062).

### Przykład 6.5. Muskingum–Cunge na odcinku R8

```sh
hydrolog route muskingum-cunge --length-km 11.6591 --slope-m-per-m 0.004258 --manning-n 0.035 --bottom-width-m 10 --side-slope-m-per-m 1.5 --input-file kamiennik/KAMIENNIK.csv
```

| Wielkość | Wartość |
|---|---|
| przepływ odniesienia (kulminacja dopływu) | 52,36 m³/s |
| prędkość fali $c$, szerokość zwierciadła $T$ | 3,351 m/s; 15,36 m |
| krok drogi NRCS → przyjęty | 1124,7 m (11 kroków) → 1943,2 m (6 kroków) |
| $K$ odcinka, $X$ | 57,99 min; 0,439 |
| wagi kroku drogi (dopływ bieżący, dopływ poprzedni, odpływ poprzedni) | 0,0730; 0,8861; 0,0409 |
| $C_g$, $D_g$, granica NRCS | 1,035; 0,123; 10,8 |
| kulminacja odpływu | 52,26 m³/s po 470 min (−0,19 %, opóźnienie 60 min) |

Długość dyfuzji $D = D_g\,\Delta x$ ≈ 239 m jest krótka wobec 11,66 km odcinka, a $X$ bliskie górnej
granicy: na stromym odcinku Kaczawy fala Kamiennika, narastająca przez kilka godzin, prawie się nie
spłaszcza, tylko przesuwa o godzinę. Muskingum z „typowym” $X$ = 0,2 (przykład 6.3) dał pięć razy
większe spłaszczenie. Gdy brak danych do kalibracji, parametry z fizyki koryta są bezpieczniejsze od
wartości przyjętych z podręcznika.

### Przykład 6.6. Sprawdzenie na przykładzie 17-4 z NEH 630

Plik `tests/fixtures/neh17_4_inflow.csv` zawiera dopływ przykładu 17-4 NEH 630 w jednostkach SI
(odcinek 2600 ft = 792,48 m, spadek 0,00091, krok 0,1 h; przepływ odniesienia 684,18 ft³/s, prędkość
fali 4,297 ft/s i szerokość zwierciadła 44,6 ft podane w źródle):

```sh
hydrolog route muskingum-cunge --length-km 0.79248 --slope-m-per-m 0.00091 --celerity-m-per-s 1.3097256 --top-width-m 13.59408 --reference-discharge-m3s 19.374 --input-file tests/fixtures/neh17_4_inflow.csv
```

Hydrolog liczy jeden krok drogi o $K$ = 10,08 min (605,1 s), $X$ = −0,254, $C_g$ = 0,595,
$D_g$ = 1,509 i granicy NRCS 3,93 — jak NEH. Kulminacja odpływu 18,287 m³/s (645,78 ft³/s) po
786 min (13,1 h) odpowiada 645,72 ft³/s o 13,1 h w NEH; HEC-RAS (model nieustalony) daje według NEH
647 ft³/s.

## 6.6. Kaskada zbiorników liniowych

**Idea.** Odcinek (albo zlewnia, rozdz. 5) jako $n$ jednakowych **zbiorników liniowych** połączonych
szeregowo, każdy o retencji proporcjonalnej do odpływu przez stałą $K$. Odpowiedzią na impuls jest
rozkład gamma (Nash 1957), o średnim opóźnieniu $nK$ i wariancji $nK^2$; $n$ nie musi być
całkowite. Przy stałym $nK$ spłaszczenie rośnie, gdy $n$ maleje; bardzo duże $n$ to prawie czyste
przesunięcie.

<!-- spec:linear_reservoir_cascade -->
<!-- /spec:linear_reservoir_cascade -->

Stałą $K$ podaje się wprost albo z długości odcinka i prędkości fali:

<!-- spec:cascade_time_scale -->
<!-- /spec:cascade_time_scale -->

**Metoda Kalinina–Milukowa** to ta sama kaskada z liczbą zbiorników równą stosunkowi długości odcinka
do długości charakterystycznej, czyli długości dyfuzji $D$ z p. 6.5 (Ponce, online). Kaskada ma wtedy
ten sam średni czas przepływu i ten sam rozrzut co fala dyfuzyjna, więc daje wynik bliski metodzie
Muskingum–Cunge.

**Brak warunku stabilności.** Hydrolog liczy odpływ kaskady jako dokładną odpowiedź na dopływ
zmieniający się liniowo między rzędnymi (niepełna funkcja gamma), a nie rekurencją. Dlatego każdy
krok czasowy jest dozwolony: kaskada nie ma okna wag, pododcinków ani kroków pośrednich. Opublikowanej
tabeli obliczeń kaskadą nie ma w źródłach otwartych; specyfikacja ma status `oracle only` i jest
sprawdzana rozwiązaniami ścisłymi.

**Typowe błędy.** Mylenie $K$ jednego zbiornika z czasem opóźnienia całego odcinka ($nK$) oraz
utożsamianie $nK$ (środka ciężkości odpowiedzi) z opóźnieniem kulminacji.

### Przykład 6.7. Kaskada na odcinku R8

Długość dyfuzji odcinka R8 wynosi około 239 m (przykład 6.5), więc według Kalinina–Milukowa $n$ =
11 659 / 239 ≈ 48,8, a czas przepływu $nK$ = $L/c$:

```sh
hydrolog route cascade --n 48.8 --length-km 11.6591 --celerity-m-per-s 3.351 --input-file kamiennik/KAMIENNIK.csv
```

Hydrolog liczy $K$ = 1,188 min, a kulminację odpływu 52,23 m³/s po 470 min (−0,24 %) — prawie tyle
co Muskingum–Cunge. Jeden zbiornik o tym samym czasie przepływu (`--n 1`, $K$ = 57,99 min) daje
47,76 m³/s, o 8,8 % mniej: przeszacowuje spłaszczenie, bo jego rozrzut jest kilkadziesiąt razy
większy od rozrzutu fali dyfuzyjnej. Błąd bilansu wynosi tu 0,016 m³ przy 977 269 m³ — to błąd
całkowania metodą trapezów (p. 6.1).

## 6.7. Zbiornik: metoda Pulsa

**Idea.** W zbiorniku, stawie, polderze lub odcinku, w którym zwierciadło jest prawie poziome,
retencja jest jednoznaczną funkcją odpływu (bez pętli histerezy). Jedynym parametrem jest wtedy
tabela pojemność–odpływ (opcjonalnie z rzędną zwierciadła). Równanie ciągłości przekształca się
tak, by niewiadome — retencja i odpływ na końcu kroku — były po jednej stronie, a odpływ odczytuje
się z **krzywej roboczej** zbudowanej z tabeli: to **metoda Pulsa** w odmianie *storage indication*
(ang. *level pool routing*, *modified Puls*; USDA-NRCS 2014, rozdz. 17; HEC-HMS).

<!-- spec:level_pool -->
<!-- /spec:level_pool -->

**Krok obliczeń.** NRCS wymaga, by krzywa robocza leżała po właściwej stronie linii równych wartości
dla całej tabeli (USDA-NRCS 2014, s. 17-11). Hydrolog stosuje warunek ostrzejszy, na każdym odcinku
tabeli osiąganym przez falę (ADR-0008, ADR-0062): przy załamaniu krzywej odpływu, np. tuż po
przelaniu się wody przez próg przelewu, warunek NRCS przepuszcza krok, przy którym odpływ przekracza
kulminację dopływu. Dłuższy krok Hydrolog dzieli na części (uwaga `timestep_refined`):

<!-- spec:level_pool_substeps -->
<!-- /spec:level_pool_substeps -->

**Zakres tabeli.** Hydrolog nigdy nie ekstrapoluje tabeli: fala, która napełnia zbiornik ponad
ostatni wiersz albo opróżnia go poniżej pierwszego, kończy obliczenie błędem (`table_exceeded`,
`table_emptied`). Pojemność poniżej progu bez odpływu (pojemność martwa) jest dozwolona — zbiornik
stoi wtedy na początku pełny do progu.

**Typowe błędy.** Tabela, która nie obejmuje całej fali; pojemność martwa liczona jako czynna; krok
zbyt długi wobec stromego odcinka krzywej odpływu.

### Przykład 6.8. Hipotetyczny suchy zbiornik na Kamienniku

Przyjmijmy suchy zbiornik przeciwpowodziowy na Kamienniku tuż powyżej Świerzawy, z upustem dennym i
przelewem o progu 6 m nad dnem. Tabelę pojemność–odpływ przyjęto do przykładu (nie opisuje
rzeczywistego obiektu):

| Rzędna nad dnem [m] | 0 | 0,5 | 1 | 2 | 3 | 4 | 5 | 6 | 6,5 | 7 | 7,5 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pojemność [tys. m³] | 0 | 15 | 35 | 90 | 165 | 260 | 375 | 510 | 585 | 665 | 750 | 840 | 1035 |
| Odpływ [m³/s] | 0 | 2,47 | 3,50 | 4,95 | 6,06 | 7,00 | 7,83 | 8,57 | 17,94 | 34,76 | 56,43 | 82,02 | 143,00 |

```sh
hydrolog route level-pool --storage-m3 0,15000,35000,90000,165000,260000,375000,510000,585000,665000,750000,840000,1035000 --outflow-m3s 0,2.47,3.5,4.95,6.06,7,7.83,8.57,17.94,34.76,56.43,82.02,143 --stage-m 0,0.5,1,2,3,4,5,6,6.5,7,7.5,8,9 --input-file kamiennik/KAMIENNIK.csv
```

Kulminacja odpływu wynosi 24,67 m³/s po 590 min — o 52,9 % mniej niż dopływu i o 3 h później. Woda
wznosi się do 6,70 m, 0,70 m ponad próg przelewu, a zbiornik gromadzi najwyżej 616 985 m³. Kulminacja
odpływu leży na opadającej gałęzi dopływu, w chwili, gdy dopływ spadł do wartości odpływu (24,71 m³/s
po 590 min): w zbiorniku o poziomym zwierciadle retencja i odpływ są największe właśnie wtedy.
Najdłuższy krok, na jaki pozwala ta tabela, to 130,7 min, więc krok 10 min nie wymaga podziału.
Zbiornik opróżnia się długo: oś czasu wydłużono o 1210 min po końcu dopływu (uwaga `tail_extended`).

## 6.8. Sieć rzeczna

Hydrolog składa obliczenia zlewni (rozdz. 5) i transformacji w **sieć** (ADR-0010, ADR-0012):
dokument `hydrolog-network/1` z węzłami pięciu typów. **Zlewnia cząstkowa** (`subcatchment`) ma
gotowy hydrogram albo liczy go z opadu metodą SCS-CN i hydrogramem jednostkowym, **odcinek**
(`reach`) przeprowadza hydrogram węzła powyżej jedną z metod tego rozdziału, **zbiornik**
(`reservoir`) — metodą Pulsa, **węzeł** (`junction`) sumuje dopływające hydrogramy, a **wylot**
(`outlet`) daje wynik. Cała sieć ma jeden krok czasowy i nic nie jest przepróbkowywane:

<!-- spec:junction_sum -->
<!-- /spec:junction_sum -->

**Liniowość.** Dla metod liniowych — przesunięcia, Muskingum, kaskady, a także Muskingum–Cunge z
podanym przepływem odniesienia — suma przetransformowanych hydrogramów równa się przetransformowanej
sumie. Zbiornik i Muskingum–Cunge z przepływem odniesienia z kulminacji dopływu są nieliniowe:
kolejność sumowania i transformacji zmienia wtedy wynik.

### Przykład 6.9. Sieć do punktu A: Nysa Szalona i Kaczawa

Hydrograf wyznaczył sieć zlewni do punktu A (51,15636° N, 16,07643° E): 18 zlewni o łącznej
powierzchni 747,3 km², 9 odcinków o długościach i spadkach z NMT, 9 węzłów; jedna gałąź to Nysa
Szalona, druga — Kaczawa z dopływami, w tym z Kamiennikiem (zlewnia Z15, 37,23 km²; w tym
przekazaniu CN = 61,2 i inne charakterystyki niż w rozdz. 5, stąd niższa kulminacja). Przekazanie
zapisano w pliku `tests/fixtures/handoff_hydrograf_network_nysa_szalona.json`. Do przykładu dodano
(plik `docs/podrecznik/dane/nysa_szalona_siec.json`): opad projektowy Kamiennika jednakowy w całej
sieci, przekrój każdego odcinka jak w przykładzie 6.4, współczynnik Kerby’ego $N$ = 0,4 i czas
koncentracji metodą Kerby’ego–Kirpicha w każdej zlewni.

```sh
hydrolog route network --network-file docs/podrecznik/dane/nysa_szalona_siec.json --nodes OUT --output-dir siec
```

| Węzeł | Opis | Kulminacja [m³/s] | Czas kulminacji [min] |
|---|---|---|---|
| Z15 | zlewnia Kamiennika | 42,64 | 420 |
| J7 | Kaczawa poniżej ujścia Kamiennika | 157,83 | 400 |
| R8 | koniec odcinka R8 (11,66 km) | 157,52 | 450 |
| J8 | Kaczawa poniżej ujścia Wilczy | 265,14 | 430 |
| R9 | koniec odcinka R9 (23,36 km) | 263,25 | 520 |
| J5 | Nysa Szalona, punkt P1 | 610,58 | 540 |
| OUT | punkt A | 1011,67 | 530 |

Objętość fali w punkcie A wynosi 22 408 503 m³, tyle co suma objętości 18 zlewni: transformacja
zachowuje objętość. Odcinki na tych stromych rzekach spłaszczają kulminacje o ułamki procenta i
opóźniają je o 0–90 min. Suma kulminacji wszystkich zlewni wynosi 1092,8 m³/s, a kulminacja w
punkcie A — 1011,67 m³/s: 7 % mniej, głównie dlatego, że kulminacje zlewni przychodzą w różnych
chwilach (od 310 do 570 min), a nie z powodu spłaszczenia w korytach.

Uwagi wyniku warto przeczytać: dla odcinków R5 (7,1 m), R6 i R7 Hydrolog podzielił krok na kroki
pośrednie (`substeps_added`), dla pięciu odcinków zmienił liczbę kroków drogi NRCS
(`subreaches_adjusted`), a dla wielu zlewni zgłosił wartości spoza zakresów typowych wzorów
(`outside_typical_range`), np. powierzchnię większą niż zalecana dla hydrogramu SCS. Wynik nie jest
przepływem o prawdopodobieństwie 1 % w punkcie A: opad punktowy przyjęto bez redukcji obszarowej
(rozdz. 2) w całej zlewni o powierzchni ponad 700 km², a czasu trwania opadu nie dobrano jako
krytycznego (rozdz. 5). Przykład pokazuje mechanikę sieci, nie hydrogram projektowy dla punktu A.

## 6.9. Warunki stabilności — podsumowanie

Metody rekurencyjne (Muskingum, Muskingum–Cunge, metoda Pulsa, zbiornik liniowy modelu Clarka)
dają przy zbyt długim lub zbyt krótkim kroku **ujemne wagi**: odpływ może wtedy oscylować albo
spaść poniżej zera, a pierwsza rzędna wznoszącej fali „zabiera” wodę z odpływu. Hydrolog nie liczy na
takich siatkach — warunki są **warunkami wstępnymi** specyfikacji (ADR-0061), a nie ostrzeżeniami.

| Metoda | Warunek | Co robi Hydrolog |
|---|---|---|
| Muskingum | okno kroku względem $K/N$ i $X$ (ramka `muskingum`) | dobiera $N$, w razie potrzeby dzieli krok na części (`substeps_added`); $N$ podane przez użytkownika poza oknem — odmowa (`unstable_timestep`) |
| Muskingum–Cunge | okno kroku drogi względem $c\,\Delta t$ i $D$ (ramka `muskingum_cunge`); minimalna liczba kroków na wznoszeniu (ramka `muskingum_cunge_rise`) | zmienia liczbę kroków drogi (`subreaches_adjusted`), zagęszcza krok (`timestep_refined`, `substeps_added`); bez siatki — kaskada zbiorników liniowych (`diffusion_dominated`) |
| Metoda Pulsa | krok względem najkrótszej stałej retencji odcinków tabeli (ramka `level_pool`) | dzieli krok (`timestep_refined`) |
| Zbiornik liniowy Clarka | krok nie dłuższy niż $2R$ (ramka `clark`, rozdz. 5) | odmowa (`precondition_failed`) |
| Kaskada, przesunięcie | brak | — |

Okno wag Muskingum wynika wprost z ramki `muskingum`: waga dopływu bieżącego jest nieujemna dopiero
od pewnego kroku, a waga odpływu poprzedniego — do pewnego kroku. USACE (1994) zaleca dodatkowo
krok nie dłuższy niż $K$, a NRCS — minimalną liczbę kroków od początku wznoszenia do kulminacji
(ramka `muskingum_cunge_rise`). Ogólna zasada: krok powinien być wyraźnie krótszy od czasu
narastania fali.

### Przykład 6.10. Odmowa poza oknem wag

Ten sam odcinek co w przykładzie 6.3, ale z jednym pododcinkiem podanym przez użytkownika:

```sh
hydrolog route muskingum --k-min 58 --x 0.2 --subreaches 1 --input-file kamiennik/KAMIENNIK.csv
```

Hydrolog odmawia (`validation_error`, `details.reason` = `unstable_timestep`): przy kroku 10 min wagi
są nieujemne tylko dla 3–9 pododcinków; jeden pododcinek wymagałby kroku od 23,2 do 92,8 min. Bez
opcji `--subreaches` Hydrolog sam wybiera 6 pododcinków (przykład 6.3).

### Przykład 6.11. Odcinek bez siatki Muskingum–Cunge

Krótki i płaski odcinek o szerokim korycie może mieć długość dyfuzji tak dużą wobec własnej długości
i drogi, jaką fala przebywa w jednym kroku, że żaden podział odcinka i kroku nie daje nieujemnych
wag. Odcinek nizinny przyjęty do przykładu — 1 km, spadek 0,3 ‰, dno 40 m, skarpy 1:1,5,
$n$ = 0,035:

```sh
hydrolog route muskingum-cunge --length-km 1 --slope-m-per-m 0.0003 --manning-n 0.035 --bottom-width-m 40 --side-slope-m-per-m 1.5 --input-file kamiennik/KAMIENNIK.csv
```

Prędkość fali wynosi 1,09 m/s, a długość dyfuzji 3541 m, więcej niż długość odcinka ($X$ wyniosłoby
−1,27). Hydrolog nie odmawia, lecz liczy odcinek jako kaskadę zbiorników liniowych (ADR-0026):
tutaj jeden zbiornik o $K$ = 15,34 min, kulminacja 51,95 m³/s po 430 min (−0,79 %), z ostrzeżeniem
`diffusion_dominated`, że spłaszczenie jest przybliżone:

<!-- spec:muskingum_cunge_fallback -->
<!-- /spec:muskingum_cunge_fallback -->

## 6.10. Jak wybrać metodę i jak czytać wynik

- **Odcinek bez danych o korycie, krótki wobec czasu narastania fali** — przesunięcie o $L/c$.
- **Odcinek z zarejestrowanymi hydrogramami dopływu i odpływu** — Muskingum ze skalibrowanymi $K$ i
  $X$ (pamiętając, że parametry zależą od wielkości fali).
- **Odcinek o znanym przekroju i spadku, bez cofki** — Muskingum–Cunge albo kaskada
  Kalinina–Milukowa.
- **Zbiornik, staw, polder** — metoda Pulsa z tabelą pojemność–odpływ obejmującą całą falę.
- **Cofka, przepływ pozakorytowy, budowle** — model hydrauliczny, nie metoda tego rozdziału.

Czytając wynik, warto sprawdzić: bilans objętości (`balance_error_m3`), uwagi o zmianie siatki i
wydłużeniu osi czasu, parametry, które Hydrolog dobrał sam ($N$, $\Delta x$, $X$, liczba kroków
pośrednich), oraz to, czy spłaszczenie wynika z fizyki odcinka, czy z przyjętych parametrów —
przykłady 6.3, 6.5 i 6.7 dają na tym samym odcinku spłaszczenie od 0,2 % do 8,8 %.

## Źródła

Źródła oznaczone (*) nie są dostępne w otwartym dostępie.

- Arcement G.J., Schneider V.R. (1989). *Guide for selecting Manning’s roughness coefficients for
  natural channels and flood plains*. USGS Water-Supply Paper 2339. https://pubs.usgs.gov/wsp/2339/report.pdf
- Baláž M., Danáčová M., Szolgay J. (2010). On the use of the Muskingum method for the simulation of
  flood wave movements. *Slovak Journal of Civil Engineering* 2010/3, 14–20.
  https://reference-global.com/article/10.2478/v10189-010-0012-6
- Cunge J.A. (1969). On the subject of a flood propagation computation method (Muskingum method).
  *Journal of Hydraulic Research* 7(2), 205–230 (*).
- McCarthy G.T. (1938). *The unit hydrograph and flood routing*. Conference of the North Atlantic
  Division, US Army Corps of Engineers (*).
- Nash J.E. (1957). The form of the instantaneous unit hydrograph. *IAHS Publication* 45, 114–121 (*).
- Ponce V.M. (online). *Linear reservoirs and numerical diffusion*. San Diego State University.
  https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html
- Ponce V.M. (online). Materiały do wykładu CIVE 445, rozdz. 9C–9D (transformacja fali, fala
  dyfuzyjna). San Diego State University. https://ton.sdsu.edu/
- USACE (1994). *Engineering and Design: Flood-Runoff Analysis*. EM 1110-2-1417, rozdz. 9.
  https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf
- USACE-HEC (online). *HEC-HMS Technical Reference Manual*, rozdz. „Channel Flow”: Lag, Muskingum,
  Muskingum-Cunge, Modified Puls. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow
- USDA-NRCS (2014). *National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing*
  (210-VI-NEH, Amend. 69): przykłady 17-1, 17-2, 17-4 i 17-5, dodatki 17B i 17C.

Decyzje projektowe Hydrologa przywołane w rozdziale: ADR-0008 (zasady transformacji), ADR-0010 i
ADR-0012 (dokument sieci, zlewnie liczące opad), ADR-0026 (odcinek bez siatki Muskingum–Cunge),
ADR-0061 (wzory transformacji w specyfikacjach) i ADR-0062 (odstępstwa od NEH 630 i HEC-HMS) w
katalogu `docs/decisions/`.
