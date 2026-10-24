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

# NRCS National Engineering Handbook Part 630, Chapter 17 "Flood Routing" (Amendment 69,
# April 2014, a work of the US federal government), Example 17-4, Tables 17-16 to 17-18:
# constant-coefficient Muskingum-Cunge routing of a hydrograph through a trapezoidal
# channel (bottom width 15 ft, side slope 2:1, Manning n 0.04, slope 0.00091, length
# 2,600 ft). The reference discharge is the inflow peak, 684.18 ft3/s; the text takes
# the celerity c = m Q / A = 4.297 ft/s (m = 1.3873, A = 220.9 ft2) and the top width
# 44.6 ft from a HEC-RAS rating table. Flows are in ft3/s at a step of 0.1 h from
# 10.0 h; the inflow and outflow of Table 17-18 are printed to 0.01 ft3/s, and the
# coefficients to three decimals, with which the table was evidently computed.
FT_M = 0.3048
CFS_M3S = FT_M**3
NEH17_4_LENGTH_FT = 2600.0
NEH17_4_SLOPE = 0.00091
NEH17_4_CELERITY_FT_PER_S = 4.297
NEH17_4_TOP_WIDTH_FT = 44.6
NEH17_4_SECTION = {"bottom_width_ft": 15.0, "side_slope": 2.0, "manning_n": 0.04}
NEH17_4_STEP_MIN = 6.0
NEH17_4_START_MIN = 600.0
NEH17_4_INFLOW_CFS = [
    0.00, 0.74, 1.13, 1.63, 2.27, 3.06, 4.01, 5.15, 6.48, 8.03,
    9.82, 11.89, 14.29, 17.09, 20.37, 24.27, 29.31, 37.03, 50.70, 76.68,
    119.72, 179.04, 254.20, 344.67, 442.98, 533.83, 604.92, 652.85, 678.15, 684.18,
    672.05, 645.30, 608.62, 562.41, 509.94, 459.53, 416.94,
]  # fmt: skip
NEH17_4_OUTFLOW_CFS = [
    0.00, 0.26, 0.58, 0.97, 1.45, 2.04, 2.77, 3.65, 4.70, 5.93,
    7.37, 9.04, 10.99, 13.25, 15.88, 18.99, 22.80, 28.03, 36.33, 51.06,
    76.15, 113.90, 165.53, 231.61, 309.81, 393.07, 472.22, 540.06, 592.24, 627.28,
    644.77, 645.72, 632.54, 606.97, 571.28, 529.89, 487.82,
]  # fmt: skip
# C1 (previous inflow), C2 (current inflow), C3 (previous outflow), as printed
NEH17_4_COEFFICIENTS = (0.028, 0.355, 0.617)
NEH17_4_K_S = 605.07
NEH17_4_X = -0.254
NEH17_4_COURANT = 0.595
NEH17_4_GRID_REYNOLDS = 1.508
NEH17_4_GRID_REYNOLDS_LIMIT = 3.93
NEH17_4_DX_FT = 2735.0
NEH17_4_PEAK_OUTFLOW_CFS = 645.72
NEH17_4_PEAK_TIME_H = 13.1
# Table 17-16 at 684.18 ft3/s: A = 220.9 ft2, T = 44.6 ft, m = 1.3873
NEH17_4_AREA_FT2 = 220.9
NEH17_4_ROUNDING_CFS = 0.005  # half of the last printed digit of the outflow
