import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)


async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 To'lov uchun web app dan foydalaning.\n\n"
        "Profil → Do'kon ochish → To'lov"
    )


def get_payment_handlers():
    return [
        CallbackQueryHandler(payment_method_selected, pattern=r"^payment:"),
    ]
