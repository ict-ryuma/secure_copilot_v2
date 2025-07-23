import sqlite3
import os
import json

# === 相対パス指定（score_log.db に統一） ===
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")

def parse_score_items(score_items_str):
    """score_items文字列を安全にリストに変換"""
    if not score_items_str:
        return []
    
    score_items_str = score_items_str.strip()
    
    # 1. JSON形式として試行
    if score_items_str.startswith('[') and score_items_str.endswith(']'):
        try:
            return json.loads(score_items_str)
        except json.JSONDecodeError:
            print(f"⚠️ JSON形式のパースに失敗: {score_items_str}")
    
    # 2. カンマ区切り文字列として処理
    items = []
    for item in score_items_str.split(','):
        cleaned = item.strip().strip('"').strip("'").strip('[]')
        if cleaned:
            items.append(cleaned)
    
    return items

def get_prompts_for_team(team_name):
    """DBからチームのプロンプトを取得（管理画面の変更を即座に反映）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT text_prompt, audio_prompt, score_items, notes
            FROM team_master 
            WHERE team_name = ? AND is_active = 1
        """, (team_name,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("チーム '{}' のプロンプト設定が見つかりません、または無効化されています".format(team_name))
        
        # ✅ 安全なscore_itemsパース
        score_items_list = parse_score_items(result[2])
        
        print(f"🔍 team_name: {team_name}")
        print(f"🔍 raw score_items: {result[2]}")
        print(f"🔍 parsed score_items: {score_items_list}")
        
        return {
            "text_prompt": result[0] or "",
            "audio_prompt": result[1] or "", 
            "score_items": score_items_list,
            "notes": result[3] or ""
        }
        
    finally:
        conn.close()

# 旧YAML対応（後方互換性のため一時保持）
def load_prompt_config():
    """非推奨: YAMLからの読み込み"""
    import yaml
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt_config.yaml")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except:
        print("⚠️ prompt_config.yaml が見つかりません。DB方式に移行してください。")
        return {}
