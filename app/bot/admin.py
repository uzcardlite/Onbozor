"""Admin commands — stats, moderation, broadcast."""
import uuid as uuidlib

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select, func

from app.config import settings
from app.database import async_session
from app.models.user import User
from app.models.listing import Listing
from app.models.enums import ListingStatusEnum, PaymentStatusEnum
from app.services.listing_service import (
    approve_listing, reject_listing, get_pending_listings, count_listings,
)
from app.services.shop_service import count_shops
from app.bot import keyboards as kb
from app.bot.common import (
    logger, is_admin, section_label, fmt_price, safe_edit,
)
from app.bot.states import Adm


def _guard(update: Update) -> bool:
    return is_admin(update.effective_user.id)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    try:
        from app.models.payment import Payment
        async with async_session() as s:
            users = (await s.execute(select(func.count(User.id)))).scalar() or 0
            active = await count_listings(s, ListingStatusEnum.ACTIVE)
            pending = await count_listings(s, ListingStatusEnum.PENDING)
            shops = await count_shops(s, active_only=True)
            revenue = (await s.execute(
                select(func.coalesce(func.sum(Payment.amount), 0))
                .where(Payment.status == PaymentStatusEnum.PAID)
            )).scalar() or 0
        await update.message.reply_text(
            "📊 <b>OnBozor statistikasi</b>\n\n"
            f"👥 Foydalanuvchilar: <b>{users}</b>\n"
            f"✅ Faol e'lonlar: <b>{active}</b>\n"
            f"⏳ Kutayotgan: <b>{pending}</b>\n"
            f"🏪 Faol do'konlar: <b>{shops}</b>\n"
            f"💰 Daromad: <b>{fmt_price(revenue)} so'm</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("stats_cmd error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    try:
        async with async_session() as s:
            listings = await get_pending_listings(s)
    except Exception as e:
        logger.error("pending_cmd error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")
        return
    if not listings:
        await update.message.reply_text("✅ Kutayotgan e'lonlar yo'q.")
        return
    await update.message.reply_text(f"⏳ Kutayotgan e'lonlar: {len(listings)}")
    for l in listings[:15]:
        await update.message.reply_text(
            f"📢 <b>E'lon</b> #{str(l.id)[:8]}\n\n"
            f"{section_label(l.section)} › {l.subcategory or '—'}\n"
            f"💰 {fmt_price(l.price)} so'm\n"
            f"📍 {l.viloyat}\n"
            f"📞 {l.seller_username}\n\n"
            f"📝 {l.description[:300]}",
            parse_mode="HTML",
            reply_markup=kb.admin_moderation_kb(l.id),
        )


async def _notify_owner_approved(context, listing):
    try:
        async with async_session() as s:
            owner = await s.get(User, listing.user_id) if listing.user_id else None
        if owner:
            from app.services.notification import notify_listing_approved
            await notify_listing_approved(owner.tg_id, str(listing.id), section_label(listing.section))
    except Exception as e:
        logger.warning("notify approved failed: %s", e)


async def approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _guard(update):
        await query.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    await query.answer()
    listing_id = query.data.split(":", 1)[1]
    try:
        async with async_session() as s:
            listing = await approve_listing(s, uuidlib.UUID(listing_id))
        if listing:
            await safe_edit(query, f"✅ E'lon #{listing_id[:8]} tasdiqlandi!")
            await _notify_owner_approved(context, listing)
        else:
            await safe_edit(query, "❌ E'lon topilmadi.")
    except Exception as e:
        logger.error("approve_cb error: %s", e, exc_info=True)
        await safe_edit(query, "❌ Xatolik yuz berdi.")


async def reject_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _guard(update):
        await query.answer("❌ Ruxsat yo'q", show_alert=True)
        return ConversationHandler.END
    await query.answer()
    context.user_data["reject_id"] = query.data.split(":", 1)[1]
    await safe_edit(query, "❌ Rad etish sababini yozing:")
    return Adm.REJECT_REASON


async def reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    listing_id = context.user_data.pop("reject_id", None)
    if not listing_id:
        return ConversationHandler.END
    reason = update.message.text.strip()
    try:
        async with async_session() as s:
            listing = await reject_listing(s, uuidlib.UUID(listing_id), reason)
            owner = await s.get(User, listing.user_id) if listing and listing.user_id else None
        await update.message.reply_text(f"❌ E'lon rad etildi.\nSabab: {reason}")
        if owner:
            from app.services.notification import notify_listing_rejected
            await notify_listing_rejected(owner.tg_id, section_label(listing.section), reason)
    except Exception as e:
        logger.error("reject_reason error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")
    return ConversationHandler.END


# ───────────────────────── Text command forms (/approve_xxxx) ─────────────────────────
async def _find_by_prefix(s, prefix: str) -> Listing | None:
    listings = (await s.execute(
        select(Listing).where(Listing.status == ListingStatusEnum.PENDING)
    )).scalars().all()
    for l in listings:
        if str(l.id).startswith(prefix.lower()):
            return l
    return None


async def approve_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    prefix = update.message.text.split("_", 1)[1].strip()
    try:
        async with async_session() as s:
            l = await _find_by_prefix(s, prefix)
            if not l:
                await update.message.reply_text("❌ E'lon topilmadi.")
                return
            listing = await approve_listing(s, l.id)
        await update.message.reply_text(f"✅ E'lon #{str(listing.id)[:8]} tasdiqlandi!")
        await _notify_owner_approved(context, listing)
    except Exception as e:
        logger.error("approve_text error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def reject_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    prefix = update.message.text.split("_", 1)[1].strip()
    try:
        async with async_session() as s:
            l = await _find_by_prefix(s, prefix)
            if not l:
                await update.message.reply_text("❌ E'lon topilmadi.")
                return
            await reject_listing(s, l.id, "Admin tomonidan rad etildi")
            owner = await s.get(User, l.user_id) if l.user_id else None
        await update.message.reply_text(f"❌ E'lon #{str(l.id)[:8]} rad etildi.")
        if owner:
            from app.services.notification import notify_listing_rejected
            await notify_listing_rejected(owner.tg_id, section_label(l.section), "Admin tomonidan rad etildi")
    except Exception as e:
        logger.error("reject_text error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


# ───────────────────────── Broadcast ─────────────────────────
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return ConversationHandler.END
    await update.message.reply_text("📨 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:")
    return Adm.BROADCAST_MSG


async def broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast"] = update.message.text
    await update.message.reply_text(
        f"📨 Xabar:\n\n{update.message.text}\n\nYuborishni tasdiqlaysizmi? (Ha / Yo'q)"
    )
    return Adm.BROADCAST_CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() not in ("ha", "yes", "ok", "ha'"):
        context.user_data.pop("broadcast", None)
        await update.message.reply_text("❌ Broadcast bekor qilindi.")
        return ConversationHandler.END
    text = context.user_data.pop("broadcast", "")
    try:
        async with async_session() as s:
            ids = (await s.execute(
                select(User.tg_id).where(User.is_blocked == False)  # noqa: E712
            )).scalars().all()
        sent = 0
        for uid in ids:
            try:
                await context.bot.send_message(uid, text)
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Xabar {sent}/{len(ids)} foydalanuvchiga yuborildi.")
    except Exception as e:
        logger.error("broadcast error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")
    return ConversationHandler.END


async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("broadcast", None)
    context.user_data.pop("reject_id", None)
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END
