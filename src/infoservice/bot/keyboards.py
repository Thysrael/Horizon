from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


MAIN_MENU_CALLBACKS = ("reports", "llm", "settings", "help")


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отчёты", callback_data="reports"), InlineKeyboardButton(text="LLM", callback_data="llm")],
        [InlineKeyboardButton(text="Настройки", callback_data="settings"), InlineKeyboardButton(text="Помощь", callback_data="help")],
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


def source_catalog_menu(report_id: str, capabilities) -> InlineKeyboardMarkup:
    rows = []
    for capability in capabilities:
        suffix = " β" if capability.stability == "beta" else ""
        rows.append([InlineKeyboardButton(text=f"{capability.label}{suffix}", callback_data=f"source:create:{capability.type}:{report_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def source_menu(source_id: str, enabled: bool) -> InlineKeyboardMarkup:
    toggle = "disable" if enabled else "enable"
    label = "Отключить" if enabled else "Включить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить", callback_data=f"source:edit:{source_id}"), InlineKeyboardButton(text=label, callback_data=f"source:{toggle}:{source_id}")],
        [InlineKeyboardButton(text="Удалить", callback_data=f"source:delete:{source_id}")],
    ])
