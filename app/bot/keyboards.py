"""All inline keyboards for the OnBozor bot."""
from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M, WebAppInfo

from app.config import settings
from app.bot.common import SECTIONS, PAYMENTS, CONDITIONS, REGIONS, WEB_APP

BACK = "⬅️ Orqaga"
HOME = "🏠 Bosh menyu"


def _rows(buttons, per_row=2):
    return [buttons[i:i + per_row] for i in range(0, len(buttons), per_row)]


# ───────────────────────── Subscription / menu ─────────────────────────
def subscribe_kb() -> M:
    return M([
        [B("📢 Kanalga o'tish", url=settings.channel_link)],
        [B("✅ Obuna bo'ldim", callback_data="check_sub")],
    ])


def regions_kb(prefix: str, extra_all: bool = False) -> M:
    btns = []
    if extra_all:
        btns.append([B("🌍 Barcha viloyatlar", callback_data=f"{prefix}:__all__")])
    row = []
    for r in REGIONS:
        row.append(B(r, callback_data=f"{prefix}:{r}"))
        if len(row) == 2:
            btns.append(row)
            row = []
    if row:
        btns.append(row)
    return M(btns)


def main_menu_kb() -> M:
    return M([
        [B("🌐 Web saytga o'tish", web_app=WebAppInfo(url=WEB_APP))],
        [B("📢 E'lon berish", callback_data="menu:listing"),
         B("🔍 Qidiruv", callback_data="menu:search")],
        [B("🏪 Do'konlar", callback_data="menu:shops"),
         B("👤 Profilim", callback_data="menu:profile")],
        [B("🔗 Referral", callback_data="menu:referral"),
         B("❤️ Sevimlilar", callback_data="menu:favs")],
        [B("💬 Xabarlar", callback_data="menu:messages"),
         B("⭐ Reyting", callback_data="menu:rating")],
    ])


def home_kb() -> M:
    return M([[B(HOME, callback_data="menu:home")]])


# ───────────────────────── Listing flow ─────────────────────────
def sections_kb() -> M:
    btns = [B(f"{v['emoji']} {v['name']}", callback_data=f"l_sec:{k}") for k, v in SECTIONS.items()]
    rows = _rows(btns, 2)
    rows.append([B("❌ Bekor qilish", callback_data="l_cancel")])
    return M(rows)


def subcats_kb(section_key: str) -> M:
    subs = SECTIONS[section_key]["subs"]
    btns = [B(s, callback_data=f"l_sub:{s}") for s in subs]
    rows = _rows(btns, 2)
    rows.append([B(BACK, callback_data="l_back:section")])
    return M(rows)


def payments_kb() -> M:
    btns = [B(label, callback_data=f"l_pay:{k}") for k, (label, _) in PAYMENTS.items()]
    return M([btns, [B(BACK, callback_data="l_back:category")]])


def conditions_kb() -> M:
    btns = [B(label, callback_data=f"l_cond:{k}") for k, (label, _) in CONDITIONS.items()]
    return M([btns, [B(BACK, callback_data="l_back:payment")]])


def back_only_kb(target: str) -> M:
    return M([[B(BACK, callback_data=f"l_back:{target}")]])


def listing_region_kb() -> M:
    kb = regions_kb("l_reg")
    return M(kb.inline_keyboard + [[B(BACK, callback_data="l_back:price")]])


def skip_photo_kb() -> M:
    return M([
        [B("⏭ O'tkazib yuborish", callback_data="l_skip")],
        [B(BACK, callback_data="l_back:desc")],
    ])


def listing_confirm_kb() -> M:
    return M([
        [B("✅ Yuborish", callback_data="l_confirm"),
         B("✏️ Tahrirlash", callback_data="l_edit")],
        [B("❌ Bekor qilish", callback_data="l_cancel")],
    ])


# ───────────────────────── Search / listing cards ─────────────────────────
def listing_card_kb(listing_id, bot_username: str, is_fav: bool = False) -> M:
    fav_text = "💔 Sevimlidan" if is_fav else "❤️ Sevimliga"
    share = f"https://t.me/{bot_username}?start=listing_{listing_id}"
    return M([
        [B("👁 Ko'rish", callback_data=f"l_view:{listing_id}"),
         B(fav_text, callback_data=f"fav:listing:{listing_id}")],
        [B("📤 Ulashish", url=f"https://t.me/share/url?url={share}")],
    ])


def listing_view_kb(listing_id, seller_tg_id, viewer_is_seller: bool, is_fav: bool = False) -> M:
    rows = []
    fav_text = "💔 Sevimlidan o'chirish" if is_fav else "❤️ Sevimliga qo'shish"
    rows.append([B(fav_text, callback_data=f"fav:listing:{listing_id}")])
    if not viewer_is_seller:
        rows.append([B("💬 Sotuvchiga yozish", callback_data=f"chat_start:{listing_id}")])
        rows.append([B("⭐ Reyting qoldirish", callback_data=f"rate:{listing_id}")])
    rows.append([B(HOME, callback_data="menu:home")])
    return M(rows)


def pagination_kb(prefix: str, offset: int, total: int, limit: int) -> list:
    page = offset // limit + 1
    pages = (total + limit - 1) // limit
    row = []
    if offset > 0:
        row.append(B("◀️ Oldingi", callback_data=f"{prefix}:{offset - limit}"))
    row.append(B(f"{page}/{pages}", callback_data="noop"))
    if offset + limit < total:
        row.append(B("Keyingi ▶️", callback_data=f"{prefix}:{offset + limit}"))
    return [row] if pages > 1 else []


# ───────────────────────── Shops browse ─────────────────────────
def shop_sections_kb() -> M:
    btns = [B(f"{v['emoji']} {v['name']}", callback_data=f"sh_cat:{k}") for k, v in SECTIONS.items()]
    rows = _rows(btns, 2)
    rows.append([B(HOME, callback_data="menu:home")])
    return M(rows)


def shop_card_kb(shop_id, is_fav: bool = False) -> M:
    fav_text = "💔 Kuzatishni bekor" if is_fav else "🔔 Kuzatish"
    return M([
        [B("👁 Ko'rish", callback_data=f"sh_view:{shop_id}"),
         B(fav_text, callback_data=f"fav:shop:{shop_id}")],
    ])


# ───────────────────────── Profile ─────────────────────────
def profile_kb() -> M:
    return M([
        [B("📢 E'lonlarim", callback_data="my_listings"),
         B("🏪 Do'konim", callback_data="my_shop")],
        [B("🏪 Do'kon ochish", callback_data="shop_open")],
        [B("🌐 Web saytda ko'rish", web_app=WebAppInfo(url=f"{WEB_APP}/profile"))],
        [B(HOME, callback_data="menu:home")],
    ])


# ───────────────────────── Rating ─────────────────────────
def stars_kb(listing_id) -> M:
    rows = [[B("⭐" * n, callback_data=f"star:{listing_id}:{n}")] for n in range(1, 6)]
    rows.append([B("❌ Bekor", callback_data="menu:home")])
    return M(rows)


def rate_skip_kb() -> M:
    return M([[B("⏭ Izohsiz yuborish", callback_data="rate_skip")]])


# ───────────────────────── Shop create ─────────────────────────
def shop_cat_kb() -> M:
    btns = [B(f"{v['emoji']} {v['name']}", callback_data=f"sc_cat:{k}") for k, v in SECTIONS.items()]
    return M(_rows(btns, 2) + [[B("❌ Bekor qilish", callback_data="sc_cancel")]])


def shop_region_kb() -> M:
    return regions_kb("sc_reg")


def shop_confirm_kb() -> M:
    return M([
        [B("💳 Payme", callback_data="sc_pay:payme"),
         B("💳 Click", callback_data="sc_pay:click")],
        [B("❌ Bekor qilish", callback_data="sc_cancel")],
    ])


# ───────────────────────── Messages ─────────────────────────
def chat_kb() -> M:
    return M([[B("⬅️ Suhbatlar", callback_data="menu:messages"),
               B(HOME, callback_data="menu:home")]])


# ───────────────────────── Admin ─────────────────────────
def admin_moderation_kb(listing_id) -> M:
    return M([
        [B("✅ Tasdiqlash", callback_data=f"adm_ok:{listing_id}"),
         B("❌ Rad etish", callback_data=f"adm_no:{listing_id}")],
    ])
