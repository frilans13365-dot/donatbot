import time
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config
from database import (
    count_users, count_users_today, get_donation_amount,
    get_queue, queue_count, set_setting, all_user_ids,
    get_admin_wallet, add_to_queue
)
from keyboards.keyboards import (
    admin_keyboard, admin_back_keyboard, admin_donate_confirm_keyboard
)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


class AdminState(StatesGroup):
    waiting_amount = State()
    waiting_wallet = State()
    waiting_ad = State()
    waiting_broadcast = State()
    waiting_add_wallet = State()


async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())


async def admin_panel(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Access denied", show_alert=True)
        return
    await call.message.edit_text("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())
    await call.answer()


async def admin_stats(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    total = await count_users()
    today = await count_users_today()
    amount = await get_donation_amount()
    in_queue = await queue_count()
    text = (
        f"📊 <b>Статистика / Statistics</b>\n\n"
        f"👥 Всего / Total: <b>{total}</b>\n"
        f"📅 За сутки / Today: <b>{today}</b>\n"
        f"💰 Сумма / Amount: <b>{amount} USDT</b>\n"
        f"📋 В очереди / Queue: <b>{in_queue}</b>"
    )
    await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    await call.answer()


async def admin_queue(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    queue = await get_queue()
    lines = []
    for item in queue:
        wallet = item['wallet']
        lines.append(f"{item['position']}. <code>{wallet[:16]}...</code>")
    text = "📋 <b>Очередь / Queue:</b>\n\n" + "\n".join(lines) if lines else "📋 Очередь пуста / Queue is empty"
    await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    await call.answer()


async def admin_add_to_queue(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    in_queue = await queue_count()
    await call.message.edit_text(
        f"➕ В очереди сейчас: <b>{in_queue}/5</b>\n\n"
        f"Введите USDT-адрес для добавления в очередь:",
        reply_markup=admin_back_keyboard()
    )
    await state.set_state(AdminState.waiting_add_wallet)
    await call.answer()


async def process_add_to_queue(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    wallet = message.text.strip()
    if len(wallet) < 10:
        await message.answer("❌ Неверный адрес. Попробуйте снова.")
        return
    await state.finish()
    fake_user_id = -int(time.time() % 100000)
    await add_to_queue(fake_user_id, wallet)
    in_queue = await queue_count()
    await message.answer(
        f"✅ Адрес добавлен в очередь!\n"
        f"<code>{wallet}</code>\n\n"
        f"В очереди: <b>{in_queue}/5</b>",
        reply_markup=admin_back_keyboard()
    )


async def admin_set_amount(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "💰 Введите новую сумму доната в USDT:",
        reply_markup=admin_back_keyboard()
    )
    await state.set_state(AdminState.waiting_amount)
    await call.answer()


async def process_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.strip())
        await set_setting('donation_amount', str(amount))
        await state.finish()
        await message.answer(
            f"✅ Сумма: <b>{amount} USDT</b>",
            reply_markup=admin_back_keyboard()
        )
    except ValueError:
        await message.answer("❌ Введите число!")


async def admin_set_wallet(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "👛 Введите адрес кошелька:",
        reply_markup=admin_back_keyboard()
    )
    await state.set_state(AdminState.waiting_wallet)
    await call.answer()


async def process_wallet(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting('admin_wallet', message.text.strip())
    await state.finish()
    await message.answer("✅ Кошелёк обновлён.", reply_markup=admin_back_keyboard())


async def admin_set_ad(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "📢 Введите текст рекламы (или /skip чтобы убрать):",
        reply_markup=admin_back_keyboard()
    )
    await state.set_state(AdminState.waiting_ad)
    await call.answer()


async def process_ad(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = "" if message.text.strip() == "/skip" else message.text.strip()
    await set_setting('ad_text', text)
    await state.finish()
    await message.answer("✅ Реклама обновлена.", reply_markup=admin_back_keyboard())


async def admin_broadcast(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "📣 Введите текст рассылки:",
        reply_markup=admin_back_keyboard()
    )
    await state.set_state(AdminState.waiting_broadcast)
    await call.answer()


async def process_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.finish()
    user_ids = await all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            pass
    await message.answer(
        f"✅ Рассылка: {sent}",
        reply_markup=admin_back_keyboard()
    )


async def admin_donate_now(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    queue = await get_queue()
    if not queue:
        await call.message.edit_text(
            "❌ Очередь пуста.",
            reply_markup=admin_back_keyboard()
        )
        await call.answer()
        return

    amount = await get_donation_amount()
    addr_text = ""
    for item in queue:
        addr_text += f"{item['position']}. <code>{item['wallet']}</code>\n"

    await call.message.edit_text(
        f"💸 <b>Донат вне очереди</b>\n\n"
        f"Сумма: <b>{amount} USDT</b>\n"
        f"Комментарий: <b>DONAT</b>\n\n"
        f"Адреса:\n{addr_text}\n\n"
        f"После отправки нажмите Подтвердить.",
        reply_markup=admin_donate_confirm_keyboard()
    )
    await call.answer()


async def admin_donate_confirm(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "✅ Донат засчитан! Спасибо за участие.",
        reply_markup=admin_back_keyboard()
    )
    await call.answer()


def register_admin(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"], state="*")
    dp.register_callback_query_handler(admin_panel, lambda c: c.data == "admin_panel", state="*")
    dp.register_callback_query_handler(admin_stats, lambda c: c.data == "admin_stats", state="*")
    dp.register_callback_query_handler(admin_queue, lambda c: c.data == "admin_queue", state="*")
    dp.register_callback_query_handler(admin_add_to_queue, lambda c: c.data == "admin_add_to_queue", state="*")
    dp.register_message_handler(process_add_to_queue, state=AdminState.waiting_add_wallet)
    dp.register_callback_query_handler(admin_set_amount, lambda c: c.data == "admin_set_amount", state="*")
    dp.register_message_handler(process_amount, state=AdminState.waiting_amount)
    dp.register_callback_query_handler(admin_set_wallet, lambda c: c.data == "admin_set_wallet", state="*")
    dp.register_message_handler(process_wallet, state=AdminState.waiting_wallet)
    dp.register_callback_query_handler(admin_set_ad, lambda c: c.data == "admin_set_ad", state="*")
    dp.register_message_handler(process_ad, state=AdminState.waiting_ad)
    dp.register_callback_query_handler(admin_broadcast, lambda c: c.data == "admin_broadcast", state="*")
    dp.register_message_handler(process_broadcast, state=AdminState.waiting_broadcast)
    dp.register_callback_query_handler(admin_donate_now, lambda c: c.data == "admin_donate_now", state="*")
    dp.register_callback_query_handler(admin_donate_confirm, lambda c: c.data == "admin_donate_confirm", state="*")
