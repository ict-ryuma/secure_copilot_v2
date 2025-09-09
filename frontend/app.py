import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
from dotenv import load_dotenv
from logger_config import logger

from users.hyouka_lists import mi_hyouka_list_view,hyouka_list_view

from admins.login_check import login_check,login
from admins.logout import logout,logout_view
from users.menu import menu
from users.load_prompts import load_team_prompts
from users.hyouka_form import hyouka_form
from team_validation import get_valid_team_for_user
from auto_refresh import auto_refresh_view

# --- 初期化 ---
app_name="python-APP-user"
load_dotenv()
# init_db()
# init_auth_db()
BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")

LOGIN_API_URL = BASE_API_URL+"/login"
GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"
cookie_manager,cookie_user_data=login_check(app_name)
# st.set_page_config(page_title="📞 商談テキスト評価AI", layout="wide")

    # --- セッション初期化 ---
if st.session_state["authentication_status"] and cookie_user_data:
    # name = st.session_state.get("name")
    st.title("🔧 Userダッシュボード")
    st.markdown("## 👤 ログイン情報")
    st.write(f"ようこそ、{st.session_state.username}さん！")
    st.markdown(f"- チーム: `{st.session_state.team_name}`")
        
    st.markdown("---")

    # ✅ Always run this once for any action
    get_valid_team_for_user(cookie_manager,app_name)
    # auto_refresh_view(cookie_manager,app_name) # Auto-refresh function for team info every 5 seconds
    # --- サイドバー：ログインUI or ログイン情報 ---
    with st.sidebar:
        menu = menu()
        # Logout function
        logout_view(cookie_manager,app_name)
        st.markdown("---")
        st.write(menu)
    if menu == "商談を作成":
        hyouka_form()
    if menu == "未評価の商談を選択してください":
        mi_hyouka_list_view()
    if menu == "評価の商談を選択してください":
        hyouka_list_view()
else:
    # --- ログイン画面 ---
    st.write("### 🔐 ログイン画面")
    login(cookie_manager,app_name,login_type="user")
