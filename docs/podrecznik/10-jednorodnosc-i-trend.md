# 10. Jednorodność i trend

Analiza częstości przepływów maksymalnych (rozdział 7) zakłada, że maksima roczne pochodzą z jednego, niezmiennego
rozkładu prawdopodobieństwa: szereg jest jednorodny (*homogeneous*) i stacjonarny (*stationary*). Założenie to łamią
zmiany klimatu i użytkowania zlewni, budowa zbiornika, regulacja koryta, a także zmiany samego wodowskazu i krzywej
natężenia przepływu (p. 9.7). Dlatego metodyka KZGW (2017, s. 7–11) wymaga sprawdzenia jednorodności szeregu przed
obliczeniem przepływów o zadanym prawdopodobieństwie przewyższenia.

Rozdział opisuje testy, którymi Hydrolog bada szereg wartości rocznych: test Manna–Kendalla (trend monotoniczny) z
nachyleniem Sena (wielkość zmiany), testy dwóch prób Manna–Whitneya i Kołmogorowa–Smirnowa (różnica między częściami
szeregu) oraz test Pettitta (punkt zmiany). Zaczyna od tego, jak czytać wynik każdego testu statystycznego.

## Dane przykładów

- Średnie roczne temperatury i sumy roczne opadu stacji Warszawa-Okęcie z lat 1991–2020, policzone przez Hydrolog
  z pliku testowego `tests/fixtures/warszawa_okecie_1991_2020.csv.gz` (rozpakowanie pliku: rozdział 9).
- Maksima roczne Bobru w Bukówce z lat 1965–2005, wydrukowane w metodyce KZGW (2017, tab. 1.1) jako przykład testu
  Manna–Kendalla.
- Maksima roczne przepływów dobowych Nysy Kłodzkiej w Kłodzku z lat hydrologicznych 1951–2025, wybierane przez
  Hydrolog z szeregu dobowego `docs/podrecznik/dane/klodzko_1951_2025.csv.gz` (rozdział 9; brak roku 1997).

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy. Dane
Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone. Regulamin danych
IMGW-PIB: https://danepubliczne.imgw.pl/regulations

## 10.1. Jak czytać wynik testu statystycznego

Test statystyczny (*hypothesis test*) sprawdza, czy dane są zgodne z hipotezą zerową $H_0$ (*null hypothesis*): w tym
rozdziale – „szereg nie ma trendu” albo „obie części szeregu pochodzą z tego samego rozkładu”. Z danych liczy się
statystykę testową, a z jej rozkładu przy prawdziwej $H_0$ – poziom krytyczny $p$ (*p-value*).

- **$p$** to prawdopodobieństwo otrzymania statystyki co najmniej tak skrajnej jak obliczona, gdyby $H_0$ była
  prawdziwa (Helsel i in. 2020, rozdz. 4). Nie jest to prawdopodobieństwo, że $H_0$ jest prawdziwa.
- **Poziom istotności $\alpha$** (*significance level*) to ryzyko błędnego odrzucenia prawdziwej $H_0$ (błąd pierwszego
  rodzaju), które godzimy się ponieść. Wybiera się go przed obliczeniami; najczęściej $\alpha = 0{,}05$, jak w metodyce
  KZGW (2017). Hipotezę odrzuca się, gdy $p < \alpha$.
- **Brak podstaw do odrzucenia $H_0$ nie dowodzi, że $H_0$ jest prawdziwa.** Test może nie wykryć istniejącej zmiany
  (błąd drugiego rodzaju), zwłaszcza w krótkim szeregu albo przy małej zmianie: moc testu (*power*) rośnie z liczbą
  lat. Słowo „jednorodny” w wyniku Hydrologa znaczy tylko, że test nie wykrył różnicy (ADR-0022).
- **$p$ nie mówi, jak duża jest zmiana.** Przy długim szeregu nawet mała, praktycznie bez znaczenia zmiana daje małe
  $p$. Dlatego obok testu Manna–Kendalla Hydrolog podaje nachylenie Sena z przedziałem ufności.
- **Raportuj liczbę wartości, hipotezy, $\alpha$ i samo $p$**, a nie tylko „$p < 0{,}05$”, żeby czytelnik mógł ocenić
  wynik przy innym poziomie istotności (Helsel i in. 2020, rozdz. 4.6).

Wszystkie testy tego rozdziału zakładają, że wartości są **niezależne**. Kolejne przepływy dobowe czy miesięczne są
silnie skorelowane, więc testy stosuje się do wartości rocznych (maksimów, minimów, średnich). Gdy i wartości roczne
są skorelowane (np. średnie roczne przepływy dużych rzek), test zbyt często wykrywa trend, którego nie ma; stosuje się
wtedy testy zmodyfikowane (Hamed i Rao 1998; Yue i Wang 2004), których Hydrolog nie oferuje. Trzeba też pamiętać o
wielokrotnym testowaniu: przy wielu stacjach albo wielu testach część odrzuceń wypada przypadkiem, średnio w odsetku
równym $\alpha$.

## 10.2. Test Manna–Kendalla

**Idea.** Test Manna–Kendalla (*Mann–Kendall test*) porównuje każdą parę wartości szeregu: liczy, ile razy wartość
późniejsza jest większa od wcześniejszej, a ile razy mniejsza. Statystyka $S$ to różnica tych liczb: duża dodatnia przy
trendzie rosnącym, duża ujemna przy malejącym, bliska zera bez trendu (Mann 1945; Kendall 1975; Hirsch, Slack i Smith
1982; Gilbert 1987). Test jest nieparametryczny: nie zakłada rozkładu normalnego, a ponieważ korzysta tylko ze
znaków różnic, pojedyncza wartość odstająca ma na niego mały wpływ. Wykrywa trend monotoniczny, niekoniecznie
liniowy.

<!-- spec:mann_kendall -->
<!-- /spec:mann_kendall -->

**Konwencje Hydrologa.** Wartości równe (*ties*) to wartości dokładnie równe; szereg policzony w arytmetyce
zmiennoprzecinkowej trzeba najpierw zaokrąglić do dokładności pomiaru, bo 4,7 i 4,6999999 nie są dla testu równe
(sumy opadu Hydrolog zaokrągla sam, ADR-0033). Wariancja $S$ jest pomniejszona o poprawkę na grupy wartości równych,
jak u Gilberta (1987) i w pakiecie R `trend`; metodyka KZGW (2017, s. 11) tej poprawki nie stosuje. Dla krótkiego
szeregu (mniej niż $n_0$ wartości) $p$ pochodzi z dokładnego rozkładu $S$ – wszystkich uporządkowań wartości,
jednakowo prawdopodobnych przy braku trendu – a od $n_0$ wartości z przybliżenia normalnego z poprawką na ciągłość
(Gilbert 1987, rozdz. 16.4; ADR-0049). Pole `p_value_method` mówi, którą drogę wybrano. Decyzję i kierunek trendu
opisuje ramka:

<!-- spec:trend_decision -->
<!-- /spec:trend_decision -->

**Zakres stosowania.** Wartości roczne, niezależne, w kolejności czasowej, po jednej na rok; brakujące lata nie
zmieniają testu (liczy się tylko kolejność), ale z opcją `--years` nachylenie Sena jest liczone na rok, a bez niej –
na krok szeregu. Polskie zastosowania to przede wszystkim szeregi kilkudziesięciu maksimów rocznych przed analizą
częstości (KZGW 2017) oraz trendy wskaźników klimatycznych (rozdział 11).

**Typowe błędy.**

- **Remisy liczone jako −1.** W czterech przykładach metodyki KZGW (2017) wydrukowane $S$ jest mniejsze od poprawnego
  dokładnie o liczbę par wartości równych: arkusz liczył parę równą jako −1, choć wzór (1.2) metodyki daje dla niej 0.
  Wnioski przykładów się nie zmieniają, ale wydrukowanych wartości $S$ nie należy brać za wzorcowe (przykład niżej).
- **Wartości „prawie równe”** z obliczeń zmiennoprzecinkowych (zaokrąglij szereg do dokładności danych).
- **Test wartości dobowych** zamiast rocznych: silna autokorelacja daje fałszywe trendy.
- **Testowanie wielu szeregów i raportowanie tylko istotnych.**

### Przykład 1: temperatura powietrza w Warszawie, 1991–2020

Średnie roczne temperatury daje polecenie

```bash
hydrolog meteo temperature --index means --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

(pole `years[].tmean_c`). Zaokrąglone do 0,01 °C:

| Rok | 1991 | 1992 | 1993 | 1994 | 1995 | 1996 | 1997 | 1998 | 1999 | 2000 |
|---|---|---|---|---|---|---|---|---|---|---|
| $T$ [°C] | 7,96 | 8,76 | 7,76 | 8,84 | 8,21 | 6,83 | 7,85 | 8,18 | 9,04 | 9,63 |
| **Rok** | **2001** | **2002** | **2003** | **2004** | **2005** | **2006** | **2007** | **2008** | **2009** | **2010** |
| $T$ [°C] | 8,32 | 9,31 | 8,26 | 8,41 | 8,58 | 8,95 | 9,63 | 9,79 | 8,83 | 7,95 |
| **Rok** | **2011** | **2012** | **2013** | **2014** | **2015** | **2016** | **2017** | **2018** | **2019** | **2020** |
| $T$ [°C] | 9,13 | 8,79 | 8,91 | 9,83 | 10,33 | 9,78 | 9,39 | 10,43 | 10,89 | 10,51 |

```bash
hydrolog stats mann-kendall --values 7.96,8.76,7.76,8.84,8.21,6.83,7.85,8.18,9.04,9.63,8.32,9.31,8.26,8.41,8.58,8.95,9.63,9.79,8.83,7.95,9.13,8.79,8.91,9.83,10.33,9.78,9.39,10.43,10.89,10.51 --years 1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020
```

Wynik: $S = 248$, $\mathrm{Var}(S) = 3140{,}67$ (jedna para wartości równych: 9,63 °C w latach 2000 i 2007),
$Z = 4{,}407$, $p = 1{,}05\cdot10^{-5}$ (`p_value_method` = `normal`), trend rosnący (`trend_detected`,
`trend_direction` = `increasing`). Nachylenie Sena wynosi 0,0738 °C na rok, czyli około 0,7 °C na dziesięciolecie
(p. 10.3).

### Przykład 2: opad roczny w Warszawie, 1991–2020

Sumy roczne (pole `years[].total_mm`) daje polecenie

```bash
hydrolog meteo precipitation --index sums --input-file tests/fixtures/warszawa_okecie_1991_2020.csv
```

```bash
hydrolog stats mann-kendall --values 487.6,484.3,453.6,652.3,571.4,453.6,588.5,616.7,484.1,523.8,544.8,552.8,534.7,522.8,490.3,478.6,601.5,537,652.2,798.1,604.4,519.3,613.3,555.3,403.5,593.3,705.1,433.4,390.2,645.5 --years 1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020
```

Wynik: $S = 44$, $Z = 0{,}767$, $p = 0{,}443$ – brak podstaw do stwierdzenia trendu. Nachylenie Sena +2,30 mm na rok
z przedziałem 95% od −2,66 do +5,85 mm na rok: przedział obejmuje zero, a także zmiany o kilka milimetrów rocznie w obu
kierunkach. Szereg 30 sum rocznych o tak dużej zmienności z roku na rok nie pozwala ani wykazać trendu, ani go
wykluczyć.

### Przykład 3: Bóbr w Bukówce według metodyki KZGW

Maksima roczne z tab. 1.1 metodyki KZGW (2017) [m³/s]:

| Rok | 1965 | 1966 | 1967 | 1968 | 1969 | 1970 | 1971 | 1972 | 1973 | 1974 | 1975 | 1976 | 1977 | 1978 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $Q$ | 18,6 | 13,2 | 22,1 | 20,4 | 23,0 | 10,7 | 27,8 | 14,7 | 8,62 | 15,9 | 22,1 | 16,6 | 27,8 | 4,76 |
| **Rok** | **1979** | **1980** | **1981** | **1982** | **1983** | **1984** | **1985** | **1986** | **1987** | **1988** | **1989** | **1990** | **1991** | **1992** |
| $Q$ | 11,3 | 32,3 | 32,3 | 33,8 | 21,7 | 9,23 | 14,3 | 8,28 | 10,7 | 9,16 | 10,3 | 6,72 | 4,43 | 6,72 |
| **Rok** | **1993** | **1994** | **1995** | **1996** | **1997** | **1998** | **1999** | **2000** | **2001** | **2002** | **2003** | **2004** | **2005** | |
| $Q$ | 3,08 | 7,26 | 4,70 | 6,05 | 8,75 | 5,24 | 6,59 | 4,70 | 4,16 | 4,97 | 3,25 | 5,92 | 1,90 | |

(W tabeli KZGW wartość z 1995 r. wydrukowano jako „4,7,0”; przyjęto 4,70 – tylko ten odczyt odtwarza zależność między
wydrukowanym a poprawnym $S$ opisaną niżej.)

```bash
hydrolog stats mann-kendall --values 18.6,13.2,22.1,20.4,23,10.7,27.8,14.7,8.62,15.9,22.1,16.6,27.8,4.76,11.3,32.3,32.3,33.8,21.7,9.23,14.3,8.28,10.7,9.16,10.3,6.72,4.43,6.72,3.08,7.26,4.7,6.05,8.75,5.24,6.59,4.7,4.16,4.97,3.25,5.92,1.9 --years 1965,1966,1967,1968,1969,1970,1971,1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005
```

Wynik: $S = -460$, $\mathrm{Var}(S) = 7920{,}67$, $Z = -5{,}157$, $p = 2{,}5\cdot10^{-7}$ – istotny trend malejący. KZGW
drukuje $S = -466$: sześć par wartości równych (np. 22,1 w latach 1967 i 1975) policzono jako −1 zamiast 0. Metodyka
nie stosuje też poprawki wariancji na wartości równe (odchylenie standardowe $S$ 89,03 zamiast 89,00). Wniosek – trend
malejący – jest w obu rachunkach ten sam.

### Przykład 4: krótki szereg i dokładne $p$

Helsel i in. (2020, przykład 10.3) testują siedem wartości:

```bash
hydrolog stats mann-kendall --values 1,2,3,4,5,16,7
```

Wynik: $S = 19$, $p = 0{,}00278$ z rozkładu dokładnego (`p_value_method` = `exact`). Przybliżenie normalne dałoby
$p = 0{,}0069$ (Helsel i in. 2020), dwa i pół razy więcej. Bez lat nachylenie Sena (1,0) jest liczone na krok szeregu,
a jego przedziału przy tak krótkim szeregu Hydrolog nie podaje (pola `sen_slope_lower` i `sen_slope_upper` są puste).

## 10.3. Nachylenie Sena i jego przedział ufności

**Idea.** Test mówi, czy trend jest, a nachylenie Sena (*Sen's slope*, estymator Theila–Sena) – jak szybko wartości się
zmieniają: to mediana nachyleń odcinków łączących wszystkie pary punktów szeregu (Sen 1968; Gilbert 1987, rozdz. 16.5;
Helsel i in. 2020, rozdz. 10.1). Mediana sprawia, że wartości odstające mają na wynik mały wpływ, inaczej niż w
regresji liniowej. Wyraz wolny prostej to wyraz Conovera (Conover 1980), czyli wartość prostej w chwili zerowej.

<!-- spec:sen_slope -->
<!-- /spec:sen_slope -->

Przedział ufności nachylenia wyznacza się z rang uporządkowanych nachyleń, przesuniętych o wielkość zależną od wariancji
$S$ tego samego testu (Gilbert 1987, rozdz. 16.5). Hydrolog interpoluje między rangami, jak w przykładzie 16.5 i
programie Gilberta; pakiet R `trend` zaokrągla rangi, przez co dla krótkich szeregów granice różnią się o kilka
procent. Przedział ma ten sam poziom ufności $1 - \alpha$ co test, a dla szeregu krótszego niż $n_0$ wartości nie jest
podawany, bo opiera się na przybliżeniu normalnym $S$ (ADR-0049).

<!-- spec:sen_interval -->
<!-- /spec:sen_interval -->

**Jak czytać.** Nachylenie ma jednostkę szeregu na rok (z latami) albo na krok szeregu (bez lat). Przedział
obejmujący zero odpowiada zwykle brakowi istotnego trendu przy tym samym $\alpha$. Prostą Sena stosuj tylko w zakresie
lat danych: wyraz wolny to wartość prostej w roku zerowym naszej ery, sama w sobie bez znaczenia.

**Przykłady** (z tych samych wywołań co w p. 10.2):

| Szereg | Nachylenie Sena | Przedział 95% | Wyraz wolny |
|---|---|---|---|
| Warszawa, średnia temperatura roczna 1991–2020 | 0,0738 °C/rok | 0,0498 do 0,1095 °C/rok | −139,03 °C |
| Warszawa, opad roczny 1991–2020 | 2,30 mm/rok | −2,66 do 5,85 mm/rok | −4063 mm |
| Bóbr – Bukówka, maksima roczne 1965–2005 | −0,434 m³/s na rok | −0,553 do −0,298 m³/s na rok | 870,8 m³/s |

Wyrazy wolne pokazują, dlaczego prostej nie należy przedłużać: w roku zerowym temperatura „wynosiłaby” −139 °C.
Wartość prostej dla roku 2020 to $-139{,}0306 + 0{,}07375 \cdot 2020 \approx 9{,}94$ °C. W Bukówce spadek o 0,43 m³/s
na rok przez 40 lat to około 17 m³/s – mniej więcej połowa największego maksimum szeregu (33,8 m³/s). Taki szereg
nie nadaje się do analizy częstości bez wyjaśnienia przyczyny zmiany.

## 10.4. Testy jednorodności

### Podział szeregu

Testy dwóch prób porównują dwie części szeregu: wartości sprzed i od wskazanego roku. Rok podziału powinien wynikać
ze znanego zdarzenia – oddania zbiornika do użytku, przeniesienia wodowskazu, regulacji koryta – ustalonego **przed**
obejrzeniem danych (Helsel i in. 2020, rozdz. 12.6.1). Bez takiego roku Hydrolog dzieli szereg na połowy.

<!-- spec:homogeneity_split -->
<!-- /spec:homogeneity_split -->

**Nie wybieraj roku podziału z tych samych danych.** Analityk, który widzi „skok” w szeregu i dzieli szereg w tym
miejscu, zawsze dostanie zaniżone $p$, bo wybrał podział najbardziej różnicujący części (Helsel i in. 2020,
rozdz. 12.6.3). Do szukania punktu zmiany służy test Pettitta, którego $p$ uwzględnia to przeszukiwanie (przykład 3
niżej).

### Test Manna–Whitneya

**Idea.** Test Manna–Whitneya (*Mann–Whitney U test*, test sumy rang Wilcoxona) sprawdza, czy wartości jednej części
są na ogół większe od wartości drugiej (Mann i Whitney 1947; Helsel i in. 2020, rozdz. 5.1). Statystyka $U$ pierwszej
części to liczba par (wartość z pierwszej części, wartość z drugiej), w których pierwsza jest większa; para wartości
równych liczy się za pół. Przy jednorodności $U$ jest bliskie połowy liczby wszystkich par, a skrajnie małe albo duże
$U$ oznacza przesunięcie. Hydrolog liczy test dwustronnie biblioteką SciPy (`mannwhitneyu`): rozkładem dokładnym dla
małych prób bez wartości równych, w pozostałych przypadkach przybliżeniem normalnym z poprawkami na wartości równe i
ciągłość (ADR-0022). Test nie ma własnej specyfikacji w Hydrologu, bo jest obliczeniem powierzonym bibliotece.

<!-- TODO spec: Mann–Whitney U of the two parts of a series and its two-sided p (SciPy mannwhitneyu, a delegated computation, CMP-1.2) -->

### Test Kołmogorowa–Smirnowa

**Idea.** Test Kołmogorowa–Smirnowa dla dwóch prób (*two-sample Kolmogorov–Smirnov test*) porównuje dystrybuanty
empiryczne obu części: statystyka $D$ to największa odległość między nimi. Reaguje na każdą różnicę rozkładów – położenia,
rozrzutu i kształtu – ale samo przesunięcie wykrywa zwykle słabiej niż test Manna–Whitneya. Maksima roczne podawane z dokładnością
trzech cyfr znaczących często się powtarzają, a dokładny rozkład $D$ z biblioteki SciPy zakłada brak wartości równych i
wtedy zawyża $p$. Dlatego dla prób z wartościami równymi i niezbyt dużych Hydrolog liczy $p$ dokładnie, przeliczając
wszystkie podziały połączonych wartości (Schröer i Trenkler 1995, jak funkcja `ks.test` w R; ADR-0049). Na danych z
przykładu 5.1 Helsela i in. (2020) $p$ maleje przez to z 0,0524 do 0,0478, a decyzja przy $\alpha = 0{,}05$ się
odwraca.

<!-- spec:ks_exact -->
<!-- /spec:ks_exact -->

### Test Pettitta

**Idea.** Test Pettitta (*Pettitt's change-point test*) nie wymaga roku podziału: dla każdego możliwego podziału
porównuje wartości przed nim i po nim, a punkt zmiany wskazuje tam, gdzie różnica jest największa (Pettitt 1979;
Helsel i in. 2020, rozdz. 12.6.3). Jego $p$ jest przybliżone i zachowawcze – dla krótkich szeregów zawyżone – ale
uwzględnia to, że punkt zmiany wybrano z danych.

<!-- spec:pettitt -->
<!-- /spec:pettitt -->

**Jak Hydrolog nazywa punkt zmiany.** `change_point_index` to liczba wartości przed zmianą, a `change_point_year` –
rok pierwszej wartości po zmianie. Ten rok można więc podać wprost jako `--split-year`, ale wtedy $p$ testów
Manna–Whitneya i Kołmogorowa–Smirnowa jest zaniżone (wyżej i przykład 3).

<!-- spec:homogeneity_decision -->
<!-- /spec:homogeneity_decision -->

**Zakres stosowania.** Wartości niezależne; test Pettitta zakłada co najwyżej jedną zmianę położenia. Testy nie
odróżniają skoku od trendu: szereg z trendem ma różne połowy i wyraźny „punkt zmiany” (przykład 1). Krótki szereg
rzadko daje odrzucenie: przy podziale na połowy testy Manna–Whitneya i Kołmogorowa–Smirnowa mogą odrzucić jednorodność
dopiero od 8 wartości, a test Pettitta od 11 (ADR-0022).

**Typowe błędy.** Uznanie „jednorodny” za dowód braku zmiany. Rok podziału wybrany z wykresu albo z wyniku testu
Pettitta na tych samych danych. Przypisanie zmiany przyczynie bez sprawdzenia historii zlewni i wodowskazu. Pominięcie
tego, że szereg niekompletny (np. bez roku największej powodzi) może być „jednorodny”, a mimo to nieprzydatny do
analizy częstości.

### Przykład 1: temperatura w Warszawie – trend, a nie skok

```bash
hydrolog stats homogeneity --values 7.96,8.76,7.76,8.84,8.21,6.83,7.85,8.18,9.04,9.63,8.32,9.31,8.26,8.41,8.58,8.95,9.63,9.79,8.83,7.95,9.13,8.79,8.91,9.83,10.33,9.78,9.39,10.43,10.89,10.51 --years 1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020
```

| Test | Statystyka | $p$ | Jednorodny |
|---|---|---|---|
| Mann–Whitney (podział 2006: 15 + 15 lat) | $U = 29{,}5$ | 0,00062 | nie |
| Kołmogorow–Smirnow | $D = 0{,}667$ | 0,0018 | nie |
| Pettitt | $K = 166$, zmiana przed 2006 | 0,0053 | nie |

Wszystkie testy odrzucają jednorodność, a Hydrolog dodaje uwagę `homogeneity_rejected`. Test Manna–Kendalla (p. 10.2)
pokazał jednak trend rosnący przez cały okres. Druga połowa szeregu jest cieplejsza od pierwszej, więc testy dwóch
prób i test Pettitta to wykrywają, ale „punkt zmiany” w 2006 r. nie jest żadnym zdarzeniem – to środek stopniowej
zmiany. Zawsze obejrzyj wykres szeregu i zestaw testy jednorodności z testem trendu.

### Przykład 2: Bóbr w Bukówce – punkt zmiany

```bash
hydrolog stats homogeneity --values 18.6,13.2,22.1,20.4,23,10.7,27.8,14.7,8.62,15.9,22.1,16.6,27.8,4.76,11.3,32.3,32.3,33.8,21.7,9.23,14.3,8.28,10.7,9.16,10.3,6.72,4.43,6.72,3.08,7.26,4.7,6.05,8.75,5.24,6.59,4.7,4.16,4.97,3.25,5.92,1.9 --years 1965,1966,1967,1968,1969,1970,1971,1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005
```

| Test | Statystyka | $p$ | Jednorodny |
|---|---|---|---|
| Mann–Whitney (podział 1985: 20 + 21 lat) | $U = 394{,}5$ | $1{,}6\cdot10^{-6}$ | nie |
| Kołmogorow–Smirnow | $D = 0{,}757$ | $2{,}7\cdot10^{-6}$ | nie |
| Pettitt | $K = 381$, 21 wartości przed zmianą | $8{,}8\cdot10^{-6}$ | nie |

Test Pettitta wskazuje zmianę między rokiem 1985 a 1986 (`change_point_year` = 1986). Metodyka KZGW nie podaje
przyczyny. Wynik testu wskazuje miejsce w czasie, które trzeba sprawdzić w historii zlewni i wodowskazu, a nie
przyczynę zmiany.

### Przykład 3: Nysa Kłodzka w Kłodzku – jednorodność i pułapka podziału

```bash
hydrolog stats homogeneity --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date
```

Hydrolog wybiera maksimum każdego pełnego roku hydrologicznego (74 lata; rok 1997 bez danych pominięty, uwaga
`missing_values_removed`) i dzieli szereg na połowy (od 1988 r.):

| Test | Statystyka | $p$ | Jednorodny |
|---|---|---|---|
| Mann–Whitney (podział 1988: 37 + 37 lat) | $U = 718$ | 0,72 | tak |
| Kołmogorow–Smirnow | $D = 0{,}162$ | 0,71 | tak |
| Pettitt | $K = 340$, zmiana przed 2012 | 0,37 | tak |

Żaden test nie wykrywa niejednorodności. Test Pettitta wskazuje rok 2012, ale z $p = 0{,}37$, czyli bez podstaw do
uznania tej zmiany. Gdyby jednak użyć tego roku jako podziału:

```bash
hydrolog stats homogeneity --input-file docs/podrecznik/dane/klodzko_1951_2025.csv --value-column Q --date-column date --split-year 2012
```

testy Manna–Whitneya ($p = 0{,}019$) i Kołmogorowa–Smirnowa ($p = 0{,}014$) „odrzucają” jednorodność, a Hydrolog
zgłasza uwagę `homogeneity_rejected`. To błąd opisany przez Helsela i in. (2020, rozdz. 12.6.3): rok podziału wybrano
tam, gdzie te same dane różnią się najbardziej, więc ich $p$ jest zaniżone. Właściwą odpowiedzią jest $p$ testu
Pettitta. Uwaga Hydrologa sygnalizuje wynik testu; ocena, czy podział był uprawniony, należy do użytkownika.

Jednorodność nie oznacza przy tym kompletności: w szeregu Kłodzka brakuje roku 1997 z największą powodzią wielolecia,
więc do analizy częstości (rozdział 7) trzeba go uzupełnić z innego źródła; publiczne pliki IMGW-PIB, także półroczne,
tego roku nie mają.

## 10.5. Lista kontrolna

1. Co jest hipotezą zerową, jakie $\alpha$ i ile wartości? Czy wartości są roczne i niezależne?
2. Podaj $p$, a nie tylko decyzję, i wielkość zmiany (nachylenie Sena z przedziałem).
3. Brak odrzucenia nie dowodzi braku zmiany: krótki szereg ma małą moc.
4. Odrzucenie nie wskazuje przyczyny. Sprawdź historię zlewni i wodowskazu, zmianę krzywej natężenia przepływu
   (p. 9.7) i braki danych.
5. Trend czy skok? Testy reagują na oba; obejrzyj wykres szeregu.
6. Rok podziału ustal przed testem, na podstawie znanego zdarzenia, a nie z tych samych danych.
7. Wiele stacji i wiele testów to także przypadkowe odrzucenia.
8. Zaokrąglij szereg do dokładności danych, zanim policzysz wartości równe.

## Źródła

Źródła oznaczone „niedostępne” nie są w otwartym dostępie; ich treść znamy z cytowań w źródłach otwartych.

- Conover W.J. (1980) Practical Nonparametric Statistics, wyd. 2. Wiley, Nowy Jork. Niedostępne.
- Gilbert R.O. (1987) Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, Nowy Jork,
  rozdz. 16. https://digital.library.unt.edu/ark:/67531/metadc1197046/m2/1/high_res_d/7037501.pdf
- Hamed K.H., Rao A.R. (1998) A modified Mann-Kendall trend test for autocorrelated data. Journal of Hydrology 204,
  182–196. Niedostępne.
- Helsel D.R., Hirsch R.M., Ryberg K.R., Archfield S.A., Gilroy E.J. (2020) Statistical Methods in Water Resources.
  U.S. Geological Survey Techniques and Methods 4-A3. https://pubs.usgs.gov/tm/04/a03/tm4a3.pdf
- Hirsch R.M., Slack J.R., Smith R.A. (1982) Techniques of trend analysis for monthly water quality data. Water
  Resources Research 18(1), 107–121; wersja otwarta: USGS Open-File Report 81-488 (1981).
  https://pubs.usgs.gov/of/1981/0488/report.pdf
- Hussain M.M. pyHomogeneity: pakiet Pythona testów jednorodności. https://github.com/mmhs013/pyHomogeneity
- Hydrolog, decyzje architektoniczne: ADR-0022 (testy jednorodności), ADR-0033 (wartości równe w teście
  Manna–Kendalla), ADR-0049 (dokładne $p$ małych prób), ADR-0063 (statystyki stacji według specyfikacji), katalog
  `docs/decisions/`.
- Kendall M.G. (1975) Rank Correlation Methods, wyd. 4. Griffin, Londyn. Niedostępne.
- KZGW (2017) Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie
  przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona).
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Mann H.B. (1945) Nonparametric tests against trend. Econometrica 13, 245–259. Niedostępne.
- Mann H.B., Whitney D.R. (1947) On a test of whether one of two random variables is stochastically larger than the
  other. Annals of Mathematical Statistics 18, 50–60. Nie otwierano; cytowane za Helsel i in. (2020).
- Pettitt A.N. (1979) A non-parametric approach to the change-point problem. Journal of the Royal Statistical Society,
  Series C (Applied Statistics) 28(2), 126–135. Niedostępne.
- Pohlert T. trend: Non-Parametric Trend Tests and Change-Point Detection, pakiet R 1.1.10. https://cran.r-project.org/package=trend
- R Core Team: R 4.4.3, pakiet stats, funkcja `ks.test`. https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html
- Schröer G., Trenkler D. (1995) Exact and randomization distributions of Kolmogorov-Smirnov tests two or three
  samples. Computational Statistics & Data Analysis 20(2), 185–202. Niedostępne.
- Sen P.K. (1968) Estimates of the regression coefficient based on Kendall's tau. Journal of the American Statistical
  Association 63, 1379–1389. Niedostępne.
- Yue S., Wang C. (2004) The Mann-Kendall test modified by effective sample size to detect trend in serially
  correlated hydrological series. Water Resources Management 18, 201–218. Niedostępne.
