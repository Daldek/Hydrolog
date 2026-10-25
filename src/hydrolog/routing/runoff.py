"""Runoff of a subcatchment: how a rainfall becomes a hydrograph (ADR-0012).

A subcatchment is one lumped, homogeneous area: it has no flow paths inside. What it
does with the rain that falls on it is the job of a *runoff model*, an object that turns
a hyetograph and the :class:`~hydrolog.morphometry.WatershedParameters` of the area into
a :class:`~hydrolog.routing.Hydrograph` at the time step of the network. The network
does not know the model; it calls the protocol, so a model that keeps state between the
steps (GR4J, HBV) plugs in the way the first one does, without touching the network.

:class:`RunoffModel` is the protocol. To be named in a ``hydrolog-network/1`` document
the class has a ``model``, reads and writes its own fields
(:meth:`~RunoffModel.from_document`, :meth:`~RunoffModel.to_document`) and is registered
in :data:`RUNOFF_MODELS`. One is in the package:

* ``curve-number``: :class:`CurveNumberRunoff`, the SCS Curve Number loss and a unit
  hydrograph (``scs``, ``nash``, ``clark`` or ``snyder``), by
  :class:`~hydrolog.runoff.HydrographGenerator`, with the fields of the command
  ``hydrograph generate``. The watershed gives the area, the CN and, when the time of
  concentration is not given, the data that a formula of it needs.

The watershed of a document is the object of ``WatershedParameters.to_dict()``; see
:func:`watershed_from_document`.

Examples
--------
>>> from hydrolog.morphometry import WatershedParameters
>>> from hydrolog.precipitation import BlockHietogram
>>> from hydrolog.routing import CurveNumberRunoff
>>> area = WatershedParameters(
...     area_km2=12.0, perimeter_km=18.0, length_km=6.0,
...     elevation_min_m=210.0, elevation_max_m=330.0, cn=75,
... )
>>> storm = BlockHietogram()
>>> rain = storm.generate(total_mm=40.0, duration_min=60.0, timestep_min=10.0)
>>> flood = CurveNumberRunoff(tc_min=90.0).hydrograph(rain, area, timestep_min=10.0)
>>> round(flood.peak_discharge_m3s, 2)
12.1
"""

from __future__ import annotations

import dataclasses
import math
import numbers
import typing
import warnings
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Protocol,
    Self,
    runtime_checkable,
)

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry.watershed_params import TC_METHODS, WatershedParameters
from hydrolog.precipitation.hietogram import HietogramResult
from hydrolog.routing._checks import in_range, one_complete_group, positive, shown
from hydrolog.routing._reading import (
    as_object,
    check_fields,
    constructor_arguments,
    fail,
    required,
    without_defaults,
)
from hydrolog.routing._registry import Registry
from hydrolog.routing.hydrograph import STEP_TOLERANCE, Hydrograph
from hydrolog.routing.parameters import Parameter, ParameterSource, parameter

if TYPE_CHECKING:
    from hydrolog.runoff.scs_cn import AMC

__all__ = [
    "RUNOFF_MODELS",
    "CurveNumberRunoff",
    "RunoffModel",
    "runoff_from_document",
    "watershed_from_document",
]

UH_MODELS: Final = ("scs", "nash", "clark", "snyder")
"""The unit hydrograph models of :class:`CurveNumberRunoff`."""
AMC_CLASSES: Final = ("I", "II", "III")
"""The antecedent moisture conditions of :class:`CurveNumberRunoff`."""
DEFAULT_TC_METHOD: Final = "kirpich"
"""The formula of the time of concentration when none was chosen, as in the command."""
_SNYDER_CT: Final = 1.5
_SNYDER_CP: Final = 0.6
_UH_OPTIONS: Final[Mapping[str, tuple[str, ...]]] = {
    "nash": ("nash_n", "nash_k_min"),
    "clark": ("clark_r_min", "clark_r_tc_ratio"),
    "snyder": (
        "snyder_length_km",
        "snyder_centroid_length_km",
        "snyder_ct",
        "snyder_cp",
    ),
}
_NEEDS_TC: Final = ("scs", "clark")


@runtime_checkable
class RunoffModel(Protocol):
    """What a subcatchment needs of its runoff model, and what a document needs of it.

    The calculation uses :meth:`validate`, :meth:`hydrograph` and :meth:`describe`. A
    model that a document can name has the rest: a ``model``, :meth:`to_document` and
    :meth:`from_document`, and is registered in :data:`RUNOFF_MODELS`.

    Attributes
    ----------
    model : str
        The ``model`` of the runoff in a document.
    """

    model: ClassVar[str]

    def validate(self, watershed: WatershedParameters) -> None:
        """Refuse a watershed that the model cannot work with.

        Called when the subcatchment is made, so that a watershed without the CN or the
        data of a formula is found there and not when the network is routed.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` (``missing_field``...) and ``details.field``.
        """
        ...

    def hydrograph(
        self,
        rainfall: HietogramResult,
        watershed: WatershedParameters,
        timestep_min: float,
    ) -> Hydrograph:
        """Return the discharge that the area gives for the rainfall.

        Parameters
        ----------
        rainfall : HietogramResult
            The depth of every step [mm], from time 0, at ``timestep_min``.
        watershed : WatershedParameters
            The area.
        timestep_min : float
            The time step of the network [min].

        Returns
        -------
        Hydrograph
            The discharge [m3/s] at ``timestep_min``, from time 0.
        """
        ...

    def describe(
        self,
        watershed: WatershedParameters | None = None,
        rainfall: HietogramResult | None = None,
    ) -> list[Parameter]:
        """List the values that the model uses.

        Parameters
        ----------
        watershed : WatershedParameters, optional
            With it the list holds the values that come from the area (its CN, the
            time of concentration that a formula gave).
        rainfall : HietogramResult, optional
            With it, with the watershed, the list holds the values that the rain
            gave too (the effective depth, the runoff coefficient).

        Returns
        -------
        list of Parameter
            Name, value, unit and source (``given``, ``computed``, ``default``).
        """
        ...

    def to_document(self) -> dict[str, Any]:
        """Return the model as the object of a document, with its ``model``."""
        ...

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Read the model from the object of a document (see :meth:`to_document`)."""
        ...


RUNOFF_MODELS: Registry[RunoffModel] = Registry(
    "model",
    key="model",
    reason="unknown_model",
    needs=("from_document", "to_document"),
)
"""The runoff models by name, the ``model`` of a ``runoff`` in a document: a new model
is a class that is registered here (``@RUNOFF_MODELS.register``)."""


def _option_error(
    option: str, reason: str, message: str, hint: str | None = None, **details: object
) -> InvalidParameterError:
    """Return the error of an option, in the vocabulary of the catalog."""
    return InvalidParameterError(
        message, details={"option": option, "reason": reason, **details}, hint=hint
    )


def _choice(option: str, value: object, allowed: Sequence[str]) -> str:
    """Return ``value`` when it is one of ``allowed``."""
    if not isinstance(value, str) or value not in allowed:
        raise _option_error(
            option,
            "choice",
            f"Option {option!r}: {shown(value)} is not one of {', '.join(allowed)}",
            allowed=list(allowed),
            value=shown(value),
        )
    return value


def _base_type(hint: object) -> object:
    """Return the base type of an optional field: ``float`` for ``float | None``."""
    arguments = [item for item in typing.get_args(hint) if item is not type(None)]
    return arguments[0] if arguments else hint


def watershed_from_document(document: object) -> WatershedParameters:
    """Read the ``watershed`` of a document: the object of ``WatershedParameters``.

    The fields are those of
    :class:`~hydrolog.morphometry.WatershedParameters`: ``area_km2``, ``perimeter_km``,
    ``length_km``, ``elevation_min_m`` and ``elevation_max_m`` are required, the rest
    is optional. A field that the class does not have is an error (the class itself
    ignores it).

    Parameters
    ----------
    document : mapping
        The object.

    Returns
    -------
    WatershedParameters
        The watershed.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type``, ``unknown_field``, ``missing_field``
        (``details.missing``) or the reason of the value, and ``details.field``.
    """
    fields = as_object(document, "The watershed")
    members = dataclasses.fields(WatershedParameters)
    names = [item.name for item in members]
    check_fields("The watershed", fields, names)
    mandatory = [
        item.name
        for item in members
        if item.default is dataclasses.MISSING
        and item.default_factory is dataclasses.MISSING
    ]
    missing = [name for name in mandatory if fields.get(name) is None]
    if missing:
        fail(
            f"The watershed needs {', '.join(missing)}",
            reason="missing_field",
            hint=f"Required: {', '.join(mandatory)}.",
            field=missing[0],
            missing=missing,
        )
    hints = typing.get_type_hints(WatershedParameters)
    for name, value in fields.items():
        if value is None:
            continue
        kind = _base_type(hints[name])
        valid = (
            isinstance(value, str)
            if kind is str
            else (
                not isinstance(value, bool)
                and isinstance(value, numbers.Real)
                and math.isfinite(value)
            )
        )
        if not valid:
            fail(
                f"{name} must be {'a string' if kind is str else 'a finite number'}, "
                f"got {shown(value)}",
                reason="type",
                field=name,
                value=shown(value),
            )
    return WatershedParameters(
        **{name: value for name, value in fields.items() if value is not None}
    )


def runoff_from_document(document: object) -> RunoffModel:
    """Read a ``runoff`` of a document: the class is found by its ``model``.

    Parameters
    ----------
    document : mapping
        The object: ``model`` and the fields of that model.

    Returns
    -------
    RunoffModel
        The model.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` (not an object), ``missing_field`` (no
        ``model``), ``unknown_model`` (``value`` and ``allowed``), or the reason that
        the class gives, with ``details.field``.
    """
    fields = as_object(document, "The runoff")
    name = required(
        "The runoff",
        fields,
        "model",
        hint=f"The models are {', '.join(RUNOFF_MODELS.names)}.",
    )
    cls = RUNOFF_MODELS.resolve(name, "The runoff", field="model")
    return cls.from_document(fields)


@RUNOFF_MODELS.register
class CurveNumberRunoff:
    """The SCS Curve Number loss and a unit hydrograph, by ``HydrographGenerator``.

    The model of the command ``hydrograph generate``, and with the same fields: the CN
    takes the rain that is not lost, the unit hydrograph (``uh_model``) spreads it in
    time. The area and the CN are those of the watershed; the time of concentration is
    given (``tc_min``) or computed from the watershed by a formula (``tc_method``,
    ``kirpich`` unless another one is chosen), and only the models ``scs`` and
    ``clark`` use it. The parameters of the other models are given by their fields:
    ``nash_n`` and ``nash_k_min``, ``clark_r_min`` or ``clark_r_tc_ratio``,
    ``snyder_length_km`` and ``snyder_centroid_length_km`` (``snyder_ct`` and
    ``snyder_cp`` are optional). A field that does not belong to the chosen
    ``uh_model`` is refused.

    Parameters
    ----------
    tc_min : float, optional
        Time of concentration [min], > 0; not with ``tc_method``; ``scs`` and ``clark``
        only.
    tc_method : str, optional
        The formula that gives it from the watershed: ``kirpich`` (the default when the
        model needs a time of concentration and ``tc_min`` is not given), ``nrcs``,
        ``giandotti``, ``faa``, ``kerby`` or ``kerby_kirpich``.
    ia_coefficient : float, optional
        Initial abstraction ratio, 0 < ratio <= 1, by default 0.2.
    amc : {"I", "II", "III"}, optional
        Antecedent moisture condition, by default ``"II"``.
    uh_model : {"scs", "nash", "clark", "snyder"}, optional
        Unit hydrograph model, by default ``"scs"``.
    nash_n, nash_k_min : float, optional
        Nash parameters ``n`` and ``K`` [min], > 0; both for ``nash``.
    clark_r_min : float, optional
        Clark storage constant ``R`` [min], > 0; for ``clark``, exactly one of it and
        ``clark_r_tc_ratio``.
    clark_r_tc_ratio : float, optional
        Clark ratio ``R / tc``, > 0.
    snyder_length_km, snyder_centroid_length_km : float, optional
        Snyder ``L`` and ``Lc`` [km], > 0; both for ``snyder``.
    snyder_ct, snyder_cp : float, optional
        Snyder coefficients, > 0; defaults 1.5 and 0.6.

    Raises
    ------
    InvalidParameterError
        With ``details.option`` and ``details.reason``: ``choice`` (``uh_model``,
        ``amc``, ``tc_method``), ``conflict`` (``tc_min`` with ``tc_method``),
        ``not_applicable`` (a field of another ``uh_model``, or a time of concentration
        for a model that has none), ``required`` (a field that the model needs),
        ``one_of`` (the two Clark fields), or the reason of a value (``type``,
        ``exclusive_minimum``, ``maximum``...).

    Examples
    --------
    >>> from hydrolog.routing import CurveNumberRunoff
    >>> model = CurveNumberRunoff(tc_min=90.0, ia_coefficient=0.05, amc="III")
    >>> model.to_document()
    {'model': 'curve-number', 'tc_min': 90.0, 'ia_coefficient': 0.05, 'amc': 'III'}
    """

    model: ClassVar[str] = "curve-number"

    def __init__(
        self,
        *,
        tc_min: float | None = None,
        tc_method: str | None = None,
        ia_coefficient: float = 0.2,
        amc: str = "II",
        uh_model: str = "scs",
        nash_n: float | None = None,
        nash_k_min: float | None = None,
        clark_r_min: float | None = None,
        clark_r_tc_ratio: float | None = None,
        snyder_length_km: float | None = None,
        snyder_centroid_length_km: float | None = None,
        snyder_ct: float | None = None,
        snyder_cp: float | None = None,
    ) -> None:
        """Create the model."""
        self._uh_model = _choice("uh_model", uh_model, UH_MODELS)
        self._amc = _choice("amc", amc, AMC_CLASSES)
        self._ia_coefficient = in_range(
            positive(ia_coefficient, "ia_coefficient"), "ia_coefficient", maximum=1.0
        )
        self._tc_min = None if tc_min is None else positive(tc_min, "tc_min")
        self._tc_method = (
            None if tc_method is None else _choice("tc_method", tc_method, TC_METHODS)
        )
        self._check_tc()
        given = {
            "nash_n": nash_n,
            "nash_k_min": nash_k_min,
            "clark_r_min": clark_r_min,
            "clark_r_tc_ratio": clark_r_tc_ratio,
            "snyder_length_km": snyder_length_km,
            "snyder_centroid_length_km": snyder_centroid_length_km,
            "snyder_ct": snyder_ct,
            "snyder_cp": snyder_cp,
        }
        self._uh: dict[str, float] = {
            name: positive(value, name)
            for name, value in given.items()
            if value is not None
        }
        self._check_uh()

    def _check_tc(self) -> None:
        """Check the time of concentration against itself and the unit hydrograph."""
        if self._tc_min is not None and self._tc_method is not None:
            raise _option_error(
                "tc_method",
                "conflict",
                "Give tc_min or tc_method, not both",
                "tc_method computes the time of concentration from the watershed; "
                "tc_min is a value.",
            )
        if self._uh_model not in _NEEDS_TC:
            for name, value in (
                ("tc_min", self._tc_min),
                ("tc_method", self._tc_method),
            ):
                if value is not None:
                    raise _option_error(
                        name,
                        "not_applicable",
                        f"Option {name!r} does not apply when uh_model is "
                        f"{self._uh_model!r}: the model does not use a time of "
                        "concentration",
                        "Only the scs and clark models use it.",
                    )

    def _check_uh(self) -> None:
        """Check the fields of the unit hydrograph model against the model."""
        model = self._uh_model
        for other, names in _UH_OPTIONS.items():
            if other == model:
                continue
            for name in names:
                if name in self._uh:
                    raise _option_error(
                        name,
                        "not_applicable",
                        f"Option {name!r} does not apply when uh_model is {model!r}",
                        f"These options belong to uh_model {other!r}.",
                    )
        if model == "clark":
            one_complete_group(
                self._uh, [["clark_r_min"], ["clark_r_tc_ratio"]], "The clark model"
            )
        elif model != "scs":
            for name in _UH_OPTIONS[model][:2]:
                if name not in self._uh:
                    raise _option_error(
                        name,
                        "required",
                        f"Option {name!r} is required when uh_model is {model!r}",
                    )

    # --- what the model is -----------------------------------------------------------

    @property
    def uh_model(self) -> str:
        """Str: the unit hydrograph model."""
        return self._uh_model

    @property
    def amc(self) -> str:
        """Str: the antecedent moisture condition, ``"I"``, ``"II"`` or ``"III"``."""
        return self._amc

    @property
    def ia_coefficient(self) -> float:
        """Float: the initial abstraction ratio."""
        return self._ia_coefficient

    @property
    def tc_min(self) -> float | None:
        """Float or None: the time of concentration that was given [min]."""
        return self._tc_min

    @property
    def tc_method(self) -> str | None:
        """Str or None: the formula that was chosen for the time of concentration."""
        return self._tc_method

    @property
    def _needs_tc(self) -> bool:
        """Whether the unit hydrograph model uses a time of concentration."""
        return self._uh_model in _NEEDS_TC

    @property
    def _formula(self) -> str:
        """Str: the formula of the time of concentration, the default if none chosen."""
        return self._tc_method or DEFAULT_TC_METHOD

    # --- the protocol ----------------------------------------------------------------

    def validate(self, watershed: WatershedParameters) -> None:
        """Refuse a watershed that the model cannot work with.

        A watershed without a CN, or without what the formula of the time of
        concentration needs, is refused.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``type`` (not a ``WatershedParameters``),
            ``missing_field`` (``details.field`` ``cn``, or ``details.missing`` the
            fields of the formula) or ``minimum`` (a CN below 1).
        """
        if not isinstance(watershed, WatershedParameters):
            raise _option_error(
                "watershed",
                "type",
                "The watershed must be a WatershedParameters, not "
                f"{type(watershed).__name__}",
            )
        if watershed.cn is None:
            raise InvalidParameterError(
                "The watershed has no cn: the curve-number model needs it",
                details={"reason": "missing_field", "field": "cn"},
                hint="Set cn (SCS Curve Number, AMC II) on the watershed.",
            )
        if watershed.cn < 1:
            raise InvalidParameterError(
                f"The curve number must be at least 1, got {watershed.cn:g}",
                details={
                    "reason": "minimum",
                    "field": "cn",
                    "minimum": 1,
                    "value": watershed.cn,
                },
            )
        if self._needs_tc and self._tc_min is None:
            watershed.tc_parameters(self._formula)

    def _time_of_concentration(self, watershed: WatershedParameters) -> float | None:
        """Return the time of concentration that the unit hydrograph uses [min]."""
        if not self._needs_tc:
            return None
        if self._tc_min is not None:
            return self._tc_min
        return watershed.calculate_tc(self._formula)

    def _uh_params(self, tc_min: float | None) -> dict[str, Any]:
        """Return ``uh_params`` of :class:`~hydrolog.runoff.HydrographGenerator`."""
        if self._uh_model == "nash":
            return {
                "n": self._uh["nash_n"],
                "k": self._uh["nash_k_min"],
                "k_unit": "min",
            }
        if self._uh_model == "clark":
            if "clark_r_min" in self._uh:
                return {"r": self._uh["clark_r_min"]}
            assert tc_min is not None  # the model needs it: _time_of_concentration
            return {"r": self._uh["clark_r_tc_ratio"] * tc_min}
        if self._uh_model == "snyder":
            return {
                "L_km": self._uh["snyder_length_km"],
                "Lc_km": self._uh["snyder_centroid_length_km"],
                "ct": self._uh.get("snyder_ct", _SNYDER_CT),
                "cp": self._uh.get("snyder_cp", _SNYDER_CP),
            }
        return {}

    def hydrograph(
        self,
        rainfall: HietogramResult,
        watershed: WatershedParameters,
        timestep_min: float,
    ) -> Hydrograph:
        """Return the direct runoff of the watershed, from time 0.

        It is the hydrograph of ``HydrographGenerator(...).generate(rainfall)``, to the
        last ordinate.

        Parameters
        ----------
        rainfall : HietogramResult
            The rain, at ``timestep_min``.
        watershed : WatershedParameters
            The area: its ``area_km2``, ``cn`` and the data of the formula of the time
            of concentration.
        timestep_min : float
            The time step of the network [min].

        Returns
        -------
        Hydrograph
            The discharge [m3/s].

        Raises
        ------
        InvalidParameterError
            If the watershed is not valid for the model (:meth:`validate`), the rain
            is at another time step (``details.reason`` ``timestep_mismatch``) or a
            parameter is rejected by a unit hydrograph.
        """
        from hydrolog.runoff.generator import HydrographGenerator

        self.validate(watershed)
        step = positive(timestep_min, "timestep_min")
        if abs(rainfall.timestep_min - step) > STEP_TOLERANCE * step:
            raise _option_error(
                "timestep_min",
                "timestep_mismatch",
                f"The rainfall has a time step of {rainfall.timestep_min:g} min, the "
                f"network of {step:g} min",
                "Nothing is resampled.",
                expected=step,
                value=rainfall.timestep_min,
            )
        assert watershed.cn is not None  # validate
        tc_min = self._time_of_concentration(watershed)
        generator = HydrographGenerator(
            area_km2=watershed.area_km2,
            cn=watershed.cn,
            tc_min=tc_min,
            ia_coefficient=self._ia_coefficient,
            uh_model=self._uh_model,
            uh_params=self._uh_params(tc_min),
        )
        result = generator.generate(rainfall, amc=self._moisture())
        return Hydrograph(result.hydrograph.times_min, result.hydrograph.discharge_m3s)

    def _moisture(self) -> AMC:
        """Return the antecedent moisture condition as the enum of the library."""
        from hydrolog.runoff.scs_cn import AMC

        return {"I": AMC.I, "II": AMC.II, "III": AMC.III}[self._amc]

    def describe(
        self,
        watershed: WatershedParameters | None = None,
        rainfall: HietogramResult | None = None,
    ) -> list[Parameter]:
        """List the options, what the watershed gives and what the rain gave.

        The options are ``"given"``, or ``"default"`` when they are the defaults of the
        constructor (the formula of the time of concentration, the Snyder coefficients,
        ``ia_coefficient``, ``amc``, ``uh_model``). From the watershed come the area
        and the CN (``"given"``), the time of concentration of a formula, the CN of the
        moisture condition, the retention and the initial abstraction (``"computed"``);
        with the rain too, the effective depth and the runoff coefficient.
        """
        from hydrolog.runoff.scs_cn import SCSCN

        listed: list[Parameter] = []

        def add(name: str, value: object, source: ParameterSource) -> None:
            listed.append(parameter(name, value, source))

        def chosen(value: object, default: object) -> ParameterSource:
            return "default" if value == default else "given"

        if watershed is not None:
            add("area_km2", watershed.area_km2, "given")
            if watershed.cn is not None:
                add("cn", watershed.cn, "given")
        add("ia_coefficient", self._ia_coefficient, chosen(self._ia_coefficient, 0.2))
        add("amc", self._amc, chosen(self._amc, "II"))
        add("uh_model", self._uh_model, chosen(self._uh_model, "scs"))
        tc_min: float | None = None
        if self._needs_tc:
            if self._tc_min is not None:
                tc_min = self._tc_min
                add("tc_min", tc_min, "given")
            else:
                add(
                    "tc_method",
                    self._formula,
                    "given" if self._tc_method else "default",
                )
                if watershed is not None:
                    with warnings.catch_warnings():
                        # the run has told the caller of a value outside the usual range
                        warnings.simplefilter("ignore")
                        tc_min = self._time_of_concentration(watershed)
                    add("tc_min", tc_min, "computed")
        for name, value in self._uh.items():
            add(name, value, "given")
        if self._uh_model == "snyder":
            for name, value in (("snyder_ct", _SNYDER_CT), ("snyder_cp", _SNYDER_CP)):
                if name not in self._uh:
                    add(name, value, "default")
        if "clark_r_tc_ratio" in self._uh and tc_min is not None:
            add("clark_r_min", self._uh["clark_r_tc_ratio"] * tc_min, "computed")
        if watershed is not None and watershed.cn is not None:
            scs = SCSCN(cn=watershed.cn, ia_coefficient=self._ia_coefficient)
            moisture = self._moisture()
            adjusted = scs.adjust_cn_for_amc(moisture)
            retention = scs.retention(adjusted)
            if adjusted != watershed.cn:
                add("cn_adjusted", adjusted, "computed")
            add("retention_mm", retention, "computed")
            add(
                "initial_abstraction_mm", scs.initial_abstraction(retention), "computed"
            )
            if rainfall is not None:
                effective = scs.effective_precipitation(
                    rainfall.intensities_mm, amc=moisture
                )
                add("total_effective_mm", effective.total_effective_mm, "computed")
                if rainfall.total_mm > 0.0:
                    add(
                        "runoff_coefficient",
                        effective.total_effective_mm / rainfall.total_mm,
                        "computed",
                    )
        return listed

    def to_document(self) -> dict[str, Any]:
        """Return ``model`` and the fields that are not the defaults.

        The fields are in the order of the constructor.
        """
        values = {
            "tc_min": self._tc_min,
            "tc_method": self._tc_method,
            "ia_coefficient": self._ia_coefficient,
            "amc": self._amc,
            "uh_model": self._uh_model,
            **self._uh,
        }
        given = {name: value for name, value in values.items() if value is not None}
        ordered = {
            name: given[name]
            for name in constructor_arguments(type(self))[0]
            if name in given
        }
        return {"model": self.model, **without_defaults(type(self), ordered)}

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Self:
        """Read the object of a document: the fields of the constructor.

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_field`` or the reason that the
            constructor gives, and ``details.option`` or ``details.field``.
        """
        names, _ = constructor_arguments(cls)
        check_fields("A curve-number runoff", document, ("model", *names))
        return cls(
            **{name: document[name] for name in names if document.get(name) is not None}
        )

    def __eq__(self, other: object) -> bool:
        """Compare the documents of two models."""
        return isinstance(other, CurveNumberRunoff) and (
            self.to_document() == other.to_document()
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Return the fields that are not the defaults."""
        fields = ", ".join(
            f"{name}={value!r}"
            for name, value in self.to_document().items()
            if name != "model"
        )
        return f"CurveNumberRunoff({fields})"
