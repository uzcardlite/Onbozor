"""Shared Application factory for webhook mode (FastAPI)."""
from telegram.ext import Application

from app.config import settings
from app.bot.registry import register_handlers

_bot_app: Application | None = None


async def get_bot_application() -> Application:
    global _bot_app
    if _bot_app is not None:
        return _bot_app

    app = Application.builder().token(settings.BOT_TOKEN).updater(None).build()
    register_handlers(app)
    await app.initialize()
    _bot_app = app
    return _bot_app
