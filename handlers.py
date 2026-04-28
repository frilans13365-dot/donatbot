from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import save_user, set_user_wallet, is_donation_confirmed, save_payment, update_payment_status
from payment import create_invoice
from config import BASE_URL

router = Router()

# Машина состояний для сбора кошелька
class DonationState(StatesGroup):
    waiting_for_wallet = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    save_user(user_id, username)
    if is_donation_confirmed(user_id):
        await message.answer("✅ Вы уже подтвердили донат! Доступ открыт.")
        # Здесь вызовите вашу логику "пропустить юзера"
    else:
        await message.answer(
            "Привет! Для доступа нужно сделать донат.\n\n"
            "Отправьте ваш криптокошелёк (например, USDT (TRC-20) адрес):"
        )
        await state.set_state(DonationState.waiting_for_wallet)

@router.message(DonationState.waiting_for_wallet)
async def get_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()
    user_id = message.from_user.id
    set_user_wallet(user_id, wallet)

    # Создаём счёт в Paymento на фиксированную сумму (например, 10 USDT)
    try:
        invoice = await create_invoice(amount=10.0, currency="USDT", order_id=str(user_id))
        # invoice должен содержать pay_url
        pay_url = invoice["payment_url"]
        invoice_id = invoice["id"]
        save_payment(user_id, invoice_id, "10.0")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Оплатить донат", url=pay_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")]
        ])
        await message.answer(
            f"Кошелёк {wallet} сохранён. Перейдите по ссылке для оплаты 10 USDT:\n{pay_url}\n\n"
            "После оплаты нажмите «Проверить оплату».",
            reply_markup=kb
        )
    except Exception as e:
        await message.answer(f"Ошибка создания платежа: {e}")
    finally:
        await state.clear()

@router.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    if is_donation_confirmed(user_id):
        await callback.message.edit_text("✅ Донат подтверждён! Доступ открыт.")
        # Здесь ваша логика пропуска
    else:
        await callback.answer("Платёж пока не найден. Подождите немного или оплатите.", show_alert=True)
