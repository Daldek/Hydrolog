"""The PMAXTP depths of IMGW-PIB, fetched through Obserwator (extra ``pmaxtp``).

PMAXTP is the atlas of the maximum precipitation of a duration and a probability of
exceedance that IMGW-PIB publishes for every point of Poland, estimated by two methods:
POT (peaks over a threshold, the one IMGW-PIB recommends) and AMP (annual maxima).
:func:`fetch_depth` asks Obserwator (``obserwator.fetch_pmaxtp``), which queries the
PMAXTP API of IMGW-PIB for the table of a point, and picks the depth of one duration and
one probability. It is the only network access of Hydrolog (ADR-0018): Obserwator is
imported when a depth is fetched, and without it the fetch is a ``missing_dependency``
error that names the extra.

The durations and probabilities are those the tables of IMGW-PIB hold
(:data:`DURATIONS_MIN`, :data:`PROBABILITIES_PERCENT`, as Obserwator documents them);
another value is a ``validation_error`` that lists the allowed ones, before anything is
fetched. The errors of Obserwator become Hydrolog's registry codes: a point outside the
atlas is a ``validation_error`` of ``latitude`` (or of the coordinate Obserwator names),
an unreachable server ``source_unavailable`` and an answer that cannot be read
``data_error``. A depth of PMAXTP must name its source: the lines its terms prescribe
are in :mod:`hydrolog._attribution` (PS, PP, M and the terms link RK; ADR-0028).

The module is a leaf: it imports only :mod:`hydrolog.exceptions`, so the catalog can
read its values without Obserwator or the numerical libraries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, cast

from hydrolog.exceptions import (
    HydrologError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
)

__all__ = [
    "DURATIONS_MIN",
    "EXTRA",
    "INSTALL_HINT",
    "LATITUDE_RANGE",
    "LONGITUDE_RANGE",
    "METHODS",
    "PROBABILITIES_PERCENT",
    "TIMEOUT_S",
    "PmaxtpDepth",
    "PmaxtpMethod",
    "fetch_depth",
]

PmaxtpMethod = Literal["POT", "AMP"]
"""The estimation methods of PMAXTP: peaks over a threshold, annual maxima."""
METHODS: Final[tuple[str, ...]] = ("POT", "AMP")
"""The values of :data:`PmaxtpMethod`; POT is the default (IMGW-PIB recommends it)."""
DURATIONS_MIN: Final[tuple[int, ...]] = (
    5,
    10,
    15,
    30,
    45,
    60,
    90,
    120,
    180,
    360,
    720,
    1080,
    1440,
    2160,
    2880,
    4320,
)
"""The durations of the PMAXTP tables [min], 5 min to 72 h."""
PROBABILITIES_PERCENT: Final[tuple[float, ...]] = (
    0.01,
    0.02,
    0.03,
    0.05,
    0.1,
    0.2,
    0.3,
    0.5,
    1,
    2,
    3,
    5,
    10,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    95,
    98,
    98.5,
    99,
    99.5,
    99.9,
)
"""The probabilities of exceedance of the PMAXTP tables [%]."""
LATITUDE_RANGE: Final = (49.0, 55.0)
"""The latitudes of Poland that Obserwator accepts [degrees, WGS84]."""
LONGITUDE_RANGE: Final = (14.0, 24.5)
"""The longitudes of Poland that Obserwator accepts [degrees, WGS84]."""
EXTRA: Final = "pmaxtp"
"""The extra of Hydrolog that installs Obserwator."""
INSTALL_HINT: Final = 'pip install "hydrolog[pmaxtp]"'
"""Command that installs the extra, as shown in the ``missing_dependency`` error."""
TIMEOUT_S: Final = 20.0
"""How long a request to IMGW-PIB may take [s]: less than a run of the GUI (30 s)."""
_SOURCE: Final = "imgw-pmaxtp"
"""``details.source`` of the errors of IMGW-PIB."""


@dataclass(frozen=True)
class PmaxtpDepth:
    """The PMAXTP depth of a point, a duration and a probability.

    Attributes
    ----------
    depth_mm : float
        Maximum precipitation of the duration at the probability [mm].
    latitude, longitude : float
        The point [degrees, WGS84].
    method : {"POT", "AMP"}
        The estimation method.
    duration_min : float
        The duration [min], one of :data:`DURATIONS_MIN`.
    probability_percent : float
        The probability of exceedance [%], one of :data:`PROBABILITIES_PERCENT`.
    """

    depth_mm: float
    latitude: float
    longitude: float
    method: str
    duration_min: float
    probability_percent: float


def _not_offered(
    option: str, value: object, allowed: tuple[float, ...] | tuple[str, ...], what: str
) -> InvalidParameterError:
    """Build the error of a value that PMAXTP does not have, listing those it has."""
    listed = ", ".join(
        f"{item:g}" if isinstance(item, float) else str(item) for item in allowed
    )
    return InvalidParameterError(
        f"Option {option!r}: PMAXTP has no {what} {value!r}; it has {listed}",
        details={
            "option": option,
            "reason": "choice",
            "value": value if isinstance(value, str | int | float) else str(value),
            "allowed": list(allowed),
        },
        hint=f"Pick {option} from the values of the PMAXTP tables: {listed}.",
    )


def _check(
    method: str, duration_min: float, probability_percent: float
) -> tuple[PmaxtpMethod, int, float]:
    """Return the method, the duration and the probability, or fail naming the option.

    Raises
    ------
    InvalidParameterError
        If a value is not one that the PMAXTP tables hold (reason ``choice``).
    """
    if method not in METHODS:
        raise _not_offered("method", method, METHODS, "method")
    if isinstance(duration_min, bool) or duration_min not in DURATIONS_MIN:
        raise _not_offered("duration_min", duration_min, DURATIONS_MIN, "duration")
    if (
        isinstance(probability_percent, bool)
        or probability_percent not in PROBABILITIES_PERCENT
    ):
        raise _not_offered(
            "probability_percent",
            probability_percent,
            PROBABILITIES_PERCENT,
            "probability",
        )
    return cast(PmaxtpMethod, method), int(duration_min), float(probability_percent)


def _missing_obserwator(exc: ImportError) -> MissingDependencyError:
    """Build the ``missing_dependency`` error that names the extra ``pmaxtp``."""
    return MissingDependencyError(
        "precip pmaxtp fetches the depth through Obserwator, the optional extra "
        f"'{EXTRA}' (obserwator>=3.0.0.dev0,<4): cannot import 'obserwator' ({exc})",
        hint=INSTALL_HINT,
        details={"extra": EXTRA, "module": "obserwator"},
    )


def fetch_depth(
    latitude: float,
    longitude: float,
    duration_min: float,
    probability_percent: float,
    method: str = "POT",
) -> PmaxtpDepth:
    """Fetch the PMAXTP depth of a point from IMGW-PIB through Obserwator.

    Parameters
    ----------
    latitude, longitude : float
        A point in Poland [degrees, WGS84].
    duration_min : float
        The duration [min], one of :data:`DURATIONS_MIN`.
    probability_percent : float
        The probability of exceedance [%], one of :data:`PROBABILITIES_PERCENT`.
    method : {"POT", "AMP"}, optional
        The estimation method, by default POT.

    Returns
    -------
    PmaxtpDepth
        The depth of the cell of the PMAXTP table of the point.

    Raises
    ------
    InvalidParameterError
        If the method, the duration or the probability is not one of PMAXTP (reason
        ``choice``, ``details.allowed``), or the point lies outside the atlas (reason
        ``outside_pmaxtp``, ``details.option`` ``latitude`` or the coordinate that
        Obserwator names).
    MissingDependencyError
        If Obserwator is not installed (extra ``pmaxtp``).
    HydrologError
        Code ``source_unavailable``: IMGW-PIB did not answer.
    InputDataError
        If the answer of IMGW-PIB cannot be read or lacks the cell.
    """
    method, duration, probability = _check(method, duration_min, probability_percent)
    try:
        import obserwator
    except ImportError as exc:
        raise _missing_obserwator(exc) from exc
    try:
        result = obserwator.fetch_pmaxtp(
            latitude, longitude, method=method, timeout=TIMEOUT_S
        )
    except obserwator.ObserwatorValidationError as exc:
        named = exc.details.get("option")
        option = named if named in ("latitude", "longitude") else "latitude"
        raise InvalidParameterError(
            f"PMAXTP has no data for the point {latitude}, {longitude}: {exc}",
            details={
                "option": option,
                "reason": "outside_pmaxtp",
                "latitude": latitude,
                "longitude": longitude,
            },
            hint=(
                "PMAXTP covers Poland: give a point inside the country (WGS84, "
                f"latitude {LATITUDE_RANGE[0]:g}-{LATITUDE_RANGE[1]:g}, longitude "
                f"{LONGITUDE_RANGE[0]:g}-{LONGITUDE_RANGE[1]:g}), not at sea."
            ),
        ) from exc
    except obserwator.ObserwatorConnectionError as exc:
        raise HydrologError(
            f"IMGW-PIB did not answer the PMAXTP request: {exc}",
            code="source_unavailable",
            details={"source": _SOURCE, **dict(exc.details)},
            hint=(
                "Check the network and try again later, or give the depth yourself "
                "(`precip hietogram --total-mm`)."
            ),
        ) from exc
    except obserwator.ObserwatorError as exc:
        raise InputDataError(
            f"The PMAXTP answer of IMGW-PIB could not be read: {exc}",
            details={"source": _SOURCE},
        ) from exc
    depth = result.data.get_precipitation(duration, probability)
    if depth is None:
        raise InputDataError(
            f"The PMAXTP table of IMGW-PIB has no depth for {duration} min at "
            f"{probability:g} %",
            details={
                "source": _SOURCE,
                "duration_min": duration,
                "probability_percent": probability,
            },
        )
    return PmaxtpDepth(
        depth_mm=float(depth),
        latitude=float(latitude),
        longitude=float(longitude),
        method=method,
        duration_min=float(duration_min),
        probability_percent=probability,
    )
