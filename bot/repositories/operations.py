from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.operation import Operation

HEAVY_OPERATION_TYPES = ("backup", "restore")
ACTIVE_STATUSES = ("queued", "running")


class OperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        operation_type: str,
        status: str = "queued",
        telegram_user_id: int | None = None,
        backup_id: int | None = None,
        details_json: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> Operation:
        operation = Operation(
            operation_type=operation_type,
            status=status,
            telegram_user_id=telegram_user_id,
            backup_id=backup_id,
            details_json=details_json,
            error_message=error_message,
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def get(self, operation_id: int) -> Operation | None:
        return await self.session.get(Operation, operation_id)

    async def update_status(
        self,
        operation_id: int,
        *,
        status: str,
        details_json: dict[str, Any] | None = None,
        error_message: str | None = None,
        backup_id: int | None = None,
        finish: bool | None = None,
    ) -> Operation | None:
        operation = await self.get(operation_id)
        if operation is None:
            return None
        operation.status = status
        if details_json is not None:
            operation.details_json = details_json
        if backup_id is not None:
            operation.backup_id = backup_id
        operation.error_message = error_message
        if finish is True or status in {"success", "failed", "cancelled"}:
            operation.finished_at = datetime.now(UTC)
        await self.session.flush()
        return operation

    async def list_recent(self, *, limit: int = 20) -> Sequence[Operation]:
        stmt = select(Operation).order_by(Operation.started_at.desc()).limit(limit)
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_active_heavy_operation(self) -> Operation | None:
        stmt = (
            select(Operation)
            .where(
                Operation.operation_type.in_(HEAVY_OPERATION_TYPES),
                Operation.status.in_(ACTIVE_STATUSES),
            )
            .order_by(Operation.started_at.asc())
            .limit(1)
        )
        return await self.session.scalar(stmt)
