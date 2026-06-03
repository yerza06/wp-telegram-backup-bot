from __future__ import annotations

from bot.core.config import sanitize_text


def safe_error_text(error: BaseException | str, *, max_length: int = 500) -> str:
    text = sanitize_text(str(error))
    if len(text) > max_length:
        return text[: max_length - 1].rstrip() + "…"
    return text


def safe_telegram_error(error: BaseException | str) -> str:
    return f"❌ Ошибка: {safe_error_text(error, max_length=250)}\nПодробности записаны в локальный лог."
