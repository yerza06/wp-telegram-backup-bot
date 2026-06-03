from __future__ import annotations

from bot.core.roles import Role
from bot.core.security import callback_required_role, command_required_role, text_required_role


def test_command_access_matrix() -> None:
    assert command_required_role("status") is Role.viewer
    assert command_required_role("disk") is Role.viewer
    assert command_required_role("backups") is Role.viewer
    assert command_required_role("backup") is Role.admin
    assert command_required_role("clear_cache") is Role.admin
    assert command_required_role("restore") is Role.superadmin
    assert command_required_role("restore_42") is Role.superadmin


def test_callback_access_matrix() -> None:
    assert callback_required_role("disk:check") is Role.viewer
    assert callback_required_role("backup:create") is Role.admin
    assert callback_required_role("cache:clear:confirm") is Role.admin
    assert callback_required_role("restore:confirm:42") is Role.superadmin


def test_reply_button_access_matrix() -> None:
    assert text_required_role("💽 Проверить диск") is Role.viewer
    assert text_required_role("💾 Создать полный бэкап") is Role.admin
    assert text_required_role("🧹 Очистить кэш") is Role.admin
    assert text_required_role("обычное сообщение") is None
