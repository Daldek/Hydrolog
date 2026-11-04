"""The registry of notice codes, :data:`NOTICES` (plan D16).

Every notice that Hydrolog puts in a ``hydrolog-result/1`` envelope has a code listed
here with its level, its English template and the keys of its ``details``, so that a
client can word each notice by its code (the GUI in Polish) and fall back to the
English ``message``:

* an operation builds its notices with :func:`notice`: the message is the template
  filled with the details (:func:`hydrolog._warnings.render`), and the details are
  next to it in the envelope;
* a warning of the library (a :class:`hydrolog._warnings.HydrologWarning`, class
  ``OutsideTypicalRange`` for ``outside_typical_range``) caught by
  :func:`~hydrolog.catalog.capture_warnings` becomes a notice with the code, message
  and details of its class; the specs of those codes are made from the classes;
* an ``own_text`` code carries the English text of its emitter and no details: the
  notices of the routing models (``tail_extended``...; the routing code is not changed,
  plan D1) and the warnings of other libraries (``user_warning``,
  ``runtime_warning``). Their template only says what such a notice means.

``route network`` starts the message of a node's notice with ``"<node id>: "`` and
gives it ``details.node_id``. A routing model or a library warning has no other
details there, and the ``duration_not_covered`` of a node is worded by the routing
module (the rain of a node, not a hyetograph of ``precip hietogram``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

from hydrolog._warnings import (
    HydrologWarning,
    IncompleteYears,
    KsTestApproximate,
    OutsideTypicalRange,
    OutsideUnverifiedRange,
    ShortRecord,
    SmallSample,
    UhModelMismatch,
    UnknownHietogramType,
    render,
)
from hydrolog.catalog.envelope import Notice, NoticeLevel

__all__ = ["NOTICES", "NoticeSpec", "notice"]


@dataclass(frozen=True)
class NoticeSpec:
    """One code of the registry :data:`NOTICES`.

    Parameters
    ----------
    code : str
        Stable ``snake_case`` identifier of the notice.
    level : {"info", "warning"}
        Level of every notice of the code.
    template : str
        English message whose ``{name}`` fields are keys of ``details`` (a list is
        written as its items, at most 10); for an ``own_text`` code, a sentence of what
        such a notice means.
    details : tuple of str, optional
        Keys of the ``details`` that every notice of the code carries (a value may be
        null), by default none.
    own_text : bool, optional
        The notice carries the English text of its emitter and no details, by
        default ``False``.
    """

    code: str
    level: NoticeLevel
    template: str
    details: tuple[str, ...] = ()
    own_text: bool = False


def _library(warning: type[HydrologWarning]) -> NoticeSpec:
    """Return the spec of a library warning class: its code, level, template, keys."""
    return NoticeSpec(warning.code(), warning.level, warning.template, warning.keys)


def _own_text(code: str, level: NoticeLevel, meaning: str) -> NoticeSpec:
    """Return the spec of a code whose notices carry their emitter's text."""
    return NoticeSpec(code, level, meaning, own_text=True)


_SPECS: Final[tuple[NoticeSpec, ...]] = (
    NoticeSpec(
        "missing_values_removed",
        "warning",
        "{missing} of {total} values are missing (NaN) and were removed before the "
        "analysis",
        ("missing", "total", "first_date"),
    ),
    NoticeSpec(
        "missing_pairs_removed",
        "warning",
        "{missing} of {total} measurement pairs have a missing value (NaN) and were "
        "removed before the fit",
        ("missing", "total"),
    ),
    NoticeSpec(
        "condition_defaulted",
        "info",
        "No hydrologic condition given for {land_cover!r}: 'fair' was used.",
        ("land_cover",),
    ),
    NoticeSpec(
        "condition_ignored",
        "info",
        "{land_cover!r} has a single CN: condition {condition!r} was ignored.",
        ("land_cover", "condition"),
    ),
    NoticeSpec(
        "tc_not_used",
        "info",
        "tc = {tc_min:g} min is not used by the {uh_model} model.",
        ("tc_min", "uh_model"),
    ),
    NoticeSpec(
        "slopes_from_relief",
        "info",
        "{option} = {given_m_per_m:g} m/m is not used here: the slope is computed "
        "from the relief, {computed_m_per_m:.4g} m/m. The commands for the time of "
        "concentration use the given slope.",
        ("option", "given_m_per_m", "computed_m_per_m"),
    ),
    NoticeSpec(
        "mean_elevation_approximated",
        "info",
        "elevation_mean_m is not given: the mean elevation is approximated by "
        "(elevation_min_m + elevation_max_m) / 2",
    ),
    NoticeSpec(
        "channel_length_defaulted",
        "info",
        "channel_length_km is not given: the channel slope is computed with the "
        "watershed length",
    ),
    NoticeSpec(
        "duration_not_covered",
        "warning",
        "duration_min = {duration_min:g} is not a multiple of timestep_min = "
        "{timestep_min:g}: the hyetograph has {steps} steps and covers "
        "{covered_min:g} min.",
        ("duration_min", "timestep_min", "steps", "covered_min"),
    ),
    NoticeSpec(
        "stations_without_polygon",
        "warning",
        "Gauges without a polygon area were not used: {stations}.",
        ("stations",),
    ),
    NoticeSpec(
        "pmaxtp_attribution",
        "info",
        "Name IMGW-PIB as the source of this PMAXTP depth, in the wording of the "
        "result's `attribution`; terms of use: {terms_url}",
        ("attribution", "terms_url"),
    ),
    NoticeSpec(
        "ia_coefficient_nonstandard",
        "info",
        "ia_coefficient = {ia_coefficient:g}: the standard CN tables (TR-55) are "
        "calibrated for 0.2; other ratios need recalibrated CN values.",
        ("ia_coefficient",),
    ),
    NoticeSpec(
        "empty_area",
        "warning",
        "bbox does not overlap the raster: all counts and areas are zero",
    ),
    _library(IncompleteYears),
    NoticeSpec(
        "single_value_month",
        "warning",
        "Month(s) {months} hold a single value: their standard deviation, coefficient "
        "of variation, skewness and confidence interval are undefined (null)",
        ("months",),
    ),
    NoticeSpec(
        "large_result",
        "warning",
        "the result is {size_chars:,} characters, over the {page_chars:,} of a page "
        "that a client reads whole: give `nodes` to return fewer hydrographs, or "
        "`output_dir` to write one table per node",
        ("size_chars", "page_chars"),
    ),
    _library(OutsideTypicalRange),
    _library(OutsideUnverifiedRange),
    _library(SmallSample),
    _library(ShortRecord),
    _library(KsTestApproximate),
    _library(UnknownHietogramType),
    _library(UhModelMismatch),
    NoticeSpec(
        "exposed_without_auth",
        "warning",
        "The server listens on {host}, beyond this computer, and has no sign-in: "
        "anyone who reaches {url} can use it. Expose it only behind an "
        "authenticating proxy.",
        ("host", "url"),
    ),
    NoticeSpec(
        "superseded",
        "info",
        "A newer run of the same channel replaced this one.",
    ),
    NoticeSpec(
        "timeout",
        "warning",
        "The run took longer than {timeout_s:g} s and was stopped.",
        ("timeout_s",),
    ),
    _own_text(
        "user_warning",
        "warning",
        "A warning of another library, in its own words.",
    ),
    _own_text(
        "runtime_warning",
        "warning",
        "A numerical warning (NumPy, SciPy), in its own words.",
    ),
    _own_text(
        "tail_extended",
        "info",
        "The time axis was extended after the last inflow ordinate for the outflow "
        "to settle.",
    ),
    _own_text(
        "lag_interpolated",
        "info",
        "The lag is not a whole number of time steps: the shifted ordinates are "
        "interpolated linearly, which flattens sharp peaks.",
    ),
    _own_text(
        "timestep_refined",
        "info",
        "Each time step was divided into sub-steps that the routing method needs; "
        "the volume balance has a sampling error.",
    ),
    _own_text(
        "substeps_added",
        "info",
        "No number of sub-reaches keeps the routing weights non-negative on this "
        "time step: each step was divided into sub-steps.",
    ),
    _own_text(
        "subreaches_adjusted",
        "info",
        "The number of distance steps of the NRCS rule was changed to keep the "
        "routing weights non-negative.",
    ),
    _own_text(
        "accuracy_limit",
        "info",
        "The grid of the NRCS rule is beyond the accuracy limit of NEH-630: the reach "
        "was routed on a grid inside the limit.",
    ),
    _own_text(
        "tail_truncated",
        "warning",
        "The outflow had not settled to within 0.1 % of the inflow peak at the end of "
        "the series.",
    ),
)

NOTICES: Final[Mapping[str, NoticeSpec]] = MappingProxyType(
    {spec.code: spec for spec in _SPECS}
)
"""Every notice code of Hydrolog and its :class:`NoticeSpec` (read-only).

The codes of operations come first, then those of the library warnings, the GUI
server, other libraries and the routing models.
"""


def notice(code: str, /, **details: Any) -> Notice:
    """Build a notice of a registered code from its details.

    Parameters
    ----------
    code : str
        A code of :data:`NOTICES` that is not ``own_text``.
    **details : Any
        Exactly the detail keys of the code (``NOTICES[code].details``); a value may
        be ``None``.

    Returns
    -------
    Notice
        The level of the code, the template filled with the details as the message
        (:func:`hydrolog._warnings.render`) and the details in the order of the
        registry (``None`` when the code has none).

    Raises
    ------
    ValueError
        If the code is not in :data:`NOTICES`, carries the text of its emitter
        (``own_text``), or the details are not exactly its keys.

    Examples
    --------
    >>> item = notice("tc_not_used", tc_min=90.0, uh_model="nash")
    >>> item.message
    'tc = 90 min is not used by the nash model.'
    >>> item.to_dict()["details"]
    {'tc_min': 90.0, 'uh_model': 'nash'}
    """
    spec = NOTICES.get(code)
    if spec is None:
        raise ValueError(f"Unknown notice code {code!r}: it is not in NOTICES")
    if spec.own_text:
        raise ValueError(
            f"Notice {code!r} carries the text of its emitter: build a Notice directly"
        )
    if set(details) != set(spec.details):
        raise ValueError(
            f"Notice {code!r} takes the details {', '.join(spec.details) or '(none)'}; "
            f"got {', '.join(details) or '(none)'}"
        )
    ordered = {key: details[key] for key in spec.details}
    return Notice(spec.level, code, render(spec.template, ordered), ordered or None)
