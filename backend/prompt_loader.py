# import sqlite3
import json
import os
from pathlib import Path
from mysql_connector import execute_query


# ✅ 統一DBパス
# DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def get_prompts_for_team(team_name: str) -> dict:
    """
    フロントエンド用：チーム別プロンプト取得（包括的検証版）
    """
    print(f"🚀 get_prompts_for_team 開始: team_name='{team_name}'")
    
    # ✅ 1. auth.pyの包括的検証を使用
    try:
        from backend.auth import validate_team_comprehensive
        
        validation = validate_team_comprehensive(team_name)
        
        if not validation["valid"]:
            # エラー情報をそのまま返す
            return {
                "error": True,
                "error_type": validation["reason"],
                "message": validation["message"],
                "suggestions": validation.get("suggestions", []),
                "team_name": team_name
            }
        
        # ✅ 2. プロンプト取得（検証済みチームのみ）
        prompts = get_team_prompts_verified(team_name)
        
        if prompts.get("error", False):
            return prompts
        
        # ✅ 3. 正常ケース
        prompts["error"] = False
        print(f"✅ get_prompts_for_team 成功: {team_name}")
        return prompts
        
    except ImportError:
        # auth.pyが利用できない場合のフォールバック
        print("⚠️ auth.py の包括検証が利用できません。基本検証を使用します。")
        return get_team_prompts_fallback(team_name)
    except Exception as e:
        print(f"❌ get_prompts_for_team システムエラー: {str(e)}")
        return {
            "error": True,
            "error_type": "system_error",
            "message": f"システムエラー: {str(e)}",
            "suggestions": ["システム管理者にお問い合わせください"],
            "team_name": team_name
        }

def get_team_prompts_verified(team_name: str) -> dict:
    """検証済みチームからプロンプト設定を取得"""
    
    try:
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()
        
        # ✅ 検証済みチームから取得
        rows = execute_query("""
            SELECT id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at
            FROM team_master
            WHERE team_name = %s AND is_active = %s
        """, (team_name, 1), fetch=True)

        if not rows:
            return {
                "error": True,
                "error_type": "data_not_found",
                "message": f"チーム '{team_name}' のデータが見つかりません",
                "suggestions": ["データベースの整合性を確認してください"]
            }
        
        # ✅ データ展開（9列対応）
        team_id, team_name_db, prompt_key, text_prompt, audio_prompt, score_items_raw, notes, is_active, updated_at = result
        
        # ✅ score_items の安全な変換
        score_items = parse_score_items_safe(score_items_raw)
        
        return {
            "team_name": team_name_db,
            "prompt_key": prompt_key or f"default_{team_name.lower()}",
            "text_prompt": text_prompt or "デフォルトテキスト評価プロンプト",
            "audio_prompt": audio_prompt or "デフォルト音声評価プロンプト",
            "score_items": score_items,
            "notes": notes or "",
            "updated_at": updated_at or "不明",
            "error": False
        }
        
    except Exception as e:
        print(f"❌ get_team_prompts_verified エラー: {str(e)}")
        return {
            "error": True,
            "error_type": "database_error",
            "message": f"データベースエラー: {str(e)}",
            "suggestions": ["データベース接続を確認してください"]
        }

def parse_score_items_safe(score_items_raw) -> list:
    """score_items の安全な解析"""
    
    if not score_items_raw:
        return ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"]
    
    try:
        # JSON形式の場合
        if isinstance(score_items_raw, str) and score_items_raw.strip().startswith('['):
            return json.loads(score_items_raw)
        
        # カンマ区切り文字列の場合
        if isinstance(score_items_raw, str):
            items = [item.strip() for item in score_items_raw.split(',') if item.strip()]
            return items if items else ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"]
        
        # リスト形式の場合
        if isinstance(score_items_raw, list):
            return score_items_raw
        
        # その他の場合はデフォルト
        return ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"]
        
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        print(f"⚠️ score_items解析エラー: {score_items_raw} - {str(e)}")
        return ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"]

def get_team_prompts_fallback(team_name: str) -> dict:
    """フォールバック用の基本プロンプト取得"""
    
    if not team_name or not team_name.strip():
        return {
            "error": True,
            "error_type": "invalid_input",
            "message": "チーム名が指定されていません",
            "suggestions": ["有効なチーム名を指定してください"]
        }
    
    try:
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()

        rows = execute_query("""
            SELECT team_name, is_active 
            FROM team_master 
            WHERE team_name = %s
        """, (team_name,))
        result = rows[0] if rows else None

        if not result:
            return {
                "error": True,
                "error_type": "team_not_found",
                "message": f"チーム '{team_name}' が見つかりません",
                "suggestions": ["管理者にチーム登録を依頼してください"]
            }
        
        if result[1] != 1:
            return {
                "error": True,
                "error_type": "team_inactive",
                "message": f"チーム '{team_name}' は無効化されています",
                "suggestions": ["管理者にチーム有効化を依頼してください"]
            }
        
        # プロンプト取得
        return get_team_prompts_verified(team_name)
        
    except Exception as e:
        return {
            "error": True,
            "error_type": "system_error",
            "message": f"システムエラー: {str(e)}",
            "suggestions": ["システム管理者にお問い合わせください"]
        }

def get_available_teams_for_user() -> list:
    """ユーザーが選択可能なアクティブチーム一覧（統一版）"""
    try:
        import backend.auth
        return backend.auth.get_all_teams_safe()
        # from backend.auth import get_all_teams_safe
        # return get_all_teams_safe()
    except ImportError:
        # フォールバック
        try:
            # conn = sqlite3.connect(DB_PATH)
            # cursor = conn.cursor()
            rows = execute_query("""
                SELECT DISTINCT team_name FROM team_master 
                WHERE is_active = 1 
                AND team_name NOT IN ('A_team', 'B_team', 'C_team', 'F_team')
                ORDER BY team_name
            """)
            teams = [row[0] for row in rows]
            print(f"🔍 get_all_teams_safe取得結果: {teams}")
            return teams
        except Exception as e:
            print(f"❌ get_available_teams_for_user エラー: {e}")
            return []

# ✅ デバッグ・診断関数
def diagnose_prompts_system():
    """プロンプトシステムの包括診断"""
    try:
        from backend.auth import diagnose_team_integrity, get_all_teams_safe
        
        # チーム整合性診断
        team_diagnosis = diagnose_team_integrity()
        
        # プロンプト取得テスト
        available_teams = get_all_teams_safe()
        prompt_tests = []
        
        for team in available_teams[:3]:  # 最大3チームをテスト
            result = get_prompts_for_team(team)
            prompt_tests.append({
                "team": team,
                "success": not result.get("error", False),
                "error_type": result.get("error_type", "none"),
                "message": result.get("message", "OK")
            })
        
        return {
            "team_diagnosis": team_diagnosis,
            "available_teams": available_teams,
            "prompt_tests": prompt_tests,
            # "db_path": DB_PATH
        }
        
    except Exception as e:
        return {"error": f"診断エラー: {str(e)}"}

if __name__ == "__main__":
    # 診断実行
    print("🧪 prompt_loader.py 包括診断")
    diagnosis = diagnose_prompts_system()
    print(f"診断結果: {diagnosis}")
