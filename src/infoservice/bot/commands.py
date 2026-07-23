"""Telegram command menu configuration."""

from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS = (
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="menu", description="Открыть главное меню"),
    BotCommand(command="reports", description="Показать мои отчёты"),
    BotCommand(command="newreport", description="Создать новый отчёт"),
    BotCommand(command="sources", description="Управлять источниками"),
    BotCommand(command="settings", description="Настройки и ключ DeepSeek"),
    BotCommand(command="help", description="Команды и примеры"),
    BotCommand(command="cancel", description="Отменить текущее действие"),
)


async def configure_bot_commands(bot: Bot) -> None:
    """Register the default command menu before polling starts."""
    await bot.set_my_commands(list(BOT_COMMANDS))
