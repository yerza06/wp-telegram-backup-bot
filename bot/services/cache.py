from __future__ import annotations

import logging
import shutil

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.config import Settings
from bot.core.errors import MissingUtilityError, ProcessExecutionError, WpCliError
from bot.repositories.operations import OperationRepository
from bot.services.filesystem import ensure_wordpress_path
from bot.services.process import CommandRunner
from bot.utils.sanitize import safe_error_text

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, settings: Settings, runner: CommandRunner, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.settings = settings
        self.runner = runner
        self.sessionmaker = sessionmaker

    def build_wp_command(self, wp_args: list[str]) -> list[str]:
        base = [self.settings.tools.wp_cli_path, *wp_args, f"--path={self.settings.wordpress.path}"]
        user = self.settings.wordpress.cli_run_as_user
        if user:
            return [self.settings.tools.runuser_path, "-u", user, "--", *base]
        return base

    async def clear_cache(self, *, telegram_user_id: int | None = None) -> str:
        async with self.sessionmaker() as session:
            op = await OperationRepository(session).create(
                operation_type="cache_clear",
                status="running",
                telegram_user_id=telegram_user_id,
            )
            await session.commit()
            try:
                ensure_wordpress_path(self.settings.wordpress.path)
                if shutil.which(self.settings.tools.wp_cli_path) is None and "/" not in self.settings.tools.wp_cli_path:
                    raise MissingUtilityError(f"WP-CLI не найден: {self.settings.tools.wp_cli_path}")
                for args in (["cache", "flush"], ["transient", "delete", "--all"]):
                    await self.runner.run(self.build_wp_command(args), cwd=str(self.settings.wordpress.path))
                await OperationRepository(session).update_status(op.id, status="success")
                await session.commit()
                logger.info("WordPress cache cleared")
                return "✅ Кэш WordPress очищен."
            except ProcessExecutionError as exc:
                safe = safe_error_text(exc)
                logger.exception("WP-CLI command failed")
                await OperationRepository(session).update_status(op.id, status="failed", error_message=safe)
                await session.commit()
                return f"❌ Кэш не очищен: {safe}\nПодробности записаны в локальный лог."
            except Exception as exc:
                safe = safe_error_text(exc)
                logger.exception("Cache clear failed")
                await OperationRepository(session).update_status(op.id, status="failed", error_message=safe)
                await session.commit()
                return f"❌ Кэш не очищен: {safe}\nПодробности записаны в локальный лог."
