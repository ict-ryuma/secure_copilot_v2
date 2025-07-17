import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import yaml
import sqlite3
import fitz  # PyMuPDF
from dotenv import load_dotenv
from backend.auth import (
    get_current_user, register_user, get_all_teams, login_user,
    update_user_role, delete_user
)
from backend.db_team_master import (
    create_team_master_table, insert_team_prompt,
    fetch_all_team_prompts, update_team_prompt, delete_team_prompt
)
from backend.db_prompt_key_master import (
    create_prompt_key_master_table, insert_prompt_key,
    fetch_all_prompt_keys, get_active_prompt_keys
)

# --- パス設定 ---
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

user = get_current_user()
if not user["is_admin"]:
    st.error("このページは管理者専用です。ログインしてください。")
    st.stop()

with st.sidebar:
    st.header("📋 管理メニュー")
    menu = st.radio("操作を選択", [
        "ユーザー登録", "チーム管理",
        "チームプロンプト設定", "プロンプトキー管理",
        "会社ビジョン学習", "ユーザー一覧",
        "チームごとのプロンプトキー設定" 
    ])

# --- ユーザー登録 ---
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

# --- チーム管理 ---
elif menu == "チーム管理":
    st.subheader("🏷️ チーム一覧管理")
    create_team_master_table()
    teams = fetch_all_team_prompts()
    for t in teams:
        st.markdown(f"- `{t[1]}` → プロンプトキー: `{t[2]}`")

    # --- チーム追加フォーム ---
    st.markdown("---")
    st.subheader("🆕 チーム追加フォーム")
    with st.form("add_team_form"):
        new_name = st.text_input("チーム名")
        new_key = st.text_input("プロンプトキー")
        new_desc = st.text_input("チームの説明", placeholder="任意（例：新車担当）")

        if st.form_submit_button("✅ チームを登録"):
            if new_name and new_key:
                insert_team_prompt(
                    name=new_name,
                    key=new_key,
                    text_prompt="（未設定）",
                    audio_prompt="（未設定）",
                    score_items="ヒアリング姿勢,説明のわかりやすさ,クロージングの一貫性,感情の乗せ方と誠実さ,対話のテンポ",
                    notes=new_desc or "（備考なし）"
                )
                st.success("✅ チームを追加しました")
                st.rerun()
            else:
                st.warning("⚠️ チーム名とプロンプトキーは必須です")

# --- チームプロンプト設定 ---
elif menu == "チームプロンプト設定":
    st.subheader("🧠 チームプロンプト管理（DBベース）")
    teams = fetch_all_team_prompts()
    for team in teams:
        st.markdown("---")
        with st.expander(f"✏️ {team[1]} ({team[2]})"):
            with st.form(f"form_{team[0]}"):
                new_name = st.text_input("チーム名", team[1])
                new_key = st.text_input("プロンプトキー", team[2])
                new_text = st.text_area("テキストプロンプト", team[3], height=120)
                new_audio = st.text_area("音声プロンプト", team[4], height=80)
                new_score = st.text_input("スコア項目（カンマ区切り）", team[5])
                new_note = st.text_area("補足・備考", team[6])
                is_active = st.checkbox("✅ このチームを有効にする", value=team[7] == 1)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 更新"):
                        update_team_prompt(team[0], new_name, new_key, new_text, new_audio, new_score, new_note, int(is_active))
                        st.success("更新しました")
                        st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ 削除"):
                        delete_team_prompt(team[0])
                        st.warning("削除しました")
                        st.rerun()
# --- プロンプトキー管理 ---
elif menu == "プロンプトキー管理":
    st.subheader("📋 プロンプトキー一覧と操作")
    create_prompt_key_master_table()
    keys = fetch_all_prompt_keys()

    for key in keys:
        id_, prompt_key, description, is_active, created_at = key
        status = "🟢 有効" if is_active else "⚪️ 無効"
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"**{status}** `{prompt_key}` — {description or '(説明なし)'}")
            st.caption(f"作成日: {created_at}")
        with col2:
            if is_active:
                if st.button(f"⚪️ 無効化", key=f"deactivate_{id_}"):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE prompt_key_master SET is_active = 0 WHERE id = ?", (id_,))
                    conn.commit()
                    conn.close()
                    st.success(f"'{prompt_key}' を無効化しました")
                    st.rerun()

    st.markdown("---")
    st.subheader("🆕 プロンプトキー新規追加")
    with st.form("new_prompt_form"):
        new_key = st.text_input("プロンプトキー名")
        new_desc = st.text_area("説明", height=80)  # ✅ height修正：60 → 80（68以上必要）
        if st.form_submit_button("✅ 登録"):
            if new_key:
                insert_prompt_key(new_key.strip(), new_desc.strip())
                st.success(f"✅ '{new_key}' を登録しました")
                st.rerun()
            else:
                st.warning("プロンプトキー名を入力してください")
# --- チームごとのプロンプトキー設定 ---
elif menu == "チームごとのプロンプトキー設定":
    st.subheader("🧩 チームごとのプロンプトキー設定")

    teams = fetch_all_team_prompts()
    keys = get_active_prompt_keys()  # 有効なプロンプトキーのみ取得
    key_options = [k[1] for k in keys]  # [(id, key, ...)] → keyだけ抽出

    if not key_options:
        st.info("有効なプロンプトキーがありません。まずはプロンプトキーを登録してください。")
    else:
        for team in teams:
            team_id, team_name, current_key = team[0], team[1], team[2]

            st.markdown(f"---\n### 🧩 {team_name}")
            with st.form(f"form_update_key_{team_id}"):
                st.caption(f"プロンプトキー（現在: `{current_key}`）")
                new_key = st.selectbox("プロンプトキーを選択", key_options, index=key_options.index(current_key) if current_key in key_options else 0)
                if st.form_submit_button("更新する"):
                    update_team_prompt(
                        team_id,
                        team_name,
                        new_key,
                        team[3],
                        team[4],
                        team[5],
                        team[6],
                        team[7]
                    )
                    st.success(f"{team_name} のプロンプトキーを `{new_key}` に更新しました")
                    st.rerun()
# --- 会社ビジョン学習 ---
elif menu == "会社ビジョン学習":
    st.subheader("🏢 会社ビジョンを学習させる")
    uploaded_file = st.file_uploader("会社ビジョンPDFをアップロード", type=["pdf"])
    if uploaded_file:
        try:
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                text = "\n".join([page.get_text() for page in doc])
            st.success("✅ PDFを読み込みました")
            st.text_area("抽出されたテキスト", text, height=300)
            if st.button("📥 YAMLとして保存"):
                os.makedirs(os.path.dirname(VISION_PATH), exist_ok=True)
                with open(VISION_PATH, "w", encoding="utf-8") as f:
                    yaml.dump({"company_vision": text}, f, allow_unicode=True)
                st.success("✅ company.yaml に保存しました")
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {e}")

# --- ユーザー一覧 ---
elif menu == "ユーザー一覧":
    st.subheader("👥 登録ユーザー一覧と編集")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, team_name, is_admin FROM users ORDER BY team_name, username")
    users = cursor.fetchall()
    conn.close()

    if users:
        current_team = None
        for username, team, is_admin in users:
            if current_team != team:
                st.markdown(f"### 🏷️ チーム: `{team}`")
                current_team = team
            with st.form(f"user_form_{username}"):
                cols = st.columns([4, 2, 2])
                with cols[0]:
                    st.markdown(f"**{username}**")
                with cols[1]:
                    admin_flag = st.checkbox("管理者", value=bool(is_admin), key=f"admin_{username}")
                with cols[2]:
                    if st.form_submit_button("🗑️ 削除", type="primary"):
                        delete_user(username)
                        st.warning(f"{username} を削除しました")
                        st.rerun()
                if st.form_submit_button(f"💾 更新（{username}）", type="secondary"):
                    update_user_role(username, admin_flag)
                    st.success(f"{username} の権限を更新しました")
                    st.rerun()
    else:
        st.info("登録されているユーザーがいません。")
