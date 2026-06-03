from __future__ import annotations

import logging

from aiogram import Bot

from bot.core.config import Settings

logger = logging.getLogger(__name__)


class AdminNotificationService:
    def __init__(self, bot: Bot, settings: Settings) -> None:
        self.bot = bot
        self.settings = settings

    def admin_user_ids(self) -> list[int]:
        ids = set(self.settings.telegram.superadmin_users) | set(self.settings.telegram.admin_users)
        return sorted(ids)

    async def notify_admins(self, text: str) -> None:
        for user_id in self.admin_user_ids():
            try:
                await self.bot.send_message(user_id, text)
            except Exception:
                logger.exception("Failed to send admin notification to %s", user_id)
