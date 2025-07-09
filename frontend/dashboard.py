import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import yaml
from backend.auth import get_current_user, register_user, get_all_teams
from backend.prompt_loader import get_prompts_for_team

PROMPT_PATH = os.path.join(Path(__file__).resolve().parents[1], "backend", "prompt_config.yaml")

# --- 管理者チェック ---
user = get_current_user()
if not user or not user.get("is_admin"):
    st.error("このページは管理者専用です。ログインしてください。")
    st.stop()

st.set_page_config(page_title="🛠 管理者ダッシュボード", layout="wide")
st.title("🛠 管理者ダッシュボード")

# --- サイドバーの機能選択 ---
with st.sidebar:
    st.header("📋 管理メニュー")
    menu = st.radio("操作を選択", ["ユーザー登録", "プロンプト設定"])

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
