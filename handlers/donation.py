import uuid
import aiohttp
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database import (
    get_user, set_user_wallet, get_user_wallet,
    get_queue_wallets, get_admin_wallet,
    get_donation_amount, create_payment, get_paid_count,
    add_to_queue, is_in_queue, get_user_queue_position,
    queue_count, set_user_status, confirm_payment
)
from keyboards.keyboards import (
    back_keyboard, check_payment_keyboard, main_menu_keyboard
)
from locales import ru, en
from config import config


def get_texts(lang: str):
    return ru.TEXTS if lang == 'ru' else en.TEXTS


async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    return user['language'] if user else 'ru'


class DonationState(StatesGroup):
    waiting_wallet = State()


async def check_ton_usdt_transaction(from_address: str, to_address: str, amount: float) -> bool:
    """Проверяет прошла ли транзакция USDT Jetton на TON с комментарием DONAT"""
    try:
        # USDT Jetton на TON
        USDT_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
        headers = {"X-API-Key": config.TONCENTER_API_KEY}

        # Получаем Jetton кошелёк пользователя для USDT
        url = f"https://toncenter.com/api/v3/jetton/wallets"
        params = {
            "owner_address": from_address,
            "jetton_address": USDT_MASTER,
            "limit": 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                wallets = data.get("jetton_wallets", [])
                if not wallets:
                    return False
                jetton_wallet = wallets[0]["address"]

            # Получаем транзакции Jetton кошелька
            url2 = f"https://toncenter.com/api/v3/jetton/transfers"
            params2 = {
                "address": jetton_wallet,
                "limit": 50,
                "direction": "out"
            }
            async with session.get(url2, params=params2, headers=headers) as resp2:
                data2 = await resp2.json()
                transfers = data2.get("jetton_transfers", [])

                amount_nano = int(amount * 1_000_000)  # USDT 6 decimals

                for tx in transfers:
                    # Проверяем получателя
                    dest = tx.get("destination", {})
                    if isinstance(dest, dict):
                        dest_addr = dest.get("address", "")
                    else:
                        dest_addr = str(dest)

                    if dest_addr != to_address:
                        continue

                    # Проверяем сумму
                    tx_amount = int(tx.get("amount", 0))
                    if tx_amount < amount_nano:
                        continue

                    # Проверяем комментарий
                    comment = tx.get("comment", "") or ""
                    if "DONAT" in comment.upper():
                        return True

        return False
    except Exception as e:
        print(f"TON check error: {e}")
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

    # Проверка TON адреса
    if not (wallet.startswith("EQ") or wallet.startswith("UQ")) or len(wallet) < 40:
        await message.answer(t["invalid_wallet"])
        return

    await set_user_wallet(user_id, wallet)
    await state.finish()

    queue_wallets = await get_queue_wallets()
    admin_wallet = await get_admin_wallet()

    targets = []
    if admin_wallet:
        targets.append(admin_wallet)
    targets.extend(queue_wallets)
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

    try:
        await call.message.edit_text(t["payment_pending"])
    except Exception:
        pass
    await call.answer()

    user_wallet = await get_user_wallet(user_id)
    if not user_wallet:
        await call.message.answer(t["payment_failed"], reply_markup=check_payment_keyboard(lang))
        return

    queue_wallets = await get_queue_wallets()
    admin_wallet = await get_admin_wallet()
    targets = []
    if admin_wallet:
        targets.append(admin_wallet)
    targets.extend(queue_wallets)
    targets = targets[:5]

    amount = await get_donation_amount()
    confirmed = 0

    for addr in targets:
        ok = await check_ton_usdt_transaction(user_wallet, addr, amount)
        if ok:
            confirmed += 1

    required = len(targets)

    if confirmed >= required and user_wallet:
        removed_user_id = await add_to_queue(user_id, user_wallet)
        await set_user_status(user_id, 'active')
        try:
            await call.message.edit_text(
                t["payment_success"],
                reply_markup=main_menu_keyboard(lang)
            )
        except Exception:
            await call.message.answer(
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
        try:
            await call.message.edit_text(
                t["payment_failed"].format(confirmed=confirmed, required=required),
                reply_markup=check_payment_keyboard(lang)
            )
        except Exception:
            await call.message.answer(
                t["payment_failed"].format(confirmed=confirmed, required=required),
                reply_markup=check_payment_keyboard(lang)
            )


def register_donation(dp: Dispatcher):
    dp.register_callback_query_handler(agree_rules, lambda c: c.data == "agree_rules", state="*")
    dp.register_message_handler(process_wallet, state=DonationState.waiting_wallet)
    dp.register_callback_query_handler(check_payment, lambda c: c.data == "check_payment", state="*")
