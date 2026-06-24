from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user, get_referral_count


async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            return

        ref_count = await get_referral_count(session, user.id)

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user.referral_code}"

    await update.message.reply_text(
        f"👥 Referral tizim\n\n"
        f"🔗 Sizning havolangiz:\n{ref_link}\n\n"
        f"👥 Taklif qilganlar: {ref_count}\n"
        f"💰 Referral balans: {user.referral_balance:,} so'm\n\n"
        f"ℹ️ Har bir taklif qilgan do'stingiz orqali amalga oshirilgan "
        f"xaridlardan 5% bonus olasiz!"
    )


def get_referral_handlers():
    return [
        MessageHandler(filters.Regex(r"^👥 Referral$"), show_referral),
    ]
