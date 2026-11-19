# Frozen oracle for the power-law rating curve Q = a (H - H0)^b fitted by
# least squares on Q (arithmetic residuals), bounds a >= 0, b >= 0, H0 < min(H),
# as Hydrolog's RatingCurve.fit() does; R's nls(algorithm = "port") is an
# independent optimiser. A log-space fit (WMO-No. 1044 Vol. II, 1.12.2: least
# squares assuming a straight line on logarithmic paper) is reported for contrast.
#   Rscript r_rating_oracle.R r_rating_outputs.csv
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) >= 1) args[1] else "r_rating_outputs.csv"
sets <- list(
  doc_negative_stages = list(
    H = c(-10, 5, 20, 40, 80, 120), Q = c(0.5, 1.2, 2.5, 4.8, 10.1, 17.3), unit = "cm"),
  fixture_pairs = list(
    H = c(62, 75, 88, 101, 115, 128, 142, 155, 170, 185, 200, 218, 235, 252, 270),
    Q = c(1.05, 2.14, 3.40, 4.67, 6.32, 8.27, 10.48, 12.46, 20.75, 17.72, 20.50, 23.40,
          26.63, 31.80, 34.92), unit = "cm"),
  # WMO-No. 1044 Vol. II (2010), Table II.1.1: gauge height [m], discharge [m3/s]
  wmo1044_table_II_1_1 = list(
    H = c(2.682, 2.786, 2.002, 1.981, 2.374, 1.557, 1.490, 1.509, 1.838, 1.780, 1.710,
          1.573, 1.570, 1.414, 1.396, 2.432),
    Q = c(99.12, 11.02, 33.13, 30.02, 67.40, 7.080, 4.928, 5.296, 20.99, 17.13, 13.54,
          7.703, 7.590, 3.483, 3.313, 69.95), unit = "m")
)
rows <- list()
put <- function(ds, method, stat, value) {
  rows[[length(rows) + 1]] <<- data.frame(dataset = ds, method = method, statistic = stat,
    value = sprintf("%.17g", value), stringsAsFactors = FALSE)
}
for (nm in names(sets)) {
  s <- sets[[nm]]
  H <- s$H; Q <- s$Q
  hmin <- min(H); span <- max(H) - hmin
  h0s <- hmin - max(if (s$unit == "cm") 1 else 0.01, 0.1 * span)
  fit <- try(nls(Q ~ a * (H - h0)^b, start = list(a = 1, b = 1.5, h0 = h0s),
                 algorithm = "port", lower = c(0, 0, -Inf), upper = c(Inf, Inf, hmin - 1e-6),
                 control = nls.control(maxiter = 1000, warnOnly = TRUE)), silent = TRUE)
  if (!inherits(fit, "try-error")) {
    cf <- coef(fit)
    put(nm, "nls_port_arith", "a", cf["a"]); put(nm, "nls_port_arith", "b", cf["b"])
    put(nm, "nls_port_arith", "h0", cf["h0"])
    put(nm, "nls_port_arith", "sse", sum(residuals(fit)^2))
  }
  # log-space least squares: profile over h0 (grid + optimize), OLS of log Q on log(H - h0)
  sse_log <- function(h0) { m <- lm(log(Q) ~ log(H - h0)); sum(residuals(m)^2) }
  lo <- hmin - 3 * span; hi <- hmin - 1e-6 * max(1, span)
  opt <- optimize(sse_log, c(lo, hi))
  m <- lm(log(Q) ~ log(H - opt$minimum))
  put(nm, "ols_log_profile_h0", "a", exp(coef(m)[1])); put(nm, "ols_log_profile_h0", "b", coef(m)[2])
  put(nm, "ols_log_profile_h0", "h0", opt$minimum); put(nm, "ols_log_profile_h0", "sse_log", opt$objective)
  put(nm, "ols_log_profile_h0", "h0_at_bound", as.numeric(abs(opt$minimum - lo) < 1e-3 * span))
}
write.csv(do.call(rbind, rows), out, row.names = FALSE, quote = TRUE)
cat(R.version.string, "\n")
