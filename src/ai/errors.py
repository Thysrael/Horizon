"""Errors that require stopping AI work rather than retrying each item."""


class AIProviderUnavailableError(RuntimeError):
    """The account, permission, configuration, or allowance needs user action."""
