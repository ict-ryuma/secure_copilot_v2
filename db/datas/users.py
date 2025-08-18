from backend.mysql_connector import execute_query
import hashlib
def migrate_users(name,username, password, is_admin=False):
    """ユーザーデータをMySQLに移行"""

    print("🗂️ 環境: MySQL")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        execute_query("""
            INSERT INTO users (name,username, password_hash, is_admin)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            password_hash = VALUES(password_hash),
            name = VALUES(name),
            is_admin = VALUES(is_admin)
        """, (name,username, password_hash, is_admin))
        print("✅ 管理者ユーザー作成: admin / admin123")
    except Exception as e:
        print(f"❌ 管理者ユーザー作成エラー: {e}")