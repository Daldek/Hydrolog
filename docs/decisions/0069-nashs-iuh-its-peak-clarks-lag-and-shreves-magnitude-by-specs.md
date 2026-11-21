# 0069. Nash's IUH and its peak, Clark's lag and Shreve's magnitude by specs; no peak of an IUH of n ≤ 1

- Status: accepted
- Date: 2026-11-21
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (specs, Nogat CMP),
  [ADR-0057](0057-the-unit-hydrographs-declared-by-specs.md) and [ADR-0058](0058-snyder-and-clark-declared-by-specs.md)
  (the other unit hydrographs), [ADR-0065](0065-morphometry-and-network-indices-by-specs.md) (Strahler's order and
  the network indices), the literature research of the unit hydrographs of 2026-11-18 (`unit-hydrographs.md`)

## Context

Four Tier A formulas of the unit hydrograph and river network families were left without specs after ADR-0057,
ADR-0058 and ADR-0065 (Nogat CMP-2.1): Nash's instantaneous unit hydrograph and its unit hydrograph of a rainfall
duration (`NashIUH`), the time to peak and the peak ordinate of that IUH (`NashIUH.time_to_peak_min`,
`peak_ordinate_per_min`), the lag of Clark's model (`ClarkIUH.lag_time_min`) and Shreve's magnitude
(`StreamNetwork.classify(OrderingMethod.SHREVE)`). The peak of Nash's IUH was tp = (n − 1) K and
up = (n − 1)^(n−1) e^−(n−1) / (K Γ(n)) for n > 1 and, for n ≤ 1, tp = 0 and up = 1/K. The IUH of n ≤ 1 reservoirs
decreases from the instant of the rainfall: it is 1/K at t = 0 for n = 1 and unbounded there for n < 1, so 1/K was a
peak the IUH of n < 1 does not have, and KZGW (2017, annex 2, eq. 6.14) defines tp = (N − 1) k as a time after the
rainfall, positive for N > 1 only. Nothing refused or flagged such an n: `NashIUH` takes n of 1–10 as a range to be
verified (ADR-0058) and computes the IUH of any positive n.

## Decision

1. **Four specs, `formula_version` 1.** `nash_iuh` (`hydrolog.runoff.nash_iuh.nash_unit_hydrograph`: the IUH at the
   step times, KZGW eq. 6.13, the lag n K, eq. 6.15, and the unit hydrograph of D by the exact S-curve P(n, t/K) of
   SciPy's `gammainc`, a delegated computation; status referenced by KZGW's Example 6.2), `nash_iuh_peak`
   (`nash_iuh_peak(n, k_min)`, `NashPeak`: eqs. 6.14 and 6.16 through logarithms; referenced by Table C.2 and
   Example 6.2, with SciPy's gamma density at its mode as an established oracle), `clark_lag`
   (`hydrolog.runoff.clark_iuh.clark_lag_time`: tc/2 + R; oracle only, the quadrature of the time-area curve and the
   first moment of the spec `clark`) and `shreve_magnitude` (`hydrolog.network.stream_order.shreve_magnitude`: 1 for a
   source, else the sum of the upstream magnitudes; referenced by the four cases of Esri's „How Stream Order works”).
   `NashIUH`, `ClarkIUH` and `StreamNetwork` compute through them; `uh nash`, `uh clark` and `network stats --method
   shreve` carry their `formula_versions`.
2. **The peak is a precondition of n > 1.** The spec `nash_iuh_peak` refuses n ≤ 1 with `validation_error`,
   `details.reason` `precondition_failed` and `details.constraint` `peak_defined`. Its other precondition,
   `representable`, asks for a K whose reciprocal float64 holds; `nash_iuh` refuses a subnormal n, for which SciPy's
   incomplete gamma is not monotonic.
3. **`NashIUH` gives no peak for n ≤ 1, with a notice.** `NashIUH.time_to_peak_min`, `peak_ordinate_per_min` and the
   same fields of `IUHResult` (`generate_iuh`) are `None` (null in `to_dict()`) for n ≤ 1, with the warning
   `IuhPeakUndefined`, notice `iuh_peak_undefined` (level `warning`, details `n` and `k_min`; Polish text in the
   GUI's notice labels). The IUH itself, its unit hydrographs and every command are computed as before; the plots of
   `hydrolog.visualization` print „brak (n ≤ 1)” and scale to the largest ordinate.

## Consequences

- Breaking for a library caller that reads the IUH's peak of n ≤ 1: 0 and 1/K become `None` with the notice; the
  type of the two properties and fields is `float | None`. No command returns them, so no envelope changes.
- `docs/FORMULAS.md` and `formulas/*.toml` list the four specs; the handbook includes their blocks by name and needs
  their Polish entries in `docs/podrecznik/_specs_pl.toml`.
- Results of n > 1 are unchanged but for the last digits of the peak, now computed through logarithms.

## Alternatives considered

- **Keep tp = 0 and up = 1/K for n ≤ 1:** true for n = 1 only, at the instant of the rainfall, which eq. 6.14 does not
  call a peak; wrong for n < 1, whose IUH is unbounded at t = 0.
- **Refuse n ≤ 1 in `NashIUH`:** the IUH and the unit hydrograph of such a cascade are defined and a fitted n may be
  below 1; only its peak is not.
- **The largest ordinate of the grid as the peak:** it depends on the time step and lies at the first step after
  t = 0, not at a peak of the IUH.
