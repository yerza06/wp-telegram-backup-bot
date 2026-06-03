from __future__ import annotations

from bot.core.config import Settings
from bot.services.disk import DiskService, format_bytes
from bot.services.operations import OperationService


class StatusService:
    def __init__(self, settings: Settings, operations: OperationService, disk_service: DiskService) -> None:
        self.settings = settings
        self.operations = operations
        self.disk_service = disk_service

    async def get_status_text(self) -> str:
        active = await self.operations.get_active_heavy_operation()
        busy_text = "нет" if active is None else f"{active.operation_type} #{active.id} ({active.status})"
        try:
            usage = await self.disk_service.get_usage(self.settings.backup.path_dir)
            disk_text = f"Свободно на диске: {format_bytes(usage.available_bytes)}"
        except Exception:
            disk_text = "Свободно на диске: не удалось определить"
        return (
            "🤖 Бот запущен.\n"
            f"Сайт: <code>{self.settings.wordpress.path}</code>\n"
            f"Папка бэкапов: <code>{self.settings.backup.path_dir}</code>\n"
            f"Текущая тяжелая операция: {busy_text}\n"
            f"{disk_text}"
        )
