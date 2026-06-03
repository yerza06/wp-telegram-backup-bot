from __future__ import annotations

from bot.core.config import TelegramSettings
from bot.core.roles import Role


def get_user_role(user_id: int, telegram: TelegramSettings) -> Role | None:
    role: Role | None = None
    if user_id in telegram.viewer_users:
        role = Role.viewer
    if user_id in telegram.admin_users:
        role = Role.admin
    if user_id in telegram.superadmin_users:
        role = Role.superadmin
    return role


def has_role(user_role: Role | None, required_role: Role) -> bool:
    return user_role is not None and user_role >= required_role
