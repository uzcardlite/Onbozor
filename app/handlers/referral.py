import logging
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user, get_referral_count

logger = logging.getLogger(__name__)


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            ref_count = await get_referral_count(session, user.id)

        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user.ref_code}"
        share_text = quote(f"OnBozor — O'zbekiston bozori! Ro'yxatdan o'ting:\n{ref_link}")
        share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={share_text}"

        await update.message.reply_text(
            f"👥 <b>Referral tizim</b>\n\n"
            f"🔗 Sizning kodingiz: <code>{user.ref_code}</code>\n"
            f"Havola:\n<code>{ref_link}</code>\n\n"
            f"👥 Taklif qilganlar: <b>{ref_count}</b>\n"
            f"💰 Daromad: <b>{user.ref_earnings:,} so'm</b>\n\n"
            f"ℹ️ Har bir do'stingiz orqali amalga oshirilgan "
            f"xaridlardan <b>5% bonus</b> olasiz!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Do'stga yuborish", url=share_url)],
            ]),
        )
    except Exception as e:
        logger.error("referral_command error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def get_referral_handlers():
    return [
        CommandHandler("referral", referral_command),
        MessageHandler(filters.Regex(r"^👥 Referral$"), referral_command),
    ]
