# init_complete_system.py（完全版）

from backend.auth import init_auth_db
from backend.init_db_teams import create_team_table
from backend.init_placeholder_teams import init_placeholder_teams
from backend.save_log import create_conversation_logs_table
import traceback

def init_complete_system():
    """システム全体の完全初期化"""

    print("🚀 システム完全初期化開始")
    print("=" * 50)

    # 1. ユーザーDB初期化
    try:
        print("\n🔧 ユーザーDBを初期化中...")
        init_auth_db()
        print("✅ ユーザーDB初期化完了")
    except Exception as e:
        print("❌ ユーザーDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)

    # 2. チームDB初期化
    try:
        print("\n🔧 チームDBを初期化中...")
        create_team_table()
        print("✅ チームDB初期化完了")
    except Exception as e:
        print("❌ チームDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)

    # 3. プレースホルダーチーム登録
    try:
        print("\n🔧 プレースホルダーチームを登録中...")
        init_placeholder_teams()
        print("✅ プレースホルダーチーム初期化完了")
    except Exception as e:
        print("❌ プレースホルダーチーム初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)

    # 4. 商談ログテーブル作成
    try:
        print("\n🔧 商談ログテーブルを初期化中...")
        create_conversation_logs_table()
        print("✅ 商談ログテーブル初期化完了")
    except Exception as e:
        print("❌ 商談ログテーブル初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    print("\n🎉 システム完全初期化完了 🎉")
    print("📁 使用DB: /home/ec2-user/secure_copilot_v2/score_log.db")
    print("\n📋 次にすべきステップ:")
    print("1️⃣ 管理者ダッシュボードで実際のチームを作成")
    print("2️⃣ ユーザーを実チームへ移行（A/B/C/F_teamを卒業）")
    print("3️⃣ `debug_full_system.py` を実行して整合性を確認")
    print("4️⃣ StreamlitとFastAPIを再起動して反映確認")

    return True

if __name__ == "__main__":
    init_complete_system()
