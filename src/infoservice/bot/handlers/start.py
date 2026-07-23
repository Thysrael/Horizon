from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.bot.keyboards import main_menu, timezone_menu
from src.infoservice.bot.messages_ru import MAIN_MENU, TIMEZONE_INVALID, TIMEZONE_REQUEST, TIMEZONE_SAVED, WELCOME
from src.infoservice.bot.states import Onboarding
from src.infoservice.db.models import User

router = Router(name="start")


async def _save_timezone(message: Message, state: FSMContext, session: AsyncSession, user: User, timezone: str) -> None:
    user.timezone = timezone
    await session.flush()
    await state.clear()
    await message.answer(f"{TIMEZONE_SAVED}\n{MAIN_MENU}", reply_markup=main_menu())


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(Onboarding.timezone)
    await message.answer(f"{WELCOME}\n{TIMEZONE_REQUEST}", reply_markup=timezone_menu())


@router.callback_query(Onboarding.timezone, F.data.startswith("timezone:"))
async def timezone_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    await callback.answer()
    timezone = callback.data.removeprefix("timezone:")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        await callback.message.answer(TIMEZONE_INVALID)
        return
    await _save_timezone(callback.message, state, session, user, timezone)


@router.message(Onboarding.timezone, F.text)
async def timezone_text(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    timezone = message.text.strip()
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        await message.answer(TIMEZONE_INVALID)
        return
    await _save_timezone(message, state, session, user, timezone)
