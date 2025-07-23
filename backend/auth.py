import sqlite3
import hashlib
from typing import Tuple, List
import os

# === 相対パス指定（backend/user_db.db） ===
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend/user_db.db")

# ✅ デバッグ用：パス確認
print(f"🔍 auth.py DB_PATH: {DB_PATH}")

# === パスワードをSHA256でハッシュ化 ===
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# === DB初期化（ユーザーテーブルのみ） ===
def init_auth_db():
    create_user_table()

# === ユーザーテーブル作成 ===
def create_user_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            team_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# === チーム一覧取得（エラーハンドリング追加） ===
def get_all_teams() -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT team_name FROM teams")
        rows = cursor.fetchall()
        return [r[0] for r in rows]
    except sqlite3.OperationalError as e:
        print("❌ teams テーブルエラー: {}".format(str(e)))
        return ["A_team", "B_team", "C_team", "F_team"]
    finally:
        conn.close()

# === ユーザー登録 ===
def register_user(username, password, team_name, is_admin=False):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, team_name, is_admin)
            VALUES (?, ?, ?, ?)
        """, (username, hash_password(password), team_name, int(is_admin)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print("❌ ユーザー登録失敗: {} は既に存在します".format(username))
        return False
    except Exception as e:
        print("❌ ユーザー登録エラー: {}".format(str(e)))
        return False
    finally:
        conn.close()

# === ログイン認証 ===
def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password_hash, team_name, is_admin
        FROM users
        WHERE username = ?
    """, (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True, row[1], bool(row[2])
    else:
        return False, "", False

# === ユーザー存在確認 ===
def user_exists(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# === 管理者権限更新 ===
def update_user_role(username, is_admin):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_admin = ? WHERE username = ?
        """, (int(is_admin), username))
        conn.commit()
        return True
    except Exception as e:
        print("❌ 権限更新エラー: {}".format(str(e)))
        return False
    finally:
        conn.close()

# === ユーザー削除 ===
def delete_user(username):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return True
    except Exception as e:
        print("❌ ユーザー削除エラー: {}".format(str(e)))
        return False
    finally:
        conn.close()

# === chat_secure_gpt.py 用ログイン認証ラッパー ===
def verify_user(username, password):
    print("🛂 verify_user() called with username='{}'".format(username))
    
    success, team_name, is_admin = login_user(username, password)
    print("✅ login_user result: success={}, team_name='{}', is_admin={}".format(success, team_name, is_admin))

    if not success:
        print("❌ 認証失敗: パスワード不一致またはユーザー存在しない")
        return False, {}

    return True, {
        "team_name": team_name,
        "is_admin": is_admin
    }

# === ユーザー情報取得 ===
def get_current_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, team_name, is_admin
        FROM users
        WHERE username = ?
    """, (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "username": row[0],
            "team_name": row[1],
            "is_admin": bool(row[2])
        }
    else:
        raise ValueError("指定されたユーザーが存在しません")
