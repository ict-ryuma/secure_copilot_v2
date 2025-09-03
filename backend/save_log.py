# import sqlite3
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from .mysql_connector import execute_query,execute_query_with_dict_cursor
from mysql.connector import Error
from logger_config import logger
from frontend.outcomes import display_outcome

# ✅ 修正: 絶対パスに統一

def save_evaluation(shodan_id,reply, full_prompt, audio_features,audio_feedback,evaluated_by=None,evaluation_outcome=None,comment=None):
    """評価結果をDBに保存"""
    try:
        execute_query('''
            INSERT INTO evaluation_logs (shodan_id, reply, full_prompt, audio_features, audio_feedback, evaluated_by, evaluation_outcome, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (shodan_id, json.dumps(reply, ensure_ascii=False), full_prompt, json.dumps(audio_features, ensure_ascii=False), json.dumps(audio_feedback, ensure_ascii=False), evaluated_by, evaluation_outcome, comment))
        return True, "✅ 評価ログが保存されました！"
    except Exception as e:
        logger.info(f"❌ 評価ログの保存に失敗しました。 エラー: {str(e)}")
        return False, "❌ 評価ログの保存に失敗しました。"

def already_logged(shodan_id):
    """既に同じ評価が保存されているかチェック"""
    count = 0  # default
    try:
        rows = execute_query('''
            SELECT COUNT(*) FROM evaluation_logs 
            WHERE shodan_id = %s
        ''', (shodan_id,), fetch=True)

        count = rows[0][0] if rows else 0
    except Exception as e:
        # Avoid crash if logging fails
        pass

    return count > 0

def getUniqueEvaluations(member_id=None):
    """全評価ログを取得"""
    """最新のshodan_dateごとの評価ログを取得"""
    if member_id:
        query = '''
            SELECT el.*
            FROM evaluation_logs el
            INNER JOIN (
                SELECT shodan_date, MAX(created_at) AS max_created
                FROM evaluation_logs
                WHERE member_id = %s
                GROUP BY shodan_date
            ) latest ON el.shodan_date = latest.shodan_date AND el.created_at = latest.max_created
            WHERE el.member_id = %s
            ORDER BY el.shodan_date DESC
        '''
        params = (member_id, member_id)
    else:
        query = '''
            SELECT el.*
            FROM evaluation_logs el
            INNER JOIN (
                SELECT shodan_date, MAX(created_at) AS max_created
                FROM evaluation_logs
                GROUP BY shodan_date
            ) latest ON el.shodan_date = latest.shodan_date AND el.created_at = latest.max_created
            ORDER BY el.shodan_date DESC
        '''
        params = ()

    rows = execute_query(query, params, fetch=True)
    return rows
def get_all_evaluations(member_id=None, shodan_date=None):
    """全評価ログを取得"""
    if member_id and shodan_date:
        rows = execute_query('SELECT * FROM evaluation_logs WHERE member_id = %s AND shodan_date = %s ORDER BY created_at DESC', (member_id, shodan_date), fetch=True)
    else:
        rows = execute_query('SELECT * FROM evaluation_logs ORDER BY created_at DESC', fetch=True)
    return rows
# def get_evaluations_admin(member_id=None, shodan_date_start=None, shodan_date_end=None, kintone_id=None, phone_no=None, outcome=None, evaluation_status=None, score_range=None):
#     """全評価ログを条件に応じて取得"""
#     query = 'SELECT * FROM evaluation_logs WHERE 1=1'
#     params = []

#     if member_id:
#         query += ' AND member_id = %s'
#         params.append(member_id)

#     if shodan_date_start and shodan_date_end:
#         query += ' AND shodan_date BETWEEN %s AND %s'
#         params.extend([shodan_date_start, shodan_date_end])
#     elif shodan_date_start:
#         query += ' AND shodan_date >= %s'
#         params.append(shodan_date_start)
#     elif shodan_date_end:
#         query += ' AND shodan_date <= %s'
#         params.append(shodan_date_end)

#     if kintone_id:
#         query += ' AND kintone_id = %s'
#         params.append(kintone_id)

#     if phone_no:
#         query += ' AND phone_no = %s'
#         params.append(phone_no)

#     if outcome:
#         query += ' AND outcome = %s'
#         params.append(outcome)

#     # if score_range and isinstance(score_range, tuple) and len(score_range) == 2:
#     #     query += ' AND avg_score BETWEEN %s AND %s'
#     #     params.extend(score_range)

#     query += ' ORDER BY created_at DESC'

#     # with open("/app/eval_debug.log", "a") as log:
#     #     log.write(f"🚨 get_evaluations_admin() called\n")
#     #     log.write(f"query: {query} params: {params}\n")
#     rows = execute_query(query, tuple(params), fetch=True)
#     return rows

# def get_evaluations_admin(
#     member_id=None,
#     shodan_date_start=None,
#     shodan_date_end=None,
#     kintone_id=None,
#     phone_no=None,
#     outcome=None,
#     evaluation_status=None,  # is_evaluated に対応
#     score_range=None,
# ):
#     """全評価ログを条件に応じて取得"""
#     query = '''
#         SELECT el.*, s.user_id, s.team_id, s.kintone_id, s.phone_no, 
#                s.shodan_date, s.outcome, s.is_evaluated, s.is_evaluation_saved
#         FROM evaluation_logs el
#         INNER JOIN shodans s ON el.shodan_id = s.id
#         WHERE 1=1
#     '''
#     params = []

#     if member_id:
#         query += ' AND s.user_id = %s'
#         params.append(member_id)

#     if shodan_date_start and shodan_date_end:
#         query += ' AND s.shodan_date BETWEEN %s AND %s'
#         params.extend([shodan_date_start, shodan_date_end])
#     elif shodan_date_start:
#         query += ' AND s.shodan_date >= %s'
#         params.append(shodan_date_start)
#     elif shodan_date_end:
#         query += ' AND s.shodan_date <= %s'
#         params.append(shodan_date_end)

#     if kintone_id:
#         query += ' AND s.kintone_id = %s'
#         params.append(kintone_id)

#     if phone_no:
#         query += ' AND s.phone_no = %s'
#         params.append(phone_no)

#     if outcome is not None:
#         query += ' AND s.outcome = %s'
#         params.append(outcome)

#     if evaluation_status is not None:
#         query += ' AND s.is_evaluated = %s'
#         params.append(evaluation_status)

#     # 将来的に avg_score を shodans に追加した場合
#     # if score_range and isinstance(score_range, tuple) and len(score_range) == 2:
#     #     query += ' AND s.avg_score BETWEEN %s AND %s'
#     #     params.extend(score_range)

#     query += ' ORDER BY el.created_at DESC'

#     rows = execute_query(query, tuple(params), fetch=True)
#     return rows
def get_evaluations_admin(
    member_id=None,
    shodan_date_start=None,
    shodan_date_end=None,
    kintone_id=None,
    phone_no=None,
    outcome=None,
    evaluation_status=1,
    team_id=None,
    score_range=None
):
    """全評価ログ or shodans データを条件に応じて取得"""

    params = []

    # ---------------------------
    # case 1: evaluation_status=0 → shodans
    # ---------------------------
    if evaluation_status == 0:
        query = "SELECT s.*,u.name,u.username,p.prompt_key,p.text_prompt,p.audio_prompt,p.score_items,p.notes FROM shodans s " \
        "INNER JOIN users u ON s.user_id = u.id " \
        "INNER JOIN prompts p ON s.prompt_id = p.id " \
        "WHERE 1=1"

        if member_id is not None:
            query += " AND s.user_id = %s"
            params.append(member_id)

        if shodan_date_start is not None and shodan_date_end is not None:
            query += " AND s.shodan_date BETWEEN %s AND %s"
            params.extend([shodan_date_start, shodan_date_end])
        elif shodan_date_start is not None:
            query += " AND s.shodan_date >= %s"
            params.append(shodan_date_start)
        elif shodan_date_end is not None:
            query += " AND s.shodan_date <= %s"
            params.append(shodan_date_end)

        if kintone_id or kintone_id is not None:
            query += " AND s.kintone_id = %s"
            params.append(kintone_id)

        if phone_no or phone_no is not None:
            query += " AND s.phone_no = %s"
            params.append(phone_no)

        if outcome is not None:
            query += " AND s.outcome = %s"
            params.append(outcome)
        if team_id is not None:
            query += " AND s.team_id = %s"
            params.append(team_id)

        query += " AND is_evaluated = 0 and is_evaluation_saved=0 ORDER BY s.created_at DESC"

    # ---------------------------
    # case 2: evaluation_status=1 → evaluation_logs
    # ---------------------------
    else:
        query = """
            SELECT el.*, s.shodan_date, s.kintone_id, s.phone_no,s.shodan_text, s.outcome, s.user_id,u.name,u.username,p.prompt_key,p.text_prompt,p.audio_prompt,p.score_items,p.notes
            FROM evaluation_logs el
            JOIN shodans s ON el.shodan_id = s.id
            JOIN users u ON s.user_id = u.id
            JOIN prompts p ON s.prompt_id = p.id
            WHERE 1=1
        """

        if member_id is not None:
            query += " AND s.user_id = %s"
            params.append(member_id)

        if shodan_date_start is not None and shodan_date_end is not None:
            query += " AND s.shodan_date BETWEEN %s AND %s"
            params.extend([shodan_date_start, shodan_date_end])
        elif shodan_date_start is not None:
            query += " AND s.shodan_date >= %s"
            params.append(shodan_date_start)
        elif shodan_date_end is not None:
            query += " AND s.shodan_date <= %s"
            params.append(shodan_date_end)

        if kintone_id or kintone_id is not None:
            query += " AND s.kintone_id = %s"
            params.append(kintone_id)

        if phone_no or phone_no is not None:
            query += " AND s.phone_no = %s"
            params.append(phone_no)

        if outcome is not None:
            query += " AND s.outcome = %s"
            params.append(outcome)
        if team_id is not None:
            query += " AND s.team_id = %s"
            params.append(team_id)

        query += " ORDER BY el.created_at DESC"
    logger.info(f"Query: {query}")
    logger.info(f"Params: {params}")

    rows = execute_query_with_dict_cursor(query, tuple(params), fetch=True)
    return rows


def getEvaluationById(id=None):
    """評価ログをIDで取得"""
    if id:
        rows = execute_query('SELECT * FROM evaluation_logs WHERE id = %s', (id,), fetch=True)
    else:
        rows = []
    return rows



def save_conversation_log(date_str, time_str, customer_name, conversation_text, gpt_feedback, score, username, status="未設定", followup_date=None, tags=""):
    """商談ログを保存（拡張版）"""
    execute_query('''
        INSERT INTO conversation_logs (date, time, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (date_str, time_str, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags))

def get_conversation_logs(username=None, start_date=None, end_date=None, status_filter=None, customer_filter=None, score_min=None, score_max=None, tag_filter=None):
    """商談ログを取得（フィルター強化版）"""
    
    query = 'SELECT * FROM conversation_logs WHERE 1=1'
    params = []
    
    if username:
        query += " AND username = %s"
        params.append(username)
    
    if start_date:
        query += " AND date >= %s"
        params.append(start_date.strftime('%Y-%m-%d'))
    
    if end_date:
        query += " AND date <= %s"
        params.append(end_date.strftime('%Y-%m-%d'))
    
    if status_filter and status_filter != "全て":
        query += " AND status = %s"
        params.append(status_filter)
        
    if customer_filter:
        query += " AND customer_name LIKE %s"
        params.append(f"%{customer_filter}%")
        
    if score_min is not None:
        query += " AND score >= %s"
        params.append(score_min)
        
    if score_max is not None:
        query += " AND score <= %s"
        params.append(score_max)
        
    if tag_filter:
        query += " AND tags LIKE %s"
        params.append(f"%{tag_filter}%")
    
    query += " ORDER BY date DESC, time DESC"

    rows = execute_query(query, params, fetch=True)
    return rows or []

def get_team_dashboard_stats(team):
    """チーム別ダッシュボード統計を取得"""

    query = "SELECT el.*,s.outcome,p.score_items FROM evaluation_logs as el " \
    "INNER JOIN shodans as s ON el.shodan_id=s.id " \
    "INNER JOIN prompts as p ON s.prompt_id=p.id WHERE 1=1"
    params = []

    if team['id'] is not None:
        # ユーザー名からチーム絞り込み（簡易版）
        query += " AND s.team_id = %s"
        params.append(team['id'])

    rows = execute_query_with_dict_cursor(query, params, fetch=True)

    if not rows:
        return {
            "total_logs": 0,
            "avg_score": 0,
            "success_rate": 0,
            "status_breakdown": {},
            "recent_activity": 0
        }
    
    # 統計計算
    total_logs = len(rows)
    scores = [log['score_items'] for log in rows if log['score_items'] is not None]
    # avg_score = sum(scores) / len(scores) if scores else 0
    try:
        avg_score = sum(scores) / len(scores) if scores else 0
    except (json.JSONDecodeError, TypeError, KeyError):
        avg_score = 0
    
    # ステータス分布（新カラムに対応）
    status_counts = {}
    for log in rows:
        # status = log['outcome'] if 'outcome' in log else "未設定"
        status = display_outcome(log['outcome'])
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # 成約率計算
    success_count = status_counts.get(0, 0) # 成約
    completed_deals = success_count + status_counts.get(1, 0) # 未成約
    success_rate = (success_count / completed_deals * 100) if completed_deals > 0 else 0
    
    # 今月の活動数
    # current_month = datetime.now().strftime('%Y-%m')
    # recent_activity = sum(1 for log in rows if log['created_at'].startswith(current_month))
    current_month = datetime.now().strftime('%Y-%m')
    recent_activity = sum(
        1 for log in rows if log['created_at'].strftime('%Y-%m') == current_month
    )

    return {
        "total_logs": total_logs,
        "avg_score": round(avg_score, 1),
        "success_rate": round(success_rate, 1),
        "status_breakdown": status_counts,
        "recent_activity": recent_activity
    }
# def get_team_dashboard_stats(team_name=None):
#     """チーム別ダッシュボード統計を取得"""
    
#     query = "SELECT * FROM conversation_logs WHERE 1=1"
#     params = []
    
#     if team_name:
#         # ユーザー名からチーム絞り込み（簡易版）
#         query += " AND username IN (SELECT username FROM users WHERE team_name = %s)"
#         params.append(team_name)

#     rows = execute_query(query, params, fetch=True)

#     if not rows:
#         return {
#             "total_logs": 0,
#             "avg_score": 0,
#             "success_rate": 0,
#             "status_breakdown": {},
#             "recent_activity": 0
#         }
    
#     # 統計計算
#     total_logs = len(rows)
#     scores = [log[6] for log in rows if log[6] is not None]
#     avg_score = sum(scores) / len(scores) if scores else 0
    
#     # ステータス分布（新カラムに対応）
#     status_counts = {}
#     for log in rows:
#         status = log[9] if len(log) > 9 else "未設定"
#         status_counts[status] = status_counts.get(status, 0) + 1
    
#     # 成約率計算
#     success_count = status_counts.get("成約", 0)
#     completed_deals = success_count + status_counts.get("失注", 0)
#     success_rate = (success_count / completed_deals * 100) if completed_deals > 0 else 0
    
#     # 今月の活動数
#     current_month = datetime.now().strftime('%Y-%m')
#     recent_activity = sum(1 for log in rows if log[1].startswith(current_month))

#     return {
#         "total_logs": total_logs,
#         "avg_score": round(avg_score, 1),
#         "success_rate": round(success_rate, 1),
#         "status_breakdown": status_counts,
#         "recent_activity": recent_activity
#     }

def get_followup_schedule(username=None, date_range_days=30, status_filter=None):
    """フォローアップ予定を取得（安全性・拡張性強化版）"""
    conn = None
    
    try:
        
        # ✅ 入力値検証・正規化
        if not isinstance(date_range_days, (int, float)) or date_range_days <= 0:
            date_range_days = 30  # デフォルト値
        
        date_range_days = int(date_range_days)  # 整数に正規化
        
        # ✅ 完全に安全な日付計算（timedelta使用）
        today = date.today()
        end_date = today + timedelta(days=date_range_days)
        
        # ✅ 日付を統一フォーマットで文字列化
        today_str = today.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # ✅ 拡張性を考慮したステータスフィルター
        if status_filter:
            # 複数ステータス対応（将来の拡張用）
            if isinstance(status_filter, str):
                status_list = [status_filter]
            elif isinstance(status_filter, list):
                status_list = status_filter
            else:
                status_list = ['再商談']  # デフォルト
        else:
            # デフォルト：再商談のみ
            status_list = ['再商談']
        
        # ✅ 動的なSQLクエリ構築（安全なパラメータ化）
        placeholders = ','.join(['?' for _ in status_list])
        
        query = f"""
            SELECT * FROM conversation_logs 
            WHERE status IN ({placeholders})
            AND followup_date IS NOT NULL 
            AND followup_date != '' 
            AND TRIM(followup_date) != ''
            AND followup_date >= ?
            AND followup_date <= ?
        """
        
        # ✅ パラメータ組み立て
        params = status_list + [today_str, end_date_str]
        
        # ✅ ユーザー名フィルター（安全な文字列処理）
        if username and isinstance(username, str) and username.strip():
            query += " AND username = ?"
            params.append(username.strip())
        
        # ✅ ソート：緊急度順（日付昇順、時間昇順）
        query += " ORDER BY followup_date ASC, COALESCE(time, '00:00') ASC, customer_name ASC"
        
        # ✅ クエリ実行
        rows = execute_query(query, params)

        # ✅ 結果検証・後処理
        valid_rows = []
        for row in rows:
            try:
                # 日付形式の再検証
                followup_date_str = row[10] if len(row) > 10 else None
                if followup_date_str and followup_date_str.strip():
                    # 日付パース可能性チェック
                    datetime.strptime(followup_date_str.strip(), '%Y-%m-%d')
                    valid_rows.append(row)
            except (ValueError, IndexError):
                # 無効な日付形式のレコードはスキップ
                print(f"⚠️ 無効な日付形式をスキップ: {row[0] if row else 'Unknown'}")
                continue
        
        # ✅ デバッグ情報（詳細版）
        print(f"""
🔍 フォローアップ検索結果:
  - 期間: {today_str} ～ {end_date_str} ({date_range_days}日間)
  - ユーザー: {username or '全員'}
  - ステータス: {', '.join(status_list)}
  - 総件数: {len(rows)}件
  - 有効件数: {len(valid_rows)}件
        """)
        
        return valid_rows
    except Error as db_error:
        print(f"❌ DB エラー: {db_error}")
        return []

    except Exception as e:
        print(f"❌ フォローアップ取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        
    # except sqlite3.Error as db_error:
    #     print(f"❌ DB エラー: {db_error}")
    #     return []
        
    # except Exception as e:
    #     print(f"❌ フォローアップ取得エラー: {e}")
    #     import traceback
    #     traceback.print_exc()  # デバッグ用詳細エラー
    #     return []
        
    # finally:
    #     # ✅ 確実なDB接続クローズ
    #     if conn:
    #         conn.close()

# ✅ 新機能: フォローアップ統計取得（拡張機能）
def get_followup_stats(username=None, days_ahead=30):
    """フォローアップ統計を取得（緊急度別集計）"""
    try:
        followup_logs = get_followup_schedule(username, days_ahead)
        
        if not followup_logs:
            return {
                "total": 0,
                "urgent": 0,
                "this_week": 0,
                "later": 0,
                "by_user": {}
            }
        
        today = date.today()
        urgent_count = 0  # 今日・明日
        week_count = 0    # 今週中
        later_count = 0   # それ以降
        by_user = {}
        
        for log in followup_logs:
            try:
                followup_date_str = log[10] if len(log) > 10 else None
                username_log = log[7] if len(log) > 7 else "不明"
                
                if followup_date_str:
                    followup_date = datetime.strptime(followup_date_str, '%Y-%m-%d').date()
                    days_until = (followup_date - today).days
                    
                    # 緊急度分類
                    if days_until <= 1:
                        urgent_count += 1
                    elif days_until <= 7:
                        week_count += 1
                    else:
                        later_count += 1
                    
                    # ユーザー別集計
                    by_user[username_log] = by_user.get(username_log, 0) + 1
                        
            except (ValueError, IndexError):
                continue
        
        return {
            "total": len(followup_logs),
            "urgent": urgent_count,
            "this_week": week_count, 
            "later": later_count,
            "by_user": by_user
        }
        
    except Exception as e:
        print(f"❌ フォローアップ統計エラー: {e}")
        return {"total": 0, "urgent": 0, "this_week": 0, "later": 0, "by_user": {}}

def delete_conversation_log(log_id):
    """商談ログを削除（管理者機能）"""
    try:
        execute_query("DELETE FROM conversation_logs WHERE id = %s", (log_id,))
        print(f"✅ ログ削除完了: ID={log_id}")
        return True
    except Exception as e:
        print(f"❌ ログ削除エラー: {e}")
        return False
