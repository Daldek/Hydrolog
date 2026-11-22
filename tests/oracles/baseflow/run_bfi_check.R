source("BFI.R")
Q <- as.vector(unlist(read.csv("BassRiver@Loch.csv", header=FALSE)))
cat("n =", length(Q), " sum =", sum(Q), "\n")
r98 <- BFI(Q, alpha=0.98, ReturnQbase=TRUE)
cat(sprintf("alpha=0.98 passes=3 BFI=%.7f FractionUsed=%g\n", r98$BFI, r98$FractionUsed))
r925 <- BFI(Q, alpha=0.925, ReturnQbase=TRUE)
cat(sprintf("alpha=0.925 passes=3 BFI=%.7f\n", r925$BFI))
r9 <- BFI(Q, alpha=0.925, passes=9)
cat(sprintf("alpha=0.925 passes=9 BFI=%.7f\n", r9$BFI))
cat("Qbase alpha=0.98:\n"); print(round(r98$Qbase, 4))
cat("Qbase alpha=0.925:\n"); print(round(r925$Qbase, 4))
Qm <- c(NA,5,7,108,117,57,36,26,95,1169,308,
       144,89,62,48,40,35,73,82,342,393,310,
       275,260,245,256,141,119,934,382,158,96,
       122,103,83,67,148,NA,366,161,119,82,330,294,
       261,266,153,247,703,498,286,163,124,85,94,
       81,62,47,37,30,26,24,24,22,21,20,19,18,18,17,16,NA,20,19,18,18,NA)
rm <- BFI(Qm, alpha=0.98)
cat(sprintf("missing example alpha=0.98 BFI=%.7f FractionUsed=%.7f\n", rm$BFI, rm$FractionUsed))
