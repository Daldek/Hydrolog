"""The GUI worker with a slow ``tc kirpich``: it first sleeps ``length_km`` seconds.

The tests of the timeout and of the newest run need runs that take long; this is
``hydrolog.gui._worker`` with that one operation slowed down, started by the app when
``hydrolog.gui._runner.WORKER_MODULE`` names this module.
"""

import time
from typing import Any

import hydrolog.operations
from hydrolog.gui import _worker

_kirpich = hydrolog.operations.tc_kirpich


def _slow_kirpich(**options: Any) -> Any:
    time.sleep(options["length_km"])
    return _kirpich(**options)


hydrolog.operations.tc_kirpich = _slow_kirpich  # type: ignore[assignment]

if __name__ == "__main__":
    _worker.main()
