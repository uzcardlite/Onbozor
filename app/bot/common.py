"""Shared constants, lookups and helpers for the OnBozor bot."""
import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.config import settings
from app.models.enums import SectionEnum, PaymentTypeEnum, ConditionEnum

logger = logging.getLogger("onbozor.bot")

# Telegram only accepts HTTPS URLs in WebAppInfo buttons. FRONTEND_URL may be
# unset or a localhost http:// value on the server, which would make every
# inline menu raise BadRequest — so fall back to the production URL unless we
# have a real https:// origin.
_frontend = (settings.FRONTEND_URL or "").strip().rstrip("/")
WEB_APP = _frontend if _frontend.startswith("https://") else "https://onbozor.vercel.app"

# ───────────────────────── Catalog ─────────────────────────
# Keyed by the SectionEnum value so callback data maps straight to the DB enum.
SECTIONS: dict[str, dict] = {
    "uyjoy": {
        "emoji": "🏠", "name": "Uy-joy", "enum": SectionEnum.UYJOY,
        "subs": ["Sotish", "Ijara", "Dacha", "Garaj"],
    },
    "texnika": {
        "emoji": "📱", "name": "Texnika", "enum": SectionEnum.TEXNIKA,
        "subs": ["Telefon", "Noutbuk", "Maishiy texnika", "Boshqa"],
    },
    "avto": {
        "emoji": "🚗", "name": "Avtomobil", "enum": SectionEnum.AVTO,
        "subs": ["Yangi", "Ishlatilgan", "Ehtiyot qism"],
    },
    "moto": {
        "emoji": "🏍", "name": "Moto", "enum": SectionEnum.MOTO,
        "subs": ["Skuter", "Moto"],
    },
    "kiyim": {
        "emoji": "👕", "name": "Kiyim", "enum": SectionEnum.KIYIM,
        "subs": ["Erkak", "Ayol", "Bola"],
    },
}

PAYMENTS: dict[str, tuple[str, PaymentTypeEnum]] = {
    "naqd": ("💵 Naqd", PaymentTypeEnum.NAQD),
    "nasiya": ("📅 Nasiya", PaymentTypeEnum.NASIYA),
    "ikkalasi": ("✅ Ikkalasi", PaymentTypeEnum.IKKALASI),
}

CONDITIONS: dict[str, tuple[str, ConditionEnum]] = {
    "yangi": ("✨ Yangi", ConditionEnum.YANGI),
    "ishlatilgan": ("🔄 Ishlatilgan", ConditionEnum.ISHLATILGAN),
}

REGIONS = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
    "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
    "Jizzax", "Navoiy", "Xorazm", "QQR",
]

STATUS_LABELS = {
    "pending": "⏳ Tekshiruvda",
    "active": "✅ Faol",
    "rejected": "❌ Rad etilgan",
    "deleted": "🗑 O'chirilgan",
}


# ───────────────────────── Display helpers ─────────────────────────
def section_label(value) -> str:
    """Human label for a SectionEnum / its raw value."""
    key = value.value if hasattr(value, "value") else str(value)
    info = SECTIONS.get(key)
    return f"{info['emoji']} {info['name']}" if info else key


def payment_label(value) -> str:
    key = value.value if hasattr(value, "value") else str(value)
    return PAYMENTS.get(key, (key, None))[0]


def condition_label(value) -> str:
    key = value.value if hasattr(value, "value") else str(value)
    return CONDITIONS.get(key, (key, None))[0]


def enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def fmt_price(amount: int) -> str:
    try:
        return f"{int(amount):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(amount)


def parse_price(text: str) -> int | None:
    cleaned = text.replace(" ", "").replace(",", "").replace(".", "")
    return int(cleaned) if cleaned.isdigit() and int(cleaned) > 0 else None


def normalize_username(text: str) -> str:
    u = text.strip().lstrip("@").split("/")[-1]
    return f"@{u}" if u else "@—"


def listing_summary(listing) -> str:
    return (
        f"📢 <b>{section_label(listing.section)}</b> | 📍 {listing.viloyat}\n"
        f"💰 {fmt_price(listing.price)} so'm\n"
        f"📞 {listing.seller_username}\n"
        f"👁 {listing.views} marta ko'rildi"
    )


def listing_full(listing) -> str:
    return (
        f"📢 <b>{section_label(listing.section)}</b>"
        + (f" › {listing.subcategory}" if listing.subcategory else "")
        + "\n\n"
        f"💰 Narx: <b>{fmt_price(listing.price)} so'm</b>\n"
        f"💳 To'lov: {payment_label(listing.payment_type)}\n"
        f"📦 Holat: {condition_label(listing.condition)}\n"
        f"📍 Viloyat: {listing.viloyat}\n"
        f"📞 Kontakt: {listing.seller_username}\n"
        f"👁 {listing.views} marta ko'rildi\n\n"
        f"📝 {listing.description}"
    )


def expiry(days: int = 30) -> datetime:
    from datetime import timedelta
    return datetime.now(timezone.utc) + timedelta(days=days)


# ───────────────────────── Telegram helpers ─────────────────────────
async def is_subscribed(bot, user_id: int) -> bool:
    """True if the user is a member of the mandatory channel.

    Fails open (returns True) when the check itself errors so a
    misconfigured channel never locks every user out of the bot.
    """
    if not settings.CHANNEL_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Subscription check failed for %s: %s", user_id, e)
        return True


async def safe_edit(query, text: str, reply_markup=None, parse_mode="HTML"):
    """edit_message_text that tolerates 'message is not modified' and
    captionless/photo messages (falls back to a fresh message)."""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return
        try:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e2:
            logger.warning("safe_edit fallback failed: %s", e2)


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


async def reply(update: Update, text: str, reply_markup=None, parse_mode="HTML"):
    """Reply whether the update is a message or a callback query."""
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
