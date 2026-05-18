import uuid
import aiohttp
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config
from database import (
    get_user, set_user_wallet, get_user_wallet,
    get_queue_wallets, get_admin_wallet,
    get_donation_amount, create_payment, get_paid_count,
    add_to_queue, is_in_queue, get_user_queue_position,
    queue_count, set_user_status, get_pending_payments, confirm_payment
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


async def check_ton_transaction(sender_wallet: str, target_wallet: str, amount: float) -> bool:
    """
    Проверяет через TON Center API наличие транзакции:
    - от sender_wallet на target_wallet
    - на сумму не меньше amount TON
    - с комментарием DONAT
    За последние 100 транзакций.
    """
    # TON хранит сумму в нановалюте (1 TON = 1_000_000_000 нано)
    amount_nano = int(amount * 1_000_000_000)

    url = "https://toncenter.com/api/v2/getTransactions"
    params = {
        "address": target_wallet,
        "limit": 100,
        "archival": "false",
    }
    headers = {}
    if config.TONCENTER_API_KEY:
        headers["X-API-Key"] = config.TONCENTER_API_KEY

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()

        if not data.get("ok"):
            return False

        transactions = data.get("result", [])
        for tx in transactions:
            in_msg = tx.get("in_msg", {})
            # Проверяем отправителя
            src = in_msg.get("source", "")
            if src.lower() != sender_wallet.lower():
                continue
            # Проверяем сумму
            value = int(in_msg.get("value", 0))
            if value < amount_nano:
                continue
            # Проверяем комментарий
            msg_data = in_msg.get("msg_data", {})
            comment = ""
            if msg_data.get("@type") == "msg.dataText":
                comment = msg_data.get("text", "")
            # Иногда комментарий в decoded_body
            if not comment:
                comment = in_msg.get("message", "")
            if "DONAT" in comment.upper():
                return True

    except Exception:
        return False

    return False


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
    amount = await get_donation_amount()

    await call.message.edit_text(t["payment_pending"])
    await call.answer()

    # Получаем кошелёк отправителя
    sender_wallet = await get_user_wallet(user_id)
    if not sender_wallet:
        await call.message.edit_text(
            t["payment_failed"].format(amount=amount),
            reply_markup=check_payment_keyboard(lang)
        )
        return

    # Проверяем каждый pending-платёж через TON API
    pending = await get_pending_payments(user_id)
    for payment in pending:
        ok = await check_ton_transaction(
            sender_wallet=sender_wallet,
            target_wallet=payment['target_wallet'],
            amount=payment['amount']
        )
        if ok:
            await confirm_payment(payment['invoice_id'])

    # Считаем сколько подтверждено
    paid = await get_paid_count(user_id)
    queue_wallets = await get_queue_wallets()
    admin_wallet = await get_admin_wallet()
    targets = list(queue_wallets)
    if admin_wallet and admin_wallet not in targets:
        targets.append(admin_wallet)
    required = min(len(targets), 5)

    if paid >= required and sender_wallet:
        removed_user_id = await add_to_queue(user_id, sender_wallet)
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
            t["payment_failed"].format(amount=amount),
            reply_markup=check_payment_keyboard(lang)
        )


def register_donation(dp: Dispatcher):
    dp.register_callback_query_handler(agree_rules, lambda c: c.data == "agree_rules", state="*")
    dp.register_message_handler(process_wallet, state=DonationState.waiting_wallet)
    dp.register_callback_query_handler(check_payment, lambda c: c.data == "check_payment", state="*")
