from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bot.core.config import Settings
from bot.db.base import Base
# import bot.models  # noqa: F401  # ensure model metadata is registered
import bot.models


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.sqlite_url, future=True)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def configure_database(settings: Settings) -> async_sessionmaker[AsyncSession]:
    global _engine, _sessionmaker
    if settings.core.sqlite_path.parent != settings.core.sqlite_path:
        settings.core.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(settings)
    _sessionmaker = create_sessionmaker(_engine)
    await init_db(_engine)
    return _sessionmaker


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Database is not configured")
    return _sessionmaker


async def session_scope() -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session


async def close_database() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
