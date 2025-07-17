# backend/db_team_master.py

import sqlite3
from datetime import datetime

DB_PATH = "backend/user_db.db"

# --- テーブル作成 ---
def create_team_master_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL UNIQUE,
            prompt_key TEXT NOT NULL UNIQUE,
            text_prompt TEXT NOT NULL,
            audio_prompt TEXT NOT NULL,
            score_items TEXT NOT NULL,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# --- 新規登録 ---
def insert_team_prompt(team_name, prompt_key, text_prompt, audio_prompt, score_items, notes=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO team_master (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes))
    conn.commit()
    conn.close()

# --- 一覧取得 ---
def fetch_all_team_prompts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_master WHERE is_active = 1")
    results = cursor.fetchall()
    conn.close()
    return results

# --- 1件取得（ID指定） ---
def fetch_team_prompt_by_id(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_master WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- 更新 ---
def update_team_prompt(id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active=1):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE team_master SET
            team_name = ?,
            prompt_key = ?,
            text_prompt = ?,
            audio_prompt = ?,
            score_items = ?,
            notes = ?,
            is_active = ?,
            last_updated = ?
        WHERE id = ?
    """, (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, datetime.now(), id))
    conn.commit()
    conn.close()

# --- 削除（物理削除） ---
def delete_team_prompt(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM team_master WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# --- 初期化（テスト用） ---
if __name__ == "__main__":
    create_team_master_table()
    insert_team_prompt(
        team_name="チームA",
        prompt_key="A_team",
        text_prompt="以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
        audio_prompt="音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
        score_items="ヒアリング姿勢,説明のわかりやすさ,クロージングの一貫性,感情の乗せ方と誠実さ,対話のテンポ",
        notes="初期登録"
    )
