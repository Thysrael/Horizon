"""Schedule validation and pause/resume controls."""

from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.infoservice.bot.handlers.reports import callback_report_id
from src.infoservice.bot.messages_ru import REPORT_NOT_FOUND, REPORT_PAUSED, REPORT_RESUMED, SCHEDULE_INVALID
from src.infoservice.bot.states import EditSchedule
from src.infoservice.db.repositories.reports import ReportRepository, UpdateReport
from src.infoservice.errors import NotFound
from src.infoservice.scheduling.calculator import ScheduleSpec, next_occurrence

router = Router(name="schedules")

def make_schedule_spec(kind: str, value: str, timezone_name: str) -> ScheduleSpec:
    return ScheduleSpec(kind, value, timezone_name)


def _schedule_hint(kind: str) -> str:
    return {
        "daily": "Введите время в формате HH:MM.",
        "weekdays": "Введите время в формате HH:MM.",
        "weekly": "Введите день и время, например mon 09:00.",
        "cron": "Введите cron из пяти полей, не чаще раза в час.",
    }[kind]

async def set_report_enabled(session, user, report_id, enabled: bool):
    repository = ReportRepository(session)
    report = await repository.get_owned(report_id, user.id)
    next_run_at = None
    if enabled:
        spec = make_schedule_spec(report.schedule_kind, report.schedule_value, report.timezone or user.timezone)
        next_run_at = next_occurrence(spec, datetime.now(timezone.utc))
    return await repository.update(report_id, user.id, UpdateReport(enabled=enabled, next_run_at=next_run_at))

async def _toggle(callback: CallbackQuery, session, user, enabled: bool, text: str):
    report_id = callback_report_id(callback.data)
    try:
        if report_id is None: raise NotFound(REPORT_NOT_FOUND)
        await set_report_enabled(session, user, report_id, enabled)
    except (NotFound, ValueError):
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer()
    await callback.message.answer(text)

@router.callback_query(F.data.startswith("report:pause:"))
async def pause_report(callback: CallbackQuery, session, user) -> None: await _toggle(callback, session, user, False, REPORT_PAUSED)

@router.callback_query(F.data.startswith("report:resume:"))
async def resume_report(callback: CallbackQuery, session, user) -> None: await _toggle(callback, session, user, True, REPORT_RESUMED)

@router.callback_query(F.data.startswith("report:schedule:"))
async def edit_schedule(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    report_id = callback_report_id(callback.data)
    try: report = await ReportRepository(session).get_owned(report_id, user.id) if report_id else None
    except NotFound: report = None
    if report is None: await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer(); await state.set_state(EditSchedule.kind); await state.update_data(report_id=str(report.id))
    await callback.message.answer("Введите тип расписания: daily, weekdays, weekly или cron.")


@router.message(EditSchedule.kind, F.text)
async def receive_schedule_kind(message: Message, state: FSMContext) -> None:
    kind = message.text.strip().lower()
    if kind not in {"daily", "weekdays", "weekly", "cron"}:
        await message.answer(SCHEDULE_INVALID); return
    await state.update_data(schedule_kind=kind)
    await state.set_state(EditSchedule.value)
    await message.answer(_schedule_hint(kind))


@router.message(EditSchedule.value, F.text)
async def receive_schedule_value(message: Message, state: FSMContext, session, user) -> None:
    data = await state.get_data()
    try:
        report_id = callback_report_id(f"report:{data['report_id']}")
        if report_id is None:
            raise ValueError
        timezone_name = getattr(user, "timezone", "UTC")
        spec = make_schedule_spec(data["schedule_kind"], message.text.strip(), timezone_name)
        next_run_at = next_occurrence(spec, datetime.now(timezone.utc))
        await ReportRepository(session).update(
            report_id, user.id,
            UpdateReport(schedule_kind=spec.kind, schedule_value=spec.value, timezone=timezone_name, next_run_at=next_run_at),
        )
    except (KeyError, ValueError, NotFound):
        await message.answer(SCHEDULE_INVALID); return
    await state.clear()
    await message.answer("Расписание сохранено.")
