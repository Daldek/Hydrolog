# Frozen oracles of the trend-regime domain (Hydrolog statistics.stationarity,
# statistics.homogeneity). Run once; never regenerate into the same file.
#   Rscript r_oracle.R datasets.csv r_oracle_outputs.csv r_oracle_meta.txt
# Conventions of the outputs (state them in every comparison):
#   trend::mk.test        S, varS tie-corrected (Kendall 1975), z with continuity
#                         correction, p two-sided = 2*min(0.5, P(Z>|z|)).
#   modifiedmk::mkttest   same S, Var(S) tie-corrected, z continuity-corrected,
#                         p = 2*pnorm(-|z|); Sen slope per index step (j - i).
#   Kendall::MannKendall  Fortran tauk2 on SINGLE precision copies of the data
#                         (as.single): values that differ below ~1e-7 relative tie;
#                         sl = two-sided p (normal approximation of S with continuity
#                         correction and tie-corrected variance, see the package docs).
#   trend::sens.slope     slopes per index step (j - i); CI ranks rounded with R's
#                         round() (IEC 60559, half to even): lo = d[round((N'-C)/2)],
#                         up = d[round((N'+C)/2 + 1)], C = z_{1-a/2} sqrt(varS)
#                         (NOT Gilbert's linear interpolation between ranks).
#   trend::pettitt.test   U_k = 2 sum_{i<=k} r_i - k(n+1), k = 1..n, mid-ranks;
#                         K = max|U_k|; p = min(1, 2 exp(-6K^2/(n^3+n^2))); estimate = all
#                         k attaining K (1-based index of the last value before the change).
#   stats::wilcox.test    two-sided; W = U of the FIRST sample; exact when n < 50 in
#                         both samples and no ties, else normal with continuity and tie
#                         correction (correct = TRUE).
#   stats::ks.test        two-sample, two-sided; exact when n.x*n.y < 10000 (R >= 4.3
#                         also with ties via psmirnov), else asymptotic.
args <- commandArgs(trailingOnly = TRUE)
inp <- if (length(args) >= 1) args[1] else "datasets.csv"
out <- if (length(args) >= 2) args[2] else "r_oracle_outputs.csv"
meta <- if (length(args) >= 3) args[3] else "r_oracle_meta.txt"
suppressPackageStartupMessages({
  library(trend); library(Kendall); library(modifiedmk)
})
d <- read.csv(inp, colClasses = c("character", "integer", "numeric", "character", "character"))
d$value <- as.numeric(d$value)
res <- list()
put <- function(ds, pkg, fun, args, stat, value) {
  res[[length(res) + 1]] <<- data.frame(dataset = ds, package = pkg, fun = fun,
    args = args, statistic = stat, value = sprintf("%.17g", as.numeric(value)),
    stringsAsFactors = FALSE)
}
single_series <- c("gilbert_ex16_1", "helsel_ex10_1", "kzgw_bobr_bukowka",
  "kzgw_czarna_polana", "kzgw_rypienica_rypin", "kzgw_swislina_rzepin",
  "pettitt_page", "nile", "maxau_Q", "maxau_s", "seeded_ties", "seeded_step",
  "luke_peaks")
for (ds in single_series) {
  x <- d$value[d$dataset == ds]
  m <- trend::mk.test(x)
  put(ds, "trend", "mk.test", "continuity=TRUE", "S", m$estimates["S"])
  put(ds, "trend", "mk.test", "continuity=TRUE", "varS", m$estimates["varS"])
  put(ds, "trend", "mk.test", "continuity=TRUE", "tau", m$estimates["tau"])
  put(ds, "trend", "mk.test", "continuity=TRUE", "z", m$statistic)
  put(ds, "trend", "mk.test", "continuity=TRUE", "p", m$p.value)
  mm <- modifiedmk::mkttest(x)
  for (nm in names(mm)) put(ds, "modifiedmk", "mkttest", "", nm, mm[[nm]])
  k <- suppressWarnings(Kendall::MannKendall(x))
  put(ds, "Kendall", "MannKendall", "single precision", "S", k$S)
  put(ds, "Kendall", "MannKendall", "single precision", "varS", k$varS)
  put(ds, "Kendall", "MannKendall", "single precision", "tau", k$tau)
  put(ds, "Kendall", "MannKendall", "single precision", "sl", k$sl)
  for (cl in c(0.95, 0.90)) {
    s <- trend::sens.slope(x, conf.level = cl)
    a <- sprintf("conf.level=%.2f", cl)
    put(ds, "trend", "sens.slope", a, "slope", s$estimates)
    put(ds, "trend", "sens.slope", a, "lower", s$conf.int[1])
    put(ds, "trend", "sens.slope", a, "upper", s$conf.int[2])
  }
  p <- trend::pettitt.test(x)
  put(ds, "trend", "pettitt.test", "", "K", p$statistic)
  put(ds, "trend", "pettitt.test", "", "p", p$p.value)
  put(ds, "trend", "pettitt.test", "", "t_first", min(p$estimate))
  put(ds, "trend", "pettitt.test", "", "n_t", length(p$estimate))
}
two_sample <- c("helsel_ex5_1", "luke_peaks", "seeded_step")
for (ds in two_sample) {
  x <- d$value[d$dataset == ds & d$group == "1"]
  y <- d$value[d$dataset == ds & d$group == "2"]
  w <- suppressWarnings(wilcox.test(x, y, alternative = "two.sided", correct = TRUE))
  put(ds, "stats", "wilcox.test", "default exact", "W", w$statistic)
  put(ds, "stats", "wilcox.test", "default exact", "p", w$p.value)
  wa <- suppressWarnings(wilcox.test(x, y, alternative = "two.sided", correct = TRUE,
    exact = FALSE))
  put(ds, "stats", "wilcox.test", "exact=FALSE", "W", wa$statistic)
  put(ds, "stats", "wilcox.test", "exact=FALSE", "p", wa$p.value)
  ks <- suppressWarnings(ks.test(x, y, alternative = "two.sided"))
  put(ds, "stats", "ks.test", "default", "D", ks$statistic)
  put(ds, "stats", "ks.test", "default", "p", ks$p.value)
  put(ds, "stats", "ks.test", "default", "exact", as.numeric(isTRUE(ks$exact)))
}
write.csv(do.call(rbind, res), out, row.names = FALSE, quote = TRUE)
info <- c(
  R.version.string,
  paste("platform", R.version$platform),
  paste("trend", as.character(packageVersion("trend"))),
  paste("Kendall", as.character(packageVersion("Kendall"))),
  paste("modifiedmk", as.character(packageVersion("modifiedmk"))),
  paste("date", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
  paste("input", inp, "sha256", digest_sha <- tryCatch(
    system2("sha256sum", inp, stdout = TRUE), error = function(e) "n/a"))
)
writeLines(info, meta)
