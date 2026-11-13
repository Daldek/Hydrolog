"""The lines that the data providers' terms require on every product (Nogat DEV §20).

Hydrolog computes with data of IMGW-PIB and ČHMÚ: the PMAXTP depth that ``precip
pmaxtp`` fetches, and the station series that Obserwator exports or Archiwista hands
off. Their terms bind every product made with the data, so a result, a file Hydrolog
writes and every view of the GUI carry, verbatim, the lines below (Nogat's standard,
DEV-20.1 to DEV-20.7, decisions ECO-060 and ECO-065). This module is their one source in
Hydrolog.

Attribution lines, in the order of DEV-20.4:

* :data:`IMGW_SOURCE` (S) and :data:`IMGW_PROCESSED` (P): data of
  danepubliczne.imgw.pl (archives, station series) and of hydro.imgw.pl; §5 ust. 3 and 4
  of the IMGW-PIB terms;
* :data:`PMAXTP_SOURCE` (PS), :data:`PMAXTP_PROCESSED` (PP) and the monograph
  :data:`PMAXTP_MONOGRAPH` (M): data of the PMAXTP project, whose own terms replace S
  and P (ust. 1 and 2);
* :data:`CHMI_SOURCE` (C) and :data:`CHMI_PROCESSED` (CP): ČHMÚ open data under CC BY
  4.0, whose §3(a)(1) asks for the creator, the address, the licence with its link and
  the fact of a modification; a producer's own CP (Obserwator's "normalizacja i zmiana
  formatu") is kept before Hydrolog's.

The terms lines (DEV-20.7), a link to each terms that apply, in their order:
:data:`TERMS_DANEPUBLICZNE` (RD), :data:`TERMS_HYDRO` (RH), :data:`TERMS_PMAXTP` (RK);
none for ČHMÚ, whose C links its licence. No product restates the terms (ECO-065).

Hydrolog processes every input it computes with, so a product always has the processed
line of its provider: :class:`Attribution` turns the providers found in an input into
their complete lines. It recognises the lines it knows (a final full stop and the
surrounding blanks ignored; a ČHMÚ credit by its beginning, whatever its producer's
wording after it) and carries any other line verbatim, after the known ones, so no
producer's line is ever dropped. The lines Nogat retired (ECO-065) are read as what they
stood for, so an input or an ``ATTRIBUTION.txt`` written before gives the current lines:
the line of hydro.imgw.pl (H) names its provider, the old „Regulamin: <address>” of a
known terms becomes its new line, and IMGW-PIB's summary of its terms (N) and any other
„Regulamin: …” line are dropped.

A command collects the lines of its run: :func:`~hydrolog.catalog.run_command` opens
:func:`collecting`, the readers of input files :func:`cite` the lines a file carries
(the CSV columns ``attribution`` and ``terms_notice``, Obserwator's
``attribution_source`` and ``attribution_processed``, the fields ``attribution`` and
``terms_notice`` of a JSON document), an operation cites its option ``attribution`` and
the lines of its own source, a writing operation puts :func:`current` into its files,
and the envelope gets the fields ``attribution`` and ``terms_notice``.

The module is a leaf (standard library only), so the catalog, the readers and the
operations import it without cycles.
"""

from __future__ import annotations

import contextlib
import contextvars
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal, get_args

__all__ = [
    "ATTRIBUTION_FILE",
    "ATTRIBUTION_COLUMN",
    "CHMI_PROCESSED",
    "CHMI_SOURCE",
    "CSV_COLUMNS",
    "IMGW_PROCESSED",
    "IMGW_SOURCE",
    "PMAXTP_MONOGRAPH",
    "PMAXTP_PROCESSED",
    "PMAXTP_SOURCE",
    "PMAXTP_TERMS_URL",
    "PROVIDERS",
    "TERMS_COLUMN",
    "TERMS_DANEPUBLICZNE",
    "TERMS_HYDRO",
    "TERMS_PMAXTP",
    "Attribution",
    "Collector",
    "Provider",
    "attribution_text",
    "cite",
    "collecting",
    "csv_with_attribution",
    "current",
    "lines_of_columns",
    "lines_of_document",
    "provider_lines",
    "retired_lines",
]

Provider = Literal["imgw", "imgw_hydro", "pmaxtp", "chmi"]
"""A provider whose terms Hydrolog knows: IMGW-PIB's public data
(danepubliczne.imgw.pl), its hydrological service (hydro.imgw.pl), the PMAXTP project,
ČHMÚ's open data."""
PROVIDERS: Final[tuple[str, ...]] = get_args(Provider)
"""The values of :data:`Provider`, in the order of their lines."""

_IMGW: Final = "Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy"
_IMGW_GENITIVE: Final = (
    "Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego"
)
_PMAXTP_PAGE: Final = "https://klimat.imgw.pl/opady-maksymalne"

IMGW_SOURCE: Final = f"Źródłem pochodzenia danych jest {_IMGW}"
"""S: the source of IMGW-PIB's data (§5 ust. 3 of the terms)."""
IMGW_PROCESSED: Final = f"Dane {_IMGW_GENITIVE} zostały przetworzone"
"""P: the data of IMGW-PIB were processed (§5 ust. 4 of the terms)."""
_HYDRO_TERMS_PAGE: Final = "https://hydro.imgw.pl/#/regulamin"
PMAXTP_SOURCE: Final = f"{IMGW_SOURCE}, dane pochodzą ze strony {_PMAXTP_PAGE}"
"""PS: the source of PMAXTP's data and the project's address (ust. 1 of its terms)."""
PMAXTP_PROCESSED: Final = (
    f"Dane {_IMGW_GENITIVE} pochodzące ze strony {_PMAXTP_PAGE} zostały przetworzone"
)
"""PP: the data of PMAXTP were processed (ust. 2 of its terms)."""
PMAXTP_MONOGRAPH: Final = (
    "„Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i "
    "prawdopodobieństwie przewyższenia – Projekt PMAXTP”, red. Bogdan Ozga-Zieliński, "
    f"{_IMGW}, Warszawa 2022"
)
"""M: the monograph of the PMAXTP project, which its terms require (ust. 1)."""
CHMI_SOURCE: Final = (
    "Źródło danych: Český hydrometeorologický ústav (ČHMÚ), https://opendata.chmi.cz, "
    "licencja CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)"
)
"""C: the creator, the address of the material and the licence with its link."""
CHMI_PROCESSED: Final = (
    "Dane ČHMÚ zostały przetworzone (obliczenia hydrologiczne programem Hydrolog)"
)
"""CP: what Hydrolog did with ČHMÚ's data (CC BY 4.0, §3(a)(1)(B))."""
TERMS_DANEPUBLICZNE: Final = (
    "Regulamin danych IMGW-PIB: https://danepubliczne.imgw.pl/regulations"
)
"""RD: the terms of danepubliczne.imgw.pl."""
TERMS_HYDRO: Final = f"Regulamin serwisu hydrologicznego IMGW-PIB: {_HYDRO_TERMS_PAGE}"
"""RH: the terms of hydro.imgw.pl."""
TERMS_PMAXTP: Final = f"Regulamin danych PMAXTP: {_PMAXTP_PAGE}"
"""RK: the terms of PMAXTP, a dialog on the project's page."""
PMAXTP_TERMS_URL: Final = _PMAXTP_PAGE
"""The page of PMAXTP whose dialog holds its terms."""

ATTRIBUTION_FILE: Final = "ATTRIBUTION.txt"
"""The file of the lines beside files without a place of their own (DEV-20.5): at the
root of an output directory."""
ATTRIBUTION_COLUMN: Final = "attribution"
"""The CSV column of the attribution lines (DEV-20.5)."""
TERMS_COLUMN: Final = "terms_notice"
"""The CSV column of the terms notice (DEV-20.5)."""
_SOURCE_COLUMNS: Final = ("attribution_source", "attribution_processed")
"""Obserwator's columns of its two lines, read like ``attribution`` (DEV-20.6)."""
CSV_COLUMNS: Final = (ATTRIBUTION_COLUMN, TERMS_COLUMN, *_SOURCE_COLUMNS)
"""Every column that holds lines, not data."""

_CHMI_CREDIT: Final = "Źródło danych: Český hydrometeorologický ústav (ČHMÚ)"
"""How every ČHMÚ credit begins, whatever its producer wrote after it."""
_CHMI_MODIFIED: Final = "Dane ČHMÚ zostały przetworzone"
"""How every statement of a modification of ČHMÚ's data begins."""
_TERMS_LINE: Final = re.compile(r"Regulamin [^:]+: \S")
"""The form of every terms line, „Regulamin <whose terms>: <address>” (DEV §20)."""
_RETIRED_TERMS_PREFIX: Final = "Regulamin: "
"""How a terms line began before ECO-065, without whose terms it links."""
_RETIRED_PROVIDER_OF: Final[Mapping[str, str]] = {
    "Dane pochodzą z serwisu hydrologicznego IMGW-PIB https://hydro.imgw.pl": (
        "imgw_hydro"
    ),
}
"""H, retired by ECO-065, and the provider it names."""
_RETIRED_TERMS: Final[Mapping[str, str]] = {
    "Regulamin: https://danepubliczne.imgw.pl/regulations": TERMS_DANEPUBLICZNE,
    f"Regulamin: {_HYDRO_TERMS_PAGE}": TERMS_HYDRO,
    f"Regulamin: {_PMAXTP_PAGE}": TERMS_PMAXTP,
}
"""The terms lines of before ECO-065 and the lines that replace them."""
_RETIRED_NOTICE: Final = (
    "Dane IMGW-PIB można wykorzystywać nieodpłatnie do celów prywatnych "
    "(niezarobkowych). Wykorzystanie w działalności gospodarczej, na stronach z "
    "reklamami lub do celów wymienionych w regulaminie (m.in. planowanie w "
    "gospodarowaniu wodami, art. 317 Prawa wodnego) wymaga umowy z IMGW-PIB."
)
"""N, IMGW-PIB's terms summarised, retired by ECO-065: recognised only to be dropped."""

_LINES: Final[Mapping[str, tuple[str, ...]]] = {
    "imgw": (IMGW_SOURCE, IMGW_PROCESSED),
    "imgw_hydro": (IMGW_SOURCE, IMGW_PROCESSED),
    "pmaxtp": (PMAXTP_SOURCE, PMAXTP_PROCESSED, PMAXTP_MONOGRAPH),
    "chmi": (CHMI_SOURCE, CHMI_PROCESSED),
}
_TERMS: Final[Mapping[str, tuple[str, ...]]] = {
    "imgw": (TERMS_DANEPUBLICZNE,),
    "imgw_hydro": (TERMS_HYDRO,),
    "pmaxtp": (TERMS_PMAXTP,),
    "chmi": (),
}
_ORDER: Final = (
    IMGW_SOURCE,
    IMGW_PROCESSED,
    PMAXTP_SOURCE,
    PMAXTP_PROCESSED,
    PMAXTP_MONOGRAPH,
    CHMI_SOURCE,
)
"""The known attribution lines before the ČHMÚ modifications (DEV-20.4)."""
_TERMS_ORDER: Final = (TERMS_DANEPUBLICZNE, TERMS_HYDRO, TERMS_PMAXTP)
"""The known terms lines, in the order of DEV-20.7."""
_PROVIDER_OF: Final[Mapping[str, str]] = {
    IMGW_SOURCE: "imgw",
    IMGW_PROCESSED: "imgw",
    PMAXTP_SOURCE: "pmaxtp",
    PMAXTP_PROCESSED: "pmaxtp",
    PMAXTP_MONOGRAPH: "pmaxtp",
    CHMI_SOURCE: "chmi",
    CHMI_PROCESSED: "chmi",
}


def _key(line: str) -> str:
    """Return the form a line is recognised by: no blanks around, no final full stop."""
    return line.strip().removesuffix(".").rstrip()


_KNOWN: Final[Mapping[str, str]] = {
    _key(line): provider
    for line, provider in (*_PROVIDER_OF.items(), *_RETIRED_PROVIDER_OF.items())
}
"""The provider each known attribution line names, by its recognised form."""
_KNOWN_TERMS: Final[Mapping[str, str]] = {
    **{_key(line): line for line in _TERMS_ORDER},
    **{_key(old): line for old, line in _RETIRED_TERMS.items()},
}
"""The current terms line each known terms line stands for, by its recognised form."""


def _split(lines: Iterable[object]) -> Iterator[str]:
    """Yield every non-empty line of ``lines``; a cell may hold several, one per row."""
    for item in lines:
        if not isinstance(item, str):
            continue
        for line in item.splitlines():
            if line.strip():
                yield line.strip()


def _union(*groups: Iterable[str]) -> tuple[str, ...]:
    """Return the lines of every group in their first order, each once."""
    return tuple(dict.fromkeys(line for group in groups for line in group))


@dataclass(frozen=True)
class Attribution:
    """The provider lines of a product: its attribution and the terms notice.

    Build it from providers (:meth:`of`) or from the lines of an input
    (:meth:`from_lines`), merge with ``|`` and read :attr:`lines` and
    :attr:`terms_notice`, each complete and in the order of DEV-20.4 and DEV-20.7.

    Attributes
    ----------
    providers : frozenset of str
        The providers (:data:`Provider`) whose data the product holds.
    other_lines : tuple of str
        Attribution lines Hydrolog does not know (a producer's statement of what it did
        with ČHMÚ's data, another provider's credit), verbatim, in their first order.
    terms : frozenset of str
        The known terms lines given with the data.
    other_terms : tuple of str
        Terms lines Hydrolog does not know, verbatim, in their first order.
    """

    providers: frozenset[str] = frozenset()
    other_lines: tuple[str, ...] = ()
    terms: frozenset[str] = frozenset()
    other_terms: tuple[str, ...] = ()

    @classmethod
    def of(cls, *providers: Provider) -> Attribution:
        """Return the lines of data of ``providers``.

        Parameters
        ----------
        *providers : {"imgw", "imgw_hydro", "pmaxtp", "chmi"}
            The providers of the data.

        Returns
        -------
        Attribution
            Their complete lines.

        Raises
        ------
        ValueError
            If a provider is not one of :data:`PROVIDERS`.
        """
        unknown = [name for name in providers if name not in PROVIDERS]
        if unknown:
            raise ValueError(f"unknown providers {unknown}; known: {list(PROVIDERS)}")
        return cls(providers=frozenset(providers))

    @classmethod
    def from_lines(
        cls, lines: Iterable[object] = (), terms: Iterable[object] = ()
    ) -> Attribution:
        """Recognise the lines of an input.

        A known line names its provider, whose complete lines the result then has (a
        ČHMÚ credit is known by its beginning and replaced by :data:`CHMI_SOURCE`, which
        has every element the licence asks for); a statement of a modification of
        ČHMÚ's data other than Hydrolog's is kept. A known terms line is a terms line
        wherever it is given; any other line is kept verbatim, as a terms line when it
        is given in ``terms`` or has the form „Regulamin <whose terms>: <address>”. A
        line retired by ECO-065 is read as what it stood for (see the module).

        Parameters
        ----------
        lines : iterable of str
            Attribution lines; a string may hold several, one per text line. Items that
            are not strings are skipped.
        terms : iterable of str
            Lines of a terms notice, the same way.

        Returns
        -------
        Attribution
            The providers found and the lines kept.
        """
        providers: set[str] = set()
        known_terms: set[str] = set()
        others: list[str] = []
        other_terms: list[str] = []
        given = [(line, False) for line in _split(lines)]
        given += [(line, True) for line in _split(terms)]
        for line, is_terms in given:
            key = _key(line)
            if key in _KNOWN:
                providers.add(_KNOWN[key])
            elif key in _KNOWN_TERMS:
                known_terms.add(_KNOWN_TERMS[key])
            elif key == _key(_RETIRED_NOTICE) or line.startswith(_RETIRED_TERMS_PREFIX):
                continue  # N, or the bare address of a terms Hydrolog does not know
            elif line.startswith(_CHMI_CREDIT):
                providers.add("chmi")
            elif line.startswith(_CHMI_MODIFIED):
                providers.add("chmi")
                others.append(line)
            elif is_terms or _TERMS_LINE.match(line):
                other_terms.append(line)
            else:
                others.append(line)
        return cls(
            providers=frozenset(providers),
            other_lines=_union(others),
            terms=frozenset(known_terms),
            other_terms=_union(other_terms),
        )

    def __or__(self, other: Attribution) -> Attribution:
        """Return the lines of both products, each once."""
        return Attribution(
            providers=self.providers | other.providers,
            other_lines=_union(self.other_lines, other.other_lines),
            terms=self.terms | other.terms,
            other_terms=_union(self.other_terms, other.other_terms),
        )

    def __bool__(self) -> bool:
        """Return ``True`` when the product has any line."""
        return bool(self.lines or self.terms_notice)

    @property
    def lines(self) -> tuple[str, ...]:
        """Tuple of str: the attribution lines, in the order of DEV-20.4."""
        known = {line for name in self.providers for line in _LINES[name]}
        modified = [
            line for line in self.other_lines if line.startswith(_CHMI_MODIFIED)
        ]
        rest = [line for line in self.other_lines if line not in modified]
        chmi = (*modified, CHMI_PROCESSED) if "chmi" in self.providers else modified
        return _union((line for line in _ORDER if line in known), chmi, rest)

    @property
    def terms_notice(self) -> tuple[str, ...]:
        """Tuple of str: the terms notice, in the order of DEV-20.7."""
        known = set(self.terms).union(*(_TERMS[name] for name in self.providers))
        return _union(
            (line for line in _TERMS_ORDER if line in known), self.other_terms
        )

    def to_dict(self) -> dict[str, list[str]]:
        """Return ``attribution`` and ``terms_notice`` as lists, each when not empty.

        Returns
        -------
        dict
            The fields of a JSON document (DEV-20.6, DEV-20.7).
        """
        fields: dict[str, list[str]] = {}
        if self.lines:
            fields["attribution"] = list(self.lines)
        if self.terms_notice:
            fields["terms_notice"] = list(self.terms_notice)
        return fields


def provider_lines() -> dict[str, dict[str, list[str]]]:
    """Return the complete lines of each provider, for a client that names a provider.

    Returns
    -------
    dict
        ``{provider: {"attribution": [...], "terms_notice": [...]}}`` for every
        :data:`Provider`; ``terms_notice`` is empty for ČHMÚ.
    """
    return {
        name: {
            "attribution": list(_LINES[name]),
            "terms_notice": list(Attribution(providers=frozenset({name})).terms_notice),
        }
        for name in PROVIDERS
    }


def retired_lines() -> dict[str, str | None]:
    """Return the lines retired by ECO-065, each with the line that replaces it.

    For a client that keeps lines Hydrolog gave before (the GUI's kept PMAXTP depth, an
    older hand-off) and shows them without a run, which would replace them.

    Returns
    -------
    dict
        ``{retired line: its current line, or None when it is dropped}``: H and N
        go (S and P stand beside H), the old addresses of RD, RH and RK become the
        new ones.
    """
    return {
        **dict.fromkeys(_RETIRED_PROVIDER_OF),
        _RETIRED_NOTICE: None,
        **_RETIRED_TERMS,
    }


def _cell(text: str) -> str:
    """Return a CSV cell: quoted when it holds a separator, a quote or a line end."""
    if any(character in text for character in ',"\n\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def _column(lines: Sequence[str], rows: int) -> list[str]:
    """Return the cells of a column of lines in ``rows`` rows (DEV-20.5)."""
    cells = list(lines[: rows - 1]) if len(lines) > rows else list(lines)
    if len(lines) > rows:
        cells.append("\n".join(lines[rows - 1 :]))
    return cells + [""] * (rows - len(cells))


def attribution_text(attribution: Attribution, existing: str = "") -> str:
    """Return the text of :data:`ATTRIBUTION_FILE` (DEV-20.5).

    One line per line, the attribution lines first, then the terms notice; the lines of
    a file already there are kept, merged with the new ones, each once and in order.

    Parameters
    ----------
    attribution : Attribution
        The lines of the data written.
    existing : str, optional
        The text of the file already there.

    Returns
    -------
    str
        UTF-8 text with LF line ends and a final one.
    """
    merged = Attribution.from_lines(existing.splitlines()) | attribution
    return "".join(f"{line}\n" for line in (*merged.lines, *merged.terms_notice))


def csv_with_attribution(text: str, attribution: Attribution) -> str:
    """Append the columns ``attribution`` and ``terms_notice`` to a CSV table.

    The form of DEV-20.5: two trailing columns, one line per cell from the first data
    row down, empty cells below; a table with fewer rows than lines joins the rest into
    its last row's cell with a line end. Without lines the text is returned unchanged.

    Parameters
    ----------
    text : str
        The table: a header and at least one data row, comma separated, LF line ends
        (Hydrolog's tables, ``Hydrograph.to_table``).
    attribution : Attribution
        The lines of the table's data.

    Returns
    -------
    str
        The table with the two columns, LF line ends and a final one.

    Raises
    ------
    ValueError
        If the table has no data row to hold the lines.
    """
    if not attribution:
        return text
    rows = text.splitlines()
    header, data = rows[0], rows[1:]
    if not data:
        raise ValueError("a table without data rows cannot hold attribution lines")
    lines = _column(attribution.lines, len(data))
    terms = _column(attribution.terms_notice, len(data))
    out = [f"{header},{ATTRIBUTION_COLUMN},{TERMS_COLUMN}"]
    out += [
        f"{row},{_cell(line)},{_cell(term)}"
        for row, line, term in zip(data, lines, terms, strict=True)
    ]
    return "\n".join(out) + "\n"


def lines_of_columns(columns: Mapping[str, Sequence[object]]) -> Attribution:
    """Recognise the lines of the attribution columns of a table.

    Parameters
    ----------
    columns : Mapping[str, sequence]
        Cells by column name; columns other than those of :data:`CSV_COLUMNS` are
        ignored.

    Returns
    -------
    Attribution
        The lines of ``attribution``, ``attribution_source``, ``attribution_processed``
        and ``terms_notice``.
    """
    lines = [
        cell
        for name in (*_SOURCE_COLUMNS, ATTRIBUTION_COLUMN)
        for cell in columns.get(name, ())
    ]
    return Attribution.from_lines(lines, columns.get(TERMS_COLUMN, ()))


def lines_of_document(document: object) -> Attribution:
    """Recognise the fields ``attribution`` and ``terms_notice`` of a JSON document.

    Parameters
    ----------
    document : object
        A parsed JSON document; only an object's fields that are lists are read.

    Returns
    -------
    Attribution
        Their lines (empty for anything else).
    """
    if not isinstance(document, Mapping):
        return Attribution()
    lines = document.get(ATTRIBUTION_COLUMN)
    terms = document.get(TERMS_COLUMN)
    return Attribution.from_lines(
        lines if isinstance(lines, list) else (),
        terms if isinstance(terms, list) else (),
    )


@dataclass
class Collector:
    """The lines a run has met so far (see :func:`collecting`).

    Attributes
    ----------
    value : Attribution
        Their union.
    """

    value: Attribution = field(default_factory=Attribution)

    def add(self, attribution: Attribution) -> None:
        """Merge ``attribution`` into :attr:`value`."""
        self.value = self.value | attribution


_ACTIVE: contextvars.ContextVar[Collector | None] = contextvars.ContextVar(
    "hydrolog_attribution", default=None
)


@contextlib.contextmanager
def collecting() -> Iterator[Collector]:
    """Collect the lines that :func:`cite` meets inside the block.

    A block inside another hands its lines to the outer one when it ends.

    Yields
    ------
    Collector
        The lines met, complete when the block ends.
    """
    outer = _ACTIVE.get()
    collector = Collector()
    token = _ACTIVE.set(collector)
    try:
        yield collector
    finally:
        _ACTIVE.reset(token)
        if outer is not None:
            outer.add(collector.value)


def cite(attribution: Attribution | Iterable[str] | None) -> None:
    """Record lines of the data a run uses (nothing outside :func:`collecting`).

    Parameters
    ----------
    attribution : Attribution, iterable of str or None
        The lines, or lines to recognise (:meth:`Attribution.from_lines`, attribution
        and terms lines mixed, as the option ``attribution`` gives them).
    """
    collector = _ACTIVE.get()
    if collector is None or attribution is None:
        return
    if not isinstance(attribution, Attribution):
        attribution = Attribution.from_lines(attribution)
    collector.add(attribution)


def current() -> Attribution:
    """Return the lines the run has met so far (empty outside :func:`collecting`).

    Returns
    -------
    Attribution
        What a writing operation puts into its files.
    """
    collector = _ACTIVE.get()
    return Attribution() if collector is None else collector.value
