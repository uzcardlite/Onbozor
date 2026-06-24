from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.config import settings


async def create_payment(session: AsyncSession, user_id: int, shop_id: int, provider: str) -> Payment:
    payment = Payment(
        user_id=user_id,
        shop_id=shop_id,
        amount=settings.SHOP_MONTHLY_PRICE,
        provider=provider,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


def generate_payme_url(payment: Payment) -> str:
    import base64
    params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={payment.id};a={payment.amount * 100}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"


def generate_click_url(payment: Payment) -> str:
    return (
        f"https://my.click.uz/services/pay"
        f"?service_id={settings.CLICK_MERCHANT_ID}"
        f"&merchant_id={settings.CLICK_MERCHANT_ID}"
        f"&amount={payment.amount}"
        f"&transaction_param={payment.id}"
    )


async def confirm_payment(session: AsyncSession, payment_id: int, transaction_id: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment:
        payment.status = "completed"
        payment.transaction_id = transaction_id
        await session.commit()
    return payment
