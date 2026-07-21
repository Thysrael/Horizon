"""DeepSeek bring-your-own-key handlers.

The handler deliberately keeps the submitted key in a local variable only.  It
is validated before it reaches the database and the Telegram message is
deleted regardless of the validation outcome.
"""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.bot.keyboards import confirmation_menu, credential_menu
from src.infoservice.bot.messages_ru import (
    ACTION_CANCELLED,
    KEY_DELETED,
    KEY_INVALID,
    KEY_MISSING,
    KEY_REQUEST,
    KEY_SAVED,
    KEY_UNAVAILABLE,
    LLM_MENU,
    REPLACE_CONFIRMATION,
)
from src.infoservice.bot.states import Credentials
from src.infoservice.db.models import LLMCredential, Report, User
from src.infoservice.db.repositories.credentials import CreateCredential, CredentialRepository
from src.infoservice.llm.deepseek import (
    CredentialVerificationUnavailable,
    DeepSeekVerifier,
    InvalidCredential,
)
from src.infoservice.security.credentials import CredentialCipher


router = Router(name="credentials")


def encrypt_deepseek_key(cipher: CredentialCipher, key: str) -> tuple[str, str]:
    """Return encrypted storage data and a safe display mask for ``key``."""
    return cipher.encrypt(key), cipher.mask(key)


async def _credential_for_user(session: AsyncSession, user: User) -> LLMCredential | None:
    return await session.scalar(
        select(LLMCredential).where(LLMCredential.user_id == user.id, LLMCredential.provider == "deepseek")
    )


async def delete_deepseek_key(session: AsyncSession, user: User) -> bool:
    """Remove a user's key and stop reports that cannot run without it."""
    credential = await _credential_for_user(session, user)
    if credential is None:
        return False
    await session.delete(credential)
    await session.execute(update(Report).where(Report.user_id == user.id).values(enabled=False))
    await session.flush()
    return True


@router.callback_query(F.data == "llm")
async def llm_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(LLM_MENU, reply_markup=credential_menu())


@router.callback_query(F.data == "llm:add")
async def add_key(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    await callback.answer()
    if await _credential_for_user(session, user) is not None:
        await state.set_state(Credentials.replace_confirmation)
        await callback.message.answer(REPLACE_CONFIRMATION, reply_markup=confirmation_menu())
        return
    await state.set_state(Credentials.deepseek_key)
    await callback.message.answer(KEY_REQUEST)


@router.callback_query(F.data == "llm:replace")
async def replace_key(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    await add_key(callback, state, session, user)


@router.callback_query(Credentials.replace_confirmation, F.data == "llm:replace:confirm")
async def confirm_replace(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Credentials.deepseek_key)
    await callback.message.answer(KEY_REQUEST)


@router.callback_query(Credentials.replace_confirmation, F.data == "llm:replace:cancel")
async def cancel_replace(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(ACTION_CANCELLED)


@router.callback_query(F.data == "llm:delete")
async def delete_key(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await callback.answer()
    if await delete_deepseek_key(session, user):
        await callback.message.answer(KEY_DELETED)
    else:
        await callback.message.answer(KEY_MISSING)


@router.message(Credentials.deepseek_key, F.text)
async def receive_key(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    cipher: CredentialCipher,
    verifier: DeepSeekVerifier,
) -> None:
    key = message.text.strip()
    try:
        await asyncio.to_thread(verifier.verify, key)
        ciphertext, mask = encrypt_deepseek_key(cipher, key)
        await CredentialRepository(session).upsert(
            user.id,
            CreateCredential(provider="deepseek", model="deepseek-v4-flash", ciphertext=ciphertext.encode(), key_mask=mask),
        )
        await session.execute(update(Report).where(Report.user_id == user.id).values(enabled=True))
    except InvalidCredential:
        await message.answer(KEY_INVALID)
    except CredentialVerificationUnavailable:
        await message.answer(KEY_UNAVAILABLE)
    else:
        await state.clear()
        await message.answer(KEY_SAVED.format(mask=mask), reply_markup=credential_menu())
    finally:
        await message.delete()
