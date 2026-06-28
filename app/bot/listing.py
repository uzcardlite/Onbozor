"""E'lon berish (listing creation FSM) + listing view."""
import asyncio
import re
import uuid as uuidlib

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.listing import Listing
from app.models.enums import ListingStatusEnum
from app.services.user_service import get_user
from app.services.cloudinary import upload_image_bytes
from app.services.favourite_service import toggle_favourite_listing
from app.bot import keyboards as kb
from app.bot.common import (
    SECTIONS, PAYMENTS, CONDITIONS, WEB_APP, logger,
    section_label, payment_label, condition_label, fmt_price, parse_price,
    normalize_username, listing_full, expiry, is_subscribed, safe_edit, is_admin,
)
from app.bot.states import L

USERNAME_OK = re.compile(r"^@[a-zA-Z0-9_]{3,}$")


def _data(context):
    return context.user_data.setdefault("listing", {})


async def _gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if await is_subscribed(context.bot, update.effective_user.id):
        return True
    msg = update.message or update.callback_query.message
    await msg.reply_text(
        "📢 Avval kanalga obuna bo'ling 👇", reply_markup=kb.subscribe_kb()
    )
    return False


# ───────────────────────── Entry ─────────────────────────
async def start_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _gate(update, context):
        return ConversationHandler.END
    context.user_data["listing"] = {}
    text = "📋 Bo'limni tanlang:"
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit(update.callback_query, text, reply_markup=kb.sections_kb())
    else:
        await update.message.reply_text(text, reply_markup=kb.sections_kb())
    return L.SECTION


# ───────────────────────── Steps ─────────────────────────
async def pick_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    _data(context)["section_key"] = key
    await safe_edit(query, f"{section_label(SECTIONS[key]['enum'])}\n\n📂 Kategoriyani tanlang:",
                    reply_markup=kb.subcats_kb(key))
    return L.CATEGORY


async def pick_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _data(context)["subcategory"] = query.data.split(":", 1)[1]
    await safe_edit(query, "💰 To'lov turini tanlang:", reply_markup=kb.payments_kb())
    return L.PAYMENT


async def pick_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _data(context)["payment_key"] = query.data.split(":", 1)[1]
    await safe_edit(query, "📦 Holati:", reply_markup=kb.conditions_kb())
    return L.CONDITION


async def pick_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _data(context)["condition_key"] = query.data.split(":", 1)[1]
    await safe_edit(query, "💰 Narxni kiriting (so'mda):", reply_markup=kb.back_only_kb("condition"))
    return L.PRICE


async def enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = parse_price(update.message.text)
    if price is None:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting (masalan: 1500000):")
        return L.PRICE
    _data(context)["price"] = price
    await update.message.reply_text("📍 Viloyatni tanlang:", reply_markup=kb.listing_region_kb())
    return L.VILOYAT


async def pick_viloyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _data(context)["viloyat"] = query.data.split(":", 1)[1]
    await safe_edit(query, "📞 Telegram username kiriting:\n(masalan: @username)",
                    reply_markup=kb.back_only_kb("price"))
    return L.USERNAME


async def enter_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = normalize_username(update.message.text)
    if not USERNAME_OK.match(username):
        await update.message.reply_text(
            "❌ Username noto'g'ri. Kamida 3 ta harf/raqam, masalan: @username"
        )
        return L.USERNAME
    _data(context)["username"] = username
    await update.message.reply_text("📝 E'lon tavsifini yozing (kamida 10 ta belgi):")
    return L.DESC


async def enter_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("❌ Tavsif juda qisqa. Kamida 10 ta belgi yozing:")
        return L.DESC
    _data(context)["description"] = text[:2000]
    await update.message.reply_text(
        "📷 Rasm yuboring (ixtiyoriy)\nO'tkazib yuborish uchun tugmani bosing:",
        reply_markup=kb.skip_photo_kb(),
    )
    return L.IMAGE


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Rasm yuklanmoqda...")
    try:
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        buf = await tg_file.download_as_bytearray()
        url = await asyncio.to_thread(upload_image_bytes, bytes(buf), "image/jpeg")
        _data(context)["image_url"] = url
    except Exception as e:
        logger.error("photo upload error: %s", e, exc_info=True)
        _data(context)["image_url"] = None
        await update.message.reply_text("⚠️ Rasm yuklanmadi, rasm­siz davom etamiz.")
    return await _show_confirm(update, context)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    _data(context)["image_url"] = None
    return await _show_confirm(update, context)


def _preview_text(d: dict) -> str:
    rasm = "✅ bor" if d.get("image_url") else "— yo'q"
    return (
        "✅ E'loningiz ma'lumotlari:\n\n"
        f"Bo'lim: {section_label(SECTIONS[d['section_key']]['enum'])}\n"
        f"Kategoriya: {d.get('subcategory', '—')}\n"
        f"To'lov: {payment_label(d['payment_key'])}\n"
        f"Holat: {condition_label(d['condition_key'])}\n"
        f"Narx: {fmt_price(d['price'])} so'm\n"
        f"Viloyat: {d['viloyat']}\n"
        f"Kontakt: {d['username']}\n"
        f"Tavsif: {d['description']}\n"
        f"Rasm: {rasm}"
    )


async def _show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = _data(context)
    msg = update.message or update.callback_query.message
    await msg.reply_text(_preview_text(d), reply_markup=kb.listing_confirm_kb(), parse_mode="HTML")
    return L.CONFIRM


# ───────────────────────── Back navigation ─────────────────────────
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target = query.data.split(":", 1)[1]
    d = _data(context)
    if target == "section":
        await safe_edit(query, "📋 Bo'limni tanlang:", reply_markup=kb.sections_kb())
        return L.SECTION
    if target == "category":
        await safe_edit(query, "📂 Kategoriyani tanlang:", reply_markup=kb.subcats_kb(d["section_key"]))
        return L.CATEGORY
    if target == "payment":
        await safe_edit(query, "💰 To'lov turini tanlang:", reply_markup=kb.payments_kb())
        return L.PAYMENT
    if target == "condition":
        await safe_edit(query, "📦 Holati:", reply_markup=kb.conditions_kb())
        return L.CONDITION
    if target == "price":
        await safe_edit(query, "💰 Narxni kiriting (so'mda):", reply_markup=kb.back_only_kb("condition"))
        return L.PRICE
    if target == "desc":
        await safe_edit(query, "📝 E'lon tavsifini yozing (kamida 10 ta belgi):")
        return L.DESC
    return L.CONFIRM


# ───────────────────────── Confirm / cancel ─────────────────────────
async def confirm_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("listing")
    if not d:
        await safe_edit(query, "❌ Ma'lumot topilmadi. /elon_berish dan qayta boshlang.")
        return ConversationHandler.END
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await safe_edit(query, "❌ Avval /start bosing.")
                return ConversationHandler.END
            section = SECTIONS[d["section_key"]]
            listing = Listing(
                user_id=user.id,
                section=section["enum"],
                category=section["name"],
                subcategory=d.get("subcategory"),
                payment_type=PAYMENTS[d["payment_key"]][1],
                condition=CONDITIONS[d["condition_key"]][1],
                price=d["price"],
                viloyat=d["viloyat"],
                seller_username=d["username"],
                description=d["description"],
                image_urls=[d["image_url"]] if d.get("image_url") else [],
                status=ListingStatusEnum.PENDING,
                expires_at=expiry(30),
            )
            s.add(listing)
            await s.commit()
            await s.refresh(listing)
            try:
                from app.services.gamification import award_points
                await award_points(s, user.id, "new_listing")
                await s.commit()
            except Exception as e:
                logger.warning("listing points error: %s", e)
            listing_id = listing.id
    except Exception as e:
        logger.error("confirm_listing error: %s", e, exc_info=True)
        await safe_edit(query, "❌ Xatolik yuz berdi. /elon_berish dan qayta boshlang.")
        return ConversationHandler.END

    context.user_data.pop("listing", None)
    await safe_edit(query,
        "✅ E'loningiz muvaffaqiyatli yuborildi!\nAdmin tekshiruvidan so'ng faollashadi.",
        reply_markup=kb.home_kb())
    await _notify_admins(context, listing_id, d)
    return ConversationHandler.END


async def _notify_admins(context, listing_id, d):
    text = (
        f"🆕 <b>Yangi e'lon</b> #{str(listing_id)[:8]}\n\n"
        f"Bo'lim: {section_label(SECTIONS[d['section_key']]['enum'])}\n"
        f"Kategoriya: {d.get('subcategory', '—')}\n"
        f"Narx: {fmt_price(d['price'])} so'm\n"
        f"Viloyat: {d['viloyat']}\n"
        f"Kontakt: {d['username']}\n\n"
        f"📝 {d['description'][:300]}"
    )
    for admin_id in settings.admin_ids_list:
        try:
            await context.bot.send_message(
                admin_id, text, parse_mode="HTML",
                reply_markup=kb.admin_moderation_kb(listing_id),
            )
        except Exception as e:
            logger.warning("admin notify failed (%s): %s", admin_id, e)


async def edit_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await safe_edit(update.callback_query, "📋 Bo'limni qaytadan tanlang:", reply_markup=kb.sections_kb())
    context.user_data["listing"] = {}
    return L.SECTION


async def cancel_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("listing", None)
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit(update.callback_query, "❌ E'lon bekor qilindi.", reply_markup=kb.home_kb())
    else:
        await update.message.reply_text("❌ E'lon bekor qilindi.", reply_markup=kb.home_kb())
    return ConversationHandler.END


# ───────────────────────── Listing view (shared) ─────────────────────────
async def open_listing_view(update: Update, context: ContextTypes.DEFAULT_TYPE, listing_id):
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    try:
        lid = uuidlib.UUID(str(listing_id))
    except (ValueError, AttributeError):
        if msg:
            await msg.reply_text("❌ E'lon topilmadi.")
        return
    try:
        from app.models.user import User as UserModel
        from app.models.favourite import Favourite
        async with async_session() as s:
            listing = await s.get(Listing, lid)
            if not listing or listing.status == ListingStatusEnum.DELETED:
                if msg:
                    await msg.reply_text("❌ E'lon topilmadi.")
                return
            listing.views = (listing.views or 0) + 1

            viewer = await get_user(s, update.effective_user.id)
            seller_obj = await s.get(UserModel, listing.user_id) if listing.user_id else None
            seller_tg = seller_obj.tg_id if seller_obj else None
            viewer_is_seller = bool(viewer and listing.user_id == viewer.id)

            is_fav = False
            if viewer:
                is_fav = (await s.execute(
                    select(Favourite).where(
                        Favourite.user_id == viewer.id, Favourite.listing_id == listing.id
                    )
                )).scalar_one_or_none() is not None

            await s.commit()
            text = listing_full(listing)
            image = listing.image_urls[0] if listing.image_urls else None
            kb_markup = kb.listing_view_kb(listing.id, seller_tg, viewer_is_seller, is_fav)
    except Exception as e:
        logger.error("open_listing_view error: %s", e, exc_info=True)
        if msg:
            await msg.reply_text("❌ Xatolik yuz berdi.")
        return

    if msg:
        if image and not str(image).startswith("data:"):
            try:
                await msg.reply_photo(image, caption=text, parse_mode="HTML", reply_markup=kb_markup)
                return
            except Exception:
                pass
        await msg.reply_text(text, parse_mode="HTML", reply_markup=kb_markup)


async def view_listing_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    listing_id = query.data.split(":", 1)[1]
    await open_listing_view(update, context, listing_id)


async def toggle_fav_listing_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    listing_id = query.data.split(":", 2)[2]
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await query.answer("Avval /start bosing", show_alert=True)
                return
            added = await toggle_favourite_listing(s, user.id, uuidlib.UUID(listing_id))
        await query.answer("❤️ Sevimlilarga qo'shildi!" if added else "💔 O'chirildi", show_alert=False)
    except Exception as e:
        logger.error("toggle fav listing error: %s", e)
        await query.answer("❌ Xatolik", show_alert=True)
