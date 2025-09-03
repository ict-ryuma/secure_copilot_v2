from backend.mysql_connector import execute_query
from backend.auth import get_all_teams
# ✅ 修正: プレースホルダーチームを除外した安全なチーム取得
def get_all_teams_safe():
    """team_masterから実際に登録されたアクティブなチームのみを返す"""
    try:
        # まずbackend.authのget_all_teamsを試行
        teams = get_all_teams()
        
        # プレースホルダーチームを除外
        filtered_teams = [
            team for team in teams 
            if team["team_name"] not in ['A_team', 'B_team', 'C_team', 'F_team']
        ]
        if filtered_teams:
            return filtered_teams
    except (ImportError, AttributeError):
        pass
    
    # フォールバック: teamsテーブルから直接取得
    try:
        # ✅ 修正: 列名を team_name に統一
        rows=execute_query("""
            SELECT id, team_name FROM teams
            WHERE is_active = 1 
            AND team_name NOT IN ('A_team', 'B_team', 'C_team', 'F_team')
            ORDER BY team_name
        """, fetch=True)
        teams = [{"id": row[0], "team_name": row[1]} for row in rows]
        print(f"🔍 取得したアクティブチーム（プレースホルダー除外）: {rows}")
        return teams
        
    except Exception as e:
        print(f"❌ チーム取得エラー: {e}")
        return []
# def get_all_teams_safe():
#     """team_masterから実際に登録されたアクティブなチームのみを返す"""
#     try:
#         # まずbackend.authのget_all_teamsを試行
#         from backend.auth import get_all_teams
#         teams = get_all_teams()
        
#         # プレースホルダーチームを除外
#         filtered_teams = [team for team in teams if team not in ['A_team', 'B_team', 'C_team', 'F_team']]
#         if filtered_teams:
#             return filtered_teams
#     except (ImportError, AttributeError):
#         pass
    
#     # フォールバック: team_masterテーブルから直接取得
#     try:
#         # ✅ 修正: 列名を team_name に統一
#         execute_query("""
#             SELECT team_name FROM team_master 
#             WHERE is_active = 1 
#             AND team_name NOT IN ('A_team', 'B_team', 'C_team', 'F_team')
#             ORDER BY team_name
#         """, fetch=True)
#         teams = [row[0] for row in teams]
#         print(f"🔍 取得したアクティブチーム（プレースホルダー除外）: {teams}")
#         return teams
        
#     except Exception as e:
#         print(f"❌ チーム取得エラー: {e}")
#         return []
    



# ✅ ヘルパー関数: ステータスバッジ（先頭で定義）
def get_status_badge(status):
    """商談状態をバッジ形式で返す"""
    badges = {
        "成約": "🟢 成約",
        "失注": "🔴 失注", 
        "再商談": "🟡 再商談",
        "未設定": "⚪ 未設定"
    }
    return badges.get(status, "⚪ 未設定")

