from backend.mysql_connector import execute_query,execute_modify_query

def get_prompts(only_active=None):
    """
    Get prompts from the database.
    
    :param only_active: 
        - None → get all prompts
        - 1 → only active prompts
        - 0 → only inactive prompts
    """
    if only_active is None:
        query = '''
            SELECT id as prompt_id, prompt_key, text_prompt,audio_prompt,score_items,notes, is_active, created_by, created_at, updated_at
            FROM prompts
        '''
        params = ()
    else:
        query = '''
            SELECT id as prompt_id, prompt_key, text_prompt,audio_prompt,score_items,notes, is_active, created_by, created_at, updated_at
            FROM prompts
            WHERE is_active=%s
        '''
        params = (only_active,)

    teams = execute_query(query, params, fetch=True)
    return teams


def get_team_prompts(team_id):
    prompts = execute_query('''
            SELECT uht.team_id, t.team_name, t.descriptions, t.is_active 
            FROM user_has_teams AS uht
            INNER JOIN teams AS t ON t.id = uht.team_id
            WHERE uht.user_id = %s
        ''', (team_id,), fetch=True)
    # prompts = prompts[0] if (teams and len(teams) > 0) else None
    return prompts


def create_prompt(prompt_key, text_prompt,audio_prompt,score_items,notes, is_active=1, created_by=None):
    """
    Create a new prompt.
    
    :param prompt_key: Name of the prompt
    :param text_prompt: Description of the prompt text
    :param is_active: 1 for active, 0 for inactive
    :param created_by: ID of the user creating the team
    :return: Number of rows affected
    """

    rows = execute_query("SELECT * FROM prompts WHERE prompt_key = %s", (prompt_key,), fetch=True)
    if rows and len(rows) > 0:
        return False, f"プロンプトキー '{prompt_key}' は既に登録されています"
    
    try:
        query = """
            INSERT INTO prompts (prompt_key, text_prompt,audio_prompt,score_items,notes, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (prompt_key, text_prompt,audio_prompt,score_items,notes, is_active, created_by)
        execute_query(query, params)
        return True, f"✅ プロンプトキー '{prompt_key}' を追加しました"
    except Exception as e:
        return False, f"登録中にエラーが発生しました: {str(e)}"


def update_prompt(id, prompt_key=None, text_prompt=None,audio_prompt=None,score_items=None,notes=None, is_active=None):
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

    if prompt_key is not None:
        updates.append("prompt_key=%s")
        params.append(prompt_key)
    if text_prompt is not None:
        updates.append("text_prompt=%s")
        params.append(text_prompt)
    if audio_prompt is not None:
        updates.append("audio_prompt=%s")
        params.append(audio_prompt)
    if score_items is not None:
        updates.append("score_items=%s")
        params.append(score_items)
    if notes is not None:
        updates.append("notes=%s")
        params.append(notes)
    if is_active is not None:
        updates.append("is_active=%s")
        params.append(is_active)

    if not updates:
        # Nothing to update
        return 0

    params.append(id)
    query = f"""
        UPDATE prompts
        SET {', '.join(updates)}
        WHERE id=%s
    """
    return execute_modify_query(query, tuple(params))


def delete_prompt(id):
        """
        Delete a team by its ID.
        
        :param id: Team ID to delete
        :return: Number of rows affected
        """
        query = "DELETE FROM prompts WHERE id = %s"
        return execute_query(query, (id,))