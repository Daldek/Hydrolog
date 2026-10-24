"""Published reference values of the routing models (data only).

The numbers are copied as they are printed in the sources, with their rounding; the
tolerance that a test may use follows from that rounding and is given next to them.
"""

# University of Iowa, Lesson 27 "Hydrologic Routing, Muskingum Method", worked example
# (https://user.engineering.uiowa.edu/~flood/handouts/EX-L27-Muskingum-soln.pdf):
# K = 20 h, X = 0.25, dt = 12 h, one reach, flows in cfs at 12, 24, ... 120 h. The
# handout prints the outflow to 0.1 cfs, so a printed value is right within 0.05, and
# the weights to four decimals.
IOWA_K_MIN = 20.0 * 60.0
IOWA_X = 0.25
IOWA_STEP_MIN = 12.0 * 60.0
IOWA_TIMES_MIN = [IOWA_STEP_MIN * hour for hour in range(1, 11)]
IOWA_INFLOW = [100.0, 300.0, 680.0, 500.0, 400.0, 310.0, 230.0, 180.0, 100.0, 50.0]
IOWA_OUTFLOW = [100.0, 109.5, 236.5, 481.3, 487.2, 433.1, 358.9, 282.9, 220.3, 149.2]
IOWA_WEIGHTS = (0.0476, 0.5238, 0.4286)
IOWA_TOLERANCE = 0.05
