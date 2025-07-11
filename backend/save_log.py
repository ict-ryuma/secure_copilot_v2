import sqlite3
from datetime import datetime

DB_PATH = "score_log.db"

def init_db():
    """初回起動時にDBとテーブルを作成"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT,
            member_name TEXT,
            result TEXT,
            rapport INTEGER,
            presentation INTEGER,
            closing INTEGER,
            hearing INTEGER,
            objection INTEGER,
            strengths TEXT,
            improvements TEXT,
            cautions TEXT,
            actions TEXT,
            gpt_output TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def already_logged(deal_id: str, member_name: str) -> bool:
    """既に同一商談IDと営業名の組み合わせが登録済みかチェック"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM evaluations WHERE deal_id=? AND member_name=?",
        (deal_id, member_name)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_evaluation(deal_id, member_name, result, parsed, gpt_output):
    """評価結果をDBに保存"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluations (
            deal_id, member_name, result,
            rapport, presentation, closing, hearing, objection,
            strengths, improvements, cautions, actions,
            gpt_output, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        deal_id,
        member_name,
        result,
        parsed["scores"]["ラポール構築"],
        parsed["scores"]["プレゼンテーション"],
        parsed["scores"]["クロージング"],
        parsed["scores"]["ヒアリング"],
        parsed["scores"]["異議処理"],
        parsed["strengths"],
        parsed["improvements"],
        parsed["cautions"],
        parsed["actions"],
        gpt_output,
        datetime.now()
    ))
    conn.commit()
    conn.close()
