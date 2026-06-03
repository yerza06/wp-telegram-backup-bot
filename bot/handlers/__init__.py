from aiogram import Router

from bot.handlers import backup, cache, common, disk, restore


def build_router() -> Router:
    router = Router(name="telegram_wp_backup")
    router.include_routers(
        common.router,
        backup.router,
        disk.router,
        cache.router,
        restore.router,
    )
    return router


__all__ = ["build_router"]
