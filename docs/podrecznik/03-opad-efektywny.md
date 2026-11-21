# 3. Opad efektywny: metoda SCS-CN

Nie cały opad, który spadnie na zlewnię, odpływa z niej w czasie wezbrania. Część zatrzymują
rośliny (intercepcja), część zagłębienia terenu, część wsiąka w glebę i dopiero ta, która
pozostanie, tworzy **odpływ bezpośredni** (ang. *direct runoff*; powierzchniowy i szybki podpowierzchniowy). Wysokość
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
- **retencja rzeczywista** $F$ [mm] (ang. *actual retention*): woda zatrzymana po rozpoczęciu odpływu, czyli opad minus
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
  stosowalności uwagą `outside_applicability`; o małym odpływie nie ostrzega.
- Duży odpływ podpowierzchniowy i wysoki poziom wód gruntowych (często gleby grupy A i lasy)
  wymagają osądu projektanta (TR-55, s. 2-11).

## 3.3. Retencja potencjalna i liczba CN

Liczba CN to retencja potencjalna przeniesiona na bezwymiarową skalę: im większa liczba CN, tym
mniejsza retencja; największa liczba CN oznacza powierzchnię, która nie zatrzymuje nic, a cały
opad z niej odpływa. Związek retencji z CN pochodzi z NEH 630 w calach; Hydrolog liczy w
milimetrach przez dokładne przeliczenie cala.

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

<a id="spec-scs_cn_runoff"></a>

> **Odpływ bezpośredni z opadu według metody SCS-CN** · specyfikacja [`scs_cn_runoff`](../FORMULAS.md#scs_cn_runoff) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q(P) = \begin{cases} \dfrac{(P - I_a)^2}{P - I_a + S} & P > I_a \\ 0 & P \le I_a \end{cases},\quad I_a = \lambda S,\quad q_i = Q(P_i) - Q(P_{i-1}),\quad C = \frac{Q}{P}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\Delta P_i$ | `precipitation_mm` (ciąg) | Wysokość opadu w każdym kroku czasowym (suma to jeden krok) | mm | [0; ∞) | nie podano w źródłach | [0; 350] (źr. 4) |
> | $CN$ | `cn` | Liczba CN dla warunków wilgotnościowych poprzedzających przyjętych we wzorze | – | [1; 100] | [40; 100] (źr. 5) | [30; 98] (źr. 6) |
> | $\lambda$ | `ia_coefficient` | Współczynnik strat początkowych Ia / S | – | (0; 1] | nie podano w źródłach | [0,05; 0,2] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q$ | `total_effective_mm` | Odpływ bezpośredni z całego opadu | mm | [0; ∞) |
> | $q_i$ | `effective_mm` (ciąg) | Odpływ bezpośredni w każdym kroku | mm | [0; ∞) |
> | $C$ | `runoff_coefficient` | Stosunek odpływu bezpośredniego do opadu | – | [0; 1] |
> | $S$ | `retention_mm` | Retencja maksymalna S | mm | [0; ∞) |
> | $I_a$ | `initial_abstraction_mm` | Straty początkowe Ia | mm | [0; ∞) |
>
> **Konwencje**
>
> - jednostki SI: wysokości w mm
> - równanie stosuje się do sumy narastającej opadu, a odpływ w każdym kroku to różnica sum narastających odpływu (NEH 630-10, przykład 10-6; KZGW 2017, wzór 6.2); sumę opadu traktuje się jak opad o jednym kroku
> - Ia = lambda S przy zadanym lambda; S z CN według `scs_cn_retention`
> - CN dla ARC (AMC) II, chyba że przeliczono ją przez `scs_cn_amc`
> - C = Q / P dla całego opadu, 0 przy braku opadu
>
> **Założenia**
>
> - wartości CN z tablic NRCS zakładają lambda = 0,2; inna wartość lambda wymaga CN dopasowanych do niej (NEH 630-10 s. 10-4; Woodward i in. 2003), a polecenie `scs effective` wydaje wtedy uwagę `ia_coefficient_nonstandard`
> - odpływ bezpośredni z jednego opadu, a nie model infiltracji ani symulacja ciągła (NEH 630-10 s. 10-19); nie dla topnienia śniegu ani deszczu na zamarzniętym gruncie (TR-55 s. 2-11)
> - TR-55 (s. 2-11) uznaje metodę za mniej dokładną dla odpływu poniżej 0,5 cala (12,7 mm); wynik poniżej tej granicy nie wywołuje uwagi
>
> **Zgodność z obserwacjami według źródeł:** NEH 630-9 (s. 9-1) wyprowadza liczby CN swoich tablic z rocznych wezbrań małych zlewni rolniczych o powierzchni na ogół poniżej 1 mili kwadratowej i z opadów trwających najwyżej jeden dzień; źródła nie podają żadnej miary błędu równania
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eqs. 10-9 to 10-11, pp. 10-2 to 10-4; example 10-6 and table 10-2, pp. 10-17 to 10-18 (cumulative rainfall of a storm) <https://www.hydrocad.net/neh/630ch10.pdf>
> 2. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), eqs. 2-1 to 2-4, p. 2-1 <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.2, p. 88 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 %
> 5. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), chapter 2, limitations, p. 2-11: when the weighted CN is less than 40, use another procedure <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
> 6. Hydrolog's table of TR-55 curve numbers (cn list), the CN its users take for soil-cover complexes, its least and largest CN, 30 (woods and brush, good, A) and 98 (impervious and water)
> 7. Hydrolog's command scs effective: the ratio 0.2 of the CN tables and 0.05 of Woodward et al. (2003), the two its catalog and GUI name, catalog option ia_coefficient
>
> Funkcja `hydrolog.runoff.scs_cn.runoff_depths`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:scs_cn_runoff -->

**Hietogram.** Aby rozłożyć opad efektywny w czasie, równanie stosuje się do **sumy narastającej**
opadu po każdym kroku, a opad efektywny kroku to różnica kolejnych wartości (NEH 630, rozdz. 10,
przykład 10-6; KZGW 2017, wzór 6.2). Tak liczy Hydrolog. Stosowanie równania osobno do opadu
każdego kroku jest błędem: straty początkowe odejmowałoby się wtedy w każdym kroku od nowa.

**Interpretacja wyniku.** Opad efektywny to wysokość warstwy odpływu nad całą zlewnią; objętość
fali to opad efektywny razy powierzchnia zlewni. Stosunek opadu efektywnego do opadu to
**współczynnik odpływu** zdarzenia $C$ (ang. *runoff coefficient*). Odpływ nie jest proporcjonalny ani do CN, ani do opadu
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

<a id="spec-tr55_cn"></a>

> **Liczba CN kompleksu glebowo-roślinnego z tablic TR-55** · specyfikacja [`tr55_cn`](../FORMULAS.md#tr55_cn) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> CN = T(\text{pokrycie terenu}, \text{stan hydrologiczny}, \text{HSG})
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\text{HSG}$ | `hsg` (wybór) | Hydrologiczna grupa gleby | – | jedna z: `A`, `B`, `C`, `D` | – | – |
> | $\text{pokrycie terenu}$ | `land_cover` (wybór) | Klasa pokrycia terenu w Hydrologu | – | jedna z: `fallow`, `row_crops`, `small_grain`, `pasture`, `meadow`, `brush`, `forest`, `herbaceous`, `woods_grass`, `farmstead`, `residential_low`, `residential_medium`, `residential_quarter_acre`, `residential_high`, `commercial`, `industrial`, `open_space`, `paved`, `paved_road_open_ditches`, `gravel`, `dirt`, `water` | – | – |
> | $\text{stan hydrologiczny}$ | `condition` (wybór) | Stan hydrologiczny; brak dla pokrycia o jednym wierszu | – | jedna z: `poor`, `fair`, `good`, `none` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $CN$ | `cn` (liczba całkowita) | Liczba CN dla ARC II i Ia = 0,2 S | – | [1; 100] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | tablica ma wiersz danego pokrycia terenu w danym stanie hydrologicznym | `row_in_table` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - ARC (AMC) II i Ia = 0,2 S (TR-55, tab. 2-2a do 2-2c, przypis 1)
> - `herbaceous` to wiersz „pastwisko, łąka lub wypas ekstensywny” (pasture, grassland or range) z tab. 2-2c, jak każe przypis 1 tab. 2-2d dla wypasu ekstensywnego w regionach wilgotnych; samej tab. 2-2d (pastwiska ekstensywne obszarów suchych i półsuchych) się nie używa
> - uprawy rzędowe i zboża to wiersze „rzędy proste” (straight row) z tab. 2-2b, tylko w stanie złym i dobrym: TR-55 nie ma dla nich stanu średniego
> - woda ma CN 98 (NEH 630-9 s. 9-1), a nie 100 jak w niektórych opracowaniach
>
> **Zgodność z obserwacjami według źródeł:** NEH 630-9 (s. 9-1) wyprowadza CN swoich kompleksów z rocznych wezbrań małych zlewni rolniczych o jednej grupie glebowej i jednym pokryciu; tablica nie podaje żadnej miary błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, p. 2-8 <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
> 2. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 9: Hydrologic Soil-Cover Complexes, p. 9-1: impervious and water surfaces are always assigned a CN of 98 <https://www.hydrocad.net/neh/630ch9.pdf>
>
> Funkcja `hydrolog.runoff.cn_lookup.table_curve_number`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:tr55_cn -->

<!-- spec-table:tr55_cn -->

> **Tablica `src/hydrolog/_data/tables/tr55_cn.csv`** · specyfikacja `tr55_cn` · SHA-256 `781fdd02b39aa868571ec09cb92516716a79c0d74a77640fe810e794cfd3a6e8`
>
> | Pokrycie terenu | Stan hydrologiczny | CN, grupa A | CN, grupa B | CN, grupa C | CN, grupa D | Źródło |
> |---|---|---|---|---|---|---|
> | fallow | – | 77 | 86 | 91 | 94 | TR-55 table 2-2b, p. 2-6 |
> | row_crops | poor | 72 | 81 | 88 | 91 | TR-55 table 2-2b, p. 2-6 |
> | row_crops | good | 67 | 78 | 85 | 89 | TR-55 table 2-2b, p. 2-6 |
> | small_grain | poor | 65 | 76 | 84 | 88 | TR-55 table 2-2b, p. 2-6 |
> | small_grain | good | 63 | 75 | 83 | 87 | TR-55 table 2-2b, p. 2-6 |
> | pasture | poor | 68 | 79 | 86 | 89 | TR-55 table 2-2c, p. 2-7 |
> | pasture | fair | 49 | 69 | 79 | 84 | TR-55 table 2-2c, p. 2-7 |
> | pasture | good | 39 | 61 | 74 | 80 | TR-55 table 2-2c, p. 2-7 |
> | meadow | – | 30 | 58 | 71 | 78 | TR-55 table 2-2c, p. 2-7 |
> | brush | poor | 48 | 67 | 77 | 83 | TR-55 table 2-2c, p. 2-7 |
> | brush | fair | 35 | 56 | 70 | 77 | TR-55 table 2-2c, p. 2-7 |
> | brush | good | 30 | 48 | 65 | 73 | TR-55 table 2-2c, p. 2-7 |
> | forest | poor | 45 | 66 | 77 | 83 | TR-55 table 2-2c, p. 2-7 |
> | forest | fair | 36 | 60 | 73 | 79 | TR-55 table 2-2c, p. 2-7 |
> | forest | good | 30 | 55 | 70 | 77 | TR-55 table 2-2c, p. 2-7 |
> | herbaceous | poor | 68 | 79 | 86 | 89 | TR-55 table 2-2c, p. 2-7, pasture, grassland or range (table 2-2d, footnote 1: for range in humid regions, use table 2-2c) |
> | herbaceous | fair | 49 | 69 | 79 | 84 | TR-55 table 2-2c, p. 2-7, pasture, grassland or range (table 2-2d, footnote 1: for range in humid regions, use table 2-2c) |
> | herbaceous | good | 39 | 61 | 74 | 80 | TR-55 table 2-2c, p. 2-7, pasture, grassland or range (table 2-2d, footnote 1: for range in humid regions, use table 2-2c) |
> | woods_grass | poor | 57 | 73 | 82 | 86 | TR-55 table 2-2c, p. 2-7 |
> | woods_grass | fair | 43 | 65 | 76 | 82 | TR-55 table 2-2c, p. 2-7 |
> | woods_grass | good | 32 | 58 | 72 | 79 | TR-55 table 2-2c, p. 2-7 |
> | farmstead | – | 59 | 74 | 82 | 86 | TR-55 table 2-2c, p. 2-7 |
> | residential_low | – | 46 | 65 | 77 | 82 | TR-55 table 2-2a, p. 2-5 |
> | residential_medium | – | 57 | 72 | 81 | 86 | TR-55 table 2-2a, p. 2-5 |
> | residential_quarter_acre | – | 61 | 75 | 83 | 87 | TR-55 table 2-2a, p. 2-5 |
> | residential_high | – | 77 | 85 | 90 | 92 | TR-55 table 2-2a, p. 2-5 |
> | commercial | – | 89 | 92 | 94 | 95 | TR-55 table 2-2a, p. 2-5 |
> | industrial | – | 81 | 88 | 91 | 93 | TR-55 table 2-2a, p. 2-5 |
> | open_space | poor | 68 | 79 | 86 | 89 | TR-55 table 2-2a, p. 2-5 |
> | open_space | fair | 49 | 69 | 79 | 84 | TR-55 table 2-2a, p. 2-5 |
> | open_space | good | 39 | 61 | 74 | 80 | TR-55 table 2-2a, p. 2-5 |
> | paved | – | 98 | 98 | 98 | 98 | TR-55 table 2-2a, p. 2-5 |
> | paved_road_open_ditches | – | 83 | 89 | 92 | 93 | TR-55 table 2-2a, p. 2-5 |
> | gravel | – | 76 | 85 | 89 | 91 | TR-55 table 2-2a, p. 2-5 |
> | dirt | – | 72 | 82 | 87 | 89 | TR-55 table 2-2a, p. 2-5 |
> | water | – | 98 | 98 | 98 | 98 | NEH 630 ch. 9, p. 9-1: impervious and water surfaces are always assigned a CN of 98 |
>
> Źródło (w brzmieniu specyfikacji): USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, p. 2-8 <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>. Dwie niezależne transkrypcje porównano: tests/oracles/tr55_cn_text_layer.csv (transcribed from the PDF's text layer by tests/oracles/transcribe_tr55_cn.py) against tests/oracles/tr55_cn_hydrolog_0_8_1.csv (typed for Hydrolog 0.8.1), compared by tests/unit/test_formulas_cn_table.py
>
> Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-weighted_cn"></a>

> **Liczba CN ważona powierzchnią** · wzór grupy B `weighted_cn` (Tier B, CMP-2.2)
>
> **Definicja:** CN_w = sum(A_j CN_j) / sum(A_j), średnia ważona powierzchnią liczb CN części zlewni (źr. 1)
>
> **Konwencja:** powierzchnie lub udziały w dowolnej, ale jednej jednostce; część o zerowej powierzchni nie wnosi nic
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) <https://www.hydrocad.net/neh/630ch10.pdf>
>
> Funkcja `hydrolog.runoff.cn_lookup.calculate_weighted_cn`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:weighted_cn -->

Szczególnym przypadkiem jest teren zabudowany o znanym udziale powierzchni nieprzepuszczalnych
połączonych z odwodnieniem (NEH 630, rozdz. 9, wzór 9-1): to ta sama średnia ważona dwóch części,
przepuszczalnej i nieprzepuszczalnej, z CN powierzchni nieprzepuszczalnych z tablicy.

Równanie odpływu jest nieliniowe, więc odpływ obliczony z CN ważonego nie jest równy średniej
ważonej odpływów obliczonych osobno dla każdego kompleksu. Ten drugi sposób, **ważony odpływ** (ang. *weighted runoff*),
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
grupy C zamiast B. Przypisanie grupy glebom (podrozdział 3.8) jest więc w metodzie SCS-CN równie
ważne jak mapa pokrycia terenu.

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

<a id="spec-scs_cn_amc"></a>

> **Liczba CN dla warunków wilgotnościowych poprzedzających I lub III (Hawkins i in. 1985)** · specyfikacja [`scs_cn_amc`](../FORMULAS.md#scs_cn_amc) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> CN_x = \operatorname{round}\frac{CN}{k_x + (1 - k_x)\,CN/100},\quad k_{I} = 2{,}281,\ k_{III} = 0{,}427
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $CN$ | `cn` | Liczba CN dla warunków wilgotnościowych poprzedzających przyjętych we wzorze | – | [1; 100] | [55; 95] (źr. 3) | [51,8; 81,4] (źr. 4) |
> | $ARC$ | `amc` (wybór) | Warunki wilgotnościowe poprzedzające, na które przelicza się CN: I suche, III wilgotne | – | jedna z: `I`, `III` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $CN_x$ | `cn_adjusted` (liczba całkowita) | Liczba CN dla tych warunków | – | [1; 100] |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $k_{I}$ | `ratio_i` | Stosunek retencji maksymalnej w warunkach I do retencji w warunkach II | 2,281 | – | (źr. 5) |
> | $k_{III}$ | `ratio_iii` | Stosunek retencji maksymalnej w warunkach III do retencji w warunkach II | 0,427 | – | (źr. 6) |
> | $100$ | `cn_scale` | Liczba CN przy zerowej retencji maksymalnej | 100 | – | (źr. 7) |
>
> **Konwencje**
>
> - dopasowanie Hawkinsa i in. (1985) do krzywych NRCS, a nie sama tab. 10-1 NEH 630-10 (NEH 630-10 s. 10-6; podaje tę tablicę) ani wzory 5.5.7-5.5.8 Chowa i in. (1988), będące innym dopasowaniem
> - zaokrąglana do najbliższej liczby całkowitej, tak jak drukuje je tab. 10-1, połowa do liczby parzystej; co najmniej 1
> - dla ARC II CN pozostaje taka, jak podano: bez wzoru
>
> **Założenia**
>
> - NEH 630-10 (s. 10-5, 10-7) nie stwierdził związku między opadem z pięciu poprzedzających dni a CN: warunki wybiera inżynier
>
> **Zgodność z obserwacjami według źródeł:** Ponce i Hawkins (1996, s. 15) podają dopasowania S_I = 2,281 S_II (r2 0,999, błąd standardowy 0,206 cala) i S_III = 0,427 S_II (r2 0,994, 0,088 cala) do tab. 10-1 NEH oraz błędy standardowe 1,0 CN (wzór 15) i 0,7 CN (wzór 16); względem tej tablicy przy CN od 55 do 95 zaokrąglone przeliczenie różni się najwyżej o 2 CN dla ARC I i o 1 CN dla ARC III (bez zaokrąglenia najwyżej 2,45 CN dla ARC I przy CN 92 i 1,19 CN dla ARC III przy CN 79)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eqs. 13-16, p. 15 (S_I = 2.281 S_II, S_III = 0.427 S_II) <https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf>
> 2. Banasik, K., Rutkowska, A. and Kohnová, S. (2014). Retention and curve number variability in a small agricultural catchment: the probabilistic approach. Water 6(5), 1118-1133, doi:10.3390/w6051118, eqs. 12-13, p. 1124 (eq. 12 misprints 0.01381 for 0.01281) <https://mdpi-res.com/d_attachment/water/water-06-01118/article_deploy/water-06-01118.pdf>
> 3. Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, p. 15: eqs. 15-16 applicable in the range 55 <= CN <= 95 <https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf>
> 4. Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the 223 catchments of the Hydroni run h07 (2,941 km2), Consequences: CN of AMC II 51.8 to 81.4, median 70.8 <https://github.com/Daldek/Hydrograf/blob/develop/docs/decisions/0075-cn-of-soil-cover-complexes.md>
> 5. Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eq. 13, p. 15 (r2 = 0.999); Banasik et al. (2014) eq. 12 <https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf>
> 6. Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eq. 14, p. 15 (r2 = 0.994); Banasik et al. (2014) eq. 13 <https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf>
> 7. USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-11, p. 10-4: CN = 1000/(10 + S), 100 at S = 0 <https://www.hydrocad.net/neh/630ch10.pdf>
>
> Funkcja `hydrolog.runoff.scs_cn.amc_curve_number`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
(Hydrolog ostrzega uwagą `outside_applicability`); przeliczanie CN poszczególnych kompleksów i
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

Ten sam opad o prawdopodobieństwie przewyższenia 1 % daje po suchym okresie 4,5 mm odpływu, a po
mokrym 54,1 mm: dwanaście razy więcej. W przykładach tego rozdziału warunki wilgotnościowe
zmieniają wynik bardziej niż jakikolwiek inny wybór, a nie wynikają z żadnego wzoru; przyjęte
warunki trzeba zawsze podać razem z wynikiem.

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

<a id="spec-usda_texture"></a>

> **Klasa uziarnienia gleby USDA według zawartości iłu, piasku i pyłu** · specyfikacja [`usda_texture`](../FORMULAS.md#usda_texture) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{class} = C \iff \exists j\ \forall (a, b, c, \sim, k) \in T_{C,j}:\ 100\,(a\,m_\mathrm{clay} + b\,m_\mathrm{sand} + c\,m_\mathrm{silt}) \sim k\,(m_\mathrm{clay} + m_\mathrm{sand} + m_\mathrm{silt})
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $m_\mathrm{clay}$ | `clay` | Zawartość iłu (< 0,002 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [0; ∞) | nie podano w źródłach | [0; 1000] (źr. 2) |
> | $m_\mathrm{sand}$ | `sand` | Zawartość piasku (0,05 do 2 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [0; ∞) | nie podano w źródłach | [0; 1000] (źr. 2) |
> | $m_\mathrm{silt}$ | `silt` | Zawartość pyłu (0,002 do 0,05 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [0; ∞) | nie podano w źródłach | [0; 1000] (źr. 2) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{class}$ | `texture_class` (wybór) | Klasa uziarnienia USDA, jedna z dwunastu klas Soil Survey Manual | – | jedna z: `sand`, `loamy_sand`, `sandy_loam`, `loam`, `silt_loam`, `silt`, `sandy_clay_loam`, `clay_loam`, `silty_clay_loam`, `sandy_clay`, `silty_clay`, `clay` |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | clay + sand + silt > 0 | `positive_total` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Konwencje**
>
> - zawartości w dowolnej jednostce wspólnej dla trzech frakcji (procent, g/kg), odnoszone do ich sumy: klasa zależy tylko od udziałów w sumie ił + piasek + pył, która nie musi wynosić 100 % (materia organiczna i żwir leżą poza częściami ziemistymi)
> - frakcje USDA: piasek 0,05 do 2 mm, pył 0,002 do 0,05 mm, ił poniżej 0,002 mm (polska klasyfikacja PTG 2008 przyjmuje te same granice); dwanaście klas pokrywa każdy skład w trójkącie, więc żadna zawartość nie ma zakresu stosowalności (niepodany)
> - „od X do mniej niż Y procent” to X <= udział < Y, „więcej niż X” to > X, „X lub więcej” to >= X, „X lub mniej” to <= X, „więcej niż 20 do 45 procent piasku” (glina ilasta) to 20 < sand <= 45, zgodnie z brzmieniem opisu każdej klasy w Soil Survey Manual
> - zakresy piasku, które Soil Survey Manual podaje także słownie — piaski „więcej niż 85 procent piasku” i piaski gliniaste „od 70 do 90 procent piasku” — wynikają z pozostałych nierówności tych klas (silt + 1,5 clay < 15 daje sand > 85; silt + 1,5 clay >= 15 oraz silt + 2 clay < 30 dają 70 < sand <= 90) i nie są wierszami tabeli
> - obliczenia w całości we float64, po wcześniejszym przeskalowaniu zawartości przez jedną potęgę dwójki; wynik dokładny dla zawartości całkowitych (suma poniżej 10**13); inne zawartości odległe od granicy klasy o kilka jednostek na ostatnim miejscu mogą trafić po dowolnej jej stronie, a gdy zaokrąglenie dopuszcza dwie klasy, przyjmowana jest pierwsza w kolejności tabeli
> - zerowa suma nie ma uziarnienia i jest odrzucana (warunek wstępny `positive_total`); wariant tablicowy przypisuje jej glinę jako brak danych (wzór Tier B `usda_texture_codes`)
>
> **Założenia**
>
> - zawartości dotyczą części ziemistych (< 2 mm) gleby mineralnej; podklasy Soil Survey Manual według wielkości ziaren piasku (piasek gruboziarnisty, glina piaszczysta drobnoziarnista, ...) nie są wyznaczane
>
> **Zgodność z obserwacjami według źródeł:** brak: klasy są zdefiniowane w podręczniku Soil Survey Manual, a nie dopasowane do obserwacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 <https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/GOVPUB-A-PURL-gpo113168.pdf>
> 2. ISRIC - World Soil Information (2026). SoilGrids FAQ, 'Which soil properties are predicted': clay, sand and silt of the fine earth in g/kg, the data Kartograf downloads for Hydrolog's soil hsg: integers 0 to 1000 g/kg; soil texture takes percent (0 to 100) or g/kg <https://www.isric.org/explore/soilgrids/faq-soilgrids>
>
> Funkcja `hydrolog.soil.texture.classify_usda_texture`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:usda_texture -->

<!-- spec-table:usda_texture -->

> **Tablica `src/hydrolog/_data/tables/usda_texture_classes.csv`** · specyfikacja `usda_texture` · SHA-256 `b957a339f36ec7c0ee82ec1f25e286e401f26afeffa85dcccca24f9a4e61c381`
>
> | Klasa uziarnienia (USDA) | Wariant | Mnożnik iłu | Mnożnik piasku | Mnożnik pyłu | Relacja | Próg [%] | Strona | Brzmienie w źródle (ang.) |
> |---|---|---|---|---|---|---|---|---|
> | sand | 1 | 1,5 | 0 | 1 | < | 15 | 122 | the percentage of silt plus 1.5 times the percentage of clay is less than 15 |
> | loamy_sand | 1 | 1,5 | 0 | 1 | >= | 15 | 122 | the percentage of silt plus 1.5 times the percentage of clay is 15 or more |
> | loamy_sand | 1 | 2 | 0 | 1 | < | 30 | 122 | the percentage of silt plus twice the percentage of clay is less than 30 |
> | sandy_loam | 1 | 1 | 0 | 0 | >= | 7 | 123 | 7 to less than 20 percent clay |
> | sandy_loam | 1 | 1 | 0 | 0 | < | 20 | 123 | 7 to less than 20 percent clay |
> | sandy_loam | 1 | 0 | 1 | 0 | > | 52 | 123 | more than 52 percent sand |
> | sandy_loam | 1 | 2 | 0 | 1 | >= | 30 | 123 | the percentage of silt plus twice the percentage of clay is 30 or more |
> | sandy_loam | 2 | 1 | 0 | 0 | < | 7 | 123 | less than 7 percent clay |
> | sandy_loam | 2 | 0 | 0 | 1 | < | 50 | 123 | less than 50 percent silt |
> | sandy_loam | 2 | 2 | 0 | 1 | >= | 30 | 123 | the percentage of silt plus twice the percentage of clay is 30 or more |
> | loam | 1 | 1 | 0 | 0 | >= | 7 | 124 | 7 to less than 27 percent clay |
> | loam | 1 | 1 | 0 | 0 | < | 27 | 124 | 7 to less than 27 percent clay |
> | loam | 1 | 0 | 0 | 1 | >= | 28 | 124 | 28 to less than 50 percent silt |
> | loam | 1 | 0 | 0 | 1 | < | 50 | 124 | 28 to less than 50 percent silt |
> | loam | 1 | 0 | 1 | 0 | <= | 52 | 124 | 52 percent or less sand |
> | silt_loam | 1 | 0 | 0 | 1 | >= | 50 | 124 | 50 percent or more silt |
> | silt_loam | 1 | 1 | 0 | 0 | >= | 12 | 124 | 12 to less than 27 percent clay |
> | silt_loam | 1 | 1 | 0 | 0 | < | 27 | 124 | 12 to less than 27 percent clay |
> | silt_loam | 2 | 0 | 0 | 1 | >= | 50 | 124 | 50 to less than 80 percent silt |
> | silt_loam | 2 | 0 | 0 | 1 | < | 80 | 124 | 50 to less than 80 percent silt |
> | silt_loam | 2 | 1 | 0 | 0 | < | 12 | 124 | less than 12 percent clay |
> | silt | 1 | 0 | 0 | 1 | >= | 80 | 124 | 80 percent or more silt |
> | silt | 1 | 1 | 0 | 0 | < | 12 | 124 | less than 12 percent clay |
> | sandy_clay_loam | 1 | 1 | 0 | 0 | >= | 20 | 124 | 20 to less than 35 percent clay |
> | sandy_clay_loam | 1 | 1 | 0 | 0 | < | 35 | 124 | 20 to less than 35 percent clay |
> | sandy_clay_loam | 1 | 0 | 0 | 1 | < | 28 | 124 | less than 28 percent silt |
> | sandy_clay_loam | 1 | 0 | 1 | 0 | > | 45 | 124 | more than 45 percent sand |
> | clay_loam | 1 | 1 | 0 | 0 | >= | 27 | 124 | 27 to less than 40 percent clay |
> | clay_loam | 1 | 1 | 0 | 0 | < | 40 | 124 | 27 to less than 40 percent clay |
> | clay_loam | 1 | 0 | 1 | 0 | > | 20 | 124 | more than 20 to 45 percent sand |
> | clay_loam | 1 | 0 | 1 | 0 | <= | 45 | 124 | more than 20 to 45 percent sand |
> | silty_clay_loam | 1 | 1 | 0 | 0 | >= | 27 | 124 | 27 to less than 40 percent clay |
> | silty_clay_loam | 1 | 1 | 0 | 0 | < | 40 | 124 | 27 to less than 40 percent clay |
> | silty_clay_loam | 1 | 0 | 1 | 0 | <= | 20 | 124 | 20 percent or less sand |
> | sandy_clay | 1 | 1 | 0 | 0 | >= | 35 | 124 | 35 percent or more clay |
> | sandy_clay | 1 | 0 | 1 | 0 | > | 45 | 124 | more than 45 percent sand |
> | silty_clay | 1 | 1 | 0 | 0 | >= | 40 | 124 | 40 percent or more clay |
> | silty_clay | 1 | 0 | 0 | 1 | >= | 40 | 124 | 40 percent or more silt |
> | clay | 1 | 1 | 0 | 0 | >= | 40 | 124 | 40 percent or more clay |
> | clay | 1 | 0 | 1 | 0 | <= | 45 | 124 | 45 percent or less sand |
> | clay | 1 | 0 | 0 | 1 | < | 40 | 124 | less than 40 percent silt |
>
> Źródło (w brzmieniu specyfikacji): Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 <https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/GOVPUB-A-PURL-gpo113168.pdf>. Dwie niezależne transkrypcje porównano: tests/oracles/usda_texture_classes_first.csv (typed from the Manual's text by the author of the spec) against tests/oracles/usda_texture_classes_second.csv (typed independently by a second agent from the same pages), compared with the data file by tests/unit/test_formulas_texture.py
>
> Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec-table:usda_texture -->

Klasa zależy tylko od udziałów frakcji w ich sumie: zawartości można podać w procentach albo w
g/kg (jak w SoilGrids), a trzy zawartości nie muszą składać się na całą próbkę, bo materia
organiczna i szkielet leżą poza częściami ziemistymi. Trzy zera nie są glebą i Hydrolog je
odrzuca.

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

<a id="spec-texture_hsg"></a>

> **Grupa hydrologiczna gleby według klasy uziarnienia USDA** · specyfikacja [`texture_hsg`](../FORMULAS.md#texture_hsg) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{HSG} = G(\mathrm{class})
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\mathrm{class}$ | `texture_class` (wybór) | Klasa uziarnienia USDA (specyfikacja `usda_texture`) | – | jedna z: `sand`, `loamy_sand`, `sandy_loam`, `loam`, `silt_loam`, `silt`, `sandy_clay_loam`, `clay_loam`, `silty_clay_loam`, `sandy_clay`, `silty_clay`, `clay` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{HSG}$ | `hsg` (wybór) | Grupa hydrologiczna gleby, od A (mały potencjał odpływu) do D (duży) | – | jedna z: `A`, `B`, `C`, `D` |
>
> **Konwencje**
>
> - załącznik A TR-55 podaje grupy dla przekształconych profili glebowych (tereny zurbanizowane, bez istotnego zagęszczenia); tabela stosuje je do wszystkich gleb
> - udokumentowane odstępstwa od załącznika A TR-55: glina piaszczysta B (w TR-55 A), glina ilasta i glina pylasto-ilasta C (w TR-55 D), ponieważ NEH 630 rozdz. 7 s. 7-2 wymienia typowe uziarnienia grup B i C (Kartograf ADR-025, decyzja b): surowiej niż TR-55 dla gliny piaszczystej, łagodniej dla obu glin ilastych
> - pył, którego TR-55 nie wymienia, otrzymuje grupę pyłu gliniastego, B; NEH 630 rozdz. 7 s. 7-2 zalicza dobrze zagregowany pył do grupy B
> - według NEH 630 rozdz. 7 glina i pył gliniasty (a ze względu na Ksat także pył) należałyby do grupy C, a piasek gliniasty do B; tabela zachowuje dla nich grupy TR-55 (otwarta kwestia ADR-0066)
>
> **Założenia**
>
> - grupa wynika z samego uziarnienia: bez uwzględnienia zwierciadła wody gruntowej, warstwy nieprzepuszczalnej, odłamków skalnych, gęstości objętościowej ani struktury gleby (NEH 630 rozdz. 7, tab. 7-1)
>
> **Zgodność z obserwacjami według źródeł:** brak (źródła jej nie podają): TR-55 wyprowadza grupy dla klas uziarnienia z pracy Brakensieka i Rawlsa (1983) dla profili przekształconych; NEH 630 rozdz. 7 podaje typowe uziarnienia, a nie dopasowanie
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
> 2. USDA-NRCS (2009). National Engineering Handbook, Part 630 Hydrology, Chapter 7: Hydrologic Soil Groups (210-VI-NEH, January 2009), p. 7-2: the textures groups A to D 'typically' have; group B 'loamy sand or sandy loam', group C 'loam, silt loam, sandy clay loam, clay loam, and silty clay loam', well aggregated silt may be B <https://www.hydrocad.net/neh/630ch7.pdf>
>
> Funkcja `hydrolog.soil.texture.texture_to_hsg`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:texture_hsg -->

<!-- spec-table:texture_hsg -->

> **Tablica `src/hydrolog/_data/tables/texture_hsg.csv`** · specyfikacja `texture_hsg` · SHA-256 `f8e1d4b427ae6bb4c0abf7afbbbf9a70f3c32c42de0b5fe5a0ee2157daebef4a`
>
> | Klasa uziarnienia (USDA) | Grupa HSG | Źródło |
> |---|---|---|
> | sand | A | TR-55 (1986) appendix A, p. A-1 |
> | loamy_sand | A | TR-55 (1986) appendix A, p. A-1 |
> | sandy_loam | B | NEH 630 ch. 7 (2009), p. 7-2: group B typically loamy sand or sandy loam (TR-55: A) |
> | loam | B | TR-55 (1986) appendix A, p. A-1 |
> | silt_loam | B | TR-55 (1986) appendix A, p. A-1 |
> | silt | B | the group of silt loam (TR-55 has no silt; NEH 630 ch. 7, p. 7-2, puts well aggregated silt in B) |
> | sandy_clay_loam | C | TR-55 (1986) appendix A, p. A-1 |
> | clay_loam | C | NEH 630 ch. 7 (2009), p. 7-2: group C typically clay loam (TR-55: D) |
> | silty_clay_loam | C | NEH 630 ch. 7 (2009), p. 7-2: group C typically silty clay loam (TR-55: D) |
> | sandy_clay | D | TR-55 (1986) appendix A, p. A-1 |
> | silty_clay | D | TR-55 (1986) appendix A, p. A-1 |
> | clay | D | TR-55 (1986) appendix A, p. A-1 |
>
> Źródło (w brzmieniu specyfikacji): USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>. Dwie niezależne transkrypcje porównano: tests/oracles/tr55_hsg_text_layer.csv (read from the PDF's text layer by tests/oracles/transcribe_tr55_hsg.py) and tests/oracles/kartograf_0_8_2_texture_hsg.csv (Kartograf 0.8.2's table), compared with the data file by tests/unit/test_formulas_texture_hsg.py
>
> Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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

<a id="spec-hsg_of_amounts"></a>

> **Grupa hydrologiczna gleby z zawartości iłu, piasku i pyłu** · wzór grupy B `hsg_of_amounts` (Tier B, CMP-2.2)
>
> **Definicja:** grupa ze specyfikacji `texture_hsg` dla klasy ze specyfikacji `usda_texture`, komórka po komórce, w postaci kodu rastra 1-4 dla A-D (źr. 1)
>
> **Konwencja:** 0 (brak danych) dla komórki z wartością NaN lub z nieskończoną zawartością, z zawartością równą znacznikowi nodata jej danych wejściowych albo ze wszystkimi trzema zawartościami równymi zeru (luka w SoilGrids); ujemna zawartość w komórce z danymi jest odrzucana
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Kartograf ADR-025 (HSG from SoilGrids clay, sand and silt), ported to Hydrolog 0.8.0, raster codes uint8, 0 no data, 1-4 the groups A-D
>
> Funkcja `hydrolog.soil.hsg.classify_hsg`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hsg_of_amounts -->

<!-- spec:usda_texture_codes -->

<a id="spec-usda_texture_codes"></a>

> **Kody klas uziarnienia USDA w rastrze** · wzór grupy B `usda_texture_codes` (Tier B, CMP-2.2)
>
> **Definicja:** klasa ze specyfikacji `usda_texture`, komórka po komórce, w postaci jej kodu 1-12 (`TEXTURE_CLASSES`) (źr. 1)
>
> **Konwencja:** komórka bez danych glebowych — o zerowej sumie, z wartością NaN lub z nieskończoną zawartością — otrzymuje kod gliny (4) jako wartość zastępczą, którą `classify_hsg` maskuje jako brak danych; ujemna zawartość jest odrzucana
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 <https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/GOVPUB-A-PURL-gpo113168.pdf>
>
> Funkcja `hydrolog.soil.texture.classify_usda_texture_array`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:usda_texture_codes -->

<!-- spec:texture_hsg_codes -->

<a id="spec-texture_hsg_codes"></a>

> **Kody grup hydrologicznych gleby z kodów klas uziarnienia** · wzór grupy B `texture_hsg_codes` (Tier B, CMP-2.2)
>
> **Definicja:** grupa ze specyfikacji `texture_hsg` dla każdego kodu uziarnienia, w postaci kodu rastra 1-4 dla A-D (źr. 1)
>
> **Konwencja:** kod uziarnienia 0 (brak danych) daje 0; kod spoza zakresu 0-12 jest odrzucany
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
>
> Funkcja `hydrolog.soil.texture.texture_to_hsg_array`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

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
