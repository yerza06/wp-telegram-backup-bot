from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

BACKUP_BUTTON_TEXT = "💾 Создать полный бэкап"
DISK_BUTTON_TEXT = "💽 Проверить диск"
DISK_CHART_BUTTON_TEXT = "📊 График диска"
BACKUPS_BUTTON_TEXT = "📦 Показать бэкапы"
CLEAR_CACHE_BUTTON_TEXT = "🧹 Очистить кэш"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BACKUP_BUTTON_TEXT)],
            [KeyboardButton(text=DISK_BUTTON_TEXT), KeyboardButton(text=DISK_CHART_BUTTON_TEXT)],
            [KeyboardButton(text=BACKUPS_BUTTON_TEXT)],
            [KeyboardButton(text=CLEAR_CACHE_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


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


def backups_manage_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Список бэкапов: по кнопке на каждый бэкап (id, подпись)."""
    builder = InlineKeyboardBuilder()
    for backup_id, label in items:
        builder.button(text=label, callback_data=f"backup:open:{backup_id}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()


def backup_actions_keyboard(backup_id: int, *, can_restore: bool, can_delete: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if can_restore:
        builder.button(text="♻️ Восстановить", callback_data=f"restore:select:{backup_id}")
    if can_delete:
        builder.button(text="🗑️ Удалить", callback_data=f"backup:delete:ask:{backup_id}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()


def backup_delete_confirm_keyboard(backup_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"backup:delete:confirm:{backup_id}")
    builder.button(text="Отмена", callback_data="menu:cancel")
    builder.adjust(1)
    return builder.as_markup()
