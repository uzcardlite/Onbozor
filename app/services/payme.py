import base64
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Payment
from app.models.shop import Shop
from app.models.enums import PaymentStatusEnum

logger = logging.getLogger(__name__)

PAYME_ERRORS = {
    "order_not_found":    {"code": -31050, "message": {"uz": "Buyurtma topilmadi", "en": "Order not found"}},
    "already_paid":       {"code": -31051, "message": {"uz": "Buyurtma allaqachon to'langan", "en": "Already paid"}},
    "wrong_amount":       {"code": -31001, "message": {"uz": "Noto'g'ri summa", "en": "Wrong amount"}},
    "cant_perform":       {"code": -31008, "message": {"uz": "Amalni bajarib bo'lmaydi", "en": "Cannot perform"}},
    "transaction_not_found": {"code": -31003, "message": {"uz": "Tranzaksiya topilmadi", "en": "Transaction not found"}},
    "auth_error":         {"code": -32504, "message": {"uz": "Avtorizatsiya xatosi", "en": "Auth error"}},
    "method_not_found":   {"code": -32601, "message": {"uz": "Metod topilmadi", "en": "Method not found"}},
}


def generate_checkout_url(payment_id: str, amount_uzs: int) -> str:
    params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={payment_id};a={amount_uzs * 100}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"


def verify_auth(auth_header: str | None) -> bool:
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header[6:]).decode()
        login, password = decoded.split(":", 1)
        return login == "Paycom" and password == settings.PAYME_KEY
    except Exception:
        return False


def _error(rpc_id, err_key: str):
    e = PAYME_ERRORS[err_key]
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": e["code"], "message": e["message"]}}


def _result(rpc_id, data: dict):
    return {"jsonrpc": "2.0", "id": rpc_id, "result": data}


def _ts():
    return int(time.time() * 1000)


async def handle_request(body: dict, auth_header: str | None, db: AsyncSession) -> dict:
    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    logger.info("Payme request: method=%s params=%s", method, params)

    if not verify_auth(auth_header):
        logger.warning("Payme auth failed")
        return _error(rpc_id, "auth_error")

    handler = {
        "CheckPerformTransaction": _check_perform,
        "CreateTransaction":      _create_transaction,
        "PerformTransaction":     _perform_transaction,
        "CancelTransaction":      _cancel_transaction,
        "CheckTransaction":       _check_transaction,
        "GetStatement":           _get_statement,
    }.get(method)

    if not handler:
        return _error(rpc_id, "method_not_found")

    try:
        result = await handler(params, db)
        return _result(rpc_id, result) if isinstance(result, dict) and "code" not in result else result if isinstance(result, dict) and "error" in result else _result(rpc_id, result)
    except PaymeError as e:
        logger.error("Payme error: %s", e.key)
        return _error(rpc_id, e.key)
    except Exception as e:
        logger.exception("Payme unexpected error: %s", e)
        return _error(rpc_id, "cant_perform")


class PaymeError(Exception):
    def __init__(self, key: str):
        self.key = key


async def _get_payment(db: AsyncSession, order_id) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == str(order_id)))
    payment = result.scalar_one_or_none()
    if not payment:
        raise PaymeError("order_not_found")
    return payment


async def _check_perform(params: dict, db: AsyncSession) -> dict:
    account = params.get("account", {})
    order_id = account.get("order_id")
    amount = params.get("amount", 0)

    payment = await _get_payment(db, order_id)

    if payment.status == PaymentStatusEnum.PAID:
        raise PaymeError("already_paid")

    if payment.amount * 100 != amount:
        raise PaymeError("wrong_amount")

    return {"allow": True}


async def _create_transaction(params: dict, db: AsyncSession) -> dict:
    account = params.get("account", {})
    order_id = account.get("order_id")
    payme_id = params.get("id")
    amount = params.get("amount", 0)
    create_time = params.get("time", _ts())

    payment = await _get_payment(db, order_id)

    if payment.status == PaymentStatusEnum.PAID:
        raise PaymeError("already_paid")

    if payment.amount * 100 != amount:
        raise PaymeError("wrong_amount")

    if payment.status == PaymentStatusEnum.PENDING:
        payment.transaction_id = payme_id
        payment.payload = {
            **(payment.payload or {}),
            "payme_create_time": create_time,
            "payme_state": 1,
        }
        await db.flush()

    return {
        "create_time": payment.payload.get("payme_create_time", create_time),
        "transaction": str(payment.id),
        "state": 1,
    }


async def _perform_transaction(params: dict, db: AsyncSession) -> dict:
    payme_id = params.get("id")
    payment = await _find_by_payme_id(db, payme_id)

    perform_time = _ts()

    if payment.status == PaymentStatusEnum.PAID:
        return {
            "state": 2,
            "perform_time": payment.payload.get("payme_perform_time", perform_time),
            "transaction": str(payment.id),
        }

    if payment.status == PaymentStatusEnum.CANCELLED:
        raise PaymeError("cant_perform")

    payment.status = PaymentStatusEnum.PAID
    payment.payload = {
        **(payment.payload or {}),
        "payme_state": 2,
        "payme_perform_time": perform_time,
    }
    await db.flush()

    await _activate_shop(db, payment)

    return {
        "state": 2,
        "perform_time": perform_time,
        "transaction": str(payment.id),
    }


async def _cancel_transaction(params: dict, db: AsyncSession) -> dict:
    payme_id = params.get("id")
    reason = params.get("reason")
    payment = await _find_by_payme_id(db, payme_id)

    cancel_time = _ts()

    if payment.status == PaymentStatusEnum.PAID:
        payment.status = PaymentStatusEnum.CANCELLED
        payment.payload = {
            **(payment.payload or {}),
            "payme_state": -2,
            "payme_cancel_time": cancel_time,
            "payme_reason": reason,
        }
        await db.flush()
        await _deactivate_shop(db, payment)
        state = -2
    elif payment.status in (PaymentStatusEnum.PENDING, PaymentStatusEnum.FAILED):
        payment.status = PaymentStatusEnum.CANCELLED
        payment.payload = {
            **(payment.payload or {}),
            "payme_state": -1,
            "payme_cancel_time": cancel_time,
            "payme_reason": reason,
        }
        await db.flush()
        state = -1
    else:
        state = payment.payload.get("payme_state", -1)

    return {
        "state": state,
        "cancel_time": cancel_time,
        "transaction": str(payment.id),
    }


async def _check_transaction(params: dict, db: AsyncSession) -> dict:
    payme_id = params.get("id")
    payment = await _find_by_payme_id(db, payme_id)

    state = payment.payload.get("payme_state", 1)
    return {
        "create_time": payment.payload.get("payme_create_time", 0),
        "perform_time": payment.payload.get("payme_perform_time", 0),
        "cancel_time": payment.payload.get("payme_cancel_time", 0),
        "transaction": str(payment.id),
        "state": state,
        "reason": payment.payload.get("payme_reason"),
    }


async def _get_statement(params: dict, db: AsyncSession) -> dict:
    from_ts = params.get("from", 0)
    to_ts = params.get("to", _ts())

    from_dt = datetime.fromtimestamp(from_ts / 1000, tz=timezone.utc)
    to_dt = datetime.fromtimestamp(to_ts / 1000, tz=timezone.utc)

    result = await db.execute(
        select(Payment)
        .where(
            Payment.transaction_id.isnot(None),
            Payment.created_at >= from_dt,
            Payment.created_at <= to_dt,
            Payment.payload["payme_state"].isnot(None),
        )
        .order_by(Payment.created_at)
    )
    payments = result.scalars().all()

    transactions = []
    for p in payments:
        transactions.append({
            "id": p.transaction_id,
            "time": p.payload.get("payme_create_time", 0),
            "amount": p.amount * 100,
            "account": {"order_id": str(p.id)},
            "create_time": p.payload.get("payme_create_time", 0),
            "perform_time": p.payload.get("payme_perform_time", 0),
            "cancel_time": p.payload.get("payme_cancel_time", 0),
            "transaction": str(p.id),
            "state": p.payload.get("payme_state", 1),
            "reason": p.payload.get("payme_reason"),
        })

    return {"transactions": transactions}


async def _find_by_payme_id(db: AsyncSession, payme_id: str) -> Payment:
    result = await db.execute(select(Payment).where(Payment.transaction_id == payme_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise PaymeError("transaction_not_found")
    return payment


async def _activate_shop(db: AsyncSession, payment: Payment):
    if not payment.shop_id:
        return
    result = await db.execute(select(Shop).where(Shop.id == payment.shop_id))
    shop = result.scalar_one_or_none()
    if shop:
        shop.is_active = True
        shop.subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
        await db.flush()
        logger.info("Shop %s activated until %s", shop.id, shop.subscription_expires)


async def _deactivate_shop(db: AsyncSession, payment: Payment):
    if not payment.shop_id:
        return
    result = await db.execute(select(Shop).where(Shop.id == payment.shop_id))
    shop = result.scalar_one_or_none()
    if shop:
        shop.is_active = False
        await db.flush()
        logger.info("Shop %s deactivated due to payment cancellation", shop.id)
