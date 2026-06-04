from __future__ import annotations

from pathlib import Path

import pytest

from bot.core.config import Settings
from bot.services.cache import CacheService
from bot.services.disk import parse_df_output, parse_du_output, resolve_existing_path
from bot.services.filesystem import activate_restored_directory, finalize_reserved_directory, reserve_directory, rollback_reserved_directory, validate_wordpress_install
from bot.services.scheduler import cron_trigger_from_config


@pytest.fixture
def settings_for_services(tmp_path, monkeypatch) -> Settings:
    monkeypatch.setenv("TELEGRAM__BOT_TOKEN", "123:token")
    monkeypatch.setenv("WORDPRESS__PATH", str(tmp_path / "wp"))
    monkeypatch.setenv("WORDPRESS__DB_NAME", "wpdb")
    monkeypatch.setenv("WORDPRESS__DB_USER", "wpuser")
    monkeypatch.setenv("WORDPRESS__DB_PASSWORD", "secret")
    monkeypatch.setenv("BACKUP__SITE_NAME", "site")
    monkeypatch.setenv("BACKUP__PATH_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("BACKUP__TMP_PATH", str(tmp_path / "tmp"))
    monkeypatch.setenv("BACKUP__MIN_FREE_SPACE_GB", "5")
    return Settings(_env_file=None)


def test_parse_df_output() -> None:
    output = "Filesystem 1B-blocks Used Available Use% Mounted on\n/dev/sda1 1000 400 600 40% /\n"
    usage = parse_df_output(output, Path("/var/backups"))
    assert usage.total_bytes == 1000
    assert usage.used_bytes == 400
    assert usage.available_bytes == 600
    assert usage.use_percent == 40


def test_parse_du_output() -> None:
    assert parse_du_output("12345\t/var/www\n") == 12345


def test_resolve_existing_path_uses_nearest_parent(tmp_path) -> None:
    existing_parent = tmp_path / "backups"
    existing_parent.mkdir()
    missing_backup_dir = existing_parent / "example.com"

    assert resolve_existing_path(missing_backup_dir) == existing_parent


def test_resolve_existing_path_keeps_existing_path(tmp_path) -> None:
    existing_path = tmp_path / "backups"
    existing_path.mkdir()

    assert resolve_existing_path(existing_path) == existing_path


def test_reserve_restore_flow_moves_source_without_copy(tmp_path) -> None:
    source = tmp_path / "restore" / "wordpress"
    source.mkdir(parents=True)
    (source / "index.php").write_text("restored", encoding="utf-8")
    target = tmp_path / "site"
    target.mkdir()
    (target / "index.php").write_text("current", encoding="utf-8")

    reserve = reserve_directory(target)
    activate_restored_directory(source, target, reserve)
    finalize_reserved_directory(reserve)

    assert not source.exists()
    assert (target / "index.php").read_text(encoding="utf-8") == "restored"
    assert not reserve.exists()


def test_rollback_reserved_directory_restores_original_target(tmp_path) -> None:
    target = tmp_path / "site"
    target.mkdir()
    (target / "index.php").write_text("current", encoding="utf-8")
    reserve = reserve_directory(target)
    target.mkdir()
    (target / "index.php").write_text("broken", encoding="utf-8")

    rollback_reserved_directory(target, reserve)

    assert (target / "index.php").read_text(encoding="utf-8") == "current"
    assert not reserve.exists()


def test_validate_wordpress_install_requires_core_paths(tmp_path) -> None:
    wp_path = tmp_path / "wp"
    wp_path.mkdir()
    (wp_path / "wp-config.php").write_text("<?php", encoding="utf-8")
    (wp_path / "wp-admin").mkdir()
    (wp_path / "wp-includes").mkdir()
    (wp_path / "wp-content").mkdir()

    validate_wordpress_install(wp_path)


def test_build_wp_runuser_command(settings_for_services: Settings) -> None:
    service = CacheService(settings_for_services, runner=None, sessionmaker=None)  # type: ignore[arg-type]
    command = service.build_wp_command(["cache", "flush"])
    assert command[:4] == ["runuser", "-u", "www-data", "--"]
    assert "wp" in command
    assert f"--path={settings_for_services.wordpress.path}" in command


def test_cron_trigger_from_config() -> None:
    trigger = cron_trigger_from_config("0 3 * * 5", "Asia/Almaty")
    assert trigger is not None
