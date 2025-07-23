# backend/db_prompt_key_master.py

import sqlite3
import os

# ✅ score_log.db に統一
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")

# --- テーブル作成 ---
def create_prompt_key_master_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_key_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_key TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# --- 新規追加 ---
def insert_prompt_key(prompt_key, description=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prompt_key_master (prompt_key, description) VALUES (?, ?)
    """, (prompt_key, description))
    conn.commit()
    conn.close()

# --- 有効なキー一覧取得 ---
def get_active_prompt_keys():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt_key FROM prompt_key_master WHERE is_active = 1")
    keys = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keys

# --- 全件取得 ---
def fetch_all_prompt_keys():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompt_key_master")
    keys = cursor.fetchall()
    conn.close()
    return keys

# --- 更新 ---
def update_prompt_key(id, prompt_key, description, is_active):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE prompt_key_master SET
            prompt_key = ?,
            description = ?,
            is_active = ?
        WHERE id = ?
    """, (prompt_key, description, is_active, id))
    conn.commit()
    conn.close()

# --- 削除 ---
def delete_prompt_key(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prompt_key_master WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# テスト実行（初期化）
if __name__ == "__main__":
    create_prompt_key_master_table()
    insert_prompt_key("A_team", "AI営業チーム")
    insert_prompt_key("B_team", "サポートチーム")
