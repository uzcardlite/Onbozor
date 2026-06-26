import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import (
    SectionEnum, PaymentTypeEnum, ConditionEnum,
    ListingStatusEnum, PaymentMethodEnum, PaymentStatusEnum,
    NotificationTypeEnum,
)


# ───────────── Auth ─────────────

class TelegramAuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    token: str
    user: "UserOut"


# ───────────── User ─────────────

class UserOut(BaseModel):
    id: uuid.UUID
    tg_id: int
    username: str | None
    full_name: str
    viloyat: str | None
    phone: str | None
    avatar_url: str | None
    ref_code: str
    ref_count: int
    ref_earnings: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    viloyat: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


# ───────────── Listing ─────────────

class ListingCreate(BaseModel):
    section: SectionEnum
    category: str
    subcategory: str | None = None
    payment_type: PaymentTypeEnum
    condition: ConditionEnum
    price: int = Field(gt=0)
    negotiable: bool = False
    viloyat: str
    seller_username: str
    description: str = Field(min_length=10)
    image_urls: list[str] = []
    shop_id: uuid.UUID | None = None


class ListingUpdate(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    payment_type: PaymentTypeEnum | None = None
    condition: ConditionEnum | None = None
    price: int | None = Field(default=None, gt=0)
    negotiable: bool | None = None
    viloyat: str | None = None
    seller_username: str | None = None
    description: str | None = None
    image_urls: list[str] | None = None


class ListingOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    shop_id: uuid.UUID | None
    section: SectionEnum
    category: str
    subcategory: str | None
    payment_type: PaymentTypeEnum
    condition: ConditionEnum
    price: int
    negotiable: bool
    viloyat: str
    seller_username: str
    description: str
    image_urls: list[str]
    views: int
    is_promoted: bool
    status: ListingStatusEnum
    reject_reason: str | None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class ListingBrief(BaseModel):
    id: uuid.UUID
    section: SectionEnum
    category: str
    price: int
    viloyat: str
    image_urls: list[str]
    views: int
    is_promoted: bool
    status: ListingStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


# ───────────── Shop ─────────────

class ShopCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    category: SectionEnum
    viloyat: str | None = None
    icon_url: str | None = None


class ShopUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    viloyat: str | None = None
    icon_url: str | None = None


class ShopOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str
    category: SectionEnum
    viloyat: str | None
    icon_url: str | None
    is_verified: bool
    is_active: bool
    monthly_fee: int
    subscription_expires: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ShopDetail(ShopOut):
    listings: list[ListingBrief] = []


# ───────────── Favourite ─────────────

class FavouriteOut(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID | None
    listing_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class FavouritesResponse(BaseModel):
    shops: list[ShopOut]
    listings: list[ListingBrief]


# ───────────── Referral ─────────────

class ReferralStats(BaseModel):
    ref_code: str
    ref_link: str
    ref_count: int
    ref_earnings: int


# ───────────── Payment ─────────────

class PaymentInitiate(BaseModel):
    shop_id: uuid.UUID
    method: PaymentMethodEnum


class PaymentOut(BaseModel):
    id: uuid.UUID
    amount: int
    payment_method: PaymentMethodEnum
    status: PaymentStatusEnum
    created_at: datetime
    payment_url: str = ""

    class Config:
        from_attributes = True


class PaymentStatusOut(BaseModel):
    id: uuid.UUID
    status: PaymentStatusEnum
    amount: int
    payment_method: PaymentMethodEnum

    class Config:
        from_attributes = True


# ───────────── Notification ─────────────

class NotificationOut(BaseModel):
    id: uuid.UUID
    type: NotificationTypeEnum
    title: str
    body: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ───────────── Admin ─────────────

class AdminStats(BaseModel):
    total_users: int
    total_listings: int
    active_listings: int
    pending_listings: int
    total_shops: int
    active_shops: int
    total_payments: int
    total_revenue: int


class RejectRequest(BaseModel):
    reason: str = Field(min_length=5)


class BroadcastRequest(BaseModel):
    text: str = Field(min_length=1)
    image_url: str | None = None


class BroadcastOut(BaseModel):
    id: uuid.UUID
    sent_count: int


# ───────────── Search ─────────────

class SearchResponse(BaseModel):
    listings: list[ListingBrief]
    shops: list[ShopOut]
    total_listings: int
    total_shops: int


# ───────────── Pagination ─────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
    pages: int


# ───────────── Upload ─────────────

class UploadResponse(BaseModel):
    url: str
    public_id: str


# ───────────── Error ─────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str


AuthResponse.model_rebuild()
