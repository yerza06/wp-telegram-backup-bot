from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from bot.core.config import Settings
from bot.core.errors import ArchiveError, ProcessExecutionError
from bot.services.process import CommandRunner


class ArchiveService:
    def __init__(self, settings: Settings, runner: CommandRunner) -> None:
        self.settings = settings
        self.runner = runner

    def validate_archive_path(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise ArchiveError(f"Архив не найден: {path}")
        if not str(path).endswith(".tar.zst"):
            raise ArchiveError("Архив должен иметь расширение .tar.zst")

    async def ensure_archive_readable(self, archive_path: Path) -> None:
        self.validate_archive_path(archive_path)
        try:
            await self.runner.run([
                self.settings.tools.tar_path,
                "--zstd",
                "-tf",
                str(archive_path),
            ])
        except ProcessExecutionError as exc:
            raise ArchiveError(f"Архив не читается: {exc}") from exc

    async def extract_and_validate(
        self,
        archive_path: Path,
        *,
        parent_dir: Path | None = None,
        run_as_user: str | None = None,
    ) -> Path:
        self.validate_archive_path(archive_path)
        target_parent = parent_dir or self.settings.backup.tmp_path
        target_parent.mkdir(parents=True, exist_ok=True)
        target = Path(tempfile.mkdtemp(prefix="restore_", dir=target_parent))
        if run_as_user:
            shutil.chown(target, user=run_as_user, group=run_as_user)
        tar_command = [
            self.settings.tools.tar_path,
            "--zstd",
            "-xf",
            str(archive_path),
            "-C",
            str(target),
        ]
        if run_as_user:
            tar_command = [self.settings.tools.runuser_path, "-u", run_as_user, "--", *tar_command]
        try:
            await self.runner.run(tar_command)
            self.validate_extracted(target)
            return target
        except ProcessExecutionError as exc:
            shutil.rmtree(target, ignore_errors=True)
            raise ArchiveError(f"Архив не читается: {exc}") from exc
        except Exception:
            shutil.rmtree(target, ignore_errors=True)
            raise

    def validate_extracted(self, path: Path) -> None:
        if not (path / "wordpress").is_dir():
            raise ArchiveError("В архиве нет директории wordpress/")
        if not (path / "database" / "db.sql").is_file():
            raise ArchiveError("В архиве нет database/db.sql")
        metadata = path / "metadata.json"
        if metadata.exists():
            try:
                json.loads(metadata.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ArchiveError("metadata.json поврежден") from exc
