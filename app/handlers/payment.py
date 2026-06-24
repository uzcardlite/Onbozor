from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.database import async_session
from app.services.user_service import get_user
from app.services.payment_service import create_payment, generate_payme_url, generate_click_url
from app.keyboards.main import payment_method_keyboard


async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    provider = parts[1]
    shop_id = int(parts[2])

    async with async_session() as session:
        user = await get_user(session, update.effective_user.id)
        if not user:
            return

        payment = await create_payment(session, user.id, shop_id, provider)

    if provider == "payme":
        url = generate_payme_url(payment)
    else:
        url = generate_click_url(payment)

    await query.edit_message_text(
        f"💳 To'lov #{payment.id}\n\n"
        f"Summa: {payment.amount:,} so'm\n"
        f"Provayder: {provider.upper()}\n\n"
        "Quyidagi tugmani bosib to'lovni amalga oshiring:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💳 {provider.upper()} orqali to'lash", url=url)]
        ]),
    )


def get_payment_handlers():
    return [
        CallbackQueryHandler(payment_method_selected, pattern=r"^payment:(payme|click):\d+$"),
    ]
