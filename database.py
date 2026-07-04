import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            file_id TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            upload_date TIMESTAMP,
            uploaded_by INTEGER,
            views INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            tags TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP,
            last_active TIMESTAMP,
            total_requests INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_title TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            request_date TIMESTAMP,
            completed_date TIMESTAMP,
            notes TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns(
            user_id INTEGER PRIMARY KEY,
            last_message TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_id INTEGER,
            movie_id INTEGER,
            expire_time TIMESTAMP,
            UNIQUE(chat_id, message_id)
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_title ON movies(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_tags ON movies(tags)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_status ON requests(status)")
        self.conn.commit()

    def add_movie(self, title, description, file_id, file_size=0, uploaded_by=0, tags="") -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO movies(title, description, file_id, file_size, upload_date, uploaded_by, tags)
        VALUES(?,?,?,?,?,?,?)
        """, (title, description, file_id, file_size or 0, datetime.now().isoformat(), uploaded_by, tags))
        self.conn.commit()
        return cursor.lastrowid

    def movie_exists(self, title: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM movies WHERE LOWER(title)=LOWER(?)", (title,))
        return cursor.fetchone()

    def search_movies(self, query: str, limit: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        q = f"%{query}%"
        cursor.execute("""
        SELECT id, title, description, file_id, file_size, views, downloads
        FROM movies
        WHERE title LIKE ? OR tags LIKE ?
        ORDER BY views DESC, downloads DESC, id DESC
        LIMIT ?
        """, (q, q, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_movie(self, movie_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT id, title, description, file_id, file_size, views, downloads
        FROM movies WHERE id=?
        """, (movie_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def increment_views(self, movie_id: int):
        self.conn.execute("UPDATE movies SET views=views+1 WHERE id=?", (movie_id,))
        self.conn.commit()

    def increment_downloads(self, movie_id: int):
        self.conn.execute("UPDATE movies SET downloads=downloads+1 WHERE id=?", (movie_id,))
        self.conn.commit()

    def add_or_update_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        now = datetime.now().isoformat()
        self.conn.execute("""
        INSERT INTO users(user_id, username, first_name, last_name, join_date, last_active)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            last_active=excluded.last_active
        """, (user_id, username, first_name, last_name, now, now))
        self.conn.commit()

    def increment_user_requests(self, user_id: int):
        self.conn.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (user_id,))
        self.conn.commit()

    def add_request(self, user_id: int, movie_title: str, description: str = "") -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO requests(user_id, movie_title, description, request_date)
        VALUES(?,?,?,?)
        """, (user_id, movie_title, description, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def get_pending_requests(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT r.id, r.user_id, r.movie_title, r.description, r.status, r.request_date,
               u.username, u.first_name
        FROM requests r
        LEFT JOIN users u ON r.user_id = u.user_id
        WHERE r.status='pending'
        ORDER BY r.request_date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def update_request_status(self, request_id: int, status: str, notes: str = ""):
        completed = datetime.now().isoformat() if status in ("completed", "rejected") else None
        self.conn.execute("""
        UPDATE requests SET status=?, completed_date=?, notes=? WHERE id=?
        """, (status, completed, notes, request_id))
        self.conn.commit()

    def check_cooldown(self, user_id: int, seconds: int = 60) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_message FROM cooldowns WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        now = datetime.now()
        if row:
            last = datetime.fromisoformat(row["last_message"])
            if now - last < timedelta(seconds=seconds):
                return False
        self.conn.execute("INSERT OR REPLACE INTO cooldowns(user_id, last_message) VALUES(?,?)", (user_id, now.isoformat()))
        self.conn.commit()
        return True

    def cooldown_remaining(self, user_id: int, seconds: int = 60) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_message FROM cooldowns WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return 0
        last = datetime.fromisoformat(row["last_message"])
        remaining = seconds - int((datetime.now() - last).total_seconds())
        return max(0, remaining)

    def add_message(self, chat_id: int, message_id: int, movie_id=None, seconds: int = 300):
        expire = datetime.now() + timedelta(seconds=seconds)
        self.conn.execute("""
        INSERT OR REPLACE INTO messages(chat_id, message_id, movie_id, expire_time)
        VALUES(?,?,?,?)
        """, (chat_id, message_id, movie_id, expire.isoformat()))
        self.conn.commit()

    def get_expired_messages(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT chat_id, message_id, movie_id FROM messages WHERE expire_time<?", (datetime.now().isoformat(),))
        return cursor.fetchall()

    def remove_message(self, chat_id: int, message_id: int):
        self.conn.execute("DELETE FROM messages WHERE chat_id=? AND message_id=?", (chat_id, message_id))
        self.conn.commit()

    def delete_movie(self, movie_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def close(self):
        self.conn.close()
