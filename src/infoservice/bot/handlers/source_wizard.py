"""Conversational creation flow for stable report sources."""

from __future__ import annotations

from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.infoservice.bot.keyboards import (
    accepted_value_menu,
    primary_input_menu,
    source_catalog_menu,
    source_menu,
    source_options_menu,
    summary_menu,
)
from src.infoservice.bot.messages_ru import (
    SOURCE_FIELD_ERROR,
    SOURCE_OPTIONS,
    SOURCE_PRIMARY_PROMPTS,
    SOURCE_VALUE_ACCEPTED,
)
from src.infoservice.bot.source_forms import (
    SourceDraft,
    SourceFieldError,
    format_source_card,
    parse_primary,
    resolve_rss_name,
    validated_config,
)
from src.infoservice.bot.states import SourceForm
from src.infoservice.bot.ui import replace_or_answer
from src.infoservice.db.repositories.reports import CreateSource, ReportRepository
from src.infoservice.errors import LimitExceeded, NotFound

router = Router(name="source_wizard")


def _uuid(value: str | None) -> UUID | None:
    try:
        return UUID(value or "")
    except (TypeError, ValueError):
        return None


def _github_kind_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Релизы репозитория",
                    callback_data="source:github-kind:repo_releases",
                )
            ],
            [
                InlineKeyboardButton(
                    text="События пользователя",
                    callback_data="source:github-kind:user_events",
                )
            ],
            [
                InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel"),
            ],
        ]
    )


async def load_draft(state: FSMContext) -> SourceDraft:
    """Restore a source draft from FSM JSON storage."""
    raw = (await state.get_data()).get("source_draft")
    if not isinstance(raw, dict):
        raise ValueError("source draft is missing")
    return SourceDraft.from_storage(raw)


async def store_draft(
    state: FSMContext,
    draft: SourceDraft,
    next_state: State,
) -> None:
    """Persist a JSON-safe source draft and advance the FSM."""
    await state.update_data(source_draft=draft.to_storage())
    await state.set_state(next_state)


def step_label(draft: SourceDraft, screen: str) -> str:
    """Return the user-facing progress label for a wizard screen."""
    if draft.source_type == "hackernews":
        current = {"options": 1, "advanced": 1, "summary": 2}[screen]
        return f"Шаг {current} из 2"
    current = {
        "primary": 1,
        "value_review": 1,
        "options": 2,
        "advanced": 2,
        "field_input": 2,
        "field_review": 2,
        "summary": 3,
    }[screen]
    return f"Шаг {current} из 3"


def _with_screen(
    draft: SourceDraft,
    screen: str,
    history: list[str],
) -> SourceDraft:
    raw = draft.to_storage()
    raw.update(screen=screen, history=history)
    return SourceDraft.from_storage(raw)


def _accepted_value(draft: SourceDraft) -> str:
    if draft.values.get("owner") and draft.values.get("repo"):
        return f"{draft.values['owner']}/{draft.values['repo']}"
    return str(
        draft.values.get("url")
        or draft.values.get("channel")
        or draft.values.get("username")
        or ""
    )


@router.callback_query(F.data.startswith("source:create:"))
async def begin_create(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer("Источник не найден", show_alert=True)
        return
    source_type, report_text = parts[2], parts[3]
    report_id = _uuid(report_text)
    try:
        if report_id is None:
            raise NotFound("Отчёт не найден")
        await ReportRepository(session).get_owned(report_id, user.id)
        draft = SourceDraft.new(str(report_id), source_type)
    except (NotFound, ValueError):
        await callback.answer(
            "Отчёт или источник не найден",
            show_alert=True,
        )
        return

    await callback.answer()
    if source_type == "hackernews":
        draft = _with_screen(draft, "options", ["catalog"])
        await store_draft(state, draft, SourceForm.options)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
            source_options_menu(),
        )
        return

    if source_type == "github":
        draft = _with_screen(draft, "github_kind", ["catalog"])
        await store_draft(state, draft, SourceForm.primary_input)
        await replace_or_answer(
            callback.message,
            "Что отслеживать в GitHub?",
            _github_kind_menu(),
        )
        return

    draft = _with_screen(draft, "primary", ["catalog"])
    await store_draft(state, draft, SourceForm.primary_input)
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'primary')}\n"
        f"{SOURCE_PRIMARY_PROMPTS[source_type]}",
        primary_input_menu(),
    )


@router.callback_query(
    SourceForm.primary_input,
    F.data.startswith("source:github-kind:"),
)
async def choose_github_kind(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    draft = await load_draft(state)
    kind = (callback.data or "").rsplit(":", 1)[-1]
    if (
        draft.source_type != "github"
        or draft.screen != "github_kind"
        or kind not in {"repo_releases", "user_events"}
    ):
        await callback.answer("Некорректный режим GitHub", show_alert=True)
        return
    draft = draft.with_values(type=kind)
    draft = _with_screen(
        draft,
        "primary",
        [*draft.history, "github_kind"],
    )
    await store_draft(state, draft, SourceForm.primary_input)
    await callback.answer()
    example = "pallets/flask" if kind == "repo_releases" else "octocat"
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'primary')}\n"
        f"Отправьте цель GitHub.\nПример: {example}",
        primary_input_menu(),
    )


@router.message(SourceForm.primary_input, F.text)
async def receive_primary(message: Message, state: FSMContext) -> None:
    draft = await load_draft(state)
    if draft.screen != "primary":
        await message.answer("Сначала выберите режим источника.")
        return
    try:
        values = parse_primary(
            draft.source_type,
            message.text,
            (
                str(draft.values.get("type"))
                if draft.source_type == "github"
                else None
            ),
        )
        if draft.source_type == "rss":
            values["name"] = await resolve_rss_name(str(values["url"]))
        draft = draft.with_values(**values)
    except SourceFieldError as exc:
        await message.answer(
            SOURCE_FIELD_ERROR.format(
                field=exc.field,
                reason=exc.reason,
                example=exc.example,
            )
        )
        return

    draft = _with_screen(
        draft,
        "value_review",
        [*draft.history, "primary"],
    )
    await store_draft(state, draft, SourceForm.value_review)
    await message.answer(
        f"{step_label(draft, 'value_review')}\n"
        f"{SOURCE_VALUE_ACCEPTED.format(value=_accepted_value(draft))}",
        reply_markup=accepted_value_menu(),
    )


@router.callback_query(SourceForm.value_review, F.data == "source:next")
async def accept_primary(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    draft = await load_draft(state)
    draft = _with_screen(
        draft,
        "options",
        [*draft.history, "value_review"],
    )
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
        source_options_menu(),
    )


@router.callback_query(SourceForm.options, F.data == "source:advanced")
@router.callback_query(SourceForm.summary, F.data == "source:advanced")
async def show_advanced(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Keep advanced navigation safe until Task 5 owns field input."""
    draft = await load_draft(state)
    await callback.answer(
        "Дополнительные настройки будут доступны на следующем шаге разработки."
    )
    if draft.screen == "summary":
        card = str((await state.get_data()).get("last_card") or "")
        await replace_or_answer(callback.message, card, summary_menu())
        return
    await store_draft(state, draft, SourceForm.options)
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
        source_options_menu(),
    )


@router.callback_query(SourceForm.options, F.data == "source:summary")
@router.callback_query(SourceForm.field_input, F.data == "source:summary")
async def show_summary(
    callback: CallbackQuery,
    state: FSMContext,
    settings,
) -> None:
    draft = await load_draft(state)
    try:
        config = validated_config(draft, settings)
    except SourceFieldError as exc:
        await callback.answer(
            SOURCE_FIELD_ERROR.format(
                field=exc.field,
                reason=exc.reason,
                example=exc.example,
            ),
            show_alert=True,
        )
        return
    draft = _with_screen(
        draft,
        "summary",
        [*draft.history, draft.screen],
    )
    card = (
        f"{step_label(draft, 'summary')}\n\n"
        f"{format_source_card(draft.source_type, config, draft.enabled)}"
    )
    await state.update_data(
        source_draft=draft.to_storage(),
        last_card=card,
    )
    await state.set_state(SourceForm.summary)
    await callback.answer()
    await replace_or_answer(callback.message, card, summary_menu())


async def _render_previous(
    callback: CallbackQuery,
    state: FSMContext,
    draft: SourceDraft,
    previous: str,
) -> None:
    if previous == "catalog":
        report_id = draft.report_id
        await state.clear()
        if report_id is None:
            await replace_or_answer(
                callback.message,
                "Выберите отчёт заново.",
            )
        else:
            await replace_or_answer(
                callback.message,
                "Выберите тип источника.",
                source_catalog_menu(report_id),
            )
        return

    if previous == "source_card":
        await state.clear()
        if draft.source_id is None:
            await replace_or_answer(callback.message, "Источник не найден.")
        else:
            await replace_or_answer(
                callback.message,
                format_source_card(
                    draft.source_type,
                    draft.values,
                    draft.enabled,
                ),
                source_menu(
                    draft.source_id,
                    draft.enabled,
                    editable=True,
                ),
            )
        return

    if previous == "github_kind":
        await store_draft(state, draft, SourceForm.primary_input)
        await replace_or_answer(
            callback.message,
            "Что отслеживать в GitHub?",
            _github_kind_menu(),
        )
        return

    if previous == "value_review":
        await store_draft(state, draft, SourceForm.value_review)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'value_review')}\n"
            f"{SOURCE_VALUE_ACCEPTED.format(value=_accepted_value(draft))}",
            accepted_value_menu(),
        )
        return

    if previous == "options":
        await store_draft(state, draft, SourceForm.options)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
            source_options_menu(),
        )
        return

    await store_draft(state, draft, SourceForm.primary_input)
    prompt = SOURCE_PRIMARY_PROMPTS.get(
        draft.source_type,
        "Выберите тип источника заново.",
    )
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'primary')}\n{prompt}",
        primary_input_menu(),
    )


@router.callback_query(SourceForm.primary_input, F.data == "source:back")
@router.callback_query(SourceForm.value_review, F.data == "source:back")
@router.callback_query(SourceForm.options, F.data == "source:back")
@router.callback_query(SourceForm.field_input, F.data == "source:back")
@router.callback_query(SourceForm.summary, F.data == "source:back")
async def go_back(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    draft = await load_draft(state)
    history = list(draft.history)
    previous = history.pop() if history else "catalog"
    draft = _with_screen(draft, previous, history)
    await callback.answer()
    await _render_previous(callback, state, draft, previous)


@router.callback_query(SourceForm.summary, F.data == "source:save")
async def save_source(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
    settings,
) -> None:
    draft = await load_draft(state)
    try:
        config = validated_config(draft, settings)
        display_name = str(
            config.get("name")
            or config.get("channel")
            or config.get("username")
            or (
                f"{config.get('owner')}/{config.get('repo')}"
                if config.get("owner") and config.get("repo")
                else "Hacker News"
            )
        )
        repository = ReportRepository(session)
        if draft.mode == "edit":
            source_id = _uuid(draft.source_id)
            if source_id is None:
                raise NotFound("Источник не найден")
            source = await repository.update_source(
                source_id,
                user.id,
                config=config,
                display_name=display_name,
            )
            text = "Источник обновлён."
        else:
            report_id = _uuid(draft.report_id)
            if report_id is None:
                raise NotFound("Отчёт не найден")
            source = await repository.add_source(
                report_id,
                user.id,
                CreateSource(
                    source_type=draft.source_type,
                    display_name=display_name,
                    config=config,
                ),
            )
            text = "Источник добавлен."
    except LimitExceeded as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except (NotFound, SourceFieldError):
        await callback.answer(
            "Источник или отчёт не найден",
            show_alert=True,
        )
        return

    await state.clear()
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{text}\n\n"
        f"{format_source_card(draft.source_type, config, source.enabled)}",
        source_menu(str(source.id), source.enabled, editable=True),
    )
