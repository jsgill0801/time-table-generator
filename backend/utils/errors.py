"""
Custom exception classes used across the backend.

These provide clear, descriptive errors instead of generic
Python exceptions, making debugging and API error responses
much easier.
"""


class DataError(Exception):
    """
    Raised when input data is invalid.

    Attributes:
        field   -- the field that caused the error
        message -- human-readable explanation
        row     -- optional row number (for CSV parsing)
    """

    def __init__(self, field, message, row=None):
        self.field = field
        self.message = message
        self.row = row
        super().__init__(self._format())

    def _format(self):
        if self.row is not None:
            return f"Row {self.row}, field '{self.field}': {self.message}"
        return f"Field '{self.field}': {self.message}"


class ValidationError(Exception):
    """
    Raised when pre-generation validation fails.

    Contains a list of individual problems found during
    the integrity check so they can all be reported at once.
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s)")


class SchedulingError(Exception):
    """
    Raised when the scheduling engine encounters a
    fatal problem that prevents it from continuing.
    """
    pass


class AuthError(Exception):
    """
    Raised for authentication/authorisation failures
    (bad credentials, duplicate username, etc.).
    """
    pass
