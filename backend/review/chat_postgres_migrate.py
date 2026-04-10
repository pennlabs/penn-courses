#!/usr/bin/env python
"""
Temporary script: same chat functionality as views.py but using Postgres instead of Redis.
Uses the same DB as the app (Django connection). Run from backend/ with:
  uv run python review/chat_postgres_migrate.py

Tables created: pg_chat_sessions, pg_chat_messages (safe to drop later).
"""

import json
import os
import sys
import time
import uuid

# Only bootstrap when run as script; when imported by views.py Django is already set up
if __name__ == "__main__":
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend_dir not in sys.path:
        sys.path.insert(0, _backend_dir)
    os.chdir(_backend_dir)
    from dotenv import load_dotenv
    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PennCourses.settings.development")
    import django
    django.setup()

from django.db import connection

# --- Constants (match views.py) ---
CHAT_TTL_SECONDS = 7 * 24 * 3600
MAX_MESSAGES_PER_CHAT = 50
MAX_CHATS_PER_DAY = 5


def _today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _new_chat_id():
    return uuid.uuid4().hex[:8]


def _make_msg(role, content, citations=None):
    return {
        "id": uuid.uuid4().hex,
        "role": role,
        "content": content,
        "citations": citations or [],
        "ts": int(time.time()),
    }


# --- Schema: create tables if not exist ---
def ensure_tables():
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pg_chat_sessions (
                id VARCHAR(8) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at BIGINT NOT NULL,
                expires_at BIGINT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pg_chat_messages (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(8) NOT NULL REFERENCES pg_chat_sessions(id) ON DELETE CASCADE,
                msg_id VARCHAR(32) NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                citations JSONB DEFAULT '[]',
                ts BIGINT NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pg_chat_messages_chat_id ON pg_chat_messages(chat_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pg_chat_sessions_user_created ON pg_chat_sessions(user_id, created_at)")
    connection.commit()
    print("Tables pg_chat_sessions, pg_chat_messages ready.")


# --- Postgres equivalents of Redis operations ---
def postgres_chat_start(user_id: int):
    """Returns (chat_id, expires_at) or raises ValueError if quota exceeded."""
    today = _today()
    now_ts = int(time.time())
    expires_at = now_ts + CHAT_TTL_SECONDS

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM pg_chat_sessions
            WHERE user_id = %s AND created_at >= %s
            """,
            [user_id, now_ts - 24 * 3600],  # last 24h
        )
        count = cur.fetchone()[0]
    if count >= MAX_CHATS_PER_DAY:
        raise ValueError("Daily quota exceeded")

    chat_id = _new_chat_id()
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pg_chat_sessions (id, user_id, created_at, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            [chat_id, user_id, now_ts, expires_at],
        )
    connection.commit()
    return chat_id, expires_at


def postgres_chat_meta(chat_id: str):
    """Returns dict with user_id, created_at or None if not found/expired."""
    now_ts = int(time.time())
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, created_at, expires_at
            FROM pg_chat_sessions WHERE id = %s
            """,
            [chat_id],
        )
        row = cur.fetchone()
    if not row or row[2] < now_ts:
        return None
    return {"user_id": row[0], "created_at": row[1]}


def postgres_message_count(chat_id: str) -> int:
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pg_chat_messages WHERE chat_id = %s", [chat_id])
        return cur.fetchone()[0]


def postgres_append_message(chat_id: str, msg: dict):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pg_chat_messages (chat_id, msg_id, role, content, citations, ts)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                chat_id,
                msg["id"],
                msg["role"],
                msg["content"],
                json.dumps(msg.get("citations") or []),
                msg["ts"],
            ],
        )
    connection.commit()


def postgres_chat_history(chat_id: str, limit: int = 20):
    """Returns list of message dicts (id, role, content, citations, ts)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT msg_id, role, content, citations, ts
            FROM pg_chat_messages
            WHERE chat_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            [chat_id, limit],
        )
        rows = cur.fetchall()
    # Return in chronological order (oldest first)
    out = []
    for r in reversed(rows or []):
        out.append({
            "id": r[0],
            "role": r[1],
            "content": r[2],
            "citations": r[3] if isinstance(r[3], list) else json.loads(r[3] or "[]"),
            "ts": r[4],
        })
    return out


# --- Simulated chat_message flow (no real LLM; echo reply for test) ---
def postgres_chat_message(chat_id: str, user_id: int, text: str, mock_reply: str = None):
    """
    Appends user message and a mock assistant message. Returns assistant message dict.
    For a full migration you would call call_llm() here instead of mock_reply.
    """
    meta = postgres_chat_meta(chat_id)
    if not meta:
        raise ValueError("Chat not found or expired")
    if meta["user_id"] != user_id:
        raise ValueError("Chat does not belong to user")

    if postgres_message_count(chat_id) >= MAX_MESSAGES_PER_CHAT:
        raise ValueError("Message quota exceeded")

    user_msg = _make_msg("user", text)
    postgres_append_message(chat_id, user_msg)

    reply_text = mock_reply or f"[Postgres test] You said: {text}"
    assistant_msg = _make_msg("assistant", reply_text, citations=[])
    postgres_append_message(chat_id, assistant_msg)

    return {
        "id": assistant_msg["id"],
        "role": "assistant",
        "content": assistant_msg["content"],
        "citations": assistant_msg["citations"],
        "ts": assistant_msg["ts"],
    }


# --- Self-test ---
def get_any_user_id():
    """Use first user from auth_user so we can run without passing user_id."""
    with connection.cursor() as cur:
        cur.execute("SELECT id FROM auth_user ORDER BY id LIMIT 1")
        row = cur.fetchone()
    return row[0] if row else 1


def run_test():
    print("Using DB:", connection.settings_dict.get("NAME"), "at", connection.settings_dict.get("HOST"))
    ensure_tables()

    user_id = get_any_user_id()
    print("Using user_id:", user_id)

    # 1) Start chat
    chat_id, expires_at = postgres_chat_start(user_id)
    print("Started chat:", chat_id, "expires_at:", expires_at)

    # 2) Send message (mock reply)
    reply = postgres_chat_message(chat_id, user_id, "What CS courses do you recommend?", mock_reply="Try CIS-120 and CIS-121.")
    print("Assistant reply:", reply["content"])

    # 3) History
    history = postgres_chat_history(chat_id, limit=20)
    print("History messages:", len(history))
    for m in history:
        print("  -", m["role"], ":", m["content"][:60] + ("..." if len(m["content"]) > 60 else ""))

    # 4) Meta still there
    meta = postgres_chat_meta(chat_id)
    print("Meta:", meta)

    print("\nPostgres chat migration test OK. Tables pg_chat_sessions, pg_chat_messages are in use.")
    print("To drop them later: DROP TABLE IF EXISTS pg_chat_messages; DROP TABLE IF EXISTS pg_chat_sessions;")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
