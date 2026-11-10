"""The one place a collection window is validated."""


def collection_hours(configured: int, override: int | None = None) -> int:
    """Return the hours a collection run will use.

    A configuration value arrives as ``configured``. A CLI flag or an MCP
    argument arrives as ``override`` and replaces it. Call this once where
    those inputs meet, and pass the returned int inward. Nothing past this
    function checks the window again.
    """
    hours = configured if override is None else override
    if isinstance(hours, bool) or not isinstance(hours, int) or hours <= 0:
        raise ValueError("hours must be greater than 0")
    return hours
