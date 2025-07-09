# patch_add_admin_flag.py

import sqlite3

DB_PATH = "secure_copilot.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

try:
    c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    conn.commit()
    print("✅ is_admin カラムを追加しました")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ is_admin カラムは既に存在します")
    else:
        raise
finally:
    conn.close()
