from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    bot_token: str = Field(min_length=1)
    superadmin_users: list[int] = Field(default_factory=list)
    admin_users: list[int] = Field(default_factory=list)
    viewer_users: list[int] = Field(default_factory=list)

    @field_validator("superadmin_users", "admin_users", "viewer_users", mode="before")
    @classmethod
    def parse_user_ids(cls, value: Any) -> list[int]:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if stripped in ("", "[]"):
                return []
            if stripped.startswith("[") and stripped.endswith("]"):
                inner = stripped[1:-1].strip()
                if not inner:
                    return []
                return [int(part.strip().strip('"\'')) for part in inner.split(",") if part.strip()]
            return [int(part.strip()) for part in stripped.split(",") if part.strip()]
        return value


class WordPressSettings(BaseSettings):
    path: Path
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = Field(min_length=1)
    db_user: str = Field(min_length=1)
    db_password: str = Field(min_length=1)
    cli_run_as_user: str = "www-data"


class BackupSettings(BaseSettings):
    site_name: str = Field(min_length=1)
    path_dir: Path
    tmp_path: Path
    timezone: str = "Asia/Almaty"
    min_free_space_gb: float = Field(gt=0)
    file_prefix: str = ""


class CoreSettings(BaseSettings):
    sqlite_path: Path = Path("bot.sqlite3")
    logs_dir: Path = Path("logs")


class DiskChartSettings(BaseSettings):
    enabled: bool = True
    format: Literal["png"] = "png"


class ScheduleSettings(BaseSettings):
    enabled: bool = False
    backup_cron: str = "0 3 * * 5"


class ToolsSettings(BaseSettings):
    mysqldump_path: str = "mysqldump"
    mysql_path: str = "mysql"
    tar_path: str = "tar"
    zstd_path: str = "zstd"
    df_path: str = "df"
    du_path: str = "du"
    cp_path: str = "cp"
    wp_cli_path: str = "wp"
    runuser_path: str = "runuser"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    telegram: TelegramSettings
    wordpress: WordPressSettings
    backup: BackupSettings
    core: CoreSettings = Field(default_factory=CoreSettings)
    disk_chart: DiskChartSettings = Field(default_factory=DiskChartSettings)
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)
    tools: ToolsSettings = Field(default_factory=ToolsSettings)

    # Flat env variables from the technical specification.
    mysqldump_path: str | None = None
    mysql_path: str | None = None
    tar_path: str | None = None
    zstd_path: str | None = None
    df_path: str | None = None
    du_path: str | None = None
    cp_path: str | None = None
    wp_cli_path: str | None = None
    runuser_path: str | None = None

    def model_post_init(self, __context: Any) -> None:
        for source, target in (
            ("mysqldump_path", "mysqldump_path"),
            ("mysql_path", "mysql_path"),
            ("tar_path", "tar_path"),
            ("zstd_path", "zstd_path"),
            ("df_path", "df_path"),
            ("du_path", "du_path"),
            ("cp_path", "cp_path"),
            ("wp_cli_path", "wp_cli_path"),
            ("runuser_path", "runuser_path"),
        ):
            value = getattr(self, source)
            if value:
                setattr(self.tools, target, value)

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.core.sqlite_path}"

    def safe_dump(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return mask_secrets(data)


_SECRET_KEYS = ("token", "password", "secret", "key")
_SECRET_PATTERN = re.compile(
    r'(?i)((?:TELEGRAM__BOT_TOKEN|WORDPRESS__DB_PASSWORD|BOT_TOKEN|DB_PASSWORD)\s*=\s*)[^\s\n]+',
)


def mask_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if any(secret in str(key).lower() for secret in _SECRET_KEYS):
                result[key] = "***"
            else:
                result[key] = mask_secrets(item)
        return result
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    return value


def sanitize_text(text: str) -> str:
    return _SECRET_PATTERN.sub(r"\1***", text)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
