import sqlite3
import pandas as pd
import os

DB_NAME = "gowcounter.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id TEXT PRIMARY KEY,
            video_name TEXT,
            class_name TEXT,
            timestamp DATETIME,
            track_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_detection(video_name, class_name, timestamp, track_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO detections (id, video_name, class_name, timestamp, track_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (f"{video_name}_{class_name}_{track_id}", video_name, class_name, timestamp, track_id))
    conn.commit()
    conn.close()

def get_all_detections():
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM detections", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df
