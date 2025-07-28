# check_db_init.py
from backend.save_log import init_db
from backend.mysql_connector import execute_query

init_db()


print("📋 現在のテーブル一覧:")
tables = execute_query("SELECT name FROM sqlite_master WHERE type='table';", fetch=True)
for t in tables:
    print(" -", t[0])

print("\n📌 evaluations テーブル構造:")
columns = execute_query("PRAGMA table_info(evaluations);", fetch=True)
for col in columns:
    print(f" - {col[1]} ({col[2]})")
