# register_user_cli.py
from backend.auth import register_user

# 登録内容
username = "ryuma"
password = "star76"
team_name = "A_team"
is_admin = True

# 登録実行
success = register_user(username, password, team_name, is_admin)
if success:
    print("✅ ユーザー登録成功")
else:
    print("❌ ユーザー登録失敗（すでに存在？）")
