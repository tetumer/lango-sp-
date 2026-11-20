
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "lingo.db"


def connect():
    return sqlite3.connect(DB_PATH)


def initialize():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                meaning TEXT,
                part_of_speech TEXT,
                gender TEXT,
                pronunciation TEXT,
                example TEXT,
                translation TEXT,
                status TEXT DEFAULT 'learned',
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                last_reviewed TEXT
            )
        """)


def get_saved_word_set():
    with connect() as db:
        rows = db.execute("SELECT word FROM words").fetchall()
        return {row[0].lower() for row in rows}


def save_learned_word(data):
    with connect() as db:
        db.execute("""
            INSERT INTO words (
                word, meaning, part_of_speech, gender,
                pronunciation, example, translation, status,
                last_reviewed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'learned', CURRENT_TIMESTAMP)
            ON CONFLICT(word) DO UPDATE SET
                meaning = excluded.meaning,
                part_of_speech = excluded.part_of_speech,
                gender = excluded.gender,
                pronunciation = excluded.pronunciation,
                example = excluded.example,
                translation = excluded.translation,
                status = 'learned',
                last_reviewed = CURRENT_TIMESTAMP
        """, (
            data["word"],
            data.get("meaning", ""),
            data.get("part_of_speech", ""),
            data.get("gender", ""),
            data.get("pronunciation", ""),
            data.get("example", ""),
            data.get("translation", "")
        ))


def get_learned_words():
    with connect() as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""
            SELECT * FROM words
            WHERE status = 'learned'
            ORDER BY word COLLATE NOCASE
        """).fetchall()
        return [dict(row) for row in rows]


initialize()
