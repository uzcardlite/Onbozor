import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"


async def send_telegram_message(tg_id: int, text: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BOT_API}/sendMessage",
                json={"chat_id": tg_id, "text": text, "parse_mode": "HTML"},
            )
            if resp.status_code != 200:
                logger.warning("Telegram send failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.exception("Telegram send error: %s", e)


async def notify_payment_success(tg_id: int, shop_name: str, amount: int):
    text = (
        "✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
        f"🏪 Do'kon: {shop_name}\n"
        f"💰 Summa: {amount:,} so'm\n"
        f"📅 Obuna: 30 kun\n\n"
        "Do'koningiz faollashtirildi!"
    )
    await send_telegram_message(tg_id, text)


async def notify_payment_failed(tg_id: int, amount: int):
    text = (
        "❌ <b>To'lov amalga oshmadi</b>\n\n"
        f"💰 Summa: {amount:,} so'm\n\n"
        "Iltimos, qaytadan urinib ko'ring."
    )
    await send_telegram_message(tg_id, text)
