from __future__ import annotations

from bot.core.auth import get_user_role, has_role
from bot.core.config import TelegramSettings
from bot.core.roles import Role


def test_role_priority_uses_highest_role() -> None:
    telegram = TelegramSettings(
        bot_token="token",
        viewer_users=[10, 20, 30],
        admin_users=[20, 30],
        superadmin_users=[30],
    )

    assert get_user_role(10, telegram) is Role.viewer
    assert get_user_role(20, telegram) is Role.admin
    assert get_user_role(30, telegram) is Role.superadmin
    assert get_user_role(40, telegram) is None


def test_has_role() -> None:
    assert has_role(Role.superadmin, Role.admin)
    assert has_role(Role.admin, Role.viewer)
    assert not has_role(Role.viewer, Role.admin)
    assert not has_role(None, Role.viewer)
