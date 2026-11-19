# 0044. Multi-month normals from monthly normals, spells in the year they end, frost and freeze-thaw days, and the hydrothermal season of April to September

- Status: accepted
- Date: 2026-11-18
- Builds on: the audit of the formulas of 2026-11-18 (Nogat CMP-9.1, TRIAGE item T33; research `meteo-indices`,
  sections 3, 12, 14, 15 and 24, and its reference cases), the coordinator's direction of 2026-11-18 (breaking
  changes of results allowed in 0.9.0, each stated in the CHANGELOG)
- Amends: [ADR-0032](0032-meteorological-statistics-of-a-station-the-group-meteo.md) (its points 3, 4, 6 and 8:
  the normals of `sums`, the year of a spell, the days of `meteo temperature` and the season of `meteo
  hydrothermal`) and [ADR-0033](0033-review-of-the-station-analyses.md) (its point 4: the annual and seasonal normals
  of a reference period)

## Context

The audit compared the `meteo` group with the sources it cites and found four places where the code and its texts
part from them.

1. **Multi-month normals.** The annual normal of `meteo precipitation` (`sums`), `meteo spi` and `meteo temperature`
   (`means`), and the half-year and season normals of `sums`, were the mean of the multi-month values of the years
   that had all their months, under the 80 % rule. WMO-No. 1203 (2017), 4.3.3, says the opposite: the normal of a
   sum or count over several months is the sum of the monthly normals, of a mean their mean, "annual normals should be
   calculated from the monthly normals, and not from the individual annual values"; the two agree when no month is
   missing. With one missing day in a different month of each of 7 of 30 years every monthly normal exists, but only
   23 years have an annual sum: Hydrolog gave no annual normal (and no % of it, no Kaczorowska class), WMO 767.95 mm.
   The notice `normal_not_computed` credited the old rule to WMO-No. 1203.
2. **Spells over 1 January.** `meteo spells` credited a spell to the year it starts and called the yearly longest
   spell CDD or CWD of the ETCCDI. The ETCCDI's software (fclimdex; climdex.pcic, whose `spells.can.span.years = TRUE`
   is "the default for fclimdex") and ECA&D (ATBD v11, 2021, p. 20: "a spell can continue into the next year and is
   counted against the year in which the spell ends") credit it whole to the year it ends; the literal ETCCDI text cuts
   it at the year's end. At Warszawa-Okęcie 1966–2020 the start-year CDD differed from ECA&D/climdex in 8 years, by up
   to 34 days (1996: 59 instead of 25).
3. **„Dni przymrozkowe”.** The GUI labelled FD (Tmin < 0 °C) „Dni przymrozkowe”. Polish usage has two meanings: the
   *Atlas klimatu Polski* (2005) and KLIMADA 2.0 call Tmin < 0 °C „dni przymrozkowe”, but the *Słownik
   meteorologiczny* (2003, as quoted by Kossowska-Cezak 2014, p. 14), IMGW-PIB Agrometeo and IMGW-PIB's normals
   1991–2020 (product PRZYMROZKI, „Liczba dni przymrozkowych (TMAX>0 & TMIN<0)”) mean Tmin < 0 °C and Tmax > 0 °C.
   At Warszawa-Okęcie 1991–2020 the GUI showed 97.9 days where IMGW-PIB's normals print 64.0 under the same name.
4. **The hydrothermal season.** The season coefficient summed every day of the calendar year with Tmean > 10 °C and
   cited Selyaninov (1928) and Miś (2026). Miś (eq. 4) sums the days above 10 °C within April–September; the classical
   Russian definition sums every day between the stable spring and autumn transitions through 10 °C. The code matched
   neither: at Warszawa 1991–2020 the class differed from Miś's in 3 years and from the classical period in 9.

The degree days were right but described loosely: Eurostat's daily mean is (Tmin + Tmax) / 2 (Directive (EU)
2015/1127), its English "base temperature" is the 15 °C threshold, and the season (the whole year) was not stated.

## Decision

1. **Multi-month normals by WMO-No. 1203, 4.3.3.** A monthly normal keeps the 80 % rule of 4.4.2. The annual normal of
   precipitation (`sums`, `meteo spi`) and the half-year and season normals of `sums` are the sums of the normals of
   their months; the annual normal of Tmean (`means`) is their unweighted mean (4.3.3, footnote 1); each is `null` when
   one of its monthly normals is. `normal_years` is the fewest years with a value among the twelve months, so the
   annual normal exists exactly when `normal_years` reaches 80 % of the reference period; `normal_not_computed` keeps
   its details and says so. The monthly normals are not rounded to 0.1 before they are summed (WMO's 4.7 recommends
   it for exchanged products; the difference stays below the printed unit). Counts have no normals in Hydrolog, so the
   February rule of 4.3.2 c (× 28.25) does not arise.
2. **A spell counts whole in the year it ends**, as the ETCCDI's software and ECA&D do; `spells[].year` is the year of
   its last day. A complete year that lies wholly inside a longer spell has no longest spell (`max_duration_days`
   `null`), as in climdex.pcic. The yearly summaries still need every day of their year.
3. **FD and the freeze-thaw days side by side.** `frost_days` stays FD of the ETCCDI (Tmin < `frost_tmin_c`), named in
   Polish „dni z przymrozkiem”; the new `freeze_thaw_days` (months, years, period) counts the days with Tmin <
   `frost_tmin_c` and Tmax > `ice_tmax_c` (both 0 °C by default), the „dni przymrozkowe” of the *Słownik* and of
   IMGW-PIB, reproducing IMGW-PIB's 64.0 days at Warszawa. No new option: the two existing thresholds bound the
   freeze-thaw day, so with any thresholds FD = freeze-thaw + ice days + the days with Tmax exactly at the ice
   threshold. The GUI labels say which is which; the strict signs (IMGW-PIB's yearbooks count Tmin ≤ 0 and Tmax ≥ 25
   or 30 °C) are stated in the guide and the docs.
4. **The hydrothermal season is the days of April–September with Tmean > 10 °C** (Miś, 2026, eq. 4; Chmist-Sikorska,
   Kępińska-Kasprzak and Struzik, 2022), and needs both values on every day of April–September (no longer of the whole
   year). The classes stay those of Skowera and Puła (2004); the texts name the season and its source, and say that the
   classical stable-transition season is not implemented.
5. **Degree days unchanged, described.** GDD (Wypych et al., 2017, eq. 1) and HDD (Eurostat; Directive (EU)
   2015/1127) are summed over every day of the year of `year_type`; the docs state that the Directive's Tm is (Tmin +
   Tmax) / 2 while Hydrolog takes the daily mean given (at Warszawa 1991–2020 HDD 3407 against 3365 °C·d, +1.25 %), and
   name 18 °C the reference ("temperatura bazowa") and 15 °C the threshold ("temperatura graniczna", Eurostat's English
   "base temperature").

## Consequences

- Results change (0.9.0, breaking): a reference period with missing months now has annual, half-year and season
  normals where it had none, and slightly different ones where it had them (the shipped fixture 2019–2023, with gaps
  in 2022: 703.285 mm instead of 683.35 mm), and with them every `percent_of_normal`, Kaczorowska class and Tmean
  anomaly of the years; `normal_years` may fall (the fewest years of a month). A complete reference gives the same
  numbers. CDD and CWD of a year change when a spell crosses its start or end (Warszawa: 8 of 55 years); a spell's
  `year` is that of its end. `freeze_thaw_days` is a new field of `meteo temperature --index days`. The season
  coefficient, its class, `season_days` and the period's mean change in most years (Warszawa 1991–2020: mean 1.144 →
  1.154), and a year with a gap outside April–September now has a season.
- Obserwator shows these analyses (`temperature.*`, `hydrothermal`, `precipitation.*`, `spells.*`,
  `mann_kendall.temperature.frost_days`): its analyses are to be computed again, its labels of `frost_days` follow
  „dni z przymrozkiem (FD)” and it may show `freeze_thaw_days` as „dni przymrozkowe”; a `request` issue in its
  repository (DEV-17.5).
- The defaults stay ETCCDI's strict signs; a user who needs IMGW-PIB's yearbook counts (≤, ≥) of data in 0.1 °C
  shifts the thresholds by 0.05 °C.

## Alternatives considered

- **Keep the annual normal from the annual values and say so**: simpler, but WMO-No. 1203 asks for the monthly normals
  explicitly (IMGW-PIB's annual count TMAX_0 at Warszawa, 32.6 days, is the sum of its monthly normals), and the old
  rule loses an annual normal to a single missing day in seven years.
- **Cut spells at 1 January** (the literal ETCCDI text, climdex.pcic's non-default option): matches neither the
  default of the ETCCDI's software nor ECA&D, and splits a long winter drought into two short ones.
- **Rename FD „dni przymrozkowe” only in the label**: leaves Polish users without the count IMGW-PIB publishes under
  that name; the count needs no new option.
- **The classical stable-transition season**: needs a transition rule (the Russian handbook's deviation sums or a
  running mean) that no open Polish source fixes; Selyaninov's own papers are not open. Miś (2026) is open, Polish and
  explicit.
- **HDD from (Tmin + Tmax) / 2 when both are given**: matches the Directive, but mixes inputs inside one index and
  changes every HDD; left to the author (open question in the report of T33).
