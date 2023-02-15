import sqlite3 as sql

db_path = r'./data/AppData.db'
workfile_path = r'./data/workfile'

conn = sql.connect(db_path)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS checkers (
    id INTEGER PRIMARY KEY,
    firstname VARCHAR(255),
    lastname VARCHAR(255),
    email VARCHAR(255)
    )"""
)

c.execute("""
    CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY,
    reps VARCHAR(255),
    checker_id INTEGER,
    is_valid INTEGER NOT NULL,
    reason INTEGER,
    FOREIGN KEY (checker_id) REFERENCES checker (id)
    )"""
)

c.execute("""
    CREATE TABLE IF NOT EXISTS candidate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    department INTEGER,
    valid INTEGER,
    void INTEGER
    )"""
)

conn.commit()
conn.close()
