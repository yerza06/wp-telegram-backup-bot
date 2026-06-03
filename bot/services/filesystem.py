from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from bot.core.errors import BackupPathError, InvalidWordPressPathError


def ensure_wordpress_path(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise InvalidWordPressPathError(f"Каталог WordPress не найден: {path}")


def validate_wordpress_install(path: Path) -> None:
    ensure_wordpress_path(path)
    required_paths = ("wp-config.php", "wp-admin", "wp-includes", "wp-content")
    missing = [item for item in required_paths if not (path / item).exists()]
    if missing:
        raise InvalidWordPressPathError(f"Восстановленный WordPress неполный, отсутствует: {', '.join(missing)}")


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


def reserve_directory(target: Path) -> Path:
    reserve_target = target.with_name(f"{target.name}_reserve")
    if reserve_target.exists():
        shutil.rmtree(reserve_target)
    target.rename(reserve_target)
    return reserve_target


def activate_restored_directory(source: Path, target: Path, reserve_target: Path) -> None:
    if not reserve_target.exists():
        raise FileNotFoundError(f"Reserve directory not found: {reserve_target}")
    source.rename(target)


def rollback_reserved_directory(target: Path, reserve_target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    if reserve_target.exists():
        reserve_target.rename(target)


def finalize_reserved_directory(reserve_target: Path) -> None:
    if reserve_target.exists():
        shutil.rmtree(reserve_target)
