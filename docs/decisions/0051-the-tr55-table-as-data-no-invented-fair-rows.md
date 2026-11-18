# 0051. The TR-55 curve number table as data: no invented `fair` rows, no silent condition

- Status: accepted
- Date: 2026-11-18
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (specs, Nogat CMP-2.5: a published table is a data file
  transcribed twice), the audit of the formulas of 2026-11-18 (TRIAGE T12, research `scs-cn.md` §4) and the
  coordinator's decision of 2026-11-18 on the default condition

## Context

Hydrolog's curve numbers were a dictionary in `runoff/cn_lookup.py`. The audit compared its 152 cells with TR-55
(USDA-SCS 1986, tables 2-2a to 2-2d) and NEH 630-9: 133 match; 8 cells, row crops and small grain in `fair`
condition, have no source (TR-55 table 2-2b gives these straight-row covers in poor and good condition only; the
cells are the mean of the two rows, rounded down), and `fair` was what `get_cn` and `cn lookup` used when no
condition was given; the `herbaceous` cells are TR-55's pasture values of table 2-2c, which footnote 1 of table 2-2d
prescribes for range in humid regions, though no text said so (table 2-2d's own herbaceous row is for arid and
semiarid rangelands). CMP-2.5 asks for a published table as a data file with its source, transcribed twice
independently and compared.

## Decision

1. **The table is data.** `src/hydrolog/_data/tables/tr55_cn.csv` holds every row with its source (table and page of
   TR-55, the footnote for `herbaceous`, NEH 630-9 p. 9-1 for water at 98). The spec `tr55_cn`
   (`table_curve_number(hsg, land_cover, condition)`, condition `none` for a cover of one row) records its SHA-256;
   a lookup of a row the table lacks fails its precondition (`precondition_failed`).
2. **Two transcriptions.** `tests/oracles/tr55_cn_text_layer.csv`, read from the text layer of the TR-55 PDF by
   `tests/oracles/transcribe_tr55_cn.py`, and `tests/oracles/tr55_cn_hydrolog_0_8_1.csv`, the table typed for 0.8.1,
   agree with the data file on every cell but the 8 unsourced ones; `tests/unit/test_formulas_cn_table.py` compares
   them, and 144 reference cases check the lookup cell by cell.
3. **No invented rows.** Row crops and small grain have `poor` and `good` only.
4. **No silent condition where TR-55 has no fair row.** `get_cn` and `cn lookup` without a condition still take `fair`
   for a cover that has it (with the notice `condition_defaulted`), but refuse row crops and small grain without a
   condition (`validation_error`, `details.reason` `required`, `details.option` `condition`, `details.allowed` the
   cover's conditions) and with `fair` (`details.reason` `choice`, the same `details.allowed`). The person chooses
   between poor and good.
5. **`herbaceous` stays, explained.** Its meaning in the catalog states the substitution of footnote 1 of table 2-2d.

## Consequences

- `get_cn("B", "row_crops")` and `cn lookup --land-cover row_crops` without a condition fail where they returned 79 (an
  unsourced value); `cn list` and `cn range` give the two rows of TR-55.
- Hydrograf maps its categories to sourced rows only (small grain *good*, ADR-0075 of Hydrograf) and passes the
  condition: no change for it. Hydraulik reads its own `classes.csv`.
- A future row (TR-55's 1/2-acre and 1-acre residential districts, newly graded areas) is a line of the data file and
  of both transcriptions, and a new SHA-256 in the spec.

## Alternatives considered

- **Keep the interpolated `fair` rows labelled as such:** values of no source, and the default would still pick one.
- **Default to `good` where `fair` is missing (Hydrograf's choice for small grain):** a silent choice between two
  published rows that differ by up to 9 CN; the person makes it.
- **Use TR-55 table 2-2d for `herbaceous`:** that row is for arid and semiarid rangelands; Polish catchments are humid.
