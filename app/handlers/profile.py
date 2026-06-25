import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from app.database import async_session
from app.services.user_service import get_user, get_referral_count

logger = logging.getLogger(__name__)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ Profil topilmadi. /start buyrug'ini yuboring.")
                return

            ref_count = await get_referral_count(session, user.id)

        await update.message.reply_text(
            f"👤 <b>Profil</b>\n\n"
            f"📛 Ism: {user.full_name}\n"
            f"📱 Username: @{user.username or '—'}\n"
            f"📍 Viloyat: {user.viloyat or 'tanlanmagan'}\n"
            f"👥 Referrallar: {ref_count}\n"
            f"💰 Referral balans: {user.ref_earnings:,} so'm\n"
            f"🆔 ID: {user.tg_id}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("profile_command error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")


async def mylisting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from app.services.listing_service import get_user_listings

        async with async_session() as session:
            user = await get_user(session, update.effective_user.id)
            if not user:
                await update.message.reply_text("❌ /start buyrug'ini yuboring.")
                return

            listings = await get_user_listings(session, user.id)

        if not listings:
            await update.message.reply_text(
                "📋 Sizda hali e'lonlar yo'q.\n\n"
                "📢 E'lon berish uchun web app dan foydalaning."
            )
            return

        text = "📋 <b>Mening e'lonlarim:</b>\n\n"
        for i, l in enumerate(listings[:20], 1):
            status_emoji = {"pending": "⏳", "active": "✅", "rejected": "❌", "deleted": "🗑"}.get(l.status.value if hasattr(l.status, 'value') else l.status, "❓")
            text += f"{i}. {status_emoji} {l.category} — {l.price:,} so'm ({l.viloyat})\n"

        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error("mylisting_command error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def get_profile_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("mylisting", mylisting_command),
        MessageHandler(filters.Regex(r"^👤 Profil$"), profile_command),
        MessageHandler(filters.Regex(r"^📋 Mening e'lonlarim$"), mylisting_command),
    ]
