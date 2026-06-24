from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from app.database import async_session
from app.services.user_service import get_user, get_referral_count
from app.services.listing_service import get_user_listings
from app.keyboards.main import regions_keyboard


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Profil topilmadi. /start buyrug'ini yuboring.")
            return

        ref_count = await get_referral_count(session, user.id)
        listings = await get_user_listings(session, user.id)

    await update.message.reply_text(
        f"👤 Profil\n\n"
        f"📛 Ism: {user.full_name}\n"
        f"📱 Username: @{user.username or 'yo❜q'}\n"
        f"📍 Viloyat: {user.region or 'tanlanmagan'}\n"
        f"📢 E'lonlar: {len(listings)}\n"
        f"👥 Referrallar: {ref_count}\n"
        f"💰 Referral balans: {user.referral_balance:,} so'm\n"
    )


async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            return

        listings = await get_user_listings(session, user.id)

    if not listings:
        await update.message.reply_text("📋 Sizda hali e'lonlar yo'q.")
        return

    text = "📋 Mening e'lonlarim:\n\n"
    for i, listing in enumerate(listings[:20], 1):
        status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(listing.status, "❓")
        text += f"{i}. {status_emoji} {listing.subcategory} — {listing.price:,} so'm ({listing.region})\n"

    await update.message.reply_text(text)


def get_profile_handlers():
    return [
        MessageHandler(filters.Regex(r"^👤 Profil$"), show_profile),
        MessageHandler(filters.Regex(r"^📋 Mening e'lonlarim$"), my_listings),
    ]
