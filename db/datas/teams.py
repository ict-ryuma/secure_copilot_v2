from backend.mysql_connector import execute_query

def create_teams():
    teams = [
        ("A_team", "プレースホルダーチーム（移行用）", 1),
        ("B_team", "プレースホルダーチーム（移行用）", 1),
        ("C_team", "プレースホルダーチーム（移行用）", 0),
        ("F_team", "プレースホルダーチーム（移行用）", 0),
    ]
    
    for team in teams:
        try:
            execute_query('''
                INSERT INTO teams 
                (team_name, descriptions, is_active)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                team_name = VALUES(team_name),
                descriptions = VALUES(descriptions),
                is_active = VALUES(is_active)
            ''', (
                team[0],
                team[1], 
                team[2]
            ))
            print(f"✅ プレースホルダーチーム '{team[0]}' を登録しました")
        except Exception as e:
            print(f"❌ {team[0]} 登録エラー: {e}")