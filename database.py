import asyncpg
import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                wallet_address TEXT,
                donation_confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                invoice_id TEXT UNIQUE,
                amount TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

async def save_user(user_id: int, username: str = None, wallet_address: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, wallet_address)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET username = $2, wallet_address = $3
        """, user_id, username, wallet_address)

async def set_user_wallet(user_id: int, wallet: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET wallet_address = $1 WHERE user_id = $2",
            wallet, user_id
        )

async def set_donation_confirmed(user_id: int, confirmed: int = 1):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET donation_confirmed = $1 WHERE user_id = $2",
            confirmed, user_id
        )

async def is_donation_confirmed(user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT donation_confirmed FROM users WHERE user_id = $1",
            user_id
        )
        return bool(row and row["donation_confirmed"])

async def save_payment(user_id: int, invoice_id: str, amount: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO payments (user_id, invoice_id, amount, status) VALUES ($1, $2, $3, 'pending')",
            user_id, invoice_id, amount
        )

async def update_payment_status(invoice_id: str, status: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE payments SET status = $1 WHERE invoice_id = $2",
            status, invoice_id
        )
        if status == "paid":
            row = await conn.fetchrow(
                "SELECT user_id FROM payments WHERE invoice_id = $1",
                invoice_id
            )
            if row:
                await set_donation_confirmed(row["user_id"], 1)
