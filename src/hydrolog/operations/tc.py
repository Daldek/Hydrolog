"""Operations of the group ``tc``: time of concentration.

Each ``tc_<method>`` function wraps one static method of
:class:`~hydrolog.time.ConcentrationTime`; :func:`tc_watershed` applies a method to
:class:`~hydrolog.morphometry.WatershedParameters`. The library reports parameters
outside the typical range of a formula as ``UserWarning``; the operations turn them
into notices of the result envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, cast, get_args

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import OperationOutput, capture_warnings
from hydrolog.catalog.inputs import load_watershed
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.time import ConcentrationTime

__all__ = [
    "TC_METHODS",
    "TcMethod",
    "TcResult",
    "tc_faa",
    "tc_giandotti",
    "tc_kerby",
    "tc_kerby_kirpich",
    "tc_kirpich",
    "tc_nrcs",
    "tc_watershed",
    "watershed_concentration_time",
]

TcMethod = Literal["kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"]
TC_METHODS: tuple[str, ...] = get_args(TcMethod)
"""Methods accepted by :func:`tc_watershed` (``WatershedParameters.calculate_tc``)."""


@dataclass
class TcResult(JsonResultMixin):
    """Time of concentration with the parameters of the formula.

    Attributes
    ----------
    method : str
        Formula: ``"kirpich"``, ``"nrcs"``, ``"giandotti"``, ``"faa"``, ``"kerby"``
        or ``"kerby_kirpich"``.
    tc_min : float
        Time of concentration [min].
    tc_h : float
        Time of concentration [h] (``tc_min / 60``).
    parameters : dict of str to float
        Arguments of the formula (units as in the command options); for
        :func:`tc_watershed` the values actually derived from the watershed.
    watershed_name : str or None
        Name of the watershed (``tc watershed`` only).
    """

    method: str
    tc_min: float
    tc_h: float
    parameters: dict[str, float] = field(default_factory=dict)
    watershed_name: str | None = None


def _result(method: str, tc_min: float, parameters: dict[str, float]) -> TcResult:
    return TcResult(
        method=method,
        tc_min=tc_min,
        tc_h=tc_min / 60.0,
        parameters=parameters,
    )


def tc_kirpich(*, length_km: float, slope_m_per_m: float) -> OperationOutput:
    """Time of concentration by the Kirpich formula (``tc kirpich``).

    Parameters
    ----------
    length_km : float
        Main channel length from the watershed divide to the outlet [km], > 0.
    slope_m_per_m : float
        Mean slope of the main channel [m/m], > 0.

    Returns
    -------
    OperationOutput
        :class:`TcResult` (``tc_min = 3.981 * L**0.77 * S**-0.385``) with a notice
        for every parameter outside the typical range of the formula.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    with capture_warnings() as notices:
        tc_min = ConcentrationTime.kirpich(
            length_km=length_km, slope_m_per_m=slope_m_per_m
        )
    parameters = {"length_km": length_km, "slope_m_per_m": slope_m_per_m}
    return OperationOutput(_result("kirpich", tc_min, parameters), notices)


def tc_nrcs(*, length_km: float, slope_m_per_m: float, cn: float) -> OperationOutput:
    """Time of concentration by the NRCS (TR-55 lag) method (``tc nrcs``).

    Parameters
    ----------
    length_km : float
        Hydraulic length of the watershed [km], > 0.
    slope_m_per_m : float
        Mean watershed slope [m/m], > 0.
    cn : float
        Curve Number for AMC II, 1-100 (fractional values are accepted).

    Returns
    -------
    OperationOutput
        :class:`TcResult` with ``tc = tlag / 0.6`` and notices for parameters outside
        the typical range.

    Raises
    ------
    InvalidParameterError
        If a parameter is out of range.
    """
    with capture_warnings() as notices:
        # ConcentrationTime.nrcs is annotated ``cn: int`` but computes with any real.
        tc_min = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=slope_m_per_m, cn=cast(int, cn)
        )
    parameters = {"length_km": length_km, "slope_m_per_m": slope_m_per_m, "cn": cn}
    return OperationOutput(_result("nrcs", tc_min, parameters), notices)


def tc_giandotti(
    *, area_km2: float, length_km: float, elevation_diff_m: float
) -> OperationOutput:
    """Time of concentration by the Giandotti formula (``tc giandotti``).

    Parameters
    ----------
    area_km2 : float
        Watershed area [km2], > 0.
    length_km : float
        Main channel length [km], > 0.
    elevation_diff_m : float
        Difference between the mean watershed elevation and the outlet [m], > 0.

    Returns
    -------
    OperationOutput
        :class:`TcResult` (``tc = (4 sqrt(A) + 1.5 L) / (0.8 sqrt(H))`` hours,
        converted to minutes) with notices for parameters outside the typical range.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    with capture_warnings() as notices:
        tc_min = ConcentrationTime.giandotti(
            area_km2=area_km2, length_km=length_km, elevation_diff_m=elevation_diff_m
        )
    parameters = {
        "area_km2": area_km2,
        "length_km": length_km,
        "elevation_diff_m": elevation_diff_m,
    }
    return OperationOutput(_result("giandotti", tc_min, parameters), notices)


def tc_faa(
    *, length_km: float, slope_m_per_m: float, runoff_coeff: float
) -> OperationOutput:
    """Time of concentration by the FAA method (``tc faa``).

    Parameters
    ----------
    length_km : float
        Overland flow length [km], > 0.
    slope_m_per_m : float
        Mean ground slope [m/m], > 0.
    runoff_coeff : float
        Rational-method runoff coefficient, 0 < C <= 1.

    Returns
    -------
    OperationOutput
        :class:`TcResult` (``tc = 22.213 (1.1 - C) sqrt(L) / S**(1/3)``) with notices
        for parameters outside the typical range.

    Raises
    ------
    InvalidParameterError
        If a parameter is out of range.
    """
    with capture_warnings() as notices:
        tc_min = ConcentrationTime.faa(
            length_km=length_km,
            slope_m_per_m=slope_m_per_m,
            runoff_coeff=runoff_coeff,
        )
    parameters = {
        "length_km": length_km,
        "slope_m_per_m": slope_m_per_m,
        "runoff_coeff": runoff_coeff,
    }
    return OperationOutput(_result("faa", tc_min, parameters), notices)


def tc_kerby(
    *, length_km: float, slope_m_per_m: float, retardance: float
) -> OperationOutput:
    """Time of concentration by the Kerby formula (``tc kerby``).

    Parameters
    ----------
    length_km : float
        Overland flow length [km], > 0.
    slope_m_per_m : float
        Mean ground slope [m/m], > 0.
    retardance : float
        Kerby retardance coefficient N, > 0 (usually 0.02-0.80).

    Returns
    -------
    OperationOutput
        :class:`TcResult` (``tc = 36.37 (L N)**0.467 S**-0.2335``; ``S + 0.0005``
        below ``S = 0.002``) with notices for parameters outside the typical range.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    with capture_warnings() as notices:
        tc_min = ConcentrationTime.kerby(
            length_km=length_km,
            slope_m_per_m=slope_m_per_m,
            retardance=retardance,
        )
    parameters = {
        "length_km": length_km,
        "slope_m_per_m": slope_m_per_m,
        "retardance": retardance,
    }
    return OperationOutput(_result("kerby", tc_min, parameters), notices)


def tc_kerby_kirpich(
    *,
    overland_length_km: float,
    overland_slope_m_per_m: float,
    retardance: float,
    channel_length_km: float,
    channel_slope_m_per_m: float,
) -> OperationOutput:
    """Time of concentration by the composite Kerby-Kirpich method.

    Implements ``tc kerby-kirpich``: Kerby for the overland segment plus Kirpich for
    the channel segment.

    Parameters
    ----------
    overland_length_km : float
        Overland flow length [km], > 0.
    overland_slope_m_per_m : float
        Mean overland slope [m/m], > 0.
    retardance : float
        Kerby retardance coefficient N, > 0.
    channel_length_km : float
        Channel length from the start of the channel to the outlet [km], > 0.
    channel_slope_m_per_m : float
        Mean channel slope [m/m], > 0.

    Returns
    -------
    OperationOutput
        :class:`TcResult` (``tc = t_overland + t_channel``) with notices for
        parameters outside the typical ranges of the two formulas.

    Raises
    ------
    InvalidParameterError
        If a parameter is not positive.
    """
    with capture_warnings() as notices:
        tc_min = ConcentrationTime.kerby_kirpich(
            overland_length_km=overland_length_km,
            overland_slope_m_per_m=overland_slope_m_per_m,
            retardance=retardance,
            channel_length_km=channel_length_km,
            channel_slope_m_per_m=channel_slope_m_per_m,
        )
    parameters = {
        "overland_length_km": overland_length_km,
        "overland_slope_m_per_m": overland_slope_m_per_m,
        "retardance": retardance,
        "channel_length_km": channel_length_km,
        "channel_slope_m_per_m": channel_slope_m_per_m,
    }
    return OperationOutput(_result("kerby_kirpich", tc_min, parameters), notices)


def _effective_parameters(
    watershed: WatershedParameters, method: str
) -> dict[str, float]:
    """Derive formula arguments that ``WatershedParameters.calculate_tc`` derives.

    Taken from :meth:`WatershedParameters.tc_parameters`, the one place that
    selects them from the watershed fields (FAA and Kerby: the overland flow
    length and slope; Kirpich: the channel slope first; NRCS: the mean slope of
    the watershed first; Giandotti: mean elevation, by default the middle of the
    range, minus the outlet), so the result shows what the method was fed with.
    """
    return {
        name: float(value) for name, value in watershed.tc_parameters(method).items()
    }


def watershed_concentration_time(
    watershed: WatershedParameters,
    method: str = "kirpich",
    *,
    option: str = "watershed",
) -> TcResult:
    """Time of concentration of a watershed by one of the six methods.

    Wraps ``WatershedParameters.calculate_tc`` and reports its failures as
    validation errors that name the missing fields. Library warnings are *not*
    captured here (the caller owns the :func:`capture_warnings` block).

    Parameters
    ----------
    watershed : WatershedParameters
        Validated watershed parameters.
    method : str, optional
        One of :data:`TC_METHODS`, by default ``"kirpich"``.
    option : str, optional
        Name of the option the watershed came from (``"watershed"`` or
        ``"watershed_file"``), reported in ``details.option`` of the errors.

    Returns
    -------
    TcResult
        ``tc_min``, ``tc_h``, the formula arguments derived from the watershed and
        the watershed name.

    Raises
    ------
    InvalidParameterError
        If ``method`` is unknown (``details.reason = "choice"``) or the watershed
        lacks the fields the method needs (``details.reason = "missing_field"``,
        ``details.missing``), or the formula rejects a value.
    """
    if method not in TC_METHODS:
        raise InvalidParameterError(
            f"Unknown method {method!r}; allowed: {', '.join(TC_METHODS)}",
            details={
                "option": "method",
                "reason": "choice",
                "allowed": list(TC_METHODS),
                "value": method,
            },
        )
    try:
        tc_min = watershed.calculate_tc(method=method)
    except InvalidParameterError as exc:
        if exc.details.get("reason") == "missing_field":
            missing = list(exc.details["missing"])
            raise InvalidParameterError(
                f"Method {method!r} needs watershed parameters that are missing: "
                f"{', '.join(missing)}",
                details={
                    "option": option,
                    "reason": "missing_field",
                    "method": method,
                    "missing": missing,
                },
                hint=exc.hint
                or (
                    f"Add {', '.join(missing)} to the watershed parameters or use "
                    "another method."
                ),
            ) from exc
        raise InvalidParameterError(
            str(exc),
            details={"option": option, "reason": "invalid_value", "method": method},
            hint=exc.hint,
        ) from exc
    result = _result(method, tc_min, _effective_parameters(watershed, method))
    result.watershed_name = watershed.name
    return result


def tc_watershed(
    *,
    watershed: dict[str, Any] | None = None,
    watershed_file: str | None = None,
    method: TcMethod = "kirpich",
) -> OperationOutput:
    """Time of concentration from watershed parameters (``tc watershed``).

    Parameters
    ----------
    watershed : dict, optional
        Inline ``WatershedParameters`` object. Exactly one of ``watershed`` and
        ``watershed_file`` is required.
    watershed_file : str, optional
        JSON file in the ``WatershedParameters.to_json()`` format.
    method : {"kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"}, optional
        Formula, by default ``"kirpich"``. Length: ``channel_length_km``, else
        ``length_km``; slope: ``channel_slope_m_per_m``, then
        ``mean_slope_m_per_m``, then relief over length (``nrcs`` takes the mean
        slope of the watershed first: the average land slope Y of TR-55).
        ``nrcs`` needs ``cn``. ``faa`` and ``kerby`` time the overland flow, so
        they use ``overland_length_km`` and ``overland_slope_m_per_m`` (not the
        channel) and need them, besides ``runoff_coeff`` (``faa``) or
        ``retardance`` (``kerby``); for a watershed with a channel use
        ``kerby_kirpich``, which needs ``retardance``, ``overland_length_km``,
        ``overland_slope_m_per_m``, ``channel_length_km`` and
        ``channel_slope_m_per_m``.

    Returns
    -------
    OperationOutput
        :class:`TcResult` with notices for parameters outside the typical range.

    Raises
    ------
    InvalidParameterError
        If both or neither watershed source is given, the watershed is invalid, or
        the method needs fields the watershed lacks (``details.missing``).
    NotFoundError
        If ``watershed_file`` does not exist.
    InputDataError
        If ``watershed_file`` is malformed.
    """
    parameters = load_watershed(watershed=watershed, watershed_file=watershed_file)
    option = "watershed_file" if watershed_file is not None else "watershed"
    with capture_warnings() as notices:
        result = watershed_concentration_time(parameters, method, option=option)
    return OperationOutput(result, notices)
