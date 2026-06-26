from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_admin_user
from app.models.user import User
from app.models.listing import Listing
from app.models.listing_view import ListingView
from app.models.favourite import Favourite
from app.models.shop import Shop
from app.models.payment import Payment
from app.models.enums import ListingStatusEnum, PaymentStatusEnum

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/my")
async def my_analytics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    my_listings = (await db.execute(
        select(Listing.id).where(Listing.user_id == user.id)
    )).scalars().all()

    listing_ids = list(my_listings)

    total_views = 0
    views_by_day = []
    top_listings = []
    total_favourites = 0

    if listing_ids:
        total_views = (await db.execute(
            select(func.count(ListingView.id)).where(ListingView.listing_id.in_(listing_ids))
        )).scalar() or 0

        total_favourites = (await db.execute(
            select(func.count(Favourite.id)).where(Favourite.listing_id.in_(listing_ids))
        )).scalar() or 0

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        daily = await db.execute(
            select(
                cast(ListingView.created_at, Date).label("day"),
                func.count(ListingView.id).label("count"),
            )
            .where(ListingView.listing_id.in_(listing_ids), ListingView.created_at >= week_ago)
            .group_by("day")
            .order_by("day")
        )
        views_by_day = [{"date": str(row.day), "views": row.count} for row in daily.all()]

        top = await db.execute(
            select(Listing.id, Listing.category, Listing.price, Listing.views, Listing.viloyat)
            .where(Listing.id.in_(listing_ids))
            .order_by(Listing.views.desc())
            .limit(3)
        )
        top_listings = [
            {"id": str(r.id), "category": r.category, "price": r.price, "views": r.views, "viloyat": r.viloyat}
            for r in top.all()
        ]

    return {
        "total_views": total_views,
        "total_listings": len(listing_ids),
        "total_favourites": total_favourites,
        "views_by_day": views_by_day,
        "top_listings": top_listings,
    }


@router.get("/admin")
async def admin_analytics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    users_total = (await db.execute(select(func.count(User.id)))).scalar()
    users_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )).scalar()

    listings_total = (await db.execute(
        select(func.count(Listing.id)).where(Listing.status == ListingStatusEnum.ACTIVE)
    )).scalar()
    listings_today = (await db.execute(
        select(func.count(Listing.id)).where(Listing.created_at >= today_start)
    )).scalar()

    revenue_total = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatusEnum.PAID)
    )).scalar()
    revenue_today = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatusEnum.PAID, Payment.created_at >= today_start
        )
    )).scalar()

    cat_result = await db.execute(
        select(Listing.category, func.count(Listing.id).label("count"))
        .where(Listing.status == ListingStatusEnum.ACTIVE)
        .group_by(Listing.category)
        .order_by(func.count(Listing.id).desc())
        .limit(10)
    )
    top_categories = [{"name": r.category, "count": r.count} for r in cat_result.all()]

    region_result = await db.execute(
        select(Listing.viloyat, func.count(Listing.id).label("count"))
        .where(Listing.status == ListingStatusEnum.ACTIVE)
        .group_by(Listing.viloyat)
        .order_by(func.count(Listing.id).desc())
        .limit(13)
    )
    top_regions = [{"name": r.viloyat, "count": r.count} for r in region_result.all()]

    week_ago = now - timedelta(days=7)
    daily_users = await db.execute(
        select(cast(User.created_at, Date).label("day"), func.count(User.id).label("count"))
        .where(User.created_at >= week_ago)
        .group_by("day").order_by("day")
    )
    users_by_day = [{"date": str(r.day), "count": r.count} for r in daily_users.all()]

    daily_revenue = await db.execute(
        select(cast(Payment.created_at, Date).label("day"), func.coalesce(func.sum(Payment.amount), 0).label("amount"))
        .where(Payment.status == PaymentStatusEnum.PAID, Payment.created_at >= week_ago)
        .group_by("day").order_by("day")
    )
    revenue_by_day = [{"date": str(r.day), "amount": r.amount} for r in daily_revenue.all()]

    pending = (await db.execute(
        select(func.count(Listing.id)).where(Listing.status == ListingStatusEnum.PENDING)
    )).scalar()

    shops_active = (await db.execute(
        select(func.count(Shop.id)).where(Shop.is_active == True)
    )).scalar()

    return {
        "users_today": users_today,
        "users_total": users_total,
        "listings_today": listings_today,
        "listings_total": listings_total,
        "revenue_today": revenue_today,
        "revenue_total": revenue_total,
        "pending_listings": pending,
        "active_shops": shops_active,
        "top_categories": top_categories,
        "top_regions": top_regions,
        "users_by_day": users_by_day,
        "revenue_by_day": revenue_by_day,
    }
