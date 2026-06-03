from __future__ import annotations

from pathlib import Path

import pytest

from bot.core.config import Settings
from bot.services.cache import CacheService
from bot.services.disk import parse_df_output, parse_du_output
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


def test_build_wp_runuser_command(settings_for_services: Settings) -> None:
    service = CacheService(settings_for_services, runner=None, sessionmaker=None)  # type: ignore[arg-type]
    command = service.build_wp_command(["cache", "flush"])
    assert command[:4] == ["runuser", "-u", "www-data", "--"]
    assert "wp" in command
    assert f"--path={settings_for_services.wordpress.path}" in command


def test_cron_trigger_from_config() -> None:
    trigger = cron_trigger_from_config("0 3 * * 5", "Asia/Almaty")
    assert trigger is not None
