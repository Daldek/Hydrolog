# 0017. Typical ranges: one table in Hydrolog, served in the document of one command

- Status: accepted
- Date: 2026-11-04
- Amends: [ADR-0015](0015-catalog-additions-for-the-gui.md) (the `outside_typical_range` notices: their bounds come
  from one table, a threshold without a published source is gone, and the area of a watershed and of three unit
  hydrographs is checked)
- Builds on: [ADR-0001](0001-catalog-english-and-operation-ids.md) (the catalog document `hydrolog-commands/1`, English
  with the Polish texts in `i18n.pl`), [ADR-0006](0006-mcp-server-conformance.md) (`hydrolog_commands_schema`, the
  discovery tool of agents)

## Context

The typical range of a formula or a model is the range of the data it was derived from, or the range its literature
recommends; outside it the formula still computes and Hydrolog warns (`outside_typical_range`, with `details.field`
since [ADR-0015](0015-catalog-additions-for-the-gui.md)). The ranges were written in several places that did not
agree:

- the library had constants per module (`time/concentration.py`, `runoff/*`, `statistics/high_flows.py`), several of
  them without a source: Kirpich's length of 0.001-80 km, the length and slope of the NRCS lag, Giandotti's length and
  elevation difference, the length and slope of FAA;
- the GUI's explanations (i) and notes kept their own copies, `{option, min, max, source}` in `labels/info/*.js`
  (plan [2026-11-02-hydrolog-gui.md](../plans/2026-11-02-hydrolog-gui.md), D16), some of them quoting the library's
  thresholds as „próg ostrzeżenia Hydrologu” and some with sources the library did not use (the areas of Kirpich's
  data, of the SCS unit hydrograph and of the Lutz method);
- the option descriptions of the catalog repeated the numbers in prose.

So the GUI could warn where the library did not, and an agent or a CLI user saw neither the GUI's ranges nor any source.
The author decided on 2026-11-04 that Hydrolog is the only source of the typical ranges and that each range names its
literature (the plan's erratum of that date, which supersedes D16's GUI-owned ranges).

## Decision

- **One table, `hydrolog._ranges.TYPICAL_RANGES`:** one `TypicalRange` per method and parameter with `minimum` and
  `maximum` (bounds included, `None` for none), `unit`, `source` and `source_pl`, `relative_to` (the result field the
  bounds are shares of: the time step is at most 0.25 of `uh_time_to_peak_min`) and `notice` (`outside_typical_range`,
  or `short_record` for the record of a flood frequency analysis). The formulas and models warn with its bounds and the
  option descriptions quote it (`catalog/groups/_typical.py`); no bound is written anywhere else. The module is a
  leaf, so the catalog reads it without the numerical libraries.
- **A range without a published source is not kept.** The thresholds above are gone, and so are the overland slope of
  Kerby-Kirpich and the lower bounds of Kerby's length and slope and of the FAA coefficient. The others come from the
  data or the literature of each method (Kirpich 1940, Mockus 1961, Giandotti 1934, FAA 1970, Kerby 1959, Roussel et
  al. 2005, Sorrell 2010, Snyder 1938, KZGW 2017, HEC-HMS, Hawkins et al. 1985, NEH 630); the CHANGELOG lists every
  change with its source. The area, an argument of Giandotti's formula only, is checked by
  `WatershedParameters.calculate_tc` against the data of Kirpich, NRCS, Kerby and Kerby-Kirpich (`details.field`
  `area_km2`); `uh scs`, `uh snyder` and `uh nash` with the Lutz options check theirs. One exception: no published
  range of a given Nash cascade was found, so n 1-10 and K 10-200 min stay with a source that says they are
  Hydrolog's own.
- **`typical_ranges`, a Hydrolog addition to the entry of a command** in `hydrolog-commands/1`, next to `one_of`. A
  command declares the ranges it checks (`Command.typical_ranges`, `RangeCheck(method, parameter, inputs, result)`,
  validated against the table at import). Each served entry has `method` and `parameter` (as `details.method` and
  `details.parameter` of the notice name them), `inputs` (the options of the command or the fields of its watershed
  the value comes from, first choice first), `result` (for a value of the result that is not an input: the record
  length `n_years`), `minimum` and `maximum` (`null` for none; shares of `relative_to` when it is given), `unit`,
  `relative_to`, `notice`, `source` and `i18n.pl.source`.
- **Only the document of one command carries them:** `commands schema --command` (`hydrolog_commands_schema` with
  `command`), `hydrolog <group> <command> --schema` and `hydrolog.catalog.command_schema`, which the GUI's
  `api/commands/{group}/{verb}` serves. A page of `commands schema`, of any `limit`, the document of a group
  (`hydrolog <group> --schema`) and that of the catalog (`hydrolog --schema`) leave them out. The choice is explicit,
  `catalog_document(commands, *, typical_ranges=False)` passed down to `command_entry`, and not inferred from the
  number of commands: a page of one command is still a page.
- **The budget is DOC-1.7's:** a default page at most 20,000 characters, a whole response at most 50,000. The default
  pages of `hydrolog_commands_list` (8,966 characters) and `hydrolog_commands_schema` (13,663) carry no ranges. The
  document of one command is one whole response; the largest are `report generate` (27,860 characters with its 27
  ranges) and `hydrograph generate` (27,145). A test holds every agent tool's document to 50,000.
- **Clients read the ranges and keep no numbers.** The GUI (its explanations, field warnings and notes) and agents
  take the bounds and the sources from `typical_ranges`, and the warning about a value from the notice
  `outside_typical_range` and its `details.field`.

## Consequences

- **Breaking:** values that warned no longer do and others now do. The documented Kirpich example (8.2 km at 0.023)
  has a slope notice, and a 45 km² watershed has an area notice for Kirpich, NRCS and Kerby. `uh scs` returns an
  `OperationOutput` with notices, and `hydrolog.runoff.generator.TIMESTEP_SHARE_OF_TP` is removed (the share is the
  range of `timestep_min`). The form of the notice and its `details` keys are unchanged.
- Changing a range is one line of the table with its source; the notices, the catalog, the descriptions and the GUI
  follow. The tests hold the published numbers, not the table's.
- An agent reading a page sees a range only in an option description; it asks for the command (`commands schema
  --command`, as the description of the tool says) to get the bounds and the sources.
- The documents of `report generate` and `hydrograph generate` are above 20,000 characters, as a whole response may
  be.

## Alternatives considered

- **Ranges in every page:** the default page of `hydrolog_commands_schema` would grow from 13,663 to 17,271 characters
  and the page with `uh nash`, `uh scs`, `uh snyder` and `hydrograph generate` from 39,226 to 52,495, over the 50,000
  of a whole response; every range added later would grow the pages again.
- **Compact entries:** without the sources, or with the 15 time of concentration ranges of a watershed referred to
  `tc watershed`, the document of `report generate` would still be 21,394 or 22,395 characters, over 20,000, and the
  GUI would lose the sources it shows, or need a second call.
- **A separate command for the ranges:** a new command, MCP tool and result schema that every client would call next
  to `commands schema`, although a range belongs to the command that checks it.
- **Ranges kept by the GUI (D16):** two copies drift, and an agent or the CLI never sees them.
