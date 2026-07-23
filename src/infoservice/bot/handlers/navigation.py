"""Global command and callback navigation available in every FSM state."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.infoservice.bot.keyboards import back_to_menu, main_menu, settings_menu, timezone_menu
from src.infoservice.bot.messages_ru import (
    ACTION_CANCELLED_MENU,
    COMMAND_HELP,
    MAIN_MENU,
    NOTHING_TO_CANCEL,
    SETTINGS_MENU,
    TIMEZONE_REQUEST,
)
from src.infoservice.bot.ui import replace_or_answer


router = Router(name="navigation")


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MAIN_MENU, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await replace_or_answer(callback.message, MAIN_MENU, main_menu())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(COMMAND_HELP, reply_markup=back_to_menu())


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await replace_or_answer(callback.message, COMMAND_HELP, back_to_menu())


@router.message(Command("settings"))
async def settings_command(message: Message, user) -> None:
    await message.answer(
        SETTINGS_MENU.format(timezone=user.timezone),
        reply_markup=settings_menu(),
    )


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery, user) -> None:
    await callback.answer()
    await replace_or_answer(
        callback.message,
        SETTINGS_MENU.format(timezone=user.timezone),
        settings_menu(),
    )


@router.callback_query(F.data == "settings:timezone")
async def timezone_settings(callback: CallbackQuery, state: FSMContext) -> None:
    from src.infoservice.bot.states import Onboarding

    await callback.answer()
    await state.clear()
    await state.set_state(Onboarding.timezone)
    await replace_or_answer(callback.message, TIMEZONE_REQUEST, timezone_menu())


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    text = ACTION_CANCELLED_MENU if current else NOTHING_TO_CANCEL
    await message.answer(text, reply_markup=main_menu())


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await replace_or_answer(callback.message, ACTION_CANCELLED_MENU, main_menu())
