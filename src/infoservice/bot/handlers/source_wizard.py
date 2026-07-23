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
    field_menu,
    primary_input_menu,
    source_catalog_menu,
    source_menu,
    source_options_menu,
    summary_menu,
)
from src.infoservice.bot.messages_ru import (
    SOURCE_FIELD_ERROR,
    SOURCE_FIELD_PROMPTS,
    SOURCE_OPTIONS,
    SOURCE_PRIMARY_PROMPTS,
    SOURCE_VALUE_ACCEPTED,
)
from src.infoservice.bot.source_forms import (
    SourceDraft,
    SourceFieldError,
    STABLE_SOURCE_TYPES,
    apply_field,
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
    if draft.current_field is not None and draft.screen == "field_review":
        history = list(draft.history)
        if history[-2:] == ["advanced", "field_input"]:
            history = history[:-2]
        raw = draft.to_storage()
        raw.update(screen="advanced", current_field=None, history=history)
        draft = SourceDraft.from_storage(raw)
        await store_draft(state, draft, SourceForm.options)
        await callback.answer()
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'advanced')}\nПараметр сохранён. Можно изменить ещё один.",
            field_menu(draft.source_type),
        )
        return
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
    draft = await load_draft(state)
    draft = _with_screen(draft, "advanced", [*draft.history, draft.screen])
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'advanced')}\nВыберите параметр для изменения.",
        field_menu(draft.source_type),
    )


@router.callback_query(SourceForm.options, F.data.startswith("source:field:"))
async def choose_field(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    field_name = (callback.data or "").rsplit(":", 1)[-1]
    allowed_fields = {
        "rss": {"name", "category"},
        "telegram": {"category", "fetch_limit"},
        "github": {"category"},
        "hackernews": {"fetch_top_stories", "min_score", "category"},
    }[draft.source_type]
    if field_name not in SOURCE_FIELD_PROMPTS or field_name not in allowed_fields:
        await callback.answer("Поле недоступно", show_alert=True)
        return
    raw = draft.to_storage()
    raw.update(
        current_field=field_name,
        screen="field_input",
        history=[*draft.history, "advanced"],
    )
    draft = SourceDraft.from_storage(raw)
    await store_draft(state, draft, SourceForm.field_input)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'field_input')}\n{SOURCE_FIELD_PROMPTS[field_name]}",
    )


@router.message(SourceForm.field_input, F.text)
async def receive_field(message: Message, state: FSMContext) -> None:
    draft = await load_draft(state)
    if draft.current_field is None:
        await message.answer("Выберите поле заново.")
        return
    try:
        draft = apply_field(draft, draft.current_field, message.text)
    except SourceFieldError as exc:
        await message.answer(
            SOURCE_FIELD_ERROR.format(
                field=exc.field,
                reason=exc.reason,
                example=exc.example,
            )
        )
        return
    raw = draft.to_storage()
    raw.update(screen="field_review", history=[*draft.history, "field_input"])
    draft = SourceDraft.from_storage(raw)
    await store_draft(state, draft, SourceForm.value_review)
    await message.answer(
        f"{step_label(draft, 'field_review')}\n"
        f"{SOURCE_VALUE_ACCEPTED.format(value=message.text.strip())}",
        reply_markup=accepted_value_menu(),
    )


@router.callback_query(F.data.startswith("source:edit:"))
async def begin_edit(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    user,
) -> None:
    source_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    try:
        if source_id is None:
            raise NotFound("Источник не найден")
        source = await ReportRepository(session).get_source_owned(source_id, user.id)
    except NotFound:
        await callback.answer("Источник не найден", show_alert=True)
        return
    if source.source_type not in STABLE_SOURCE_TYPES:
        await callback.answer(
            "Редактирование этого типа пока недоступно. Его можно отключить или удалить.",
            show_alert=True,
        )
        return
    draft = SourceDraft.edit(
        str(source.id), source.source_type, source.config, source.enabled
    )
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        format_source_card(source.source_type, source.config, source.enabled),
        field_menu(source.source_type),
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

    if previous == "advanced":
        raw = draft.to_storage()
        raw.update(screen="advanced", current_field=None)
        draft = SourceDraft.from_storage(raw)
        await store_draft(state, draft, SourceForm.options)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'advanced')}\nВыберите параметр для изменения.",
            field_menu(draft.source_type),
        )
        return

    if previous == "summary":
        await store_draft(state, draft, SourceForm.summary)
        card = str((await state.get_data()).get("last_card") or "")
        await replace_or_answer(callback.message, card, summary_menu())
        return

    if previous == "field_input" and draft.current_field is not None:
        await store_draft(state, draft, SourceForm.field_input)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'field_input')}\n"
            f"{SOURCE_FIELD_PROMPTS[draft.current_field]}",
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
