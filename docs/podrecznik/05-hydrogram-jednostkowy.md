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
<!-- /spec:scs -->

Tablicę kształtu (NEH 630, tab. 16-1) Hydrolog przechowuje jako plik danych, przepisany dwukrotnie
i niezależnie (ADR-0057); między wierszami interpoluje liniowo, jak NEH w tabeli 16-2:

<!-- spec-table:scs -->
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

<!-- TODO spec: chwilowy hydrogram jednostkowy Nasha (gęstość rozkładu gamma o parametrach n i K, KZGW 2017 wzory 6.13–6.16) i jego hydrogram jednostkowy kroku Δt (średnia IUH w kroku z różnicy krzywej S, wzory 6.22–6.23); NashIUH, uh nash z --n i --k-min -->

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
`--urban-…`), lecz nie ma ona jeszcze specyfikacji. Częsty błąd to podanie udziału terenów
zabudowanych zamiast udziału powierzchni nieprzepuszczalnych.

<!-- TODO spec: parametry Nasha dla zlewni zurbanizowanych, regresja Rao, Delleura i Sarmy (1972) za KZGW 2017, wzory 6.26–6.28; NashIUH.from_urban_regression, uh nash --urban-* -->

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
<!-- /spec:clark -->

Środek ciężkości krzywej czas–powierzchnia zlewni eliptycznej leży w połowie czasu koncentracji,
więc czas opóźnienia hydrogramu Clarka (od środka ciężkości opadu do środka ciężkości odpływu) jest
sumą połowy $t_c$ i stałej $R$; polecenie `uh clark` podaje go jako `lag_time_min`. Większe $R$
spłaszcza i wydłuża hydrogram, większe $t_c$ przesuwa kulminację.

<!-- TODO spec: czas opóźnienia hydrogramu Clarka (połowa tc plus R, środek ciężkości krzywej czas–powierzchnia HEC-HMS i zbiornika liniowego); ClarkIUH.lag_time_min, wynik lag_time_min polecenia uh clark -->

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
Wariant z czasem koncentracji Kirpicha daje uwagi `outside_typical_range`: Kamiennik leży poza
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
