# Export the published data sets shipped with R and the trend package, at full
# precision, for the frozen oracles of the trend-regime domain.
#   PagesData  Page (1955) series as tabulated by Pettitt (1979), Table 1 (trend pkg)
#   Nile       annual flow of the Nile at Aswan 1871-1970, 10^8 m^3 (R datasets)
#   maxau      Rhine at Maxau 1965-2009: s suspended sediment mg/l, Q discharge m^3/s (trend pkg)
# Usage: Rscript r_export_datasets.R <out.csv>
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) >= 1) args[1] else "datasets_r.csv"
suppressPackageStartupMessages(library(trend))
data(PagesData)
data(maxau)
rows <- list()
add <- function(name, values, years = NA, group = NA) {
  n <- length(values)
  data.frame(dataset = name, index = seq_len(n),
             time = if (all(is.na(years))) seq_len(n) else years,
             group = group, value = sprintf("%.17g", as.numeric(values)),
             stringsAsFactors = FALSE)
}
rows[[1]] <- add("pettitt_page", as.numeric(PagesData))
rows[[2]] <- add("nile", as.numeric(Nile), years = as.integer(time(Nile)))
rows[[3]] <- add("maxau_Q", as.numeric(maxau[, "Q"]), years = as.integer(time(maxau)))
rows[[4]] <- add("maxau_s", as.numeric(maxau[, "s"]), years = as.integer(time(maxau)))
write.csv(do.call(rbind, rows), out, row.names = FALSE, quote = TRUE)
