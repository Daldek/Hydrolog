# 3. Opad efektywny: metoda SCS-CN

Nie cały opad, który spadnie na zlewnię, odpływa z niej w czasie wezbrania. Część zatrzymują
rośliny (intercepcja), część zagłębienia terenu, część wsiąka w glebę i dopiero ta, która
pozostanie, tworzy **odpływ bezpośredni** (powierzchniowy i szybki podpowierzchniowy). Wysokość
tej części, wyrażoną w milimetrach nad całą zlewnią, nazywa się **opadem efektywnym** (ang.
*effective rainfall*, *rainfall excess*). To ona jest daną wejściową hydrogramu jednostkowego
(rozdział 5), który rozkłada ją w czasie na hydrogram odpływu.

Najczęściej używaną metodą wyznaczania opadu efektywnego w małych zlewniach niekontrolowanych
jest metoda SCS-CN (ang. *Soil Conservation Service Curve Number*; dziś NRCS, Natural Resources
Conservation Service), opracowana w latach 50. XX wieku w Służbie Ochrony Gleb USA. W Polsce
jest podstawą obliczania opadu efektywnego w metodyce obliczania przepływów maksymalnych w
zlewniach niekontrolowanych (KZGW 2017, zał. 2, rozdz. VI, wzory 6.1–6.3). Ten rozdział
przedstawia równania metody, liczbę CN i jej tablice, warunki wilgotnościowe poprzedzające
opad oraz grupy hydrologiczne gleb, a w przykładach liczy opad efektywny zlewni Kamiennika.

> **Przykład przewodni.** Zlewnia Kamiennika po Świerzawę (37,22 km², rozdział 1) ma w pliku
> `tests/fixtures/kamiennik.json` liczbę CN = 65 dla przeciętnych warunków wilgotnościowych.
> Opad projektowy to opad o czasie trwania 12 h i prawdopodobieństwie przewyższenia 1 % z atlasu
> PMAXTP IMGW-PIB dla ujścia zlewni (metoda POT): 101,82 mm, pobrany w listopadzie 2026 r. i
> zapisany w `tests/fixtures/pmaxtp_kamiennik_pot.json` (rozdział 2). Źródłem pochodzenia danych
> jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy, dane pochodzą ze
> strony https://klimat.imgw.pl/opady-maksymalne; dane IMGW-PIB zostały przetworzone. Monografia
> projektu: „Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i
> prawdopodobieństwie przewyższenia – Projekt PMAXTP”, red. Bogdan Ozga-Zieliński, IMGW-PIB,
> Warszawa 2022.

## 3.1. Idea metody

Na wykresie zależności odpływu od opadu, sporządzonym dla wielu zdarzeń w jednej zlewni, punkty
układają się wzdłuż krzywej: małe opady nie dają odpływu wcale, a przy dużych krzywa staje się
równoległa do prostej, na której odpływ równa się opadowi, bo zdolność zlewni do zatrzymania
wody się wyczerpuje. V. Mockus opisał tę krzywą jednym założeniem: **stosunek retencji
rzeczywistej do retencji potencjalnej jest równy stosunkowi odpływu rzeczywistego do odpływu
potencjalnego**, a straty i odpływ muszą się bilansować z opadem (NEH 630, rozdz. 10, s. 10-2,
wzory 10-6 i 10-7). Z tych dwóch warunków wynika równanie odpływu metody.

Poszczególne wielkości to:

- **opad** $P$ [mm]: suma opadu zdarzenia, w hietogramie suma narastająca od początku opadu;
- **straty początkowe** $I_a$ [mm] (ang. *initial abstraction*): intercepcja, retencja w
  zagłębieniach terenu, parowanie i wsiąkanie, zanim zacznie się odpływ (TR-55, s. 2-1);
- **retencja potencjalna** $S$ [mm] (ang. *potential maximum retention*; w części polskiej
  literatury $R$): największa ilość wody, jaką zlewnia może jeszcze zatrzymać po rozpoczęciu
  odpływu;
- **retencja rzeczywista** $F$ [mm]: woda zatrzymana po rozpoczęciu odpływu, czyli opad minus
  straty początkowe minus odpływ;
- **opad efektywny** $Q$ [mm] (w Hydrologu $P_e$): wysokość odpływu bezpośredniego.

Metoda jest modelem koncepcyjnym, a nie modelem infiltracji: nie zawiera czasu ani natężenia
opadu, tylko sumy (TR-55, s. 2-11). Wszystkie cechy zlewni, które decydują o stratach — gleba,
pokrycie i użytkowanie terenu, stan roślinności, uwilgotnienie przed opadem — zbiera jedna
liczba: **liczba CN** (numer krzywej odpływu, ang. *runoff curve number*).

## 3.2. Założenia i zakres stosowalności

- Liczba CN z tablic opisuje przeciętne warunki wilgotnościowe przed opadem (podrozdział 3.7) i
  standardowy stosunek strat początkowych do retencji potencjalnej (ramka w podrozdziale 3.4).
  Tablice skalibrowano właśnie przy tym stosunku; inny wymaga innych wartości CN (NEH 630,
  rozdz. 10, s. 10-4).
- Tablice CN wyprowadzono z rocznych wezbrań małych zlewni rolniczych i krótkich opadów (NEH 630,
  rozdz. 9, s. 9-1; zakres danych podaje ramka). Do zlewni dużych i niejednorodnych metodę stosuje
  się po podziale na zlewnie cząstkowe o jednorodnej glebie, pokryciu i opadzie (NEH 630, rozdz. 10,
  s. 10-17).
- Metoda opisuje odpływ bezpośredni z jednego zdarzenia: nie obejmuje przepływu podstawowego, nie
  służy do symulacji ciągłej ani do bilansu rocznego (NEH 630, rozdz. 10, s. 10-2 i 10-19).
- Nie stosuje się jej do roztopów ani do deszczu na zamarzniętym gruncie (TR-55, s. 2-11).
- Przy małym ważonym CN źródło każe użyć innej metody, a przy małym odpływie uważa wynik za mniej
  dokładny (TR-55, s. 2-11; granice podają ramki). Hydrolog ostrzega o CN spoza zakresu
  stosowalności uwagą `outside_typical_range`; o małym odpływie nie ostrzega.
- Duży odpływ podpowierzchniowy i wysoki poziom wód gruntowych (często gleby grupy A i lasy)
  wymagają osądu projektanta (TR-55, s. 2-11).

## 3.3. Retencja potencjalna i liczba CN

Liczba CN to retencja potencjalna przeniesiona na bezwymiarową skalę: im większa liczba CN, tym
mniejsza retencja; największa liczba CN oznacza powierzchnię, która nie zatrzymuje nic, a cały
opad z niej odpływa. Związek retencji z CN pochodzi z NEH 630 w calach; Hydrolog liczy w
milimetrach przez dokładne przeliczenie cala.

<!-- spec:scs_cn_retention -->
<!-- /spec:scs_cn_retention -->

Równanie jest jednorodne w jednostkach długości: przy tym samym CN wynik w milimetrach jest tyle
razy większy od wyniku w calach, ile milimetrów ma cal. Przykłady z podręczników amerykańskich
można więc przeliczać, mnożąc opad i odpływ przez długość cala w milimetrach. **Nie wolno**
natomiast wstawić postaci calowej wzoru na $S$ do obliczeń w milimetrach: retencja wyszłaby tyle
razy za mała, a odpływ znacznie zawyżony.

## 3.4. Straty początkowe i opad efektywny

Straty początkowe przyjmuje się jako stałą część retencji potencjalnej; tę część oznacza się
$\lambda$ i nazywa **współczynnikiem strat początkowych** (ang. *initial abstraction ratio*).
Dopóki opad nie przekroczy strat początkowych, odpływu nie ma; potem odpływ rośnie z opadem coraz
szybciej, a łączne straty zbliżają się do sumy strat początkowych i retencji potencjalnej, nigdy
jej nie przekraczając (NEH 630, rozdz. 10, wzór 10-16).

<!-- spec:scs_cn_runoff -->
<!-- /spec:scs_cn_runoff -->

**Hietogram.** Aby rozłożyć opad efektywny w czasie, równanie stosuje się do **sumy narastającej**
opadu po każdym kroku, a opad efektywny kroku to różnica kolejnych wartości (NEH 630, rozdz. 10,
przykład 10-6; KZGW 2017, wzór 6.2). Tak liczy Hydrolog. Stosowanie równania osobno do opadu
każdego kroku jest błędem: straty początkowe odejmowałoby się wtedy w każdym kroku od nowa.

**Interpretacja wyniku.** Opad efektywny to wysokość warstwy odpływu nad całą zlewnią; objętość
fali to opad efektywny razy powierzchnia zlewni. Stosunek opadu efektywnego do opadu to
**współczynnik odpływu** zdarzenia $C$. Odpływ nie jest proporcjonalny ani do CN, ani do opadu
(NEH 630, rozdz. 10, przykład 10-2): wyników nie wolno skalować, każdy wariant trzeba policzyć.

**Współczynnik strat początkowych.** Hydrolog przyjmuje domyślnie wartość standardową, dla której
skalibrowano tablice CN (ramka). Analiza danych z kilkuset zlewni i poletek doświadczalnych
(Woodward i in. 2003) wykazała lepsze dopasowanie przy mniejszym $\lambda$, ale z inną retencją:
zmiana $\lambda$ wymaga przeliczenia CN zależnością podaną przez tych autorów. NRCS nie przyjęło
tej zmiany w wydaniu NEH 630 z 2025 r. (NEH 630 Subpart H, §630.114). Hydrolog pozwala podać
dowolne $\lambda$ z dopuszczalnego przedziału, ale liczby CN nie przelicza i informuje o tym uwagą
`ia_coefficient_nonstandard`. Najczęstszy błąd to zmiana $\lambda$ przy CN z tablic: odpływ rośnie
wtedy wyraźnie, choć zlewnia się nie zmieniła.

<!-- TODO spec: Woodward et al. (2003) conversion of a curve number of the standard initial abstraction ratio to one of a smaller ratio (S of the smaller ratio a power function of S of the standard one); not computed by Hydrolog -->

W polskiej literaturze dydaktycznej (Pociask-Karteczka 2006, tab. 3.2.4, za Ozga-Zielińska i
Brzeziński 1994) straty początkowe są ułamkiem $\mu$ retencji, który rośnie z liczbą CN w kilku
przedziałach, przy tych samych tablicach CN. Hydrolog nie dobiera $\mu$ sam; wartość z tabeli
podaje się jako współczynnik strat początkowych (przykład 3 niżej).

<!-- TODO spec: the initial losses of Ozga-Zielińska and Brzeziński (1994), a share mu of the retention growing with CN in classes (Pociask-Karteczka 2006, tab. 3.2.4); Hydrolog takes mu as ia_coefficient -->

**Typowe błędy.** Wzór w calach w obliczeniach w milimetrach; równanie zastosowane do opadów
kolejnych kroków zamiast do sumy narastającej; stosowanie metody do zdarzeń wielodniowych, roztopów
i bilansu rocznego; zmiana $\lambda$ bez zmiany CN; porównywanie z przykładem z podręcznika bez
odtworzenia jego zaokrągleń pośrednich (podręczniki często zaokrąglają $S$ lub CN).

### Przykład 1: Kamiennik, opad 12-godzinny o prawdopodobieństwie 1 %

```bash
hydrolog scs effective --cn 65 --precipitation-mm 101.82
```

```text
Wynik:
  cn:                     65
  amc:                    II
  cn_adjusted:            65
  ia_coefficient:         0.2
  retention_mm:           136.769
  initial_abstraction_mm: 27.3538
  total_precipitation_mm: 101.82
  total_effective_mm:     26.2513
  runoff_coefficient:     0.257821
  effective_mm:           brak
```

Retencja potencjalna zlewni wynosi 136,77 mm, a straty początkowe 27,35 mm: dopiero po
27,35 mm deszczu zaczyna się odpływ. Ze 101,82 mm opadu odpływa 26,25 mm, czyli ok. jedna
czwarta (współczynnik odpływu 0,258); 75,57 mm zostaje w zlewni. W rozdziałach 5 i 12 ten sam
opad, rozłożony w czasie hietogramem, przechodzi przez hydrogram jednostkowy; suma opadu
efektywnego jest ta sama, bo równanie liczy się z sumy narastającej.

Ten sam CN z mniejszym współczynnikiem strat początkowych:

```bash
hydrolog scs effective --cn 65 --precipitation-mm 101.82 --ia-coefficient 0.05
```

daje 38,93 mm (współczynnik odpływu 0,382) i uwagę `ia_coefficient_nonstandard`: prawie o połowę
więcej odpływu z tej samej zlewni, tylko dlatego, że zmieniono $\lambda$, a nie przeliczono CN.

### Przykład 2: hietogram godzinowy, potok Niedźwiadka (KZGW 2017)

Metodyka KZGW (2017, zał. 2, przykład 6.2, s. 99–101) liczy opad efektywny zlewni potoku
Niedźwiadka do km 3+450 (7,2 km²) z CN = 79,4 i dobowego opadu 100 mm o prawdopodobieństwie
1 %, rozłożonego na godziny. Hietogram z tabeli 6.3 tej metodyki:

```bash
hydrolog scs effective --cn 79.4 --values 0,0,0,0.01,0.05,0.13,0.27,0.49,0.82,1.28,1.86,2.58,3.44,4.41,5.48,6.59,7.7,8.72,9.56,10.1,10.19,9.67,8.34,5.98,2.33
```

Hydrolog daje retencję 65,90 mm, straty początkowe 13,18 mm i opad efektywny 49,36 mm
(współczynnik odpływu 0,494). Opad efektywny kolejnych kroków (w pierwszych dwunastu, z
7,49 mm opadu, odpływu nie ma):

| krok | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opad [mm] | 3,44 | 4,41 | 5,48 | 6,59 | 7,70 | 8,72 | 9,56 | 10,10 | 10,19 | 9,67 | 8,34 | 5,98 | 2,33 |
| opad efektywny, KZGW [mm] | 0,00 | 0,07 | 0,73 | 1,73 | 2,95 | 4,25 | 5,51 | 6,54 | 7,18 | 7,23 | 6,50 | 4,79 | 1,89 |
| opad efektywny, Hydrolog [mm] | 0,00 | 0,07 | 0,73 | 1,73 | 2,95 | 4,25 | 5,51 | 6,54 | 7,18 | 7,23 | 6,50 | 4,78 | 1,89 |

Wyniki zgadzają się z tabelą metodyki z dokładnością do 0,006 mm. W tekście przykładu KZGW
podano jednak retencję 68,9 mm; dla CN = 79,4 wynosi ona 65,90 mm i tylko z tą wartością tabelę
da się odtworzyć: to błąd druku. W przykładzie 6.1 tej samej metodyki (Jasienica, CN = 81,5,
s. 92–94) Hydrolog odtwarza retencję 57,66 mm i sumę opadu efektywnego 79,6 mm, ale nie wartości
godzinowe tabeli 6.1 (np. w 15. godzinie 4,24 mm wobec wydrukowanych 4,0 mm); ten przykład nadaje
się więc do sprawdzania sumy, a nie przebiegu.

### Przykład 3: straty początkowe według tablicy polskiej

Pociask-Karteczka (2006, s. 111–112) liczy opad efektywny zlewni o CN = 61,2 z 7-godzinnego
opadu 33 mm przy $\mu$ z tablicy dla tego CN, 0,075:

```bash
hydrolog scs effective --cn 61.2 --precipitation-mm 33 --ia-coefficient 0.075
```

Hydrolog daje 2,41 mm (retencja 161,03 mm, straty początkowe 12,08 mm). Podręcznik podaje
2,5 mm, bo zaokrąglił po drodze retencję do 152 mm i straty do 12 mm.

## 3.5. Tablice CN

Liczbę CN odczytuje się dla **kompleksu glebowo-roślinnego** (ang. *hydrologic soil-cover
complex*): połączenia hydrologicznej grupy gleby (podrozdział 3.8) z pokryciem i użytkowaniem
terenu, sposobem uprawy i **stanem hydrologicznym** pokrycia (ang. *hydrologic condition*: zły,
średni, dobry) (NEH 630, rozdz. 9, s. 9-1). Dla pastwisk stan zależy od zwarcia darni i
intensywności wypasu, dla lasu od tego, czy ściółkę i podszyt zniszczył wypas lub wypalanie
(TR-55, tab. 2-2c, przypisy). Wartości dla terenów zabudowanych są złożone: powierzchnie
nieprzepuszczalne połączone z kanalizacją i reszta działki jako teren otwarty w dobrym stanie
(TR-55, tab. 2-2a, przypisy).

Hydrolog trzyma tablicę TR-55 jako plik danych ze źródłem każdego wiersza, przepisany dwa razy
niezależnie i porównany (standard Nogat CMP-2.5; ADR-0051); w kodzie nie ma ani jednej wartości
CN.

<!-- spec:tr55_cn -->
<!-- /spec:tr55_cn -->

<!-- spec-table:tr55_cn -->
<!-- /spec-table:tr55_cn -->

Kilka zasad tablicy Hydrologu:

- **Uprawy rzędowe i zboża** (`row_crops`, `small_grain`) mają w TR-55 tylko stan zły i dobry, w
  rzędach prostych. Hydrolog do wersji 0.8.1 miał dla nich także stan średni, bez źródła (średnia
  z dwóch wierszy), i przyjmował go, gdy stanu nie podano; wersja rozwojowa 0.9.0 wymaga podania
  stanu dla tych pokryć i odrzuca stan średni (ADR-0051).
- Dla pozostałych pokryć zależnych od stanu Hydrolog bez podanego stanu przyjmuje stan średni i
  informuje o tym uwagą `condition_defaulted`. Podawaj stan zawsze.
- **Roślinność zielna** (`herbaceous`) ma wartości pastwiska z tablicy 2-2c, jak każe przypis 1
  tablicy 2-2d dla terenów w klimacie wilgotnym; własny wiersz tablicy 2-2d dotyczy terenów
  suchych i półsuchych.
- **Wody powierzchniowe** mają CN według NEH 630 (rozdz. 9, s. 9-1), jak powierzchnie
  nieprzepuszczalne, a nie największą możliwą liczbę CN spotykaną w części podręczników (Chow i
  in. 1988; HEC-HMS).

Polska tablica metodyki KZGW (2017, zał. 2, tabela C.1, s. 131) powtarza większość wierszy TR-55,
ale różni się w kilku: dla lasu gęstego na glebach grupy A podaje 25, dla pastwisk w warunkach
przeciętnych na glebach grupy C 78, a wierszy upraw (okopowych, zbożowych, motylkowych) w
„warunkach przeciętnych” w TR-55 nie ma. Hydrolog tej tablicy nie zawiera; czy powinien ją
oferować dla polskich projektów, jest otwartym pytaniem przeglądu literatury z 2026 r.

**Przykład: odczyt z tablicy.**

```bash
hydrolog cn lookup --hsg C --land-cover pasture --condition good
```

daje CN = 74, wartość przykładu 10-1 NEH 630 (pastwisko w dobrym stanie na glebie grupy C).
Ten sam odczyt dla innych kompleksów:

| Polecenie | CN |
|---|---|
| `hydrolog cn lookup --hsg B --land-cover forest --condition good` | 55 |
| `hydrolog cn lookup --hsg C --land-cover forest --condition good` | 70 |
| `hydrolog cn lookup --hsg B --land-cover small_grain --condition good` | 75 |
| `hydrolog cn lookup --hsg C --land-cover small_grain --condition good` | 83 |
| `hydrolog cn lookup --hsg B --land-cover residential_quarter_acre` | 75 |
| `hydrolog cn lookup --hsg B --land-cover meadow` | 58 |

Bez stanu hydrologicznego pastwisko dostaje stan średni z uwagą:

```bash
hydrolog cn lookup --hsg B --land-cover pasture
```

```text
  cn:                69
  ...
  condition_applied: fair
Uwagi:
  [informacja] condition_defaulted: No hydrologic condition given for 'pasture': 'fair' was used.
```

a uprawy rzędowe bez stanu są odrzucane, bo TR-55 nie ma dla nich stanu średniego:

```bash
hydrolog cn lookup --hsg B --land-cover row_crops
```

```text
Błąd (validation_error): Nieprawidłowe dane wejściowe
  TR-55 gives 'row_crops' in the conditions ['poor', 'good'] only: give one of them
```

Rozrzut CN jednego pokrycia między stanami pokazuje `cn range`; dla lasu:

```bash
hydrolog cn range --land-cover forest
```

daje na glebach grup A, B, C i D odpowiednio 30–45, 55–66, 70–77 i 77–83: stan lasu zmienia CN o
6–15, a grupa gleby o kilkadziesiąt.

## 3.6. CN ważony zlewni

Zlewnia składa się zwykle z wielu kompleksów glebowo-roślinnych. Najprostszy sposób to średnia
liczb CN ważona ich powierzchniami (NEH 630, rozdz. 10, przykład 10-4; TR-55, arkusz 2; KZGW 2017,
wzór 6.3); polecenie `cn weighted` liczy ją z powierzchni albo udziałów części. Wynik jest
ułamkowy i tak przekazuje się go dalej, bez zaokrąglania.

<!-- spec:weighted_cn -->
<!-- /spec:weighted_cn -->

Szczególnym przypadkiem jest teren zabudowany o znanym udziale powierzchni nieprzepuszczalnych
połączonych z odwodnieniem (NEH 630, rozdz. 9, wzór 9-1): to ta sama średnia ważona dwóch części,
przepuszczalnej i nieprzepuszczalnej, z CN powierzchni nieprzepuszczalnych z tablicy.

Równanie odpływu jest nieliniowe, więc odpływ obliczony z CN ważonego nie jest równy średniej
ważonej odpływów obliczonych osobno dla każdego kompleksu. Ten drugi sposób, **ważony odpływ**,
NEH 630 (rozdz. 10, s. 10-11) uznaje za zgodny z danymi, a ważony CN za prostszy; różnica jest
największa przy dużym zróżnicowaniu CN i małych opadach (przykład 10-5 NEH 630: przy opadzie
2 cali odpływ z ważonego CN 0,17 cala, a ważony odpływ 0,26 cala; przy 10 calach 5,83 i 5,85
cala). Hydrolog liczy odpływ z CN ważonego.

<!-- TODO spec: the weighted runoff of NEH 630 ch. 10 (p. 10-11), the area-weighted mean of the runoff of each soil-cover complex; not computed by Hydrolog -->

**Przykład: jak bardzo CN zależy od gleby (dane umowne).** W zlewni Kamiennika lasy zajmują
57,4 %, a zabudowa 1 % powierzchni (pola `forest_pct` i `urban_pct` pliku przykładu). Przyjmijmy
dla ilustracji, że pozostałe 41,6 % to zboża w dobrym stanie, a zabudowa to działki ¼ akra, i
policzmy CN zlewni dla dwóch wariantów gleb: wszystkie w grupie B albo wszystkie w grupie C (CN
części z tabeli w podrozdziale 3.5).

```bash
hydrolog cn weighted --cn-values 55,75,75 --fractions 0.574,0.01,0.416
hydrolog cn weighted --cn-values 70,83,83 --fractions 0.574,0.01,0.416
hydrolog scs effective --cn 63.52 --precipitation-mm 101.82
hydrolog scs effective --cn 75.54 --precipitation-mm 101.82
```

| Gleby | CN ważony | Opad efektywny z 101,82 mm | Współczynnik odpływu |
|---|---|---|---|
| grupa B | 63,52 | 24,15 mm | 0,237 |
| grupa C | 75,54 | 43,48 mm | 0,427 |

Ta sama zlewnia i to samo pokrycie dają o 80 % więcej opadu efektywnego, gdy gleby zaliczy się do
grupy C zamiast B. Dlatego przypisanie grupy glebom (podrozdział 3.8) waży w metodzie SCS-CN co
najmniej tyle co mapa pokrycia terenu.

## 3.7. Warunki wilgotnościowe poprzedzające opad (AMC)

Ta sama zlewnia daje z tego samego deszczu inny odpływ po suchym tygodniu, a inny po kilku dniach
deszczowych. Metoda SCS-CN ujmuje to przez **warunki wilgotnościowe poprzedzające** (ang.
*antecedent moisture condition*, AMC): I — sucho, II — przeciętnie, III — mokro. Wartości CN w
tablicach odpowiadają warunkom II. Nowsze wydania NEH 630 mówią o **warunkach odpływu
poprzedzających** (ang. *antecedent runoff condition*, ARC), bo zmienność CN wynika nie tylko z
wilgotności gleby, ale też z natężenia i czasu trwania opadu, pokrycia, fazy wegetacji i
temperatury (NEH 630, rozdz. 10, s. 10-5); warunki I i III odpowiadają w przybliżeniu 10. i 90.
percentylowi rozkładu CN zlewni (NEH 630, rozdz. 10, rys. 10-4, za Hjelmfeltem 1991).

Dawniej klasę AMC wyznaczano z sumy opadów z pięciu dni poprzedzających, z innymi progami w
okresie wegetacyjnym i poza nim (SCS 1972, za Chow i in. 1988, tab. 5.5.1; w milimetrach
Pociask-Karteczka 2006, tab. 3.2.2, za Ozga-Zielińska i Brzeziński 1994). NEH 630 stwierdza
jednak, że w badanych zlewniach nie znaleziono związku między opadem z pięciu dni poprzedzających
a CN (rozdz. 10, s. 10-7), a tabelę pięciodniową usunięto z NEH-4 w 1993 r. (Ponce i Hawkins
1996). Wybór warunków jest więc decyzją projektanta; w przykładach metodyki KZGW (2017) przyjęto
warunki przeciętne. Hydrolog też nie wyznacza klasy sam: podaje się ją opcją `amc`.

**Przeliczenie CN.** NEH 630 (rozdz. 10, tabela 10-1) podaje odpowiedniki CN dla warunków I i
III w tabeli. Hydrolog przelicza je wzorami Hawkinsa, Hjelmfelta i Zevenbergena (1985, za Ponce
i Hawkins 1996), dopasowanymi do tej tabeli przez stały stosunek retencji w warunkach I lub III
do retencji w warunkach II, i zaokrągla wynik do liczby całkowitej, jak tabela.

<!-- spec:scs_cn_amc -->
<!-- /spec:scs_cn_amc -->

Konwencji przeliczania jest kilka: tabela NRCS, dopasowanie Hawkinsa i in. (1985), inne
dopasowanie Chow i in. (1988, wzory 5.5.7–5.5.8) i czeskie (Janeček i Kovář 2010, za Stehlík i
in. 2016). Różnią się o pojedyncze jednostki CN (różnice wzorów Hydrologu względem tabeli NRCS
podaje ramka), a przy warunkach suchych zmienia to odpływ nawet o kilkanaście procent. Zawsze
podawaj, której użyłeś.

**Typowe błędy.** Przypisywanie wzorów Hawkinsa i in. autorom Chow i in. (to inne wzory); błędy
druku w literaturze: we wzorze 12 artykułu Banasika i in. (2014) wydrukowano błędnie jeden ze
współczynników (poprawną postać podają źródła ramki), a w internetowym wydaniu artykułu Ponce'a i
Hawkinsa wzór 16 ma znak minus zamiast plusa; przeliczanie CN poza zakresem stosowalności wzorów
(Hydrolog ostrzega uwagą `outside_typical_range`); przeliczanie CN poszczególnych kompleksów i
dopiero potem ważenie — przeliczenie jest nieliniowe, więc Hydrolog i Hydrograf przeliczają CN
ważony zlewni.

**Przykład 1: Zagożdżonka (Banasik i in. 2014).** Tablicowy CN zlewni Zagożdżonki (23,4 km²,
zlewnia doświadczalna SGGW w Polsce centralnej) wynosi 74,6. Hydrolog przelicza go na CN = 87
dla warunków III (artykuł podaje 87,3) i CN = 56 dla warunków I; artykuł podaje 59,6, bo liczył
z błędnie wydrukowanym współczynnikiem.

```bash
hydrolog scs effective --cn 74.6 --precipitation-mm 50 --amc III
hydrolog scs effective --cn 74.6 --precipitation-mm 50 --amc I
```

**Przykład 2: Kamiennik w trzech stanach wilgotności.**

```bash
hydrolog scs effective --cn 65 --precipitation-mm 101.82 --amc I
hydrolog scs effective --cn 65 --precipitation-mm 101.82
hydrolog scs effective --cn 65 --precipitation-mm 101.82 --amc III
```

| Warunki | CN | Retencja $S$ [mm] | Straty początkowe [mm] | Opad efektywny [mm] | Współczynnik odpływu |
|---|---|---|---|---|---|
| I (sucho) | 45 | 310,44 | 62,09 | 4,51 | 0,044 |
| II (przeciętnie) | 65 | 136,77 | 27,35 | 26,25 | 0,258 |
| III (mokro) | 81 | 59,58 | 11,92 | 54,07 | 0,531 |

Ten sam opad stuletni daje po suchym okresie 4,5 mm odpływu, a po mokrym 54,1 mm: dwanaście razy
więcej. Warunki wilgotnościowe zmieniają wynik bardziej niż jakikolwiek inny wybór w metodzie, a
nie wynikają z żadnego wzoru; przyjęte warunki trzeba zawsze podać razem z wynikiem.

## 3.8. Grupy hydrologiczne gleb (HSG)

**Grupa hydrologiczna gleby** (ang. *hydrologic soil group*, HSG) opisuje zdolność gleby do
przyjmowania i przewodzenia wody w najbardziej niekorzystnych warunkach: przy glebie najsilniej
nawilgoconej w ciągu roku, niezamarzniętej, gołej i przy największym pęcznieniu iłów; nachylenia
terenu nie bierze się pod uwagę (NEH 630, rozdz. 7, s. 7-1). Grupa nie jest liczbą CN: wyznacza
ją dopiero razem z pokryciem terenu (podrozdział 3.5).

| Grupa | Potencjał odpływu (NEH 630, rozdz. 7) | Typowe uziarnienie |
|---|---|---|
| A | mały; woda przewodzona swobodnie | piaski, żwiry |
| B | umiarkowanie mały; przewodzenie nieutrudnione | piaski gliniaste, gliny piaszczyste |
| C | umiarkowanie duży; przewodzenie nieco ograniczone | gliny, pyły gliniaste, gliny piaszczysto-ilaste, gliny ilaste, gliny pylasto-ilaste |
| D | duży; ruch wody ograniczony lub bardzo ograniczony | iły; także gleby z płytką warstwą nieprzepuszczalną lub płytkim zwierciadłem wody gruntowej |

O grupie decyduje według NEH 630 (rozdz. 7, tabela 7-1) przewodność hydrauliczna nasycona
(współczynnik filtracji, ang. *saturated hydraulic conductivity*) **warstwy najmniej
przepuszczalnej** profilu oraz głębokość do warstwy nieprzepuszczalnej i do zwierciadła wody
gruntowej. Gleby z wysoko położonym zwierciadłem wody, które można odwodnić, mają grupy podwójne
(A/D, B/D, C/D): pierwsza litera dotyczy gleby odwodnionej, druga nieodwodnionej.

W Polsce przy metodzie SCS-CN grupy przypisuje się zwykle na podstawie map glebowo-rolniczych i
uziarnienia; jednolitej, otwarcie dostępnej tabeli przejścia od polskich kategorii glebowych do
grup HSG przegląd literatury nie odnalazł. Hydrolog wyznacza grupę z uziarnienia (podrozdziały
3.9–3.10).

**Typowe błędy.** Grupa wzięta tylko z wierzchniej warstwy (piasek na glinie wygląda jak grupa A,
a decyduje warstwa niżej); pominięcie płytkiej wody gruntowej w dolinach i na mokradłach (takie
gleby są w grupie D albo w grupie podwójnej); grupy gleb naturalnych na terenach przekształconych
(wykopy, nasypy, zagęszczenie), gdzie NEH zaleca badania terenowe.

## 3.9. Uziarnienie gleby: trójkąt USDA

**Uziarnienie** (ang. *soil texture*) to udział frakcji piasku, pyłu i iłu w częściach ziemistych
gleby. Klasyfikacja Polskiego Towarzystwa Gleboznawczego z 2008 r. (PTG 2009) przyjęła granice
frakcji amerykańskiego Departamentu Rolnictwa (USDA, ramka niżej) i dzieli część klas USDA na
podgrupy:

| Klasa USDA (kod Hydrologu) | Grupa granulometryczna PTG 2008 |
|---|---|
| sand (`sand`) | piasek luźny (pl), piasek słabogliniasty (ps) |
| loamy sand (`loamy_sand`) | piasek gliniasty (pg) |
| sandy loam (`sandy_loam`) | glina piaszczysta (gp), glina lekka (gl) |
| loam (`loam`) | glina zwykła (gz) |
| silt loam (`silt_loam`) | pył gliniasty (pyg), pył ilasty (pyi) |
| silt (`silt`) | pył zwykły (pyz) |
| sandy clay loam (`sandy_clay_loam`) | glina piaszczysto-ilasta (gpi) |
| clay loam (`clay_loam`) | glina ilasta (gi) |
| silty clay loam (`silty_clay_loam`) | glina pylasto-ilasta (gpyi) |
| sandy clay (`sandy_clay`) | ił piaszczysty (ip) |
| silty clay (`silty_clay`) | ił pylasty (ipy) |
| clay (`clay`) | ił zwykły (iz), ił ciężki (ic) |

Dwanaście klas USDA dzieli trójkąt uziarnienia bez luk i bez nakładania się. Ich definicje
(Soil Survey Manual, Soil Science Division Staff 2017, rozdz. 3, s. 122–124) Hydrolog trzyma jako
plik danych: każdy warunek klasy to nierówność liniowa względem udziałów trzech frakcji, z
granicą włączoną albo wyłączoną tak, jak brzmi tekst podręcznika (ADR-0066).

<!-- spec:usda_texture -->
<!-- /spec:usda_texture -->

<!-- spec-table:usda_texture -->
<!-- /spec-table:usda_texture -->

Klasa zależy tylko od udziałów frakcji w ich sumie: zawartości można podać w procentach albo w
g/kg (jak w SoilGrids), a suma nie musi wynosić 100, bo materia organiczna i szkielet leżą poza
częściami ziemistymi. Trzy zera nie są glebą i Hydrolog je odrzuca.

**Typowe błędy.** Stare polskie mapy glebowo-rolnicze opisują uziarnienie według normy
BN-78/9180-11 (inne granice frakcji i grup) albo kategoriami agronomicznymi; przed użyciem
trójkąta USDA trzeba je przeliczyć (tabele zgodności podaje aneks PTG 2008). SoilGrids łączy dane,
w których granica pyłu i piasku leży w różnych miejscach (według USDA i według ISO/FAO), więc
klasy blisko tej granicy są niepewne (ISRIC). Hydrolog i Kartograf do wersji 0.8.1 włącznie
zaliczały składy leżące dokładnie na dwóch liniach trójkąta do klasy sąsiedniej; Kartograf 0.8.2 i
wersja rozwojowa 0.9.0 Hydrologu liczą je tak, jak definiuje podręcznik USDA (przykład niżej).

**Przykład.** Polecenie `soil texture` klasyfikuje jedną próbkę i od razu przypisuje grupę
(podrozdział 3.10). Składy z przykładów definicji podręcznika USDA:

| Polecenie | Klasa | Grupa |
|---|---|---|
| `hydrolog soil texture --clay 5 --sand 90 --silt 5` | `sand` | A |
| `hydrolog soil texture --clay 10 --sand 60 --silt 30` | `sandy_loam` | B |
| `hydrolog soil texture --clay 20 --sand 40 --silt 40` | `loam` | B |
| `hydrolog soil texture --clay 15 --sand 20 --silt 65` | `silt_loam` | B |
| `hydrolog soil texture --clay 30 --sand 30 --silt 40` | `clay_loam` | C |
| `hydrolog soil texture --clay 45 --sand 20 --silt 35` | `clay` | D |
| `hydrolog soil texture --clay 450 --sand 200 --silt 350` | `clay` | D |

Ostatni wiersz to skład z poprzedniego w g/kg: klasa jest ta sama. Składy na granicach klas:

| Polecenie | Klasa | Grupa |
|---|---|---|
| `hydrolog soil texture --clay 19.9 --sand 60.1 --silt 20` | `sandy_loam` | B |
| `hydrolog soil texture --clay 20 --sand 60 --silt 20` | `sandy_clay_loam` | C |
| `hydrolog soil texture --clay 27 --sand 38 --silt 35` | `clay_loam` | C |

W definicjach gliny piaszczystej i gliny podręcznik USDA mówi o zawartości iłu „mniejszej niż”
wartość graniczna (tabela definicji wyżej), więc składy z dokładnie 20 i 27 % iłu należą już do
klas o większej zawartości iłu, a wraz z nimi do grupy C. Hydrolog do wersji 0.8.1 włącznie
dawał dla nich glinę piaszczystą i glinę (grupa B).

## 3.10. Od uziarnienia do grupy HSG

Hydrolog przypisuje grupę klasie uziarnienia tablicą, również trzymaną jako plik danych ze
źródłem każdego wiersza (ADR-0066). Jej podstawą jest tablica TR-55 (aneks A, s. A-1) dla gleb
przekształconych (np. przy urbanizacji), uzupełniona o typowe uziarnienie grup według NEH 630
(rozdz. 7, s. 7-2).

<!-- spec:texture_hsg -->
<!-- /spec:texture_hsg -->

<!-- spec-table:texture_hsg -->
<!-- /spec-table:texture_hsg -->

Tablica jest więc mieszana: dla gliny piaszczystej surowsza od TR-55, dla glin ilastych i
pylasto-ilastych łagodniejsza, a pył dostaje grupę pyłu gliniastego (ramka). Gdyby trzymać się
NEH 630 i przewodności hydraulicznej typowej dla klas (Rawls i in. 1982, cytowani za źródłami
wtórnymi), glina i pył gliniasty — gleby lessowe południowej Polski — trafiłyby do grupy C, a
piasek gliniasty do B; powrót do samej tablicy TR-55 dałby glinie piaszczystej grupę A, a glinom
ilastym D. Każda z tych zmian przesuwa liczby CN wszystkich programów, które z tablicy korzystają
(Hydrograf, Kartograf); wybór tablicy pozostaje otwartym pytaniem autora (ADR-0066). Przykład z
podrozdziału 3.6 pokazuje, ile to znaczy dla odpływu.

**Rastry.** Dla całej zlewni grupy wyznacza się z rastrów zawartości iłu, piasku i pyłu, np. z
SoilGrids (ISRIC), które pobiera Kartograf: `soil hsg` klasyfikuje każdą komórkę, a `soil
hsg-stats` liczy powierzchnie grup, które są wagami dla `cn weighted`.

<!-- spec:hsg_of_amounts -->
<!-- /spec:hsg_of_amounts -->

<!-- spec:usda_texture_codes -->
<!-- /spec:usda_texture_codes -->

<!-- spec:texture_hsg_codes -->
<!-- /spec:texture_hsg_codes -->

```bash
hydrolog soil hsg --clay-path clay.tif --sand-path sand.tif --silt-path silt.tif --output hsg.tif
hydrolog soil hsg-stats --hsg-path hsg.tif
```

Grupa z samego uziarnienia nie uwzględnia wody gruntowej, warstw nieprzepuszczalnych, szkieletu
ani struktury gleby (NEH 630, rozdz. 7, tabela 7-1). Kartograf bierze w każdej komórce warstwę
najmniej przepuszczalną z pięciu warstw SoilGrids do głębokości 1 m, co jest bliższe idei NEH,
ale kryteriów wody gruntowej i warstwy nieprzepuszczalnej nie stosuje, bo SoilGrids ich nie
podaje; Hydrograf przypisuje grupę D glebom pod mokradłami z BDOT10k. Mapy globalne o oczku
250 m, takie jak SoilGrids, nie zastępują kartowania gleb (ISRIC).

## 3.11. Podsumowanie: opad efektywny Kamiennika

| Wariant | CN | Opad efektywny z 101,82 mm | Współczynnik odpływu |
|---|---|---|---|
| warunki przeciętne (II), tablicowe $\lambda$ | 65 | 26,25 mm | 0,258 |
| warunki suche (I) | 45 | 4,51 mm | 0,044 |
| warunki mokre (III) | 81 | 54,07 mm | 0,531 |
| warunki II, $\lambda$ = 0,05 bez przeliczenia CN | 65 | 38,93 mm | 0,382 |
| warunki II, gleby B, pokrycie umowne | 63,52 | 24,15 mm | 0,237 |
| warunki II, gleby C, pokrycie umowne | 75,54 | 43,48 mm | 0,427 |

Opad efektywny w warunkach przeciętnych, 26,25 mm, jest daną wejściową hydrogramu
jednostkowego (rozdział 5) i studium przypadku (rozdział 12). Rozrzut wariantów pokazuje, że w
metodzie SCS-CN najwięcej niepewności wnoszą warunki wilgotnościowe i grupy gleb, a nie samo
równanie.

## Źródła

- Banasik K., Rutkowska A., Kohnová S. (2014). Retention and curve number variability in a small
  agricultural catchment: the probabilistic approach. *Water* 6(5), 1118–1133.
  https://doi.org/10.3390/w6051118
- Chow V.T., Maidment D.R., Mays L.W. (1988). *Applied Hydrology*. McGraw-Hill, New York, §5.5
  (niedostępne w otwartym dostępie).
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych*, załącznik 2
  do OPZ (wersja ujednolicona), rozdz. VI i tabela C.1.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Pociask-Karteczka J. (2006). 3.2. Opad efektywny. W: Pociask-Karteczka J. (red.), *Zlewnia.
  Właściwości i procesy*. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, s. 106–112.
  https://ruj.uj.edu.pl/server/api/core/bitstreams/4f97c03a-5c36-4e18-9d00-f93f8c754db9/content
- Polskie Towarzystwo Gleboznawcze (2009). Klasyfikacja uziarnienia gleb i utworów mineralnych —
  PTG 2008. *Roczniki Gleboznawcze* 60(2), 5–16 (kopia:
  https://mpodlasinski.zut.edu.pl/fileadmin/Pdfy/Uziarnienie_PTG_2008.pdf).
- Ponce V.M., Hawkins R.H. (1996). Runoff curve number: has it reached maturity? *Journal of
  Hydrologic Engineering* 1(1), 11–19. https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf
- Soil Science Division Staff (2017). *Soil Survey Manual*. USDA Agriculture Handbook No. 18,
  rozdz. 3, s. 122–125.
  https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/GOVPUB-A-PURL-gpo113168.pdf
- Stehlík M., Pavel M., Burian V. (2016). Postup vyhodnocení odtokových poměrů… *VTEI* 58(4),
  20–22. https://doi.org/10.46555/VTEI.2016.05.004
- USDA-NRCS (2004). *National Engineering Handbook, Part 630 Hydrology*, rozdz. 9: Hydrologic
  Soil-Cover Complexes i rozdz. 10: Estimation of Direct Runoff from Storm Rainfall.
  https://www.hydrocad.net/neh/630ch9.pdf, https://www.hydrocad.net/neh/630ch10.pdf
- USDA-NRCS (2009). *National Engineering Handbook, Part 630 Hydrology*, rozdz. 7: Hydrologic Soil
  Groups. https://www.hydrocad.net/neh/630ch7.pdf
- USDA-NRCS (2025). *210 NEH Part 630 Subpart H – Estimation of Direct Runoff from Storm Rainfall*.
  https://directives.nrcs.usda.gov/sites/default/files2/1754923466/Subpart%20H%20%E2%80%93%20Estimation%20of%20Direct%20Runoff%20from%20Storm%20Rainfall.pdf
- USDA-SCS (1986). *Urban Hydrology for Small Watersheds*, Technical Release 55, 2nd ed.
  https://www.hydrocad.net/pdf/TR-55%20Manual.pdf
- Woodward D.E., Hawkins R.H., Jiang R., Hjelmfelt A.T., Van Mullem J.A., Quan Q.D. (2003). Runoff
  curve number method: examination of the initial abstraction ratio. *World Water & Environmental
  Resources Congress*, ASCE. http://ruby.fgcu.edu/courses/twimberley/EnviroPol/CurveNumber.pdf
- ISRIC — World Soil Information. SoilGrids, dokumentacja (FAQ).
  https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html
- IMGW-PIB. Atlas PMAXTP, https://klimat.imgw.pl/opady-maksymalne; monografia: Ozga-Zieliński B.
  (red.) (2022), *Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i
  prawdopodobieństwie przewyższenia – Projekt PMAXTP*, IMGW-PIB, Warszawa.
- Hydrolog: ADR-0050 (wzory deklarowane specyfikacjami), ADR-0051 (tablica TR-55 jako dane),
  ADR-0066 (tablice uziarnienia i HSG jako dane), `docs/decisions/` w repozytorium.

Cytowane za źródłami wtórnymi (niedostępne w otwartym dostępie albo nieotwierane): Hawkins R.H.,
Hjelmfelt A.T., Zevenbergen A.W. (1985), *Journal of Irrigation and Drainage Engineering* 111(4),
330–340; Hjelmfelt A.T. (1991); Janeček M., Kovář P. (2010), *Vodní hospodářství* 7/2010;
Ozga-Zielińska M., Brzeziński J. (1994), *Hydrologia stosowana*, PWN; Rawls W.J., Brakensiek
D.L., Saxton K.E. (1982), *Transactions of the ASAE* 25(5); SCS (1972), *National Engineering
Handbook*, Section 4.
