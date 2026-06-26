import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from sqlalchemy import select, func
from app.database import async_session
from app.services.user_service import get_user, get_referral_count
from app.models.listing import Listing
from app.models.shop import Shop

logger = logging.getLogger(__name__)

WEB_APP = "https://onbozor.vercel.app"
LEVEL_NAMES = {1: "Yangi", 2: "Faol", 3: "Tajribali", 4: "Professional", 5: "Ekspert ⭐"}


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            ref_count = await get_referral_count(session, user.id)
            listings_count = (await session.execute(select(func.count(Listing.id)).where(Listing.user_id == user.id))).scalar() or 0
            shops = (await session.execute(select(Shop).where(Shop.owner_id == user.id))).scalars().all()
            level_name = LEVEL_NAMES.get(user.level, "Yangi")

        shop_text = f"🏪 Do'kon: {shops[0].name}" if shops else "🏪 Do'kon: yo'q"

        await update.message.reply_text(
            f"👤 <b>Sizning profilingiz</b>\n\n"
            f"📛 Ism: {user.full_name}\n"
            f"📱 Username: @{user.username or '—'}\n"
            f"📍 Viloyat: {user.viloyat or '—'}\n"
            f"🏆 Daraja: {level_name}\n"
            f"⭐ Ball: {user.points}\n\n"
            f"📢 E'lonlar: {listings_count}\n"
            f"{shop_text}\n"
            f"👥 Referrallar: {ref_count}\n"
            f"💰 Daromad: {user.ref_earnings:,} so'm",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 E'lonlarimni ko'rish", callback_data="my_listings")],
                [InlineKeyboardButton("🏪 Do'konimni ko'rish", web_app=WebAppInfo(url=f"{WEB_APP}/profile"))],
                [InlineKeyboardButton("🛍 Web App da ochish", web_app=WebAppInfo(url=f"{WEB_APP}/profile"))],
            ]),
        )
    except Exception as e:
        logger.error("profile error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi. Qayta urining: /start")


async def listings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            result = await session.execute(
                select(Listing).where(Listing.user_id == user.id).order_by(Listing.created_at.desc()).limit(10)
            )
            listings = result.scalars().all()

        if not listings:
            await update.message.reply_text(
                "📋 Sizda hali e'lonlar yo'q.\n\nBirinchi e'loningizni bering!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 E'lon berish", web_app=WebAppInfo(url=f"{WEB_APP}/add-listing"))],
                ]),
            )
            return

        for l in listings:
            status_map = {"pending": "⏳ Kutmoqda", "active": "✅ Faol", "rejected": "❌ Rad", "deleted": "🗑 O'chirilgan"}
            s = l.status.value if hasattr(l.status, 'value') else l.status
            status = status_map.get(s, s)

            await update.message.reply_text(
                f"📢 <b>{l.category}</b>\n"
                f"💰 {l.price:,} so'm\n"
                f"📍 {l.viloyat}\n"
                f"👁 {l.views} marta ko'rildi\n"
                f"📊 Status: {status}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👁 Ko'rish", web_app=WebAppInfo(url=f"{WEB_APP}/listing/{l.id}")),
                        InlineKeyboardButton("🚀 Promote", web_app=WebAppInfo(url=f"{WEB_APP}/listing/{l.id}")),
                    ],
                ]),
            )
    except Exception as e:
        logger.error("listings error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            result = await session.execute(select(Shop).where(Shop.owner_id == user.id).limit(1))
            shop = result.scalar_one_or_none()

        if not shop:
            await update.message.reply_text(
                "🏪 Sizda hali do'kon yo'q.\n\nDo'kon oching va mahsulotlaringizni soting!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏪 Do'kon ochish", web_app=WebAppInfo(url=f"{WEB_APP}/open-shop"))],
                ]),
            )
            return

        status = "🟢 Faol" if shop.is_active else "🔴 Nofaol"
        expires = shop.subscription_expires.strftime("%d.%m.%Y") if shop.subscription_expires else "—"

        await update.message.reply_text(
            f"🏪 <b>{shop.name}</b>\n\n"
            f"📁 Kategoriya: {shop.category}\n"
            f"📍 Viloyat: {shop.viloyat or '—'}\n"
            f"📊 Status: {status}\n"
            f"📅 Obuna: {expires}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏪 Do'konni ochish", web_app=WebAppInfo(url=f"{WEB_APP}/shop/{shop.id}"))],
            ]),
        )
    except Exception as e:
        logger.error("shop error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def my_listings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    update.message = query.message
    update.effective_user = query.from_user
    await listings_command(update, context)


def get_profile_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("listings", listings_command),
        CommandHandler("mylisting", listings_command),
        CommandHandler("shop", shop_command),
        CallbackQueryHandler(my_listings_callback, pattern=r"^my_listings$"),
        MessageHandler(filters.Regex(r"^👤 Profil$"), profile_command),
        MessageHandler(filters.Regex(r"^📋 Mening e'lonlarim$"), listings_command),
    ]
