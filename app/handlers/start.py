from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    CallbackQueryHandler,
)

WEB_APP_URL = "https://onbozor.vercel.app"

def webapp_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 OnBozor ga o'tish", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
from app.database import async_session
from app.services.user_service import get_or_create_user, get_user, process_referral
from app.keyboards.main import main_menu_keyboard, regions_keyboard
from app.states import RegistrationState
import logging

logger = logging.getLogger(__name__)


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
                    "📍 Viloyatingizni tanlang:",
                    reply_markup=regions_keyboard(),
                )
                return RegistrationState.REGION

        await update.message.reply_text(
            f"👋 Salom, {update.effective_user.first_name}!\n\n"
            "OnBozor — O'zbekiston bozori.\n"
            "Quyidagi tugmani bosib bozorga kiring:",
            reply_markup=webapp_keyboard(),
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error("start_command error: %s", e, exc_info=True)
        await update.message.reply_text(
            "👋 OnBozor ga xush kelibsiz!\n\n"
            "Quyidagi tugmani bosib bozorga kiring:",
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

    await query.edit_message_text(
        f"✅ Viloyat saqlandi: {region}\n\n"
        "OnBozor ga xush kelibsiz! Quyidagi menyudan foydalaning:",
    )
    await query.message.reply_text(
        "Quyidagi tugmani bosib bozorga kiring:",
        reply_markup=webapp_keyboard(),
    )
    return ConversationHandler.END


def get_start_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            RegistrationState.REGION: [
                CallbackQueryHandler(select_region, pattern=r"^region:"),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
