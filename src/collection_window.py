"""Single validation boundary for collection time windows."""

from typing import Annotated

from pydantic import AfterValidator


def require_positive_hours(hours: int) -> int:
    """Return ``hours`` when it is a positive collection window.

    Configuration values and external overrides enter through this function.
    Callers that already hold the returned value do not validate it again.
    """
    if isinstance(hours, bool) or not isinstance(hours, int) or hours <= 0:
        raise ValueError("hours must be greater than 0")
    return hours


PositiveHours = Annotated[int, AfterValidator(require_positive_hours)]
