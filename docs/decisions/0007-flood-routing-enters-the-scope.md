# 0007. Lumped hydrologic flood routing enters the scope of Hydrolog

- Status: accepted
- Date: 2026-10-24

## Context

[SCOPE.md](../SCOPE.md) listed channel flow routing and retention reservoir modelling as
out of scope (§2.2) and "no routing: hydrograph for the closing cross-section" as a
limitation (§5.1); [PRD.md](../PRD.md) said "No flow routing". The research report
[2026-10-24-long-term-and-routing.md](../plans/2026-10-24-long-term-and-routing.md)
(decision D1) shows that routing stays inside the "hydrological calculations" of the
tool when it is lumped and hydrologic (storage and translation), and that it has what
the other candidate directions lack: a closed method set, documented numerical rules and
public-domain reference data (NRCS NEH-630 chapter 17). Hydraulics (levels, inundation,
backwater, structures) stays with Hydraulik, HEC-RAS and IMGW HD; Hydrograf supplies the
network and Hydraulik takes hydrographs as forcing, so a routing layer in Hydrolog sits
between them.

The author delegated the decisions D1, D9, D10, D13 and D14 of the report to the
coordinating session on 2026-10-24. The branches that implement them are not merged,
tagged or pushed until the author has reviewed them.

## Decision

- **In scope:** lumped hydrologic routing of discharge hydrographs: lag, Muskingum with
  automatic sub-reaches, Muskingum-Cunge with constant coefficients (NRCS form), a
  cascade of linear reservoirs (Kalinin-Milyukov, Nash), level-pool reservoir routing
  (storage-indication, modified Puls) and the composition of these over a river network
  (a directed acyclic graph).
- **Non-goals:** water levels, inundation extents, backwater, bridges and culverts, dam
  breaks and 2-D flow (hydraulics); reservoir operation (gates, release rules);
  Saint-Venant solvers (kinematic, diffusive or dynamic wave); real-time forecasting
  and data assimilation. Continuous (long-term) modelling is not part of this decision.
- **Names (D13):** command group `route` (`route lag`, `route muskingum`,
  `route muskingum-cunge`, `route cascade`, `route level-pool`, `route network`), Python
  package `hydrolog.routing`, result schemas `hydrolog-route-<verb>/1`. One tool per
  command (`hydrolog_route_lag`...); the `core` family is unchanged.
- **Location of the report (D14):** DEV-17.4 says `docs/research/` is not used for new
  work, so the report moved to `docs/plans/` (a rename).
- **Delivery:** one branch per model, each started from the previous one
  (`feature/routing-core`, `-muskingum`, `-muskingum-cunge`, `-cascade`, `-level-pool`,
  `-network`); the plan is [2026-10-24-flood-routing.md](../plans/2026-10-24-flood-routing.md).

## Consequences

- SCOPE.md (§1.2, §2.1.11, §2.2, §3.1, §5.1), PRD.md, INTEGRATION.md, README.md and the
  guide templates no longer list channel routing and reservoirs as out of scope; they say
  where hydrologic routing ends.
- The Hydrograf scope text ("no routing in the channel") and the hydrograph file contract
  with Hydraulik need `request` issues in those repositories (DEV-17.5); this change does
  not make them.
- The numerical conventions are in [ADR-0008](0008-routing-conventions.md); the effect
  on the agent guide is in [ADR-0009](0009-compact-index-line-for-large-groups.md).
