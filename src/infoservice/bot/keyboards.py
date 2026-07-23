from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.infoservice.bot.source_forms import STABLE_SOURCE_TYPES


MAIN_MENU_CALLBACKS = ("reports", "report:create", "llm", "settings", "help")


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📰 Мои отчёты", callback_data="reports"),
            InlineKeyboardButton(text="➕ Новый отчёт", callback_data="report:create"),
        ],
        [
            InlineKeyboardButton(text="🔑 DeepSeek", callback_data="llm"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])


def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 DeepSeek", callback_data="llm")],
        [InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:timezone")],
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")],
    ])


def timezone_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=zone, callback_data=f"timezone:{zone}")]
        for zone in ("UTC", "Europe/Moscow", "Europe/Berlin")
    ])


def credential_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить ключ", callback_data="llm:add")],
        [InlineKeyboardButton(text="Заменить ключ", callback_data="llm:replace")],
        [InlineKeyboardButton(text="Удалить ключ", callback_data="llm:delete")],
    ])


def confirmation_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, заменить", callback_data="llm:replace:confirm")],
        [InlineKeyboardButton(text="Отмена", callback_data="llm:replace:cancel")],
    ])


def report_confirmation_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data="report:confirm")],
        [InlineKeyboardButton(text="Отмена", callback_data="report:cancel")],
    ])


def report_menu(report_id: str, enabled: bool = True) -> InlineKeyboardMarkup:
    toggle = "pause" if enabled else "resume"
    toggle_label = "Приостановить" if enabled else "Возобновить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Источники", callback_data=f"source:list:{report_id}")],
        [InlineKeyboardButton(text="Правила", callback_data=f"report:rules:{report_id}"), InlineKeyboardButton(text="Расписание", callback_data=f"report:schedule:{report_id}")],
        [InlineKeyboardButton(text=toggle_label, callback_data=f"report:{toggle}:{report_id}"), InlineKeyboardButton(text="Запустить", callback_data=f"report:run:{report_id}")],
        [InlineKeyboardButton(text="История", callback_data=f"report:history:{report_id}"), InlineKeyboardButton(text="Удалить", callback_data=f"report:delete:{report_id}")],
    ])


def source_catalog_menu(report_id: str, _capabilities=None) -> InlineKeyboardMarkup:
    labels = {
        "rss": "🟠 RSS / Atom",
        "telegram": "🔵 Telegram-канал",
        "github": "⚫ GitHub",
        "hackernews": "🟠 Hacker News",
    }
    rows = [
        [InlineKeyboardButton(text=labels[source_type], callback_data=f"source:create:{source_type}:{report_id}")]
        for source_type in STABLE_SOURCE_TYPES
    ]
    rows.extend([
        [InlineKeyboardButton(text="‹ Назад", callback_data=f"source:list:{report_id}")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirmation_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, удалить", callback_data="source:delete-confirm")],
        [
            InlineKeyboardButton(text="‹ Назад", callback_data="source:delete-back"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])


def primary_input_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel"),
    ]])


def accepted_value_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее →", callback_data="source:next")],
        [
            InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])


def source_options_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее →", callback_data="source:summary")],
        [InlineKeyboardButton(text="⚙️ Дополнительные настройки", callback_data="source:advanced")],
        [InlineKeyboardButton(text="Значения по умолчанию", callback_data="source:summary")],
        [
            InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])


def field_menu(source_type: str) -> InlineKeyboardMarkup:
    fields = {
        "rss": [("Название", "name"), ("Категория", "category")],
        "telegram": [("Категория", "category"), ("Количество сообщений", "fetch_limit")],
        "github": [("Категория", "category")],
        "hackernews": [
            ("Количество публикаций", "fetch_top_stories"),
            ("Минимальный рейтинг", "min_score"),
            ("Категория", "category"),
        ],
    }[source_type]
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"source:field:{name}")]
        for label, name in fields
    ]
    rows.extend([
        [InlineKeyboardButton(text="Готово", callback_data="source:summary")],
        [
            InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def summary_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Сохранить источник", callback_data="source:save"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="source:advanced"),
        ],
        [
            InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])


def source_menu(
    source_id: str,
    enabled: bool,
    editable: bool = True,
) -> InlineKeyboardMarkup:
    toggle = "disable" if enabled else "enable"
    label = "Отключить" if enabled else "Включить"
    rows = []
    if editable:
        rows.append([InlineKeyboardButton(text="Изменить", callback_data=f"source:edit:{source_id}")])
    rows.extend([
        [InlineKeyboardButton(text=label, callback_data=f"source:{toggle}:{source_id}")],
        [InlineKeyboardButton(text="Удалить", callback_data=f"source:delete:{source_id}")],
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
