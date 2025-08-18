from backend.mysql_connector import execute_query

def create_user_has_teams():
    user_teams = [
        ("1", "1",1, 1),
        ("2", "1",1, 1),
        ("3", "2",1, 1)
    ]
    
    for user_team in user_teams:
        try:
            execute_query('''
                INSERT INTO user_has_teams 
                (user_id, team_id, is_active, created_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                user_id = VALUES(user_id),
                team_id = VALUES(team_id),
                is_active = VALUES(is_active),
                created_by = VALUES(created_by)
            ''', (
                user_team[0],
                user_team[1], 
                user_team[2],
                user_team[3]
            ))
            print(f"✅ プレースホルダーチーム '{user_team[0]}' を登録しました")
        except Exception as e:
            print(f"❌ {user_team[0]} 登録エラー: {e}")