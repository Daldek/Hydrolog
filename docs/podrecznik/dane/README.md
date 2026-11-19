# Dane przykładów podręcznika

Każdy plik ma tu swoją sekcję: polecenie eksportu, data, wiersze atrybucji dostawcy i regulamin.

## Nysa Kłodzka — Kłodzko (IMGW-PIB 150160180)

Plik `klodzko_1951_2025.csv.gz`: dobowe stany wody `H [cm]` i przepływy `Q [m3/s]` wodowskazu Kłodzko na
Nysie Kłodzkiej z lat hydrologicznych 1951–2025 (od 1 listopada 1950 r. do 31 października 2025 r.), z kolumnami
statusu (`H_flag`, `Q_flag`) i wierszami atrybucji, tak jak zapisuje je Obserwator. W publicznych danych IMGW-PIB
brakuje całego roku hydrologicznego 1997 (od 1 listopada 1996 r. do 31 października 1997 r.): 365 dni ma status
`missing`.

Eksport z magazynu Obserwatora (zbiór `pl.imgw.hydro_daily`, wersja szeregu `2026-09-21_95988ba3`), 19 listopada
2026 r.:

```bash
obserwator series export --root <katalog danych Obserwatora> --dataset pl.imgw.hydro_daily --station 150160180 --variables H,Q --format csv --output klodzko_1951_2025.csv
gzip -9 klodzko_1951_2025.csv
```

Hydrolog czyta pliki tekstowe UTF-8, nie archiwa `.gz`, więc przed użyciem plik trzeba rozpakować (z katalogu
głównego repozytorium):

```bash
gzip -dk docs/podrecznik/dane/klodzko_1951_2025.csv.gz
```

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.
Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations

## Warszawa-Okęcie (IMGW-PIB 352200375), pokrywa śnieżna

Plik `warszawa_okecie_snieg_1991_2020.csv`: dobowa grubość pokrywy śnieżnej `snow_cover [cm]` stacji synoptycznej
Warszawa-Okęcie od 1 sierpnia 1990 r. do 31 lipca 2020 r. (zimy 1991–2020 w rozumieniu polecenia `meteo snow`), ze
statusem (`snow_cover_flag`) i wierszami atrybucji. Uzupełnia plik testowy Hydrologa
`tests/fixtures/warszawa_okecie_1991_2020.csv.gz` (temperatura i opad tej samej stacji z lat 1991–2020), który nie
ma pokrywy śnieżnej.

Eksport z magazynu Obserwatora (zbiór `pl.imgw.meteo_synop_daily`, wersja szeregu `2026-11-10_b11f7874`),
19 listopada 2026 r.:

```bash
obserwator series export --root <katalog danych Obserwatora> --dataset pl.imgw.meteo_synop_daily --station 352200375 --variables snow_cover --start 1990-08-01 --end 2020-07-31 --format csv --output warszawa_okecie_snieg_1991_2020.csv
```

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.
Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations
