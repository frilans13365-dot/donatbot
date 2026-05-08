from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config
from database import (
    count_users, count_users_today, get_donation_amount,
    get_queue, queue_count, set_setting, all_user_ids,
    get_admin_wallet
)
from keyboards.keyboards import admin_keyboard, admin_back_keyboard


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


class AdminState(StatesGroup):
    waiting_amount = State()
    waiting_wallet = State()
    waiting_ad = State()
    waiting_broadcast = State()


async def cmd_admin(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.finish()
    await message.answer("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())


async def admin_panel(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Access denied", show_alert=True)
        return
    await state.finish()
    try:
        await call.message.edit_text("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())
    except Exception:
        await call.message.answer("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())
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
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


async def admin_queue(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    queue = await get_queue()
    admin_wallet = await get_admin_wallet()
    lines = []
    if admin_wallet:
        lines.append(f"1. 👑 Admin: <code>{admin_wallet[:16]}...</code>")
    for item in queue:
        wallet = item['wallet']
        lines.append(f"{item['position'] + 1}. <code>{wallet[:16]}...</code>")
    text = "📋 <b>Очередь:</b>\n\n" + "\n".join(lines) if lines else "📋 Очередь пуста"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_keyboard())
    await call.answer()


async def admin_set_amount(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.edit_text("💰 Введите новую сумму доната в USDT:", reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer("💰 Введите новую сумму доната в USDT:", reply_markup=admin_back_keyboard())
    await state.set_state(AdminState.waiting_amount)
    await call.answer()


async def process_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.strip())
        await set_setting('donation_amount', str(amount))
        await state.finish()
        await message.answer(f"✅ Сумма: <b>{amount} USDT</b>", reply_markup=admin_back_keyboard())
    except ValueError:
        await message.answer("❌ Введите число!")


async def admin_set_wallet(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.edit_text("👛 Введите адрес кошелька:", reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer("👛 Введите адрес кошелька:", reply_markup=admin_back_keyboard())
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
    try:
        await call.message.edit_text("📢 Введите текст рекламы (или /skip чтобы убрать):", reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer("📢 Введите текст рекламы (или /skip чтобы убрать):", reply_markup=admin_back_keyboard())
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
    try:
        await call.message.edit_text("📣 Введите текст рассылки:", reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.answer("📣 Введите текст рассылки:", reply_markup=admin_back_keyboard())
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
    await message.answer(f"✅ Рассылка: {sent}", reply_markup=admin_back_keyboard())


def register_admin(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"], state="*")
    dp.register_callback_query_handler(admin_panel, lambda c: c.data == "admin_panel", state="*")
    dp.register_callback_query_handler(admin_stats, lambda c: c.data == "admin_stats", state="*")
    dp.register_callback_query_handler(admin_queue, lambda c: c.data == "admin_queue", state="*")
    dp.register_callback_query_handler(admin_set_amount, lambda c: c.data == "admin_set_amount", state="*")
    dp.register_message_handler(process_amount, state=AdminState.waiting_amount)
    dp.register_callback_query_handler(admin_set_wallet, lambda c: c.data == "admin_set_wallet", state="*")
    dp.register_message_handler(process_wallet, state=AdminState.waiting_wallet)
    dp.register_callback_query_handler(admin_set_ad, lambda c: c.data == "admin_set_ad", state="*")
    dp.register_message_handler(process_ad, state=AdminState.waiting_ad)
    dp.register_callback_query_handler(admin_broadcast, lambda c: c.data == "admin_broadcast", state="*")
    dp.register_message_handler(process_broadcast, state=AdminState.waiting_broadcast)
