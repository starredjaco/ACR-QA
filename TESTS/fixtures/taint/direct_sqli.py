"""Fixture: 1-hop SQL injection — request.args directly into cursor.execute."""

import sqlite3

from flask import request


def search(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = request.args.get("q")  # taint source
    cursor.execute("SELECT * FROM users WHERE name = " + query)  # taint sink (1 hop)
    return cursor.fetchall()


def safe_search(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = request.args.get("q")
    cursor.execute("SELECT * FROM users WHERE name = ?", (query,))  # parameterized — clean
    return cursor.fetchall()
