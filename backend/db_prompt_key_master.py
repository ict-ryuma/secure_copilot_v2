# backend/db_prompt_key_master.py

# import sqlite3
from .mysql_connector import execute_query, execute_select_query, execute_modify_query
import os

# ✅ 修正: 絶対パスに統一
DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

# --- テーブル作成 ---
def create_prompt_key_master_table():
    execute_modify_query("""
        CREATE TABLE IF NOT EXISTS prompt_key_master (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prompt_key VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            is_active TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

# --- 新規追加 ---
def insert_prompt_key(prompt_key, description=""):
    execute_modify_query("""
        INSERT INTO prompt_key_master (prompt_key, description) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            description = VALUES(description),
            is_active = 1,
            created_at = CURRENT_TIMESTAMP
    """, (prompt_key, description))

# --- 有効なキー一覧取得 ---
def get_active_prompt_keys():
    rows = execute_select_query("SELECT prompt_key FROM prompt_key_master WHERE is_active = 1")
    return [row[0] for row in rows] if rows else []

# --- 全件取得 ---
def fetch_all_prompt_keys():
    rows = execute_select_query("SELECT * FROM prompt_key_master ORDER BY id")
    return rows if rows else []

# --- 更新 ---
def update_prompt_key(id, prompt_key, description, is_active):
    execute_modify_query("""
        UPDATE prompt_key_master SET
            prompt_key = %s,
            description = %s,
            is_active = %s
        WHERE id = %s
    """, (prompt_key, description, is_active, id))

# --- 削除 ---
def delete_prompt_key(id):
    execute_modify_query("DELETE FROM prompt_key_master WHERE id = %s", (id,))

# テスト実行（初期化）
if __name__ == "__main__":
    create_prompt_key_master_table()
    insert_prompt_key("A_team", "AI営業チーム")
    insert_prompt_key("B_team", "サポートチーム")
