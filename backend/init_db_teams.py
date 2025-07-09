# backend/init_db_teams.py

import sqlite3
import os

DB_PATH = "secure_copilot.db"

def init_team_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE NOT NULL
        )
    ''')
    # 初期データ挿入
    c.executemany('INSERT OR IGNORE INTO teams (team_name) VALUES (?)', [
        ('A_team',),
        ('B_team',),
    ])
    conn.commit()
    conn.close()
    print("✅ teamsテーブルを初期化しました")

if __name__ == "__main__":
    init_team_db()
