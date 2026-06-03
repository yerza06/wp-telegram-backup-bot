from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.core.auth import get_user_role, has_role
from bot.core.config import Settings
from bot.core.roles import CALLBACK_MIN_ROLES, COMMAND_MIN_ROLES, TEXT_MIN_ROLES, Role

logger = logging.getLogger(__name__)


def command_required_role(command: str) -> Role | None:
    if command.startswith("restore_"):
        return Role.superadmin
    return COMMAND_MIN_ROLES.get(command)


def callback_required_role(data: str | None) -> Role | None:
    if not data:
        return None
    if data.startswith("restore:confirm") or data.startswith("restore:path:confirm"):
        return Role.superadmin
    return CALLBACK_MIN_ROLES.get(data)


def text_required_role(text: str | None) -> Role | None:
    if not text:
        return None
    return TEXT_MIN_ROLES.get(text.strip())


class AccessMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        required_role = self._required_role(event)
        if required_role is None:
            return await handler(event, data)

        user = getattr(event, "from_user", None)
        user_id = user.id if user else None
        if user_id is None:
            logger.warning("Access denied: no Telegram user in event")
            return None

        role = get_user_role(user_id, self.settings.telegram)
        data["user_role"] = role

        if role is None:
            logger.warning("Unauthorized Telegram user %s tried to access %s", user_id, required_role.title)
            await self._answer(event, "⛔ Доступ запрещен.")
            return None

        if not has_role(role, required_role):
            logger.warning(
                "Telegram user %s with role %s lacks required role %s",
                user_id,
                role.title,
                required_role.title,
            )
            await self._answer(event, "⛔ Недостаточно прав для выполнения команды.")
            return None

        return await handler(event, data)

    def _required_role(self, event: TelegramObject) -> Role | None:
        if isinstance(event, Message) and event.text:
            if event.text.startswith("/"):
                command = event.text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lstrip("/")
                return command_required_role(command)
            return text_required_role(event.text)
        if isinstance(event, CallbackQuery):
            return callback_required_role(event.data)
        return None

    async def _answer(self, event: TelegramObject, text: str) -> None:
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
