"""Validation and owner-scoped rule editing helpers."""

from __future__ import annotations

from dataclasses import replace

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.infoservice.bot.handlers.reports import callback_report_id
from src.infoservice.bot.messages_ru import REPORT_NOT_FOUND, RULES_INVALID
from src.infoservice.bot.states import EditRules
from src.infoservice.db.repositories.reports import ReportRepository, UpdateReport
from src.infoservice.errors import NotFound

router = Router(name="rules")


def _csv(value: str) -> list[str]: return [item.strip() for item in value.split(",") if item.strip()]
def validate_custom_instruction(value: str) -> str | None:
    value = value.strip()
    if len(value) > 2000: raise ValueError("Инструкция не длиннее 2000 символов")
    return value or None

def build_rule_update(threshold: str, max_items: str, language: str, lookback: str, categories: str, exclusions: str) -> UpdateReport:
    score, count, hours = float(threshold), int(max_items), int(lookback)
    if not 0 <= score <= 10 or not 1 <= count <= 30 or language not in {"ru", "en"} or hours < 1: raise ValueError("invalid rules")
    return UpdateReport(ai_score_threshold=score, max_items=count, language=language, lookback_hours=hours, categories=_csv(categories), exclusions=_csv(exclusions))


async def _advance(message: Message, state: FSMContext, key: str, value: str, next_state, prompt: str) -> None:
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(prompt)

@router.callback_query(F.data.startswith("report:rules:"))
async def edit_rules(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    report_id = callback_report_id(callback.data)
    try:
        report = await ReportRepository(session).get_owned(report_id, user.id) if report_id else None
    except NotFound:
        report = None
    if report is None:
        await callback.answer(REPORT_NOT_FOUND, show_alert=True); return
    await callback.answer()
    await state.set_state(EditRules.threshold)
    await state.update_data(report_id=str(report.id))
    await callback.message.answer("Введите порог от 0 до 10.")


@router.message(EditRules.threshold, F.text)
async def receive_threshold(message: Message, state: FSMContext) -> None:
    try:
        if not 0 <= float(message.text) <= 10:
            raise ValueError
    except ValueError:
        await message.answer(RULES_INVALID); return
    await _advance(message, state, "threshold", message.text, EditRules.categories, "Категории через запятую (или - для всех).")


@router.message(EditRules.categories, F.text)
async def receive_categories(message: Message, state: FSMContext) -> None:
    await _advance(message, state, "categories", "" if message.text.strip() == "-" else message.text, EditRules.exclusions, "Исключения через запятую (или -).")


@router.message(EditRules.exclusions, F.text)
async def receive_exclusions(message: Message, state: FSMContext) -> None:
    await _advance(message, state, "exclusions", "" if message.text.strip() == "-" else message.text, EditRules.max_items, "Сколько материалов: от 1 до 30.")


@router.message(EditRules.max_items, F.text)
async def receive_max_items(message: Message, state: FSMContext) -> None:
    try:
        if not 1 <= int(message.text) <= 30:
            raise ValueError
    except ValueError:
        await message.answer(RULES_INVALID); return
    await _advance(message, state, "max_items", message.text, EditRules.language, "Язык отчёта: ru или en.")


@router.message(EditRules.language, F.text)
async def receive_language(message: Message, state: FSMContext) -> None:
    language = message.text.strip().lower()
    if language not in {"ru", "en"}:
        await message.answer(RULES_INVALID); return
    await _advance(message, state, "language", language, EditRules.lookback, "Глубина поиска в часах (не менее 1).")


@router.message(EditRules.lookback, F.text)
async def receive_lookback(message: Message, state: FSMContext) -> None:
    try:
        if int(message.text) < 1:
            raise ValueError
    except ValueError:
        await message.answer(RULES_INVALID); return
    await _advance(message, state, "lookback", message.text, EditRules.custom_instruction, "Дополнительная инструкция (до 2000 символов, или -).")

@router.message(EditRules.custom_instruction, F.text)
async def save_custom_instruction(message: Message, state: FSMContext, session, user) -> None:
    data = await state.get_data()
    try:
        instruction = validate_custom_instruction("" if message.text.strip() == "-" else message.text)
        update = build_rule_update(data["threshold"], data["max_items"], data["language"], data["lookback"], data["categories"], data["exclusions"])
        update = replace(update, custom_instruction=instruction)
        await ReportRepository(session).update(callback_report_id(f"x:{data['report_id']}"), user.id, update)
    except (ValueError, KeyError, NotFound):
        await message.answer(RULES_INVALID); return
    await state.clear()
    await message.answer("Правила сохранены.")
