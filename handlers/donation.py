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
    await call.answer()


async def process_wallet(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    t = get_texts(lang)

    wallet = message.text.strip()
    if len(wallet) < 10:
        await message.answer(t["invalid_wallet"])
        return

    await set_user_wallet(user_id, wallet)
    await state.finish()

    queue_wallets = await get_queue_wallets()
    admin_wallet = await get_admin_wallet()

    targets = list(queue_wallets)
    if admin_wallet and admin_wallet not in targets:
        targets.append(admin_wallet)
    targets = targets[:5]

    if not targets:
        await message.answer("⚠️ Система не настроена. Обратитесь к администратору.")
        return

    amount = await get_donation_amount()
    addr_text = ""
    for i, addr in enumerate(targets, 1):
        addr_text += f"{i}. <code>{addr}</code>\n"

    for addr in targets:
        order_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        await create_payment(user_id, addr, order_id, amount)

    await message.answer(
        t["donate_instructions"].format(amount=amount, addresses=addr_text),
        reply_markup=check_payment_keyboard(lang)
    )


async def check_payment(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    t = get_texts(lang)

    await call.message.edit_text(t["payment_pending"])
    await call.answer()

    paid = await get_paid_count(user_id)
    wallet = await get_user_wallet(user_id)

    queue_wallets = await get_queue_wallets()
    admin_wallet = await get_admin_wallet()
    targets = list(queue_wallets)
    if admin_wallet and admin_wallet not in targets:
        targets.append(admin_wallet)
    required = min(len(targets), 5)

    if paid >= required and wallet:
        removed_user_id = await add_to_queue(user_id, wallet)
        await set_user_status(user_id, 'active')
        await call.message.edit_text(
            t["payment_success"],
            reply_markup=main_menu_keyboard(lang)
        )
        if removed_user_id:
            try:
                removed_lang = await get_lang(removed_user_id)
                removed_t = get_texts(removed_lang)
                await call.bot.send_message(removed_user_id, removed_t["graduated"])
            except Exception:
                pass
    else:
        await call.message.edit_text(
            t["payment_failed"],
            reply_markup=check_payment_keyboard(lang)
        )


def register_donation(dp: Dispatcher):
    dp.register_callback_query_handler(agree_rules, lambda c: c.data == "agree_rules", state="*")
    dp.register_message_handler(process_wallet, state=DonationState.waiting_wallet)
    dp.register_callback_query_handler(check_payment, lambda c: c.data == "check_payment", state="*")
