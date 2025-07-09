import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import yaml
import requests
import sqlite3
import fitz  # PyMuPDF for PDF parsing
from dotenv import load_dotenv
from backend.auth import get_current_user, register_user, get_all_teams, login_user
from backend.prompt_loader import get_prompts_for_team

# --- 安定動作のためのフルパス指定 ---
BASE_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = os.path.join(BASE_DIR, "backend", "prompt_config.yaml")
VISION_PATH = os.path.join(BASE_DIR, "team_knowledge", "company.yaml")
DB_PATH = os.path.join(BASE_DIR, "backend", "user_db.db")

load_dotenv()

st.set_page_config(page_title="🛠 管理者ダッシュボード", layout="wide")
st.title("🛠 管理者ダッシュボード")

# --- セッション初期化 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.team_name = ""
    st.session_state.is_admin = False

# --- ログイン画面 ---
if not st.session_state.logged_in:
    st.subheader("🔐 管理者ログイン")
    username = st.text_input("ユーザー名").strip()
    password = st.text_input("パスワード", type="password").strip()

    if st.button("ログイン"):
        success, team_name, is_admin = login_user(username, password)
        if success and is_admin:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.team_name = team_name
            st.session_state.is_admin = True
            st.rerun()
        elif success:
            st.error("❌ 管理者ではありません。")
        else:
            st.error("❌ ログインに失敗しました。")
    st.stop()

# --- 管理者チェック ---
user = get_current_user()
if not user or not user.get("is_admin"):
    st.error("このページは管理者専用です。ログインしてください。")
    st.stop()

# --- サイドバーの機能選択 ---
with st.sidebar:
    st.header("📋 管理メニュー")
    menu = st.radio("操作を選択", ["ユーザー登録", "プロンプト設定", "チーム管理", "会社ビジョン学習"])

# --- ユーザー登録機能 ---
if menu == "ユーザー登録":
    st.subheader("👤 新規ユーザー登録")
    new_username = st.text_input("ユーザー名")
    new_password = st.text_input("パスワード", type="password")
    team_options = get_all_teams()
    selected_team = st.selectbox("チームを選択", options=team_options)
    is_admin_flag = st.checkbox("管理者として登録")

    if st.button("登録実行"):
        if register_user(new_username, new_password, selected_team, is_admin_flag):
            st.success(f"✅ {new_username} を登録しました")
        else:
            st.error("❌ 登録に失敗しました（ユーザー名が重複している可能性）")

# --- プロンプト設定機能 ---
elif menu == "プロンプト設定":
    st.subheader("📝 チーム別プロンプト編集")
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            current_prompts = yaml.safe_load(f)
    except Exception as e:
        st.error(f"YAML読み込み失敗: {e}")
        current_prompts = {}

    if isinstance(current_prompts, dict) and current_prompts:
        team_keys = [k for k, v in current_prompts.items() if isinstance(v, dict)]
        edit_team = st.selectbox("編集するチームを選択", options=team_keys)

        if edit_team:
            new_text_prompt = st.text_area(
                "🗒 テキストプロンプト",
                current_prompts.get(edit_team, {}).get("text_prompt", ""),
                height=200
            )
            new_audio_prompt = st.text_area(
                "🎧 音声プロンプト",
                current_prompts.get(edit_team, {}).get("audio_prompt", ""),
                height=200
            )
            if st.button("💾 プロンプトを保存"):
                current_prompts[edit_team]["text_prompt"] = new_text_prompt
                current_prompts[edit_team]["audio_prompt"] = new_audio_prompt
                try:
                    with open(PROMPT_PATH, "w", encoding="utf-8") as f:
                        yaml.safe_dump(current_prompts, f, allow_unicode=True)
                    st.success("✅ YAMLを更新しました")
                except Exception as e:
                    st.error(f"❌ 保存に失敗しました: {e}")
    else:
        st.warning("⚠️ 編集可能なチームプロンプトが見つかりません。")

# --- チーム管理機能 ---
elif menu == "チーム管理":
    st.subheader("🏷 チーム一覧管理")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, prompt_key FROM teams")
    teams = cursor.fetchall()

    for team in teams:
        team_id, name, desc, key = team
        with st.expander(f"✏️ {name}"):
            new_name = st.text_input(f"チーム名（{name}）", value=name, key=f"name_{team_id}")
            new_desc = st.text_area(f"説明（{name}）", value=desc, key=f"desc_{team_id}")
            new_key = st.text_input(f"プロンプトキー（{name}）", value=key, key=f"key_{team_id}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存", key=f"save_{team_id}"):
                    cursor.execute("""
                        UPDATE teams SET name = ?, description = ?, prompt_key = ?
                        WHERE id = ?
                    """, (new_name, new_desc, new_key, team_id))
                    conn.commit()
                    st.success("✅ チーム情報を更新しました")
                    st.rerun()
            with col2:
                if st.button("🗑️ 削除", key=f"delete_{team_id}"):
                    cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
                    conn.commit()
                    st.warning("⚠️ チームを削除しました")
                    st.rerun()
    conn.close()

# --- 会社ビジョン学習機能 ---
elif menu == "会社ビジョン学習":
    st.subheader("🏢 会社資料をアップロードしてビジョンを学習")
    title = st.text_input("ビジョンのタイトル")
    pdf_file = st.file_uploader("📄 PDFファイルをアップロード", type="pdf")

    if pdf_file:
        try:
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
            st.text_area("📖 抽出された内容", text, height=300)

            if st.button("💾 YAMLに保存"):
                if not os.path.exists(os.path.dirname(VISION_PATH)):
                    os.makedirs(os.path.dirname(VISION_PATH))
                try:
                    if os.path.exists(VISION_PATH):
                        with open(VISION_PATH, "r", encoding="utf-8") as f:
                            existing = yaml.safe_load(f) or {}
                    else:
                        existing = {}

                    if "ビジョン一覧" not in existing:
                        existing["ビジョン一覧"] = []

                    existing["ビジョン一覧"].append({
                        "タイトル": title,
                        "内容": text,
                        "登録者": st.session_state.username,
                        "登録日時": st.session_state.get("timestamp", "")
                    })

                    with open(VISION_PATH, "w", encoding="utf-8") as f:
                        yaml.safe_dump(existing, f, allow_unicode=True)
                    st.success("✅ ビジョンを保存しました")
                except Exception as e:
                    st.error(f"❌ 保存エラー: {e}")
        except Exception as e:
            st.error(f"❌ PDF読み込みエラー: {e}")
