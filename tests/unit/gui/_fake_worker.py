"""A stand-in for the GUI worker: its protocol, without Hydrolog's libraries.

The runner's tests start it instead of ``hydrolog.gui._worker`` (it starts in
milliseconds). Commands:

* ``echo`` -- answers an ``ok`` envelope whose result holds the worker's ``pid``, the
  ``options`` and the thread variables of its environment;
* ``sleep`` -- waits ``seconds``, then answers like ``echo``;
* ``wait`` -- waits until the file ``release`` exists, then answers like ``echo``;
* ``exit`` -- ends the process with the exit code ``code``.

Every request is appended to the file named by ``FAKE_WORKER_LOG`` (if set). With
``FAKE_WORKER_BROKEN`` set, the worker ends before it is ready.
"""

import json
import os
import sys
import time
from pathlib import Path

THREAD_VARIABLES = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


def main() -> None:
    out = sys.stdout.buffer

    def send(message: dict) -> None:
        out.write(json.dumps(message).encode("utf-8") + b"\n")
        out.flush()

    if os.environ.get("FAKE_WORKER_BROKEN"):
        sys.exit(3)
    send({"ready": True, "pid": os.getpid()})
    for line in sys.stdin.buffer:
        request = json.loads(line)
        options = request["options"]
        log = os.environ.get("FAKE_WORKER_LOG")
        if log:
            with open(log, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(request) + "\n")
        command = request["command"]
        if command == "exit":
            os._exit(options["code"])
        if command == "sleep":
            time.sleep(options["seconds"])
        if command == "wait":
            while not Path(options["release"]).exists():
                time.sleep(0.01)
        result = {
            "schema": "fake-echo/1",
            "pid": os.getpid(),
            "options": options,
            "environment": {name: os.environ.get(name) for name in THREAD_VARIABLES},
        }
        envelope = {
            "schema": "hydrolog-result/1",
            "tool": "hydrolog",
            "version": "0",
            "command": command,
            "check": request["check"],
            "status": "ok",
            "result": result,
            "notices": [],
        }
        send({"document": envelope, "error": False})


if __name__ == "__main__":
    main()
