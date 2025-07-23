import sqlite3
import json
import os
from datetime import datetime

# === 相対パス指定（score_log.db に統一） ===
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")

def init_db():
    """評価ログテーブルを初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT,
            member_name TEXT,
            outcome TEXT,
            scores TEXT,
            raw_output TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_evaluation(deal_id, member_name, outcome, parsed_data, raw_output):
    """評価結果をDBに保存"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluation_logs (deal_id, member_name, outcome, scores, raw_output)
        VALUES (?, ?, ?, ?, ?)
    ''', (deal_id, member_name, outcome, json.dumps(parsed_data, ensure_ascii=False), raw_output))
    conn.commit()
    conn.close()

def already_logged(deal_id, member_name):
    """既に同じ評価が保存されているかチェック"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM evaluation_logs 
        WHERE deal_id = ? AND member_name = ?
    ''', (deal_id, member_name))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def get_all_evaluations():
    """全評価ログを取得"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_logs ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows
