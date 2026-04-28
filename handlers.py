from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from database import save_user, set_user_wallet, is_donation_confirmed, save_payment
from payment import create_invoice
from config import BASE_URL

class DonationState(StatesGroup):
    waiting_for_wallet = State()

async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    save_user(user_id, username)
    if is_donation_confirmed(user_id):
        await message.answer("✅ Вы уже подтвердили донат! Доступ открыт.")
    else:
        await message.answer(
            "Привет! Для доступа нужно сделать донат.\n\n"
            "Отправьте ваш криптокошелёк (например, USDT (TRC-20) адрес):"
        )
        await state.set_state(DonationState.waiting_for_wallet)

async def get_wallet(message: types.Message, state: FSMContext):
    wallet = message.text.strip()
    user_id = message.from_user.id
    set_user_wallet(user_id, wallet)

    try:
        invoice = await create_invoice(amount=10.0, currency="USDT", order_id=str(user_id))
        pay_url = invoice["payment_url"]
        invoice_id = invoice["id"]
        save_payment(user_id, invoice_id, "10.0")

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text="💸 Оплатить донат", url=pay_url))
        kb.add(types.InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment"))

        await message.answer(
            f"Кошелёк {wallet} сохранён. Перейдите по ссылке для оплаты 10 USDT:\n{pay_url}\n\n"
            "После оплаты нажмите «Проверить оплату».",
            reply_markup=kb
        )
    except Exception as e:
        await message.answer(f"Ошибка создания платежа: {e}")
    finally:
        await state.finish()

async def check_payment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if is_donation_confirmed(user_id):
        await callback_query.message.edit_text("✅ Донат подтверждён! Доступ открыт.")
    else:
        await callback_query.answer("Платёж пока не найден. Подождите немного или оплатите.", show_alert=True)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"], state="*")
    dp.register_message_handler(get_wallet, state=DonationState.waiting_for_wallet)
    dp.register_callback_query_handler(check_payment, Text(equals="check_payment"), state="*")
