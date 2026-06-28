"""Xabarlar — in-bot conversations between buyers and sellers."""
import uuid as uuidlib

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select, or_, func

from app.database import async_session
from app.models.listing import Listing
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.services.user_service import get_user
from app.bot import keyboards as kb
from app.bot.common import logger, section_label, safe_edit, reply
from app.bot.states import Chat


def _other_party(conv: Conversation, me_id):
    return conv.seller_id if conv.buyer_id == me_id else conv.buyer_id


async def messages_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await reply(update, "❌ Avval /start bosing.")
                return
            convs = (await s.execute(
                select(Conversation)
                .where(or_(Conversation.buyer_id == user.id, Conversation.seller_id == user.id))
                .order_by(func.coalesce(Conversation.last_message_at, Conversation.created_at).desc())
                .limit(15)
            )).scalars().all()

            rows = []
            for c in convs:
                other_id = _other_party(c, user.id)
                other = await s.get(User, other_id)
                listing = await s.get(Listing, c.listing_id)
                title = section_label(listing.section) if listing else "e'lon"
                who = f"@{other.username}" if other and other.username else (other.full_name if other else "—")
                snippet = (c.last_message or "...")[:30]
                rows.append([B(f"💬 {who} · {title}: {snippet}", callback_data=f"conv_open:{c.id}")])
    except Exception as e:
        logger.error("messages_entry error: %s", e, exc_info=True)
        await reply(update, "❌ Xatolik yuz berdi.")
        return

    if not rows:
        text = "💬 Sizda hali xabarlar yo'q.\nE'lon ko'rib, sotuvchiga yozing!"
        markup = kb.home_kb()
    else:
        rows.append([B("🏠 Bosh menyu", callback_data="menu:home")])
        text = "💬 <b>Sizning xabarlaringiz:</b>"
        markup = InlineKeyboardMarkup(rows)

    if update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyer taps '💬 Sotuvchiga yozish' on a listing."""
    query = update.callback_query
    await query.answer()
    listing_id = query.data.split(":", 1)[1]
    try:
        async with async_session() as s:
            buyer = await get_user(s, update.effective_user.id)
            listing = await s.get(Listing, uuidlib.UUID(listing_id))
            if not buyer or not listing or not listing.user_id:
                await query.message.reply_text("❌ Suhbatni boshlab bo'lmadi.")
                return ConversationHandler.END
            if listing.user_id == buyer.id:
                await query.message.reply_text("ℹ️ Bu sizning e'loningiz.")
                return ConversationHandler.END
            conv = (await s.execute(
                select(Conversation).where(
                    Conversation.listing_id == listing.id, Conversation.buyer_id == buyer.id
                )
            )).scalar_one_or_none()
            if not conv:
                conv = Conversation(listing_id=listing.id, buyer_id=buyer.id, seller_id=listing.user_id)
                s.add(conv)
                await s.commit()
                await s.refresh(conv)
            conv_id = conv.id
            title = section_label(listing.section)
    except Exception as e:
        logger.error("chat_start error: %s", e, exc_info=True)
        await query.message.reply_text("❌ Xatolik yuz berdi.")
        return ConversationHandler.END

    context.user_data["conv_id"] = str(conv_id)
    await query.message.reply_text(
        f"💬 <b>{title}</b> bo'yicha suhbat.\nXabaringizni yozing:",
        parse_mode="HTML", reply_markup=kb.chat_kb(),
    )
    return Chat.TYPING


async def conv_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conv_id = query.data.split(":", 1)[1]
    try:
        async with async_session() as s:
            me = await get_user(s, update.effective_user.id)
            conv = await s.get(Conversation, uuidlib.UUID(conv_id))
            if not conv or not me or me.id not in (conv.buyer_id, conv.seller_id):
                await query.message.reply_text("❌ Suhbat topilmadi.")
                return ConversationHandler.END
            msgs = (await s.execute(
                select(Message).where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc()).limit(10)
            )).scalars().all()
            msgs = list(reversed(msgs))
            lines = []
            for m in msgs:
                prefix = "🟢 Siz" if m.sender_id == me.id else "⬜️ U"
                lines.append(f"{prefix}: {m.text}")
    except Exception as e:
        logger.error("conv_open error: %s", e, exc_info=True)
        await query.message.reply_text("❌ Xatolik yuz berdi.")
        return ConversationHandler.END

    context.user_data["conv_id"] = conv_id
    history = "\n".join(lines) if lines else "Hali xabar yo'q."
    await safe_edit(query, f"💬 <b>Suhbat:</b>\n\n{history}\n\n✍️ Javob yozing:",
                    reply_markup=kb.chat_kb())
    return Chat.TYPING


async def chat_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conv_id = context.user_data.get("conv_id")
    if not conv_id:
        await update.message.reply_text("❌ Suhbat yopilgan. /xabarlar dan oching.")
        return ConversationHandler.END
    text = update.message.text.strip()
    try:
        async with async_session() as s:
            me = await get_user(s, update.effective_user.id)
            conv = await s.get(Conversation, uuidlib.UUID(conv_id))
            if not conv or not me:
                await update.message.reply_text("❌ Suhbat topilmadi.")
                return ConversationHandler.END
            from datetime import datetime, timezone
            s.add(Message(conversation_id=conv.id, sender_id=me.id, text=text))
            conv.last_message = text
            conv.last_message_at = datetime.now(timezone.utc)
            other_id = _other_party(conv, me.id)
            other = await s.get(User, other_id)
            await s.commit()
            other_tg = other.tg_id if other else None
            me_name = f"@{me.username}" if me.username else me.full_name
    except Exception as e:
        logger.error("chat_send error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xabar yuborilmadi.")
        return Chat.TYPING

    await update.message.reply_text("✅ Yuborildi", reply_markup=kb.chat_kb())
    if other_tg:
        try:
            await context.bot.send_message(
                other_tg,
                f"💬 <b>{me_name}</b> sizga yozdi:\n\n{text}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[B("✍️ Javob berish", callback_data=f"conv_open:{conv.id}")]]),
            )
        except Exception as e:
            logger.warning("chat relay failed: %s", e)
    return Chat.TYPING


async def chat_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("conv_id", None)
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    if action == "messages":
        await messages_entry(update, context)
    else:
        from app.bot.menu import show_main_menu
        await show_main_menu(update, context, edit=True)
    return ConversationHandler.END
