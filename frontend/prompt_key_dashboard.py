import sys
import os

# --- 親ディレクトリをパスに追加（backendを読み込むため） ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend import db_prompt_key_master

st.set_page_config(page_title="プロンプトキー管理", page_icon="🧠")

st.title("🧠 プロンプトキー管理ダッシュボード")

# --- 初期化：テーブル作成（初回のみ必要） ---
db_prompt_key_master.create_prompt_key_master_table()

# --- サクセスメッセージ用セッションステート ---
if "success_message" not in st.session_state:
    st.session_state.success_message = ""

# --- 表示：登録済みプロンプトキー一覧（全件） ---
st.subheader("📋 プロンプトキー一覧")

all_keys = db_prompt_key_master.fetch_all_prompt_keys()

if all_keys:
    for key in all_keys:
        id_, prompt_key, description, is_active, created_at = key
        status_icon = "🟢" if is_active else "⚪️"
        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(
                f"""**{status_icon} {prompt_key}** — {description or '(説明なし)'}  
<span style='font-size:12px;color:gray;'>作成日: {created_at}</span>""",
                unsafe_allow_html=True,
            )

        with col2:
            if is_active:
                if st.button("無効化", key=f"deactivate_{id_}"):
                    db_prompt_key_master.update_prompt_key(
                        id=id_,
                        prompt_key=prompt_key,
                        description=description,
                        is_active=0,
                    )
                    st.success(f"'{prompt_key}' を無効化しました")
                    st.rerun()
else:
    st.info("登録されたプロンプトキーがありません。")

st.markdown("---")

# --- 新規登録フォーム ---
st.subheader("🆕 プロンプトキーの新規追加")

with st.form("prompt_key_form"):
    new_key = st.text_input("プロンプトキー", max_chars=100)
    description = st.text_area("説明（任意）", height=80)
    submitted = st.form_submit_button("登録する")

    if submitted:
        if new_key.strip():
            try:
                db_prompt_key_master.insert_prompt_key(new_key.strip(), description.strip())
                st.session_state.success_message = f"✅ '{new_key}' を登録しました"
                st.rerun()
            except Exception as e:
                st.error(f"登録に失敗しました: {e}")
        else:
            st.warning("プロンプトキーは必須です。")

# --- 成功メッセージ表示（再描画用） ---
if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = ""
