"""Referral — code, stats and share link."""
from urllib.parse import quote

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import ContextTypes

from app.database import async_session
from app.services.user_service import get_user, get_referral_count
from app.bot import keyboards as kb
from app.bot.common import logger, fmt_price, safe_edit, reply


async def referral_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await reply(update, "❌ Avval /start bosing.")
                return
            ref_count = await get_referral_count(s, user.id)
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start={user.ref_code}"
        share_text = quote(f"OnBozor — O'zbekiston bozori! Ro'yxatdan o'ting:\n{ref_link}")
        share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={share_text}"
        text = (
            "🔗 <b>Sizning referral kodingiz:</b>\n\n"
            f"Kod: <code>{user.ref_code}</code>\n"
            f"Havola: {ref_link}\n\n"
            f"👥 Taklif qilganlar: {ref_count}\n"
            f"💰 Daromad: {fmt_price(user.ref_earnings)} so'm\n\n"
            "Har taklif qilgan do'stdan bonus ball olasiz!"
        )
        markup = InlineKeyboardMarkup([
            [B("📤 Do'stga yuborish", url=share_url)],
            [B("🏠 Bosh menyu", callback_data="menu:home")],
        ])
    except Exception as e:
        logger.error("referral error: %s", e, exc_info=True)
        await reply(update, "❌ Xatolik yuz berdi.")
        return
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
