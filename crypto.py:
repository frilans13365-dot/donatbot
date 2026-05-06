import base64
import hashlib
from cryptography.fernet import Fernet
from config import config


def _get_key() -> bytes:
    raw = config.ENCRYPTION_KEY or "default-change-me-in-production"
    key = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(key)


_fernet = Fernet(_get_key())


def encrypt(text: str) -> str:
    if not text:
        return text
    return _fernet.encrypt(text.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext
