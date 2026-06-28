"""Do'kon ochish — shop creation FSM ending in a payment link."""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import ContextTypes, ConversationHandler

from app.config import settings
from app.database import async_session
from app.models.shop import Shop
from app.models.payment import Payment
from app.models.enums import PaymentMethodEnum
from app.services.user_service import get_user
from app.services.payment_service import generate_payme_url, generate_click_url
from app.bot import keyboards as kb
from app.bot.common import (
    logger, SECTIONS, section_label, fmt_price, safe_edit, is_subscribed,
)
from app.bot.states import Shop as St


def _d(context):
    return context.user_data.setdefault("shop", {})


async def start_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context.bot, update.effective_user.id):
        msg = update.message or update.callback_query.message
        await msg.reply_text("📢 Avval kanalga obuna bo'ling 👇", reply_markup=kb.subscribe_kb())
        return ConversationHandler.END
    context.user_data["shop"] = {}
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("🏪 Do'kon ochish\n\n1️⃣ Do'kon nomini kiriting:")
    return St.NAME


async def shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Nom juda qisqa. Qaytadan kiriting:")
        return St.NAME
    _d(context)["name"] = name[:255]
    await update.message.reply_text("2️⃣ Do'kon tavsifini yozing (kamida 10 ta belgi):")
    return St.DESC


async def shop_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if len(desc) < 10:
        await update.message.reply_text("❌ Tavsif juda qisqa. Kamida 10 ta belgi:")
        return St.DESC
    _d(context)["description"] = desc
    await update.message.reply_text("3️⃣ Kategoriyani tanlang:", reply_markup=kb.shop_cat_kb())
    return St.CATEGORY


async def shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _d(context)["category_key"] = query.data.split(":", 1)[1]
    await safe_edit(query, "4️⃣ Viloyatni tanlang:", reply_markup=kb.shop_region_kb())
    return St.VILOYAT


async def shop_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = _d(context)
    d["viloyat"] = query.data.split(":", 1)[1]
    text = (
        "✅ Do'kon ma'lumotlari:\n\n"
        f"🏪 Nom: {d['name']}\n"
        f"📁 Kategoriya: {section_label(SECTIONS[d['category_key']]['enum'])}\n"
        f"📍 Viloyat: {d['viloyat']}\n"
        f"📝 {d['description']}\n\n"
        f"💳 Oylik to'lov: {fmt_price(settings.SHOP_MONTHLY_PRICE)} so'm\n\n"
        "To'lov tizimini tanlang:"
    )
    await safe_edit(query, text, reply_markup=kb.shop_confirm_kb())
    return St.CONFIRM


async def shop_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.split(":", 1)[1]
    d = context.user_data.get("shop")
    if not d:
        await safe_edit(query, "❌ Ma'lumot topilmadi. /dokon_ochish dan qayta boshlang.")
        return ConversationHandler.END
    try:
        async with async_session() as s:
            user = await get_user(s, update.effective_user.id)
            if not user:
                await safe_edit(query, "❌ Avval /start bosing.")
                return ConversationHandler.END
            shop = Shop(
                owner_id=user.id,
                name=d["name"],
                description=d["description"],
                category=SECTIONS[d["category_key"]]["enum"],
                viloyat=d["viloyat"],
                monthly_fee=settings.SHOP_MONTHLY_PRICE,
                is_active=False,
            )
            s.add(shop)
            await s.commit()
            await s.refresh(shop)
            payment = Payment(
                user_id=user.id,
                shop_id=shop.id,
                amount=settings.SHOP_MONTHLY_PRICE,
                payment_method=PaymentMethodEnum.PAYME if method == "payme" else PaymentMethodEnum.CLICK,
            )
            s.add(payment)
            await s.commit()
            await s.refresh(payment)
            url = generate_payme_url(payment) if method == "payme" else generate_click_url(payment)
            shop_name = shop.name
            shop_id = shop.id
    except Exception as e:
        logger.error("shop_pay error: %s", e, exc_info=True)
        await safe_edit(query, "❌ Xatolik yuz berdi. /dokon_ochish dan qayta boshlang.")
        return ConversationHandler.END

    context.user_data.pop("shop", None)
    await safe_edit(query,
        f"🏪 <b>{shop_name}</b> yaratildi!\n\n"
        f"💳 To'lovni amalga oshiring — so'ng do'koningiz faollashadi:",
        reply_markup=InlineKeyboardMarkup([
            [B("💳 To'lovga o'tish", url=url)],
            [B("🏠 Bosh menyu", callback_data="menu:home")],
        ]),
    )
    # notify admins
    for admin_id in settings.admin_ids_list:
        try:
            await context.bot.send_message(
                admin_id, f"🏪 Yangi do'kon arizasi: <b>{shop_name}</b> ({d['viloyat']})",
                parse_mode="HTML",
            )
        except Exception:
            pass
    return ConversationHandler.END


async def shop_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("shop", None)
    if update.callback_query:
        await update.callback_query.answer()
        await safe_edit(update.callback_query, "❌ Do'kon ochish bekor qilindi.", reply_markup=kb.home_kb())
    else:
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=kb.home_kb())
    return ConversationHandler.END
