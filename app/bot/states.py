"""Finite-State-Machine states for every conversational flow in the bot."""
from enum import IntEnum, auto


class Reg(IntEnum):
    REGION = auto()


class L(IntEnum):
    """E'lon berish (listing creation)."""
    SECTION = auto()
    CATEGORY = auto()
    PAYMENT = auto()
    CONDITION = auto()
    PRICE = auto()
    VILOYAT = auto()
    USERNAME = auto()
    DESC = auto()
    IMAGE = auto()
    CONFIRM = auto()


class S(IntEnum):
    """Qidiruv (search)."""
    QUERY = auto()


class Chat(IntEnum):
    """Xabarlar (messaging)."""
    TYPING = auto()


class Rate(IntEnum):
    """Reyting (rating a seller)."""
    STARS = auto()
    COMMENT = auto()


class Shop(IntEnum):
    """Do'kon ochish (shop creation)."""
    NAME = auto()
    DESC = auto()
    CATEGORY = auto()
    VILOYAT = auto()
    USERNAME = auto()
    CONFIRM = auto()


class Adm(IntEnum):
    """Admin flows."""
    REJECT_REASON = auto()
    BROADCAST_MSG = auto()
    BROADCAST_CONFIRM = auto()
