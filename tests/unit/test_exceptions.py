"""Tests for the error registry, exception classes and the error document."""

import json
import pickle
from pathlib import PurePosixPath

import numpy as np
import pytest

from hydrolog.exceptions import (
    ERROR_CODES,
    ERROR_SCHEMA,
    CalculationError,
    ErrorSpec,
    ForbiddenPathError,
    HydrologError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
    error_document,
)

SPEC_TABLE = {
    "validation_error": 2,
    "not_found": 3,
    "calculation_error": 4,
    "data_error": 7,
    "missing_dependency": 6,
    "forbidden": 8,
    "io_error": 9,
    "internal_error": 1,
}


class TestErrorCodes:
    """Tests for the closed registry ``ERROR_CODES``."""

    def test_registry_has_exactly_the_codes_and_exit_codes_of_the_spec(self):
        """The registry matches the design table (code -> exit code)."""
        assert {
            code: spec.exit_code for code, spec in ERROR_CODES.items()
        } == SPEC_TABLE

    def test_every_entry_is_keyed_by_its_own_code(self):
        """Keys and ``ErrorSpec.code`` agree."""
        for code, spec in ERROR_CODES.items():
            assert isinstance(spec, ErrorSpec)
            assert spec.code == code

    def test_exit_codes_are_distinct(self):
        """Each error code has its own exit code."""
        exit_codes = [spec.exit_code for spec in ERROR_CODES.values()]
        assert len(set(exit_codes)) == len(exit_codes)

    def test_titles_exist_in_both_languages_and_differ(self):
        """Polish and English titles are non-empty and not copies of each other."""
        for spec in ERROR_CODES.values():
            assert spec.title.strip()
            assert spec.title_en.strip()
            assert spec.title != spec.title_en

    def test_registry_is_read_only(self):
        """The registry cannot be modified at runtime."""
        with pytest.raises(TypeError):
            ERROR_CODES["new"] = ErrorSpec(  # type: ignore[index]
                "internal_error", "a", "b", 1
            )

    def test_error_spec_is_frozen(self):
        """``ErrorSpec`` entries are immutable."""
        with pytest.raises(AttributeError):
            ERROR_CODES["not_found"].exit_code = 99  # type: ignore[misc]


class TestExceptionClasses:
    """Tests for default codes and constructor behaviour."""

    @pytest.mark.parametrize(
        ("cls", "code"),
        [
            (HydrologError, "internal_error"),
            (InvalidParameterError, "validation_error"),
            (CalculationError, "calculation_error"),
            (InputDataError, "data_error"),
            (MissingDependencyError, "missing_dependency"),
            (ForbiddenPathError, "forbidden"),
            (NotFoundError, "not_found"),
            (OutputError, "io_error"),
        ],
    )
    def test_default_code_of_each_class(self, cls, code):
        """Each class carries the code of the spec table."""
        exc = cls("message")
        assert exc.code == code == cls.default_code
        assert code in ERROR_CODES

    def test_all_classes_derive_from_hydrolog_error(self):
        """Every error class can be caught as ``HydrologError``."""
        for cls in (
            InvalidParameterError,
            CalculationError,
            InputDataError,
            MissingDependencyError,
            ForbiddenPathError,
            NotFoundError,
            OutputError,
        ):
            assert issubclass(cls, HydrologError)

    def test_existing_positional_message_call_still_works(self):
        """``raise InvalidParameterError("...")`` keeps its meaning and ``str``."""
        exc = InvalidParameterError("CN must be 0-100, got 120")
        assert str(exc) == "CN must be 0-100, got 120"
        assert exc.details == {}
        assert exc.hint is None
        assert exc.code == "validation_error"

    def test_exceptions_still_catchable_with_pytest_raises_match(self):
        """The message is what ``pytest.raises(match=...)`` sees."""
        with pytest.raises(CalculationError, match="did not converge"):
            raise CalculationError("fit did not converge")

    def test_message_may_be_omitted(self):
        """A bare ``HydrologError()`` is valid, as it was before the registry."""
        assert str(HydrologError()) == ""

    def test_code_override_and_exit_code(self):
        """``code=`` replaces the class default; ``exit_code`` follows the registry."""
        exc = CalculationError("disk", code="io_error")
        assert exc.code == "io_error"
        assert exc.exit_code == 9

    def test_unknown_code_is_rejected(self):
        """A code outside the registry is a programming error."""
        with pytest.raises(ValueError, match="Unknown error code 'nope'"):
            HydrologError("x", code="nope")  # type: ignore[arg-type]

    def test_details_are_copied(self):
        """Mutating the caller's mapping afterwards does not change the exception."""
        source = {"option": "cn", "allowed": ["a"]}
        exc = InvalidParameterError("x", details=source)
        source["allowed"].append("b")
        source["option"] = "other"
        assert exc.details == {"option": "cn", "allowed": ["a"]}

    def test_hint_and_details_survive_pickling(self):
        """Errors cross process boundaries intact (multiprocessing, MCP workers)."""
        exc = NotFoundError("gone", details={"path": "/x"}, hint="Look elsewhere.")
        clone = pickle.loads(pickle.dumps(exc))
        assert type(clone) is NotFoundError
        assert (str(clone), clone.code, clone.details, clone.hint) == (
            "gone",
            "not_found",
            {"path": "/x"},
            "Look elsewhere.",
        )


class TestValueErrorCompatibility:
    """``InvalidParameterError`` is a ``ValueError`` (and only it is)."""

    def test_invalid_parameter_error_is_a_value_error(self):
        """Code written for the plain ``ValueError`` of older versions keeps working."""
        with pytest.raises(ValueError, match="CN must be 0-100"):
            raise InvalidParameterError("CN must be 0-100, got 120")

    def test_other_hydrolog_errors_are_not_value_errors(self):
        """``except ValueError`` must not swallow calculation or file-system errors."""
        for cls in (
            CalculationError,
            InputDataError,
            MissingDependencyError,
            ForbiddenPathError,
            NotFoundError,
            OutputError,
        ):
            assert not issubclass(cls, ValueError), cls.__name__
        assert not issubclass(HydrologError, ValueError)

    def test_a_value_error_hydrolog_error_is_not_reported_as_a_bug(self):
        """The document checks ``HydrologError`` before the foreign-exception
        branch, so the ``ValueError`` base does not turn it into ``internal_error``."""
        exc = InvalidParameterError("bad", details={"option": "cn"}, hint="Use 0-100.")
        doc = error_document(exc, command="cn lookup")
        assert doc["code"] == "validation_error"
        assert doc["exit_code"] == 2
        assert doc["details"] == {"option": "cn"}
        assert doc["hint"] == "Use 0-100."

    def test_pickling_keeps_class_and_value_error_nature(self):
        exc = InvalidParameterError("bad", details={"option": "cn"}, hint="h")
        clone = pickle.loads(pickle.dumps(exc))
        assert type(clone) is InvalidParameterError
        assert isinstance(clone, ValueError)
        assert (str(clone), clone.code, clone.details, clone.hint) == (
            "bad",
            "validation_error",
            {"option": "cn"},
            "h",
        )


class TestErrorDocument:
    """Tests for ``error_document`` (``hydrolog-error/1``)."""

    def test_hydrolog_error_document_has_all_keys(self):
        """The document carries the keys of the spec, filled from the exception."""
        exc = InvalidParameterError(
            "Option 'cn': must be <= 100, got 120",
            details={"option": "cn", "reason": "maximum", "maximum": 100, "value": 120},
            hint="Use 0-100.",
        )
        doc = error_document(exc, command="cn lookup", lang="en")
        assert list(doc) == [
            "schema",
            "code",
            "title",
            "message",
            "hint",
            "details",
            "exit_code",
            "command",
        ]
        assert doc == {
            "schema": "hydrolog-error/1",
            "code": "validation_error",
            "title": "Invalid input",
            "message": "Option 'cn': must be <= 100, got 120",
            "hint": "Use 0-100.",
            "details": {
                "option": "cn",
                "reason": "maximum",
                "maximum": 100,
                "value": 120,
            },
            "exit_code": 2,
            "command": "cn lookup",
        }
        assert doc["schema"] == ERROR_SCHEMA

    def test_title_follows_language(self):
        """``lang`` selects the Polish or the English registry title."""
        exc = NotFoundError("no such command")
        assert error_document(exc)["title"] == ERROR_CODES["not_found"].title
        assert error_document(exc, lang="pl")["title"] == "Nie znaleziono"
        assert error_document(exc, lang="en")["title"] == "Not found"

    def test_command_defaults_to_none_and_hint_to_none(self):
        """Missing command and hint are explicit ``None`` values."""
        doc = error_document(CalculationError("no convergence"))
        assert doc["command"] is None
        assert doc["hint"] is None
        assert doc["details"] == {}
        assert doc["exit_code"] == 4

    @pytest.mark.parametrize(
        "exc", [ValueError("boom"), TypeError("bad"), KeyError("k")]
    )
    def test_foreign_exception_is_an_internal_error(self, exc):
        """Non-Hydrolog exceptions are bugs: ``internal_error`` with the class name."""
        doc = error_document(exc, command="tc kirpich")
        assert doc["code"] == "internal_error"
        assert doc["exit_code"] == 1
        assert doc["message"].startswith(type(exc).__name__ + ": ")
        assert doc["details"] == {"exception": type(exc).__name__}
        assert doc["hint"]
        assert doc["command"] == "tc kirpich"

    def test_os_error_is_reported_as_io_error_with_path(self):
        """A leaked file-system error is ``io_error``, not a bug report."""
        exc = PermissionError(13, "Permission denied", "/data/out.json")
        doc = error_document(exc)
        assert doc["code"] == "io_error"
        assert doc["exit_code"] == 9
        assert doc["message"] == "Permission denied: /data/out.json"
        assert doc["details"] == {"errno": "EACCES", "path": "/data/out.json"}

    def test_os_error_without_errno_or_path(self):
        """A bare ``OSError`` still gives a readable message and no invented details."""
        doc = error_document(OSError("disk on fire"))
        assert doc["code"] == "io_error"
        assert doc["message"] == "disk on fire"
        assert doc["details"] == {}

    def test_details_are_made_json_compatible(self):
        """NumPy scalars and paths in ``details`` serialize without loss of meaning."""
        exc = InvalidParameterError(
            "x",
            details={
                "value": np.float64(2.5),
                "count": np.int64(3),
                "path": PurePosixPath("/a/b"),
                "bad": float("nan"),
                "allowed": ("a", "b"),
            },
        )
        doc = error_document(exc)
        assert doc["details"] == {
            "value": 2.5,
            "count": 3,
            "path": "/a/b",
            "bad": None,
            "allowed": ["a", "b"],
        }
        json.dumps(doc, allow_nan=False)

    def test_unserializable_details_fall_back_to_text(self):
        """Reporting an error never fails because of an odd ``details`` value."""
        exc = HydrologError("x", details={"obj": object, "n": 1})
        doc = error_document(exc)
        assert doc["details"]["n"] == 1
        assert isinstance(doc["details"]["obj"], str)
        json.dumps(doc)

    def test_unknown_language_is_rejected(self):
        """Only ``pl`` and ``en`` exist."""
        with pytest.raises(ValueError, match="Unknown language 'de'"):
            error_document(NotFoundError("x"), lang="de")  # type: ignore[arg-type]
