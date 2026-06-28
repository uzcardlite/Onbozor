"""Polling entry point for the OnBozor Telegram bot (@onbozornewbot)."""
import logging

from telegram.ext import Application, CommandHandler

from app.config import settings
from app.bot.registry import register_handlers

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("onbozor.bot")


async def start_scheduler():
    try:
        from app.services.scheduler import scheduler_loop
        await scheduler_loop()
    except Exception as e:
        logger.error("Scheduler crashed: %s", e, exc_info=True)


async def _leaderboard_cmd(update, context):
    try:
        from app.database import async_session
        from app.services.gamification import get_leaderboard
        async with async_session() as session:
            leaders = await get_leaderboard(session, 10)
        if not leaders:
            await update.message.reply_text("🏆 Hali reyting yo'q.")
            return
        text = "🏆 <b>Top 10 sotuvchilar:</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, u in enumerate(leaders):
            m = medals[i] if i < 3 else f"{i + 1}."
            text += f"{m} {u['name']} — <b>{u['points']}</b> ball\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error("leaderboard cmd error: %s", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def build_application() -> Application:
    app = Application.builder().token(settings.BOT_TOKEN).build()
    register_handlers(app)
    app.add_handler(CommandHandler("leaderboard", _leaderboard_cmd))
    return app


def main():
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set")
        return

    app = build_application()

    async def _post_init(application):
        application.create_task(start_scheduler())
        logger.info("Scheduler task created in bot loop")

    app.post_init = _post_init
    logger.info("Bot polling + scheduler starting")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
