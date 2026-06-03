from __future__ import annotations

from bot.core.config import Settings, sanitize_text


def test_settings_load_required_and_flat_tools(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TELEGRAM__BOT_TOKEN", "123:token")
    monkeypatch.setenv("TELEGRAM__SUPERADMIN_USERS", "[1, 2]")
    monkeypatch.setenv("TELEGRAM__ADMIN_USERS", "[3, 4]")
    monkeypatch.setenv("TELEGRAM__VIEWER_USERS", "[]")
    monkeypatch.setenv("WORDPRESS__PATH", str(tmp_path / "wp"))
    monkeypatch.setenv("WORDPRESS__DB_NAME", "wpdb")
    monkeypatch.setenv("WORDPRESS__DB_USER", "wpuser")
    monkeypatch.setenv("WORDPRESS__DB_PASSWORD", "secret")
    monkeypatch.setenv("BACKUP__SITE_NAME", "site")
    monkeypatch.setenv("BACKUP__PATH_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("BACKUP__TMP_PATH", str(tmp_path / "tmp"))
    monkeypatch.setenv("BACKUP__MIN_FREE_SPACE_GB", "5")
    monkeypatch.setenv("MYSQLDUMP_PATH", "/usr/bin/mysqldump")

    settings = Settings(_env_file=None)

    assert settings.telegram.superadmin_users == [1, 2]
    assert settings.telegram.admin_users == [3, 4]
    assert settings.backup.timezone == "Asia/Almaty"
    assert settings.schedule.backup_cron == "0 3 * * 5"
    assert settings.tools.mysqldump_path == "/usr/bin/mysqldump"
    assert "secret" not in str(settings.safe_dump())


def test_sanitize_text_masks_known_secrets() -> None:
    text = 'TELEGRAM__BOT_TOKEN="123:abc" WORDPRESS__DB_PASSWORD=secret'
    sanitized = sanitize_text(text)
    assert "123:abc" not in sanitized
    assert "secret" not in sanitized
