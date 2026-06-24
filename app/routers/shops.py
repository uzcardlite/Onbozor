import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.enums import SectionEnum, ListingStatusEnum
from app.crud import (
    create_shop, get_shop, update_shop, get_shops_by_category,
    get_shops_by_owner, get_listings_by_filter,
)
from app.config import settings
from app.schemas.schemas import ShopCreate, ShopUpdate, ShopOut, ShopDetail, ListingBrief

router = APIRouter(prefix="/shops", tags=["Shops"])


@router.get("", response_model=list[ShopOut])
async def list_shops(
    category: SectionEnum | None = None,
    viloyat: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from app.services.search_engine import search_shops
    shops, _ = await search_shops(db, section=category, viloyat=viloyat, limit=limit, offset=(page - 1) * limit)
    return [ShopOut.model_validate(s) for s in shops]


@router.get("/my", response_model=list[ShopOut])
async def my_shops(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shops = await get_shops_by_owner(db, user.id)
    return [ShopOut.model_validate(s) for s in shops]


@router.get("/{shop_id}", response_model=ShopDetail)
async def get_single_shop(shop_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    shop = await get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")

    listings = await get_listings_by_filter(db, section=shop.category, status=ListingStatusEnum.ACTIVE)
    shop_listings = [l for l in listings if l.shop_id == shop_id]

    result = ShopDetail.model_validate(shop)
    result.listings = [ListingBrief.model_validate(l) for l in shop_listings]
    return result


@router.post("", response_model=ShopOut, status_code=201)
async def create_new_shop(
    body: ShopCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await create_shop(
        db,
        owner_id=user.id,
        name=body.name,
        description=body.description,
        category=body.category,
        viloyat=body.viloyat,
        icon_url=body.icon_url,
        monthly_fee=settings.SHOP_MONTHLY_PRICE,
    )
    return ShopOut.model_validate(shop)


@router.put("/{shop_id}", response_model=ShopOut)
async def update_my_shop(
    shop_id: uuid.UUID,
    body: ShopUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")
    if shop.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="O'zgarish kiritilmadi")

    updated = await update_shop(db, shop_id, **updates)
    return ShopOut.model_validate(updated)
