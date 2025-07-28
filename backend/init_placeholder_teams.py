# init_placeholder_teams.py（新規作成）
# import sqlite3
import json
from datetime import datetime
from mysql_connector import execute_query

# DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def init_placeholder_teams():
    """プレースホルダーチームをteam_masterに登録"""
    
    placeholder_teams = [
        {
            "team_name": "A_team",
            "prompt_key": "prompt_a_team", 
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 1  # ✅ 有効状態に変更
        },
        {
            "team_name": "B_team", 
            "prompt_key": "prompt_b_team",
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        },
        {
            "team_name": "C_team",
            "prompt_key": "prompt_c_team", 
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        },
        {
            "team_name": "F_team",
            "prompt_key": "prompt_f_team",
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        }
    ]
    
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    
    # team_masterテーブル作成
    execute_query('''
        CREATE TABLE IF NOT EXISTS team_master (
            id INT PRIMARY KEY AUTO_INCREMENT,
            team_name VARCHAR(50) UNIQUE NOT NULL,
            prompt_key VARCHAR(50) NOT NULL,
            text_prompt TEXT,
            audio_prompt TEXT,
            score_items TEXT,
            notes TEXT,
            is_active TINYINT DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    for team in placeholder_teams:
        try:
            execute_query('''
                INSERT INTO team_master 
                (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                text_prompt = VALUES(text_prompt),
                audio_prompt = VALUES(audio_prompt),
                score_items = VALUES(score_items),
                notes = VALUES(notes),
                is_active = VALUES(is_active),
                updated_at = CURRENT_TIMESTAMP
            ''', (
                team["team_name"],
                team["prompt_key"], 
                team["text_prompt"],
                team["audio_prompt"],
                team["score_items"],
                team["notes"],
                team["is_active"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            print(f"✅ プレースホルダーチーム '{team['team_name']}' を登録しました")
        except Exception as e:
            print(f"❌ {team['team_name']} 登録エラー: {e}")
    
    # conn.commit()
    # conn.close()
    print("🎉 プレースホルダーチーム初期化完了")

if __name__ == "__main__":
    init_placeholder_teams()