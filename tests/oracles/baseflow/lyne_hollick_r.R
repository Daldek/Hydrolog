# Frozen-oracle generator (Nogat CMP-6.4) of the Lyne and Hollick filter: Ladson's own
# R function BFI() (BFI.R of github.com/TonyLadson/BaseflowSeparation_LyneHollick,
# commit 8d09646, 2014-02-12, copied unchanged into this directory) on
#   * bass_river: the 67 daily flows [ML/d] of the Bass River at Loch of Ladson et al.
#     (2013), Table 3 (BassRiver@Loch.csv of github.com/TonyLadson/data, unchanged);
#   * synthetic: 730 daily flows [m3/s] drawn here with set.seed(20261119), a seasonal
#     cycle with lognormal AR(1) noise and storm pulses, rounded to 0.001.
# Writes lyne_hollick_r.csv (the daily baseflow, ReturnQbase = TRUE) and
# lyne_hollick_bfi_r.csv (the BFI that BFI() reports) once, from this directory:
#   Rscript lyne_hollick_r.R
# Never rerun into the same files: a new run writes new files.
source("BFI.R")

bass <- as.vector(unlist(read.csv("BassRiver@Loch.csv", header = FALSE)))

set.seed(20261119)
n <- 730
day <- seq_len(n)
noise <- as.numeric(stats::filter(rnorm(n, sd = 0.15), 0.9, method = "recursive"))
storms <- stats::filter(rbinom(n, 1, 0.05) * rexp(n, 1 / 4), 0.6, method = "recursive")
synthetic <- round(2 + 1.2 * sin(2 * pi * day / 365.25) + exp(noise) + storms, 3)

datasets <- list(bass_river = bass, synthetic = synthetic)
alphas <- c(0.9, 0.925, 0.95, 0.98, 0.987)
passes <- c(3, 5, 9)

header <- c(
  paste0("# tool: ", R.version.string),
  "# packages: base R and stats only; BFI.R of Ladson (github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646, 2014-02-12), unchanged, in this directory",
  paste0("# platform: ", R.version$platform),
  paste0("# date: ", format(Sys.Date(), "%Y-%m-%d")),
  "# script: tests/oracles/baseflow/lyne_hollick_r.R",
  "# conventions: Ladson et al. (2013): 30 values reflected at each end without the end value, the quickflow of each pass starting at the first value of its input and kept unclipped, the baseflow below 0 set to 0 after the last pass; BFI = sum(baseflow) / sum(flow)"
)

daily <- file("lyne_hollick_r.csv", "w")
writeLines(c(header, "dataset,alpha,passes,day,flow,baseflow"), daily)
index <- file("lyne_hollick_bfi_r.csv", "w")
writeLines(c(header, "dataset,alpha,passes,bfi,fraction_used"), index)
for (name in names(datasets)) {
  q <- datasets[[name]]
  for (a in alphas) {
    for (p in passes) {
      r <- BFI(q, alpha = a, passes = p, ReturnQbase = TRUE)
      writeLines(sprintf("%s,%s,%d,%d,%s,%s", name, format(a), p, seq_along(q),
                         format(q, digits = 17, trim = TRUE),
                         sprintf("%.17g", r$Qbase)), daily)
      writeLines(sprintf("%s,%s,%d,%.17g,%.17g", name, format(a), p, r$BFI,
                         r$FractionUsed), index)
    }
  }
}
close(daily)
close(index)
