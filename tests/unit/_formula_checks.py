"""The checks of Nogat's computation standard for the tests of a formula family.

The reference module's ``run_case``, ``assert_property_contract``,
``assert_properties``, ``assert_limits`` and ``assert_case`` read the standard's
notice ``outside_applicability`` with ``details.variable`` or, for a violated
applicability constraint, ``details.constraint``. Until that code replaces
``outside_applicability`` together with its consumers (ADR-0050, point 3), the
library warns with :class:`~hydrolog._warnings.OutsideApplicability`, whose
``parameter`` is the input and whose ``constraint`` names a violated constraint:
:func:`as_standard` gives the assertions the function with each such warning read as
the standard's notice, and nothing else changed.
"""

import warnings
from collections.abc import Callable, Mapping

from hydrolog._warnings import OutsideApplicability


class _Applicability(UserWarning):
    """The notice ``outside_applicability`` as the reference module reads a warning."""

    code = "outside_applicability"

    def __init__(self, details: Mapping[str, object]) -> None:
        super().__init__(f"outside_applicability: {dict(details)}")
        self.details = dict(details)


def as_standard(function: Callable[..., object]) -> Callable[..., object]:
    """Return ``function`` with its ``outside_applicability`` read as the standard's.

    Parameters
    ----------
    function : callable
        A formula with a spec.

    Returns
    -------
    callable
        Takes the same keyword arguments and returns the same result; it issues each
        ``OutsideApplicability`` of the call as ``outside_applicability`` whose
        ``variable`` is the warning's ``parameter``, or whose ``constraint`` is the
        warning's for a violated constraint, and every other warning as it was.
    """

    def call(**inputs: object) -> object:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = function(**inputs)
        for item in caught:
            message = item.message
            if isinstance(message, OutsideApplicability) and message.details:
                details = dict(message.details)
                if details.get("constraint") is None:
                    details = {"variable": details["parameter"], **details}
                warnings.warn(_Applicability(details), stacklevel=2)
            else:
                warnings.warn_explicit(
                    message, item.category, item.filename, item.lineno
                )
        return result

    call.__qualname__ = getattr(function, "__qualname__", "call")
    return call
