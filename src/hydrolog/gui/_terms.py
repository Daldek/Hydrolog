"""The regulamin of a public GUI (Nogat DEV-15.7, ECO-061 to ECO-063).

A deployment that sets ``[nogat.operator]`` in ``nogat.toml`` opens the GUI to anyone,
and the GUI then serves its terms at ``regulamin.html`` beside its page: the template
of Nogat's GUI kit (``web/nogat/nogat-terms.html``, a byte-for-byte copy) filled as
Nogat's ``design/README.md`` says, in two steps (reference: ``fill`` of Nogat's
``scripts/terms.py``):

1. Blocks. The lines between ``<!-- block: <name> -->`` and ``<!-- /block -->`` stay,
   without the two marker lines, for the blocks of Hydrolog's data sources
   (:data:`BLOCKS`); every other block goes with its markers. Each source block holds
   the provider's required lines and the link to its terms, never a summary of them
   (Nogat DEV-20.7, ECO-065).
2. Fields. Every ``{{name}}`` becomes its value, HTML-escaped. Every field needs a
   value, non-empty but for :data:`OPTIONAL`.

Hydrolog's data sources (ADR-0034): the PMAXTP depth that Hydrogram zlewni fetches
(``pmaxtp``) and the station series of IMGW-PIB and ČHMÚ that Archiwista hands off and
Obserwator exports (``imgw``, ``chmi``). The GUI draws no map, so no basemap block.

A missing operator field or a value that cannot be used is a :class:`TermsError`: the
GUI then serves no page and no link, as the kit's README asks.
"""

from __future__ import annotations

import datetime as dt
import html
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from hydrolog.gui import WEB_DIR

__all__ = [
    "BLOCKS",
    "OPERATOR_FIELDS",
    "OPTIONAL",
    "PAGE",
    "TEMPLATE",
    "Terms",
    "TermsError",
    "fill",
    "load_terms",
]

TEMPLATE: Final = WEB_DIR / "nogat" / "nogat-terms.html"
"""The kit's template of the regulamin (Nogat kit 0.6.0, regulamin 1.0)."""
PAGE: Final = "regulamin.html"
"""The address of the filled regulamin, relative to the GUI's page."""
BLOCKS: Final[tuple[str, ...]] = ("imgw", "pmaxtp", "chmi")
"""The blocks of Hydrolog's data sources (Nogat ``design/README.md``)."""
OPTIONAL: Final = frozenset({"processor_transfer", "processor_cookie", "mail_transfer"})
"""The fields whose value may be empty (each is a whole sentence or nothing)."""
OPERATOR_FIELDS: Final[Mapping[str, str]] = {
    "operator_name": "name",
    "operator_email": "email",
    "terms_effective": "terms_effective",
    "processor": "processor",
    "processor_transfer": "processor_transfer",
    "processor_cookie": "processor_cookie",
    "mail_provider": "mail_provider",
    "mail_transfer": "mail_transfer",
}
"""The fields of the template that ``[nogat.operator]`` gives: field -> its key."""
PROJECT: Final[Mapping[str, str]] = {
    "service_name": "Hydrolog",
    "software_licence": "MIT",
    "source_url": "https://github.com/Daldek/Hydrolog",
    "tokens_href": "nogat/tokens.css",
    "kit_href": "nogat/",
}
"""The fields Hydrolog gives itself: its registry name, the ``license`` of
``pyproject.toml``, the ``repo`` of its entry in Nogat's ``ecosystem.yaml`` and its
copies of ``tokens.css`` and the kit, relative to ``regulamin.html``."""

_PLACEHOLDER = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
_BLOCK = re.compile(
    r"^<!-- block: (?P<name>[a-z][a-z0-9-]*) -->\n(?P<body>.*?)^<!-- /block -->\n",
    re.MULTILINE | re.DOTALL,
)


class TermsError(ValueError):
    """The regulamin cannot be filled: a field is missing or unusable."""


@dataclass(frozen=True)
class Terms:
    """The filled regulamin of a deployment.

    Attributes
    ----------
    page : bytes
        ``regulamin.html`` in UTF-8, ready to serve.
    operator_email : str
        The operator's address (``[nogat.operator] email``), also the one „Zgłoś
        uwagę” names.
    """

    page: bytes
    operator_email: str


def fill(template: str, values: Mapping[str, str], listed: Iterable[str]) -> str:
    """Return the template with its blocks chosen and its fields filled.

    Parameters
    ----------
    template : str
        The kit's ``nogat-terms.html``.
    values : Mapping
        A value for every field of the template; only :data:`OPTIONAL` ones may be
        empty.
    listed : iterable of str
        The blocks to keep.

    Returns
    -------
    str
        The page, every value HTML-escaped.

    Raises
    ------
    TermsError
        When a field has no value, an empty one it may not have, or a ``{{`` is left.
    """
    keep = set(listed)
    missing = sorted(
        name
        for name in set(_PLACEHOLDER.findall(template))
        if name not in values or (name not in OPTIONAL and not values[name].strip())
    )
    if missing:
        raise TermsError(f"missing values: {', '.join(missing)}")
    text = _BLOCK.sub(lambda m: m["body"] if m["name"] in keep else "", template)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = _PLACEHOLDER.sub(lambda m: html.escape(values[m[1]].strip()), text)
    if "{{" in text:
        raise TermsError("a field of the template is left unfilled")
    return text


def _text(value: object) -> str | None:
    """Return a value of ``[nogat.operator]`` as text: a string, or a TOML date."""
    if isinstance(value, str):
        return value
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value.isoformat()
    return None


def operator_values(
    operator: Mapping[str, Any], service_url: str | None
) -> dict[str, str]:
    """Return the values of the template's fields for a deployment.

    Parameters
    ----------
    operator : Mapping
        The table ``[nogat.operator]`` of ``nogat.toml``.
    service_url : str or None
        Hydrolog's address, its entry of ``[nogat] gui``.

    Returns
    -------
    dict
        Every field that has a usable value: Hydrolog's own (:data:`PROJECT`), the
        service's address and the operator's; a field without a usable value is left
        out, so :func:`fill` names it.
    """
    values = dict(PROJECT)
    if service_url and service_url.strip():
        values["service_url"] = service_url.strip()
    for field, key in OPERATOR_FIELDS.items():
        text = _text(operator.get(key))
        if text is not None:
            values[field] = text
    return values


def load_terms(
    operator: Mapping[str, Any], service_url: str | None, template: Path = TEMPLATE
) -> Terms:
    """Fill the kit's regulamin for a deployment.

    Parameters
    ----------
    operator : Mapping
        The table ``[nogat.operator]`` of ``nogat.toml``.
    service_url : str or None
        Hydrolog's address, its entry of ``[nogat] gui``.
    template : Path, optional
        The template, the kit's ``nogat-terms.html`` by default.

    Returns
    -------
    Terms
        The page and the operator's address.

    Raises
    ------
    TermsError
        When a field is missing or unusable, or the template cannot be read.
    """
    values = operator_values(operator, service_url)
    try:
        source = template.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise TermsError(f"the template {template.name} cannot be read") from exc
    page = fill(source, values, BLOCKS)
    return Terms(page=page.encode("utf-8"), operator_email=values["operator_email"])
