# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime

# ✅ score_log.db に統一
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")

def create_team_table():
    """チーム関連テーブルを作成"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # チーム情報テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.executemany('INSERT OR IGNORE INTO teams (team_name) VALUES (?)', [
        ('A_team',), ('B_team',), ('C_team',), ('F_team',)
    ])

    # チームプロンプトマスターテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE NOT NULL,
            prompt_key TEXT NOT NULL,
            text_prompt TEXT,
            audio_prompt TEXT,
            score_items TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ teams & team_master テーブルを初期化しました")

# 互換用関数
def init_team_db():
    create_team_table()

if __name__ == "__main__":
    create_team_table()
