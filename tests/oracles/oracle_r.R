# Frozen-oracle generator: R lmom / lmomco / evd / extRemes / ismev / goftest outputs
# for the datasets dumped by hydrolog_eval.py. Writes oracle_r.json.
suppressPackageStartupMessages({
  library(lmom); library(lmomco); library(evd); library(extRemes); library(ismev)
  library(goftest); library(jsonlite)
})
dir <- "/home/claude-agent/tmp/research-ResFloodFrequency/data"
names_ <- c("floods11", "ozone", "portpirie", "gev_c-0.1_n30", "pe3_g1.0_n50", "ln_s0.6_n40", "wei_k1.5_n35")
T <- c(2, 5, 10, 20, 50, 100, 500, 1000)
F <- 1 - 1 / T
res <- list()
for (nm in names_) {
  x <- scan(file.path(dir, paste0(nm, ".txt")), quiet = TRUE)
  r <- list(n = length(x))
  lm <- lmom::samlmu(x, nmom = 4)
  r$samlmu <- as.list(lm)
  pg <- lmom::pelgev(lm); r$pelgev <- as.list(pg); r$quagev <- lmom::quagev(F, pg)
  pp3 <- lmom::pelpe3(lm); r$pelpe3 <- as.list(pp3); r$quape3 <- lmom::quape3(F, pp3)
  pl <- tryCatch(lmom::pelln3(lm, bound = 0), error = function(e) NULL)
  if (!is.null(pl)) { r$pelln3_b0 <- as.list(pl); r$qualn3_b0 <- lmom::qualn3(F, pl) }
  pw <- tryCatch(lmom::pelwei(lm), error = function(e) NULL)
  if (!is.null(pw)) { r$pelwei <- as.list(pw); r$quawei <- lmom::quawei(F, pw) }
  # lmomco independent implementation (Asquith)
  lmr <- lmomco::lmoms(x, nmom = 4)
  r$lmomco_lmoms <- list(L1 = lmr$lambdas[1], L2 = lmr$lambdas[2], T3 = lmr$ratios[3])
  g2 <- lmomco::pargev(lmr, useHosking = FALSE); r$lmomco_pargev_exact <- as.list(g2$para)
  p2 <- lmomco::parpe3(lmr, useHosking = TRUE); r$lmomco_parpe3_hosking <- as.list(p2$para)
  # plotting positions (ascending non-exceedance)
  r$pp_weibull <- lmomco::pp(x, a = 0); r$pp_cunnane <- lmomco::pp(x, a = 0.4); r$pp_hazen <- lmomco::pp(x, a = 0.5)
  # GEV maximum likelihood by three implementations; loglik reported
  f1 <- tryCatch(evd::fgev(x), error = function(e) NULL)
  if (!is.null(f1)) r$evd_fgev <- list(loc = unname(f1$estimate["loc"]), scale = unname(f1$estimate["scale"]),
                                         shape_xi = unname(f1$estimate["shape"]), loglik = -f1$deviance / 2)
  f2 <- tryCatch(extRemes::fevd(x, type = "GEV", method = "MLE"), error = function(e) NULL)
  if (!is.null(f2)) { p <- f2$results$par
    r$extRemes_fevd <- list(loc = unname(p["location"]), scale = unname(p["scale"]), shape_xi = unname(p["shape"]),
                            loglik = -f2$results$value,
                            rl = as.numeric(extRemes::return.level(f2, return.period = T))) }
  f3 <- tryCatch({ sink(tempfile()); o <- ismev::gev.fit(x, show = FALSE); sink(); o }, error = function(e) { sink(); NULL })
  if (!is.null(f3)) r$ismev_gevfit <- list(loc = f3$mle[1], scale = f3$mle[2], shape_xi = f3$mle[3], loglik = -f3$nllh)
  # lmomco general ML for PE3 and Weibull (3-parameter), started from L-moments
  m3 <- tryCatch(lmomco::mle2par(x, type = "pe3", init.para = p2), error = function(e) NULL)
  if (!is.null(m3)) r$lmomco_mle_pe3 <- list(para = as.list(m3$para), loglik = -m3$optim$value)
  w0 <- tryCatch(lmomco::parwei(lmr), error = function(e) NULL)
  if (!is.null(w0)) { m4 <- tryCatch(lmomco::mle2par(x, type = "wei", init.para = w0), error = function(e) NULL)
    if (!is.null(m4)) r$lmomco_mle_wei <- list(para = as.list(m4$para), loglik = -m4$optim$value) }
  # 2-parameter log-normal ML (closed form, divisor n)
  if (all(x > 0)) { lx <- log(x); r$ln2_mle <- list(meanlog = mean(lx), sdlog = sqrt(mean((lx - mean(lx))^2))) }
  res[[nm]] <- r
}
write(toJSON(res, auto_unbox = TRUE, digits = NA, pretty = TRUE), "/home/claude-agent/tmp/research-ResFloodFrequency/oracle_r.json")
cat("R", R.version.string, "lmom", as.character(packageVersion("lmom")), "lmomco", as.character(packageVersion("lmomco")),
    "evd", as.character(packageVersion("evd")), "extRemes", as.character(packageVersion("extRemes")),
    "ismev", as.character(packageVersion("ismev")), "goftest", as.character(packageVersion("goftest")), "\n")
