from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main import BACKUP_BUTTON_TEXT, BACKUPS_BUTTON_TEXT
from bot.services import BackupService, OperationBusyError

router = Router(name=__name__)


async def _run_backup(service: BackupService, user_id: int | None) -> str:
    try:
        return await service.start_backup(telegram_user_id=user_id)
    except OperationBusyError as exc:
        return f"⏳ Сейчас уже выполняется операция {exc.operation.operation_type} #{exc.operation.id}. Дождитесь завершения."


@router.message(Command("backup"))
async def backup(message: Message, backup_service: BackupService) -> None:
    await message.answer(await _run_backup(backup_service, message.from_user.id if message.from_user else None))


@router.message(F.text == BACKUP_BUTTON_TEXT)
async def backup_reply_button(message: Message, backup_service: BackupService) -> None:
    await message.answer(await _run_backup(backup_service, message.from_user.id if message.from_user else None))


@router.callback_query(F.data == "backup:create")
async def backup_callback(callback: CallbackQuery, backup_service: BackupService) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(await _run_backup(backup_service, callback.from_user.id if callback.from_user else None))


@router.message(Command("backups"))
async def backups(message: Message, backup_service: BackupService) -> None:
    await message.answer(await backup_service.list_backups())


@router.message(F.text == BACKUPS_BUTTON_TEXT)
async def backups_reply_button(message: Message, backup_service: BackupService) -> None:
    await message.answer(await backup_service.list_backups())


@router.callback_query(F.data == "backups:list")
async def backups_callback(callback: CallbackQuery, backup_service: BackupService) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(await backup_service.list_backups())
