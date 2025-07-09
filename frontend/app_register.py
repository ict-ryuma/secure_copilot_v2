import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.auth import init_auth_db, register_user, get_all_teams

# --- 初期化 ---
init_auth_db()
st.title("🆕 ユーザー登録（初期用）")

username = st.text_input("ユーザー名")
password = st.text_input("パスワード", type="password")
team = st.selectbox("所属チーム", get_all_teams())
is_admin = st.checkbox("管理者として登録")

if st.button("登録"):
    if register_user(username, password, team, is_admin):
        st.success("✅ 登録完了しました。ログイン画面に戻ってください。")
    else:
        st.error("⚠️ このユーザー名は既に存在します。")
