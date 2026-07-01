import sqlite3


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imdb_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                year TEXT,
                poster TEXT,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5))
            '''
        )

init_db()