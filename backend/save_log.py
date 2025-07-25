# import sqlite3
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from mysql_connector import execute_query
from mysql.connector import Error

# ✅ 修正: 絶対パスに統一
DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

def init_db():
    """評価ログテーブルを初期化"""
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    execute_query('''
        CREATE TABLE IF NOT EXISTS evaluation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT,
            member_name TEXT,
            outcome TEXT,
            scores TEXT,
            raw_output TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # conn.commit()
    # conn.close()

def save_evaluation(deal_id, member_name, outcome, parsed_data, raw_output):
    """評価結果をDBに保存"""
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    execute_query('''
        INSERT INTO evaluation_logs (deal_id, member_name, outcome, scores, raw_output)
        VALUES (%s, %s, %s, %s, %s)
    ''', (deal_id, member_name, outcome, json.dumps(parsed_data, ensure_ascii=False), raw_output))
    # conn.commit()
    # conn.close()

def already_logged(deal_id, member_name):
    """既に同じ評価が保存されているかチェック"""
    rows = execute_query('''
        SELECT COUNT(*) FROM evaluation_logs 
        WHERE deal_id = %s AND member_name = %s
    ''', (deal_id, member_name))
    count = rows[0][0] if rows else 0
    return count > 0

def get_all_evaluations():
    """全評価ログを取得"""
    rows = execute_query('SELECT * FROM evaluation_logs ORDER BY created_at DESC')
    return rows

# ✅ 商談評価ログ管理機能（拡張版）
def create_conversation_logs_table():
    """商談評価ログテーブルを作成・拡張（なければ）"""
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    
    # ✅ 基本テーブル作成
    execute_query('''
        CREATE TABLE IF NOT EXISTS conversation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT,
            customer_name TEXT,
            conversation_text TEXT,
            gpt_feedback TEXT,
            score REAL,
            username TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

        # ✅ 新カラム追加（既存テーブルに対応）
    alter_statements = [
        'ALTER TABLE conversation_logs ADD COLUMN status TEXT DEFAULT "未設定"',
        'ALTER TABLE conversation_logs ADD COLUMN followup_date TEXT',
        'ALTER TABLE conversation_logs ADD COLUMN tags TEXT',
    ]

    for stmt in alter_statements:
        try:
            execute_query(stmt)
        except Error as err:
            if "Duplicate column" in str(err):
                pass  # 既にカラムが存在する
            else:
                print(f"❌ カラム追加失敗: {err}")
    
    # ✅ 新カラム追加（既存テーブルに対応）
    # try:
    #     execute_query('ALTER TABLE conversation_logs ADD COLUMN status TEXT DEFAULT "未設定"')
    # except sqlite3.OperationalError:
    #     pass  # カラムが既に存在する場合
        
    # try:
    #     execute_query('ALTER TABLE conversation_logs ADD COLUMN followup_date TEXT')
    # except sqlite3.OperationalError:
    #     pass
        
    # try:
    #     execute_query('ALTER TABLE conversation_logs ADD COLUMN tags TEXT')
    # except sqlite3.OperationalError:
    #     pass

    # conn.commit()
    # conn.close()

def save_conversation_log(date_str, time_str, customer_name, conversation_text, gpt_feedback, score, username, status="未設定", followup_date=None, tags=""):
    """商談ログを保存（拡張版）"""
    create_conversation_logs_table()
    execute_query('''
        INSERT INTO conversation_logs (date, time, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (date_str, time_str, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags))
    # cursor = conn.cursor()
    # cursor.execute('''
    #     INSERT INTO conversation_logs (date, time, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags)
    #     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    # ''', (date_str, time_str, customer_name, conversation_text, gpt_feedback, score, username, status, followup_date, tags))
    # conn.commit()
    # conn.close()

def get_conversation_logs(username=None, start_date=None, end_date=None, status_filter=None, customer_filter=None, score_min=None, score_max=None, tag_filter=None):
    """商談ログを取得（フィルター強化版）"""
    create_conversation_logs_table()
    rows = execute_query('SELECT * FROM conversation_logs WHERE 1=1')
    params = []
    
    if username:
        query += " AND username = ?"
        params.append(username)
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date.strftime('%Y-%m-%d'))
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.strftime('%Y-%m-%d'))
    
    if status_filter and status_filter != "全て":
        query += " AND status = ?"
        params.append(status_filter)
        
    if customer_filter:
        query += " AND customer_name LIKE ?"
        params.append(f"%{customer_filter}%")
        
    if score_min is not None:
        query += " AND score >= ?"
        params.append(score_min)
        
    if score_max is not None:
        query += " AND score <= ?"
        params.append(score_max)
        
    if tag_filter:
        query += " AND tags LIKE ?"
        params.append(f"%{tag_filter}%")
    
    query += " ORDER BY date DESC, time DESC"

    rows = execute_query(query, params)

    return rows

def get_team_dashboard_stats(team_name=None):
    """チーム別ダッシュボード統計を取得"""
    create_conversation_logs_table()
    rows = execute_query("SELECT * FROM conversation_logs WHERE 1=1")
    params = []
    
    if team_name:
        # ユーザー名からチーム絞り込み（簡易版）
        query += " AND username IN (SELECT username FROM users WHERE team_name = ?)"
        params.append(team_name)

    rows = execute_query(query, params)

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
    scores = [log[6] for log in rows if log[6] is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # ステータス分布（新カラムに対応）
    status_counts = {}
    for log in rows:
        status = log[9] if len(log) > 9 else "未設定"
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # 成約率計算
    success_count = status_counts.get("成約", 0)
    completed_deals = success_count + status_counts.get("失注", 0)
    success_rate = (success_count / completed_deals * 100) if completed_deals > 0 else 0
    
    # 今月の活動数
    current_month = datetime.now().strftime('%Y-%m')
    recent_activity = sum(1 for log in rows if log[1].startswith(current_month))

    return {
        "total_logs": total_logs,
        "avg_score": round(avg_score, 1),
        "success_rate": round(success_rate, 1),
        "status_breakdown": status_counts,
        "recent_activity": recent_activity
    }

def get_followup_schedule(username=None, date_range_days=30, status_filter=None):
    """フォローアップ予定を取得（安全性・拡張性強化版）"""
    create_conversation_logs_table()
    conn = None
    
    try:
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()
        
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
    # conn = sqlite3.connect(DB_PATH)
    # cursor = conn.cursor()
    rows = execute_query("DELETE FROM conversation_logs WHERE id = ?", (log_id,))
    return rows > 0
