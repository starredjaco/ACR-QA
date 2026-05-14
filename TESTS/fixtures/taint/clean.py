"""Fixture: no taint flows — should produce 0 findings (FP check)."""

import sqlite3

ALLOWED_TERMS = {"alpha", "beta", "gamma"}


def safe_lookup(db_path, term: str):
    if term not in ALLOWED_TERMS:
        raise ValueError("disallowed term")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE category = ?", (term,))
    return cursor.fetchall()


def compute(x: int, y: int) -> int:
    result = x + y
    return result


def greet(name: str) -> str:
    return f"Hello, {name}!"


class Processor:
    def run(self, value: str) -> str:
        cleaned = value.strip().lower()
        return cleaned
