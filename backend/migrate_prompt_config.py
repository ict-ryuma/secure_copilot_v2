# -*- coding: utf-8 -*-
# import sqlite3
import yaml
import os
import codecs
from datetime import datetime
from mysql_connector import execute_query

# === 定数（score_log.db に統一） ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # ~/secure_copilot_v2/
YAML_PATH = os.path.join(BASE_DIR, "prompt_config.yaml")
# DB_PATH = os.path.join(BASE_DIR, "score_log.db")  # ← 統一

# === YAML読み込み ===
def load_yaml_config():
    # Python 2.7/3.x 完全互換
    with codecs.open(YAML_PATH, mode="r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# === DBへマイグレーション ===
def migrate_to_db(config):
    common_score_items = config.get("score_items", [])
    score_items_str = ",".join(common_score_items)

    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()

    for team_name, data in config.items():
        if team_name == "score_items":
            continue

        if not isinstance(data, dict):
            print("⚠️ スキップ（形式不正）: {}".format(team_name))
            continue

        text_prompt = data.get("text_prompt", "")
        audio_prompt = data.get("audio_prompt", "")
        notes = data.get("notes", "")

    #    execute_query("""
    #         INSERT OR REPLACE INTO team_master (
    #             team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at
    #         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #     """, (
    #         team_name,
    #         team_name.lower(),
    #         text_prompt,
    #         audio_prompt,
    #         score_items_str,
    #         notes,
    #         1,
    #         datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     ))
    sql = """
        INSERT INTO team_master (
            team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            prompt_key = VALUES(prompt_key),
            text_prompt = VALUES(text_prompt),
            audio_prompt = VALUES(audio_prompt),
            score_items = VALUES(score_items),
            notes = VALUES(notes),
            is_active = VALUES(is_active),
            updated_at = VALUES(updated_at)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = (
        team_name,
        team_name.lower(),
        text_prompt,
        audio_prompt,
        score_items_str,
        notes,
        1,
        now
    )
    execute_query(sql, params)

        # print("✅ 移行済み: {}".format(team_name))

    # conn.commit()
    # conn.close()
    print("🎉 すべてのプロンプトをDBに移行しました！")

# === 実行 ===
if __name__ == "__main__":
    try:
        config = load_yaml_config()
        migrate_to_db(config)
    except IOError:
        print("❌ prompt_config.yaml が見つかりません")
    except Exception as e:
        print("❌ エラー: {}".format(str(e)))
