from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.config import Settings
from bot.core.errors import DiskCheckError, InsufficientSpaceError, ProcessExecutionError
from bot.repositories.operations import OperationRepository
from bot.services.process import CommandRunner

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiskUsage:
    filesystem: str
    total_bytes: int
    used_bytes: int
    available_bytes: int
    use_percent: int
    mounted_on: str
    checked_path: Path


def parse_df_output(output: str, checked_path: Path) -> DiskUsage:
    lines = [line for line in output.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise DiskCheckError("Не удалось разобрать вывод df")
    parts = re.split(r"\s+", lines[-1])
    if len(parts) < 6:
        raise DiskCheckError("Неверный формат вывода df")
    return DiskUsage(
        filesystem=parts[0],
        total_bytes=int(parts[1]),
        used_bytes=int(parts[2]),
        available_bytes=int(parts[3]),
        use_percent=int(parts[4].rstrip("%")),
        mounted_on=parts[5],
        checked_path=checked_path,
    )


def parse_du_output(output: str) -> int:
    first = output.strip().split(maxsplit=1)[0]
    return int(first)


def format_bytes(value: int) -> str:
    units = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} Б"


def resolve_existing_path(path: Path) -> Path:
    """Return path itself or the nearest existing parent for df checks.

    The backup directory may not exist before the first backup. `df` fails for
    missing paths, but checking the nearest existing parent reports the same
    filesystem free space that the future backup directory will use.
    """
    current = path
    while not current.exists():
        parent = current.parent
        if parent == current:
            return current
        current = parent
    return current


class DiskService:
    def __init__(self, settings: Settings, runner: CommandRunner, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.settings = settings
        self.runner = runner
        self.sessionmaker = sessionmaker

    async def get_usage(self, path: Path | None = None) -> DiskUsage:
        checked_path = path or self.settings.backup.path_dir
        df_path = resolve_existing_path(checked_path)
        try:
            result = await self.runner.run([self.settings.tools.df_path, "-B1", str(df_path)])
            return parse_df_output(result.stdout, checked_path)
        except ProcessExecutionError as exc:
            raise DiskCheckError("Ошибка выполнения df", returncode=exc.returncode, stderr=exc.stderr) from exc

    async def get_dir_size(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            result = await self.runner.run([self.settings.tools.du_path, "-sb", str(path)])
            return parse_du_output(result.stdout)
        except ProcessExecutionError as exc:
            raise DiskCheckError("Ошибка выполнения du", returncode=exc.returncode, stderr=exc.stderr) from exc

    async def ensure_min_free_space(self) -> None:
        usage = await self.get_usage(self.settings.backup.path_dir)
        required = int(self.settings.backup.min_free_space_gb * 1024**3)
        if usage.available_bytes < required:
            raise InsufficientSpaceError(
                f"Свободно {format_bytes(usage.available_bytes)}, требуется минимум {self.settings.backup.min_free_space_gb} ГБ"
            )

    async def get_disk_text(self) -> str:
        async with self.sessionmaker() as session:
            op = await OperationRepository(session).create(operation_type="disk_check", status="running")
            try:
                usage = await self.get_usage(self.settings.backup.path_dir)
                await OperationRepository(session).update_status(op.id, status="success")
                await session.commit()
            except Exception as exc:
                await OperationRepository(session).update_status(op.id, status="failed", error_message=str(exc))
                await session.commit()
                raise
        return (
            "💽 Диск\n"
            f"Путь проверки: <code>{usage.checked_path}</code>\n"
            f"Раздел: <code>{usage.filesystem}</code> смонтирован в <code>{usage.mounted_on}</code>\n"
            f"Всего: {format_bytes(usage.total_bytes)}\n"
            f"Занято: {format_bytes(usage.used_bytes)}\n"
            f"Свободно: {format_bytes(usage.available_bytes)}\n"
            f"Использовано: {usage.use_percent}%"
        )
