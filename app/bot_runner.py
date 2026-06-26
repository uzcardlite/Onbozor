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

    logger.info("Bot polling + scheduler starting")
    loop = asyncio.new_event_loop()
    loop.create_task(start_scheduler())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
