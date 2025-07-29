# mysql_connector.py

import os
import mysql.connector
from mysql.connector import pooling


# 接続プール設定
connection_pool = None
appEnv=os.environ.get("APP_ENV", "local")
if appEnv == "local":
    dbHost="host.docker.internal"
else:
    dbHost=os.environ.get("DB_HOST", "mysql")

def init_connection_pool():
    """MySQL接続プールを初期化"""
    global connection_pool
    if connection_pool is None:
        config = {
            'host': dbHost,
            'user': os.environ.get("DB_USER", "root"),
            'password': os.environ.get("DB_PASSWORD", ""),
            'database': os.environ.get("DB_NAME", ""),
            'port': int(os.environ.get("DB_PORT", 3306)),
            'pool_name': 'secure_copilot_pool',
            'pool_size': 5,
            'pool_reset_session': True,
            'autocommit': False,
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        connection_pool = pooling.MySQLConnectionPool(**config)

def get_connection():
    """Establish and return a connection to the MySQL database."""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
    
    try:
        return connection_pool.get_connection()
    except Exception as e:
        print(f"[ERROR] Failed to get connection from pool: {e}")
        # フォールバック: 直接接続
        return mysql.connector.connect(
            host=dbHost,
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", ""),
            port=int(os.environ.get("DB_PORT", 3306)),
            charset='utf8mb4',
            use_unicode=True
        )

def execute_query(query, params=None, fetch=False):
    """Executes a given SQL query with optional parameters and fetch option."""
    conn = None
    cursor = None
    result = None

    try:
        conn = get_connection()
        cursor = conn.cursor(buffered=True)  # buffered=Trueを追加
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
        
        # 残りの結果セットがあれば消費
        try:
            while cursor.nextset():
                if fetch:
                    cursor.fetchall()
        except:
            pass
            
    except Exception as e:
        print(f"[ERROR] execute_query: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

    return result

def execute_select_query(query, params=None):
    """SELECT専用のクエリ実行関数"""
    conn = None
    cursor = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        
        # 残りの結果セットがあれば消費
        try:
            while cursor.nextset():
                cursor.fetchall()
        except:
            pass
            
        return result
    except Exception as e:
        print(f"[ERROR] {e}")
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def execute_modify_query(query, params=None):
    """INSERT/UPDATE/DELETE専用のクエリ実行関数"""
    conn = None
    cursor = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute(query, params or ())
        conn.commit()
        rowcount = cursor.rowcount
        
        # 残りの結果セットがあれば消費
        try:
            while cursor.nextset():
                pass
        except:
            pass
            
        return rowcount
    except Exception as e:
        print(f"[ERROR] {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
