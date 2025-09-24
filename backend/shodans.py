from .mysql_connector import execute_query,execute_modify_query,execute_query_with_dict_cursor
from logger_config import logger
import datetime

def save_shodan(shodan_array):
    """評価プロンプトをDBに保存"""
    logger.info(f"🚀 save_shodan 開始: {shodan_array}")
    user_id=shodan_array['user_id']
    team_has_prompt_id=shodan_array['team_has_prompt_id']
    kintone_id=shodan_array['kintone_id']
    phone_no=shodan_array['phone_no']
    customer_number=shodan_array['customer_number']
    shodan_date=shodan_array['shodan_date']
    shodan_text=shodan_array['shodan_text']
    audio_file=shodan_array['audio_file']
    outcome=shodan_array['outcome']
    prompt_key=shodan_array['prompt_key']
    created_by=shodan_array['created_by']
    rows = execute_query('''
        SELECT id FROM shodans WHERE user_id = %s AND team_has_prompt_id = %s AND kintone_id = %s AND customer_number = %s AND shodan_date = %s AND shodan_text = %s AND outcome = %s
    ''', (user_id, team_has_prompt_id, kintone_id, customer_number, shodan_date, shodan_text, outcome), fetch=True)
    if rows and len(rows) > 0:
        return False, f"❌ すでに同じ評価が存在します。prompt_key: {prompt_key}"
    
    try:
        execute_query('''
            INSERT INTO shodans (user_id, team_has_prompt_id, kintone_id, phone_no, customer_number, shodan_date, shodan_text, audio_file, outcome, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, team_has_prompt_id, kintone_id, phone_no, customer_number, shodan_date, shodan_text, audio_file, outcome, created_by))
        return True, f"✅ 商談が保存されました！prompt_key: {prompt_key}"
    except Exception as e:
        logger.error(f"prompt_key: {prompt_key}. ❌ エラー: {str(e)}")
        return False, f"❌ prompt_key: {prompt_key} システムエラー: {str(e)}"
    
def get_shodan_by_user(
        user_id=None, 
        kintone_id=None, 
        shodan_date_start=None,
        shodan_date_end=None,
        customer_number=None,
        outcome=None,
        is_evaluated=None,
        is_evaluation_saved=None
        ):
    """Retrieve a list of deals (shodans) for a specific user, optionally filtered by evaluation status and join evaluation logs."""

    # logger.info(f"Retrieve Shodans - User ID: {user_id}, Kintone ID: {kintone_id}, Date Range: {shodan_date_start} to {shodan_date_end}, Customer Number: {customer_number}, Outcome: {outcome}, Is Evaluated: {is_evaluated}, Is Evaluation Saved: {is_evaluation_saved}")
    try:
        # Base query with prompts join
        # 0-16 Shodan 
        # 17 to 21 Prompts
        query = """
            SELECT s.id as shodan_id,s.user_id,s.team_has_prompt_id,s.kintone_id,s.phone_no,s.customer_number,
            s.shodan_date,s.shodan_text,s.audio_file,s.outcome,s.is_evaluated,s.is_evaluation_saved,
            s.created_by,s.evaluated_time,s.evaluation_save_time,s.created_at,s.updated_at,
            p.id as prompt_id, p.prompt_key, p.text_prompt, p.audio_prompt, p.score_items, p.notes,
            t.id as team_id,t.team_name
        """

        # If evaluation_logs should be joined
        # 22 to 27 evaluation_logs
        if is_evaluation_saved == 1:
            query += """,
                   el.evaluation_outcome, el.reply, el.full_prompt, el.audio_features, el.audio_feedback,el.comment
            """

        query += """
            FROM shodans AS s
            INNER JOIN team_has_prompts AS thp ON thp.id = s.team_has_prompt_id
            INNER JOIN prompts AS p ON p.id = thp.prompt_id
            INNER JOIN teams AS t ON t.id = thp.team_id
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
        # Filters     
        if shodan_date_start is not None and shodan_date_end is not None:
            query += " AND s.shodan_date BETWEEN %s AND %s"
            params.extend([shodan_date_start, shodan_date_end])
        elif shodan_date_start is not None:
            query += " AND s.shodan_date >= %s"
            params.append(shodan_date_start)
        elif shodan_date_end is not None:
            query += " AND s.shodan_date <= %s"
            params.append(shodan_date_end)

        if kintone_id is not None:
            query += " AND s.kintone_id = %s"
            params.append(kintone_id)

        if customer_number is not None:
            query += " AND s.customer_number LIKE %s"
            params.append(f"%{customer_number}%")

        if outcome is not None:
            query += " AND s.outcome = %s"
            params.append(outcome)

        query += " ORDER BY s.shodan_date DESC"

        logger.info(query)
        logger.info(params)
        rows = execute_query_with_dict_cursor(query, tuple(params), fetch=True)
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
def update_shodan_outcome(shodan_id, outcome):

    updates = []
    params = []

    if outcome is not None:
        updates.append("outcome = %s")
        params.append(outcome)

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
        return True, f"✅ Shodan(ID={shodan_id}) outcomeを更新しました"
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