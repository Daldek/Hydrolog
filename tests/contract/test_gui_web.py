"""The GUI's static files keep their contracts (GUI plan D9, D10, D16; ADR-0027).

The copies of Nogat's identity and kit and the vendored Preact and htm are
byte-identical to the SHA-256 their manifests record, and every file of ``web/nogat/``
is recorded in one of them; the pages (the app, its guide ``instrukcja/`` and the admin
page ``admin/``) load nothing remote, have no inline script, style or event handler
(CSP ``'self'``, D8) and link only files of ``web/``; the (i) texts hold no scripts,
inline styles, event attributes or remote URLs; every option and every ``one_of`` group
of the commands the GUI offers has a Polish label.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest

from hydrolog.catalog import NOTICES

WEB = Path(__file__).resolve().parents[2] / "src" / "hydrolog" / "gui" / "web"
NOGAT_COMMIT = "7786271caba188a4b3bf8a1af7bb5dc944f3b50b"
GUIS = ("archiwista", "hydrograf", "hydrolog", "obserwator")
"""The GUIs of Nogat's app menu (``GUIS`` of ``nogat-app-menu.js``): each has a mark."""
# XML namespaces are names, not resources the page loads.
NAMESPACE = re.compile(r"https?://www\.w3\.org/(2000/svg|1999/xlink|1998/Math/MathML)")
REMOTE = re.compile(r"(?:https?:)?//[A-Za-z0-9.-]+\.[A-Za-z]{2,}[/\"'\s)]")
PAGES = ["index.html", "instrukcja/index.html", "admin/index.html"]
"""The HTML pages of the GUI: the app, its guide and the admin page."""
OPTION_LABELS = WEB / "src" / "labels" / "options.js"
"""The Polish labels of the generated forms: options, a command's own, ``one_of``."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js_object(source: str, name: str) -> str:
    """The body of the top-level ``export const <name> = {...};`` of a labels file."""
    found = re.search(
        rf"^export const {name} = \{{\n(.*?)^\}};",
        source,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert found, name
    return found.group(1)


def own_files(*suffixes: str) -> list[Path]:
    """Files of the GUI written for Hydrolog (not the vendored libraries)."""
    return sorted(
        path
        for path in WEB.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and "vendor" not in path.relative_to(WEB).parts
    )


def test_nogat_copies_match_their_manifest() -> None:
    manifest = json.loads((WEB / "nogat" / "nogat.json").read_text(encoding="utf-8"))

    assert manifest["commit"] == NOGAT_COMMIT
    assert {name: sha256(WEB / "nogat" / name) for name in manifest["files"]} == {
        name: entry["sha256"] for name, entry in manifest["files"].items()
    }
    assert set(manifest["files"]) >= {
        "tokens.css",
        "marks/nogat.svg",
        *(f"marks/{name}.svg" for name in GUIS),
    }


def test_the_kit_matches_its_own_manifest() -> None:
    """The kit's files are Nogat's, byte for byte (DEV-15.6): ``nogat-kit.json``."""
    kit = json.loads((WEB / "nogat" / "nogat-kit.json").read_text(encoding="utf-8"))

    assert {name: sha256(WEB / "nogat" / name) for name in kit["files"]} == kit["files"]


def test_every_file_of_the_nogat_folder_is_a_recorded_copy() -> None:
    folder = WEB / "nogat"
    manifest = json.loads((folder / "nogat.json").read_text(encoding="utf-8"))
    kit = json.loads((folder / "nogat-kit.json").read_text(encoding="utf-8"))
    present = {
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file()
    }

    assert present == {
        "nogat.json",
        "nogat-kit.json",
        *manifest["files"],
        *kit["files"],
    }


def test_tokens_copy_names_its_nogat_commit() -> None:
    header = (WEB / "nogat" / "tokens.css").read_text(encoding="utf-8").splitlines()[0]

    assert NOGAT_COMMIT[:7] in header


def test_vendored_libraries_match_their_manifest() -> None:
    manifest = json.loads((WEB / "vendor" / "vendor.json").read_text(encoding="utf-8"))
    files = {
        name: entry
        for library in manifest["libraries"]
        for name, entry in library["files"].items()
    }

    assert {name: sha256(WEB / "vendor" / name) for name in files} == {
        name: entry["sha256"] for name, entry in files.items()
    }
    assert {library["name"] for library in manifest["libraries"]} == {"preact", "htm"}
    assert all(
        (WEB / "vendor" / lib["license_file"]).is_file()
        for lib in manifest["libraries"]
    )


def test_the_page_loads_nothing_remote() -> None:
    # nogat.json records where the copies came from; the page never reads it.
    found = [
        f"{path.relative_to(WEB)}: {match.group(0)}"
        for path in own_files(".html", ".css", ".js", ".json", ".svg")
        if path.name != "nogat.json"
        for match in REMOTE.finditer(
            NAMESPACE.sub("", path.read_text(encoding="utf-8"))
        )
    ]

    assert found == []


@pytest.mark.parametrize("name", PAGES)
def test_the_page_has_no_inline_script_style_or_handler(name: str) -> None:
    page = (WEB / name).read_text(encoding="utf-8")
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", page, flags=re.DOTALL)

    assert scripts and all(
        "src=" in attrs and not body.strip() for attrs, body in scripts
    )
    assert "<style" not in page
    assert not re.search(r"\sstyle\s*=", page)
    assert not re.search(r"\son[a-z]+\s*=", page)


@pytest.mark.parametrize("name", PAGES)
def test_every_local_file_the_page_links_exists(name: str) -> None:
    page = (WEB / name).read_text(encoding="utf-8")
    linked = re.findall(r'(?:src|href)="([^"#?]+)"', page)
    # A link to a directory is served its index.html (StaticFiles, html=True)
    targets = [(WEB / name).parent.joinpath(link).resolve() for link in linked]
    missing = [
        link
        for link, target in zip(linked, targets, strict=True)
        if not target.is_relative_to(WEB)
        or not (target.is_file() or (target / "index.html").is_file())
    ]

    assert linked and missing == []


@pytest.mark.parametrize(
    "pattern",
    [r"<script", r"\sstyle\s*=", r"\son[a-z]+\s*=", r"javascript:", r"https?://"],
)
def test_info_texts_hold_only_trusted_markup(pattern: str) -> None:
    texts = sorted((WEB / "src" / "labels" / "info").glob("*.js"))

    assert [
        path.name
        for path in texts
        if re.search(
            pattern, NAMESPACE.sub("", path.read_text(encoding="utf-8")), re.IGNORECASE
        )
    ] == []


def test_every_notice_code_has_polish_text() -> None:
    """Every code of the NOTICES registry is worded in labels/notices.js (D16)."""
    source = (WEB / "src" / "labels" / "notices.js").read_text(encoding="utf-8")
    worded = set(re.findall(r"^\s{4}([a-z][a-z0-9_]*):", source, flags=re.MULTILINE))

    assert sorted(set(NOTICES) - worded) == []


def test_every_structure_reason_has_polish_text() -> None:
    """Every structure reason of Sieć's editor is worded in labels/siec.js (D8)."""
    graph = WEB / "src" / "sections" / "siec" / "editor" / "graph.js"
    listed = re.search(
        r"export const REASONS = Object\.freeze\(\[(.*?)\]\);",
        graph.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    labels = (WEB / "src" / "labels" / "siec.js").read_text(encoding="utf-8")
    block = re.search(
        r"^  reasons: \{\n(.*?)^  \},", labels, flags=re.DOTALL | re.MULTILINE
    )
    assert listed and block
    reasons = re.findall(r'"([a-z_]+)"', listed.group(1))
    worded = set(
        re.findall(r"^\s{4}([a-z][a-z0-9_]*):", block.group(1), flags=re.MULTILINE)
    )

    assert "cycle" in reasons
    assert sorted(set(reasons) - worded) == []


def test_every_option_and_one_of_group_of_the_gui_has_a_polish_label() -> None:
    """Every option of every command of „Wszystkie polecenia” has a Polish label, shared
    (``options``) or the command's own (``commandOptions``), and every ``one_of`` choice
    of two or more groups names each of its groups (``oneOf``), so no form shows a bare
    option name (``labels/options.js``)."""
    pytest.importorskip("starlette")
    from hydrolog import command_schema, list_commands
    from hydrolog.gui._app import EXCLUDED

    source = OPTION_LABELS.read_text(encoding="utf-8")
    key = re.compile(r"\b([a-z][a-z0-9_]*):")
    shared = set(
        re.findall(r"^  ([a-z][a-z0-9_]*):", js_object(source, "options"), re.MULTILINE)
    )
    own = {
        command: set(key.findall(body))
        for command, body in re.findall(
            r'^  "([^"]+)": \{(.*?)\},$',
            js_object(source, "commandOptions"),
            flags=re.DOTALL | re.MULTILINE,
        )
    }
    named = {
        command: re.findall(r'"([^"]+)"', groups)
        for command, groups in re.findall(
            r'^  "([^"]+)": \{ title: "[^"]+", groups: \[(.*?)\] \},$',
            js_object(source, "oneOf"),
            flags=re.MULTILINE,
        )
    }
    unlabelled: list[str] = []
    unnamed: list[str] = []
    for item in list_commands().to_dict()["commands"]:
        name = item["name"]
        if name in EXCLUDED:
            continue
        entry = command_schema(name).to_dict()["commands"][0]
        labelled = shared | own.get(name, set())
        unlabelled += [
            f"{name}: {option['name']}"
            for option in entry.get("options", [])
            if option["name"] not in labelled
        ]
        groups = entry.get("one_of") or []
        if len(groups) >= 2 and len(named.get(name, [])) != len(groups):
            unnamed.append(name)

    assert unlabelled == []
    assert unnamed == []
