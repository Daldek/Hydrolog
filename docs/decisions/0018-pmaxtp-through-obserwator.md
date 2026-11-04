# 0018. PMAXTP through Obserwator: `precip pmaxtp`, the one command that uses the network

- Status: accepted
- Date: 2026-11-04
- Amends: [ADR-0005](0005-error-registry.md) (`ERROR_CODES` gains the registry code `source_unavailable`),
  [ADR-0014](0014-web-gui-enters-the-scope.md) (Hydrogram zlewni fetches the PMAXTP depth instead of asking for it;
  the plan [2026-11-02-hydrolog-gui.md](../plans/2026-11-02-hydrolog-gui.md), D15 and D18, has an erratum of this date)
- Builds on: [ADR-0006](0006-mcp-server-conformance.md) (the tool annotations, `openWorldHint` among them),
  [ADR-0015](0015-catalog-additions-for-the-gui.md) (the notice registry `NOTICES`)

## Context

PMAXTP is the atlas of maximum precipitation of IMGW-PIB: for a point of Poland, a table of design depths for 16
durations (5 min to 72 h) and 27 probabilities of exceedance (0.01 % to 99.9 %), by two methods, POT (peaks over a
threshold, which IMGW-PIB recommends) and AMP (annual maxima). It is the usual design rainfall of a Polish watershed,
and the first input of Hydrogram zlewni.

Hydrolog downloaded nothing: Kartograf and Obserwator supplied files, and a PMAXTP depth was a number the person
looked up elsewhere and typed (`--total-mm`; in the GUI the field „Wysokość opadu P” next to p and the duration, the
plan's D18: „Hydrolog downloads nothing; the depth is typed or comes with a hand-off”). So the person left the GUI to
read the atlas, a typed depth could belong to another point, probability or duration than the ones written beside
it, and nothing recorded where it came from. Obserwator, Nogat's data tool, already fetches PMAXTP tables
(`obserwator.fetch_pmaxtp`, the PMAXTP API of IMGW-PIB).

The author decided on 2026-11-04 that with PMAXTP the person gives the location, the probability and the duration,
and the depth is fetched from IMGW-PIB through Obserwator, never typed. This reverses „Hydrolog niczego nie pobiera”
(Hydrolog downloads nothing) for PMAXTP only.

## Decision

- **One command, `precip pmaxtp`** (`hydrolog_precip_pmaxtp`, `hydrolog.operations.precip_pmaxtp`, result
  `hydrolog-precip-pmaxtp/1`): `latitude` and `longitude` (WGS84, decimal degrees, the box of Poland 49-55 and
  14-24.5), `duration_min` (one of the 16), `probability_percent` (one of the 27) and `method` (`POT`, the default,
  or `AMP`) give `depth_mm`, with the point, the method, the duration, the probability and `attribution`. It is the
  only command that uses the network; every other command still computes offline on numbers and local files.
  The depth is the `total_mm` of `precip hietogram` and `hydrograph generate`; those commands do not fetch it.
- **Declared as such.** `Command.network` (default false) is true for this command alone; it is `effects.network`
  of `hydrolog-commands/1` and the `openWorldHint` of its MCP tool. The agent guides, the MCP instructions and the
  README say that only `precip pmaxtp` goes online.
- **An optional extra.** `pmaxtp` brings `obserwator>=3.0.0.dev0,<4`, repeated in `gui` and `all`. Obserwator is not
  tagged yet, so `[tool.uv.sources]` pins commit `1ee54573453473392f21e2c8bb34f76e4976e03f` of Nogat's release set
  candidate-1; the release replaces it with a tag. `hydrolog._pmaxtp` (the durations, the probabilities, the methods,
  the box, the attribution, the timeout) is a leaf module that the catalog reads, and Obserwator is imported only when
  the command runs: without it the command ends with `missing_dependency` (`details.extra` `pmaxtp`,
  `details.module` `obserwator`, hint `pip install "hydrolog[pmaxtp]"`).
- **Checked before any fetch.** A duration or probability the atlas lacks, or another method, is a
  `validation_error` (`details.reason` `choice`, `details.allowed`), and a point outside the box one of the catalog's
  bounds (`minimum`, `maximum`), before anything is sent.
- **What goes out.** Obserwator asks the PMAXTP API of IMGW-PIB for the table of the point (its coordinates and the
  method) and Hydrolog reads the cell of the duration and the probability. A request may take 20 s
  (`hydrolog._pmaxtp.TIMEOUT_S`), less than the 30 s of a run of the GUI, so the GUI's own timeout does not hide
  IMGW-PIB's. Nothing is cached or stored.
- **Errors.** Obserwator's errors become registry codes: a point inside the box but outside the atlas (at sea, near
  a border) is `validation_error` with `details.reason` `outside_pmaxtp` on `latitude` (or the coordinate Obserwator
  names); IMGW-PIB unreachable or too slow is `source_unavailable` (exit 5, `details.source` `imgw-pmaxtp` with
  Obserwator's `url`, `reason` and `status`; the hint offers `precip hietogram --total-mm`); an answer that cannot be
  read or lacks the cell is `data_error`. `source_unavailable` is a code of Nogat's registry that Hydrolog had not
  used; it joins `ERROR_CODES`, and Hydrolog still adds no code of its own.
- **Attribution.** The terms of IMGW-PIB (<https://danepubliczne.imgw.pl/regulations>) prescribe naming the source.
  The result carries it as `attribution`, „Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej
  – Państwowy Instytut Badawczy”, and every run adds the notice `pmaxtp_attribution` (level `info`, `details`
  `attribution` and `terms_url`), whose message points to the result's field, so the CLI prints the formula once.
- **The GUI.** Hydrogram zlewni, step 2 „Hietogram”, source PMAXTP: the fields „Szerokość geograficzna φ”
  (`pmaxtp_latitude`) and „Długość geograficzna λ” (`pmaxtp_longitude`), checked at once against the bounds of
  `precip pmaxtp`; p (all 27 values) and the duration (all 16); the method, POT by default, or AMP. Once the point,
  p and the duration are complete and valid, the page runs `precip pmaxtp` on a channel of its own,
  `hydrogram-pmaxtp`, debounced and separate from the runs of the hydrograph, and shows the depth read-only
  („Wysokość opadu P”, „PMAXTP IMGW-PIB, metoda POT”); `hydrograph generate` takes it as `total_mm`, and no
  hydrograph is computed until a depth is known. The fetched depth is kept with the inputs (`pmaxtp_fetched` in
  `hydrolog-gui/hydrogram/2`: the options it was fetched for, `latitude`, `longitude`, `duration_min`,
  `probability_percent` and `method`, with `depth_mm`), so a reload does not fetch again and a change of the point,
  p, the duration or the method fetches anew. A point outside the box stands on its field, one outside the atlas on
  the latitude („Punkt poza atlasem PMAXTP”), `source_unavailable` or a timeout on the depth's row, with „Pobierz
  ponownie”; step 2 shows the attribution. The browser never calls IMGW-PIB: the server runs the command.
- **The hand-off.** `provenance.rainfall` of a hand-off from Hydrogram zlewni is `{"source": "pmaxtp",
  "probability_percent", "duration_min", "latitude", "longitude", "method"}`. Reading one, the point comes from
  `provenance.rainfall`, else from `provenance.watershed` (Hydrograf's outlet). The payload's depth is kept without
  a fetch only when `provenance.rainfall` carries the point; with a point only in the watershed's provenance the page
  fetches the depth for it; with no point at all the rainfall opens as a design hyetograph with the payload's depth
  and duration.
- **Tests stay offline.** An autouse fixture of `tests/conftest.py` answers `obserwator.fetch_pmaxtp` with a table
  of IMGW-PIB recorded on 2026-11-04 (`tests/fixtures/pmaxtp_warszawa_pot.json`, Warsaw, POT), with the asked point
  and method, so Hydrolog's real code reads it; the browser tests route `api/run/precip/pmaxtp` to an envelope
  computed in the test process from the table at Kamiennik's outlet (`tests/fixtures/pmaxtp_kamiennik_pot.json`,
  51.01544, 15.88984, POT). One test, marked `live`, asks IMGW-PIB itself; the gate deselects it
  (`-m 'not live'`). The result schema is written by hand, because its example would need the network.

## Consequences

- `precip pmaxtp`, and Hydrogram zlewni under PMAXTP, need the network and IMGW-PIB: when either is down the command
  ends with `source_unavailable` and the GUI computes no hydrograph until the depth comes, or until the person picks
  another rainfall. Every other command, and the GUI's other sources of rainfall, work offline as before.
- IMGW-PIB may update the atlas, so the same point, p and duration can give another depth, and so another result,
  later. The guide's worked example (Kamiennik at Świerzawa, 51,01544 / 15,88984, p 1 %, 12 h, POT) gave 101,82 mm
  on 2026-11-04 (AMP 99,10 mm), so 56,39 m³/s at 6:20 h, 976 759 m³ and C 0,258 (AMC III 109,92 m³/s), where the
  typed 105 mm gave 60,21 m³/s, 1 046 213 m³, 0,268 and 115,23; the guide says the depth may change. A remembered
  depth (`pmaxtp_fetched`) stays until its inputs change.
- What goes out is stated in SECURITY.md and the README: the point's coordinates and the method, to the PMAXTP API
  of IMGW-PIB, through Obserwator, only when `precip pmaxtp` runs.
- The gate stays offline and deterministic; IMGW-PIB is checked only by the `live` test, on demand
  (`uv run pytest -m live`).
- Hydrolog depends on Obserwator again, optionally, and on its pre-release until it is tagged.

## Alternatives considered

- **Keep typing the depth:** the person leaves the page to read the atlas, a typed number can belong to another
  point, probability or duration than the ones written beside it, and nothing records its source; the author's
  requirement is that the depth is never typed.
- **Hydrolog calls IMGW-PIB's API itself:** a second client of the same API next to Obserwator's, with its own URL,
  answer format, errors and attribution to keep in step; Obserwator is the ecosystem's tool for IMGW-PIB data.
- **The browser fetches from IMGW-PIB directly:** the page's Content-Security-Policy is `'self'` (`connect-src`
  would have to name IMGW-PIB), the API's CORS headers are not Hydrolog's to rely on, and the depth would reach
  `hydrograph generate` without the server's validation, error mapping and attribution; CLI, MCP and Python users
  would get nothing.
- **Bundle the atlas:** the tables of every grid point of Poland are a large dataset under IMGW-PIB's terms, which
  IMGW-PIB updates; a copy in the wheel would go stale silently, and Hydrolog ships no dataset except the TR-55
  table.
