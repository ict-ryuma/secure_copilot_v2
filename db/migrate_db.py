import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
import traceback
from models import (
    add_evaluated_by_column_to_evaluation_logs_table,
    create_users_table,
    create_teams_table,
    create_prompts_table,
    create_team_has_prompts_table,
    create_user_has_teams_table,
    create_shodans_table,
    create_evaluation_logs_table,
    create_batch_last_success_times_table,
    create_shodan_details_table,
    add_some_columns_to_shodans_table,
    add_some_columns_to_users_table,
    delete_some_columns_to_shodans_table
)

def init_complete_system():
    """システム全体の完全初期化"""

    print("🚀 システム完全初期化開始")
    print("=" * 50)

    # 1. ユーザーDB初期化
    try:
        print("\n🔧 ユーザーDBを初期化中...")
        create_users_table()
        print("✅ ユーザーDB初期化完了")
    except Exception as e:
        print("❌ ユーザーDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)

    # 2. チームDB初期化
    try:
        print("\n🔧 チームDBを初期化中...")
        create_teams_table()
        print("✅ チームDB初期化完了")
    except Exception as e:
        print("❌ チームDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    # 3. プロンプトDB初期化
    try:
        print("\n🔧 プロンプトDBを初期化中...")
        create_prompts_table()
        print("✅ プロンプトDB初期化完了")
    except Exception as e:
        print("❌ プロンプトDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    # 4. チームのプロンプトDB初期化
    try:
        print("\n🔧 チームのプロンプトDBを初期化中...")
        create_team_has_prompts_table()
        print("✅ チームのプロンプトDB初期化完了")
    except Exception as e:
        print("❌ チームのプロンプトDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    # 5. ユーザーのチームDB初期化
    try:
        print("\n🔧 ユーザーのチームDBを初期化中...")
        create_user_has_teams_table()
        print("✅ ユーザーのチームDB初期化完了")
    except Exception as e:
        print("❌ ユーザーのチームDB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    # 6. 商談DB初期化
    try:
        print("\n🔧 商談DBを初期化中...")
        create_shodans_table()
        print("✅ 商談DB初期化完了")
    except Exception as e:
        print("❌ 商談DB初期化エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    # 7. 商談評価ログDB初期化
    try:
        print("\n🔧 商談評価ログDBを初期化中...")
        create_evaluation_logs_table()
        print("✅ 商談評価ログDB初期化完了")
    except Exception as e:
        print("❌ 商談評価ログDB初期化エラー:")
        traceback.print_exc()
        return False
    print("=" * 50)
    # 8. 商談評価ログDBにevaluated_byカラムを追加
    try:
        print("\n🔧 商談評価ログDBにevaluated_byカラムを追加中...")
        add_evaluated_by_column_to_evaluation_logs_table()
        print("✅ 商談評価ログDBにevaluated_byカラムを追加完了")
    except Exception as e:
        print("❌ 商談評価ログDBにevaluated_byカラムを追加エラー:")
        traceback.print_exc()
        return False
    # 9. create_batch_last_success_times_table
    try:
        print("\n🔧 batch_last_success_times DBを追加中...")
        create_batch_last_success_times_table()
        print("✅ batch_last_success_times DBを追加完了")
    except Exception as e:
        print("❌batch_last_success_times DBを追加エラー:")
        traceback.print_exc()
        return False
    # 10. create_shodan_details_table
    try:
        print("\n🔧 create_shodan_details_table DBを追加中...")
        create_shodan_details_table()
        print("✅ create_shodan_details_table DBを追加完了")
    except Exception as e:
        print("create_shodan_details_table DBを追加エラー:")
        traceback.print_exc()
        return False
    # 11. add_some_columns_to_shodans_table
    try:
        print("\n🔧 add_some_columns_to_shodans_table DBを追加中...")
        add_some_columns_to_shodans_table()
        print("✅ add_some_columns_to_shodans_table DBを追加完了")
    except Exception as e:
        print("add_some_columns_to_shodans_table DBを追加エラー:")
        traceback.print_exc()
        return False
    # 12. add_some_columns_to_users_table
    try:
        print("\n🔧 add_some_columns_to_users_table DBを追加中...")
        add_some_columns_to_users_table()
        print("✅ add_some_columns_to_users_table DBを追加完了")
    except Exception as e:
        print("add_some_columns_to_users_table DBを追加エラー:")
        traceback.print_exc()
        return False
    # 13. delete_some_columns_to_shodans_table
    try:
        print("\n🔧 delete_some_columns_to_shodans_table DBを追加中...")
        delete_some_columns_to_shodans_table()
        print("✅ delete_some_columns_to_shodans_table DBを追加完了")
    except Exception as e:
        print("delete_some_columns_to_shodans_table DBを追加エラー:")
        traceback.print_exc()
        return False

    print("=" * 50)
    print("\n🎉 システム完全初期化完了 🎉")
    print("\n📋 次にすべきステップ:")
    print("1️⃣ 管理者ダッシュボードで実際のチームを作成")
    print("2️⃣ ユーザーを実チームへ移行（A/B/C/F_teamを卒業）")
    print("3️⃣ `debug_full_system.py` を実行して整合性を確認")
    print("4️⃣ StreamlitとFastAPIを再起動して反映確認")

    return True

if __name__ == "__main__":
    init_complete_system()
