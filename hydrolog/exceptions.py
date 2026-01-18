"""Custom exceptions for Hydrolog library."""


class HydrologError(Exception):
    """Base exception for Hydrolog."""

    pass


class InvalidParameterError(HydrologError):
    """Invalid parameter value."""

    pass


class CalculationError(HydrologError):
    """Error during calculation."""

    pass
