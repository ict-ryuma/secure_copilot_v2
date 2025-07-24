#!/usr/bin/env python3
"""ユーザーデータを score_log.db に統合（Macローカル / EC2 両対応）"""

import sqlite3
import os
import hashlib
from pathlib import Path
import platform

# --- パスを環境によって自動切替 ---
if "ec2-user" in os.getenv("HOME", ""):
    # EC2 環境
    BASE_DIR = "/home/ec2-user/secure_copilot_v2"
else:
    # Mac ローカル環境
    BASE_DIR = str(Path(__file__).resolve().parent)

OLD_USER_DB = os.path.join(BASE_DIR, "backend", "user_db.db")
NEW_DB = os.path.join(BASE_DIR, "score_log.db")

def migrate_users():
    """既存のユーザーデータを統合DBに移行"""

    print(f"🗂️ BASE_DIR = {BASE_DIR}")
    print(f"📁 OLD_USER_DB = {OLD_USER_DB}")
    print(f"📁 NEW_DB = {NEW_DB}")

    # 新DBにusersテーブル作成
    conn_new = sqlite3.connect(NEW_DB)
    cursor_new = conn_new.cursor()
    cursor_new.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            team_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn_new.commit()

    # 既存のユーザーDBがあれば移行
    if os.path.exists(OLD_USER_DB):
        print(f"🔄 既存ユーザーデータを移行: {OLD_USER_DB} → {NEW_DB}")

        conn_old = sqlite3.connect(OLD_USER_DB)
        cursor_old = conn_old.cursor()

        try:
            cursor_old.execute("SELECT username, password_hash, team_name, is_admin FROM users")
            users = cursor_old.fetchall()

            for user in users:
                try:
                    cursor_new.execute("""
                        INSERT OR REPLACE INTO users (username, password_hash, team_name, is_admin)
                        VALUES (?, ?, ?, ?)
                    """, user)
                    print(f"✅ 移行: {user[0]} (チーム: {user[2]})")
                except Exception as e:
                    print(f"❌ 移行エラー ({user[0]}): {e}")

            conn_new.commit()
            print(f"✅ {len(users)}人のユーザーを移行完了")

        except Exception as e:
            print(f"❌ 移行処理エラー: {e}")
        finally:
            conn_old.close()

    else:
        print("📝 新規セットアップ: 管理者ユーザーを作成します")
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()

        cursor_new.execute("""
            INSERT OR REPLACE INTO users (username, password_hash, team_name, is_admin)
            VALUES (?, ?, ?, ?)
        """, ("admin", admin_hash, "イネーブラー", 1))
        conn_new.commit()
        print("✅ 管理者ユーザー作成: admin / admin123")

    conn_new.close()


if __name__ == "__main__":
    migrate_users()
