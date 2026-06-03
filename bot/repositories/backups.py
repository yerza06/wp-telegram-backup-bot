from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.backup import Backup


class BackupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        status: str = "created",
        archive_path: str | None = None,
        file_size_bytes: int | None = None,
        error_message: str | None = None,
    ) -> Backup:
        backup = Backup(
            status=status,
            archive_path=archive_path,
            file_size_bytes=file_size_bytes,
            error_message=error_message,
        )
        self.session.add(backup)
        await self.session.flush()
        return backup

    async def get(self, backup_id: int) -> Backup | None:
        return await self.session.get(Backup, backup_id)

    async def list_recent(self, *, limit: int = 10, include_removed: bool = False) -> Sequence[Backup]:
        stmt = select(Backup).order_by(Backup.created_at.desc()).limit(limit)
        if not include_removed:
            stmt = stmt.where(Backup.is_removed.is_(False))
        result = await self.session.scalars(stmt)
        return result.all()

    async def mark_removed(self, backup_id: int) -> Backup | None:
        backup = await self.get(backup_id)
        if backup is None:
            return None
        backup.is_removed = True
        await self.session.flush()
        return backup

    async def update_status(
        self,
        backup_id: int,
        *,
        status: str,
        archive_path: str | None = None,
        file_size_bytes: int | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> Backup | None:
        backup = await self.get(backup_id)
        if backup is None:
            return None
        backup.status = status
        if archive_path is not None:
            backup.archive_path = archive_path
        if file_size_bytes is not None:
            backup.file_size_bytes = file_size_bytes
        backup.error_message = error_message
        backup.finished_at = finished_at or datetime.now(UTC)
        await self.session.flush()
        return backup
