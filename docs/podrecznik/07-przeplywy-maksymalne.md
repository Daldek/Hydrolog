# 7. Przepływy maksymalne prawdopodobne

Rozdział opisuje statystyczną analizę częstości wezbrań (ang. *flood frequency analysis*): jak z ciągu
maksimów rocznych zmierzonych na wodowskazie wyznaczyć przepływ, który w każdym roku jest przewyższany
z zadanym prawdopodobieństwem. W polskiej praktyce taki przepływ nazywa się przepływem maksymalnym
prawdopodobnym albo, dokładniej, przepływem maksymalnym rocznym o określonym prawdopodobieństwie
przewyższenia $Q_{p\%}$ (np. $Q_{1\%}$). Jest to kwantyl rozkładu maksimów rocznych. Nie należy go mylić
z wezbraniem maksymalnym możliwym (ang. *probable maximum flood*, PMF), które jest górną granicą
fizyczną, a nie kwantylem — tak samo jak opady PMAXTP z rozdziału 2 nie są opadem maksymalnym
prawdopodobnym PMP.

Metoda wymaga długiego ciągu obserwacji przepływu w przekroju. Zlewnia Kamiennika, przykład przewodni
podręcznika, nie ma wodowskazu: jej hydrogram projektowy wyznacza się z opadu (rozdziały 2–6). Ten
rozdział pokazuje drugą drogę na danych dwóch wodowskazów: Polany na Czarnej (przykład metodyki KZGW
2017) i Świerzawy na Kaczawie — wodowskazu IMGW-PIB w tej samej miejscowości, w której zamyka się
zlewnia Kamiennika. Przepływy niskie i minima roczne omawia rozdział 8, testy trendu i jednorodności
rozdział 10.

## 7.1. Idea: maksimum roczne jako zmienna losowa

Największy przepływ roku hydrologicznego, $WQ$ (ang. *annual maximum flow*), traktuje się jak zmienną
losową. Jej dystrybuanta $F(x)$ podaje prawdopodobieństwo, że maksimum roku nie przekroczy wartości $x$
(prawdopodobieństwo nieprzewyższenia, ang. *non-exceedance probability*). W projektowaniu używa się
prawdopodobieństwa przewyższenia $p$ (ang. *exceedance probability*), czyli dopełnienia dystrybuanty
do jedności, zapisywanego w procentach. Okres powtarzalności $T$ (ang. *return period*) to odwrotność
prawdopodobieństwa przewyższenia: średni odstęp w latach między latami, w których przepływ $Q_{p\%}$
jest przekroczony. „Woda stuletnia” $Q_{1\%}$ nie zdarza się więc raz na sto lat jak w kalendarzu:
w każdym roku jest przewyższana z prawdopodobieństwem 1 %, niezależnie od tego, kiedy wystąpiła
ostatnio. Prawdopodobieństwo, że w ciągu wielu lat przepływ ten zostanie przewyższony choć raz, rośnie
z liczbą lat i dla okresu użytkowania budowli porównywalnego z $T$ jest znaczne; dlatego okres
powtarzalności nie jest gwarancją bezpieczeństwa na $T$ lat.

Analiza opiera się na trzech założeniach. Maksima kolejnych lat są niezależne (jedna wartość na rok
hydrologiczny), pochodzą z jednego rozkładu (ciąg jednorodny, ang. *homogeneous*: bez zbiornika,
regulacji czy przeniesienia wodowskazu w trakcie obserwacji) i ten rozkład nie zmienia się w czasie
(stacjonarność, ang. *stationarity*: brak trendu). Ramki specyfikacji poniżej podają je jako założenie
niezależności i jednakowego rozkładu maksimów rocznych.
Czwarta, ukryta trudność to ekstrapolacja: przepływy o okresie powtarzalności 100–1000 lat wyznacza się
z ciągów 30–70-letnich, więc o wyniku decyduje w dużej mierze przyjęty kształt rozkładu.

## 7.2. Dane: szereg maksimów rocznych

### Rok hydrologiczny i maksimum roku

Maksima liczy się w latach hydrologicznych, nie kalendarzowych: wezbranie roztopowe z przełomu zimy
i wiosny należy wtedy w całości do jednego roku.

<!-- spec:hydrological_year -->

<a id="spec-hydrological_year"></a>

> **Rok hydrologiczny daty** · wzór grupy B `hydrological_year` (Tier B, CMP-2.2)
>
> **Definicja:** Rok hydrologiczny daty: jej rok kalendarzowy, a dla listopada i grudnia rok następny. (źr. 1)
>
> **Konwencja:** Rok IMGW-PIB trwa od 1 listopada do 31 października i nosi nazwę roku kalendarzowego, w którym się kończy (2016 = 1.11.2015–31.10.2016); w ČHMÚ tak samo (Hydrologická ročenka České republiky 2010, wstęp).
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | – | `first_month` | Pierwszy miesiąc roku hydrologicznego | 11 | mies. | (źr. 1) |
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/hydrologia_info_ogolne.txt>
>
> Funkcja `hydrolog.statistics._hydrological_year.hydrological_year`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:hydrological_year -->

IMGW-PIB publikuje przepływy charakterystyczne półroczy (zimowego XI–IV i letniego V–X) wyznaczone ze
wszystkich obserwacji i pomiarów, a więc maksima bliskie kulminacji chwilowej. Hydrolog przyjmuje za
maksimum roczne większe z maksimów obu półroczy, a rok z jednym półroczem pomija i wymienia, bo brakujące
półrocze mogło zawierać wezbranie:

<!-- spec:half_year_annual_extremes -->

<a id="spec-half_year_annual_extremes"></a>

> **Ekstrema roczne z charakterystyk półroczy** · wzór grupy B `half_year_annual_extremes` (Tier B, CMP-2.2)
>
> **Definicja:** Maksima (minima) roczne z charakterystyk półroczy IMGW-PIB: większa (mniejsza) z wartości półrocza zimowego i letniego każdego roku, który ma obie. (źr. 1)
>
> **Konwencja:** Przy równości przyjmuje się wartość zimową, z datą z jej półrocza; rok z tylko jednym półroczem jest pomijany i wymieniony w `incomplete_years`.
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), PLWSKP 13 winter half-year XI-IV, 14 summer half-year V-X, 15 year; PLWSKEX 1 minimum, 2 mean, 3 maximum; a value 99999.999 or NULL is a break in observations <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/polroczne_i_roczne/POLR_publiczne_format.txt>
>
> Funkcja `hydrolog.statistics.characteristic.annual_extremes_from_half_years`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:half_year_annual_extremes -->

Z szeregu dobowego (np. eksportu Obserwatora) maksimum roku jest największym średnim przepływem dobowym,
i to tylko z lat, w których każdy dzień ma wartość:

<!-- spec:complete_year_extremes -->

<a id="spec-complete_year_extremes"></a>

> **Ekstrema roczne lat kompletnych** · wzór grupy B `complete_year_extremes` (Tier B, CMP-2.2)
>
> **Definicja:** Maksimum albo minimum każdego kompletnego roku hydrologicznego, czyli takiego, który ma wartość w każdym ze swoich 365 albo 366 dni. (źr. 1)
>
> **Konwencja:** Rok z dniem bez wartości jest pomijany i zgłaszany (jego ekstremum mogło przypaść na ten dzień); data podana dwukrotnie liczy się raz.
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), 'Wartość stanu wody/przepływu/temperatury wody równa 99999.999 albo NULL oznacza przerwy w obserwacjach': no characteristic of a period with a break <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/polroczne_i_roczne/POLR_publiczne_format.txt>
>
> Funkcja `hydrolog.statistics._hydrological_year.annual_extremes`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:complete_year_extremes -->

Średnia dobowa spłaszcza kulminację, tym bardziej, im szybciej reaguje zlewnia. Polska metodyka
(KZGW 2017) definiuje przepływ maksymalny roczny jako najwyższą w roku wartość przepływu chwilowego lub
dobowego, a w praktyce posługuje się kulminacjami. W małych zlewniach różnica jest duża: na Kaczawie
w Świerzawie kwantyl stuletni z maksimów dobowych jest o ponad jedną trzecią mniejszy niż z maksimów IMGW-PIB
(przykład 7.10). Polecenia Hydrologa czytają oba rodzaje danych: `--half-year-file` (charakterystyki
półroczne IMGW-PIB w eksporcie Obserwatora), `--input-file` z `--date-column` (szereg dobowy) albo
`--values` (gotowe maksima roczne).

### Długość, jednorodność i trend

Metodyka KZGW (2017) wymaga ciągu co najmniej 30-letniego; krótszy należy najpierw przedłużyć, np.
korelacją z sąsiednim wodowskazem. Hydrolog liczy także krótsze ciągi, ale dołącza do wyniku uwagę
`short_record`, a przy bardzo krótkich `small_sample`. Przed dopasowaniem rozkładu trzeba sprawdzić, czy
ciąg jest jednorodny i bez trendu: KZGW (2017) wymaga testu Manna–Kendalla na poziomie istotności 0,05.
W Hydrologu służą do tego `hydrolog stats mann-kendall` i `hydrolog stats homogeneity` (testy
Manna–Whitneya, Kołmogorowa–Smirnowa i Pettitta); ich teorię i interpretację podaje rozdział 10. Wynik
„brak trendu” znaczy tylko, że test go nie wykrył: krótki ciąg rzadko daje odrzucenie hipotezy.

Najczęstsze błędy danych:

- maksima lat kalendarzowych zamiast hydrologicznych;
- łączenie w jednym ciągu kulminacji chwilowych i maksimów średnich dobowych;
- ciąg z luką w roku największego wezbrania. Publiczne dane IMGW-PIB nie mają np. roku hydrologicznego
  1997 dla wodowskazu Kłodzko na Nysie Kłodzkiej, czyli roku powodzi lipcowej; analiza częstości takiego
  ciągu bez uzupełnienia luki zaniża kwantyle rzadkich przepływów;
- rok z brakami pozostawiony w ciągu maksimów: Hydrolog pomija rok niepełny (uwaga `incomplete_years`),
  bo jego maksimum mogło wypaść w dniu bez danych.

## 7.3. Prawdopodobieństwo empiryczne: pozycje wykreślne

Uporządkowane maksima dostają prawdopodobieństwa empiryczne (pozycje wykreślne, ang. *plotting
positions*), które pozwalają nanieść próbę na siatkę prawdopodobieństwa obok dopasowanego rozkładu.
Hydrolog daje je w bloku `empirical` wyniku `stats flood-frequency`.

<!-- spec:plotting_positions -->

<a id="spec-plotting_positions"></a>

> **Pozycje wykreślne maksimów rocznych: prawdopodobieństwa przewyższenia i okresy powtarzalności** · specyfikacja [`plotting_positions`](../FORMULAS.md#plotting_positions) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> p_i = \frac{i - a}{n + 1 - 2a},\qquad T_i = \frac{1}{p_i}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_{(i)}$ | `values` (ciąg) | Próba: maksima roczne przepływu lub stanu wody | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
> | $a$ | `method` (wybór) | Formuła pozycji wykreślnej: Weibulla, Hazena lub Cunnane'a | – | jedna z: `weibull`, `hazen`, `cunnane` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $x_{(i)}$ | `values_sorted` (ciąg) | Wartości uporządkowane malejąco | m³/s | (−∞; ∞) |
> | $p_i$ | `exceedance_prob` (ciąg) | Prawdopodobieństwo przewyższenia każdej wartości | – | (0; 1) |
> | $T_i$ | `return_periods` (ciąg) | Okres powtarzalności każdej wartości, przewyższanej raz na T lat | lata | (1; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $a$ | `a_weibull` | Parametr a formuły pozycji wykreślnej Weibulla | 0 | – | (źr. 1) |
> | $a$ | `a_hazen` | Parametr a formuły pozycji wykreślnej Hazena | 1/2 | – | (źr. 1) |
> | $a$ | `a_cunnane` | Parametr a formuły pozycji wykreślnej Cunnane'a | 2/5 | – | (źr. 1) |
>
> **Konwencje**
>
> - prawdopodobieństwo przewyższenia i-tej co do wielkości wartości, ranga 1 to wartość największa (WMO-No. 168, § 5.6.1; KZGW 2017, wzór 3.7, polskie p_i = i / (N + 1)); okres powtarzalności T = 1 / p, jak dla kwantyli maksimów
> - postać ogólna (i - a) / (n + 1 - 2a) z WMO-No. 1029, wzór 7.3, z wartościami a z WMO-No. 168, § 5.6.1; bez wzoru Gringortena
> - wartości wiązane otrzymują kolejne rangi, każda z własną pozycją, tak jak w KZGW 2017, tab. 3.13, kolejne rangi mają dwie wartości 10,3 i dwie wartości 7,88 m³/s
> - próba w dowolnej jednostce: pozycje zależą tylko od rang
>
> **Zgodność z obserwacjami według źródeł:** brak: oszacowanie prawdopodobieństwa każdej wartości uporządkowanej próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 3.7, p. 29: p_i = i / (N + 1) 100 %, the empirical exceedance probability of the ith largest annual maximum; example 3.4, table 3.13, pp. 54-55 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 3. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.3, eq. 7.3, p. 59: P_i = (i - a) / (n + 1 - 2a), the non-exceedance probability of the ith smallest of n events; p. 60: the Weibull formula is a = 0; sect. 7.8, step I, p. 65: the AM(7) values ranked ascending, the smallest rank 1, and the Weibull formula <https://library.wmo.int/idurl/4/32176>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
>
> Funkcja `hydrolog.statistics._types.compute_plotting_positions`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:plotting_positions -->

Domyślny wzór Weibulla jest wzorem polskiej metodyki (KZGW 2017). Wzory Hazena i Cunnane’a różnią się
głównie w ogonach próby; WMO (2009) wymienia wszystkie trzy. Wzór Weibulla nigdy nie przypisuje
wartości prawdopodobieństwa 0 ani 1, ale też nie mówi, jak rzadkie było największe wezbranie: największe
z $N$ maksimów stoi zawsze przy okresie powtarzalności o rok dłuższym od długości ciągu, choćby było
wezbraniem tysiącletnim. Częsty błąd przy odczycie z siatki to pomylenie prawdopodobieństwa przewyższenia
z prawdopodobieństwem nieprzewyższenia; blok `empirical` Hydrologu podaje prawdopodobieństwo
przewyższenia (`exceedance_prob`) i okres powtarzalności (`return_periods`) każdego maksimum.

## 7.4. Charakterystyki próby: momenty i L-momenty

Rozkład dopasowuje się do kilku liczb opisujących próbę. Momenty zwykłe (ang. *product moments*) to
średnia, odchylenie standardowe i współczynnik skośności:

<!-- spec:sample_moments -->

<a id="spec-sample_moments"></a>

> **Średnia, odchylenie standardowe i skośność próby (momenty zwykłe)** · specyfikacja [`sample_moments`](../FORMULAS.md#sample_moments) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \bar{x} = \frac{1}{n}\sum_i x_i,\quad s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}{n - 1}},\quad G = \frac{\sqrt{n(n - 1)}}{n - 2}\,\frac{m_3}{m_2^{3/2}},\quad m_k = \frac{1}{n}\sum_i (x_i - \bar{x})^k
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `values` (ciąg) | Próba: maksima lub minima roczne | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\bar{x}$ | `mean` | Średnia arytmetyczna | m³/s | (−∞; ∞) |
> | $s$ | `std` | Odchylenie standardowe z dzielnikiem n - 1 | m³/s | [0; ∞) |
> | $G$ | `skewness` | Skorygowany współczynnik skośności Fishera–Pearsona | – | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 3 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - odchylenie standardowe z dzielnikiem n - 1 (Bulletin 17B, wzór 3a; WMO-No. 1029, wzór 7.8)
> - skośność G z Bulletin 17B, wzór 4a, N sum((X - mean)**3) / ((N - 1)(N - 2) S**3), czyli skorygowany współczynnik Fishera–Pearsona G1 funkcji scipy.stats.skew z bias=False; WMO-No. 1029, wzór 7.9, podaje obciążony m3 / m2**1.5, czyli G (n - 2) / sqrt(n (n - 1))
> - próba w dowolnej jednostce: średnia i odchylenie standardowe w jej jednostce, skośność bezwymiarowa
> - momenty odchyleń od średniej (wzory 3a i 4a, które według Bulletin 17B, s. 10, są mniej wrażliwe na liczbę zachowanych cyfr niż sumy potęg ze wzorów 3b i 4b), centrowane dwukrotnie, na próbie podzielonej przez potęgę dwójki
>
> **Zgodność z obserwacjami według źródeł:** brak: definicje statystyk z próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eqs. 2, 3a and 4a (equal to 3b and 4b), pp. 9-10; appendix 12, example 1, table 12-2 and eqs. 12-1 to 12-3 <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 2. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.6.1, eqs. 7.7 and 7.8, p. 63 (its eq. 7.9 is the biased skewness m3 / m2**1.5); table 7.1, p. 64 <https://library.wmo.int/idurl/4/32176>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.skew with bias=False: the adjusted Fisher-Pearson standardized moment coefficient G1 = sqrt(n (n - 1)) / (n - 2) m3 / m2**1.5 <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by (N - 1)(N - 2) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 6. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by S cubed, 0 for equal values <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
>
> Funkcja `hydrolog.statistics.frequency.sample_moments`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:sample_moments -->

L-momenty (ang. *L-moments*; Hosking 1990) są liniowymi kombinacjami uporządkowanych wartości. Pierwszy
jest średnią, drugi miarą rozrzutu w jednostce przepływu, a ich iloraz z trzecim — L-skośność $\tau_3$,
bez jednostki:

<!-- spec:sample_l_moments -->

<a id="spec-sample_l_moments"></a>

> **L-momenty i L-skośność próby (nieobciążone momenty ważone prawdopodobieństwem)** · specyfikacja [`sample_l_moments`](../FORMULAS.md#sample_l_moments) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> b_r = \frac{1}{n}\binom{n - 1}{r}^{-1}\sum_{j=1}^{n}\binom{j - 1}{r}x_{(j)},\quad \lambda_1 = b_0,\quad \lambda_2 = 2b_1 - b_0,\quad \tau_3 = \frac{6b_2 - 6b_1 + b_0}{\lambda_2}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `values` (ciąg) | Próba: maksima lub minima roczne | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 6) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\lambda_1$ | `l1` | Pierwszy L-moment, średnia | m³/s | (−∞; ∞) |
> | $\lambda_2$ | `l2` | Drugi L-moment, połowa średniej różnicy dwóch wartości | m³/s | [0; ∞) |
> | $\tau_3$ | `t3` | L-skośność; 1 (lub -1), gdy wszystkie wartości poza największą (najmniejszą) są równe | – | [−1; 1] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 3 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Konwencje**
>
> - nieobciążone momenty ważone prawdopodobieństwem b_r próby uporządkowanej rosnąco (Hosking 1990; lmom samlmu; lmomco pwm.ub), a nie obciążone estymatory oparte na pozycjach wykreślnych
> - L-skośność t3 = lambda3 / lambda2 (WMO-No. 168, tab. II.5.4)
> - próba w dowolnej jednostce: l1 i l2 w jej jednostce, t3 bezwymiarowe
> - lambda2 i lambda3 jako sumy ważone uporządkowanych odchyleń od średniej, które tworzą b_r (z wagami zsumowanymi najpierw), na próbie podzielonej przez potęgę dwójki; l1 to średnia centrowana dwukrotnie
> - \|t3\| = 1, gdy wszystkie wartości poza największą lub najmniejszą są równe; sumy ważone n wartości mają błąd zaokrąglenia do n ulp, więc t3 przekraczające 1 lub -1 o nie więcej niż 1e-9 ustawia się na tę granicę (tolerancja brzegowa)
>
> **Zgodność z obserwacjami według źródeł:** brak: definicje statystyk z próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hosking, J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of order statistics. Journal of the Royal Statistical Society, Series B 52(1), 105-124, sect. 2: probability-weighted moments and the sample L-moments of their unbiased estimators — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), samlmu: the sample L-moments of Hosking (1990) from the unbiased probability-weighted moments <https://cran.r-project.org/package=lmom>
> 3. Asquith, W.H. lmomco: L-moments, censored L-moments, trimmed L-moments, L-comoments, and many distributions, R package version 2.5.8, CRAN, pwm.ub: beta_r = n^-1 C(n - 1, r)^-1 sum C(j - 1, r) x(j:n); lmoms <https://cran.r-project.org/package=lmomco>
> 4. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5.1, eqs. 5.25 to 5.27 and table II.5.4, pp. II.5-11 to II.5-12 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 5. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.6.2, eqs. 7.11 and 7.12, p. 64; table 7.1, p. 64 <https://library.wmo.int/idurl/4/32176>
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Asquith, W.H. lmomco: L-moments, censored L-moments, trimmed L-moments, L-comoments, and many distributions, R package version 2.5.8, CRAN, pwm.ub: b2 divides by C(n - 1, 2), 0 for n < 3 <https://cran.r-project.org/package=lmomco>
> 8. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.4: the L-skewness is lambda3 / lambda2, and lambda2 is 0 for equal values <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
>
> Funkcja `hydrolog.statistics.frequency.sample_l_moments`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:sample_l_moments -->

Ponieważ wartości wchodzą do L-momentów liniowo, a nie w drugiej i trzeciej potędze, pojedyncze duże
wezbranie waży w nich znacznie mniej niż w odchyleniu standardowym i skośności. WMO (2009, § 5.5.1)
zauważa, że L-współczynnik zmienności i L-skośność są prawie nieobciążone, podczas gdy zwykłe $C_v$
i $C_s$ krótkich prób są silnie obciążone i bardzo zmienne. W obu przykładach tego rozdziału skośność
maksimów jest dodatnia i duża: kilka wielkich wezbrań na tle wielu umiarkowanych.

## 7.5. Rozkłady prawdopodobieństwa maksimów rocznych

Hydrolog dopasowuje cztery rozkłady. Każda ramka podaje wzór kwantyla dla okresu powtarzalności $T$
i umowy dotyczące parametrów. Kwantyl liczy się z odwrotności funkcji przeżycia w punkcie $1/T$, co
zachowuje dokładność także dla bardzo długich okresów.

### Uogólniony rozkład wartości ekstremalnych (GEV)

Rozkład GEV (ang. *generalized extreme value*) wynika z teorii wartości ekstremalnych: jest granicznym
rozkładem maksimów z dużej liczby zdarzeń (Coles 2001). Jego parametr kształtu decyduje o górnym ogonie.

<!-- spec:gev_quantiles -->

<a id="spec-gev_quantiles"></a>

> **Kwantyle uogólnionego rozkładu wartości ekstremalnych (GEV) dla okresów powtarzalności** · specyfikacja [`gev_quantiles`](../FORMULAS.md#gev_quantiles) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_T = \xi + \alpha\,\frac{1 - y^{c}}{c},\quad y = -\ln\left(1 - \frac{1}{T}\right);\qquad Q_T = \xi - \alpha \ln y \ \ (c = 0)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $c$ | `shape` | Parametr kształtu c: górne ograniczenie dla c > 0, ciężki górny ogon dla c < 0 | – | (−∞; ∞) | nie podano w źródłach | [−0,6; 0] (źr. 4) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) | nie podano w źródłach | [2; 22,2] (źr. 4) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1; 19,5] (źr. 4) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_T$ | `quantiles` (ciąg) | Przepływy o danych okresach powtarzalności | m³/s | (−∞; ∞) |
>
> **Konwencje**
>
> - parametr kształtu c funkcji genextreme biblioteki scipy, równy k u Hoskinga i kappa w WMO-No. 168 i WMO-No. 1029 oraz -xi u Colesa (2001): przy c > 0 rozkład ma górne ograniczenie loc + scale/c, przy c < 0 — ciężki górny ogon
> - kwantyl okresu powtarzalności T przy rocznym prawdopodobieństwie przewyższenia 1/T, czyli nieprzewyższenia 1 - 1/T (polskie Q_p% z p = 100/T %, KZGW 2017, wzór 3.7; WMO-No. 168, § 5.6.1), liczony z odwrotnej funkcji przeżycia w punkcie 1/T, która zachowuje cyfry znaczące dla długich okresów powtarzalności
> - loc i scale w jednostce próby; wzór jest jednorodny
>
> **Zgodność z obserwacjami według źródeł:** brak: funkcja kwantylowa rozkładu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5 (the GEV of Stedinger et al. 1993, F(x) = exp{-[1 - kappa (x - xi) / alpha]^(1/kappa)}); sect. 5.6.1, p. II.5-14 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 2. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, eq. 7.5, p. 62 (the same GEV, kappa > 0 bounded above) <https://library.wmo.int/idurl/4/32176>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
>
> Funkcja `hydrolog.statistics.frequency.gev_quantiles`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:gev_quantiles -->

Uwaga na znak parametru kształtu. Hydrolog używa parametru $c$ biblioteki SciPy, równego $k$ Hoskinga
i $\kappa$ WMO (2009). Coles (2001) i wiele programów (np. pakiety R `evd`, `extRemes`) używają
$\xi = -c$. Ujemne $c$ (dodatnie $\xi$) oznacza ciężki górny ogon: kwantyle rosną z $T$ szybciej niż
w rozkładzie Gumbela, który odpowiada $c = 0$. Dodatnie $c$ daje rozkład ograniczony od góry. Rozkładu
GEV nie ma w metodyce KZGW (2017); jest w programie PrzepływyMax2011 IMGW-PIB (Węglarczyk red. 2013).

### Rozkład logarytmiczno-normalny

Rozkład logarytmiczno-normalny (ang. *log-normal*): logarytm przepływu pomniejszonego o dolne
ograniczenie $\epsilon$ ma rozkład normalny.

<!-- spec:log_normal_quantiles -->

<a id="spec-log_normal_quantiles"></a>

> **Kwantyle rozkładu logarytmiczno-normalnego dla okresów powtarzalności** · specyfikacja [`log_normal_quantiles`](../FORMULAS.md#log_normal_quantiles) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_T = \epsilon + e^{\mu} \exp\left(\sigma\,\Phi^{-1}\left(1 - \frac{1}{T}\right)\right)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\sigma$ | `shape` | Odchylenie standardowe logarytmów x - loc | – | (0; ∞) | nie podano w źródłach | [0,6; 0,9] (źr. 4) |
> | $\epsilon$ | `loc` | Dolne ograniczenie: 0 dla rozkładu dwuparametrowego dopasowywanego w Hydrologu | m³/s | (−∞; ∞) | nie podano w źródłach | [0; 0,4] (źr. 4) |
> | $e^{\mu}$ | `scale` | Funkcja wykładnicza (exp) średniej logarytmów | m³/s | (0; ∞) | nie podano w źródłach | [2,4; 27] (źr. 4) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_T$ | `quantiles` (ciąg) | Przepływy o danych okresach powtarzalności | m³/s | (−∞; ∞) |
>
> **Konwencje**
>
> - lognorm(s, loc, scale) biblioteki scipy: s = sigma, loc = epsilon (dolne ograniczenie z KZGW 2017, wzór 3.35), scale = exp(mu)
> - kwantyl okresu powtarzalności T przy rocznym prawdopodobieństwie przewyższenia 1/T, czyli nieprzewyższenia 1 - 1/T (polskie Q_p% z p = 100/T %, KZGW 2017, wzór 3.7; WMO-No. 168, § 5.6.1), liczony z odwrotnej funkcji przeżycia w punkcie 1/T, która zachowuje cyfry znaczące dla długich okresów powtarzalności
> - loc i scale w jednostce próby; wzór jest jednorodny
>
> **Zgodność z obserwacjami według źródeł:** brak: funkcja kwantylowa rozkładu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.35 and 3.40, p. 46 (Q_p = epsilon + exp(mu + sigma u_p)); example 3.3, table 3.12, p. 51 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5 and its note a (the three-parameter log-normal with Y = ln(X - xi)) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
>
> Funkcja `hydrolog.statistics.frequency.log_normal_quantiles`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:log_normal_quantiles -->

Analiza częstości w Hydrologu (`stats flood-frequency`) dopasowuje wersję dwuparametrową, z dolnym
ograniczeniem równym zeru, więc wszystkie maksima muszą być dodatnie. Metodyka KZGW (2017) stosuje
wersję trójparametrową, z dolnym ograniczeniem szacowanym ze skrajnych wartości i mediany próby; tego
wariantu Hydrolog nie dopasowuje i jego wyniki rozkładu logarytmiczno-normalnego nie są wynikami KZGW.

### Rozkład Pearsona typu III

Trójparametrowy rozkład gamma (ang. *Pearson type III*) jest podstawowym rozkładem polskiej metodyki
(KZGW 2017) i amerykańskiego Bulletin 17B (IACWD 1982, tam dla logarytmów przepływów).

<!-- spec:pearson3_quantiles -->

<a id="spec-pearson3_quantiles"></a>

> **Kwantyle rozkładu Pearsona typu III dla okresów powtarzalności** · specyfikacja [`pearson3_quantiles`](../FORMULAS.md#pearson3_quantiles) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_T = \mu + K_{\gamma}\!\left(1 - \frac{1}{T}\right)\sigma
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\gamma$ | `skew` | Skośność rozkładu | – | (−∞; ∞) | nie podano w źródłach | [1,3; 2,7] (źr. 4) |
> | $\mu$ | `loc` | Średnia rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [3; 35,4] (źr. 4) |
> | $\sigma$ | `scale` | Odchylenie standardowe rozkładu | m³/s | (0; ∞) | nie podano w źródłach | [2; 29,6] (źr. 4) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_T$ | `quantiles` (ciąg) | Przepływy o danych okresach powtarzalności | m³/s | (−∞; ∞) |
>
> **Konwencje**
>
> - pearson3(skew, loc, scale) biblioteki scipy jest parametryzowany średnią, odchyleniem standardowym i skośnością, jak w Bulletin 17B i rozkładzie PE3 pakietu lmom (mu, sigma, gamma); parametry (epsilon, alpha, lambda) z KZGW 2017 dają skew = 2 / sqrt(lambda), loc = epsilon + lambda / alpha oraz scale = sqrt(lambda) / alpha
> - przy dodatniej skośności rozkład ma dolne ograniczenie loc - 2 scale / skew, przy ujemnej — górne ograniczenie loc - 2 scale / skew
> - kwantyl okresu powtarzalności T przy rocznym prawdopodobieństwie przewyższenia 1/T, czyli nieprzewyższenia 1 - 1/T (polskie Q_p% z p = 100/T %, KZGW 2017, wzór 3.7; WMO-No. 168, § 5.6.1), liczony z odwrotnej funkcji przeżycia w punkcie 1/T, która zachowuje cyfry znaczące dla długich okresów powtarzalności
> - loc i scale w jednostce próby; wzór jest jednorodny
>
> **Zgodność z obserwacjami według źródeł:** brak: funkcja kwantylowa rozkładu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 1, p. 9 (log Q = X + K S) and appendix 3, pp. 3-1 to 3-10 (the frequency factors K of Harter 1969 for skews of -9 to 9) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.1 and 3.3, p. 28 (Q_p = epsilon + the gamma quantile of 1 - p with lambda and 1/alpha); example 3.2, table 3.9, p. 44 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
>
> Funkcja `hydrolog.statistics.frequency.pearson3_quantiles`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:pearson3_quantiles -->

Hydrolog parametryzuje go średnią, odchyleniem standardowym i skośnością; ramka podaje przeliczenie na
parametry KZGW (dolne ograniczenie $\epsilon$, skala $\alpha$, kształt $\lambda$). Przy dodatniej
skośności rozkład ma dolne ograniczenie. Gdy skośność przekracza wartość, przy której gęstość staje się
nieskończona na tej granicy, metoda największej wiarygodności przestaje działać (p. 7.6).

### Trójparametrowy rozkład Weibulla

Rozkład Weibulla ograniczony od dołu stosuje KZGW (2017) „w uzasadnionych przypadkach”.

<!-- spec:weibull_quantiles -->

<a id="spec-weibull_quantiles"></a>

> **Kwantyle trójparametrowego rozkładu Weibulla dla okresów powtarzalności** · specyfikacja [`weibull_quantiles`](../FORMULAS.md#weibull_quantiles) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_T = \epsilon + \frac{1}{\alpha_W}\left(\ln T\right)^{1/\beta_W}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $\beta_W$ | `shape` | Parametr kształtu k rozkładu | – | (0; ∞) | nie podano w źródłach | [0,7; 1,4] (źr. 4) |
> | $\epsilon$ | `loc` | Dolne ograniczenie | m³/s | (−∞; ∞) | nie podano w źródłach | [−1; 4,9] (źr. 4) |
> | $1/\alpha_W$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1,5; 37] (źr. 4) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_T$ | `quantiles` (ciąg) | Przepływy o danych okresach powtarzalności | m³/s | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | ln(scale) + ln(ln T) / k < 708,78 dla każdego T: scale (ln T)**(1/k) poniżej e**-1 największej liczby float64 | `finite_quantiles` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - weibull_min(k, loc, scale) biblioteki scipy, rozkład Weibulla z dolnym ograniczeniem dopasowywany do maksimów jak w KZGW 2017, wzór 3.52 (epsilon = loc, alpha_W = 1/scale, beta_W = k), i w pakiecie lmom (zeta, beta, delta)
> - kwantyl okresu powtarzalności T przy rocznym prawdopodobieństwie przewyższenia 1/T, czyli nieprzewyższenia 1 - 1/T (polskie Q_p% z p = 100/T %, KZGW 2017, wzór 3.7; WMO-No. 168, § 5.6.1), liczony z odwrotnej funkcji przeżycia w punkcie 1/T, która zachowuje cyfry znaczące dla długich okresów powtarzalności
> - loc i scale w jednostce próby; wzór jest jednorodny
>
> **Zgodność z obserwacjami według źródeł:** brak: funkcja kwantylowa rozkładu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.52 and 3.55, pp. 53-54 (P(Q >= x) = exp(-[alpha_W (x - epsilon)]^beta_W)); example 3.4, table 3.15, p. 60 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, eq. 7.6, p. 62 (F(x) = 1 - exp[-((x - xi) / alpha)^kappa]) and eq. 7.13, p. 64 <https://library.wmo.int/idurl/4/32176>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
> 6. Harris, C.R. et al. (2020). Array programming with NumPy. Nature 585, 357-362, numpy.finfo(numpy.float64).max, about 1.8e308, the largest IEEE 754 binary64 number <https://numpy.org/doc/stable/reference/generated/numpy.finfo.html>
>
> Funkcja `hydrolog.statistics.frequency.weibull_quantiles`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:weibull_quantiles -->

W Hydrologu kształt to $\beta_W$ KZGW, położenie to dolne ograniczenie $\epsilon$, a skala to odwrotność
$\alpha_W$. Metody momentów i L-momentów traktują rozkład Weibulla jak GEV próby o przeciwnym znaku
(ramki p. 7.6), co zawęża zakres możliwej skośności próby.

## 7.6. Estymacja parametrów

Każda metoda szacowania daje parametry tych samych czterech rozkładów; kwantyle, testy i AIC liczy się
z nich jednakowo. Opcja `--fit-method` wybiera metodę (`l_moments` domyślnie, `moments`, `mle`,
`least_squares`), a wartość `all` dopasowuje każdy rozkład każdą metodą i szereguje wszystkie
kombinacje według AIC. Próbę, której metoda nie potrafi dopasować, Hydrolog odrzuca z nazwą
niespełnionego warunku (ramki: `enough_values`, `values_not_all_equal`, `positive_values`,
`l_moments_within_distribution`, `skewness_within_distribution`, `likelihood_has_a_maximum`,
`squares_have_a_minimum`); przy wielu kombinacjach pomija tylko tę jedną z uwagą
`distribution_left_out`.

### Metoda L-momentów (domyślna)

Parametry dobiera się tak, by L-momenty rozkładu były równe L-momentom próby (Hosking i Wallis 1997).

<!-- spec:fit_l_moments -->

<a id="spec-fit_l_moments"></a>

> **Parametry rozkładu maksimów rocznych metodą L-momentów** · specyfikacja [`fit_l_moments`](../FORMULAS.md#fit_l_moments) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> \tau_3 = \frac{2(1 - 3^{-c})}{1 - 2^{-c}} - 3,\quad \alpha = \frac{\lambda_2 c}{(1 - 2^{-c})\Gamma(1 + c)},\quad \xi = \lambda_1 - \alpha\frac{1 - \Gamma(1 + c)}{c};\qquad s = 2\,\mathrm{erf}^{-1}\frac{\lambda_2}{\lambda_1};\qquad \sigma = \lambda_2\sqrt{\pi a}\,\frac{\Gamma(a)}{\Gamma(a + 1/2)},\ G = \frac{2\,\mathrm{sign}\,\tau_3}{\sqrt{a}}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) |
> | $\xi$ | `loc` | Parametr położenia: 0 dla rozkładu logarytmiczno-normalnego, średnia rozkładu Pearsona III, dolne ograniczenie rozkładu Weibulla | m³/s | (−∞; ∞) |
> | $\alpha$ | `scale` | Parametr skali; wartość, która uległaby niedomiarowi, zastępuje się najmniejszą liczbą float64 (tolerancja brzegowa) | m³/s | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 3 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | min(x) > 0 dla rozkładu logarytmiczno-normalnego (parametr położenia 0) | `positive_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | l2 < l1 (rozkład logarytmiczno-normalny); -1 < t3 < 1 (GEV, Pearson III); -0,1699 < t3 < 1 (Weibull) | `l_moments_within_distribution` | odmowa obliczeń: wzór jest nieokreślony | (źr. 1) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $A_1$ | `a1` | Współczynnik liniowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | 0,2906 | – | (źr. 1) |
> | $A_2$ | `a2` | Współczynnik kwadratowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | 0,1882 | – | (źr. 1) |
> | $A_3$ | `a3` | Współczynnik sześcienny mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | 0,0442 | – | (źr. 1) |
> | $B_1$ | `b1` | Współczynnik liniowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | 0,36067 | – | (źr. 1) |
> | $B_2$ | `b2` | Współczynnik kwadratowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | −0,59567 | – | (źr. 1) |
> | $B_3$ | `b3` | Współczynnik sześcienny licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | 0,25361 | – | (źr. 1) |
> | $C_1$ | `b4` | Współczynnik liniowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | −2,78861 | – | (źr. 1) |
> | $C_2$ | `b5` | Współczynnik kwadratowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | 2,56096 | – | (źr. 1) |
> | $C_3$ | `b6` | Współczynnik sześcienny mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | −0,77045 | – | (źr. 1) |
> | $\tau_{3,0}$ | `normal_below` | Wartość bezwzględna L-skośności, poniżej której rozkład Pearsona III przyjmuje się za normalny | 1·10⁻⁶ | – | (źr. 1) |
> | $\tau_{3,G}$ | `gumbel_l_skewness` | L-skośność rozkładu Gumbela, granica zanegowanej L-skośności przy dopasowaniu rozkładu Weibulla | 0,1699250014423126 | – | (źr. 8) |
>
> **Konwencje**
>
> - nieobciążone L-momenty próby ze wzoru `sample_l_moments`
> - parametry w konwencji scipy: parametr kształtu c rozkładu GEV to k Hoskinga i -xi Colesa; parametry (loc, scale, shape) rozkładu Pearsona III to jego średnia, odchylenie standardowe i skośność; rozkład logarytmiczno-normalny ma parametr położenia 0
> - parametr kształtu GEV wyznaczany dokładnie metodą brentq w przedziale -1 < c <= 50 (funkcja pelgev pakietu lmom używa przybliżenia Donaldsona, zgodnego z nim z dokładnością do 2e-7); t3 poza L-skośnością odpowiadającą końcowi tego przedziału daje ten koniec
> - rozkład Weibulla jako GEV zanegowanych L-momentów, jak w funkcji pelwei pakietu lmom
>
> **Założenia**
>
> - maksima roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: estymator daje rozkład o L-momentach próby; Hosking i Wallis (1997) podają jego efektywność dla prób symulowanych
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments <https://cran.r-project.org/package=lmom>
> 2. Hosking, J.R.M. and Wallis, J.R. (1997). Regional Frequency Analysis: An Approach Based on L-Moments. Cambridge University Press, appendix A.5 (GEV), A.8 (log-normal), A.9 (Pearson type III, the rational approximations of alpha from \|t3\|) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Hosking, J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of order statistics. Journal of the Royal Statistical Society, Series B 52(1), 105-124, sect. 2: probability-weighted moments and the sample L-moments of their unbiased estimators — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), samlmu: t3 needs 3 values <https://cran.r-project.org/package=lmom>
> 6. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelgev, pelpe3: l2 must be positive <https://cran.r-project.org/package=lmom>
> 7. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 <https://cran.r-project.org/package=lmom>
> 8. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelwei: the GEV of the negated L-moments, which needs -t3 below the Gumbel's L-skewness 2 ln 3 / ln 2 - 3 = 0.1699 <https://cran.r-project.org/package=lmom>
>
> Funkcja `hydrolog.statistics.frequency.fit_l_moments`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fit_l_moments -->

Metoda jest odporna na pojedyncze skrajne wartości i stabilna w krótkich ciągach, dlatego jest domyślna.
Nie występuje w metodyce KZGW (2017). Jej słabość: dopasowany rozkład z dolnym ograniczeniem (Pearson III,
Weibull) może zostawić najmniejsze maksima poza nośnikiem (ang. *support*), czyli przypisać im zerową
gęstość; Hydrolog sygnalizuje to uwagą `outside_support` (p. 7.7).

### Metoda momentów

W metodzie momentów (ang. *method of moments*) średnia, odchylenie standardowe i skośność rozkładu są
równe tym z próby.

<!-- spec:fit_moments -->

<a id="spec-fit_moments"></a>

> **Parametry rozkładu maksimów rocznych metodą momentów** · specyfikacja [`fit_moments`](../FORMULAS.md#fit_moments) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \sigma_l = \sqrt{\ln(1 + C_v^2)},\ e^{\mu} = \frac{\bar{x}}{\sqrt{1 + C_v^2}};\qquad (\gamma, \mu, \sigma) = (G, \bar{x}, s);\qquad \gamma_{GEV}(c) = G,\ \alpha = \frac{s}{\sigma_{GEV}(c)},\ \xi = \bar{x} - \alpha\,\mu_{GEV}(c)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) |
> | $\xi$ | `loc` | Parametr położenia: 0 dla rozkładu logarytmiczno-normalnego, średnia rozkładu Pearsona III, dolne ograniczenie rozkładu Weibulla | m³/s | (−∞; ∞) |
> | $\alpha$ | `scale` | Parametr skali; wartość, która uległaby niedomiarowi, zastępuje się najmniejszą liczbą float64 (tolerancja brzegowa) | m³/s | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 3 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | min(x) > 0 dla rozkładu logarytmiczno-normalnego (parametr położenia 0) | `positive_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | G > -1,1395 dla rozkładu Weibulla — skośność odwróconego rozkładu Gumbela | `skewness_within_distribution` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $\gamma_G$ | `gumbel_skewness` | Skośność rozkładu Gumbela | 1,1395470994046488 | – | (źr. 8) |
>
> **Konwencje**
>
> - momenty próby ze wzoru `sample_moments`: s z dzielnikiem n - 1, G — skorygowany współczynnik Fishera–Pearsona
> - rozkład logarytmiczno-normalny o parametrze położenia 0 ze średniej i Cv samych wartości, a nie ich logarytmów
> - parametry w konwencji scipy: parametr kształtu c rozkładu GEV to k Hoskinga i -xi Colesa; parametry (loc, scale, shape) rozkładu Pearsona III to jego średnia, odchylenie standardowe i skośność
> - parametr kształtu GEV wyznaczany metodą brentq w przedziale -1/3 < c <= 50 (skośność istnieje powyżej -1/3); rozkład Weibulla jako GEV zanegowanych momentów, z c w przedziale 0 < c <= 50
>
> **Założenia**
>
> - maksima roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: estymator daje rozkład o momentach próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, pp. 9-10 and appendix 12, example 1: the log-Pearson type III distribution of the mean, standard deviation and skewness of the logarithms (eqs. 2, 3a, 4a) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 2. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5 and table II.5.2, pp. II.5-5 to II.5-12: the method of moments and the moments of the GEV, log-normal, Pearson type III and Weibull distributions <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 3. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by (N - 1)(N - 2) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 6. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by S cubed, 0 for equal values <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 7. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 <https://cran.r-project.org/package=lmom>
> 8. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
>
> Funkcja `hydrolog.statistics.frequency.fit_moments`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fit_moments -->

Dla rozkładu Pearsona III to wprost trzy momenty próby. Skośność próby jest silnie obciążona
w krótkich ciągach (p. 7.4), a WMO (2009, § 5.3.3) ostrzega, że momenty mogą dać granicę rozkładu
sprzeczną z obserwacjami.

### Metoda największej wiarygodności (MNW)

Parametry maksymalizują logarytm funkcji wiarygodności (ang. *maximum likelihood*).

<!-- spec:fit_maximum_likelihood -->

<a id="spec-fit_maximum_likelihood"></a>

> **Parametry rozkładu maksimów rocznych metodą największej wiarygodności** · specyfikacja [`fit_maximum_likelihood`](../FORMULAS.md#fit_maximum_likelihood) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> (\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\max \sum_i \ln f(x_i; k, \xi, \alpha);\qquad \hat{\mu} = \frac{1}{n}\sum_i \ln x_i,\ \hat{s}^2 = \frac{1}{n}\sum_i (\ln x_i - \hat{\mu})^2
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) |
> | $\xi$ | `loc` | Parametr położenia: 0 dla rozkładu logarytmiczno-normalnego, średnia rozkładu Pearsona III, dolne ograniczenie rozkładu Weibulla | m³/s | (−∞; ∞) |
> | $\alpha$ | `scale` | Parametr skali; wartość, która uległaby niedomiarowi, zastępuje się najmniejszą liczbą float64 (tolerancja brzegowa) | m³/s | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n > p, liczba parametrów: n >= 3 dla rozkładu logarytmiczno-normalnego, n >= 4 dla pozostałych | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | min(x) > 0 dla rozkładu logarytmiczno-normalnego (parametr położenia 0) | `positive_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | wiarygodność ma maksimum wewnątrz przeszukiwanego zakresu parametru kształtu: poszukiwanie nie kończy się bliżej niż 1e-3 od kształtów, przy których gęstość jest nieskończona na granicy nośnika (GEV c >= 1, Pearson III \|G\| >= 2, kształt Weibulla <= 1), ani od GEV c = -1 (brak średniej) lub kształtu Weibulla 50, ani przy parametrze skali równym milionowej części odchylenia standardowego; przy GEV najwyżej połowa wartości to wartości wiązane równe najmniejszej; poszukiwanie się stabilizuje | `likelihood_has_a_maximum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Konwencje**
>
> - gęstości i parametry w konwencji scipy: parametr kształtu c rozkładu GEV to -xi Colesa (evd, extRemes, ismev)
> - poszukiwanie prowadzi się na próbie standaryzowanej (x / 2**e - mean) / sd, startując z oszacowania metodą L-momentów; metodę Neldera–Meada (xatol 1e-10, fatol 1e-12) uruchamia się ponownie od jej punktu końcowego, aż przebieg zwiększy logarytm wiarygodności najwyżej o 1e-9, przy najwyżej 21 przebiegach
> - rozkład logarytmiczno-normalny o parametrze położenia 0 w postaci jawnej (lognorm.fit biblioteki scipy z floc=0)
>
> **Założenia**
>
> - maksima roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: estymator daje najbardziej wiarygodny rozkład dla próby
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer, sect. 3.3.2 (the likelihood of the GEV) and 3.4.1 (Port Pirie) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the likelihood of a three-parameter distribution has no maximum where its density is infinite at the bound of its support — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5, p. II.5-11: the method of maximum likelihood; sect. 5.3.2.3: the Weibull density goes to infinity at its bound for k < 1 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, n values fit n parameters exactly, where the likelihood has no maximum — *źródło niedostępne publicznie (dostarczone przez autora)*
> 6. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5: the likelihood of values all equal grows without limit as the scale falls to 0 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 7. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 <https://cran.r-project.org/package=lmom>
> 8. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the bound placed at the closest value makes the likelihood grow without limit — *źródło niedostępne publicznie (dostarczone przez autora)*
>
> Funkcja `hydrolog.statistics.frequency.fit_maximum_likelihood`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fit_maximum_likelihood -->

Dla rozkładów trójparametrowych z ograniczonym nośnikiem wiarygodność może rosnąć bez końca, gdy granica
nośnika zbliża się do najbliższej obserwacji, a gęstość na granicy jest nieskończona (Smith 1985). Tak
jest dla GEV, Pearsona III i Weibulla przy kształtach podanych w warunku `likelihood_has_a_maximum`.
Program, który mimo to zwraca „maksimum”, podaje punkt przy osobliwości: dolne ograniczenie równe
najmniejszemu maksimum, często z najmniejszym AIC ze wszystkich dopasowań. Hydrolog takiego dopasowania
nie zwraca (błąd `precondition_failed` albo uwaga `distribution_left_out` z przyczyną
`unbounded_likelihood`). W wersjach do 0.8.1 włącznie metoda `mle` korzystała z domyślnej optymalizacji
SciPy, która dla maksimów rzędu setek m³/s często zatrzymywała się daleko od maksimum wiarygodności
i dawała absurdalnie duże kwantyle rzadkich przepływów; wyniki tej metody z tamtych wersji należy
przeliczyć.

Metodyka KZGW (2017) szacuje rozkład Pearsona III warunkową MNW: dolne ograniczenie odczytuje się
graficznie z krzywej empirycznej, a pozostałe dwa parametry oblicza ze wzorów przybliżonych. Tego
wariantu, podobnie jak historycznej metody kwantyli (decyli) instrukcji CUGW z 1968 r., którą KZGW
dopuszcza w uzasadnionych przypadkach, Hydrolog nie ma.

### Metoda najmniejszych kwadratów (MNK)

Metoda najmniejszych kwadratów (ang. *least squares*) dobiera parametry tak, by suma kwadratów różnic
między uporządkowanymi maksimami a kwantylami rozkładu w pozycjach Weibulla była najmniejsza.

<!-- spec:fit_least_squares -->

<a id="spec-fit_least_squares"></a>

> **Parametry rozkładu maksimów rocznych metodą najmniejszych kwadratów na pozycjach wykreślnych** · specyfikacja [`fit_least_squares`](../FORMULAS.md#fit_least_squares) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> (\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\min \sum_{j=1}^{n}\left(x_{(j)} - Q\left(\frac{j}{n + 1}; k, \xi, \alpha\right)\right)^2
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 3) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) |
> | $\xi$ | `loc` | Parametr położenia: 0 dla rozkładu logarytmiczno-normalnego, średnia rozkładu Pearsona III, dolne ograniczenie rozkładu Weibulla | m³/s | (−∞; ∞) |
> | $\alpha$ | `scale` | Parametr skali; wartość, która uległaby niedomiarowi, zastępuje się najmniejszą liczbą float64 (tolerancja brzegowa) | m³/s | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n >= 3 | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 4) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | min(x) > 0 dla rozkładu logarytmiczno-normalnego (parametr położenia 0) | `positive_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
> | G > -1,1395 dla rozkładu Weibulla: poszukiwanie startuje z oszacowania metodą momentów | `skewness_within_distribution` | odmowa obliczeń: wzór jest nieokreślony | (źr. 7) |
> | suma kwadratów ma minimum wewnątrz przeszukiwanych kształtów (logarytmiczno-normalny s < 5, GEV -1 < c < 50, Pearson III \|G\| < 9, kształt Weibulla < 50), na którym poszukiwanie się stabilizuje | `squares_have_a_minimum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $\gamma_G$ | `gumbel_skewness` | Skośność rozkładu Gumbela | 1,1395470994046488 | – | (źr. 7) |
>
> **Konwencje**
>
> - pozycje wykreślne Weibulla j / (n + 1) próby uporządkowanej rosnąco, reszty bez wag w jednostce próby
> - parametry w konwencji scipy, jak w `fit_moments`
> - poszukiwanie prowadzi się na próbie standaryzowanej (dla rozkładu logarytmiczno-normalnego o parametrze położenia 0 próbę tylko dzieli się przez jej odchylenie standardowe), startując z oszacowania metodą momentów; metodę Neldera–Meada (xatol 1e-10, fatol 1e-12) uruchamia się ponownie od jej punktu końcowego, aż przebieg poprawi wynik najwyżej o 1e-9, przy najwyżej 21 przebiegach
>
> **Założenia**
>
> - maksima roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: estymator daje rozkład najbliższy naniesionej próbie
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the Weibull plotting position i / (n + 1) of the graphical fit of a distribution to the ordered sample <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 3.7: the empirical probability m / (N + 1) of the ordered annual maxima <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the moments of the start divide by (N - 1)(N - 2) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
> 5. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1: values all equal have no spread to fit <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 6. Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 <https://cran.r-project.org/package=lmom>
> 7. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 8. Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, appendix 3: the frequency factors of Pearson type III, tabulated for skews of -9 to 9 <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
>
> Funkcja `hydrolog.statistics.frequency.fit_least_squares`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:fit_least_squares -->

Różnice są w m³/s, a największe maksima leżą najdalej od siebie, więc to one decydują o dopasowaniu.
Kwantyle rzadkich przepływów z MNK bywają przez to wyraźnie wyższe niż z innych metod (przykład 7.9).

## 7.7. Ocena dopasowania i wybór rozkładu

### Statystyka Andersona–Darlinga $A^2$

Statystyka $A^2$ (ang. *Anderson–Darling*) mierzy odległość dystrybuanty dopasowanej od empirycznej,
z większą wagą w ogonach niż test Kołmogorowa–Smirnowa.

<!-- spec:anderson_darling -->

<a id="spec-anderson_darling"></a>

> **Statystyka A² Andersona–Darlinga dla próby względem dopasowanego rozkładu** · specyfikacja [`anderson_darling`](../FORMULAS.md#anderson_darling) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> A^2 = -n - \sum_{i=1}^{n} \frac{2i - 1}{n}\left[\ln F(x_{(i)}) + \ln\left(1 - F(x_{(n+1-i)})\right)\right]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 4) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) | nie podano w źródłach | [−0,6; 2,7] (źr. 5) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) | nie podano w źródłach | [−1; 35,4] (źr. 5) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1; 37] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $A^2$ | `a_squared` | Statystyka: n razy całka z kwadratu różnicy dystrybuanty empirycznej i dopasowanej, ważona przez 1 / (F (1 - F)) | – | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | shape > 0 dla rozkładu logarytmiczno-normalnego (s) i Weibulla (k) | `shape_of_the_distribution` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 6) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $\epsilon$ | `cdf_clip` | Margines obcięcia dystrybuanty F od zera i od jedności | 1·10⁻¹⁰ | – | (źr. 7) |
>
> **Konwencje**
>
> - statystyka dla rozkładu zadanego z góry (przypadek 0 u Stephensa 1974), tu liczona przy parametrach oszacowanych z tej samej próby: jej wartości krytyczne nie są wartościami przypadku 0
> - wartości krytyczne, które FloodFrequencyAnalysis podaje dla dopasowania metodą L-momentów, pochodzą z parametrycznego bootstrapu tego dopasowania (ADR-0048): 999 prób po n wartości wylosowanych z niego z ziarnem 20261118, każda dopasowana ponownie metodą L-momentów; dopasowanie inną metodą nie ma wartości krytycznych
> - F obcięte do [cdf_clip, 1 - cdf_clip], więc wartość poza nośnikiem rozkładu dodaje duży skończony składnik zamiast nieskończonego
> - F z scipy.stats przy parametrach jego rozkładów lognorm, genextreme, pearson3 lub weibull_min
> - próba w dowolnej jednostce, w tej samej jednostce loc i scale: A² jest bezwymiarowe
>
> **Zgodność z obserwacjami według źródeł:** brak: miara odległości między próbą a dopasowanym rozkładem
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. NIST/SEMATECH e-Handbook of Statistical Methods (2012), sect. 1.3.5.14, Anderson-Darling test: A² = -N - S, S = sum (2i - 1) / N [ln F(Y_i) + ln(1 - F(Y_(N+1-i)))] of the ordered data <https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm>
> 2. Anderson, T.W. and Darling, D.A. (1954). A test of goodness of fit. Journal of the American Statistical Association 49(268), 765-769, the statistic W_n² and its computing form — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Stephens, M.A. (1974). EDF statistics for goodness of fit and some comparisons. Journal of the American Statistical Association 69(347), 730-737, the computing form of A²; case 0, a distribution given in advance — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 6. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 7. Hydrolog (2026). ADR-0048: Anderson-Darling critical values by a parametric bootstrap, decision 1: A² keeps its form, F clipped to [1e-10, 1 - 1e-10] <https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md>
>
> Funkcja `hydrolog.statistics.frequency.anderson_darling`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:anderson_darling -->

Tablicowe wartości krytyczne $A^2$ (Stephens 1974) dotyczą rozkładu znanego z góry. Gdy parametry
oszacowano z tej samej próby, rozkład dopasowuje się do niej i $A^2$ jest znacznie mniejsze: test
z wartościami tablicowymi prawie nigdy nie odrzuca. Hydrolog nadaje więc każdemu dopasowaniu metodą
L-momentów własne wartości krytyczne z parametrycznego bootstrapu (ang. *parametric bootstrap*; Stute,
González Manteiga i Presedo Quindimil 1993): losuje wiele prób o liczności badanej próby z dopasowanego
rozkładu, każdą dopasowuje ponownie tą samą metodą i za wartości krytyczne bierze kwantyle otrzymanych
$A^2$ (pole `ad_critical_values`, poziomy 15, 10, 5, 2,5 i 1 %). Liczbę prób i ziarno losowania podaje
ramka; wynik jest powtarzalny. Dopasowania innymi metodami wymagają iteracyjnej optymalizacji, więc nie
mają wartości krytycznych (`null`), a ich $A^2$ służy tylko do porównań. Interpretacja: $A^2$ większe od
wartości krytycznej na poziomie 5 % oznacza, że rozkład źle opisuje próbę; $A^2$ mniejsze nie dowodzi, że
rozkład jest właściwy. Gdy próbka bootstrapu wypada poza nośnik swojego dopasowania, jej $A^2$ jest
bardzo duże; dlatego wartości krytyczne rozkładów ograniczonych od dołu (Pearson III, Weibull) bywają
wysokie i test słabo je różnicuje.

### Test Kołmogorowa–Smirnowa

<!-- TODO spec: test Kołmogorowa–Smirnowa rozkładu dopasowanego (scipy.stats.kstest, obliczenie delegowane, CMP-1.2) -->

Hydrolog podaje też statystykę Kołmogorowa–Smirnowa i jej poziom krytyczny (`ks_statistic`,
`ks_p_value`), liczone przez SciPy dla rozkładu o parametrach z próby. Z tego samego powodu co wyżej
poziom krytyczny jest zawyżony, dlatego wynik ma `ks_valid: false` i uwagę `ks_test_approximate`; służy
tylko do orientacji. Test λ-Kołmogorowa z metodyki KZGW (2017) jest inną statystyką (różnice
dystrybuant w pozycjach Weibulla) z inną wartością krytyczną; Hydrolog go nie liczy.

### Kryterium informacyjne Akaikego (AIC)

<!-- spec:akaike_information_criterion -->

<a id="spec-akaike_information_criterion"></a>

> **Kryterium informacyjne Akaikego dla rozkładu dopasowanego do próby** · specyfikacja [`akaike_information_criterion`](../FORMULAS.md#akaike_information_criterion) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> \mathrm{AIC} = 2k - 2\sum_{i=1}^{n} \ln f(x_i; k, \xi, \alpha)
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `annual_maxima` (ciąg) | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 3) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) | nie podano w źródłach | [−0,6; 2,7] (źr. 4) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) | nie podano w źródłach | [−1; 35,4] (źr. 4) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1; 37] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $\mathrm{AIC}$ | `aic` | Kryterium: im mniejsze, tym lepsze dopasowanie przy danej liczbie parametrów | – | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | shape > 0 dla rozkładu logarytmiczno-normalnego (s) i Weibulla (k) | `shape_of_the_distribution` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 5) |
> | ln f(x_i) jest skończony dla każdej wartości, a więc i ich suma: każda wartość leży wewnątrz nośnika rozkładu, gdzie gęstość jest dodatnia i skończona | `values_within_support` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - wiarygodność przy parametrach z metody, która je wyznaczyła, maksymalna tylko w metodzie największej wiarygodności (ADR-0021, pkt 7): ranking według AIC porównuje wiarygodność parametrów każdego dopasowania
> - k to liczba dopasowywanych parametrów: 2 dla rozkładu logarytmiczno-normalnego, którego parametr położenia jest ustalony na 0, 3 dla pozostałych
> - dopasowanie, które pozostawia wartość poza swoim nośnikiem, nie ma skończonego AIC: FloodFrequencyAnalysis nadaje mu nieskończone AIC bez użycia wzoru, z komunikatem `outside_support`, i umieszcza je na ostatnim miejscu
> - ln f z scipy.stats przy parametrach jego rozkładów lognorm, genextreme, pearson3 lub weibull_min, sumowane z dokładnym zaokrągleniem (math.fsum)
> - logarytm naturalny; AIC zależy od jednostki próby
>
> **Zgodność z obserwacjami według źródeł:** brak: kryterium do porównywania dopasowań; według WMO-No. 168 samo nie wystarcza do wyboru jednego z nich
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.3, eq. 5.31, pp. II.5-14 and II.5-15: AIC(f) = -2 log L(theta, x) + 2k, with L the likelihood function and k the number of parameters; alone not appropriate for model selection <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 2. Akaike, H. (1974). A new look at the statistical model identification. IEEE Transactions on Automatic Control 19(6), 716-723, the criterion -2 ln (maximum likelihood) + 2 k — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 6. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.3, eq. 5.31: the logarithm of the likelihood, -inf where a value has no density <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
>
> Funkcja `hydrolog.statistics.frequency.akaike_information_criterion`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:akaike_information_criterion -->

AIC (ang. *Akaike information criterion*) nagradza wiarygodność i karze liczbę parametrów; mniejsze
znaczy lepsze. Znaczenie mają różnice, nie wartości: różnica rzędu 2 i mniejsza nie rozstrzyga
(Burnham i Anderson 2002). Hydrolog liczy AIC w punkcie parametrów danej metody, więc MNW zwykle daje
swojemu rozkładowi najmniejsze AIC spośród metod. Pole `best_distribution` wskazuje dopasowanie
z najmniejszym AIC. Dopasowanie, które zostawia maksimum poza nośnikiem, ma nieskończony logarytm
wiarygodności: jego AIC jest `null`, trafia na koniec rankingu, a uwaga `outside_support` wymienia te
maksima (kwantyle, $A^2$ i statystyka K–S zostają podane).

WMO (2009, § 5.6.3) przestrzega, że samo kryterium Akaikego nie wystarcza do wyboru modelu. W polskiej
praktyce II cyklu planistycznego wybierano nim rozkład spośród dopasowań MNW niesprzecznych z testem
zgodności (IMGW-PIB i in. 2022). Rozsądna kolejność: najpierw odrzucić rozkłady z $A^2$ powyżej wartości
krytycznej i dopasowania z maksimami poza nośnikiem, potem porównać AIC pozostałych, a na końcu
sprawdzić, czy kwantyle rzadkich przepływów są fizycznie wiarygodne.

## 7.8. Przepływ miarodajny i kontrolny, niepewność

Rozporządzenie Ministra Infrastruktury z dnia 4 maja 2026 r. w sprawie warunków technicznych, jakim
powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2026 poz. 692), które zastąpiło
rozporządzenie Ministra Środowiska z 2007 r. (Dz.U. 2007 nr 86 poz. 579), określa w załączniku nr 3
prawdopodobieństwo przewyższenia przepływów miarodajnych $Q_m$ (ang. *design flood*; projektowanie)
i kontrolnych $Q_k$ (ang. *check flood*; sprawdzenie bezpieczeństwa w wyjątkowym układzie obciążeń) dla
stałych budowli hydrotechnicznych:

| Rodzaj budowli | Przepływ | Klasa I | Klasa II | Klasa III | Klasa IV |
|---|---|---|---|---|---|
| posadowione na podłożu łatwo rozmywalnym oraz budowle ziemne (bez wałów przeciwpowodziowych) | $Q_m$ | 0,1 % | 0,3 % | 0,5 % | 1,0 % |
| | $Q_k$ | 0,02 % | 0,05 % | 0,2 % | 0,5 % |
| pozostałe, w tym wały przeciwpowodziowe | $Q_m$ | 0,5 % | 1,0 % | 2,0 % | 3,0 % |
| | $Q_k$ | 0,1 % | 0,3 % | 0,5 % | 1,0 % |

Dla rzek i potoków górskich i podgórskich do przepływu kontrolnego dodaje się średni błąd jego
oszacowania $\delta$ przy poziomie ufności 0,84 i do wymiarowania przyjmuje $(1 + \delta)Q_k$
(objaśnienie 3 załącznika). Metodyka KZGW (2017) wyznacza w tym celu górną granicę jednostronnego
przedziału ufności kwantyla na poziomie $\beta$ = 84 %. Hydrolog podaje przedział ufności każdego
kwantyla (pole `intervals`, opcja `--confidence-level`, domyślnie 0,95). Przedział jest dwustronny
i centralny, więc **jego górna granica przy poziomie 0,68 jest jednostronną górną granicą 84 % według
KZGW** ($c = 2\beta - 1$). Dla dopasowania metodą największej wiarygodności Hydrolog liczy ją regułą
KZGW (metoda delta), dla dopasowania metodą L-momentów z bootstrapu parametrycznego: to ta sama
jednostronna granica 84 %, wyznaczona inną metodą. $(1 + \delta)Q_k$ to więc górna granica
przedziału kwantyla $Q_k$ przy poziomie 0,68 (`--confidence-level 0.68` albo `0.95,0.68`).

Prawdopodobieństwa z tabeli odpowiadają okresom powtarzalności od kilkudziesięciu do kilku tysięcy lat,
daleko poza długością obserwacji. W tym zakresie różnice między rozkładami i metodami są największe,
a próba prawie nic o nich nie mówi (przykłady 7.9 i 7.10). Kwantyl $Q_{0{,}1\%}$ z 34 lat danych jest
ekstrapolacją kształtu rozkładu, nie pomiarem.

### Przedział ufności kwantyla

Przedział ufności (ang. *confidence interval*) na poziomie $c$ to przedział wyznaczony metodą, która przy
wielokrotnym powtórzeniu obserwacji tej samej długości obejmowałaby prawdziwy kwantyl w około $c$
przypadków. Hydrolog liczy go na każdym poziomie podanym w `--confidence-level` (jedna liczba albo lista
różnych liczb, np. `0.95,0.68`); wszystkie poziomy jednego dopasowania pochodzą z jednego obliczenia,
a wynik ma jeden wpis na poziom, w podanej kolejności (`confidence_level`, `ci_method`, `ci_lower`,
`ci_upper`, `ci_samples`). Metoda zależy od metody estymacji parametrów (p. 7.6):

- **L-momenty** (domyślne): przedział percentylowy bootstrapu parametrycznego (Efron i Tibshirani 1993).
  Próby losowane z dopasowanego rozkładu i dopasowywane ponownie są tymi samymi, z których pochodzą
  wartości krytyczne $A^2$ (p. 7.7); granicami są kwantyle empiryczne kwantyli tych dopasowań. Liczbę
  prób, ziarno i regułę kwantyla empirycznego podaje ramka, a `ci_samples` mówi, ile prób dało się
  dopasować ponownie.
- **MNW**: metoda delta w postaci KZGW (2017), $Q_T \mp z\,\sigma_T$ z $z = \Phi^{-1}((1 + c)/2)$, gdzie
  $\sigma_T$ wynika z informacji oczekiwanej dwóch parametrów przy ustalonej granicy nośnika (rozkłady
  Pearsona III, Weibulla i logarytmiczno-normalny) albo z informacji obserwowanej trzech parametrów (GEV).
  Dla GEV z $c \ge 0{,}5$ ($\xi \le -0{,}5$) wiarygodność nie jest regularna i przedziału nie ma (uwaga
  `interval_not_computed`, przyczyna `nonregular_fit`).
- **Momenty i MNK**: przedziału nie ma (przyczyna `fit_method`): bootstrap tych metod, które wymagają
  iteracyjnej optymalizacji, trwałby minuty.

Granica przedziału przepływu lub opadu, która wypadłaby poniżej zera, jest pusta (`null`, przyczyna
`below_physical_range`); stan wody zachowuje każdą granicę. Metoda delta jest przybliżeniem
asymptotycznym: przy 30–60 latach rzeczywiste pokrycie jej przedziału bywa niższe od $c$, zwłaszcza dla
długich okresów powtarzalności. Pokrycie obu metod, symulowane przy 30 i 60 wartościach, podaje
`docs/FORMULAS.md` pod każdym wzorem. Przedział opisuje niepewność parametrów przyjętego rozkładu, a nie
niepewność wyboru rozkładu, która dla długich $T$ bywa większa (p. 7.9).

<!-- spec:quantile_interval_bootstrap -->

<a id="spec-quantile_interval_bootstrap"></a>

> **Przedział ufności kwantyli dopasowania metodą L-momentów z bootstrapu parametrycznego (przedział percentylowy)** · specyfikacja [`quantile_interval_bootstrap`](../FORMULAS.md#quantile_interval_bootstrap) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> \hat{Q}^{*}_{b}(T) = F^{-1}\left(1 - \tfrac{1}{T};\ \hat\theta^{*}_{b}\right),\ b = 1 \dots K;\qquad [L, U] = \left[\hat{Q}^{*}_{((K + 1)(1 - c)/2)},\ \hat{Q}^{*}_{((K + 1)(1 + c)/2)}\right]
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) | nie podano w źródłach | [−0,6; 2,7] (źr. 6) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) | nie podano w źródłach | [−1; 35,4] (źr. 6) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1; 37] (źr. 6) |
> | $n$ | `size` (liczba całkowita) | Liczba wartości próby, do której dopasowano rozkład | – | [1; ∞) | nie podano w źródłach | [30; 60] (źr. 7) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 8) |
> | $c$ | `confidence_levels` (ciąg) | Poziomy ufności, różne: każdy przedział jest dwustronny i centralny, każdy ogon (1 - c) / 2 | – | (0; 1) | nie podano w źródłach | [0,68; 0,95] (źr. 9) |
> | $v$ | `variable` (wybór) | Rodzaj ekstremów: przepływ albo inna wielkość nigdy poniżej 0, np. wysokość opadu, albo stan wody, którego 0 jest zerem wodowskazu | – | jedna z: `discharge`, `stage` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $L$ | `lower` (ciąg) | Dolna granica dla każdego poziomu (wiersz na poziom, w podanej kolejności) i okresu powtarzalności; luka tam, gdzie granica przepływu byłaby poniżej 0 | m³/s | (−∞; ∞) |
> | $U$ | `upper` (ciąg) | Górna granica, jak dolna | m³/s | (−∞; ∞) |
> | $K$ | `samples` (liczba całkowita) | Zachowane próby bootstrapu: dopasowane ponownie metodą L-momentów | – | [990; 999] |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | shape > 0 dla rozkładu logarytmiczno-normalnego (s) i Weibulla (k) | `shape_of_the_distribution` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 10) |
> | n >= 3: L-skośność próby wymaga 3 wartości | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 2) |
> | poziomy ufności są różne | `distinct_levels` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
> | co najmniej K_min = 990 z B = 999 prób daje się dopasować ponownie metodą L-momentów | `enough_refits` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $B$ | `samples` | Liczba prób bootstrapu | 999 | – | (źr. 5) |
> | $s$ | `seed` | Ziarno generatora liczb losowych | 20 261 118 | – | (źr. 5) |
> | $K_{min}$ | `least_kept` | Najmniejsza liczba zachowanych prób, przy której przedział jest wyznaczany | 990 | – | (źr. 11) |
>
> **Konwencje**
>
> - dwustronny i centralny przy każdym poziomie ufności c, każdy ogon (1 - c) / 2; górna granica przy c = 0,68 to jednostronna górna granica KZGW przy beta = 84 % (c = 2 beta - 1); wszystkie poziomy jednego wywołania z jednego obliczenia
> - bootstrap parametryczny, przedział percentylowy Efrona i Tibshiraniego (1993, rozdz. 13): B = 999 prób po n wartości z dopasowanego rozkładu, default_rng biblioteki numpy z ziarnem 20261118, te same próby i ponowne dopasowania co wartości krytyczne A² dopasowania (ADR-0048)
> - kwantyl empiryczny typu 6 Hyndmana i Fana (1996), pozycje i / (K + 1): metoda 'weibull' biblioteki numpy, typ 6 funkcji quantile w R (empiryczne granice lmomco); przy K = 999 granice przy c = 0,95 to 25. ponowne dopasowanie od każdego końca, a przy 0,68 — 160., wartość ((B + 1) alfa)-ta Efrona i Tibshiraniego; poziom poza zasięgiem K dopasowań, (K + 1)(1 - c) / 2 < 1, przyjmuje najmniejsze i największe
> - próbę, której L-momentów rozkład nie może przyjąć, pomija się, a nie losuje ponownie (qua2ci.simple pakietu lmomco losuje ponownie), i liczy: samples to liczba K zachowanych; mniej niż 990 oznacza odmowę (enough_refits)
> - ponowne dopasowania funkcją fit_l_moments, kwantyle z isf biblioteki scipy przy prawdopodobieństwie przewyższenia 1/T, jak w specyfikacjach kwantyli; parametry w konwencji scipy (c rozkładu GEV to -xi Colesa)
> - variable discharge (przepływ albo inna wielkość nigdy poniżej 0, np. wysokość opadu): granica poniżej 0 jest luką, z komunikatem interval_not_computed (below_physical_range), który podaje jej okresy powtarzalności i poziomy; stage: bez tej reguły
>
> **Założenia**
>
> - dopasowany rozkład zastępuje rozkład populacji: przedział to rozrzut estymatora L-momentów w próbach po n wartości z tego rozkładu
> - ekstrema roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: przedział estymatora; jego pokrycie, symulowane z rozkładów, które dopasowuje, przy 30 i 60 wartościach, podaje się pod wzorem (CMP-6.11)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Efron, B. and Tibshirani, R.J. (1993). An Introduction to the Bootstrap. Chapman and Hall, ch. 6 (the parametric bootstrap), ch. 13 (the percentile interval, the empirical (B + 1) alpha-th value of the B replications) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 2. Hosking, J.R.M. and Wallis, J.R. (1997). Regional Frequency Analysis: An Approach Based on L-Moments. Cambridge University Press, appendix A.5 (GEV), A.8 (log-normal), A.9 (Pearson type III, the rational approximations of alpha from \|t3\|) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 3. Kyselý, J. (2008). A cautionary note on the use of nonparametric bootstrap for estimating uncertainties in extreme-value models. Journal of Applied Meteorology and Climatology 47, 3236-3251, the parametric bootstrap before the nonparametric one for short samples of extremes <https://doi.org/10.1175/2008JAMC1763.1> — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. R Core Team. R: A Language and Environment for Statistical Computing, stats::quantile, Sample Quantiles (Hyndman and Fan 1996, types 1 to 9), type 6: m = p, p_k = k / (n + 1), the plotting position of Weibull <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/quantile.html>
> 5. Hydrolog (2026). ADR-0048: Anderson-Darling critical values by a parametric bootstrap, decision 1: 999 samples of n values drawn from the fitted distribution, each refitted by the same method, seed 20261118; a sample the method cannot fit is left out <https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md>
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Nogat (2026). Computations: formulas, their limits and their verification, standard 1.3, CMP-6.11: the sample sizes of the ecosystem's use, 30 and 60 values for annual series <https://github.com/Daldek/Nogat/blob/main/standards/COMPUTATIONS.md>
> 8. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
> 9. Nogat (2026). Decisions of the ecosystem, ECO-091: Intervals beside point estimates, computed by Hydrolog, shown by Obserwator, two-sided and central at each confidence_level asked; Obserwator stores 0.95 and 0.68 <https://github.com/Daldek/Nogat/blob/main/standards/DECISIONS.md>
> 10. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 11. Hydrolog (2026). ADR-0074: Intervals of the quantiles and of the median annual flow-duration curve, decisions 1 and 2: the refits of ADR-0048 give the percentile interval, fewer than 990 kept give none; the delta method of KZGW for maximum likelihood <https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/0074-intervals-of-the-quantiles-and-of-the-median-annual-flow-duration-curve.md>
>
> Funkcja `hydrolog.statistics.intervals.quantile_interval_bootstrap`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:quantile_interval_bootstrap -->

<!-- spec:quantile_interval_delta -->

<a id="spec-quantile_interval_delta"></a>

> **Przedział ufności kwantyli dopasowania metodą największej wiarygodności, wyznaczany metodą delta (KZGW 2017)** · specyfikacja [`quantile_interval_delta`](../FORMULAS.md#quantile_interval_delta) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_T \mp z\,\sigma_T,\quad z = \Phi^{-1}\left(\tfrac{1 + c}{2}\right);\quad\sigma_T^2 = \frac{\varphi^2(p, \lambda)}{\alpha^2 N},\ \varphi^2 = \frac{\lambda t'^2 - 2 t' t + \psi'(\lambda) t^2}{\lambda\psi'(\lambda) - 1};\quad \sigma_T = \frac{Q_T - \varepsilon}{k\sqrt{N}}\sqrt{1 + \frac{(\Gamma'(2) - \ln(-\ln p))^2}{\pi^2/6}};\quad \varepsilon + (Q_T - \varepsilon)\,e^{\mp z \frac{s}{\sqrt{N}}\sqrt{1 + u_p^2/2}};\quad \sigma_T^2 = \nabla Q_T^{\top} I_o^{-1} \nabla Q_T
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $x_i$ | `values` (ciąg) | Próba, do której dopasowano rozkład metodą największej wiarygodności: maksima roczne albo minima roczne (extremes minima) | m³/s | (−∞; ∞) | nie podano w źródłach | [0,81; 111] (źr. 5) |
> | $F$ | `distribution` (wybór) | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | jedna z: `log_normal`, `gev`, `pearson3`, `weibull` | – | – |
> | $k$ | `shape` | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | (−∞; ∞) | nie podano w źródłach | [−0,6; 2,7] (źr. 6) |
> | $\xi$ | `loc` | Parametr położenia | m³/s | (−∞; ∞) | nie podano w źródłach | [−1; 35,4] (źr. 6) |
> | $\alpha$ | `scale` | Parametr skali | m³/s | (0; ∞) | nie podano w źródłach | [1; 37] (źr. 6) |
> | $T$ | `return_periods_years` (ciąg) | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | (1; ∞) | nie podano w źródłach | [2; 5000] (źr. 7) |
> | $c$ | `confidence_levels` (ciąg) | Poziomy ufności, różne: każdy przedział jest dwustronny i centralny, każdy ogon (1 - c) / 2 | – | (0; 1) | nie podano w źródłach | [0,68; 0,95] (źr. 8) |
> | $v$ | `variable` (wybór) | Rodzaj ekstremów: przepływ albo inna wielkość nigdy poniżej 0, np. wysokość opadu, albo stan wody, którego 0 jest zerem wodowskazu | – | jedna z: `discharge`, `stage` | – | – |
> | $e$ | `extremes` (wybór) | Maksima albo minima dopasowane jako rozkład GEV zanegowanych minimów (fisher_tippett_minima: jego parametr położenia odnosi się do minimów) | – | jedna z: `maxima`, `minima` | – | – |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $L$ | `lower` (ciąg) | Dolna granica dla każdego poziomu (wiersz na poziom, w podanej kolejności) i okresu powtarzalności; luka tam, gdzie granica przepływu byłaby poniżej 0 | m³/s | (−∞; ∞) |
> | $U$ | `upper` (ciąg) | Górna granica, jak dolna | m³/s | (−∞; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | shape > 0 dla rozkładu logarytmiczno-normalnego (s) i Weibulla (k) | `shape_of_the_distribution` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 9) |
> | N > p, liczba parametrów dopasowania: N >= 3 dla rozkładu logarytmiczno-normalnego, N >= 4 dla pozostałych | `enough_values` | odmowa obliczeń: wzór jest nieokreślony | (źr. 10) |
> | min(x) < max(x) | `values_not_all_equal` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
> | kształty, przy których poszukiwanie fit_maximum_likelihood znajduje maksimum: GEV -1 < c < 1, Pearson III \|G\| < 2, Weibull 1 < k < 50 | `shape_of_a_likelihood_maximum` | odmowa obliczeń: wzór jest nieokreślony | (źr. 12) |
> | minima tylko jako rozkład GEV zanegowanych minimów | `minima_of_the_gev` | odmowa obliczeń: wzór jest nieokreślony | (źr. 13) |
> | poziomy ufności są różne | `distinct_levels` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | rozkład GEV regularny w punkcie: c < 0,5 (xi > -0,5) i dodatnio określona macierz informacji obserwowanej | `regular_likelihood` | odmowa obliczeń: wzór jest nieokreślony | (źr. 14) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $\Gamma'(2)$ | `gamma_prime_2` | Wartość pochodnej funkcji gamma w punkcie dwa | 0,42278433509846713 | – | (źr. 1) |
>
> **Konwencje**
>
> - dwustronny i centralny przy każdym poziomie ufności c, każdy ogon (1 - c) / 2; górna granica przy c = 0,68 to jednostronna górna granica KZGW przy beta = 84 % (c = 2 beta - 1); wszystkie poziomy jednego wywołania z jednego obliczenia
> - metoda delta w postaci stosowanej przez KZGW (2017): granica nośnika ustalona na swoim oszacowaniu (loc - 2 scale / G rozkładu Pearsona III, loc rozkładu Weibulla, loc rozkładu logarytmiczno-normalnego, 0 w dopasowaniach Hydrologa) i informacja oczekiwana dwóch pozostałych parametrów w postaci jawnej: dla rozkładu Pearsona III lambda i alfa rozkładu gamma, dla rozkładu Weibulla ln(x - loc) jako rozkładu Gumbela minimów, dla rozkładu logarytmiczno-normalnego średniej i odchylenia standardowego rozkładu normalnego ln(x - loc), z przedziałem wyznaczanym w tej skali; dla GEV informacja obserwowana jego trzech parametrów
> - parametry z fit_maximum_likelihood: s rozkładu logarytmiczno-normalnego z dzielnikiem N (wzór 2.6 KZGW dzieli przez N - 1); N to liczba wartości
> - u_beta = 0,994 KZGW przy beta = 84 % to z przy c = 0,68, bez zaokrąglenia 0,99446
> - wzór 3.27 dla rozkładu Pearsona III przekształcony tak, by uniknąć skracania się wyrazów rzędu lambda przy G -> 0: dK/dG z różnic centralnych pearson3.isf biblioteki scipy względem G, z krokami 1e-3 i 5e-4 połączonymi ekstrapolacją Richardsona, dla \|G\| >= 0,01, a poniżej z rozwinięcia Cornisha–Fishera kwantyla rozkładu gamma do G**3; lambda (lambda psi'(lambda) - 1) z szeregu asymptotycznego powyżej lambda = 10; ujemne G przez rozkład lustrzany, tym samym wyrażeniem
> - wzór 3.57 dla rozkładu Weibulla zastosowany do kwantyla powyżej granicy, Q_T - loc (kwantyla dwuparametrowego, dla którego go wyprowadzono); przykład 3.4 KZGW stosuje go do Q_T (5,24 wobec 4,88 m3/s przy p = 10 %), więc przykład 3.4 nie jest przypadkiem referencyjnym, dopóki nie zostanie przeczytana praca Heo i in. (2001), źródło wzoru 3.57 (CMP-5.2; źródło niedostępne publicznie 2026-11-25)
> - informacja obserwowana rozkładu GEV z różnic centralnych logarytmu wiarygodności próby standaryzowanej (tej, na której szuka fit_maximum_likelihood), z krokami 1e-4 dla c i loc oraz 1e-4 razy scale dla parametru skali, 19 obliczeń; genextreme biblioteki scipy z c = -xi; regularna, gdy c < 0,5, a macierz informacji jest dodatnio określona (Smith 1985), w przeciwnym razie odmowa (regular_likelihood)
> - tam, gdzie KZGW odczytuje granicę z wykresu (przykłady 3.2, 3.4) albo ze swojego wzoru na kwantyl (wzór 3.36), Hydrolog ustala własne oszacowanie; wzory 2.9 i 3.41 KZGW mnożą cały kwantyl jego trójparametrowego rozkładu logarytmiczno-normalnego (granica 19,6 mm w tabeli 2.3, 0,384 m3/s w przykładzie 3.3), a rozkład logarytmiczno-normalny Hydrologa ma granicę 0, przy której oba się zgadzają (przypadki referencyjne przyjmują loc 0 i skalę drukowanego kwantyla)
> - minima (stats low-flow): rozkład GEV zanegowanych minimów z parametrem położenia z fisher_tippett_minima, kwantyl minimów przy prawdopodobieństwie nieprzewyższenia 1/T
> - variable discharge (przepływ albo inna wielkość nigdy poniżej 0, np. wysokość opadu): granica poniżej 0 jest luką, z komunikatem interval_not_computed (below_physical_range), który podaje jej okresy powtarzalności i poziomy; stage: bez tej reguły
>
> **Założenia**
>
> - estymator ma rozkład bliski normalnemu z wariancją z teorii asymptotycznej: przybliżenie dla 30–60 wartości, którego pokrycie się symuluje (CMP-6.11)
> - ekstrema roczne są niezależne i mają jednakowy rozkład
>
> **Zgodność z obserwacjami według źródeł:** brak: przedział estymatora; jego pokrycie, symulowane z rozkładów, które dopasowuje, przy 30 i 60 wartościach, podaje się pod wzorem (CMP-6.11)
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 3.26-3.27 and ex. 3.2 (Pearson III), eq. 3.41 and ex. 3.3, eq. 2.9 and table 2.3 (log-normal), eq. 3.56-3.57 and ex. 3.4 (Weibull), pp. 21-55; the upper bound at beta = 84 % with u_beta = 0.994 (eq. 3.12) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Stedinger, J.R., Vogel, R.M. and Foufoula-Georgiou, E. (1993). Frequency analysis of extreme events. In: Maidment, D.R. (ed.), Handbook of Hydrology, ch. 18. McGraw-Hill, sect. 18.4.2, eqs. 18.4.7-18.4.8, p. 18.30: the variance of the log-normal quantile by maximum likelihood (the source of KZGW's eq. 2.9) <https://efi.eng.uci.edu/papers/efg_FA.pdf>
> 3. Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer, sect. 3.3.2-3.3.3: the observed information of the GEV's maximum likelihood, the delta method for return levels, regular for xi > -0.5 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. Heo, J.-H., Salas, J.D. and Kim, K.-D. (2001). Estimation of confidence intervals of quantiles for the Weibull distribution. Stochastic Environmental Research and Risk Assessment 15(4), 284-309, the variance of the Weibull quantile by maximum likelihood (KZGW's eq. 3.57) — *źródło niedostępne publicznie (dostarczone przez autora)*
> 5. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579>
> 8. Nogat (2026). Decisions of the ecosystem, ECO-091: Intervals beside point estimates, computed by Hydrolog, shown by Obserwator, two-sided and central at each confidence_level asked; Obserwator stores 0.95 and 0.68 <https://github.com/Daldek/Nogat/blob/main/standards/DECISIONS.md>
> 9. Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 <https://docs.scipy.org/doc/scipy/reference/stats.html>
> 10. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, n values fit n parameters exactly, where the likelihood has no maximum — *źródło niedostępne publicznie (dostarczone przez autora)*
> 11. WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5: the likelihood of values all equal grows without limit as the scale falls to 0 <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
> 12. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the density infinite at the bound of the support (GEV c >= 1, Pearson III \|G\| >= 2, Weibull k <= 1) leaves the likelihood without a maximum — *źródło niedostępne publicznie (dostarczone przez autora)*
> 13. WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5: the GEV of minima, min(x) = -max(-x) <https://library.wmo.int/idurl/4/32176>
> 14. Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the maximum-likelihood estimators of the GEV are regular, with the usual asymptotic normality, for xi > -0.5 — *źródło niedostępne publicznie (dostarczone przez autora)*
>
> Funkcja `hydrolog.statistics.intervals.quantile_interval_delta`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:quantile_interval_delta -->

## 7.9. Przykład: Czarna — Polana (metodyka KZGW 2017, przykład 3.2)

**Dane.** KZGW (2017, przykład 3.2, tab. 3.5) podaje 34 maksima roczne przepływu Czarnej w przekroju
wodowskazu Polana (zlewnia 94,17 km²) z lat hydrologicznych 1972–2005, w m³/s. W poleceniach
podaje się je wprost opcją `--values`, w kolejności lat.

**Trend.** Najpierw test Manna–Kendalla (rozdział 10):

```sh
hydrolog stats mann-kendall --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --years 1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005
```

Statystyka $S = 86$, $Z = 1{,}260$, poziom krytyczny $p = 0{,}208$: brak istotnego trendu na poziomie
0,05 (nachylenie Sena 0,60 m³/s na rok, przedział ufności od −0,30 do 1,35 m³/s na rok obejmuje
zero). KZGW (2017) drukuje $S = 85$; różnica wynika z innego liczenia par wartości równych (rozdział 10).

**Dopasowanie metodą L-momentów** (domyślną), dla prawdopodobieństw przewyższenia z tablicy KZGW:

```sh
hydrolog stats flood-frequency --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --return-periods 2,10,20,50,100,200,1000
```

| Rozkład (L-momenty) | $Q_{50\%}$ [m³/s] | $Q_{10\%}$ [m³/s] | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | $A^2$ | $A^2$ krytyczne 5 % | AIC |
|---|---|---|---|---|---|---|---|
| logarytmiczno-normalny | 25,4 | 67,2 | 148,6 | 265,3 | 0,362 | 0,922 | 303,0 |
| Weibulla | 26,4 | 69,8 | 126,5 | 180,3 | 0,290 | 5,37 | 303,8 |
| Pearsona III | 26,5 | 69,5 | 127,7 | 184,6 | 0,301 | 5,65 | 304,4 |
| GEV | 27,1 | 66,4 | 138,9 | 247,6 | 0,463 | 0,576 | 308,4 |

Żaden rozkład nie jest odrzucony testem $A^2$ na poziomie 5 %. GEV jest najbliżej granicy: jego $A^2$
przekracza wartość krytyczną poziomu 15 % (0,439), ale nie 10 % (0,497). Parametr kształtu GEV,
$c = -0{,}18$, oznacza ciężki ogon. Hydrolog wskazuje jako najlepszy rozkład logarytmiczno-normalny
(najmniejsze AIC, 303,0), lecz trzy pierwsze rozkłady dzielą mniej niż 1,4 jednostki AIC, czyli AIC ich
nie rozróżnia. Kwantyle bliskie środka próby ($Q_{50\%}$, $Q_{10\%}$) zgadzają się w granicach kilku
procent; $Q_{1\%}$ różnią się o 17 %, a $Q_{0{,}1\%}$ o 47 %. Największe maksimum próby, 111 m³/s,
ma prawdopodobieństwo empiryczne 0,0286, czyli okres powtarzalności 35 lat (pole `empirical`).

**Wszystkie metody naraz** (`--fit-method all`, 16 kombinacji w jednym rankingu AIC):

```sh
hydrolog stats flood-frequency --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --fit-method all --return-periods 2,10,20,50,100,200,1000
```

| Rozkład | Metoda | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | AIC |
|---|---|---|---|---|
| Pearsona III | momenty | 117,0 | 162,2 | 309,3 |
| Pearsona III | L-momenty | 127,7 | 184,6 | 304,4 |
| Pearsona III | MNW | 131,3 | 192,0 | 303,0 |
| Pearsona III | MNK | 140,9 | 207,3 | 303,3 |
| GEV | momenty | 117,3 | 169,5 | 311,7 |
| GEV | L-momenty | 138,9 | 247,6 | 308,4 |
| GEV | MNW | 204,2 | 543,1 | 306,7 |
| GEV | MNK | 158,4 | 296,3 | 309,3 |
| logarytmiczno-normalny | MNW | 152,4 | 273,4 | 303,0 |
| Weibulla | MNW | 126,8 | 181,8 | 302,8 |

Najmniejsze AIC całego rankingu ma rozkład Weibulla z MNW (302,8), ale dziewięć kombinacji mieści się
w 2 jednostkach od niego. Ta sama próba daje $Q_{1\%}$ od ok. 117 do 204 m³/s, a $Q_{0{,}1\%}$ od ok. 159
do 543 m³/s (pełny wynik polecenia). Skrajna jest GEV z MNW: parametr kształtu $c = -0{,}41$ (bardzo
ciężki ogon) daje $Q_{0{,}1\%}$ prawie trzy razy większe niż Pearson III, choć różnica AIC jest
niewielka. Momenty dają kwantyle najniższe, MNK — wysokie, zgodnie z p. 7.6.

**Porównanie z metodyką KZGW.** KZGW (2017, tab. 3.9) dopasowuje rozkład Pearsona III warunkową MNW
z dolnym ograniczeniem odczytanym graficznie i otrzymuje $Q_{1\%} = 123{,}2$ m³/s oraz
$Q_{0{,}1\%} = 177{,}1$ m³/s, a jako górne granice jednostronnego przedziału ufności 84 % 144,8 i 210,9 m³/s.
Rozkład Pearsona III z L-momentów daje w Hydrologu kwantyle o ok. 4 % wyższe, z pełnej MNW o 6,5 %
($Q_{1\%}$) i 8,4 % ($Q_{0{,}1\%}$) wyższe, a domyślny „najlepszy” rozkład według AIC (logarytmiczno-normalny
z L-momentów) $Q_{1\%}$ wyższe o 21 %. Jeżeli projekt ma być zgodny z metodyką KZGW, trzeba zastosować jej
procedurę (z graficznym dolnym ograniczeniem); Hydrolog daje wtedy niezależne oszacowanie do porównania.

**Przedziały ufności** rozkładu Pearsona III, na poziomach 0,95 i 0,68:

```sh
hydrolog stats flood-frequency --values 10.2,9.24,58.8,8.23,16.2,4.92,26.8,25.1,97.2,23.5,22.3,21.1,59.9,55.1,16.2,24.6,14.8,73.8,28.9,18.6,18.2,25.8,14.5,11.2,54.5,111,35.1,43,52,45.4,8.9,9.72,57.4,50.8 --distribution pearson3 --fit-method mle --return-periods 2,10,100,1000 --confidence-level 0.95,0.68
```

| Pearson III | | $Q_{50\%}$ [m³/s] | $Q_{10\%}$ [m³/s] | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] |
|---|---|---|---|---|---|
| MNW (metoda delta) | kwantyl | 25,9 | 69,9 | 131,3 | 192,0 |
| | przedział 95 % | 18,5–33,2 | 48,2–91,7 | 83,3–179,2 | 115,7–268,3 |
| | przedział 68 % | 22,1–29,6 | 58,9–80,9 | 106,9–155,6 | 153,2–230,7 |
| L-momenty (bootstrap) | kwantyl | 26,5 | 69,5 | 127,7 | 184,6 |
| | przedział 95 % | 18,9–36,3 | 50,1–91,7 | 81,7–183,7 | 105,7–285,4 |
| | przedział 68 % | 22,6–31,0 | 59,0–80,1 | 100,0–155,7 | 135,8–232,0 |

Górna granica przy 68 % z MNW, 155,6 m³/s dla $Q_{1\%}$ i 230,7 m³/s dla $Q_{0{,}1\%}$, odpowiada górnej
granicy 84 % KZGW (144,8 i 210,9 m³/s). Jest wyższa, bo wyższe są same kwantyle Hydrologa (dolne
ograniczenie z MNW zamiast odczytanego z wykresu), ale zapas nad kwantylem jest podobny: 18,5 % wobec
17,5 % dla $Q_{1\%}$ i 20,2 % wobec 19,1 % dla $Q_{0{,}1\%}$. Bootstrap dopasowania L-momentami (polecenie
bez `--fit-method mle`; 999 z 999 prób dopasowanych ponownie) daje prawie te same górne granice przy 68 %.
Przedział 95 % kwantyla $Q_{0{,}1\%}$ sięga od ok. 106 do 285 m³/s: z 34 lat obserwacji przepływ
tysiącletni jest znany z dokładnością do czynnika bliskiego trzem, i to przy założeniu, że rozkład
Pearsona III jest właściwy.

## 7.10. Przykład: Kaczawa — Świerzawa (IMGW-PIB 151150170), lata 1961–2025

**Dane.** Plik `docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv` zawiera
charakterystyki półroczne przepływu IMGW-PIB wodowskazu Świerzawa na Kaczawie, a plik
`kaczawa_swierzawa_Q_dobowe_1961_2025.csv` przepływy średnie dobowe; oba pochodzą z eksportu
Obserwatora (opis i warunki korzystania: `docs/podrecznik/dane/README.md`). Wszystkie 65 lat
hydrologicznych 1961–2025 są kompletne, łącznie z rokiem 1997.

**Jednorodność i trend** (rozdział 10):

```sh
hydrolog stats homogeneity --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv
```

Ciąg 65 maksimów rocznych podzielony na połowy (1961–1992 i 1993–2025) nie wykazuje różnic: test
Manna–Whitneya $p = 0{,}203$, Kołmogorowa–Smirnowa $p = 0{,}230$; test Pettitta wskazuje najbardziej
prawdopodobną zmianę przed rokiem 1994, ale z $p = 0{,}654$, czyli nieistotną. Test Manna–Kendalla na tych
samych maksimach z latami:

```sh
hydrolog stats mann-kendall --values 17.2,21.5,17.9,114,52.3,11.4,27.5,59.6,15.1,5.96,52.8,16.2,9.58,19.3,18.6,13.8,116,9.06,12.9,15.7,57,13,11.8,10.3,8.61,11.5,16,11.5,7.15,2.32,8.05,7.75,11.2,28.2,13,13.8,152,11.5,31,11.5,106,41,10.4,11.2,31,35,11.4,10,38,24,18.4,115,57.7,36.8,10,14.5,9.3,7.18,15.5,51,30.7,10.7,19,80.5,12.2 --years 1961,1962,1963,1964,1965,1966,1967,1968,1969,1970,1971,1972,1973,1974,1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025
```

daje $S = -38$, $p = 0{,}834$: brak trendu. Ciąg można analizować jako jednorodny.

**Próba.** Maksima roczne IMGW-PIB wynoszą od 2,32 m³/s (1990) do 152 m³/s (1997); kolejne największe to
116 m³/s (1977), 115 m³/s (2012), 114 m³/s (1964) i 106 m³/s (2001). Momenty próby, odczytane
z dopasowania rozkładu Pearsona III metodą momentów (ramka `fit_moments`: parametry to średnia,
odchylenie i skośność próby), to średnia 28,8 m³/s, odchylenie standardowe 31,4 m³/s i skośność 2,24:
kilka wielkich wezbrań na tle wielu małych.

**Dopasowanie metodą L-momentów** (domyślne okresy powtarzalności):

```sh
hydrolog stats flood-frequency --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv
```

| Rozkład (L-momenty) | $Q_{50\%}$ [m³/s] | $Q_{10\%}$ [m³/s] | $Q_{1\%}$ [m³/s] | $Q_{0{,}1\%}$ [m³/s] | $A^2$ | $A^2$ krytyczne 5 % | AIC |
|---|---|---|---|---|---|---|---|
| GEV | 17,9 | 54,7 | 184,9 | 578,2 | 1,19 | 0,868 | 548,0 |
| logarytmiczno-normalny | 18,5 | 61,7 | 164,3 | 336,4 | 1,74 | 1,04 | 552,1 |
| Pearsona III | 15,2 | 66,8 | 166,6 | 276,2 | 11,8 | 70,3 | `null` |
| Weibulla | 16,0 | 64,1 | 175,4 | 324,7 | 5,47 | 31,0 | `null` |

Ten wynik wymaga ostrożności:

- Rozkłady Pearsona III i Weibulla z L-momentów mają dolne ograniczenie powyżej najmniejszych maksimów
  (uwaga `outside_support`: cztery najmniejsze maksima, od 2,32 do 7,18 m³/s, dla rozkładu Weibulla
  i sześć, do 8,05 m³/s, dla rozkładu Pearsona III), więc ich AIC jest `null` i trafiają na koniec
  rankingu.
- GEV ma najmniejsze AIC, ale jego $A^2 = 1{,}19$ przekracza wartość krytyczną poziomu 5 % (0,868) z jego
  własnego bootstrapu; rozkład logarytmiczno-normalny przekracza nawet wartość poziomu 1 % (1,46). Żaden
  z czterech rozkładów nie opisuje tej próby dobrze. Przy takim wyniku warto sprawdzić, czy maksima nie
  pochodzą z wezbrań o różnej genezie (np. roztopowych i opadowych), które należałoby analizować osobno.
- Kształt GEV $c = -0{,}48$ oznacza bardzo ciężki ogon: $Q_{0{,}1\%}$ jest trzykrotnie większe od $Q_{1\%}$
  i ponad dwukrotnie większe niż z rozkładu Pearsona III.

Pełny ranking (`--fit-method all`) dodaje dwie lekcje:

```sh
hydrolog stats flood-frequency --half-year-file docs/podrecznik/dane/kaczawa_swierzawa_Q_polroczne_1961_2025.csv --fit-method all --return-periods 2,10,100,1000
```

Najmniejsze AIC (546,7) ma GEV z MNW, z $Q_{1\%} = 212{,}0$ m³/s i $Q_{0{,}1\%} = 759{,}3$ m³/s. Rozkład
Weibulla z MNW został pominięty (uwaga `distribution_left_out`, przyczyna `unbounded_likelihood`): jego
wiarygodność rośnie bez końca, gdy kształt spada do granicy podanej w ramce `fit_maximum_likelihood`,
a dolne ograniczenie zbliża się do najmniejszego maksimum (Smith 1985), więc maksimum nie istnieje.
Rozkład Pearsona III z MNW ma skośność 1,96, tuż poniżej granicy, i daje $Q_{1\%}$ tylko 121,8 m³/s
przy znacznie gorszym AIC (561,8).

**Maksima dobowe zamiast kulminacji.** To samo dopasowanie z maksimów średnich dobowych:

```sh
hydrolog stats flood-frequency --input-file docs/podrecznik/dane/kaczawa_swierzawa_Q_dobowe_1961_2025.csv --value-column Q --date-column date
```

daje GEV z $Q_{1\%} = 118{,}4$ m³/s zamiast 184,9 m³/s, czyli o 36 % mniej, a największe maksimum dobowe
roku 1997 wynosi 92,7 m³/s wobec 152 m³/s kulminacji. Kwantyle ze średnich dobowych nie zastąpią
kwantyli przepływów kulminacyjnych w małej zlewni. W trzech latach (1992, 1993 i 1995) maksimum półrocza
w danych IMGW-PIB jest nieco mniejsze od największego przepływu dobowego tego roku w danych dobowych —
publiczne dane różnych rodzajów nie zawsze są ze sobą uzgodnione, warto je porównać przed analizą.

**Związek z Kamiennikiem.** Zlewnia Kamiennika (37,22 km²) nie ma wodowskazu, więc jej przepływ
miarodajny wyznacza się z opadu (rozdziały 2–6). Analiza z tego przykładu pokazuje rząd wielkości
i rozrzut kwantyli w tej samej okolicy oraz to, jak mocno kulminacje małej zlewni przewyższają średnie
dobowe.

## 7.11. Podsumowanie: jak czytać wynik

- Sprawdź dane: rok hydrologiczny, kompletność lat, rodzaj maksimów (kulminacje czy średnie dobowe),
  długość ciągu, jednorodność i trend.
- Porównaj kilka rozkładów i metod, nie tylko pole `best_distribution`. Odrzuć dopasowania z $A^2$
  powyżej wartości krytycznej i z maksimami poza nośnikiem.
- Kwantyle dla $T$ wielokrotnie dłuższych od ciągu zależą bardziej od przyjętego rozkładu niż od danych;
  podawaj je z rozkładem, metodą i liczbą lat.
- Podawaj kwantyl z przedziałem ufności (`--confidence-level`); górna granica przy poziomie 0,68 to
  jednostronna górna granica 84 % według KZGW. Przedział nie obejmuje niepewności wyboru rozkładu.
- Hydrolog nie realizuje procedury KZGW 2017 w całości (graficzne dolne ograniczenie, metoda decyli,
  trójparametrowy rozkład logarytmiczno-normalny); wynik zgodny z metodyką trzeba policzyć jej procedurą.

## Źródła

- Akaike H. (1974). A new look at the statistical model identification. *IEEE Transactions on Automatic
  Control* 19(6), 716–723. Niedostępne w otwartym dostępie.
- Burnham K.P., Anderson D.R. (2002). *Model Selection and Multimodel Inference: A Practical
  Information-Theoretic Approach*, wyd. 2. Springer, Nowy Jork. Niedostępne w otwartym dostępie.
- Coles S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer, Londyn.
  Niedostępne w otwartym dostępie.
- Efron B., Tibshirani R.J. (1993). *An Introduction to the Bootstrap*. Chapman and Hall, Nowy Jork.
  Niedostępne w otwartym dostępie.
- Hosking J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of
  order statistics. *Journal of the Royal Statistical Society, Series B* 52(1), 105–124. Niedostępne
  w otwartym dostępie.
- Hosking J.R.M., Wallis J.R. (1997). *Regional Frequency Analysis: An Approach Based on L-Moments*.
  Cambridge University Press. Niedostępne w otwartym dostępie.
- Hosking J.R.M. *lmom: L-moments*, pakiet R, wersja 3.3. https://cran.r-project.org/package=lmom
- IACWD — Interagency Advisory Committee on Water Data (1982). *Guidelines for Determining Flood Flow
  Frequency, Bulletin 17B*. U.S. Geological Survey, Reston.
  https://pubs.usgs.gov/unnumbered/70275162/report.pdf
- IMGW-PIB, Arcadis, Multiconsult (2022). *Raport z opracowania danych hydrologicznych na potrzeby
  modelowania hydraulicznego*, zał. 4 do raportu z przeglądu i aktualizacji map zagrożenia powodziowego
  i map ryzyka powodziowego, wersja 2.00.
  https://powodz.gov.pl/wp-content/uploads/2026/10/aMZPiMRP-Zal4-Raport-HYDROLOGIA-20220907-v2.00-pub.pdf
- IMGW-PIB. Dane publiczne, dane hydrologiczne, opis `hydrologia_info_ogolne.txt` (rok hydrologiczny
  i półrocza). https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych oraz identyfikacji
  modeli transformacji opadu w odpływ* (oprac. K. Banasik, A. Wałęga, S. Węglarczyk, B. Więzik,
  Stowarzyszenie Hydrologów Polskich), załącznik 2 do OPZ, wersja ujednolicona. Krajowy Zarząd Gospodarki
  Wodnej, Warszawa.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- NIST/SEMATECH (2012). *e-Handbook of Statistical Methods*, rozdz. 1.3.5.14 (test Andersona–Darlinga).
  https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm
- Rozporządzenie Ministra Infrastruktury z dnia 4 maja 2026 r. w sprawie warunków technicznych, jakim
  powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2026 poz. 692), załącznik nr 3.
  https://dziennikustaw.gov.pl/D2026000069201.pdf
- Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim
  powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579), uchylone.
- Smith R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. *Biometrika* 72(1),
  67–90. Niedostępne w otwartym dostępie.
- Stephens M.A. (1974). EDF statistics for goodness of fit and some comparisons. *Journal of the American
  Statistical Association* 69(347), 730–737. Niedostępne w otwartym dostępie.
- Stute W., González Manteiga W., Presedo Quindimil M. (1993). Bootstrap based goodness-of-fit-tests.
  *Metrika* 40, 243–256. Skan w bibliotece EuDML: https://eudml.org/doc/176470
- Virtanen P. i in. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python.
  *Nature Methods* 17, 261–272 (`scipy.stats`). https://docs.scipy.org/doc/scipy/reference/stats.html
- Węglarczyk S. (red.) (2013). *Problemy obliczania przepływów ekstremalnych w zlewniach kontrolowanych
  i niekontrolowanych*. Monografie Komitetu Gospodarki Wodnej PAN 35, Warszawa.
  https://kgw.pan.pl/files/35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf
- WMO (2009). *Guide to Hydrological Practices*, wyd. 6, t. II: *Management of Water Resources and
  Application of Hydrological Practices*, WMO-No. 168, rozdz. 5. Genewa.
  https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf

Dane przykładu 7.10: źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej –
Państwowy Instytut Badawczy; dane IMGW-PIB zostały przetworzone (regulamin:
https://danepubliczne.imgw.pl/regulations).
