from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.schemas import ReferralStats

router = APIRouter(prefix="/referral", tags=["Referral"])


@router.get("", response_model=ReferralStats)
async def get_referral_stats(user: User = Depends(get_current_user)):
    return ReferralStats(
        ref_code=user.ref_code,
        ref_link=f"https://t.me/onbozornewbot?startapp={user.ref_code}",
        ref_count=user.ref_count,
        ref_earnings=user.ref_earnings,
    )
