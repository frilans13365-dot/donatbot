import uuid
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database import (
    get_user, set_user_wallet, get_user_wallet,
    get_queue_wallets, get_admin_wallet,
    get_donation_amount, create_payment, get_paid_count,
    add_to_queue, is_in_queue, get_user_queue_position,
    queue_count, set_user_status
)
from keyboards.keyboards import (
    back_keyboard, check_payment_keyboard, main_menu_keyboard
)
from locales import ru, en


def get_texts(lang: str):
    return ru.TEXTS if lang == 'ru' else en.TEXTS


async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    if not user:
        return 'ru'
    try:
        return user['language'] or 'ru'
    except (KeyError, TypeError):
        return 'ru'


class DonationState(StatesGroup):
    waiting_wallet = State()


async def agree_rules(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    t = get_texts(lang)

    if await is_in_queue(user_id):
        pos = await get_user_queue_position(user_id)
        total = await queue_count()
        await call.message.edit_text(
            t["already_in_queue"] + "\n\n" + t["queue_position"].format(position=pos, total=total),
            reply_markup=main_menu_keyboard(lang)
        )
        await call.answer()
        return

    await call.message.edit_text(
        t["enter_wallet"],
        reply_markup=back_keyboard(lang, "show_rules")
    )
    await state.set_state(DonationState.waiting_wallet)
    await call.answer
