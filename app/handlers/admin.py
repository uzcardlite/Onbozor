from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
from app.database import async_session
from app.config import settings
from app.services.listing_service import (
    approve_listing, reject_listing, get_pending_listings, count_listings,
)
from app.services.shop_service import approve_shop, reject_shop, count_shops
from app.services.user_service import get_user
from app.keyboards.main import admin_menu_keyboard, main_menu_keyboard, admin_listing_keyboard
from app.states import AdminRejectState, BroadcastState
from app.constants import ListingStatus, ShopStatus
from sqlalchemy import select, func
from app.models.user import User


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    await update.message.reply_text("🔧 Admin panel:", reply_markup=admin_menu_keyboard())


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar()
        total_listings = await count_listings(session)
        pending_listings = await count_listings(session, ListingStatus.PENDING)
        approved_listings = await count_listings(session, ListingStatus.APPROVED)
        total_shops = await count_shops(session)
        active_shops = await count_shops(session, ShopStatus.ACTIVE)

    await update.message.reply_text(
        "📊 Statistika\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"📢 Jami e'lonlar: {total_listings}\n"
        f"⏳ Kutayotgan e'lonlar: {pending_listings}\n"
        f"✅ Faol e'lonlar: {approved_listings}\n"
        f"🏪 Jami do'konlar: {total_shops}\n"
        f"✅ Faol do'konlar: {active_shops}\n"
    )


async def admin_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    async with async_session() as session:
        listings = await get_pending_listings(session)

    if not listings:
        await update.message.reply_text("✅ Kutayotgan e'lonlar yo'q.")
        return

    for listing in listings[:10]:
        text = (
            f"📢 E'lon #{listing.id}\n\n"
            f"📁 {listing.category} → {listing.subcategory}\n"
            f"💵 {listing.price:,} so'm\n"
            f"📍 {listing.region}\n"
            f"📱 {listing.contact_username}\n"
            f"📝 {listing.description}\n"
        )
        await update.message.reply_text(text, reply_markup=admin_listing_keyboard(listing.id))


async def approve_listing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    listing_id = int(query.data.split(":")[1])
    async with async_session() as session:
        listing = await approve_listing(session, listing_id)

    if listing:
        await query.edit_message_text(f"✅ E'lon #{listing_id} tasdiqlandi!")
        try:
            user_session = async_session()
            async with user_session as session:
                from app.models.listing import Listing as ListingModel
                result = await session.execute(select(ListingModel).where(ListingModel.id == listing_id))
                l = result.scalar_one_or_none()
                if l:
                    user = await get_user(session, 0)  # placeholder
            await context.bot.send_message(
                listing.user_id,
                f"✅ Sizning e'loningiz #{listing_id} tasdiqlandi!",
            )
        except Exception:
            pass


async def start_reject_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    listing_id = int(query.data.split(":")[1])
    context.user_data["reject_listing_id"] = listing_id
    await query.edit_message_text(f"❌ E'lon #{listing_id} rad etish sababini yozing:")
    return AdminRejectState.REASON


async def reject_listing_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    listing_id = context.user_data.pop("reject_listing_id", None)
    if not listing_id:
        return ConversationHandler.END

    reason = update.message.text
    async with async_session() as session:
        await reject_listing(session, listing_id, reason)

    await update.message.reply_text(f"❌ E'lon #{listing_id} rad etildi.\nSabab: {reason}")
    return ConversationHandler.END


async def approve_shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    shop_id = int(query.data.split(":")[1])
    async with async_session() as session:
        shop = await approve_shop(session, shop_id)

    if shop:
        await query.edit_message_text(f"✅ Do'kon #{shop_id} tasdiqlandi!")


async def reject_shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return

    shop_id = int(query.data.split(":")[1])
    async with async_session() as session:
        await reject_shop(session, shop_id)

    await query.edit_message_text(f"❌ Do'kon #{shop_id} rad etildi.")


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
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id).where(User.is_blocked == False))
        user_ids = result.scalars().all()

    sent = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(f"✅ Xabar {sent}/{len(user_ids)} foydalanuvchiga yuborildi.")
    return ConversationHandler.END


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Asosiy menyu:", reply_markup=main_menu_keyboard())


def get_admin_handlers():
    reject_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_reject_listing, pattern=r"^reject:\d+$")],
        states={
            AdminRejectState.REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reject_listing_reason),
            ],
        },
        fallbacks=[],
    )

    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📨 Broadcast$"), start_broadcast)],
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
        MessageHandler(filters.Regex(r"^📊 Statistika$"), admin_stats),
        MessageHandler(filters.Regex(r"^📢 E'lonlar$"), admin_pending_listings),
        MessageHandler(filters.Regex(r"^🔙 Asosiy menyu$"), back_to_main),
        CallbackQueryHandler(approve_listing_handler, pattern=r"^approve:\d+$"),
        CallbackQueryHandler(approve_shop_handler, pattern=r"^shop_approve:\d+$"),
        CallbackQueryHandler(reject_shop_handler, pattern=r"^shop_reject:\d+$"),
        reject_conv,
        broadcast_conv,
    ]
