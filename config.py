import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = field(default_factory=list)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    TONCENTER_API_KEY: str = os.getenv("TONCENTER_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8000"))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    DEFAULT_DONATION_AMOUNT: float = float(os.getenv("DEFAULT_DONATION_AMOUNT", "10"))
    SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "@admin")

    def __post_init__(self):
        raw = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in raw.split(",") if x.strip()]


config = Config()
