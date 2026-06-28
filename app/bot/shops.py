"""Do'konlar (browse shops) — in-bot."""
import uuid as uuidlib

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from app.database import async_session
from app.models.shop import Shop
from app.models.listing import Listing
from app.models.review import Review
from app.models.enums import SectionEnum, ListingStatusEnum
from app.services.shop_service import get_shops_by_category, get_shop_products
from app.services.favourite_service import toggle_favourite_shop, is_favourite_shop
from app.services.user_service import get_user
from app.bot import keyboards as kb
from app.bot.common import logger, SECTIONS, section_label, fmt_price, safe_edit, is_subscribed


async def shops_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context.bot, update.effective_user.id):
        msg = update.message or update.callback_query.message
        await msg.reply_text("📢 Avval kanalga obuna bo'ling 👇", reply_markup=kb.subscribe_kb())
        return
    text = "🏪 Kategoriyani tanlang:"
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=kb.shop_sections_kb())
    else:
        await update.message.reply_text(text, reply_markup=kb.shop_sections_kb())


async def shop_category_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    section_enum = SECTIONS[key]["enum"]
    try:
        async with async_session() as s:
            shops = await get_shops_by_category(s, section_enum)
            rows = []
            for shop in shops[:15]:
                cnt = (await s.execute(
                    select(func.count(Listing.id)).where(
                        Listing.shop_id == shop.id, Listing.status == ListingStatusEnum.ACTIVE
                    )
                )).scalar() or 0
                rows.append([B(f"🏪 {shop.name} ({cnt})", callback_data=f"sh_view:{shop.id}")])
    except Exception as e:
        logger.error("shop_category error: %s", e, exc_info=True)
        await safe_edit(query, "❌ Xatolik yuz berdi.", reply_markup=kb.home_kb())
        return

    if not rows:
        await safe_edit(query, "😔 Bu bo'limda hozircha do'kon yo'q.", reply_markup=kb.shop_sections_kb())
        return
    rows.append([B("⬅️ Orqaga", callback_data="menu:shops")])
    await safe_edit(query, f"{section_label(section_enum)} — do'konlar:", reply_markup=InlineKeyboardMarkup(rows))


async def open_shop_view(update: Update, context: ContextTypes.DEFAULT_TYPE, shop_id):
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    try:
        sid = uuidlib.UUID(str(shop_id))
    except (ValueError, AttributeError):
        if msg:
            await msg.reply_text("❌ Do'kon topilmadi.")
        return
    try:
        async with async_session() as s:
            shop = await s.get(Shop, sid)
            if not shop:
                if msg:
                    await msg.reply_text("❌ Do'kon topilmadi.")
                return
            products = await get_shop_products(s, sid)
            avg = (await s.execute(
                select(func.avg(Review.rating)).join(Listing, Review.listing_id == Listing.id)
                .where(Listing.shop_id == sid)
            )).scalar()
            viewer = await get_user(s, update.effective_user.id)
            is_fav = await is_favourite_shop(s, viewer.id, sid) if viewer else False
            rating = f"{float(avg):.1f}" if avg else "—"
            text = (
                f"🏪 <b>{shop.name}</b>\n\n"
                f"📍 {shop.viloyat or 'Barcha viloyatlar'}\n"
                f"📁 {section_label(shop.category)}\n"
                f"📢 {len(products)} ta e'lon\n"
                f"⭐ Reyting: {rating}\n\n"
                f"📝 {shop.description}"
            )
            rows = []
            for p in products[:10]:
                rows.append([B(f"{section_label(p.section)} — {fmt_price(p.price)} so'm",
                               callback_data=f"l_view:{p.id}")])
            fav_text = "💔 Kuzatishni bekor" if is_fav else "🔔 Kuzatish"
            rows.append([B(fav_text, callback_data=f"fav:shop:{shop.id}")])
            rows.append([B("🏠 Bosh menyu", callback_data="menu:home")])
    except Exception as e:
        logger.error("open_shop_view error: %s", e, exc_info=True)
        if msg:
            await msg.reply_text("❌ Xatolik yuz berdi.")
        return
    if msg:
        await msg.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))


async def shop_view_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await open_shop_view(update, context, query.data.split(":", 1)[1])


async def toggle_fav_shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    shop_id = query.data.split(":", 2)[2]
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await query.answer("Avval /start bosing", show_alert=True)
                return
            added = await toggle_favourite_shop(s, user.id, uuidlib.UUID(shop_id))
        await query.answer("🔔 Kuzatishga qo'shildi!" if added else "💔 O'chirildi")
    except Exception as e:
        logger.error("toggle fav shop error: %s", e)
        await query.answer("❌ Xatolik", show_alert=True)
