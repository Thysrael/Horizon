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
