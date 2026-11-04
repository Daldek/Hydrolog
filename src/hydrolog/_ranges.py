"""The typical ranges of the formulas and models, each with its source (one table).

A typical range is the range of the data a formula was derived from, or the range its
literature recommends. Outside it the formula still computes and the library warns
(:class:`~hydrolog._warnings.OutsideTypicalRange`, notice ``outside_typical_range``)
with the bounds of :data:`TYPICAL_RANGES`; the record length of a flood frequency
analysis has the notice ``short_record`` instead. The catalog serves the table in the
``typical_ranges`` of the commands that check it, in the document of one command
(``commands schema --command``, ADR-0017), so a client, the GUI or an agent, shows the
same numbers and sources instead of keeping its own.
A range without a published source is not kept (the author's decision of 2026-11-04,
plan 2026-11-02), except the given parameters of the Nash cascade: they are kept as
to be verified (``verified`` false), and a value outside them gives the notice
``outside_unverified_range`` (:class:`~hydrolog._warnings.OutsideUnverifiedRange`).

:data:`TC_INPUTS` names the watershed fields each argument of a time of concentration
formula is taken from, first choice first: ``WatershedParameters`` selects with it,
and the catalog serves it as the ``inputs`` of a range checked on a watershed.

The module is a leaf: it imports only :mod:`hydrolog._warnings`, so the catalog can
read it without the numerical libraries.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from hydrolog._warnings import warn_outside_typical_range

__all__ = [
    "TC_INPUTS",
    "TYPICAL_RANGES",
    "UH_MODELS",
    "TypicalRange",
    "typical_range",
    "typical_ranges",
    "warn_if_outside",
]


@dataclass(frozen=True)
class TypicalRange:
    """The typical range of one parameter of a formula or a model.

    Attributes
    ----------
    method : str
        The formula or the model, as ``details.method`` of its notices names it: a
        time of concentration method, ``scs_cn_amc``, a unit hydrograph model,
        ``lutz`` (Nash's parameters by the Lutz method), ``flood_frequency``.
    parameter : str
        The argument of the formula, as ``details.parameter`` names it.
    minimum, maximum : float or None
        The bounds, included, in the unit of the parameter; ``None`` is no bound.
        With ``relative_to`` they are shares of that quantity.
    unit : str
        Unit of the parameter: ``km2``, ``km``, ``m/m``, ``min``, ``years`` or ``-``.
    source : str
        Where the range comes from (English).
    source_pl : str
        The same in Polish.
    relative_to : str or None
        The result field the bounds are shares of (``uh_time_to_peak_min`` for the
        time step), else ``None``.
    notice : str
        Code of the notice a value outside the range gives:
        ``outside_typical_range``, ``outside_unverified_range`` for a range to be
        verified, or ``short_record``.
    verified : bool
        Whether the range has a published source; one without is kept only to be
        verified, and its notice is ``outside_unverified_range``.
    """

    method: str
    parameter: str
    minimum: float | None
    maximum: float | None
    unit: str
    source: str
    source_pl: str
    relative_to: str | None = None
    notice: str = "outside_typical_range"
    verified: bool = True

    def __post_init__(self) -> None:
        """Refuse a range whose notice does not say whether it is verified.

        Raises
        ------
        ValueError
            If a range to be verified has another notice than
            ``outside_unverified_range``, or a verified one has that notice.
        """
        if self.verified == (self.notice == "outside_unverified_range"):
            raise ValueError(
                f"{self.method}.{self.parameter}: a range is outside_unverified_range "
                "if and only if it is not verified"
            )

    def check(self, value: float, *, scale: float = 1.0, stacklevel: int = 2) -> None:
        """Warn (:class:`~hydrolog._warnings.OutsideTypicalRange`) outside the range.

        A range to be verified warns with the subclass
        :class:`~hydrolog._warnings.OutsideUnverifiedRange`.

        Parameters
        ----------
        value : float
            The value of the parameter.
        scale : float, optional
            The quantity ``relative_to`` names: the bounds are multiplied by it.
        stacklevel : int, optional
            As in ``warnings.warn``, counted from the caller of this method.

        Raises
        ------
        TypeError
            If the range lacks a bound, or its notice is neither
            ``outside_typical_range`` nor ``outside_unverified_range``.
        """
        if (
            self.notice not in _RANGE_NOTICES
            or self.minimum is None
            or self.maximum is None
        ):
            raise TypeError(f"{self.method}.{self.parameter} is not a two-sided range")
        warn_outside_typical_range(
            self.method,
            self.parameter,
            value,
            self.minimum * scale,
            self.maximum * scale,
            verified=self.verified,
            stacklevel=stacklevel + 1,
        )


_RANGE_NOTICES: Final = ("outside_typical_range", "outside_unverified_range")
"""The notices of a value outside a two-sided range."""


UH_MODELS: Final = ("scs", "nash", "clark", "snyder")
"""The unit hydrograph models; each has the range of the time step."""

_KERBY_N = (
    (
        "Kerby (1959): the retardance N of his table, pavement to dense grass and "
        "coniferous forest (Roussel et al. 2005)"
    ),
    (
        "Kerby (1959): współczynnik N z jego tabeli, od nawierzchni do gęstej trawy "
        "i lasu iglastego (Roussel i in. 2005)"
    ),
)
_NASH = (
    "Hydrolog; no published source, to be verified",
    "Hydrolog; brak opublikowanego źródła, do weryfikacji",
)
_TIMESTEP_SHARE = 0.25
_TIMESTEP = (
    (
        "USDA-NRCS (2007), NEH 630 ch. 16: a longer unit duration (the time step) "
        "does not resolve the peak of the unit hydrograph"
    ),
    (
        "USDA-NRCS (2007), NEH 630 rozdz. 16: dłuższy czas trwania opadu "
        "jednostkowego (krok) nie odwzorowuje szczytu hydrogramu jednostkowego"
    ),
)

TYPICAL_RANGES: Final[tuple[TypicalRange, ...]] = (
    # --- time of concentration ---------------------------------------------------
    TypicalRange(
        "kirpich",
        "area_km2",
        0.005,
        0.45,
        "km2",
        "Kirpich (1940): data of 7 rural watersheds in Tennessee, 1.25-112 acres "
        "(USDA-NRCS 2010, NEH 630 ch. 15; Roussel et al. 2005)",
        "Kirpich (1940): dane 7 zlewni rolniczych w Tennessee, 1,25–112 akrów "
        "(USDA-NRCS 2010, NEH 630 rozdz. 15; Roussel i in. 2005)",
    ),
    TypicalRange(
        "kirpich",
        "slope_m_per_m",
        0.03,
        0.10,
        "m/m",
        "Kirpich (1940): slopes of the 7 Tennessee watersheds, 3-10% (Roussel et "
        "al. 2005)",
        "Kirpich (1940): spadki 7 zlewni w Tennessee, 3–10% (Roussel i in. 2005)",
    ),
    TypicalRange(
        "nrcs",
        "area_km2",
        0.005,
        24.0,
        "km2",
        "Mockus (1961): the lag equation from 24 watersheds of 1.3 acres to 9.2 mi² "
        "(USDA-NRCS 2010, NEH 630 ch. 15)",
        "Mockus (1961): równanie opóźnienia z 24 zlewni od 1,3 akra do 9,2 mi² "
        "(USDA-NRCS 2010, NEH 630 rozdz. 15)",
    ),
    TypicalRange(
        "nrcs",
        "cn",
        50.0,
        95.0,
        "-",
        "Mockus (1961): a CN outside these bounds is not to be used in the lag "
        "equation (USDA-NRCS 2010, NEH 630 ch. 15)",
        "Mockus (1961): CN spoza tych granic nie stosuje się w równaniu opóźnienia "
        "(USDA-NRCS 2010, NEH 630 rozdz. 15)",
    ),
    TypicalRange(
        "giandotti",
        "area_km2",
        170.0,
        70000.0,
        "km2",
        "Giandotti (1934): the Italian basins of the formula (Grimaldi et al. 2012)",
        "Giandotti (1934): zlewnie włoskie, z których pochodzi wzór (Grimaldi i in. "
        "2012)",
    ),
    TypicalRange(
        "faa",
        "runoff_coeff",
        0.0,
        0.95,
        "-",
        "FAA (1970), AC 150/5320-5B, table I: the runoff coefficients of the method",
        "FAA (1970), AC 150/5320-5B, tabela I: współczynniki odpływu metody",
    ),
    TypicalRange(
        "kerby",
        "area_km2",
        0.0,
        0.04,
        "km2",
        "Kerby (1959): watersheds below 10 acres (Roussel et al. 2005)",
        "Kerby (1959): zlewnie poniżej 10 akrów (Roussel i in. 2005)",
    ),
    TypicalRange(
        "kerby",
        "length_km",
        0.0,
        0.366,
        "km",
        "Kerby (1959): overland flow up to 1200 ft (Roussel et al. 2005; TxDOT 2019)",
        "Kerby (1959): spływ po stoku do 1200 stóp (Roussel i in. 2005; TxDOT 2019)",
    ),
    TypicalRange(
        "kerby",
        "slope_m_per_m",
        0.0,
        0.01,
        "m/m",
        "Kerby (1959): slopes below 1% (Roussel et al. 2005)",
        "Kerby (1959): spadki poniżej 1% (Roussel i in. 2005)",
    ),
    TypicalRange("kerby", "retardance", 0.02, 0.80, "-", *_KERBY_N),
    TypicalRange(
        "kerby_kirpich",
        "area_km2",
        0.65,
        388.0,
        "km2",
        "Roussel et al. (2005): 92 Texas watersheds of 0.25-150 mi² (TxDOT report "
        "0-4696-2; Cleveland et al. 2012)",
        "Roussel i in. (2005): 92 zlewnie w Teksasie, 0,25–150 mi² (raport TxDOT "
        "0-4696-2; Cleveland i in. 2012)",
    ),
    TypicalRange(
        "kerby_kirpich",
        "overland_length_km",
        0.0,
        0.366,
        "km",
        "Kerby (1959): overland flow of about 1200 ft as an upper limit (Roussel et "
        "al. 2005)",
        "Kerby (1959): spływ po stoku ok. 1200 stóp jako górna granica (Roussel i "
        "in. 2005)",
    ),
    TypicalRange("kerby_kirpich", "retardance", 0.02, 0.80, "-", *_KERBY_N),
    TypicalRange(
        "kerby_kirpich",
        "channel_length_km",
        1.6,
        80.0,
        "km",
        "Roussel et al. (2005): main channels of 1-50 mi of the 92 Texas watersheds",
        "Roussel i in. (2005): cieki główne 92 zlewni w Teksasie, 1–50 mil",
    ),
    TypicalRange(
        "kerby_kirpich",
        "channel_slope_m_per_m",
        0.002,
        0.02,
        "m/m",
        "Roussel et al. (2005): main channel slopes of the 92 Texas watersheds",
        "Roussel i in. (2005): spadki cieków głównych 92 zlewni w Teksasie",
    ),
    # --- SCS-CN ------------------------------------------------------------------
    TypicalRange(
        "scs_cn_amc",
        "cn",
        55.0,
        95.0,
        "-",
        "Hawkins et al. (1985): the AMC conversion formulas approximate the table of "
        "NEH 630 (after Ponce and Hawkins 1996)",
        "Hawkins i in. (1985): wzory przeliczenia AMC przybliżają tabelę NEH 630 (za "
        "Ponce i Hawkins 1996)",
    ),
    # --- unit hydrographs --------------------------------------------------------
    TypicalRange(
        "scs",
        "area_km2",
        0.0,
        52.0,
        "km2",
        "Sorrell (2010), Michigan DNRE: the NRCS unit hydrograph for watersheds up to "
        "about 20 mi², over which the rainfall is uniform; a larger one is divided",
        "Sorrell (2010), Michigan DNRE: hydrogram jednostkowy NRCS dla zlewni do ok. "
        "20 mi², na których opad jest równomierny; większą się dzieli",
    ),
    TypicalRange(
        "nash",
        "n",
        1.0,
        10.0,
        "-",
        *_NASH,
        notice="outside_unverified_range",
        verified=False,
    ),
    TypicalRange(
        "nash",
        "k_min",
        10.0,
        200.0,
        "min",
        *_NASH,
        notice="outside_unverified_range",
        verified=False,
    ),
    TypicalRange(
        "lutz",
        "area_km2",
        0.0,
        236.0,
        "km2",
        "KZGW (2017), annex 2, p. 96: the largest watershed the Lutz method is "
        "recommended for",
        "KZGW (2017), zał. 2, s. 96: największa zlewnia, dla której zaleca się "
        "metodę Lutza",
    ),
    TypicalRange(
        "clark",
        "r_tc_ratio",
        0.2,
        1.5,
        "-",
        "0.2-0.4 steep, urban; 0.4-0.8 average natural; 0.8-1.5 flat, swampy "
        "catchments (USACE, HEC-HMS Technical Reference Manual; engineering practice)",
        "0,2–0,4 zlewnie strome, zurbanizowane; 0,4–0,8 przeciętne naturalne; "
        "0,8–1,5 płaskie, podmokłe (USACE, HEC-HMS Technical Reference Manual; "
        "praktyka inżynierska)",
    ),
    TypicalRange(
        "snyder",
        "ct",
        1.35,
        1.65,
        "-",
        "KZGW (2017), annex 2, eq. 6.5; Snyder's (1938) 1.8-2.2 in English units "
        "times 0.75 in SI (Chow et al. 1988, 7.7)",
        "KZGW (2017), zał. 2, wzór 6.5; 1,8–2,2 Snydera (1938) w jednostkach "
        "angielskich razy 0,75 w SI (Chow i in. 1988, 7.7)",
    ),
    TypicalRange(
        "snyder",
        "cp",
        0.4,
        0.8,
        "-",
        "KZGW (2017), annex 2, eq. 6.7; Snyder (1938): 0.56-0.69 (USACE 2000, HEC-HMS)",
        "KZGW (2017), zał. 2, wzór 6.7; Snyder (1938): 0,56–0,69 (USACE 2000, HEC-HMS)",
    ),
    TypicalRange(
        "snyder",
        "area_km2",
        26.0,
        26000.0,
        "km2",
        "Snyder (1938): watersheds of the Appalachian Highlands, 10-10,000 mi² (Chow "
        "et al. 1988, 7.7)",
        "Snyder (1938): zlewnie Appalachów, 10–10 000 mi² (Chow i in. 1988, 7.7)",
    ),
    *(
        TypicalRange(
            model,
            "timestep_min",
            0.0,
            _TIMESTEP_SHARE,
            "min",
            *_TIMESTEP,
            relative_to="uh_time_to_peak_min",
        )
        for model in UH_MODELS
    ),
    # --- statistics --------------------------------------------------------------
    TypicalRange(
        "flood_frequency",
        "years",
        30.0,
        None,
        "years",
        "KZGW (2017): the series of annual maxima of a flood frequency analysis",
        "KZGW (2017): szereg maksimów rocznych w analizie częstości wezbrań",
        notice="short_record",
    ),
)
"""Every typical range, one per method and parameter."""

_BY_KEY: Final[Mapping[tuple[str, str], TypicalRange]] = {
    (entry.method, entry.parameter): entry for entry in TYPICAL_RANGES
}

_LENGTH = ("channel_length_km", "length_km")
_KERBY_KIRPICH = (
    "area_km2",
    "retardance",
    "overland_length_km",
    "overland_slope_m_per_m",
    "channel_length_km",
    "channel_slope_m_per_m",
)

TC_INPUTS: Final[Mapping[str, Mapping[str, tuple[str, ...]]]] = {
    "kirpich": {
        "area_km2": ("area_km2",),
        "length_km": _LENGTH,
        "slope_m_per_m": ("channel_slope_m_per_m", "mean_slope_m_per_m"),
    },
    "nrcs": {
        "area_km2": ("area_km2",),
        "length_km": _LENGTH,
        "slope_m_per_m": ("mean_slope_m_per_m", "channel_slope_m_per_m"),
        "cn": ("cn",),
    },
    "giandotti": {
        "area_km2": ("area_km2",),
        "length_km": _LENGTH,
        "elevation_diff_m": (),
    },
    "faa": {
        "length_km": ("overland_length_km",),
        "slope_m_per_m": ("overland_slope_m_per_m",),
        "runoff_coeff": ("runoff_coeff",),
    },
    "kerby": {
        "area_km2": ("area_km2",),
        "length_km": ("overland_length_km",),
        "slope_m_per_m": ("overland_slope_m_per_m",),
        "retardance": ("retardance",),
    },
    "kerby_kirpich": {name: (name,) for name in _KERBY_KIRPICH},
}
"""Watershed fields of the arguments of each time of concentration method.

For each method: argument name to the fields it is taken from, first choice first
(``area_km2`` too, though only Giandotti's formula takes it: the others are checked
against their data on the area of the watershed). A slope of Kirpich or NRCS without
its fields is the relief over the length, and Giandotti's elevation difference is
always derived: they list no field.
"""


def typical_range(method: str, parameter: str) -> TypicalRange:
    """Return the typical range of a parameter of a method.

    Parameters
    ----------
    method, parameter : str
        As in :class:`TypicalRange`.

    Returns
    -------
    TypicalRange
        The range.

    Raises
    ------
    KeyError
        If the method has no range for the parameter.
    """
    return _BY_KEY[(method, parameter)]


def typical_ranges(method: str) -> tuple[TypicalRange, ...]:
    """Return the typical ranges of a method, in the order of the table.

    Parameters
    ----------
    method : str
        As in :class:`TypicalRange`.

    Returns
    -------
    tuple of TypicalRange
        The ranges; empty for a method without any.
    """
    return tuple(entry for entry in TYPICAL_RANGES if entry.method == method)


def warn_if_outside(
    method: str,
    parameter: str,
    value: float,
    *,
    scale: float = 1.0,
    stacklevel: int = 2,
) -> None:
    """Warn if ``value`` is outside the typical range of a parameter of a method.

    Parameters
    ----------
    method, parameter : str
        The range (:func:`typical_range`).
    value : float
        The value.
    scale : float, optional
        The quantity the bounds are shares of (``relative_to``), else 1.
    stacklevel : int, optional
        As in ``warnings.warn``, counted from the caller of this function.
    """
    typical_range(method, parameter).check(
        value, scale=scale, stacklevel=stacklevel + 1
    )
