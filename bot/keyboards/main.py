from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💾 Создать полный бэкап", callback_data="backup:create")
    builder.button(text="💽 Проверить диск", callback_data="disk:check")
    builder.button(text="📊 График диска", callback_data="disk:chart")
    builder.button(text="📦 Показать бэкапы", callback_data="backups:list")
    builder.button(text="🧹 Очистить кэш", callback_data="cache:clear:ask")
    builder.adjust(1)
    return builder.as_markup()


def cache_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, очистить кэш", callback_data="cache:clear:confirm")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()


def restore_confirm_keyboard(backup_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить восстановление", callback_data=f"restore:confirm:{backup_id}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()
