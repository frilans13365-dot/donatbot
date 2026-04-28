import asyncio
import json
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, BASE_URL, WEBHOOK_PORT, PAYMENTO_WEBHOOK_SECRET
from database import init_db, update_payment_status
from handlers import router
from payment import verify_webhook_signature

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

# Эндпоинт для вебхуков Paymento
async def payment_webhook(request: web.Request):
    """Принимает уведомления от Paymento об успешной оплате"""
    signature = request.headers.get("X-Paymento-Signature", "")
    body = await request.read()
    if not verify_webhook_signature(body, signature):
        return web.Response(status=401, text="Invalid signature")
    
    data = json.loads(body)
    invoice_id = data.get("invoice_id")
    status = data.get("status")  # 'paid', 'expired', etc.
    if status == "paid":
        update_payment_status(invoice_id, "paid")
        # Здесь можно добавить уведомление пользователю через bot.send_message
    return web.Response(status=200, text="OK")

async def on_startup():
    """Инициализация БД и установка вебхука для Telegram"""
    init_db()
    await bot.set_webhook(f"{BASE_URL}/webhook")
    print(f"Webhook set to {BASE_URL}/webhook")

async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

def main():
    app = web.Application()
    # Telegram webhook
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    # Paymento webhook
    app.router.add_post("/payment-webhook", payment_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=WEBHOOK_PORT)

if __name__ == "__main__":
    main()
