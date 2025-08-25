from .mysql_connector import execute_query,execute_modify_query
from logger_config import logger
import datetime

def save_shodan(shodan_array):
    """評価プロンプトをDBに保存"""
    logger.info(f"🚀 save_shodan 開始: {shodan_array}")
    user_id=shodan_array['user_id']
    team_id=shodan_array['team_id']
    prompt_id=shodan_array['prompt_id']
    kintone_id=shodan_array['kintone_id']
    phone_no=shodan_array['phone_no']
    shodan_date=shodan_array['shodan_date']
    shodan_text=shodan_array['shodan_text']
    audio_file=shodan_array['audio_file']
    outcome=shodan_array['outcome']
    prompt_key=shodan_array['prompt_key']
    rows = execute_query('''
        SELECT id FROM shodans WHERE user_id = %s AND team_id = %s AND prompt_id= %s AND kintone_id = %s AND phone_no = %s AND shodan_date = %s AND shodan_text = %s AND outcome = %s
    ''', (user_id, team_id, prompt_id, kintone_id, phone_no, shodan_date, shodan_text, outcome), fetch=True)
    if rows and len(rows) > 0:
        return False, f"❌ すでに同じ評価が存在します。prompt_key: {prompt_key}"
    
    try:
        execute_query('''
            INSERT INTO shodans (user_id, team_id,prompt_id, kintone_id, phone_no, shodan_date, shodan_text,audio_file, outcome)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, team_id, prompt_id, kintone_id, phone_no, shodan_date, shodan_text, audio_file, outcome))
        return True, f"✅ 商談が保存されました！prompt_key: {prompt_key}"
    except Exception as e:
        logger.error(f"prompt_key: {prompt_key}. ❌ エラー: {str(e)}")
        return False, f"❌ prompt_key: {prompt_key} システムエラー: {str(e)}"
    

def get_shodan_by_user(user_id, is_evaluated=None, is_evaluation_saved=None):
    """Retrieve a list of deals (shodans) for a specific user, optionally filtered by evaluation status and join evaluation logs."""
    try:
        # Base query with prompts join
        # 0-16 Shodan 
        # 17 to 21 Prompts
        query = """
            SELECT s.*,
                   p.prompt_key, p.text_prompt, p.audio_prompt, p.score_items, p.notes
        """

        # If evaluation_logs should be joined
        # 22 to 27 evaluation_logs
        if is_evaluation_saved == 1:
            query += """,
                   el.evaluation_outcome, el.reply, el.full_prompt, el.audio_features, el.audio_feedback,el.comment
            """

        query += """
            FROM shodans AS s
            INNER JOIN prompts AS p ON p.id = s.prompt_id
        """

        # Add evaluation_logs join conditionally
        if is_evaluation_saved == 1:
            query += " INNER JOIN evaluation_logs AS el ON el.shodan_id = s.id"

        query += " WHERE s.user_id = %s"
        params = [user_id]

        # Add conditional filters
        if is_evaluated is not None:
            query += " AND s.is_evaluated = %s"
            params.append(is_evaluated)

        if is_evaluation_saved is not None:
            query += " AND s.is_evaluation_saved = %s"
            params.append(is_evaluation_saved)

        query += " ORDER BY shodan_date DESC"

        logger.info(query)
        logger.info(params)
        rows = execute_query(query, tuple(params), fetch=True)
        return rows

    except Exception as e:
        logger.error(f"❌ System Error: {str(e)}")
        return False, f"❌ System Error: {str(e)}"



def update_shodan_status(shodan_id, is_evaluated=None, is_evaluation_saved=None):
    """
    shodansテーブルの評価状態を更新する
    Args:
        shodan_id (int): 更新対象の商談ID
        is_evaluated (int|None): 評価済みフラグ (0 or 1)
        is_evaluation_saved (int|None): 保存済みフラグ (0 or 1)
    Returns:
        (bool, str): 成功/失敗, メッセージ
    """

    updates = []
    params = []

    if is_evaluated is not None:
        updates.append("is_evaluated = %s")
        params.append(is_evaluated)
        if is_evaluated == 1:
            updates.append("evaluated_time = %s")
            params.append(datetime.datetime.now())

    if is_evaluation_saved is not None:
        updates.append("is_evaluation_saved = %s")
        params.append(is_evaluation_saved)
        if is_evaluation_saved == 1:
            updates.append("evaluation_save_time = %s")
            params.append(datetime.datetime.now())

    if not updates:
        return False, "⚠️ 更新対象がありません"

    params.append(shodan_id)
    
    query = f"""
        UPDATE shodans
        SET {', '.join(updates)}
        WHERE id = %s
    """
    try:
        execute_modify_query(query, tuple(params))
        return True, f"✅ Shodan(ID={shodan_id}) を更新しました"
    except Exception as e:
        return False, f"❌ 更新エラー: {e}"

# def get_shodan_by_user(user_id, is_evaluated=None, is_evaluation_saved=None):
#     """Retrieve a list of deals (shodans) for a specific user, optionally filtered by evaluation status."""
#     try:
#         query = "SELECT s.*,p.prompt_key,p.text_prompt,p.audio_prompt,score_items,notes FROM shodans as s INNER JOIN prompts as p ON p.id=s.prompt_id WHERE s.user_id = %s"
#         params = [user_id]

#         # Add conditional filters if provided
#         if is_evaluated is not None:
#             query += " AND s.is_evaluated = %s"
#             params.append(is_evaluated)

#         if is_evaluation_saved is not None:
#             query += " AND s.is_evaluation_saved = %s"
#             params.append(is_evaluation_saved)

#         query += " ORDER BY shodan_date DESC"

#         rows = execute_query(query, tuple(params), fetch=True)
#         return rows

#     except Exception as e:
#         logger.error(f"❌ System Error: {str(e)}")
#         return False, f"❌ System Error: {str(e)}"