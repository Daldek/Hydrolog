# 4. Czas koncentracji

Czas koncentracji $t_c$ (ang. *time of concentration*) wyznacza skalę czasu, w jakiej zlewnia odpowiada na
opad. Od niego zależy czas trwania deszczu projektowego (rozdz. 2), kształt hydrogramu jednostkowego SCS i
Clarka (rozdz. 5), a w odwodnieniu dróg i lotnisk — czas dopływu wody do wpustu. Zarazem jest to jedna z
najmniej pewnych wielkości hydrologii stosowanej: różne wzory dają dla tej samej zlewni wyniki różniące się
kilkakrotnie, a czas reakcji zmierzony w zlewni zmienia się od wezbrania do wezbrania.

Rozdział omawia sześć metod, które liczy Hydrolog: wzór Kirpicha, metodę opóźnienia NRCS, wzór Giandottiego,
wzór FAA, wzór Kerby'ego i metodę Kerby'ego–Kirpicha. Przy każdej podaje ideę i pochodzenie, dane, których
wymaga źródło, zakres stosowania, przykład z wynikiem Hydrologa, interpretację wyniku i typowe błędy. Na końcu
porównuje wszystkie metody na zlewni Kamiennika po Świerzawę i pokazuje, jak wybór metody zmienia hydrogram
projektowy.

Równanie, zmienne z jednostkami, stałe i trzy zakresy wartości każdej metody stoją w ramce generowanej ze
specyfikacji formuły w kodzie Hydrologa (zob. „Jak czytać” w [README](README.md) i
[dodatek D](D-weryfikacja.md)). Tekst rozdziału ich nie powtarza: wyjaśnia, skąd się wzięły, kiedy ich
używać i jak czytać wynik.

## 4.1 Definicje

**Czas koncentracji** to czas, w którym woda dopływa z punktu zlewni najdalszego hydraulicznie (ang.
*hydraulically most distant point*) do przekroju zamykającego (ang. *outlet*). Najdalszy hydraulicznie jest
punkt o najdłuższym czasie dopływu, „niekoniecznie punkt o największej odległości spływu do przekroju”
(USDA-NRCS 2010, s. 15-3). Polska metodyka określa go jako czas, „w którym kropla wody dopłynie z
najdalszego, pod względem hydraulicznym, punktu zlewni do przekroju obliczeniowego” (KZGW 2017, s. 105). W
analizie hydrogramu NRCS mierzy $t_c$ od końca opadu efektywnego do punktu przegięcia na gałęzi opadania
bezwymiarowego hydrogramu jednostkowego (USDA-NRCS 2010, s. 15-3).

**Czas opóźnienia** (ang. *lag time*) $t_{lag}$ to według NRCS odstęp między środkiem masy opadu efektywnego a
kulminacją odpływu. Dla przeciętnych zlewni naturalnych, w których odpływ formuje się w przybliżeniu
równomiernie, NEH 630 przyjmuje opóźnienie jako stały ułamek czasu koncentracji (USDA-NRCS 2010, wzór 15-3,
za Mockusem 1957 i Simasem 1996); wartość tego ułamka podaje ramka metody NRCS (p. 4.5). W polskich pracach
pomiarowych opóźnienie wyznacza się często metodą momentów, jako odstęp między środkami ciężkości opadu
efektywnego i hydrogramu odpływu bezpośredniego (Banasik i Barszcz 2004; Krajewski i Banasik 2013). To inna
wielkość niż opóźnienie NRCS, więc porównania obu trzeba czytać ostrożnie.

**Czas przepływu** (czas dobiegu, ang. *travel time*) odcinka drogi wody to jego długość podzielona przez
średnią prędkość przepływu. Metoda prędkości NRCS (ang. *velocity method*) sumuje czasy przepływu kolejnych
odcinków najdłuższej drogi: spływu po stoku, spływu skoncentrowanego i przepływu korytem (USDA-NRCS 2010,
wzór 15-7). Hydrolog tej metody nie liczy; najbliższa jej jest metoda Kerby'ego–Kirpicha (p. 4.9), która dzieli
drogę na odcinek po stoku i odcinek korytowy.

**Krytyczny czas trwania deszczu** (ang. *critical storm duration*) $D_{kr}$ to czas trwania opadu, który przy
przyjętych charakterystykach opadu i zlewni wywołuje największe wezbranie. Według polskiej metodyki przy
stałym natężeniu deszczu i stałym współczynniku odpływu jest nim czas koncentracji. Ta sama metodyka
przestrzega jednak: „W wielu przypadkach stwierdzono, że czasy koncentracji obliczane z podanych w literaturze
wzorów są znacznie zaniżone”, i za niemieckim związkiem DVWK (1984) podaje przedział $t_c < D_{kr} < 2\,t_c$
(KZGW 2017, s. 105). Dlatego wezbranie projektowe liczy się zwykle dla kilku czasów trwania deszczu i wybiera
ten, który daje największą kulminację (rozdz. 2).

Trzy rzeczy warto mieć w pamięci od początku:

1. **Czas reakcji nie jest stałą zlewni.** W zurbanizowanej zlewni Potoku Służewieckiego po przekrój Wyścigi
   (28,7 km²) opóźnienie wyznaczone z kolejnych wezbrań zmieniało się od 1,44 do 15,8 h, przy średniej
   5,65 h (Krajewski i Banasik 2013). Ramka metody NRCS przytacza podobny przykład z NEH 630.
2. **Wzory dają bardzo różne wyniki.** Grimaldi i in. (2012) nazwali czas koncentracji „paradoksem”
   współczesnej hydrologii: oszacowania różnymi metodami mogą się różnić nawet o 500 % (za Beven 2020). Na
   Kamienniku rozrzut czterech wzorów dla całej zlewni jest ponad dwukrotny (p. 4.10).
3. **Wzór niesie dane, na których powstał.** Każdy z omawianych wzorów wyprowadzono na zlewniach innego
   kraju, klimatu i wielkości. Poza tymi danymi wynik jest ekstrapolacją; Hydrolog liczy go, ale mówi o tym
   w uwagach (p. 4.3).

## 4.2 Długości i spadki: co jest czym

Najczęstszym błędem w obliczeniach $t_c$ nie jest zły wybór wzoru, tylko podanie mu niewłaściwej długości
albo niewłaściwego spadku. Każde źródło definiuje swoje wielkości, a Hydrolog bierze dla każdej metody
wyłącznie pola, które definiuje jej źródło, bez zastępników ([ADR-0019](../decisions/0019-tc-from-the-inputs-its-source-defines.md)):
zlewnia bez najdłuższej drogi spływu nie zostanie policzona wzorem Kirpicha z długością cieku, tylko
`tc watershed` zakończy się błędem `validation_error` z powodem `missing_field` i nazwą brakującego pola.

| Wielkość | Ang. | Definicja | Metody (pole `WatershedParameters`) |
|---|---|---|---|
| najdłuższa droga spływu, długość hydrauliczna | longest flow path, hydraulic length | droga wody po kierunkach spływu od punktu najdalszego hydraulicznie (zwykle na dziale wodnym, czasem na grzbiecie wewnątrz zlewni) do przekroju zamykającego | Kirpich, NRCS, Kerby–Kirpich (`flow_path_length_km`) |
| spadek drogi spływu | flow-path slope | wysokość początku tej drogi minus wysokość przekroju, podzielona przez jej długość | Kirpich, Kerby–Kirpich (`flow_path_slope_m_per_m`) |
| ciek główny | main channel | od przekroju w górę cieku do początku koryta | Giandotti (`channel_length_km`) |
| średni spadek terenu zlewni | average watershed land slope | średni spadek stoków całej zlewni | NRCS (`mean_slope_m_per_m`) |
| odcinek spływu po stoku i jego spadek | overland (sheet) flow length and slope | od punktu najdalszego do początku wyraźnego koryta | FAA, Kerby, Kerby–Kirpich (`overland_length_km`, `overland_slope_m_per_m`) |
| wyniesienie średniej wysokości zlewni nad przekrój | mean basin elevation above the outlet | średnia wysokość zlewni minus wysokość przekroju | Giandotti (`elevation_mean_m` − `elevation_min_m`) |
| spadek wyrównany profilu podłużnego | equal-area slope | spadek prostej przez przekrój, która odcina nad profilem i pod nim równe pola | żadna metoda $t_c$; metoda Lutza (rozdz. 5) |
| długość zlewni | watershed (basin) length | odcinek prosty we wskaźnikach kształtu (rozdz. 1) | żadna metoda $t_c$ |

**Spadki podaje się w m/m, nie w procentach**, a długości w kilometrach. Źródła używają stóp, cali i
procentów; Hydrolog przelicza dane do jednostek źródła dokładnymi przelicznikami i liczy wzór w tej postaci,
w której go opublikowano ([ADR-0052](../decisions/0052-the-time-of-concentration-formulas-by-specs.md)).

Hydrograf wyznacza te wielkości z numerycznego modelu terenu: najdłuższą drogę spływu jako największą
odległość spływu po kierunkach D8 od przekroju, jej spadek z wysokości jej początku i przekroju, średni
spadek terenu jako średnią spadków komórek, a ciek główny od przekroju do początku koryta. Dla zlewni
Kamiennika po Świerzawę (dorzecze Kaczawy) daje to wartości z pliku `tests/fixtures/kamiennik.json`
repozytorium Hydrologa (przykład z instrukcji Hydrologa; najdłuższą drogę spływu wyznaczył Hydrograf
5 listopada 2026 r.):

| Pole | Wartość | Znaczenie |
|---|---|---|
| `area_km2` | 37,22 km² | powierzchnia zlewni |
| `flow_path_length_km` | 15,88 km | najdłuższa droga spływu, od działu wodnego (440,16 m n.p.m.) do przekroju (258,72 m n.p.m.) |
| `flow_path_slope_m_per_m` | 0,0114 | spadek tej drogi |
| `flow_path_equal_area_slope_m_per_m` | 0,00848 | spadek wyrównany jej profilu (metoda Lutza, rozdz. 5) |
| `channel_length_km` | 14,78 km | ciek główny do początku koryta |
| `channel_slope_m_per_m` | 0,0142 | spadek cieku głównego (żadna metoda $t_c$ go nie używa) |
| `mean_slope_m_per_m` | 0,082 | średni spadek terenu zlewni |
| `elevation_mean_m`, `elevation_min_m` | 363,2 i 257,3 m n.p.m. | średnia i najniższa wysokość zlewni |
| `cn` | 65 | liczba CN dla AMC II (rozdz. 3) |
| `overland_length_km`, `overland_slope_m_per_m` | 0,3 km; 0,082 | odcinek spływu po stoku i jego spadek (wartości przykładu instrukcji) |
| `runoff_coeff`, `retardance` | 0,25; 0,4 | współczynnik C metody FAA i współczynnik N Kerby'ego, przyjęte w przykładzie |

Te liczby pokazują, jak bardzo różnią się „spadki” jednej zlewni: spadek terenu (0,082) jest ponad siedem
razy większy od spadku najdłuższej drogi spływu (0,0114), a spadek cieku (0,0142) leży między nimi. Wysokość
przekroju na końcu drogi spływu (258,72 m) różni się nieco od najniższej wysokości zlewni (257,3 m), którą
Hydrolog bierze we wzorze Giandottiego za wysokość przekroju.

## 4.3 Trzy zakresy i uwagi Hydrologa

Każda zmienna w ramce ma trzy zakresy (standard obliczeń Nogat, CMP-1.3–1.5):

- **Zakres fizyczny** (ang. *physical range*): wartości, które mogą istnieć, np. dodatnia długość i dodatni
  spadek. Poza nim Hydrolog odmawia obliczenia: spadek 0 kończy się błędem `validation_error` z powodem
  `exclusive_minimum`, a droga spływu nie dłuższa od odcinka po stoku w metodzie Kerby'ego–Kirpicha —
  błędem z powodem `outside_physical_range` i nazwą naruszonego ograniczenia.
- **Zakres stosowania** (ang. *applicability range*): wartości z danych, na których wzór wyprowadzono lub
  sprawdzono, wraz ze źródłem, które je podaje. Poza nim Hydrolog liczy, ale dodaje ostrzeżenie o kodzie
  `outside_applicability`, nazwanym tak jak w standardzie od wersji 0.9.0; do wersji 0.8.1 nazywało się
  `outside_typical_range`
  ([ADR-0070](../decisions/0070-the-notice-outside-applicability.md)).
  Również pomoc poleceń (`hydrolog tc kirpich --help`) opisuje te przedziały słowem „typowo”; należy je
  czytać jako „w danych źródła”.
- **Zakres typowy** (ang. *typical range*): wartości spotykane w praktyce, tu — w zlewniach, które Hydrograf
  przekazuje Hydrologowi. Nie wywołuje uwag; mówi, gdzie wzór jest naprawdę używany.

Dla większości wzorów z USA zakres typowy polskich zlewni leży poza zakresem stosowania. Wynik jest wtedy
ekstrapolacją i uwaga Hydrologa tego nie naprawia — tylko o tym przypomina. Gdy źródło nie podaje zakresu
danej zmiennej, ramka mówi „nie podano” i Hydrolog nie ma czego sprawdzić: przy metodzie NRCS i FAA spadek
podany w procentach przejdzie bez ostrzeżenia (p. 4.5 i 4.7).

Polecenie `tc watershed` sprawdza dodatkowo powierzchnię zlewni, której sam wzór nie zawiera, z powierzchniami
zlewni źródła (podanymi w założeniach ramek). Polecenia jednej metody (`tc kirpich` i pozostałe) powierzchni
nie znają i tej uwagi nie dają.

## 4.4 Wzór Kirpicha

**Idea.** Czas koncentracji małej zlewni rolniczej z wyraźnym korytem, policzony z długości i spadku drogi
wody. Wzór nie zawiera pokrycia terenu ani szorstkości: opisuje głównie przepływ korytem.

**Pochodzenie.** Podstawą były pomiary C.E. Ramsera (1927) w małych zlewniach rolniczych koło Jackson w
stanie Tennessee. Kirpich (1940) opublikował krótki artykuł z wykresem i krzywymi, bez jawnego wzoru; postać
potęgową podali Rowe i Thomas (1942) (Mota i Kobiyama 2015). Stąd nazwa „postać z Tennessee” w tytule
ramki.

<!-- spec:kirpich -->

<a id="spec-kirpich"></a>

> **Czas koncentracji według wzoru Kirpicha (postać z Tennessee)** · specyfikacja [`kirpich`](../FORMULAS.md#kirpich) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_c = 0{,}0078\,L^{0{,}77}\,S^{-0{,}385},\quad L\ \mathrm{[ft]}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $L$ | `length_km` | Długość najdłuższej drogi spływu, od przekroju do punktu zlewni najdalszego hydraulicznie | km | (0; ∞) | [0,10668; 1,2192] (źr. 5) | [0,05; 30] (źr. 6) |
> | $S$ | `slope_m_per_m` | Spadek najdłuższej drogi spływu: wysokość jej początku minus wysokość przekroju, podzielona przez jej długość | m/m | (0; ∞) | [0,025; 0,1] (źr. 7) | [0,002; 0,11] (źr. 8) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}0078$ | `kirpich_coefficient` | Współczynnik wzoru Kirpicha | 0,0078 | $\mathrm{min\,ft^{-0{,}77}}$ | (źr. 9) |
> | $0{,}77$ | `kirpich_length_exponent` | Wykładnik długości drogi spływu | 0,77 | – | (źr. 10) |
> | $-0{,}385$ | `kirpich_slope_exponent` | Wykładnik spadku drogi spływu | −0,385 | – | (źr. 10) |
>
> **Konwencje**
>
> - postać z Tennessee w jednostkach źródła: L w stopach przez dokładny przelicznik 0,3048 m/ft z tabeli jednostek, tc w minutach; stałe SI 0,0195 (L w m; Roussel i in. 2005, TxDOT 2019) i 0,01947 (WR-D-71-1, 2023) są zaokrągleniami 0,0078 (1/0,3048)^0,77 = 0,019472, a stała Hydrologu 3,981 (L w km) do wersji 0.8.1 była o 0,136 % większa od dokładnej 3,97560
> - L wzdłuż cieku od przekroju do najdalszego punktu zlewni, czyli najdłuższa droga spływu, a S to różnica wysokości jej końców podzielona przez L (Fang i in. 2005, wzór 3.14) — ani koryto do jego początku, ani średni spadek zlewni; Kirpich (1940) mierzył L do najwyższego punktu zlewni (Mota i Kobiyama 2015, s. 56)
> - S w m/m (ft/ft), nie w procentach
> - sam wzór nie ma poprawki małych spadków; Kerby–Kirpich stosuje ją w swojej części korytowej (Cleveland i in. 2012)
>
> **Założenia**
>
> - małe zlewnie wiejskie z wyraźnymi korytami, 1,25-112 akrów (0,005-0,45 km², sprawdzane przez `WatershedParameters.calculate_tc`), a więc głównie przepływ korytem; Kirpich stosował wzór do ok. 200 akrów (Roussel i in. 2005, s. 5); mnożniki 0,4 dla spływu po stoku po betonie lub asfalcie i 0,2 dla koryt betonowych z praktyki amerykańskiej (Fang i in. 2005, s. 22) nie są stosowane
> - zlewnie Hydrografu (drogi spływu 0,05-30 km) leżą w większości poza zakresem danych Kirpicha (0,107-1,22 km): ich wyniki są ekstrapolacją, z uwagą
>
> **Zgodność z obserwacjami według źródeł:** Kirpich (1940) opublikował krzywe dla sześciu zlewni Ramsera (1927) koło Jackson w stanie Tennessee (z siedmiu pominięto zlewnię 2), a nie wzór; Mota i Kobiyama (2015, s. 57-58) otrzymują z własnego dopasowania do tych danych wyniki odbiegające od wzoru o 2 do 9 % w zakresie L 350-4 000 ft i S 0,025-0,1, a poza nim do 30 %
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22 (L the channel length to the most remote point, S its drop over L) <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 2. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, eq. 7, p. 7; supplement, p. 29 (K = 0.0078 for feet) <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 3. Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, pp. 56-58: Kirpich's curves and data of 1940, table 1; the formula published by Rowe and Thomas (1942) <https://revistas.abrhidro.org.br/article.php?Article=5027>
> 4. Florida Department of Transportation (2024). Drainage Design Guide, chapter 2, eq. 2.2-9 <https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/roadway/drainage/files/drainagedesignguide/chapter2.pdf>
> 5. Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, p. 58: the data of Kirpich (1940), table 1, give the range of the formula, L between 350 and 4,000 ft <https://revistas.abrhidro.org.br/article.php?Article=5027>
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km
> 7. Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, p. 58: the data of Kirpich (1940), table 1, give the range of the formula, S from 0.025 to 0.1 <https://revistas.abrhidro.org.br/article.php?Article=5027>
> 8. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow path slopes of 0.00244 to 0.1055 m/m
> 9. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; the same in Roussel et al. (2005) eq. 7, Mota and Kobiyama (2015) and FDOT (2024) eq. 2.2-9 <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 10. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.kirpich`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:kirpich -->

**Jednostki.** Hydrolog liczy wzór w jednostkach źródła, z długością przeliczoną dokładnie na stopy, i
podaje wynik w minutach (`tc_min`) i godzinach (`tc_h`). W literaturze krążą postacie metryczne ze stałą
zaokrągloną na różne sposoby: teksańska (TxDOT) i polska (WR-D-71-1 2023) różnią się ostatnią cyfrą. Wyniki
różnią się wtedy o ułamki procenta, ale stała zawsze musi pasować do jednostki długości (ramka, konwencje).
Do wersji 0.8 Hydrolog używał własnej stałej dla kilometrów; od wersji 0.9 jego wyniki są nieco krótsze
([ADR-0052](../decisions/0052-the-time-of-concentration-formulas-by-specs.md)).

**Zakres stosowania.** Dane Kirpicha to bardzo małe zlewnie z czasami koncentracji rzędu minut (ramka).
Zlewnie, dla których w Polsce liczy się hydrogramy projektowe, są o rzędy wielkości większe; wynik jest dla
nich ekstrapolacją i Hydrolog dodaje uwagę.

**Zastosowanie w Polsce.** Wytyczne odwodnienia dróg WR-D-71-1 (2023, §5.4.2, wzór 5.4.2.2) podają wzór
Kirpicha w jednostkach metrycznych do czasu koncentracji spływu ze zlewni w stanie naturalnym: L to odległość
od przekroju do najdalszego punktu zlewni, J — spadek między tymi punktami. W Hydrologu Kirpich jest metodą
domyślną (`tc_method`) poleceń `hydrograph generate` i `report generate` — wygodną, ale dla większości
polskich zlewni leżącą daleko poza swoimi danymi.

**Przykład 4.1. Zbiornik retencyjny przy drodze (WR-D-71-1 2023).** Droga wody L = 1,55 km, spadek
J = 0,025:

```sh
hydrolog tc kirpich --length-km 1.55 --slope-m-per-m 0.025
```

Hydrolog daje $t_c$ = 23,05 min (0,384 h); wytyczne podają 23 min. Uwaga `outside_applicability` dotyczy
długości: droga 1,55 km jest dłuższa niż drogi wody w zlewniach Kirpicha.

**Interpretacja.** Czas rośnie z długością drogi i maleje ze spadkiem, potęgowo (wykładniki w ramce). Na
Kamienniku podwojenie drogi (31,76 km zamiast 15,88 km przy tym samym spadku) wydłuża czas ze 187,13 do
319,11 min, czyli o 70,5 %.

**Typowe błędy** (liczby dla Kamiennika, gdzie poprawny wynik to 187,13 min):

- **Spadek w procentach zamiast w m/m.** `--slope-m-per-m 1.14` daje 31,78 min, sześć razy za mało. Tu
  Hydrolog ostrzega, bo 1,14 leży poza zakresem stosowania spadku, ale przy metodach bez takiego zakresu
  ostrzeżenia nie będzie.
- **Ciek główny do początku koryta zamiast drogi do działu wodnego.** 14,78 km przy spadku cieku 0,0142
  daje 162,71 min, o 13 % mniej. Tak liczył Hydrolog przed wersją 0.8.0, która dodała pole najdłuższej
  drogi spływu ([ADR-0019](../decisions/0019-tc-from-the-inputs-its-source-defines.md)).
- **Średni spadek terenu zamiast spadku drogi.** 0,082 daje 87,55 min, o 53 % mniej.
- **Stała z błędnego wydruku.** NEH 630 (2010, zał. 15A; wydanie z 2025 r.) drukuje stałą Kirpicha o ok.
  10 % za małą, a podręcznik INDOT (rozdz. 29) — postać ze stałą po złej stronie potęgi, zawyżającą wynik o
  3,5 %. Przykład 29-7.8 z INDOT jest w danych testowych Hydrologa zapisany jako rozbieżność z winy źródła.
- **Spadek bliski zera.** Wynik rośnie wtedy bez ograniczeń, a spadek 0 Hydrolog odrzuca. Sam wzór
  Kirpicha nie ma poprawki małych spadków; ma ją metoda Kerby'ego–Kirpicha (p. 4.9).

## 4.5 Metoda opóźnienia NRCS

**Idea.** Mockus (1961) powiązał opóźnienie zlewni z długością drogi spływu, średnim spadkiem terenu i
retencją potencjalną $S$ wyznaczoną z liczby CN, która w tym równaniu zastępuje współczynnik oporu
powierzchni dla spływu (ang. *retardance factor*). Czas koncentracji wynika z opóźnienia (USDA-NRCS 2010,
wzory 15-3, 15-4a i 15-4b; tak samo w wydaniu zmienionym 210 H 630, 2025). Wbrew częstym odwołaniom
TR-55 (1986) tych równań nie zawiera
([ADR-0019](../decisions/0019-tc-from-the-inputs-its-source-defines.md)).

<!-- spec:nrcs -->

<a id="spec-nrcs"></a>

> **Czas koncentracji z równania opóźnienia zlewni NRCS (Mockus 1961)** · specyfikacja [`nrcs`](../FORMULAS.md#nrcs) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> T_c = \frac{\ell^{0{,}8}\,(S + 1)^{0{,}7}}{1140\,Y^{0{,}5}},\quad S = \frac{1000}{CN} - 10,\quad \ell\ \mathrm{[ft]},\ S\ \mathrm{[in]},\ Y\ [\%]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\ell$ | `length_km` | Długość spływu: najdłuższa droga, którą woda spływa od działu wodnego do przekroju | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 3) |
> | $Y$ | `slope_m_per_m` | Średni spadek terenu zlewni, nie spadek drogi spływu | m/m | (0; ∞) | nie podano w źródłach | [0,04; 0,19] (źr. 4) |
> | $CN$ | `cn` | Liczba CN dla AMC II, zastępująca współczynnik oporu cn' | – | [1; 100] | [50; 95] (źr. 5) | [51,8; 81,4] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1140$ | `tc_denominator` | Mianownik wzoru na opóźnienie zlewni | 1140 | $\mathrm{ft^{0{,}8}\,in^{0{,}7}\,h^{-1}\,\%^{0{,}5}}$ | (źr. 7) |
> | $0{,}8$ | `length_exponent` | Wykładnik długości spływu | 0,8 | – | (źr. 8) |
> | $0{,}7$ | `retention_exponent` | Wykładnik członu z retencją maksymalną | 0,7 | – | (źr. 8) |
> | $1$ | `retention_shift` | Składnik dodawany do retencji maksymalnej | 1 | in | (źr. 9) |
> | $1000$ | `s_scale` | Licznik ilorazu przez cn' w retencji maksymalnej (w calach) | 1000 | in | (źr. 10) |
> | $10$ | `s_offset` | Składnik odejmowany od ilorazu w retencji maksymalnej (w calach) | 10 | in | (źr. 10) |
> | $100$ | `percent` | Przelicznik spadku z m/m na procenty | 100 | % na m/m | (źr. 11) |
>
> **Konwencje**
>
> - wzór 15-4b w jednostkach źródła: l w stopach i S w calach przez dokładne przeliczniki 0,3048 m/ft i 25,4 mm/cal z tabeli jednostek, Y w procentach (100 na m/m), Tc w godzinach, przeliczany na minuty; w SI ma postać 100 l[m]^0,8 (S[mm] + 25,4)^0,7 / (7068,86 Y^0,5), gdzie 100/7068,86 = 0,0141466, podczas gdy Hydrolog do wersji 0.8.1 stosował 0,01416 (+0,095 %, TRIAGE T8)
> - Tc = lag / 0,6 (wzór 15-3, Mockus 1957; Simas 1996); hydrogram jednostkowy przyjmuje tp = D/2 + 0,6 Tc (USACE HEC-HMS Technical Reference Manual, hydrogram jednostkowy SCS, wzory 1 i 3); TR-55 (1986) nie podaje zależności dla opóźnienia
> - l to najdłuższa droga spływu od działu wodnego do przekroju (s. 15-5); Y to średni spadek terenu zlewni, „nie mylić ze spadkiem drogi spływu” (s. 15-5)
> - współczynnik oporu cn' to CN dla AMC II (s. 15-6: CN służy jako zamiennik cn'); S = 0 przy CN 100; ułamkowa CN, będąca średnią ważoną, jest używana bez zmian
>
> **Założenia**
>
> - przeciętne naturalne warunki zlewni z w przybliżeniu równomiernym rozkładem odpływu (wzór 15-3); powierzchnię 24 zlewni, 0,005-24 km², sprawdza `WatershedParameters.calculate_tc`
> - drogi spływu Hydrografu (0,05-30 km) i CN jego zlewni (51,8-81,4) leżą w zakresie CN równania; CN poniżej 50 lub powyżej 95 daje uwagę
>
> **Zgodność z obserwacjami według źródeł:** NEH 630-15 (s. 15-6) podaje dane równania: 24 zlewnie od 1,3 akra do 9,2 mili kwadratowej, w większości poniżej 2 000 akrów (Mockus 1961), oraz to, że Folmar i Miller (2000) uznali za rozsądną górną granicę do 19 mil kwadratowych; tab. 15-4 pokazuje, że opóźnienie jednej zlewni zmienia się od opadu do opadu (Jones Falls, Maryland: od 4,16 do 6,91 h)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-3, 15-4a and 15-4b and their variables, pp. 15-3 to 15-6; the example of the lag method, p. 15-12 <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 2. USDA-NRCS (2025). 210 NEH Part 630 Hydrology, Subpart F: Time of Concentration (amended June 2025), eqs. 630.15-3, 630.15-4a and 630.15-4b, the same equations and limits <https://directives.nrcs.usda.gov/sites/default/files2/1749749287/Subpart%20F%20%E2%80%93%20Time%20of%20Concentration.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: mean land slopes of 0.0500 to 0.1831 m/m
> 5. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), p. 15-6: a CN of less than 50, or greater than 95 should not be used in the solution of equations 15-4a and 15-4b (Mockus 1961) <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 6. Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the 223 catchments of the Hydroni run h07 (2,941 km2), Consequences: CN of AMC II 51.8 to 81.4, median 70.8 <https://github.com/Daldek/Hydrograf/blob/develop/docs/decisions/0075-cn-of-soil-cover-complexes.md>
> 7. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eq. 15-4b, p. 15-5: eq. 15-4a (1,900) with L = 0.6 Tc <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 8. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-4a and 15-4b, p. 15-5 <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 9. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-4a and 15-4b, p. 15-5: S + 1 <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 10. USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), p. 15-5: S = 1,000 / cn' - 10 <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
> 11. BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01 <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.nrcs`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:nrcs -->

**Dane.** Długość ℓ to najdłuższa droga spływu od działu wodnego do przekroju. Spadek Y to średni spadek
terenu całej zlewni, „nie mylić ze spadkiem drogi spływu” (USDA-NRCS 2010, s. 15-5). CN to liczba krzywej
dla przeciętnych warunków wilgotnościowych AMC II (rozdz. 3); ułamkowe CN, np. średnią ważoną z
`cn weighted`, Hydrolog przyjmuje bez zaokrąglania.

**Wilgotność poprzedzająca.** CN występuje tu jako miara oporu powierzchni, nie strat. Polecenie
`hydrograph generate` z `--amc III` liczy straty z CN przeliczonego na AMC III (na Kamienniku 81), a czas
koncentracji nadal z CN 65:

```sh
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method nrcs --amc III --hietogram-type beta --total-mm 101.82 --duration-min 720 --timestep-min 10
```

W wyniku `tc_min` = 399,39 min, tyle samo co przy AMC II, a `cn_adjusted` = 81: wilgotność zmienia opad
efektywny, nie czas koncentracji. Inaczej działa opcja `--cn` podana obok zlewni: zastępuje jej CN w całym
obliczeniu, także w czasie koncentracji ([COMPUTATION_PATHS](../COMPUTATION_PATHS.md), p. 3.7.1).

**Zakres stosowania.** Równanie wyprowadzono na niewielkich zlewniach rolniczych USA; ramka podaje ich
wielkość i przedział CN, poza którym NEH 630 odradza równanie. Sprawdzenia w Polsce: Banasik i Barszcz (2004)
porównali opóźnienia z pomiarów i ze wzoru SCS (w ich zapisie L — długość cieku głównego, $J_z$ — średni
spadek zlewni w %). Dla Zagożdżonki po Czarną (23,4 km², Równina Radomska) otrzymali 7,00 h z pomiarów i
5,54 h ze wzoru, dla Bauny w Hesji (49,1 km²) 2,03 h i 2,55 h; wzór SCS należał w obu zlewniach do
najbliższych pomiarom. W zurbanizowanej zlewni Potoku Służewieckiego (28,7 km²) wzór USDA-SCS dał 9,06 h
wobec zmierzonych średnio 5,65 h (Krajewski i Banasik 2013). W obu pracach opóźnienie mierzono między
środkami ciężkości opadu efektywnego i odpływu (p. 4.1), a nie do kulminacji: porównania pokazują rząd
błędu, nie poprawkę do wzoru.

**Przykład 4.2. Mawney Brook (NEH 630).** Zlewnia w Rhode Island, ℓ = 3865 ft = 1,178052 km, Y = 4,79 %,
czyli 0,0479 m/m, CN 63 (USDA-NRCS 2010, §630.1504(a), s. 15-12):

```sh
hydrolog tc nrcs --length-km 1.178052 --slope-m-per-m 0.0479 --cn 63
```

Hydrolog daje 68,68 min, czyli 1,145 h; NEH 630 podaje 1,14 h.

**Kamiennik.** ℓ = 15,88 km, Y = 0,082, CN 65:

```sh
hydrolog tc nrcs --length-km 15.88 --slope-m-per-m 0.082 --cn 65
```

Wynik: 399,39 min (6,66 h), najdłuższy czas spośród metod (p. 4.10). `tc watershed` dodaje uwagę o
powierzchni: Kamiennik jest większy od zlewni, na których powstało równanie.

**Interpretacja.** Czas skraca się z rosnącym CN (powierzchnia gładsza, mniej retencji) i ze spadkiem
terenu, a wydłuża z długością drogi. Wpływ CN jest duży: przy tej samej drodze i tym samym spadku Kamiennika
CN 55 daje 515,06 min, a CN 85 — 222,31 min, 2,3 raza mniej.

**Typowe błędy** (Kamiennik, poprawny wynik 399,39 min):

- **Spadek drogi spływu lub cieku zamiast średniego spadku terenu.** `--slope-m-per-m 0.0114` daje
  1071,17 min, 2,7 raza za dużo — bez ostrzeżenia, bo źródło nie podaje zakresu Y.
- **Opóźnienie wzięte za czas koncentracji** albo odwrotnie (zależność między nimi w ramce); `tc nrcs`
  zwraca czas koncentracji.
- **Godziny i minuty.** Równanie w źródle daje godziny; Hydrolog podaje oba wyniki.
- **Długość cieku do źródła zamiast najdłuższej drogi spływu od działu wodnego.**

## 4.6 Wzór Giandottiego

**Idea.** Czas koncentracji (wł. *tempo di corrivazione*) dużej zlewni z jej powierzchni, długości cieku
głównego i wyniesienia średniej wysokości zlewni nad przekrój. Giandotti (1934) wyprowadził go dla rzek
środkowych i północnych Włoch; wzór pozostaje podstawą praktyki włoskiej, np. dyrektywy Urzędu Dorzecza
Padu o wezbraniu projektowym (Autorità di bacino del fiume Po 2001, §6.1).

<!-- spec:giandotti -->

<a id="spec-giandotti"></a>

> **Czas koncentracji według wzoru Giandottiego (1934)** · specyfikacja [`giandotti`](../FORMULAS.md#giandotti) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_c = \frac{4\sqrt{A} + 1{,}5\,L}{0{,}8\sqrt{H}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | [170; 70 000] (źr. 3) | [0,0003; 250] (źr. 4) |
> | $L$ | `length_km` | Długość cieku głównego | km | (0; ∞) | nie podano w źródłach | [0,007; 27] (źr. 5) |
> | $H$ | `elevation_diff_m` | Średnia wysokość zlewni ponad przekrojem | m | (0; ∞) | nie podano w źródłach | [2,5; 210] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $4$ | `area_factor` | Współczynnik przy pierwiastku z powierzchni zlewni | 4 | $\mathrm{h\,km^{-1}\,m^{0{,}5}}$ | (źr. 1) |
> | $1{,}5$ | `length_factor` | Współczynnik przy długości cieku głównego | 1,5 | $\mathrm{h\,km^{-1}\,m^{0{,}5}}$ | (źr. 1) |
> | $0{,}8$ | `height_factor` | Współczynnik przy pierwiastku ze średniej wysokości zlewni ponad przekrojem | 0,8 | – | (źr. 1) |
>
> **Konwencje**
>
> - A w km², L w km i H w m, jak podają źródła; tc w godzinach przeliczany na minuty
> - H to średnia wysokość zlewni minus wysokość przekroju, a nie deniwelacja (maksimum minus minimum) ani sama średnia wysokość
> - L to ciek główny, pole `channel_length_km`, za Grimaldim i in. (2012, wzór 5); Autorità di bacino del Po (2001, §6.1: „percorso idraulicamente più lungo”) i Michailidi i in. (2018) przyjmują najdłuższą drogę spływu, dłuższą o odcinek spływu po stoku (Kamiennik: 14,78 wobec 15,88 km, +3,5 % w tc)
>
> **Założenia**
>
> - zlewnie środkowych i północnych Włoch o powierzchni 170-70 000 km² (Almeida i in. 2014, tab. 1); zlewnie Hydrografu, do 250 km², leżą w większości poniżej tego zakresu: ich wyniki są ekstrapolacją, z uwagą
>
> **Zgodność z obserwacjami według źródeł:** brak w otwartych źródłach (Giandotti 1934 nie jest dostępny otwarcie)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto idrogeologico (PAI), Direttiva sulla piena di progetto, §6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937) <https://www.adbpo.it/PAI/7%20-%20Norme%20di%20attuazione/7.2%20-%20Direttive%20di%20Piano/Direttiva2/DIRETTIVA/DIRETTIVA.PDF>
> 2. Michailidi, E.M., Antoniadi, S., Koukouvinos, A., Bacchi, B. and Efstratiadis, A. (2018). Timing the time of concentration: shedding light on a paradox. Hydrological Sciences Journal 63(5), 721-740, doi:10.1080/02626667.2018.1450985, table 2 (the formula), table 3 (30 basins) <https://www.itia.ntua.gr/en/getfile/1777/2/documents/Timing_the_time_of_concentration_shedding_light_on_a_paradox_nNWG5Fq.pdf>
> 3. Almeida, I.K., Almeida, A.K., Anache, J.A.A., Steffen, J.L. and Alves Sobrinho, T. (2014). Estimation on time of concentration of overland flow in watersheds: a review. Geociências 33(4), 661-671, table 1, Giandotti: basins of central and northern Italy, 170-70,000 km2 (after Giandotti 1940, Preti et al. 2011, Radice et al. 2012) <https://www.revistageociencias.com.br/geociencias-arquivos/33/volume33_4_files/33-4-artigo-9.pdf>
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: main channels of 0.0071 to 26.18 km
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: mean elevations of 2.89 to 204 m above the outlet
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.giandotti`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:giandotti -->

**Dane.** A — powierzchnia zlewni; L — długość cieku głównego; H — średnia wysokość zlewni minus wysokość
przekroju, w Hydrologu `elevation_mean_m` − `elevation_min_m`. Źródła różnią się co do L: Grimaldi i in.
(2012) biorą ciek główny, dyrektywa Padu — „najdłuższą hydraulicznie drogę”, Michailidi i in. (2018) —
najdłuższą drogę spływu. Hydrolog bierze ciek główny (`channel_length_km`) i mówi o tym w konwencjach ramki.
Na Kamienniku najdłuższa droga spływu (15,88 km) w miejsce cieku (14,78 km) wydłuża wynik z 339,43 do
351,46 min (`hydrolog tc giandotti --area-km2 37.22 --length-km 15.88 --elevation-diff-m 105.9`).

**Zakres stosowania.** Duże zlewnie włoskie (ramka). Niemal wszystkie zlewnie, dla których w Polsce liczy się
hydrogram metodą opad–odpływ, są mniejsze: Hydrolog liczy i dodaje uwagę o powierzchni.

**Przykład 4.3. Rafina w Grecji (Michailidi i in. 2018, tab. 3).** A = 123,3 km², L = 29,6 km, H = 226 m:

```sh
hydrolog tc giandotti --area-km2 123.3 --length-km 29.6 --elevation-diff-m 226
```

Hydrolog daje 443,10 min, czyli 7,385 h; tabela źródła podaje 7,4 h. Uwaga dotyczy powierzchni. Ta sama
tabela podaje czasy trzydziestu zlewni; Hydrolog odtwarza je wszystkie z dokładnością druku (przypadki
odniesienia w `tests/fixtures/formulas/tc-cases.json`).

**Kamiennik.** A = 37,22 km², L = 14,78 km, H = 363,2 − 257,3 = 105,9 m:

```sh
hydrolog tc giandotti --area-km2 37.22 --length-km 14.78 --elevation-diff-m 105.9
```

Wynik: 339,43 min (5,66 h), z uwagą o powierzchni.

**Interpretacja.** Czas rośnie z powierzchnią i długością cieku, a maleje z wyniesieniem zlewni nad przekrój:
w zlewniach nizinnych o małej deniwelacji wychodzi długi.

**Typowe błędy** (Kamiennik, poprawny wynik 339,43 min):

- **Deniwelacja $H_{max} - H_{min}$ zamiast $H_{śr} - H_0$.** 475,1 − 257,3 = 217,8 m daje 236,68 min, o 30 %
  mniej.
- **Sama średnia wysokość zlewni** (363,2 m) zamiast jej wyniesienia nad przekrój: 183,28 min, o 46 % mniej.
- **Godziny wzięte za minuty**: źródło podaje godziny, Hydrolog — oba wyniki.

## 4.7 Wzór FAA

**Idea.** Czas spływu wody po powierzchni terenu od najdalszego punktu do wpustu (ang. *inlet time*), z
okólnika amerykańskiej Federalnej Agencji Lotnictwa o odwadnianiu lotnisk (FAA 1970). To nie jest czas
koncentracji zlewni z korytem, tylko czas dopływu do wpustu albo do początku koryta. Wzór opisuje krzywe
rysunku 7 okólnika; późniejsze okólniki FAA go nie zawierają i liczą czas odcinkami, jak metoda prędkości
NRCS (ramka, założenia).

<!-- spec:faa -->

<a id="spec-faa"></a>

> **Czas spływu po stoku według wzoru FAA (AC 150/5320-5B, 1970)** · specyfikacja [`faa`](../FORMULAS.md#faa) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> T = \frac{1{,}8\,(1{,}1 - C)\,\sqrt{D}}{\sqrt[3]{S}},\quad D\ \mathrm{[ft]},\ S\ [\%]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $L$ | `length_km` | Długość spływu po stoku (warstwą), od najdalszego punktu do wyraźnego koryta lub wpustu | km | (0; ∞) | nie podano w źródłach | [0,04; 0,7] (źr. 2) |
> | $S$ | `slope_m_per_m` | Spadek powierzchni, po której spływa woda | m/m | (0; ∞) | nie podano w źródłach | [0,005; 0,19] (źr. 3) |
> | $C$ | `runoff_coeff` | Współczynnik spływu metody racjonalnej | – | (0; 1] | [0; 0,95] (źr. 4) | [0,05; 0,95] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1{,}8$ | `faa_coefficient` | Współczynnik wzoru FAA | 1,8 | $\mathrm{min\,ft^{-0{,}5}\,\%^{1/3}}$ | (źr. 6) |
> | $1{,}1$ | `c_offset` | Składnik, od którego odejmuje się współczynnik spływu | 1,1 | – | (źr. 6) |
> | $100$ | `percent` | Przelicznik spadku z m/m na procenty | 100 | % na m/m | (źr. 7) |
>
> **Konwencje**
>
> - rys. 7 w jednostkach źródła: D w stopach przez dokładny przelicznik 0,3048 m/ft z tabeli jednostek, S w procentach (100 na m/m; krzywe opisano w procentach), T w minutach; stała Hydrologu 22,213 dla L w km i S w m/m do wersji 0.8.1 była zaokrągleniem 22,2125
> - czas dopływu do wpustu: spływ po stoku „od najdalszego punktu zlewni cząstkowej do wpustu” (§6b), a nie czas koncentracji zlewni z korytem
> - C z tab. I w przedziale (0, 1]: C = 0, które tablica podaje dla umiarkowanie przepuszczalnych gleb z darnią (0,00-0,10), jest odrzucane
>
> **Założenia**
>
> - „Wzoru należy używać dla odległości większych niż 800 stóp” (rys. 7): krzywe kończą się na 800 ft, a wzór służy dłuższym drogom; późniejsze okólniki AC 150/5320-5C (2006) i 5D (2013) liczą zamiast tego czas spływu metodą odcinków NRCS
>
> **Zgodność z obserwacjami według źródeł:** brak w źródle
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, chapter 3, §6, figure 7 'Surface flow time curves', p. 11; table I, p. 10 <https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf>
> 2. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m
> 4. Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, table I, p. 10: the values of factor C, 0.00 to 0.95 <https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf>
> 5. Hydrolog's catalog: the coefficients of table I of AC 150/5320-5B, which the option runoff_coeff of tc faa quotes, without its 0.00, table I, p. 10: moderately pervious soils 0.05-0.20 to watertight roofs 0.75-0.95
> 6. Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, figure 7, p. 11 <https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf>
> 7. BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01 <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.faa`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:faa -->

**Dane.** Długość i spadek powierzchni, po której spływa woda (`overland_length_km`,
`overland_slope_m_per_m`), oraz współczynnik spływu C metody wymiernej (ang. *runoff coefficient*; w
Hydrologu `runoff_coeff`, „współczynnik odpływu”) dla tej powierzchni. C dobiera się z tablicy I okólnika
(FAA 1970, s. 10): od gruntów przepuszczalnych porośniętych darnią po szczelne dachy.

**Przykład 4.4. Trawnik na ciężkim gruncie (INDOT, przykład 29-7.4).** L = 45 m, spadek 2 %, C = 0,18:

```sh
hydrolog tc faa --length-km 0.045 --slope-m-per-m 0.02 --runoff-coeff 0.18
```

Hydrolog daje 15,97 min; INDOT podaje 16 min.

**Kamiennik.** Odcinek spływu po stoku 0,3 km o spadku 0,082, C = 0,25:

```sh
hydrolog tc faa --length-km 0.3 --slope-m-per-m 0.082 --runoff-coeff 0.25
```

Wynik: 23,80 min. To czas spływu po stoku do koryta, nie czas koncentracji zlewni.

**Typowe błędy** (Kamiennik, poprawny wynik 23,80 min):

- **Spadek w procentach.** `--slope-m-per-m 8.2` daje 5,13 min — bez ostrzeżenia, bo źródło nie podaje
  zakresu spadku.
- **Wynik użyty jako czas koncentracji zlewni z korytem.**
- **C średnie dla całej zlewni** zamiast C powierzchni, po której spływa woda.

## 4.8 Wzór Kerby'ego

**Idea.** Czas spływu cienką warstwą po stoku (spływ po stoku, ang. *overland* lub *sheet flow*) do
początku wyraźnego koryta, z uwzględnieniem oporu powierzchni. Kerby (1959) rozwinął pracę Hathawaya (1945)
o projektowaniu urządzeń odwadniających (Fang i in. 2005, s. 22).

<!-- spec:kerby -->

<a id="spec-kerby"></a>

> **Czas spływu po stoku według wzoru Kerby'ego (1959)** · specyfikacja [`kerby`](../FORMULAS.md#kerby) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_c = \left(\frac{0{,}67\,N\,L}{\sqrt{S}}\right)^{0{,}467},\quad L\ \mathrm{[ft]},\quad S \to S + 0{,}0005\ \text{dla}\ S < 0{,}002
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $L$ | `length_km` | Długość spływu po stoku (warstwą), od najdalszego punktu do wyraźnego koryta lub wpustu | km | (0; ∞) | [0; 0,366] (źr. 5) | [0,04; 0,7] (źr. 6) |
> | $S$ | `slope_m_per_m` | Spadek powierzchni, po której spływa woda | m/m | (0; ∞) | [0; 0,01] (źr. 7) | [0,005; 0,19] (źr. 8) |
> | $N$ | `retardance` | Współczynnik oporu (retardacji) Kerby'ego dla powierzchni stoku, nie współczynnik Manninga n | – | (0; ∞) | [0,02; 0,8] (źr. 9) | [0,02; 0,8] (źr. 10) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}67$ | `kerby_coefficient` | Współczynnik wzoru Kerby'ego | 0,67 | $\mathrm{min^{1/0{,}467}\,ft^{-1}}$ | (źr. 11) |
> | $0{,}467$ | `kerby_exponent` | Wykładnik wzoru Kerby'ego | 0,467 | – | (źr. 12) |
> | $0{,}002$ | `low_slope_threshold` | Próg małego spadku | 0,002 | m/m | (źr. 13) |
> | $0{,}0005$ | `low_slope_offset` | Poprawka dodawana do małego spadku | 0,0005 | m/m | (źr. 14) |
>
> **Konwencje**
>
> - postać Kerby'ego w jednostkach źródła: L w stopach przez dokładny przelicznik 0,3048 m/ft z tabeli jednostek, tc w minutach; postaci K (L N)^0,467 S^-0,235 z TxDOT (K 0,828 dla ft, 1,44 dla m) zaokrąglają 0,67^0,467 i wykładnik 0,467/2 = 0,2335; stała Hydrologu 36,37 dla L w km do wersji 0.8.1 była zaokrągleniem 36,3699
> - N to współczynnik oporu (retardacji) Kerby'ego dla powierzchni stoku (Roussel i in. 2005, suplement, s. 29), a nie współczynnik Manninga n; NEH 630-15, załącznik 15A, wzór 15A-2 drukuje (2,2 n l / S^0,5)^0,324, co jest błędnym zapisem tego wzoru
> - poprawka małych spadków Clevelanda i in. (2012, wzory 1-2): spadek poniżej 0,002 przyjmuje się jako S + 0,0005; sam wzór rozstrzyga o niej według własnego spadku, podczas gdy Cleveland i in. rozstrzygają według spadku cieku głównego, którego sam spływ po stoku nie ma; przy 0,002 poprawka znika, więc tc rośnie o 5,35 %, gdy S dochodzi do 0,002 od dołu, i jest monotoniczny względem S tylko po każdej stronie 0,002
>
> **Założenia**
>
> - dane Kerby'ego: zlewnie poniżej 10 akrów (0,04 km², sprawdzane przez `WatershedParameters.calculate_tc`), spływ po stoku do 1 200 ft, spadki poniżej 1 %, N do 0,8 (Roussel i in. 2005, s. 5); tylko spływ po stoku (warstwą)
> - N z tablicy Kerby'ego (Roussel i in. 2005, suplement, s. 29): nawierzchnia utwardzona 0,02; gładka, naga, ubita gleba 0,10; słaba trawa, uprawy rzędowe lub umiarkowanie szorstkie ubite powierzchnie 0,20; pastwisko, przeciętna trawa 0,40; las liściasty 0,60; gęsta trawa, las iglasty lub las liściasty z grubą ściółką 0,80
> - odcinki spływu po stoku w Hydrografie (0,04-0,7 km przy 0,005-0,19 m/m) są w większości bardziej strome niż w danych Kerby'ego: ich wyniki są ekstrapolacją, z uwagą
>
> **Zgodność z obserwacjami według źródeł:** brak w otwartych źródłach (Kerby 1959 nie jest dostępny otwarcie)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12 and table 3.3, p. 22 <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 2. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, eq. 3, p. 5; supplement, p. 29 (the form K (L N)^0.467 S^-0.235) <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 3. Indiana Department of Transportation. Indiana Design Manual (metric, archived), Part IV, chapter 29: Hydrology, eq. 29-7.14, Kerby's formula in SI units with K = 1.44 <https://www.in.gov/dot/div/contracts/standards/dm-Archived/07%20Metric/Part%204%20Vol.%201/Ch%2029/Ch29.pdf>
> 4. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures and eq. 2, pp. 1-2 <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
> 5. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: in the development of Kerby's equation the length of overland flow was as much as about 1,200 feet (366 meters), an upper limit <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km
> 7. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, p. 5: the watersheds of Kerby (1959) have dimensionless slopes less than 0.01 <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 8. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m
> 9. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: Kerby's table of the retardance N, pavement 0.02 to dense grass, coniferous forest or deciduous forest with deep litter 0.80 <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 10. Hydrolog's catalog and GUI: Kerby's table of N (Roussel et al. 2005, supplement, p. 29), from which their users take N, option retardance of tc kerby and tc kerby-kirpich: 0.02 (pavement) to 0.80 (dense grass, coniferous forest)
> 11. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22, (0.67 N L / S^0.5)^0.467 with L in ft; the same in Roussel et al. (2005) eq. 3 <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 12. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22; INDOT eq. 29-7.14 and TxDOT (2019) take the same exponent of L N <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 13. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, step 2(c), p. 2: a main channel slope less than 0.002 is low slope; TxDOT (2019), section 11 <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
> 14. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, step 3 and eq. 1, p. 2: S_low slope = S0 + 0.0005; TxDOT (2019), section 11 <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.kerby`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:kerby -->

**Współczynnik N** Kerby'ego (ang. *retardance coefficient*) to opór powierzchni dla spływu warstwowego, od
gładkiej nawierzchni po gęstą trawę i las iglasty (tablica w założeniach ramki, za Roussel i in. 2005). To
nie jest współczynnik szorstkości Manninga $n$. NEH 630 (2010, zał. 15A; 2025) drukuje wzór Kerby'ego błędnie
— z innym wykładnikiem, inną stałą i „współczynnikiem Manninga” — i nie należy go stamtąd przepisywać
(ramka, konwencje).

**Poprawka małych spadków.** Dla bardzo płaskiego stoku wzór dodaje do spadku stałą wartość (Cleveland i in.
2012), więc wynik nie rośnie bez końca; ceną jest skok wyniku na progu poprawki (ramka). Więcej w p. 4.9.

**Przykład 4.5. Trawa na łagodnym stoku (INDOT, przykład 29-7.7).** L = 200 m, spadek 0,5 %, N = 0,40:

```sh
hydrolog tc kerby --length-km 0.2 --slope-m-per-m 0.005 --retardance 0.4
```

Hydrolog daje 38,53 min; INDOT podaje 38,4 min. Różnica wynika z zaokrąglenia stałej w metrycznej postaci
wzoru, której używa INDOT.

**Kamiennik.** Stok 0,3 km o spadku 0,082, N = 0,4:

```sh
hydrolog tc kerby --length-km 0.3 --slope-m-per-m 0.082 --retardance 0.4
```

Wynik: 24,23 min, z uwagą o spadku — stok Kamiennika jest wielokrotnie bardziej stromy niż stoki w danych
Kerby'ego. `tc watershed` dodaje uwagę o powierzchni zlewni.

**Typowe błędy:**

- **Cała droga spływu jako spływ po stoku.** 15,88 km przy spadku 0,0114 daje 245,14 min — liczbę bez
  sensu fizycznego, bo woda nie spływa cienką warstwą przez kilkanaście kilometrów.
- **N wzięty z tablic Manninga.**
- **Wynik użyty jako czas koncentracji zlewni** — ten daje dopiero metoda Kerby'ego–Kirpicha.

## 4.9 Metoda Kerby'ego–Kirpicha

**Idea.** Najdłuższą drogę spływu dzieli się na odcinek spływu po stoku, liczony wzorem Kerby'ego, i resztę
— przepływ korytem (ang. *channel flow*), liczony wzorem Kirpicha; czasy się sumuje. Roussel i in. (2005)
sprawdzili metodę na zlewniach Teksasu, z dobrą zgodnością z czasami wyznaczonymi z obserwowanych wezbrań
(ramka, walidacja). Metodę opisuje podręcznik hydrauliczny TxDOT (2019, rozdz. 4, sekcja 11).

<!-- spec:kerby_kirpich -->

<a id="spec-kerby_kirpich"></a>

> **Czas koncentracji metodą Kerby'ego–Kirpicha (Roussel i in. 2005)** · specyfikacja [`kerby_kirpich`](../FORMULAS.md#kerby_kirpich) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_c = \left(\frac{0{,}67\,N\,L_{ov}}{\sqrt{S_{ov}}}\right)^{0{,}467} + 0{,}0078\,(L_{fp} - L_{ov})^{0{,}77}\,S_{fp}^{-0{,}385},\quad L\ \mathrm{[ft]}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $L_{ov}$ | `overland_length_km` | Długość spływu po stoku (warstwą), od najdalszego punktu do wyraźnego koryta lub wpustu | km | (0; ∞) | [0; 0,366] (źr. 4) | [0,04; 0,7] (źr. 5) |
> | $S_{ov}$ | `overland_slope_m_per_m` | Spadek powierzchni, po której spływa woda | m/m | (0; ∞) | nie podano w źródłach | [0,005; 0,19] (źr. 6) |
> | $N$ | `retardance` | Współczynnik oporu (retardacji) Kerby'ego dla powierzchni stoku, nie współczynnik Manninga n | – | (0; ∞) | [0,02; 0,8] (źr. 7) | [0,02; 0,8] (źr. 8) |
> | $L_{fp}$ | `flow_path_length_km` | Długość cieku głównego w rozumieniu metody: najdłuższa droga spływu od działu wodnego do przekroju, łącznie z odcinkiem po stoku | km | (0; ∞) | [1,6; 80] (źr. 9) | [0,05; 30] (źr. 10) |
> | $S_{fp}$ | `flow_path_slope_m_per_m` | Spadek tej drogi: wysokość jej początku minus wysokość przekroju, podzielona przez jej długość | m/m | (0; ∞) | [0,002; 0,02] (źr. 11) | [0,002; 0,11] (źr. 12) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji | min | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | flow_path_length_km > overland_length_km | `flow_path_longer_than_overland` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 13) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}67$ | `kerby_coefficient` | Współczynnik wzoru Kerby'ego | 0,67 | $\mathrm{min^{1/0{,}467}\,ft^{-1}}$ | (źr. 14) |
> | $0{,}467$ | `kerby_exponent` | Wykładnik wzoru Kerby'ego | 0,467 | – | (źr. 15) |
> | $0{,}002$ | `low_slope_threshold` | Próg małego spadku | 0,002 | m/m | (źr. 16) |
> | $0{,}0005$ | `low_slope_offset` | Poprawka dodawana do małego spadku | 0,0005 | m/m | (źr. 17) |
> | $0{,}0078$ | `kirpich_coefficient` | Współczynnik wzoru Kirpicha | 0,0078 | $\mathrm{min\,ft^{-0{,}77}}$ | (źr. 18) |
> | $0{,}77$ | `kirpich_length_exponent` | Wykładnik długości drogi spływu we wzorze Kirpicha | 0,77 | – | (źr. 19) |
> | $-0{,}385$ | `kirpich_slope_exponent` | Wykładnik spadku drogi spływu we wzorze Kirpicha | −0,385 | – | (źr. 19) |
>
> **Konwencje**
>
> - tc = t_overland + t_channel: `kerby` na odcinku spływu po stoku, `kirpich` na odcinku korytowym, czyli drodze spływu minus odcinek po stoku, przy spadku całej drogi od działu wodnego do przekroju (Roussel i in. 2005, suplement, s. 29-30), w jednostkach i ze stałymi tych specyfikacji
> - odstępstwo od Clevelanda i in. (2012, s. 1-2): o poprawce małych spadków (S + 0,0005 poniżej 0,002) rozstrzyga się dla każdego odcinka według jego własnego spadku — spadku stoku dla Kerby'ego i spadku drogi spływu dla Kirpicha — podczas gdy Cleveland i in. rozstrzygają według spadku cieku głównego dla obu odcinków (poniżej 0,002 poprawka w obu, powyżej 0,003 w żadnym), a przedział 0,002-0,003 pozostawiają inżynierowi („przy niejednoznacznym kierunku spływu traktować jak mały spadek”); oba podejścia są zgodne, gdy oba spadki leżą po tej samej stronie 0,002, a różnią się dla płaskiego cieku głównego przy bardziej stromym odcinku po stoku (Cleveland i in. poprawiają także ten odcinek), dla stromego cieku głównego przy płaskim odcinku po stoku (Hydrolog poprawia ten odcinek) i w strefie przejściowej (Hydrolog nigdy nie poprawia tam koryta)
> - przy spadku drogi spływu równym 0,002 część korytowa rośnie o 8,97 %, a przy spadku stoku równym 0,002 część po stoku o 5,35 %, gdy poprawka znika: tc nie jest monotoniczny względem żadnego z tych spadków
>
> **Założenia**
>
> - 92 zlewnie w Teksasie z pracy Roussela i in. (2005): 0,25-150 mil kwadratowych (0,65-388 km², sprawdzane przez `WatershedParameters.calculate_tc`), cieki główne o długości 1-50 mil i spadku 0,002-0,02; „w bazie danych, na której oparto metodę, nie ma zlewni o małych spadkach terenu” (suplement, s. 29)
> - odcinek spływu po stoku do 1 200 ft, górnej granicy Kerby'ego (suplement, s. 29); metoda nie podaje zakresu spadku stoku, a jej własny przykład przyjmuje 2 %
>
> **Zgodność z obserwacjami według źródeł:** Roussel i in. (2005, suplement, s. 29) uznają szacunki metody Kerby'ego–Kirpicha za „zgodne z czasami zlewni wyznaczonymi niezależnie z rzeczywistych opadów i hydrogramów odpływu” dla swoich 92 zlewni w Teksasie
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement 'Guidance for estimation of time of concentration in Texas', pp. 29-30, and its example <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 2. Texas Department of Transportation (2019). Hydraulic Design Manual, chapter 4, section 11: Time of Concentration, eqs. 4-13 to 4-15 <https://www.txdot.gov/manuals/des/hyd/chapter-4--hydrology/section-11--time-of-concentration.html>
> 3. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, eqs. 1-3, pp. 1-3, and its example <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
> 4. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: in the development of Kerby's equation the length of overland flow was as much as about 1,200 feet (366 meters), an upper limit <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m
> 7. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: Kerby's table of the retardance N, pavement 0.02 to dense grass, coniferous forest or deciduous forest with deep litter 0.80 <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 8. Hydrolog's catalog and GUI: Kerby's table of N (Roussel et al. 2005, supplement, p. 29), from which their users take N, option retardance of tc kerby and tc kerby-kirpich: 0.02 (pavement) to 0.80 (dense grass, coniferous forest)
> 9. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: main channel lengths of the 92 Texas watersheds approximately 1 to 50 miles, from the outlet to the divide <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 10. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km
> 11. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: dimensionless main channel slopes approximately 0.002 to 0.02, from the divide to the outlet <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 12. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow path slopes of 0.00244 to 0.1055 m/m
> 13. Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 30: the subtraction of the overland flow length from the overall main-channel length (watershed divide to outlet) is necessary <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
> 14. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22, (0.67 N L / S^0.5)^0.467 with L in ft; the same in Roussel et al. (2005) eq. 3 <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 15. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22; INDOT eq. 29-7.14 and TxDOT (2019) take the same exponent of L N <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 16. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, step 2(c), p. 2: a main channel slope less than 0.002 is low slope; TxDOT (2019), section 11 <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
> 17. Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, step 3 and eq. 1, p. 2: S_low slope = S0 + 0.0005; TxDOT (2019), section 11 <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>
> 18. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; the same in Roussel et al. (2005) eq. 7, Mota and Kobiyama (2015) and FDOT (2024) eq. 2.2-9 <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
> 19. Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
>
> Funkcja `hydrolog.time.concentration.ConcentrationTime.kerby_kirpich`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:kerby_kirpich -->

**Dane.** Odcinek po stoku: długość, spadek i N. Droga spływu: **cała** najdłuższa droga od działu wodnego
do przekroju i jej spadek, czyli „zmiana wysokości od działu wodnego do przekroju podzielona przez
krzywoliniową długość cieku głównego” (Roussel i in. 2005, suplement). Odcinek po stoku Hydrolog odejmuje od
drogi sam; droga nie dłuższa od niego jest błędem fizycznym (`validation_error`, `outside_physical_range`,
ograniczenie `flow_path_longer_than_overland`). Wynik zawiera tylko sumę; składniki dają polecenia
`tc kerby` i `tc kirpich`, to drugie z drogą pomniejszoną o odcinek po stoku.

**Poprawka małych spadków** (ang. *low-slope adjustment*; Cleveland i in. 2012). Gdy spadek dąży do zera,
czas we wzorach ze spadkiem w mianowniku rośnie bez końca. Cleveland i in. rozstrzygają według spadku cieku
głównego: przy dostatecznie dużym spadku stosuje się zwykłe wzory, poniżej progu do obu spadków dodaje się
stałą wartość, a pas pośredni zostawiają decyzji inżyniera („przy niejednoznacznym kierunku spływu
traktować jak mały spadek”). Hydrolog rozstrzyga osobno dla każdego odcinka według jego własnego spadku i nie
ma pasa pośredniego — to odstępstwo od źródła zadeklarowane w specyfikacji (ramka, konwencje;
[ADR-0052](../decisions/0052-the-time-of-concentration-formulas-by-specs.md)). Oba sposoby dają ten sam wynik,
gdy spadek stoku i spadek drogi leżą po tej samej stronie progu; różnią się dla płaskiego koryta pod
stromszym stokiem, stromego koryta pod płaskim stokiem i w pasie pośrednim. Na samym progu wynik skacze:
spadek nieco mniejszy od progowego daje krótszy czas niż progowy (wielkość skoku w ramce). Czy rozstrzygać
według spadku cieku, jak Cleveland i in., jest pytaniem otwartym, pozostawionym autorowi Hydrologa (ADR-0052).

**Przykład 4.6. Zlewnia 0,5 mi² (Roussel i in. 2005, suplement).** Droga od działu do przekroju 5280 ft
(1,609344 km), spadek (750 − 700)/5280 = 0,0095; spływ po stoku 500 ft (0,1524 km) po przeciętnej trawie
(N = 0,40) o spadku 2 %:

```sh
hydrolog tc kerby-kirpich --overland-length-km 0.1524 --overland-slope-m-per-m 0.02 --retardance 0.4 --flow-path-length-km 1.609344 --flow-path-slope-m-per-m 0.0095
```

Hydrolog daje 56,45 min; źródło — ok. 57 min (25 + 32 min). Składniki:

```sh
hydrolog tc kerby --length-km 0.1524 --slope-m-per-m 0.02 --retardance 0.4
hydrolog tc kirpich --length-km 1.456944 --slope-m-per-m 0.0095
```

dają 24,55 min po stoku i 31,90 min korytem.

**Przykład 4.7. Ta sama zlewnia, płaska (Cleveland i in. 2012).** Dział wodny leży tylko 1,1 ft nad
przekrojem: spadek drogi 0,00021, spadek stoku 0,0003:

```sh
hydrolog tc kerby-kirpich --overland-length-km 0.1524 --overland-slope-m-per-m 0.0003 --retardance 0.4 --flow-path-length-km 1.609344 --flow-path-slope-m-per-m 0.00021
```

Hydrolog daje 138,66 min (52,06 min po stoku i 86,60 min korytem, oba z poprawką), z uwagą, że spadek drogi
leży poza danymi metody; źródło — ok. 140 min (53 + 87 min). Bez poprawki sam odcinek korytowy dałby
138,42 min (`hydrolog tc kirpich --length-km 1.456944 --slope-m-per-m 0.00021`).

**Zastosowanie w Polsce.** Wachulec, Wałęga i Młyński (2016) policzyli tą metodą czas koncentracji małej
zlewni Sidzinki w Krakowie: 3,59 h, wobec 2,035 h według procedury TR-55. Przy deszczu o największym natężeniu
na początku kulminacja w modelu SCS-UH wypadła odpowiednio po 3,15 h i 2,25 h, a dłuższy czas koncentracji
dawał mniejszą kulminację. Wzór Kerby'ego wydrukowano tam z błędnym wykładnikiem, a zakres metody inaczej niż
u Roussela i in. (2005) — kolejny powód, by przepisywać wzory ze źródła, nie z drugiej ręki.

**Typowe błędy:**

- **Długość koryta zamiast całej drogi od działu wodnego.** Hydrolog odejmuje odcinek po stoku sam.
- **Spadek odcinka korytowego zamiast spadku całej drogi.**
- **Poprawka małych spadków poza terenem płaskim**, np. dodana ręcznie do spadków zlewni pagórkowatej.

## 4.10 Porównanie metod: Kamiennik po Świerzawę

Wszystkie sześć metod liczy się z pliku zlewni jednym poleceniem, zmieniając tylko metodę:

```sh
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method kirpich
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method nrcs
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method giandotti
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method faa
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method kerby
hydrolog tc watershed --watershed-file tests/fixtures/kamiennik.json --method kerby_kirpich
```

To samo porównanie pokazują „Kalkulatory” interfejsu graficznego Hydrologa dla zlewni z „Hydrogramu
zlewni”.

| Metoda | Dane zlewni | $t_c$ [min] | $t_c$ [h] | Uwagi `tc watershed` (zmienne poza zakresem stosowania) | Co oznacza wynik |
|---|---|---|---|---|---|
| Kirpich | droga 15,88 km, spadek 0,0114 | 187,13 | 3,12 | powierzchnia, długość, spadek | czas zlewni z korytem |
| NRCS | droga 15,88 km, spadek terenu 0,082, CN 65 | 399,39 | 6,66 | powierzchnia | czas zlewni |
| Giandotti | A 37,22 km², ciek 14,78 km, H 105,9 m | 339,43 | 5,66 | powierzchnia | czas zlewni |
| FAA | stok 0,3 km, spadek 0,082, C 0,25 | 23,80 | 0,40 | — | czas spływu po stoku |
| Kerby | stok 0,3 km, spadek 0,082, N 0,4 | 24,23 | 0,40 | powierzchnia, spadek | czas spływu po stoku |
| Kerby–Kirpich | stok jak wyżej i droga 15,88 km, spadek 0,0114 | 208,63 | 3,48 | — | czas zlewni z korytem |

**Jak czytać tabelę.**

- Czasy zlewni z korytem rozkładają się od 187,13 do 399,39 min — ponad dwukrotnie. To nie jest błąd
  programu, tylko rzeczywista niepewność metod (p. 4.1).
- W danych swojego źródła mieści się tylko metoda Kerby'ego–Kirpicha. Kirpich, metoda domyślna Hydrologa,
  leży daleko poza swoimi danymi. NRCS i Giandotti wychodzą poza zakres powierzchni w przeciwne strony:
  Kamiennik jest większy od zlewni Mockusa i mniejszy od zlewni Giandottiego.
- FAA i Kerby dają ok. 24 min, ale to czasy spływu po stoku, nie czasy zlewni. W metodzie Kerby'ego–Kirpicha
  odcinek po stoku (24,23 min) to ok. 12 % całości; reszta, 184,40 min, to przepływ korytem po 15,58 km
  drogi (`hydrolog tc kirpich --length-km 15.58 --slope-m-per-m 0.0114`).
- Wynik Kerby'ego–Kirpicha (208,63 min) jest dłuższy od wyniku Kirpicha o 21,50 min, bo po stoku woda płynie
  wolniej niż w korycie. Dalsze rozdziały przyjmują dla Kamiennika właśnie ten czas.

**Jak wybór metody zmienia hydrogram.** Ten sam opad projektowy — PMAXTP, metoda POT, prawdopodobieństwo
przewyższenia 1 %, czas trwania 720 min, 101,82 mm, hietogram Beta (2; 5) z krokiem 10 min (rozdz. 2) — i te
same straty SCS-CN (CN 65, AMC II, rozdz. 3) dają z hydrogramem jednostkowym SCS (rozdz. 5) różne kulminacje
zależnie od tego, którą metodą policzono $t_c$:

```sh
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type beta --total-mm 101.82 --duration-min 720 --timestep-min 10
```

(z `--tc-method kirpich`, `giandotti` i `nrcs` dla pozostałych wierszy):

| Metoda $t_c$ | $t_c$ [min] | $Q_{max}$ [m³/s] | Czas do kulminacji [h:min] |
|---|---|---|---|
| Kirpich | 187,13 | 54,23 | 6:40 |
| Kerby–Kirpich | 208,63 | 52,36 | 6:50 |
| Giandotti | 339,43 | 42,62 | 8:20 |
| NRCS | 399,39 | 38,96 | 9:00 |

Opad efektywny (26,25 mm) i objętość odpływu bezpośredniego (ok. 977 tys. m³) są we wszystkich wierszach te
same; czas koncentracji przesuwa i spłaszcza falę. Kulminacja z czasem Kirpicha jest o 39 % wyższa niż z
czasem NRCS, choć opad i straty są te same. Dlatego wybór metody $t_c$ trzeba uzasadnić, a nie zostawić
domyślnym.

Krytyczny czas trwania deszczu mieści się według DVWK (1984, za KZGW 2017) między $t_c$ a $2\,t_c$, czyli dla
czasu Kerby'ego–Kirpicha między ok. 3,5 a 7 h. Dwunastogodzinny deszcz z przykładu instrukcji Hydrologa jest
dłuższy; jak sprawdzić, który czas trwania daje największą kulminację, pokazuje rozdz. 2.

Dane PMAXTP: „Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut
Badawczy, dane pochodzą ze strony https://klimat.imgw.pl/opady-maksymalne”; „Dane Instytutu Meteorologii i
Gospodarki Wodnej – Państwowego Instytutu Badawczego pochodzące ze strony
https://klimat.imgw.pl/opady-maksymalne zostały przetworzone” (Ozga-Zieliński red. 2022).

## 4.11 Jak wybrać metodę

1. **Ustal, czego potrzebujesz:** czasu zlewni z korytem (Kirpich, NRCS, Giandotti, Kerby–Kirpich) czy
   czasu spływu po stoku do wpustu, rowu lub koryta (FAA, Kerby).
2. **Zmierz właściwe wielkości** (p. 4.2). Zła długość albo zły spadek to częstszy błąd niż zły wzór.
3. **Porównaj zlewnię z zakresem stosowania** w ramkach i z opisem zlewni źródła. Z grubsza: Kirpich —
   bardzo małe zlewnie z wyraźnym korytem; NRCS — małe zlewnie rolnicze o znanym CN; Kerby–Kirpich —
   zlewnie z korytem, od małych po średnie; Giandotti — duże zlewnie; FAA i Kerby — tylko spływ po stoku.
4. **Policz kilka metod** (`tc watershed` z każdą metodą albo „Kalkulatory”) i potraktuj rozrzut jako miarę
   niepewności. Sprawdź, jak zmienia on kulminację (p. 4.10).
5. **Jeśli są pomiary** opadu i odpływu w zlewni lub w zlewni podobnej, wyznacz z nich opóźnienie (Banasik i
   Barszcz 2004; Krajewski i Banasik 2013). Żaden wzór tego nie zastąpi.
6. **Pamiętaj o krytycznym czasie trwania deszczu:** policz wezbranie dla kilku czasów trwania (rozdz. 2).

## Źródła

Źródła otwarte (dostępne w sieci w chwili pisania):

- Autorità di bacino del fiume Po (2001). *Piano stralcio per l'Assetto Idrogeologico (PAI). Direttiva sulla
  piena di progetto*, §6.1.
  https://www.adbpo.it/PAI/7%20-%20Norme%20di%20attuazione/7.2%20-%20Direttive%20di%20Piano/Direttiva2/DIRETTIVA/DIRETTIVA.PDF
- Banasik K., Barszcz M. (2004). Porównanie ocen opóźnień odpływu wezbraniowego dla wybranych małych zlewni
  rzecznych. *Przegląd Naukowy – Inżynieria i Kształtowanie Środowiska* 13, 2(29). http://iks.pn.sggw.pl/z29/art1.pdf
- Beven K.J. (2020). A history of the concept of time of concentration. *Hydrology and Earth System Sciences*
  24, 2655–2670. https://hess.copernicus.org/articles/24/2655/2020/
- Cleveland T.G., Thompson D.B., Fang X., Li M.-H. (2012). *Guidance for Estimation of Time of Concentration in
  Texas for Low-Slope Conditions*. TxDOT Product 0-6382-P1, Texas Tech University.
  https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf
- Fang X., Cleveland T.G., Garcia C.A., Thompson D.B., Malla R. (2005). *Literature Review on Timing
  Parameters for Hydrographs*. TxDOT Research Report 0-4696-1, Lamar University.
  https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf
- Federal Aviation Agency (1970). *Airport Drainage*. Advisory Circular AC 150/5320-5B, rozdz. 3, rys. 7 i
  tab. I. https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf
- Indiana Department of Transportation. *Indiana Design Manual* (wersja metryczna, archiwalna), cz. IV,
  rozdz. 29 „Hydrology”, przykłady 29-7.4, 29-7.7 i 29-7.8.
  https://www.in.gov/dot/div/contracts/standards/dm-Archived/07%20Metric/Part%204%20Vol.%201/Ch%2029/Ch29.pdf
- Krajewski A., Banasik K. (2013). Czas reakcji zlewni zurbanizowanej na opady wywołujące wezbrania. *Acta
  Scientiarum Polonorum, Architectura* 12(4), 135–146. http://www.architectura.actapol.net/pub/12_4_135.pdf
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych oraz identyfikacji
  modeli transformacji opadu w odpływ* (Banasik K., Wałęga A., Węglarczyk S., Więzik B.), zał. 2 do OPZ,
  Krajowy Zarząd Gospodarki Wodnej, s. 105.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Michailidi E.M., Antoniadi S., Koukouvinos A., Bacchi B., Efstratiadis A. (2018). Timing the time of
  concentration: shedding light on a paradox. *Hydrological Sciences Journal* 63(5), 721–740.
  https://www.itia.ntua.gr/en/getfile/1777/2/documents/Timing_the_time_of_concentration_shedding_light_on_a_paradox_nNWG5Fq.pdf
- Mota A.A., Kobiyama M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de
  concentração. *Revista Brasileira de Recursos Hídricos* 20(1), 55–59.
  https://revistas.abrhidro.org.br/article.php?Article=5027
- Ozga-Zieliński B. (red.) (2022). *Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i
  prawdopodobieństwie przewyższenia – Projekt PMAXTP*. Instytut Meteorologii i Gospodarki Wodnej – Państwowy
  Instytut Badawczy, Warszawa. https://klimat.imgw.pl/opady-maksymalne/
- Roussel M.C., Thompson D.B., Fang X., Cleveland T.G., Garcia C.A. (2005). *Time-Parameter Estimation for
  Applicable Texas Watersheds*. TxDOT Research Report 0-4696-2, Lamar University (z suplementem *Guidance for
  estimation of time of concentration in Texas*). https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf
- Texas Department of Transportation (2019). *Hydraulic Design Manual*, rozdz. 4, sekcja 11 „Time of
  Concentration”.
  https://www.txdot.gov/manuals/des/hyd/chapter-4--hydrology/section-11--time-of-concentration.html
- USDA-NRCS (2010). *National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration*
  (210-VI-NEH, maj 2010). https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf; wydanie
  zmienione: 210 H 630 Subpart F (2025).
  https://directives.nrcs.usda.gov/sites/default/files2/1749749287/Subpart%20F%20%E2%80%93%20Time%20of%20Concentration.pdf
- Wachulec K., Wałęga A., Młyński D. (2016). Wpływ czasu koncentracji i charakterystyk opadu na kształtowanie
  się hydrogramu odpływu w małej zlewni niekontrolowanej. *Przegląd Naukowy – Inżynieria i Kształtowanie
  Środowiska* 25, 1(71), 72–82. http://iks.pn.sggw.pl/PN71/A8/art8.pdf
- *Wytyczne projektowania urządzeń do odwodnienia dróg zamiejskich i ulic. Część 1: Wymagania podstawowe*
  (WR-D-71-1, wersja 01-2023.11.28). Wzorce i standardy rekomendowane przez ministra właściwego do spraw
  transportu, §5.4.2, wzór 5.4.2.2 i przykład zbiornika retencyjnego.
  https://www.gov.pl/attachment/9361c405-b42a-436d-a5b6-037e87d88695

Dokumenty Hydrologa: [ADR-0019](../decisions/0019-tc-from-the-inputs-its-source-defines.md) (dane każdej
metody), [ADR-0052](../decisions/0052-the-time-of-concentration-formulas-by-specs.md) (specyfikacje, stałe
w jednostkach źródła, odstępstwo poprawki małych spadków),
[ADR-0064](../decisions/0064-notices-of-applicability-constraints-and-unreferenced-formulas.md) (kod
ostrzeżenia), [COMPUTATION_PATHS](../COMPUTATION_PATHS.md), p. 3.7; przypadki odniesienia
`tests/fixtures/formulas/tc-cases.json`.

Źródła niedostępne w otwartym dostępie, cytowane za źródłami powyżej: Kirpich Z.P. (1940) *Civil Engineering*
10(6), 362; Ramser C.E. (1927); Rowe R.R., Thomas R.L. (1942); Hathaway G.A. (1945); Kerby W.S. (1959)
*Civil Engineering* 29(3); Mockus V. (1957, 1961); Simas M. (1996); Giandotti M. (1934) *Memorie e Studi
Idrografici* 8; Grimaldi S., Petroselli A., Tauro F., Porfiri M. (2012) *Hydrological Sciences Journal*
57(2), 217–228 (cytowane za Beven 2020 i Michailidi i in. 2018); DVWK (1984) (cytowane za KZGW 2017).
