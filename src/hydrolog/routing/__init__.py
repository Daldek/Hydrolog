"""Lumped hydrologic flood routing (ADR-0007).

The package routes a discharge hydrograph through a reach, a reservoir or a network
with storage-based methods. It computes discharge only: water levels, inundation,
backwater and structures are hydraulics and stay with Hydraulik, HEC-RAS and IMGW HD.
Time is in minutes and discharge in m3/s.

The recurrences shared with the Clark unit hydrograph are in
``hydrolog.routing._kernels``.
"""

from __future__ import annotations
