"""The daily series of Warszawa-Okęcie 1991-2020: the station of the meteo tests.

``tests/fixtures/warszawa_okecie_1991_2020.csv.gz``: the daily Tmax, Tmin, Tmean and P
of the IMGW-PIB synop station Warszawa-Okęcie (352200375) in 1991-2020, every day with
a value, from the files ``s_d_375_*`` of danepubliczne.imgw.pl. Źródłem pochodzenia
danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy;
dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego
zostały przetworzone (a CSV of four columns).
"""

import csv
import gzip
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "warszawa_okecie_1991_2020.csv.gz"
)
with gzip.open(FIXTURE, "rt", encoding="utf-8") as _stream:
    _ROWS = list(csv.DictReader(_stream))
DATES = np.array([row["date"] for row in _ROWS], dtype="datetime64[D]")


def _column(name: str) -> NDArray[np.float64]:
    return np.array([float(row[name]) for row in _ROWS])


TMAX, TMIN = _column("Tmax [degC]"), _column("Tmin [degC]")
TMEAN, P = _column("Tmean [degC]"), _column("P [mm]")
