import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Payment
from app.models.shop import Shop
from app.models.enums import PaymentStatusEnum

logger = logging.getLogger(__name__)

CLICK_ERRORS = {
    0: "Success",
    -1: "SIGN CHECK FAILED!",
    -2: "Incorrect parameter amount",
    -4: "Already paid",
    -5: "Order does not exist",
    -6: "Transaction does not exist",
    -8: "Error in request from click",
    -9: "Transaction cancelled",
}


def generate_payment_url(payment_id: str, amount_uzs: int) -> str:
    return (
        f"https://my.click.uz/services/pay"
        f"?service_id={settings.CLICK_SERVICE_ID}"
        f"&merchant_id={settings.CLICK_MERCHANT_ID}"
        f"&amount={amount_uzs}"
        f"&transaction_param={payment_id}"
        f"&return_url={settings.FRONTEND_URL}/payment-result"
    )


def _verify_sign(params: dict) -> bool:
    sign_string = params.get("sign_string", "")
    expected = hashlib.md5(
        "{click_trans_id}{service_id}{secret}{merchant_trans_id}{amount}{action}{sign_time}".format(
            click_trans_id=params.get("click_trans_id", ""),
            service_id=params.get("service_id", ""),
            secret=settings.CLICK_SECRET_KEY,
            merchant_trans_id=params.get("merchant_trans_id", ""),
            amount=params.get("amount", ""),
            action=params.get("action", ""),
            sign_time=params.get("sign_time", ""),
        ).encode()
    ).hexdigest()
    return sign_string == expected


async def handle_webhook(params: dict, db: AsyncSession) -> dict:
    action = int(params.get("action", -1))
    click_trans_id = params.get("click_trans_id", "")
    merchant_trans_id = params.get("merchant_trans_id", "")
    amount = params.get("amount", "0")

    logger.info("Click webhook: action=%s click_trans_id=%s merchant_trans_id=%s amount=%s",
                action, click_trans_id, merchant_trans_id, amount)

    base_response = {
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
    }

    if not _verify_sign(params):
        logger.warning("Click sign verification failed")
        return {**base_response, "error": -1, "error_note": CLICK_ERRORS[-1]}

    result = await db.execute(select(Payment).where(Payment.id == merchant_trans_id))
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning("Click payment not found: %s", merchant_trans_id)
        return {**base_response, "error": -5, "error_note": CLICK_ERRORS[-5]}

    if payment.status == PaymentStatusEnum.CANCELLED:
        return {**base_response, "error": -9, "error_note": CLICK_ERRORS[-9]}

    if payment.status == PaymentStatusEnum.PAID:
        return {**base_response, "error": -4, "error_note": CLICK_ERRORS[-4]}

    amount_float = float(amount)
    if abs(amount_float - payment.amount) > 1:
        logger.warning("Click amount mismatch: expected=%s got=%s", payment.amount, amount)
        return {**base_response, "error": -2, "error_note": CLICK_ERRORS[-2]}

    if action == 0:
        return await _prepare(payment, params, db, base_response)
    elif action == 1:
        return await _complete(payment, params, db, base_response)
    else:
        return {**base_response, "error": -8, "error_note": CLICK_ERRORS[-8]}


async def _prepare(payment: Payment, params: dict, db: AsyncSession, base: dict) -> dict:
    payment.transaction_id = str(params.get("click_trans_id", ""))
    payment.payload = {
        **(payment.payload or {}),
        "click_prepare_time": datetime.now(timezone.utc).isoformat(),
        "click_trans_id": params.get("click_trans_id"),
    }
    await db.flush()

    logger.info("Click prepare OK for payment %s", payment.id)

    return {
        **base,
        "merchant_prepare_id": str(payment.id),
        "error": 0,
        "error_note": CLICK_ERRORS[0],
    }


async def _complete(payment: Payment, params: dict, db: AsyncSession, base: dict) -> dict:
    error_code = int(params.get("error", 0))

    if error_code < 0:
        payment.status = PaymentStatusEnum.FAILED
        payment.payload = {
            **(payment.payload or {}),
            "click_error": error_code,
            "click_complete_time": datetime.now(timezone.utc).isoformat(),
        }
        await db.flush()
        logger.warning("Click complete with error %s for payment %s", error_code, payment.id)
        return {**base, "error": -9, "error_note": CLICK_ERRORS[-9]}

    payment.status = PaymentStatusEnum.PAID
    payment.payload = {
        **(payment.payload or {}),
        "click_complete_time": datetime.now(timezone.utc).isoformat(),
        "click_trans_id": params.get("click_trans_id"),
    }
    await db.flush()

    await _activate_shop(db, payment)

    logger.info("Click payment %s completed successfully", payment.id)

    return {
        **base,
        "merchant_confirm_id": str(payment.id),
        "error": 0,
        "error_note": CLICK_ERRORS[0],
    }


async def _activate_shop(db: AsyncSession, payment: Payment):
    if not payment.shop_id:
        return
    result = await db.execute(select(Shop).where(Shop.id == payment.shop_id))
    shop = result.scalar_one_or_none()
    if shop:
        shop.is_active = True
        shop.subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
        await db.flush()
        logger.info("Shop %s activated via Click until %s", shop.id, shop.subscription_expires)
