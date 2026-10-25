"""Tests for the output plan of the writing commands (``plan_outputs`` and friends)."""

from __future__ import annotations

from pathlib import Path

import pytest

from hydrolog.exceptions import ConflictError, InvalidParameterError
from hydrolog.operations._outputs import (
    PLAN_SCHEMA,
    STORE_MARKERS,
    conflict_error,
    plan_directory,
    plan_output,
    plan_outputs,
    refuse_input_as_output,
    store_around,
)
from hydrolog.operations.meta import commands_guide


def _actions(plan) -> list[str]:
    return [item.action for item in plan.targets]


class TestPlanOutputs:
    """What would happen to each target."""

    def test_a_new_file_is_written(self, tmp_path):
        plan = plan_outputs({"output": tmp_path / "new.md"}, force=False)
        assert _actions(plan) == ["write"]
        assert plan.targets[0].path == str(tmp_path / "new.md")
        assert plan.targets[0].reason is None
        assert plan.conflicts == ()
        assert plan.replaced == ()

    def test_an_existing_file_is_a_conflict_without_force(self, tmp_path):
        target = tmp_path / "old.md"
        target.write_text("x")
        plan = plan_outputs({"output": target}, force=False)
        assert _actions(plan) == ["conflict"]
        assert plan.targets[0].reason == "output_exists"
        assert [item.path for item in plan.conflicts] == [str(target)]

    def test_an_existing_file_is_replaced_with_force(self, tmp_path):
        target = tmp_path / "old.md"
        target.write_text("x")
        plan = plan_outputs({"output": target}, force=True)
        assert _actions(plan) == ["replace"]
        assert plan.replaced == (str(target),)
        assert plan.conflicts == ()

    def test_force_does_not_matter_for_a_new_file(self, tmp_path):
        plan = plan_outputs({"output": tmp_path / "new.md"}, force=True)
        assert _actions(plan) == ["write"]
        assert plan.replaced == ()

    def test_a_directory_in_the_way_is_not_overwritten_silently(self, tmp_path):
        """A directory exists, so the target is a conflict (or a replace)."""
        assert _actions(plan_outputs({"output": tmp_path}, force=False)) == ["conflict"]

    def test_a_dangling_symlink_counts_as_existing(self, tmp_path):
        link = tmp_path / "link.md"
        try:
            link.symlink_to(tmp_path / "nowhere")
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")
        assert _actions(plan_outputs({"output": link}, force=False)) == ["conflict"]

    def test_options_that_were_not_given_are_skipped(self, tmp_path):
        plan = plan_outputs({"output": None, "other": tmp_path / "a"}, force=False)
        assert [item.option for item in plan.targets] == ["other"]
        assert plan_outputs({"output": None}, force=False).targets == ()

    def test_paths_are_made_absolute(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        plan = plan_outputs({"output": "rel/../a.md"}, force=False)
        assert plan.targets[0].path == str(tmp_path / "a.md")
        assert Path(plan.targets[0].path).is_absolute()

    def test_two_options_naming_one_file_are_a_duplicate(self, tmp_path):
        plan = plan_outputs(
            {"output": tmp_path / "a.md", "other": tmp_path / "x" / ".." / "a.md"},
            force=True,
        )
        assert _actions(plan) == ["write", "conflict"]
        assert plan.targets[1].reason == "duplicate_output_name"

    def test_planning_creates_nothing(self, tmp_path):
        target = tmp_path / "sub" / "new.md"
        plan_outputs({"output": target}, force=False)
        assert not target.parent.exists()


class TestConflictError:
    """The error of a real run with conflicts."""

    def test_no_conflict_no_error(self, tmp_path):
        assert (
            conflict_error(plan_outputs({"output": tmp_path / "a"}, force=False))
            is None
        )

    def test_every_existing_path_is_listed(self, tmp_path):
        first, second = tmp_path / "a.md", tmp_path / "b.md"
        first.write_text("1")
        second.write_text("2")
        plan = plan_outputs(
            {"output": first, "other": second, "third": tmp_path / "c.md"},
            force=False,
        )
        error = conflict_error(plan)
        assert isinstance(error, ConflictError)
        assert error.code == "conflict"
        assert error.exit_code == 4
        assert error.details == {
            "reason": "output_exists",
            "paths": [str(first), str(second)],
        }
        assert str(first) in str(error)
        assert str(second) in str(error)
        assert "--force" in error.hint

    def test_duplicate_names_come_before_existing_files(self, tmp_path):
        existing = tmp_path / "old.md"
        existing.write_text("1")
        plan = plan_outputs(
            {"output": tmp_path / "a.md", "other": tmp_path / "a.md", "x": existing},
            force=False,
        )
        error = conflict_error(plan)
        assert error is not None
        assert error.details == {
            "reason": "duplicate_output_name",
            "paths": [str(tmp_path / "a.md")],
        }

    def test_force_removes_the_existing_file_conflict(self, tmp_path):
        existing = tmp_path / "old.md"
        existing.write_text("1")
        assert conflict_error(plan_outputs({"output": existing}, force=True)) is None


class TestCheckResult:
    """The ``hydrolog-plan/1`` document of a ``check`` run."""

    def test_the_plan_is_the_result_and_nothing_is_reported_written(self, tmp_path):
        existing = tmp_path / "old.md"
        existing.write_text("1")
        plan = plan_outputs(
            {"output": existing, "other": tmp_path / "new"}, force=False
        )
        output = plan_output(plan)
        assert output.check is True
        assert output.files == ()
        assert output.result == {
            "schema": PLAN_SCHEMA,
            "targets": [
                {
                    "option": "output",
                    "path": str(existing),
                    "action": "conflict",
                    "reason": "output_exists",
                },
                {"option": "other", "path": str(tmp_path / "new"), "action": "write"},
            ],
        }

    def test_a_plan_with_a_conflict_is_still_a_result(self, tmp_path):
        """Only the real run fails; ``check`` reports the conflict."""
        existing = tmp_path / "old.md"
        existing.write_text("1")
        output = plan_output(plan_outputs({"output": existing}, force=False))
        assert output.result["targets"][0]["action"] == "conflict"

    def test_commands_guide_without_a_target_plans_nothing(self):
        """``check`` always answers with a plan, an empty one without a target."""
        output = commands_guide(format="llms", check=True)
        assert output.check is True
        assert output.result == {"schema": PLAN_SCHEMA, "targets": []}


class TestPlanDirectory:
    """The files of a directory of plain output (DEV-19.5, DEV-19.6, DEV-19.11)."""

    def test_new_files_are_written_into_the_directory_in_the_order_given(
        self, tmp_path
    ):
        plan = plan_directory(
            "output_dir", tmp_path / "out", ["B.csv", "A.csv"], force=False
        )

        assert _actions(plan) == ["write", "write"]
        assert [item.path for item in plan.targets] == [
            str(tmp_path / "out" / "B.csv"),
            str(tmp_path / "out" / "A.csv"),
        ]
        assert {item.option for item in plan.targets} == {"output_dir"}
        assert not (tmp_path / "out").exists()  # planning creates nothing

    def test_existing_files_conflict_without_force_and_are_replaced_with_it(
        self, tmp_path
    ):
        (tmp_path / "A.csv").write_text("old")

        without = plan_directory(
            "output_dir", tmp_path, ["A.csv", "B.csv"], force=False
        )
        forced = plan_directory("output_dir", tmp_path, ["A.csv", "B.csv"], force=True)

        assert _actions(without) == ["conflict", "write"]
        assert without.targets[0].reason == "output_exists"
        assert _actions(forced) == ["replace", "write"]
        assert forced.replaced == (str(tmp_path / "A.csv"),)

    def test_names_that_differ_only_in_case_are_a_duplicate(self, tmp_path):
        # a FAT, exFAT or SMB share would keep one file for the two (DEV-19.8)
        plan = plan_directory(
            "output_dir", tmp_path, ["a.csv", "B.csv", "A.CSV"], force=True
        )

        assert _actions(plan) == ["write", "write", "conflict"]
        assert plan.targets[2].reason == "duplicate_output_name"

    def test_every_conflicting_path_of_the_first_reason_is_in_the_error(self, tmp_path):
        for name in ("A.csv", "C.csv"):
            (tmp_path / name).write_text("old")

        error = conflict_error(
            plan_directory(
                "output_dir", tmp_path, ["A.csv", "B.csv", "C.csv"], force=False
            )
        )

        assert error is not None
        assert error.details == {
            "reason": "output_exists",
            "paths": [str(tmp_path / "A.csv"), str(tmp_path / "C.csv")],
        }

    def test_a_long_list_of_paths_is_shortened_in_the_message_but_not_in_the_details(
        self, tmp_path
    ):
        names = [f"n{i}.csv" for i in range(8)]
        for name in names:
            (tmp_path / name).write_text("old")

        error = conflict_error(
            plan_directory("output_dir", tmp_path, names, force=False)
        )

        assert error is not None
        assert len(error.details["paths"]) == 8
        assert "and 3 more" in str(error)
        assert str(tmp_path / "n7.csv") not in str(error)

    def test_a_duplicate_comes_before_an_existing_file_in_the_error(self, tmp_path):
        (tmp_path / "B.csv").write_text("old")

        error = conflict_error(
            plan_directory(
                "output_dir", tmp_path, ["A.csv", "a.csv", "B.csv"], force=False
            )
        )

        assert error is not None
        assert error.details == {
            "reason": "duplicate_output_name",
            "paths": [str(tmp_path / "a.csv")],
        }


class TestStoreOfAnotherTool:
    """A store is recognised by its marker file name alone (DEV-19.11, DEV-19.12)."""

    @pytest.mark.parametrize("marker", STORE_MARKERS)
    def test_the_store_root_and_every_directory_below_it_are_in_the_store(
        self, tmp_path, marker
    ):
        root = tmp_path / "store"
        (root / "versions" / "x").mkdir(parents=True)
        (root / marker).write_text("{}")

        assert store_around(root) == root.resolve()
        assert store_around(root / "versions" / "x") == root.resolve()
        assert store_around(root / "not" / "made" / "yet") == root.resolve()

    def test_a_store_below_the_directory_does_not_matter(self, tmp_path):
        (tmp_path / "data" / "kartograf").mkdir(parents=True)
        (tmp_path / "data" / "kartograf" / "kartograf-store.json").write_text("{}")

        assert store_around(tmp_path / "data") is None
        assert store_around(tmp_path / "elsewhere") is None

    def test_a_directory_in_a_store_refuses_every_file_with_the_store_in_the_error(
        self, tmp_path
    ):
        (tmp_path / "imgw-store.json").write_text("{}")
        (tmp_path / "A.csv").write_text("old")

        plan = plan_directory(
            "output_dir", tmp_path / "sub", ["A.csv", "B.csv"], force=True
        )
        error = conflict_error(plan)

        assert [(item.action, item.reason) for item in plan.targets] == [
            ("conflict", "output_in_store"),
            ("conflict", "output_in_store"),
        ]
        assert error is not None
        assert error.code == "conflict"
        assert error.details == {
            "reason": "output_in_store",
            "paths": [str(tmp_path / "sub" / "A.csv"), str(tmp_path / "sub" / "B.csv")],
            "store": str(tmp_path.resolve()),
        }
        assert "--root" in error.hint

    def test_a_link_into_a_store_is_in_the_store(self, tmp_path):
        store = tmp_path / "store"
        store.mkdir()
        (store / "kartograf-store.json").write_text("{}")
        link = tmp_path / "link"
        try:
            link.symlink_to(store, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        assert store_around(link) == store.resolve()


class TestRefuseInputAsOutputOption:
    def test_the_error_names_the_output_option_that_was_given(self, tmp_path):
        source = tmp_path / "rating.csv"
        source.write_text("x")

        with pytest.raises(InvalidParameterError) as caught:
            refuse_input_as_output(
                tmp_path / "." / "rating.csv",
                {"rating_file": source},
                option="output_dir",
            )

        assert caught.value.details == {
            "option": "output_dir",
            "reason": "conflict",
            "input": "rating_file",
        }
