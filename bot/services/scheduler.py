from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.core.config import Settings
from bot.repositories.operations import OperationRepository
from bot.services.admin_notifications import AdminNotificationService
from bot.services.backup import BackupService
from bot.services.operations import OperationService

logger = logging.getLogger(__name__)


def cron_trigger_from_config(cron: str, timezone: str) -> CronTrigger:
    return CronTrigger.from_crontab(cron, timezone=timezone)


class BackupSchedulerService:
    def __init__(
        self,
        settings: Settings,
        backup_service: BackupService,
        operation_service: OperationService,
        notifications: AdminNotificationService,
    ) -> None:
        self.settings = settings
        self.backup_service = backup_service
        self.operation_service = operation_service
        self.notifications = notifications
        self.scheduler = AsyncIOScheduler(timezone=settings.backup.timezone)
        self._deferred_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self.settings.schedule.enabled:
            logger.info("Backup scheduler disabled")
            return
        trigger = cron_trigger_from_config(self.settings.schedule.backup_cron, self.settings.backup.timezone)
        self.scheduler.add_job(self.run_scheduled_backup, trigger=trigger, id="scheduled_backup", replace_existing=True)
        self.scheduler.start()
        logger.info("Backup scheduler started: %s", self.settings.schedule.backup_cron)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def run_scheduled_backup(self) -> None:
        active = await self.operation_service.get_active_heavy_operation()
        if active is not None:
            logger.warning("Scheduled backup deferred because %s #%s is active", active.operation_type, active.id)
            await self.notifications.notify_admins(
                f"⏳ Плановый бэкап отложен: выполняется {active.operation_type} #{active.id}."
            )
            if self._deferred_task is None or self._deferred_task.done():
                self._deferred_task = asyncio.create_task(self._wait_and_run())
            return
        result = await self.backup_service.start_backup(scheduled=True)
        await self.notifications.notify_admins(f"Плановый бэкап:\n{result}")

    async def _wait_and_run(self) -> None:
        while await self.operation_service.get_active_heavy_operation() is not None:
            await asyncio.sleep(30)
        result = await self.backup_service.start_backup(scheduled=True)
        await self.notifications.notify_admins(f"Отложенный плановый бэкап:\n{result}")
