# 0029. Station analyses for Obserwator: characteristic values of both degrees, threshold events, rating curves by period, low flows across gaps, duration curves and runoff volumes

- Status: accepted
- Date: 2026-11-13
- Builds on: plan `docs/plans/2026-11-13-station-analyses.md` (decisions D1 to D8, step S1), Nogat's plan `2026-11-12-station-data-and-analyses` (step H1, decisions D6, D8, D12, F1), approved by the author on 2026-11-13; ADR-0028 (the providers' lines)

## Context

Nogat's plan of 2026-11-12 makes Hydrolog the one computer of the station analyses that Obserwator stores and serves (ECO-059): the same series and options give the same number in Obserwator and in Hydrolog. Obserwator's GUI mockup computed most of its hydrological sections in labelled prototypes (`mockup/gui/server/analyses/_hydro_proto.py`, Obserwator branch `feat/gui-mockup`). The author answered on 2026-11-13: reference periods are the whole record by default, adjustable, with a note under 30 years; IMGW-PIB's warning and alarm levels are not archived.

## Decision

1. **The reference period** (plan D1): `first_year` and `last_year`, hydrological years, the whole record by default; the result names the period (`first_year`, `last_year`, `period_years`); a result that characterises the period as a whole gives the notice `short_reference_period` (info) under 30 years. A period without a value is `calculation_error`, `no_values_in_period`.
2. **`stats characteristic`** (D3): the first degree of each hydrological year and half-year (`years`: min, mean, max with the dates of the extremes and the days with data) and the second degree of each half-year (`winter`, `summer`) beside the year's (the top-level keys, unchanged); `labels` (WWQ…NNQ, WWW…NNW, WWT…NNT) and `first_degree_labels`; `parameter` gains T; `half_year_file` reads Obserwator's export of IMGW-PIB's half-year characteristics, the annual maximum being the larger of the half-year maxima (F1). A year with missing days stays in the values, named in `incomplete_years` and the notice `years_with_missing_days`.
3. **`stats threshold-events`** (D4, new): runs of days at or above a level (or below it), with start, end, duration, peak and the days beyond it per hydrological year; the threshold level method on the calendar of the series, a day without a value ending a run unless `max_gap_days` bridges it.
4. **`hydrometrics rating-curve`** (D5): dates of the pairs (`dates`, `date_column`), `first_year`/`last_year`, and `years_per_period`: the curve of each block of years starting at y with (y − 1) mod n = 0, fitted from 30 pairs, read at the median level and discharge of the pairs. The result is `RatingCurveAnalysis`, a `RatingCurveResult` with `first_year`, `last_year`, `periods`, `reference_level`, `reference_discharge_m3s`.
5. **`stats low-flow-sequences`** (D6): gaps in the record are allowed (a day without a value is a gap day; the errors `missing_values` and `date_gap` are gone); `threshold_method` `value`, `mean_annual_minimum` (SNQ) or `exceedance` (`exceedance_percent`, Q70 by default); `parameter` Q gives deficit volumes in m³; a summary per hydrological year (a sequence counts in the year it starts). `LowFlowAnalysis.detect_sequences` lays the flows on their calendar, so its sequences carry `missing_days`, `open_start`, `open_end`.
6. **`stats duration-curve`** (D7, new): the Weibull duration curve and its table, the classes of equal width from a multiple of the width (the author's 10 cm table) or logarithmic, with the days including higher and lower, by hydrological month, and the modal class.
7. **`stats runoff-volume`** (D8, new): the volumes of years and months, their means over complete years and months, the cumulative volume of a year and the mean one.
8. Budgets: the three new commands join the compact `stats` line of `AGENTS.md` (16,045 of 16,384 bytes); every description stays within 600 characters.

## Consequences

- Additive for the existing schemas (`_ADDED_FIELDS`); three new result schemas. The only behaviour change is that `stats low-flow-sequences` computes across gaps it refused, and `stats characteristic` names partial years and short periods in notices.
- The numbers of the mockup's prototypes on Kłodzko (150160180, 1951–2025 without 1997) are reproduced exactly by the new commands (the plan's Results); the classes of a period whose lowest value is not a multiple of the class width start at that multiple, where the mockup took `hydrometrics water-level-zones` classes from the floored lowest value.
- The providers' lines (ADR-0028) reach these results as every `stats` result's: the readers of `hydrolog.catalog.inputs` cite the lines of an input file (an Obserwator export, IMGW-PIB's half-year file), and the three new commands take the option `attribution` for a series given inline.

## Alternatives considered

- **One command for events above and below a level and the low-flow deficits**: the low-flow sequences keep their own defaults (5 days, gaps under 4 days), thresholds from the series and deficits; events above a level have peaks and days per year. The run logic is shared (`hydrolog.statistics.threshold_runs`).
- **Skipping years with missing days in the second degree**: it would change the numbers of `stats characteristic`, which the mockup and its users already show; the years are named instead.
- **Classes of the duration curve from the floored lowest value** (as `hydrometrics water-level-zones`): edges such as 81–91 cm; the author's table used multiples of the width.
