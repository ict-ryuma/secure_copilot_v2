# import sqlite3
import hashlib
from typing import List, Dict, Tuple, Any, Union
import os
from backend.mysql_connector import execute_query,execute_modify_query,execute_query_with_dict_cursor
from logger_config import logger
from backend.teams import get_teams,get_user_team


def hash_password(password: str) -> str:
    """パスワードをSHA256でハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 統一チーム取得関数（プレースホルダー完全除外）
def get_all_teams_safe() -> List[str]:
    """
    teamsから有効なチームのみを取得
    全箇所でこの関数を使用することで一貫性を保つ
    """
    try:
        rows=execute_query("""
            SELECT DISTINCT id, team_name FROM teams
            WHERE is_active = 1 
            AND team_name IS NOT NULL
            AND team_name != ''
            ORDER BY team_name
        """, fetch=True)
        teams = [{"id": row[0], "team_name": row[1]} for row in rows]
        print(f"🔍 get_all_teams_safe取得結果: {teams}")
        print(f"DEBUG: result = {teams}")
        return teams
        
    except Exception as e:
        print(f"❌ get_all_teams_safe エラー: {str(e)}")
        return []
# def get_all_teams_safe() -> List[str]:
#     """
#     team_masterから有効なチームのみを取得
#     全箇所でこの関数を使用することで一貫性を保つ
#     """
#     try:
#         rows=execute_query("""
#             SELECT DISTINCT team_name FROM team_master 
#             WHERE is_active = 1 
#             AND team_name IS NOT NULL
#             AND team_name != ''
#             ORDER BY team_name
#         """, fetch=True)
#         teams = [row[0] for row in rows]
#         print(f"🔍 get_all_teams_safe取得結果: {teams}")
#         print(f"DEBUG: result = {teams}")
#         return teams
        
#     except Exception as e:
#         print(f"❌ get_all_teams_safe エラー: {str(e)}")
#         return []

# ✅ 旧関数は廃止予定（互換性のためラッパーとして残す）
def get_all_teams() -> List[str]:
    """
    ⚠️ 廃止予定：get_all_teams_safe()を使用してください
    """
    print("⚠️ get_all_teams()は廃止予定です。get_all_teams_safe()を使用してください。")
    return get_all_teams_safe()

def validate_team_comprehensive(team_name: str) -> Dict[str, any]:
    """
    チームの包括的検証（存在・有効性・プロンプト設定）
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
        # ✅ 1. 基本存在確認
        rows = execute_query("""
            SELECT team_name, is_active, text_prompt, audio_prompt, score_items 
            FROM team_master 
            WHERE team_name = %s
        """, (team_name,), fetch=True)
        result = rows[0] if (rows and len(rows) > 0) else None
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
        
        # ✅ 2. 有効性チェック
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
        
        # ✅ 3. プロンプト設定チェック
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
        
        # ✅ 4. 正常ケース
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

# def register_user(name,username: str, password: str, team_id: str, is_admin: bool = False,adm_user_id:int=None) -> Tuple[bool, str]:
def register_user(
        first_name: str,
        last_name: str,
        name: str,
        username: str,
        password: str,
        email: str,
        phone_no: str,
        team_id: str,
        is_admin: bool = False,
        adm_user_id: int = None) -> Tuple[bool, str]:
    """
    ユーザー登録（包括的チーム検証付き）
    """
    # ✅ 1. 入力検証
    if not name or not name.strip():
        return False, "名前が空です"
    if not username or not username.strip():
        return False, "ユーザー名が空です"
    if not password or len(password) < 4:
        return False, "パスワードは4文字以上である必要があります"
    if not team_id:
        return False, "チーム名が空です"
    
    username = username.strip()
    
    try:
        # ✅ 3. ユーザー重複チェック
        rows = execute_query("SELECT username FROM users WHERE username = %s", (username,), fetch=True)
        if rows and len(rows) > 0:
            return False, f"ユーザー名 '{username}' は既に登録されています"
        
        # ✅ 4. ユーザー登録実行
        hashed_password = hash_password(password)
        inserted=execute_query('''
            INSERT INTO users (first_name,last_name, name, username, password_hash, email, phone_no, is_admin, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, name, username, hashed_password, email, phone_no, is_admin, adm_user_id))

        # if inserted:
        userInfos = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch=True)
        user_id = userInfos[0][0] if (userInfos and len(userInfos) > 0) else None
        try:
            checking_teams = execute_query("SELECT * FROM user_has_teams WHERE user_id = %s AND team_id = %s", (user_id,team_id), fetch=True)
            if checking_teams and len(checking_teams) > 0:
                return False, f"ユーザー名 '{username}' はチーム既{team_id}に登録されています"
            execute_query('''
            INSERT INTO user_has_teams (user_id,team_id, created_by)
            VALUES (%s, %s, %s)
        ''', (user_id,team_id, adm_user_id))
        except Exception as e:
            print(f"❌ チーム登録エラー: {str(e)}")
            return False, f"登録中にエラーが発生しました: {str(e)}"

        print(f"✅ ユーザー登録成功: {username} → {team_id} (管理者: {is_admin})")
        return True, f"ユーザー '{username}' をチーム '{team_id}' に登録しました"
        
    except Exception as e:
        print(f"❌ ユーザー登録エラー: {str(e)}")
        return False, f"登録中にエラーが発生しました: {str(e)}"


def login_user(username: str, password: str) -> Tuple[bool, Any, str, bool]:
    """
    ユーザーログイン認証（基本認証のみ）
    戻り値: (成功フラグ, ユーザーID, チーム名, 管理者フラグ)
    """
    try:
        hashed_password = hash_password(password)
        rows = execute_query('''
            SELECT id,name, username, is_admin 
            FROM users 
            WHERE username = %s AND password_hash = %s
        ''', (username, hashed_password), fetch=True)

        result = rows[0] if (rows and len(rows) > 0) else None
        if result:
            id, name, username, is_admin = result
            try:
                team=get_user_team(id)
                # team = teams[0] if (teams and len(teams) > 0) else None
            except Exception as e:
                logger.error(f"❌ Team Error: {str(e)}")
                return False, "", "","", False,""
            print(f"✅ 基本認証成功: {username} → Name: {name}, 管理者: {bool(is_admin)}, id: {id}")
            return True, id,name, username, bool(is_admin),team
        else:
            print(f"❌ 基本認証失敗: {username}")
            return False, "", "","", False,""

    except Exception as e:
        print(f"❌ ログイン認証エラー: {str(e)}")
        return False,"","", "", False,""


def update_user_role(username: str, is_admin: bool, team_name: str = None) -> Tuple[bool, str]:
    """
    ユーザーの権限とチームを更新（チーム検証強化版）
    """
    # try:
        # ✅ チーム変更がある場合は検証
        # if team_name is not None:
            # team_validation = validate_team_comprehensive(team_name)
            # if not team_validation["valid"]:
            #     error_msg = team_validation["message"]
            #     suggestions = team_validation.get("suggestions", [])
            #     return False, f"{error_msg}\n対処法: {'; '.join(suggestions)}"
        
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()
        
        # if team_name is not None:
        #     execute_query('''
        #         UPDATE users 
        #         SET is_admin = %s, team_name = %s 
        #         WHERE username = %s
        #     ''', (int(is_admin), team_name, username))
        # else:
        #     execute_query('''
        #         UPDATE users 
        #         SET is_admin = %s 
        #         WHERE username = %s
        #     ''', (int(is_admin), username))

        # conn.commit()
        # conn.close()

        # update_msg = f"ユーザー '{username}' を更新しました"
        # if team_name:
        #     update_msg += f" (チーム: {team_name})"
        
        # print(f"✅ {update_msg}")
        # return True, update_msg
        
    # except Exception as e:
    #     error_msg = f"更新中にエラーが発生しました: {str(e)}"
    #     print(f"❌ {error_msg}")
    #     return False, error_msg
def update_user_has_team(user_has_team_id, user_id, team_id, created_by, username):
    try:
        # 既存チェック（同じユーザーが同じチームに重複登録されていないか）
        checking_teams = execute_query(
            """
            SELECT * FROM user_has_teams 
            WHERE user_id = %s AND team_id = %s AND id != %s
            """,
            (user_id, team_id, user_has_team_id),
            fetch=True
        )

        if checking_teams and len(checking_teams) > 0:
            return False, f"ユーザー '{username}' はチーム {team_id} に既に登録されています"

        # 正しい UPDATE 文
        execute_modify_query(
            """
            UPDATE user_has_teams
            SET user_id = %s, team_id = %s, created_by = %s
            WHERE id = %s
            """,
            (user_id, team_id, created_by, user_has_team_id)
        )

        return True, "✅ ユーザーのチーム情報を更新しました"

    except Exception as e:
        return False, f"チーム更新エラー: {str(e)}"

def update_user(id, first_name=None, last_name=None,name=None, username=None, password=None,email=None,phone_no=None, is_admin=None, created_by=None,user_has_team_id=None,team_id=None):
    """
    Update a users in the database.
    
    :param id: user ID to update
    :param team_id: Team ID
    :param username:Username ID
    :param is_admin: Admin status (optional)
    :return: status and message
    """
    updates = []
    params = []

    rows = execute_query("SELECT username FROM users WHERE username = %s and id != %s", (username,id), fetch=True)
    if rows and len(rows) > 0:
        return False, f"ユーザー名 '{username}' は既に登録されています"
    
    if name is not None:
        updates.append("name=%s")
        params.append(name)
    if username is not None:
        updates.append("username=%s")
        params.append(username)
    if password is not None:
        hashed_password = hash_password(password)
        updates.append("password=%s")
        params.append(hashed_password)
    if is_admin is not None:
        updates.append("is_admin=%s")
        params.append(is_admin)
    if created_by is not None:
        updates.append("created_by=%s")
        params.append(created_by)

    updates.append("first_name=%s")
    params.append(first_name)
    updates.append("last_name=%s")
    params.append(last_name)
    updates.append("email=%s")
    params.append(email)
    updates.append("phone_no=%s")
    params.append(phone_no)
    if not updates:
        # Nothing to update
        return 0

    params.append(id)
    query = f"""
        UPDATE users
        SET {', '.join(updates)}
        WHERE id=%s
    """
    try:
        execute_modify_query(query, tuple(params))
        return update_user_has_team(user_has_team_id, id, team_id, created_by, username)
    except Exception as e:
        return False, f"❌ 更新エラー: {e}"
    

def delete_user(username: str) -> bool:
    """ユーザー削除"""
    try:
        deleted=execute_query("DELETE FROM users WHERE username = %s", (username,))

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
        rows = execute_query("SELECT 1 FROM users WHERE username = %s", (username,), fetch=True)
        exists = bool(rows and len(rows) > 0)
        return exists
    except Exception as e:
        print(f"❌ ユーザー存在確認エラー: {str(e)}")
        return False

def get_current_user(username: str) -> Dict[str, any]:
    """現在のユーザー情報取得（チーム検証付き）"""
    try:
        rows = execute_query('''
            SELECT username, team_name, is_admin 
            FROM users 
            WHERE username = %s
        ''', (username,), fetch=True)
        result = rows[0] if (rows and len(rows) > 0) else None

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

def get_all_users(user_id: int = None) -> Union[List[Dict[str, any]], Dict[str, any]]:
    """
    Get all users or a specific user by ID.
    Returns a list of user dicts if no user_id is given,
    or a single user dict if user_id is provided.
    """
    try:
        if user_id:
            query = '''
                SELECT u.id as user_id,u.name, u.first_name, u.last_name,u.email,u.phone_no,u.username,uht.id as user_has_team_id, t.id as team_id, t.team_name, u.is_admin
                FROM users as u
                INNER JOIN user_has_teams as uht ON uht.user_id=u.id
                INNER JOIN teams as t ON t.id=uht.team_id
                WHERE u.id = %s
            '''
            rows = execute_query_with_dict_cursor(query, (user_id,), fetch=True)
            if not rows:
                return {"error": f"User with ID {user_id} not found."}
            user_info = rows[0]
            return user_info
        else:
            query = '''
                SELECT u.id as user_id, u.name,u.first_name, u.last_name,u.email,u.phone_no,u.username,uht.id as user_has_team_id, t.id as team_id, t.team_name, u.is_admin
                FROM users as u
                INNER JOIN user_has_teams as uht ON uht.user_id=u.id
                INNER JOIN teams as t ON t.id=uht.team_id
            '''
            rows = execute_query_with_dict_cursor(query, fetch=True)
            users = []
            for row in rows:
                users.append(row)
            return users

    except Exception as e:
        return {"error": f"Error retrieving user(s): {str(e)}"}

# ✅ 診断・デバッグ関数
def diagnose_team_integrity() -> Dict[str, any]:
    """チーム整合性の包括診断"""
    try:
        # 全ユーザー取得
        rows = execute_query("SELECT username, team_name, is_admin FROM users", fetch=True)
        users = rows if (rows and len(rows) > 0) else []

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
        return diagnosis
        
    except Exception as e:
        return {"error": f"診断エラー: {str(e)}"}

# if __name__ == "__main__":
    # テスト実行
    # print("🧪 auth.py 統合テスト")
    # print(f"有効チーム: {get_all_teams_safe()}")
    
    # # 診断実行
    # diagnosis = diagnose_team_integrity()
    # print(f"診断結果: {diagnosis}")
