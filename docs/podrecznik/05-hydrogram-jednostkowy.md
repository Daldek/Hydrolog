# 5. Hydrogram jednostkowy

Rozdział opisuje, jak Hydrolog zamienia opad efektywny w hydrogram odpływu bezpośredniego w
przekroju zamykającym zlewnię. Hydrogram projektowy powstaje w łańcuchu obliczeń:

1. opad projektowy i jego rozkład w czasie, czyli hietogram (rozdz. 2);
2. opad efektywny metodą SCS-CN (rozdz. 3);
3. hydrogram jednostkowy zlewni (ten rozdział; modele SCS i Clarka potrzebują czasu koncentracji
   z rozdz. 4);
4. splot opadu efektywnego z hydrogramem jednostkowym i kontrola bilansu objętości (ten rozdział);
5. w razie potrzeby transformacja fali w korycie lub w zbiorniku poniżej przekroju (rozdz. 6).

Przykładem przewodnim jest zlewnia Kamiennika po przekrój w Świerzawie, 37,22 km². Jej
charakterystyki (rozdz. 1) zapisano w pliku `tests/fixtures/kamiennik.json` repozytorium Hydrologa;
polecenia z przykładów uruchamia się z katalogu głównego repozytorium.

## 5.1. Zlewnia jako układ liniowy

**Hydrogram jednostkowy** (ang. *unit hydrograph*, UH) to hydrogram odpływu bezpośredniego w
przekroju zamykającym, wywołany opadem efektywnym o wysokości 1 mm, który spadł równomiernie na
całą zlewnię ze stałym natężeniem w czasie $D$, nazywanym **czasem trwania opadu jednostkowego**
(ang. *unit duration*). Rzędne hydrogramu jednostkowego mają jednostkę m³/(s·mm): to przepływ
przypadający na każdy milimetr opadu efektywnego. W starszych podręcznikach opadem jednostkowym
jest 1 cm, w literaturze amerykańskiej 1 cal; rzędne z takich źródeł trzeba przed użyciem podzielić
przez 10 albo przez 25,4.

**Chwilowy hydrogram jednostkowy** (ang. *instantaneous unit hydrograph*, IUH), $u(t)$, to granica
hydrogramu jednostkowego przy $D \to 0$: odpowiedź zlewni na jednostkową objętość opadu efektywnego
podaną w jednej chwili. Ma wymiar odwrotności czasu (1/h lub 1/min), a pole pod nim równa się
jedności. Modele Nasha i Clarka opisują właśnie IUH; Hydrolog zamienia go na hydrogram jednostkowy
kroku obliczeń $\Delta t$.

**Krzywa S** (ang. *S-curve*, *S-hydrograph*) to odpływ wywołany opadem efektywnym o stałym
natężeniu, trwającym nieskończenie długo; jest całką IUH od chwili 0 do $t$. Hydrogram jednostkowy
o czasie trwania $D$ jest różnicą krzywej S i tej samej krzywej opóźnionej o $D$, podzieloną przez
$D$. W ten sposób Hydrolog buduje hydrogram kroku $\Delta t$ z IUH Nasha i Clarka (wzór w ramce
`clark`, p. 5.7).

Wszystkie modele tego rozdziału opierają się na tych samych założeniach:

1. **Liniowość (proporcjonalność).** Opad efektywny $k$ razy większy daje rzędne $k$ razy większe;
   kształt odpowiedzi nie zależy od wysokości opadu.
2. **Superpozycja.** Odpływy od kolejnych porcji opadu efektywnego sumują się.
3. **Stacjonarność.** Zlewnia odpowiada tak samo na ten sam opad bez względu na to, kiedy spadł.
4. **Równomierność opadu w przestrzeni.** Opad efektywny jest jednakowy w całej zlewni.

Z założeń wynikają granice metody. Rzeczywista zlewnia nie jest liniowa: prędkość spływu zależy od
wielkości wezbrania, więc hydrogram wyznaczony z jednego wezbrania nie musi pasować do innego.
Założenie 4 ogranicza metodę do zlewni małych albo wymaga podziału większej zlewni na zlewnie
cząstkowe, których hydrogramy łączy się w sieci (rozdz. 6). Hydrogram jednostkowy przetwarza
wyłącznie **opad efektywny** (ang. *effective rainfall*, *rainfall excess*), czyli część opadu,
która tworzy odpływ bezpośredni; straty (intercepcję, retencję powierzchniową, infiltrację) trzeba
odjąć wcześniej (rozdz. 3).

W zlewni kontrolowanej, z wodowskazem, hydrogram jednostkowy wyznacza się z zarejestrowanych
wezbrań. W **zlewni niekontrolowanej** (ang. *ungauged catchment*) korzysta się z **syntetycznego
hydrogramu jednostkowego** (ang. *synthetic unit hydrograph*), którego parametry szacuje się z
charakterystyk zlewni. Hydrolog liczy cztery takie modele: bezwymiarowy hydrogram SCS (p. 5.3),
hydrogram Snydera (p. 5.4), chwilowy hydrogram Nasha z parametrami podanymi wprost (p. 5.5) albo
oszacowanymi metodą Lutza (p. 5.6) oraz chwilowy hydrogram Clarka (p. 5.7).

## 5.2. Splot dyskretny i bilans objętości

Zasada superpozycji zapisana dla kroków czasowych $\Delta t$ to **splot dyskretny** (ang.
*discrete convolution*). Każdy blok opadu efektywnego wywołuje hydrogram jednostkowy pomnożony przez
wysokość tego bloku i przesunięty do chwili, w której blok się zaczął; odpływ w danej chwili jest
sumą tych odpowiedzi. Wzór, przyporządkowanie bloków opadu do rzędnych odpływu i jednostki podaje
ramka.

<!-- spec:uh_convolution -->

<a id="spec-uh_convolution"></a>

> **Odpływ bezpośredni z opadu efektywnego przez splot dyskretny z hydrogramem jednostkowym** · specyfikacja [`uh_convolution`](../FORMULAS.md#uh_convolution) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> Q_n = \sum_{m} P_{e,m}\,U_{n-m},\quad t_n = n\,\Delta t,\quad V = \Delta t \sum_n Q_n
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $P_{e,m}$ | `effective_precip_mm` (ciąg) | Opad efektywny w każdym kroku | mm | [0; ∞) | nie podano w źródłach | [0; 20] (źr. 3) |
> | $U_k$ | `unit_hydrograph_m3s` (ciąg) | Rzędne hydrogramu jednostkowego dla czasu trwania równego krokowi, pierwsza w t = 0 | m³/s na mm | [0; ∞) | nie podano w źródłach | [0; 15] (źr. 4) |
> | $\Delta t$ | `timestep_min` | Krok czasowy opadu i hydrogramu jednostkowego | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 5) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $Q_{max}$ | `peak_discharge_m3s` | Największa rzędna hydrogramu | m³/s | [0; ∞) |
> | $t_{max}$ | `time_to_peak_min` | Chwila pierwszej największej rzędnej | min | [0; ∞) |
> | $V$ | `total_volume_m3` | Objętość hydrogramu, sum(Q_n) dt | m³ | [0; ∞) |
> | $Q_n$ | `discharge_m3s` (ciąg) | Odpływ bezpośredni w chwili t_n | m³/s | [0; ∞) |
> | $t_n$ | `times_min` (ciąg) | Chwile rzędnych | min | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | hydrogram ma najwyżej milion rzędnych, M + K - 1 | `length_bounded` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - jednostki SI: wysokości w mm, rzędne w m³/s na mm, przepływy w m³/s
> - Pe_m to opad efektywny przedziału od m dt do (m + 1) dt, a U_0 — rzędna w t = 0: Q_n w t = n dt to odpowiedź na końcu przedziału n, zgodnie z ustawieniem we wzorze 6.12 KZGW i w przykładzie 16-1 NEH (Q(0,6 h) = 0,12 in x UH(0,3 h))
> - hydrogram jednostkowy dotyczy czasu trwania dt, równego krokowi opadu
> - V = dt sum(Q_n), sumę liczy się dokładnie (`math.fsum`)
>
> **Założenia**
>
> - liniowość i niezmienność w czasie odpowiedzi zlewni na opad efektywny równomierny na całej zlewni
>
> **Zgodność z obserwacjami według źródeł:** brak: splot jest superpozycją, którą zakłada hydrogram jednostkowy; jego źródła nie podają własnej oceny zgodności z obserwacjami
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.12, p. 92; examples 6.2 and 6.4, pp. 100-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), example 16-1, steps 4-10 and table 16-4, pp. 16-10 to 16-13 <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 6.1, 6.2 and 6.4, tables 6.1, 6.3 and 6.4, pp. 94-110: effective rainfall of 0 to 15.3 mm per step <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 6.2 and 6.4, tables 6.2 and 6.3, pp. 100-110: ordinates up to 1.911 m3/s per mm; NEH 630 example 16-1 (11.9 km2): 1.62 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 6. Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one
>
> Funkcja `hydrolog.runoff.convolution.convolve_discrete`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:uh_convolution -->

Splot wymaga, aby hydrogram jednostkowy był policzony dla czasu trwania równego krokowi hietogramu
($D = \Delta t$). Polecenie `hydrograph generate` liczy hydrogram jednostkowy zawsze dla czasu
trwania równego krokowi, więc warunek jest spełniony samoczynnie. Kto splata hydrogram jednostkowy z
innego źródła, musi go wcześniej przeliczyć na właściwe $D$ za pomocą krzywej S. Hydrogram odpływu
trwa tyle, ile opad efektywny i hydrogram jednostkowy łącznie, bez jednego kroku.

**Bilans objętości.** Objętość odpływu bezpośredniego musi być równa objętości opadu efektywnego nad
zlewnią: 1 mm opadu na 1 km² to 1000 m³, więc $V = 1000\,P_e A$ [m³], gdy $P_e$ jest w mm, a $A$ w
km². Tę samą zasadę spełnia sam hydrogram jednostkowy, którego objętość odpowiada 1 mm nad zlewnią.
Sprawdzenie bilansu wykrywa pomyłki jednostek (np. rzędne na 1 cm zamiast na 1 mm), zbyt krótko
obcięty hydrogram jednostkowy i niezgodność kroku. Polecenie `report generate` drukuje je jako
„Weryfikację objętościową”: objętość z hydrogramu wobec iloczynu $P_e A$, z oceną zgodności, gdy
różnica nie przekracza 1 %. W przykładach tego rozdziału różnice są mniejsze niż 0,02 %.

### Przykład 5.1. Splot na danych KZGW: potok Niedźwiadka

KZGW (2017, przykład 6.2, tabele 6.2 i 6.3) podaje dla potoku Niedźwiadka w km 3+450 (7,2 km²)
opad efektywny w krokach 1 h i hydrogram jednostkowy Nasha o $n$ = 2,55 i $K$ = 0,70 h = 42 min.
Polecenie `hydrograph generate` przyjmuje opad całkowity i samo odejmuje straty; aby splatać gotowy
opad efektywny, podaje się CN = 100. Wtedy retencja maksymalna i straty początkowe są zerowe, a opad
efektywny jest równy podanemu (rozdz. 3).

```sh
hydrolog hydrograph generate --area-km2 7.2 --cn 100 --values 0,0,0,0,0,0,0,0,0,0,0,0,0.07,0.73,1.73,2.95,4.25,5.51,6.54,7.18,7.23,6.5,4.79,1.89 --timestep-min 60 --uh-model nash --nash-n 2.55 --nash-k-min 42
```

| Czas od początku opadu [h] | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|
| KZGW (2017), tab. 6.3 [m³/s] | 5,39 | 7,79 | 10,15 | 12,14 | 13,44 | 13,66 | 12,43 | 9,35 | 5,29 |
| Hydrolog [m³/s] | 5,41 | 7,83 | 10,20 | 12,20 | 13,50 | 13,72 | 12,48 | 9,38 | 5,30 |

Kulminacja przypada w tej samej godzinie, a Hydrolog daje ją o 0,4 % wyższą. Różnica pochodzi z
rzędnych hydrogramu jednostkowego: Hydrolog liczy je z $n$ i $K$ (p. 5.5) i różnią się one od
wydrukowanych w tabeli 6.2 źródła najwyżej o 0,004 m³/(s·mm). Opad efektywny wynosi 49,37 mm,
objętość odpływu 355 453 m³, a iloczyn $1000\,P_e A$ = 355 464 m³ (różnica 0,003 %). Hydrolog
dodaje uwagę `outside_unverified_range` o kroku: 60 min to więcej niż ułamek czasu do kulminacji,
który przyjmuje jako praktyczną granicę dla hydrogramu Nasha (p. 5.5).

## 5.3. Bezwymiarowy hydrogram jednostkowy SCS

**Idea.** Bezwymiarowy hydrogram jednostkowy SCS (dziś NRCS; ang. *SCS dimensionless unit
hydrograph*) to stały kształt odpływu, opracowany przez V. Mockusa jako uśredniony kształt wielu
hydrogramów jednostkowych zlewni w USA (USDA-NRCS 2007). Kształt podaje tablica stosunków
$q/q_p$ do $t/T_p$; hydrogram zlewni otrzymuje się, skalując czas przez **czas do kulminacji**
$T_p$ (ang. *time to peak*), a przepływ przez **przepływ kulminacyjny** $q_p$ (ang. *peak
discharge*). Model potrzebuje tylko powierzchni zlewni i czasu koncentracji $t_c$ (rozdz. 4): czas
opóźnienia $t_{lag}$ (ang. *lag time*, od środka masy opadu efektywnego do kulminacji) jest w tej
metodzie stałym ułamkiem czasu koncentracji, przeciętną zależnością z NEH 630, rozdz. 15
(USDA-NRCS 2010).

<!-- spec:scs -->

<a id="spec-scs"></a>

> **Bezwymiarowy hydrogram jednostkowy SCS (NRCS) dla jednostkowego czasu trwania opadu** · specyfikacja [`scs`](../FORMULAS.md#scs) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_{lag} = 0{,}6\,t_c,\quad T_p = \frac{D}{2} + t_{lag},\quad q_p = \frac{C\,A}{T_p},\quad q_k = q_p\,f\!\left(\frac{k\,D}{T_p}\right),\quad T_b = 5\,T_p
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | [0; 51,8] (źr. 4) | [0,0003; 250] (źr. 5) |
> | $t_c$ | `tc_min` | Czas koncentracji zlewni | min | (0; ∞) | nie podano w źródłach | [1; 450] (źr. 6) |
> | $D$ | `timestep_min` | Krok czasowy hydrogramu i czas trwania jego jednostkowego opadu efektywnego | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $q_p$ | `peak_discharge_m3s` | Przepływ kulminacyjny ze wzoru dla czasu trwania D | m³/s na mm | [0; ∞) |
> | $T_p$ | `time_to_peak_min` | Czas do kulminacji od początku jednostkowego opadu efektywnego | min | (0; ∞) |
> | $t_{lag}$ | `lag_time_min` | Czas opóźnienia zlewni, od środka jednostkowego opadu efektywnego do Tp | min | (0; ∞) |
> | $T_b$ | `time_base_min` | Czas podstawy hydrogramu: koniec tab. 16-1 | min | (0; ∞) |
> | $k D$ | `times_min` (ciąg) | Chwile rzędnych liczone od początku opadu efektywnego | min | [0; ∞) |
> | $q_k$ | `ordinates_m3s` (ciąg) | Rzędne hydrogramu jednostkowego dla czasu trwania D | m³/s na mm | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | float64 przedstawia tlag, Tp, podkrok i kulminacje jako liczby znormalizowane, podkroków jest najwyżej 2**53, a siatki kroku i podkroku mają każda najwyżej milion rzędnych | `steps_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}6$ | `lag_ratio` | Stosunek czasu opóźnienia do czasu koncentracji | 0,6 | – | (źr. 9) |
> | $C$ | `peak_factor` | Współczynnik przepływu kulminacyjnego (współczynnik szczytu) | 2,08 | $\mathrm{m^{3}\,s^{-1}\,km^{-2}\,cm^{-1}\,h}$ | (źr. 10) |
> | $0{,}25$ | `step_share` | Największy zalecany stosunek kroku czasowego do czasu do kulminacji | 0,25 | – | (źr. 11) |
>
> **Konwencje**
>
> - jednostki SI: A w km², czasy w min, rzędne w m³/s na mm odpływu; C = 2,08 odnosi się do cm (HEC-HMS 2000, wzór 36), na mm przeliczone przez dokładne 10 mm/cm
> - C = 2,08 odpowiada współczynnikowi szczytu NEH 483,2 w jednostkach anglosaskich (stopa–funt), a nie 484: NEH 630 (s. 16A-2) przypisuje tab. 16-1 współczynnik 483,4 wynikający z zaokrągleń jej stosunków; przy 2,08 objętość ciągłej tabeli wynosi 1,00036 mm
> - czasy liczone od początku jednostkowego opadu efektywnego; D jest krokiem czasowym
> - tab. 16-1 interpolowana liniowo między wierszami, tak jak w tab. 16-2 NEH 630 (t/Tp 2,1 daje 0,2435), oraz 0 od t/Tp = 5
> - rzędne to wartości krzywej w chwilach kroków czasowych (NEH 630, przykład 16-1, krok 2)
> - krok dłuższy niż 0,25 Tp dzieli się na podkroki, a opad kroku rozkłada się na nie równomiernie (uwaga `uh_substeps`): objętość pozostaje równa 1 mm, natomiast qp, Tp i Tb pozostają wartościami ze wzoru dla D, więc qp przewyższa wtedy największą rzędną (o 21 % dla tc 90,7 min przy kroku 60 min)
>
> **Założenia**
>
> - opad efektywny równomierny na całej zlewni i w czasie D; zlewnie cząstkowe o powierzchni najwyżej 20 mil kwadratowych, największa najwyżej 10 razy większa od najmniejszej (NEH 630, s. 16-4); większe zlewnie dzieli się, a ich hydrogramy transformuje się w korytach
> - tlag = 0,6 tc, przeciętna zależność z rozdz. 15 NEH 630
> - D = 0,2 Tp (D = 0,133 tc), najwyżej 0,25 Tp (NEH 630, s. 16A-3); powyżej tej granicy `hydrograph generate` ostrzega uwagą `outside_applicability` dla `scs.timestep_min`
>
> **Zgodność z obserwacjami według źródeł:** Mockus (1957) wyprowadził bezwymiarowy hydrogram jednostkowy z wielu naturalnych hydrogramów jednostkowych zlewni bardzo zróżnicowanych pod względem wielkości i położenia geograficznego (NEH 630-16, s. 16-2; HEC-HMS 2000, s. 55: małe zlewnie rolnicze); źródła nie podają żadnej statystyki błędu jego kształtu ani kulminacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), table 16-1, p. 16-4; appendix 16A, eqs. 16A-6 to 16A-9 and 16A-13, pp. 16A-2 to 16A-3; example 16-1, pp. 16-7 to 16-13 <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
> 2. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), SCS unit hydrograph model, eqs. 36-38, pp. 55-56 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 3. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, Snyder's synthetic UHG, pp. 76-78 (eqs. 7.7.2-7.7.4, C1 0.75, C2 2.75, C3 5.56, Cw 2.14 and 1.22 in SI, 770 and 440 in English units, areas of 30 to 30,000 km2); SCS dimensionless hydrograph, p. 79 (C = 2.08, 483.4 in English units) <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
> 4. USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), p. 16-4: no subarea to exceed 20 square miles (51.8 km2), the largest no more than 10 times the smallest <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Kirpich's tc of the flow paths of the 27 watersheds, the default method of hydrograph generate, 1.04 to 450 min
> 7. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 8. Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one
> 9. USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), eq. 16A-9, p. 16A-2: L = 0.6 Tc (after NEH 630 ch. 15); HEC-HMS 2000, eq. 38, p. 56 <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
> 10. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 36, p. 55: C = 2.08 in SI and 484 in foot-pound units; Chow et al. 1988, after Rajagopalan's notes, p. 79: C = 2.08 (483.4 in English units) <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 11. USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), p. 16A-3: the unit duration D is 0.2 Tp and no greater than 0.25 Tp; HEC-HMS 2000, p. 55: less than 29 % of tlag <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
>
> Funkcja `hydrolog.runoff.unit_hydrograph.scs_unit_hydrograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:scs -->

Tablicę kształtu (NEH 630, tab. 16-1) Hydrolog przechowuje jako plik danych, przepisany dwukrotnie
i niezależnie (ADR-0057); między wierszami interpoluje liniowo, jak NEH w tabeli 16-2:

<!-- spec-table:scs -->

> **Tablica `src/hydrolog/_data/tables/neh630_duh.csv`** · specyfikacja `scs` · SHA-256 `b465694f902953d282e964c34c7a535adc4cb8c833948ffca7c2a5080d871709`
>
> | $t/T_p$ | $q/q_p$ |
> |---|---|
> | 0,0 | 0,000 |
> | 0,1 | 0,030 |
> | 0,2 | 0,100 |
> | 0,3 | 0,190 |
> | 0,4 | 0,310 |
> | 0,5 | 0,470 |
> | 0,6 | 0,660 |
> | 0,7 | 0,820 |
> | 0,8 | 0,930 |
> | 0,9 | 0,990 |
> | 1,0 | 1,000 |
> | 1,1 | 0,990 |
> | 1,2 | 0,930 |
> | 1,3 | 0,860 |
> | 1,4 | 0,780 |
> | 1,5 | 0,680 |
> | 1,6 | 0,560 |
> | 1,7 | 0,460 |
> | 1,8 | 0,390 |
> | 1,9 | 0,330 |
> | 2,0 | 0,280 |
> | 2,2 | 0,207 |
> | 2,4 | 0,147 |
> | 2,6 | 0,107 |
> | 2,8 | 0,077 |
> | 3,0 | 0,055 |
> | 3,2 | 0,040 |
> | 3,4 | 0,029 |
> | 3,6 | 0,021 |
> | 3,8 | 0,015 |
> | 4,0 | 0,011 |
> | 4,5 | 0,005 |
> | 5,0 | 0,000 |
>
> Źródło (w brzmieniu specyfikacji): USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), table 16-1, p. 16-4: time ratios t/Tp and discharge ratios q/qp (the same ratios in NEH-4 (1972), table 16.1) <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>. Dwie niezależne transkrypcje porównano: tests/oracles/neh630_duh_text_layer.csv (transcribed from the PDF's text layer by tests/oracles/transcribe_neh630_duh.py) against tests/oracles/neh630_duh_hydrolog_0_8_1.csv (typed for Hydrolog 0.8.1), compared by tests/unit/test_formulas_unit_hydrographs.py; USDA-SCS (1972). National Engineering Handbook, Section 4 Hydrology, Chapter 16: Hydrographs (NEH Notice 4-102, August 1972; amendment 6, March 1985), table 16.1, prints the same ratios
>
> Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec-table:scs -->

**Skąd stała $C$.** Przepływ kulminacyjny wynika z bilansu objętości. NEH zastępuje krzywą
trójkątem o tej samej kulminacji, w którym przed szczytem odpływa 3/8 objętości; trójkąt musi
pomieścić 1 mm opadu efektywnego nad zlewnią (USDA-NRCS 2007, dodatek 16A). W jednostkach
anglosaskich tę samą rolę pełni **współczynnik szczytu** (ang. *peak rate factor*, PRF). Krzywa z
tablicy, której rzędne zaokrąglono, ma współczynnik nieco mniejszy niż trójkąt; Hydrolog przyjmuje
stałą odpowiadającą krzywej (ramka, konwencje), dzięki czemu hydrogram jednostkowy zachowuje
objętość 1 mm z dokładnością do kilku setnych procenta.

**Czas trwania.** Hydrogram kończy się w chwili $T_b$ z ramki. Podstawa trójkąta zastępczego jest
krótsza — nie należy jej brać za koniec hydrogramu.

**Krok obliczeń.** Czas trwania opadu jednostkowego $D$ (w Hydrologu: krok $\Delta t$) nie powinien
przekraczać ułamka $T_p$ podanego w ramce (stała `step_share`; NEH 630, s. 16A-3). Dłuższy krok
słabo odwzorowuje kształt, a próbkowanie tablicy w chwilach $k\,D$ gubiłoby objętość. Hydrolog
liczy wtedy hydrogram na krokach pośrednich i uśrednia go, zachowując objętość 1 mm, oraz dodaje
uwagę `uh_substeps`. Podawany przepływ $q_p$ jest zawsze wartością ze wzoru dla czasu trwania $D$:
gdy $T_p$ wypada między chwilami kroku, największa rzędna jest od niego trochę mniejsza, a przy
krokach pośrednich — wyraźnie mniejsza (ADR-0057). Czy wynik powinien podawać największą rzędną,
pozostaje otwartym pytaniem autora.

**Zakres stosowania.** NEH 630 (s. 16-4) zaleca, by zlewnia cząstkowa nie przekraczała powierzchni
podanej w ramce i by zlewnie cząstkowe nie różniły się zbyt mocno wielkością (założenia ramki);
większą zlewnię dzieli się, a hydrogramy części łączy splotem i transformacją w korytach (rozdz. 6).
W Polsce model SCS nie należy do metod opisanych w KZGW (2017); w Czechach SCS-CN z hydrogramem
jednostkowym w programie HEC-HMS jest typowym narzędziem projektowania małych budowli wodnych (Kavka
i in. 2018).

**Typowe błędy.**

- Czas koncentracji z innych jednostek: Hydrolog przyjmuje $t_c$ w minutach.
- Przenoszenie zależności $t_{lag}$ od $t_c$ na modele Nasha czy Clarka — to założenie wyłącznie
  metody SCS.
- Krok dłuższy niż dopuszcza ramka.
- Mylenie podstawy trójkąta zastępczego z końcem hydrogramu.
- Czas koncentracji ze wzorów na spływ po stoku (FAA, Kerby) w zlewni z wykształconym korytem
  (rozdz. 4).

### Przykład 5.2. Przykład 16-1 z NEH 630

NEH 630 (USDA-NRCS 2007, przykład 16-1) liczy hydrogram zlewni o powierzchni 4,6 mi² (11,914 km²)
i czasie koncentracji 2,3 h (138 min) dla kroku 0,3 h (18 min):

```sh
hydrolog uh scs --area-km2 11.914 --tc-min 138 --timestep-min 18
```

Hydrolog daje czas opóźnienia 82,8 min, $T_p$ = 91,8 min (1,53 h, jak w źródle) i $q_p$ =
1,6197 m³/(s·mm). NEH podaje 1455 ft³/s na cal opadu, czyli 1,622 m³/(s·mm); różnica −0,15 % wynika
z przyjętej stałej $C$ (NEH liczy ze współczynnika szczytu trójkąta). Największa rzędna to
1,6165 m³/(s·mm) w 90. minucie, bo $T_p$ = 91,8 min nie leży na siatce kroku.

### Przykład 5.3. Hydrogram jednostkowy SCS Kamiennika

Dla Kamiennika czas koncentracji metodą Kerby’ego–Kirpicha wynosi 208,63 min (rozdz. 4); to jedyna
z metod rozdz. 4, której dane źródłowe obejmują tę zlewnię. Krok 10 min:

```sh
hydrolog uh scs --area-km2 37.22 --tc-min 208.63 --timestep-min 10
```

| Wielkość | Wartość |
|---|---|
| czas opóźnienia $t_{lag}$ | 125,18 min |
| czas do kulminacji $T_p$ | 130,18 min |
| przepływ kulminacyjny $q_p$ | 3,568 m³/(s·mm) |
| największa rzędna | 3,5677 m³/(s·mm) w 130. minucie |
| koniec hydrogramu $T_b$ | 650,89 min |
| objętość hydrogramu jednostkowego | 1,0002 mm |

Krok jest krótki wobec $T_p$ ($\Delta t / T_p$ ≈ 0,08), więc Hydrolog nie dzieli go na kroki
pośrednie. Każdy milimetr opadu efektywnego, który spadnie w ciągu 10 minut, daje w Świerzawie
kulminację około 3,6 m³/s po nieco ponad 2 godzinach.

## 5.4. Syntetyczny hydrogram jednostkowy Snydera

**Idea.** Snyder (1938) powiązał charakterystyki hydrogramów jednostkowych zlewni w Appalachach z
ich geometrią. **Czas opóźnienia zlewni** $t_L$ (ang. *basin lag*) zależy od długości cieku
głównego $L$ i odległości $L_c$ od przekroju do punktu cieku najbliższego środkowi ciężkości
zlewni, przez regionalny **współczynnik czasowy** $C_t$; przepływ kulminacyjny zależy od
powierzchni i **współczynnika szczytu** $C_p$. Metoda podaje punkty hydrogramu — czas opóźnienia,
kulminację, szerokości na wysokości 50 % i 75 % kulminacji, podstawę — ale nie jego pełny kształt.
Dla czasu trwania opadu $D$ innego niż standardowy $t_D$ koryguje się czas opóźnienia
($t_{LR}$), czas do kulminacji ($t_{pR}$) i kulminację ($q_{pR}$). KZGW (2017, s. 90–95) zaleca
model Snydera razem z opadem efektywnym SCS-CN do hydrogramów hipotetycznych w zlewniach
niekontrolowanych.

<!-- spec:snyder -->

<a id="spec-snyder"></a>

> **Syntetyczny hydrogram jednostkowy Snydera: czas opóźnienia, kulminacja, czas podstawy i szerokości** · specyfikacja [`snyder`](../FORMULAS.md#snyder) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_L = C_t\,(L\,L_c)^{0{,}3},\quad t_D = \frac{t_L}{5{,}5},\quad t_{LR} = t_L + \frac{D - t_D}{4},\quad t_{pR} = t_{LR} + \frac{D}{2},\quad q_{pR} = \frac{0{,}275\,C_p\,A}{t_{LR}},\quad t_b = \frac{0{,}556\,A}{q_{pR}},\quad W_{50} = 770 \left(\frac{q_{pR}}{A}\right)^{-1{,}08}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | [30; 30 000] (źr. 6) | [0,0003; 250] (źr. 7) |
> | $L$ | `length_km` | Długość cieku głównego od przekroju zamykającego do działu wodnego | km | (0; ∞) | nie podano w źródłach | [0,05; 29] (źr. 8) |
> | $L_c$ | `centroid_length_km` | Długość wzdłuż cieku głównego od przekroju zamykającego do punktu najbliższego środkowi ciężkości zlewni | km | (0; ∞) | nie podano w źródłach | [0,05; 29] (źr. 8) |
> | $C_t$ | `ct` | Współczynnik czasowy w jednostkach SI | – | (0; ∞) | [1,35; 1,65] (źr. 9) | [1,35; 1,65] (źr. 10) |
> | $C_p$ | `cp` | Współczynnik kulminacji | – | (0; ∞) | [0,4; 0,8] (źr. 11) | [0,4; 0,8] (źr. 12) |
> | $D$ | `duration_min` | Czas trwania jednostkowego opadu efektywnego | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 13) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_L$ | `lag_time_min` | Czas opóźnienia zlewni, od środka opadu o czasie trwania tD do kulminacji | min | (0; ∞) |
> | $t_D$ | `standard_duration_min` | Standardowy czas trwania opadu | min | (0; ∞) |
> | $t_{LR}$ | `adjusted_lag_time_min` | Czas opóźnienia dla czasu trwania D | min | (0; ∞) |
> | $t_{pR}$ | `time_to_peak_min` | Czas do kulminacji dla czasu trwania D liczony od początku opadu | min | (0; ∞) |
> | $q_p$ | `standard_peak_discharge_m3s` | Kulminacja dla standardowego czasu trwania | m³/s na mm | (0; ∞) |
> | $q_{pR}$ | `peak_discharge_m3s` | Kulminacja dla czasu trwania D | m³/s na mm | (0; ∞) |
> | $t_b$ | `time_base_min` | Podstawa trójkąta o wierzchołku qpR i objętości 1 mm | min | (0; ∞) |
> | $W_{50}$ | `width_50_min` | Szerokość hydrogramu jednostkowego na wysokości 50 % kulminacji qpR | min | (0; ∞) |
> | $W_{75}$ | `width_75_min` | Szerokość hydrogramu jednostkowego na wysokości 75 % kulminacji qpR | min | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | float64 przedstawia czas opóźnienia, kulminacje, czas podstawy i szerokości jako liczby znormalizowane | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 14) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $0{,}3$ | `lag_exponent` | Wykładnik iloczynu długości L i Lc w zależności na czas opóźnienia | 0,3 | – | (źr. 15) |
> | $5{,}5$ | `standard_ratio` | Stosunek czasu opóźnienia do standardowego czasu trwania opadu | 5,5 | – | (źr. 16) |
> | $1/4$ | `adjustment` | Współczynnik korekty czasu opóźnienia przy zmianie czasu trwania opadu | 0,25 | – | (źr. 17) |
> | $0{,}275$ | `peak_factor` | Współczynnik przepływu kulminacyjnego w jednostkach SI | 0,275 | $\mathrm{m^{3}\,s^{-1}\,km^{-2}\,mm^{-1}\,h}$ | (źr. 18) |
> | $0{,}556$ | `base_factor` | Współczynnik czasu podstawy | 0,556 | $\mathrm{h\,m^{3}\,s^{-1}\,km^{-2}\,mm^{-1}}$ | (źr. 19) |
> | $770$ | `width_50` | Współczynnik szerokości hydrogramu w połowie wysokości kulminacji | 770 | $\mathrm{h\,(ft^{3}\,s^{-1}\,mi^{-2}\,in^{-1})^{1{,}08}}$ | (źr. 20) |
> | $440$ | `width_75` | Współczynnik szerokości hydrogramu na wysokości trzech czwartych kulminacji | 440 | $\mathrm{h\,(ft^{3}\,s^{-1}\,mi^{-2}\,in^{-1})^{1{,}08}}$ | (źr. 21) |
> | $1{,}08$ | `width_exponent` | Wykładnik kulminacji na jednostkę powierzchni w zależności na szerokości | 1,08 | – | (źr. 22) |
>
> **Konwencje**
>
> - jednostki SI: A w km², L i Lc w km; Ct w jednostkach SI zawiera mnożnik 0,75 Snydera (HEC-HMS: tp = C Ct (L Lc)^0,3, C = 0,75 w SI), więc jego zakres od 1,35 do 1,65 to 0,75 razy zakres Snydera od 1,8 do 2,2 (KZGW 2017, s. 90)
> - kulminacje w m³/s na mm odpływu: 0,275 i 0,556 na mm to wartości 2,75 i 5,56 na cm u Chowa (KZGW 2017, wzory 6.7 i 6.11)
> - czasy liczone od początku opadu jednostkowego, podawane w min: czas opóźnienia tL to tp Snydera w HEC-HMS i u Chowa, czas do kulminacji to tp według KZGW, tp = tL + tD / 2 dla D = tD oraz tpR = tLR + D / 2 dla innego D
> - tb to podstawa trójkąta o wierzchołku qpR i objętości 1 mm (KZGW 2017, wzór 6.11; C3 / qpR u Chowa), a nie koniec krzywej z `snyder_shape`
> - szerokości według Chowa i in. (1988), z qpR na jednostkę powierzchni, ze współczynnikami Snydera 770 i 440 przeliczonymi dokładnie z ft³/s na mi² i cal (1 / 2323,2 m³/s na km² i mm, tabela jednostek): 0,17829 i 0,10188; wartości SI Chowa 2,14 i 1,22 na cm są ich zaokrągleniami (0,17800 i 0,10148 na mm, mniejsze o 0,2 % i 0,4 %)
> - L to długość cieku głównego od przekroju zamykającego do działu wodnego, Lc — długość wzdłuż niego do punktu najbliższego środkowi ciężkości zlewni (KZGW 2017, s. 90)
>
> **Założenia**
>
> - współczynniki Ct i Cp są właściwe dla regionu i najlepiej kalibrować je na zlewniach kontrolowanych tego regionu (HEC-HMS); KZGW 2017 podaje od 1,35 do 1,65 i od 0,4 do 0,8
> - większość zlewni ekosystemu (powierzchnie w przekazaniach danych do 250 km²) jest mniejsza od zlewni Snydera, od 30 do 30 000 km²: otrzymują one uwagę `outside_applicability` dla `snyder.area_km2`
>
> **Zgodność z obserwacjami według źródeł:** Snyder (1938) wyprowadził zależności dla zlewni w Appalachach o powierzchni od 10 do 10 000 mil kwadratowych (Chow i in. 1988 za notatkami Rajagopalana, s. 76); Ct i Cp są regionalne i najlepiej wyznaczać je przez kalibrację (HEC-HMS); źródła nie podają żadnej statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 6.4 to 6.11, pp. 90-92; example 6.1, pp. 92-95 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Snyder's unit hydrograph model, eqs. 30-32, pp. 54-55 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 3. USACE-HEC. HEC-HMS Technical Reference Manual (online, read 2026-11-19), chapter Transform, Snyder Unit Hydrograph Model, eqs. 1 to 5: tp = C Ct (L Lc)^0.3, C = 0.75 in SI and 1.00 in foot-pound units <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/snyder-unit-hydrograph-model>
> 4. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, Snyder's synthetic unit hydrograph, pp. 76-78, eqs. 7.7.2-7.7.6 <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
> 5. Innovyze. InfoSWMM help, Snyder Unit Hydrograph Method (online, read 2026-11-19), the widths W50 and W75 of the unit hydrograph: C50 = 770 and C75 = 440 in U.S. customary units, 2.14 and 1.22 in S.I. units; C2 = 640 and 2.75 of the peak <https://help.innovyze.com/space/infoswmm/17598671/Snyder+Unit+Hydrograph+Method>
> 6. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 76: Snyder's watersheds in the Appalachian Highlands, of 30 to 30,000 km2 (10 to 10,000 mi2) <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
> 7. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 8. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: the longest flow paths of the 27 watersheds that have one, 0.057 to 28.9 km (flow_path_length_km): Snyder's L runs from the outlet to the divide, and Lc along it to the point nearest the centroid
> 9. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units, 0.75 times Snyder's 1.8 to 2.2 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 10. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 11. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); and USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), KZGW 2017, annex 2, p. 91, eq. 6.7: Cp from 0.4 to 0.8; HEC-HMS 2000, Snyder's unit hydrograph model, p. 54: 0.4 to 0.8 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 12. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 91, eq. 6.7: Cp from 0.4 to 0.8 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 13. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 14. IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308
> 15. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.5, p. 90: tL = Ct (L Lc)^0.3; HEC-HMS (online), Snyder Unit Hydrograph Model, eq. 5; Chow et al. 1988 after Rajagopalan's notes, eq. 7.7.2, p. 76 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 16. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 30: tp = 5.5 tr; KZGW 2017, annex 2, eq. 6.6, p. 91: tD = tL / 5.5 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 17. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 31: tpR = tp - (tr - tR) / 4; KZGW 2017, annex 2, eq. 6.8, p. 91: tLR = tL + 0.25 (D - tD) <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 18. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.7, p. 91: qp = 0.275 Cp A / tL in m3/s per mm; HEC-HMS 2000, eq. 32, and Chow et al. 1988 after Rajagopalan's notes, eq. 7.7.3, p. 77: C2 = 2.75 per cm <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 19. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.11, p. 92: tb = 0.556 A / qpR; Chow et al. 1988 after Rajagopalan's notes, p. 78: C3 = 5.56 per cm <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 20. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: W = Cw qpR^-1.08 with Cw = 770 at 50 % of the peak in English units (2.14 in SI per cm); Innovyze, Snyder Unit Hydrograph Method: C50 = 770 <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
> 21. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: Cw = 440 at 75 % of the peak in English units (1.22 in SI per cm); Innovyze, Snyder Unit Hydrograph Method: C75 = 440 <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
> 22. Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: W = Cw qpR^-1.08, qpR per unit area <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
>
> Funkcja `hydrolog.runoff.snyder_uh.snyder_parameters`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snyder -->

**Konwencje jednostek** to najczęstsze źródło pomyłek:

- $C_t$ w układzie SI zawiera mnożnik przeliczeniowy HEC-HMS (ramka, konwencje), dlatego zakres
  $C_t$ według KZGW jest inny niż w literaturze amerykańskiej; wartości z podręczników
  amerykańskich trzeba przeliczyć.
- Stałe wzorów na $q_{pR}$ i $t_b$ w ramce dotyczą rzędnych na 1 mm; u Chowa i in. (1988) te same
  stałe są dziesięciokrotnie większe, bo dotyczą 1 cm.
- $L$ mierzy się do **działu wodnego**, nie do początku koryta. W danych zlewni Hydrologu
  odpowiada mu najdłuższa droga spływu `flow_path_length_km` (ADR-0043), a nie długość koryta
  `channel_length_km`, która jest krótsza i skraca czas opóźnienia.
- $C_t$ i $C_p$ są regionalne. Najlepiej wyznaczyć je ze zlewni kontrolowanej o podobnych cechach;
  większe $C_t$ i mniejsze $C_p$ przyjmuje się dla zlewni o większej retencji i mniejszym spadku
  (KZGW 2017). Hydrolog domyślnie przyjmuje $C_t$ = 1,5 i $C_p$ = 0,6, wartości ze środka zakresów
  KZGW.

**Kształt.** Ani Snyder, ani KZGW nie podają funkcji kształtu (KZGW rysuje hydrogram liniami
prostymi), a HEC-HMS dopasowuje do parametrów Snydera hydrogram Clarka. Hydrolog prowadzi przez
punkt $(t_{pR}, q_{pR})$ krzywą gamma o objętości 1 mm (Asquith i Roussel 2007) — to odstępstwo od
źródeł metody, opisane w osobnej specyfikacji o statusie `oracle only`:

<!-- spec:snyder_shape -->

<a id="spec-snyder_shape"></a>

> **Hydrogram jednostkowy Snydera jako krzywa gamma o objętości 1 mm przechodząca przez kulminację** · specyfikacja [`snyder_shape`](../FORMULAS.md#snyder_shape) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> q(t) = q_{pR}\left[\frac{t}{t_{pR}}\,e^{1 - t/t_{pR}}\right]^K,\quad q_{pR}\,t_{pR}\,\Gamma(K)\left(\frac{e}{K}\right)^K = A \cdot 1\,\mathrm{mm},\quad \sum_k q_k\,\Delta t = A \cdot 1\,\mathrm{mm}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 3) |
> | $t_{pR}$ | `time_to_peak_min` | Czas do kulminacji od początku opadu (specyfikacja `snyder`) | min | (0; ∞) | nie podano w źródłach | [16; 760] (źr. 4) |
> | $q_{pR}$ | `peak_discharge_m3s` | Kulminacja hydrogramu jednostkowego (specyfikacja `snyder`) | m³/s na mm | (0; ∞) | nie podano w źródłach | [2,7·10⁻⁶; 235] (źr. 5) |
> | $\Delta t$ | `timestep_min` | Krok czasowy rzędnych | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 6) |
> | $T$ | `total_duration_min` | Długość hydrogramu: krzywa poza nią jest odcinana | min | (0; ∞) | nie podano w źródłach | [60; 7610] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $K$ | `shape_exponent` | Wykładnik krzywej | – | (0; ∞) |
> | $k \Delta t$ | `times_min` (ciąg) | Chwile rzędnych liczone od początku opadu | min | [0; ∞) |
> | $q_k$ | `ordinates_m3s` (ciąg) | Rzędne hydrogramu jednostkowego | m³/s na mm | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | wykładnik K krzywej o objętości 1 mm leży między 1e-12 a 1e12: qpR tpR / (A x 1 mm) między około 1e-12 a 4e5 | `root_bracketed` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | siatka ma najwyżej milion rzędnych, a float64 przedstawia (T + dt) / tpR oraz, jako liczbę znormalizowaną, rzędną odpowiadającą 1 mm w jednym kroku, A x 1 mm / dt | `grid_representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
>
> **Konwencje**
>
> - czasy od początku opadu, w min; rzędne w m³/s na mm
> - rzędne to wartości krzywej w chwilach kroków, przeskalowane tak, by zawierały dokładnie 1 mm: próbkowanie i część poza T zmieniałyby objętość
> - `SnyderUH` przyjmuje tpR i qpR ze specyfikacji `snyder` dla danego czasu trwania, a T, jeśli nie zostało podane, w chwili, w której krzywa osiąga 99,99 % swojej objętości, T = tpR P^-1(K + 1; 0,9999) / K, gdzie P to regularyzowana dolna niekompletna funkcja gamma
>
> **Założenia**
>
> - kształt hydrogramu jednostkowego między punktami wyznaczonymi metodą Snydera to krzywa gamma; KZGW 2017, przykład 6.1, łączy je odcinkami prostymi (jego tab. 6.1, kulminacja niższa o 6,9 %)
>
> **Zgodność z obserwacjami według źródeł:** brak: metoda Snydera daje kulminację, szerokości i czas podstawy, a nie krzywą (KZGW 2017, rys. 6.1; HEC-HMS dopasowuje zamiast tego hydrogram jednostkowy Clarka); Asquith i Roussel (2007) podają krzywą i jej objętość
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. Asquith, W.H. and Roussel, M.C. (2007). An initial-abstraction, constant-loss model for unit hydrograph modeling for applicable watersheds in Texas. U.S. Geological Survey Scientific Investigations Report 2007-5243, eq. 2, the gamma unit hydrograph through its peak, and eq. 4, its volume qp tp Gamma(K) (e / K)^K <https://pubs.usgs.gov/sir/2007/5243/>
> 2. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), fig. 6.1, p. 90: the unit hydrograph through (tpR, qpR), its shape not prescribed <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 4. Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give tpR of 16.6 to 758 min
> 5. Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give qpR of 2.7e-6 to 235 m3/s per mm
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give the ends of the curves at 99.99 % of their volume, the default of SnyderUH, of 61 to 7,605 min (K of 1.14 to 17.2)
> 8. Hydrolog's bracket of the root of the volume of the curve, Brent's method on ln K from 1e-12 to 1e12
> 9. Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one
>
> Funkcja `hydrolog.runoff.snyder_uh.snyder_shape`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:snyder_shape -->

Większe $C_p$ daje krzywą węższą i wyższą. Podawany przepływ kulminacyjny jest największą rzędną
krzywej, a czas $t_{pR}$ — wartością ze wzoru (ADR-0057). Podstawa $t_b$ dotyczy trójkąta o
kulminacji $q_{pR}$ i objętości 1 mm, a nie końca krzywej, który Hydrolog wyznacza tak, by krzywa
objęła prawie całą objętość (ramka, konwencje).

### Przykład 5.4. Rzeka Jasienica (KZGW 2017, przykład 6.1)

Przekrój zapory projektowanego zbiornika Międzyrzecze na Jasienicy: $A$ = 45,3 km², $L$ = 14,9 km,
$L_c$ = 7,0 km, $C_t$ = 1,65, $C_p$ = 0,565, krok i czas trwania opadu 1 h:

```sh
hydrolog uh snyder --area-km2 45.3 --length-km 14.9 --centroid-length-km 7 --ct 1.65 --cp 0.565 --timestep-min 60 --rainfall-duration-min 60
```

| Wielkość | KZGW (2017) | Hydrolog |
|---|---|---|
| $t_L$ | 6,65 h | 399,14 min = 6,652 h |
| $t_D$ | 1,21 h | 72,57 min = 1,210 h |
| $t_{LR}$ | 6,60 h | 395,99 min = 6,600 h |
| $q_{pR}$ | 1,07 m³/(s·mm) | 1,0662 m³/(s·mm) |
| $t_{pR}$ | 7,0 h | 425,99 min = 7,100 h |
| $t_b$ | 23,0 h | 1417,04 min = 23,617 h |

Dwie ostatnie wartości źródła to pomyłki rachunkowe: z wydrukowanych w nim składników wychodzi
$t_{pR}$ = 6,60 + 1,0/2 = 7,10 h oraz $t_b$ ≈ 23,5 h (ADR-0058). Hydrogram hipotetyczny z tabeli 6.1
źródła (opad efektywny z opadu dobowego o prawdopodobieństwie 1 %) można powtórzyć tak samo jak w
przykładzie 5.1:

```sh
hydrolog hydrograph generate --area-km2 45.3 --cn 100 --values 0,0,0,0,0,0,0,0,0,0,0,0,0,0.8,4,8.5,12.8,15.3,15,12,7.4,3.1,0.7,0 --timestep-min 60 --uh-model snyder --snyder-length-km 14.9 --snyder-centroid-length-km 7 --snyder-ct 1.65 --snyder-cp 0.565
```

Hydrolog daje kulminację 78,27 m³/s po 25 h, o 6,9 % wyższą niż 73,24 m³/s po 26 h w KZGW. Różnica
nie wynika z parametrów, które są zgodne, lecz z kształtu: KZGW rysuje hydrogram jednostkowy
odcinkami prostymi, Hydrolog krzywą gamma. Przy metodzie Snydera kształt trzeba więc zawsze podać
razem z wynikiem.

### Przykład 5.5. Hydrogram Snydera Kamiennika

Kamiennik: $L$ = 15,88 km (najdłuższa droga spływu), $L_c$ = 6,76 km, wartości domyślne $C_t$ i
$C_p$, czas trwania opadu równy krokowi 10 min, jak w generatorze hydrogramu:

```sh
hydrolog uh snyder --area-km2 37.22 --length-km 15.88 --centroid-length-km 6.76 --timestep-min 10 --rainfall-duration-min 10
```

Czas opóźnienia $t_L$ wynosi 366,0 min (6,10 h), standardowy czas trwania opadu $t_D$ = 66,55 min;
dla $D$ = 10 min skorygowany czas opóźnienia $t_{LR}$ = 351,86 min, czas do kulminacji $t_{pR}$ =
356,86 min, kulminacja $q_{pR}$ = 1,0472 m³/(s·mm), a podstawa trójkąta $t_b$ = 1185,7 min.
Hydrogram narasta prawie trzy razy wolniej i ma ponad trzy razy niższą kulminację niż hydrogram
SCS z przykładu 5.3; do tej różnicy wracamy w p. 5.8.

## 5.5. Chwilowy hydrogram jednostkowy Nasha

**Idea.** Nash (1957) zastąpił zlewnię kaskadą $n$ jednakowych **zbiorników liniowych** (ang.
*linear reservoir*), połączonych szeregowo; w każdym retencja jest proporcjonalna do odpływu przez
**stałą retencji** $K$ (ang. *storage constant*). Odpowiedzią kaskady na chwilowy impuls jest
gęstość rozkładu gamma o parametrze kształtu $n$ i parametrze skali $K$. Środek ciężkości IUH, a
więc czas opóźnienia od środka ciężkości opadu efektywnego do środka ciężkości odpływu, leży w
chwili $nK$; wariancja IUH wynosi $nK^2$, a kulminacja przypada w chwili $(n - 1)K$, gdy $n > 1$
(KZGW 2017, wzory 6.13–6.16). Parametr $n$ nie musi być całkowity. Ta sama odpowiedź impulsowa opisuje
kaskadę zbiorników w korycie (rozdz. 6, ramka `linear_reservoir_cascade`).

<!-- spec:nash_iuh -->

<a id="spec-nash_iuh"></a>

> **Hydrogram jednostkowy chwilowy Nasha i jego hydrogram jednostkowy dla czasu trwania opadu** · specyfikacja [`nash_iuh`](../FORMULAS.md#nash_iuh) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> u(t) = \frac{1}{K\,\Gamma(n)}\left(\frac{t}{K}\right)^{n-1} e^{-t/K};\quad t_{lag} = n K;\quad S(t) = P\!\left(n, \frac{t}{K}\right);\quad U_D(t) = \frac{S(t) - S(t - D)}{D}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $n$ | `n` | Liczba zbiorników kaskady, parametr kształtu; nie musi być całkowita | – | (0; ∞) | nie podano w źródłach | [1,1; 8] (źr. 4) |
> | $K$ | `k_min` | Stała retencji każdego zbiornika | min | (0; ∞) | nie podano w źródłach | [0,8; 270] (źr. 5) |
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 6) |
> | $\Delta t$ | `timestep_min` | Krok czasowy rzędnych | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 7) |
> | $D$ | `duration_min` | Czas trwania jednostkowego opadu efektywnego | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 7) |
> | $T$ | `total_duration_min` | Długość hydrogramu; `NashIUH` przyjmuje 5 n K + D | min | (0; ∞) | nie podano w źródłach | [9; 10 860] (źr. 8) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $i \Delta t$ | `times_min` (ciąg) | Chwile rzędnych liczone od początku opadu | min | [0; ∞) |
> | $u(i \Delta t)$ | `iuh_ordinates_per_min` (ciąg) | Rzędne hydrogramu jednostkowego chwilowego w tych chwilach | 1/min | [0; ∞) |
> | $q_i$ | `ordinates_m3s` (ciąg) | Rzędne hydrogramu jednostkowego dla czasu trwania D | m³/s na mm | [0; ∞) |
> | $t_{lag}$ | `lag_time_min` | Czas opóźnienia, pierwszy moment hydrogramu jednostkowego chwilowego | min | (0; ∞) |
> | $t_p$ | `time_to_peak_min` | Chwila największej rzędnej hydrogramu jednostkowego | min | [0; ∞) |
> | $q_p$ | `peak_discharge_m3s` | Największa rzędna hydrogramu jednostkowego | m³/s na mm | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | siatka ma najwyżej milion rzędnych | `length_bounded` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
> | float64 przedstawia T / K, 1 / K oraz 1 mm nad zlewnią na sekundę czasu D, A x 1 mm / D, a n, K i D są liczbami znormalizowanymi (niekompletna funkcja gamma SciPy dla n podnormalnego nie jest monotoniczna) | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 10) |
>
> **Konwencje**
>
> - czasy w min od początku opadu; hydrogram chwilowy w 1/min; rzędne w m³/s na mm
> - hydrogram chwilowy w t = 0 ma na siatce wartość 0, także dla n <= 1, gdzie gęstość wynosi 1 / K (n = 1) lub jest nieograniczona (n < 1), gdy t dąży do 0
> - hydrogram jednostkowy dla D to hydrogram chwilowy uśredniony w czasie D za pomocą dokładnej krzywej S, czyli wzory 6.22-6.23 KZGW dla D = dt: D nie musi być całkowitą wielokrotnością kroku; D dużo krótsze niż dt traci cyfry znaczące w różnicy S(t) - S(t - D)
> - S(t) - S(t - D) to różnica P tam, gdzie S(t) <= 1/2, a dalej różnica Q = 1 - P, regularyzowanej górnej niekompletnej funkcji gamma: P z SciPy nie jest monotoniczna względem t dla n rzędu 1e-12 i mniejszych (i przekracza 1 poniżej 1e-14), a jej Q jest
> - siatka kończy się w T (`NashIUH`: 5 n K + D, a dla samego hydrogramu chwilowego max(5 n K, 10 K)): rzędne mieszczą S(T) jednostki, mniej niż 1 mm o ogon poza T
> - n poza przedziałem od 1 do 10 lub K poza przedziałem od 10 do 200 min podane klasie `NashIUH` dają uwagę `outside_unverified_range` (`nash.n`, `nash.k_min`): żadne źródło nie publikuje tych przedziałów
>
> **Założenia**
>
> - zlewnia odpowiada jak kaskada n jednakowych zbiorników liniowych
> - opad efektywny równomierny na całej zlewni i w czasie D
>
> **Zgodność z obserwacjami według źródeł:** brak: Nash (1957) podaje model; n i K dopasowuje się do wezbrań obserwowanych lub szacuje (specyfikacje `lutz` i `nash_urban_regression`), a źródła nie podają żadnej statystyki błędu kształtu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), annex 2, section 3.1.2, p. 96: eqs. 6.13 (the IUH) and 6.15 (LAG = N k); p. 99: eqs. 6.22-6.23, the ordinates of the unit hydrograph of dt as the IUH averaged over dt times A / 3.6 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236, eqs. 8-10, p. 1225: the IUH of the cascade, tp and up <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>
> 3. Nash, J.E. (1957). The form of the instantaneous unit hydrograph. International Association of Scientific Hydrology, Publication 45(3): 114-121, the IUH of a cascade of n equal linear reservoirs of storage constant K, a gamma density of shape n and scale K, and its first moment n K (not opened; the equations as KZGW 2017 and Sikorska et al. 2012 print them)
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), Table C.2, pp. 132-133: N from 1.10 to 7.99, the cascades the method reads off <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: K of 0.87 to 264.3 min by the spec lutz for the shortest and the longest flow path, 23.7 to 107.4 min by the spec nash_urban_regression for its points; KZGW Ex. 6.2: 42 min
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 7. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 8. Hydrolog: the default length 5 n K + D over the typical ranges of n, K and D, 5 x 1.1 x 0.8 + 5 = 9.4 to 5 x 8 x 270 + 60 = 10,860 min
> 9. Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one
> 10. IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308
>
> Funkcja `hydrolog.runoff.nash_iuh.nash_unit_hydrograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:nash_iuh -->

<!-- spec:nash_iuh_peak -->

<a id="spec-nash_iuh_peak"></a>

> **Czas do szczytu i rzędna szczytowa hydrogramu jednostkowego chwilowego Nasha** · specyfikacja [`nash_iuh_peak`](../FORMULAS.md#nash_iuh_peak) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_p = (n - 1) K;\quad u_p = \frac{(n-1)^{n-1} e^{-(n-1)}}{K\,\Gamma(n)}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $n$ | `n` | Liczba zbiorników kaskady, parametr kształtu; nie musi być całkowita | – | (0; ∞) | nie podano w źródłach | [1,1; 8] (źr. 3) |
> | $K$ | `k_min` | Stała retencji każdego zbiornika | min | (0; ∞) | nie podano w źródłach | [0,8; 270] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_p$ | `time_to_peak_min` | Chwila szczytu hydrogramu jednostkowego chwilowego, czyli jego dominanta | min | (0; ∞) |
> | $u_p$ | `peak_ordinate_per_min` | Rzędna szczytowa hydrogramu jednostkowego chwilowego | 1/min | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | n > 1: dla n <= 1 hydrogram chwilowy maleje od t = 0, gdzie wynosi 1 / K (n = 1) lub jest nieograniczony (n < 1), więc nie ma szczytu dla t > 0 | `peak_defined` | odmowa obliczeń: wzór jest nieokreślony | (źr. 5) |
> | K jest liczbą znormalizowaną, a float64 przedstawia 1 / K, ograniczenie szczytu | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 6) |
>
> **Konwencje**
>
> - tp w min od chwili opadu, up w 1/min
> - `NashIUH.time_to_peak_min` i `peak_ordinate_per_min` są puste (null) dla n <= 1, z uwagą `iuh_peak_undefined`, tam gdzie wersje do 0.8.1 podawały 0 i 1 / K
>
> **Założenia**
>
> - hydrogram jednostkowy chwilowy kaskady n jednakowych zbiorników liniowych (specyfikacja `nash_iuh`)
>
> **Zgodność z obserwacjami według źródeł:** brak: dokładne własności gęstości gamma Nasha (1957); źródła nie podają żadnej statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), annex 2, section 3.1.2, p. 96: eqs. 6.14 (tp) and 6.16 (up) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236, eqs. 9-10, p. 1225: tp and up of the IUH of the cascade <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>
> 3. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), Table C.2, pp. 132-133: N from 1.10 to 7.99, the cascades the method reads off <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: K of 0.87 to 264.3 min by the spec lutz for the shortest and the longest flow path, 23.7 to 107.4 min by the spec nash_urban_regression for its points; KZGW Ex. 6.2: 42 min
> 5. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 96, eq. 6.14: tp = (N - 1) k, positive for N > 1 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 6. IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308
>
> Funkcja `hydrolog.runoff.nash_iuh.nash_iuh_peak`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:nash_iuh_peak -->

Hydrogram jednostkowy kroku $\Delta t$ jest średnią IUH w tym kroku, pomnożoną przez powierzchnię
zlewni i przeliczoną na m³/(s·mm) (KZGW 2017, wzory 6.22–6.23). Średnią Hydrolog liczy dokładnie,
z różnicy krzywej S, którą dla kaskady Nasha jest dystrybuanta rozkładu gamma (niepełna funkcja
gamma). Hydrogram trwa domyślnie do chwili, w której odpłynęła prawie cała objętość.

**Interpretacja.** Parametr $n$ steruje kształtem: $n$ = 1 to jeden zbiornik (od razu najwyższa
rzędna, potem zanik wykładniczy), większe $n$ dają hydrogram coraz bardziej symetryczny i wąski
względem czasu kulminacji. $K$ przy stałym $n$ rozciąga hydrogram w czasie. Hydrolog uznaje za
typowe wartości $n$ i $K$ podane w opisie polecenia `uh nash`, ale te zakresy nie mają
opublikowanego źródła i czekają na weryfikację; tak samo granica kroku czasowego, która dla modelu
SCS pochodzi z NEH 630, a dla modeli Nasha, Clarka i Snydera jest tylko praktyczną regułą (uwaga
`outside_unverified_range`, ADR-0058).

### Przykład 5.6. Potok Niedźwiadka z parametrami KZGW

KZGW (2017, przykład 6.2, tabela 6.2): $n$ = 2,55, $K$ = 0,70 h = 42 min, $A$ = 7,2 km², krok 1 h:

```sh
hydrolog uh nash --area-km2 7.2 --n 2.55 --k-min 42 --timestep-min 60
```

| Czas [h] | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| KZGW (2017), tab. 6.2 [m³/(s·mm)] | 0,528 | 0,771 | 0,425 | 0,175 | 0,063 |
| Hydrolog [m³/(s·mm)] | 0,532 | 0,774 | 0,426 | 0,175 | 0,063 |

Czas opóźnienia $nK$ = 107,1 min. Ten hydrogram jednostkowy splata przykład 5.1.

## 5.6. Parametry Nasha metodą Lutza

**Cel.** Oszacować $n$ i $K$ zlewni niekontrolowanej z jej charakterystyk. Lutz (1984) opracował
zależności na podstawie zlewni południowo-zachodnich Niemiec; KZGW (2017, s. 96–100) zaleca je dla
zlewni quasi-naturalnych, o niewielkim uszczelnieniu i zabudowie rozłożonej względnie równomiernie,
jako alternatywę dla modelu Snydera (zakres powierzchni w założeniach ramki). Najpierw liczy się
czas do kulminacji $t_p$ z geometrii cieku, szorstkości koryta i udziałów zabudowy i lasów, potem
rzędną kulminacyjną IUH $u_p$, a z nich $n$ i $K$:

<!-- spec:lutz -->

<a id="spec-lutz"></a>

> **Parametry n i K kaskady Nasha dla zlewni niekontrolowanej metodą Lutza (KZGW 2017)** · specyfikacja [`lutz`](../FORMULAS.md#lutz) · wersja wzoru 1 · status: **sprawdzony na przypadkach referencyjnych** (`referenced`)
>
> $$
> t_p = P_1 \left(\frac{L\,L_c}{J_g^{1{,}5}}\right)^{0{,}26} e^{-0{,}016\,U} e^{0{,}004\,W},\quad P_1 = 3{,}989\,n_M + 0{,}028,\quad u_p = \frac{0{,}66}{t_p^{1{,}04}},\quad \frac{(N-1)^N e^{-(N-1)}}{\Gamma(N)} = t_p\,u_p,\quad K = \frac{t_p}{N-1}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $L$ | `length_km` | Długość wzdłuż cieku głównego od przekroju zamykającego do działu wodnego: najdłuższa droga spływu | km | (0; ∞) | nie podano w źródłach | [0,05; 30] (źr. 3) |
> | $Lc$ | `centroid_length_km` | Długość wzdłuż cieku głównego od przekroju zamykającego do jego punktu najbliższego środkowi ciężkości zlewni | km | (0; ∞) | nie podano w źródłach | [0,004; 15] (źr. 4) |
> | $Jg$ | `slope_m_per_m` | Spadek profilu podłużnego cieku głównego uśredniony metodą równych pól (specyfikacja `equal_area_slope`), a nie spadek między jego końcami | m/m | (0; ∞) | nie podano w źródłach | [0,002; 0,11] (źr. 5) |
> | $nM$ | `manning_n` | Współczynnik szorstkości Manninga koryta głównego | $\mathrm{s\,m^{-1/3}}$ | (0; ∞) | nie podano w źródłach | [0,025; 0,035] (źr. 6) |
> | $U$ | `urban_pct` | Udział terenów zurbanizowanych w powierzchni zlewni | % | [0; 100] | nie podano w źródłach | [0; 10] (źr. 7) |
> | $W$ | `forest_pct` | Udział lasów w powierzchni zlewni | % | [0; 100] | nie podano w źródłach | [0; 100] (źr. 8) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $tp$ | `time_to_peak_h` | Czas do kulminacji chwilowego hydrogramu jednostkowego | h | (0; ∞) |
> | $up$ | `peak_ordinate_per_h` | Rzędna kulminacyjna chwilowego hydrogramu jednostkowego (dt -> 0) | 1/h | (0; ∞) |
> | $N$ | `n` | Liczba zbiorników kaskady Nasha | – | (1; ∞) |
> | $K$ | `k_min` | Stała retencji każdego zbiornika | min | (0; ∞) |
> | $P1$ | `p1` | Parametr szorstkościowy Lutza w zależności na tp | $\mathrm{h\,km^{-0{,}52}}$ | (0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | Lc <= L: obie długości mierzy się wzdłuż cieku głównego od przekroju zamykającego, Lc do jego punktu najbliższego środkowi ciężkości zlewni, L do działu wodnego | `centroid_within_length` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 9) |
> | U + W <= 100: tereny zurbanizowane i lasy to udziały w powierzchni tej samej zlewni, które się nie pokrywają | `shares_within_catchment` | odmowa obliczeń: wartości niemożliwe fizycznie | (źr. 10) |
> | f(1,1) <= tp up <= f(20), tp od około 3,4e-11 do 3,4e23 h: pierwiastek N równania f(N) = tp up leży w przeszukiwanym przedziale, zaczynającym się od pierwszego wiersza tab. C.2, a float64 mieści każdy krok obliczeń | `root_in_bracket` | odmowa obliczeń: wzór jest nieokreślony | (źr. 11) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $3{,}989$ | `p1_slope` | Współczynnik kierunkowy zależności parametru szorstkościowego od współczynnika n Manninga | 3,989 | $\mathrm{h\,km^{-0{,}52}\,s^{-1}\,m^{1/3}}$ | (źr. 12) |
> | $0{,}028$ | `p1_intercept` | Wyraz wolny zależności parametru szorstkościowego od współczynnika n Manninga | 0,028 | $\mathrm{h\,km^{-0{,}52}}$ | (źr. 13) |
> | $1{,}5$ | `slope_exponent` | Wykładnik spadku cieku głównego w czynniku geometrycznym | 1,5 | – | (źr. 14) |
> | $0{,}26$ | `geometric_exponent` | Wykładnik czynnika geometrycznego w zależności na czas do kulminacji | 0,26 | – | (źr. 14) |
> | $-0{,}016$ | `urban_coefficient` | Współczynnik przy udziale terenów zurbanizowanych w wykładniku funkcji wykładniczej | −0,016 | 1/% | (źr. 14) |
> | $0{,}004$ | `forest_coefficient` | Współczynnik przy udziale lasów w wykładniku funkcji wykładniczej | 0,004 | 1/% | (źr. 14) |
> | $0{,}66$ | `peak_coefficient` | Współczynnik zależności rzędnej kulminacyjnej od czasu do kulminacji | 0,66 | $\mathrm{h^{0{,}04}}$ | (źr. 15) |
> | $1{,}04$ | `peak_exponent` | Wykładnik czasu do kulminacji w zależności na rzędną kulminacyjną | 1,04 | – | (źr. 16) |
>
> **Konwencje**
>
> - up = 0,66 / tp**1,04 to zależność Lutza dla dt -> 0 (KZGW 2017, wzór 6.19, s. 98), czyli kulminacja chwilowego hydrogramu jednostkowego; hydrogram jednostkowy dla kroku dt uśrednia ten chwilowy hydrogram dokładnie na przedziale dt (`NashIUH.to_unit_hydrograph`). Przykład 6.2 KZGW (s. 100) przyjmuje natomiast zależność dla dt = 1 h, up = 0,464 / tp**0,824, a Sikorska i in. (2012, tab. 1) stwierdzają, że P2 i P3 zależą od przedziału czasu: tamto podejście daje N 2,55 i k 0,70 h, podczas gdy przyjęte tutaj daje N 3,88 i K 0,377 h (przypadek `kzgw2017-ex6-2-n-k`, rozbieżność)
> - P1 = 3,989 nM + 0,028: wzór 6.18 (KZGW 2017, s. 97) podaje „- 0,028”, co jest błędem druku, jak pokazują rys. 6.3 (P1 = 3,9886 n + 0,0284) i przykład 6.2 (P1 = 0,128 dla n = 0,025)
> - 0,66 ze wzoru 6.19 KZGW, a nie 0,64 podane przez Sikorską i in. (2012, tab. 1), którzy powołują się na tę samą pracę Lutza (1984)
> - L i Lc w km, Jg w m/m — spadek profilu podłużnego cieku głównego uśredniony metodą równych pól (KZGW 2017, s. 97; specyfikacja `equal_area_slope`), nM w s m^-1/3, U i W w procentach powierzchni zlewni; tp w h, up w 1/h, K zwracane w min po przeliczeniu przez dokładne 60 min/h
> - N jest rozwiązaniem równania f(N) = tp up na przedziale [1,1; 20] metodą Brenta (`scipy.optimize.brentq`, `xtol` 1e-6), podczas gdy KZGW odczytuje je z tab. C.2 (s. 132–133); f jest tam ściśle rosnąca, od 0,0755 do 1,731, i zgadza się z 13 wierszami tabeli od N = 1,10 do 7,99 z dokładnością do połowy ostatniej drukowanej cyfry
>
> **Założenia**
>
> - zlewnie o powierzchni do 236 km² z zabudową rozmieszczoną dość równomiernie (KZGW 2017, s. 97); `NashIUH.from_lutz` ostrzega przy większej powierzchni; dane Lutza obejmowały 75 zlewni o powierzchni do 250 km² (Sikorska i in. 2012, s. 1225)
> - zlewnia zbliżona do naturalnej: KZGW (2017, s. 96) stosuje model Nasha z parametrami Lutza przy udziale powierzchni nieprzepuszczalnych poniżej 5 %
>
> **Zgodność z obserwacjami według źródeł:** Lutz (1984) dopasował zależności do 75 zlewni południowo-zachodnich Niemiec o powierzchni do 250 km² (Sikorska i in. 2012, s. 1225); KZGW (2017, rys. 6.3) podaje R² = 0,9974 dla zależności P1 od współczynnika n Manninga; żadne źródło dostępne dla Hydrologu nie podaje błędów tp, up ani przepływów kulminacyjnych względem obserwacji
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), annex 2, section 3.1.2, pp. 97-98: eqs. 6.17-6.21, Fig. 6.3 and the definitions of L, Lc, Jg, U and W; Ex. 6.2, pp. 99-100; Table C.2, pp. 132-133 (N against f(N)) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236, Table 1, p. 1226: Lutz's tp with the exponent 0.26 and up = P2 / tp**P3, P2 = 0.64 and P3 = 1.04, 'dependent on the interval of estimation' <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km
> 4. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Lc of 0.0042 to 14.49 km
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: slopes between the ends of the flow paths, 0.00244 to 0.1055 m/m, which bound their equal-area slopes on concave profiles (Kamiennik: 0.00848 against 0.0114)
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); and Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), KZGW Ex. 6.2, p. 99: n = 0.025 for the Niedźwiadka; tests/fixtures/kamiennik.json: n = 0.035 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: urbanized shares of 0 to 9 %
> 8. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: forest shares of 0 to 100 %
> 9. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the definitions of L and Lc under eq. 6.17 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 10. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the definitions of U and W under eq. 6.17 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 11. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.20, p. 98, and Table C.2, pp. 132-133, from N = 1.10 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 12. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.18, p. 97; Fig. 6.3, p. 98: P1 = 3.9886 n + 0.0284 (R2 = 0.9974), after Lutz (1984) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 13. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), Fig. 6.3, p. 98 (+0.0284) and Ex. 6.2, p. 99 (P1 = 0.128 for n = 0.025); eq. 6.18, p. 97, prints '- 0,028', a misprint <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 14. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 15. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.19, p. 98, for dt -> 0; Sikorska et al. 2012, Table 1, give P2 = 0.64 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 16. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.19, p. 98; the same in Sikorska et al. 2012, Table 1 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
>
> Funkcja `hydrolog.runoff.nash_iuh.lutz_parameters`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:lutz -->

Zmienne wejściowe:

- $L$ — długość cieku głównego od przekroju do **działu wodnego**: w Hydrologu najdłuższa droga
  spływu `flow_path_length_km` (ADR-0024);
- $L_c$ — długość wzdłuż cieku od przekroju do punktu najbliższego środkowi ciężkości zlewni;
- $J_g$ — **spadek wyrównany** cieku głównego (p. niżej);
- $n_M$ — współczynnik szorstkości Manninga koryta głównego;
- $U$ i $W$ — udziały terenów zurbanizowanych i lasów w powierzchni zlewni, w procentach.

Las i szorstkie koryto wydłużają $t_p$ i spłaszczają wezbranie, zabudowa i większy spadek je
skracają.

**Spadek wyrównany $J_g$.** KZGW (2017, s. 97) definiuje $J_g$ jako spadek prostej wychodzącej z
najniższego punktu profilu podłużnego cieku, dla której pola między prostą a profilem powyżej i
poniżej prostej są równe — w literaturze niemieckiej *gewogenes Gefälle*, po angielsku
*equal-area slope*. Hydrolog liczy go z profilu najdłuższej drogi spływu (ADR-0053):

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

Profil cieku jest zwykle wklęsły, więc spadek między końcami profilu jest większy od spadku
wyrównanego i skraca $t_p$. Dlatego Hydrolog nie przyjmuje w metodzie Lutza spadku między końcami
(`flow_path_slope_m_per_m`) i wymaga pola `flow_path_equal_area_slope_m_per_m`; zlewnia bez niego
daje błąd `missing_field`. Hydrograf liczy ten spadek z NMT i przekazuje go razem ze zlewnią.
Funkcja nie ma własnego polecenia; z profilu Kamiennika (1593 punkty NMT od przekroju w górę,
15,88 km, od 258,72 do 440,16 m n.p.m.) można ją wywołać z Pythona:

```python
import json
from hydrolog.morphometry import equal_area_slope

profil = json.load(open("tests/fixtures/kamiennik_flow_path_profile.json"))
print(equal_area_slope(profil["distance_m"], profil["elevation_m"]))   # 0.00847661771905156
```

Spadek wyrównany Kamiennika wynosi 0,00848, a spadek między końcami profilu 0,0114 — około jedną
trzecią więcej.

**Krok obliczeń i rzędna kulminacyjna — kwestia otwarta.** Zależność $u_p(t_p)$ w ramce to postać
Lutza dla $\Delta t \to 0$, czyli rzędna kulminacyjna IUH (KZGW 2017, wzór 6.19). Hydrolog wyznacza
z niej $n$ i $K$, a hydrogram kroku $\Delta t$ uśrednia IUH w kroku. Tymczasem przykład 6.2 KZGW dla
kroku 1 h stosuje inną, „przekształconą” postać zależności, a Sikorska i in. (2012) piszą, że jej
współczynniki zależą od kroku obliczeń. Dla potoku Niedźwiadka obie drogi dają wyraźnie różne
parametry:

```sh
hydrolog uh nash --area-km2 7.2 --lutz-length-km 4.3 --lutz-centroid-length-km 2.7 --lutz-slope-m-per-m 0.03 --lutz-manning-n 0.025 --lutz-forest-pct 33.6 --timestep-min 60
```

| Wielkość | KZGW (2017), przykład 6.2 | Hydrolog |
|---|---|---|
| $P_1$ | 0,128 | 0,1277 |
| $t_p$ | 1,09 h | 1,085 h |
| $u_p$ | 0,433 1/h (postać dla kroku 1 h) | 0,606 1/h (postać dla $\Delta t \to 0$) |
| $n$ | 2,55 | 3,880 |
| $K$ | 0,70 h | 0,377 h = 22,60 min |
| kulminacja hydrogramu jednostkowego | 0,771 m³/(s·mm) | 0,989 m³/(s·mm) |

Czas $t_p$ jest zgodny; cała różnica pochodzi z postaci zależności $u_p(t_p)$. Kulminacja
hydrogramu jednostkowego Hydrologu jest o 28 % wyższa. Dla długiego opadu z tabeli 6.3 źródła
różnica maleje: splot z parametrami Lutza Hydrologu

```sh
hydrolog hydrograph generate --watershed '{"name":"Niedźwiadka km 3+450","area_km2":7.2,"flow_path_length_km":4.3,"flow_path_equal_area_slope_m_per_m":0.03,"Lc_km":2.7,"manning_n":0.025,"forest_pct":33.6}' --cn 100 --values 0,0,0,0,0,0,0,0,0,0,0,0,0.07,0.73,1.73,2.95,4.25,5.51,6.54,7.18,7.23,6.5,4.79,1.89 --timestep-min 60 --uh-model nash --nash-estimation lutz
```

daje kulminację 14,03 m³/s po 21 h, o 2,7 % więcej niż 13,66 m³/s źródła. Hydrolog świadomie
zostaje przy postaci dla $\Delta t \to 0$, spójnej z dokładnym uśrednieniem IUH (konwencje ramki);
możliwość wyboru postaci zależnej od kroku czeka na decyzję autora (TRIAGE T2). Rozstrzygnąć to może
dopiero oryginał Lutza (1984), niedostępny w otwartym dostępie. W raporcie z obliczeń trzeba więc
podawać, którą postać przyjęto.

**Zlewnie zurbanizowane.** Dla małych zlewni zurbanizowanych KZGW (2017, s. 107) podaje inną
regresję parametrów Nasha (Rao, Delleur i Sarma 1972): $n$ i $K$ zależą od powierzchni zlewni,
udziału powierzchni nieprzepuszczalnych oraz wysokości i czasu trwania opadu efektywnego, więc
liczy się je od nowa dla każdego opadu. Hydrolog oferuje ją w poleceniu `uh nash` (opcje
`--urban-…`). Częsty błąd to podanie udziału terenów zabudowanych zamiast udziału powierzchni
nieprzepuszczalnych.

<!-- spec:nash_urban_regression -->

<a id="spec-nash_urban_regression"></a>

> **Parametry n i K modelu Nasha dla zlewni zurbanizowanej z regresji Rao, Delleura i Sarmy (1972)** · specyfikacja [`nash_urban_regression`](../FORMULAS.md#nash_urban_regression) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> LAG = 1{,}28\,A^{0{,}46}(1+U)^{-1{,}66}H^{-0{,}27}D^{0{,}37},\quad k = 0{,}56\,A^{0{,}39}(1+U)^{-0{,}62}H^{-0{,}11}D^{0{,}22},\quad N = \frac{LAG}{k}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | [0; 52] (źr. 4) | [1,3; 52] (źr. 5) |
> | $H$ | `effective_precip_mm` | Wysokość opadu efektywnego danego deszczu | mm | (0; ∞) | nie podano w źródłach | [1; 100] (źr. 6) |
> | $D$ | `duration_h` | Czas trwania opadu efektywnego | h | (0; ∞) | nie podano w źródłach | [0,167; 24] (źr. 7) |
> | $U$ | `urban_fraction` | Udział powierzchni nieprzepuszczalnych w powierzchni zlewni | – | [0; 1) | [0,05; 1] (źr. 8) | [0,05; 0,32] (źr. 9) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $LAG$ | `lag_time_h` | Czas opóźnienia hydrogramu jednostkowego chwilowego, N K | h | [0; ∞) |
> | $N$ | `n` | Liczba zbiorników kaskady Nasha | – | [0; ∞) |
> | $k$ | `k_min` | Stała retencji każdego zbiornika | min | [0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1{,}28$ | `lag_coefficient` | Współczynnik zależności czasu opóźnienia | 1,28 | $\mathrm{h\,km^{-0{,}92}\,mm^{0{,}27}\,h^{-0{,}37}}$ | (źr. 10) |
> | $0{,}46$ | `lag_area_exponent` | Wykładnik powierzchni zlewni w zależności czasu opóźnienia | 0,46 | – | (źr. 10) |
> | $-1{,}66$ | `lag_urban_exponent` | Wykładnik udziału powierzchni nieprzepuszczalnych w zależności czasu opóźnienia | −1,66 | – | (źr. 10) |
> | $-0{,}27$ | `lag_depth_exponent` | Wykładnik wysokości opadu efektywnego w zależności czasu opóźnienia | −0,27 | – | (źr. 10) |
> | $0{,}37$ | `lag_duration_exponent` | Wykładnik czasu trwania opadu efektywnego w zależności czasu opóźnienia | 0,37 | – | (źr. 10) |
> | $0{,}56$ | `k_coefficient` | Współczynnik zależności stałej retencji | 0,56 | $\mathrm{h\,km^{-0{,}78}\,mm^{0{,}11}\,h^{-0{,}22}}$ | (źr. 10) |
> | $0{,}39$ | `k_area_exponent` | Wykładnik powierzchni zlewni w zależności stałej retencji | 0,39 | – | (źr. 10) |
> | $-0{,}62$ | `k_urban_exponent` | Wykładnik udziału powierzchni nieprzepuszczalnych w zależności stałej retencji | −0,62 | – | (źr. 10) |
> | $-0{,}11$ | `k_depth_exponent` | Wykładnik wysokości opadu efektywnego w zależności stałej retencji | −0,11 | – | (źr. 10) |
> | $0{,}22$ | `k_duration_exponent` | Wykładnik czasu trwania opadu efektywnego w zależności stałej retencji | 0,22 | – | (źr. 10) |
>
> **Konwencje**
>
> - A w km², H w mm, D w h, U bezwymiarowe; LAG i k w h, K zwracane w min przez dokładne 60 min/h: stałe 1,28 i 0,56 obowiązują tylko dla tych jednostek (KZGW 2017, s. 107)
> - U to udział powierzchni nieprzepuszczalnych (KZGW 2017, s. 107; Sikorska i in. 2012, tab. 1), a nie udział terenów zabudowanych
> - iloczyn potęg A, H i D: wyrażają to własności skalowania, a jednostki niosą stałe (tą własnością nie jest jednorodność wymiarowa)
> - H i D dotyczą danego opadu: parametry zmieniają się z każdym opadem
>
> **Założenia**
>
> - zlewnie zurbanizowane o powierzchni do 52 km², których parametrów nie da się dopasować do pomierzonych opadów i odpływów (KZGW 2017, s. 107)
>
> **Zgodność z obserwacjami według źródeł:** Rao i in. (1972) dopasowali zależności do opadów w urbanizujących się zlewniach koło Indianapolis (tak podają je KZGW i Sikorska i in. 2012, bez statystyk błędu); KZGW (2017, s. 107) zaleca je tylko tam, gdzie parametrów nie da się dopasować do pomierzonych opadów i odpływów
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 6.26-6.28, p. 107 (U the fraction of impervious area, dimensionless); the same in Sikorska et al. 2012 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 2. Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236, Table 1, p. 1226: the same equations, U the fraction of the impervious area, Lag and k in h <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>
> 3. Rao, A.R., Delleur, J.W. and Sarma, B.S.P. (1972). Conceptual hydrologic models for urbanizing basins. Journal of the Hydraulics Division, ASCE 98(HY7), 1205-1220 — *źródło niedostępne publicznie (dostarczone przez autora)*
> 4. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 107: the relations for urbanized watersheds of up to 52 km2 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 5. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236; Hydrolog's catalog example of uh nash (urban regression), KZGW p. 107 (up to 52 km2); Sikorska et al. p. 1227 (the Służew Creek, 26.9 km2); src/hydrolog/catalog/groups/uh.py (1.3 km2) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); Hydrolog's catalog example of uh nash, KZGW Ex. 6.4, p. 109: effective depths of steps of 1.4 to 2.1 mm; Ex. 6.1, p. 93: 15.3 mm in an hour; the catalog's 1.305 mm <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); Hydrolog's catalog example of uh nash, KZGW ch. II.3, p. 25: a daily design storm split into hours; the catalog's 10 min (0.167 h) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 8. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 102 (zlewnia zurbanizowana: more than 5 % impervious) and p. 107 (the relations for urbanized watersheds) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 9. Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236; Hydrolog's catalog example, p. 1227: 32 % impervious in the Służew Creek; the catalog's 0.05 <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>
> 10. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 6.26-6.28, p. 107; Sikorska et al. (2012), Table 1, p. 1226; the same in Sikorska et al. 2012 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
>
> Funkcja `hydrolog.runoff.nash_iuh.urban_regression_parameters`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:nash_urban_regression -->

**Typowe błędy.** Spadek w ‰ lub % zamiast w m/m (30 zamiast 0,03 skraca $t_p$ wielokrotnie);
$L_c$ większe od $L$ (Hydrolog odrzuca takie dane); $L$ mierzone do początku koryta zamiast do działu
wodnego; spadek między końcami profilu zamiast spadku wyrównanego; stosowanie metody w zlewni
zurbanizowanej.

### Przykład 5.7. Parametry Lutza dla Kamiennika

Kamiennik: $L$ = 15,88 km, $L_c$ = 6,76 km, $J_g$ = 0,00848, $n_M$ = 0,035, $U$ = 1 %,
$W$ = 57,4 %:

```sh
hydrolog uh nash --area-km2 37.22 --lutz-length-km 15.88 --lutz-centroid-length-km 6.76 --lutz-slope-m-per-m 0.00848 --lutz-manning-n 0.035 --lutz-urban-pct 1 --lutz-forest-pct 57.4 --timestep-min 10
```

Hydrolog podaje $P_1$ = 0,1676, $t_p$ = 4,498 h, $u_p$ = 0,1382 1/h, $n$ = 3,587 i $K$ = 104,30 min
(1,738 h). Czas opóźnienia $nK$ wynosi 374,2 min, kulminacja hydrogramu jednostkowego
1,4277 m³/(s·mm) w 270. minucie. Ta sama zlewnia ze spadkiem między końcami profilu (0,0114,
polecenie z `--lutz-slope-m-per-m 0.0114`) dałaby $n$ = 3,610, $K$ = 92,13 min i kulminację
1,6096 m³/(s·mm) w 250. minucie — o 13 % wyższą i 20 minut wcześniejszą.

## 5.7. Chwilowy hydrogram jednostkowy Clarka

**Idea.** Clark (1945) rozdzielił dwa procesy. **Translację** (ang. *translation*), czyli
przemieszczanie się opadu efektywnego do przekroju, opisuje **krzywa czas–powierzchnia** (ang.
*time–area curve*): jaka część zlewni dopływa do przekroju w czasie $t$. Buduje się ją z
**izochron** (ang. *isochrones*); gdy nie są znane, Hydrolog, tak jak HEC-HMS, przyjmuje krzywą
zlewni eliptycznej. **Wytłumienie** (ang. *attenuation*), czyli retencję zlewni, opisuje jeden
zbiornik liniowy o stałej retencji $R$, przez który przepuszcza się wynik translacji. Hydrogram
kroku $\Delta t$ powstaje z krzywej S.

<!-- spec:clark -->

<a id="spec-clark"></a>

> **Hydrogram jednostkowy Clarka dla czasu trwania opadu: krzywa czas–powierzchnia i zbiornik liniowy** · specyfikacja [`clark`](../FORMULAS.md#clark) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> \frac{A_t}{A} = 1{,}414\left(\frac{t}{t_c}\right)^{1{,}5},\ t \le \frac{t_c}{2};\quad O_i = O_{i-1} + \frac{\Delta t}{2R + \Delta t}\,(I_i + I_{i-1} - 2\,O_{i-1});\quad U_D(t) = \frac{S(t) - S(t - D)}{D}
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji, czyli czas translacji zlewni | min | (0; ∞) | nie podano w źródłach | [1; 450] (źr. 3) |
> | $R$ | `r_min` | Stała retencji zbiornika liniowego, S = R O | min | (0; ∞) | nie podano w źródłach | [0,2; 1050] (źr. 4) |
> | $A$ | `area_km2` | Powierzchnia zlewni | km² | (0; ∞) | nie podano w źródłach | [0,0003; 250] (źr. 5) |
> | $\Delta t$ | `timestep_min` | Krok czasowy rzędnych i zbiornika | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 6) |
> | $D$ | `duration_min` | Czas trwania jednostkowego opadu efektywnego | min | (0; ∞) | nie podano w źródłach | [5; 60] (źr. 6) |
> | $T$ | `total_duration_min` | Długość hydrogramu; `ClarkIUH` przyjmuje tc + 5 R + D | min | (0; ∞) | nie podano w źródłach | [7; 5760] (źr. 7) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $i \Delta t$ | `times_min` (ciąg) | Chwile rzędnych liczone od początku opadu | min | [0; ∞) |
> | $q_i$ | `ordinates_m3s` (ciąg) | Rzędne hydrogramu jednostkowego dla czasu trwania D | m³/s na mm | [0; ∞) |
> | $t_p$ | `time_to_peak_min` | Chwila największej rzędnej | min | [0; ∞) |
> | $q_p$ | `peak_discharge_m3s` | Największa rzędna | m³/s na mm | [0; ∞) |
>
> **Warunki**
>
> | Warunek | Nazwa | Gdy nie jest spełniony | Źródło |
> |---|---|---|---|
> | krok czasowy wynosi najwyżej dwukrotność stałej retencji, dt <= 2 R (z tolerancją 1e-9 · 2 R na zaokrąglenia): powyżej tej granicy poprzedni odpływ ma ujemną wagę (2 R - dt) / (2 R + dt), a rzędne oscylują poniżej 0 | `step_stable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 8) |
> | siatka ma najwyżej milion rzędnych | `length_bounded` | odmowa obliczeń: wzór jest nieokreślony | (źr. 9) |
> | float64 przedstawia jako liczby znormalizowane pierwszy odpływ ze zbiornika, C A(dt) / A, oraz 1 mm nad zlewnią na sekundę czasu D, A x 1 mm / D | `representable` | odmowa obliczeń: wzór jest nieokreślony | (źr. 10) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1{,}414$ | `time_area_factor` | Współczynnik krzywej czas–powierzchnia zlewni eliptycznej | 1,414 | – | (źr. 11) |
> | $1{,}5$ | `time_area_exponent` | Wykładnik krzywej czas–powierzchnia zlewni eliptycznej | 1,5 | – | (źr. 11) |
>
> **Konwencje**
>
> - czasy w min od początku opadu; rzędne w m³/s na mm
> - krzywa czas–powierzchnia zlewni eliptycznej z HEC-HMS, z 1,414 zamiast pierwiastka z 2 (połówki spotykają się w 0,49992 i 0,50008, uskok 1,6e-4)
> - zbiornik liczony metodą trapezów, O_i = O_i-1 + C (I_i + I_i-1 - 2 O_i-1), gdzie C = dt / (2 R + dt): to równanie HEC-HMS O_t = CA I_t + CB O_t-1 wraz z jego średnią z dwóch odpływów, z uśrednianiem przeniesionym z odpływu na dopływ, co daje ten sam wynik dla zbiornika startującego ze stanu spoczynku
> - siatka kończy się w T (`ClarkIUH`: tc + 5 R + D), podczas gdy HEC-HMS zatrzymuje się przy 0,995 objętości; oba dzielą rzędne po transformacji przez ich objętość, sprowadzając ją do jednej jednostki
> - hydrogram jednostkowy dla D z krzywej S, z S(t - D) interpolowanym liniowo między węzłami siatki: D nie musi być całkowitą wielokrotnością kroku, a D krótsze niż dt daje hydrogram dla D = dt
> - R/tc poza przedziałem od 0,2 do 1,5 daje uwagę `outside_unverified_range` klasy `ClarkIUH` (`clark.r_tc_ratio`): żadne źródło nie publikuje tego przedziału, a polskie kalibracje dla Stobnicy dają od 1,7 do 2,3 (Wałęga i Cupak 2013)
>
> **Założenia**
>
> - tc to czas translacji z najdalszego punktu zlewni; krzywa czas–powierzchnia jest krzywą zlewni eliptycznej, chyba że znana jest właściwa krzywa
> - opad efektywny równomierny na całej zlewni i w czasie D
>
> **Zgodność z obserwacjami według źródeł:** brak: Clark (1945) i HEC-HMS podają model; jego parametry tc i R kalibruje się na wezbraniach obserwowanych (HEC-HMS), a źródła nie podają żadnej statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eqs. 47-50, pp. 58-59 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 2. USACE-HEC. HEC-HMS Technical Reference Manual (online, read 2026-11-19), chapter Transform, Clark Unit Hydrograph Model: the time-area curve of an elliptical watershed, O_t = CA I_t + CB O_t-1, CA = dt / (R + 0.5 dt), the unit hydrograph the mean of two outflows <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/clark-unit-hydrograph-model>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Kirpich's tc of the flow paths of the 27 watersheds, the default method of hydrograph generate, 1.04 to 450 min
> 4. Wałęga, A. and Cupak, A. (2013). In Węglarczyk, S. (ed.), Problemy obliczania przepływów ekstremalnych, Monografie Komitetu Gospodarki Wodnej PAN 35, pp. 145-151, table 2, p. 148: R of 12.14 and 17.4 h calibrated for the Stobnica (335.84 km2); and Hydrolog's R/tc of 0.2 to 1.5 times the typical tc of 1 to 450 min, R from 0.2 min <https://kgw.pan.pl/files/35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf>
> 5. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)
> 6. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
> 7. Hydrolog: the default length tc + 5 R + D over the typical ranges of tc, R and D, 1 + 5 x 0.2 + 5 = 7 to 450 + 5 x 1050 + 60 = 5,760 min
> 8. Hydrolog ADR-0008, the conventions of routing: the window of non-negative weights of the Muskingum scheme, dt <= 2 K (1 - X), here X = 0 and K = R
> 9. Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one
> 10. IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308
> 11. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eq. 50, p. 59: At / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for t >= tc / 2 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
>
> Funkcja `hydrolog.runoff.clark_iuh.clark_unit_hydrograph`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:clark -->

Środek ciężkości krzywej czas–powierzchnia zlewni eliptycznej leży w połowie czasu koncentracji,
więc czas opóźnienia hydrogramu Clarka (od środka ciężkości opadu do środka ciężkości odpływu) jest
sumą połowy $t_c$ i stałej $R$; polecenie `uh clark` podaje go jako `lag_time_min`. Większe $R$
spłaszcza i wydłuża hydrogram, większe $t_c$ przesuwa kulminację.

<!-- spec:clark_lag -->

<a id="spec-clark_lag"></a>

> **Czas opóźnienia modelu Clarka: środek ciężkości krzywej czas–powierzchnia plus R** · specyfikacja [`clark_lag`](../FORMULAS.md#clark_lag) · wersja wzoru 1 · status: **sprawdzony tylko wyroczniami** (`oracle only`)
>
> $$
> t_{lag} = \frac{t_c}{2} + R
> $$
>
> **Dane wejściowe**
>
> | Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | Zakres stosowalności | Zakres typowy |
> |---|---|---|---|---|---|---|
> | $t_c$ | `tc_min` | Czas koncentracji, czyli czas translacji zlewni | min | (0; ∞) | nie podano w źródłach | [1; 450] (źr. 3) |
> | $R$ | `r_min` | Stała retencji zbiornika liniowego, S = R O | min | (0; ∞) | nie podano w źródłach | [0,2; 1050] (źr. 4) |
>
> **Wyniki**
>
> | Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |
> |---|---|---|---|---|
> | $t_{lag}$ | `lag_time_min` | Czas opóźnienia, pierwszy moment hydrogramu jednostkowego chwilowego Clarka liczony od chwili opadu | min | (0; ∞) |
>
> **Stałe**
>
> | Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |
> |---|---|---|---|---|---|
> | $1/2$ | `centroid_share` | Względne położenie środka ciężkości krzywej czas–powierzchnia, ułamek tc | 0,5 | – | (źr. 5) |
>
> **Konwencje**
>
> - opóźnienie od chwili jednostki opadu do środka ciężkości odpowiedzi, w min; hydrogram jednostkowy dla D jest opóźniony o dalsze D / 2 względem początku opadu
> - środek ciężkości eliptycznej krzywej czas–powierzchnia z HEC-HMS leży w tc / 2 niezależnie od jej współczynnika (1,414): pola, które jej dwie połówki odcinają od prostej A = 1, są równe
>
> **Założenia**
>
> - krzywa czas–powierzchnia zlewni eliptycznej (specyfikacja `clark`); inna krzywa ma inny środek ciężkości
>
> **Zgodność z obserwacjami według źródeł:** brak: dokładna własność modelu; parametry tc i R Clarka kalibruje się na wezbraniach obserwowanych (HEC-HMS), a źródła nie podają żadnej statystyki błędu
>
> **Źródła** (opisy w brzmieniu specyfikacji)
>
> 1. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eq. 50, p. 59: the time-area curve of an elliptical watershed, whose centroid is at tc / 2; eqs. 47-49, p. 58: the linear reservoir S = R O, whose response has the first moment R <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
> 2. Nash, J.E. (1959). Systematic determination of unit hydrograph parameters. Journal of Geophysical Research 64(1): 111-115, the theorem of moments: the first moment of a linear system's response to an input is the input's first moment plus the IUH's, so translation and reservoir add their lags (not opened) <https://doi.org/10.1029/JZ064i001p00111>
> 3. Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Kirpich's tc of the flow paths of the 27 watersheds, the default method of hydrograph generate, 1.04 to 450 min
> 4. Wałęga, A. and Cupak, A. (2013). In Węglarczyk, S. (ed.), Problemy obliczania przepływów ekstremalnych, Monografie Komitetu Gospodarki Wodnej PAN 35, pp. 145-151, table 2, p. 148: R of 12.14 and 17.4 h calibrated for the Stobnica (335.84 km2); and Hydrolog's R/tc of 0.2 to 1.5 times the typical tc of 1 to 450 min, R from 0.2 min <https://kgw.pan.pl/files/35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf>
> 5. USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eq. 50, p. 59: At / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for t >= tc / 2 <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
>
> Funkcja `hydrolog.runoff.clark_iuh.clark_lag_time`. Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; nie edytuj jej ręcznie.

<!-- /spec:clark_lag -->

**Krok obliczeń.** Zbiornik liniowy liczony wzorem trapezów ma wagę poprzedniego odpływu, która
staje się ujemna, gdy krok przekracza $2R$; rzędne zaczęłyby wtedy oscylować. Hydrolog odrzuca taki
krok (warunek `step_stable` w ramce, ADR-0058).

**Wybór $R$.** Podręcznik HEC-HMS nie podaje liczbowego stosunku $R/t_c$. Zakres typowy Hydrologu
(ramka) nie ma opublikowanego źródła i daje uwagę `outside_unverified_range`. Wałęga i Cupak (2013)
skalibrowali hydrogram Clarka dla zlewni Stobnicy (335,84 km², Pogórze Dynowskie) na dwóch
wezbraniach i otrzymali $t_c$ = 10 h, $R$ = 17,4 h oraz $t_c$ = 5,3 h, $R$ = 12,14 h — w obu
przypadkach $R$ wyraźnie większe od $t_c$. W Czechach ČHMÚ używa hydrogramu Clarka w HEC-HMS razem z
SCS-CN i transformacją Muskingum (Tyl i in. 2023). $R$ najlepiej wyznaczyć z zarejestrowanych
wezbrań; częstym błędem jest utożsamianie $t_c$ ze wzoru empirycznego (np. Kirpicha) z parametrem
kalibracyjnym modelu.

### Przykład 5.8. Hydrogram Clarka Kamiennika

Bez danych kalibracyjnych $R$ trzeba przyjąć. Dla $R = t_c$ = 208,63 min:

```sh
hydrolog uh clark --area-km2 37.22 --tc-min 208.63 --r-tc-ratio 1 --timestep-min 10
```

Czas opóźnienia wynosi 312,95 min, kulminacja hydrogramu jednostkowego 1,9151 m³/(s·mm) w 190.
minucie, objętość 1,0000 mm. Wpływ $R$ na hydrogram projektowy pokazuje tabela w p. 5.8.

## 5.8. Hydrogram projektowy Kamiennika

Łańcuch obliczeń dla Kamiennika w Świerzawie:

- opad: maksymalny opad o czasie trwania 12 h (720 min) i prawdopodobieństwie przewyższenia
  $p$ = 1 % z PMAXTP IMGW-PIB (metoda POT), 101,82 mm (rozdz. 2, plik
  `tests/fixtures/pmaxtp_kamiennik_pot.json`); hietogram Beta o parametrach domyślnych (2; 5), krok
  10 min;
- opad efektywny: SCS-CN, CN = 65, AMC II, $\lambda$ = 0,2; retencja maksymalna $S$ = 136,77 mm,
  straty początkowe 27,35 mm, opad efektywny 26,25 mm, współczynnik odpływu 0,258 (rozdz. 3);
- czas koncentracji (modele SCS i Clarka): Kerby–Kirpich, 208,63 min (rozdz. 4);
- hydrogram jednostkowy: cztery modele z poprzednich punktów.

Wysokość opadu pochodzi z PMAXTP: „Źródłem pochodzenia danych jest Instytut Meteorologii i
Gospodarki Wodnej – Państwowy Instytut Badawczy. Dane Instytutu Meteorologii i Gospodarki Wodnej –
Państwowego Instytutu Badawczego zostały przetworzone”.

Polecenie dla modelu SCS (pozostałe różnią się opcjami modelu podanymi w tabeli):

```sh
hydrolog hydrograph generate --watershed-file tests/fixtures/kamiennik.json --tc-method kerby_kirpich --hietogram-type beta --total-mm 101.82 --duration-min 720 --timestep-min 10 --uh-model scs
```

| Model hydrogramu jednostkowego | Opcje modelu | Kulminacja [m³/s] | Czas kulminacji od początku opadu | Objętość [m³] |
|---|---|---|---|---|
| SCS, $t_c$ Kerby–Kirpich | `--tc-method kerby_kirpich --uh-model scs` | 52,36 | 410 min (6 h 50 min) | 977 269 |
| SCS, $t_c$ Kirpich (187,13 min) | `--tc-method kirpich --uh-model scs` | 54,23 | 400 min | 977 249 |
| Snyder, $C_t$ 1,5, $C_p$ 0,6 | `--uh-model snyder --snyder-length-km 15.88 --snyder-centroid-length-km 6.76` | 25,20 | 670 min (11 h 10 min) | 977 074 |
| Nash, parametry Lutza | `--uh-model nash --nash-estimation lutz` | 32,17 | 580 min (9 h 40 min) | 977 067 |
| Clark, $R/t_c$ = 0,5 | `--tc-method kerby_kirpich --uh-model clark --clark-r-tc-ratio 0.5` | 47,14 | 450 min | 977 074 |
| Clark, $R/t_c$ = 1 | `--tc-method kerby_kirpich --uh-model clark --clark-r-tc-ratio 1` | 35,82 | 490 min | 977 074 |
| Clark, $R/t_c$ = 2 | `--tc-method kerby_kirpich --uh-model clark --clark-r-tc-ratio 2` | 24,15 | 540 min | 977 074 |

**Bilans objętości.** Opad efektywny 26,25 mm na 37,22 km² to 977 073 m³. Objętości odpływu różnią
się od tej liczby najwyżej o 0,02 % (SCS: hydrogram jednostkowy zachowuje objętość 1,0002 mm, p. 5.3).
Wszystkie modele dzielą więc tę samą wodę, a różnią się tylko tym, jak rozkładają ją w czasie.
Wariant z czasem koncentracji Kirpicha daje uwagi `outside_applicability`: Kamiennik leży poza
danymi, z których wyprowadzono ten wzór (rozdz. 4); Clark z $R/t_c$ = 2 — uwagę
`outside_unverified_range`.

**Interpretacja.** Kulminacje różnią się dwukrotnie: od 24–25 m³/s (Snyder, Clark z dużym $R$) do
52–54 m³/s (SCS). Rozstrzyga czas opóźnienia, który każdy model wyznacza inaczej: w modelu SCS
125 min ze wzoru na czas koncentracji, w modelu Clarka połowa $t_c$ plus $R$ (od 209 do 522 min
zależnie od $R$), u Snydera 366 min, a w metodzie Lutza 374 min, oba z regionalnych regresji
geometrii zlewni (Appalachy, południowo-zachodnie Niemcy). Dla zlewni niekontrolowanej żaden z
tych wyników nie jest „prawdziwy”; wybór modelu i jego parametrów to najważniejsza decyzja
projektanta. Dobrą praktyką jest:

- porównać kilka modeli, jak w tabeli, i uzasadnić wybór założeniami modelu (np. metoda Lutza dla
  zlewni quasi-naturalnej z przewagą lasu, jaką jest Kamiennik);
- skalibrować parametry na wezbraniach zarejestrowanych w zlewni kontrolowanej o podobnych cechach
  i przenieść je na zlewnię badaną (KZGW 2017);
- sprawdzić rząd wielkości wyniku metodą statystyczną dla najbliższego wodowskazu (rozdz. 7);
- podawać w raporcie model, jego parametry, metodę czasu koncentracji i krok obliczeń.

**Czas trwania opadu.** Najwyższą kulminację daje opad o **czasie trwania krytycznym**, który
znajduje się, licząc hydrogramy dla kilku czasów trwania tego samego prawdopodobieństwa (rozdz. 2,
p. 2.5, pokazuje taki przegląd dla modelu SCS, także dla opadów krótszych niż 3 h). Wysokości opadu
PMAXTP dla $p$ = 1 % i polecenia z odpowiednimi `--total-mm` i `--duration-min` dają:

| Czas trwania opadu [min] | Opad [mm] | Opad efektywny [mm] | SCS: kulminacja [m³/s] (czas [min]) | Nash–Lutz: kulminacja [m³/s] (czas [min]) |
|---|---|---|---|---|
| 180 | 65,58 | 8,35 | 28,23 (210) | 11,82 (350) |
| 360 | 81,50 | 15,36 | 44,37 (280) | 21,12 (430) |
| 720 | 101,82 | 26,25 | 52,36 (410) | 32,17 (580) |
| 1080 | 116,56 | 35,22 | 51,97 (530) | 37,19 (730) |
| 1440 | 128,58 | 43,05 | 49,86 (640) | 39,18 (850) |

Dla modelu SCS opad 12-godzinny daje największą kulminację spośród sprawdzonych czasów trwania —
jest praktycznie krytyczny; dla metody Lutza kulminacja rośnie jeszcze przy 24 h. Czas krytyczny zależy
więc od modelu, a przy metodzie SCS-CN także od strat: przy CN = 65 straty początkowe wynoszą
27,35 mm, więc krótki, intensywny opad daje mało odpływu, a dłuższy, choć mniej intensywny, coraz
więcej. Reguła DVWK przytaczana przez KZGW (2017, s. 105; rozdz. 4, p. 4.1), według której czas
krytyczny leży między $t_c$ a $2t_c$, wskazywałaby tu 3,5–7 h; nie uwzględnia ona strat
początkowych, dlatego przy dużych stratach trzeba sprawdzić także dłuższe opady.

**Prawdopodobieństwo wyniku.** Obliczenie przyjmuje, że wezbranie wywołane opadem o
prawdopodobieństwie przewyższenia 1 % ma to samo prawdopodobieństwo. To założenie metody, a nie
jej wynik: prawdopodobieństwo kulminacji zależy też od wilgotności zlewni przed opadem (AMC) i od
rozkładu opadu w czasie.

## 5.9. Typowe błędy — podsumowanie

- Hydrogram jednostkowy policzony dla innego czasu trwania niż krok hietogramu.
- Rzędne na 1 cm lub na 1 cal zamiast na 1 mm; brak kontroli bilansu objętości.
- Czas koncentracji wstawiony w niewłaściwych jednostkach albo z metody, której dane nie obejmują
  zlewni (rozdz. 4).
- Długość $L$ (Snyder, Lutz) mierzona do początku koryta zamiast do działu wodnego; spadek między
  końcami profilu zamiast spadku wyrównanego (Lutz).
- $C_t$ z literatury amerykańskiej bez przeliczenia na układ SI.
- Traktowanie podstawy trójkąta zastępczego ($T_b$ SCS w trójkącie, $t_b$ Snydera) jako końca
  hydrogramu.
- Jeden wynik jednego modelu bez porównania z innymi modelami i bez sprawdzenia czasu trwania
  krytycznego.

## Źródła

Źródła oznaczone (*) nie są dostępne w otwartym dostępie; tekst opiera się na ich omówieniu w
źródłach otwartych.

- Asquith W.H., Roussel M.C. (2007). *An initial-abstraction, constant-loss model for unit hydrograph
  modeling for applicable watersheds in Texas*. USGS Scientific Investigations Report 2007-5243.
  https://pubs.usgs.gov/sir/2007/5243/
- Chow V.T., Maidment D.R., Mays L.W. (1988). *Applied Hydrology*. McGraw-Hill (*); rozdz. 7
  omówiony w: Rajagopalan B., *Unit Hydrographs (Chow Chap 7)*, materiały do wykładu CVEN 5333,
  University of Colorado. https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf
- Clark C.O. (1945). Storage and the unit hydrograph. *Transactions of the ASCE* 110 (*).
- Kavka P., Müller M. i in. (2018). *Krátkodobé srážky pro hydrologické modelování a navrhování
  drobných vodohospodářských staveb v krajině*. Metodika ČVUT w Pradze i ÚFA AV ČR.
  https://rain.fsv.cvut.cz/data/files/metodika_old_web.pdf
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym
  prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych*, załącznik 2 do
  OPZ (wersja ujednolicona): rozdz. 6, przykłady 6.1, 6.2 i 6.4.
  https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
- Lutz W. (1984). *Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen*.
  Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe (*).
- Ministry of Works and Development, Water and Soil Division (1980). *A method for estimating design
  peak discharge*. Technical Memorandum 61, Wellington (dodatek A: spadek wyrównany).
  https://web.archive.org/web/20170228021947/http://docs.niwa.co.nz/library/public/TM61_1980.pdf
- Nash J.E. (1957). The form of the instantaneous unit hydrograph. *IAHS Publication* 45, 114–121 (*).
- Rao A.R., Delleur J.W., Sarma B.S.P. (1972). Conceptual hydrologic models for urbanizing basins.
  *Journal of the Hydraulics Division ASCE* 98(HY7) (*).
- Sikorska A.E., Scheidegger A., Banasik K., Rieckermann J. (2012). Bayesian uncertainty assessment
  of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. *Hydrology
  and Earth System Sciences* 16, 1221–1236. https://hess.copernicus.org/articles/16/1221/2012/
- Snyder F.F. (1938). Synthetic unit-graphs. *Transactions of the American Geophysical Union* 19 (*).
- Tyl R., Svoboda V., Šercl P., Pecha M. (2023). Využití srážkoodtokového modelování v hydrologické
  praxi ČHMÚ. *Meteorologické zprávy* 76. http://www.chmi.cz/documents/d/chmi.cz/10-59984-mz2023-05-02
- USACE-HEC (2000). *Hydrologic Modeling System HEC-HMS, Technical Reference Manual* (CPD-74B), oraz
  wydanie online, rozdz. „Transform”: SCS, Snyder i Clark Unit Hydrograph.
  https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/
- USDA-NRCS (2007). *National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs*
  (210-VI-NEH): tabela 16-1, przykład 16-1, dodatek 16A.
  https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf
- USDA-NRCS (2010). *National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of
  Concentration* (210-VI-NEH).
- Wałęga A., Cupak A. (2013). Zastosowanie geomorfoklimatycznego chwilowego hydrogramu jednostkowego
  Clarka do symulacji wezbrań opadowych. W: Węglarczyk S. (red.), *Problemy obliczania przepływów
  ekstremalnych w zlewniach kontrolowanych i niekontrolowanych*. Monografie Komitetu Gospodarki
  Wodnej PAN 35, 145–151. https://kgw.pan.pl/files/35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf

Decyzje projektowe Hydrologa przywołane w rozdziale: ADR-0024 (Nash metodą Lutza ze zlewni),
ADR-0043 (długość $L$ Snydera), ADR-0053 (spadek wyrównany $J_g$), ADR-0057 (hydrogram SCS i splot
w specyfikacjach), ADR-0058 (Snyder i Clark w specyfikacjach) w katalogu `docs/decisions/`; ustalenie
T2 przeglądu literatury (postać zależności $u_p(t_p)$ Lutza).
