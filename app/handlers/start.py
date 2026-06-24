from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from app.database import async_session
from app.services.user_service import get_or_create_user, get_user, process_referral
from app.keyboards.main import main_menu_keyboard, regions_keyboard
from app.states import RegistrationState


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        if is_new or not user.region:
            await update.message.reply_text(
                "👋 OnBozor ga xush kelibsiz!\n\n"
                "📍 Viloyatingizni tanlang:",
                reply_markup=regions_keyboard(),
            )
            return RegistrationState.REGION

    await update.message.reply_text(
        f"👋 Salom, {update.effective_user.first_name}!\n\n"
        "OnBozor — O'zbekiston bozori. Quyidagi menyudan foydalaning:",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def select_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    region = query.data.split(":")[1]

    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if user:
            user.region = region
            await session.commit()

    await query.edit_message_text(
        f"✅ Viloyat saqlandi: {region}\n\n"
        "OnBozor ga xush kelibsiz! Quyidagi menyudan foydalaning:",
    )
    await query.message.reply_text("Menyuni tanlang:", reply_markup=main_menu_keyboard())
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
