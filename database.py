import aiosqlite
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telestream.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable Write-Ahead Logging for high concurrent read/write throughput
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS media_links (
                id TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_name TEXT,
                file_size INTEGER DEFAULT 0,
                mime_type TEXT,
                duration INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_media_links_created ON media_links(created_at);")
        await db.commit()

async def save_media(link_id: str, chat_id: int, message_id: int, file_id: str,
                     file_name: str, file_size: int, mime_type: str, duration: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO media_links 
            (id, chat_id, message_id, file_id, file_name, file_size, mime_type, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (link_id, chat_id, message_id, file_id, file_name, file_size, mime_type, duration))
        await db.commit()

async def get_media(link_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM media_links WHERE id = ?", (link_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
