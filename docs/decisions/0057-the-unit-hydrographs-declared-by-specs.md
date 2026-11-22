# 0057. The unit hydrographs declared by specs: NEH's table as data, C = 2.08 per cm, 20 mi²

- Status: accepted (the SCS unit hydrograph and the convolution; Snyder, Clark and the generator follow)
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (specs, Nogat CMP), [ADR-0051](0051-the-tr55-table-as-data-no-invented-fair-rows.md)
  (a published table as data, transcribed twice), the literature research of the unit hydrographs of 2026-11-18
  (`unit-hydrographs.md`, its reference cases and verdicts)

## Context

The SCS dimensionless unit hydrograph kept table 16-1 of NEH 630 chapter 16 as a NumPy literal in
`runoff/unit_hydrograph.py`, its peak as `0.208 A / tp` with no source of the constant, its area range as 52 km²
credited to Sorrell (2010), and its sources as TR-55, which contains neither the table nor tlag = 0.6 tc. Its
constructor and `convolve_discrete` checked their inputs by hand, with messages but no standard `details.reason`. The
standard asks for one spec per Tier A formula, a published table as data transcribed twice (CMP-2.5), constants
confirmed by a primary or two secondary sources (CMP-2.4) and conversions through the units table (CMP-4.3).

## Decision

1. **The table is data.** `src/hydrolog/_data/tables/neh630_duh.csv` holds the 33 time and discharge ratios of NEH 630
   table 16-1 (p. 16-4); the spec `scs` records its SHA-256. It is accepted because the transcription of the PDF's text
   layer (`tests/oracles/transcribe_neh630_duh.py`) and the table typed for Hydrolog 0.8.1 agree with it row by row;
   NEH-4 (1972) prints the same ratios. `SCS_DIMENSIONLESS_UH` is the read-only array read from the file.
2. **C = 2.08 per cm, not 484 converted.** The peak is qp = C·A/Tp with C = 2.08 m³/s per km² cm/h (HEC-HMS Technical
   Reference Manual 2000, eq. 36; Chow et al. 1988 after Rajagopalan's notes, p. 79: „2.08 (483.4 English units)”),
   per mm by the exact 10 mm/cm of the units table. It is NEH's peak rate factor 483.2, 0.16 % below the 484 of the
   triangle (NEH 630 eq. 16A-6); NEH itself gives the curvilinear table the factor 483.4 (p. 16A-2), and with 2.08 the
   continuous table holds 1.00036 mm. The numbers of 0.8.1 stay (0.208 differed from 2.08 × 0.1 in the last bit only).
3. **The area range is NEH's.** No subarea above 20 square miles (NEH 630 p. 16-4): 51.8 km², served as the
   applicability range of `scs.area_km2` instead of 52 km² from Sorrell (2010). The second condition of NEH (the largest
   subarea at most 10 times the smallest) is an assumption of the spec, not a check.
4. **What the computation cannot hold is a precondition.** `steps_representable` (scs) refuses a step whose sub-step,
   peak or count of sub-steps float64 cannot hold, or whose grid has more than a million ordinates (the bound of a
   routed hydrograph, `hydrolog.routing.reach.MAX_ORDINATES`); `length_bounded` (uh_convolution) refuses a hydrograph of
   more than a million ordinates. The count of sub-steps is a closed form corrected at most twice, so no loop depends
   on the rounding of a huge count.
5. **The peaks say what they are.** The SCS qp is the formula's value for the duration of the step: up to 1.7 % above
   the largest ordinate when Tp falls between two step times, and well above it when sub-steps act (notice
   `uh_substeps`). The Snyder peak is its largest ordinate; only its time tpR is the formula's. The documents of
   `uh scs` and `hydrograph generate` say so; whether the SCS result should report the largest ordinate instead is the
   author's question.
6. **The published misprint is recorded, not followed.** NEH 630 figure 16-2 prints qp = 988 ft³/s for area C2 (2.0 mi²,
   Tc 1.5 h, ΔD 0.2 h), where its eq. 16A-6 gives 968, as NEH-4 (1972) example 4 computes for the same watershed: the
   case is a `discrepancy` with that cause (CMP-5.2).
7. **The family shares its declarations.** `hydrolog.runoff._uh_specs` holds the sources (NEH 630 ch. 16, NEH-4,
   HEC-HMS 2000, KZGW 2017, Chow's notes), the physical and typical ranges of the area, tc and the step (typical: the
   hand-offs of Hydrograf; the step 5–60 min also from KZGW's examples) and the bound of the ordinates.

## Consequences

- `SCSUnitHydrograph(...)` and `convolve_discrete` refuse invalid inputs with `validation_error` and the standard's
  `details.reason`; the constructor checks nothing, the methods do. Breaking for callers that matched the old messages.
- The notice `outside_typical_range` of `scs.area_km2` starts above 51.8 km².
- `hydrograph generate` and `uh scs` carry `formula_versions` `scs` (and `uh_convolution` for the generator).
- Snyder, Clark and the generator's volume conservation get their specs on the same branch, with the same shared
  declarations (ADR-0058 if their decisions need one).

## Alternatives considered

- **PRF 484 converted exactly (0.20833):** the triangle's factor, 0.16 % above the curvilinear table's own; it would
  change every SCS peak and hold 1.0019 mm instead of 1.0004.
- **Keep 52 km²:** a rounding of 20 mi² credited to a secondary source; the primary says 20 square miles.
- **A sub-step count without bound:** it loops forever once the count passes 2**53, where adding one no longer changes
  it.
