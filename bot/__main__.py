from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.core.config import get_settings, sanitize_text
from bot.core.logging import setup_logging
from bot.core.security import AccessMiddleware
from bot.db.session import close_database, configure_database
from bot.handlers import build_router
from bot.services import (
    AdminNotificationService,
    ArchiveService,
    BackupSchedulerService,
    BackupService,
    CacheService,
    CommandRunner,
    DiskChartService,
    DiskService,
    OperationService,
    RestoreService,
    StatusService,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    try:
        settings = get_settings()
    except Exception as exc:  # pragma: no cover - startup diagnostics
        raise RuntimeError(sanitize_text(str(exc))) from exc

    setup_logging(settings)
    logger.info("Starting Telegram WP Backup bot with config: %s", settings.safe_dump())

    sessionmaker = await configure_database(settings)
    runner = CommandRunner()
    operation_service = OperationService(sessionmaker)
    disk_service = DiskService(settings, runner, sessionmaker)
    disk_chart_service = DiskChartService(disk_service)
    archive_service = ArchiveService(settings, runner)
    backup_service = BackupService(settings, runner, sessionmaker, operation_service, disk_service)
    restore_service = RestoreService(
        settings,
        runner,
        sessionmaker,
        operation_service,
        backup_service,
        disk_service,
        archive_service,
    )
    cache_service = CacheService(settings, runner, sessionmaker)

    bot = Bot(token=settings.telegram.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    notifications = AdminNotificationService(bot, settings)
    scheduler = BackupSchedulerService(settings, backup_service, operation_service, notifications)

    dispatcher = Dispatcher()
    dispatcher["settings"] = settings
    dispatcher["operation_service"] = operation_service
    dispatcher["status_service"] = StatusService(settings, operation_service, disk_service)
    dispatcher["backup_service"] = backup_service
    dispatcher["restore_service"] = restore_service
    dispatcher["disk_service"] = disk_service
    dispatcher["disk_chart_service"] = disk_chart_service
    dispatcher["cache_service"] = cache_service

    router = build_router()
    router.message.outer_middleware(AccessMiddleware(settings))
    router.callback_query.outer_middleware(AccessMiddleware(settings))
    dispatcher.include_router(router)

    scheduler.start()
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await close_database()
        logger.info("Telegram WP Backup bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
