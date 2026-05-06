from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

async def echo_all(message: types.Message, state: FSMContext):
    """Временный обработчик всех сообщений для отладки"""
    current_state = await state.get_state()
    await message.answer(
        f"✅ Сообщение получено!\n\n"
        f"Текст: {message.text}\n"
        f"Состояние: {current_state}\n\n"
        f"Бот работает, но нет обработчика для этого сообщения."
    )

def register_echo(dp: Dispatcher):
    dp.register_message_handler(echo_all, state="*", content_types=types.ContentTypes.ANY)
