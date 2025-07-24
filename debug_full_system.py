# debug_full_system.py（新規作成）
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def diagnose_full_system():
    """システム全体の整合性診断"""
    
    print("🔍 システム全体診断開始")
    print("=" * 60)
    
    # 1. データベース接続確認
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"✅ データベース接続成功: {DB_PATH}")
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 テーブル一覧: {tables}")
        
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return
    
    # 2. team_master整合性チェック
    print("\n🏷️ team_master テーブル診断")
    if "team_master" in tables:
        cursor.execute("SELECT COUNT(*) FROM team_master")
        team_count = cursor.fetchone()[0]
        print(f"📊 総チーム数: {team_count}")
        
        cursor.execute("SELECT COUNT(*) FROM team_master WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        print(f"🟢 アクティブチーム数: {active_count}")
        
        # プレースホルダーチェック
        cursor.execute("""
            SELECT team_name, is_active FROM team_master 
            WHERE team_name IN ('A_team', 'B_team', 'C_team', 'F_team')
        """)
        placeholders = cursor.fetchall()
        print(f"🚨 プレースホルダーチーム: {len(placeholders)}件")
        for name, is_active in placeholders:
            status = "有効" if is_active else "無効"
            print(f"  - {name}: {status}")
            
        # score_items形式チェック
        cursor.execute("SELECT team_name, score_items FROM team_master WHERE score_items IS NOT NULL")
        score_items_data = cursor.fetchall()
        
        json_valid = 0
        csv_format = 0
        invalid = 0
        
        for team_name, score_items in score_items_data:
            if score_items:
                try:
                    json.loads(score_items)
                    json_valid += 1
                except:
                    if ',' in score_items:
                        csv_format += 1
                    else:
                        invalid += 1
                        print(f"  ⚠️ {team_name}: 不正なscore_items形式")
        
        print(f"📊 score_items形式: JSON={json_valid}, CSV={csv_format}, 不正={invalid}")
    
    # 3. users テーブル診断
    print("\n👥 users テーブル診断")
    if "users" in tables:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"📊 総ユーザー数: {user_count}")
        
        # チーム別ユーザー分布
        cursor.execute("""
            SELECT team_name, COUNT(*) as count 
            FROM users 
            GROUP BY team_name 
            ORDER BY count DESC
        """)
        team_distribution = cursor.fetchall()
        
        print("📊 チーム別ユーザー分布:")
        placeholder_users = 0
        for team_name, count in team_distribution:
            is_placeholder = team_name in ['A_team', 'B_team', 'C_team', 'F_team']
            if is_placeholder:
                placeholder_users += count
                print(f"  🚨 {team_name}: {count}人 (プレースホルダー)")
            else:
                print(f"  ✅ {team_name}: {count}人")
        
        if placeholder_users > 0:
            print(f"⚠️ プレースホルダーチーム所属ユーザー: {placeholder_users}人 (要移行)")
    
    # 4. 孤立ユーザーチェック
    print("\n🔍 孤立ユーザーチェック")
    cursor.execute("""
        SELECT u.username, u.team_name 
        FROM users u 
        LEFT JOIN team_master t ON u.team_name = t.team_name 
        WHERE t.team_name IS NULL OR t.is_active = 0
    """)
    orphaned_users = cursor.fetchall()
    
    if orphaned_users:
        print(f"🚨 孤立ユーザー: {len(orphaned_users)}人")
        for username, team_name in orphaned_users:
            print(f"  - {username} → {team_name} (存在しないか無効)")
    else:
        print("✅ 孤立ユーザーなし")
    
    # 5. 推奨修正アクション
    print("\n💡 推奨修正アクション")
    actions = []
    
    if placeholder_users > 0:
        actions.append("1. プレースホルダーチーム所属ユーザーを実際のチームに移行")
    
    if orphaned_users:
        actions.append("2. 孤立ユーザーのチーム設定を修正")
        
    if invalid > 0:
        actions.append("3. 不正なscore_items形式を修正")
    
    if not actions:
        print("✅ 修正不要：システムは正常です")
    else:
        for action in actions:
            print(f"  {action}")
    
    conn.close()
    print("\n🎉 診断完了")

if __name__ == "__main__":
    diagnose_full_system()