import asyncio
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

from config import BOT_TOKEN, BASE_URL, WEBHOOK_PORT, PAYMENTO_WEBHOOK_SECRET
from database import init_db, update_payment_status
from handlers import register_handlers
from payment import verify_webhook_signature

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
register_handlers(dp)

async def payment_webhook(request: web.Request):
    signature = request.headers.get("X-Paymento-Signature", "")
    body = await request.read()
    if not verify_webhook_signature(body, signature):
        return web.Response(status=401, text="Invalid signature")
    
    data = json.loads(body)
    invoice_id = data.get("invoice_id")
    status = data.get("status")
    if status == "paid":
        update_payment_status(invoice_id, "paid")
        # можно отправить уведомление пользователю через bot.send_message
    return web.Response(status=200, text="OK")

async def on_startup(dp):
    await bot.set_webhook(f"{BASE_URL}/webhook")
    init_db()

async def on_shutdown(dp):
    await bot.delete_webhook()
    await bot.session.close()

def main():
    app = web.Application()
    app.router.add_post("/payment-webhook", payment_webhook)

    # Запуск с вебхуком от aiogram
    start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        webhook_url=f"{BASE_URL}/webhook"
    )

if __name__ == "__main__":
    main()
