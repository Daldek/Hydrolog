# 0059. The meteorological indices declared by specs: formulas of a day, a sum or a class beside the series

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs, Nogat's computation standard,
  CMP §1–§9), the plan of the standard (Nogat `docs/plans/2026-11-18-computation-standard.md`, step 5: SPI and the
  meteorological indices after the SCS-CN, tc, unit hydrograph and flood frequency families), the research
  `meteo-indices` of 2026-11-18 (its reference cases and open questions) and
  [ADR-0044](0044-normals-spells-frost-days-and-the-hydrothermal-season.md)
- Amends: [ADR-0032](0032-meteorological-statistics-of-a-station-the-group-meteo.md) (point 5: the classes of a year
  and the fit of the SPI)

## Context

The `meteo` group computes its indices from a daily series laid on the calendar (`hydrolog.statistics._climate`): the
WMO-No. 1203 rules of missing days, sums, normals and years are conventions of a calendar (Tier B of CMP-1.1), while
the indices, distribution fits and classifications are Tier A formulas. A spec of the reference module declares a
function whose inputs are numbers, arrays of numbers or choices, named with their units (CMP-2.1, CMP-4.3); the series
functions take dates, flags and years and return documents of months, years and periods, so their own signatures cannot
be specs.

Besides the conventions the research asked to state, the specs must settle one reading of a source: Kaczorowska's
classes are ranges of whole percents while the code rounded the percentage with Python's `round`, a half to even, so
74.5 % was very dry and 75.5 % dry, 110.5 % normal and 111.5 % wet (the classes were no longer intervals).

## Decision

1. **A spec declares the formula of a day, a sum or a class; the series function computes through it.** Each Tier A
   formula of the group is a function of its own with the inputs of its spec (`fit_gamma(sums_mm)`,
   `spi_values(sums_mm, alpha, beta_mm, zero_probability)`, `year_precipitation_class(percent_of_normal)`, …), and the
   series function (`standardized_precipitation_index`, …) calls it for each month, year or day it reports, so every
   result records the `formula_version` of the formulas it used (ADR-0050, point 5). What the series function does
   around them (the calendar, the WMO-No. 1203 rules, the reference period) is declared in each module's `TIER_B`
   table. A value the spec refuses for a precondition (fewer than three positive sums, sums all equal) leaves the
   series function's field `null` with its notice, as before; any other refusal is an error of the call.
2. **Kaczorowska's classes take the percentage rounded to a whole percent, a half up.** Kaczorowska (1962, p. 72) and
   IMGW-PIB's yearbooks (Rocznik Meteorologiczny 2022, Tab. 5 and 9) give ranges of whole percents and print whole
   percents; a percentage counts in the class of its rounding, a half up, so each class is an interval of the
   percentage: [49.5, 74.5) very dry, [74.5, 89.5) dry, [89.5, 110.5) normal and so on. Only a percentage of exactly a
   half changes class (74.5, 110.5, 150.5 %). The reading of Łabędzki and Bąk (2004), decimal bounds 75.0–89.9, is
   recorded on the spec as another convention.
3. **The SPI's numerics do not lose digits where the formula does not.** Thom's A is computed as the mean of
   d − ln(1 + d) with d = x / x̄ − 1, which equals ln x̄ − mean(ln x) without its cancellation (sums equal to a few
   digits lose every digit of A the other way; doubling the sums leaves A exact); the zero probability is m / n
   itself, not 1 − (n − m) / n; the SPI above the median is −Φ⁻¹((1 − q) Q(α, x/β)) with Q the upper incomplete gamma
   function, and both incomplete gamma functions are held in [0, 1], which scipy leaves at a subnormal shape. On
   Warszawa-Okęcie 1991–2020 the SPI of scales 1 to 48 changes by at most 6·10⁻¹³ and every class stays.
4. **The inputs are refused as the specs say.** `fit_gamma` refuses a negative or missing sum and, for its
   preconditions, sums with fewer than three positive values or positive values all equal (it returned `None`);
   `spi_values` refuses a negative sum (taken as 0) and keeps a missing one missing; the classes refuse NaN and `None`
   (they returned `None`), which the series functions no longer pass. `precipitation_spells` refuses a negative
   precipitation, which it counted as a dry day, as the other functions of daily precipitation do; their refusal
   names `details.reason` `outside_physical_range` and the day (`details.index`).

## Consequences

- `meteo spi` gives the same numbers but for the classes of years at exactly a half percent; its envelope carries
  `formula_versions` `spi_gamma_fit`, `spi`, `kaczorowska_class` and `month_precipitation_class`.
- `meteo spells` gives the same spells and carries `formula_versions` `spell_lengths` (the length of the spell ending
  on each day, from which `precipitation_spells` builds its spells); the year a spell counts in (ADR-0044) and the
  yearly summaries are its Tier B.
- Breaking for library callers: `fit_gamma(sums_mm)` returns `(alpha, beta_mm, zero_probability)` and raises
  `InvalidParameterError` (`precondition_failed`) where it returned `None`; `spi_values` takes `beta_mm`;
  `year_precipitation_class` and `month_precipitation_class` take `percent_of_normal`, a number.
- `docs/FORMULAS.md` lists the specs with their sources, ranges and reference cases; the frozen output of
  climate_indices 3.2.0 on Warszawa-Okęcie 1991–2020 (`tests/oracles/spi_climate_indices_warszawa.csv`) checks the
  whole pipeline of the SPI.

## Alternatives considered

- **Specs on the series functions:** their dates, flags and years are not inputs a spec can declare, and their outputs
  are documents, not numbers; the generated tests could not reach the formula.
- **Keeping Python's rounding and stating it:** it makes the classes depend on the parity of the whole percent, which
  no source does.
- **The decimal bounds of Łabędzki and Bąk:** a reading of one later paper, not of the source or of IMGW-PIB's
  yearbooks, which print whole percents.
