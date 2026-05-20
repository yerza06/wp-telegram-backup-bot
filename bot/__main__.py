import asyncio
import logging

from aiogram import Bot, Dispatcher
from pydantic import ValidationError

from bot.core.config import get_settings
from bot.core.logging import setup_logging
from bot.core.security import sanitize_text
from bot.db.session import close_engine, init_db
from bot.handlers import setup_handlers


async def run() -> None:
    settings = get_settings()
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    await init_db(settings)
    dispatcher = Dispatcher()
    setup_handlers(dispatcher)

    bot = Bot(token=settings.tg.bot_token.get_secret_value())
    logger.info("Бот запускается в режиме polling")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await close_engine()
        logger.info("Бот остановлен")


def main() -> None:
    try:
        asyncio.run(run())
    except ValidationError as exc:
        message = sanitize_text(exc)
        raise SystemExit(f"Ошибка конфигурации: {message}") from exc


if __name__ == "__main__":
    main()
