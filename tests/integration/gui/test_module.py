"""The GUI as a module of Nogat's GUI platform: the ``nogat.gui`` entry point (D4)."""

import dataclasses
import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

import pytest

import hydrolog.gui
from hydrolog.gui import GuiModule, create_app, gui_module


def test_the_entry_point_loads_the_module_description():
    (entry,) = entry_points(group="nogat.gui", name="hydrolog")

    module = entry.load()()

    assert module == GuiModule(
        name="hydrolog",
        title="Hydrolog",
        web=Path(hydrolog.gui.__file__).resolve().parent / "web",
        index="index.html",
        sections=(
            ("hydrogram", "Hydrogram zlewni"),
            ("siec", "Sieć i trasowanie"),
            ("statystyka", "Statystyka przepływów"),
            ("kalkulatory", "Kalkulatory"),
            ("polecenia", "Wszystkie polecenia"),
        ),
        app=create_app,
    )


def test_the_description_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        gui_module().name = "other"  # type: ignore[misc]


def test_describing_the_module_imports_no_web_or_numerical_library():
    script = (
        "import sys\n"
        "from importlib.metadata import entry_points\n"
        "(entry,) = entry_points(group='nogat.gui', name='hydrolog')\n"
        "entry.load()()\n"
        "print(sorted({'starlette', 'uvicorn', 'numpy'} & set(sys.modules)))\n"
    )

    shown = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout

    assert shown.strip() == "[]"
