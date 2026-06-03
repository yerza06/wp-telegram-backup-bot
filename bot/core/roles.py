from __future__ import annotations

from enum import IntEnum


class Role(IntEnum):
    viewer = 1
    admin = 2
    superadmin = 3

    @property
    def title(self) -> str:
        return {
            Role.viewer: "viewer",
            Role.admin: "admin",
            Role.superadmin: "superadmin",
        }[self]


COMMAND_MIN_ROLES: dict[str, Role] = {
    "start": Role.viewer,
    "help": Role.viewer,
    "status": Role.viewer,
    "disk": Role.viewer,
    "disk_chart": Role.viewer,
    "backups": Role.viewer,
    "backup": Role.admin,
    "clear_cache": Role.admin,
    "restore": Role.superadmin,
    "restore_path": Role.superadmin,
}

CALLBACK_MIN_ROLES: dict[str, Role] = {
    "backup:create": Role.admin,
    "disk:check": Role.viewer,
    "disk:chart": Role.viewer,
    "backups:list": Role.viewer,
    "cache:clear:ask": Role.admin,
    "cache:clear:confirm": Role.admin,
    "restore:confirm": Role.superadmin,
}

TEXT_MIN_ROLES: dict[str, Role] = {
    "💾 Создать полный бэкап": Role.admin,
    "💽 Проверить диск": Role.viewer,
    "📊 График диска": Role.viewer,
    "📦 Показать бэкапы": Role.viewer,
    "🧹 Очистить кэш": Role.admin,
}
