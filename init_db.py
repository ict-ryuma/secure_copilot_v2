# backend/init_db.py
from backend.auth import init_auth_db
from backend.init_db_teams import create_team_table

if __name__ == "__main__":
    print("🔧 データベース初期化を開始...")
    
    # ユーザーDB初期化
    init_auth_db()
    print("✅ ユーザーDB初期化完了")
    
    # チームDB初期化
    create_team_table()
    print("✅ チームDB初期化完了")
    
    print("🎉 すべてのDBを初期化しました")
