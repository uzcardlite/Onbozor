"""Builds the Application and registers every handler in the right order.

Order matters: ConversationHandlers are added before the generic callback
routers so their entry points win, and text-input states use ~COMMAND so
slash commands always escape an active conversation.
"""
import logging

from telegram import Update
from telegram.ext import (
    Application, ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.config import settings
from app.bot import menu, listing, search, shops, profile, favourites, referral
from app.bot import messages as msgs
from app.bot import rating, shop_create, admin
from app.bot.states import Reg, L, S, Chat, Rate, Shop as St, Adm

logger = logging.getLogger("onbozor.bot")

TEXT = filters.TEXT & ~filters.COMMAND


def _start_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", menu.start),
            CallbackQueryHandler(menu.check_sub, pattern=r"^check_sub$"),
        ],
        states={
            Reg.REGION: [CallbackQueryHandler(menu.set_region, pattern=r"^reg_region:")],
        },
        fallbacks=[CommandHandler("start", menu.start)],
        name="start_conv", allow_reentry=True,
    )


def _listing_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(listing.start_listing, pattern=r"^menu:listing$"),
            CommandHandler("elon_berish", listing.start_listing),
        ],
        states={
            L.SECTION: [
                CallbackQueryHandler(listing.pick_section, pattern=r"^l_sec:"),
                CallbackQueryHandler(listing.cancel_listing, pattern=r"^l_cancel$"),
            ],
            L.CATEGORY: [
                CallbackQueryHandler(listing.pick_subcategory, pattern=r"^l_sub:"),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.PAYMENT: [
                CallbackQueryHandler(listing.pick_payment, pattern=r"^l_pay:"),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.CONDITION: [
                CallbackQueryHandler(listing.pick_condition, pattern=r"^l_cond:"),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.PRICE: [
                MessageHandler(TEXT, listing.enter_price),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.VILOYAT: [
                CallbackQueryHandler(listing.pick_viloyat, pattern=r"^l_reg:"),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.USERNAME: [
                MessageHandler(TEXT, listing.enter_username),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.DESC: [
                MessageHandler(TEXT, listing.enter_desc),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.IMAGE: [
                MessageHandler(filters.PHOTO, listing.receive_photo),
                CallbackQueryHandler(listing.skip_photo, pattern=r"^l_skip$"),
                CallbackQueryHandler(listing.go_back, pattern=r"^l_back:"),
            ],
            L.CONFIRM: [
                CallbackQueryHandler(listing.confirm_listing, pattern=r"^l_confirm$"),
                CallbackQueryHandler(listing.edit_listing, pattern=r"^l_edit$"),
                CallbackQueryHandler(listing.cancel_listing, pattern=r"^l_cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(listing.cancel_listing, pattern=r"^l_cancel$"),
            CallbackQueryHandler(menu.end_to_menu, pattern=r"^menu:home$"),
            CommandHandler("start", menu.start),
        ],
        name="listing_conv", allow_reentry=True,
    )


def _search_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(search.start_search, pattern=r"^menu:search$"),
            CommandHandler("qidiruv", search.start_search),
        ],
        states={S.QUERY: [MessageHandler(TEXT, search.run_query)]},
        fallbacks=[
            CallbackQueryHandler(menu.end_to_menu, pattern=r"^menu:home$"),
            CommandHandler("start", menu.start),
        ],
        name="search_conv", allow_reentry=True,
    )


def _chat_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(msgs.chat_start, pattern=r"^chat_start:"),
            CallbackQueryHandler(msgs.conv_open, pattern=r"^conv_open:"),
        ],
        states={
            Chat.TYPING: [
                MessageHandler(TEXT, msgs.chat_send),
                CallbackQueryHandler(msgs.chat_exit, pattern=r"^menu:(messages|home)$"),
            ],
        },
        fallbacks=[CommandHandler("start", menu.start)],
        name="chat_conv", allow_reentry=True,
    )


def _rating_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(rating.rate_start, pattern=r"^rate:")],
        states={
            Rate.STARS: [CallbackQueryHandler(rating.rate_stars, pattern=r"^star:")],
            Rate.COMMENT: [
                MessageHandler(TEXT, rating.rate_comment),
                CallbackQueryHandler(rating.rate_skip, pattern=r"^rate_skip$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(menu.end_to_menu, pattern=r"^menu:home$"),
            CommandHandler("start", menu.start),
        ],
        name="rating_conv", allow_reentry=True,
    )


def _shop_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("dokon_ochish", shop_create.start_shop),
            CallbackQueryHandler(shop_create.start_shop, pattern=r"^shop_open$"),
        ],
        states={
            St.NAME: [MessageHandler(TEXT, shop_create.shop_name)],
            St.DESC: [MessageHandler(TEXT, shop_create.shop_desc)],
            St.CATEGORY: [
                CallbackQueryHandler(shop_create.shop_category, pattern=r"^sc_cat:"),
                CallbackQueryHandler(shop_create.shop_cancel, pattern=r"^sc_cancel$"),
            ],
            St.VILOYAT: [CallbackQueryHandler(shop_create.shop_region, pattern=r"^sc_reg:")],
            St.CONFIRM: [
                CallbackQueryHandler(shop_create.shop_pay, pattern=r"^sc_pay:"),
                CallbackQueryHandler(shop_create.shop_cancel, pattern=r"^sc_cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(shop_create.shop_cancel, pattern=r"^sc_cancel$"),
            CallbackQueryHandler(menu.end_to_menu, pattern=r"^menu:home$"),
            CommandHandler("start", menu.start),
        ],
        name="shop_conv", allow_reentry=True,
    )


def _admin_reject_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.reject_start_cb, pattern=r"^adm_no:")],
        states={Adm.REJECT_REASON: [MessageHandler(TEXT, admin.reject_reason)]},
        fallbacks=[CommandHandler("cancel", admin.cancel_admin)],
        name="admin_reject_conv", allow_reentry=True,
    )


def _broadcast_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("broadcast", admin.broadcast_start)],
        states={
            Adm.BROADCAST_MSG: [MessageHandler(TEXT, admin.broadcast_msg)],
            Adm.BROADCAST_CONFIRM: [MessageHandler(TEXT, admin.broadcast_confirm)],
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_admin)],
        name="broadcast_conv", allow_reentry=True,
    )


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled error: %s", context.error, exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Xatolik yuz berdi.\n/start dan qayta boshlang"
            )
    except Exception:
        pass


async def _stray_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.bot.keyboards import main_menu_kb
    await update.message.reply_text("👇 Quyidagi menyudan tanlang:", reply_markup=main_menu_kb())


def register_handlers(app: Application) -> None:
    # 1) Conversation flows (entry points must win over generic routers)
    app.add_handler(_start_conv())
    app.add_handler(_listing_conv())
    app.add_handler(_search_conv())
    app.add_handler(_chat_conv())
    app.add_handler(_rating_conv())
    app.add_handler(_shop_conv())
    app.add_handler(_admin_reject_conv())
    app.add_handler(_broadcast_conv())

    # 2) Standalone commands
    app.add_handler(CommandHandler("help", menu.help_cmd))
    app.add_handler(CommandHandler("profil", profile.profile_entry))
    app.add_handler(CommandHandler("dokonlar", shops.shops_entry))
    app.add_handler(CommandHandler("sevimlilar", favourites.favourites_entry))
    app.add_handler(CommandHandler("referral", referral.referral_entry))
    app.add_handler(CommandHandler("xabarlar", msgs.messages_entry))
    app.add_handler(CommandHandler("stats", admin.stats_cmd))
    app.add_handler(CommandHandler("pending", admin.pending_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/approve_"), admin.approve_text_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^/reject_"), admin.reject_text_cmd))

    # 3) Generic callback routers
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(listing.view_listing_cb, pattern=r"^l_view:"))
    app.add_handler(CallbackQueryHandler(listing.toggle_fav_listing_cb, pattern=r"^fav:listing:"))
    app.add_handler(CallbackQueryHandler(shops.toggle_fav_shop_cb, pattern=r"^fav:shop:"))
    app.add_handler(CallbackQueryHandler(shops.shop_category_cb, pattern=r"^sh_cat:"))
    app.add_handler(CallbackQueryHandler(shops.shop_view_cb, pattern=r"^sh_view:"))
    app.add_handler(CallbackQueryHandler(search.page_cb, pattern=r"^s_page:"))
    app.add_handler(CallbackQueryHandler(profile.my_listings_cb, pattern=r"^my_listings$"))
    app.add_handler(CallbackQueryHandler(profile.my_shop_cb, pattern=r"^my_shop$"))
    app.add_handler(CallbackQueryHandler(admin.approve_cb, pattern=r"^adm_ok:"))
    app.add_handler(CallbackQueryHandler(menu.noop, pattern=r"^noop$"))

    # 4) Catch-all stray text
    app.add_handler(MessageHandler(TEXT, _stray_text))

    app.add_error_handler(_on_error)
    logger.info("All bot handlers registered")
