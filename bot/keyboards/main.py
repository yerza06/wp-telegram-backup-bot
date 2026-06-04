from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

BACKUP_BUTTON_TEXT = "💾 Создать полный бэкап"
DISK_BUTTON_TEXT = "💽 Проверить диск"
DISK_CHART_BUTTON_TEXT = "📊 График диска"
BACKUPS_BUTTON_TEXT = "📦 Показать бэкапы"
RESTORE_BUTTON_TEXT = "♻️ Восстановить сайт"
CLEAR_CACHE_BUTTON_TEXT = "🧹 Очистить кэш"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BACKUP_BUTTON_TEXT)],
            [KeyboardButton(text=DISK_BUTTON_TEXT), KeyboardButton(text=DISK_CHART_BUTTON_TEXT)],
            [KeyboardButton(text=BACKUPS_BUTTON_TEXT), KeyboardButton(text=RESTORE_BUTTON_TEXT)],
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
