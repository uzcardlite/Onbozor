from enum import IntEnum, auto


class RegistrationState(IntEnum):
    FULL_NAME = auto()
    PHONE = auto()
    REGION = auto()


class ListingState(IntEnum):
    CATEGORY = auto()
    SUBCATEGORY = auto()
    PAYMENT_TYPE = auto()
    CONDITION = auto()
    PRICE = auto()
    REGION = auto()
    USERNAME = auto()
    DESCRIPTION = auto()
    PHOTO = auto()
    CONFIRM = auto()


class ShopCreateState(IntEnum):
    NAME = auto()
    CATEGORY = auto()
    DESCRIPTION = auto()
    REGION = auto()
    USERNAME = auto()
    LOGO = auto()
    CONFIRM = auto()


class AdminRejectState(IntEnum):
    REASON = auto()


class BroadcastState(IntEnum):
    MESSAGE = auto()
    CONFIRM = auto()
