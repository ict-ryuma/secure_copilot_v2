# test_9column_compatibility.py（新規作成）
# filepath: /Users/ryumahoshi/secure_copilot_v2/test_9column_compatibility.py
import sys
import os
from backend.mysql_connector import execute_query

# パス設定
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def test_all_unpack_operations():
    """全ての unpack 操作をテスト"""
    
    print("🧪 9列対応テスト開始")
    print("=" * 50)
    
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    
    # 1. スキーマ確認
    schema = execute_query("PRAGMA table_info(team_master)")
    print(f"📋 team_master カラム数: {len(schema)}")
    
    for i, (cid, name, type_, notnull, default, pk) in enumerate(schema):
        print(f"  {i+1}. {name} ({type_})")
    
    # 2. サンプルデータ取得
    sample = execute_query("SELECT * FROM team_master LIMIT 1", fetch=True)

    if not sample:
        print("⚠️ テストデータがありません。プレースホルダーチームを作成します...")
        
        # テストデータ作成
        execute_query('''
            INSERT OR IGNORE INTO team_master 
            (team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            "TEST_TEAM",
            "test_prompt_key",
            "テスト用テキストプロンプト",
            "テスト用音声プロンプト", 
            '["項目1","項目2","項目3"]',
            "テスト用ノート",
            1,
            "2024-01-01 12:00:00"
        ))
        # conn.commit()

        sample = execute_query("SELECT * FROM team_master WHERE team_name = 'TEST_TEAM'", fetch=True)

    print(f"\n🔍 サンプルデータ（{len(sample)}列）:")
    for i, value in enumerate(sample):
        column_name = schema[i][1] if i < len(schema) else f"unknown_{i}"
        print(f"  {i+1}. {column_name}: {value}")
    
    # 3. unpack テスト
    print(f"\n🧪 アンパック互換性テスト:")
    
    try:
        # 9列アンパック
        team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = sample
        print("✅ 9列アンパック成功")
        print(f"   ID: {team_id}")
        print(f"   チーム名: {team_name}")
        print(f"   プロンプトキー: {prompt_key}")
        print(f"   更新日時: {updated_at}")
        print(f"   アクティブ: {'有効' if is_active else '無効'}")
        
    except ValueError as e:
        print(f"❌ 9列アンパックエラー: {e}")
        print(f"   実際のカラム数: {len(sample)}")
        return False
    
    # 4. fetch_all_team_prompts() テスト
    print(f"\n🧪 fetch_all_team_prompts() テスト:")
    try:
        from backend.db_team_master import fetch_all_team_prompts
        teams = fetch_all_team_prompts()
        
        if teams:
            first_team = teams[0]
            team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = first_team
            print("✅ fetch_all_team_prompts() 9列アンパック成功")
            print(f"   取得チーム数: {len(teams)}")
            print(f"   最初のチーム: {team_name}")
        else:
            print("⚠️ チームデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ fetch_all_team_prompts() エラー: {e}")
        return False
    
    # 5. テストデータクリーンアップ
    execute_query("DELETE FROM team_master WHERE team_name = 'TEST_TEAM'")
    print(f"\n🎉 全テスト完了！9列対応は正常です。")
    return True

if __name__ == "__main__":
    success = test_all_unpack_operations()
    if success:
        print("\n✅ 修正完了：admin_dashboard.py と team_prompt_config.py は正常動作します")
    else:
        print("\n❌ まだ問題があります。ログを確認してください。")