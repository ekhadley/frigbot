import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
DB_PATH = Path(__file__).parent / "data" / "streaks.db"


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS solves (
              guild_id     TEXT NOT NULL,
              puzzle_date  TEXT NOT NULL,
              user_id      TEXT NOT NULL,
              username     TEXT,
              guesses      INTEGER NOT NULL,
              avg_bits     REAL,
              solved_at    TEXT NOT NULL,
              PRIMARY KEY (guild_id, puzzle_date, user_id)
            );
            CREATE TABLE IF NOT EXISTS launches (
              guild_id        TEXT NOT NULL,
              puzzle_date     TEXT NOT NULL,
              channel_id      TEXT NOT NULL,
              first_launch_at TEXT NOT NULL,
              PRIMARY KEY (guild_id, puzzle_date)
            );
            CREATE TABLE IF NOT EXISTS guild_channels (
              guild_id   TEXT PRIMARY KEY,
              channel_id TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS boards (
              game        TEXT NOT NULL,
              puzzle_date TEXT NOT NULL,
              user_id     TEXT NOT NULL,
              payload     TEXT NOT NULL,
              updated_at  TEXT NOT NULL,
              PRIMARY KEY (game, puzzle_date, user_id)
            );
            """
        )


def record_solve(guild_id: str, puzzle_date: str, user_id: str, username: str | None,
                 guesses: int, avg_bits: float | None) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO solves (guild_id, puzzle_date, user_id, username, guesses, avg_bits, solved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, puzzle_date, user_id, username, guesses, avg_bits, datetime.now(ET).isoformat()),
        )


def save_board(game: str, puzzle_date: str, user_id: str, payload: dict) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO boards (game, puzzle_date, user_id, payload, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(game, puzzle_date, user_id) DO UPDATE SET "
            "payload = excluded.payload, updated_at = excluded.updated_at",
            (game, puzzle_date, user_id, json.dumps(payload), datetime.now(ET).isoformat()),
        )


def delete_board(game: str, puzzle_date: str, user_id: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "DELETE FROM boards WHERE game = ? AND puzzle_date = ? AND user_id = ?",
            (game, puzzle_date, user_id),
        )


def load_boards(game: str, puzzle_date: str) -> dict[str, dict]:
    with db_connect() as conn:
        rows = conn.execute(
            "SELECT user_id, payload FROM boards WHERE game = ? AND puzzle_date = ?",
            (game, puzzle_date),
        ).fetchall()
    return {row["user_id"]: json.loads(row["payload"]) for row in rows}


def streak_length_through(guild_id: str, end_date: str) -> int:
    with db_connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT puzzle_date FROM solves WHERE guild_id = ? AND puzzle_date <= ? ORDER BY puzzle_date DESC",
            (guild_id, end_date),
        ).fetchall()
    cursor = datetime.fromisoformat(end_date).date()
    streak = 0
    for row in rows:
        if row["puzzle_date"] == cursor.isoformat():
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break
    return streak


def yesterday_summary(guild_id: str) -> dict:
    yday = (datetime.now(ET).date() - timedelta(days=1)).isoformat()
    today = datetime.now(ET).date().isoformat()
    with db_connect() as conn:
        solvers = conn.execute(
            "SELECT user_id, username, guesses, avg_bits, solved_at FROM solves "
            "WHERE guild_id = ? AND puzzle_date = ? ORDER BY solved_at ASC",
            (guild_id, yday),
        ).fetchall()
        today_count = conn.execute(
            "SELECT COUNT(*) AS n FROM solves WHERE guild_id = ? AND puzzle_date = ?",
            (guild_id, today),
        ).fetchone()["n"]
        channel_row = conn.execute(
            "SELECT channel_id FROM guild_channels WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
    streak = streak_length_through(guild_id, yday) if solvers else 0
    return {
        "puzzle_date": yday,
        "streak": streak,
        "channel_id": channel_row["channel_id"] if channel_row else None,
        "today_solvers": today_count,
        "solvers": [
            {
                "user_id": r["user_id"],
                "username": r["username"],
                "guesses": r["guesses"],
                "avg_bits": r["avg_bits"],
            }
            for r in solvers
        ],
    }


def record_launch_first_today(guild_id: str, channel_id: str, today: str) -> bool:
    """Returns True if this is the first launch for (guild, today)."""
    now = datetime.now(ET).isoformat()
    with db_connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO launches (guild_id, puzzle_date, channel_id, first_launch_at) VALUES (?, ?, ?, ?)",
            (guild_id, today, channel_id, now),
        )
        first = cur.rowcount == 1
        conn.execute(
            "INSERT INTO guild_channels (guild_id, channel_id, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id, updated_at = excluded.updated_at",
            (guild_id, channel_id, now),
        )
    return first


def launched_today(guild_id: str, today: str) -> bool:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM launches WHERE guild_id = ? AND puzzle_date = ?",
            (guild_id, today),
        ).fetchone()
    return row is not None
