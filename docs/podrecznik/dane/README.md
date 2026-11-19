# Dane przykładów podręcznika

Każdy plik ma tu swoją sekcję: polecenie eksportu, data, wiersze atrybucji dostawcy i regulamin.

## Kaczawa — Świerzawa (IMGW-PIB 151150170)

Pliki (rozdziały 7 i 8):

- `kaczawa_swierzawa_Q_dobowe_1961_2025.csv` — przepływ średni dobowy Q [m³/s], kolumny `date`, `year`
  (rok hydrologiczny), `Q [m3/s]`, `Q_flag` i kolumny atrybucji; lata hydrologiczne 1961–2025
  (1 listopada 1960 – 31 października 2025), każdy dzień z wartością;
- `kaczawa_swierzawa_Q_polroczne_1961_2025.csv` — charakterystyki półroczne i roczne przepływu
  IMGW-PIB (`period`: `winter` XI–IV, `summer` V–X, `annual`; `Q_min`, `Q_mean`, `Q_max` z datami
  wystąpienia), lata hydrologiczne 1961–2025, oba półrocza w każdym roku.

Stacja: ŚWIERZAWA, rzeka Kaczawa (kod hydrograficzny 138), 51,0178° N, 15,8878° E.

Eksport Obserwatorem 3.1.0.dev0, 2026-11-19, z katalogu danych z publicznymi zbiorami IMGW-PIB
`pl.imgw.hydro_daily` i `pl.imgw.hydro_semiannual` (`KATALOG_DANYCH` to katalog danych Obserwatora):

```sh
obserwator series export --root KATALOG_DANYCH --dataset pl.imgw.hydro_daily --station 151150170 --variables Q --format csv --output kaczawa_swierzawa_Q_dobowe_1961_2025.csv
obserwator series export --root KATALOG_DANYCH --dataset pl.imgw.hydro_semiannual --station 151150170 --variables Q_min,Q_mean,Q_max --format csv --output kaczawa_swierzawa_Q_polroczne_1961_2025.csv
```

Wiersze atrybucji dostawcy (zapisane przez Obserwatora w kolumnach pliku):

- Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy
- Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone
- Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations

## Czarna Woda — Bukowna (IMGW-PIB 151160040)

Plik (rozdział 8):

- `czarna_woda_bukowna_Q_polroczne_1973_2025.csv` — charakterystyki półroczne i roczne przepływu
  IMGW-PIB, kolumny jak wyżej; lata hydrologiczne 1973–2025, bez lat 1992–1994, dla których dane
  publiczne nie mają wartości przepływu.

Stacja: BUKOWNA, rzeka Czarna Woda (kod hydrograficzny 1386, dorzecze Kaczawy).

Eksport Obserwatorem 3.1.0.dev0, 2026-11-19:

```sh
obserwator series export --root KATALOG_DANYCH --dataset pl.imgw.hydro_semiannual --station 151160040 --variables Q_min,Q_mean,Q_max --format csv --output czarna_woda_bukowna_Q_polroczne_1973_2025.csv
```

Wiersze atrybucji dostawcy (zapisane przez Obserwatora w kolumnach pliku):

- Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy
- Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone
- Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations
