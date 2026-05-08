import asyncpg
from datetime import datetime, date
from typing import Optional, List
from config import config
from utils.crypto import encrypt, decrypt

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            config.DATABASE_URL,
            statement_cache_size=0
        )
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                wallet TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                wallet_encrypted TEXT NOT NULL,
                position INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                target_wallet_encrypted TEXT,
                invoice_id TEXT UNIQUE,
                amount FLOAT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Миграции
        await conn.execute("""
            ALTER TABLE payments 
            ADD COLUMN IF NOT EXISTS target_wallet_encrypted TEXT
        """)
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'ru'
        """)
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS wallet TEXT
        """)
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'new'
        """)
        # Исправляем тип колонки amount если она TEXT
        await conn.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='payments' AND column_name='amount'
                    AND data_type='text'
                ) THEN
                    ALTER TABLE payments ALTER COLUMN amount TYPE FLOAT USING amount::float;
                END IF;
            END$$
        """)
        await conn.execute("""
            INSERT INTO settings (key, value) VALUES
                ('donation_amount', '10'),
                ('admin_wallet', ''),
                ('ad_text', '')
            ON CONFLICT (key) DO NOTHING
        """)


async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)


async def create_user(user_id: int, language: str = 'ru'):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, language) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, language
        )


async def set_user_language(user_id: int, language: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, language) VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO UPDATE SET language=$2",
            user_id, language
        )


async def set_user_wallet(user_id: int, wallet: str):
    pool = await get_pool()
    encrypted = encrypt(wallet)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET wallet=$1 WHERE user_id=$2",
            encrypted, user_id
        )


async def get_user_wallet(user_id: int) -> Optional[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT wallet FROM users WHERE user_id=$1", user_id)
        if row and row['wallet']:
            return decrypt(row['wallet'])
        return None


async def set_user_status(user_id: int, status: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET status=$1 WHERE user_id=$2",
            status, user_id
        )


async def count_users() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users")


async def count_users_today() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at::date = $1",
            date.today()
        )


async def all_user_ids() -> List[int]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users")
        return [r['user_id'] for r in rows]


async def get_queue() -> List[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM queue ORDER BY position ASC")
        result = []
        for r in rows:
            result.append({
                'id': r['id'],
                'user_id': r['user_id'],
                'wallet': decrypt(r['wallet_encrypted']),
                'position': r['position'],
                'joined_at': r['joined_at']
            })
        return result


async def get_queue_wallets() -> List[str]:
    queue = await get_queue()
    return [item['wallet'] for item in queue]


async def add_to_queue(user_id: int, wallet: str):
    pool = await get_pool()
    encrypted = encrypt(wallet)
    removed_user_id = None
    async with pool.acquire() as conn:
        async with conn.transaction():
            rows = await conn.fetch("SELECT * FROM queue ORDER BY position ASC")
            if len(rows) >= 4:
                removed = next((r for r in rows if r['position'] == 2), None)
                if removed:
                    removed_user_id = removed['user_id']
                await conn.execute("DELETE FROM queue WHERE position=2")
                await conn.execute(
                    "UPDATE queue SET position=position-1 WHERE position IN (3,4,5)"
                )
            await conn.execute(
                "INSERT INTO queue (user_id, wallet_encrypted, position) VALUES ($1, $2, 5)",
                user_id, encrypted
            )
    return removed_user_id


async def get_user_queue_position(user_id: int) -> Optional[int]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT position FROM queue WHERE user_id=$1", user_id
        )
        return row['position'] if row else None


async def queue_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM queue")


async def is_in_queue(user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM queue WHERE user_id=$1", user_id)
        return row is not None


async def create_payment(user_id: int, target_wallet: str, invoice_id: str, amount: float):
    pool = await get_pool()
    encrypted = encrypt(target_wallet)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO payments (user_id, target_wallet_encrypted, invoice_id, amount) "
            "VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
            user_id, encrypted, invoice_id, float(amount)
        )


async def confirm_payment(invoice_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE payments SET status='paid' WHERE invoice_id=$1", invoice_id
        )


async def get_paid_count(user_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM payments WHERE user_id=$1 AND status='paid'",
            user_id
        )


async def get_setting(key: str) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM settings WHERE key=$1", key)
        return row['value'] if row else ""


async def set_setting(key: str, value: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO settings (key, value) VALUES ($1, $2) "
            "ON CONFLICT (key) DO UPDATE SET value=$2",
            key, value
        )


async def get_donation_amount() -> float:
    val = await get_setting('donation_amount')
    return float(val) if val else 10.0


async def get_admin_wallet() -> str:
    return await get_setting('admin_wallet')


async def get_ad_text() -> str:
    return await get_setting('ad_text')
