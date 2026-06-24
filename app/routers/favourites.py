import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.crud import (
    get_shop, get_listing, is_favourite, create_favourite,
    remove_favourite, get_user_favourite_shops, get_user_favourite_listings,
)
from app.schemas.schemas import FavouritesResponse, ShopOut, ListingBrief

router = APIRouter(prefix="/favourites", tags=["Favourites"])


@router.get("", response_model=FavouritesResponse)
async def get_favourites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav_shops = await get_user_favourite_shops(db, user.id)
    fav_listings = await get_user_favourite_listings(db, user.id)

    shops = []
    for fav in fav_shops:
        shop = await get_shop(db, fav.shop_id)
        if shop:
            shops.append(ShopOut.model_validate(shop))

    listings = []
    for fav in fav_listings:
        listing = await get_listing(db, fav.listing_id)
        if listing:
            listings.append(ListingBrief.model_validate(listing))

    return FavouritesResponse(shops=shops, listings=listings)


@router.post("/shop/{shop_id}")
async def toggle_shop_favourite(
    shop_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")

    if await is_favourite(db, user.id, shop_id=shop_id):
        await remove_favourite(db, user.id, shop_id=shop_id)
        return {"status": "removed"}

    await create_favourite(db, user_id=user.id, shop_id=shop_id)
    return {"status": "added"}


@router.post("/listing/{listing_id}")
async def toggle_listing_favourite(
    listing_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")

    if await is_favourite(db, user.id, listing_id=listing_id):
        await remove_favourite(db, user.id, listing_id=listing_id)
        return {"status": "removed"}

    await create_favourite(db, user_id=user.id, listing_id=listing_id)
    return {"status": "added"}
