from datetime import datetime, timezone

import pytest

from src.infoservice.scheduling.calculator import ScheduleSpec, ScheduleValidationError, next_occurrence


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_daily_moscow_schedule_returns_utc():
    spec = ScheduleSpec(kind="daily", value="09:00", timezone="Europe/Moscow")

    assert next_occurrence(spec, dt("2026-07-20T05:00:00Z")) == dt("2026-07-20T06:00:00Z")


def test_weekdays_skips_weekend():
    spec = ScheduleSpec(kind="weekdays", value="09:00", timezone="UTC")

    assert next_occurrence(spec, dt("2026-07-17T10:00:00Z")) == dt("2026-07-20T09:00:00Z")


def test_weekly_uses_iso_weekday_and_time():
    spec = ScheduleSpec(kind="weekly", value="mon 09:00", timezone="UTC")

    assert next_occurrence(spec, dt("2026-07-20T09:00:00Z")) == dt("2026-07-27T09:00:00Z")


def test_cron_rejects_more_than_hourly():
    with pytest.raises(ScheduleValidationError):
        ScheduleSpec(kind="cron", value="*/15 * * * *", timezone="UTC")


def test_cron_rejects_subhourly_sunday_schedule():
    with pytest.raises(ScheduleValidationError):
        ScheduleSpec(kind="cron", value="*/15 * * * sun", timezone="UTC")


@pytest.mark.parametrize("expression", ["0 0 * *", "0 0 * * * *", "0 0 * * * * *"])
def test_cron_requires_exactly_five_fields(expression: str):
    with pytest.raises(ScheduleValidationError):
        ScheduleSpec(kind="cron", value=expression, timezone="UTC")


def test_nonexistent_dst_wall_time_moves_to_first_valid_minute():
    spec = ScheduleSpec(kind="daily", value="02:30", timezone="America/New_York")

    assert next_occurrence(spec, dt("2026-03-08T06:00:00Z")) == dt("2026-03-08T07:00:00Z")


def test_ambiguous_dst_wall_time_uses_first_occurrence():
    spec = ScheduleSpec(kind="daily", value="01:30", timezone="America/New_York")

    assert next_occurrence(spec, dt("2026-11-01T04:00:00Z")) == dt("2026-11-01T05:30:00Z")
