import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any

DB_NAME = "bot.db"

def get_db():
    """Возвращает соединение с БД и курсор (контекстный менеджер)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицы, если их нет"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                wallet_address TEXT,
                donation_confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                invoice_id TEXT UNIQUE,
                amount TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_user(user_id: int, username: str = None, wallet_address: str = None):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, wallet_address) VALUES (?, ?, ?)",
            (user_id, username, wallet_address)
        )
        conn.commit()

def set_user_wallet(user_id: int, wallet: str):
    with get_db() as conn:
        conn.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet, user_id))
        conn.commit()

def set_donation_confirmed(user_id: int, confirmed: int = 1):
    with get_db() as conn:
        conn.execute("UPDATE users SET donation_confirmed = ? WHERE user_id = ?", (confirmed, user_id))
        conn.commit()

def is_donation_confirmed(user_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute("SELECT donation_confirmed FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return bool(row and row["donation_confirmed"])

def save_payment(user_id: int, invoice_id: str, amount: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO payments (user_id, invoice_id, amount, status) VALUES (?, ?, ?, ?)",
            (user_id, invoice_id, amount, "pending")
        )
        conn.commit()

def update_payment_status(invoice_id: str, status: str):
    with get_db() as conn:
        conn.execute("UPDATE payments SET status = ? WHERE invoice_id = ?", (status, invoice_id))
        conn.commit()
        # Если статус 'paid' – обновляем флаг у пользователя
        if status == "paid":
            row = conn.execute("SELECT user_id FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchone()
            if row:
                set_donation_confirmed(row["user_id"], 1)
