from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.handlers import rules, schedules
from src.infoservice.db.repositories.reports import CreateReport


@pytest.mark.parametrize(("threshold", "max_items"), [(0, 1), (10, 30)])
def test_rule_boundaries_are_accepted(threshold, max_items):
    draft = rules.build_rule_update(str(threshold), str(max_items), "ru", "24", "", "")
    assert draft.ai_score_threshold == threshold
    assert draft.max_items == max_items
    assert draft.language == "ru"


@pytest.mark.parametrize("prompt", ["x" * 2001, "x"])
def test_custom_instruction_is_limited_to_2000_characters(prompt):
    if len(prompt) > 2000:
        with pytest.raises(ValueError, match="2000"):
            rules.validate_custom_instruction(prompt)
    else:
        assert rules.validate_custom_instruction(prompt) == prompt


def test_schedule_uses_schedule_spec_for_cron_validation():
    assert schedules.make_schedule_spec("cron", "0 * * * *", "UTC").expression == "0 * * * *"
    with pytest.raises(ValueError):
        schedules.make_schedule_spec("cron", "* * * * *", "UTC")


@pytest.mark.asyncio
async def test_pause_and_resume_recalculate_next_run(monkeypatch):
    report = SimpleNamespace(id=uuid4(), enabled=True, schedule_kind="daily", schedule_value="09:00", timezone="UTC")
    updates = []

    class Repository:
        def __init__(self, session): pass
        async def get_owned(self, *_args): return report
        async def update(self, report_id, user_id, data): updates.append(data); return report

    monkeypatch.setattr(schedules, "ReportRepository", Repository)
    await schedules.set_report_enabled(object(), SimpleNamespace(id="owner"), report.id, False)
    await schedules.set_report_enabled(object(), SimpleNamespace(id="owner"), report.id, True)

    assert updates[0].enabled is False
    assert updates[0].next_run_at is None
    assert updates[1].enabled is True
    assert updates[1].next_run_at is not None
