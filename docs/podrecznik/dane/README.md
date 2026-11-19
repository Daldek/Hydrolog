# Dane przykładów podręcznika

Każdy plik ma tu swoją sekcję: pochodzenie, polecenie eksportu, data, wiersze atrybucji dostawcy i regulamin.

## Opad dobowy 13 września 2024 r. wokół zlewni Kamiennika (rozdz. 2, przykład 2.1)

Plik `kamiennik_opad_2024-09-13.csv`: sumy opadu `precipitation_mm` [mm] z doby opadowej z datą 13 września
2024 r. (od 13 IX 06 UTC do 14 IX 06 UTC) na pięciu posterunkach opadowych IMGW-PIB i na stacji synoptycznej
Jelenia Góra, ze współrzędnymi `x` (na wschód) i `y` (na północ) w układzie PL-1992 (EPSG:2180) w metrach, w
formacie opcji `--stations-file` polecenia `hydrolog precip areal`. Wszystkie wartości mają w danych IMGW-PIB
status `value`. Posterunek Kaczorów (250150110) nie ma wartości z tej doby (status `missing`) i nie ma go w
pliku.

Wartości odczytano z magazynu Obserwatora 19 listopada 2026 r.: zbiór `pl.imgw.meteo_precip_daily` (wersja
szeregu `2026-09-15_8dd3574e`) dla posterunków Świerzawa (251150360), Bolków (250160030), Jawor (251160290),
Twardocice (251150280) i Ciechanowice (250150130) oraz zbiór `pl.imgw.meteo_synop_daily` (wersja
`2026-11-10_b11f7874`) dla stacji Jelenia Góra (350150500), np.:

```bash
obserwator series export --root <katalog danych Obserwatora> --dataset pl.imgw.meteo_precip_daily --station 251150360 --variables P --start 2024-09-13 --end 2024-09-13 --format csv
```

Współrzędne: położenie stacji z metadanych IMGW-PIB w magazynie Obserwatora (wersja `2026-11-15_43ce2c18`,
WGS84), przeliczone na PL-1992 biblioteką pyproj (`Transformer.from_crs("EPSG:4326", "EPSG:2180",
always_xy=True)`) i zaokrąglone do 1 m.

Pola wieloboków Thiessena i siatka IDW z przykładu 2.1 pochodzą z granicy zlewni Kamiennika po Świerzawę,
wyznaczonej przez Hydrograf z numerycznego modelu terenu (plik `data/boundary/kamiennik_37km2_sfincs.gpkg`
repozytorium Hydrografu, 37,2234 km², PL-1992). Wielobok posterunku to część granicy zlewni przycięta
półpłaszczyznami symetralnych odcinków łączących go z pozostałymi posterunkami; siatka to środki kwadratów
kilometrowej siatki PL-1992 (współrzędne kończące się na 500 m), które leżą w granicy zlewni.

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.
Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations
