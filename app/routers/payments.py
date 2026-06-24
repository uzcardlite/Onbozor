import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.enums import PaymentMethodEnum, PaymentStatusEnum, NotificationTypeEnum
from app.config import settings
from app.crud import create_payment, get_payment, get_shop, create_notification
from app.schemas.schemas import PaymentInitiate, PaymentOut, PaymentStatusOut
from app.services import payme, click
from app.services.notification import notify_payment_success

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ────────────────── Initiate ──────────────────

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
        db,
        user_id=user.id,
        shop_id=body.shop_id,
        amount=shop.monthly_fee,
        payment_method=body.method,
    )

    if body.method == PaymentMethodEnum.PAYME:
        url = payme.generate_checkout_url(str(payment.id), payment.amount)
    else:
        url = click.generate_payment_url(str(payment.id), payment.amount)

    result = PaymentOut.model_validate(payment)
    result.payment_url = url
    return result


# ────────────────── Status check (polling) ──────────────────

@router.get("/status/{payment_id}", response_model=PaymentStatusOut)
async def check_payment_status(
    payment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi")
    if payment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    return PaymentStatusOut(
        id=payment.id,
        status=payment.status,
        amount=payment.amount,
        payment_method=payment.payment_method,
    )


# ────────────────── Payme Merchant API ──────────────────

@router.post("/payme/webhook")
async def payme_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        logger.error("Payme webhook: invalid JSON body")
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}

    auth_header = request.headers.get("Authorization")
    result = await payme.handle_request(body, auth_header, db)

    method = body.get("method", "")
    if method == "PerformTransaction" and "result" in result:
        await _on_payme_success(body, db)

    logger.info("Payme webhook response: method=%s result_keys=%s", method, list(result.keys()))
    return result


async def _on_payme_success(body: dict, db: AsyncSession):
    try:
        order_id = body.get("params", {}).get("account", {}).get("order_id")
        if not order_id:
            return
        payment = await get_payment(db, order_id)
        if not payment or payment.status != PaymentStatusEnum.PAID:
            return

        shop = await get_shop(db, payment.shop_id) if payment.shop_id else None
        shop_name = shop.name if shop else "Noma'lum"

        await create_notification(
            db,
            user_id=payment.user_id,
            type=NotificationTypeEnum.PAYMENT_SUCCESS,
            title="To'lov muvaffaqiyatli!",
            body=f"🏪 {shop_name} uchun {payment.amount:,} so'm to'lov qabul qilindi. Obuna 30 kunga faollashtirildi.",
        )

        from app.models.user import User as UserModel
        result = await db.execute(select(UserModel).where(UserModel.id == payment.user_id))
        user = result.scalar_one_or_none()
        if user:
            await notify_payment_success(user.tg_id, shop_name, payment.amount)
    except Exception as e:
        logger.exception("Post-payme notification error: %s", e)


# ────────────────── Click Webhook ──────────────────

@router.post("/click/webhook")
async def click_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        params = await request.json()
    else:
        form = await request.form()
        params = {k: v for k, v in form.items()}

    result = await click.handle_webhook(params, db)

    action = params.get("action", "")
    if str(action) == "1" and result.get("error") == 0:
        await _on_click_success(params, db)

    logger.info("Click webhook response: action=%s error=%s", action, result.get("error"))
    return result


async def _on_click_success(params: dict, db: AsyncSession):
    try:
        merchant_trans_id = params.get("merchant_trans_id")
        if not merchant_trans_id:
            return
        payment = await get_payment(db, merchant_trans_id)
        if not payment or payment.status != PaymentStatusEnum.PAID:
            return

        shop = await get_shop(db, payment.shop_id) if payment.shop_id else None
        shop_name = shop.name if shop else "Noma'lum"

        await create_notification(
            db,
            user_id=payment.user_id,
            type=NotificationTypeEnum.PAYMENT_SUCCESS,
            title="To'lov muvaffaqiyatli!",
            body=f"🏪 {shop_name} uchun {payment.amount:,} so'm to'lov qabul qilindi. Obuna 30 kunga faollashtirildi.",
        )

        from app.models.user import User as UserModel
        result = await db.execute(select(UserModel).where(UserModel.id == payment.user_id))
        user = result.scalar_one_or_none()
        if user:
            await notify_payment_success(user.tg_id, shop_name, payment.amount)
    except Exception as e:
        logger.exception("Post-click notification error: %s", e)
