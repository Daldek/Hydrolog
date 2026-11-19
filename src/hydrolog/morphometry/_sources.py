"""Sources, ranges and variables shared by the morphometric specs (Nogat CMP-2.1).

The shape indicators (:mod:`hydrolog.morphometry.geometric`), the relief ratio
(:mod:`hydrolog.morphometry.terrain`), the hypsometric integral
(:mod:`hydrolog.morphometry.hypsometry`) and the indices of the river network
(:mod:`hydrolog.network.stream_order`) read the same watershed: its area, length,
perimeter and elevations, with the ranges of Hydrograf's hand-offs. Each range is
written here once.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Final

from hydrolog.nogat_formulas import Range, Source, Variable

__all__ = [
    "AREA",
    "BASCIK",
    "BENDJOUDI_HUBERT",
    "ELEVATION_REASON",
    "LENGTH",
    "PERIMETER",
    "WARTALSKA",
    "decimal_pi",
    "from_handoffs",
]

BENDJOUDI_HUBERT: Final = (
    "Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : "
    "analyse critique d'un indice de forme des bassins versants. Hydrological "
    "Sciences Journal 47(6): 921-930"
)
BENDJOUDI_HUBERT_URL: Final = "https://doi.org/10.1080/02626660209493000"
WARTALSKA: Final = (
    "Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki "
    "charakteryzujące zlewnię. Politechnika Wrocławska, course material"
)
WARTALSKA_URL: Final = (
    "https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZj"
    "YEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpu"
    "fFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf"
)
BASCIK: Final = (
    "Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), "
    "Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, "
    "Kraków, pp. 21-34"
)
BASCIK_URL: Final = (
    "https://ruj.uj.edu.pl/server/api/core/bitstreams/"
    "c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content"
)

_HANDOFFS = (
    "Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November "
    "2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa "
    "(134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, "
    "and the guide's Kamiennik to Świerzawa (37.22 km2)"
)
_HANDOFF_FILES = (
    "tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json"
)

ELEVATION_REASON: Final = (
    "the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and "
    "Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of "
    "Jordan and Nepal)"
)


def from_handoffs(what: str) -> Source:
    """Return the source of a typical range: Hydrograf's hand-offs (CMP-1.5)."""
    return Source(citation=_HANDOFFS, locator=f"{_HANDOFF_FILES}: {what}")


def decimal_pi() -> Decimal:
    """Return pi at the precision of the current decimal context.

    The series of the recipe ``pi()`` in the documentation of Python's ``decimal``
    module, summed with two guard digits: an oracle of the shape indices in another
    form than ``math.pi`` (CMP-6.2).
    """
    with localcontext() as context:
        context.prec += 2
        three = Decimal(3)
        last, term, total = Decimal(0), three, three
        n, na, d, da = 1, 0, 0, 24
        while total != last:
            last = total
            n, na = n + na, na + 8
            d, da = d + da, da + 32
            term = (term * n) / d
            total += term
    return +total


AREA: Final = Variable(
    name="area_km2",
    symbol="A",
    unit="km2",
    description="Planimetric area of the watershed.",
    physical=Range(
        low=0.0,
        low_inclusive=False,
        test_high=1.49e8,
        test_reason="the land area of the Earth, 148.94 million km2 (CIA, The World "
        "Factbook, 2025, field Area: land): no watershed is larger",
    ),
    applicability="unstated",
    typical=Range(
        low=0.0003,
        high=250.0,
        source=from_handoffs(
            "areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of "
            "watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)"
        ),
    ),
)
"""The watershed's area, of every index that divides by it or by its root."""

LENGTH: Final = Variable(
    name="length_km",
    symbol="L",
    unit="km",
    description="Length of the watershed: the straight line from the outlet to the "
    "farthest point of the divide, or the longest flow path Hydrograf hands over.",
    physical=Range(
        low=0.0,
        low_inclusive=False,
        test_high=20000.0,
        test_reason="20,000 km, half the circumference of the Earth (40,075 km at the "
        "equator): no two points of a watershed lie farther apart",
    ),
    applicability="unstated",
    typical=Range(
        low=0.05,
        high=30.0,
        source=from_handoffs("lengths (longest flow paths) of 0.0566 to 28.88 km"),
    ),
)
"""The watershed's length, of the indices of its elongation."""

PERIMETER: Final = Variable(
    name="perimeter_km",
    symbol="P",
    unit="km",
    description="Perimeter of the watershed, the length of its divide.",
    physical=Range(
        low=0.0,
        low_inclusive=False,
        test_high=1.0e6,
        test_reason="a million km, 25 times the circumference of the Earth (40,075 km "
        "at the equator): no divide traced on a map is longer",
    ),
    applicability="unstated",
    typical=Range(
        low=0.17,
        high=90.0,
        source=from_handoffs("perimeters of 0.1756 to 84.46 km"),
    ),
)
"""The watershed's perimeter, of the indices of its compactness."""
