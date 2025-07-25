# patch_add_admin_flag.py

from backend.mysql_connector import execute_query
try:
    execute_query("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    print("✅ is_admin カラムを追加しました")
except Exception as e:
    if "duplicate column name" in str(e):
        print("⚠️ is_admin カラムは既に存在します")
    else:
        raise
finally:
    pass
