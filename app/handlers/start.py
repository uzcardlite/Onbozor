import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler,
)
from sqlalchemy import func, select
from app.config import settings
from app.database import async_session
from app.services.user_service import get_or_create_user, get_user, process_referral
from app.keyboards.main import regions_keyboard
from app.states import RegistrationState
from app.models.user import User
from app.models.listing import Listing
from app.models.shop import Shop
from app.models.enums import ListingStatusEnum

logger = logging.getLogger(__name__)

WEB_APP = "https://onbozor.vercel.app"


def webapp_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Bozorga kirish", web_app=WebAppInfo(url=WEB_APP))],
        [
            InlineKeyboardButton("📢 E'lon berish", web_app=WebAppInfo(url=f"{WEB_APP}/add-listing")),
            InlineKeyboardButton("🏪 Do'konlar", web_app=WebAppInfo(url=f"{WEB_APP}/shops")),
        ],
        [
            InlineKeyboardButton("👤 Profilim", web_app=WebAppInfo(url=f"{WEB_APP}/profile")),
            InlineKeyboardButton("🔗 Referral", web_app=WebAppInfo(url=f"{WEB_APP}/referral")),
        ],
    ])


def subscribe_keyboard():
    channel_url = f"https://t.me/{settings.CHANNEL_ID.lstrip('@')}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga o'tish", url=channel_url)],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_sub")],
    ])


def deep_link_keyboard(item_type, item_id):
    url = f"{WEB_APP}/listing/{item_id}" if item_type == "listing" else f"{WEB_APP}/shop/{item_id}"
    label = "📢 E'lonni ko'rish" if item_type == "listing" else "🏪 Do'konni ko'rish"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton("🛍 Bosh sahifa", web_app=WebAppInfo(url=WEB_APP))],
    ])


async def _is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Sub check failed: %s", e)
        return True


def _parse_deep_link(args):
    if not args:
        return None, None
    arg = args[0]
    if arg.startswith("listing_"):
        return "listing", arg[8:]
    if arg.startswith("shop_"):
        return "shop", arg[5:]
    return "referral", arg


async def _get_stats():
    try:
        async with async_session() as session:
            users = (await session.execute(select(func.count(User.id)))).scalar() or 0
            listings = (await session.execute(select(func.count(Listing.id)).where(Listing.status == ListingStatusEnum.ACTIVE))).scalar() or 0
            shops = (await session.execute(select(func.count(Shop.id)).where(Shop.is_active == True))).scalar() or 0
        return users, listings, shops
    except Exception:
        return 0, 0, 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await _is_subscribed(context.bot, update.effective_user.id):
            channel_name = settings.CHANNEL_ID.lstrip("@")
            await update.message.reply_text(
                f"👋 <b>OnBozor</b> ga xush kelibsiz!\n\n"
                f"Botdan foydalanish uchun avval\n📢 <b>{channel_name}</b> kanaliga obuna bo'ling:",
                parse_mode="HTML", reply_markup=subscribe_keyboard(),
            )
            return ConversationHandler.END

        link_type, link_id = _parse_deep_link(context.args)

        async with async_session() as session:
            user, is_new = await get_or_create_user(
                session,
                telegram_id=update.effective_user.id,
                full_name=update.effective_user.full_name,
                username=update.effective_user.username,
            )
            if is_new and link_type == "referral" and link_id:
                await process_referral(session, link_id, user)
            if is_new:
                from app.services.gamification import award_points
                await award_points(session, user.id, "register")

            if is_new or not user.viloyat:
                context.user_data["pending_deep_link"] = (link_type, link_id)
                await update.message.reply_text(
                    "👋 OnBozor ga xush kelibsiz!\n📍 Avval viloyatingizni tanlang:",
                    reply_markup=regions_keyboard(),
                )
                return RegistrationState.REGION

        if link_type in ("listing", "shop") and link_id:
            await update.message.reply_text("Quyidagi tugmani bosib ko'ring:", reply_markup=deep_link_keyboard(link_type, link_id))
        else:
            users, listings, shops = await _get_stats()
            await update.message.reply_text(
                f"👋 Salom, <b>{update.effective_user.first_name}</b>!\n\n"
                f"🛍 <b>OnBozor</b> — O'zbekistonning eng yirik\nTelegram marketplace platformasi\n\n"
                f"📊 <b>Statistika:</b>\n"
                f"• 👥 {users} ta foydalanuvchi\n"
                f"• 📢 {listings} ta faol e'lon\n"
                f"• 🏪 {shops} ta do'kon",
                parse_mode="HTML", reply_markup=webapp_keyboard(),
            )
        return ConversationHandler.END
    except Exception as e:
        logger.error("start error: %s", e, exc_info=True)
        await update.message.reply_text("👋 OnBozor ga xush kelibsiz!", reply_markup=webapp_keyboard())
        return ConversationHandler.END


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await _is_subscribed(context.bot, update.effective_user.id):
        await query.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return
    await query.edit_message_text("✅ Obuna tasdiqlandi!")
    try:
        async with async_session() as session:
            user, is_new = await get_or_create_user(session, telegram_id=update.effective_user.id, full_name=update.effective_user.full_name, username=update.effective_user.username)
            if is_new or not user.viloyat:
                await query.message.reply_text("📍 Viloyatingizni tanlang:", reply_markup=regions_keyboard())
                return RegistrationState.REGION
        await query.message.reply_text("🛍 <b>OnBozor</b> tayyor!", parse_mode="HTML", reply_markup=webapp_keyboard())
    except Exception as e:
        logger.error("check_sub error: %s", e)
        await query.message.reply_text("👋 Xush kelibsiz!", reply_markup=webapp_keyboard())


async def select_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    region = query.data.split(":")[1]
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if user:
                user.viloyat = region
                await session.commit()
    except Exception as e:
        logger.error("region error: %s", e)
    await query.edit_message_text(f"✅ Viloyat: {region}")
    pending = context.user_data.pop("pending_deep_link", (None, None))
    if pending[0] in ("listing", "shop") and pending[1]:
        await query.message.reply_text("Ko'ring:", reply_markup=deep_link_keyboard(pending[0], pending[1]))
    else:
        await query.message.reply_text("🛍 <b>OnBozor</b> tayyor!", parse_mode="HTML", reply_markup=webapp_keyboard())
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>OnBozor qo'llanmasi</b>\n\n"
        "🛍 <b>OnBozor</b> — O'zbekiston uchun Telegram marketplace\n\n"
        "📌 <b>Buyruqlar:</b>\n"
        "/start — Botni boshlash\n"
        "/help — Yordam\n"
        "/profile — Mening profilim\n"
        "/listings — Mening e'lonlarim\n"
        "/shop — Mening do'konim\n"
        "/referral — Referral tizimi\n"
        "/leaderboard — Top sotuvchilar\n"
        "/mybadges — Mening medallarim\n\n"
        "📌 <b>Imkoniyatlar:</b>\n"
        "• 📢 E'lon berish (5 ta bo'lim)\n"
        "• 🏪 Do'kon ochish (oylik obuna)\n"
        "• 🔍 Qidiruv + Filterlar\n"
        "• ❤️ Sevimlilar\n"
        "• 💬 Xabarlar\n"
        "• 👥 Referral — 5% bonus\n"
        "• 🏆 Reyting tizimi\n\n"
        "💬 Yordam: @onbozor_support",
        parse_mode="HTML",
    )


def get_start_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            RegistrationState.REGION: [
                CallbackQueryHandler(select_region, pattern=r"^region:"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CallbackQueryHandler(check_subscription, pattern=r"^check_sub$"),
        ],
    )
