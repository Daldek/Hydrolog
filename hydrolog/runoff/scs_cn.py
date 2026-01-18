"""SCS Curve Number method for runoff calculation."""

from dataclasses import dataclass
from enum import Enum
from typing import Union

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


class AMC(Enum):
    """
    Antecedent Moisture Condition (AMC).

    AMC represents the soil moisture condition before a storm event,
    which affects the runoff potential.

    Attributes
    ----------
    I : str
        Dry conditions - lowest runoff potential.
    II : str
        Average/normal conditions (default).
    III : str
        Wet conditions - highest runoff potential.
    """

    I = "dry"
    II = "normal"
    III = "wet"


@dataclass
class EffectivePrecipitationResult:
    """
    Result of effective precipitation calculation.

    Attributes
    ----------
    effective_mm : NDArray[np.float64] | float
        Effective precipitation (runoff depth) [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    cn_adjusted : int
        CN value used (adjusted for AMC if applicable).
    """

    effective_mm: Union[NDArray[np.float64], float]
    total_effective_mm: float
    retention_mm: float
    initial_abstraction_mm: float
    cn_adjusted: int


class SCSCN:
    """
    SCS Curve Number method for rainfall-runoff calculation.

    The SCS-CN method estimates direct runoff from rainfall based on
    land use, soil type, and antecedent moisture conditions.

    Parameters
    ----------
    cn : int
        Curve Number for AMC-II conditions (1-100).
        CN=100 means all precipitation becomes runoff.
    ia_coefficient : float, optional
        Initial abstraction coefficient, by default 0.2.
        Ia = ia_coefficient * S

    Examples
    --------
    >>> scs = SCSCN(cn=72)
    >>> result = scs.effective_precipitation(precipitation_mm=50.0)
    >>> print(f"Effective: {result.total_effective_mm:.2f} mm")
    Effective: 12.89 mm
    """

    def __init__(self, cn: int, ia_coefficient: float = 0.2) -> None:
        """
        Initialize SCS-CN calculator.

        Parameters
        ----------
        cn : int
            Curve Number for AMC-II (1-100).
        ia_coefficient : float, optional
            Initial abstraction coefficient, by default 0.2.

        Raises
        ------
        InvalidParameterError
            If cn not in range 1-100 or ia_coefficient not in range (0, 1].
        """
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"cn must be in range 1-100, got {cn}")
        if not 0 < ia_coefficient <= 1:
            raise InvalidParameterError(
                f"ia_coefficient must be in range (0, 1], got {ia_coefficient}"
            )

        self.cn = cn
        self.ia_coefficient = ia_coefficient

    def adjust_cn_for_amc(self, amc: AMC) -> int:
        """
        Adjust CN for Antecedent Moisture Condition.

        Parameters
        ----------
        amc : AMC
            Antecedent Moisture Condition (I, II, or III).

        Returns
        -------
        int
            Adjusted CN value.

        Notes
        -----
        Conversion formulas (Chow et al., 1988):
        - AMC-I (dry): CN_I = CN_II / (2.281 - 0.01281 * CN_II)
        - AMC-II (normal): CN_II (no change)
        - AMC-III (wet): CN_III = CN_II / (0.427 + 0.00573 * CN_II)
        """
        cn_ii = self.cn

        if amc == AMC.II:
            return cn_ii
        elif amc == AMC.I:
            # Dry conditions - lower CN
            cn_i = cn_ii / (2.281 - 0.01281 * cn_ii)
            return max(1, min(100, round(cn_i)))
        elif amc == AMC.III:
            # Wet conditions - higher CN
            cn_iii = cn_ii / (0.427 + 0.00573 * cn_ii)
            return max(1, min(100, round(cn_iii)))
        else:
            raise InvalidParameterError(f"Unknown AMC: {amc}")

    def retention(self, cn: int) -> float:
        """
        Calculate maximum retention S.

        Parameters
        ----------
        cn : int
            Curve Number (1-100).

        Returns
        -------
        float
            Maximum retention S [mm].

        Notes
        -----
        Formula: S = 25400/CN - 254 (metric)
        For CN=100, S=0 (no retention, all runoff).
        """
        if cn == 100:
            return 0.0
        return (25400.0 / cn) - 254.0

    def initial_abstraction(self, retention_mm: float) -> float:
        """
        Calculate initial abstraction Ia.

        Parameters
        ----------
        retention_mm : float
            Maximum retention S [mm].

        Returns
        -------
        float
            Initial abstraction Ia [mm].

        Notes
        -----
        Formula: Ia = ia_coefficient * S (default: Ia = 0.2 * S)
        Initial abstraction represents interception, depression
        storage, and infiltration before runoff begins.
        """
        return self.ia_coefficient * retention_mm

    def effective_precipitation(
        self,
        precipitation_mm: Union[NDArray[np.float64], float, list],
        amc: AMC = AMC.II,
    ) -> EffectivePrecipitationResult:
        """
        Calculate effective precipitation (runoff depth).

        Parameters
        ----------
        precipitation_mm : NDArray[np.float64] | float | list
            Precipitation depth(s) [mm]. Can be:
            - Single value (total precipitation)
            - Array of values (hyetograph intervals)
        amc : AMC, optional
            Antecedent Moisture Condition, by default AMC.II.

        Returns
        -------
        EffectivePrecipitationResult
            Result containing effective precipitation and parameters.

        Notes
        -----
        Formula: Pe = (P - Ia)² / (P - Ia + S) when P > Ia, else Pe = 0

        For array input, the effective precipitation is calculated
        cumulatively and then differenced to get incremental values.

        Examples
        --------
        >>> scs = SCSCN(cn=72)
        >>> result = scs.effective_precipitation(50.0)
        >>> print(f"Pe = {result.total_effective_mm:.2f} mm")
        Pe = 12.89 mm
        """
        # Adjust CN for moisture conditions
        cn_adjusted = self.adjust_cn_for_amc(amc)

        # Calculate retention and initial abstraction
        s = self.retention(cn_adjusted)
        ia = self.initial_abstraction(s)

        # Convert input to numpy array
        if isinstance(precipitation_mm, (int, float)):
            p_array = np.array([precipitation_mm], dtype=np.float64)
            is_scalar = True
        else:
            p_array = np.asarray(precipitation_mm, dtype=np.float64)
            is_scalar = False

        # Calculate cumulative precipitation
        p_cumulative = np.cumsum(p_array)

        # Calculate cumulative effective precipitation
        # Pe_cum = (P_cum - Ia)² / (P_cum - Ia + S) when P_cum > Ia
        pe_cumulative = np.zeros_like(p_cumulative)
        mask = p_cumulative > ia

        if s > 0:
            # Standard case
            pe_cumulative[mask] = (p_cumulative[mask] - ia) ** 2 / (
                p_cumulative[mask] - ia + s
            )
        else:
            # CN=100: all precipitation after Ia becomes runoff
            pe_cumulative[mask] = p_cumulative[mask] - ia

        # Calculate incremental effective precipitation
        pe_incremental = np.diff(pe_cumulative, prepend=0.0)

        # Ensure non-negative values
        pe_incremental = np.maximum(pe_incremental, 0.0)

        total_effective = float(pe_cumulative[-1])

        effective: Union[NDArray[np.float64], float]
        if is_scalar:
            effective = float(pe_incremental[0])
        else:
            effective = pe_incremental

        return EffectivePrecipitationResult(
            effective_mm=effective,
            total_effective_mm=total_effective,
            retention_mm=s,
            initial_abstraction_mm=ia,
            cn_adjusted=cn_adjusted,
        )

    def runoff_coefficient(
        self,
        precipitation_mm: float,
        amc: AMC = AMC.II,
    ) -> float:
        """
        Calculate runoff coefficient.

        Parameters
        ----------
        precipitation_mm : float
            Total precipitation depth [mm].
        amc : AMC, optional
            Antecedent Moisture Condition, by default AMC.II.

        Returns
        -------
        float
            Runoff coefficient C = Pe / P (0 to 1).

        Examples
        --------
        >>> scs = SCSCN(cn=72)
        >>> c = scs.runoff_coefficient(50.0)
        >>> print(f"C = {c:.3f}")
        C = 0.258
        """
        if precipitation_mm <= 0:
            return 0.0

        result = self.effective_precipitation(precipitation_mm, amc)
        return result.total_effective_mm / precipitation_mm
