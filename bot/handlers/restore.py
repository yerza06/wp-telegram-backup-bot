from __future__ import annotations

from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import restore_confirm_keyboard
from bot.services import OperationBusyError, RestoreService

router = Router(name=__name__)
_external_restore_requests: dict[str, str] = {}


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


@router.message(Command("restore"))
async def restore(message: Message, restore_service: RestoreService) -> None:
    await message.answer(await _safe_restore_message(restore_service.list_restore_points()))


@router.message(F.text.regexp(r"^/restore_\d+(?:@\w+)?$"))
async def restore_by_id(message: Message) -> None:
    command = (message.text or "").split("@", maxsplit=1)[0]
    backup_id = int(command.removeprefix("/restore_"))
    await message.answer(
        f"Вы выбрали восстановление из бэкапа #{backup_id}. Подтвердите опасную операцию.",
        reply_markup=restore_confirm_keyboard(backup_id),
    )


@router.callback_query(F.data.startswith("restore:confirm:"))
async def restore_confirm(callback: CallbackQuery, restore_service: RestoreService) -> None:
    backup_id = int((callback.data or "").rsplit(":", maxsplit=1)[-1])
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            await _safe_restore_message(
                restore_service.restore_by_id(backup_id, telegram_user_id=callback.from_user.id if callback.from_user else None)
            )
        )


@router.message(Command("restore_path"))
async def restore_path(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("Укажите локальный путь: /restore_path /path/to/backup.tar.zst")
        return
    token = uuid4().hex[:16]
    _external_restore_requests[token] = command.args.strip()
    await message.answer(
        f"Вы выбрали восстановление из внешнего архива:\n<code>{command.args.strip()}</code>\nПодтвердите опасную операцию.",
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
        await callback.message.answer(
            await _safe_restore_message(
                restore_service.restore_by_path(path, telegram_user_id=callback.from_user.id if callback.from_user else None)
            )
        )
