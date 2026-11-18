"""Published reference cases of the ``meteo`` group on a real station series.

``tests/fixtures/warszawa_okecie_1991_2020.csv.gz``: the daily Tmax, Tmin, Tmean and P
of the IMGW-PIB synop station Warszawa-Okęcie (352200375) in 1991-2020, every day with
a value, from the files ``s_d_375_*`` of danepubliczne.imgw.pl. Źródłem pochodzenia
danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy;
dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego
zostały przetworzone (a CSV of four columns).

The published values are IMGW-PIB's climate normals 1991-2020 of the station WARSZAWA
12375 (klimat.imgw.pl, „Normy klimatyczne 1991-2020”, read 2026-11-18), printed to
0.1; the others are independent recounts of the same rows named in each test (the
audit of the formulas of 2026-11-18, research ``meteo-indices``).
"""

import csv
import gzip
from pathlib import Path

import numpy as np
import pytest

from hydrolog.statistics import (
    hydrothermal_coefficient,
    precipitation_spells,
    precipitation_sums,
    temperature_days,
    temperature_means,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "warszawa_okecie_1991_2020.csv.gz"
)
with gzip.open(FIXTURE, "rt", encoding="utf-8") as _stream:
    _ROWS = list(csv.DictReader(_stream))
DATES = np.array([row["date"] for row in _ROWS], dtype="datetime64[D]")


def _column(name: str) -> np.ndarray:
    return np.array([float(row[name]) for row in _ROWS])


TMAX, TMIN = _column("Tmax [degC]"), _column("Tmin [degC]")
TMEAN, P = _column("Tmean [degC]"), _column("P [mm]")
PRINTED = 0.05 + 1e-9  # half the printed unit of 0.1


class TestImgwNormals1991To2020:
    """IMGW-PIB's normals of WARSZAWA 12375 from the daily rows."""

    def test_precipitation_normals(self):
        """OPAD_SUMA: the months and the year 549.7 mm, the sum of the months."""
        printed = [
            31.0,
            29.8,
            29.0,
            35.1,
            55.5,
            63.9,
            82.2,
            60.6,
            50.4,
            40.2,
            36.0,
            36.1,
        ]
        period = precipitation_sums(P, DATES).period
        normals = [month.normal_mm for month in period.months]
        assert normals == pytest.approx(printed, abs=PRINTED)
        assert period.normal_mm == pytest.approx(549.7, abs=PRINTED)
        assert period.normal_mm == pytest.approx(sum(normals), abs=1e-9)

    def test_temperature_normals(self):
        """TSR_AVE: the months and the year 9.0 °C, the mean of the months."""
        printed = [-1.5, -0.4, 3.2, 9.2, 14.3, 17.7, 19.7, 19.1, 14.0, 8.7, 3.8, -0.1]
        period = temperature_means(DATES, tmean_c=TMEAN).period
        normals = [month.normal_c for month in period.months]
        assert normals == pytest.approx(printed, abs=PRINTED)
        assert period.normal_c == pytest.approx(9.0, abs=PRINTED)

    def test_frost_days_and_dni_przymrozkowe(self):
        """TMIN_0 „Tmin < 0C” is FD, 97.9 days; PRZYMROZKI „Liczba dni przymrozkowych
        (TMAX>0 & TMIN<0)” the freeze-thaw days, 64.0 days (recount 64.03)."""
        period = temperature_days(DATES, tmax_c=TMAX, tmin_c=TMIN).period
        assert period.frost_days == pytest.approx(97.9, abs=PRINTED)
        assert period.freeze_thaw_days == pytest.approx(64.0, abs=PRINTED)


class TestConventionsOnTheRecord:
    """Year attribution of spells and the season of the hydrothermal coefficient."""

    def test_a_dry_spell_over_new_year_counts_in_the_year_it_ends(self):
        """CDD as ECA&D and climdex.pcic: the 59 days of 1996-12-15 to 1997-02-11
        count in 1997; 1996's longest is then 25 days (independent recount)."""
        result = precipitation_spells(P, DATES, kind="dry")
        cdd = {row.year: row.max_duration_days for row in result.years}
        assert (cdd[1996], cdd[1997]) == (25, 59)
        spell = next(s for s in result.spells if s.start_date == "1996-12-15")
        assert (spell.end_date, spell.duration_days, spell.year) == (
            "1997-02-11",
            59,
            1997,
        )
        assert result.period.mean_max_duration_days == pytest.approx(773 / 30)

    def test_the_hydrothermal_season_is_april_to_september(self):
        """Miś (2026), eq. 4: P and Σt of the days above 10 °C in IV-IX; the mean of
        1991-2020 by an independent recount is 1.154276982 (all-year days: 1.144)."""
        result = hydrothermal_coefficient(DATES, precipitation_mm=P, tmean_c=TMEAN)
        assert result.period.n_years == 30
        assert result.period.mean_season_coefficient == pytest.approx(
            1.154276982001756, rel=1e-12
        )
        year = next(row for row in result.years if row.year == 2015)
        assert year.season_days == 164
