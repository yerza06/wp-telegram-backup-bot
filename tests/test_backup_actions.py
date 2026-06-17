from __future__ import annotations

import pytest

from bot.core.config import Settings
from bot.db.session import create_engine, create_sessionmaker, init_db
from bot.repositories.backups import BackupRepository
from bot.repositories.operations import OperationRepository
from bot.services.backup import BackupService
from bot.services.operations import OperationBusyError, OperationService


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


def _backup_service(settings: Settings, sessionmaker) -> BackupService:
    operations = OperationService(sessionmaker)
    return BackupService(settings, runner=None, sessionmaker=sessionmaker, operations=operations, disk_service=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_delete_backup_removes_file_and_marks_removed(settings: Settings, tmp_path) -> None:
    archive = tmp_path / "backup.tar.zst"
    archive.write_text("data", encoding="utf-8")
    engine = create_engine(settings)
    try:
        await init_db(engine)
        sessionmaker = create_sessionmaker(engine)
        async with sessionmaker() as session:
            backup = await BackupRepository(session).create(archive_path=str(archive))
            await session.commit()
            backup_id = backup.id

        service = _backup_service(settings, sessionmaker)
        result = await service.delete_backup(backup_id, telegram_user_id=1)

        assert "удален" in result
        assert not archive.exists()
        async with sessionmaker() as session:
            stored = await BackupRepository(session).get(backup_id)
            assert stored is not None and stored.is_removed is True
            # удаление должно остаться в истории операций как тип "delete"
            ops = await OperationRepository(session).list_recent()
            assert any(op.operation_type == "delete" and op.status == "success" for op in ops)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_delete_backup_blocked_during_heavy_operation(settings: Settings, tmp_path) -> None:
    archive = tmp_path / "backup.tar.zst"
    archive.write_text("data", encoding="utf-8")
    engine = create_engine(settings)
    try:
        await init_db(engine)
        sessionmaker = create_sessionmaker(engine)
        async with sessionmaker() as session:
            backup = await BackupRepository(session).create(archive_path=str(archive))
            await OperationRepository(session).create(operation_type="restore", status="running")
            await session.commit()
            backup_id = backup.id

        service = _backup_service(settings, sessionmaker)
        with pytest.raises(OperationBusyError):
            await service.delete_backup(backup_id, telegram_user_id=1)

        # файл не должен быть удален, пока идёт тяжёлая операция
        assert archive.exists()
    finally:
        await engine.dispose()
