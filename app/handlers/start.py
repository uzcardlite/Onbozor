import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler,
)
from app.database import async_session
from app.services.user_service import get_or_create_user, get_user, process_referral
from app.keyboards.main import main_menu_keyboard, regions_keyboard
from app.states import RegistrationState

logger = logging.getLogger(__name__)

WEB_APP_URL = "https://onbozor.vercel.app"


def webapp_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 OnBozor ga o'tish", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("📢 E'lon berish", web_app=WebAppInfo(url=f"{WEB_APP_URL}/add-listing")),
            InlineKeyboardButton("🏪 Do'konlar", web_app=WebAppInfo(url=f"{WEB_APP_URL}/shops")),
        ],
        [
            InlineKeyboardButton("🔍 Qidiruv", web_app=WebAppInfo(url=f"{WEB_APP_URL}/search")),
            InlineKeyboardButton("👤 Profil", web_app=WebAppInfo(url=f"{WEB_APP_URL}/profile")),
        ],
        [InlineKeyboardButton("🔗 Referral", web_app=WebAppInfo(url=f"{WEB_APP_URL}/referral"))],
    ])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        async with async_session() as session:
            user, is_new = await get_or_create_user(
                session,
                telegram_id=update.effective_user.id,
                full_name=update.effective_user.full_name,
                username=update.effective_user.username,
            )
            if is_new and args:
                await process_referral(session, args[0], user)

            if is_new or not user.viloyat:
                await update.message.reply_text(
                    "👋 OnBozor ga xush kelibsiz!\n\n"
                    "📍 Avval viloyatingizni tanlang:",
                    reply_markup=regions_keyboard(),
                )
                return RegistrationState.REGION

        await update.message.reply_text(
            f"👋 Salom, {update.effective_user.first_name}!\n\n"
            "🛒 <b>OnBozor</b> — O'zbekiston bozori.\n"
            "Quyidagi tugmalardan foydalaning:",
            parse_mode="HTML",
            reply_markup=webapp_keyboard(),
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error("start_command error: %s", e, exc_info=True)
        await update.message.reply_text(
            "👋 OnBozor ga xush kelibsiz!",
            reply_markup=webapp_keyboard(),
        )
        return ConversationHandler.END


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
        logger.error("select_region error: %s", e)

    await query.edit_message_text(f"✅ Viloyat saqlandi: {region}")
    await query.message.reply_text(
        "🛒 <b>OnBozor</b> — O'zbekiston bozori.\n"
        "Quyidagi tugmalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=webapp_keyboard(),
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>OnBozor qo'llanmasi</b>\n\n"
        "🛒 <b>OnBozor</b> — O'zbekiston uchun Telegram marketplace.\n\n"
        "📌 <b>Buyruqlar:</b>\n"
        "/start — Botni ishga tushirish\n"
        "/help — Qo'llanma\n"
        "/profile — Mening profilim\n"
        "/mylisting — Mening e'lonlarim\n"
        "/referral — Referral tizim\n\n"
        "📌 <b>Imkoniyatlar:</b>\n"
        "• 📢 E'lon berish (5 ta bo'lim)\n"
        "• 🏪 Do'kon ochish (oylik obuna)\n"
        "• 🔍 Qidiruv (narx, viloyat, bo'lim)\n"
        "• ❤️ Sevimlilar saqlash\n"
        "• 👥 Referral — do'stlarni taklif qiling, 5% bonus oling\n\n"
        "💬 Savollar uchun: @onbozor_support",
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
        ],
    )
