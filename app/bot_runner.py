import asyncio
import logging
from telegram.ext import Application, CommandHandler
from app.config import settings
from app.handlers.start import get_start_handler, help_command
from app.handlers.listing import get_listing_handler
from app.handlers.shops import get_shop_handlers
from app.handlers.profile import get_profile_handlers
from app.handlers.referral import get_referral_handlers
from app.handlers.favourites import get_favourite_handlers
from app.handlers.admin import get_admin_handlers
from app.handlers.payment import get_payment_handlers

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
        medals = ['🥇', '🥈', '🥉']
        for i, u in enumerate(leaders):
            m = medals[i] if i < 3 else f"{i+1}."
            text += f"{m} {u['name']} — <b>{u['points']}</b> ball\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error("leaderboard cmd error: %s", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def _mybadges_cmd(update, context):
    try:
        from app.database import async_session
        from app.services.user_service import get_user
        from app.services.gamification import get_user_badges, level_progress
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return
            badges = await get_user_badges(session, user.id)
            progress = level_progress(user.points)

        text = f"🎖 <b>Mening medallarim</b>\n\n"
        text += f"📊 Ball: <b>{progress['points']}</b> | Daraja: <b>{progress['name']}</b>\n\n"
        for b in badges:
            status = "✅" if b["earned"] else "🔒"
            text += f"{status} {b['emoji']} {b['name']} — {b['desc']}\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error("mybadges cmd error: %s", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def main():
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set")
        return

    app = Application.builder().token(settings.BOT_TOKEN).build()

    app.add_handler(get_start_handler())
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(get_listing_handler())

    for h in get_shop_handlers():
        app.add_handler(h)
    for h in get_profile_handlers():
        app.add_handler(h)
    for h in get_referral_handlers():
        app.add_handler(h)
    for h in get_favourite_handlers():
        app.add_handler(h)
    for h in get_payment_handlers():
        app.add_handler(h)
    for h in get_admin_handlers():
        app.add_handler(h)
    app.add_handler(CommandHandler("leaderboard", _leaderboard_cmd))
    app.add_handler(CommandHandler("mybadges", _mybadges_cmd))

    logger.info("Bot polling + scheduler starting")
    loop = asyncio.new_event_loop()
    loop.create_task(start_scheduler())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
