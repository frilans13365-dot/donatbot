import aiohttp
import json
import hmac
import hashlib
from config import PAYMENTO_API_KEY, PAYMENTO_WEBHOOK_SECRET, BASE_URL

async def create_invoice(amount: float, currency: str = "USDT", order_id: str = None) -> dict:
    url = "https://api.paymento.io/v1/invoice"
    headers = {
        "Authorization": f"Bearer {PAYMENTO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": amount,
        "currency": currency,
        "order_id": order_id,
        "webhook_url": f"{BASE_URL}/payment-webhook"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                text = await resp.text()
                raise Exception(f"Paymento API error: {resp.status} {text}")

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    return True
