"""Operations of the group ``scs``: effective precipitation by SCS-CN.

Wraps :class:`~hydrolog.runoff.SCSCN`. The helpers :func:`to_amc`,
:func:`load_precipitation_depths` and :func:`ia_coefficient_notices` are shared with
``hydrograph generate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast, get_args

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_series
from hydrolog.exceptions import InputDataError
from hydrolog.operations._common import check_choice, option_error, select_group
from hydrolog.runoff import AMC, SCSCN

__all__ = [
    "AMC_CLASSES",
    "Amc",
    "ScsEffectiveResult",
    "ia_coefficient_notices",
    "load_precipitation_depths",
    "scs_effective",
    "to_amc",
]

Amc = Literal["I", "II", "III"]
AMC_CLASSES: tuple[str, ...] = get_args(Amc)

_AMC = {"I": AMC.I, "II": AMC.II, "III": AMC.III}
_STANDARD_IA = 0.2


@dataclass
class ScsEffectiveResult(JsonResultMixin):
    """Effective precipitation by SCS-CN.

    Attributes
    ----------
    cn : float
        Curve Number for AMC II as given.
    amc : str
        Antecedent moisture condition used (``"I"``, ``"II"`` or ``"III"``).
    cn_adjusted : float
        CN after the AMC adjustment (an integer for AMC I and III).
    ia_coefficient : float
        Initial abstraction ratio.
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    total_precipitation_mm : float
        Total precipitation [mm] (sum of the series).
    total_effective_mm : float
        Total effective precipitation [mm].
    runoff_coefficient : float
        ``total_effective_mm / total_precipitation_mm`` (0 without precipitation).
    effective_mm : numpy.ndarray or None
        Effective precipitation of each step [mm]; ``None`` for a total.
    """

    cn: float
    amc: str
    cn_adjusted: float
    ia_coefficient: float
    retention_mm: float
    initial_abstraction_mm: float
    total_precipitation_mm: float
    total_effective_mm: float
    runoff_coefficient: float
    effective_mm: NDArray[np.float64] | None = None


def to_amc(amc: str) -> AMC:
    """Convert ``"I"``, ``"II"`` or ``"III"`` to :class:`~hydrolog.runoff.AMC`.

    Parameters
    ----------
    amc : str
        Antecedent moisture condition.

    Returns
    -------
    AMC
        The enum member.

    Raises
    ------
    InvalidParameterError
        If ``amc`` is not one of :data:`AMC_CLASSES`.
    """
    return _AMC[check_choice("amc", amc, AMC_CLASSES)]


def ia_coefficient_notices(ia_coefficient: float) -> list[Notice]:
    """Notice for an initial abstraction ratio other than the standard 0.2.

    Parameters
    ----------
    ia_coefficient : float
        Initial abstraction ratio.

    Returns
    -------
    list of Notice
        One info notice when the ratio differs from 0.2 (the standard CN tables
        are calibrated for it), else empty.
    """
    if ia_coefficient == _STANDARD_IA:
        return []
    return [
        Notice(
            "info",
            "ia_coefficient_nonstandard",
            f"ia_coefficient = {ia_coefficient:g}: the standard CN tables (TR-55) "
            "are calibrated for 0.2; other ratios need recalibrated CN values.",
        )
    ]


def load_precipitation_depths(
    *,
    values: list[float] | None,
    input_file: str | None,
    value_column: str | None,
) -> NDArray[np.float64]:
    """Precipitation depths per step from inline values or a file.

    Parameters
    ----------
    values : list of float, optional
        Inline depths [mm].
    input_file : str, optional
        CSV or JSON file (see :func:`hydrolog.catalog.inputs.load_series`).
    value_column : str, optional
        Column of ``input_file`` holding the depths.

    Returns
    -------
    numpy.ndarray
        Depths [mm], one per step.

    Raises
    ------
    InvalidParameterError
        If neither or both sources are given, or an inline value is missing or
        negative.
    InputDataError
        If the file is malformed or holds a missing or negative value.
    NotFoundError
        If ``input_file`` does not exist.
    """
    series = load_series(
        values=values, input_file=input_file, value_column=value_column
    )
    depths = series.values
    for problem, mask in (
        ("missing_value", np.isnan(depths)),
        ("negative_value", depths < 0),
    ):
        if mask.any():
            row = int(np.flatnonzero(mask)[0]) + 1
            what = "is missing" if problem == "missing_value" else "is negative"
            message = f"precipitation value in row {row} {what}"
            if series.source == "inline":
                raise option_error(
                    "values", problem, f"Option 'values': {message}", index=row - 1
                )
            raise InputDataError(
                f"{series.source}: {message}",
                details={
                    "path": str(series.source),
                    "reason": problem,
                    "row": row,
                },
            )
    return depths


def scs_effective(
    *,
    cn: float,
    precipitation_mm: float | None = None,
    values: list[float] | None = None,
    input_file: str | None = None,
    value_column: str | None = None,
    amc: Amc = "II",
    ia_coefficient: float = 0.2,
) -> OperationOutput:
    """Effective precipitation by the SCS-CN method (``scs effective``).

    Give exactly one of ``precipitation_mm``, ``values`` and ``input_file``.

    Parameters
    ----------
    cn : float
        Curve Number for AMC II, 1-100 (fractional values are accepted).
    precipitation_mm : float, optional
        Total precipitation [mm], >= 0.
    values : list of float, optional
        Precipitation depths per time step [mm], each >= 0.
    input_file : str, optional
        CSV or JSON file with the depths per step.
    value_column : str, optional
        Column of ``input_file`` with the depths.
    amc : {"I", "II", "III"}, optional
        Antecedent moisture condition, by default ``"II"``.
    ia_coefficient : float, optional
        Initial abstraction ratio, 0 < ratio <= 1, by default 0.2.

    Returns
    -------
    OperationOutput
        :class:`ScsEffectiveResult` and an info notice when ``ia_coefficient`` is
        not the standard 0.2.

    Raises
    ------
    InvalidParameterError
        If the precipitation source is ambiguous or missing, ``cn`` or
        ``ia_coefficient`` is out of range, or an inline value is missing or
        negative.
    InputDataError
        If ``input_file`` is malformed or holds a missing or negative value.
    NotFoundError
        If ``input_file`` does not exist.
    """
    select_group(
        {
            "precipitation_mm": precipitation_mm,
            "values": values,
            "input_file": input_file,
            "value_column": value_column,
        },
        {
            "total": ("precipitation_mm",),
            "values": ("values",),
            "file": ("input_file",),
        },
        extra={"value_column": "file"},
    )
    calculator = SCSCN(cn=cast(int, cn), ia_coefficient=ia_coefficient)
    moisture = to_amc(amc)
    total: float
    effective: NDArray[np.float64] | None
    if precipitation_mm is not None:
        total = float(precipitation_mm)
        outcome = calculator.effective_precipitation(total, moisture)
        effective = None
    else:
        depths = load_precipitation_depths(
            values=values, input_file=input_file, value_column=value_column
        )
        total = float(np.sum(depths))
        outcome = calculator.effective_precipitation(depths, moisture)
        effective = np.asarray(outcome.effective_mm, dtype=np.float64)
    result = ScsEffectiveResult(
        cn=float(cn),
        amc=amc,
        cn_adjusted=outcome.cn_adjusted,
        ia_coefficient=ia_coefficient,
        retention_mm=outcome.retention_mm,
        initial_abstraction_mm=outcome.initial_abstraction_mm,
        total_precipitation_mm=total,
        total_effective_mm=outcome.total_effective_mm,
        runoff_coefficient=outcome.total_effective_mm / total if total > 0 else 0.0,
        effective_mm=effective,
    )
    return OperationOutput(result, ia_coefficient_notices(ia_coefficient))
