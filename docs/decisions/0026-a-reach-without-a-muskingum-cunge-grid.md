# 0026. A reach without a Muskingum-Cunge grid: linear reservoirs with a warning, not a refusal

- Status: accepted
- Date: 2026-11-11
- Amends: [ADR-0008](0008-routing-conventions.md) (stability: a Muskingum-Cunge reach for which no division of the
  reach and of the time step into at most 100 parts keeps the weights non-negative is routed as linear reservoirs with
  the warning `diffusion_dominated` instead of being refused with `unstable_timestep`)
- Builds on: the author's report of 2026-11-11 (Hydrograf's networks of lowland reaches cannot be routed in Sieć), the
  coordinator's decision of the same day (the fallback, and the number of reservoirs matched to the first two moments
  of the diffusion wave) and [ADR-0015](0015-catalog-additions-for-the-gui.md) (the notices of the routing models
  carry the text of their emitter)

## Context

Muskingum-Cunge (`MuskingumCungeReach`, NEH-630 chapter 17) routes a reach of length `L` on equal distance steps
`dx` with `K = dx / c` and `X = (1 - D / dx) / 2`, where `D = Q / (T S0 c)` is the diffusion length at the reference
discharge. The weights of a step are non-negative only when `|c dt - D| <= dx <= c dt + D`. The planner takes the
NRCS number of steps or the nearest one inside that window and, when no whole number fits, divides the time step into
2 to 100 sub-steps; NEH-630's rule of at least 10 steps on the rise of the inflow divides a long step first. Sub-steps
only shorten the step, so when the diffusion length is long against the distance `c dt` that the wave travels in a
step and lies far from every whole fraction `L / n` of the reach, no division helps, and ADR-0008 refused such a reach
(`unstable_timestep`, "a short, flat reach, which is storage").

The author's report: the network of the Nysa Szalona above point A that Hydrograf's kaczawa2 instance delineated
(18 subcatchments, 9 reaches; the fixture `tests/fixtures/handoff_hydrograf_network_nysa_szalona.json`), with a
60 mm rain in a 120 min block and the default 5 min step, could not be routed:

- with Manning's n 0.05 and a 5 m bottom, R2 (7,700.6 m at 2.78 per mille) was refused: `c` = 1.93 m/s and `D` =
  6,740 m, so one step needs `c dt >= L - D` = 961 m, the wave travels 578 m in 5 min, and every other division is
  farther from `D`. A step of 8.3 to 15.5 min (the rise rule's limit) would have routed R2, but at 10 min R4
  (5,336.5 m, `D` = 9,375 m) needs a step of at least 40 min against the rule's 32 min: no step routes the network;
- with n 0.035 and a 10 m bottom, R5 (7.1 m, `D` = 365 m) was refused: its steps with a window lie between 51.7 and
  53.8 s, and no division of 5 min lands there;
- a 490 m reach of an earlier network (`c` = 3.04 m/s, `D` = 9,028 m) was refused at every step from 1 to 60 min.

The GUI's words of the refusal (fix `caf617c`) said that no time step could help, which was wrong for R2, and offered
a lag or a level-pool storage in its place.

## Options considered

1. **Keep the refusal and name the steps that would help.** R2's steps exist, but at them another reach of the same
   network has none: the network still cannot be routed, and each reach would have to be replaced by hand.
2. **A finer scheme for such a reach** (Crank-Nicolson of the diffusion wave, or Muskingum with `X` set to 0 on the
   grid of the run). The first is a new solver with its own boundary conditions inside one routing method; the second
   keeps a window (`dt <= 2 K / n`) and refuses again on short reaches.
3. **A lag of the travel time `L / c`** (the GUI's one-click change): no attenuation at all on a reach whose physics is
   mostly diffusion.
4. **Linear reservoirs with the exact kernel of the cascade** (chosen): the Muskingum scheme with `X = 0` in the limit
   of an exact integration, which has no window, takes any step, keeps every weight non-negative and the volume, and is
   already in the library (`CascadeReach`, ADR-0008: "a scheme with an exact kernel has no window").

## Decision

1. **Where.** Only where the planner finds no grid (`_grid` returns none): every reach that a grid routes is routed
   bit for bit as before. On 6,000 random reaches (length 3 m to 63 km, slope 1e-4 to 0.03, both groups of hydraulics,
   steps of 1 to 60 min, extensions and initial outflows) 3,294 gave the same outflow, parameters, notices, storage and
   balance as before to the last bit, the 2,706 that were refused are now routed, and nothing else changed. The refusal
   of a grid that would need more than a million ordinates stays (`unstable_timestep`).
2. **How.** `n` equal linear reservoirs of `K = L / (n c)` with `n = L / D` rounded half up, at least 1, through the
   exact kernel of `CascadeReach` (the incomplete gamma function): every reservoir starts with the initial outflow, the
   storage follows from continuity. The diffusion wave of the reach has the mean travel time `L / c` and the variance
   `D L / c^2`; `n` reservoirs have `n K` and `n K^2`, so `K` keeps the travel time and `n` matches the variance as
   nearly as a whole number can (`n` = 1 whenever `D > L / 1.5`). No sub-step is taken: the rise rule of NEH-630 is a
   rule of the grid, and the kernel is exact for the inflow drawn as straight lines between the ordinates.
3. **What it says.** The notice `diffusion_dominated` (level `warning`, the emitter's own English text like every
   routing notice, ADR-0015) gives the length, the step, the celerity, the diffusion length (and, when `D > L`, the
   negative `X = (1 - D / L) / 2` of one step over the reach), `n` and `K`, and that the attenuation is approximate.
   `route network` starts it with the node's id and gives it `details.node_id`.
4. **Its parameters.** The run's `parameters` are the hydraulics of the reach (`length_km`, `slope_m_per_m`,
   `reference_discharge_m3s`, `celerity_m_per_s`, `top_width_m`), `diffusion_length_m`, `scheme` `linear_reservoir`
   and the options of `route cascade` that reproduce the run, `n` and `k_min` (one reservoir), with `lag_min` (`n K =
   L / c`). The parameters of a grid are unchanged and have no `scheme`. `ReachRun.parameters`,
   `RoutingResult.parameters` and `RouteResult.parameters` are typed `dict[str, ParameterValue]`; the result schemas
   do not change (`parameters` is an open object).
5. **The GUI (Sieć).** A reach without a grid is no error: the network computes, the reach chosen in „Wyniki” shows
   „Odcinek R2 trasowano jako zbiornik liniowy o K = … min, bo …” (by its diffusion length against its length, with
   both, the celerity and the step) and its parameters „Schemat obliczeń: zbiorniki liniowe”, and the notices name the
   node. The words of `unstable_timestep` are now: a step too short for the sub-reaches given to Muskingum, with the
   steps on which they fit (the refusal's details gain `minimum_timestep_min` and `maximum_timestep_min`, `2KX / N`
   and `2K(1 - X) / N`, and its hint the same range); a step that would need too many ordinates; otherwise a step too
   long. The one-click changes of a refused reach (a typed lag, a level-pool storage) stay for those refusals; the lag
   of the travel time, which only the refusal of a reach without a grid gave, is gone.

## The approximation

The reference is the linear diffusion wave `dQ/dt + c dQ/dx = (c D / 2) d2Q/dx2` on a semi-infinite channel with the
inflow at `x = 0`, read at `x = L`: Hayami's response, the inverse Gaussian of mean `L / c` and shape `L^2 / (c D)`,
applied exactly to the inflow drawn as straight lines between the ordinates, and checked by Crank-Nicolson on a grid of
5 to 40 m and 5 s reaching 12 diffusion lengths below the reach (largest difference 4.7e-5, 3.9e-6 and 2.9e-4 m3/s in
the three cases). The inflow is the one of R2 above (n 0.05, 5 m bottom): a peak of 180.51 m3/s at 270 min, 5 min
step, 2.2323 hm3 over 116.5 h; the 490 m reach and the reach of `L / D` = 3.3 (R2's hydraulics on 22.24 km) take
the same inflow. Peak, time to peak and volume on the 5 min ordinates (the volume over the 116.5 h):

| Reach | `L` [m] | `c` [m/s] | `D` [m] | `L / D` | Reference peak [m3/s] at [min] | Fallback | Fallback peak [m3/s] at [min] | Peak error |
|---|---|---|---|---|---|---|---|---|
| R2 | 7,700.6 | 1.928 | 6,739.8 | 1.14 | 151.18 at 325 | `n` = 1, `K` = 66.56 min | 143.74 at 325 | -4.9 % |
| the 490 m reach | 490 | 3.04 | 9,028 | 0.054 | 179.08 at 270 | `n` = 1, `K` = 2.686 min | 180.23 at 270 | +0.6 % |
| `L / D` = 3.3 | 22,241.4 | 1.928 | 6,739.8 | 3.30 | 117.03 at 435 | `n` = 3, `K` = 64.08 min | 107.91 at 440 | -7.8 % (5 min late) |
| the same, one reservoir | 22,241.4 | 1.928 | 6,739.8 | 3.30 | 117.03 at 435 | `n` = 1, `K` = 192.2 min | 91.95 at 365 | -21.4 % (70 min early) |

The volume of every fallback equals the reference's to 0.001 %. One reservoir over-attenuates where the reach is
longer than its diffusion length (variance `L^2 / c^2` against `D L / c^2`, R2) and under-attenuates where it is far
shorter (the 490 m reach, where both responses are short against the rise of the flood); `n = L / D` keeps a long
reach from the large error and the early peak of one reservoir. The cascade with the unrounded `n = L / D` (the
moments exactly) gives -3.7 %, -0.2 % and -5.8 %: what remains is the shape, a gamma density against an inverse
Gaussian of the same mean and variance.

## Consequences

- The author's network routes at the 5 min step: with n 0.05 and a 5 m bottom the outlet's peak is 239.85 m3/s at
  445 min (R2, R4 and R5 as one reservoir each, R1, R3 and R6 to R9 on grids); with n 0.035 and a 10 m bottom
  392.03 m3/s at 345 min (R5 as one reservoir); with n 0.035 and a 20 m bottom, where every reach has a grid, 425.25
  m3/s as before.
- A result can now hold a reach routed approximately; the warning says so, and a client reads it by the code and by
  `parameters.scheme` (rule 7 of the agent guide: read `notices`).
- A short or flat reach no longer needs the lag or the storage that the GUI offered: the network computes with the
  reach as storage, which is what ADR-0008's refusal advised.
- `tests/unit/test_routing_cunge.py` holds the rule on 300 random reaches against a brute-force search of every grid,
  the moments of the reservoirs, `n`, the balance and the outflow; the e2e test routes the author's hand-off in Sieć.
