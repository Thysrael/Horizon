"""Owner-scoped Telegram UI for the source catalog."""

from __future__ import annotations

import json
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.infoservice.bot.keyboards import delete_confirmation_menu, source_catalog_menu, source_menu
from src.infoservice.bot.messages_ru import (SOURCE_CONFIG_REQUEST, SOURCE_CREATED, SOURCE_DELETED, SOURCE_DELETE_CONFIRMATION, SOURCE_INVALID,
    SOURCE_NOT_FOUND, SOURCE_OPTIONAL_PREREQUISITE, SOURCE_UNAVAILABLE, SOURCE_UPDATED, SOURCES_MENU)
from src.infoservice.bot.states import SourceForm
from src.infoservice.db.repositories.reports import CreateSource, ReportRepository
from src.infoservice.errors import LimitExceeded, NotFound
from src.infoservice.sources.catalog import SourceCatalog, SourceValidationError

router = Router(name="sources")


def available_source_labels(settings) -> set[str]:
    """Public catalogue labels, used by UI and regression tests."""
    return {capability.label.replace("X (Twitter)", "Twitter / X") for capability in SourceCatalog.available(settings)}


def _uuid(value: str | None) -> UUID | None:
    try:
        return UUID(value or "")
    except ValueError:
        return None


def _display_name(source_type: str, config: dict) -> str:
    return str(config.get("name") or config.get("channel") or config.get("query") or config.get("username") or source_type)


async def _source_or_hidden(callback: CallbackQuery, session, user, source_id: UUID):
    try:
        return await ReportRepository(session).get_source_owned(source_id, user.id)
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return None


@router.callback_query(F.data.startswith("source:list:"))
async def list_sources(callback: CallbackQuery, session, user, settings) -> None:
    report_id = _uuid(callback.data.rsplit(":", 1)[-1])
    if report_id is None:
        await callback.answer("Отчёт не найден", show_alert=True); return
    repository = ReportRepository(session)
    try:
        sources = await repository.list_sources(report_id, user.id)
    except NotFound:
        await callback.answer("Отчёт не найден", show_alert=True); return
    await callback.answer()
    buttons = [[InlineKeyboardButton(text="Добавить источник", callback_data=f"source:catalog:{report_id}")]]
    buttons.extend([[
        InlineKeyboardButton(text=f"{'✅' if item.enabled else '⏸'} {item.display_name}", callback_data=f"source:view:{item.id}")
    ] for item in sources])
    await callback.message.answer(SOURCES_MENU, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("source:catalog:"))
async def open_catalog(callback: CallbackQuery, session, user, settings) -> None:
    report_id = _uuid(callback.data.rsplit(":", 1)[-1])
    if report_id is None:
        await callback.answer("Отчёт не найден", show_alert=True); return
    try:
        await ReportRepository(session).get_owned(report_id, user.id)
    except NotFound:
        await callback.answer("Отчёт не найден", show_alert=True); return
    await callback.answer()
    await callback.message.answer("Выберите тип источника.", reply_markup=source_catalog_menu(str(report_id), SourceCatalog.available(settings)))


@router.callback_query(F.data.startswith("source:create:"))
async def begin_source_form(callback: CallbackQuery, state: FSMContext, session, user, settings) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    _, _, source_type, raw_report_id = parts
    report_id = _uuid(raw_report_id)
    capability = next((item for item in SourceCatalog.available(settings) if item.type == source_type), None)
    if report_id is None or capability is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    try:
        await ReportRepository(session).get_owned(report_id, user.id)
    except NotFound:
        await callback.answer("Отчёт не найден", show_alert=True); return
    await state.update_data(source_draft={"report_id": str(report_id), "source_type": source_type})
    await state.set_state(SourceForm.config)
    await callback.answer()
    if capability.stability == "optional":
        await callback.message.answer(SOURCE_OPTIONAL_PREREQUISITE)
    await callback.message.answer(SOURCE_CONFIG_REQUEST.format(fields=", ".join(capability.input_fields)))


@router.message(SourceForm.config, F.text)
async def receive_source_config(message: Message, state: FSMContext, session, user, settings=None) -> None:
    data = await state.get_data()
    draft = data.get("source_draft", {})
    report_id = _uuid(draft.get("report_id"))
    source_id = _uuid(draft.get("source_id"))
    source_type = draft.get("source_type")
    if not source_type or (report_id is None and source_id is None):
        await state.clear(); await message.answer(SOURCE_NOT_FOUND); return
    try:
        raw = json.loads(message.text)
        if not isinstance(raw, dict):
            raise ValueError
        if settings is None:
            from types import SimpleNamespace
            settings = SimpleNamespace(enable_twitter=False, enable_openbb=False)
        normalized = SourceCatalog.validate(source_type, raw, settings).model_dump(mode="json", exclude_none=True)
        repository = ReportRepository(session)
        if source_id is not None:
            source = await repository.update_source(source_id, user.id, config=normalized, display_name=_display_name(source_type, normalized))
        else:
            source = await repository.add_source(report_id, user.id, CreateSource(source_type=source_type, display_name=_display_name(source_type, normalized), config=normalized))
    except NotFound:
        await state.clear()
        await message.answer(SOURCE_NOT_FOUND if source_id is not None else "Отчёт не найден")
        return
    except (ValueError, TypeError, SourceValidationError, LimitExceeded):
        await message.answer(SOURCE_INVALID)
        return
    await state.clear()
    await message.answer(SOURCE_UPDATED if source_id is not None else SOURCE_CREATED, reply_markup=source_menu(str(source.id), source.enabled))


@router.callback_query(F.data.startswith("source:view:"))
async def view_source(callback: CallbackQuery, session, user) -> None:
    source_id = _uuid(callback.data.rsplit(":", 1)[-1])
    if source_id is None: await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    source = await _source_or_hidden(callback, session, user, source_id)
    if source is None: return
    await callback.answer()
    await callback.message.answer(f"{source.display_name}\nТип: {source.source_type}", reply_markup=source_menu(str(source.id), source.enabled))


@router.callback_query(F.data.startswith("source:enable:") | F.data.startswith("source:disable:"))
async def toggle_source(callback: CallbackQuery, session, user, settings) -> None:
    action, raw_id = (callback.data or "").rsplit(":", 2)[1:]
    source_id = _uuid(raw_id)
    if source_id is None: await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    try:
        repository = ReportRepository(session)
        source = await repository.get_source_owned(source_id, user.id)
        if action == "enable" and source.source_type not in {item.type for item in SourceCatalog.available(settings)}:
            await callback.answer(SOURCE_UNAVAILABLE, show_alert=True); return
        await repository.update_source(source_id, user.id, enabled=action == "enable")
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    await callback.answer(); await callback.message.answer(SOURCE_UPDATED)


@router.callback_query(F.data.startswith("source:edit:"))
async def edit_source(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    source_id = _uuid(callback.data.rsplit(":", 1)[-1])
    if source_id is None: await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    source = await _source_or_hidden(callback, session, user, source_id)
    if source is None: return
    await state.update_data(source_draft={"source_id": str(source.id), "source_type": source.source_type, "edit": True})
    await state.set_state(SourceForm.config); await callback.answer()
    await callback.message.answer(SOURCE_CONFIG_REQUEST.format(fields="JSON"))


@router.callback_query(F.data.startswith("source:delete:"))
async def request_delete_source(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    source_id = _uuid(callback.data.rsplit(":", 1)[-1])
    if source_id is None or await _source_or_hidden(callback, session, user, source_id) is None: return
    await state.update_data(source_delete_id=str(source_id)); await state.set_state(SourceForm.delete_confirmation)
    await callback.answer(); await callback.message.answer(SOURCE_DELETE_CONFIRMATION, reply_markup=delete_confirmation_menu())


@router.callback_query(SourceForm.delete_confirmation, F.data == "source:delete-back")
async def return_to_source_from_delete(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    source_id = _uuid((await state.get_data()).get("source_delete_id"))
    if source_id is None:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True)
        return
    source = await _source_or_hidden(callback, session, user, source_id)
    if source is None:
        return
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        f"{source.display_name}\nТип: {source.source_type}",
        reply_markup=source_menu(str(source.id), source.enabled),
    )


@router.callback_query(SourceForm.delete_confirmation, F.data == "source:delete-confirm")
async def delete_source(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    source_id = _uuid((await state.get_data()).get("source_delete_id"))
    if source_id is None: await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    try:
        await ReportRepository(session).delete_source(source_id, user.id)
    except NotFound:
        await callback.answer(SOURCE_NOT_FOUND, show_alert=True); return
    await state.clear(); await callback.answer(); await callback.message.answer(SOURCE_DELETED)
