"""Tests for the atomic writing shared by the three writers of the library.

``report generate``, ``soil hsg`` and ``commands guide --path`` write their file aside
and rename it over the target. The MCP server runs the calls in worker threads of one
process, so two calls may write the same file: the temporary name used to hold only
the process id (report, HSG raster), and the second call then failed with
``[Errno 2] No such file or directory: '.<name>.<pid>.tmp'`` after the first one had
renamed the shared file (the reviewers saw 16 failures in 40 pairs of calls for the
report and 10 in 30 for the raster).
"""

import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest

from hydrolog._atomic import STAGING_NAME, atomic_output, staging_directory
from hydrolog.catalog import run_command
from hydrolog.exceptions import HydrologError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

concurrent = pytest.mark.skipif(
    sys.platform == "win32",
    reason="renaming over a file that another thread is reading is refused on Windows",
)


class TestAtomicOutput:
    """The helper: a unique temporary file beside the target, renamed on success."""

    def test_the_content_appears_at_the_target_and_nothing_else_is_left(self, tmp_path):
        target = tmp_path / "report.md"

        with atomic_output(target) as temporary:
            temporary.write_text("new", encoding="utf-8")
            assert not target.exists()  # nothing is visible before the rename

        assert target.read_text(encoding="utf-8") == "new"
        assert [path.name for path in tmp_path.iterdir()] == ["report.md"]

    def test_the_temporary_file_is_a_hidden_sibling_of_the_target(self, tmp_path):
        target = tmp_path / "report.md"

        with atomic_output(target) as temporary:
            temporary.write_text("new", encoding="utf-8")
            assert temporary.parent == tmp_path
            assert temporary.name.startswith(".report.md.")
            assert temporary.name.endswith(".tmp")

    def test_an_existing_file_stays_until_the_block_succeeds(self, tmp_path):
        target = tmp_path / "report.md"
        target.write_text("old", encoding="utf-8")

        with atomic_output(target) as temporary:
            temporary.write_text("new", encoding="utf-8")
            assert target.read_text(encoding="utf-8") == "old"

        assert target.read_text(encoding="utf-8") == "new"

    def test_a_failing_block_keeps_the_old_file_and_removes_the_temporary_one(
        self, tmp_path
    ):
        target = tmp_path / "report.md"
        target.write_text("old", encoding="utf-8")

        with (
            pytest.raises(RuntimeError, match="boom"),
            atomic_output(target) as temporary,
        ):
            temporary.write_text("partial", encoding="utf-8")
            raise RuntimeError("boom")

        assert target.read_text(encoding="utf-8") == "old"
        assert [path.name for path in tmp_path.iterdir()] == ["report.md"]

    def test_missing_directories_are_created(self, tmp_path):
        target = tmp_path / "a" / "b" / "report.md"

        with atomic_output(target) as temporary:
            temporary.write_text("new", encoding="utf-8")

        assert target.read_text(encoding="utf-8") == "new"

    def test_a_directory_that_cannot_be_created_is_an_oserror(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed", encoding="utf-8")

        with pytest.raises(OSError), atomic_output(blocker / "report.md"):
            pytest.fail("the block must not run")

    def test_calls_in_several_threads_get_their_own_temporary_files(self, tmp_path):
        """All the temporary files exist at the same moment: their names differ.

        With a name made of the process id only (the former scheme) every thread would
        write, and then rename, the same file.
        """
        target = tmp_path / "report.md"
        workers = 8
        all_inside = threading.Barrier(workers, timeout=30)
        names: list[Path] = []
        errors: list[BaseException] = []

        def write() -> None:
            try:
                with atomic_output(target) as temporary:
                    temporary.write_text(threading.current_thread().name)
                    all_inside.wait()
                    names.append(temporary)
            except BaseException as exc:  # noqa: BLE001 - reported by the assertion
                errors.append(exc)

        threads = [
            threading.Thread(target=write, name=f"writer-{n}") for n in range(workers)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []
        assert len(set(names)) == workers
        assert [path.name for path in tmp_path.iterdir()] == ["report.md"]
        assert target.read_text() in {f"writer-{n}" for n in range(workers)}


def _race(command, options_of, tmp_path, *, workers=4, rounds=12):
    """Errors of ``workers`` threads that run ``command`` on one output at once.

    Each round uses a new directory, so the calls of a round race for one target and
    the rounds do not influence each other.
    """
    errors = []
    outputs = []
    for number in range(rounds):
        output = tmp_path / f"round{number}" / "output"
        outputs.append(output)
        start = threading.Barrier(workers, timeout=30)

        def call(target=output, barrier=start) -> None:
            barrier.wait()
            try:
                run_command(command, options_of(target))
            except HydrologError as exc:
                errors.append(f"{type(exc).__name__}: {exc}")

        threads = [threading.Thread(target=call) for _ in range(workers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    return errors, outputs


@concurrent
class TestConcurrentWriters:
    """Four threads replace the same file at once (``force``), as MCP calls do."""

    def test_report_generate(self, tmp_path):
        def options(target):
            return {
                "output": str(target.with_suffix(".md")),
                "force": True,
                "area_km2": 45.0,
                "cn": 72,
                "tc_min": 90.0,
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
            }

        errors, outputs = _race("report generate", options, tmp_path)

        assert errors == []
        for output in outputs:
            report = output.with_suffix(".md")
            assert report.read_text(encoding="utf-8").startswith("# Raport")
            assert [path.name for path in report.parent.iterdir()] == [report.name]

    def test_commands_guide(self, tmp_path):
        errors, outputs = _race(
            "commands guide",
            lambda target: {"format": "llms", "output": str(target), "force": True},
            tmp_path,
        )

        assert errors == []
        for output in outputs:
            assert output.read_text(encoding="utf-8").startswith("# Hydrolog")
            assert [path.name for path in output.parent.iterdir()] == [output.name]

    def test_soil_hsg(self, tmp_path):
        rasterio = pytest.importorskip("rasterio")
        pytest.importorskip("pyproj")

        def options(target):
            return {
                "clay_path": str(FIXTURES / "hsg_clay.tif"),
                "sand_path": str(FIXTURES / "hsg_sand.tif"),
                "silt_path": str(FIXTURES / "hsg_silt.tif"),
                "output": str(target.with_suffix(".tif")),
                "force": True,
            }

        errors, outputs = _race("soil hsg", options, tmp_path)

        assert errors == []
        with rasterio.open(FIXTURES / "hsg_result.tif") as reference:
            expected = reference.read(1)
        for output in outputs:
            raster = output.with_suffix(".tif")
            with rasterio.open(raster) as written:
                np.testing.assert_array_equal(written.read(1), expected)
            assert [path.name for path in raster.parent.iterdir()] == [raster.name]


class TestStagingDirectory:
    """A write of several files stages them first and leaves nothing of its own."""

    def test_the_staging_is_a_new_directory_of_the_run_inside_the_output_directory(
        self, tmp_path
    ):
        with staging_directory(tmp_path / "out") as staging:
            assert staging.parent == tmp_path / "out" / STAGING_NAME
            assert staging.is_dir()
            assert list(staging.iterdir()) == []
            host, pid, token = staging.name.rsplit("_", 2)
            assert (pid, len(token)) == (str(os.getpid()), 8)
            assert host

    def test_it_is_removed_with_its_parent_when_the_block_ends(self, tmp_path):
        with staging_directory(tmp_path / "out") as staging:
            (staging / "a.csv").write_text("x", encoding="utf-8")

        assert list((tmp_path / "out").iterdir()) == []  # the directory stays, empty

    def test_it_is_removed_after_an_error_and_after_an_interrupt(self, tmp_path):
        for error in (RuntimeError("boom"), KeyboardInterrupt()):
            with (
                pytest.raises(type(error)),
                staging_directory(tmp_path) as staging,
            ):
                (staging / "a.csv").write_text("x", encoding="utf-8")
                raise error

            assert list(tmp_path.iterdir()) == []

    def test_a_file_moved_into_place_stays_when_the_block_ends(self, tmp_path):
        with staging_directory(tmp_path) as staging:
            (staging / "a.csv").write_text("x", encoding="utf-8")
            os.replace(staging / "a.csv", tmp_path / "a.csv")

        assert [path.name for path in tmp_path.iterdir()] == ["a.csv"]

    def test_two_runs_in_one_directory_do_not_meet(self, tmp_path):
        with staging_directory(tmp_path) as first:
            with staging_directory(tmp_path) as second:
                assert first != second
            assert first.is_dir()  # the other run's end does not remove its staging

        assert list(tmp_path.iterdir()) == []

    def test_the_leftover_of_a_killed_run_goes_after_a_day_and_a_fresh_one_stays(
        self, tmp_path
    ):
        parent = tmp_path / STAGING_NAME
        old, fresh = parent / "host_1_old", parent / "host_2_fresh"
        for leftover in (old, fresh):
            leftover.mkdir(parents=True)
            (leftover / "a.csv").write_text("x", encoding="utf-8")
        two_days_ago = time.time() - 2 * 24 * 3600.0
        os.utime(old, (two_days_ago, two_days_ago))

        with staging_directory(tmp_path):
            assert not old.exists()
            assert fresh.is_dir()

        assert fresh.is_dir()  # still there: the parent is not empty

    def test_nothing_but_the_staging_is_created_or_deleted(self, tmp_path):
        (tmp_path / "keep.csv").write_text("x", encoding="utf-8")

        with staging_directory(tmp_path):
            pass

        assert [path.name for path in tmp_path.iterdir()] == ["keep.csv"]
