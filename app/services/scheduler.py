import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.shop import Shop
from app.models.listing import Listing
from app.models.user import User
from app.models.enums import ListingStatusEnum
from app.services.notification import (
    notify_shop_expiring, notify_shop_expired, notify_listing_expiring,
)

logger = logging.getLogger(__name__)


async def check_expiring_shops():
    now = datetime.now(timezone.utc)
    warn_date = now + timedelta(days=3)

    async with async_session() as session:
        result = await session.execute(
            select(Shop, User.tg_id)
            .join(User, Shop.owner_id == User.id)
            .where(
                Shop.is_active == True,
                Shop.subscription_expires.isnot(None),
                Shop.subscription_expires <= warn_date,
                Shop.subscription_expires > now,
            )
        )
        rows = result.all()

    sent = 0
    for shop, tg_id in rows:
        days_left = max(1, (shop.subscription_expires - now).days)
        await notify_shop_expiring(tg_id, shop.name, days_left)
        sent += 1

    logger.info("Expiring shop reminders sent: %d", sent)


async def deactivate_expired_shops():
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        result = await session.execute(
            select(Shop, User.tg_id)
            .join(User, Shop.owner_id == User.id)
            .where(
                Shop.is_active == True,
                Shop.subscription_expires.isnot(None),
                Shop.subscription_expires <= now,
            )
        )
        rows = result.all()

        for shop, tg_id in rows:
            shop.is_active = False
            await notify_shop_expired(tg_id, shop.name)

        await session.commit()

    logger.info("Expired shops deactivated: %d", len(rows))


async def check_expiring_listings():
    now = datetime.now(timezone.utc)
    warn_date = now + timedelta(days=1)

    async with async_session() as session:
        result = await session.execute(
            select(Listing, User.tg_id)
            .join(User, Listing.user_id == User.id)
            .where(
                Listing.status == ListingStatusEnum.ACTIVE,
                Listing.expires_at <= warn_date,
                Listing.expires_at > now,
                Listing.user_id.isnot(None),
            )
        )
        rows = result.all()

    sent = 0
    for listing, tg_id in rows:
        await notify_listing_expiring(tg_id, str(listing.id), listing.category)
        sent += 1

    logger.info("Expiring listing reminders sent: %d", sent)


async def delete_expired_listings():
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        result = await session.execute(
            update(Listing)
            .where(
                Listing.status == ListingStatusEnum.ACTIVE,
                Listing.expires_at <= now,
            )
            .values(status=ListingStatusEnum.DELETED)
        )
        await session.commit()
        logger.info("Expired listings deleted: %d", result.rowcount)


async def expire_promotions():
    from app.models.promotion import Promotion
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        result = await session.execute(
            select(Promotion, Listing, User.tg_id)
            .join(Listing, Promotion.listing_id == Listing.id)
            .join(User, Promotion.user_id == User.id)
            .where(Promotion.is_active == True, Promotion.expires_at <= now)
        )
        rows = result.all()

        for promo, listing, tg_id in rows:
            promo.is_active = False
            listing.is_promoted = False
            listing.promoted_until = None
            from app.services.notification import _send
            WEB_APP = "https://onbozor.vercel.app"
            await _send(tg_id,
                f"❌ <b>E'loningiz promosiyasi tugadi</b>\n\n📢 {listing.category}\n\nQayta faollashtiring:",
                [[{"text": "🚀 Qayta promote", "web_app": {"url": f"{WEB_APP}/listing/{listing.id}"}}]],
            )

        await session.commit()

    logger.info("Expired promotions: %d", len(rows))


async def warn_expiring_promotions():
    from app.models.promotion import Promotion
    now = datetime.now(timezone.utc)
    warn_time = now + timedelta(hours=2)

    async with async_session() as session:
        result = await session.execute(
            select(Promotion, Listing, User.tg_id)
            .join(Listing, Promotion.listing_id == Listing.id)
            .join(User, Promotion.user_id == User.id)
            .where(
                Promotion.is_active == True,
                Promotion.expires_at <= warn_time,
                Promotion.expires_at > now,
            )
        )
        rows = result.all()

    for promo, listing, tg_id in rows:
        from app.services.notification import _send
        WEB_APP = "https://onbozor.vercel.app"
        await _send(tg_id,
            f"⚠️ <b>Promosiya 2 soatda tugaydi!</b>\n\n📢 {listing.category}\n\nDavom ettirish:",
            [[{"text": "🚀 Davom ettirish", "web_app": {"url": f"{WEB_APP}/listing/{listing.id}"}}]],
        )

    logger.info("Expiring promotion warnings: %d", len(rows))


async def run_daily_tasks():
    logger.info("Running daily scheduled tasks")
    await check_expiring_shops()
    await deactivate_expired_shops()
    await check_expiring_listings()
    await delete_expired_listings()
    await expire_promotions()
    await warn_expiring_promotions()
    logger.info("Daily tasks completed")


async def scheduler_loop():
    logger.info("Scheduler started")
    while True:
        now = datetime.now(timezone.utc)
        tomorrow_9am = now.replace(hour=4, minute=0, second=0, microsecond=0)
        if tomorrow_9am <= now:
            tomorrow_9am += timedelta(days=1)

        wait_seconds = (tomorrow_9am - now).total_seconds()
        logger.info("Next scheduled run at %s (in %.0f seconds)", tomorrow_9am, wait_seconds)
        await asyncio.sleep(wait_seconds)

        try:
            await run_daily_tasks()
        except Exception as e:
            logger.error("Scheduler error: %s", e, exc_info=True)
