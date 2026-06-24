from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user
from app.services.favourite_service import get_favourite_shops, get_favourite_products
from app.services.shop_service import get_shop


async def show_favourites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            return

        fav_shops = await get_favourite_shops(session, user.id)
        fav_products = await get_favourite_products(session, user.id)

    if not fav_shops and not fav_products:
        await update.message.reply_text("❤️ Sevimlilar ro'yxati bo'sh.")
        return

    text = "❤️ Sevimlilar\n\n"

    if fav_shops:
        text += "🏪 Do'konlar:\n"
        buttons = []
        for fav in fav_shops:
            async with async_session() as session:
                shop = await get_shop(session, fav.shop_id)
                if shop:
                    text += f"  • {shop.name}\n"
                    buttons.append([InlineKeyboardButton(
                        f"🏪 {shop.name}", callback_data=f"view_shop:{shop.id}"
                    )])

        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)
    else:
        await update.message.reply_text(text)


def get_favourite_handlers():
    return [
        MessageHandler(filters.Regex(r"^❤️ Sevimlilar$"), show_favourites),
    ]
