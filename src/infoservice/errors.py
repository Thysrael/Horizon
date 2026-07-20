"""Domain errors whose messages are safe to show to a bot user."""


class InfoServiceError(Exception):
    """Base class for expected application errors."""


class NotFound(InfoServiceError):
    """The requested resource does not exist or is not owned by the user."""


class LimitExceeded(InfoServiceError):
    """A product limit prevents the requested operation."""


class Conflict(InfoServiceError):
    """The requested state conflicts with an existing resource."""
