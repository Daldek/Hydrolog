# D. Jak Hydrolog sprawdza poprawność wzorów

Wynik obliczeń hydrologicznych jest tyle wart, ile wzór, który go dał. Zły wykładnik, stała
przepisana z błędem, pomylona jednostka albo wzór użyty po cichu poza warunkami, dla których
go wyprowadzono, psują każdy wynik, który od nich zależy. Hydrolog stosuje się do standardu
obliczeń ekosystemu Nogat (wymagania o identyfikatorach `CMP-…`, Nogat 2026), który mówi, jak
wzór się deklaruje, jak zachowuje się na granicach danych wejściowych, jak się go sprawdza i
co się dzieje, gdy okaże się błędny. Jak Hydrolog ten standard wdraża, opisuje decyzja
projektowa ADR-0050 (Hydrolog 2026a).

Standard rozróżnia dwie rzeczy, które w hydrologii często się myli (Refsgaard i Henriksen
2004):

- **weryfikacja** (*verification*): czy program liczy dokładnie ten wzór, który opublikowano,
  z podaną tolerancją; za nią odpowiada Hydrolog i o niej jest ten dodatek;
- **walidacja** (*validation*): czy wzór zgadza się z przyrodą, czyli z obserwacjami; za nią
  odpowiadają źródła wzoru. Specyfikacja przytacza to, co o zgodności z obserwacjami mówi
  źródło (w ramce: „Zgodność z obserwacjami według źródeł”), i niczego ponad to nie twierdzi.

## D.1. Specyfikacja: jedna deklaracja wzoru

Hydrolog dzieli funkcje, które zwracają wielkości fizyczne lub statystyczne, na dwie grupy
(CMP-1.1):

- **wzory grupy A** (*Tier A*): równania empiryczne, modele i schematy numeryczne, estymatory
  statystyczne, testy i dopasowania rozkładów, wskaźniki, klasyfikacje według opublikowanych
  progów lub tablic;
- **wzory grupy B** (*Tier B*): przeliczenia jednostek, agregacje i wartości charakterystyczne
  według definicji kalendarzowej, interpolacje, konwencje kodów, braków danych, dni i lat w
  danych źródłowych.

Każdy wzór grupy A jest zadeklarowany dokładnie raz, w kodzie, obok swojej funkcji, przez
specyfikację (`FormulaSpec`) modułu referencyjnego `hydrolog.nogat_formulas`, skopiowanego
bajt po bajcie ze standardu Nogat (CMP-2.1, CMP-8.1). Specyfikacja podaje: równanie (tekstem i w
LaTeX), każdą zmienną z symbolem, jednostką, typem i trzema zakresami (D.2), warunki między
zmiennymi, nazwane stałe z wartościami i źródłami, wyniki z jednostkami i zakresem
fizycznym, źródła, konwencje (na przykład prawdopodobieństwo przewyższenia czy
nieprzewyższenia, znak parametru kształtu rozkładu GEV, współczynnik λ metody SCS-CN, rok
hydrologiczny), założenia, ostrzeżenia, pułapki numeryczne, własności, pliki przypadków
referencyjnych, to, co źródło mówi o zgodności z obserwacjami, oraz wersję wzoru. Wzór grupy B
ma wiersz w tabeli swojego modułu (`TierBSpec`): definicję, konwencję, źródło i stałe
(CMP-2.2). Obliczenia powierzone bibliotekom zewnętrznym (na przykład wyszukiwanie pierwiastka
w SciPy) nie są wzorami standardu; katalog wzorów wymienia je z wersją biblioteki i jednym
przypadkiem kontrolnym (CMP-1.2).

Ze specyfikacji powstaje wszystko, co o wzorze mówi dokumentacja, i nic nie jest przepisywane
ręcznie (CMP-2.6, CMP-2.7):

- katalog wzorów `docs/FORMULAS.md` i karta każdego wzoru `formulas/<nazwa>.toml` (po
  angielsku), generowane przez `scripts/generate_formulas.py`;
- ramki tego podręcznika (D.7), generowane przez `scripts/generate_handbook.py`;
- zakresy, które katalog poleceń pokazuje klientom (wiersz poleceń, serwer MCP, przeglądarkowy
  interfejs).

Opis funkcji w kodzie (docstring) podaje tylko jej cel i nazwę specyfikacji; test kontraktowy
odrzuca w nim każdą cyfrę, więc opis nie może przeczyć kodowi (CMP-2.7). Testy kontraktowe
sprawdzają też, że wygenerowane dokumenty są aktualne, a karty zgodne ze schematem standardu
(ADR-0050).

Każdy wzór ma **wersję** (`formula_version`), liczbę całkowitą zwiększaną przy każdej zmianie
jego wyników (CMP-2.8). Wynik polecenia Hydrologa (koperta `hydrolog-result/1`) niesie pole
`formula_versions` z wersją każdego wzoru, który dał wynik, a w bibliotece wersję odczytuje
się ze specyfikacji (na przykład `hydrolog.time.concentration.KIRPICH.formula_version`). Gdy
we wzorze znajdzie się błąd, zapisane wyniki, których dotyczy, da się odnaleźć po wersji.

## D.2. Trzy zakresy i zachowanie na ich granicach

Każda zmienna wejściowa ma w specyfikacji trzy zakresy (CMP-1.3 do CMP-1.5):

- **zakres fizyczny**: wartości, które mogą istnieć (powierzchnia zlewni nie może być ujemna,
  a udział nie może przekroczyć całości). Koniec nieograniczony ma granicę testową z
  uzasadnieniem, na przykład największy zanotowany na świecie opad dobowy;
- **zakres stosowalności**: wartości, dla których wzór wyprowadzono lub sprawdzono, ze źródłem,
  które go podaje; gdy źródło żadnego nie podaje, specyfikacja mówi to wprost („nie podano w
  źródłach”);
- **zakres typowy**: wartości spotykane w praktyce, z danych Hydrologa lub z nazwanego źródła
  polskiego albo czeskiego. Może leżeć częściowo poza zakresem stosowalności i wtedy
  specyfikacja to pokazuje. Przykład: wzór Kirpicha wyprowadzono na bardzo małych zlewniach
  rolniczych, a w Polsce stosuje się go do zlewni znacznie większych; wynik musi o tym
  informować.

Warunki między zmiennymi (CMP-1.6) mają jedną z trzech klas: fizyczny, konieczny (bez niego
wzór jest nieokreślony: za mała próba, ujemny argument logarytmu, krok czasowy poza granicą
stateczności schematu) albo stosowalności. Przykładem jest warunek stateczności metody
Muskingum wiążący krok czasowy z parametrami K i X.

Zachowanie na granicach jest takie samo dla wszystkich wzorów, bo sprawdza je jeden moduł
referencyjny, a nie każdy wzór osobno (CMP-3.5):

| Sytuacja | Skutek |
|---|---|
| wartość spoza zakresu fizycznego, niespełniony warunek fizyczny, wartość nieskończona lub NaN tam, gdzie potrzebna jest liczba | odmowa obliczeń: błąd `validation_error`, `details.reason` = `outside_physical_range` (CMP-3.1) |
| niespełniony warunek konieczny | odmowa obliczeń: `validation_error`, `details.reason` = `precondition_failed` (CMP-3.2) |
| wartość niewłaściwego typu (wartość logiczna, `None`, napis zamiast liczby) | odmowa obliczeń: `validation_error` (CMP-4.2) |
| wartość spoza zakresu stosowalności albo niespełniony warunek stosowalności | wynik z ostrzeżeniem, które podaje zmienną, jej wartość, zakres i jego źródło (CMP-3.3) |
| wynik nieskończony albo spoza zakresu fizycznego wyniku | błąd `calculation_error` zamiast cichego złego wyniku (CMP-3.4) |

Ostrzeżenie o wyjściu poza zakres stosowalności ma w standardzie i w Hydrologu kod
`outside_applicability`; do wersji 0.8.1 Hydrolog wydawał je pod kodem `outside_typical_range`, a
wersja 0.9.0 zmieniła kod jednocześnie dla wszystkich użytkowników (ADR-0050, ADR-0064, ADR-0070).
Inżynier może więc liczyć poza zakresem wzoru świadomie, ale nigdy nieświadomie.

## D.3. Dowody poprawności i status wzoru

Każdy wzór grupy A ma co najmniej dwa z trzech rodzajów dowodów: przypadek referencyjny,
wyrocznię i własności sprawdzane testami generowanymi (CMP-5.1). Od dowodów zależy jego
**status** (CMP-2.6), który ramka podaje w pierwszym wierszu:

- `referenced` (*sprawdzony na przypadkach referencyjnych*): przechodzi co najmniej jeden
  przypadek referencyjny ze źródła;
- `oracle only` (*sprawdzony tylko wyroczniami*): żadne źródło nie publikuje przykładu dość
  dokładnego, by go użyć, ale wzór zgadza się z niezależną wyrocznią;
- `unreferenced` (*bez przypadku referencyjnego i wyroczni*): każdy wynik takiego wzoru niesie
  informację `unreferenced_formula` (ADR-0064).

**Przypadek referencyjny** (CMP-6.1) to dane wejściowe razem z wynikiem, który źródło dla nich
publikuje, zapisane z cytatem w plikach `tests/fixtures/formulas/<rodzina>-cases.json`.
Tolerancja porównania nie jest dobierana na oko: to połowa jednostki ostatniej drukowanej cyfry
wyniku, plus wpływ połowy jednostki ostatniej cyfry każdej danej wejściowej (moduł
referencyjny oblicza go w narożnikach przedziałów zaokrągleń), plus każde pośrednie
zaokrąglenie, które źródło wykonało, wypisane krok po kroku. Jeśli to możliwe, przypadki
pokrywają cały zakres typowy. Zanim różnica z przykładem źródła zostanie uznana za błąd wzoru,
przykład sprawdza się w drugim źródle (CMP-5.2): błędny przykład jest błędem testu, a różnica,
którą potwierdzają oba źródła, zostaje zapisana przy przypadku jako rozbieżność z jej
prawdopodobną przyczyną.

**Wyrocznia** (CMP-1.7, CMP-6.2 do CMP-6.4) to niezależna droga do wyniku:

- rozwiązanie dokładne albo inny algorytm, na przykład obliczenie w arytmetyce wymiernej
  (moduł `fractions`) lub z dużą liczbą cyfr (`mpmath`); obliczenie „ręczne” liczy się tylko
  wtedy, gdy jest zapisane w innej postaci niż kod;
- uznana implementacja, na przykład SciPy, z nazwanymi konwencjami obu stron (osobny test
  pilnuje znaku parametru kształtu rozkładu GEV w SciPy);
- wyrocznia zamrożona: wyniki pakietów R (`lmom`, `trend`, `Kendall`, `SPEI`, `climdex.pcic`),
  programów i arkuszy opublikowanych przez innych, uzyskane raz skryptem przechowywanym w
  `tests/oracles/` i zapisane w pliku CSV z wersjami narzędzi, platformą i datą; nigdy nie są
  generowane ponownie do tego samego pliku.

**Tablice opublikowane** (CMP-2.5), na przykład tablice CN z TR-55 czy bezwymiarowy hydrogram
jednostkowy SCS, są plikami danych ze źródłem, wydaniem i stroną, a specyfikacja zapisuje ich
skrót SHA-256. Każdą tablicę przepisano dwa razy niezależnie, a porównanie obu przepisań
przechowuje się w `tests/oracles/`; tablica nigdy nie jest wpisana w kod. W podręczniku tablice
pokazują ramki `spec-table`, czytane wprost z tych plików.

## D.4. Testy generowane ze specyfikacji

Moduł referencyjny generuje testy ze specyfikacji, więc nowy zakres czy warunek dostaje testy
bez pisania ich ręcznie (CMP-6.5):

- **testy zakresów**: dla każdej zmiennej, warunku i warunku koniecznego punkty zakresu
  typowego, krańce zakresu stosowalności i zakresu fizycznego (albo granicy testowej), każda
  granica dokładnie i tuż za nią (najbliższa liczba zmiennoprzecinkowa i jeden procent
  wartości granicy dalej), a każdy test oczekuje skutku z tabeli w D.2;
- **testy typów**: każda zmienna dostaje każdy rodzaj wartości z CMP-4.2 (liczba całkowita i
  zmiennoprzecinkowa Pythona i NumPy, wartość logiczna, `None`, napis, liczba zespolona, tablica
  złego wymiaru, długości lub typu, element nieskończony);
- **testy własności** (biblioteka Hypothesis, MacIver i in. 2019): losowane dane z zakresu
  typowego, stosowalności i fizycznego po kolei; wynik ma być skończony i leżeć w zakresie
  fizycznym albo ma paść zadeklarowany błąd; do tego własności, które podaje specyfikacja:
  monotoniczność względem zmiennych, które wskazuje źródło, zachowanie objętości lub masy z
  podaną tolerancją, przypadki graniczne, symetrie, a dla wzoru jednorodnego wymiarowo
  skalowanie wyniku ze zmianą jednostek danych. Wzór zapisany w jednostkach swojego źródła
  (oznaczony jako zależny od jednostek) ma zamiast tego przypadek referencyjny w każdym układzie
  jednostek, w którym źródła go publikują.

Testy własności mają trzy profile modułu referencyjnego (CMP-6.9): `gate` (deterministyczny,
50 przykładów, w każdym przebiegu bramki jakości), `ci` (1000 przykładów) i `nightly` (20 000
przykładów); profil wybiera zmienna środowiskowa `HYPOTHESIS_PROFILE`. Każdy znaleziony
kontrprzykład zostaje przypięty w teście dekoratorem `@example`.

Ponadto (CMP-6.6 do CMP-6.8):

- moduł referencyjny ma listę **pułapek numerycznych** każdej rodziny wzorów: mianownik będący
  różnicą danych, logarytm lub pierwiastek na granicy dziedziny, funkcja wykładnicza
  przeskalowanej danej na granicy testowej, iteracja bez ograniczenia liczby kroków, granica
  stateczności schematu, brak danych, który się rozprzestrzenia, suma wielu małych składników,
  utrata cyfr przy obliczaniu momentów; specyfikacja wymienia pułapki, które jej dotyczą, a
  każda ma swój test;
- **procedury statystyczne** sprawdza się także na małych próbach, wartościach powtarzających
  się (wiązaniach), zerach i ciągach stałych, zawsze z ustalonym ziarnem losowania;
- każda **tolerancja** porównania ma podany powód; test repozytorium odrzuca porównanie liczb
  bez jawnej tolerancji, a testy wzorów mają znacznik `formula`.

## D.5. Testowanie mutacyjne

Testy, które przechodzą przy luźnych tolerancjach, niewiele dowodzą. Dlatego siłę testów mierzy
się mutacjami (Jia i Harman 2011): program `mutmut` wprowadza do modułów wzorów drobne zmiany
(inny operator, inną stałą, odwrócony warunek) i sprawdza, czy testy wzorów je wykryją
(CMP-7.1). Każda zmiana, która przetrwa w funkcji wzoru grupy A, wymaga nowego testu albo
adnotacji `# pragma: no mutate` z uzasadnieniem, a wydanie nie może się ukazać, dopóki przetrwa
choć jedna zmiana bez adnotacji (CMP-9.3). Testowanie mutacyjne trwa długo, więc działa nocą i
przed wydaniem, nie w bramce jakości. Katalog `docs/FORMULAS.md` podaje wynik dla każdego
modułu; dopóki pomiaru nie wykonano, podaje „not measured”.

## D.6. Błędy we wzorach

Standard dzieli błędy wzorów na dwie klasy (CMP-9.1):

- **błąd poważny**: wynik dla danych z zakresu typowego błędny ponad tolerancję (zła stała,
  wykładnik, jednostka, wpis tablicy, konwencja kalendarza lub kodów), wynik nieskończony albo
  spoza zakresu fizycznego zwrócony bez ostrzeżenia, a także dokument dla użytkownika, który
  podaje inną jednostkę lub inny zakres danej albo wyniku, niż używa kod;
- **błąd zwykły**: brak sprawdzenia skrajnej lub niedopuszczalnej wartości albo błędne równanie
  lub stała w dokumencie przy poprawnym kodzie.

Błąd poważny jest poprawiany od razu i wydawany poza planem wydań; wpis w dzienniku zmian
(`docs/CHANGELOG.md`) podaje wzór, jego wersje przed poprawką i po niej, zakres danych, których
dotyczy, wielkość błędu i sposób odnalezienia oraz przeliczenia zapisanych wyników (CMP-9.2).
Wzory Hydrologa przechodzą w listopadzie 2026 r. przegląd literatury, rodzina po rodzinie;
poprawione błędy wymienia dziennik zmian, a uzasadnienia rozstrzygnięć — decyzje projektowe
(`docs/decisions/`).

Dlatego ramki w tym podręczniku są generowane, a nie przepisywane: rozdział, który podaje
jednostkę lub zakres inny niż kod, byłby błędem poważnym.

## D.7. Jak czytać ramkę wygenerowaną ze specyfikacji

Ramka wzoru grupy A zawiera kolejno:

- **nagłówek**: polską nazwę wzoru, nazwę specyfikacji z odnośnikiem do angielskiej karty w
  `docs/FORMULAS.md`, wersję wzoru (`formula_version`) i status (D.3);
- **równanie** w zapisie matematycznym, z przecinkiem dziesiętnym;
- **dane wejściowe**: symbol, nazwę argumentu w Hydrologu (z dopiskiem „ciąg”, gdy to ciąg
  wartości), znaczenie, jednostkę i trzy zakresy (D.2). Przedziały zapisano jako `[a; b]`
  (krańce należą do przedziału) i `(a; b)` (nie należą), a `∞` oznacza brak ograniczenia;
- **wyniki** z jednostką i zakresem fizycznym;
- **warunki** między danymi i skutek ich niespełnienia;
- **stałe** z wartością, jednostką i źródłem;
- **konwencje**, **założenia** i to, co źródła mówią o zgodności wzoru z obserwacjami;
- **źródła**: każde z miejscem w źródle (wzór, tablica, strona) i adresem, jeśli jest dostępne;
  odsyłacze „(źr. n)” w tabelach wskazują pozycję na tej liście. Opisy źródeł przytoczono w
  brzmieniu specyfikacji, po angielsku, a źródło niedostępne publicznie jest tak oznaczone.

Ramka wzoru grupy B podaje jego definicję, konwencję, stałe i źródło. Ramka `spec-table`
pokazuje opublikowaną tablicę wiersz po wierszu, z jej źródłem i skrótem SHA-256.

Liczby, jednostki i zakresy pochodzą wprost ze specyfikacji. Polskie słowa (nazwy wzorów,
znaczenia zmiennych, konwencje, założenia, nazwy jednostek) są w pliku
[`_specs_pl.toml`](_specs_pl.toml); każdy wpis ma skrót SHA-256 angielskich tekstów, które
tłumaczy, a każde tłumaczenie zachowuje liczby oryginału, więc zmiana specyfikacji wzoru
pokazanego w podręczniku zatrzymuje generator, dopóki ktoś nie przejrzy polskiego tekstu.
Test kontraktowy `tests/contract/test_handbook.py` sprawdza, że ramki są aktualne, że każda
nazwa wskazuje istniejący wzór, że żadna ramka nie została pusta i że polskie teksty
pokazanych wzorów są kompletne. Ramki odświeża polecenie:

```sh
uv run scripts/generate_handbook.py          # wypełnia ramki
uv run scripts/generate_handbook.py --check  # tylko sprawdza, czy są aktualne
```

Tak wygląda ramka retencji maksymalnej S metody SCS-CN (rozdział 3 omawia ją szczegółowo):

<!-- spec:scs_cn_retention -->

<a id="spec-scs_cn_retention"></a>

> **Retencja maksymalna S w metodzie SCS-CN** · specyfikacja [`scs_cn_retention`](../FORMULAS.md#scs_cn_retention) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> S = 25{,}4\left(\frac{1000}{CN} - 10\right)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $CN$ | `cn` | Liczba CN dla warunków wilgotnościowych poprzedzających przyjętych we wzorze | – | [1; 100] | nie podano w źródłach | [30; 98] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $S$ | `retention_mm` | Retencja maksymalna po rozpoczęciu odpływu | mm | [0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1000$ | `s_scale` | Licznik ilorazu przez CN (w calach) | 1000 | in | (źr. 5) |
> | $10$ | `s_offset` | Składnik odejmowany od ilorazu (w calach) | 10 | in | (źr. 5) |
>
> **Konwencje**
>
> - S w mm z calowej postaci wzoru 10-12 NEH 630-10 przez dokładny przelicznik 25,4 mm/cal z tabeli jednostek, co daje wzór 10-13 (S = 25400/CN - 254)
> - CN dla warunków wilgotnościowych poprzedzających przyjętych w obliczeniu: ARC (AMC) II, chyba że przeliczono ją przez `scs_cn_amc`
>
> **Zgodność z obserwacjami według źródeł:** brak: S jest definicją liczby CN (NEH 630-10, wzór 10-12)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-12, p. 10-4 (S = 1000/CN - 10, in); eq. 10-13 (the same in mm) <https://www.hydrocad.net/neh/630ch10.pdf>
> 2. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), eq. 2-4, p. 2-1 <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.1, p. 88 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. Hydrolog's table of TR-55 curve numbers (cn list), the CN its users take for soil-cover complexes, its least and largest CN, 30 (woods and brush, good, A) and 98 (impervious and water)
> 5. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-12, p. 10-4 <https://www.hydrocad.net/neh/630ch10.pdf>
>
> Funkcja `hydrolog.runoff.scs_cn.potential_retention`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:scs_cn_retention -->

## D.8. Wzory pokazane w podręczniku

Wersja, status i dowody każdego wzoru, którego ramka występuje w podręczniku, z odnośnikiem do
ramki. Pełny wykaz wzorów Hydrologa, także tych spoza podręcznika, zawiera katalog
[`docs/FORMULAS.md`](../FORMULAS.md).

<!-- generated:formulas -->

| Wzór | Specyfikacja | Wersja | Status | Przypadki referencyjne | Wyrocznie | Ramka |
|---|---|---|---|---|---|---|
| Kryterium informacyjne Akaikego dla rozkładu dopasowanego do próby | [`akaike_information_criterion`](../FORMULAS.md#akaike_information_criterion) | 1 | `referenced` | 1 | niezależny algorytm | [7](07-przeplywy-maksymalne.md#spec-akaike_information_criterion) |
| Statystyka A² Andersona–Darlinga dla próby względem dopasowanego rozkładu | [`anderson_darling`](../FORMULAS.md#anderson_darling) | 1 | `oracle only` | – | rozwiązanie dokładne, uznana implementacja | [7](07-przeplywy-maksymalne.md#spec-anderson_darling) |
| Opad obszarowy jako średnia arytmetyczna z posterunków | [`areal_mean_precipitation`](../FORMULAS.md#areal_mean_precipitation) | 1 | `referenced` | 1 | rozwiązanie dokładne | [2](02-opad.md#spec-areal_mean_precipitation) |
| Wskaźnik odpływu podziemnego BFI: objętość przepływu podstawowego do objętości przepływu | [`baseflow_index`](../FORMULAS.md#baseflow_index) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-baseflow_index) |
| Hietogram projektowy Beta: całki gęstości rozkładu beta w blokach | [`beta_hyetograph`](../FORMULAS.md#beta_hyetograph) | 1 | `oracle only` | – | rozwiązanie dokładne | [2](02-opad.md#spec-beta_hyetograph) |
| Wskaźnik bifurkacji Hortona dla cieków dwóch kolejnych rzędów | [`bifurcation_ratio`](../FORMULAS.md#bifurcation_ratio) | 1 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne | [1](01-zlewnia.md#spec-bifurcation_ratio) |
| Blokowy hietogram projektowy (o stałym natężeniu) | [`block_hyetograph`](../FORMULAS.md#block_hyetograph) | 1 | `oracle only` | – | rozwiązanie dokładne | [2](02-opad.md#spec-block_hyetograph) |
| Średni kierunek i koncentracja terminów na okręgach ich lat (Bayliss i Jones) | [`circular_mean`](../FORMULAS.md#circular_mean) | 1 | `oracle only` | – | niezależny algorytm, uznana implementacja | [9](09-rezim-i-zmiennosc.md#spec-circular_mean) |
| Wskaźnik kolistości zlewni według Millera | [`circularity_ratio`](../FORMULAS.md#circularity_ratio) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-circularity_ratio) |
| Hydrogram jednostkowy Clarka dla czasu trwania opadu: krzywa czas–powierzchnia i zbiornik liniowy | [`clark`](../FORMULAS.md#clark) | 1 | `oracle only` | – | niezależny algorytm | [5](05-hydrogram-jednostkowy.md#spec-clark) |
| Czas opóźnienia modelu Clarka: środek ciężkości krzywej czas–powierzchnia plus R | [`clark_lag`](../FORMULAS.md#clark_lag) | 1 | `oracle only` | – | niezależny algorytm | [5](05-hydrogram-jednostkowy.md#spec-clark_lag) |
| Wskaźnik zwartości zlewni według Graveliusa | [`compactness_coefficient`](../FORMULAS.md#compactness_coefficient) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-compactness_coefficient) |
| Stopniodni wzrostu i grzania dla każdej doby | [`degree_days`](../FORMULAS.md#degree_days) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| Gęstość sieci rzecznej: długość cieków podzielona przez powierzchnię zlewni | [`drainage_density`](../FORMULAS.md#drainage_density) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-drainage_density) |
| Typ reżimu odpływu rzeki polskiej według Dynowskiej ze współczynników Pardégo | [`dynowska_regime_type`](../FORMULAS.md#dynowska_regime_type) | 1 | `referenced` | 1 | niezależny algorytm | [9](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| Wskaźnik wydłużenia zlewni według Schumma | [`elongation_ratio`](../FORMULAS.md#elongation_ratio) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-elongation_ratio) |
| Spadek uśredniony profilu podłużnego metodą równych pól (prosta przez przekrój z równymi polami nad nią i pod nią) | [`equal_area_slope`](../FORMULAS.md#equal_area_slope) | 1 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne | [1](01-zlewnia.md#spec-equal_area_slope), [5](05-hydrogram-jednostkowy.md#spec-equal_area_slope) |
| Deszcz modelowy Eulera typu II według ATV-DVWK-A 118 z krzywej wysokość–czas trwania | [`euler_ii_hyetograph`](../FORMULAS.md#euler_ii_hyetograph) | 1 | `referenced` | 1 | niezależny algorytm | [2](02-opad.md#spec-euler_ii_hyetograph) |
| Wartości krzywej sum czasów trwania osiągane lub przekraczane przez p % dni (pozycje Weibulla, interpolacja liniowa) | [`exceedance_values`](../FORMULAS.md#exceedance_values) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-exceedance_values) |
| Czas spływu po stoku według wzoru FAA (AC 150/5320-5B, 1970) | [`faa`](../FORMULAS.md#faa) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-faa) |
| Rozkład Fishera–Tippetta minimów rocznych metodą największej wiarygodności i jego kwantyle | [`fisher_tippett_minima`](../FORMULAS.md#fisher_tippett_minima) | 1 | `oracle only` | – | niezależny algorytm, zamrożona wyrocznia | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| Parametry rozkładu maksimów rocznych metodą L-momentów | [`fit_l_moments`](../FORMULAS.md#fit_l_moments) | 1 | `oracle only` | – | niezależny algorytm, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| Parametry rozkładu maksimów rocznych metodą najmniejszych kwadratów na pozycjach wykreślnych | [`fit_least_squares`](../FORMULAS.md#fit_least_squares) | 1 | `oracle only` | – | niezależny algorytm | [7](07-przeplywy-maksymalne.md#spec-fit_least_squares) |
| Parametry rozkładu maksimów rocznych metodą największej wiarygodności | [`fit_maximum_likelihood`](../FORMULAS.md#fit_maximum_likelihood) | 1 | `referenced` | 1 | zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood) |
| Parametry rozkładu maksimów rocznych metodą momentów | [`fit_moments`](../FORMULAS.md#fit_moments) | 1 | `referenced` | 1 | niezależny algorytm | [7](07-przeplywy-maksymalne.md#spec-fit_moments) |
| Wskaźnik formy zlewni według Hortona | [`form_factor`](../FORMULAS.md#form_factor) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-form_factor) |
| Kwantyle uogólnionego rozkładu wartości ekstremalnych (GEV) dla okresów powtarzalności | [`gev_quantiles`](../FORMULAS.md#gev_quantiles) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-gev_quantiles) |
| Czas koncentracji według wzoru Giandottiego (1934) | [`giandotti`](../FORMULAS.md#giandotti) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-giandotti) |
| Dopasowanie średniej i harmonik cyklu rocznego metodą najmniejszych kwadratów | [`harmonic_fit`](../FORMULAS.md#harmonic_fit) | 1 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne | [9](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| Opad dni powyżej progu i jego udział w opadzie dni z opadem | [`heavy_precipitation_share`](../FORMULAS.md#heavy_precipitation_share) | 1 | `referenced` | 1 | rozwiązanie dokładne | [11](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| Całka hipsometryczna zlewni obliczana metodą trapezów z krzywej hipsometrycznej (Strahler) | [`hypsometric_integral`](../FORMULAS.md#hypsometric_integral) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-hypsometric_integral) |
| Opad w punkcie metodą odwrotnych odległości (IDW) z posterunków | [`idw_precipitation`](../FORMULAS.md#idw_precipitation) | 1 | `referenced` | 1 | rozwiązanie dokładne | [2](02-opad.md#spec-idw_precipitation) |
| Opad obszarowy metodą izohiet | [`isohyet_precipitation`](../FORMULAS.md#isohyet_precipitation) | 1 | `referenced` | 1 | rozwiązanie dokładne | [2](02-opad.md#spec-isohyet_precipitation) |
| Klasa opadu rocznego według Kaczorowskiej (opad w % normy) | [`kaczorowska_class`](../FORMULAS.md#kaczorowska_class) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-kaczorowska_class) |
| Czas spływu po stoku według wzoru Kerby'ego (1959) | [`kerby`](../FORMULAS.md#kerby) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-kerby) |
| Czas koncentracji metodą Kerby'ego–Kirpicha (Roussel i in. 2005) | [`kerby_kirpich`](../FORMULAS.md#kerby_kirpich) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-kerby_kirpich) |
| Czas koncentracji według wzoru Kirpicha (postać z Tennessee) | [`kirpich`](../FORMULAS.md#kirpich) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-kirpich) |
| Dokładna dwustronna wartość p statystyki D dwupróbkowego testu Kołmogorowa–Smirnowa z uwzględnieniem wiązań | [`ks_exact`](../FORMULAS.md#ks_exact) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja, zamrożona wyrocznia | [10](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| Przesunięcie w czasie (lag): dopływ przesunięty o stały czas, liniowy między rzędnymi | [`lag`](../FORMULAS.md#lag) | 1 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne | [6](06-transformacja-fali.md#spec-lag) |
| Wskaźnik lemniskaty k zlewni według Chorleya | [`lemniscate_ratio`](../FORMULAS.md#lemniscate_ratio) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-lemniscate_ratio) |
| Wskaźnik długości cieków Hortona dla dwóch kolejnych rzędów | [`length_ratio`](../FORMULAS.md#length_ratio) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-length_ratio) |
| Transformacja fali metodą zbiornikową z krzywą roboczą (zmodyfikowana metoda Pulsa) przez N jednakowych zbiorników | [`level_pool`](../FORMULAS.md#level_pool) | 1 | `referenced` | 1 | niezależny algorytm, rozwiązanie dokładne, uznana implementacja | [6](06-transformacja-fali.md#spec-level_pool) |
| Kaskada n jednakowych zbiorników liniowych, ścisła dla dopływu liniowego między rzędnymi (Nash) | [`linear_reservoir_cascade`](../FORMULAS.md#linear_reservoir_cascade) | 1 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne, uznana implementacja | [6](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| Kwantyle rozkładu logarytmiczno-normalnego dla okresów powtarzalności | [`log_normal_quantiles`](../FORMULAS.md#log_normal_quantiles) | 1 | `referenced` | 1 | niezależny algorytm, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-log_normal_quantiles) |
| Parametry n i K kaskady Nasha dla zlewni niekontrolowanej metodą Lutza (KZGW 2017) | [`lutz`](../FORMULAS.md#lutz) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja | [5](05-hydrogram-jednostkowy.md#spec-lutz) |
| Przepływ podstawowy szeregu dobowego z filtru Lyne'a i Hollicka (standard Ladsona i in. 2013) | [`lyne_hollick`](../FORMULAS.md#lyne_hollick) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-lyne_hollick) |
| Test trendu Manna–Kendalla: S, Var(S) z poprawką na wiązania, Z i dwustronne p | [`mann_kendall`](../FORMULAS.md#mann_kendall) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja, zamrożona wyrocznia | [10](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| Przepływ normalny w korycie trapezowym, prostokątnym lub trójkątnym ze wzoru Manninga, z kinematyczną prędkością fali dQ/dA | [`manning_normal_flow`](../FORMULAS.md#manning_normal_flow) | 1 | `referenced` | 1 | niezależny algorytm, rozwiązanie dokładne | [6](06-transformacja-fali.md#spec-manning_normal_flow) |
| Klasa opadu miesięcznego (opad w % normy) | [`month_precipitation_class`](../FORMULAS.md#month_precipitation_class) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-month_precipitation_class) |
| Transformacja fali metodą Muskingum w N jednakowych pododcinkach (retencja McCarthy'ego, ciągłość wzorem trapezów) | [`muskingum`](../FORMULAS.md#muskingum) | 1 | `referenced` | 1 | rozwiązanie dokładne | [6](06-transformacja-fali.md#spec-muskingum) |
| Transformacja fali metodą Muskingum-Cunge ze stałymi współczynnikami na N jednakowych krokach przestrzennych (K i X według Cunge'a) | [`muskingum_cunge`](../FORMULAS.md#muskingum_cunge) | 1 | `referenced` | 1 | rozwiązanie dokładne | [6](06-transformacja-fali.md#spec-muskingum_cunge) |
| Hydrogram jednostkowy chwilowy Nasha i jego hydrogram jednostkowy dla czasu trwania opadu | [`nash_iuh`](../FORMULAS.md#nash_iuh) | 1 | `referenced` | 1 | niezależny algorytm, rozwiązanie dokładne | [5](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| Czas do szczytu i rzędna szczytowa hydrogramu jednostkowego chwilowego Nasha | [`nash_iuh_peak`](../FORMULAS.md#nash_iuh_peak) | 1 | `referenced` | 1 | uznana implementacja | [5](05-hydrogram-jednostkowy.md#spec-nash_iuh_peak) |
| Parametry n i K modelu Nasha dla zlewni zurbanizowanej z regresji Rao, Delleura i Sarmy (1972) | [`nash_urban_regression`](../FORMULAS.md#nash_urban_regression) | 1 | `oracle only` | – | rozwiązanie dokładne | [5](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| Pozycje wykreślne minimów rocznych: prawdopodobieństwa nieprzewyższenia i okresy powtarzalności | [`non_exceedance_positions`](../FORMULAS.md#non_exceedance_positions) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| Czas koncentracji z równania opóźnienia zlewni NRCS (Mockus 1961) | [`nrcs`](../FORMULAS.md#nrcs) | 1 | `referenced` | 1 | rozwiązanie dokładne | [4](04-czas-koncentracji.md#spec-nrcs) |
| Współczynniki Pardégo: średni przepływ każdego miesiąca do średniego przepływu rocznego | [`parde_coefficients`](../FORMULAS.md#parde_coefficients) | 1 | `referenced` | 1 | rozwiązanie dokładne | [9](09-rezim-i-zmiennosc.md#spec-parde_coefficients) |
| Klasa wskaźnika koncentracji opadów według Olivera | [`pci_class`](../FORMULAS.md#pci_class) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-pci_class) |
| Kwantyle rozkładu Pearsona typu III dla okresów powtarzalności | [`pearson3_quantiles`](../FORMULAS.md#pearson3_quantiles) | 1 | `referenced` | 1 | niezależny algorytm, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-pearson3_quantiles) |
| Test punktu zmiany Pettitta: K, punkt zmiany i przybliżone p | [`pettitt`](../FORMULAS.md#pettitt) | 1 | `referenced` | 1 | niezależny algorytm, zamrożona wyrocznia | [10](10-jednorodnosc-i-trend.md#spec-pettitt) |
| Pozycje wykreślne maksimów rocznych: prawdopodobieństwa przewyższenia i okresy powtarzalności | [`plotting_positions`](../FORMULAS.md#plotting_positions) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja | [7](07-przeplywy-maksymalne.md#spec-plotting_positions) |
| Wskaźnik koncentracji opadów Olivera z dwunastu sum miesięcznych | [`precipitation_concentration_index`](../FORMULAS.md#precipitation_concentration_index) | 1 | `referenced` | 1 | rozwiązanie dokładne | [11](11-wskazniki-meteorologiczne.md#spec-precipitation_concentration_index) |
| Przepływ przy danym stanie wody z potęgowej krzywej natężenia przepływu | [`rating_curve`](../FORMULAS.md#rating_curve) | 1 | `oracle only` | – | rozwiązanie dokładne | [9](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| Krzywa natężenia przepływu Q = a (H - H0)^b dopasowana do par stan–przepływ metodą najmniejszych kwadratów na Q | [`rating_curve_fit`](../FORMULAS.md#rating_curve_fit) | 2 | `oracle only` | – | niezależny algorytm, rozwiązanie dokładne, zamrożona wyrocznia | [9](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| Wiarygodność krzywej natężenia przepływu jako krzywej jednej zależności stan–przepływ (reguła Hydrologa z ADR-0041) | [`rating_curve_plausibility`](../FORMULAS.md#rating_curve_plausibility) | 1 | `unreferenced` | – | – | [9](09-rezim-i-zmiennosc.md#spec-rating_curve_plausibility) |
| Stała recesji przepływu całkowitego: mediana dobowych ilorazów w ciągach malejącego przepływu | [`recession_constant`](../FORMULAS.md#recession_constant) | 1 | `oracle only` | – | rozwiązanie dokładne | [8](08-przeplywy-charakterystyczne-nizowki.md#spec-recession_constant) |
| Wskaźnik rzeźby: deniwelacja zlewni podzielona przez długość (Schumm) | [`relief_ratio`](../FORMULAS.md#relief_ratio) | 1 | `referenced` | 1 | rozwiązanie dokładne | [1](01-zlewnia.md#spec-relief_ratio) |
| Strefy niskiego, średniego i wysokiego tła wodnego według Rybczyńskiego (NTW, STW, WTW) | [`rybczynski_zones`](../FORMULAS.md#rybczynski_zones) | 1 | `unreferenced` | – | – | [9](09-rezim-i-zmiennosc.md#spec-rybczynski_zones) |
| L-momenty i L-skośność próby (nieobciążone momenty ważone prawdopodobieństwem) | [`sample_l_moments`](../FORMULAS.md#sample_l_moments) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-sample_l_moments) |
| Średnia, odchylenie standardowe i skośność próby (momenty zwykłe) | [`sample_moments`](../FORMULAS.md#sample_moments) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja | [7](07-przeplywy-maksymalne.md#spec-sample_moments) |
| Bezwymiarowy hydrogram jednostkowy SCS (NRCS) dla jednostkowego czasu trwania opadu | [`scs`](../FORMULAS.md#scs) | 1 | `referenced` | 1 | rozwiązanie dokładne | [5](05-hydrogram-jednostkowy.md#spec-scs) |
| Liczba CN dla warunków wilgotnościowych poprzedzających I lub III (Hawkins i in. 1985) | [`scs_cn_amc`](../FORMULAS.md#scs_cn_amc) | 1 | `referenced` | 1 | rozwiązanie dokładne | [3](03-opad-efektywny.md#spec-scs_cn_amc) |
| Retencja maksymalna S w metodzie SCS-CN | [`scs_cn_retention`](../FORMULAS.md#scs_cn_retention) | 1 | `referenced` | 1 | rozwiązanie dokładne | [3](03-opad-efektywny.md#spec-scs_cn_retention), [D](D-weryfikacja.md#spec-scs_cn_retention) |
| Odpływ bezpośredni z opadu według metody SCS-CN | [`scs_cn_runoff`](../FORMULAS.md#scs_cn_runoff) | 1 | `referenced` | 1 | rozwiązanie dokładne | [3](03-opad-efektywny.md#spec-scs_cn_runoff) |
| Wskaźnik intensywności opadu SDII: średni opad dnia z opadem | [`sdii`](../FORMULAS.md#sdii) | 1 | `oracle only` | – | rozwiązanie dokładne | [11](11-wskazniki-meteorologiczne.md#spec-sdii) |
| Wskaźnik sezonowości Walsha i Lawlera z dwunastu sum miesięcznych | [`seasonality_index`](../FORMULAS.md#seasonality_index) | 1 | `referenced` | 1 | rozwiązanie dokładne | [9](09-rezim-i-zmiennosc.md#spec-seasonality_index), [11](11-wskazniki-meteorologiczne.md#spec-seasonality_index) |
| Przedział ufności nachylenia Sena według Gilberta | [`sen_interval`](../FORMULAS.md#sen_interval) | 1 | `referenced` | 1 | niezależny algorytm, zamrożona wyrocznia | [10](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| Nachylenie Sena szeregu z wyrazem wolnym Conovera | [`sen_slope`](../FORMULAS.md#sen_slope) | 1 | `referenced` | 1 | rozwiązanie dokładne, uznana implementacja, zamrożona wyrocznia | [10](10-jednorodnosc-i-trend.md#spec-sen_slope) |
| Magnituda odcinka cieku poniżej węzła według Shreve'a | [`shreve_magnitude`](../FORMULAS.md#shreve_magnitude) | 1 | `referenced` | 1 | niezależny algorytm | [1](01-zlewnia.md#spec-shreve_magnitude) |
| Klasa wskaźnika sezonowości według Walsha i Lawlera | [`si_class`](../FORMULAS.md#si_class) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-si_class) |
| Klasa współczynnika hydrotermicznego Sielianinowa (Skowera i Puła) | [`sielianinov_class`](../FORMULAS.md#sielianinov_class) | 1 | `referenced` | 1 | – | [11](11-wskazniki-meteorologiczne.md#spec-sielianinov_class) |
| Współczynnik hydrotermiczny Sielianinowa dla miesiąca lub sezonu | [`sielianinov_coefficient`](../FORMULAS.md#sielianinov_coefficient) | 1 | `referenced` | 1 | rozwiązanie dokładne | [11](11-wskazniki-meteorologiczne.md#spec-sielianinov_coefficient) |
| Syntetyczny hydrogram jednostkowy Snydera: czas opóźnienia, kulminacja, czas podstawy i szerokości | [`snyder`](../FORMULAS.md#snyder) | 1 | `referenced` | 1 | rozwiązanie dokładne | [5](05-hydrogram-jednostkowy.md#spec-snyder) |
| Hydrogram jednostkowy Snydera jako krzywa gamma o objętości 1 mm przechodząca przez kulminację | [`snyder_shape`](../FORMULAS.md#snyder_shape) | 1 | `oracle only` | 1 | rozwiązanie dokładne, uznana implementacja | [5](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| Długość ciągu dni bezopadowych lub z opadem kończącego się w danym dniu | [`spell_lengths`](../FORMULAS.md#spell_lengths) | 1 | `oracle only` | – | niezależny algorytm | [11](11-wskazniki-meteorologiczne.md#spec-spell_lengths) |
| Standaryzowany wskaźnik opadu (SPI) dla sum opadu | [`spi`](../FORMULAS.md#spi) | 1 | `referenced` | 1 | niezależny algorytm, zamrożona wyrocznia | [11](11-wskazniki-meteorologiczne.md#spec-spi) |
| Rozkład gamma sum opadu według przybliżenia Thoma | [`spi_gamma_fit`](../FORMULAS.md#spi_gamma_fit) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [11](11-wskazniki-meteorologiczne.md#spec-spi_gamma_fit) |
| Udział marca i kwietnia w rocznej objętości średnich przepływów miesięcznych | [`spring_share`](../FORMULAS.md#spring_share) | 1 | `oracle only` | – | rozwiązanie dokładne | [9](09-rezim-i-zmiennosc.md#spec-spring_share) |
| Rząd cieku poniżej węzła według Strahlera | [`strahler_order`](../FORMULAS.md#strahler_order) | 1 | `referenced` | 1 | niezależny algorytm | [1](01-zlewnia.md#spec-strahler_order) |
| Wskaźnik częstości cieków: liczba cieków podzielona przez powierzchnię zlewni | [`stream_frequency`](../FORMULAS.md#stream_frequency) | 1 | `oracle only` | – | rozwiązanie dokładne | [1](01-zlewnia.md#spec-stream_frequency) |
| Grupa hydrologiczna gleby według klasy uziarnienia USDA | [`texture_hsg`](../FORMULAS.md#texture_hsg) | 1 | `referenced` | 1 | zamrożona wyrocznia | [3](03-opad-efektywny.md#spec-texture_hsg) |
| Opad obszarowy metodą wieloboków Thiessena | [`thiessen_precipitation`](../FORMULAS.md#thiessen_precipitation) | 1 | `referenced` | 1 | rozwiązanie dokładne | [2](02-opad.md#spec-thiessen_precipitation) |
| Dzień FD, przymrozkowy, mroźny, gorący i upalny oraz noc tropikalna dla jednej doby | [`threshold_days`](../FORMULAS.md#threshold_days) | 1 | `referenced` | 1 | niezależny algorytm | [11](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| Liczba CN kompleksu glebowo-roślinnego z tablic TR-55 | [`tr55_cn`](../FORMULAS.md#tr55_cn) | 1 | `referenced` | 1 | – | [3](03-opad-efektywny.md#spec-tr55_cn) |
| Trójkątny hietogram projektowy Yena i Chowa: całki trójkąta w blokach | [`triangular_hyetograph`](../FORMULAS.md#triangular_hyetograph) | 1 | `referenced` | 1 | rozwiązanie dokładne | [2](02-opad.md#spec-triangular_hyetograph) |
| Odpływ bezpośredni z opadu efektywnego przez splot dyskretny z hydrogramem jednostkowym | [`uh_convolution`](../FORMULAS.md#uh_convolution) | 1 | `referenced` | 1 | rozwiązanie dokładne | [5](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| Klasa uziarnienia gleby USDA według zawartości iłu, piasku i pyłu | [`usda_texture`](../FORMULAS.md#usda_texture) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [3](03-opad-efektywny.md#spec-usda_texture) |
| Kwantyle trójparametrowego rozkładu Weibulla dla okresów powtarzalności | [`weibull_quantiles`](../FORMULAS.md#weibull_quantiles) | 1 | `referenced` | 1 | rozwiązanie dokładne, zamrożona wyrocznia | [7](07-przeplywy-maksymalne.md#spec-weibull_quantiles) |
| Percentyl opadu dni z opadem (kwantyl typu 8) | [`wet_day_percentile`](../FORMULAS.md#wet_day_percentile) | 1 | `referenced` | 1 | rozwiązanie dokładne | [11](11-wskazniki-meteorologiczne.md#spec-wet_day_percentile) |

<!-- /generated:formulas -->

## Źródła

- Hydrolog (2026a). ADR-0050: Formulas declared by specs: Nogat's reference module,
  `formula_versions` in the envelope. [`docs/decisions/0050-formulas-declared-by-specs.md`](../decisions/0050-formulas-declared-by-specs.md).
- Hydrolog (2026b). ADR-0064: Notices of applicability constraints and unreferenced formulas.
  [`docs/decisions/0064-notices-of-applicability-constraints-and-unreferenced-formulas.md`](../decisions/0064-notices-of-applicability-constraints-and-unreferenced-formulas.md).
- Jia Y., Harman M. (2011). An analysis and survey of the development of mutation testing.
  IEEE Transactions on Software Engineering, 37(5), 649–678.
  <https://doi.org/10.1109/TSE.2010.62> (dostęp płatny).
- MacIver D. R., Hatfield-Dodds Z. i in. (2019). Hypothesis: A new approach to property-based
  testing. Journal of Open Source Software, 4(43), 1891. <https://doi.org/10.21105/joss.01891>.
- Nogat (2026). Standard 1.1, *Computations: formulas, their limits and their verification*
  (`standards/COMPUTATIONS.md`, wymagania CMP-1.1 do CMP-9.3). <https://github.com/Daldek/Nogat>.
- Refsgaard J. C., Henriksen H. J. (2004). Modelling guidelines – terminology and guiding
  principles. Advances in Water Resources, 27(1), 71–82.
  <https://doi.org/10.1016/j.advwatres.2003.08.006> (dostęp płatny).
