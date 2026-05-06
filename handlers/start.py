from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from database import (
    get_user, create_user, set_user_language,
    get_donation_amount, get_ad_text,
    is_in_queue, get_user_queue_position, queue_count
)
from keyboards.keyboards import language_keyboard, main_menu_keyboard, rules_keyboard
from locales import ru, en

router = Router()


def get_texts(lang: str):
    return ru.TEXTS if lang == 'ru' else en.TEXTS


async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    return user['language'] if user else 'ru'


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
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


@router.callback_query(F.data.startswith("lang_"))
async def set_language(call: CallbackQuery):
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


@router.callback_query(F.data == "main_menu")
async def main_menu(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    t = get_texts(lang)
    ad = await get_ad_text()
    ad_block = f"\n📢 {ad}" if ad else ""
    await call.message.edit_text(
        t["welcome"].format(ad=ad_block),
        reply_markup=main_menu_keyboard(lang)
    )
    await call.answer()


@router.callback_query(F.data == "show_rules")
async def show_rules(call: CallbackQuery):
    lang = await get_lang(call.from_user.id)
    t = get_texts(lang)
    amount = await get_donation_amount()
    await call.message.edit_text(
        t["rules"].format(amount=amount),
        reply_markup=rules_keyboard(lang)
    )
    await call.answer()
