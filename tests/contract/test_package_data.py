"""Package data is read from the installed package, not from the source tree."""

from importlib import resources

DATA = resources.files("hydrolog")


def test_marker_py_typed_ships_with_the_package():
    assert (DATA / "py.typed").is_file()


def test_agent_guide_templates_are_readable_as_package_data():
    templates = [
        entry.name for entry in (DATA / "_data" / "agents").iterdir() if entry.is_file()
    ]

    assert templates
    for name in templates:
        text = (DATA / "_data" / "agents" / name).read_text(encoding="utf-8")
        assert text.strip(), name
