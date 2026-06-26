import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"
WEB_APP = "https://onbozor.vercel.app"


async def _send(tg_id: int, text: str, buttons: list[list[dict]] | None = None):
    payload = {"chat_id": tg_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{BOT_API}/sendMessage", json=payload)
            if resp.status_code != 200:
                logger.warning("TG send failed [%s]: %s", tg_id, resp.text[:200])
    except Exception as e:
        logger.error("TG send error [%s]: %s", tg_id, e)


async def _notify_admins(text: str, buttons: list[list[dict]] | None = None):
    for admin_id in settings.admin_ids_list:
        await _send(admin_id, text, buttons)


# ────────────── User notifications ──────────────

async def notify_listing_approved(tg_id: int, listing_id: str, category: str):
    await _send(tg_id,
        f"✅ <b>E'loningiz tasdiqlandi!</b>\n\n"
        f"📢 {category}\n\n"
        f"Endi barcha foydalanuvchilar ko'ra oladi.",
        [[{"text": "👁 Ko'rish", "web_app": {"url": f"{WEB_APP}/listing/{listing_id}"}}]],
    )


async def notify_listing_rejected(tg_id: int, category: str, reason: str):
    await _send(tg_id,
        f"❌ <b>E'loningiz rad etildi</b>\n\n"
        f"📢 {category}\n"
        f"📝 Sabab: {reason}\n\n"
        f"Tahrirlash va qayta yuborish mumkin.",
        [[{"text": "📢 Qayta yuborish", "web_app": {"url": f"{WEB_APP}/add-listing"}}]],
    )


async def notify_shop_approved(tg_id: int, shop_name: str, shop_id: str):
    await _send(tg_id,
        f"🏪 <b>Do'koningiz faollashdi!</b>\n\n"
        f"🏪 {shop_name}\n"
        f"📅 Obuna: 30 kun\n\n"
        f"Mahsulotlaringizni qo'shishni boshlang!",
        [[{"text": "🏪 Do'konimga o'tish", "web_app": {"url": f"{WEB_APP}/shop/{shop_id}"}}]],
    )


async def notify_shop_expiring(tg_id: int, shop_name: str, days_left: int):
    await _send(tg_id,
        f"⚠️ <b>Do'kon obunangiz {days_left} kunda tugaydi!</b>\n\n"
        f"🏪 {shop_name}\n\n"
        f"Obunani yangilang — do'koningiz nofaol bo'lib qolmasin.",
        [[{"text": "💳 Obunani yangilash", "web_app": {"url": f"{WEB_APP}/open-shop"}}]],
    )


async def notify_shop_expired(tg_id: int, shop_name: str):
    await _send(tg_id,
        f"🔴 <b>Do'kon obunangiz tugadi</b>\n\n"
        f"🏪 {shop_name}\n\n"
        f"Do'koningiz nofaol. Qayta faollashtiring:",
        [[{"text": "💳 Qayta faollashtirish", "web_app": {"url": f"{WEB_APP}/open-shop"}}]],
    )


async def notify_listing_expiring(tg_id: int, listing_id: str, category: str):
    await _send(tg_id,
        f"⏰ <b>E'loningiz ertaga tugaydi</b>\n\n"
        f"📢 {category}\n\n"
        f"Yangilash yoki qayta yuborish mumkin.",
        [[{"text": "📢 Ko'rish", "web_app": {"url": f"{WEB_APP}/listing/{listing_id}"}}]],
    )


async def notify_payment_success(tg_id: int, shop_name: str, amount: int):
    await _send(tg_id,
        f"✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
        f"🏪 Do'kon: {shop_name}\n"
        f"💰 Summa: {amount:,} so'm\n"
        f"📅 Obuna: 30 kun\n\n"
        f"Do'koningiz faollashtirildi!",
    )


async def notify_payment_failed(tg_id: int, amount: int):
    await _send(tg_id,
        f"❌ <b>To'lov amalga oshmadi</b>\n\n"
        f"💰 Summa: {amount:,} so'm\n\n"
        f"Qaytadan urinib ko'ring.",
        [[{"text": "💳 Qayta to'lash", "web_app": {"url": f"{WEB_APP}/open-shop"}}]],
    )


async def notify_new_message(tg_id: int, from_username: str):
    await _send(tg_id,
        f"💬 <b>Yangi xabar!</b>\n\n"
        f"👤 @{from_username} sizga yozdi.",
    )


# ────────────── Admin notifications ──────────────

async def admin_new_listing(listing_id: str, category: str, price: int, viloyat: str):
    await _notify_admins(
        f"📢 <b>Yangi e'lon tasdiqlash kutmoqda!</b>\n\n"
        f"📁 {category}\n"
        f"💵 {price:,} so'm\n"
        f"📍 {viloyat}",
        [[{"text": "✅ Ko'rish va tasdiqlash", "web_app": {"url": f"{WEB_APP}/admin"}}]],
    )


async def admin_new_shop(shop_name: str, viloyat: str):
    await _notify_admins(
        f"🏪 <b>Yangi do'kon arizasi keldi!</b>\n\n"
        f"🏪 {shop_name}\n"
        f"📍 {viloyat}",
        [[{"text": "✅ Ko'rish", "web_app": {"url": f"{WEB_APP}/admin"}}]],
    )


async def admin_new_payment(amount: int, shop_name: str, method: str):
    await _notify_admins(
        f"💰 <b>Yangi to'lov keldi!</b>\n\n"
        f"💵 {amount:,} so'm ({method})\n"
        f"🏪 Do'kon: {shop_name}",
    )
