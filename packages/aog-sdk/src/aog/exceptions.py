"""
Custom exceptions for AOG SDK.
"""


class AOGError(Exception):
    """Base exception for all AOG errors."""

    def __init__(self, message: str = "", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class AOGConfigError(AOGError):
    """Raised when AOG configuration is invalid."""

    pass


class AOGExportError(AOGError):
    """Raised when event export fails."""

    pass


class AOGValidationError(AOGError):
    """Raised when event validation fails."""

    pass


class AOGContextError(AOGError):
    """Raised when context operations fail."""

    pass


class AOGGraphIntegrityError(AOGError):
    """Raised when graph integrity is violated."""

    pass


class AOGTimeoutError(AOGError):
    """Raised when AOG operations time out."""

    pass
