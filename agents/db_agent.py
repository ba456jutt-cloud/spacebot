import sqlite3
import os
import time

DB_PATH = "fugu_data.db"

def init_db():
    """Initializes the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table to track YouTube videos we have already used as inspiration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_trends (
            source_video_id TEXT PRIMARY KEY,
            title TEXT,
            processed_at INTEGER
        )
    ''')
    
    # Table to track our own uploaded videos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            upload_id TEXT PRIMARY KEY,
            source_video_id TEXT,
            seo_title TEXT,
            uploaded_at INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[*] DB Agent: Database initialized.")

def is_trend_processed(video_id: str) -> bool:
    """Checks if a source YouTube video ID has already been covered by the bot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_trends WHERE source_video_id = ?', (video_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_trend_processed(video_id: str, title: str):
    """Marks a source YouTube video ID as processed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO processed_trends (source_video_id, title, processed_at) VALUES (?, ?, ?)',
        (video_id, title, int(time.time()))
    )
    conn.commit()
    conn.close()

def log_upload(upload_id: str, source_video_id: str, seo_title: str):
    """Logs a successful upload."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO uploads (upload_id, source_video_id, seo_title, uploaded_at) VALUES (?, ?, ?, ?)',
        (upload_id, source_video_id, seo_title, int(time.time()))
    )
    conn.commit()
    conn.close()

def get_recent_uploads(limit: int = 3) -> list:
    """Fetches the recent uploads from the database to inject as 'Watch Next' links."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads'")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT upload_id, seo_title FROM uploads ORDER BY uploaded_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"id": row[0], "title": row[1]} for row in rows]
    except Exception as e:
        print(f"[-] DB Agent Error: Failed to fetch recent uploads: {e}")
        return []
