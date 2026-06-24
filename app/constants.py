from enum import Enum

REGIONS = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
    "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
    "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

CATEGORIES = {
    "🏠 Uy-joy": {
        "slug": "uy_joy",
        "subcategories": ["Sotish", "Ijara", "Dacha", "Garaj"],
    },
    "📱 Texnika": {
        "slug": "texnika",
        "subcategories": ["Telefon", "Noutbuk", "Maishiy texnika", "Boshqalar"],
    },
    "🚗 Avtomobil": {
        "slug": "avtomobil",
        "subcategories": ["Yangi", "Ishlatilgan", "Ehtiyot qismlar"],
    },
    "🏍 Moto": {
        "slug": "moto",
        "subcategories": ["Skuterlar", "Motolar"],
    },
    "👕 Kiyim": {
        "slug": "kiyim",
        "subcategories": ["Erkak", "Ayol", "Bola"],
    },
}

CLOTHING_TYPES = ["Futbolka", "Ko'ylak", "Shim", "Kurtka", "Boshqa"]

PAYMENT_TYPES = ["💵 Naqd", "💳 Nasiya", "💵💳 Ikkalasi"]
CONDITION_TYPES = ["🆕 Yangi", "♻️ Ishlatilgan"]


class ListingStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ShopStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REJECTED = "rejected"
