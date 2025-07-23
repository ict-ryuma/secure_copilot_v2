# backend/db_team_master.py

import sqlite3
import os
from datetime import datetime

# === 相対パス指定（score_log.db に統一） ===
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")

# --- テーブル作成 ---
def create_team_master_table():
    """team_master テーブルを作成"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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

# --- 新規登録 ---
def insert_team_prompt(name, key, text_prompt, audio_prompt, score_items, notes):
    """新しいチームプロンプトを追加"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO team_master (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- 一覧取得 ---
def fetch_all_team_prompts():
    """全てのチームプロンプトを取得"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM team_master ORDER BY team_name')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- 1件取得（ID指定） ---
def fetch_team_prompt_by_id(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_master WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- 更新 ---
def update_team_prompt(team_id, name, key, text_prompt, audio_prompt, score_items, notes, is_active):
    """チームプロンプトを更新"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE team_master 
        SET team_name=?, prompt_key=?, text_prompt=?, audio_prompt=?, score_items=?, notes=?, is_active=?, updated_at=?
        WHERE id=?
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, is_active, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), team_id))
    conn.commit()
    conn.close()

# --- 削除（物理削除） ---
def delete_team_prompt(team_id):
    """チームプロンプトを削除"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM team_master WHERE id=?', (team_id,))
    conn.commit()
    conn.close()

def fetch_all_prompt_keys():
    """プロンプトキー一覧を取得"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, prompt_key, notes, is_active, updated_at FROM team_master')
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_prompt_key_master_table():
    """後方互換性のため（実際は team_master を使用）"""
    create_team_master_table()

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
