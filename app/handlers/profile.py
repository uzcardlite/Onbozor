import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user, get_referral_count
from app.keyboards.main import main_menu_keyboard

logger = logging.getLogger(__name__)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ Profil topilmadi. /start buyrug'ini yuboring.")
                return

            ref_count = await get_referral_count(session, user.id)

        await update.message.reply_text(
            f"👤 Profil\n\n"
            f"📛 Ism: {user.full_name}\n"
            f"📱 Username: @{user.username or 'yoq'}\n"
            f"📍 Viloyat: {user.viloyat or 'tanlanmagan'}\n"
            f"👥 Referrallar: {ref_count}\n"
            f"💰 Referral balans: {user.ref_earnings:,} so'm\n"
        )
    except Exception as e:
        logger.error("show_profile error: %s", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 E'lonlaringizni ko'rish uchun web app dan foydalaning.")


def get_profile_handlers():
    return [
        MessageHandler(filters.Regex(r"^👤 Profil$"), show_profile),
        MessageHandler(filters.Regex(r"^📋 Mening e'lonlarim$"), my_listings),
    ]
