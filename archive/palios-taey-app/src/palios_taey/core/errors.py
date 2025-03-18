"""Core error definitions for PALIOS-TAEY."""


class PaliosTaeyError(Exception):
    """Base exception for all PALIOS-TAEY errors."""
    pass


class ValidationError(PaliosTaeyError):
    """Raised when validation fails."""
    pass


class NotFoundError(PaliosTaeyError):
    """Raised when a requested resource is not found."""
    pass


class AuthorizationError(PaliosTaeyError):
    """Raised when authorization fails."""
    pass


class ConfigurationError(PaliosTaeyError):
    """Raised when there is a configuration error."""
    pass


class ExternalServiceError(PaliosTaeyError):
    """Raised when an external service request fails."""
    pass
