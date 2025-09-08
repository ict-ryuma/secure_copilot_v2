import streamlit as st
from backend.teams import get_teams,create_team_has_prompts,get_team_has_prompts,update_team_has_prompts
from backend.prompts import get_prompts
from pagination import paginate

def create_team_prompt(team_options,prompt_options,adm_user_id):
    st.markdown("---")
    st.subheader("🆕 チーム追加フォーム")
    try:
        
        selected_team = st.selectbox(
            "チームを選択",
            options=team_options,
            format_func=lambda team: team[1],  # Display team_name
            help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）"
        )
        selected_prompt = st.selectbox(
            "プロンプトキーを選択",
            options=prompt_options,
            format_func=lambda prompt: prompt[1],  # Display team_name
            help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）"
        )
        is_active = st.checkbox("有効化",value=1)
        if st.button("登録実行"):
            success,message=create_team_has_prompts(selected_team[0],selected_prompt[0],is_active,adm_user_id)
            if success:
                st.success(message)
            else:
                st.error(message)
    except Exception as e:
        st.error(f"プロンプトキー設定でエラーが発生しました: {e}")

def view_team_prompt(team_options,prompt_options,adm_user_id):
    st.markdown("### 📋 現在のチームごとのプロンプトキー一覧")
    team_prompts = get_team_has_prompts()
    # st.write(team_prompts)
    if team_prompts:
        page_datas, start_idx, _ = paginate(team_prompts)
        for i, thp in enumerate(page_datas):
            # ✅ 修正: 9列に対応
            team_has_prompt_id, team_id, prompt_id, is_active_db, created_by, created_at, updated_at, team_name, prompt_key = thp
            if is_active_db==1:
                status = "🟢 正常"
            else:
                status = "⚠️ 非アクティブ"
            with st.expander(f"{status} `{team_name}` | `{prompt_key}` → (更新: {updated_at})"):
                default_team_option = next((opt_team for opt_team in team_options if opt_team[0] == team_id), None)
                default_prompt_option = next((opt for opt in prompt_options if opt[0] == prompt_id), None)
                selected_team = st.selectbox(
                    "チームを選択",
                    options=team_options,
                    format_func=lambda team: team[1],  # Display team_name
                    help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）",
                    index=team_options.index(default_team_option) if default_team_option else 0,
                    key=f"team_select_{i}"
                )
                selected_prompt = st.selectbox(
                    "プロンプトキーを選択",
                    options=prompt_options,
                    format_func=lambda prompt: prompt[1],  # Display team_name
                    help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）",
                    index=prompt_options.index(default_prompt_option) if default_prompt_option else 0,
                    key=f"prompt_select_{i}"
                )
                is_active = st.checkbox("有効化",value=is_active_db,key=f"is_active_{i}")
                if st.button("更新実行",key=f"update_btn_{i}"):
                    success,message=update_team_has_prompts(team_has_prompt_id,selected_team[0],selected_prompt[0],is_active,adm_user_id)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    else:
        st.info("登録されているチームがありません。")


def team_prompt_settings():
    st.subheader("🧩 チームごとのプロンプトキー設定")
    adm_user_id = st.session_state["user_id"]
    team_options = get_teams(only_active=1)
    prompt_options = get_prompts(only_active=1)

    view_team_prompt(team_options,prompt_options,adm_user_id)
    create_team_prompt(team_options,prompt_options,adm_user_id)