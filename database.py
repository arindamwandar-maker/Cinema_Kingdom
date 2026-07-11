import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class Database:

    def __init__(self, db_path: str = "bot.db"):
        db_path = db_path or "bot.db"

        parent = os.path.dirname(
            os.path.abspath(db_path)
        )

        if parent:
            os.makedirs(
                parent,
                exist_ok=True
            )

        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=30
        )

        self.conn.row_factory = sqlite3.Row

        self.conn.execute(
            "PRAGMA foreign_keys=ON"
        )

        self.conn.execute(
            "PRAGMA journal_mode=WAL"
        )

        self.conn.execute(
            "PRAGMA busy_timeout=30000"
        )

        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # =========================
        # MOVIES TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            file_id TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            upload_date TEXT,
            uploaded_by INTEGER,
            views INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            tags TEXT,
            source_chat_id INTEGER,
            source_message_id INTEGER,
            status TEXT DEFAULT 'active',
            deleted_at TEXT,
            deleted_by INTEGER
        )
        """)

        # Safe migration for older databases

        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(movies)"
            ).fetchall()
        }

        if "source_chat_id" not in columns:
            cursor.execute(
                "ALTER TABLE movies ADD COLUMN source_chat_id INTEGER"
            )

        if "source_message_id" not in columns:
            cursor.execute(
                "ALTER TABLE movies ADD COLUMN source_message_id INTEGER"
            )

        if "status" not in columns:
            cursor.execute(
                "ALTER TABLE movies ADD COLUMN status TEXT DEFAULT 'active'"
            )

        if "deleted_at" not in columns:
            cursor.execute(
                "ALTER TABLE movies ADD COLUMN deleted_at TEXT"
            )

        if "deleted_by" not in columns:
            cursor.execute(
                "ALTER TABLE movies ADD COLUMN deleted_by INTEGER"
            )

        # Old movies active করে রাখবে

        cursor.execute("""
        UPDATE movies
        SET status='active'
        WHERE status IS NULL
           OR TRIM(status)=''
        """)

        # =========================
        # USERS TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TEXT,
            last_active TEXT,
            total_requests INTEGER DEFAULT 0
        )
        """)

        # =========================
        # REQUESTS TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_title TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            request_date TEXT,
            completed_date TEXT,
            notes TEXT
        )
        """)

        # =========================
        # COOLDOWN TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns(
            user_id INTEGER PRIMARY KEY,
            last_message TEXT
        )
        """)

        # =========================
        # AUTO DELETE TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_id INTEGER,
            movie_id INTEGER,
            expire_time TEXT,
            UNIQUE(chat_id, message_id)
        )
        """)

        # =========================
        # BOT ADMIN TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_admins(
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at TEXT
        )
        """)

        # =========================
        # DOWNLOAD TOKEN TABLE
        # =========================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS download_tokens(
            token TEXT PRIMARY KEY,
            movie_id INTEGER NOT NULL,
            expire_time TEXT NOT NULL,
            used INTEGER DEFAULT 0
        )
        """)

        # =========================
        # INDEXES
        # =========================

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_movie_title
        ON movies(title)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_movie_tags
        ON movies(tags)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_movie_status
        ON movies(status)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_request_status
        ON requests(status)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_token_expire
        ON download_tokens(expire_time)
        """)

        self.conn.commit()

    # =========================
    # ADMIN METHODS
    # =========================

    def seed_admins(
        self,
        admin_ids: List[int],
        super_admin_id: int = 0
    ):
        for admin_id in admin_ids:
            self.add_admin(
                admin_id,
                super_admin_id or admin_id
            )

    def add_admin(
        self,
        user_id: int,
        added_by: int = 0
    ) -> bool:

        self.conn.execute(
            """
            INSERT OR IGNORE INTO bot_admins(
                user_id,
                added_by,
                added_at
            )
            VALUES(?,?,?)
            """,
            (
                user_id,
                added_by,
                datetime.now().isoformat()
            )
        )

        self.conn.commit()

        return True

    def remove_admin(
        self,
        user_id: int
    ) -> bool:

        cursor = self.conn.cursor()

        cursor.execute(
            """
            DELETE FROM bot_admins
            WHERE user_id=?
            """,
            (user_id,)
        )

        self.conn.commit()

        return cursor.rowcount > 0

    def get_admin_ids(self) -> List[int]:

        rows = self.conn.execute(
            "SELECT user_id FROM bot_admins"
        ).fetchall()

        return [
            int(row[0])
            for row in rows
        ]

    def is_admin(
        self,
        user_id: int,
        config_admin_ids=None
    ) -> bool:

        if config_admin_ids and user_id in config_admin_ids:
            return True

        row = self.conn.execute(
            """
            SELECT 1
            FROM bot_admins
            WHERE user_id=?
            """,
            (user_id,)
        ).fetchone()

        return row is not None

    # =========================
    # MOVIE METHODS
    # =========================

    def add_movie(
        self,
        title,
        description,
        file_id,
        file_size=0,
        uploaded_by=0,
        tags="",
        source_chat_id=None,
        source_message_id=None
    ) -> int:

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO movies(
            title,
            description,
            file_id,
            file_size,
            upload_date,
            uploaded_by,
            tags,
            source_chat_id,
            source_message_id,
            status
        )
        VALUES(?,?,?,?,?,?,?,?,?,'active')
        """, (
            title,
            description,
            file_id,
            file_size or 0,
            datetime.now().isoformat(),
            uploaded_by,
            tags,
            source_chat_id,
            source_message_id
        ))

        self.conn.commit()

        return cursor.lastrowid

    def movie_exists(
        self,
        title: str
    ):

        return self.conn.execute(
            """
            SELECT id
            FROM movies
            WHERE LOWER(TRIM(title))=LOWER(TRIM(?))
              AND status='active'
            """,
            (title,)
        ).fetchone()

    def search_movies(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:

        search_text = query.strip()
        q = f"%{search_text}%"

        rows = self.conn.execute("""
        SELECT
            id,
            title,
            description,
            file_id,
            file_size,
            views,
            downloads,
            source_chat_id,
            source_message_id,
            status
        FROM movies
        WHERE status='active'
          AND (
              title LIKE ? COLLATE NOCASE
              OR tags LIKE ? COLLATE NOCASE
          )
        ORDER BY
            CASE
                WHEN LOWER(title)=LOWER(?)
                THEN 0
                ELSE 1
            END,
            views DESC,
            downloads DESC,
            id DESC
        LIMIT ?
        """, (
            q,
            q,
            search_text,
            limit
        )).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_movie(
        self,
        movie_id: int,
        include_deleted: bool = False
    ) -> Optional[Dict]:

        if include_deleted:

            row = self.conn.execute("""
            SELECT
                id,
                title,
                description,
                file_id,
                file_size,
                views,
                downloads,
                source_chat_id,
                source_message_id,
                status,
                deleted_at,
                deleted_by
            FROM movies
            WHERE id=?
            """, (
                movie_id,
            )).fetchone()

        else:

            row = self.conn.execute("""
            SELECT
                id,
                title,
                description,
                file_id,
                file_size,
                views,
                downloads,
                source_chat_id,
                source_message_id,
                status,
                deleted_at,
                deleted_by
            FROM movies
            WHERE id=?
              AND status='active'
            """, (
                movie_id,
            )).fetchone()

        return dict(row) if row else None

    def increment_views(
        self,
        movie_id: int
    ):

        self.conn.execute(
            """
            UPDATE movies
            SET views=views+1
            WHERE id=?
              AND status='active'
            """,
            (movie_id,)
        )

        self.conn.commit()

    def increment_downloads(
        self,
        movie_id: int
    ):

        self.conn.execute(
            """
            UPDATE movies
            SET downloads=downloads+1
            WHERE id=?
              AND status='active'
            """,
            (movie_id,)
        )

        self.conn.commit()

    def delete_movie(
        self,
        movie_id: int,
        deleted_by: int = 0
    ) -> bool:

        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE movies
        SET
            status='deleted',
            deleted_at=?,
            deleted_by=?
        WHERE id=?
          AND status='active'
        """, (
            datetime.now().isoformat(),
            deleted_by,
            movie_id
        ))

        self.conn.commit()

        return cursor.rowcount > 0

    def restore_movie(
        self,
        movie_id: int
    ) -> bool:

        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE movies
        SET
            status='active',
            deleted_at=NULL,
            deleted_by=NULL
        WHERE id=?
          AND status='deleted'
        """, (
            movie_id,
        ))

        self.conn.commit()

        return cursor.rowcount > 0

    def count_active_movies(self) -> int:

        row = self.conn.execute("""
        SELECT COUNT(*)
        FROM movies
        WHERE status='active'
        """).fetchone()

        return int(row[0])

    def count_deleted_movies(self) -> int:

        row = self.conn.execute("""
        SELECT COUNT(*)
        FROM movies
        WHERE status='deleted'
        """).fetchone()

        return int(row[0])

    # =========================
    # USER METHODS
    # =========================

    def add_or_update_user(
        self,
        user_id: int,
        username: str,
        first_name: str,
        last_name: str = ""
    ):

        now = datetime.now().isoformat()

        self.conn.execute("""
        INSERT INTO users(
            user_id,
            username,
            first_name,
            last_name,
            join_date,
            last_active
        )
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            last_active=excluded.last_active
        """, (
            user_id,
            username,
            first_name,
            last_name,
            now,
            now
        ))

        self.conn.commit()

    def increment_user_requests(
        self,
        user_id: int
    ):

        self.conn.execute("""
        UPDATE users
        SET total_requests=total_requests+1
        WHERE user_id=?
        """, (
            user_id,
        ))

        self.conn.commit()

    # =========================
    # REQUEST METHODS
    # =========================

    def add_request(
        self,
        user_id: int,
        movie_title: str,
        description: str = ""
    ) -> int:

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO requests(
            user_id,
            movie_title,
            description,
            request_date
        )
        VALUES(?,?,?,?)
        """, (
            user_id,
            movie_title,
            description,
            datetime.now().isoformat()
        ))

        self.conn.commit()

        return cursor.lastrowid

    def get_pending_requests(
        self
    ) -> List[Dict]:

        rows = self.conn.execute("""
        SELECT
            r.id,
            r.user_id,
            r.movie_title,
            r.description,
            r.status,
            r.request_date,
            u.username,
            u.first_name
        FROM requests r
        LEFT JOIN users u
            ON r.user_id=u.user_id
        WHERE r.status='pending'
        ORDER BY r.request_date DESC
        """).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================
    # COOLDOWN METHODS
    # =========================

    def check_cooldown(
        self,
        user_id: int,
        seconds: int = 60
    ) -> bool:

        row = self.conn.execute(
            """
            SELECT last_message
            FROM cooldowns
            WHERE user_id=?
            """,
            (user_id,)
        ).fetchone()

        now = datetime.now()

        if row:

            last_time = datetime.fromisoformat(
                row["last_message"]
            )

            if now - last_time < timedelta(
                seconds=seconds
            ):
                return False

        self.conn.execute("""
        INSERT OR REPLACE INTO cooldowns(
            user_id,
            last_message
        )
        VALUES(?,?)
        """, (
            user_id,
            now.isoformat()
        ))

        self.conn.commit()

        return True

    def cooldown_remaining(
        self,
        user_id: int,
        seconds: int = 60
    ) -> int:

        row = self.conn.execute(
            """
            SELECT last_message
            FROM cooldowns
            WHERE user_id=?
            """,
            (user_id,)
        ).fetchone()

        if not row:
            return 0

        elapsed = (
            datetime.now()
            - datetime.fromisoformat(
                row["last_message"]
            )
        ).total_seconds()

        return max(
            0,
            seconds - int(elapsed)
        )

    # =========================
    # AUTO DELETE METHODS
    # =========================

    def add_message(
        self,
        chat_id: int,
        message_id: int,
        movie_id=None,
        seconds: int = 300
    ):

        expire = datetime.now() + timedelta(
            seconds=seconds
        )

        self.conn.execute("""
        INSERT OR REPLACE INTO messages(
            chat_id,
            message_id,
            movie_id,
            expire_time
        )
        VALUES(?,?,?,?)
        """, (
            chat_id,
            message_id,
            movie_id,
            expire.isoformat()
        ))

        self.conn.commit()

    def get_expired_messages(self):

        return self.conn.execute("""
        SELECT
            chat_id,
            message_id,
            movie_id
        FROM messages
        WHERE expire_time<=?
        """, (
            datetime.now().isoformat(),
        )).fetchall()

    def remove_message(
        self,
        chat_id: int,
        message_id: int
    ):

        self.conn.execute("""
        DELETE FROM messages
        WHERE chat_id=?
          AND message_id=?
        """, (
            chat_id,
            message_id
        ))

        self.conn.commit()

    # =========================
    # DOWNLOAD TOKEN METHODS
    # =========================

    def create_download_token(
        self,
        token: str,
        movie_id: int,
        seconds: int
    ):

        expire = datetime.now() + timedelta(
            seconds=seconds
        )

        self.conn.execute("""
        INSERT OR REPLACE INTO download_tokens(
            token,
            movie_id,
            expire_time,
            used
        )
        VALUES(?,?,?,0)
        """, (
            token,
            movie_id,
            expire.isoformat()
        ))

        self.conn.commit()

    def verify_download_token(
        self,
        token: str
    ):

        row = self.conn.execute("""
        SELECT
            movie_id,
            expire_time,
            used
        FROM download_tokens
        WHERE token=?
        """, (
            token,
        )).fetchone()

        if not row:

            return None

        if row["used"]:

            self.consume_download_token(token)
            return None

        if datetime.now() > datetime.fromisoformat(
            row["expire_time"]
        ):

            self.consume_download_token(token)
            return None

        movie = self.get_movie(
            int(row["movie_id"])
        )

        if not movie:

            self.consume_download_token(token)
            return None

        return int(row["movie_id"])

    def consume_download_token(
        self,
        token: str
    ):

        self.conn.execute("""
        DELETE FROM download_tokens
        WHERE token=?
        """, (
            token,
        ))

        self.conn.commit()

    def cleanup_tokens(self):

        self.conn.execute("""
        DELETE FROM download_tokens
        WHERE expire_time<=?
           OR used=1
        """, (
            datetime.now().isoformat(),
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()
