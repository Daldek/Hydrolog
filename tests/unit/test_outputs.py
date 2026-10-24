"""Tests for the output plan of the writing commands (``plan_outputs`` and friends)."""

from __future__ import annotations

from pathlib import Path

import pytest

from hydrolog.exceptions import ConflictError
from hydrolog.operations._outputs import (
    PLAN_SCHEMA,
    conflict_error,
    plan_output,
    plan_outputs,
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
