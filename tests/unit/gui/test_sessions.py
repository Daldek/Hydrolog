"""Sessions of the GUI server: names, paths, work directories, limits (plan D7)."""

import hashlib
import os
import stat
import sys

import pytest

from hydrolog.catalog import get_command
from hydrolog.exceptions import ConflictError, ForbiddenPathError
from hydrolog.gui._sessions import (
    Limits,
    Sessions,
    check_name,
    relative_paths,
    split_path,
)

posix_modes = pytest.mark.skipif(
    sys.platform == "win32", reason="Windows has no POSIX file modes"
)


class Clock:
    """A clock the test moves."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def sessions(tmp_path, clock):
    created = Sessions(work_root=tmp_path / "work", limits=Limits(), clock=clock)
    yield created
    created.close()


@pytest.mark.parametrize(
    "name",
    ["x.csv", "Kamiennik 1998-2023.csv", "a", "A_b-c.d e", "9" * 128, "com10", "conx"],
)
def test_names_of_the_rule_are_accepted(name):
    assert check_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".hidden",
        "-dash",
        " space",
        "a/b",
        "a\\b",
        "..",
        "x" * 129,
        "łódź.csv",
        "tab\t.csv",
        "name.",
        "name ",
        "CON",
        "nul.txt",
        "Com1.csv",
        "lpt9",
        "aux .md",
    ],
)
def test_names_outside_the_rule_or_reserved_by_windows_are_refused(name):
    assert not check_name(name)


@pytest.mark.parametrize(
    ("value", "split"),
    [
        ("in/x.csv", ("in", ("x.csv",))),
        ("out/y.md", ("out", ("y.md",))),
        ("out/net/A.csv", ("out", ("net", "A.csv"))),
    ],
)
def test_paths_of_the_page_split_into_area_and_names(value, split):
    assert split_path(value) == split


@pytest.mark.parametrize(
    "value",
    [
        "x.csv",
        "in",
        "in/",
        "tmp/x.csv",
        "/etc/passwd",
        "in/../x.csv",
        "in/./x.csv",
        "in//x.csv",
        "in\\x.csv",
        "IN/x.csv",
        "C:/x.csv",
        "in/" + "/".join(["d"] * 9),
    ],
)
def test_other_paths_do_not_split(value):
    assert split_path(value) is None


def test_a_new_session_has_its_directories(sessions):
    session = sessions.create()

    assert session.directory == sessions.root / session.id
    assert (session.directory / "in").is_dir()
    assert (session.directory / "out").is_dir()
    assert sessions.get(session.id) is session


@posix_modes
def test_session_directories_are_private(tmp_path):
    owned = Sessions(work_root=None, limits=Limits())
    try:
        session = owned.create()
        for path in (owned.root, session.directory, session.directory / "in"):
            assert stat.S_IMODE(path.stat().st_mode) == 0o700, path
    finally:
        owned.close()


@pytest.mark.parametrize("value", [None, "", "x", "../../etc", "A" * 42, "A" * 44])
def test_ids_that_are_not_session_ids_find_nothing(sessions, value):
    sessions.create()

    assert sessions.get(value) is None


def test_the_least_recently_used_idle_session_makes_room(tmp_path, clock):
    sessions = Sessions(work_root=tmp_path, limits=Limits(sessions=2), clock=clock)
    first = sessions.create()
    clock.now += 1
    second = sessions.create()
    clock.now += 1
    sessions.get(first.id)  # used again: the second is now the least recent

    third = sessions.create()

    assert sessions.get(second.id) is None
    assert not second.directory.exists()
    assert sessions.get(first.id) is first
    assert sessions.get(third.id) is third


def test_a_busy_session_is_not_removed_to_make_room(tmp_path, clock):
    sessions = Sessions(work_root=tmp_path, limits=Limits(sessions=1), clock=clock)
    busy = sessions.create()

    with busy.use(), pytest.raises(ConflictError) as raised:
        sessions.create()

    assert raised.value.details["reason"] == "too_many_sessions"
    assert sessions.get(busy.id) is busy
    assert sessions.create() is not busy  # idle again: it makes room


def test_idle_sessions_end_after_the_idle_time(sessions, clock):
    idle = sessions.create()
    busy = sessions.create()
    clock.now += Limits().idle_s - 1
    assert sessions.get(idle.id) is idle  # used again: its idle time restarts

    clock.now += Limits().idle_s + 1
    with busy.use():
        sessions.sweep()
        assert sessions.get(busy.id) is busy

    assert sessions.get(idle.id) is None
    assert not idle.directory.exists()


def test_closing_removes_the_sessions_and_keeps_a_given_root(sessions):
    session = sessions.create()

    sessions.close()

    assert not session.directory.exists()
    assert sessions.root.is_dir()
    assert list(sessions.root.iterdir()) == []
    with pytest.raises(ConflictError):
        sessions.create()


def test_closing_removes_a_root_created_by_the_sessions():
    owned = Sessions(work_root=None, limits=Limits())
    owned.create()

    owned.close()

    assert not owned.root.exists()
    assert owned.root.name.startswith(f"hydrolog-gui-{os.getpid()}-")


def test_the_files_of_a_session_are_listed_with_their_hashes(sessions):
    session = sessions.create()
    (session.directory / "in" / "a.csv").write_bytes(b"q\n1\n")
    (session.directory / "out" / "net").mkdir()
    (session.directory / "out" / "net" / "A.csv").write_bytes(b"x")
    (session.directory / "in" / ".upload-0123").write_bytes(b"partial")

    files = session.files()

    assert files == [
        {
            "path": "in/a.csv",
            "size_bytes": 4,
            "sha256": hashlib.sha256(b"q\n1\n").hexdigest(),
        },
        {
            "path": "out/net/A.csv",
            "size_bytes": 1,
            "sha256": hashlib.sha256(b"x").hexdigest(),
        },
    ]
    assert session.usage() == (5, 2)


def test_a_changed_file_is_hashed_again(sessions):
    session = sessions.create()
    path = session.directory / "in" / "a.csv"
    path.write_bytes(b"1")
    session.files()

    path.write_bytes(b"22")

    assert session.files()[0]["sha256"] == hashlib.sha256(b"22").hexdigest()


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links need a privilege")
def test_links_are_not_files_of_a_session(sessions, tmp_path):
    session = sessions.create()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (session.directory / "in" / "link.txt").symlink_to(secret)

    assert session.files() == []
    assert session.usage() == (0, 0)


def test_paths_of_the_page_become_paths_of_the_session(sessions):
    session = sessions.create()
    command = get_command("route lag")

    options = session.command_options(
        command,
        {"input_file": "in/flood.csv", "output": "out/outflow.csv", "lag_min": 10},
    )

    assert options == {
        "input_file": str(session.directory / "in" / "flood.csv"),
        "output": str(session.directory / "out" / "outflow.csv"),
        "lag_min": 10,
    }


def test_a_command_may_read_what_another_wrote(sessions):
    session = sessions.create()

    options = session.command_options(
        get_command("route lag"), {"input_file": "out/outflow.csv"}
    )

    assert options["input_file"] == str(session.directory / "out" / "outflow.csv")


@pytest.mark.parametrize(
    "value", ["/etc/passwd", "../x.csv", "in/../../x.csv", "flood.csv", "in/d/x.csv"]
)
def test_paths_outside_the_session_are_forbidden(sessions, value):
    session = sessions.create()

    with pytest.raises(ForbiddenPathError) as raised:
        session.command_options(get_command("route lag"), {"input_file": value})

    assert raised.value.code == "forbidden"
    assert raised.value.details["option"] == "input_file"
    assert raised.value.details["reason"] == "outside_session"
    assert raised.value.details["value"] == value


def test_a_command_writes_only_into_out(sessions):
    session = sessions.create()

    with pytest.raises(ForbiddenPathError) as raised:
        session.command_options(get_command("route lag"), {"output": "in/x.csv"})

    assert raised.value.details["reason"] == "output_area"


def test_values_that_are_not_paths_are_left_to_the_catalog(sessions):
    session = sessions.create()
    given = {"input_file": 5, "lag_min": "/etc/passwd"}

    assert session.command_options(get_command("route lag"), given) == given


def test_paths_inside_the_session_become_relative(tmp_path):
    root = str(tmp_path / "session")
    sep = os.sep
    document = {
        "inputs": {"input_file": f"{root}{sep}in{sep}a.csv", "lag_min": 10.0},
        "files": [{"path": f"{root}{sep}out{sep}o.csv"}],
        "allowed_dirs": [root],
        "message": f"No such file: {root}{sep}in{sep}b.csv (in {root})",
        "other": "/elsewhere/x.csv",
        "values": [1.0, None, True],
    }

    assert relative_paths(document, root) == {
        "inputs": {"input_file": "in/a.csv", "lag_min": 10.0},
        "files": [{"path": "out/o.csv"}],
        "allowed_dirs": ["."],
        "message": f"No such file: in{sep}b.csv (in .)",
        "other": "/elsewhere/x.csv",
        "values": [1.0, None, True],
    }


def test_the_limits_of_the_plan(tmp_path):
    assert Limits().to_dict() == {
        "file_bytes": 20 * 2**20,
        "session_bytes": 100 * 2**20,
        "session_files": 200,
        "request_bytes": 5 * 2**20,
        "sessions": 64,
        "idle_s": 12 * 3600.0,
        "name_pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$",
    }
