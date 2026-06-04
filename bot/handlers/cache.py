from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main import CLEAR_CACHE_BUTTON_TEXT, cache_confirm_keyboard
from bot.services import CacheService

router = Router(name=__name__)


@router.message(Command("clear_cache"))
async def clear_cache(message: Message) -> None:
    await message.answer(
        "Очистка кэша может повлиять на работу сайта. Подтвердите действие.",
        reply_markup=cache_confirm_keyboard(),
    )


@router.message(F.text == CLEAR_CACHE_BUTTON_TEXT)
async def clear_cache_reply_button(message: Message) -> None:
    await clear_cache(message)


@router.callback_query(F.data == "cache:clear:ask")
async def clear_cache_ask(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Очистка кэша может повлиять на работу сайта. Подтвердите действие.",
            reply_markup=cache_confirm_keyboard(),
        )


@router.callback_query(F.data == "cache:clear:confirm")
async def clear_cache_confirm(callback: CallbackQuery, cache_service: CacheService) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(await cache_service.clear_cache(telegram_user_id=callback.from_user.id if callback.from_user else None))
