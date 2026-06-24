from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from app.constants import CATEGORIES, REGIONS, PAYMENT_TYPES, CONDITION_TYPES


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📢 E'lon berish", "🏪 Do'konlar"],
            ["📋 Mening e'lonlarim", "❤️ Sevimlilar"],
            ["👥 Referral", "👤 Profil"],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📊 Statistika", "👥 Foydalanuvchilar"],
            ["📢 E'lonlar", "🏪 Do'konlar"],
            ["📨 Broadcast", "⚙️ Sozlamalar"],
            ["🔙 Asosiy menyu"],
        ],
        resize_keyboard=True,
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"cat:{data['slug']}")]
        for name, data in CATEGORIES.items()
    ]
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def subcategories_keyboard(category_slug: str) -> InlineKeyboardMarkup:
    for name, data in CATEGORIES.items():
        if data["slug"] == category_slug:
            buttons = [
                [InlineKeyboardButton(sub, callback_data=f"subcat:{sub}")]
                for sub in data["subcategories"]
            ]
            buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_cat")])
            return InlineKeyboardMarkup(buttons)
    return InlineKeyboardMarkup([])


def regions_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(REGIONS), 2):
        row = [InlineKeyboardButton(REGIONS[i], callback_data=f"region:{REGIONS[i]}")]
        if i + 1 < len(REGIONS):
            row.append(InlineKeyboardButton(REGIONS[i + 1], callback_data=f"region:{REGIONS[i + 1]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def payment_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(pt, callback_data=f"pay:{pt}")]
        for pt in PAYMENT_TYPES
    ]
    return InlineKeyboardMarkup(buttons)


def condition_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(ct, callback_data=f"cond:{ct}")]
        for ct in CONDITION_TYPES
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yuborish", callback_data="confirm_listing"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"),
        ]
    ])


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip")]
    ])


def shop_categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"shop_cat:{data['slug']}")]
        for name, data in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(buttons)


def admin_listing_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{listing_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{listing_id}"),
        ]
    ])


def admin_shop_keyboard(shop_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"shop_approve:{shop_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"shop_reject:{shop_id}"),
        ]
    ])


def payment_method_keyboard(shop_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💳 Payme", callback_data=f"payment:payme:{shop_id}"),
            InlineKeyboardButton("💳 Click", callback_data=f"payment:click:{shop_id}"),
        ]
    ])


def favourite_toggle_keyboard(item_type: str, item_id: int, is_fav: bool) -> InlineKeyboardMarkup:
    text = "💔 Sevimlilardan o'chirish" if is_fav else "❤️ Sevimlilarga qo'shish"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=f"fav:{item_type}:{item_id}")]
    ])
