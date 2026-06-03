from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.models.operation import Operation
from bot.repositories.operations import OperationRepository


class OperationBusyError(RuntimeError):
    def __init__(self, operation: Operation) -> None:
        self.operation = operation
        super().__init__(f"Heavy operation already active: {operation.operation_type} #{operation.id}")


class OperationService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def get_active_heavy_operation(self) -> Operation | None:
        async with self.sessionmaker() as session:
            return await OperationRepository(session).get_active_heavy_operation()

    async def ensure_no_active_heavy_operation(self) -> None:
        operation = await self.get_active_heavy_operation()
        if operation is not None:
            raise OperationBusyError(operation)
