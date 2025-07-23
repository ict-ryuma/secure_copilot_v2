# backend/init_db.py
from backend.auth import init_auth_db
from backend.init_db_teams import create_team_table

if __name__ == "__main__":
    init_auth_db()
    create_team_table()
    print("✅ ユーザーとチームのDBを初期化しました")
