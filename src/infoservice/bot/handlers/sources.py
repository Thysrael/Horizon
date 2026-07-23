"""Owner-scoped Telegram UI for report source CRUD."""

from __future__ import annotations

from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.infoservice.bot.keyboards import (
    delete_confirmation_menu,
    source_catalog_menu,
    source_menu,
)
from src.infoservice.bot.messages_ru import (
    SOURCE_DELETED,
    SOURCE_DELETE_CONFIRMATION,
    SOURCE_NOT_FOUND,
    SOURCE_UNAVAILABLE,
    SOURCE_UPDATED,
    SOURCES_MENU,
)
from src.infoservice.bot.source_forms import (
    STABLE_SOURCE_TYPES,
    format_source_card,
)
from src.infoservice.bot.states import SourceForm
from src.infoservice.bot.ui import replace_or_answer
from src.infoservice.db.repositories.reports import ReportRepository
from src.infoservice.errors import NotFound
from src.infoservice.sources.catalog import SourceCatalog

router = Router(name="sources")


def _uuid(value: str | None) -> UUID | None:
    try:
        return UUID(value or "")
    except (TypeError, ValueError):
        return None


def _is_stable(source_type: str) -> bool:
    return source_type in STABLE_SOURCE_TYPES


def _source_card(source) -> str:
    if _is_stable(source.source_type):
        return format_source_card(
            source.source_type,
            source.config,
            source.enabled,
        )
    return f"{source.display_name}\nТип: {source.source_type}"


def _source_markup(source) -> InlineKeyboardMarkup:
    return source_menu(
        str(source.id),
        source.enabled,
        editable=_is_stable(source.source_type),
    )


async def _source_or_hidden(
    callback: CallbackQuery,
    session,
    user,
    source_id: UUID,
):
    try:
        return await ReportRepository(session).get_source_owned(
            source_id,
            user.id,
        )
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return None


@router.message(Command("sources"))
async def sources_command(message: Message, state: FSMContext, session, user) -> None:
    await state.clear()
    reports = await ReportRepository(session).list_owned(user.id)
    if not reports:
        await message.answer(
            "Сначала создайте отчёт.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="➕ Новый отчёт", callback_data="report:create")
            ]]),
        )
        return
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=report.name, callback_data=f"source:list:{report.id}")]
        for report in reports
    ])
    await message.answer("Выберите отчёт.", reply_markup=markup)


@router.callback_query(F.data.startswith("source:list:"))
async def list_sources(callback: CallbackQuery, session, user, settings) -> None:
    report_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    if report_id is None:
        await callback.answer("Отчёт не найден", show_alert=True)
        return
    try:
        sources = await ReportRepository(session).list_sources(
            report_id,
            user.id,
        )
    except NotFound:
        await callback.answer("Отчёт не найден", show_alert=True)
        return
    buttons = [
        [
            InlineKeyboardButton(
                text="Добавить источник",
                callback_data=f"source:catalog:{report_id}",
            )
        ]
    ]
    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text=(
                        f"{'✅' if item.enabled else '⏸'} "
                        f"{item.display_name}"
                    ),
                    callback_data=f"source:view:{item.id}",
                )
            ]
            for item in sources
        ]
    )
    await callback.answer()
    await replace_or_answer(
        callback.message,
        SOURCES_MENU,
        InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("source:catalog:"))
async def open_catalog(callback: CallbackQuery, session, user, settings) -> None:
    report_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    if report_id is None:
        await callback.answer("Отчёт не найден", show_alert=True)
        return
    repository = ReportRepository(session)
    try:
        await repository.get_owned(report_id, user.id)
        current_sources = await repository.list_sources(report_id, user.id)
    except NotFound:
        await callback.answer("Отчёт не найден", show_alert=True)
        return
    limit = getattr(repository, "max_sources_per_report", 30)
    if len(current_sources) >= limit:
        await callback.answer(
            f"В отчёте может быть не более {limit} источников",
            show_alert=True,
        )
        return
    await callback.answer()
    await replace_or_answer(
        callback.message,
        "Выберите тип источника.",
        source_catalog_menu(str(report_id)),
    )


@router.callback_query(F.data.startswith("source:view:"))
async def view_source(callback: CallbackQuery, session, user) -> None:
    source_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    source = await _source_or_hidden(
        callback,
        session,
        user,
        source_id,
    )
    if source is None:
        return
    await callback.answer()
    await replace_or_answer(
        callback.message,
        _source_card(source),
        _source_markup(source),
    )


@router.callback_query(
    F.data.startswith("source:enable:")
    | F.data.startswith("source:disable:")
)
async def toggle_source(callback: CallbackQuery, session, user, settings) -> None:
    action, raw_id = (callback.data or "").rsplit(":", 2)[1:]
    source_id = _uuid(raw_id)
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    try:
        repository = ReportRepository(session)
        source = await repository.get_source_owned(source_id, user.id)
        available_types = {
            capability.type for capability in SourceCatalog.available(settings)
        }
        if action == "enable" and source.source_type not in available_types:
            await callback.answer(SOURCE_UNAVAILABLE, show_alert=True)
            return
        source = await repository.update_source(
            source_id,
            user.id,
            enabled=action == "enable",
        )
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{SOURCE_UPDATED}\n\n{_source_card(source)}",
        _source_markup(source),
    )


@router.callback_query(F.data.startswith("source:delete:"))
async def request_delete_source(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
) -> None:
    source_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    source = await _source_or_hidden(
        callback,
        session,
        user,
        source_id,
    )
    if source is None:
        return
    await state.update_data(source_delete_id=str(source_id))
    await state.set_state(SourceForm.delete_confirmation)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        SOURCE_DELETE_CONFIRMATION,
        delete_confirmation_menu(),
    )


@router.callback_query(
    SourceForm.delete_confirmation,
    F.data == "source:delete-back",
)
async def return_to_source_from_delete(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
) -> None:
    source_id = _uuid(
        (await state.get_data()).get("source_delete_id")
    )
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    source = await _source_or_hidden(
        callback,
        session,
        user,
        source_id,
    )
    if source is None:
        return
    await state.clear()
    await callback.answer()
    await replace_or_answer(
        callback.message,
        _source_card(source),
        _source_markup(source),
    )


@router.callback_query(
    SourceForm.delete_confirmation,
    F.data == "source:delete-confirm",
)
async def delete_source(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
) -> None:
    source_id = _uuid(
        (await state.get_data()).get("source_delete_id")
    )
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    try:
        await ReportRepository(session).delete_source(source_id, user.id)
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    await state.clear()
    await callback.answer()
    await replace_or_answer(callback.message, SOURCE_DELETED)
