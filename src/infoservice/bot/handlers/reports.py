"""Owner-scoped report creation, CRUD and history callbacks."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.bot.keyboards import report_confirmation_menu, report_menu
from src.infoservice.bot.messages_ru import (ACTION_CANCELLED, HISTORY_EMPTY, MANUAL_RUN_COOLDOWN, MANUAL_RUN_UNAVAILABLE, REPORT_CONFIRMATION, REPORT_CREATED,
    REPORT_DELETE_CONFIRMATION, REPORT_DELETED, REPORT_NAME_REQUEST, REPORT_NOT_FOUND, REPORTS_MENU)
from src.infoservice.bot.states import CreateReport
from src.infoservice.db.models import LLMCredential, Report, ReportRun, RunStatus
from src.infoservice.db.repositories.reports import CreateReport as CreateReportData, ReportRepository
from src.infoservice.db.repositories.manual_runs import ManualRunRepository, ManualRunResult
from src.infoservice.errors import NotFound
from src.infoservice.scheduling.calculator import ScheduleSpec, next_occurrence

router = Router(name="reports")


class ReportDraft(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    language: str = "en"
    lookback_hours: int = 24
    ai_score_threshold: float = 7.0
    max_items: int = 10
    categories: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    custom_instruction: str | None = None
    schedule_kind: str = "daily"
    schedule_value: str = "09:00"

    def create_data(self, timezone_name: str | None) -> CreateReportData:
        return CreateReportData(**self.model_dump(), timezone=timezone_name)


def callback_report_id(data: str | None) -> UUID | None:
    try:
        return UUID((data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError, AttributeError):
        return None


async def _owned(callback: CallbackQuery, session: AsyncSession, user, report_id: UUID):
    try:
        return await ReportRepository(session).get_owned(report_id, user.id)
    except NotFound:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True)
        return None


@router.callback_query(F.data == "reports")
async def list_reports(callback: CallbackQuery, session: AsyncSession, user) -> None:
    await callback.answer()
    reports = await ReportRepository(session).list_owned(user.id)
    text = REPORTS_MENU if reports else f"{REPORTS_MENU}\nСоздайте первый отчёт."
    buttons = [[InlineKeyboardButton(text="Создать отчёт", callback_data="report:create")]]
    buttons.extend([[InlineKeyboardButton(text=report.name, callback_data=f"report:view:{report.id}")]] for report in reports)
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "report:create")
async def begin_create_report(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(CreateReport.name)
    await callback.message.answer(REPORT_NAME_REQUEST)


@router.message(CreateReport.name, F.text)
async def receive_report_name(message: Message, state: FSMContext) -> None:
    try:
        draft = ReportDraft(name=message.text.strip())
    except ValueError:
        await message.answer(REPORT_NAME_REQUEST)
        return
    await state.update_data(report_draft=draft.model_dump())
    await state.set_state(CreateReport.confirmation)
    await message.answer(REPORT_CONFIRMATION.format(name=draft.name), reply_markup=report_confirmation_menu())


@router.callback_query(CreateReport.confirmation, F.data == "report:confirm")
async def confirm_create_report(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user) -> None:
    await callback.answer()
    data = await state.get_data()
    raw_draft = data.get("report_draft")
    if raw_draft is None:
        await callback.message.answer(ACTION_CANCELLED)
        return
    draft = ReportDraft.model_validate(raw_draft)
    timezone_name = getattr(user, "timezone", None) or "UTC"
    create_data = draft.create_data(timezone_name)
    spec = ScheduleSpec(create_data.schedule_kind, create_data.schedule_value, timezone_name)
    create_data = replace(create_data, next_run_at=next_occurrence(spec, datetime.now(timezone.utc)))
    report = await ReportRepository(session).create(user.id, create_data)
    await state.clear()
    await callback.message.answer(REPORT_CREATED, reply_markup=report_menu(str(report.id), report.enabled))


@router.callback_query(CreateReport.confirmation, F.data == "report:cancel")
async def cancel_create_report(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(ACTION_CANCELLED)


@router.callback_query(F.data.startswith("report:view:"))
async def view_report(callback: CallbackQuery, session: AsyncSession, user) -> None:
    report_id = callback_report_id(callback.data)
    if report_id is None:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True)
        return
    report = await _owned(callback, session, user, report_id)
    if report is None:
        return
    await callback.answer()
    await callback.message.answer(f"{report.name}\nПорог: {report.ai_score_threshold}", reply_markup=report_menu(str(report.id), report.enabled))


@router.callback_query(F.data.startswith("report:delete:"))
async def request_delete_report(callback: CallbackQuery, session: AsyncSession, user) -> None:
    report_id = callback_report_id(callback.data)
    if report_id is None or await _owned(callback, session, user, report_id) is None: return
    await callback.answer()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    await callback.message.answer(REPORT_DELETE_CONFIRMATION, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Да, удалить", callback_data=f"report:delete-confirm:{report_id}")]]))


@router.callback_query(F.data.startswith("report:delete-confirm:"))
async def delete_report(callback: CallbackQuery, session: AsyncSession, user) -> None:
    report_id = callback_report_id(callback.data)
    if report_id is None or await _owned(callback, session, user, report_id) is None: return
    await ReportRepository(session).delete(report_id, user.id)
    await callback.answer()
    await callback.message.answer(REPORT_DELETED)


async def completed_history(session: AsyncSession, user_id, report_id: UUID):
    await ReportRepository(session).get_owned(report_id, user_id)
    rows = await session.execute(select(ReportRun).where(ReportRun.report_id == report_id).order_by(ReportRun.created_at.desc()).limit(20))
    return rows.scalars().all()


@router.callback_query(F.data.startswith("report:history:"))
async def report_history(callback: CallbackQuery, session: AsyncSession, user) -> None:
    report_id = callback_report_id(callback.data)
    try:
        history = await completed_history(session, user.id, report_id) if report_id else []
    except NotFound:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer()
    if not history:
        await callback.message.answer(HISTORY_EMPTY); return
    buttons = [[InlineKeyboardButton(text=f"Повторить {run.created_at:%d.%m %H:%M}", callback_data=f"report:resend:{run.id}")]
               for run in history if run.status == RunStatus.SUCCEEDED and run.result_markdown and run.created_at >= datetime.now(timezone.utc) - timedelta(days=30)]
    await callback.message.answer("\n".join(f"{run.status}: {run.created_at:%d.%m %H:%M}" for run in history), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None)


@router.callback_query(F.data.startswith("report:run:"))
async def manual_run(callback: CallbackQuery, session: AsyncSession, user) -> None:
    report_id = callback_report_id(callback.data)
    try:
        if report_id is None:
            raise NotFound(REPORT_NOT_FOUND)
        credential = await session.scalar(select(LLMCredential.id).where(LLMCredential.user_id == user.id, LLMCredential.provider == "deepseek"))
        if credential is None:
            await callback.answer(MANUAL_RUN_UNAVAILABLE, show_alert=True); return
        now = datetime.now(timezone.utc)
        outcome = await ManualRunRepository(session).enqueue(user.id, report_id, now)
        if outcome is ManualRunResult.COOLDOWN:
            await callback.answer(MANUAL_RUN_COOLDOWN, show_alert=True); return
    except NotFound:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer()
    await callback.message.answer("Запуск поставлен в очередь.")


@router.callback_query(F.data.startswith("report:resend:"))
async def resend_run(callback: CallbackQuery, session: AsyncSession, user) -> None:
    run_id = callback_report_id(callback.data)
    if run_id is None:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    run = await session.scalar(select(ReportRun).join(Report).where(ReportRun.id == run_id, Report.user_id == user.id))
    if run is None or run.status != RunStatus.SUCCEEDED or not run.result_markdown or run.created_at < datetime.now(timezone.utc) - timedelta(days=30):
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer()
    await callback.message.answer(run.result_markdown)
