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

<a id="spec-routing_initial_state"></a>

> **Stan początkowy transformacji fali** · wzór grupy B `routing_initial_state` (Tier B, CMP-2.2)
>
> **Definicja:** odpływ w chwili pierwszej rzędnej: podany odpływ początkowy, a w przeciwnym razie pierwsza rzędna dopływu; każdy pododcinek, zbiornik lub zbiornik liniowy elementu startuje z tym odpływem w stanie ustalonym (spoczynku) (źr. 1)
>
> **Konwencja:** stan ustalony na początku (HEC-HMS inicjalizuje odcinek jego dopływem); podany odpływ początkowy jest skończony i nieujemny
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Initial condition
>
> Funkcja `hydrolog.routing.reach._initial_outflow`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:routing_initial_state -->

Odpływ trwa dłużej niż dopływ, więc Hydrolog wydłuża oś czasu, utrzymując ostatnią wartość dopływu,
dopóki odpływ się nie ustali (uwaga `tail_extended`; gdy to się nie udaje — `tail_truncated`):

<!-- spec:routing_tail -->

<a id="spec-routing_tail"></a>

> **Wydłużenie osi czasu transformacji fali po końcu dopływu** · wzór grupy B `routing_tail` (Tier B, CMP-2.2)
>
> **Definicja:** najkrótsze wydłużenie osi czasu, przy utrzymanym ostatnim dopływie, po którym odpływ różni się od końcowego dopływu najwyżej o tolerancję (względem kulminacji dopływu), a woda zmagazynowana ponad ilość w stanie ustalonym nie przekracza tolerancji objętości dopływu (albo nadwyżki, z którą element startował, gdy jest ona większa); wydłużenie wynosi najwyżej dziesięciokrotność czasu trwania dopływu i co najmniej minimalną liczbę kroków (źr. 1)
>
> **Konwencja:** dopływ po jego ostatniej rzędnej jest równy ostatniej wartości; odpływ, który nie ustalił się do osiągnięcia limitu, daje ostrzeżenie `tail_truncated`
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `tail_tolerance` | Względna tolerancja ustalenia odpływu i retencji | 0,001 | – | (źr. 2) |
> | – | `min_extension_steps` | Minimalna liczba kroków wydłużenia osi czasu | 100 | – | (źr. 3) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Tail
> 2. Hydrolog ADR-0008: routing conventions, 0.1 % of the peak
> 3. Hydrolog ADR-0008: routing conventions, at least 100 steps
>
> Funkcja `hydrolog.routing.reach._settled`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:routing_tail -->

Każdy wynik podaje objętość dopływu i odpływu, retencję na początku i na końcu oraz błąd bilansu:

<!-- spec:routing_volume_balance -->

<a id="spec-routing_volume_balance"></a>

> **Błąd bilansu objętości transformacji fali** · wzór grupy B `routing_volume_balance` (Tier B, CMP-2.2)
>
> **Definicja:** objętość dopływu na wydłużonej osi czasu (z utrzymanym ostatnim dopływem) minus objętość odpływu minus retencja na końcu plus retencja na początku, każda objętość obliczona metodą trapezów (źr. 1)
>
> **Konwencja:** zero z dokładnością do zaokrągleń dla rekurencji na pierwotnym kroku; w pozostałych przypadkach błąd próbkowania metody trapezów po podziale na podkroki, błąd kwadratury ścisłego jądra (kaskada) albo interpolowanego opóźnienia
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Balance
>
> Funkcja `hydrolog.routing.reach.RoutingResult.balance_error_m3`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-lag"></a>

> **Przesunięcie w czasie (lag): dopływ przesunięty o stały czas, liniowy między rzędnymi** · specyfikacja [`lag`](../FORMULAS.md#lag) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> O(t) = I(t - \tau),\quad O_j = (1 - f)\,I_{j-w} + f\,I_{j-w-1},\ \frac{\tau}{\Delta t} = w + f,\ 0 \le f < 1,\quad S(t) = \int_{t-\tau}^{t} I(s)\,ds
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $I_t$ | `inflow_m3s` (ciąg) | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 2) |
> | $\Delta t$ | `timestep_min` | Krok czasowy dopływu i odpływu | min | (0; ∞) | nie podano w źródłach | [5; 720] (źr. 3) |
> | $\tau$ | `lag_min` | Przesunięcie, czas przepływu przez odcinek | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 4) |
> | $O_0$ | `initial_outflow_m3s` | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $O_t$ | `outflow_m3s` (ciąg) | Odpływ w rzędnych dopływu | m³/s | [0; ∞) |
> | $S$ | `storage_start_m3` | Objętość wody w drodze przez odcinek w pierwszej rzędnej, lag O0 | m³ | [0; ∞) |
> | $S$ | `storage_end_m3` | Objętość wody w drodze przez odcinek w ostatniej rzędnej, dopływ z ostatnich lag minut | m³ | [0; ∞) |
> | $S$ | `storage_steady_m3` | Objętość wody w drodze przez odcinek w stanie ustalonym przy ostatnim dopływie, lag I[-1] | m³ | [0; ∞) |
> | $w + f$ | `lag_steps` | Przesunięcie podzielone przez krok czasowy | – | [0; ∞) |
> | $f$ | `lag_fraction` | Waga wcześniejszej rzędnej: część kroku, o którą przesunięcie odbiega od całkowitej liczby kroków | – | [0; 1) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | lag / dt i objętość wody w drodze lag max(I, O0) są skończone w float64 | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
>
> **Konwencje**
>
> - jednostki SI: przepływ w m³/s, czas w min, retencja w m³ (przesunięcie w min razy przepływ w m³/s razy 60 s minuty z tabeli jednostek)
> - przed pierwszą rzędną dopływ jest równy odpływowi początkowemu (odcinek w stanie ustalonym, ADR-0008); HEC-HMS TRM, model Lag, wzór 1 przyjmuje zamiast tego O_t = I_t dla t < lag
> - przesunięcie niebędące całkowitą liczbą kroków interpoluje dopływ liniowo między dwiema rzędnymi otaczającymi t - lag, co spłaszcza ostre kulminacje; jeden krok przed pierwszą rzędną dopływ wynosi O0, więc rzędne odpływu odpowiadają dopływowi rosnącemu liniowo od O0 do I[0] w tym kroku, podczas gdy objętości retencji przyjmują O0 aż do pierwszej rzędnej
> - przesunięcie różniące się od całkowitej liczby kroków o nie więcej niż 1e-9 kroku liczy się jako całkowite (`LAG_ROUNDING`); objętości retencji zachowują przesunięcie w podanej postaci
> - transformowane są tylko podane rzędne: `LagReach` wydłuża oś czasu o przesunięcie (Tier B, ADR-0008) i dodaje uwagę `lag_interpolated` dla przesunięcia niebędącego całkowitą liczbą kroków
>
> **Założenia**
>
> - odcinek przesuwa falę bez tłumienia, a czas przepływu jest stały w czasie wezbrania
> - brak cofki: odpływ nie zależy od wody poniżej odcinka
>
> **Zgodność z obserwacjami według źródeł:** brak: przesunięcie to czas przepływu przez odcinek, ustalany z jego długości i prędkości fali albo kalibrowany (HEC-HMS TRM, model Lag); źródło nie podaje oceny zgodności z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Lag Model, eq. 1: O_t = I_(t - lag) for t >= lag and O_t = I_t before; the lag suits short reaches with a predictable travel time <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/lag-model>
> 2. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s
> 3. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d)
> 4. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), lags of 5 to 30 min in tests/unit/test_routing_core.py and of 10 to 60 min in docs/USAGE.md (route lag, networks)
> 5. IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, the lag over the step, and the water in transit lag max(I, O0)
>
> Funkcja `hydrolog.routing.formulas.lag.lag_route`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-muskingum"></a>

> **Transformacja fali metodą Muskingum w N jednakowych pododcinkach (retencja McCarthy'ego, ciągłość wzorem trapezów)** · specyfikacja [`muskingum`](../FORMULAS.md#muskingum) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1},\quad c_0 = \frac{\Delta t - 2kX}{D},\ c_1 = \frac{\Delta t + 2kX}{D},\ c_2 = \frac{2k(1-X) - \Delta t}{D},\ D = 2k(1-X) + \Delta t,\ k = \frac{K}{N}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $I_t$ | `inflow_m3s` (ciąg) | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 5) |
> | $\Delta t$ | `timestep_min` | Krok czasowy dopływu i odpływu | min | (0; ∞) | nie podano w źródłach | [5; 720] (źr. 6) |
> | $K$ | `k_min` | Czas przepływu przez cały odcinek, stała retencji K | min | (0; ∞) | nie podano w źródłach | [10; 1200] (źr. 7) |
> | $X$ | `x` | Waga dopływu w retencji: 0 — zbiornik liniowy, 0,5 — fala nietłumiona | – | [0; 0,5] | [0; 0,5] (źr. 1) | [0,1; 0,3] (źr. 8) |
> | $N$ | `subreaches` (liczba całkowita) | Liczba jednakowych pododcinków o stałej K / N połączonych szeregowo | – | [1; ∞) | nie podano w źródłach | [1; 10] (źr. 9) |
> | $O_0$ | `initial_outflow_m3s` | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $O_t$ | `outflow_m3s` (ciąg) | Odpływ w rzędnych dopływu | m³/s | [0; ∞) |
> | $c_0$ | `c_current` | Waga I[t] w jednym pododcinku | – | [0; 1] |
> | $c_1$ | `c_previous` | Waga I[t-1] w jednym pododcinku | – | [0; 1] |
> | $c_2$ | `c_outflow` | Waga O[t-1] w jednym pododcinku | – | [0; 1] |
> | $S$ | `storage_start_m3` | Objętość wody w pododcinkach w pierwszej rzędnej | m³ | [0; ∞) |
> | $S$ | `storage_end_m3` | Objętość wody w pododcinkach w ostatniej rzędnej | m³ | [0; ∞) |
> | $S$ | `storage_steady_m3` | Objętość wody w pododcinkach w stanie ustalonym przy ostatnim dopływie, K I[-1] | m³ | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | dt, K / N i dt / (K / N) >= 2,2e-308, najmniejsza liczba znormalizowana float64, a 2 K [s] i objętość wody K max(I, O0) [m³] są skończone: poniżej tej granicy wagi zaokrąglają się do mniejszej liczby cyfr albo wagi dopływu ulegają niedomiarowi i wpływająca woda ginie; powyżej wagi są NaN | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 10) |
> | 2 K X / N <= dt <= 2 K (1 - X) / N, każdy koniec z dokładnością do 1e-9 swojej wartości: każda waga jest nieujemna, więc nieujemny dopływ daje nieujemny odpływ | `nonnegative_weights` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
>
> **Konwencje**
>
> - jednostki SI: przepływ w m³/s, czas w min, retencja w m³ (K w min razy przepływ w m³/s razy 60 s minuty z tabeli jednostek)
> - wagi nazwano według tego, co mnożą: `c_current` — I[t], `c_previous` — I[t-1], `c_outflow` — O[t-1]; NEH 630 i HEC-HMS nazywają je C2, C1 i C3, przykłady z Iowa i NPTEL — C1, C2 i C3
> - ciągłość wzorem trapezów, (S[t] - S[t-1]) / dt = (I[t] + I[t-1]) / 2 - (O[t] + O[t-1]) / 2, przy S = k [X I + (1 - X) O] w każdym pododcinku
> - N jednakowych pododcinków o stałej K / N połączonych szeregowo, z tym samym X (HEC-HMS); każdy pododcinek startuje w stanie ustalonym z odpływem O0, więc w pierwszej rzędnej wszystkie poza pierwszym są zasilane przez O0
> - w granicach tolerancji okna waga, którą zaokrąglenie sprowadza poniżej zera, jest zerowana, a pozostałe dzieli się przez ich sumę (`hydrolog.routing._kernels.nonnegative_coefficients`)
> - transformowane są tylko podane rzędne: `MuskingumReach` dobiera N (zaokrąglone K / dt) oraz podkroki kroku, dla którego nie ma okna, interpoluje między nimi dopływ liniowo i wydłuża oś czasu (Tier B, ADR-0008)
>
> **Założenia**
>
> - retencja odcinka jest liniową funkcją ważonego przepływu, S = K [X I + (1 - X) O], przy K i X stałych w czasie wezbrania
> - brak cofki: odpływ nie zależy od wody poniżej odcinka
>
> **Zgodność z obserwacjami według źródeł:** brak: K i X kalibruje się na wezbraniach obserwowanych na odcinku (HEC-HMS TRM, model Muskingum; EM 1110-2-1417 rozdz. 9); źródła nie podają oceny zgodności samego schematu z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, equations of the storage and of the weights; X from 0 to 0.5; sub-reaches whose travel time is about the time step <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-model>
> 2. US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, eqs. 9-15 to 9-19, pp. 9-12 to 9-15 <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>
> 3. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-6 to 17-11 and the Muskingum method, pp. 17-14 to 17-18 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 4. McCarthy, G.T. (1938). The unit hydrograph and flood routing, Conference of the North Atlantic Division, US Army Corps of Engineers, New London, Conn. — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s
> 6. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d)
> 7. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), K of 10 to 60 min in the tests of the reach, 2.3 h (NPTEL) and 20 h (Iowa) in the published examples
> 8. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), X of 0.2 in most tests of the reach, 0.15 (NPTEL) and 0.25 (Iowa) in the published examples; 0.1 to 0.3 for natural streams after Fread (1993), as Balaz, Danacova and Szolgay (2010, Slovak Journal of Civil Engineering 18(3)) cite it
> 9. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 to 3 sub-reaches in the tests of the reach and in the published examples; K / dt rounded up to 10 in the network tests
> 10. IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, smallest normal 2.2e-308, the ratio of the step to K / N in the weights, K in seconds in their denominator and the storage K max(I, O0)
> 11. the signs of the numerators of the weights (Hydrolog ADR-0008); Ponce's form \|C - D\| <= 1 <= C + D, c_current >= 0 iff dt >= 2KX/N, c_previous >= 0 iff dt >= -2KX/N, c_outflow >= 0 iff dt <= 2K(1 - X)/N
>
> Funkcja `hydrolog.routing.formulas.muskingum.muskingum_route`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-muskingum_subreaches"></a>

> **Liczba pododcinków w metodzie Muskingum** · wzór grupy B `muskingum_subreaches` (Tier B, CMP-2.2)
>
> **Definicja:** liczby całkowite N jednakowych pododcinków, przy których wagi są nieujemne dla kroku dt, ceil(2KX/dt) <= N <= floor(2K(1 - X)/dt), każdy koniec z dokładnością do 1e-9 swojej wartości; `MuskingumReach` transformuje z N = K/dt zaokrąglonym (połowa w górę, co najmniej 1), które leży w oknie zawsze, gdy leży w nim jakakolwiek liczba całkowita, a krok, dla którego nie ma okna, dzieli na najmniejszą liczbę od 2 do 100 jednakowych podkroków, dla której okno istnieje, przy dopływie liniowym między rzędnymi (źr. 1)
>
> **Konwencja:** czas przepływu przez pododcinek wynosi około jednego kroku czasowego (HEC-HMS); liczby pododcinków podanej przez wywołującego nigdy się nie zmienia: poza oknem jest odrzucana (`unstable_timestep`, ADR-0008)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, the number of subreaches: the travel time through a subreach approximately equal to the simulation time step <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-model>
>
> Funkcja `hydrolog.routing.muskingum.subreach_window`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-manning_normal_flow"></a>

> **Przepływ normalny w korycie trapezowym, prostokątnym lub trójkątnym ze wzoru Manninga, z kinematyczną prędkością fali dQ/dA** · specyfikacja [`manning_normal_flow`](../FORMULAS.md#manning_normal_flow) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q = \frac{1}{n} A R^{2/3} S^{1/2},\quad A = (b + z y) y,\ P = b + 2 y \sqrt{1 + z^2},\ R = \frac{A}{P};\quad T = b + 2 z y,\ V = \frac{Q}{A},\ c = \frac{dQ}{dA} = V \left(\frac{5}{3} - \frac{2}{3} \frac{A P'}{T P}\right)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $Q$ | `discharge_m3s` | Przepływ, dla którego wyznacza się przepływ normalny | m³/s | (0; ∞) | nie podano w źródłach | [1; 300] (źr. 6) |
> | $S$ | `slope_m_per_m` | Spadek dna, równy spadkowi linii energii przy przepływie jednostajnym | m/m | (0; ∞) | nie podano w źródłach | [0,0002; 0,02] (źr. 7) |
> | $b$ | `bottom_width_m` | Szerokość dna przekroju; zero dla trójkąta | m | [0; ∞) | nie podano w źródłach | [0; 30] (źr. 8) |
> | $z$ | `side_slope_m_per_m` | Odległość pozioma w metrach na metr wysokości obu skarp; zero dla prostokąta | m/m | [0; ∞) | nie podano w źródłach | [0; 2] (źr. 9) |
> | $n$ | `manning_n` | Współczynnik szorstkości Manninga dla całego obwodu zwilżonego | $\mathrm{s/m^{1/3}}$ | (0; ∞) | nie podano w źródłach | [0,03; 0,05] (źr. 10) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $y$ | `depth_m` | Głębokość normalna | m | (0; ∞) |
> | $A$ | `area_m2` | Pole przekroju przepływu przy głębokości normalnej | m² | (0; ∞) |
> | $T$ | `top_width_m` | Szerokość zwierciadła wody przy głębokości normalnej | m | (0; ∞) |
> | $V$ | `velocity_m_per_s` | Prędkość średnia Q / A | m/s | (0; ∞) |
> | $c$ | `celerity_m_per_s` | Prędkość kinematycznej fali wezbraniowej, dQ/dA przy stałym spadku | m/s | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | b + z > 0: przekrój ma dno lub skarpy; bez żadnego z nich nie mieści wody | `has_width` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 3) |
> | 2,2e-308 <= y, A, T, V, c < inf: float64 przechowuje przepływ normalny z dokładnością do szesnastu cyfr; przekrój tak wąski, płaski lub szorstki albo przepływ tak duży lub mały, że któraś z tych wielkości przekracza zakres lub trafia między liczby subnormalne, nie ma przepływu normalnego | `representable_flow` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $2/3$ | `radius_exponent` | Wykładnik promienia hydraulicznego | 2/3 | – | (źr. 1) |
> | $1/2$ | `slope_exponent` | Wykładnik spadku linii energii | 1/2 | – | (źr. 1) |
>
> **Konwencje**
>
> - jednostki SI: Q w m³/s, długości w m, n w s/m^(1/3); postać w jednostkach amerykańskich mnoży przez 1,486, zaokrąglony pierwiastek sześcienny z liczby stóp w metrze (1,4859), tak jak HEC-RAS (USGS WSP 2339, wzór 1)
> - spadek dna jest spadkiem linii energii (spadkiem tarcia): przepływ jest jednostajny
> - prędkość fali to lokalna kinematyczna prędkość fali dQ/dA przy danej głębokości (HEC-HMS, wzór 4; NEH, wzór 17-25 z m = d ln Q / d ln A); przykład 17-4 z NEH przyjmuje m krzywej natężenia przepływu ważone przepływem od zera do Q (wzory 17-29, 17-30a), o 2 % większe od lokalnego (przypadek `mc_neh17_example17_4_from_section`)
> - jedna szorstkość dla całego obwodu zwilżonego; trapez z obiema skarpami o nachyleniu z:1, prostokąt przy z = 0 i trójkąt przy b = 0; bez terenów zalewowych
> - głębokość normalną wyznacza się metodą Brenta względem ln y (`scipy.optimize.brentq`, delegowane, CMP-1.2) w przedziale wyznaczonym z nachylenia ln K względem ln y, mieszczącego się między 1 a 10/3, z dokładnością do czterech jednostek 1e-16 wartości max(1, \|ln y\|)
>
> **Założenia**
>
> - przepływ ustalony jednostajny: głębokość jest głębokością normalną danego przepływu
> - koryto pryzmatyczne, którego n nie zmienia się z głębokością
> - przepływ mieści się w przekroju, który nie ma górnego ograniczenia
>
> **Zgodność z obserwacjami według źródeł:** brak: źródła podają wzór Manninga jako praktykę obliczeń ustalonego przepływu jednostajnego w korytach otwartych i nie podają własnej oceny zgodności z obserwacjami; n dobiera się z tabel albo kalibruje (USGS WSP 2339)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Arcement, G.J. and Schneider, V.R. (1989). Guide for selecting Manning's roughness coefficients for natural channels and flood plains, US Geological Survey Water-Supply Paper 2339, Introduction, eqs. 1 and 2 (the first page of the text): V = 1.486/n R^(2/3) Se^(1/2) and the conveyance K = 1.486/n A R^(2/3), in feet <https://pubs.usgs.gov/wsp/2339/report.pdf>
> 2. US Army Corps of Engineers, Hydrologic Engineering Center. Water Surface Profile Calculations with HEC-RAS (training lesson 1.6, PROSPECT course), slides 'Cross Section Subdivision for Conveyance Calculations' (Q = 1.486/n A R^(2/3) Sf^(1/2), in feet) and 'Computational Procedure: Tolerances and trials' (water surface calculation tolerance 0.01 ft by default) <https://www.hec.usace.army.mil/confluence/prospect/files/124452884/124453107/1/1669663021202/1.6+L+-+Water+Surface+Profile+Calculations.pdf>
> 3. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum-Cunge Model, eq. 4, the flood wave celerity c = dQ/dA; Required Parameters: the reach's Manning's n and a rectangle, trapezoid or triangle by its bottom width and side slope <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-cunge-model>
> 4. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-24 and 17-25, c = dQ/dA = m Q / A, and 17-29 and 17-30a, the weighted m of a rating table; Table 17-16 and example 17-4, pp. 17-36 to 17-43 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 5. Manning, R. (1891). On the flow of water in open channels and pipes, Transactions of the Institution of Civil Engineers of Ireland 20, 161-207 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 6. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), reference discharges of 0.95 to 300.05 m3/s in the tests of the reach (tests/unit/test_routing_cunge.py), 12 m3/s in tests/fixtures/network_flood.json; NEH 630 examples 17-4 and 17-5, 684.18 and 3,385.4 ft3/s (19.4 and 95.9 m3/s)
> 7. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.0002 to 0.002778 in the tests of the reach (tests/unit/test_routing_cunge.py), 0.00208 to 0.009859 on the reaches of Hydrograf's Nysa Szalona network from the DEM (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json), 0.02 in tests/fixtures/handoff_hydrograf_network.json; 0.00091 in NEH 630 examples 17-4 and 17-5
> 8. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0 (a triangle) to 30 m in the tests of the section (tests/unit/test_routing_sections.py), 5 to 15 m in the tests of the reach, 8 m in tests/fixtures/network_flood.json; NEH 630 example 17-4, 15 ft (4.57 m)
> 9. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0 (a rectangle) to 2 (2:1 banks) in the tests of the section and of the reach, 2 in tests/fixtures/network_flood.json and NEH 630 example 17-4
> 10. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.03 to 0.05 in the tests of the section and of the reach, 0.035 in docs/USAGE.md and tests/fixtures/network_flood.json; NEH 630 example 17-4, 0.04
> 11. IEEE 754-2019, binary64: normal numbers of magnitude about 2.2e-308 to 1.8e308, with 53 significant bits; below them the subnormal numbers keep fewer, the depth, the area, the top width, the velocity and the celerity of a flow must be normal numbers to hold their sixteen digits
>
> Funkcja `hydrolog.routing.formulas.manning.normal_flow`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-muskingum_cunge"></a>

> **Transformacja fali metodą Muskingum-Cunge ze stałymi współczynnikami na N jednakowych krokach przestrzennych (K i X według Cunge'a)** · specyfikacja [`muskingum_cunge`](../FORMULAS.md#muskingum_cunge) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> D = \frac{Q}{T S_0 c},\ \Delta x = \frac{L}{N},\ K = \frac{\Delta x}{c},\ X = \frac{1}{2}\left(1 - \frac{D}{\Delta x}\right);\quad O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1};\quad C_g = \frac{c \Delta t}{\Delta x},\ D_g = \frac{D}{\Delta x} = 1 - 2X
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $I_t$ | `inflow_m3s` (ciąg) | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 5) |
> | $\Delta t$ | `timestep_min` | Krok czasowy dopływu i odpływu | min | (0; ∞) | nie podano w źródłach | [5; 720] (źr. 6) |
> | $L$ | `length_km` | Długość odcinka | km | (0; ∞) | nie podano w źródłach | [0,1; 23,4] (źr. 7) |
> | $S_0$ | `slope_m_per_m` | Spadek dna odcinka | m/m | (0; ∞) | nie podano w źródłach | [0,0002; 0,02] (źr. 8) |
> | $c$ | `celerity_m_per_s` | Prędkość fali wezbraniowej przy przepływie odniesienia | m/s | (0; ∞) | nie podano w źródłach | [0,2; 5] (źr. 9) |
> | $T$ | `top_width_m` | Szerokość zwierciadła wody przy przepływie odniesienia | m | (0; ∞) | nie podano w źródłach | [10; 225] (źr. 10) |
> | $Q$ | `reference_discharge_m3s` | Przepływ odniesienia, przy którym przyjmuje się prędkość fali i szerokość zwierciadła, wspólny dla całego obliczenia | m³/s | (0; ∞) | nie podano w źródłach | [1; 300] (źr. 11) |
> | $N$ | `subreaches` (liczba całkowita) | Liczba jednakowych kroków przestrzennych dx = L / N | – | [1; ∞) | nie podano w źródłach | [1; 4] (źr. 12) |
> | $O_0$ | `initial_outflow_m3s` | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $O_t$ | `outflow_m3s` (ciąg) | Odpływ w rzędnych dopływu | m³/s | [0; ∞) |
> | $K$ | `k_min` | Czas przepływu L / c przez cały odcinek | min | (0; ∞) |
> | $X$ | `x` | Współczynnik wagowy każdego kroku przestrzennego, (1 - Dg) / 2 | – | (−∞; 0,5] |
> | $c_0$ | `c_current` | Waga I[t] w jednym kroku przestrzennego | – | [0; 1] |
> | $c_1$ | `c_previous` | Waga I[t-1] w jednym kroku przestrzennego | – | [0; 1] |
> | $c_2$ | `c_outflow` | Waga O[t-1] w jednym kroku przestrzennego | – | [0; 1] |
> | $\Delta x$ | `dx_m` | Krok przestrzenny L / N | m | (0; ∞) |
> | $C_g$ | `courant_number` | Liczba Couranta siatki, c dt / dx | – | (0; ∞) |
> | $D_g$ | `grid_reynolds_number` | Siatkowa liczba Reynoldsa D / dx = 1 - 2X | – | (0; ∞) |
> | $e^{2{,}3 C_g}$ | `grid_reynolds_limit` | Granica dokładności siatkowej liczby Reynoldsa według NEH, exp(2,3 Cg), ograniczona do exp(700) | – | [1; ∞) |
> | $S$ | `storage_start_m3` | Objętość wody w schemacie w pierwszej rzędnej, suma K/N [X I + (1 - X) O] po krokach przestrzennych; ujemna, gdy X < 0, a dopływ dostatecznie przewyższa odpływ początkowy | m³ | (−∞; ∞) |
> | $S$ | `storage_end_m3` | Objętość wody w schemacie w ostatniej rzędnej | m³ | (−∞; ∞) |
> | $S$ | `storage_steady_m3` | Objętość wody w schemacie w stanie ustalonym przy ostatnim dopływie, K I[-1] | m³ | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | \|c dt - D\| <= L / N <= c dt + D przy D = Q / (T S0 c), każdy koniec z dokładnością do 1e-9 swojej wartości: każda waga jest nieujemna, więc nieujemny dopływ daje nieujemny odpływ | `nonnegative_weights` | odmowa obliczeń: wzór jest nieokreślony | (źr. 13) |
> | L / c, c dt / dx, D / dx i N K (1 + 2\|X\|) max(I, O0) są skończone: float64 mieści siatkę i objętość wody, jaką może ona zatrzymać; fala tak powolna, krok tak krótki albo wezbranie tak duże, że któraś z tych wielkości przekracza zakres, nie ma siatki | `finite_grid` | odmowa obliczeń: wzór jest nieokreślony | (źr. 14) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $2{,}3$ | `accuracy_factor` | Współczynnik przy liczbie Couranta w wykładniku granicy dokładności NRCS | 2,3 | – | (źr. 1) |
> | – | `limit_exponent_cap` | Górne ograniczenie wykładnika granicy dokładności | 700 | – | (źr. 14) |
>
> **Konwencje**
>
> - jednostki SI: przepływ w m³/s, czas w min, odcinek w km, krok przestrzenny i długość dyfuzji w m, prędkość fali w m/s, retencja w m³
> - wagi nazwano według tego, co mnożą: `c_current` — I[t], `c_previous` — I[t-1], `c_outflow` — O[t-1]; NEH 630 i HEC-HMS nazywają je C2, C1 i C3
> - jeden przepływ odniesienia, jedna prędkość fali i jedna szerokość zwierciadła dla wszystkich kroków przestrzennych i czasowych, więc współczynniki są stałe: WinTR-20 z NRCS przyjmuje kulminację na górnym końcu każdego kroku przestrzennego (NEH 630 przykład 17-5), a HEC-HMS przelicza współczynniki w każdym kroku czasu i drogi (metoda o zmiennych współczynnikach, Ponce 1986): przypadek `mc_neh17_example17_5_reach`
> - X może być ujemne (NEH 630 przykład 17-4, X = -0,254); siatkę z ujemną wagą, którą NEH dopuszcza (przykład 17-5, C1 = -0,187), odrzuca warunek wstępny `nonnegative_weights` (Hydrolog ADR-0008)
> - w granicach tolerancji okna waga, którą zaokrąglenie sprowadza poniżej zera, jest zerowana, a pozostałe dzieli się przez ich sumę (`hydrolog.routing._kernels.nonnegative_coefficients`)
> - Dg oblicza się jako D / dx (NEH wzór 17-34), co z dokładnością do zaokrągleń równa się 1 - 2X (wzór 17-35); granicę dokładności exp(2,3 Cg) ogranicza się do exp(700), co przewyższa każde Dg <= 1 + Cg z okna
> - brak dopływu bocznego: człon C4 q dx we wzorze 7 HEC-HMS jest równy zeru
> - transformowana jest tylko podana siatka: `MuskingumCungeReach` przyjmuje kulminację dopływu jako przepływ odniesienia, o ile nie podano innego, dobiera N i podkroki kroku według reguł NEH 630 w obrębie okna, interpoluje między nimi dopływ liniowo, a tam, gdzie siatka nie istnieje, przechodzi na zbiorniki liniowe (Tier B, ADR-0008, ADR-0026)
>
> **Założenia**
>
> - fala dyfuzyjna: człony bezwładności w równaniu ruchu są pomijane, a równanie adwekcji–dyfuzji linearyzuje się przy przepływie odniesienia ze stałymi c i mu = Q / (2 T S0) (HEC-HMS wzory 1 do 5)
> - odcinek pryzmatyczny o jednym spadku; brak cofki
>
> **Zgodność z obserwacjami według źródeł:** brak: źródła porównują schemat z modelami przepływu nieustalonego, a nie z obserwacjami (NEH 630 przykłady 17-4 i 17-5 w porównaniu z HEC-RAS: kulminacje zgodne w granicach 0,2 i 2,5 %); NRCS dopasował swoją granicę dokładności do 140 testowych transformacji (NEH 630 załącznik 17B)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-20 to 17-22 (X, the distance step, K) and 17-31 to 17-36 (Cg, Dg and the accuracy limit, eq. 17-36 on p. 17-33); examples 17-4 and 17-5, pp. 17-36 to 17-51 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 2. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum-Cunge Model, eqs. 3 to 5 (the convective diffusion equation, c = dQ/dA, mu = Q / (2 B S0)), 6 to 10 (the weights) and 12 and 13 (K = dx / c, X = (1 - Q / (B S0 c dx)) / 2) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-cunge-model>
> 3. US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, eq. 9-22 and the reference flow, p. 9-21 <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>
> 4. Cunge, J.A. (1969). On the subject of a flood propagation computation method (Muskingum method), Journal of Hydraulic Research 7(2), 205-230 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s
> 6. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d)
> 7. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.1 to 20 km in the tests of the reach (tests/unit/test_routing_cunge.py), 1.3 to 23.4 km on Hydrograf's Nysa Szalona network besides a 7 m connector (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json); NEH 630 examples 17-4 and 17-5, 2,600 ft (0.79 km)
> 8. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.0002 to 0.002778 in the tests of the reach (tests/unit/test_routing_cunge.py), 0.00208 to 0.009859 on the reaches of Hydrograf's Nysa Szalona network from the DEM (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json), 0.02 in tests/fixtures/handoff_hydrograf_network.json; 0.00091 in NEH 630 examples 17-4 and 17-5
> 9. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.2 to 5 m/s in the tests of the reach (tests/unit/test_routing_cunge.py); NEH 630 examples 17-4 and 17-5, 4.297 and 1.779 ft/s (1.31 and 0.54 m/s)
> 10. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 10 to 200 m in the tests of the reach and of the networks (tests/unit/test_routing_cunge.py, tests/unit/test_operations_route_network.py); NEH 630 examples 17-4 and 17-5, 44.6 and 738.3 ft (13.6 and 225 m)
> 11. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), reference discharges of 0.95 to 300.05 m3/s in the tests of the reach (tests/unit/test_routing_cunge.py), 12 m3/s in tests/fixtures/network_flood.json; NEH 630 examples 17-4 and 17-5, 684.18 and 3,385.4 ft3/s (19.4 and 95.9 m3/s)
> 12. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 to 4 distance steps in the tests of the reach (tests/unit/test_routing_cunge.py); 1 and 2 in NEH 630 examples 17-4 and 17-5
> 13. the signs of the numerators of the weights (Hydrolog ADR-0008); Ponce's form \|C - D\| <= 1 <= C + D, c_current >= 0 iff dx <= c dt + D, c_previous >= 0 iff dx >= D - c dt, c_outflow >= 0 iff dx >= c dt - D
> 14. IEEE 754-2019, binary64: finite numbers of magnitude about 4.9e-324 to 1.8e308, the grid's scalars and the water it holds must be among them; exp(700), about 1.0e304, is one
>
> Funkcja `hydrolog.routing.formulas.cunge.muskingum_cunge_route`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:muskingum_cunge -->

**Siatka.** Odcinek dzieli się na $N$ równych **kroków drogi** (ang. *distance steps*) $\Delta x$;
NRCS podaje krok drogi zależny od $c\,\Delta t$ i $D$ (USDA-NRCS 2014, wzór 17-21). Hydrolog bierze
liczbę kroków NRCS albo najbliższą, przy której wszystkie wagi są nieujemne (uwaga
`subreaches_adjusted`):

<!-- spec:muskingum_cunge_grid -->

<a id="spec-muskingum_cunge_grid"></a>

> **Siatka obliczeniowa metody Muskingum-Cunge** · wzór grupy B `muskingum_cunge_grid` (Tier B, CMP-2.2)
>
> **Definicja:** przepływem odniesienia jest kulminacja dopływu, o ile nie podano innego; krok przestrzenny NRCS dx_c = (c dt + D) / 2 przy D = Q / (T S0 c) daje ceil(L / dx_c) kroków, a liczbę tę zmienia się na najbliższą liczbę w oknie nieujemnych wag \|c dt - D\| <= L / N <= c dt + D, każdy koniec z dokładnością do 1e-9 swojej wartości (`hydrolog.routing.formulas.cunge.distance_step_window`); krok, dla którego w oknie nie ma liczby całkowitej, dzieli się na najmniejszą liczbę od 2 do 100 jednakowych podkroków, dla której taka liczba istnieje, przy dopływie liniowym między rzędnymi (uwagi `subreaches_adjusted`, `substeps_added`); uwaga `accuracy_limit` sygnalizuje siatkę NRCS, której Dg = D / dx przekracza exp(2,3 Cg) (źr. 1)
>
> **Konwencja:** jeden przepływ odniesienia dla wszystkich kroków przestrzennych, podczas gdy WinTR-20 przyjmuje kulminację na górnym końcu każdego z nich; siatka z ujemną wagą, którą NEH dopuszcza (przykład 17-5), jest zastępowana (ADR-0008); siatka wymagająca ponad miliona rzędnych jest odrzucana (`unstable_timestep`)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), steps 2 to 4 of the Muskingum-Cunge method and eqs. 17-21 and 17-36, pp. 17-32 to 17-33 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
>
> Funkcja `hydrolog.routing.cunge.MuskingumCungeReach._grid`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:muskingum_cunge_grid -->

NEH 630 wymaga też odpowiedniej liczby kroków czasowych na wznoszącej gałęzi hydrogramu; krótszą
gałąź Hydrolog zagęszcza krokami pośrednimi (uwaga `timestep_refined`):

<!-- spec:muskingum_cunge_rise -->

<a id="spec-muskingum_cunge_rise"></a>

> **Czas wznoszenia fali w metodzie Muskingum-Cunge** · wzór grupy B `muskingum_cunge_rise` (Tier B, CMP-2.2)
>
> **Definicja:** liczba kroków od rzędnej poprzedzającej pierwszą rzędną powyżej 5 % kulminacji dopływu do pierwszej kulminacji wynoszącej co najmniej połowę kulminacji dopływu; wznoszenie trwające od 1 do 9 kroków powoduje podział każdego kroku siatki na ceil(10 / wznoszenie) jednakowych podkroków (co najwyżej 100), przy dopływie liniowym między rzędnymi (uwaga `timestep_refined`) (źr. 1)
>
> **Konwencja:** NEH 630 ponownie interpoluje hydrogram do dokładnie 10 przedziałów na wznoszeniu; Hydrolog dzieli krok na całkowitą liczbę podkroków, dając 10 przedziałów lub więcej, i zachowuje oryginalne rzędne; zbiorniki odcinka bez siatki są ścisłe przy każdym kroku i nie są zagęszczane
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), Muskingum-Cunge method, step 1: at least 10 time intervals from the point of 5 percent of the peak on the rise to the peak, p. 17-32 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
>
> Funkcja `hydrolog.routing.cunge.rise_steps`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-linear_reservoir_cascade"></a>

> **Kaskada n jednakowych zbiorników liniowych, ścisła dla dopływu liniowego między rzędnymi (Nash)** · specyfikacja [`linear_reservoir_cascade`](../FORMULAS.md#linear_reservoir_cascade) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> O(t) = O_0\,Q\!\left(n, \tfrac{t}{K}\right) + \int_0^t u(t-s)\,I(s)\,ds,\quad u(t) = \frac{1}{K\,\Gamma(n)}\left(\frac{t}{K}\right)^{n-1}e^{-t/K},\quad h_m = -\frac{V((m+1)a) - 2V(ma) + V((m-1)a)}{a},\ V(x) = x\,Q(n, x) + n\,P(n+1, x),\ a = \frac{\Delta t}{K}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $I_t$ | `inflow_m3s` (ciąg) | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 3) |
> | $\Delta t$ | `timestep_min` | Krok czasowy dopływu i odpływu | min | (0; ∞) | nie podano w źródłach | [5; 720] (źr. 4) |
> | $n$ | `n` | Liczba jednakowych zbiorników połączonych szeregowo; nie musi być całkowita | – | (0; ∞) | nie podano w źródłach | [1; 8] (źr. 5) |
> | $K$ | `k_min` | Stała retencji jednego zbiornika | min | (0; ∞) | nie podano w źródłach | [5; 80] (źr. 6) |
> | $O_0$ | `initial_outflow_m3s` | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 3) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $O_t$ | `outflow_m3s` (ciąg) | Odpływ w rzędnych dopływu | m³/s | [0; ∞) |
> | $S$ | `storage_start_m3` | Objętość wody w zbiornikach w pierwszej rzędnej | m³ | [0; ∞) |
> | $S$ | `storage_end_m3` | Objętość wody w zbiornikach w ostatniej rzędnej | m³ | [0; ∞) |
> | $S$ | `storage_steady_m3` | Objętość wody w zbiornikach w stanie ustalonym przy ostatnim dopływie, n K I[-1] | m³ | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 2,2e-308, 0 < dt / K, a siatka N dt / K, największy przepływ podzielony przez dt / K i retencja n K max(I, O0) są skończone w float64 | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
>
> **Konwencje**
>
> - jednostki SI: przepływ w m³/s, czas w min, retencja w m³ (K w min razy przepływ w m³/s razy 60 s minuty z tabeli jednostek)
> - dopływ jest liniowy między rzędnymi, a przed pierwszą z nich równy odpływowi początkowemu: każdy zbiornik startuje w stanie ustalonym z odpływem O0, a w pierwszej rzędnej dopływ skacze do I[0]
> - odpływ w rzędnej jest ścisłą odpowiedzią na taki dopływ, a nie krokiem metody trapezów czy Eulera; między rzędnymi nie jest liniowy, więc objętość odpływu liczona wzorem trapezów różni się od jego całki
> - waga, którą zaokrąglenie sprowadza poniżej zera, jest zerowana; tak samo reszta n - V i odpływ, które zaokrąglenie sprowadza poniżej zera
> - n nie musi być całkowite: Gamma(n) i P(n, x) z funkcji `gammainc` i `gammaincc` biblioteki SciPy
> - transformowane są tylko podane rzędne: `CascadeReach` przyjmuje K albo K = L / (n c) z długości odcinka i prędkości fali oraz wydłuża oś czasu (Tier B, ADR-0008)
>
> **Założenia**
>
> - każdy zbiornik jest liniowy, S = K O, przy K stałym w czasie wezbrania
> - brak cofki: odpływ nie zależy od wody poniżej odcinka
>
> **Zgodność z obserwacjami według źródeł:** brak: n i K kalibruje się na obserwowanych wezbraniach lub wyznacza z cech odcinka (Kalinin–Milukow); źródła nie podają oceny zgodności samej kaskady z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Nash, J.E. (1957). The form of the instantaneous unit hydrograph, IAHS Publication 45, 114-121, the cascade of n equal linear reservoirs and its gamma impulse response — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Ponce, V.M. (online). Linear reservoirs and numerical diffusion, San Diego State University, the Nash cascade and the Kalinin-Milyukov method: n reservoirs of S = K O in series, impulse response of mean n K <https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html>
> 3. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s
> 4. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d)
> 5. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), n of 1 to 8 in tests/unit/test_routing_cascade.py and 2.5 in docs/USAGE.md (route cascade)
> 6. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), K of 5 to 40 min in tests/unit/test_routing_cascade.py and 80 min in docs/USAGE.md (route cascade)
> 7. IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, smallest normal 2.2e-308; SciPy's scipy.special.gammainc and gammaincc (1.18.1) give P(a, x) = 0 and Q(a, x) <= 0 for a subnormal shape a, x = m dt / K on the grid of the ordinates, the inflow over dt / K, the storage n K I, and n as the shape of P and Q
>
> Funkcja `hydrolog.routing.formulas.cascade.cascade_route`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:linear_reservoir_cascade -->

Stałą $K$ podaje się wprost albo z długości odcinka i prędkości fali:

<!-- spec:cascade_time_scale -->

<a id="spec-cascade_time_scale"></a>

> **Stała retencji kaskady z długości odcinka i prędkości fali** · wzór grupy B `cascade_time_scale` (Tier B, CMP-2.2)
>
> **Definicja:** stała retencji jednego zbiornika wyznaczona z długości L odcinka i prędkości c fali wezbraniowej, K = L / (n c): czas przepływu L / c jest średnim opóźnieniem n K kaskady; L w km i c w m/s przeliczane według tabeli jednostek (1 km = 1000 m, 1 min = 60 s) (źr. 1)
>
> **Konwencja:** K podaje się wprost albo wyznacza z L i c, nigdy oba naraz (`details.reason` `one_of`); Kalinin i Milukow przyjmują n jako L podzielone przez długość charakterystyczną Q / (T S0 c)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ponce, V.M. (online). Linear reservoirs and numerical diffusion, San Diego State University, the Kalinin-Milyukov method: n = L / L_c reservoirs of K = L_c / c in series <https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html>
>
> Funkcja `hydrolog.routing.cascade.CascadeReach`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-level_pool"></a>

> **Transformacja fali metodą zbiornikową z krzywą roboczą (zmodyfikowana metoda Pulsa) przez N jednakowych zbiorników** · specyfikacja [`level_pool`](../FORMULAS.md#level_pool) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \frac{s_t}{\Delta t} + \frac{O_t}{2} = \frac{I_{t-1} + I_t}{2} + \frac{s_{t-1}}{\Delta t} - \frac{O_{t-1}}{2},\quad s = \frac{S(O)}{N}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $I_t$ | `inflow_m3s` (ciąg) | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy dopływu i odpływu | min | (0; ∞) | nie podano w źródłach | [5; 720] (źr. 5) |
> | $S_i$ | `table_storage_m3` (ciąg) | Retencja w każdym wierszu tabeli retencja–odpływ, niemalejąca; do odpływu wchodzą tylko jej różnice, więc jej poziom odniesienia jest dowolny | m³ | [0; ∞) | nie podano w źródłach | [0; 3 000 000] (źr. 6) |
> | $O_i$ | `table_outflow_m3s` (ciąg) | Odpływ w każdym wierszu tabeli, niemalejący; zero poniżej korony przelewu | m³/s | [0; ∞) | nie podano w źródłach | [0; 300] (źr. 7) |
> | $N$ | `subreaches` (liczba całkowita) | Liczba zbiorników połączonych szeregowo, z których każdy mieści S / N z tabeli przy tym samym odpływie | – | [1; ∞) | nie podano w źródłach | [1; 6] (źr. 8) |
> | $O_0$ | `initial_outflow_m3s` | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [0; ∞) | nie podano w źródłach | [0; 100] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $O_t$ | `outflow_m3s` (ciąg) | Odpływ w rzędnych dopływu | m³/s | [0; ∞) |
> | $S_t$ | `storage_m3` (ciąg) | Objętość wody we wszystkich zbiornikach w każdej rzędnej | m³ | [0; ∞) |
> | $s_t$ | `last_pool_storage_m3` (ciąg) | Objętość wody w ostatnim zbiorniku w każdej rzędnej, cała objętość przy N = 1 | m³ | [0; ∞) |
> | $S$ | `storage_peak_m3` | Największa objętość wody we wszystkich zbiornikach | m³ | [0; ∞) |
> | $S$ | `storage_steady_m3` | Objętość wody, jaką zbiorniki mieściłyby w stanie ustalonym przy ostatniej rzędnej dopływu | m³ | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | kolumny retencji i odpływu mają tyle samo wierszy | `table_columns_paired` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 9) |
> | S[i] <= S[i+1] i O[i] <= O[i+1]: retencja i odpływ rosną razem z poziomem wody | `table_not_decreasing` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 10) |
> | żaden wiersz nie powtarza poprzedniego: krzywa robocza rośnie z wiersza na wiersz | `table_rows_distinct` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 1) |
> | O[0] <= O0 <= O[-1]: zbiorniki startują w stanie ustalonym odpowiadającym stanowi z tabeli | `initial_outflow_in_table` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
> | dS > 0 na każdym odcinku tabeli, na którym rośnie odpływ, od stanu ustalonego przy najmniejszym przepływie obliczenia do pierwszego wiersza, który osiąga przepływ największy: na odcinku bez retencji żaden krok nie spełnia warunku kroku | `storage_where_outflow_rises` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
> | dt <= 2 min(dS/dO) / N po odcinkach, do których obliczenie może dojść (od stanu ustalonego przy najmniejszym przepływie obliczenia do pierwszego wiersza, który osiąga przepływ największy), z dokładnością do 1e-9 swojej wartości: waga (2K - dt) / (2K + dt) stanu poprzedniego nie jest ujemna na żadnym z nich, więc odpływ pozostaje między najmniejszym a największym przepływem obliczenia | `timestep_within_limit` | odmowa obliczeń: wzór jest nieokreślony | (źr. 12) |
> | S / (N dt) + O / 2 jest skończone i rośnie z wiersza na wiersz w float64: z tej krzywej odczytuje się odpływ | `working_curve_rises` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
> | żaden zbiornik nie napełnia się powyżej ostatniego wiersza (jego krzywa robocza nie przekracza wartości ostatniego wiersza o więcej niż 1e-9 tej wartości): tabela obejmuje wezbranie, nigdy nie stosuje się ekstrapolacji | `flood_below_table_top` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
> | żaden zbiornik nie opróżnia się poniżej pierwszego wiersza (jego krzywa robocza nie spada poniżej wartości pierwszego wiersza o więcej niż 1e-9 wartości ostatniego wiersza): dopływ mniejszy niż pierwszy odpływ z tabeli nie może opróżnić zbiornika | `flood_above_table_bottom` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
>
> **Konwencje**
>
> - jednostki SI: przepływ w m³/s, retencja w m³, krok w min (S / dt z 60 s minuty z tabeli jednostek)
> - odpływ odczytuje się z krzywej roboczej S / (N dt) + O / 2 interpolacją liniową między wierszami tabeli, bo tabela jest między nimi liniowa (NEH 630 interpoluje swoją tabelę roboczą, HEC-HMS rozwiązuje to samo równanie metodą prób i błędów)
> - każdy z N zbiorników połączonych szeregowo mieści S / N przy tym samym odpływie (pododcinki HEC-HMS); każdy zbiornik startuje w stanie ustalonym z odpływem O0, przy największej retencji, dla której tabela daje ten odpływ, więc zbiornik ze strefą martwą poniżej korony przelewu startuje napełniony do korony
> - poziom odniesienia kolumny retencji jest dowolny: do odpływu wchodzą tylko różnice retencji, a podawane retencje mierzy się od tego poziomu
> - stan, który zaokrąglenie wyprowadza poza koniec tabeli o co najwyżej 1e-9 górnej wartości krzywej roboczej, utrzymuje się na tym końcu; przy większym przekroczeniu zbiornik wychodzi poza tabelę, co odrzucają warunki wstępne `flood_below_table_top` i `flood_above_table_bottom`
> - retencję w stanie ustalonym przy ostatniej rzędnej dopływu odczytuje się w skrajnym wierszu tabeli, gdy przepływ wykracza poza ten wiersz
> - transformowane są tylko podane rzędne: `LevelPoolReach` dzieli dłuższy krok na podkroki przy dopływie liniowym między rzędnymi, wydłuża oś czasu i odczytuje stan wody w ostatnim zbiorniku (Tier B, ADR-0008)
>
> **Założenia**
>
> - retencja jest jednoznaczną funkcją odpływu: poziome zwierciadło wody albo odcinek, którego retencja nadąża za odpływem, bez histerezy (NEH 630: zwierciadło wody jest poziome lub prawie poziome)
> - dla koryta NEH 630 wymaga czasu przepływu przez odcinek nie większego niż około połowa czasu wznoszenia dopływu (nie jest to dana wejściowa: nie jest sprawdzane)
> - dopływ jest liniowy między rzędnymi (wzór trapezów)
>
> **Zgodność z obserwacjami według źródeł:** brak: zależność retencja–odpływ odcinka lub zbiornika pochodzi z profili zwierciadła wody, topografii zbiornika lub obserwowanych wezbrań (HEC-HMS TRM, Modified Puls; NEH 630 rozdz. 17); źródła nie podają oceny zgodności samego schematu z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-1 to 17-3, pp. 17-9 to 17-10 (a working curve of O2 against S2/dt + O2/2 is necessary); examples 17-1 and 17-2, tables 17-5 to 17-12, pp. 17-11 to 17-25 <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 2. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, eq. 3; Required Parameters: the initial outflow, a storage vs. discharge relationship and the number of subreaches <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/modified-puls-model>
> 3. US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, modified Puls, eq. 9-12 <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>
> 4. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s
> 5. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d)
> 6. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), tables up to 2.87e6 m3: NEH 630 ch. 17 example 17-2, 1,174.5 ft3/s-d; the catalog's pond, 255,000 m3 (tests/fixtures/pond_rating.csv)
> 7. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), tables up to 283.2 m3/s: NEH 630 ch. 17 example 17-1, 10,000 ft3/s; the catalog's pond, 27.17 m3/s
> 8. Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 (a pond or a reservoir, the default of LevelPoolReach) to 6 pools in the tests of the reach
> 9. US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the storage vs. discharge relationship is a paired data object whose storages cover the entire range met in a simulation; the initial storage is computed from the initial outflow and that relationship <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/modified-puls-model>
> 10. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), tables 17-4 and 17-9 to 17-11: storage and discharge accumulated with the elevation, both rising with it <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 11. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), pp. 17-10 to 17-11: negative outflows whenever dt > 2 S2/O2 (O2/2 > S2/dt); a working curve with any part left of the line of equal values is discarded and computed again with a smaller dt, as WinTR-20 does internally <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
> 12. Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Stability: a level-pool step of at most twice the shortest dS/dO of the segments between the lowest and the highest flow of the run, over the number of sub-reaches; NEH's rule for the whole curve let the outflow exceed the inflow peak on 201 of 1,499 random tables
>
> Funkcja `hydrolog.routing.formulas.level_pool.level_pool_route`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:level_pool -->

**Krok obliczeń.** NRCS wymaga, by krzywa robocza leżała po właściwej stronie linii równych wartości
dla całej tabeli (USDA-NRCS 2014, s. 17-11). Hydrolog stosuje warunek ostrzejszy, na każdym odcinku
tabeli osiąganym przez falę (ADR-0008, ADR-0062): przy załamaniu krzywej odpływu, np. tuż po
przelaniu się wody przez próg przelewu, warunek NRCS przepuszcza krok, przy którym odpływ przekracza
kulminację dopływu. Dłuższy krok Hydrolog dzieli na części (uwaga `timestep_refined`):

<!-- spec:level_pool_substeps -->

<a id="spec-level_pool_substeps"></a>

> **Podział kroku czasowego w metodzie zbiornikowej** · wzór grupy B `level_pool_substeps` (Tier B, CMP-2.2)
>
> **Definicja:** najdłuższy krok, na jaki tabela retencja–odpływ pozwala w danym obliczeniu, 2 min(dS/dO) / N po odcinkach od stanu ustalonego przy najmniejszym przepływie obliczenia do pierwszego wiersza, który osiąga przepływ największy, w min (warunek wstępny `timestep_within_limit` specyfikacji `level_pool`); `LevelPoolReach` dzieli dłuższy krok na najmniejszą liczbę jednakowych podkroków, które go spełniają, każdy koniec z dokładnością do 1e-9 swojej wartości, przy dopływie liniowym między rzędnymi, i odczytuje odpływ z powrotem w oryginalnych rzędnych (uwaga `timestep_refined`) (źr. 1)
>
> **Konwencja:** warunek dla każdego odcinka tabeli jest ostrzejszy niż warunek NEH 630 dla całej krzywej, dt <= 2 S/O w każdym wierszu (krzywa robocza na prawo od linii równych wartości), który pozwala odpływowi przekroczyć kulminację dopływu przy tabeli o gwałtownie zmieniającym się nachyleniu (ADR-0008); ponad 100 podkroków lub więcej rzędnych niż limit jest odrzucane (`unstable_timestep`), podobnie jak odcinek bez retencji, do którego dochodzi obliczenie (`working_curve`)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), pp. 17-10 to 17-11: negative outflows whenever dt > 2 S2/O2; a working curve left of the line of equal values is discarded and computed again with a smaller dt, which WinTR-20 adjusts internally <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
>
> Funkcja `hydrolog.routing.level_pool.timestep_limit_min`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-junction_sum"></a>

> **Sumowanie hydrogramów w węźle sieci** · wzór grupy B `junction_sum` (Tier B, CMP-2.2)
>
> **Definicja:** hydrogram węzła: suma jego dopływów rzędna po rzędnej na najdłuższej z ich osi czasu, przy czym krótszy hydrogram przedłuża się jego ostatnią wartością (źr. 1)
>
> **Konwencja:** jeden krok czasowy i jeden początek dla wszystkich źródeł sieci, bez przepróbkowania; przedłużenie obciętego odpływu (`tail_truncated`) wartością większą od zera dodaje objętość poniżej węzła, o czym informuje ostrzeżenie z odcinka powyżej
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog's computation paths, section 3.9.7, and ADR-0008, docs/COMPUTATION_PATHS.md, Time axes: a junction holds a shorter hydrograph at its last value; one step, nothing resampled
>
> Funkcja `hydrolog.routing.network._sum`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
(`subreaches_adjusted`), a dla wielu zlewni zgłosił wartości spoza zakresów stosowania wzorów
(`outside_applicability`), np. powierzchnię większą niż zalecana dla hydrogramu SCS. Wynik nie jest
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

<a id="spec-muskingum_cunge_fallback"></a>

> **Zastąpienie metody Muskingum-Cunge kaskadą zbiorników liniowych** · wzór grupy B `muskingum_cunge_fallback` (Tier B, CMP-2.2)
>
> **Definicja:** odcinek, dla którego nie ma siatki w granicach 100 podkroków, transformuje się jako n = L / D zbiorników liniowych (zaokrąglone, połowa w górę, co najmniej 1) o K = L / (n c) kaskadą `CascadeReach` (uwaga `diffusion_dominated`) (źr. 1)
>
> **Konwencja:** n zbiorników o średniej n K i wariancji n K^2 zachowuje średni czas przepływu L / c fali dyfuzyjnej oraz, na ile pozwala całkowite n, jej wariancję D L / c^2 = 2 mu L / c^3 przy mu = Q / (2 T S0) (HEC-HMS TRM, model Muskingum-Cunge, wzór 5)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hydrolog ADR-0026: a reach without a Muskingum-Cunge grid, linear reservoirs with a warning, not a refusal, Decision, points 1 and 2 (docs/decisions/0026-a-reach-without-a-muskingum-cunge-grid.md)
>
> Funkcja `hydrolog.routing.cunge._reservoirs`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
