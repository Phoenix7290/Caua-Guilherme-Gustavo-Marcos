"""Criação e população inicial do banco SQLite (database.db) usando sqlite3.

Uso (a partir de fastapi/):  python sqlite_database.py
"""
import os
import sqlite3

import bcrypt

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediction (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id   INTEGER NOT NULL,
    text       TEXT NOT NULL,
    intent     TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES user (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_prediction_owner_id ON prediction (owner_id);
"""

USERS = [
    ("admin", "admin123"),
    ("alice", "alice123"),
]

# (dono, texto, intenção, confiança)
PREDICTIONS = [
    ("admin", "Quero meu dinheiro de volta, o produto veio com defeito", "Refund Request", 0.91),
    ("admin", "Meu produto parou de funcionar", "Technical Issue", 0.87),
    ("alice", "Preciso cancelar meu pedido", "Cancellation Request", 0.88),
    ("alice", "Tenho uma dúvida sobre a fatura deste mês", "Billing Inquiry", 0.85),
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_database(path: str = DB_PATH) -> None:
    if os.path.exists(path):
        os.remove(path)

    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)

        for username, password in USERS:
            conn.execute(
                "INSERT INTO user (username, hashed_password) VALUES (?, ?)",
                (username, hash_password(password)),
            )

        ids = {name: uid for uid, name in conn.execute("SELECT id, username FROM user")}
        for owner, text, intent, confidence in PREDICTIONS:
            conn.execute(
                "INSERT INTO prediction (owner_id, text, intent, confidence) VALUES (?, ?, ?, ?)",
                (ids[owner], text, intent, confidence),
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
    print(f"Banco criado em {DB_PATH}")
