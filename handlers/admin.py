from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config
from database import (
    count_users, count_users_today, get_donation_amount,
    get_queue, queue_count, set_setting, all_user_ids,
    get_admin_wallet
)
from keyboards.keyboards import admin_keyboard, admin_back_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


class AdminState(StatesGroup):
    waiting_amount = State()
    waiting_wallet = State()
    waiting_ad = State()
    waiting_broadcast = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Access denied", show_alert=True)
        return
    await call.message.edit_text("🔧 <b>Admin Panel</b>", reply_markup=admin_keyboard())
    await call.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
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


@router.callback_query(F.data == "admin_queue")
async def admin_queue(call: CallbackQuery):
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
    text = "📋 <b>Очередь / Queue:</b>\n\n" + "\n".join(lines) if lines else "📋 Очередь пуста / Queue is empty"
    await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    await call.answer()


@router.callback_query(F.data == "admin_set_amount")
async def admin_set_amount(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("💰 Введите новую сумму доната в USDT:", reply_markup=admin_back_keyboard())
    await state.set_state(AdminState.waiting_amount)
    await call.answer()


@router.message(AdminState.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.strip())
        await set_setting('donation_amount', str(amount))
        await state.clear()
        await message.answer(f"✅ Сумма обновлена: <b>{amount} USDT</b>", reply_markup=admin_back_keyboard())
    except ValueError:
        await message.answer("❌ Введите число!")


@router.callback_query(F.data == "admin_set_wallet")
async def admin_set_wallet(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("👛 Введите адрес кошелька администратора:", reply_markup=admin_back_keyboard())
    await state.set_state(AdminState.waiting_wallet)
    await call.answer()


@router.message(AdminState.waiting_wallet)
async def process_wallet(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting('admin_wallet', message.text.strip())
    await state.clear()
    await message.answer("✅ Кошелёк обновлён.", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin_set_ad")
async def admin_set_ad(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("📢 Введите текст рекламы (или /skip чтобы убрать):", reply_markup=admin_back_keyboard())
    await state.set_state(AdminState.waiting_ad)
    await call.answer()


@router.message(AdminState.waiting_ad)
async def process_ad(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = "" if message.text.strip() == "/skip" else message.text.strip()
    await set_setting('ad_text', text)
    await state.clear()
    await message.answer("✅ Реклама обновлена.", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("📣 Введите текст рассылки:", reply_markup=admin_back_keyboard())
    await state.set_state(AdminState.waiting_broadcast)
    await call.answer()


@router.message(AdminState.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent}", reply_markup=admin_back_keyboard())
