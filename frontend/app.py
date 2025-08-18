import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
from dotenv import load_dotenv
from logger_config import logger

from users.hyouka_lists import hyouka_list_view

from admins.login_check import login_check,login
from admins.logout import logout
from users.menu import menu
from users.load_prompts import load_team_prompts
from users.hyouka_form import hyouka_form

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

if st.session_state["authentication_status"] and cookie_user_data:
    # name = st.session_state.get("name")
    st.title("🔧 Userダッシュボード")
    st.markdown("## 👤 ログイン情報")
    st.write(f"ようこそ、{st.session_state.username}さん！")
    st.markdown(f"- チーム: `{st.session_state.team_name}`")
        
    st.markdown("---")


    # --- セッション初期化 ---
    # --- ログイン画面 ---
    # --- サイドバー：ログインUI or ログイン情報 ---
    with st.sidebar:
        menu = menu()
    if menu == "評価を作成":
        hyouka_form()
    if menu == "🔄 プロンプト再取得":
        load_team_prompts() 
    if menu == "評価を選択":
        hyouka_list_view() 
    elif menu == "🔓 ログアウト":
        logout(cookie_manager,app_name) 
else:
    st.write("### 🔐 ログイン画面")
    login(cookie_manager,app_name,login_type="user")


    # else:
#         
        
#         if st.button("🔄 プロンプト再取得"):
#             

#         st.markdown("---")
#         


# # --- プロンプト取得（ログイン済みチェック） ---
# if not st.session_state.logged_in:
#     st.stop()

# # ✅ デバッグログで team_name 確認
# team_name = st.session_state.get("team_name", "").strip()
# print(f"✅ セッションから取得した team_name: '{team_name}'")

# if not team_name:
#     st.error("❌ チーム情報（team_name）が取得できていません。ログインし直してください。")
#     st.session_state.logged_in = False
#     st.stop()


# # ✅ プロンプト取得とエラーハンドリング（大幅改善）


# ✅ メインロジック部分の修正
# def main_app():
#     """メインアプリケーション"""
   
    
    # ✅ プロンプトが未取得、またはエラーがある場合は取得
    # if "prompts" not in st.session_state or not st.session_state.prompts or st.session_state.prompts.get("error", False):
    #     if not load_team_prompts():
    #         st.stop()  # プロンプト取得に失敗した場合は停止
    
    # # ✅ セッションからプロンプトを取得
    # prompts = st.session_state.prompts
    
    # if not prompts or prompts.get("error", False):
    #     st.error("プロンプト設定に問題があります。上記の指示に従って解決してください。")
    #     st.stop()
    
    # # ✅ 各種プロンプトを展開
    # custom_prompt = prompts.get("text_prompt", "")
    # audio_prompt = prompts.get("audio_prompt", "")
    # score_items = prompts.get("score_items", [])
    
    # # ✅ デバッグ用：プロンプト内容確認
    # print(f"🔍 使用中プロンプト:")
    # print(f"  - team_name: {prompts.get('team_name')}")
    # print(f"  - prompt_key: {prompts.get('prompt_key')}")
    # print(f"  - text_prompt: '{custom_prompt[:100]}...' (長さ: {len(custom_prompt)})")
    # print(f"  - audio_prompt: '{audio_prompt[:50]}...' (長さ: {len(audio_prompt)})")
    # print(f"  - score_items: {score_items}")
    
    # ✅ プロンプトが空の場合の警告
    # if not custom_prompt.strip():
    #     st.warning("⚠️ テキスト評価プロンプトが設定されていません。管理者にお問い合わせください。")

# ✅ メイン実行部分
# if __name__ == "__main__":
    # # ログイン処理（既存）
    # if not st.session_state.get("logged_in", False):
    #     # ログイン画面表示
    #     # ...existing login code...
    #     pass
    # else:
    #     # ログイン済みの場合、メインアプリを実行
        # main_app()
