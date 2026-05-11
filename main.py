import asyncio
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.utils.exceptions import CancelHandler

from config import config
from database import init_db
from handlers.start import register_start
from handlers.donation import register_donation, background_checker
from handlers.admin import register_admin
from handlers.webhook import payment_webhook

bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class AntiDuplicateMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self._processed = {}

    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        call_id = call.id
        now = time.time()

        if call_id in self._processed:
            await call.answer()
            raise CancelHandler()

        if call.message:
            msg_time = call.message.date.timestamp()
            if now - msg_time > 3600:
                await call.answer(
                    "⚠️ Используйте свежие кнопки. Напишите /start",
                    show_alert=True
                )
                raise CancelHandler()

        self._processed[call_id] = now

        if len(self._processed) > 1000:
            cutoff = now - 60
            self._processed = {
                k: v for k, v in self._processed.items()
                if v > cutoff
            }


dp.middleware.setup(AntiDuplicateMiddleware())

register_start(dp)
register_donation(dp)
register_admin(dp)


async def health_check(request):
    return web.Response(text="OK")


async def on_startup(app):
    await init_db()
    print("✅ DB initialized")
    asyncio.ensure_future(background_checker(bot))
    print("✅ Background checker started")


def main():
    app = get_new_configured_app(dispatcher=dp, path="/webhook")
    app.router.add_post("/payment-webhook", payment_webhook)
    app.router.add_get("/", health_check)
    app.on_startup.append(on_startup)
    web.run_app(app, host="0.0.0.0", port=config.WEBHOOK_PORT)


if __name__ == "__main__":
    main()
