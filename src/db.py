"""
src/db.py
SQLite database layer for NeuroStudy Coach.
Handles assignment, blocked day, and study session CRUD operations.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date

# Store the DB file in a local `data/` folder next to the project root
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "neurostudy.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist yet."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                course      TEXT    NOT NULL,
                due_date    TEXT    NOT NULL,
                est_hours   REAL    NOT NULL,
                priority    TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blocked_days (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                day     TEXT    NOT NULL UNIQUE   -- ISO date string e.g. 2026-04-20
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id   INTEGER NOT NULL,
                session_date    TEXT    NOT NULL,   -- ISO date string
                duration_mins   INTEGER NOT NULL,
                session_number  INTEGER NOT NULL,
                total_sessions  INTEGER NOT NULL,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    init_progress_tables()
    init_profile_table()


# ---------- CRUD ----------

def add_assignment(
    name: str,
    course: str,
    due_date: datetime,
    est_hours: float,
    priority: str,
    assignment_type: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO assignments (name, course, due_date, est_hours, priority, type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                course,
                due_date.isoformat(),
                est_hours,
                priority,
                assignment_type,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_all_assignments() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM assignments ORDER BY due_date ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_assignment(
    assignment_id: int,
    name: str,
    course: str,
    due_date: datetime,
    est_hours: float,
    priority: str,
    assignment_type: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE assignments
            SET name=?, course=?, due_date=?, est_hours=?, priority=?, type=?
            WHERE id=?
            """,
            (
                name,
                course,
                due_date.isoformat(),
                est_hours,
                priority,
                assignment_type,
                assignment_id,
            ),
        )
        conn.commit()


def delete_assignment(assignment_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
        conn.commit()

# ---------- Blocked Days ----------

def get_blocked_days() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT day FROM blocked_days ORDER BY day ASC").fetchall()
    return [r["day"] for r in rows]


def add_blocked_day(day) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO blocked_days (day) VALUES (?)",
            (day.isoformat(),)
        )
        conn.commit()


def remove_blocked_day(day) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM blocked_days WHERE day=?", (day.isoformat(),))
        conn.commit()


# ---------- Study Sessions ----------

def save_study_sessions(sessions: list) -> None:
    """Replace all existing sessions with a freshly generated schedule."""
    with get_connection() as conn:
        conn.execute("DELETE FROM study_sessions")
        conn.executemany(
            """
            INSERT INTO study_sessions
                (assignment_id, session_date, duration_mins, session_number, total_sessions)
            VALUES (:assignment_id, :session_date, :duration_mins, :session_number, :total_sessions)
            """,
            sessions,
        )
        conn.commit()


def get_study_sessions() -> list:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT ss.*, a.name as assignment_name, a.course, a.priority, a.type
            FROM study_sessions ss
            JOIN assignments a ON ss.assignment_id = a.id
            ORDER BY ss.session_date ASC
        """).fetchall()
    return [dict(r) for r in rows]


# ---------- Progress Tracking ----------

def init_progress_tables() -> None:
    """Create progress tracking tables if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_completions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      INTEGER NOT NULL UNIQUE,
                completed_at    TEXT    NOT NULL,
                FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assignment_progress (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id       INTEGER NOT NULL UNIQUE,
                actual_hours        REAL    NOT NULL DEFAULT 0,
                actual_difficulty   TEXT,   -- Easy / Medium / Hard
                completion_pct      REAL    NOT NULL DEFAULT 0,
                last_updated        TEXT    NOT NULL,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
            )
        """)
        conn.commit()


def mark_session_complete(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO session_completions (session_id, completed_at) VALUES (?, ?)",
            (session_id, datetime.now().isoformat())
        )
        conn.commit()


def unmark_session_complete(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM session_completions WHERE session_id=?", (session_id,))
        conn.commit()


def get_completed_session_ids() -> set:
    with get_connection() as conn:
        rows = conn.execute("SELECT session_id FROM session_completions").fetchall()
    return {r["session_id"] for r in rows}


def upsert_assignment_progress(
    assignment_id: int,
    actual_hours: float,
    actual_difficulty: str,
    completion_pct: float = 0.0,
) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO assignment_progress (assignment_id, actual_hours, actual_difficulty, completion_pct, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET
                actual_hours=excluded.actual_hours,
                actual_difficulty=excluded.actual_difficulty,
                completion_pct=excluded.completion_pct,
                last_updated=excluded.last_updated
        """, (assignment_id, actual_hours, actual_difficulty, completion_pct, datetime.now().isoformat()))
        conn.commit()


def get_all_progress() -> dict:
    """Returns a dict keyed by assignment_id with progress data."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM assignment_progress").fetchall()
    return {r["assignment_id"]: dict(r) for r in rows}


def get_today_sessions() -> list:
    """Get all scheduled sessions for today with assignment info."""
    today = date.today().isoformat()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT ss.*, a.name as assignment_name, a.course, a.priority, a.type,
                   a.est_hours, a.due_date
            FROM study_sessions ss
            JOIN assignments a ON ss.assignment_id = a.id
            WHERE ss.session_date = ?
            ORDER BY a.priority DESC
        """, (today,)).fetchall()
    return [dict(r) for r in rows]


# ---------- User Profile ----------

def init_profile_table() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id                      INTEGER PRIMARY KEY,
                nd_type                 TEXT    NOT NULL DEFAULT 'ADHD',
                executive_function      INTEGER NOT NULL DEFAULT 3,
                working_memory          TEXT    NOT NULL DEFAULT 'medium',
                time_blindness          INTEGER NOT NULL DEFAULT 3,
                typical_stress          INTEGER NOT NULL DEFAULT 3,
                typical_energy          INTEGER NOT NULL DEFAULT 3,
                preferred_session_len   INTEGER NOT NULL DEFAULT 50,
                preferred_study_times   TEXT    NOT NULL DEFAULT 'afternoon',
                max_daily_hours         REAL    NOT NULL DEFAULT 4.0,
                break_frequency         INTEGER NOT NULL DEFAULT 50,
                updated_at              TEXT    NOT NULL
            )
        """)
        # Add interest_level to assignments if not present
        try:
            conn.execute("ALTER TABLE assignments ADD COLUMN interest_level INTEGER NOT NULL DEFAULT 3")
        except Exception:
            pass
        conn.commit()


def get_user_profile() -> dict:
    init_profile_table()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM user_profile WHERE id=1").fetchone()
    return dict(row) if row else {}


def save_user_profile(
    nd_type: str,
    executive_function: int,
    working_memory: str,
    time_blindness: int,
    typical_stress: int,
    typical_energy: int,
    preferred_session_len: int,
    preferred_study_times: str,
    max_daily_hours: float,
    break_frequency: int,
) -> None:
    init_profile_table()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO user_profile
                (id, nd_type, executive_function, working_memory, time_blindness,
                 typical_stress, typical_energy, preferred_session_len,
                 preferred_study_times, max_daily_hours, break_frequency, updated_at)
            VALUES (1,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                nd_type=excluded.nd_type,
                executive_function=excluded.executive_function,
                working_memory=excluded.working_memory,
                time_blindness=excluded.time_blindness,
                typical_stress=excluded.typical_stress,
                typical_energy=excluded.typical_energy,
                preferred_session_len=excluded.preferred_session_len,
                preferred_study_times=excluded.preferred_study_times,
                max_daily_hours=excluded.max_daily_hours,
                break_frequency=excluded.break_frequency,
                updated_at=excluded.updated_at
        """, (nd_type, executive_function, working_memory, time_blindness,
              typical_stress, typical_energy, preferred_session_len,
              preferred_study_times, max_daily_hours, break_frequency,
              datetime.now().isoformat()))
        conn.commit()
