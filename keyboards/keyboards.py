from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from locales import ru, en


def get_texts(lang: str):
    return ru.TEXTS if lang == 'ru' else en.TEXTS


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        ]
    ])


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = get_texts(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["rules_btn"], callback_data="show_rules")],
    ])


def rules_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = get_texts(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["agree_btn"], callback_data="agree_rules")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="main_menu")],
    ])


def back_keyboard(lang: str, callback: str = "main_menu") -> InlineKeyboardMarkup:
    t = get_texts(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["back_btn"], callback_data=callback)],
    ])


def check_payment_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = get_texts(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["check_payment_btn"], callback_data="check_payment")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="main_menu")],
    ])


def admin_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    t = get_texts(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика / Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(text=t["set_amount_btn"], callback_data="admin_set_amount")],
        [InlineKeyboardButton(text=t["set_wallet_btn"], callback_data="admin_set_wallet")],
        [InlineKeyboardButton(text=t["set_ad_btn"], callback_data="admin_set_ad")],
        [InlineKeyboardButton(text=t["broadcast_btn"], callback_data="admin_broadcast")],
        [InlineKeyboardButton(text=t["queue_view_btn"], callback_data="admin_queue")],
        [InlineKeyboardButton(text=t["donate_now_btn"], callback_data="admin_donate_now")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="main_menu")],
    ])


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад / Back", callback_data="admin_panel")],
    ])


def admin_donate_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить / Confirm", callback_data="admin_donate_confirm")],
        [InlineKeyboardButton(text="🔙 Назад / Back", callback_data="admin_panel")],
    ])
