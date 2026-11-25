# Frozen oracle (Nogat CMP-6.4) of the spec quantile_interval_bootstrap: the limits
# that lmomco's qua2ci.simple (the function genci.simple calls once per probability)
# gives for the quantiles of the L-moments fits of the Polana maxima, Hydrolog's
# parent distributions of the parametric bootstrap.
#
# Run once, from the repository root, by the R of the research ResFloodFrequency
# (R 4.5.3, lmomco 2.5.8):
#   Rscript tests/oracles/interval_lmomco_r.R [tests/oracles/interval_lmomco_r.csv]
# It writes the CSV with its metadata header and refuses to overwrite it: a frozen
# oracle is never regenerated into the same file (CMP-6.4).
#
# What qua2ci.simple does (lmomco 2.5.8, read in its source): nsim samples of n values
# drawn by rlmomco (inverse transform of runif) from `para`; each refitted by
# lmom2par of its lmoms; a sample whose L-moments are invalid (are.lmom.valid) or
# whose fit fails is REDRAWN, so nsim refits are always kept (sim.attempts counts
# the draws). Its limits come in two conventions: lwr/upr are the quantiles
# (1 - level)/2 and (1 + level)/2 of an error distribution `edist` ("gno", the
# generalized normal) fitted by L-moments to the nsim simulated quantiles;
# empdist$empir.dist.lwr/upr are the empirical quantiles of the simulated quantiles,
# quantile(type = 6), positions i/(nsim + 1). Hydrolog's spec reads the empirical
# limits, type 6, of its own 999 refits (a sample the L-moments cannot fit is left
# out, not redrawn).
#
# Both levels come from one simulation per probability, as Hydrolog's: the call at
# level 0.95 returns the simulated quantiles (empdist$simquas) and the fitted gno
# (epara); the limits at 0.68 are read from them by qua2ci.simple's own expressions
# (par2qua and quantile type 6 at (1 - 0.68)/2 and 1 - (1 - 0.68)/2), which the
# script checks are identical to a call at level 0.68 with the same seed.

suppressPackageStartupMessages({
  library(lmomco)
  library(parallel)
})

args <- commandArgs(trailingOnly = TRUE)
output <- if (length(args) >= 1) args[1] else "tests/oracles/interval_lmomco_r.csv"
if (file.exists(output)) {
  stop(output, " exists: a frozen oracle is never regenerated into the same file (CMP-6.4)")
}

# The annual maxima of the Czarna at Polana [m3/s], 34 years (KZGW 2017, example 3.2,
# table 3.5): hydrolog.statistics.frequency._POLANA.
polana <- c(
  10.2, 9.24, 58.8, 8.23, 16.2, 4.92, 26.8, 25.1, 97.2, 23.5, 22.3, 21.1, 59.9,
  55.1, 16.2, 24.6, 14.8, 73.8, 28.9, 18.6, 18.2, 25.8, 14.5, 11.2, 54.5, 111.0,
  35.1, 43.0, 52.0, 45.4, 8.90, 9.72, 57.4, 50.8
)
periods <- c(2, 5, 10, 20, 50, 100, 500, 1000)  # Hydrolog's default return periods
levels <- c(0.95, 0.68)  # the levels Obserwator stores; the first is simulated
nsim <- 20000L
seed <- 20261125L
n <- length(polana)
lmr <- lmoms(polana)

# Hydrolog's L-moments fits, as lmomco types; the extra arguments reach lmom2par both
# for the parent and for every refit (qua2ci.simple passes `...` to lmom2par).
fits <- list(
  gev = list(type = "gev", extra = list(useHosking = FALSE)),  # tau3 solved exactly
  pearson3 = list(type = "pe3", extra = list()),  # Hosking's rational approximations
  log_normal = list(type = "ln3", extra = list(zeta = 0)),  # 2 parameters, bound 0
  weibull = list(type = "wei", extra = list())  # the reversed GEV of the L-moments
)

limits_of <- function(ci, level) {
  lower <- (1 - level) / 2  # qua2ci.simple's cilo and cihi
  upper <- 1 - lower
  edist <- if (is.list(ci$epara)) par2qua(c(lower, upper), ci$epara) else c(NA, NA)
  empirical <- unname(c(
    quantile(ci$empdist$simquas, probs = lower, type = 6),
    quantile(ci$empdist$simquas, probs = upper, type = 6)
  ))
  list(edist = edist, empirical = empirical)
}

simulate <- function(f, para, extra, size, level) {
  set.seed(seed)
  do.call(qua2ci.simple, c(
    list(f, para, n, level = level, edist = "gno", nsim = size, empdist = TRUE),
    extra
  ))
}

run <- function(name) {
  fit <- fits[[name]]
  para <- do.call(lmom2par, c(list(lmr, type = fit$type), fit$extra))
  # The limits at the second level read from the first level's simulation are those
  # of a call at the second level with the same seed (checked on a short run).
  short <- simulate(0.99, para, fit$extra, 200L, levels[1])
  direct <- simulate(0.99, para, fit$extra, 200L, levels[2])
  derived <- limits_of(short, levels[2])
  stopifnot(
    identical(unname(c(direct$lwr, direct$upr)), unname(derived$edist)),
    identical(
      unname(c(direct$empdist$empir.dist.lwr, direct$empdist$empir.dist.upr)),
      derived$empirical
    )
  )
  rows <- list()
  for (period in periods) {
    f <- 1 - 1 / period
    ci <- simulate(f, para, fit$extra, nsim, levels[1])
    stopifnot(ci$ifail == 0, ci$nsim == nsim)
    for (level in levels) {
      found <- limits_of(ci, level)
      if (level == levels[1]) {
        stopifnot(
          identical(unname(c(ci$lwr, ci$upr)), unname(found$edist)),
          identical(
            unname(c(ci$empdist$empir.dist.lwr, ci$empdist$empir.dist.upr)),
            found$empirical
          )
        )
      }
      rows[[length(rows) + 1]] <- data.frame(
        distribution = name, lmomco_type = fit$type,
        para_names = paste(names(para$para), collapse = " "),
        para1 = para$para[[1]], para2 = para$para[[2]], para3 = para$para[[3]],
        n = n, return_period = period, nonexceedance = f, true = ci$true,
        confidence_level = level,
        edist_lwr = found$edist[1], edist_upr = found$edist[2],
        empirical_lwr = found$empirical[1], empirical_upr = found$empirical[2],
        nsim = nsim, sim_attempts = ci$sim.attempts
      )
    }
    message(name, " T = ", period, " done")
  }
  do.call(rbind, rows)
}

table <- do.call(rbind, mclapply(names(fits), run, mc.cores = length(fits)))

# The shortest of 15 to 17 significant digits that reads back as the same double.
shortest <- function(x) {
  if (!is.numeric(x)) return(x)
  vapply(x, function(value) {
    for (count in 15:17) {
      text <- sprintf("%.*g", count, value)
      if (is.na(value) || as.numeric(text) == value) return(text)
    }
    text
  }, "")
}
table[] <- lapply(table, shortest)
version <- R.version
header <- c(
  "# Frozen oracle (Nogat CMP-6.4) of quantile_interval_bootstrap, the limits of",
  "# lmomco's qua2ci.simple for the L-moments fits of the 34 Polana maxima (KZGW 2017,",
  "# example 3.2), n = 34, nsim = 20000, return periods 2 to 1000 years, levels 0.95",
  "# and 0.68, written by the script on its one run.",
  sprintf(
    "# tool: R %s.%s (%s-%s-%s), lmomco::qua2ci.simple (genci.simple calls it per probability)",
    version$major, version$minor, version$year, version$month, version$day
  ),
  sprintf("# packages: lmomco %s (Asquith)", as.character(packageVersion("lmomco"))),
  sprintf("# platform: %s", version$platform),
  sprintf("# date: %s", format(Sys.Date(), "%Y-%m-%d")),
  "# script: tests/oracles/interval_lmomco_r.R",
  sprintf("# seed: set.seed(%d) before each probability, RNG %s", seed,
    paste(RNGkind(), collapse = "/")),
  "#   (so every probability and distribution draws the same uniforms); both levels of",
  "#   a probability are one simulation, read at (1 - c)/2 and 1 - (1 - c)/2.",
  "# conventions: the parent is lmomco's fit of lmoms(polana), para1..3 in lmomco's",
  "#   order (para_names). gev (xi, alpha, kappa) is scipy's genextreme(c = kappa,",
  "#   loc = xi, scale = alpha), pargev with useHosking = FALSE (tau3 solved by uniroot),",
  "#   for the parent and every refit; pe3 (mu, sigma, gamma) is scipy's pearson3(skew =",
  "#   gamma, loc = mu, scale = sigma), Hosking's rational approximations (parpe3's",
  "#   default); ln3 with zeta = 0 (zeta, mulog, sigmalog) is scipy's lognorm(s =",
  "#   sigmalog, loc = 0, scale = exp(mulog)), for the parent and every refit; wei",
  "#   (zeta, beta, delta) is scipy's weibull_min(delta, loc = -zeta, scale = beta), the",
  "#   reversed GEV of the L-moments (parwei calls pargev with Hosking's approximation).",
  "#   true is par2qua(nonexceedance, parent), nonexceedance = 1 - 1/return_period.",
  "# limits: edist_lwr and edist_upr are qua2ci.simple's lwr and upr, the quantiles",
  "#   (1 - c)/2 and (1 + c)/2 of the generalized normal (edist gno) fitted by L-moments",
  "#   to the nsim simulated quantiles; empirical_lwr and empirical_upr are its empdist",
  "#   empir.dist.lwr and empir.dist.upr, quantile(type = 6) of the simulated quantiles",
  "#   (positions i/(nsim + 1)). A sample lmomco cannot fit is redrawn (sim_attempts",
  "#   counts the draws); Hydrolog leaves it out. Numbers in the shortest of 15 to 17",
  "#   significant digits that reads back as R's double."
)
writeLines(header, output)
suppressWarnings(write.table(
  table, output, sep = ",", quote = FALSE, row.names = FALSE, append = TRUE
))
message("wrote ", output)
