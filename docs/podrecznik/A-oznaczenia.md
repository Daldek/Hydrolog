# A. Oznaczenia i jednostki

## Zasady zapisu

- Liczby mają przecinek dziesiętny; tysiące liczb o co najmniej pięciu cyfrach oddziela
  spacja, a potęgi dziesięciu zapisano jako `1·10⁻⁹`.
- Przedział `[a; b]` zawiera swoje krańce, `(a; b)` ich nie zawiera, a `∞` oznacza brak
  ograniczenia. Średnik oddziela krańce, bo przecinek jest dziesiętny.
- Wielkości mają jednostki układu SI z jednostkami dopuszczonymi do stosowania razem z nim
  (minuta, godzina, doba, rok). Wzory wyprowadzone w jednostkach anglosaskich Hydrolog liczy w
  jednostkach ich źródła, przeliczając dane dokładnymi przelicznikami tabeli jednostek
  standardu Nogat (CMP-4.3; BIPM 2019); stąd złożone jednostki niektórych stałych.
- Nazwa argumentu w Hydrologu zawiera jednostkę: `area_km2` (km²), `slope_m_per_m` (m/m),
  `duration_min` (min); opcja wiersza poleceń to ta sama nazwa z łącznikiem zamiast
  podkreślenia (`--area-km2`).
- Symbole pochodzą z równań specyfikacji wzorów. Ten sam symbol bywa w różnych wzorach inną
  wielkością (na przykład $S$ to retencja maksymalna w metodzie SCS-CN, a spadek we wzorze
  Kirpicha), dlatego wykaz symboli podaje znaczenie osobno dla każdego wzoru.

Oba wykazy poniżej są generowane z ramek wzorów, które pokazuje podręcznik (dodatek D, D.7):
obejmują jednostki i symbole tych wzorów i odsyłają do ramek.

## A.1. Jednostki

<!-- generated:units -->

| Jednostka | Zapis w Hydrologu | Nazwa |
|---|---|---|
| – | `-` | wielkość bezwymiarowa |
| in | `in` | cal |
| mm | `mm` | milimetr |

<!-- /generated:units -->

## A.2. Symbole

<!-- generated:symbols -->

| Symbol | Znaczenie | Jednostka | Wzory |
|---|---|---|---|
| $CN$ | Liczba CN dla warunków wilgotnościowych poprzedzających przyjętych we wzorze | – | [`scs_cn_retention`](D-weryfikacja.md#spec-scs_cn_retention) |
| $S$ | Retencja maksymalna po rozpoczęciu odpływu | mm | [`scs_cn_retention`](D-weryfikacja.md#spec-scs_cn_retention) |

<!-- /generated:symbols -->

## A.3. Skróty

| Skrót | Znaczenie |
|---|---|
| AMC, ARC | warunki wilgotnościowe poprzedzające (*antecedent moisture condition*, *antecedent runoff condition*) metody SCS-CN, klasy I, II i III |
| BFI | wskaźnik odpływu podziemnego (*baseflow index*) |
| CN | parametr krzywej odpływu metody SCS (*curve number*) |
| ETCCDI | zespół ekspertów WMO do spraw wykrywania zmian klimatu i ich wskaźników (*Expert Team on Climate Change Detection and Indices*) |
| GEV | uogólniony rozkład wartości ekstremalnych (*generalized extreme value*) |
| HSG | grupa hydrologiczna gleby (*hydrologic soil group*), A do D |
| IDW | interpolacja ważona odwrotnością odległości (*inverse distance weighting*) |
| IMGW-PIB | Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy |
| KZGW | Krajowy Zarząd Gospodarki Wodnej |
| NEH | *National Engineering Handbook* (USDA-NRCS), część 630 *Hydrology* |
| NRCS | *Natural Resources Conservation Service* (USDA), dawniej SCS |
| PMAXTP | maksymalne opady o określonym czasie trwania i prawdopodobieństwie przewyższenia (IMGW-PIB) |
| PMP | opad maksymalny prawdopodobny (*probable maximum precipitation*); nie mylić z PMAXTP |
| SCS | *Soil Conservation Service* (USDA), dziś NRCS |
| SPI | standaryzowany wskaźnik opadu (*standardized precipitation index*) |
| TR-55 | *Technical Release 55: Urban Hydrology for Small Watersheds* (USDA-SCS 1986) |
| WMO | Światowa Organizacja Meteorologiczna (*World Meteorological Organization*) |

## Źródła

- BIPM (2019). *The International System of Units (SI)*, 9th edition.
  <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>.
- Nogat (2026). Standard 1.1, *Computations: formulas, their limits and their verification*
  (`standards/COMPUTATIONS.md`, wymaganie CMP-4.3). <https://github.com/Daldek/Nogat>.
