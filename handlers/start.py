from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from database import (
    get_user, create_user, set_user_language,
    get_donation_amount, get_ad_text,
    is_in_queue, get_user_queue_position, queue_count
)
from keyboards.keyboards import language_keyboard, main_menu_keyboard, rules_keyboard
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


async def cmd_start(message: types.Message):
    user = await get_user(message.from_user.id)
if not user or 'language' not in user:
        await message.answer(
            "🌐 Выберите язык / Choose language:",
            reply_markup=language_keyboard()
        )
    else:
        lang = user['language']
        t = get_texts(lang)
        ad = await get_ad_text()
        ad_block = f"\n📢 {ad}" if ad else ""
        await message.answer(
            t["welcome"].format(ad=ad_block),
            reply_markup=main_menu_keyboard(lang)
        )


async def set_language(call: types.CallbackQuery):
    lang = call.data.replace("lang_", "")
    await set_user_language(call.from_user.id, lang)
    await create_user(call.from_user.id, lang)
    t = get_texts(lang)
    ad = await get_ad_text()
    ad_block = f"\n📢 {ad}" if ad else ""
    await call.message.edit_text(
        t["welcome"].format(ad=ad_block),
        reply_markup=main_menu_keyboard(lang)
    )
    await call.answer()


async def main_menu(call: types.CallbackQuery):
    lang = await get_lang(call.from_user.id)
    t = get_texts(lang)
    ad = await get_ad_text()
    ad_block = f"\n📢 {ad}" if ad else ""
    await call.message.edit_text(
        t["welcome"].format(ad=ad_block),
        reply_markup=main_menu_keyboard(lang)
    )
    await call.answer()


async def show_rules(call: types.CallbackQuery):
    lang = await get_lang(call.from_user.id)
    t = get_texts(lang)
    amount = await get_donation_amount()
    await call.message.edit_text(
        t["rules"].format(amount=amount),
        reply_markup=rules_keyboard(lang)
    )
    await call.answer()


def register_start(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"], state="*")
    dp.register_callback_query_handler(set_language, lambda c: c.data.startswith("lang_"), state="*")
    dp.register_callback_query_handler(main_menu, lambda c: c.data == "main_menu", state="*")
    dp.register_callback_query_handler(show_rules, lambda c: c.data == "show_rules", state="*")
