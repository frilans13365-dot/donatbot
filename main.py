import json
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.webhook import get_new_configured_app

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
    return web.Response(status=200, text="OK")

async def on_startup(app):
    await bot.set_webhook(f"{BASE_URL}/webhook")
    init_db()

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

def main():
    app = get_new_configured_app(dispatcher=dp, path="/webhook")
    app.router.add_post("/payment-webhook", payment_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=WEBHOOK_PORT)

if __name__ == "__main__":
    main()
