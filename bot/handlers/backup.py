from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.core.auth import has_role
from bot.core.roles import Role
from bot.keyboards.main import (
    BACKUP_BUTTON_TEXT,
    BACKUPS_BUTTON_TEXT,
    backup_actions_keyboard,
    backup_confirm_keyboard,
    backup_delete_confirm_keyboard,
    backups_manage_keyboard,
)
from bot.services import BackupService, OperationBusyError
from bot.services.disk import format_bytes

router = Router(name=__name__)


async def _run_backup(service: BackupService, user_id: int | None) -> str:
    try:
        return await service.start_backup(telegram_user_id=user_id)
    except OperationBusyError as exc:
        return f"⏳ Сейчас уже выполняется операция {exc.operation.operation_type} #{exc.operation.id}. Дождитесь завершения."


async def _start_backup(message: Message, service: BackupService, user_id: int | None) -> None:
    await message.answer("⏳ Запускаю полный бэкап. Это может занять несколько минут…")
    await message.answer(await _run_backup(service, user_id))


async def _ask_backup_confirm(message: Message) -> None:
    await message.answer(
        "Создать полный бэкап сайта? Операция может занять несколько минут.",
        reply_markup=backup_confirm_keyboard(),
    )


@router.message(Command("backup"))
async def backup(message: Message) -> None:
    await _ask_backup_confirm(message)


@router.message(F.text == BACKUP_BUTTON_TEXT)
async def backup_reply_button(message: Message) -> None:
    await _ask_backup_confirm(message)


@router.callback_query(F.data == "backup:create")
async def backup_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await _ask_backup_confirm(callback.message)


@router.callback_query(F.data == "backup:create:confirm")
async def backup_confirm_callback(callback: CallbackQuery, backup_service: BackupService) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await _start_backup(
            callback.message, backup_service, callback.from_user.id if callback.from_user else None
        )


def _backup_label(item) -> str:  # type: ignore[no-untyped-def]
    created = item.created_at.strftime("%Y-%m-%d %H:%M")
    size = f" · {format_bytes(item.file_size_bytes)}" if item.file_size_bytes is not None else ""
    flag = "" if item.exists else " · ⚠️ нет файла"
    return f"#{item.id} · {created}{size}{flag}"


async def _send_backups(message: Message, backup_service: BackupService) -> None:
    items = await backup_service.get_backup_items(limit=10)
    if not items:
        await message.answer("📦 Бэкапы пока не найдены.")
        return
    keyboard = backups_manage_keyboard([(item.id, _backup_label(item)) for item in items])
    await message.answer("📦 Выберите бэкап:", reply_markup=keyboard)


@router.message(Command("backups"))
async def backups(message: Message, backup_service: BackupService) -> None:
    await _send_backups(message, backup_service)


@router.message(F.text == BACKUPS_BUTTON_TEXT)
async def backups_reply_button(message: Message, backup_service: BackupService) -> None:
    await _send_backups(message, backup_service)


@router.callback_query(F.data == "backups:list")
async def backups_callback(callback: CallbackQuery, backup_service: BackupService) -> None:
    await callback.answer()
    if callback.message:
        await _send_backups(callback.message, backup_service)


@router.callback_query(F.data.startswith("backup:open:"))
async def backup_open(callback: CallbackQuery, backup_service: BackupService, user_role: Role | None = None) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if not callback.message:
        return
    item = await backup_service.get_backup_item(backup_id)
    if item is None:
        await callback.message.edit_text("❌ Бэкап не найден или уже удален.")
        return

    is_super = has_role(user_role, Role.superadmin)
    created = item.created_at.strftime("%Y-%m-%d %H:%M")
    size = format_bytes(item.file_size_bytes) if item.file_size_bytes is not None else "размер неизвестен"
    text = (
        f"📦 Бэкап #{item.id}\n"
        f"Дата: {created}\n"
        f"Размер: {size}\n"
        f"Статус: {item.status}\n"
        f"Путь: <code>{item.archive_path or 'не задан'}</code>"
    )
    if not is_super:
        text += "\n\nℹ️ Действия с бэкапом доступны только роли superadmin."
    keyboard = backup_actions_keyboard(item.id, can_restore=is_super, can_delete=is_super)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("backup:delete:ask:"))
async def backup_delete_ask(callback: CallbackQuery, backup_service: BackupService) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if not callback.message:
        return
    item = await backup_service.get_backup_item(backup_id)
    if item is None:
        await callback.message.edit_text("❌ Бэкап не найден или уже удален.")
        return
    await callback.message.edit_text(
        f"🗑️ Удалить бэкап #{backup_id} безвозвратно?\n<code>{item.archive_path or 'путь не задан'}</code>",
        reply_markup=backup_delete_confirm_keyboard(backup_id),
    )


@router.callback_query(F.data.startswith("backup:delete:confirm:"))
async def backup_delete_confirm(callback: CallbackQuery, backup_service: BackupService) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if not callback.message:
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    try:
        result = await backup_service.delete_backup(
            backup_id, telegram_user_id=callback.from_user.id if callback.from_user else None
        )
    except OperationBusyError as exc:
        result = f"⏳ Сейчас уже выполняется операция {exc.operation.operation_type} #{exc.operation.id}. Дождитесь завершения."
    await callback.message.answer(result)
