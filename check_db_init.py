# check_db_init.py
from backend.save_log import init_db
import sqlite3

init_db()

conn = sqlite3.connect("score_log.db")
cursor = conn.cursor()

print("📋 現在のテーブル一覧:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(" -", t[0])

print("\n📌 evaluations テーブル構造:")
cursor.execute("PRAGMA table_info(evaluations);")
for col in cursor.fetchall():
    print(f" - {col[1]} ({col[2]})")

conn.close()
