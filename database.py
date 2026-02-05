import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "complaints.db")

def get_connection():
    return sqlite3.connect("complaints.db", check_same_thread=False)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        complaint TEXT,
        category TEXT,
        urgency TEXT,
        priority TEXT,
        status TEXT,
        created_at TEXT,
        resolved_at TEXT
    )
    """)



    conn.commit()
    conn.close()
