import aiosqlite

DB_NAME = "prediction_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_username TEXT,
                session_time TEXT,
                status TEXT DEFAULT 'Active'
            )
        """)
        await db.commit()

async def add_channel_db(user_id: int, channel: str, session_time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO channels (user_id, channel_username, session_time) VALUES (?, ?, ?)",
            (user_id, channel, session_time)
        )
        await db.commit()

async def get_user_channels(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT channel_username, session_time, status FROM channels WHERE user_id = ?", (user_id,))
        return await cursor.fetchall()

async def get_all_configured_channels():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT channel_username, session_time FROM channels WHERE status = 'Active'")
        return await cursor.fetchall()
        
