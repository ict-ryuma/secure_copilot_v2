# backend/db_team_master.py

# import sqlite3
import json
from datetime import datetime
import os
from .mysql_connector import execute_query


def fetch_all_team_prompts():
    """全てのチームプロンプトを取得（9列対応）"""

    # ✅ 明示的に9列すべてを取得
    rows = execute_query('''
        SELECT id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at 
        FROM team_master 
        ORDER BY team_name
    ''', fetch=True)
    
    print(f"🔍 取得されたチーム数: {len(rows)}件（9列対応）")
    return rows

def fetch_team_prompt_by_id(team_id):
    """ID指定でチーム情報を取得（9列対応）"""
    
    # ✅ 明示的に9列すべてを取得
    rows = execute_query('''
        SELECT id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at 
        FROM team_master 
        WHERE id = %s
    ''', (team_id,), fetch=True)
    result = rows[0] if rows else None
    
    return result

def update_team_prompt(team_id, name, key, text_prompt, audio_prompt, score_items, notes, is_active):
    """チームプロンプトを更新（updated_at自動更新）"""
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    execute_query('''
        UPDATE team_master
        SET team_name=%s, prompt_key=%s, text_prompt=%s, audio_prompt=%s, score_items=%s, notes=%s, is_active=%s, updated_at=%s
        WHERE id=%s
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, is_active, current_time, team_id))
    
    print(f"✅ チーム '{name}' (ID: {team_id}) を更新しました（{current_time}）")

def insert_team_prompt(name, key, text_prompt, audio_prompt, score_items, notes="", is_active=1):
    """新しいチームプロンプトを挿入（updated_at自動設定）"""

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    execute_query('''
        INSERT INTO team_master (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (name, key, text_prompt, audio_prompt, score_items, notes, is_active, current_time))

    print(f"✅ 新しいチーム '{name}' を登録しました（{current_time}）")

def delete_team_prompt(team_id):
    """チームプロンプトを削除"""
    
    # 削除前にチーム名を取得（ログ用）
    rows = execute_query("SELECT team_name FROM team_master WHERE id = %s", (team_id,), fetch=True)

    team_name = rows[0][0] if rows else f"ID:{team_id}"

    execute_query("DELETE FROM team_master WHERE id = %s", (team_id,))
    print(f"✅ チーム '{team_name}' (ID: {team_id}) を削除しました")

