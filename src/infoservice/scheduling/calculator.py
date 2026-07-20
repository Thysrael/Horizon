from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter


class ScheduleValidationError(ValueError):
    """Raised when a report schedule cannot be calculated safely."""


_TIME = re.compile(r"^(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d)$")
_WEEKDAY = {
    "mon": 1,
    "monday": 1,
    "tue": 2,
    "tuesday": 2,
    "wed": 3,
    "wednesday": 3,
    "thu": 4,
    "thursday": 4,
    "fri": 5,
    "friday": 5,
    "sat": 6,
    "saturday": 6,
    "sun": 0,
    "sunday": 0,
}


@dataclass(frozen=True, slots=True)
class ScheduleSpec:
    kind: str
    value: str
    timezone: str
    expression: str = field(init=False)

    def __post_init__(self) -> None:
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ScheduleValidationError(f"Unknown timezone: {self.timezone}") from exc

        if self.kind == "daily":
            hour, minute = _parse_time(self.value)
            expression = f"{minute} {hour} * * *"
        elif self.kind == "weekdays":
            hour, minute = _parse_time(self.value)
            expression = f"{minute} {hour} * * 1-5"
        elif self.kind == "weekly":
            weekday, hour, minute = _parse_weekly(self.value)
            expression = f"{minute} {hour} * * {weekday}"
        elif self.kind == "cron":
            expression = self.value.strip()
            if not croniter.is_valid(expression):
                raise ScheduleValidationError("Invalid cron expression")
            _validate_minimum_hourly(expression)
        else:
            raise ScheduleValidationError(f"Unknown schedule kind: {self.kind}")
        object.__setattr__(self, "expression", expression)


def next_occurrence(spec: ScheduleSpec, after_utc: datetime) -> datetime:
    """Return the first schedule occurrence strictly after ``after_utc`` in UTC."""
    if after_utc.tzinfo is None:
        raise ScheduleValidationError("after_utc must be timezone-aware")

    timezone_info = ZoneInfo(spec.timezone)
    local_after = after_utc.astimezone(timezone_info).replace(tzinfo=None)
    wall_time = croniter(spec.expression, local_after).get_next(datetime)
    occurrence = _resolve_wall_time(wall_time, timezone_info)

    # A repeated local hour can yield its first instance before the UTC cursor.
    while occurrence <= after_utc.astimezone(timezone.utc):
        wall_time = croniter(spec.expression, wall_time).get_next(datetime)
        occurrence = _resolve_wall_time(wall_time, timezone_info)
    return occurrence


def _parse_time(value: str) -> tuple[int, int]:
    match = _TIME.fullmatch(value.strip())
    if match is None:
        raise ScheduleValidationError("Schedule time must be HH:MM")
    return int(match["hour"]), int(match["minute"])


def _parse_weekly(value: str) -> tuple[int, int, int]:
    parts = value.lower().split()
    if len(parts) != 2:
        raise ScheduleValidationError("Weekly schedule must be '<weekday> HH:MM'")
    weekday_value, time_value = parts
    if weekday_value.isdigit() and weekday_value in {"0", "1", "2", "3", "4", "5", "6", "7"}:
        weekday = int(weekday_value) % 7
    else:
        try:
            weekday = _WEEKDAY[weekday_value]
        except KeyError as exc:
            raise ScheduleValidationError("Unknown weekday") from exc
    hour, minute = _parse_time(time_value)
    return weekday, hour, minute


def _validate_minimum_hourly(expression: str) -> None:
    """Reject cron expressions which produce a gap shorter than one hour."""
    cursor = datetime(2026, 1, 1, tzinfo=timezone.utc)
    iterator = croniter(expression, cursor)
    end = cursor + timedelta(hours=48)
    previous = cursor
    while True:
        occurrence = iterator.get_next(datetime)
        if occurrence > end:
            return
        if occurrence - previous < timedelta(hours=1):
            raise ScheduleValidationError("Cron schedules may run at most once per hour")
        previous = occurrence


def _resolve_wall_time(wall_time: datetime, timezone_info: ZoneInfo) -> datetime:
    """Resolve a wall time, advancing gaps and preferring the first fold."""
    candidate = wall_time
    while True:
        occurrences = []
        for fold in (0, 1):
            local = candidate.replace(tzinfo=timezone_info, fold=fold)
            utc_value = local.astimezone(timezone.utc)
            if utc_value.astimezone(timezone_info).replace(tzinfo=None) == candidate:
                occurrences.append(utc_value)
        if occurrences:
            return min(occurrences)
        candidate += timedelta(minutes=1)
