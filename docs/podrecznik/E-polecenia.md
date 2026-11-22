# E. Polecenia Hydrologa a rozdziały podręcznika

Każde polecenie Hydrologa jest zadeklarowane raz, w katalogu poleceń, i z tej jednej
deklaracji powstają: polecenie wiersza poleceń `hydrolog <grupa> <polecenie>`, narzędzie
serwera MCP i funkcja biblioteki `hydrolog.operations` z tymi samymi opcjami. Każdy przykład w
podręczniku podaje wiersz `hydrolog …`, którym można go powtórzyć; dodanie `--json` daje wynik
jako dokument JSON (koperta `hydrolog-result/1` z polem `formula_versions`, zob. dodatek D),
a `--lang en` — opis po angielsku.

Opcje, jednostki, ograniczenia i przykłady polecenia podaje sam Hydrolog:

```sh
hydrolog tc kirpich --help
hydrolog commands schema --command "tc kirpich"
hydrolog commands list
```

Poniższa tabela jest generowana z katalogu poleceń: wymienia każde polecenie z jego opisem z
katalogu oraz rozdziały, których przykłady je uruchamiają. Kreska oznacza polecenie, którego
żaden rozdział jeszcze nie używa.

<!-- generated:commands -->

| Polecenie | Co robi | Rozdziały |
|---|---|---|
| `hydrolog tc faa` | Oblicz czas spływu powierzchniowego metodą FAA (L, spadek, C). | [4](04-czas-koncentracji.md) |
| `hydrolog tc giandotti` | Oblicz czas koncentracji wzorem Giandottiego (A, L, H). | [4](04-czas-koncentracji.md) |
| `hydrolog tc kerby` | Oblicz czas spływu powierzchniowego wzorem Kerby'ego. | [4](04-czas-koncentracji.md) |
| `hydrolog tc kerby-kirpich` | Oblicz czas koncentracji metodą Kerby–Kirpich (spływ + koryto). | [4](04-czas-koncentracji.md) |
| `hydrolog tc kirpich` | Oblicz czas koncentracji wzorem Kirpicha (długość i spadek drogi spływu). | [4](04-czas-koncentracji.md) |
| `hydrolog tc nrcs` | Oblicz czas koncentracji metodą opóźnienia NRCS (NEH 630) z L, Y i CN. | [4](04-czas-koncentracji.md) |
| `hydrolog tc watershed` | Oblicz czas koncentracji wybraną metodą z parametrów zlewni. | [4](04-czas-koncentracji.md) |
| `hydrolog cn list` | Zwróć pełną tablicę CN TR-55 (pokrycia, stany, grupy A–D). | – |
| `hydrolog cn lookup` | Odczytaj CN z tablic TR-55 dla grupy gleby i pokrycia terenu. | [3](03-opad-efektywny.md) |
| `hydrolog cn range` | Zwróć zakres CN pokrycia terenu po stanach hydrologicznych. | [3](03-opad-efektywny.md) |
| `hydrolog cn weighted` | Oblicz średnią ważoną CN zlewni złożonej z kilku pokryć lub gleb. | [3](03-opad-efektywny.md) |
| `hydrolog scs effective` | Oblicz opad efektywny metodą SCS-CN z sumy opadu lub hietogramu. | [3](03-opad-efektywny.md) |
| `hydrolog precip areal` | Oblicz opad obszarowy z posterunków: średnia arytmetyczna, Thiessen, IDW lub izohiety. | [2](02-opad.md) |
| `hydrolog precip hietogram` | Oblicz hietogram opadu projektowego: blokowy, trójkątny, beta lub Euler II. | [2](02-opad.md) |
| `hydrolog precip pmaxtp` | Pobierz z IMGW-PIB wysokość opadu PMAXTP dla punktu, czasu trwania i prawdopodobieństwa. | [2](02-opad.md) |
| `hydrolog uh clark` | Oblicz hydrogram jednostkowy Clarka z tc oraz stałej retencji R lub stosunku R/tc. | [5](05-hydrogram-jednostkowy.md) |
| `hydrolog uh nash` | Oblicz hydrogram jednostkowy Nasha z n i K, metodą Lutza lub regresją miejską. | [5](05-hydrogram-jednostkowy.md) |
| `hydrolog uh scs` | Oblicz hydrogram jednostkowy SCS (NRCS) z powierzchni i czasu koncentracji. | [5](05-hydrogram-jednostkowy.md) |
| `hydrolog uh snyder` | Oblicz syntetyczny hydrogram jednostkowy Snydera z L, Lc oraz współczynników Ct i Cp. | [5](05-hydrogram-jednostkowy.md) |
| `hydrolog hydrograph generate` | Oblicz projektowy hydrogram odpływu bezpośredniego: opad, SCS-CN, hydrogram jednostkowy, splot. | [2](02-opad.md), [4](04-czas-koncentracji.md), [5](05-hydrogram-jednostkowy.md) |
| `hydrolog route cascade` | Przeprowadź hydrogram przez kaskadę n zbiorników liniowych (Nash, Kalinin-Miljukow). | [6](06-transformacja-fali.md) |
| `hydrolog route lag` | Przeprowadź hydrogram metodą lagu: odpływ to dopływ przesunięty w czasie. | [6](06-transformacja-fali.md) |
| `hydrolog route level-pool` | Przeprowadź hydrogram przez zbiornik z tabelą pojemność-odpływ (level pool). | [6](06-transformacja-fali.md) |
| `hydrolog route muskingum` | Przeprowadź hydrogram metodą Muskingum: retencja K[XI + (1-X)O] na pododcinkach. | [6](06-transformacja-fali.md) |
| `hydrolog route muskingum-cunge` | Przeprowadź hydrogram metodą Muskingum-Cunge: K i X z prędkości fali, szerokości i spadku odcinka. | [6](06-transformacja-fali.md) |
| `hydrolog route network` | Przeprowadź hydrogramy przez sieć rzeczną: zlewnie, odcinki, zbiorniki, złącza. | [6](06-transformacja-fali.md) |
| `hydrolog route schematic` | Rozmieść sieć rzeczną na schemacie w stylu mapy metra, bez obliczania przepływów. | – |
| `hydrolog morphometry watershed` | Oblicz wskaźniki geometryczne, kształtu i rzeźby zlewni. | [1](01-zlewnia.md) |
| `hydrolog network stats` | Oblicz statystyki rzędów sieci rzecznej (Strahler lub Shreve). | [1](01-zlewnia.md) |
| `hydrolog stats baseflow` | Wydziel przepływ podziemny filtrem Lyne'a i Hollicka: wskaźnik BFI i stała recesji | [8](08-przeplywy-charakterystyczne-nizowki.md) |
| `hydrolog stats characteristic` | Oblicz wartości charakterystyczne I i II stopnia (WQ…NQ, WWQ…NNQ, WWW…NNW) | [8](08-przeplywy-charakterystyczne-nizowki.md) |
| `hydrolog stats daily` | Oblicz statystyki dobowe z wielolecia szeregu dobowego | – |
| `hydrolog stats duration-curve` | Oblicz krzywą czasu trwania szeregu dobowego z liczebnościami klas i klasą modalną | [8](08-przeplywy-charakterystyczne-nizowki.md) |
| `hydrolog stats flood-frequency` | Oblicz kwantyle wezbrań dla okresów powtarzalności z maksimów rocznych | [7](07-przeplywy-maksymalne.md) |
| `hydrolog stats harmonics` | Dopasuj harmoniki cyklu rocznego szeregu dobowego (średnia, amplituda, termin maksimum) | [9](09-rezim-i-zmiennosc.md) |
| `hydrolog stats homogeneity` | Zbadaj jednorodność maksimów rocznych testami Manna-Whitneya, Kołmogorowa-Smirnowa i Pettitta | [7](07-przeplywy-maksymalne.md), [10](10-jednorodnosc-i-trend.md) |
| `hydrolog stats low-flow` | Oblicz kwantyle niżówek dla okresów powtarzalności z minimów rocznych | [8](08-przeplywy-charakterystyczne-nizowki.md) |
| `hydrolog stats low-flow-sequences` | Wykryj ciągi niżówkowe (susze) poniżej progu | [8](08-przeplywy-charakterystyczne-nizowki.md) |
| `hydrolog stats mann-kendall` | Zbadaj trend monotoniczny szeregu testem Manna–Kendalla i oszacuj nachylenie Sena | [7](07-przeplywy-maksymalne.md), [8](08-przeplywy-charakterystyczne-nizowki.md), [10](10-jednorodnosc-i-trend.md) |
| `hydrolog stats monthly` | Oblicz statystyki miesięczne z przedziałem ufności średniej (t-Studenta) | – |
| `hydrolog stats regime` | Oblicz reżim odpływu: współczynniki Pardégo, typ reżimu Dynowskiej i sezonowość | [9](09-rezim-i-zmiennosc.md) |
| `hydrolog stats runoff-volume` | Oblicz roczne i miesięczne objętości odpływu oraz krzywą sumową roku | – |
| `hydrolog stats seasonality` | Oblicz średni termin i koncentrację dat maksimów albo minimów rocznych | [9](09-rezim-i-zmiennosc.md) |
| `hydrolog stats threshold-events` | Znajdź epizody i dni powyżej albo poniżej progu w szeregu dobowym | – |
| `hydrolog hydrometrics rating-curve` | Dopasuj krzywą przepływu Q = a·(H − H₀)^b do par stan–przepływ | [9](09-rezim-i-zmiennosc.md) |
| `hydrolog hydrometrics water-level-zones` | Wyznacz strefy stanów wody wg Rybczyńskiego (NTW, STW, WTW) ze szeregu stanów | [9](09-rezim-i-zmiennosc.md) |
| `hydrolog meteo hydrothermal` | Oblicz współczynnik hydrotermiczny Sielianinowa miesięcy IV–IX i dni IV–IX z Tśr > 10 °C | [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog meteo precipitation` | Oblicz statystyki opadu: sumy i normalne, maksima, dni z opadem, natężenie, opady duże, reżim | [10](10-jednorodnosc-i-trend.md), [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog meteo snow` | Oblicz pokrywę śnieżną każdej zimy: dni, największa grubość, pierwszy i ostatni dzień, śnieg świeży | [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog meteo spells` | Znajdź ciągi dni bezopadowych albo opadowych z najdłuższym ciągiem i liczebnościami lat | [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog meteo spi` | Oblicz SPI w kilku skalach oraz opad względny i jego klasy w miesiącach i latach | [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog meteo temperature` | Oblicz statystyki temperatury powietrza: średnie i normalne, dni charakterystyczne, stopniodni | [10](10-jednorodnosc-i-trend.md), [11](11-wskazniki-meteorologiczne.md) |
| `hydrolog soil hsg` | Zapisz GeoTIFF z grupami HSG sklasyfikowanymi z rastrów iłu, piasku i pyłu. | [3](03-opad-efektywny.md) |
| `hydrolog soil hsg-stats` | Oblicz powierzchnie i udziały grup HSG A-D z rastra HSG, opcjonalnie w prostokącie bbox. | [3](03-opad-efektywny.md) |
| `hydrolog soil texture` | Oblicz klasę uziarnienia USDA i grupę hydrologiczną gleby A-D dla jednej próbki gleby. | [3](03-opad-efektywny.md) |
| `hydrolog report generate` | Zapisz raport obliczeniowy hydrogramu projektowego w Markdown. | – |
| `hydrolog config show` | Pokaż obowiązujące ustawienia Hydrologa i źródło każdego. | – |
| `hydrolog gui serve` | Uruchom przeglądarkowy interfejs Hydrologa na tym komputerze. | – |
| `hydrolog commands batch` | Uruchom wywołania katalogu z pliku JSON Lines w jednym procesie, wynik każdego. | – |
| `hydrolog commands guide` | Wygeneruj z katalogu przewodnik (AGENTS.md, llms.txt, blok) dla agentów. | – |
| `hydrolog commands list` | Wylistuj komendy katalogu: nazwa, operation_id i opis. | – |
| `hydrolog commands schema` | Zwróć opcje, wynik i zasady jednej komendy albo strony katalogu. | – |

<!-- /generated:commands -->
