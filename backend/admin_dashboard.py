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
try:
    teams = get_all_teams()
    if not teams:
        teams = ["A_team", "B_team"]  # フォールバック
except Exception as e:
    st.error(f"チーム情報の取得に失敗しました: {e}")
    teams = ["A_team", "B_team"]

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
                try:
                    save_knowledge_yaml(team, title, content, user["username"])
                    st.success(f"{team} に登録しました ✅")
                except ValueError as e:
                    st.error(f"登録エラー: {e}")
                except Exception as e:
                    st.error(f"予期しないエラーが発生しました: {e}")
            else:
                st.warning("タイトルと内容を入力してください")

    with st.expander("📄 PDFから登録"):
        pdf_file = st.file_uploader("PDFファイルをアップロード", type="pdf")
        if pdf_file:
            try:
                doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
                text = "\n".join([page.get_text() for page in doc])
                doc.close()
                
                st.text_area("📖 抽出されたテキスト", text, height=300)
                
                # PDFから抽出したテキストの保存機能
                pdf_title = st.text_input("PDFのタイトル", value=pdf_file.name.replace('.pdf', ''))
                
                if st.button("📄 PDFテキストを保存", key="save_pdf"):
                    if pdf_title and text:
                        try:
                            save_knowledge_yaml(team, pdf_title, text, user["username"], "PDF資料")
                            st.success(f"PDF「{pdf_title}」を{team}に保存しました ✅")
                        except ValueError as e:
                            st.error(f"保存エラー: {e}")
                        except Exception as e:
                            st.error(f"予期しないエラーが発生しました: {e}")
                    else:
                        st.warning("タイトルとテキストが必要です")
                        
            except Exception as e:
                st.error(f"PDFの読み込みに失敗しました: {e}")

# -----------------------------
# 🔑 ユーザー登録（ひな形）
# -----------------------------
elif menu == "ユーザー登録":
    st.subheader("👤 新規ユーザー登録")
    
    with st.form("user_registration"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        selected_team = st.selectbox("所属チーム", teams)
        is_admin = st.checkbox("管理者権限")
        
        submitted = st.form_submit_button("🔑 ユーザー登録")
        
        if submitted:
            if username and password:
                try:
                    from backend.auth import register_user
                    success = register_user(username, password, selected_team, is_admin)
                    if success:
                        st.success(f"ユーザー「{username}」を{selected_team}に登録しました ✅")
                    else:
                        st.error("ユーザー登録に失敗しました（既に存在するユーザー名の可能性があります）")
                except Exception as e:
                    st.error(f"登録エラー: {e}")
            else:
                st.warning("ユーザー名とパスワードを入力してください")

# -----------------------------
# 🧠 プロンプト設定（ひな形）
# -----------------------------
elif menu == "プロンプト設定":
    st.subheader("🧠 チーム別 プロンプト設定（近日対応）")
    st.info("この機能は後ほど実装予定です")
