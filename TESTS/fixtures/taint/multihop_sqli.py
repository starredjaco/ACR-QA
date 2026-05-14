"""Fixture: 2-hop SQL injection — taint propagates through an intermediate variable."""

import sqlite3

from flask import request


def search(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    raw = request.form["q"]  # taint source
    cleaned = raw.strip()  # hop 1 — still tainted (method call on tainted var)
    cursor.execute("SELECT * FROM items WHERE name = " + cleaned)  # sink (hop 2)
    return cursor.fetchall()


def search_fstring(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    term = request.form.get("term")  # taint source
    sql = f"SELECT * FROM products WHERE name LIKE '%{term}%'"  # hop 1 — f-string
    cursor.execute(sql)  # sink (hop 2)
    return cursor.fetchall()
