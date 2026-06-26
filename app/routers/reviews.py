import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.review import Review
from app.schemas.schemas import ReviewCreate, ReviewOut, SellerRating

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _to_out(r: Review, reviewer: User | None = None) -> ReviewOut:
    return ReviewOut(
        id=r.id,
        reviewer_id=r.reviewer_id,
        reviewer_name=reviewer.full_name if reviewer else "",
        reviewer_username=reviewer.username if reviewer else None,
        rating=r.rating,
        comment=r.comment,
        created_at=r.created_at,
    )


@router.post("", response_model=ReviewOut, status_code=201)
async def create_review(
    body: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await db.get(Listing, body.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")

    if listing.user_id == user.id:
        raise HTTPException(status_code=400, detail="O'z e'loningizga reyting qoldirib bo'lmaydi")

    if not listing.user_id:
        raise HTTPException(status_code=400, detail="Anonim e'longa reyting qoldirib bo'lmaydi")

    existing = (await db.execute(
        select(Review).where(Review.reviewer_id == user.id, Review.listing_id == body.listing_id)
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Siz allaqachon reyting qoldirgansiz")

    review = Review(
        reviewer_id=user.id,
        seller_id=listing.user_id,
        listing_id=body.listing_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    return _to_out(review, user)


@router.get("/user/{user_id}", response_model=SellerRating)
async def get_seller_reviews(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    avg_result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.seller_id == user_id)
    )
    avg_rating, total = avg_result.one()

    result = await db.execute(
        select(Review, User)
        .join(User, Review.reviewer_id == User.id)
        .where(Review.seller_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    reviews = [_to_out(r, u) for r, u in rows]

    return SellerRating(
        seller_id=user_id,
        avg_rating=round(float(avg_rating or 0), 1),
        total_reviews=total or 0,
        reviews=reviews,
    )


@router.get("/listing/{listing_id}", response_model=list[ReviewOut])
async def get_listing_reviews(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review, User)
        .join(User, Review.reviewer_id == User.id)
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
        .limit(50)
    )
    return [_to_out(r, u) for r, u in result.all()]
