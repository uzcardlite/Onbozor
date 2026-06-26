import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.models.payment import Payment
from app.models.enums import PaymentMethodEnum, PaymentStatusEnum, NotificationTypeEnum
from app.config import settings
from app.crud import create_payment, get_payment, get_shop, create_notification
from app.schemas.schemas import PaymentInitiate, PaymentOut, PaymentStatusOut
from app.services import payme, click
from app.services.notification import notify_payment_success, admin_new_payment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate", response_model=PaymentOut, status_code=201)
async def initiate_payment(
    body: PaymentInitiate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop(db, body.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")
    if shop.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Bu do'kon sizga tegishli emas")

    payment = await create_payment(
        db, user_id=user.id, shop_id=body.shop_id,
        amount=shop.monthly_fee, payment_method=body.method,
    )

    if body.method == PaymentMethodEnum.PAYME:
        url = payme.generate_checkout_url(str(payment.id), payment.amount)
    else:
        url = click.generate_payment_url(str(payment.id), payment.amount)

    result = PaymentOut.model_validate(payment)
    result.payment_url = url
    return result


@router.get("/status/{payment_id}", response_model=PaymentStatusOut)
async def check_payment_status(
    payment_id: str,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi")
    return PaymentStatusOut(
        id=payment.id, status=payment.status,
        amount=payment.amount, payment_method=payment.payment_method,
    )


@router.get("/my")
async def my_payments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(50)
    )
    payments = result.scalars().all()
    out = []
    for p in payments:
        shop = await get_shop(db, p.shop_id) if p.shop_id else None
        out.append({
            "id": str(p.id),
            "amount": p.amount,
            "method": p.payment_method.value if hasattr(p.payment_method, 'value') else p.payment_method,
            "status": p.status.value if hasattr(p.status, 'value') else p.status,
            "shop_name": shop.name if shop else None,
            "type": "shop" if p.shop_id else "promotion" if p.listing_id else "other",
            "created_at": p.created_at.isoformat(),
        })
    return out


@router.post("/payme/webhook")
async def payme_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}

    auth_header = request.headers.get("Authorization")
    result = await payme.handle_request(body, auth_header, db)

    method = body.get("method", "")
    if method == "PerformTransaction" and "result" in result:
        await _on_payment_success(body.get("params", {}).get("account", {}).get("order_id"), db)

    logger.info("Payme: method=%s", method)
    return result


@router.post("/click/webhook")
async def click_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        params = await request.json()
    else:
        form = await request.form()
        params = {k: v for k, v in form.items()}

    result = await click.handle_webhook(params, db)

    if str(params.get("action", "")) == "1" and result.get("error") == 0:
        await _on_payment_success(params.get("merchant_trans_id"), db)

    logger.info("Click: action=%s error=%s", params.get("action"), result.get("error"))
    return result


async def _on_payment_success(order_id, db: AsyncSession):
    if not order_id:
        return
    try:
        payment = await get_payment(db, order_id)
        if not payment or payment.status != PaymentStatusEnum.PAID:
            return

        shop_name = "Noma'lum"
        pay_type = "other"

        if payment.shop_id:
            shop = await get_shop(db, payment.shop_id)
            if shop:
                shop_name = shop.name
                pay_type = "shop"

        if payment.listing_id:
            try:
                from app.routers.promotions import activate_promotion
                await activate_promotion(db, payment.listing_id)
                pay_type = "promotion"
            except Exception as e:
                logger.error("Promotion activation failed: %s", e)

        if payment.user_id:
            await create_notification(
                db, user_id=payment.user_id,
                type=NotificationTypeEnum.PAYMENT_SUCCESS,
                title="To'lov muvaffaqiyatli!",
                body=f"{payment.amount:,} so'm to'lov qabul qilindi.",
            )

            user = (await db.execute(
                select(User).where(User.id == payment.user_id)
            )).scalar_one_or_none()

            if user:
                await notify_payment_success(user.tg_id, shop_name, payment.amount)

        method_name = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
        await admin_new_payment(payment.amount, shop_name, method_name)

    except Exception as e:
        logger.exception("Payment success handler error: %s", e)
