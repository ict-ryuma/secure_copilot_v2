import sqlite3
import hashlib
from typing import Tuple, List
import streamlit as st
import os

# === 絶対パス指定（どこからでも参照OK） ===
DB_PATH = os.path.join(os.path.dirname(__file__), "user_db.db")


# === パスワードをSHA256でハッシュ化 ===
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# === DB初期化（ユーザー・チームテーブル） ===
def init_auth_db():
    create_user_table()
    create_team_table()


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
            is_admin INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


# === チームテーブル作成（初期データあり） ===
def create_team_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            prompt_key TEXT
        );
    """)
    teams = [
        ("A_team", "主に新車商談を担当", "A_team"),
        ("B_team", "中古車・割賦メイン", "B_team")
    ]
    for name, desc, key in teams:
        cursor.execute("""
            INSERT OR IGNORE INTO teams (name, description, prompt_key)
            VALUES (?, ?, ?)
        """, (name, desc, key))
    conn.commit()
    conn.close()


# === チーム一覧（セレクトボックス用） ===
def get_all_teams() -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM teams")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


# === ユーザー登録 ===
def register_user(username: str, password: str, team_name: str, is_admin: bool = False) -> bool:
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
        return False
    finally:
        conn.close()


# === ログイン認証 ===
def login_user(username: str, password: str) -> Tuple[bool, str, bool]:
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


# === ユーザー存在チェック ===
def user_exists(username: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# === セッション中のユーザー情報取得 ===
def get_current_user():
    return {
        "username": st.session_state.get("username", ""),
        "team_name": st.session_state.get("team_name", ""),
        "is_admin": st.session_state.get("is_admin", False)
    }


# === 管理者権限の更新 ===
def update_user_role(username: str, is_admin: bool) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET is_admin = ? WHERE username = ?
    """, (int(is_admin), username))
    conn.commit()
    conn.close()
    return True


# === ユーザー削除 ===
def delete_user(username: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True
