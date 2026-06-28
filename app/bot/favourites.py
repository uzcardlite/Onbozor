"""Sevimlilar (favourites) — listings and shops."""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import ContextTypes

from app.database import async_session
from app.models.listing import Listing
from app.models.shop import Shop
from app.services.user_service import get_user
from app.services.favourite_service import get_favourite_listings, get_favourite_shops
from app.bot import keyboards as kb
from app.bot.common import logger, section_label, fmt_price, safe_edit, reply


async def favourites_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await reply(update, "❌ Avval /start bosing.")
                return
            fav_listings = await get_favourite_listings(s, user.id)
            fav_shops = await get_favourite_shops(s, user.id)

            listing_rows, shop_rows = [], []
            for f in fav_listings[:10]:
                listing = await s.get(Listing, f.listing_id)
                if listing:
                    listing_rows.append([
                        B(f"📢 {section_label(listing.section)} — {fmt_price(listing.price)}",
                          callback_data=f"l_view:{listing.id}"),
                        B("🗑", callback_data=f"fav:listing:{listing.id}"),
                    ])
            for f in fav_shops[:10]:
                shop = await s.get(Shop, f.shop_id)
                if shop:
                    shop_rows.append([
                        B(f"🏪 {shop.name}", callback_data=f"sh_view:{shop.id}"),
                        B("🗑", callback_data=f"fav:shop:{shop.id}"),
                    ])
    except Exception as e:
        logger.error("favourites error: %s", e, exc_info=True)
        await reply(update, "❌ Xatolik yuz berdi.")
        return

    if not listing_rows and not shop_rows:
        text = "❤️ Sevimlilar ro'yxati bo'sh."
        markup = kb.home_kb()
    else:
        parts = []
        rows = []
        if listing_rows:
            parts.append(f"❤️ Sevimli e'lonlar: {len(listing_rows)}")
            rows += listing_rows
        if shop_rows:
            parts.append(f"🏪 Sevimli do'konlar: {len(shop_rows)}")
            rows += shop_rows
        rows.append([B("🏠 Bosh menyu", callback_data="menu:home")])
        text = "\n".join(parts)
        markup = InlineKeyboardMarkup(rows)

    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)
