import aiohttp
import json
import hmac
import hashlib
from config import PAYMENTO_API_KEY, PAYMENTO_WEBHOOK_SECRET

async def create_invoice(amount: float, currency: str = "USDT", order_id: str = None) -> dict:
    """
    Создаёт платёжную ссылку через Paymento.
    Документация: https://docs.paymento.io
    """
    url = "https://api.paymento.io/v1/invoice"  # уточните актуальный эндпоинт
    headers = {
        "Authorization": f"Bearer {PAYMENTO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": amount,
        "currency": currency,
        "order_id": order_id,  # можно передать user_id
        "webhook_url": f"{BASE_URL}/payment-webhook"  # ваш вебхук
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                text = await resp.text()
                raise Exception(f"Paymento API error: {resp.status} {text}")

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Проверяет подпись вебхука (HMAC-SHA256)"""
    expected = hmac.new(
        PAYMENTO_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
