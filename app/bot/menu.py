"""Start, mandatory channel subscription, registration and main menu."""
import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import func, select

from app.database import async_session
from app.models.user import User
from app.models.listing import Listing
from app.models.shop import Shop
from app.models.enums import ListingStatusEnum
from app.services.user_service import get_or_create_user, get_user, process_referral
from app.bot import keyboards as kb
from app.bot.common import is_subscribed, safe_edit, reply
from app.bot.states import Reg

logger = logging.getLogger("onbozor.bot")


async def _stats() -> tuple[int, int, int]:
    try:
        async with async_session() as s:
            users = (await s.execute(select(func.count(User.id)))).scalar() or 0
            listings = (await s.execute(
                select(func.count(Listing.id)).where(Listing.status == ListingStatusEnum.ACTIVE)
            )).scalar() or 0
            shops = (await s.execute(
                select(func.count(Shop.id)).where(Shop.is_active == True)  # noqa: E712
            )).scalar() or 0
        return users, listings, shops
    except Exception as e:
        logger.warning("stats error: %s", e)
        return 0, 0, 0


def _parse_deep_link(args):
    if not args:
        return None, None
    arg = args[0]
    if arg.startswith("listing_"):
        return "listing", arg[len("listing_"):]
    if arg.startswith("shop_"):
        return "shop", arg[len("shop_"):]
    return "referral", arg


async def _menu_text(name: str) -> str:
    users, listings, shops = await _stats()
    return (
        f"👋 Salom, <b>{name}</b>!\n"
        f"🛍 <b>OnBozor</b> ga xush kelibsiz!\n\n"
        f"O'zbekistonning eng yirik\nTelegram marketplace platformasi\n\n"
        f"📊 {users} ta foydalanuvchi\n"
        f"📢 {listings} ta faol e'lon\n"
        f"🏪 {shops} ta do'kon"
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    name = update.effective_user.first_name or "do'st"
    text = await _menu_text(name)
    if edit and update.callback_query:
        await safe_edit(update.callback_query, text, reply_markup=kb.main_menu_kb())
    else:
        await reply(update, text, reply_markup=kb.main_menu_kb())


# ───────────────────────── /start ─────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_tg = update.effective_user
        if not await is_subscribed(context.bot, user_tg.id):
            await update.message.reply_text(
                f"👋 Salom {user_tg.first_name}!\n\n"
                "⚠️ Botdan foydalanish uchun\nkanalga obuna bo'ling!",
                reply_markup=kb.subscribe_kb(),
            )
            return ConversationHandler.END

        link_type, link_id = _parse_deep_link(context.args)
        async with async_session() as s:
            user, is_new = await get_or_create_user(
                s, telegram_id=user_tg.id, full_name=user_tg.full_name, username=user_tg.username
            )
            if is_new and link_type == "referral" and link_id:
                await process_referral(s, link_id, user)
            if is_new:
                try:
                    from app.services.gamification import award_points
                    await award_points(s, user.id, "register")
                    await s.commit()
                except Exception as e:
                    logger.warning("register points error: %s", e)
            needs_region = not user.viloyat

        if needs_region:
            context.user_data["deep_link"] = (link_type, link_id)
            await update.message.reply_text(
                "📍 Boshlash uchun viloyatingizni tanlang:",
                reply_markup=kb.regions_kb("reg_region"),
            )
            return Reg.REGION

        if link_type == "listing" and link_id:
            from app.bot.listing import open_listing_view
            await open_listing_view(update, context, link_id)
        elif link_type == "shop" and link_id:
            from app.bot.shops import open_shop_view
            await open_shop_view(update, context, link_id)
        else:
            await show_main_menu(update, context)
        return ConversationHandler.END
    except Exception as e:
        logger.error("start error: %s", e, exc_info=True)
        await update.message.reply_text("👋 OnBozor ga xush kelibsiz!", reply_markup=kb.main_menu_kb())
        return ConversationHandler.END


async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        if not await is_subscribed(context.bot, update.effective_user.id):
            await query.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
            return ConversationHandler.END
        await query.answer("✅ Obuna tasdiqlandi!")
        user_tg = update.effective_user
        async with async_session() as s:
            user, _ = await get_or_create_user(
                s, telegram_id=user_tg.id, full_name=user_tg.full_name, username=user_tg.username
            )
            needs_region = not user.viloyat
        if needs_region:
            await safe_edit(query, "📍 Viloyatingizni tanlang:", reply_markup=kb.regions_kb("reg_region"))
            return Reg.REGION
        await safe_edit(query, await _menu_text(user_tg.first_name or "do'st"), reply_markup=kb.main_menu_kb())
        return ConversationHandler.END
    except Exception as e:
        logger.error("check_sub error: %s", e, exc_info=True)
        try:
            await query.message.reply_text("🛍 OnBozor tayyor!", reply_markup=kb.main_menu_kb())
        except Exception:
            pass
        return ConversationHandler.END


async def set_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    region = query.data.split(":", 1)[1]
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if user:
                user.viloyat = region
                await s.commit()
    except Exception as e:
        logger.error("set_region error: %s", e)
    await safe_edit(query, f"✅ Viloyat tanlandi: <b>{region}</b>")
    await show_main_menu(update, context)
    return ConversationHandler.END


# ───────────────────────── menu router ─────────────────────────
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles menu:* callbacks that are NOT conversation entry points."""
    query = update.callback_query
    action = query.data.split(":", 1)[1]
    await query.answer()

    if action == "home":
        await safe_edit(query, await _menu_text(update.effective_user.first_name or "do'st"),
                        reply_markup=kb.main_menu_kb())
    elif action == "shops":
        from app.bot.shops import shops_entry
        await shops_entry(update, context)
    elif action == "profile":
        from app.bot.profile import profile_entry
        await profile_entry(update, context)
    elif action == "referral":
        from app.bot.referral import referral_entry
        await referral_entry(update, context)
    elif action == "favs":
        from app.bot.favourites import favourites_entry
        await favourites_entry(update, context)
    elif action == "messages":
        from app.bot.messages import messages_entry
        await messages_entry(update, context)
    elif action == "rating":
        from app.bot.rating import rating_info
        await rating_info(update, context)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>OnBozor qo'llanmasi</b>\n\n"
        "🛍 O'zbekiston uchun Telegram marketplace\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start — Botni boshlash\n"
        "/elon_berish — E'lon berish\n"
        "/qidiruv — Qidiruv\n"
        "/dokonlar — Do'konlar\n"
        "/profil — Profilim\n"
        "/referral — Referral\n"
        "/sevimlilar — Sevimlilar\n"
        "/xabarlar — Xabarlar\n"
        "/dokon_ochish — Do'kon ochish\n"
        "/help — Yordam\n\n"
        "💬 Yordam: @onbozor_support",
        parse_mode="HTML",
    )


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


async def end_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback used inside conversations to bail out to the main menu."""
    for key in ("listing", "shop", "search_q", "rate_listing", "rate_stars", "conv_id"):
        context.user_data.pop(key, None)
    if update.callback_query:
        await update.callback_query.answer()
        await show_main_menu(update, context, edit=True)
    else:
        await show_main_menu(update, context)
    return ConversationHandler.END
