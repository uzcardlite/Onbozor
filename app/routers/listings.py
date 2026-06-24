import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.enums import SectionEnum, PaymentTypeEnum, ConditionEnum, ListingStatusEnum
from app.crud import (
    create_listing, get_listing, update_listing, delete_listing,
    get_listings_by_filter, get_listings_by_user, increment_views, count_listings,
)
from app.schemas.schemas import ListingCreate, ListingUpdate, ListingOut, ListingBrief

router = APIRouter(prefix="/listings", tags=["Listings"])


@router.get("", response_model=list[ListingBrief])
async def list_listings(
    section: SectionEnum | None = None,
    category: str | None = None,
    viloyat: str | None = None,
    payment_type: PaymentTypeEnum | None = None,
    condition: ConditionEnum | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from app.services.search_engine import search_listings
    listings, _ = await search_listings(
        db, q=search, section=section, viloyat=viloyat,
        price_min=price_min, price_max=price_max,
        limit=limit, offset=(page - 1) * limit,
    )
    return [ListingBrief.model_validate(l) for l in listings]


@router.get("/my", response_model=list[ListingOut])
async def my_listings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listings = await get_listings_by_user(db, user.id)
    return [ListingOut.model_validate(l) for l in listings]


@router.get("/{listing_id}", response_model=ListingOut)
async def get_single_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    await increment_views(db, listing_id)
    listing.views += 1
    return ListingOut.model_validate(listing)


@router.post("", response_model=ListingOut, status_code=201)
async def create_new_listing(
    body: ListingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await create_listing(
        db,
        user_id=user.id,
        shop_id=body.shop_id,
        section=body.section,
        category=body.category,
        subcategory=body.subcategory,
        payment_type=body.payment_type,
        condition=body.condition,
        price=body.price,
        negotiable=body.negotiable,
        viloyat=body.viloyat,
        seller_username=body.seller_username,
        description=body.description,
        image_urls=body.image_urls,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    return ListingOut.model_validate(listing)


@router.put("/{listing_id}", response_model=ListingOut)
async def update_my_listing(
    listing_id: uuid.UUID,
    body: ListingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    if listing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="O'zgarish kiritilmadi")

    updated = await update_listing(db, listing_id, **updates)
    return ListingOut.model_validate(updated)


@router.delete("/{listing_id}", status_code=204)
async def delete_my_listing(
    listing_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    if listing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
    await update_listing(db, listing_id, status=ListingStatusEnum.DELETED)
