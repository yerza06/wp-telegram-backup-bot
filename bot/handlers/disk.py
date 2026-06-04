from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards.main import DISK_BUTTON_TEXT, DISK_CHART_BUTTON_TEXT
from bot.services import DiskChartService, DiskService
from bot.utils.sanitize import safe_telegram_error

router = Router(name=__name__)


async def _send_disk_chart(message: Message, chart_service: DiskChartService) -> None:
    try:
        path = await chart_service.build_chart(telegram_user_id=message.from_user.id if message.from_user else None)
        await message.answer_photo(FSInputFile(path), caption="📊 График использования диска")
    except Exception as exc:
        await message.answer(safe_telegram_error(exc))


@router.message(Command("disk"))
async def disk(message: Message, disk_service: DiskService) -> None:
    try:
        await message.answer(await disk_service.get_disk_text())
    except Exception as exc:
        await message.answer(safe_telegram_error(exc))


@router.message(F.text == DISK_BUTTON_TEXT)
async def disk_reply_button(message: Message, disk_service: DiskService) -> None:
    try:
        await message.answer(await disk_service.get_disk_text())
    except Exception as exc:
        await message.answer(safe_telegram_error(exc))


@router.callback_query(F.data == "disk:check")
async def disk_callback(callback: CallbackQuery, disk_service: DiskService) -> None:
    await callback.answer()
    if callback.message:
        try:
            await callback.message.answer(await disk_service.get_disk_text())
        except Exception as exc:
            await callback.message.answer(safe_telegram_error(exc))


@router.message(Command("disk_chart"))
async def disk_chart(message: Message, disk_chart_service: DiskChartService) -> None:
    await _send_disk_chart(message, disk_chart_service)


@router.message(F.text == DISK_CHART_BUTTON_TEXT)
async def disk_chart_reply_button(message: Message, disk_chart_service: DiskChartService) -> None:
    await _send_disk_chart(message, disk_chart_service)


@router.callback_query(F.data == "disk:chart")
async def disk_chart_callback(callback: CallbackQuery, disk_chart_service: DiskChartService) -> None:
    await callback.answer()
    if callback.message:
        await _send_disk_chart(callback.message, disk_chart_service)
