import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENTO_API_KEY = os.getenv("PAYMENTO_API_KEY")
PAYMENTO_WEBHOOK_SECRET = os.getenv("PAYMENTO_WEBHOOK_SECRET")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8000))

# Константы
PAYMENTO_INVOICE_URL = "https://api.paymento.io/v1/invoice"  # Уточните в документации
