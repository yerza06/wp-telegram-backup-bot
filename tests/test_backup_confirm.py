from __future__ import annotations

import pytest

from bot.handlers import backup as backup_handler
from bot.keyboards.main import backup_confirm_keyboard


class FakeMessage:
    def __init__(self, *, from_user_id: int | None = 1) -> None:
        self.from_user = type("U", (), {"id": from_user_id})() if from_user_id is not None else None
        self.answers: list[tuple[str, object]] = []
        self.reply_markup_edits: list[object] = []

    async def answer(self, text: str, reply_markup: object = None) -> None:
        self.answers.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup: object = None) -> None:
        self.reply_markup_edits.append(reply_markup)


class FakeCallback:
    def __init__(self, message: FakeMessage | None, *, from_user_id: int | None = 1) -> None:
        self.message = message
        self.from_user = type("U", (), {"id": from_user_id})() if from_user_id is not None else None
        self.answered = False

    async def answer(self, text: str | None = None) -> None:
        self.answered = True


class StubBackupService:
    def __init__(self) -> None:
        self.started_for: list[int | None] = []

    async def start_backup(self, telegram_user_id: int | None) -> str:
        self.started_for.append(telegram_user_id)
        return "✅ Бэкап создан."


@pytest.mark.asyncio
async def test_reply_button_asks_confirmation_without_starting() -> None:
    message = FakeMessage()
    await backup_handler.backup_reply_button(message)

    assert len(message.answers) == 1
    text, markup = message.answers[0]
    assert "Создать полный бэкап" in text
    assert markup == backup_confirm_keyboard()


@pytest.mark.asyncio
async def test_command_asks_confirmation_without_starting() -> None:
    message = FakeMessage()
    await backup_handler.backup(message)

    assert len(message.answers) == 1
    _, markup = message.answers[0]
    assert markup == backup_confirm_keyboard()


@pytest.mark.asyncio
async def test_create_callback_asks_confirmation() -> None:
    message = FakeMessage()
    callback = FakeCallback(message)
    await backup_handler.backup_callback(callback)

    assert callback.answered is True
    assert len(message.answers) == 1
    _, markup = message.answers[0]
    assert markup == backup_confirm_keyboard()


@pytest.mark.asyncio
async def test_confirm_callback_starts_backup() -> None:
    message = FakeMessage(from_user_id=42)
    callback = FakeCallback(message, from_user_id=42)
    service = StubBackupService()

    await backup_handler.backup_confirm_callback(callback, service)  # type: ignore[arg-type]

    # клавиатура подтверждения снимается
    assert message.reply_markup_edits == [None]
    # бэкап запущен от имени пользователя
    assert service.started_for == [42]
    # пользователь видит прогресс и итоговый результат
    assert len(message.answers) == 2
    assert "Запускаю полный бэкап" in message.answers[0][0]
    assert message.answers[1][0] == "✅ Бэкап создан."
