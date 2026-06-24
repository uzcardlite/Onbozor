import enum


class SectionEnum(str, enum.Enum):
    UYJOY = "uyjoy"
    TEXNIKA = "texnika"
    AVTO = "avto"
    MOTO = "moto"
    KIYIM = "kiyim"


class PaymentTypeEnum(str, enum.Enum):
    NAQD = "naqd"
    NASIYA = "nasiya"
    IKKALASI = "ikkalasi"


class ConditionEnum(str, enum.Enum):
    YANGI = "yangi"
    ISHLATILGAN = "ishlatilgan"


class ListingStatusEnum(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    DELETED = "deleted"


class PaymentMethodEnum(str, enum.Enum):
    PAYME = "payme"
    CLICK = "click"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationTypeEnum(str, enum.Enum):
    NEW_LISTING = "new_listing"
    LISTING_APPROVED = "listing_approved"
    LISTING_REJECTED = "listing_rejected"
    SHOP_APPROVED = "shop_approved"
    PAYMENT_SUCCESS = "payment_success"
    REFERRAL = "referral"
    SYSTEM = "system"
