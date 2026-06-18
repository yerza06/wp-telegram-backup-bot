from __future__ import annotations

import html
from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import Settings
from bot.keyboards.main import restore_confirm_keyboard
from bot.services import OperationBusyError, RestoreService
from bot.services.disk import format_bytes

router = Router(name=__name__)
_external_restore_requests: dict[str, str] = {}


def _copy_commands_hint(settings: Settings) -> str:
    dest = html.escape(f"{settings.core.ssh}:{settings.backup.path_dir}/")
    return (
        "\n\n📤 Сначала скопируйте архив на сервер одной из команд:\n\n"
        "<b>scp:</b>\n"
        f"<code>scp ./backup.tar.zst {dest}</code>\n\n"
        "<b>rsync:</b>\n"
        f"<code>rsync -avP ./backup.tar.zst {dest}</code>"
    )


async def _safe_restore_message(coro) -> str:  # type: ignore[no-untyped-def]
    try:
        return await coro
    except OperationBusyError as exc:
        return f"⏳ Сейчас уже выполняется операция {exc.operation.operation_type} #{exc.operation.id}. Дождитесь завершения."


def external_restore_confirm_keyboard(token: str):  # type: ignore[no-untyped-def]
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить восстановление", callback_data=f"restore:path:confirm:{token}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()


async def _send_restore_points(message: Message, restore_service: RestoreService) -> None:
    try:
        restore_points = await restore_service.get_restore_points(limit=10)
    except OperationBusyError as exc:
        await message.answer(f"⏳ Сейчас уже выполняется операция {exc.operation.operation_type} #{exc.operation.id}. Дождитесь завершения.")
        return

    if not restore_points:
        await message.answer("Нет бэкапов с существующими архивами.")
        return

    builder = InlineKeyboardBuilder()
    for backup in restore_points:
        created = backup.created_at.strftime("%Y-%m-%d %H:%M")
        size = f" · {format_bytes(backup.file_size_bytes)}" if backup.file_size_bytes is not None else ""
        builder.button(text=f"#{backup.id} · {created}{size}", callback_data=f"restore:select:{backup.id}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    await message.answer("Выберите бэкап для восстановления:", reply_markup=builder.as_markup())


@router.message(Command("restore"))
async def restore(message: Message, restore_service: RestoreService) -> None:
    await _send_restore_points(message, restore_service)


@router.message(F.text.regexp(r"^/restore_\d+(?:@\w+)?$"))
async def restore_by_id(message: Message) -> None:
    command = (message.text or "").split("@", maxsplit=1)[0]
    backup_id = int(command.removeprefix("/restore_"))
    await message.answer(
        f"Вы выбрали восстановление из бэкапа #{backup_id}. Подтвердите опасную операцию.",
        reply_markup=restore_confirm_keyboard(backup_id),
    )


@router.callback_query(F.data.startswith("restore:select:"))
async def restore_select(callback: CallbackQuery) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            f"Вы выбрали восстановление из бэкапа #{backup_id}. Подтвердите опасную операцию.",
            reply_markup=restore_confirm_keyboard(backup_id),
        )


@router.callback_query(F.data.startswith("restore:confirm:"))
async def restore_confirm(callback: CallbackQuery, restore_service: RestoreService) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            await _safe_restore_message(
                restore_service.restore_by_id(backup_id, telegram_user_id=callback.from_user.id if callback.from_user else None)
            )
        )


@router.message(Command("restore_path"))
async def restore_path(message: Message, command: CommandObject, settings: Settings) -> None:
    if not command.args:
        await message.answer(
            "Укажите локальный путь: /restore_path /path/to/backup.tar.zst"
            + _copy_commands_hint(settings)
        )
        return
    token = uuid4().hex[:16]
    _external_restore_requests[token] = command.args.strip()
    await message.answer(
        f"Вы выбрали восстановление из внешнего архива:\n<code>{html.escape(command.args.strip())}</code>\n"
        "Подтвердите опасную операцию."
        + _copy_commands_hint(settings),
        reply_markup=external_restore_confirm_keyboard(token),
    )


@router.callback_query(F.data.startswith("restore:path:confirm:"))
async def restore_path_confirm(callback: CallbackQuery, restore_service: RestoreService) -> None:
    token = (callback.data or "").rsplit(":", maxsplit=1)[-1]
    path = _external_restore_requests.pop(token, None)
    await callback.answer()
    if callback.message:
        if path is None:
            await callback.message.answer("Запрос на восстановление не найден или устарел.")
            return
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            await _safe_restore_message(
                restore_service.restore_by_path(path, telegram_user_id=callback.from_user.id if callback.from_user else None)
            )
        )
