import sqlite3 as sql
import contextlib

db_path = r'./data/AppData.db'
workfile_path = r'./data/workfile'

conn = sql.connect(db_path)
c = conn.cursor()

def db():
    return contextlib.closing(sql.connect(db_path))

c.execute("""
    CREATE TABLE IF NOT EXISTS checker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id INTEGER,
    firstname VARCHAR(255),
    lastname VARCHAR(255),
    email VARCHAR(255)
    )"""
)

c.execute("""
    CREATE TABLE IF NOT EXISTS vote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER,
    rep_col INTEGER,
    checker_id INTEGER,
    is_valid INTEGER,
    reason INTEGER,
    FOREIGN KEY (checker_id) REFERENCES checker (id)
    )"""
)

conn.commit()
conn.close()
