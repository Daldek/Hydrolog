"""Fill the generated fragments of the handbook from the formula specs (Nogat CMP-2.7).

The handbook ``docs/podrecznik/`` (Polish, CC BY 4.0) reproduces the equations,
constants and ranges of Hydrolog's formulas only through fragments generated from their
specs. A fragment lies between two markers, each alone on its line and outside a code
fence; an author writes the pair empty and this script fills it:

``<!-- spec:NAME -->`` ... ``<!-- /spec:NAME -->``
    The formula ``NAME``: a Tier A spec (``formulas/<NAME>.toml``) with its equation,
    inputs, outputs, constraints, constants, conventions, assumptions, validation,
    ``formula_version``, status and sources; or a Tier B formula of
    ``docs/FORMULAS.md`` with its definition, convention, constants and source.
``<!-- spec-table:NAME -->`` ... ``<!-- /spec-table:NAME -->``
    The published tables of the spec ``NAME`` (CMP-2.5), row by row from their files.
``<!-- generated:KIND -->`` ... ``<!-- /generated:KIND -->``
    An index of the handbook: the ``symbols`` and ``units`` of the formulas it shows,
    those ``formulas`` with their status and evidence, and the catalog's ``commands``
    with the chapters whose text runs them.

The Polish texts are kept in ``docs/podrecznik/_specs_pl.toml``: per formula a title
and the meaning of each input, output, constant and constraint, the conventions,
assumptions and validation (Tier A) or the definition and convention (Tier B); the
name of each unit, the words of the equations and the headers of the tables' columns.
An entry carries the SHA-256 of the English texts it translates (``en_sha256``), and
every translated text keeps the numbers of its English one, so a change of a spec
stops the generator until its Polish texts are reviewed. A formula the handbook shows
needs its entry; ``--template NAME`` prints one to fill.

``tests/contract/test_handbook.py`` checks the fragments fresh (DEV-10.4).

Usage::

    uv run scripts/generate_handbook.py                  # fill the fragments
    uv run scripts/generate_handbook.py --check          # fail when one is stale
    uv run scripts/generate_handbook.py --template NAME  # an entry of _specs_pl.toml
"""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import tomllib
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from hydrolog._formulas import specs, tier_b
from hydrolog.catalog import data_commands
from hydrolog.nogat_formulas import (
    Constant,
    FormulaSpec,
    Output,
    Range,
    Source,
    TierBSpec,
    Variable,
)

ROOT = Path(__file__).resolve().parent.parent
HANDBOOK = ROOT / "docs" / "podrecznik"
POLISH = "_specs_pl.toml"
SCRIPT = "scripts/generate_handbook.py"
INDEXES = ("symbols", "units", "formulas", "commands")
"""The kinds of ``<!-- generated:KIND -->`` fragments."""

_MARKER = re.compile(r"<!--\s*(/?)(spec|spec-table|generated):([a-z][a-z0-9_]*)\s*-->")
_LIKE_MARKER = re.compile(r"<!--\s*/?\s*(spec|spec-table|generated)\s*:")
_FENCE = re.compile(r"`{3,}|~{3,}")
_DIGITS = re.compile(r"[0-9]+")
_WORDS = re.compile(r"\\text\{((?:[^{}\\]|\\.)*)\}")
_DECIMAL = re.compile(r"(?<=[0-9])\.(?=[0-9])")
_CHAPTER = re.compile(r"[0-9][0-9]-.+\.md")
_SUPERSCRIPT = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")
_PLAIN = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_NBSP = "\u00a0"
_MINUS = "\u2212"
_UNIT_LETTERS = frozenset({"a", "b", "C", "cm", "d", "ft", "h", "in", "km", "m", "mi"})
_UNIT_LETTERS |= {"min", "mm", "s"}
"""Symbols a unit is written with; a unit with another word needs a Polish symbol."""

_GENERATED = (
    "Ramka wygenerowana ze specyfikacji przez `scripts/generate_handbook.py`; "
    "nie edytuj jej ręcznie."
)
_STATUS = {
    "referenced": "status: **sprawdzony na przypadkach referencyjnych** (`referenced`)",
    "oracle only": "status: **sprawdzony tylko wyroczniami** (`oracle only`)",
    "unreferenced": (
        "status: **bez przypadku referencyjnego i wyroczni** (`unreferenced`)"
    ),
}
_CONSTRAINT = {
    "physical": "odmowa obliczeń: wartości niemożliwe fizycznie",
    "precondition": "odmowa obliczeń: wzór jest nieokreślony",
    "applicability": "wynik z ostrzeżeniem: poza zakresem stosowalności",
}
_KIND = {
    "real": "",
    "real_array": " (ciąg)",
    "integer": " (liczba całkowita)",
    "choice": " (wybór)",
}
_ORACLE = {
    "exact": "rozwiązanie dokładne",
    "algorithm": "niezależny algorytm",
    "established": "uznana implementacja",
    "frozen": "zamrożona wyrocznia",
}


class HandbookError(Exception):
    """What stops the generator: markers, unknown names, missing Polish texts."""

    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = list(problems)


@dataclass(frozen=True)
class Fragment:
    """A generated fragment of a handbook file: its markers' kind, name and lines."""

    path: Path
    kind: str
    name: str
    start: int
    end: int

    def where(self) -> str:
        """Return the file and line of the opening marker."""
        return f"{_relative(self.path)}:{self.start + 1}"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fragments(path: Path, text: str) -> tuple[list[Fragment], list[str]]:
    """Return the fragments of a handbook file and the problems of its markers.

    Parameters
    ----------
    path : Path
        The file, as problems name it.
    text : str
        Its text.

    Returns
    -------
    tuple of list of Fragment and list of str
        The fragments in the order of the file, and what is wrong with the markers: a
        malformed one, a closing marker without its opening one, a fragment never
        closed or closed by another name.
    """
    found: list[Fragment] = []
    problems: list[str] = []
    fence = ""
    opened: tuple[str, str, int] | None = None
    for index, line in enumerate(text.split("\n")):
        stripped = line.strip()
        where = f"{_relative(path)}:{index + 1}"
        marker = _MARKER.fullmatch(stripped)
        if opened is not None:
            if marker and marker.group(1):
                kind, name = marker.group(2), marker.group(3)
                if (kind, name) == opened[:2]:
                    found.append(Fragment(path, kind, name, opened[2], index))
                else:
                    problems.append(
                        f"{where}: {stripped} closes <!-- {opened[0]}:{opened[1]} --> "
                        f"of line {opened[2] + 1}"
                    )
                opened = None
            continue
        if fence:
            if set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                fence = ""
            continue
        opening = _FENCE.match(stripped)
        if opening:
            fence = opening.group(0)
        elif marker and marker.group(1):
            problems.append(f"{where}: {stripped} has no opening marker")
        elif marker:
            opened = (marker.group(2), marker.group(3), index)
        elif _LIKE_MARKER.match(stripped):
            problems.append(
                f"{where}: malformed marker {stripped!r}; write <!-- spec:NAME -->, "
                "<!-- spec-table:NAME --> or <!-- generated:KIND --> alone on a line"
            )
    if opened is not None:
        problems.append(
            f"{_relative(path)}:{opened[2] + 1}: <!-- {opened[0]}:{opened[1]} --> is "
            f"never closed by <!-- /{opened[0]}:{opened[1]} -->"
        )
    return found, problems


# --- the Polish texts --------------------------------------------------------------


def _expected(item: FormulaSpec | TierBSpec) -> dict[str, object]:
    """Return the English counterpart of every key of a formula's Polish entry.

    A string is translated by a string with the same numbers, a list by a list of the
    same length, a mapping by a table of the same keys; ``""`` stands for a text
    without an English counterpart (a constant's meaning, a Tier B title), which holds
    no digit.
    """
    if isinstance(item, TierBSpec):
        rule: dict[str, object] = {
            "title": "",
            "definition": item.definition,
            "convention": item.convention,
        }
        if item.constants:
            rule["constants"] = {c.name: "" for c in item.constants}
        return rule
    expected: dict[str, object] = {
        "title": item.title,
        "validation": item.validation,
        "variables": {v.name: v.description for v in item.variables},
        "outputs": {o.name: o.description for o in item.outputs},
    }
    if item.constants:
        expected["constants"] = {c.name: "" for c in item.constants}
    if item.constraints:
        expected["constraints"] = {c.name: c.text for c in item.constraints}
    if item.conventions:
        expected["conventions"] = list(item.conventions)
    if item.assumptions:
        expected["assumptions"] = list(item.assumptions)
    return expected


def fingerprint(item: FormulaSpec | TierBSpec) -> str:
    """Return the SHA-256 of the English texts a formula's Polish entry translates."""
    text = json.dumps(_expected(item), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _numbers(text: str) -> Counter[str]:
    return Counter(_DIGITS.findall(text.translate(_PLAIN)))


def _number_problem(english: str, polish: str) -> str:
    """Return how the numbers of a translation differ from its English text's."""
    want, got = _numbers(english), _numbers(polish)
    parts = []
    if missing := sorted((want - got).elements()):
        parts.append(f"lacks {', '.join(missing)}")
    if extra := sorted((got - want).elements()):
        parts.append(f"adds {', '.join(extra)}")
    return " and ".join(parts)


def _text_problems(where: str, english: str, polish: object) -> list[str]:
    if not isinstance(polish, str) or not polish.strip():
        return [f"{where}: needs a Polish text"]
    differ = _number_problem(english, polish)
    return (
        [f"{where}: the numbers differ from the spec's text: {differ}"]
        if differ
        else []
    )


def _value_problems(where: str, english: object, polish: object) -> list[str]:
    if isinstance(english, str):
        return _text_problems(where, english, polish)
    if isinstance(english, list):
        if not isinstance(polish, list) or len(polish) != len(english):
            return [f"{where}: needs a list of {len(english)} Polish texts"]
        return [
            problem
            for index, (en, pl) in enumerate(zip(english, polish, strict=True))
            for problem in _text_problems(f"{where}[{index}]", en, pl)
        ]
    assert isinstance(english, dict)
    if not isinstance(polish, dict):
        return [f"{where}: needs a table of {', '.join(english)}"]
    problems = [
        f"{where}: no {name} in the spec" for name in polish if name not in english
    ]
    for name, en in english.items():
        problems += _text_problems(f"{where}.{name}", en, polish.get(name))
    return problems


def entry_problems(item: FormulaSpec | TierBSpec, entry: object) -> list[str]:
    """Return what is missing, unknown or stale in a formula's Polish entry.

    Parameters
    ----------
    item : FormulaSpec or TierBSpec
        The formula.
    entry : object
        Its table of ``_specs_pl.toml``.

    Returns
    -------
    list of str
        Empty when the entry translates every text of the formula, keeps their
        numbers and carries the fingerprint of the formula's English texts.
    """
    section = "rules" if isinstance(item, TierBSpec) else "formulas"
    where = f"{POLISH} [{section}.{item.name}]"
    if not isinstance(entry, dict):
        return [f"{where}: not a table"]
    expected = _expected(item)
    problems = [
        f"{where}: unknown key {key!r}"
        for key in entry
        if key not in expected and key != "en_sha256"
    ]
    for key, english in expected.items():
        problems += _value_problems(f"{where}.{key}", english, entry.get(key))
    wanted = fingerprint(item)
    if entry.get("en_sha256") != wanted:
        problems.append(
            f"{where}: translated from other English texts of the spec (en_sha256 "
            f"{entry.get('en_sha256')!r}); review the Polish texts against "
            f"formulas/{item.name}.toml or docs/FORMULAS.md and set "
            f'en_sha256 = "{wanted}"'
        )
    return problems


def template(item: FormulaSpec | TierBSpec) -> str:
    """Return the entry of ``_specs_pl.toml`` to fill for a formula.

    Each key comes with its English text as a comment; the fingerprint is the one of
    the spec as it is.
    """
    section = "rules" if isinstance(item, TierBSpec) else "formulas"
    head = f"{section}.{item.name}"
    lines = [f"[{head}]", f'en_sha256 = "{fingerprint(item)}"']
    tables: list[str] = []
    hints = _hints(item)
    for key, english in _expected(item).items():
        if isinstance(english, str):
            lines += [f"# {english or hints.get(key, '')}".rstrip(), f'{key} = ""']
        elif isinstance(english, list):
            lines.append(f"{key} = [")
            for text in english:
                lines += [f"    # {text}", '    "",']
            lines.append("]")
        else:
            assert isinstance(english, dict)
            tables += ["", f"[{head}.{key}]"]
            for name, text in english.items():
                hint = text or hints.get(f"{key}.{name}", "")
                tables += [f"# {hint}".rstrip(), f'{name} = ""']
    return "\n".join(lines + tables) + "\n"


def _hints(item: FormulaSpec | TierBSpec) -> dict[str, str]:
    """Return what a translator reads for a text without an English counterpart."""
    hints = {"title": f"the Tier B formula {item.name}: {item.function}"}
    for constant in item.constants:
        hints[f"constants.{constant.name}"] = (
            f"constant {constant.symbol or constant.name} = {constant.value} "
            f"[{constant.unit}]: {constant.source.text()}"
        )
    return hints


# --- numbers, units and equations as the handbook prints them -----------------------


def number(value: float | Fraction) -> str:
    """Return a number as the handbook prints it: its exact digits, a decimal comma.

    Thousands of a number of five or more digits are parted by a non-breaking space,
    a power of ten is written ``1·10⁻⁹`` and a minus is U+2212.
    """
    if isinstance(value, Fraction):
        if value.denominator != 1:
            return f"{number(Fraction(value.numerator))}/{value.denominator}"
        text = str(value.numerator)
    elif math.isinf(value):
        return "∞" if value > 0 else f"{_MINUS}∞"
    else:
        text = repr(float(value))
    sign = _MINUS if text.startswith("-") else ""
    mantissa, _, exponent = text.lstrip("-").partition("e")
    whole, _, fraction = mantissa.partition(".")
    if len(whole) >= 5:
        head = len(whole) % 3 or 3
        groups = [whole[:head], *(whole[i : i + 3] for i in range(head, len(whole), 3))]
        whole = _NBSP.join(groups)
    shown = whole if fraction in ("", "0") else f"{whole},{fraction}"
    if exponent:
        shown += "·10" + str(int(exponent)).translate(_SUPERSCRIPT)
    return sign + shown


def interval(rng: Range) -> str:
    """Return a range as an interval: ``[0,05; 0,2]``, ``(0; ∞)``."""
    left = "[" if rng.low_inclusive and math.isfinite(rng.low) else "("
    right = "]" if rng.high_inclusive and math.isfinite(rng.high) else ")"
    return f"{left}{number(rng.low)}; {number(rng.high)}{right}"


def unit_symbol(unit: str) -> str:
    r"""Return a unit of the specs as the handbook prints it (``m3/s`` as ``m³/s``).

    A unit with a power is LaTeX (``$\mathrm{h\,km^{-0{,}52}}$``), ``-`` is a dash.
    """
    if unit == "-":
        return "–"
    shown = unit.replace("degC", "°C")
    if "^" not in shown:
        shown = re.sub(
            r"(?<=[a-z])([23])(?![0-9])",
            lambda found: found.group(1).translate(_SUPERSCRIPT),
            shown,
        )
        return shown.replace(" per ", " na ")
    latex = re.sub(r"(?<=[a-z])([23])(?![0-9^])", r"^{\1}", shown)
    latex = re.sub(
        r"\^(\([^)]*\)|-?[0-9./]+|[a-z])",
        lambda found: "^{" + found.group(1).removeprefix("(").removesuffix(")") + "}",
        latex,
    )
    latex = _DECIMAL.sub("{,}", latex).replace("%", r"\%")
    parts = [part.replace(" ", r"\,") for part in latex.split(" per ")]
    return "$\\mathrm{" + r"\text{ na }".join(parts) + "}$"


def _needs_symbol(unit: str) -> bool:
    """Return whether a unit holds a word that only a Polish symbol can show."""
    words = re.findall(r"[A-Za-z]+", unit.replace("degC", "").replace(" per ", " "))
    return any(word not in _UNIT_LETTERS for word in words)


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |"


def _quote(lines: Iterable[str]) -> list[str]:
    return [f"> {line}" if line else ">" for line in lines]


class _Sources:
    """The sources of a fragment, numbered in the order they are first cited."""

    def __init__(self) -> None:
        self._numbers: dict[Source, int] = {}

    def cite(self, source: Source | None) -> str:
        if source is None:
            return ""
        number_ = self._numbers.setdefault(source, len(self._numbers) + 1)
        return f"(źr. {number_})"

    def lines(self) -> list[str]:
        shown = []
        for source, index in self._numbers.items():
            line = f"{index}. {_cell(source.text())}"
            if source.url:
                line += f" <{source.url}>"
            if source.access == "author-provided":
                line += " — *źródło niedostępne publicznie (dostarczone przez autora)*"
            shown.append(line)
        return shown


# --- the handbook ------------------------------------------------------------------


@dataclass
class Handbook:
    """The handbook's Markdown files and what their fragments are generated from.

    Attributes
    ----------
    files : Mapping[Path, str]
        The text of each Markdown file of the handbook.
    polish : Mapping[str, Any]
        The Polish texts, ``_specs_pl.toml``.
    formulas, rules : Mapping
        The Tier A specs and the Tier B formulas by name.
    commands : sequence of (str, str)
        The catalog's commands: the name and its Polish summary.
    root : Path
        The project, where the specs' table files are.
    """

    files: Mapping[Path, str]
    polish: Mapping[str, Any]
    formulas: Mapping[str, FormulaSpec]
    rules: Mapping[str, TierBSpec]
    commands: Sequence[tuple[str, str]]
    root: Path = ROOT
    _fragments: dict[Path, list[Fragment]] = field(init=False, repr=False)
    _marker_problems: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Find the fragments of every file."""
        self._fragments = {}
        self._marker_problems = []
        for path, text in self.files.items():
            found, problems = fragments(path, text)
            self._fragments[path] = found
            self._marker_problems += problems

    # --- what the fragments name -------------------------------------------------

    def all_fragments(self) -> list[Fragment]:
        """Return every fragment of the handbook, file by file."""
        return [item for path in self.files for item in self._fragments[path]]

    def shown(self) -> dict[str, list[Path]]:
        """Return each formula a ``spec`` fragment shows with the files showing it."""
        found: dict[str, list[Path]] = {}
        for item in self.all_fragments():
            if item.kind == "spec" and self._known(item):
                paths = found.setdefault(item.name, [])
                if item.path not in paths:
                    paths.append(item.path)
        return found

    def _known(self, item: Fragment) -> bool:
        if item.kind == "spec":
            return item.name in self.formulas or item.name in self.rules
        if item.kind == "spec-table":
            return bool(item.name in self.formulas and self.formulas[item.name].tables)
        return item.name in INDEXES

    def name_problems(self) -> list[str]:
        """Return the fragments whose name is no formula, table or index."""
        problems = []
        for item in self.all_fragments():
            if self._known(item):
                continue
            if item.kind == "spec":
                problems.append(
                    f"{item.where()}: no formula {item.name!r}: neither a Tier A spec "
                    "(formulas/<name>.toml) nor a Tier B formula of docs/FORMULAS.md"
                )
            elif item.kind == "spec-table":
                problems.append(
                    f"{item.where()}: {item.name!r} is no spec with published tables"
                )
            else:
                problems.append(
                    f"{item.where()}: no index {item.name!r}; "
                    f"one of {', '.join(INDEXES)}"
                )
        return problems

    def marker_problems(self) -> list[str]:
        """Return what is wrong with the markers of the files."""
        return list(self._marker_problems)

    # --- the Polish texts ----------------------------------------------------------

    def _units_of(self, names: Iterable[str]) -> list[str]:
        units: list[str] = []
        for name in names:
            items: Sequence[Variable | Output | Constant]
            if name in self.formulas:
                spec = self.formulas[name]
                items = (*spec.variables, *spec.outputs, *spec.constants)
            else:
                items = self.rules[name].constants
            units += [item.unit for item in items]
        return list(dict.fromkeys(units))

    def _words_of(self, names: Iterable[str]) -> list[str]:
        words: list[str] = []
        for name in names:
            if name not in self.formulas:
                continue
            spec = self.formulas[name]
            items: tuple[Variable | Output | Constant, ...] = (
                *spec.variables,
                *spec.outputs,
                *spec.constants,
            )
            texts = [spec.latex] + [item.symbol for item in items]
            for text in texts:
                words += _WORDS.findall(text)
        return list(dict.fromkeys(words))

    def _columns_of(self, names: Iterable[str]) -> list[str]:
        columns: list[str] = []
        for name in names:
            for table in self.formulas[name].tables:
                columns += next(csv.reader(io.StringIO(self._table_text(table.path))))
        return list(dict.fromkeys(columns))

    def _table_text(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")

    def polish_problems(self) -> list[str]:
        """Return what is missing, unknown or stale in the Polish texts.

        Every entry of ``_specs_pl.toml`` translates its formula completely and fresh;
        every formula, unit, word of an equation and column of a table the handbook
        shows has its Polish text.
        """
        data = self.polish
        problems = [
            f"{POLISH}: unknown section [{key}]"
            for key in data
            if key not in ("formulas", "rules", "units", "words", "columns")
        ]
        for section, known in (("formulas", self.formulas), ("rules", self.rules)):
            entries = data.get(section, {})
            for name, entry in entries.items():
                if name not in known:
                    problems.append(f"{POLISH} [{section}.{name}]: no such formula")
                else:
                    problems += entry_problems(known[name], entry)
        shown = self.shown()
        for name, paths in shown.items():
            section = "formulas" if name in self.formulas else "rules"
            if name not in data.get(section, {}):
                problems.append(
                    f"{_relative(paths[0])} shows {name}, which has no Polish texts in "
                    f"{POLISH}: run `uv run {SCRIPT} --template {name}`, translate the "
                    "entry and add it"
                )
        all_names = [*self.formulas, *self.rules]
        tables = [
            item.name
            for item in self.all_fragments()
            if item.kind == "spec-table" and self._known(item)
        ]
        for key, needed, every in (
            ("units", self._units_of(shown), self._units_of(all_names)),
            ("words", self._words_of(shown), self._words_of(self.formulas)),
            (
                "columns",
                self._columns_of(tables),
                self._columns_of(n for n in self.formulas if self.formulas[n].tables),
            ),
        ):
            entries = data.get(key, {})
            problems += [
                f"{POLISH} [{key}] {name!r}: not used by any spec"
                for name in entries
                if name not in every
            ]
            problems += [
                f"{POLISH} [{key}] needs {name!r}"
                for name in needed
                if name not in entries
            ]
        for name, entry in data.get("units", {}).items():
            problems += self._unit_problems(name, entry)
        for key in ("words", "columns"):
            for name, text in data.get(key, {}).items():
                problems += _text_problems(f"{POLISH} [{key}] {name!r}", name, text)
        return problems

    def _unit_problems(self, unit: str, entry: object) -> list[str]:
        where = f"{POLISH} [units] {unit!r}"
        if not isinstance(entry, dict) or set(entry) - {"name", "symbol"}:
            return [f"{where}: a table of name and, for a word, symbol"]
        name = entry.get("name")
        problems = (
            [] if isinstance(name, str) and name.strip() else [f"{where}: no name"]
        )
        if "symbol" in entry:
            problems += _text_problems(f"{where}.symbol", unit, entry["symbol"])
        elif _needs_symbol(unit):
            problems.append(f"{where}: a unit with a word needs its Polish symbol")
        return problems

    def table_problems(self) -> list[str]:
        """Return the table files of the specs shown that differ from their SHA-256."""
        problems = []
        for item in self.all_fragments():
            if item.kind != "spec-table" or not self._known(item):
                continue
            for table in self.formulas[item.name].tables:
                data = (self.root / table.path).read_bytes()
                if hashlib.sha256(data).hexdigest() != table.sha256:
                    problems.append(f"{table.path}: not the table of spec {item.name}")
        return problems

    def problems(self) -> list[str]:
        """Return everything that stops the generator."""
        return [
            *self.marker_problems(),
            *self.name_problems(),
            *self.polish_problems(),
            *self.table_problems(),
        ]

    # --- the generated text --------------------------------------------------------

    def documents(self) -> dict[Path, str]:
        """Return the text of each file with its fragments generated.

        Raises
        ------
        HandbookError
            With every problem of :meth:`problems`.
        """
        problems = self.problems()
        if problems:
            raise HandbookError(problems)
        done: dict[Path, str] = {}
        for path, text in self.files.items():
            lines = text.split("\n")
            for item in reversed(self._fragments[path]):
                lines[item.start + 1 : item.end] = self._render(item)
            done[path] = "\n".join(lines)
        return done

    def _render(self, item: Fragment) -> list[str]:
        if item.kind == "spec-table":
            body = self._tables(self.formulas[item.name])
        elif item.kind == "generated":
            body = {
                "symbols": self._symbols,
                "units": self._units,
                "formulas": self._formulas_index,
                "commands": self._commands,
            }[item.name]()
        elif item.name in self.formulas:
            body = self._formula(self.formulas[item.name])
        else:
            body = self._rule(self.rules[item.name])
        return ["", *body, ""]

    def _equation(self, latex: str) -> str:
        words = self.polish.get("words", {})
        translated = _WORDS.sub(lambda m: "\\text{" + words[m.group(1)] + "}", latex)
        return _DECIMAL.sub("{,}", translated)

    def _symbol(self, symbol: str) -> str:
        return f"${_cell(self._equation(symbol))}$" if symbol else "–"

    def _unit(self, unit: str) -> str:
        entry = self.polish["units"][unit]
        return str(entry.get("symbol") or unit_symbol(unit))

    def _physical(self, item: Variable | Output) -> str:
        if item.kind == "choice":
            return "jedna z: " + ", ".join(f"`{c}`" for c in item.choices)
        return interval(item.physical) if item.physical is not None else "–"

    def _formula(self, spec: FormulaSpec) -> list[str]:
        polish = self.polish["formulas"][spec.name]
        sources = _Sources()
        for source in spec.sources:
            sources.cite(source)
        lines = [
            f"**{_cell(polish['title'])}** · specyfikacja "
            f"[`{spec.name}`](../FORMULAS.md#{spec.name}) · wersja wzoru "
            f"{spec.formula_version} · {_STATUS[spec.status]}",
            "",
            "$$",
            *self._equation(spec.latex).split("\n"),
            "$$",
            "",
            "**Dane wejściowe**",
            "",
            "| Symbol | Argument | Znaczenie | Jednostka | Zakres fizyczny | "
            "Zakres stosowalności | Zakres typowy |",
            "|---|---|---|---|---|---|---|",
        ]
        for var in spec.variables:
            kind = " (tablica)" if var.kind == "real_array" and var.dims > 1 else ""
            applicability = var.applicability
            if applicability == "unstated":
                stated = "nie podano w źródłach"
            elif isinstance(applicability, Range):
                stated = (
                    f"{interval(applicability)} {sources.cite(applicability.source)}"
                )
            else:
                stated = "–"
            typical = var.typical
            usual = (
                f"{interval(typical)} {sources.cite(typical.source)}"
                if typical
                else "–"
            )
            lines.append(
                _row(
                    self._symbol(var.symbol),
                    f"`{var.name}`{kind or _KIND[var.kind]}",
                    _cell(polish["variables"][var.name]),
                    self._unit(var.unit),
                    self._physical(var),
                    stated,
                    usual,
                )
            )
        lines += [
            "",
            "**Wyniki**",
            "",
            "| Symbol | Wynik | Znaczenie | Jednostka | Zakres fizyczny |",
            "|---|---|---|---|---|",
        ]
        lines += [
            _row(
                self._symbol(out.symbol),
                f"`{out.name}`{_KIND[out.kind]}",
                _cell(polish["outputs"][out.name]),
                self._unit(out.unit),
                self._physical(out),
            )
            for out in spec.outputs
        ]
        if spec.constraints:
            lines += [
                "",
                "**Warunki**",
                "",
                "| Warunek | Nazwa | Gdy nie jest spełniony | Źródło |",
                "|---|---|---|---|",
            ]
            lines += [
                _row(
                    _cell(polish["constraints"][c.name]),
                    f"`{c.name}`",
                    _CONSTRAINT[c.cls],
                    sources.cite(c.source),
                )
                for c in spec.constraints
            ]
        lines += self._constants(spec.constants, polish, sources)
        for key, title in (("conventions", "Konwencje"), ("assumptions", "Założenia")):
            if polish.get(key):
                lines += ["", f"**{title}**", ""]
                lines += [f"- {_cell(text)}" for text in polish[key]]
        lines += [
            "",
            f"**Zgodność z obserwacjami według źródeł:** {_cell(polish['validation'])}",
            "",
            "**Źródła** (opisy w brzmieniu specyfikacji)",
            "",
            *sources.lines(),
            "",
            f"Funkcja `{spec.function}`. {_GENERATED}",
        ]
        return [f'<a id="spec-{spec.name}"></a>', "", *_quote(lines)]

    def _constants(
        self,
        constants: Sequence[Constant],
        polish: Mapping[str, Any],
        sources: _Sources,
    ) -> list[str]:
        if not constants:
            return []
        lines = [
            "",
            "**Stałe**",
            "",
            "| Symbol | Stała | Znaczenie | Wartość | Jednostka | Źródło |",
            "|---|---|---|---|---|---|",
        ]
        lines += [
            _row(
                self._symbol(c.symbol),
                f"`{c.name}`",
                _cell(polish["constants"][c.name]),
                number(c.value),
                self._unit(c.unit),
                sources.cite(c.source),
            )
            for c in constants
        ]
        return lines

    def _rule(self, rule: TierBSpec) -> list[str]:
        polish = self.polish["rules"][rule.name]
        sources = _Sources()
        cited = sources.cite(rule.source)
        lines = [
            f"**{_cell(polish['title'])}** · reguła `{rule.name}` (Tier B, CMP-2.2)",
            "",
            f"**Definicja:** {_cell(polish['definition'])} {cited}",
            "",
            f"**Konwencja:** {_cell(polish['convention'])}",
            *self._constants(rule.constants, polish, sources),
            "",
            "**Źródła** (opisy w brzmieniu specyfikacji)",
            "",
            *sources.lines(),
            "",
            f"Funkcja `{rule.function}`. {_GENERATED}",
        ]
        return [f'<a id="spec-{rule.name}"></a>', "", *_quote(lines)]

    def _tables(self, spec: FormulaSpec) -> list[str]:
        columns = self.polish["columns"]
        lines: list[str] = []
        for table in spec.tables:
            rows = list(csv.reader(io.StringIO(self._table_text(table.path))))
            header, body = rows[0], rows[1:]
            source = table.source
            cited = _cell(source.text()) + (f" <{source.url}>" if source.url else "")
            part = [
                f"**Tablica `{table.path}`** · specyfikacja `{spec.name}` · "
                f"SHA-256 `{table.sha256}`",
                "",
                _row(*(_cell(columns[name]) for name in header)),
                "|" + "---|" * len(header),
                *(_row(*(_table_cell(value) for value in row)) for row in body),
                "",
                f"Źródło (w brzmieniu specyfikacji): {cited}. Dwie niezależne "
                f"transkrypcje porównano: {_cell(table.comparison)}",
                "",
                _GENERATED,
            ]
            if lines:
                lines.append("")
            lines += _quote(part)
        return lines

    # --- the indexes -----------------------------------------------------------------

    def _link(self, name: str) -> str:
        path = self.shown()[name][0]
        return f"[`{name}`]({path.name}#spec-{name})"

    def _chapter_links(self, name: str) -> str:
        return ", ".join(
            f"[{_label(path)}]({path.name}#spec-{name})" for path in self.shown()[name]
        )

    def _symbols(self) -> list[str]:
        rows: dict[tuple[str, str, str], list[str]] = {}
        for name in self.shown():
            if name not in self.formulas:
                continue
            spec = self.formulas[name]
            polish = self.polish["formulas"][name]
            items: list[tuple[str, str, str]] = [
                (v.symbol, polish["variables"][v.name], v.unit) for v in spec.variables
            ]
            items += [
                (o.symbol, polish["outputs"][o.name], o.unit)
                for o in spec.outputs
                if o.symbol
            ]
            items += [
                (c.symbol, polish["constants"][c.name], c.unit)
                for c in spec.constants
                if re.search(
                    r"[A-Za-z]", re.sub(r"\\[dt]?frac|\\cdot|\\times", "", c.symbol)
                )
            ]
            for key in items:
                names = rows.setdefault(key, [])
                if name not in names:
                    names.append(name)
        if not rows:
            return ["Podręcznik nie pokazuje jeszcze żadnego wzoru."]
        lines = ["| Symbol | Znaczenie | Jednostka | Wzory |", "|---|---|---|---|"]
        for (symbol, meaning, unit), names in sorted(
            rows.items(), key=lambda row: (_sort_key(row[0][0]), row[0][1], row[0][2])
        ):
            lines.append(
                _row(
                    self._symbol(symbol),
                    _cell(meaning),
                    self._unit(unit),
                    ", ".join(self._link(n) for n in names),
                )
            )
        return lines

    def _units(self) -> list[str]:
        units = sorted(self._units_of(self.shown()), key=str.casefold)
        if not units:
            return ["Podręcznik nie pokazuje jeszcze żadnego wzoru."]
        names = self.polish["units"]
        lines = ["| Jednostka | Zapis w Hydrologu | Nazwa |", "|---|---|---|"]
        lines += [
            _row(self._unit(unit), f"`{_cell(unit)}`", _cell(names[unit]["name"]))
            for unit in units
        ]
        return lines

    def _formulas_index(self) -> list[str]:
        shown = [name for name in self.shown() if name in self.formulas]
        if not shown:
            return ["Podręcznik nie pokazuje jeszcze żadnego wzoru."]
        lines = [
            "| Wzór | Specyfikacja | Wersja | Status | Przypadki referencyjne | "
            "Wyrocznie | Ramka |",
            "|---|---|---|---|---|---|---|",
        ]
        for name in sorted(shown):
            spec = self.formulas[name]
            kinds = sorted({_ORACLE[o.kind] for o in spec.oracles})
            lines.append(
                _row(
                    _cell(self.polish["formulas"][name]["title"]),
                    f"[`{name}`](../FORMULAS.md#{name})",
                    str(spec.formula_version),
                    f"`{spec.status}`",
                    str(len(spec.reference_cases)) if spec.reference_cases else "–",
                    ", ".join(kinds) or "–",
                    self._chapter_links(name),
                )
            )
        return lines

    def _commands(self) -> list[str]:
        chapters = [
            (path, text)
            for path, text in self.files.items()
            if _CHAPTER.fullmatch(path.name)
        ]
        lines = ["| Polecenie | Co robi | Rozdziały |", "|---|---|---|"]
        for name, summary in self.commands:
            used = re.compile(rf"(?<![\w/-])hydrolog {re.escape(name)}(?![\w-])")
            links = [
                f"[{_label(path)}]({path.name})"
                for path, text in chapters
                if used.search(text)
            ]
            lines.append(
                _row(f"`hydrolog {name}`", _cell(summary), ", ".join(links) or "–")
            )
        return lines


def _label(path: Path) -> str:
    """Return the number of a chapter (``4``) or the letter of an appendix (``A``)."""
    head = path.name.split("-", 1)[0]
    return str(int(head)) if head.isdigit() else head


def _sort_key(symbol: str) -> str:
    return re.sub(r"[\\{}_^ ]", "", symbol).casefold()


def _table_cell(value: str) -> str:
    if not value:
        return "–"
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", value):
        return value.replace(".", ",").replace("-", _MINUS)
    return _cell(value)


def handbook(root: Path = ROOT) -> Handbook:
    """Return the handbook of the project at ``root`` with its specs and catalog."""
    directory = root / "docs" / "podrecznik"
    files = {
        path: path.read_text(encoding="utf-8")
        for path in sorted(directory.glob("*.md"))
    }
    polish = tomllib.loads((directory / POLISH).read_text(encoding="utf-8"))
    return Handbook(
        files=files,
        polish=polish,
        formulas={spec.name: spec for spec in specs()},
        rules={rule.name: rule for rule in tier_b()},
        commands=[(c.name, c.summary_pl) for c in data_commands()],
        root=root,
    )


def _stale() -> list[str]:
    """Return the handbook files whose fragments differ from the generated ones."""
    book = handbook()
    return [
        _relative(path)
        for path, text in book.documents().items()
        if book.files[path] != text
    ]


def main(argv: list[str] | None = None) -> int:
    """Fill the fragments, or with ``--check`` fail when one is stale."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="do not write")
    parser.add_argument(
        "--template",
        nargs="+",
        metavar="NAME",
        help="print the entries of _specs_pl.toml to translate for these formulas",
    )
    args = parser.parse_args(argv)
    if args.template:
        known: dict[str, FormulaSpec | TierBSpec] = {s.name: s for s in specs()}
        known |= {rule.name: rule for rule in tier_b()}
        unknown = [name for name in args.template if name not in known]
        if unknown:
            print(f"no formula {', '.join(unknown)}", file=sys.stderr)
            return 1
        print("\n".join(template(known[name]) for name in args.template), end="")
        return 0
    try:
        book = handbook()
        done = book.documents()
    except HandbookError as error:
        for problem in error.problems:
            print(problem, file=sys.stderr)
        return 1
    stale = [path for path, text in done.items() if book.files[path] != text]
    if args.check:
        for path in stale:
            print(f"{_relative(path)} is stale: run {SCRIPT}")
        return 1 if stale else 0
    for path in stale:
        path.write_text(done[path], encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
