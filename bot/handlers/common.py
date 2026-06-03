from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main import main_menu_keyboard
from bot.services import StatusService

router = Router(name=__name__)

HELP_TEXT = """Доступные команды:
/start — показать меню и статус доступа
/help — показать справку
/status — состояние бота
/disk — свободное место на диске
/disk_chart — график диска
/backup — создать полный бэкап
/backups — список бэкапов
/restore — выбрать бэкап для восстановления
/restore_<id> — восстановить выбранный бэкап
/restore_path <path> — восстановить внешний локальный архив
/clear_cache — очистить кэш WordPress"""


@router.message(Command("start"))
async def start(message: Message, status_service: StatusService) -> None:
    await message.answer(
        "Здравствуйте! Это локальный бот резервного копирования WordPress.\n\n"
        + await status_service.get_status_text(),
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("status"))
async def status(message: Message, status_service: StatusService) -> None:
    await message.answer(await status_service.get_status_text(), reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:cancel")
async def cancel(callback: CallbackQuery) -> None:
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.answer("Операция отменена.", reply_markup=main_menu_keyboard())
