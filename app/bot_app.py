from telegram.ext import Application
from app.config import settings

_bot_app: Application | None = None


async def get_bot_application() -> Application:
    global _bot_app
    if _bot_app is not None:
        return _bot_app

    from app.handlers.start import get_start_handler
    from app.handlers.listing import get_listing_handler
    from app.handlers.shops import get_shop_handlers
    from app.handlers.profile import get_profile_handlers
    from app.handlers.referral import get_referral_handlers
    from app.handlers.favourites import get_favourite_handlers
    from app.handlers.admin import get_admin_handlers
    from app.handlers.payment import get_payment_handlers

    app = Application.builder().token(settings.BOT_TOKEN).updater(None).build()

    app.add_handler(get_start_handler())
    app.add_handler(get_listing_handler())

    for handler in get_shop_handlers():
        app.add_handler(handler)
    for handler in get_profile_handlers():
        app.add_handler(handler)
    for handler in get_referral_handlers():
        app.add_handler(handler)
    for handler in get_favourite_handlers():
        app.add_handler(handler)
    for handler in get_payment_handlers():
        app.add_handler(handler)
    for handler in get_admin_handlers():
        app.add_handler(handler)

    await app.initialize()
    _bot_app = app
    return _bot_app
