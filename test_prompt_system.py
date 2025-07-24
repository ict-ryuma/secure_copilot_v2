# test_prompt_system.py（新規作成）
# filepath: /Users/ryumahoshi/secure_copilot_v2/test_prompt_system.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.prompt_loader import (
    get_prompts_for_team, 
    get_available_teams_for_user,
    check_team_exists,
    debug_team_prompts
)

def test_prompt_system():
    """プロンプトシステムの全体テスト"""
    
    print("🧪 プロンプトシステム テスト開始")
    print("=" * 60)
    
    # 1. 利用可能チーム一覧テスト
    print("\n1️⃣ 利用可能チーム一覧テスト")
    available_teams = get_available_teams_for_user()
    print(f"   結果: {available_teams}")
    
    # 2. 各種チームでのプロンプト取得テスト
    test_teams = ["A_team", "B_team", "C_team", "F_team"] + available_teams + ["nonexistent_team"]
    
    print(f"\n2️⃣ プロンプト取得テスト（{len(test_teams)}チーム）")
    
    for i, team_name in enumerate(test_teams, 1):
        print(f"\n--- {i}. チーム: {team_name} ---")
        
        # チーム存在確認
        team_status = check_team_exists(team_name)
        print(f"   存在確認: {team_status}")
        
        # プロンプト取得
        prompts = get_prompts_for_team(team_name)
        
        if prompts.get("error", False):
            print(f"   ❌ エラー: {prompts.get('error_type')} - {prompts.get('message')}")
            print(f"   💡 対処法: {prompts.get('suggested_action', 'N/A')}")
        else:
            print(f"   ✅ 成功: プロンプトキー={prompts.get('prompt_key')}")
            print(f"   📝 テキストプロンプト: {len(prompts.get('text_prompt', ''))}文字")
            print(f"   🎤 音声プロンプト: {len(prompts.get('audio_prompt', ''))}文字")
            print(f"   📊 評価項目: {len(prompts.get('score_items', []))}項目")
    
    # 3. デバッグ情報表示
    print(f"\n3️⃣ データベース デバッグ情報")
    debug_info = debug_team_prompts()
    print(f"   DB情報: {debug_info}")
    
    print(f"\n🎉 テスト完了")

def test_specific_team(team_name: str):
    """特定チームの詳細テスト"""
    
    print(f"🔍 チーム '{team_name}' 詳細テスト")
    print("=" * 50)
    
    # 1. チーム存在確認
    team_status = check_team_exists(team_name)
    print(f"1. チーム存在確認: {team_status}")
    
    # 2. プロンプト取得
    prompts = get_prompts_for_team(team_name)
    print(f"2. プロンプト取得結果:")
    
    for key, value in prompts.items():
        if key == "score_items":
            print(f"   {key}: {value} ({type(value).__name__})")
        elif isinstance(value, str) and len(value) > 100:
            print(f"   {key}: '{value[:100]}...' ({len(value)}文字)")
        else:
            print(f"   {key}: {value}")
    
    # 3. デバッグ情報
    debug_info = debug_team_prompts(team_name)
    print(f"3. デバッグ情報: {debug_info}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 特定チームのテスト
        team_name = sys.argv[1]
        test_specific_team(team_name)
    else:
        # 全体テスト
        test_prompt_system()