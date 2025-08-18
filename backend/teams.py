from backend.mysql_connector import execute_query,execute_modify_query

def get_teams(only_active=None):
    """
    Get teams from the database.
    
    :param only_active: 
        - None → get all teams
        - 1 → only active teams
        - 0 → only inactive teams
    """
    if only_active is None:
        query = '''
            SELECT id as team_id, team_name, descriptions, is_active, created_by, created_at, updated_at
            FROM teams
        '''
        params = ()
    else:
        query = '''
            SELECT id as team_id, team_name, descriptions, is_active, created_by, created_at, updated_at
            FROM teams
            WHERE is_active=%s
        '''
        params = (only_active,)

    teams = execute_query(query, params, fetch=True)
    return teams

def get_user_team(user_id):
    teams = execute_query('''
            SELECT uht.team_id, t.team_name, t.descriptions, t.is_active 
            FROM user_has_teams AS uht
            INNER JOIN teams AS t ON t.id = uht.team_id
            WHERE uht.user_id = %s
        ''', (user_id,), fetch=True)
    team = teams[0] if (teams and len(teams) > 0) else None
    return team


def create_team(team_name, descriptions, is_active=1, created_by=None):
    """
    Create a new team.
    
    :param team_name: Name of the team
    :param descriptions: Description of the team
    :param is_active: 1 for active, 0 for inactive
    :param created_by: ID of the user creating the team
    :return: Number of rows affected
    """

    rows = execute_query("SELECT * FROM teams WHERE team_name = %s", (team_name,), fetch=True)
    if rows and len(rows) > 0:
        return False, f"チーム名 '{team_name}' は既に登録されています"
    
    try:
        query = """
            INSERT INTO teams (team_name, descriptions, is_active, created_by)
            VALUES (%s, %s, %s, %s)
        """
        params = (team_name, descriptions, is_active, created_by)
        execute_query(query, params)
        return True, f"✅ チーム '{team_name}' を追加しました"
    except Exception as e:
        return False, f"登録中にエラーが発生しました: {str(e)}"


def update_team(id, team_name=None, descriptions=None, is_active=None):
    """
    Update a team in the database.
    
    :param id: Team ID to update
    :param team_name: New team name (optional)
    :param descriptions: New description (optional)
    :param is_active: New active status (optional)
    :return: Number of rows affected
    """
    updates = []
    params = []

    if team_name is not None:
        updates.append("team_name=%s")
        params.append(team_name)
    if descriptions is not None:
        updates.append("descriptions=%s")
        params.append(descriptions)
    if is_active is not None:
        updates.append("is_active=%s")
        params.append(is_active)

    if not updates:
        # Nothing to update
        return 0

    params.append(id)
    query = f"""
        UPDATE teams
        SET {', '.join(updates)}
        WHERE id=%s
    """
    try:
        execute_modify_query(query, tuple(params))
        return True, "✅ チーム更新しました"
    except Exception as e:
        return False, f"❌ 更新エラー: {e}"


def delete_team(id):
        """
        Delete a team by its ID.
        
        :param id: Team ID to delete
        :return: Number of rows affected
        """
        query = "DELETE FROM teams WHERE id = %s"
        return execute_query(query, (id,))



def create_team_has_prompts(team_id, prompt_id, is_active=1, created_by=None):
    """
    Create a new team_has_prompt.
    
    :param team_id: ID of the team
    :param descriptions: Description of the team
    :param is_active: 1 for active, 0 for inactive
    :param created_by: ID of the user creating the team
    :return: Number of rows affected
    """

    rows = execute_query("SELECT * FROM team_has_prompts WHERE team_id = %s and prompt_id=%s", (team_id,prompt_id), fetch=True)
    if rows and len(rows) > 0:
        return False, f"Team and frompt pairs are already in DB"
    
    try:
        query = """
            INSERT INTO team_has_prompts (team_id, prompt_id, is_active, created_by)
            VALUES (%s, %s, %s, %s)
        """
        params = (team_id, prompt_id, is_active, created_by)
        execute_query(query, params)
        return True, f"✅ チームとプロンプトパイルを追加しました"
    except Exception as e:
        return False, f"登録中にエラーが発生しました: {str(e)}"
    


def get_team_has_prompts(only_active=None):
    """
    Get team_has_prompts from the database.
    
    :param only_active: 
        - None → get all teams
        - 1 → only active teams
        - 0 → only inactive teams
    """
    if only_active is None:
        query = '''
            SELECT thp.id as team_has_prompt_id, thp.team_id, thp.prompt_id, thp.is_active, thp.created_by, thp.created_at, thp.updated_at,
            t.team_name,p.prompt_key
            FROM team_has_prompts as thp 
            INNER JOIN teams as t ON t.id=thp.team_id 
            INNER JOIN prompts as p ON p.id=thp.prompt_id
        '''
        params = ()
    else:
        query = '''
            SELECT thp.id as team_has_prompt_id, thp.team_id, thp.prompt_id, thp.is_active, thp.created_by, thp.created_at, thp.updated_at,
            t.team_name,p.prompt_key
            FROM team_has_prompts as thp 
            INNER JOIN teams as t ON t.id=thp.team_id 
            INNER JOIN prompts as p ON p.id=thp.prompt_id
            WHERE thp.is_active=%s
        '''
        params = (only_active,)

    team_prompts = execute_query(query, params, fetch=True)
    return team_prompts



def update_team_has_prompts(id, team_id=None, prompt_id=None, is_active=None,created_by=None):
    """
    Update a team_has_prompts in the database.
    
    :param id: team_has_prompts ID to update
    :param team_id: Team ID
    :param prompt_id:Prompt ID
    :param is_active: active status (optional)
    :return: status and message
    """
    updates = []
    params = []

    if team_id is not None:
        updates.append("team_id=%s")
        params.append(team_id)
    if prompt_id is not None:
        updates.append("prompt_id=%s")
        params.append(prompt_id)
    if is_active is not None:
        updates.append("is_active=%s")
        params.append(is_active)
    if created_by is not None:
        updates.append("created_by=%s")
        params.append(created_by)

    if not updates:
        # Nothing to update
        return 0

    params.append(id)
    query = f"""
        UPDATE team_has_prompts
        SET {', '.join(updates)}
        WHERE id=%s
    """
    try:
        execute_modify_query(query, tuple(params))
        return True, "✅ チーム・プロンプトの設定を更新しました"
    except Exception as e:
        return False, f"❌ 更新エラー: {e}"
