"""Opening SQLite connections and creating the tables at startup."""
import os
import sqlite3

import config

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Open a connection to the database file in config.DATABASE_PATH."""
    connection = sqlite3.connect(config.DATABASE_PATH)
    # Rows can be read by column name: row["title"] instead of row[1].
    connection.row_factory = sqlite3.Row
    # SQLite ignores REFERENCES unless this is switched on per connection.
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def fetch_all(sql, params=()):
    """Run a SELECT and return every row as a dict."""
    connection = get_connection()
    try:
        rows = connection.execute(sql, params).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def fetch_one(sql, params=()):
    """Run a SELECT and return the first row as a dict, or None."""
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run an INSERT or UPDATE, save it, and return the new row's id."""
    connection = get_connection()
    try:
        cursor = connection.execute(sql, params)
        connection.commit()
    finally:
        connection.close()
    return cursor.lastrowid


def init_db():
    """Create the data folder and any missing tables from schema.sql."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        schema = schema_file.read()
    connection = get_connection()
    connection.executescript(schema)
    connection.close()
