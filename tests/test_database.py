from __future__ import annotations

import pytest

from bot.core.config import Settings
from bot.db.session import create_engine, create_sessionmaker, init_db
from bot.repositories.backups import BackupRepository
from bot.repositories.operations import OperationRepository


@pytest.fixture
def settings(tmp_path, monkeypatch) -> Settings:
    monkeypatch.setenv("TELEGRAM__BOT_TOKEN", "123:token")
    monkeypatch.setenv("WORDPRESS__PATH", str(tmp_path / "wp"))
    monkeypatch.setenv("WORDPRESS__DB_NAME", "wpdb")
    monkeypatch.setenv("WORDPRESS__DB_USER", "wpuser")
    monkeypatch.setenv("WORDPRESS__DB_PASSWORD", "secret")
    monkeypatch.setenv("BACKUP__SITE_NAME", "site")
    monkeypatch.setenv("BACKUP__PATH_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("BACKUP__TMP_PATH", str(tmp_path / "tmp"))
    monkeypatch.setenv("BACKUP__MIN_FREE_SPACE_GB", "5")
    monkeypatch.setenv("CORE__SQLITE_PATH", str(tmp_path / "bot.sqlite3"))
    return Settings(_env_file=None)


@pytest.mark.asyncio
async def test_create_tables_and_operation(settings: Settings) -> None:
    engine = create_engine(settings)
    try:
        await init_db(engine)
        sessionmaker = create_sessionmaker(engine)
        async with sessionmaker() as session:
            operation = await OperationRepository(session).create(
                operation_type="backup",
                status="running",
                telegram_user_id=123,
            )
            backup = await BackupRepository(session).create(archive_path="/tmp/backup.tar.zst")
            await OperationRepository(session).update_status(operation.id, status="success", backup_id=backup.id)
            await session.commit()

        async with sessionmaker() as session:
            active = await OperationRepository(session).get_active_heavy_operation()
            assert active is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_find_active_heavy_operation(settings: Settings) -> None:
    engine = create_engine(settings)
    try:
        await init_db(engine)
        sessionmaker = create_sessionmaker(engine)
        async with sessionmaker() as session:
            await OperationRepository(session).create(operation_type="restore", status="running")
            await session.commit()

        async with sessionmaker() as session:
            active = await OperationRepository(session).get_active_heavy_operation()
            assert active is not None
            assert active.operation_type == "restore"
    finally:
        await engine.dispose()
