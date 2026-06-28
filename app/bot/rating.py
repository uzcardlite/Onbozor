"""Reyting — rate a seller from a listing (1–5 stars + optional comment)."""
import uuid as uuidlib

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select

from app.database import async_session
from app.models.listing import Listing
from app.models.review import Review
from app.services.user_service import get_user
from app.bot import keyboards as kb
from app.bot.common import logger, safe_edit, reply
from app.bot.states import Rate


async def rating_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu entry — explains how rating works."""
    text = (
        "⭐ <b>Reyting</b>\n\n"
        "Sotuvchiga baho berish uchun:\n"
        "1. 🔍 Qidiruv yoki 🏪 Do'konlardan e'lonni oching\n"
        "2. «⭐ Reyting qoldirish» tugmasini bosing\n"
        "3. 1–5 yulduz va izoh qoldiring"
    )
    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=kb.home_kb())
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb.home_kb())


async def rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    listing_id = query.data.split(":", 1)[1]
    context.user_data["rate_listing"] = listing_id
    await query.message.reply_text("⭐ 1 dan 5 gacha baho bering:", reply_markup=kb.stars_kb(listing_id))
    return Rate.STARS


async def rate_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, listing_id, stars = query.data.split(":")
    context.user_data["rate_stars"] = int(stars)
    context.user_data["rate_listing"] = listing_id
    await safe_edit(query, f"{'⭐' * int(stars)}\n\n💬 Izoh qoldiring (ixtiyoriy):",
                    reply_markup=kb.rate_skip_kb())
    return Rate.COMMENT


async def rate_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text.strip()
    return await _save_review(update, context, comment)


async def rate_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return await _save_review(update, context, None)


async def _save_review(update, context, comment):
    listing_id = context.user_data.pop("rate_listing", None)
    stars = context.user_data.pop("rate_stars", None)
    msg = update.message or update.callback_query.message
    if not listing_id or not stars:
        await msg.reply_text("❌ Ma'lumot topilmadi.")
        return ConversationHandler.END
    try:
        async with async_session() as s:
            reviewer = await get_user(s, update.effective_user.id)
            listing = await s.get(Listing, uuidlib.UUID(listing_id))
            if not reviewer or not listing or not listing.user_id:
                await msg.reply_text("❌ E'lon topilmadi.")
                return ConversationHandler.END
            if listing.user_id == reviewer.id:
                await msg.reply_text("ℹ️ O'z e'loningizga baho bera olmaysiz.")
                return ConversationHandler.END
            existing = (await s.execute(
                select(Review).where(
                    Review.reviewer_id == reviewer.id, Review.listing_id == listing.id
                )
            )).scalar_one_or_none()
            if existing:
                existing.rating = stars
                existing.comment = comment
            else:
                s.add(Review(
                    reviewer_id=reviewer.id, seller_id=listing.user_id,
                    listing_id=listing.id, rating=stars, comment=comment,
                ))
            await s.commit()
            try:
                from app.services.gamification import award_points
                await award_points(s, listing.user_id, "review")
                await s.commit()
            except Exception as e:
                logger.warning("review points error: %s", e)
    except Exception as e:
        logger.error("save_review error: %s", e, exc_info=True)
        await msg.reply_text("❌ Baho saqlanmadi.")
        return ConversationHandler.END

    await msg.reply_text(f"✅ Bahoyingiz qabul qilindi: {'⭐' * stars}", reply_markup=kb.home_kb())
    return ConversationHandler.END
