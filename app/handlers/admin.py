import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
from sqlalchemy import select, func
from app.database import async_session
from app.config import settings
from app.services.listing_service import (
    approve_listing, reject_listing, get_pending_listings, count_listings,
)
from app.services.shop_service import approve_shop, reject_shop, count_shops
from app.services.user_service import get_user
from app.keyboards.main import admin_menu_keyboard, main_menu_keyboard, admin_listing_keyboard
from app.states import AdminRejectState, BroadcastState
from app.models.enums import ListingStatusEnum
from app.models.user import User

logger = logging.getLogger(__name__)

ADMIN_ID = 37453466


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list or user_id == ADMIN_ID


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return

    try:
        async with async_session() as session:
            total_users = (await session.execute(select(func.count(User.id)))).scalar()
            total_listings = await count_listings(session)
            pending_listings = await count_listings(session, ListingStatusEnum.PENDING)
            active_listings = await count_listings(session, ListingStatusEnum.ACTIVE)
            total_shops = await count_shops(session)
            active_shops = await count_shops(session, active_only=True)

        await update.message.reply_text(
            "📊 <b>Admin statistika</b>\n\n"
            f"👥 Foydalanuvchilar: <b>{total_users}</b>\n"
            f"📢 Jami e'lonlar: <b>{total_listings}</b>\n"
            f"⏳ Kutayotgan: <b>{pending_listings}</b>\n"
            f"✅ Faol e'lonlar: <b>{active_listings}</b>\n"
            f"🏪 Jami do'konlar: <b>{total_shops}</b>\n"
            f"🟢 Faol do'konlar: <b>{active_shops}</b>",
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard(),
        )
    except Exception as e:
        logger.error("admin_command error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await admin_command(update, context)


async def admin_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        async with async_session() as session:
            listings = await get_pending_listings(session)

        if not listings:
            await update.message.reply_text("✅ Kutayotgan e'lonlar yo'q.")
            return

        for listing in listings[:10]:
            text = (
                f"📢 <b>E'lon #{str(listing.id)[:8]}</b>\n\n"
                f"📁 {listing.category}\n"
                f"💵 {listing.price:,} so'm\n"
                f"📍 {listing.viloyat}\n"
                f"📱 {listing.seller_username}\n"
                f"📝 {listing.description[:200]}"
            )
            await update.message.reply_text(
                text, parse_mode="HTML",
                reply_markup=admin_listing_keyboard(listing.id),
            )
    except Exception as e:
        logger.error("admin_pending error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def approve_listing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    listing_id = query.data.split(":")[1]
    try:
        async with async_session() as session:
            listing = await approve_listing(session, listing_id)

        if listing:
            await query.edit_message_text(f"✅ E'lon tasdiqlandi!")
    except Exception as e:
        logger.error("approve error: %s", e)
        await query.edit_message_text("❌ Xatolik.")


async def start_reject_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    listing_id = query.data.split(":")[1]
    context.user_data["reject_listing_id"] = listing_id
    await query.edit_message_text("❌ Rad etish sababini yozing:")
    return AdminRejectState.REASON


async def reject_listing_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    listing_id = context.user_data.pop("reject_listing_id", None)
    if not listing_id:
        return ConversationHandler.END

    reason = update.message.text
    try:
        async with async_session() as session:
            await reject_listing(session, listing_id, reason)

        await update.message.reply_text(f"❌ E'lon rad etildi.\nSabab: {reason}")
    except Exception as e:
        logger.error("reject error: %s", e)
        await update.message.reply_text("❌ Xatolik.")
    return ConversationHandler.END


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("📨 Broadcast xabarni yozing:")
    return BroadcastState.MESSAGE


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_text"] = update.message.text
    await update.message.reply_text(
        f"📨 Xabar:\n\n{update.message.text}\n\n"
        "Yuborishni tasdiqlaysizmi? (Ha/Yo'q)"
    )
    return BroadcastState.CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() not in ("ha", "yes"):
        await update.message.reply_text("❌ Broadcast bekor qilindi.")
        return ConversationHandler.END

    text = context.user_data.pop("broadcast_text")
    try:
        async with async_session() as session:
            result = await session.execute(select(User.tg_id).where(User.is_blocked == False))
            user_ids = result.scalars().all()

        sent = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(uid, text)
                sent += 1
            except Exception:
                pass

        await update.message.reply_text(f"✅ Xabar {sent}/{len(user_ids)} foydalanuvchiga yuborildi.")
    except Exception as e:
        logger.error("broadcast error: %s", e, exc_info=True)
        await update.message.reply_text("❌ Xatolik yuz berdi.")
    return ConversationHandler.END


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.handlers.start import webapp_keyboard
    await update.message.reply_text(
        "Menyuni tanlang:",
        reply_markup=webapp_keyboard(),
    )


def get_admin_handlers():
    reject_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_reject_listing, pattern=r"^reject:")],
        states={
            AdminRejectState.REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reject_listing_reason),
            ],
        },
        fallbacks=[],
    )

    broadcast_conv = ConversationHandler(
        entry_points=[
            CommandHandler("broadcast", start_broadcast),
            MessageHandler(filters.Regex(r"^📨 Broadcast$"), start_broadcast),
        ],
        states={
            BroadcastState.MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message),
            ],
            BroadcastState.CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirm),
            ],
        },
        fallbacks=[],
    )

    return [
        CommandHandler("admin", admin_command),
        CommandHandler("help", _help_from_admin),
        MessageHandler(filters.Regex(r"^📊 Statistika$"), admin_stats),
        MessageHandler(filters.Regex(r"^📢 E'lonlar$"), admin_pending_listings),
        MessageHandler(filters.Regex(r"^🔙 Asosiy menyu$"), back_to_main),
        CallbackQueryHandler(approve_listing_handler, pattern=r"^approve:"),
        reject_conv,
        broadcast_conv,
    ]


async def _help_from_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.handlers.start import help_command
    await help_command(update, context)
