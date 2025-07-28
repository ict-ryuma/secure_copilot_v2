# init_db_teams.py
# import sqlite3
import os
from .mysql_connector import execute_query

# ✅ 修正: 絶対パスに統一
DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def create_tables():
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()

    # team_masterテーブル作成
    execute_query("""
    CREATE TABLE IF NOT EXISTS team_master (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        team_name TEXT UNIQUE NOT NULL,
        prompt_key TEXT NOT NULL,
        text_prompt TEXT,
        audio_prompt TEXT,
        score_items TEXT,
        notes TEXT,
        is_active INTEGER DEFAULT 1,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # prompt_key_masterもついでに作ってもOK
    execute_query("""
    CREATE TABLE IF NOT EXISTS prompt_key_master (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        prompt_key TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # conn.commit()
    # conn.close()
    print(f"✅ teams & team_master テーブルを初期化しました (DB: {DB_PATH})")

# ✅ 修正: create_team_table 関数も追加
def create_team_table():
    """init_db.py からの呼び出し用"""
    create_tables()

if __name__ == "__main__":
    create_tables()
