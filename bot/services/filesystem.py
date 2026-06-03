from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from bot.core.errors import BackupPathError, InvalidWordPressPathError


def ensure_wordpress_path(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise InvalidWordPressPathError(f"Каталог WordPress не найден: {path}")


def ensure_directory(path: Path, *, create: bool = True, error_cls: type[Exception] = BackupPathError) -> None:
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.exists() or not path.is_dir():
        raise error_cls(f"Каталог недоступен: {path}")


def copy_wordpress(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def replace_directory(source: Path, target: Path) -> None:
    backup_target = target.with_name(f"{target.name}.pre_restore_replace")
    if backup_target.exists():
        shutil.rmtree(backup_target)
    target.rename(backup_target)
    try:
        shutil.copytree(source, target, symlinks=True)
    except Exception:
        if target.exists():
            shutil.rmtree(target)
        backup_target.rename(target)
        raise
    shutil.rmtree(backup_target)
