"""Qidiruv (in-bot search) with pagination."""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.database import async_session
from app.services.search_engine import search_listings
from app.bot import keyboards as kb
from app.bot.common import logger, listing_summary, safe_edit, is_subscribed
from app.bot.states import S

LIMIT = 5


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context.bot, update.effective_user.id):
        msg = update.message or update.callback_query.message
        await msg.reply_text("📢 Avval kanalga obuna bo'ling 👇", reply_markup=kb.subscribe_kb())
        return ConversationHandler.END
    text = "🔍 Qidiruv so'zini kiriting:"
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit(update.callback_query, text)
    else:
        await update.message.reply_text(text)
    return S.QUERY


async def run_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.message.text.strip()
    context.user_data["search_q"] = q
    await _render_results(update, context, q, 0, new_message=True)
    return ConversationHandler.END


async def page_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    offset = int(query.data.split(":", 1)[1])
    q = context.user_data.get("search_q", "")
    await _render_results(update, context, q, offset, new_message=False)


async def _render_results(update, context, q, offset, new_message):
    bot_username = context.bot.username
    try:
        async with async_session() as s:
            listings, total = await search_listings(s, q=q, limit=LIMIT, offset=offset)
    except Exception as e:
        logger.error("search error: %s", e, exc_info=True)
        msg = update.message or update.callback_query.message
        await msg.reply_text("❌ Qidiruvda xatolik. Qaytadan urinib ko'ring.")
        return

    if not listings:
        msg = update.message or update.callback_query.message
        await msg.reply_text(
            f"😔 «{q}» bo'yicha hech narsa topilmadi.", reply_markup=kb.home_kb()
        )
        return

    header = f"🔍 «{q}» — {total} ta natija topildi:"
    if new_message:
        await update.message.reply_text(header)
    else:
        await safe_edit(update.callback_query, header)
        # the edited message is just the header; cards are sent fresh below

    target = update.message or update.callback_query.message
    for l in listings:
        await target.reply_text(
            listing_summary(l), parse_mode="HTML",
            reply_markup=kb.listing_card_kb(l.id, bot_username),
        )

    pager = kb.pagination_kb("s_page", offset, total, LIMIT)
    if pager:
        from telegram import InlineKeyboardMarkup
        await target.reply_text("📄 Sahifalar:", reply_markup=InlineKeyboardMarkup(pager))
