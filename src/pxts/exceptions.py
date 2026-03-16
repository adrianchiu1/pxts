"""pxts exception classes."""


class pxtsValidationError(TypeError):
    """Raised by standalone pxts functions when input is not a valid time series DataFrame.

    Subclasses TypeError so callers can catch either pxtsValidationError
    or TypeError. The pandas .ts accessor raises AttributeError instead
    (required by pandas accessor protocol — see accessor.py).
    """
