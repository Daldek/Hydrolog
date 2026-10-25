"""Things the library does not know, for the tests of its extension points (ADR-0012).

A rainfall, a shape of a design storm and a runoff model, each a class that implements
the protocol of its kind and nothing else of the library. The tests register them in a
registry (``monkeypatch.setitem(REGISTRY._classes, name, cls)``) to show that a document
finds them there, and use them without registering to show that the network needs the
protocol only.
"""

import numpy as np

from hydrolog.precipitation import Hietogram, HietogramResult
from hydrolog.routing import Hydrograph


class Constant:
    """A rainfall: the same depth in every one of ``steps`` steps, at any time step."""

    kind = "constant"

    def __init__(self, depth_mm, steps):
        self.depth_mm = depth_mm
        self.steps = steps

    @property
    def timestep_min(self):
        return None

    def hyetograph(self, timestep_min, duration_min=None):
        return HietogramResult(
            times_min=np.arange(1, self.steps + 1) * timestep_min,
            intensities_mm=np.full(self.steps, float(self.depth_mm)),
            total_mm=float(self.depth_mm * self.steps),
            duration_min=self.steps * timestep_min,
            timestep_min=timestep_min,
        )

    def describe(self, hyetograph=None):
        from hydrolog.routing import Parameter

        return [Parameter("depth_mm", self.depth_mm, "mm", "given")]

    def to_document(self):
        return {"kind": self.kind, "depth_mm": self.depth_mm, "steps": self.steps}

    @classmethod
    def from_document(cls, document):
        return cls(document["depth_mm"], document["steps"])


class Growing(Hietogram):
    """A shape of a design storm: the rain grows as a power of the step."""

    def __init__(self, growth=1.0):
        self.growth = growth

    def generate(self, total_mm, duration_min, timestep_min=5.0):
        count = self._validate_params(total_mm, duration_min, timestep_min)
        weights = np.arange(1, count + 1) ** self.growth
        return HietogramResult(
            times_min=np.arange(1, count + 1) * timestep_min,
            intensities_mm=total_mm * weights / weights.sum(),
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
        )


class Share:
    """A runoff model: a share of the rain leaves in the step that it fell in."""

    model = "share-of-rain"

    def __init__(self, share):
        self.share = share

    def validate(self, watershed):
        pass

    def hydrograph(self, rainfall, watershed, timestep_min):
        depth_m = rainfall.intensities_mm * self.share / 1000.0
        flow = depth_m * watershed.area_km2 * 1e6 / (timestep_min * 60.0)
        return Hydrograph(np.arange(len(flow) + 1) * timestep_min, np.append(flow, 0.0))

    def describe(self, watershed=None, rainfall=None):
        from hydrolog.routing import Parameter

        return [Parameter("share", self.share, None, "given")]

    def to_document(self):
        return {"model": self.model, "share": self.share}

    @classmethod
    def from_document(cls, document):
        return cls(document["share"])
