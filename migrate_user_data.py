#!/usr/bin/env python3
"""ユーザーデータをMySQLに統合"""

import sys
import os
import hashlib
from pathlib import Path

# backend モジュールのパスを追加
sys.path.append(str(Path(__file__).resolve().parent))

from backend.mysql_connector import execute_query

print("✅ MySQL設定で起動")

def migrate_users():
    """ユーザーデータをMySQLに移行"""

    print("🗂️ 環境: MySQL")

    # usersテーブル作成
    execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            team_name VARCHAR(50) NOT NULL,
            is_admin TINYINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    print("✅ 管理者ユーザーを作成します")
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()

    try:
        execute_query("""
            INSERT INTO users (username, password_hash, team_name, is_admin)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            password_hash = VALUES(password_hash),
            team_name = VALUES(team_name),
            is_admin = VALUES(is_admin)
        """, ("admin", admin_hash, "イネーブラー", 1))
        print("✅ 管理者ユーザー作成: admin / admin123")
    except Exception as e:
        print(f"❌ 管理者ユーザー作成エラー: {e}")

def create_additional_user(username, password, team_name, is_admin=False):
    """追加ユーザーを作成"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        execute_query("""
            INSERT INTO users (username, password_hash, team_name, is_admin)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            password_hash = VALUES(password_hash),
            team_name = VALUES(team_name),
            is_admin = VALUES(is_admin)
        """, (username, password_hash, team_name, int(is_admin)))
        print(f"✅ ユーザー作成: {username} (チーム: {team_name})")
        return True
    except Exception as e:
        print(f"❌ ユーザー作成エラー ({username}): {e}")
        return False

def list_users():
    """全ユーザーを表示"""
    try:
        users = execute_query("SELECT username, team_name, is_admin FROM users ORDER BY username", fetch=True)
        print("\n📋 登録ユーザー一覧:")
        for user in users:
            admin_flag = "👑 管理者" if user[2] else "👤 一般"
            print(f"  - {user[0]} (チーム: {user[1]}) {admin_flag}")
        return users
    except Exception as e:
        print(f"❌ ユーザー一覧取得エラー: {e}")
        return []


if __name__ == "__main__":
    migrate_users()
    
    # 追加ユーザー例
    create_additional_user("ryuma", "star76", "A_team", True)
    create_additional_user("user1", "password1", "B_team", False)
    
    # ユーザー一覧表示
    list_users()
