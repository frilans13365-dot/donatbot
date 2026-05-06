import json
from aiohttp import web
from database import confirm_payment


async def payment_webhook(request: web.Request) -> web.Response:
    try:
        body = await request.read()
        data = json.loads(body)
        invoice_id = data.get("invoice_id") or data.get("order_id")
        status = data.get("status")
        if status == "paid" and invoice_id:
            await confirm_payment(invoice_id)
        return web.Response(text="OK")
    except Exception as e:
        print(f"Webhook error: {e}")
        return web.Response(status=500, text="Error")
