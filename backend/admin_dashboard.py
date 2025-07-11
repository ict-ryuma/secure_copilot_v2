import streamlit as st
import os
import yaml
import fitz  # PyMuPDF
from datetime import datetime
from backend.auth import get_current_user, get_all_teams  # 必要に応じて修正
from backend.knowledge_writer import save_knowledge_yaml  # 次ステップで作成

# --- 管理者ログインチェック ---
user = get_current_user()
if not user or not user.get("is_admin"):
    st.error("このページは管理者専用です。ログインしてください。")
    st.stop()

st.title("🛠 管理者ダッシュボード")

# --- サイドバー ---
with st.sidebar:
    st.header("📋 メニュー")
    menu = st.radio("機能を選択してください", ["ユーザー登録", "プロンプト設定", "事業学習登録"])

# --- チーム一覧取得（DBなどから） ---
teams = get_all_teams()  # 例: ["A_team", "B_team"]

# -----------------------------
# 📚 事業学習登録
# -----------------------------
if menu == "事業学習登録":
    st.subheader("📚 チーム別 事業学習 登録")

    team = st.selectbox("📌 対象チームを選択", teams)

    with st.expander("📝 テキストで登録"):
        title = st.text_input("タイトル")
        content = st.text_area("学習内容（Markdown対応）", height=200)

        if st.button("✅ 登録する", key="register_text"):
            if title and content:
                save_knowledge_yaml(team, title, content, user["username"])  # 後ほど実装
                st.success(f"{team} に登録しました ✅")
            else:
                st.warning("タイトルと内容を入力してください")

    with st.expander("📄 PDFから登録"):
        pdf_file = st.file_uploader("PDFファイルをアップロード", type="pdf")
        if pdf_file:
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
            st.text_area("📖 抽出されたテキスト", text, height=300)
            # 後ほど保存ボタンも追加可

# -----------------------------
# 🔑 ユーザー登録（ひな形）
# -----------------------------
elif menu == "ユーザー登録":
    st.subheader("👤 新規ユーザー登録（近日対応）")
    st.info("この機能は後ほど実装予定です")

# -----------------------------
# 🧠 プロンプト設定（ひな形）
# -----------------------------
elif menu == "プロンプト設定":
    st.subheader("🧠 チーム別 プロンプト設定（近日対応）")
    st.info("この機能は後ほど実装予定です")
