"""Profil — in-bot profile, my listings, my shop."""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from app.database import async_session
from app.models.listing import Listing
from app.models.shop import Shop
from app.services.user_service import get_user, get_referral_count
from app.bot import keyboards as kb
from app.bot.common import (
    logger, STATUS_LABELS, section_label, fmt_price, safe_edit, reply, enum_value,
)

LEVELS = {1: "Yangi", 2: "Faol", 3: "Tajribali", 4: "Professional", 5: "Ekspert ⭐"}


async def profile_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await reply(update, "❌ Avval /start bosing.")
                return
            ref_count = await get_referral_count(s, user.id)
            listings_count = (await s.execute(
                select(func.count(Listing.id)).where(Listing.user_id == user.id)
            )).scalar() or 0
            shop = (await s.execute(select(Shop).where(Shop.owner_id == user.id).limit(1))).scalar_one_or_none()
            shop_name = shop.name if shop else "yo'q"
            text = (
                "👤 <b>Sizning profilingiz:</b>\n\n"
                f"Ism: {user.full_name}\n"
                f"Username: @{user.username or '—'}\n"
                f"📍 Viloyat: {user.viloyat or '—'}\n"
                f"Daraja: ⭐ {LEVELS.get(user.level, 'Yangi')}\n"
                f"Ball: {user.points} ball\n\n"
                f"📢 E'lonlar: {listings_count}\n"
                f"🏪 Do'kon: {shop_name}\n"
                f"👥 Referrallar: {ref_count}\n"
                f"💰 Referral daromad: {fmt_price(user.ref_earnings)} so'm"
            )
    except Exception as e:
        logger.error("profile error: %s", e, exc_info=True)
        await reply(update, "❌ Xatolik yuz berdi. /start dan qayta boshlang")
        return
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=kb.profile_kb())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb.profile_kb())


async def my_listings_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await query.message.reply_text("❌ Avval /start bosing.")
                return
            listings = (await s.execute(
                select(Listing).where(Listing.user_id == user.id)
                .order_by(Listing.created_at.desc()).limit(10)
            )).scalars().all()
    except Exception as e:
        logger.error("my_listings error: %s", e, exc_info=True)
        await query.message.reply_text("❌ Xatolik yuz berdi.")
        return

    if not listings:
        await query.message.reply_text("📢 Sizda hali e'lonlar yo'q.", reply_markup=kb.home_kb())
        return
    await query.message.reply_text(f"📢 Sizning e'lonlaringiz ({len(listings)}):")
    for l in listings:
        status = STATUS_LABELS.get(enum_value(l.status), enum_value(l.status))
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Bn
        await query.message.reply_text(
            f"📢 <b>{section_label(l.section)}</b>\n"
            f"💰 {fmt_price(l.price)} so'm\n"
            f"📍 {l.viloyat}\n"
            f"👁 {l.views} ko'rildi\n"
            f"📊 {status}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[Bn("👁 Ko'rish", callback_data=f"l_view:{l.id}")]]),
        )


async def my_shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            shop = (await s.execute(
                select(Shop).where(Shop.owner_id == user.id).limit(1)
            )).scalar_one_or_none() if user else None
    except Exception as e:
        logger.error("my_shop error: %s", e)
        await query.message.reply_text("❌ Xatolik yuz berdi.")
        return
    if not shop:
        await query.message.reply_text(
            "🏪 Sizda hali do'kon yo'q.\n/dokon_ochish buyrug'i bilan do'kon oching!",
            reply_markup=kb.home_kb(),
        )
        return
    status = "🟢 Faol" if shop.is_active else "🔴 Nofaol"
    expires = shop.subscription_expires.strftime("%d.%m.%Y") if shop.subscription_expires else "—"
    await query.message.reply_text(
        f"🏪 <b>{shop.name}</b>\n\n"
        f"📁 {section_label(shop.category)}\n"
        f"📍 {shop.viloyat or '—'}\n"
        f"📊 Status: {status}\n"
        f"📅 Obuna: {expires}\n\n"
        f"📝 {shop.description}",
        parse_mode="HTML",
        reply_markup=kb.home_kb(),
    )
