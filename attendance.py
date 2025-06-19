import streamlit as st
import sqlite3
import datetime

def create_tables(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS banjaarey (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banjaara_id INTEGER,
            date TEXT,
            FOREIGN KEY (banjaara_id) REFERENCES banjaarey(id),
            UNIQUE (banjaara_id, date)
        )
    ''')

def get_connection():
    return sqlite3.connect("banjaarey.db", check_same_thread=False)

def add_banjaara(name):
    try:
        conn.execute("INSERT INTO banjaarey (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_banjaarey():
    return conn.execute("SELECT id, name FROM banjaarey ORDER BY name").fetchall()

# ... (other function definitions here)

conn = get_connection()
create_tables(conn)

# Now you can use get_banjaarey()
banjaarey = get_banjaarey()
# ... rest of your Streamlit code ...
