from __future__ import annotations

import logging
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.config import Settings
from bot.core.errors import BackupPathError, MySQLDumpError, ProcessExecutionError
from bot.repositories.backups import BackupRepository
from bot.repositories.operations import OperationRepository
from bot.services.disk import DiskService
from bot.services.filesystem import copy_wordpress, ensure_directory, ensure_wordpress_path, write_json
from bot.services.operations import OperationBusyError, OperationService
from bot.services.process import CommandRunner
from bot.utils.sanitize import safe_error_text

logger = logging.getLogger(__name__)


class BackupService:
    def __init__(
        self,
        settings: Settings,
        runner: CommandRunner,
        sessionmaker: async_sessionmaker[AsyncSession],
        operations: OperationService,
        disk_service: DiskService,
    ) -> None:
        self.settings = settings
        self.runner = runner
        self.sessionmaker = sessionmaker
        self.operations = operations
        self.disk_service = disk_service

    async def start_backup(self, *, telegram_user_id: int | None = None, scheduled: bool = False) -> str:
        await self.operations.ensure_no_active_heavy_operation()
        async with self.sessionmaker() as session:
            operations_repo = OperationRepository(session)
            backups_repo = BackupRepository(session)
            operation = await operations_repo.create(
                operation_type="backup",
                status="running",
                telegram_user_id=telegram_user_id,
                details_json={"scheduled": scheduled},
            )
            backup = await backups_repo.create(status="created")
            operation.backup_id = backup.id
            await session.commit()

            try:
                archive_path = await self._create_archive(operation.id, backup.id)
                file_size = archive_path.stat().st_size
                await backups_repo.update_status(
                    backup.id,
                    status="created",
                    archive_path=str(archive_path),
                    file_size_bytes=file_size,
                )
                await operations_repo.update_status(operation.id, status="success")
                await session.commit()
                logger.info("Backup created: %s", archive_path)
                return f"✅ Полный бэкап создан.\nЛокальный путь: <code>{archive_path}</code>"
            except Exception as exc:
                safe = safe_error_text(exc)
                logger.exception("Backup failed")
                await backups_repo.update_status(backup.id, status="failed", error_message=safe)
                await operations_repo.update_status(operation.id, status="failed", error_message=safe)
                await session.commit()
                return f"❌ Бэкап не создан: {safe}\nПодробности записаны в локальный лог."

    async def _create_archive(self, operation_id: int, backup_id: int) -> Path:
        ensure_wordpress_path(self.settings.wordpress.path)
        ensure_directory(self.settings.backup.path_dir, error_cls=BackupPathError)
        ensure_directory(self.settings.backup.tmp_path, error_cls=BackupPathError)
        await self.disk_service.ensure_min_free_space()

        timestamp = datetime.now(UTC).astimezone().strftime("%Y-%m-%d_%H-%M-%S")
        prefix = self.settings.backup.file_prefix or self.settings.backup.site_name
        archive_name = f"{prefix}_backup_{timestamp}.tar.zst"
        archive_path = self.settings.backup.path_dir / archive_name

        staging = Path(tempfile.mkdtemp(prefix="backup_", dir=self.settings.backup.tmp_path))
        archive_created = False
        try:
            wordpress_dst = staging / "wordpress"
            database_dst = staging / "database"
            database_dst.mkdir(parents=True, exist_ok=True)
            copy_wordpress(self.settings.wordpress.path, wordpress_dst)
            await self._dump_database(database_dst / "db.sql")
            write_json(
                staging / "metadata.json",
                {
                    "site_name": self.settings.backup.site_name,
                    "created_at": datetime.now(UTC).isoformat(),
                    "operation_id": operation_id,
                    "backup_id": backup_id,
                    "format": "telegram-wp-backup/v1",
                },
            )
            await self.runner.run([
                self.settings.tools.tar_path,
                "--zstd",
                "-cf",
                str(archive_path),
                "-C",
                str(staging),
                ".",
            ])
            archive_created = True
            return archive_path
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            if not archive_created and archive_path.exists():
                archive_path.unlink(missing_ok=True)

    async def _dump_database(self, output_path: Path) -> None:
        args = [
            self.settings.tools.mysqldump_path,
            "--host", self.settings.wordpress.db_host,
            "--port", str(self.settings.wordpress.db_port),
            "--user", self.settings.wordpress.db_user,
            "--single-transaction",
            "--routines",
            "--triggers",
            self.settings.wordpress.db_name,
        ]
        env = {"MYSQL_PWD": self.settings.wordpress.db_password}
        try:
            result = await self.runner.run(args, env=env)
        except ProcessExecutionError as exc:
            raise MySQLDumpError("Ошибка mysqldump", returncode=exc.returncode, stderr=exc.stderr) from exc
        output_path.write_text(result.stdout, encoding="utf-8")

    async def create_emergency_backup(self, *, operation_id: int) -> Path:
        async with self.sessionmaker() as session:
            backup = await BackupRepository(session).create(status="created")
            await session.commit()
            try:
                archive_path = await self._create_archive(operation_id, backup.id)
                await BackupRepository(session).update_status(
                    backup.id,
                    status="created",
                    archive_path=str(archive_path),
                    file_size_bytes=archive_path.stat().st_size,
                )
                await session.commit()
                return archive_path
            except Exception as exc:
                await BackupRepository(session).update_status(backup.id, status="failed", error_message=safe_error_text(exc))
                await session.commit()
                raise

    async def list_backups(self, *, limit: int = 10) -> str:
        async with self.sessionmaker() as session:
            backups = await BackupRepository(session).list_recent(limit=limit)
        if not backups:
            return "📦 Бэкапы пока не найдены."
        lines = ["📦 Последние бэкапы:"]
        for item in backups:
            size = f", {item.file_size_bytes} байт" if item.file_size_bytes else ""
            lines.append(f"#{item.id} — {item.status}{size}\n<code>{item.archive_path or 'путь не задан'}</code>")
        return "\n\n".join(lines)
