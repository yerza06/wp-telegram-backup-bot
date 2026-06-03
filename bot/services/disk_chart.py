from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bot.core.errors import ChartBuildError
from bot.repositories.operations import OperationRepository
from bot.services.disk import DiskService, format_bytes


class DiskChartService:
    def __init__(self, disk_service: DiskService) -> None:
        self.disk_service = disk_service

    async def build_chart(self, *, telegram_user_id: int | None = None) -> Path:
        async with self.disk_service.sessionmaker() as session:
            op = await OperationRepository(session).create(
                operation_type="disk_check",
                status="running",
                telegram_user_id=telegram_user_id,
                details_json={"chart": True},
            )
            await session.commit()
            try:
                output = await self._build_chart_file()
                await OperationRepository(session).update_status(op.id, status="success")
                await session.commit()
                return output
            except Exception as exc:
                await OperationRepository(session).update_status(op.id, status="failed", error_message=str(exc))
                await session.commit()
                raise

    async def _build_chart_file(self) -> Path:
        try:
            settings = self.disk_service.settings
            usage = await self.disk_service.get_usage(settings.backup.path_dir)
            wp_size = await self.disk_service.get_dir_size(settings.wordpress.path)
            backup_size = await self.disk_service.get_dir_size(settings.backup.path_dir)
            server_other = max(usage.used_bytes - wp_size - backup_size, 0)
            free = max(usage.available_bytes, 0)

            labels = ["Сервер", "WordPress", "Бэкапы", "Свободно"]
            sizes = [server_other, wp_size, backup_size, free]
            legend = [f"{label}: {format_bytes(size)}" for label, size in zip(labels, sizes, strict=True)]

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            ax.set_title("Использование диска")
            ax.legend(legend, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2)
            output = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".png").name)
            fig.savefig(output, format="png", bbox_inches="tight")
            plt.close(fig)
            return output
        except Exception as exc:
            raise ChartBuildError(f"Не удалось построить график: {exc}") from exc
