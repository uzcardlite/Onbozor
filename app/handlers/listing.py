from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters,
)
from app.database import async_session
from app.services.user_service import get_user
from app.services.listing_service import create_listing
from app.keyboards.main import (
    categories_keyboard, subcategories_keyboard, payment_type_keyboard,
    condition_keyboard, regions_keyboard, confirm_keyboard, skip_keyboard,
)
from app.states import ListingState
from app.config import settings


async def start_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📢 E'lon berish\n\nBo'limni tanlang:",
        reply_markup=categories_keyboard(),
    )
    return ListingState.CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ E'lon bekor qilindi.")
        return ConversationHandler.END

    category = query.data.split(":")[1]
    context.user_data["listing"] = {"category": category}
    await query.edit_message_text(
        "Kategoriyani tanlang:",
        reply_markup=subcategories_keyboard(category),
    )
    return ListingState.SUBCATEGORY


async def select_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_cat":
        await query.edit_message_text("Bo'limni tanlang:", reply_markup=categories_keyboard())
        return ListingState.CATEGORY

    subcategory = query.data.split(":")[1]
    context.user_data["listing"]["subcategory"] = subcategory
    await query.edit_message_text(
        "💰 To'lov turini tanlang:",
        reply_markup=payment_type_keyboard(),
    )
    return ListingState.PAYMENT_TYPE


async def select_payment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["listing"]["payment_type"] = query.data.split(":")[1]
    await query.edit_message_text(
        "📦 Holatni tanlang:",
        reply_markup=condition_keyboard(),
    )
    return ListingState.CONDITION


async def select_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["listing"]["condition"] = query.data.split(":")[1]
    await query.edit_message_text("💵 Narxni kiriting (so'm):")
    return ListingState.PRICE


async def enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(" ", "").replace(",", "")
    if not text.isdigit():
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting:")
        return ListingState.PRICE

    context.user_data["listing"]["price"] = int(text)
    await update.message.reply_text(
        "📍 Viloyatni tanlang:",
        reply_markup=regions_keyboard(),
    )
    return ListingState.REGION


async def select_listing_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["listing"]["region"] = query.data.split(":")[1]
    await query.edit_message_text(
        "📱 Telegram username ni kiriting (masalan: @username):"
    )
    return ListingState.USERNAME


async def enter_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    if not username.startswith("@"):
        username = f"@{username}"
    context.user_data["listing"]["contact_username"] = username
    await update.message.reply_text("📝 E'lon tavsifini yozing:")
    return ListingState.DESCRIPTION


async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["listing"]["description"] = update.message.text
    await update.message.reply_text(
        "📷 Rasm yuboring yoki o'tkazib yuboring:",
        reply_markup=skip_keyboard(),
    )
    return ListingState.PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    context.user_data["listing"]["photo_url"] = file.file_path
    return await _show_preview(update, context)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["listing"]["photo_url"] = None
    return await _show_preview_from_query(query, context)


async def _show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["listing"]
    text = _format_listing_preview(data)
    await update.message.reply_text(text, reply_markup=confirm_keyboard())
    return ListingState.CONFIRM


async def _show_preview_from_query(query, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["listing"]
    text = _format_listing_preview(data)
    await query.edit_message_text(text, reply_markup=confirm_keyboard())
    return ListingState.CONFIRM


def _format_listing_preview(data: dict) -> str:
    return (
        "📋 E'lon ko'rinishi:\n\n"
        f"📁 Bo'lim: {data['category']}\n"
        f"📂 Kategoriya: {data['subcategory']}\n"
        f"💰 To'lov: {data['payment_type']}\n"
        f"📦 Holat: {data['condition']}\n"
        f"💵 Narx: {data['price']:,} so'm\n"
        f"📍 Viloyat: {data['region']}\n"
        f"📱 Kontakt: {data['contact_username']}\n"
        f"📝 Tavsif: {data['description']}\n"
        f"📷 Rasm: {'Bor' if data.get('photo_url') else 'Yo❜q'}\n\n"
        "Tasdiqlaysizmi?"
    )


async def confirm_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ E'lon bekor qilindi.")
        context.user_data.pop("listing", None)
        return ConversationHandler.END

    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            await query.edit_message_text("❌ Xatolik yuz berdi.")
            return ConversationHandler.END

        data = context.user_data.pop("listing")
        listing = await create_listing(
            session,
            user_id=user.id,
            category=data["category"],
            subcategory=data["subcategory"],
            payment_type=data["payment_type"],
            condition=data["condition"],
            price=data["price"],
            region=data["region"],
            contact_username=data["contact_username"],
            description=data["description"],
            photo_url=data.get("photo_url"),
        )

    await query.edit_message_text(
        f"✅ E'lon #{listing.id} yuborildi!\n"
        "Admin tasdiqlashini kuting."
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            from app.keyboards.main import admin_listing_keyboard
            await context.bot.send_message(
                admin_id,
                f"📢 Yangi e'lon #{listing.id}\n\n{_format_listing_preview(data)}",
                reply_markup=admin_listing_keyboard(listing.id),
            )
        except Exception:
            pass

    return ConversationHandler.END


async def cancel_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("listing", None)
    await update.message.reply_text("❌ E'lon bekor qilindi.")
    return ConversationHandler.END


def get_listing_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^📢 E'lon berish$"), start_listing),
        ],
        states={
            ListingState.CATEGORY: [
                CallbackQueryHandler(select_category, pattern=r"^(cat:|cancel)"),
            ],
            ListingState.SUBCATEGORY: [
                CallbackQueryHandler(select_subcategory, pattern=r"^(subcat:|back_to_cat)"),
            ],
            ListingState.PAYMENT_TYPE: [
                CallbackQueryHandler(select_payment_type, pattern=r"^pay:"),
            ],
            ListingState.CONDITION: [
                CallbackQueryHandler(select_condition, pattern=r"^cond:"),
            ],
            ListingState.PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_price),
            ],
            ListingState.REGION: [
                CallbackQueryHandler(select_listing_region, pattern=r"^region:"),
            ],
            ListingState.USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_username),
            ],
            ListingState.DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description),
            ],
            ListingState.PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                CallbackQueryHandler(skip_photo, pattern=r"^skip$"),
            ],
            ListingState.CONFIRM: [
                CallbackQueryHandler(confirm_listing, pattern=r"^(confirm_listing|cancel)$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r"^❌"), cancel_listing),
        ],
    )
