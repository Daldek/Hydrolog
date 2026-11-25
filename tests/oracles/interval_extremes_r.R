# Frozen oracle (Nogat CMP-6.4) of the spec quantile_interval_delta, its GEV: the
# return levels and their normal-approximation (delta method) intervals of extRemes,
# on the samples of frequency_ml_samples.csv (annual maxima) and on the negated annual
# minima of station 223207 (WMO-No. 1029, table 7.1), the low-flow use.
#
# Run once, from the repository root, by the R of the research ResFloodFrequency
# (R 4.5.3, extRemes 2.2.1):
#   Rscript tests/oracles/interval_extremes_r.R [tests/oracles/interval_extremes_r.csv]
# It writes the CSV with its metadata header and refuses to overwrite it: a frozen
# oracle is never regenerated into the same file (CMP-6.4).
#
# What extRemes does (2.2.1, read in its source): fevd(x, type = "GEV", method = "MLE")
# maximizes the likelihood by optim; ci.fevd(method = "normal", type = "return.level")
# (ci.fevd.mle) takes the parameter covariance of parcov.fevd, the inverse of
# optimHess at the estimate (central differences, step 1e-3, of the analytic gradient
# grlevd of the negative log-likelihood: the observed information), the analytic
# gradient of the return level (rlgrad.fevd), and gives rl -+ z se, z =
# qnorm(alpha/2, lower.tail = FALSE), se = sqrt(grad' cov grad).

suppressPackageStartupMessages(library(extRemes))

args <- commandArgs(trailingOnly = TRUE)
output <- if (length(args) >= 1) args[1] else "tests/oracles/interval_extremes_r.csv"
if (file.exists(output)) {
  stop(output, " exists: a frozen oracle is never regenerated into the same file (CMP-6.4)")
}

lines <- readLines("tests/oracles/frequency_ml_samples.csv")
samples <- read.csv(text = lines[!startsWith(lines, "#")])
# The AM(7) annual minima of station 223207 (WMO-No. 1029, table 7.1):
# hydrolog.statistics.low_flows._STATION_223207.
station_223207 <- c(
  27.3, 38.0, 72.9, 53.6, 45.7, 37.0, 21.7, 36.6, 43.1, 12.6, 20.7, 66.7, 76.6,
  53.1, 15.7, 66.6, 78.0, 53.1, 62.6, 40.7, 51.6, 23.1, 23.4, 23.0, 6.0
)
periods <- c(2, 5, 10, 20, 50, 100, 500, 1000)  # Hydrolog's default return periods
levels <- c(0.95, 0.68)  # the levels Obserwator stores

cases <- lapply(unique(samples$dataset), function(name) {
  list(dataset = name, extremes = "maxima", x = samples$value[samples$dataset == name])
})
cases[[length(cases) + 1]] <- list(
  dataset = "station_223207", extremes = "minima", x = -station_223207
)

rows <- list()
for (case in cases) {
  fit <- fevd(case$x, type = "GEV", method = "MLE")
  par <- fit$results$par
  stopifnot(fit$results$convergence == 0)
  if (!(par[["shape"]] > -0.5)) {  # not regular (Smith 1985): no interval to compare
    message(case$dataset, ": shape ", par[["shape"]], " <= -0.5, left out")
    next
  }
  for (level in levels) {
    found <- unclass(ci(
      fit, alpha = 1 - level, type = "return.level", return.period = periods,
      method = "normal"
    ))
    rows[[length(rows) + 1]] <- data.frame(
      dataset = case$dataset, extremes = case$extremes, n = length(case$x),
      location = par[["location"]], scale = par[["scale"]], shape = par[["shape"]],
      loglik = -fit$results$value, return_period = periods, confidence_level = level,
      lower = found[, 1], estimate = found[, 2], upper = found[, 3]
    )
  }
  message(case$dataset, " done")
}
table <- do.call(rbind, rows)

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
  "# Frozen oracle (Nogat CMP-6.4) of quantile_interval_delta, the GEV by maximum",
  "# likelihood and the normal-approximation intervals of its return levels by extRemes,",
  "# written by the script on its one run.",
  sprintf(
    "# tool: R %s.%s (%s-%s-%s), extRemes::fevd (GEV, MLE) and extRemes::ci.fevd (method normal)",
    version$major, version$minor, version$year, version$month, version$day
  ),
  sprintf(
    "# packages: extRemes %s (Gilleland and Katz), distillery %s, Lmoments %s",
    as.character(packageVersion("extRemes")), as.character(packageVersion("distillery")),
    as.character(packageVersion("Lmoments"))
  ),
  sprintf("# platform: %s", version$platform),
  sprintf("# date: %s", format(Sys.Date(), "%Y-%m-%d")),
  "# script: tests/oracles/interval_extremes_r.R",
  "# samples: the datasets of frequency_ml_samples.csv (annual maxima, extremes maxima)",
  "#   and station_223207, the AM(7) annual minima of WMO-No. 1029 table 7.1 negated",
  "#   (extremes minima), every one whose GEV shape xi > -0.5 (regular, Smith 1985).",
  "# conventions: location, scale and shape are extRemes's GEV (mu, sigma, xi of Coles",
  "#   2001) of the sample it fitted, xi = -c of scipy's genextreme; for minima that",
  "#   sample is the negated minima, so Hydrolog's fisher_tippett_minima has c = -shape,",
  "#   loc = -location, scale = scale, and its interval of the T-year minimum is",
  "#   (-upper, -lower) around -estimate. estimate is the return level of T years (the",
  "#   quantile 1 - 1/T of the fitted sample), lower and upper estimate -+ z se, z =",
  "#   qnorm((1 - confidence_level)/2, lower.tail = FALSE), se from the inverse of",
  "#   optimHess (step 1e-3) of the analytic gradient of the negative log-likelihood",
  "#   at the estimate (the observed information) and the analytic gradient of the",
  "#   return level. loglik is -fit$results$value. Numbers in the shortest of 15 to 17",
  "#   significant digits that reads back as R's double."
)
writeLines(header, output)
suppressWarnings(write.table(
  table, output, sep = ",", quote = FALSE, row.names = FALSE, append = TRUE
))
message("wrote ", output)
