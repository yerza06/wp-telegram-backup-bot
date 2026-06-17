from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.config import Settings
from bot.core.errors import ArchiveError, MySQLError, ProcessExecutionError
from bot.repositories.backups import BackupRepository
from bot.repositories.operations import OperationRepository
from bot.services.archive import ArchiveService
from bot.services.backup import BackupService
from bot.services.disk import DiskService
from bot.services.filesystem import (
    activate_restored_directory,
    ensure_directory,
    ensure_wordpress_path,
    finalize_reserved_directory,
    reserve_directory,
    rollback_reserved_directory,
    validate_wordpress_install,
)
from bot.services.operations import OperationService
from bot.services.process import CommandRunner
from bot.utils.sanitize import safe_error_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RestorePoint:
    id: int
    archive_path: Path
    file_size_bytes: int | None
    created_at: datetime


class RestoreService:
    def __init__(
        self,
        settings: Settings,
        runner: CommandRunner,
        sessionmaker: async_sessionmaker[AsyncSession],
        operations: OperationService,
        backup_service: BackupService,
        disk_service: DiskService,
        archive_service: ArchiveService,
    ) -> None:
        self.settings = settings
        self.runner = runner
        self.sessionmaker = sessionmaker
        self.operations = operations
        self.backup_service = backup_service
        self.disk_service = disk_service
        self.archive_service = archive_service

    async def get_restore_points(self, *, limit: int = 10) -> list[RestorePoint]:
        await self.operations.ensure_no_active_heavy_operation()
        async with self.sessionmaker() as session:
            backups = await BackupRepository(session).list_recent(limit=limit)
        return [
            RestorePoint(
                id=backup.id,
                archive_path=Path(backup.archive_path),
                file_size_bytes=backup.file_size_bytes,
                created_at=backup.created_at,
            )
            for backup in backups
            if backup.archive_path and Path(backup.archive_path).exists()
        ]

    async def list_restore_points(self) -> str:
        restore_points = await self.get_restore_points(limit=10)
        if not restore_points:
            return "Нет бэкапов с существующими архивами."
        lines = ["Выберите бэкап и отправьте команду /restore_<id>:"]
        for backup in restore_points:
            lines.append(f"/restore_{backup.id} — <code>{backup.archive_path}</code>")
        return "\n".join(lines)

    async def restore_by_id(self, backup_id: int, *, telegram_user_id: int | None = None) -> str:
        async with self.sessionmaker() as session:
            backup = await BackupRepository(session).get(backup_id)
            if backup is None or not backup.archive_path:
                return "❌ Бэкап не найден в локальной БД."
            archive_path = Path(backup.archive_path)
        return await self._restore(archive_path, telegram_user_id=telegram_user_id, backup_id=backup_id, external=False)

    async def restore_by_path(self, path: str, *, telegram_user_id: int | None = None) -> str:
        return await self._restore(Path(path), telegram_user_id=telegram_user_id, backup_id=None, external=True)

    async def _restore(self, archive_path: Path, *, telegram_user_id: int | None, backup_id: int | None, external: bool) -> str:
        await self.operations.ensure_no_active_heavy_operation()
        ensure_wordpress_path(self.settings.wordpress.path)
        ensure_directory(self.settings.backup.tmp_path)
        restore_tmp_parent = self.settings.wordpress.path.parent / ".telegram-wp-restore"
        ensure_directory(restore_tmp_parent)
        async with self.sessionmaker() as session:
            op = await OperationRepository(session).create(
                operation_type="restore",
                status="running",
                telegram_user_id=telegram_user_id,
                backup_id=backup_id,
                details_json={"archive_path": str(archive_path), "external": external},
            )
            await session.commit()
            extracted: Path | None = None
            reserve_path: Path | None = None
            try:
                self.archive_service.validate_archive_path(archive_path)
                await self.archive_service.ensure_archive_readable(archive_path)
                await self.disk_service.ensure_min_free_space()

                reserve_path = reserve_directory(self.settings.wordpress.path)
                extracted = await self.archive_service.extract_and_validate(
                    archive_path,
                    parent_dir=restore_tmp_parent,
                    run_as_user=self.settings.wordpress.cli_run_as_user,
                )
                activate_restored_directory(extracted / "wordpress", self.settings.wordpress.path, reserve_path)
                validate_wordpress_install(self.settings.wordpress.path)

                await self._restore_database(extracted / "database" / "db.sql")
                await self._apply_wordpress_owner()
                await asyncio.to_thread(finalize_reserved_directory, reserve_path)
                reserve_path = None
                if backup_id is not None:
                    await BackupRepository(session).update_status(backup_id, status="restored")
                await OperationRepository(session).update_status(op.id, status="success")
                await session.commit()
                return "✅ Восстановление завершено."
            except Exception as exc:
                if reserve_path is not None:
                    await asyncio.to_thread(rollback_reserved_directory, self.settings.wordpress.path, reserve_path)
                safe = safe_error_text(exc)
                logger.exception("Restore failed")
                await OperationRepository(session).update_status(op.id, status="failed", error_message=safe)
                await session.commit()
                return f"❌ Восстановление не выполнено: {safe}\nПодробности записаны в локальный лог."
            finally:
                if extracted:
                    await asyncio.to_thread(shutil.rmtree, extracted, True)

    async def _apply_wordpress_owner(self) -> None:
        wordpress_path = str(self.settings.wordpress.path)
        wordpress_user = self.settings.wordpress.cli_run_as_user or "www-data"
        owner = f"{wordpress_user}:{wordpress_user}"
        await self.runner.run(["chown", "-R", owner, wordpress_path])

    async def _restore_database(self, sql_path: Path) -> None:
        args = [
            self.settings.tools.mysql_path,
            "--host", self.settings.wordpress.db_host,
            "--port", str(self.settings.wordpress.db_port),
            "--user", self.settings.wordpress.db_user,
            self.settings.wordpress.db_name,
        ]
        try:
            await self.runner.run_with_stdin_file(
                args,
                input_path=sql_path,
                env={"MYSQL_PWD": self.settings.wordpress.db_password},
            )
        except ProcessExecutionError as exc:
            raise MySQLError("Ошибка mysql при восстановлении БД", returncode=exc.returncode, stderr=exc.stderr) from exc
