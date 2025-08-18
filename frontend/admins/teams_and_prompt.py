import streamlit as st
from backend.teams import get_teams,create_team_has_prompts,get_team_has_prompts,update_team_has_prompts
from backend.prompts import get_prompts
from backend.mysql_connector import execute_query

# def teamPromptKeyManage():
#     st.subheader("📋 プロンプトキー一覧と操作")
#     try:
        
#         # ✅ 修正: team_masterテーブルから取得（統一）
#         # conn = sqlite3.connect(PROMPT_DB_PATH)
#         # cursor = conn.cursor()
#         keys = execute_query("""
#             SELECT id, prompt_key, notes as description, is_active, updated_at 
#             FROM team_master 
#             ORDER BY team_name
#         """, fetch=True)
#         # keys = cursor.fetchall()
#         # conn.close()

#         # 既存のプロンプトキー表示ロジックはそのまま
#         for key in keys:
#             id_, prompt_key, description, is_active, created_at = key
#             status = "🟢 有効" if is_active else "⚪️ 無効"
#             col1, col2 = st.columns([6, 1])
#             with col1:
#                 st.markdown(f"**{status}** `{prompt_key}` — {description or '(説明なし)'}")
#                 st.caption(f"作成日: {created_at}")
#             with col2:
#                 if is_active:
#                     if st.button(f"⚪️ 無効化", key=f"deactivate_{id_}"):
#                         # conn = sqlite3.connect(PROMPT_DB_PATH)
#                         # cursor = conn.cursor()
#                         execute_query("UPDATE prompt_key_master SET is_active = 0 WHERE id = %s", (id_,))
#                         # conn.commit()
#                         # conn.close()
#                         st.success(f"'{prompt_key}' を無効化しました")
#                         st.rerun()

#         st.markdown("---")
#         st.subheader("🆕 プロンプトキー新規追加")
#         with st.form("new_prompt_form"):
#             new_key = st.text_input("プロンプトキー名")
#             new_desc = st.text_area("説明", height=80)
#             if st.form_submit_button("✅ 登録"):
#                 if new_key:
#                     # team_masterテーブルに統一して登録
#                     insert_team_prompt(
#                         name=f"チーム_{new_key}",
#                         key=new_key.strip(),
#                         text_prompt="デフォルトプロンプト",
#                         audio_prompt="デフォルト音声プロンプト", 
#                         score_items='["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
#                         notes=new_desc.strip()
#                     )
#                     st.success(f"✅ '{new_key}' を登録しました")
#                     st.rerun()
#                 else:
#                     st.warning("プロンプトキー名を入力してください")
#     except Exception as e:
#         st.error(f"プロンプトキー管理でエラーが発生しました: {e}")
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
        for i, thp in enumerate(team_prompts):
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
                    # selected_team_id=selected_team[0]
                    # selected_prompt_id=selected_prompt[0]
                    # st.write(f"選択チーム: {selected_team_id}, 選択プロンプト: {selected_prompt_id}, 状態: {is_active}")
                    success,message=update_team_has_prompts(team_has_prompt_id,selected_team[0],selected_prompt[0],is_active,adm_user_id)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                # 編集フォーム
                # with st.form(f"edit_team_{team_id}"):
                #     col1, col2, col3 = st.columns(3)
                    
                #     with col1:
                #         team_name_col = st.text_input("チーム名", value=team_name, key=f"name_{team_id}")
                    
                #     with col2:
                #         team_descriptions_col = st.text_area("説明", value=descriptions, key=f"desc_{team_id}")
                #     with col3:
                #         team_is_active_col = st.checkbox("有効化", value=bool(is_active), key=f"active_{team_id}")
                    
                #     # 更新・削除ボタン
                #     col_update, col_delete = st.columns(2)
                    
                #     with col_update:
                #         if st.form_submit_button("💾 更新", type="primary"):
                #             try:
                #                 update_team(
                #                     id=team_id, team_name=team_name_col, descriptions=team_descriptions_col, is_active=int(team_is_active_col)
                #                 )
                #                 st.success(f"✅ チーム '{team_name_col}' を更新しました")
                #                 st.rerun()
                #             except Exception as e:
                #                 st.error(f"❌ 更新エラー: {e}")
                    
                #     with col_delete:
                #         if st.form_submit_button("🗑️ 削除", type="secondary"):
                #             try:
                #                 delete_team(team_id)
                #                 st.warning(f"⚠️ チーム '{team_name}' を削除しました")
                #                 st.rerun()
                #             except Exception as e:
                #                 st.error(f"❌ 削除エラー: {e}")
    else:
        st.info("登録されているチームがありません。")


def team_prompt_settings():
    st.subheader("🧩 チームごとのプロンプトキー設定")
    adm_user_id = st.session_state["user_id"]
    team_options = get_teams(only_active=1)
    prompt_options = get_prompts(only_active=1)

    view_team_prompt(team_options,prompt_options,adm_user_id)
    create_team_prompt(team_options,prompt_options,adm_user_id)

    

    






        # if not key_options:
        #     st.info("有効なプロンプトキーがありません。まずはプロンプトキーを登録してください。")
        # else:
        #     for team in teams:
        #         # ✅ 修正: 9列に対応
        #         team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team

        #         st.markdown(f"---\n### 🧩 {team_name}")
        #         st.caption(f"最終更新: {updated_at}")
                
        #         with st.form(f"form_update_key_{team_id}"):
        #             st.caption(f"プロンプトキー（現在: `{prompt_key}`）")
        #             current_index = key_options.index(prompt_key) if prompt_key in key_options else 0
        #             new_key = st.selectbox("プロンプトキーを選択", key_options, index=current_index)
                    
        #             if st.form_submit_button("更新する"):
        #                 update_team_prompt(
        #                     team_id, team_name, new_key,
        #                     text_prompt, audio_prompt, score_items, notes, is_active
        #                 )
        #                 st.success(f"{team_name} のプロンプトキーを `{new_key}` に更新しました")
        #                 st.rerun()
