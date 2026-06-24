from fastapi import APIRouter, Request, HTTPException
from app.database import async_session
from app.services.payment_service import confirm_payment
from app.services.shop_service import activate_shop_after_payment
from app.config import settings

router = APIRouter(prefix="/api/webhooks")


@router.post("/payme")
async def payme_webhook(request: Request):
    data = await request.json()
    method = data.get("method")

    if method == "CheckPerformTransaction":
        payment_id = data.get("params", {}).get("account", {}).get("order_id")
        return {"result": {"allow": True}}

    if method == "CreateTransaction":
        return {"result": {"create_time": 0, "transaction": "0", "state": 1}}

    if method == "PerformTransaction":
        payment_id = data.get("params", {}).get("account", {}).get("order_id")
        transaction_id = data.get("params", {}).get("id", "")

        async with async_session() as session:
            payment = await confirm_payment(session, int(payment_id), transaction_id)
            if payment:
                await activate_shop_after_payment(session, payment.shop_id)

        return {"result": {"state": 2}}

    return {"error": {"code": -32601, "message": "Method not found"}}


@router.post("/click/prepare")
async def click_prepare(request: Request):
    data = await request.form()
    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "merchant_prepare_id": data.get("merchant_trans_id"),
        "error": 0,
        "error_note": "Success",
    }


@router.post("/click/complete")
async def click_complete(request: Request):
    data = await request.form()
    error = int(data.get("error", -1))

    if error == 0:
        payment_id = data.get("merchant_trans_id")
        transaction_id = data.get("click_trans_id")

        async with async_session() as session:
            payment = await confirm_payment(session, int(payment_id), str(transaction_id))
            if payment:
                await activate_shop_after_payment(session, payment.shop_id)

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "error": 0,
        "error_note": "Success",
    }
