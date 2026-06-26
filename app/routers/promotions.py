import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.promotion import Promotion, PromotionTypeEnum
from app.schemas.schemas import PromotionInitiate, PromotionOut
from app.services.payme import generate_checkout_url
from app.services.click import generate_payment_url
from app.crud import create_payment
from app.models.enums import PaymentMethodEnum

router = APIRouter(prefix="/promotions", tags=["Promotions"])

PROMO_PRICES = {
    "top": {"price": 15_000, "hours": 24},
    "featured": {"price": 25_000, "hours": 48},
    "urgent": {"price": 10_000, "hours": 24},
}


@router.post("/initiate", response_model=PromotionOut, status_code=201)
async def initiate_promotion(
    body: PromotionInitiate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await db.get(Listing, body.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    if listing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Faqat o'z e'loningizni promote qilishingiz mumkin")

    config = PROMO_PRICES.get(body.type)
    if not config:
        raise HTTPException(status_code=400, detail="Noto'g'ri promosiya turi")

    now = datetime.now(timezone.utc)
    promo = Promotion(
        listing_id=body.listing_id,
        user_id=user.id,
        type=PromotionTypeEnum(body.type),
        price=config["price"],
        starts_at=now,
        expires_at=now + timedelta(hours=config["hours"]),
        is_active=False,
    )
    db.add(promo)
    await db.flush()
    await db.refresh(promo)

    payment = await create_payment(
        db,
        user_id=user.id,
        listing_id=body.listing_id,
        amount=config["price"],
        payment_method=PaymentMethodEnum(body.method),
    )

    if body.method == "payme":
        url = generate_checkout_url(str(payment.id), config["price"])
    else:
        url = generate_payment_url(str(payment.id), config["price"])

    result = PromotionOut.model_validate(promo)
    result.payment_url = url
    return result


@router.get("/my", response_model=list[PromotionOut])
async def my_promotions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Promotion)
        .where(Promotion.user_id == user.id)
        .order_by(Promotion.created_at.desc())
        .limit(20)
    )
    return [PromotionOut.model_validate(p) for p in result.scalars().all()]


async def expire_promotions(db: AsyncSession):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Promotion).where(Promotion.is_active == True, Promotion.expires_at <= now)
    )
    expired = result.scalars().all()

    for promo in expired:
        promo.is_active = False
        await db.execute(
            update(Listing).where(Listing.id == promo.listing_id).values(
                is_promoted=False, promoted_until=None
            )
        )

    await db.flush()
    return len(expired)


async def activate_promotion(db: AsyncSession, listing_id: uuid.UUID):
    result = await db.execute(
        select(Promotion).where(
            Promotion.listing_id == listing_id,
            Promotion.is_active == False,
        ).order_by(Promotion.created_at.desc()).limit(1)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        return

    now = datetime.now(timezone.utc)
    promo.is_active = True
    promo.starts_at = now
    hours = PROMO_PRICES.get(promo.type.value, {}).get("hours", 24)
    promo.expires_at = now + timedelta(hours=hours)

    await db.execute(
        update(Listing).where(Listing.id == listing_id).values(
            is_promoted=True, promoted_until=promo.expires_at
        )
    )
    await db.flush()
