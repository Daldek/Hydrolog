"""Declarations of the Hydrolog command catalog (spec section 6.1).

A :class:`Command` describes one function of :mod:`hydrolog.operations` for every
interface generated from the catalog (CLI, MCP server, agent guides); an
:class:`Option` describes one keyword argument of that function. Both are frozen
dataclasses that check their own declaration in ``__post_init__``: a wrong
declaration raises ``ValueError`` when the group module is imported, never when a
command runs.

An option also knows how to validate and normalize one value
(:meth:`Option.normalize`) and how to describe itself as JSON Schema
(:meth:`Option.json_schema`); the command-level rules (required options, ``one_of``
groups, defaults) live in :mod:`hydrolog.catalog.dispatch`.

Option types
------------
================  ==========================  ==================================
type              accepted value              normalized value
================  ==========================  ==================================
``number``        int or float (not bool)     ``float`` (finite)
``integer``       int, or float without       ``int``
                  fractional part (not bool)
``string``        non-blank ``str``           the same ``str``
``boolean``       ``bool``                    ``bool``
``choice``        ``str`` from ``choices``    the same ``str``
``number_list``   non-empty list of numbers   ``list[float]`` (bounds per item)
``string_list``   non-empty list of strings   ``list[str]``
``object_list``   non-empty list of objects   ``list[dict]`` (JSON-native)
``path``          non-blank ``str`` or        ``str`` (resolved later by
                  ``os.PathLike``             :func:`~hydrolog.catalog.run_command`)
``object``        JSON object                 ``dict`` (JSON-native deep copy)
================  ==========================  ==================================

Only JSON-native values are accepted (no numeric strings): the CLI and the MCP server
convert their text input before validation.

Notes
-----
``string_list`` and ``object_list`` extend the eight types of the design spec: they
are needed for inline dates and for inline lists of stations or network segments.
"""

from __future__ import annotations

import copy
import keyword
import math
import numbers
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Literal, NoReturn, get_args

from hydrolog.exceptions import InvalidParameterError

OptionType = Literal[
    "number",
    "integer",
    "string",
    "boolean",
    "choice",
    "number_list",
    "string_list",
    "object_list",
    "path",
    "object",
]
PathRole = Literal["input", "output"]
Cardinality = Literal["single", "bounded", "unbounded"]
Lang = Literal["pl", "en"]

OPTION_TYPES: Final[tuple[str, ...]] = get_args(OptionType)
"""Allowed values of :attr:`Option.type`."""
LANGUAGES: Final[tuple[str, ...]] = get_args(Lang)
"""Languages of catalog texts (English is authored, Polish is the translation)."""
TOOL: Final = "hydrolog"
"""Name of the tool: the prefix of every ``operation_id`` (AGI-2.2)."""
SUMMARY_MAX_CHARS: Final = 100
"""Maximum length of :attr:`Command.summary` and its Polish copy (DOC-1.7)."""
MCP_DESCRIPTION_MAX_CHARS: Final = 600
"""Maximum length of summary, description and rules together (DOC-1.7, AGI-5.3)."""
TOOL_NAME_MAX_CHARS: Final = 48
"""Maximum length of an ``operation_id``, the MCP tool name (AGI-5.2)."""
CORE_FAMILY_MAX: Final = 10
"""Maximum number of commands of the ``core`` family (AGI-5.12); a catalog test."""
ERROR_CODE_NAMES: Final[tuple[str, ...]] = (
    "validation_error",
    "not_found",
    "data_error",
    "calculation_error",
    "missing_dependency",
    "forbidden",
    "io_error",
    "conflict",
)
"""Registry codes a command can declare in :attr:`Command.errors`."""

_NUMERIC_TYPES: Final = ("number", "integer", "number_list")
_OPTION_NAME = re.compile(r"[a-z][a-z0-9_]*")
_COMMAND_NAME = re.compile(r"[a-z][a-z0-9]* [a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_RESULT_SCHEMA = re.compile(r"hydrolog-[a-z][a-z0-9-]*/[1-9][0-9]*")
_FUNCTION_PATH = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")
_SHOWN_MAX_CHARS = 200

_EXPECTED: Final[Mapping[str, str]] = {
    "number": "number",
    "integer": "integer",
    "string": "string",
    "boolean": "boolean",
    "choice": "string",
    "number_list": "array of numbers",
    "string_list": "array of strings",
    "object_list": "array of objects",
    "path": "string (path)",
    "object": "object",
}
_ITEM_EXPECTED: Final[Mapping[str, str]] = {
    "number_list": "number",
    "string_list": "string",
    "object_list": "object",
}


# --- validation helpers ---------------------------------------------------------------


def _shown(value: object) -> object:
    """JSON-compatible, bounded rendering of an offending value for ``details``."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        number = float(value)
        return number if math.isfinite(number) else str(number)
    if isinstance(value, str):
        if len(value) > _SHOWN_MAX_CHARS:
            return value[: _SHOWN_MAX_CHARS - 1] + "…"
        return value
    return f"<{type(value).__name__}>"


def _text(value: object) -> str:
    """Value for a message: ``repr`` of scalars, the type name of anything else."""
    if value is None or isinstance(value, bool | str | numbers.Real):
        return repr(_shown(value))
    return f"a value of type {type(value).__name__}"


def _label(option: Option, index: int | None) -> str:
    return option.name if index is None else f"{option.name}[{index}]"


def _fail(
    option: Option,
    index: int | None,
    reason: str,
    message: str,
    *,
    hint: str | None = None,
    **details: object,
) -> NoReturn:
    """Raise the ``validation_error`` of an option value."""
    payload: dict[str, object] = {"option": option.name, "reason": reason}
    if index is not None:
        payload["index"] = index
    payload.update(details)
    raise InvalidParameterError(
        f"Option {_label(option, index)!r}: {message}", details=payload, hint=hint
    )


def _fail_type(option: Option, value: object, index: int | None = None) -> NoReturn:
    expected = _EXPECTED[option.type] if index is None else _ITEM_EXPECTED[option.type]
    _fail(
        option,
        index,
        "type",
        f"expected {expected}, got {_text(value)}",
        expected=expected,
        value=_shown(value),
        got=type(value).__name__,
    )


def _check_bounds(option: Option, number: float, index: int | None) -> None:
    if option.minimum is not None and number < option.minimum:
        _fail(
            option,
            index,
            "minimum",
            f"must be >= {option.minimum:g}, got {number:g}",
            minimum=option.minimum,
            value=number,
        )
    if option.maximum is not None and number > option.maximum:
        _fail(
            option,
            index,
            "maximum",
            f"must be <= {option.maximum:g}, got {number:g}",
            maximum=option.maximum,
            value=number,
        )
    if option.exclusive_minimum is not None and number <= option.exclusive_minimum:
        _fail(
            option,
            index,
            "exclusive_minimum",
            f"must be > {option.exclusive_minimum:g}, got {number:g}",
            exclusive_minimum=option.exclusive_minimum,
            value=number,
        )


def _number(option: Option, value: object, index: int | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        _fail_type(option, value, index)
    number = float(value)
    if not math.isfinite(number):
        _fail(
            option,
            index,
            "not_finite",
            f"must be a finite number, got {number}",
            value=str(number),
        )
    _check_bounds(option, number, index)
    return number


def _integer(option: Option, value: object, index: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        _fail_type(option, value, index)
    if isinstance(value, numbers.Integral):
        number = int(value)
    else:
        real = float(value)
        if not math.isfinite(real):
            _fail(
                option,
                index,
                "not_finite",
                f"must be a finite number, got {real}",
                value=str(real),
            )
        if not real.is_integer():
            _fail_type(option, value, index)
        number = int(real)
    _check_bounds(option, number, index)
    return number


def _string(option: Option, value: object, index: int | None = None) -> str:
    if not isinstance(value, str):
        _fail_type(option, value, index)
    if not value.strip():
        _fail(option, index, "empty", "must not be empty", value=value)
    return value


def _boolean(option: Option, value: object, index: int | None = None) -> bool:
    if not isinstance(value, bool):
        _fail_type(option, value, index)
    return value


def _choice(option: Option, value: object, index: int | None = None) -> str:
    if not isinstance(value, str):
        _fail_type(option, value, index)
    if value not in option.choices:
        allowed = ", ".join(option.choices)
        _fail(
            option,
            index,
            "choice",
            f"{value!r} is not one of: {allowed}",
            hint=f"Allowed values: {allowed}.",
            allowed=list(option.choices),
            value=_shown(value),
        )
    return value


def _path(option: Option, value: object, index: int | None = None) -> str:
    text = os.fspath(value) if isinstance(value, str | os.PathLike) else None
    if not isinstance(text, str):
        _fail_type(option, value, index)
    if not text.strip():
        _fail(option, index, "empty", "must not be empty", value=text)
    if "\0" in text:
        _fail(option, index, "invalid_path", "must not contain a NUL character")
    return text


def _native(option: Option, value: object, where: str) -> Any:
    """Deep copy of a JSON-native value; everything else is a ``type`` error."""
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        number = float(value)
        if not math.isfinite(number):
            _fail(
                option,
                None,
                "not_finite",
                f"{where} contains a non-finite number ({number})",
                value=str(number),
            )
        return number
    if isinstance(value, list | tuple):
        return [_native(option, item, f"{where}[{i}]") for i, item in enumerate(value)]
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _fail(
                    option,
                    None,
                    "type",
                    f"{where} has a non-string key {_shown(key)!r}",
                    expected="object with string keys",
                    value=_shown(key),
                )
            copied[key] = _native(option, item, f"{where}.{key}")
        return copied
    _fail(
        option,
        None,
        "type",
        f"{where} holds a value that is not JSON-native: {type(value).__name__}",
        expected="JSON value",
        got=type(value).__name__,
    )


def _object(option: Option, value: object, index: int | None = None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail_type(option, value, index)
    converted: dict[str, Any] = _native(option, value, _label(option, index))
    return converted


def _items(option: Option, value: object) -> Sequence[object]:
    if not isinstance(value, list | tuple):
        _fail_type(option, value)
    if not value:
        _fail(option, None, "empty", "must not be an empty list")
    return value


def _number_list(
    option: Option, value: object, index: int | None = None
) -> list[float]:
    return [_number(option, item, i) for i, item in enumerate(_items(option, value))]


def _string_list(option: Option, value: object, index: int | None = None) -> list[str]:
    return [_string(option, item, i) for i, item in enumerate(_items(option, value))]


def _object_list(
    option: Option, value: object, index: int | None = None
) -> list[dict[str, Any]]:
    return [_object(option, item, i) for i, item in enumerate(_items(option, value))]


_NORMALIZERS: Final[Mapping[str, Callable[..., Any]]] = {
    "number": _number,
    "integer": _integer,
    "string": _string,
    "boolean": _boolean,
    "choice": _choice,
    "number_list": _number_list,
    "string_list": _string_list,
    "object_list": _object_list,
    "path": _path,
    "object": _object,
}


# --- declarations ---------------------------------------------------------------------


@dataclass(frozen=True)
class Effects:
    """What a command does to the outside world (AGI-2.2 ``effects``).

    Attributes
    ----------
    read_only : bool
        The command changes nothing.
    writes : {"none", "add", "replace", "delete"}
        Kind of write; ``"replace"`` for a command that writes a file and replaces
        an existing one with ``force``.
    idempotent : bool
        Calling it again with the same options gives the same state.
    network : bool
        The command uses the network.
    destructive : bool
        The command can replace or delete existing data.
    """

    read_only: bool
    writes: Literal["none", "add", "replace", "delete"]
    idempotent: bool
    network: bool
    destructive: bool


@dataclass(frozen=True)
class Option:
    """One option of a command: a keyword argument of its operation.

    The same ``name`` is used in Python, in JSON/MCP input and, as ``--kebab-case``
    (:attr:`flag`), on the command line.

    Parameters
    ----------
    name : str
        ``snake_case`` name; must be a valid Python identifier and not a keyword.
    type : OptionType
        Value type (see the module docstring).
    description : str
        English description, for humans and agents.
    description_pl : str
        Polish translation of ``description`` (the ``i18n.pl`` text).
    required : bool, optional
        The option must be given; incompatible with ``default``.
    default : object, optional
        Default value, only when the underlying API has a documented default;
        ``None`` means "no default" (the operation applies its own).
    choices : tuple of str, optional
        Allowed values; required for ``choice`` and forbidden for other types.
    minimum, maximum : float, optional
        Inclusive bounds of ``number``/``integer``/``number_list`` (per item).
    exclusive_minimum : float, optional
        Exclusive lower bound; not combinable with ``minimum``.
    unit : str, optional
        Unit of the value (``"km"``, ``"m/m"``, ``"mm"``, ``"min"``, ``"km2"``,
        ``"m3/s"``...).
    path_role : {"input", "output"}, optional
        Role of a ``path`` option, required for it and forbidden for other types:
        ``"input"`` is read, ``"output"`` is a file the command writes.
    meanings, meanings_pl : Mapping of str to str, optional
        One-line meaning of every allowed value of a ``choice`` option (English,
        Polish); the keys are exactly ``choices``.

    Raises
    ------
    ValueError
        If the declaration is inconsistent.
    """

    name: str
    type: OptionType
    description: str
    description_pl: str
    required: bool = False
    default: object = None
    choices: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    exclusive_minimum: float | None = None
    unit: str | None = None
    path_role: PathRole | None = None
    meanings: Mapping[str, str] = field(default_factory=dict)
    meanings_pl: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the field values."""
        name = self.name
        if (
            not isinstance(name, str)
            or not _OPTION_NAME.fullmatch(name)
            or keyword.iskeyword(name)
        ):
            raise ValueError(
                f"Option name {name!r} must be snake_case and not a Python keyword"
            )
        self._check_declaration()
        if self.default is not None:
            try:
                self.normalize(self.default)
            except InvalidParameterError as exc:
                raise ValueError(
                    f"Option {name!r}: invalid default {self.default!r}: {exc}"
                ) from exc

    def _check_declaration(self) -> None:
        name = self.name

        def bad(problem: str) -> ValueError:
            return ValueError(f"Option {name!r}: {problem}")

        if self.type not in OPTION_TYPES:
            raise bad(f"unknown type {self.type!r}; allowed: {', '.join(OPTION_TYPES)}")
        for field_name in ("description", "description_pl"):
            text = getattr(self, field_name)
            if not isinstance(text, str) or not text.strip():
                raise bad(f"{field_name} must be a non-empty string")
        if self.required and self.default is not None:
            raise bad("a required option cannot have a default")
        if self.type == "choice":
            if not isinstance(self.choices, tuple) or not self.choices:
                raise bad("a choice option needs a non-empty tuple of choices")
            if not all(isinstance(c, str) and c for c in self.choices):
                raise bad("choices must be non-empty strings")
            if len(set(self.choices)) != len(self.choices):
                raise bad("choices must be unique")
            for label, meanings in (
                ("meanings", self.meanings),
                ("meanings_pl", self.meanings_pl),
            ):
                if set(meanings) != set(self.choices):
                    raise bad(f"{label} must give a meaning for every choice")
                if not all(
                    isinstance(text, str) and text.strip() for text in meanings.values()
                ):
                    raise bad(f"{label} must be non-empty strings")
        elif self.choices or self.meanings or self.meanings_pl:
            raise bad("choices and meanings are allowed only for type 'choice'")
        bounds = {
            "minimum": self.minimum,
            "maximum": self.maximum,
            "exclusive_minimum": self.exclusive_minimum,
        }
        given = {key: value for key, value in bounds.items() if value is not None}
        if given and self.type not in _NUMERIC_TYPES:
            raise bad(f"{', '.join(given)} are allowed only for numeric types")
        for key, value in given.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, numbers.Real)
                or not math.isfinite(value)
            ):
                raise bad(f"{key} must be a finite number")
        if self.minimum is not None and self.exclusive_minimum is not None:
            raise bad("minimum and exclusive_minimum are mutually exclusive")
        lower = self.minimum if self.minimum is not None else self.exclusive_minimum
        if lower is not None and self.maximum is not None and lower > self.maximum:
            raise bad("the lower bound exceeds maximum")
        if self.type == "path":
            if self.path_role not in get_args(PathRole):
                raise bad("a path option needs path_role 'input' or 'output'")
        elif self.path_role is not None:
            raise bad("path_role is allowed only for type 'path'")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit):
            raise bad("unit must be a non-empty string")

    @property
    def flag(self) -> str:
        """str: command-line flag, ``--kebab-case`` of :attr:`name`."""
        return "--" + self.name.replace("_", "-")

    @property
    def short_flag(self) -> str | None:
        """Str or None: the short command-line flag, ``-o`` of ``output_dir``.

        AGI-3.4 reserves ``-o`` as the short form of ``--output-dir`` and of no other
        option, so no other option has one.
        """
        return "-o" if self.name == "output_dir" else None

    @property
    def writes(self) -> bool:
        """bool: the option is an output path (``path_role == "output"``)."""
        return self.path_role == "output"

    def describe(self, lang: Lang = "en") -> str:
        """Return the description in ``lang``.

        Parameters
        ----------
        lang : {"pl", "en"}, optional
            Language of the text.

        Returns
        -------
        str
            ``description`` for ``"en"``, ``description_pl`` for ``"pl"``.
        """
        return self.description_pl if lang == "pl" else self.description

    def normalize(self, value: object) -> Any:
        """Validate one value and return its normalized form.

        Parameters
        ----------
        value : object
            JSON-native value of the option (``None`` is handled by the caller).

        Returns
        -------
        object
            Normalized value (see the module docstring for the type table).

        Raises
        ------
        InvalidParameterError
            If the value has the wrong type or violates a bound, the choices or an
            emptiness rule. ``details`` hold ``option``, ``reason`` (``type``,
            ``not_finite``, ``minimum``, ``maximum``, ``exclusive_minimum``,
            ``choice``, ``empty``, ``invalid_path``), the offending ``value`` and,
            for list items, the ``index``.
        """
        return _NORMALIZERS[self.type](self, value)

    def json_schema(self, lang: Lang = "en") -> dict[str, Any]:
        """Describe the option as a JSON Schema (2020-12) property.

        Parameters
        ----------
        lang : {"pl", "en"}, optional
            Language of the ``description``.

        Returns
        -------
        dict
            Property schema: ``type`` and constraints (``minimum``, ``maximum``,
            ``exclusiveMinimum``, ``enum``, ``minItems``...), ``description`` (with
            the unit in brackets when the text does not name it), ``default`` and
            for paths ``x-hydrolog-type`` (and ``x-hydrolog-writes``).
        """
        schema: dict[str, Any] = {}
        bounds: dict[str, Any] = {}
        if self.minimum is not None:
            bounds["minimum"] = self.minimum
        if self.maximum is not None:
            bounds["maximum"] = self.maximum
        if self.exclusive_minimum is not None:
            bounds["exclusiveMinimum"] = self.exclusive_minimum
        if self.type in ("number", "integer"):
            schema = {"type": self.type, **bounds}
        elif self.type == "string":
            schema = {"type": "string", "minLength": 1}
        elif self.type == "boolean":
            schema = {"type": "boolean"}
        elif self.type == "choice":
            schema = {"type": "string", "enum": list(self.choices)}
        elif self.type == "number_list":
            schema = {
                "type": "array",
                "items": {"type": "number", **bounds},
                "minItems": 1,
            }
        elif self.type == "string_list":
            schema = {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
            }
        elif self.type == "object_list":
            schema = {"type": "array", "items": {"type": "object"}, "minItems": 1}
        elif self.type == "path":
            schema = {"type": "string", "minLength": 1, "x-hydrolog-type": "path"}
            if self.writes:
                schema["x-hydrolog-writes"] = True
        else:
            schema = {"type": "object"}
        text = self.describe(lang)
        if self.unit is not None and f"[{self.unit}]" not in text:
            text = f"{text} [{self.unit}]"
        schema["description"] = text
        if self.default is not None:
            schema["default"] = copy.deepcopy(self.normalize(self.default))
        return schema


@dataclass(frozen=True)
class Command:
    """One catalog command: a function of :mod:`hydrolog.operations`.

    Parameters
    ----------
    name : str
        ``"<group> <command>"``, lowercase, e.g. ``"tc kirpich"`` or
        ``"stats flood-frequency"``.
    operation_id : str
        MCP tool name; must equal ``hydrolog_`` followed by ``name`` with spaces and
        hyphens replaced by underscores (``"hydrolog_tc_kirpich"``).
    summary, summary_pl : str
        One-line summary (English, Polish), at most 100 characters (DOC-1.7).
    description, description_pl : str
        Longer text for agents, including the method and literature (English,
        Polish).
    function : str
        ``"<module>:<attribute>"`` of the operation, e.g.
        ``"hydrolog.operations.tc_kirpich"``; imported lazily by ``run_command`` and
        called with keyword arguments named like the options.
    options : tuple of Option
        Options in catalog order; names are unique.
    one_of : tuple of tuple of str, optional
        Alternative option groups; exactly one group must be given completely.
    result_schema : str
        Id of the domain document in the ``result`` of the envelope
        (``"hydrolog-<group>-<command>/1"``).
    cardinality : {"single", "bounded", "unbounded"}, optional
        Size class of the result (AGI-2.2).
    rules, rules_pl : tuple of str, optional
        Short imperative rules for agents (English, Polish).
    errors : tuple of str, optional
        Registry codes the command can raise besides ``internal_error``.
    core : bool, optional
        The command belongs to the ``core`` family of MCP tools (at most 10).
    example_results : tuple of Mapping, optional
        Excerpt of the result of each example, in the order of ``examples``.
    examples : tuple of Mapping, optional
        Example option sets (valid inputs of the command).

    Raises
    ------
    ValueError
        If the declaration is inconsistent.
    """

    name: str
    operation_id: str
    summary: str
    summary_pl: str
    description: str
    description_pl: str
    function: str
    options: tuple[Option, ...]
    one_of: tuple[tuple[str, ...], ...] = ()
    examples: tuple[Mapping[str, object], ...] = ()
    result_schema: str = ""
    cardinality: Cardinality = "single"
    rules: tuple[str, ...] = ()
    rules_pl: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    core: bool = False
    example_results: tuple[Mapping[str, object], ...] = ()

    def __post_init__(self) -> None:
        """Validate the field values."""

        def bad(problem: str) -> ValueError:
            return ValueError(f"Command {self.name!r}: {problem}")

        if not isinstance(self.name, str) or not _COMMAND_NAME.fullmatch(self.name):
            raise bad(
                "name must be '<group> <command>' in lowercase "
                "(letters, digits, hyphens inside the command)"
            )
        expected_id = f"{TOOL}_" + self.name.replace(" ", "_").replace("-", "_")
        if self.operation_id != expected_id:
            raise bad(
                f"operation_id must be {expected_id!r}, got {self.operation_id!r}"
            )
        for field_name in ("summary", "summary_pl"):
            text = getattr(self, field_name)
            if not isinstance(text, str) or not text.strip() or "\n" in text:
                raise bad(f"{field_name} must be a non-empty single line")
            if len(text) > SUMMARY_MAX_CHARS:
                raise bad(f"{field_name} is longer than {SUMMARY_MAX_CHARS} characters")
        for field_name in ("description", "description_pl"):
            text = getattr(self, field_name)
            if not isinstance(text, str) or not text.strip():
                raise bad(f"{field_name} must be a non-empty string")
        if not _RESULT_SCHEMA.fullmatch(self.result_schema):
            raise bad(
                "result_schema must look like 'hydrolog-<kind>/<n>', got "
                f"{self.result_schema!r}"
            )
        if len(self.operation_id) > TOOL_NAME_MAX_CHARS:
            raise bad(f"operation_id is longer than {TOOL_NAME_MAX_CHARS} characters")
        if not isinstance(self.function, str) or not _FUNCTION_PATH.fullmatch(
            self.function
        ):
            raise bad("function must be a dotted path 'package.module.function'")
        for field_name in (
            "options",
            "one_of",
            "examples",
            "rules",
            "rules_pl",
            "errors",
            "example_results",
        ):
            if not isinstance(getattr(self, field_name), tuple):
                raise bad(f"{field_name} must be a tuple")
        if len(self.rules) != len(self.rules_pl):
            raise bad("rules and rules_pl must have the same number of entries")
        if not self.examples:
            raise bad("at least one example is required")
        if len(self.example_results) != len(self.examples):
            raise bad("example_results must hold one excerpt per example")
        if not all(isinstance(item, Mapping) for item in self.example_results):
            raise bad("each example result must be a mapping")
        unknown_errors = sorted(set(self.errors) - set(ERROR_CODE_NAMES))
        if unknown_errors or len(set(self.errors)) != len(self.errors):
            raise bad(f"errors must be unique registry codes, got {list(self.errors)}")
        budget = len(self.summary) + len(self.description) + len(" ".join(self.rules))
        if budget > MCP_DESCRIPTION_MAX_CHARS:
            raise bad(
                f"summary, description and rules take {budget} characters; the "
                f"MCP description allows {MCP_DESCRIPTION_MAX_CHARS}"
            )
        if not all(isinstance(option, Option) for option in self.options):
            raise bad("options must hold Option instances")
        names = [option.name for option in self.options]
        if len(set(names)) != len(names):
            raise bad("option names must be unique")
        self._check_one_of(names, bad)
        for number, example in enumerate(self.examples):
            if not isinstance(example, Mapping):
                raise bad(f"example #{number} must be a mapping")
            unknown = sorted(set(example) - set(names))
            if unknown:
                raise bad(f"example #{number} uses unknown options: {unknown}")

    def _check_one_of(self, names: list[str], bad: Callable[[str], ValueError]) -> None:
        if not self.one_of:
            return
        if len(self.one_of) < 2:
            raise bad("one_of needs at least two alternative groups")
        required = {option.name for option in self.options if option.required}
        for group in self.one_of:
            if not isinstance(group, tuple) or not group:
                raise bad("each one_of group must be a non-empty tuple")
            if len(set(group)) != len(group):
                raise bad(f"one_of group {group} repeats an option")
            unknown = [name for name in group if name not in names]
            if unknown:
                raise bad(f"one_of group {group} uses unknown options: {unknown}")
            overlap = sorted(required.intersection(group))
            if overlap:
                raise bad(f"required options cannot be part of one_of: {overlap}")

    @property
    def writes(self) -> bool:
        """bool: the command writes a file (an option has ``path_role="output"``)."""
        return any(option.writes for option in self.options)

    @property
    def effects(self) -> Effects:
        """Effects: what the command does to the outside world (AGI-2.2)."""
        return Effects(
            read_only=not self.writes,
            writes="replace" if self.writes else "none",
            idempotent=True,
            network=False,
            destructive=self.writes,
        )

    @property
    def check(self) -> str | None:
        """Return the command that plans this one (itself, with ``check``) or None."""
        return self.name if self.writes else None

    @property
    def families(self) -> tuple[str, ...]:
        """Return the MCP tool families: the group, and ``core`` where it applies."""
        return (self.group, "core") if self.core else (self.group,)

    @property
    def group(self) -> str:
        """str: first word of :attr:`name` (``"tc"``)."""
        return self.name.split(" ", 1)[0]

    @property
    def subcommand(self) -> str:
        """str: second word of :attr:`name` (``"kirpich"``)."""
        return self.name.split(" ", 1)[1]

    def option(self, name: str) -> Option:
        """Return the option called ``name``.

        Parameters
        ----------
        name : str
            Option name.

        Returns
        -------
        Option
            The declared option.

        Raises
        ------
        KeyError
            If the command has no such option.
        """
        for option in self.options:
            if option.name == name:
                return option
        raise KeyError(name)

    def summarize(self, lang: Lang = "en") -> str:
        """Return the one-line summary in ``lang``."""
        return self.summary_pl if lang == "pl" else self.summary

    def describe(self, lang: Lang = "en") -> str:
        """Return the long description in ``lang``."""
        return self.description_pl if lang == "pl" else self.description
