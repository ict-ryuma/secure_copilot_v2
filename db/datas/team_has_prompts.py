from backend.mysql_connector import execute_query

def create_team_has_prompts():
    team_prompts = [
        ("1", "1",1, 1),
        ("1", "2",1, 1),
        ("2", "1",1, 1)
    ]
    
    for team_prompt in team_prompts:
        try:
            execute_query('''
                INSERT INTO team_has_prompts 
                (team_id,prompt_id,is_active, created_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                team_id = VALUES(team_id),
                prompt_id = VALUES(prompt_id),
                is_active = VALUES(is_active),
                created_by = VALUES(created_by)
            ''', (
                team_prompt[0],
                team_prompt[1], 
                team_prompt[2],
                team_prompt[3]
            ))
            print(f"✅ プレースホルダーチーム '{team_prompt[0]}' を登録しました")
        except Exception as e:
            print(f"❌ {team_prompt[0]} 登録エラー: {e}")