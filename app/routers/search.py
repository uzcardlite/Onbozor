from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import SectionEnum
from app.services.search_engine import search_listings, search_shops
from app.schemas.schemas import SearchResponse, ListingBrief, ShopOut

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def full_search(
    q: str = Query("", min_length=0),
    section: SectionEnum | None = None,
    viloyat: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    query = q if q else None

    listings, total_listings = await search_listings(
        db, q=query, section=section, viloyat=viloyat,
        price_min=price_min, price_max=price_max,
        limit=limit, offset=offset,
    )
    shops, total_shops = await search_shops(
        db, q=query, section=section, viloyat=viloyat,
        limit=limit, offset=offset,
    )

    return SearchResponse(
        listings=[ListingBrief.model_validate(l) for l in listings],
        shops=[ShopOut.model_validate(s) for s in shops],
        total_listings=total_listings,
        total_shops=total_shops,
    )
