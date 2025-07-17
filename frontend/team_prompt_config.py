import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend import db_team_master, db_prompt_key_master

st.set_page_config(page_title="チーム × プロンプトキー設定", page_icon="🧩")

st.title("🧩 チームごとのプロンプトキー設定")

# --- データ取得 ---
teams = db_team_master.fetch_all_team_prompts()
prompt_keys = db_prompt_key_master.get_active_prompt_keys()

if not teams:
    st.warning("チームが登録されていません。")
else:
    for team in teams:
        id_, team_name, current_key, *_ = team

        st.markdown(f"### 🏷️ {team_name}")
        col1, col2 = st.columns([5, 2])

        with col1:
            new_key = st.selectbox(
                f"プロンプトキー（現在: `{current_key}`）",
                options=prompt_keys,
                index=prompt_keys.index(current_key) if current_key in prompt_keys else 0,
                key=f"key_select_{id_}"
            )

        with col2:
            if st.button("更新する", key=f"update_{id_}"):
                # チーム情報を再取得して更新（その他の値はそのまま使う）
                current = db_team_master.fetch_team_prompt_by_id(id_)
                if current:
                    _, _, _, text_prompt, audio_prompt, score_items, notes, *_ = current
                    db_team_master.update_team_prompt(
                        id=id_,
                        team_name=team_name,
                        prompt_key=new_key,
                        text_prompt=text_prompt,
                        audio_prompt=audio_prompt,
                        score_items=score_items,
                        notes=notes
                    )
                    st.success(f"{team_name} に '{new_key}' を設定しました")
                    st.rerun()

        st.markdown("---")
