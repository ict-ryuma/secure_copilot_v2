import sqlite3
import hashlib
from typing import List, Dict, Tuple
import os

# ✅ 統一DBパス
DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def hash_password(password: str) -> str:
    """パスワードをSHA256でハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth_db():
    """ユーザーDBの初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            team_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ ユーザーDBを初期化しました: {DB_PATH}")

# ✅ 統一チーム取得関数（プレースホルダー完全除外）
def get_all_teams_safe() -> List[str]:
    """
    team_masterから有効なチームのみを取得（プレースホルダー完全除外）
    全箇所でこの関数を使用することで一貫性を保つ
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT team_name FROM team_master 
            WHERE is_active = 1 
            AND team_name NOT IN ('A_team', 'B_team', 'C_team', 'F_team')
            AND team_name IS NOT NULL
            AND team_name != ''
            ORDER BY team_name
        """)
        teams = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"🔍 get_all_teams_safe取得結果: {teams}")
        return teams
        
    except Exception as e:
        print(f"❌ get_all_teams_safe エラー: {str(e)}")
        return []

# ✅ 旧関数は廃止予定（互換性のためラッパーとして残す）
def get_all_teams() -> List[str]:
    """
    ⚠️ 廃止予定：get_all_teams_safe()を使用してください
    """
    print("⚠️ get_all_teams()は廃止予定です。get_all_teams_safe()を使用してください。")
    return get_all_teams_safe()

def validate_team_comprehensive(team_name: str) -> Dict[str, any]:
    """
    チームの包括的検証（存在・有効性・プレースホルダー・プロンプト設定）
    """
    if not team_name or not team_name.strip():
        return {
            "valid": False,
            "reason": "empty_team_name",
            "message": "チーム名が空です",
            "suggestions": ["有効なチーム名を指定してください"]
        }
    
    team_name = team_name.strip()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # ✅ 1. 基本存在確認
        cursor.execute("""
            SELECT team_name, is_active, text_prompt, audio_prompt, score_items 
            FROM team_master 
            WHERE team_name = ?
        """, (team_name,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            available_teams = get_all_teams_safe()
            return {
                "valid": False,
                "reason": "team_not_found",
                "message": f"チーム '{team_name}' は team_master に登録されていません",
                "suggestions": [
                    "管理者にチーム登録を依頼してください",
                    f"利用可能なチーム: {', '.join(available_teams) if available_teams else 'なし'}"
                ]
            }
        
        team_name_db, is_active, text_prompt, audio_prompt, score_items = result
        
        # ✅ 2. プレースホルダーチェック
        if team_name in ['A_team', 'B_team', 'C_team', 'F_team']:
            available_teams = get_all_teams_safe()
            return {
                "valid": False,
                "reason": "placeholder_team",
                "message": f"'{team_name}' はプレースホルダーチームです",
                "suggestions": [
                    "実際のチームに変更してください",
                    f"利用可能なチーム: {', '.join(available_teams) if available_teams else 'なし'}"
                ]
            }
        
        # ✅ 3. 有効性チェック
        if is_active != 1:
            available_teams = get_all_teams_safe()
            return {
                "valid": False,
                "reason": "team_inactive",
                "message": f"チーム '{team_name}' は無効化されています",
                "suggestions": [
                    "管理者にチームの有効化を依頼してください",
                    f"他の有効なチーム: {', '.join(available_teams) if available_teams else 'なし'}"
                ]
            }
        
        # ✅ 4. プロンプト設定チェック
        missing_prompts = []
        if not text_prompt or text_prompt.strip() == "":
            missing_prompts.append("text_prompt")
        if not audio_prompt or audio_prompt.strip() == "":
            missing_prompts.append("audio_prompt")
        if not score_items or score_items.strip() == "":
            missing_prompts.append("score_items")
        
        if missing_prompts:
            return {
                "valid": False,
                "reason": "prompt_incomplete",
                "message": f"チーム '{team_name}' のプロンプト設定が不完全です",
                "missing_fields": missing_prompts,
                "suggestions": [
                    "管理者にプロンプト設定の完了を依頼してください",
                    f"不足項目: {', '.join(missing_prompts)}"
                ]
            }
        
        # ✅ 5. 正常ケース
        return {
            "valid": True,
            "reason": "ok",
            "message": f"チーム '{team_name}' は正常です",
            "team_data": {
                "team_name": team_name_db,
                "is_active": is_active,
                "has_text_prompt": bool(text_prompt),
                "has_audio_prompt": bool(audio_prompt),
                "has_score_items": bool(score_items)
            }
        }
        
    except Exception as e:
        return {
            "valid": False,
            "reason": "system_error",
            "message": f"チーム検証中にシステムエラーが発生しました: {str(e)}",
            "suggestions": ["システム管理者にお問い合わせください"]
        }

def register_user(username: str, password: str, team_name: str, is_admin: bool = False) -> Tuple[bool, str]:
    """
    ユーザー登録（包括的チーム検証付き）
    """
    # ✅ 1. 入力検証
    if not username or not username.strip():
        return False, "ユーザー名が空です"
    if not password or len(password) < 4:
        return False, "パスワードは4文字以上である必要があります"
    
    username = username.strip()
    team_name = team_name.strip() if team_name else ""
    
    # ✅ 2. チーム包括検証
    team_validation = validate_team_comprehensive(team_name)
    if not team_validation["valid"]:
        error_msg = team_validation["message"]
        suggestions = team_validation.get("suggestions", [])
        full_message = f"{error_msg}\n対処法: {'; '.join(suggestions)}"
        return False, full_message
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # ✅ 3. ユーザー重複チェック
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, f"ユーザー名 '{username}' は既に登録されています"
        
        # ✅ 4. ユーザー登録実行
        hashed_password = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, team_name, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (username, hashed_password, team_name, is_admin))
        
        conn.commit()
        conn.close()
        
        print(f"✅ ユーザー登録成功: {username} → {team_name} (管理者: {is_admin})")
        return True, f"ユーザー '{username}' をチーム '{team_name}' に登録しました"
        
    except Exception as e:
        print(f"❌ ユーザー登録エラー: {str(e)}")
        return False, f"登録中にエラーが発生しました: {str(e)}"

def login_user(username: str, password: str) -> Tuple[bool, str, bool]:
    """
    ユーザーログイン認証（基本認証のみ）
    戻り値: (成功フラグ, チーム名, 管理者フラグ)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        hashed_password = hash_password(password)
        cursor.execute('''
            SELECT username, team_name, is_admin 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, hashed_password))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            username_db, team_name, is_admin = result
            print(f"✅ 基本認証成功: {username_db} → チーム: {team_name}, 管理者: {bool(is_admin)}")
            return True, team_name, bool(is_admin)
        else:
            print(f"❌ 基本認証失敗: {username}")
            return False, "", False
            
    except Exception as e:
        print(f"❌ ログイン認証エラー: {str(e)}")
        return False, "", False

def verify_user(username: str, password: str) -> Tuple[bool, Dict[str, any]]:
    """
    ユーザー認証（基本認証 + チーム検証）
    """
    # ✅ 1. 基本認証
    is_valid, user_info = login_user(username, password)
    
    if not is_valid:
        return False, {"error": "認証に失敗しました"}
    
    # ✅ 2. チーム包括検証
    team_name = user_info.get("team_name", "")
    team_validation = validate_team_comprehensive(team_name)
    
    if not team_validation["valid"]:
        print(f"⚠️ ログイン後チーム検証失敗: {team_validation['message']}")
        # チーム問題情報を追加
        user_info.update({
            "team_error": team_validation["reason"],
            "team_message": team_validation["message"],
            "team_suggestions": team_validation.get("suggestions", [])
        })
    else:
        print(f"✅ ログイン後チーム検証成功: {team_name}")
    
    return is_valid, user_info

def update_user_role(username: str, is_admin: bool, team_name: str = None) -> Tuple[bool, str]:
    """
    ユーザーの権限とチームを更新（チーム検証強化版）
    """
    try:
        # ✅ チーム変更がある場合は検証
        if team_name is not None:
            team_validation = validate_team_comprehensive(team_name)
            if not team_validation["valid"]:
                error_msg = team_validation["message"]
                suggestions = team_validation.get("suggestions", [])
                return False, f"{error_msg}\n対処法: {'; '.join(suggestions)}"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if team_name is not None:
            cursor.execute('''
                UPDATE users 
                SET is_admin = ?, team_name = ? 
                WHERE username = ?
            ''', (int(is_admin), team_name, username))
        else:
            cursor.execute('''
                UPDATE users 
                SET is_admin = ? 
                WHERE username = ?
            ''', (int(is_admin), username))
        
        conn.commit()
        conn.close()
        
        update_msg = f"ユーザー '{username}' を更新しました"
        if team_name:
            update_msg += f" (チーム: {team_name})"
        
        print(f"✅ {update_msg}")
        return True, update_msg
        
    except Exception as e:
        error_msg = f"更新中にエラーが発生しました: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def delete_user(username: str) -> bool:
    """ユーザー削除"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        if deleted:
            print(f"✅ ユーザー '{username}' を削除しました")
        else:
            print(f"⚠️ ユーザー '{username}' が見つかりませんでした")
        
        return deleted
        
    except Exception as e:
        print(f"❌ ユーザー削除エラー: {str(e)}")
        return False

def user_exists(username: str) -> bool:
    """ユーザー存在確認"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except Exception as e:
        print(f"❌ ユーザー存在確認エラー: {str(e)}")
        return False

def get_current_user(username: str) -> Dict[str, any]:
    """現在のユーザー情報取得（チーム検証付き）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, team_name, is_admin 
            FROM users 
            WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"error": f"ユーザー '{username}' が見つかりません"}
        
        user_info = {
            "username": result[0],
            "team_name": result[1],
            "is_admin": bool(result[2])
        }
        
        # ✅ チーム検証追加
        team_validation = validate_team_comprehensive(result[1])
        user_info["team_validation"] = team_validation
        
        return user_info
        
    except Exception as e:
        return {"error": f"ユーザー情報取得エラー: {str(e)}"}

# ✅ 診断・デバッグ関数
def diagnose_team_integrity() -> Dict[str, any]:
    """チーム整合性の包括診断"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 全ユーザー取得
        cursor.execute("SELECT username, team_name, is_admin FROM users")
        users = cursor.fetchall()
        
        # 有効チーム取得
        valid_teams = get_all_teams_safe()
        
        # 診断結果
        diagnosis = {
            "total_users": len(users),
            "valid_teams": valid_teams,
            "valid_team_count": len(valid_teams),
            "user_issues": [],
            "summary": {}
        }
        
        # ユーザー別診断
        issue_count = 0
        for username, team_name, is_admin in users:
            team_validation = validate_team_comprehensive(team_name)
            
            if not team_validation["valid"]:
                issue_count += 1
                diagnosis["user_issues"].append({
                    "username": username,
                    "team_name": team_name,
                    "is_admin": bool(is_admin),
                    "issue_type": team_validation["reason"],
                    "message": team_validation["message"],
                    "suggestions": team_validation.get("suggestions", [])
                })
        
        # サマリー作成
        diagnosis["summary"] = {
            "healthy_users": len(users) - issue_count,
            "problematic_users": issue_count,
            "health_percentage": round((len(users) - issue_count) / len(users) * 100, 1) if users else 100
        }
        
        conn.close()
        return diagnosis
        
    except Exception as e:
        return {"error": f"診断エラー: {str(e)}"}

if __name__ == "__main__":
    # テスト実行
    print("🧪 auth.py 統合テスト")
    print(f"有効チーム: {get_all_teams_safe()}")
    
    # 診断実行
    diagnosis = diagnose_team_integrity()
    print(f"診断結果: {diagnosis}")
