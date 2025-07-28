# mysql_connector.py

import os
import mysql.connector

def get_connection():
    """Establish and return a connection to the MySQL database."""
    return mysql.connector.connect(
        host="host.docker.internal",
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", ""),
        port=int(os.environ.get("DB_PORT", 3306))

    #      DB_HOST: ${MYSQL_HOST}
    #   DB_PORT: ${MYSQL_PORT}
    #   DB_USER: ${MYSQL_USER}
    #   DB_PASSWORD: ${MYSQL_PASSWORD}
    #   DB_NAME: ${MYSQL_DATABASE}
    )

def execute_query(query, params=None, fetch=False):
    """Executes a given SQL query with optional parameters and fetch option."""
    conn = get_connection()
    cursor = conn.cursor()
    result = None

    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()

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
