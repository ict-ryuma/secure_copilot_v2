# backend/db_team_master.py

import sqlite3
import json
from datetime import datetime
import os

# ✅ 統一DBパス
DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def create_team_master_table():
    """team_masterテーブル作成（9列対応）"""
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
    print("✅ team_master テーブル作成完了（9列対応）")

def fetch_all_team_prompts():
    """全てのチームプロンプトを取得（9列対応）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ✅ 明示的に9列すべてを取得
    cursor.execute('''
        SELECT id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at 
        FROM team_master 
        ORDER BY team_name
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    print(f"🔍 取得されたチーム数: {len(rows)}件（9列対応）")
    return rows

def fetch_team_prompt_by_id(team_id):
    """ID指定でチーム情報を取得（9列対応）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ✅ 明示的に9列すべてを取得
    cursor.execute('''
        SELECT id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at 
        FROM team_master 
        WHERE id = ?
    ''', (team_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result

def update_team_prompt(team_id, name, key, text_prompt, audio_prompt, score_items, notes, is_active):
    """チームプロンプトを更新（updated_at自動更新）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        UPDATE team_master 
        SET team_name=?, prompt_key=?, text_prompt=?, audio_prompt=?, score_items=?, notes=?, is_active=?, updated_at=?
        WHERE id=?
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, is_active, current_time, team_id))
    
    conn.commit()
    conn.close()
    print(f"✅ チーム '{name}' (ID: {team_id}) を更新しました（{current_time}）")

def insert_team_prompt(name, key, text_prompt, audio_prompt, score_items, notes="", is_active=1):
    """新しいチームプロンプトを挿入（updated_at自動設定）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO team_master (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, is_active, current_time))
    
    conn.commit()
    conn.close()
    print(f"✅ 新しいチーム '{name}' を登録しました（{current_time}）")

def delete_team_prompt(team_id):
    """チームプロンプトを削除"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 削除前にチーム名を取得（ログ用）
    cursor.execute("SELECT team_name FROM team_master WHERE id = ?", (team_id,))
    result = cursor.fetchone()
    team_name = result[0] if result else f"ID:{team_id}"
    
    cursor.execute("DELETE FROM team_master WHERE id = ?", (team_id,))
    conn.commit()
    conn.close()
    print(f"✅ チーム '{team_name}' (ID: {team_id}) を削除しました")
