import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from admins.menu import menu
from admins.users import register, user_lists
from admins.teams import team_manage
from admins.prompts import prompt_manage
from admins.login_check import login_check,login
from admins.logout import logout
from logger_config import logger
from admins.teams_and_prompt import team_prompt_settings
# from admins.company_visions import companyVisionLearn
from admins.shodan_bunseki import shodan_bunseki
# from admins.team_performance_dashboard import tpdb
# from admins.followup_management import followupManagement
import json

app_name="python-APP-admin"
load_dotenv()
cookie_manager,cookie_user_data=login_check(app_name)
# logger.info(f"cookie_user_data: {cookie_user_data}")
if st.session_state["authentication_status"] and cookie_user_data:
    # name = st.session_state.get("name")
    st.title("🔧 管理者ダッシュボード")
    st.write(f"ようこそ、{st.session_state.username}さん！")
    with st.sidebar:
        menu = menu()
        # Logout function 
        logout(cookie_manager,app_name)
        # --- メニュー分岐 ---
    if menu == "チーム管理":
        team_manage()
    if menu == "プロンプト管理":
        prompt_manage()
    elif menu == "ユーザー登録":
        register() 
    elif menu == "チームプロンプト設定":
        team_prompt_settings()
    elif menu == "ユーザー一覧":
        user_lists()
    elif menu == "📊 商談振り返り・分析":
        shodan_bunseki()
    # elif menu == "チームごとのプロンプトキー設定":
    #     team_prompt_settings()
    # # ✅ 修正: ユーザー一覧編集セクション

    # # ✅ 修正: チーム管理セクション
    # elif menu == "チーム管理":
    #     teamManage()


    # elif menu == "プロンプトキー管理":
    #     teamPromptKeyManage()

    # elif menu == "会社ビジョン学習":
    #     companyVisionLearn()

    # elif menu == "ユーザー一覧":
    #     userLists()


    # # ✅ 修正: 商談評価ログ登録セクションを完全削除し、閲覧専用の商談分析に統合

    # # ✅ 既存のチーム別ダッシュボードとフォローアップ管理は変更なし
    # elif menu == "🏢 チーム別ダッシュボード":
    #     tpdb()

    # elif menu == "📅 フォローアップ管理":
    #     followupManagement()   
else:
    st.write("### 🔐 管理者ログイン")
    login(cookie_manager,app_name,login_type="admin")

    