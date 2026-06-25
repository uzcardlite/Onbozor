import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user
from app.services.favourite_service import get_favourite_shops, get_favourite_listings
from app.services.shop_service import get_shop

logger = logging.getLogger(__name__)


async def show_favourites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            fav_shops = await get_favourite_shops(session, user.id)
            fav_listings = await get_favourite_listings(session, user.id)

        if not fav_shops and not fav_listings:
            await update.message.reply_text("❤️ Sevimlilar ro'yxati bo'sh.")
            return

        text = "❤️ Sevimlilar\n\n"
        buttons = []

        if fav_shops:
            text += "🏪 Do'konlar:\n"
            for fav in fav_shops[:10]:
                async with async_session() as session:
                    shop = await get_shop(session, fav.shop_id)
                    if shop:
                        text += f"  • {shop.name}\n"
                        buttons.append([InlineKeyboardButton(
                            f"🏪 {shop.name}", callback_data=f"view_shop:{shop.id}"
                        )])

        if fav_listings:
            text += f"\n📢 E'lonlar: {len(fav_listings)} ta\n"

        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
    except Exception as e:
        logger.error("show_favourites error: %s", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def get_favourite_handlers():
    return [
        MessageHandler(filters.Regex(r"^❤️ Sevimlilar$"), show_favourites),
    ]
