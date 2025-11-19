"""Database manager responsible for connections and schema initialization."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, List

import aiosqlite


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS active_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stars_count INTEGER NOT NULL,
    ton_amount REAL NOT NULL,
    wallet_address TEXT NOT NULL,
    payment_charge_id TEXT,
    status TEXT DEFAULT 'pending',
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS completed_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tx_hash TEXT UNIQUE NOT NULL,
    stars_count INTEGER NOT NULL,
    ton_amount REAL NOT NULL,
    wallet_address TEXT NOT NULL,
    payment_charge_id TEXT,
    status TEXT DEFAULT 'completed',
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS user_states (
    user_id INTEGER PRIMARY KEY,
    stage TEXT NOT NULL DEFAULT 'idle',
    stars_count INTEGER,
    ton_amount REAL,
    wallet_address TEXT,
    payment_charge_id TEXT,
    state_data TEXT,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    primary_wallet_address TEXT,
    language TEXT DEFAULT 'ar',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    creator_id INTEGER NOT NULL,
    payer_user_id INTEGER,
    wallet_address TEXT NOT NULL,
    reason TEXT,
    stars_count INTEGER NOT NULL,
    usd_value REAL NOT NULL,
    ton_value REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users (user_id),
    FOREIGN KEY (payer_user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS invoice_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    payer_id INTEGER NOT NULL,
    stars_paid INTEGER NOT NULL,
    ton_value REAL NOT NULL,
    payment_charge_id TEXT,
    tx_hash TEXT,
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE,
    FOREIGN KEY (payer_id) REFERENCES users (user_id)
);

CREATE INDEX IF NOT EXISTS idx_active_orders_user ON active_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_transactions_user ON completed_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_code ON invoices(code);
CREATE INDEX IF NOT EXISTS idx_invoices_creator ON invoices(creator_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice ON invoice_payments(invoice_id);
CREATE TRIGGER IF NOT EXISTS trg_user_states_updated
AFTER UPDATE ON user_states
FOR EACH ROW
BEGIN
    UPDATE user_states SET updated = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
END;
"""


class DatabaseManager:
    """Manage SQLite schema initialization and connection lifecycle."""

    def __init__(self, db_path: str):
        self._db_path = Path(db_path)
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self._db_path) as conn:
                await conn.executescript(SCHEMA_SQL)
                await self._apply_user_state_migrations(conn)
                await conn.commit()
            self._initialized = True

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[aiosqlite.Connection]:
        """Yield a configured SQLite connection."""

        await self.initialize()
        conn = await aiosqlite.connect(self._db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            await conn.close()

    async def _apply_user_state_migrations(self, conn: aiosqlite.Connection) -> None:
        required_columns = {
            "stage": "TEXT NOT NULL DEFAULT 'idle'",
            "stars_count": "INTEGER",
            "ton_amount": "REAL",
            "wallet_address": "TEXT",
            "payment_charge_id": "TEXT",
        }
        existing_columns = await self._get_table_columns(conn, "user_states")

        for column, ddl in required_columns.items():
            if column not in existing_columns:
                await conn.execute(f"ALTER TABLE user_states ADD COLUMN {column} {ddl}")
                existing_columns.append(column)

        if "stage" in existing_columns and "state" in existing_columns:
            await conn.execute(
                "UPDATE user_states SET stage = state "
                "WHERE state IS NOT NULL AND state != ''"
            )
        if "stage" in existing_columns:
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_states_stage ON user_states(stage)"
            )

    async def _get_table_columns(
        self, conn: aiosqlite.Connection, table_name: str
    ) -> List[str]:
        columns: List[str] = []
        async with conn.execute(f"PRAGMA table_info({table_name})") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                columns.append(row[1])
        return columns


__all__ = ["DatabaseManager"]
