# 0073. The signatures of CAMELS-PL 2.1.0 as reference cases; five signatures by specs

- Status: accepted
- Date: 2026-11-23
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md), [ADR-0063](0063-the-station-statistics-by-specs.md),
  Nogat's computation standard (CMP-5.1, CMP-5.2, CMP-6.1, CMP-6.10), Nogat DEV §20 (DEV-20.12, ECO-086) and Nogat plan
  `2026-11-22-camels-pl`, step 5 (the author's decision 5 of 2026-11-22: „Sygnatur użyjemy do testów”)

## Context

CAMELS-PL 2.1.0 (Brzezińska et al. 2026, Zenodo record 23275336, CC BY 4.0) publishes, for its 869 gauges, the
hydrological signatures of CAMELS (Addor et al. 2017): the baseflow index of the Lyne and Hollick filter with α 0.925,
Q5 and Q95, the slope of the duration curve between its 33rd and 66th percentiles, the frequency and duration of high
(> 9 × median) and low (< 0.2 × mean) flows, the share of days without flow and the mean half-flow date. Hydrolog had
the filter, the index and the duration curve, but not the other five. The data description defines the signatures in
one line each and ships no code; how they were computed had to be found from the data.

## Decision

1. **How CAMELS-PL computed them, found on all 869 gauges (2026-11-23).** The code of CAMELS-DE
   (`08_hydrologic_attributes.ipynb`, Dolich 2024) with the hydrological year from 1 November reproduces every value but
   the baseflow index: the years with at most 5 % of their days missing, the zero days dropped before the slope, the
   frequencies divided by every day of the kept years (the missing ones too), a missing day ending a run, Python's
   `round`, and numpy's `nearest` quantiles (not CAMELS-DE's linear ones) for Q5, Q95 and the slope, whose percentiles
   are non-exceedance ones (the flows exceeded on 34 and 67 % of the days, as Addor et al. 2017, not Sawicz et al.'s 33
   and 66 %). The baseflow index is reproduced (139 of 139 gauges without a missing day, 824 of 869) by the two-pass
   filter of the `baseflow` package (Xie et al. 2020: forward then backward, the baseflow at most the flow, b = Q on the
   first day) on the days with a value to 2023-12-31.
2. **Five new formulas, `formula_version` 1, status referenced** (`hydrolog.statistics.signatures`): `fdc_slope`
   (Sawicz et al. 2011, eq. 3, on Hydrolog's duration curve, between two exceedance percentages, 33 and 66 by default;
   zeros are values and a curve at 0 is refused), `high_flow_days` and `low_flow_days` (frequency per day with a value
   × 365.25 and mean run length, 0 and 0 without an event; Westerberg and McMillan 2015, Table 2), `zero_flow_fraction`
   (share of the days with a value) and `half_flow_date` (the first day of a year whose summed flow exceeds half of
   the year's, summed exactly; Court 1962, the code of CAMELS-US). Each takes a sample, never a calendar (ADR-0063).
   The comparisons run on the values divided by a power of two, so every signature is exactly free of the unit.
3. **Thirteen gauges as reference cases** (`tests/fixtures/formulas/camels-pl-cases.json`, 104 cases): 6 to
   193,728 km², Sudetes, Carpathians, upland, lowland, lake-district and wetland rivers, the Odra and the Wisła, four
   with zero flows; their published daily discharge is kept in `tests/fixtures/camels_pl/` with
   `CAMELS_PL_ATTRIBUTION.txt` and the script that extracted it. The cases are pinned to the release (CMP-6.10): the
   attribution file names its record, version and DOI and gives the SHA-256 of the ZIP, of the data description and of
   each member read, and each case's locator names the release and the SHA-256 of the files it reads; the file carries
   the provider lines S and P (IMGW-PIB's discharge) and L and LP (CAMELS-PL 2.1.0) of Nogat DEV §20 (DEV-20.12).
   Each case names CAMELS-PL's sample and lists the steps where its computation and Hydrolog's part
   (CMP-6.1): the `nearest` order statistic against Hydrolog's Weibull interpolation (the spread of the order statistics
   between the two positions), the half-flow dates of years that tie in the published decimals (1/N each), the binary
   representation of decimals (10⁻¹²). The frequencies and the share are compared after the conversion to CAMELS-PL's
   denominator. Q5 and Q95 are cases of `exceedance_values` (95 and 5 %).
4. **The baseflow index is a discrepancy (CMP-5.2), recorded, not hidden.** CAMELS-PL's filter is not Hydrolog's:
   Hydrolog follows Ladson et al.'s standard approach (three passes, the quickflow unclipped, 30 values reflected),
   CAMELS-PL two passes with the quickflow clipped at 0. On the thirteen gauges Hydrolog's index differs from the
   two-pass filter by −0.045 to +0.027; the test checks the cause (the two-pass filter gives CAMELS-PL's values) and
   Hydrolog's numbers.

## Consequences

- Every signature but the baseflow index matches CAMELS-PL 2.1.0 on the thirteen gauges within the stated tolerances.
- A newer release of CAMELS-PL changes the cases only by a deliberate change: the script is run again on its ZIP and
  data description, whose SHA-256 it checks, and the pins of every case move with it.
- No command and no result schema change; the functions are new public library functions.

## Alternatives considered

- **CAMELS-PL's conventions in the formulas** (the `nearest` quantiles, the frame as denominator, zeros dropped):
  Hydrolog keeps one duration curve (Weibull positions) and the definitions of the primary sources; the cases carry the
  differences.
- **CAMELS-PL's two-pass filter as a second baseflow filter:** two filters of one name would differ by up to 0.19
  (the indices of the 869 gauges); the standard approach stays the one.
