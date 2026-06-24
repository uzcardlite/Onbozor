from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters,
)
from app.database import async_session
from app.services.shop_service import get_shops_by_category, get_shop, get_shop_products
from app.services.favourite_service import toggle_favourite_shop, is_favourite_shop
from app.services.user_service import get_user
from app.keyboards.main import shop_categories_keyboard, favourite_toggle_keyboard, regions_keyboard
from app.constants import CATEGORIES


async def shops_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏪 Do'konlar\n\nBo'limni tanlang:",
        reply_markup=shop_categories_keyboard(),
    )


async def shop_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split(":")[1]
    context.user_data["shop_browse_cat"] = category

    buttons = [
        [InlineKeyboardButton(r, callback_data=f"shop_region:{r}")]
        for r in ["Barcha viloyatlar"] + __import__("app.constants", fromlist=["REGIONS"]).REGIONS
    ]
    await query.edit_message_text("📍 Viloyatni tanlang:", reply_markup=InlineKeyboardMarkup(buttons[:8]))


async def shop_region_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    region_text = query.data.split(":")[1]
    category = context.user_data.get("shop_browse_cat")
    region = None if region_text == "Barcha viloyatlar" else region_text

    async with async_session() as session:
        shops = await get_shops_by_category(session, category, region)

    if not shops:
        await query.edit_message_text("😔 Bu bo'limda hozircha do'kon yo'q.")
        return

    buttons = [
        [InlineKeyboardButton(f"🏪 {shop.name}", callback_data=f"view_shop:{shop.id}")]
        for shop in shops
    ]
    await query.edit_message_text("🏪 Do'konlar:", reply_markup=InlineKeyboardMarkup(buttons))


async def view_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    shop_id = int(query.data.split(":")[1])

    async with async_session() as session:
        shop = await get_shop(session, shop_id)
        if not shop:
            await query.edit_message_text("❌ Do'kon topilmadi.")
            return

        products = await get_shop_products(session, shop_id)
        user = await get_user(session, update.effective_user.id)
        is_fav = await is_favourite_shop(session, user.id, shop_id) if user else False

    text = (
        f"🏪 {shop.name}\n\n"
        f"📁 Bo'lim: {shop.category}\n"
        f"📍 Viloyat: {shop.region}\n"
        f"📝 {shop.description}\n"
        f"📱 Kontakt: @{shop.contact_username}\n\n"
        f"📦 Mahsulotlar soni: {len(products)}"
    )

    buttons = []
    if products:
        for p in products[:10]:
            buttons.append([InlineKeyboardButton(
                f"{p.name} — {p.price:,} so'm",
                callback_data=f"view_product:{p.id}",
            )])

    fav_text = "💔 Sevimlilardan o'chirish" if is_fav else "❤️ Sevimlilarga qo'shish"
    buttons.append([InlineKeyboardButton(fav_text, callback_data=f"fav:shop:{shop_id}")])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"shop_cat:{shop.category}")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def toggle_shop_favourite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    shop_id = int(parts[2])

    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            return
        is_added = await toggle_favourite_shop(session, user.id, shop_id)

    text = "❤️ Sevimlilarga qo'shildi!" if is_added else "💔 Sevimlilardan o'chirildi!"
    await query.answer(text, show_alert=True)


def get_shop_handlers():
    return [
        MessageHandler(filters.Regex(r"^🏪 Do'konlar$"), shops_menu),
        CallbackQueryHandler(shop_category_selected, pattern=r"^shop_cat:"),
        CallbackQueryHandler(shop_region_selected, pattern=r"^shop_region:"),
        CallbackQueryHandler(view_shop, pattern=r"^view_shop:"),
        CallbackQueryHandler(toggle_shop_favourite, pattern=r"^fav:shop:"),
    ]
