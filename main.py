import asyncpg
import os

async def fix_database():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(2) DEFAULT \'ru\'')
        await conn.close()
        print("✅ Database fixed: language column added")
    except Exception as e:
        print(f"Fix error: {e}")

# Добавьте эту строку перед запуском бота
# asyncio.run(fix_database())import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.webhook import get_new_configured_app

from config import config
from database import init_db
from handlers.start import register_start
from handlers.donation import register_donation
from handlers.admin import register_admin
from handlers.webhook import payment_webhook

bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

register_start(dp)
register_donation(dp)
register_admin(dp)


async def on_startup(app):
    await bot.set_webhook(f"{config.BASE_URL}/webhook")
    await init_db()


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


def main():
    app = get_new_configured_app(dispatcher=dp, path="/webhook")
    app.router.add_post("/payment-webhook", payment_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=config.WEBHOOK_PORT)


if __name__ == "__main__":
    main()@dp.message_handler()
async def echo_all(message: types.Message):
    await message.answer("✅ Бот работает! Ваше сообщение получено, но нет обработчика для этой команды.")
