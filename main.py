import asyncio
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


async def setup():
    await init_db()
    await bot.delete_webhook()
    await bot.set_webhook(f"{config.BASE_URL}/webhook")
    print(f"✅ Webhook set: {config.BASE_URL}/webhook")


async def on_shutdown(app):
    await bot.delete_webhook()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup())

    app = get_new_configured_app(dispatcher=dp, path="/webhook")
    app.router.add_post("/payment-webhook", payment_webhook)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=config.WEBHOOK_PORT, loop=loop)


if __name__ == "__main__":
    main()
