import streamlit as st
from backend.teams import get_teams,create_team,update_team,delete_team
def team_manage():
    adm_user_id = st.session_state["user_id"]
    st.subheader("🏷️ チーム一覧管理")
    try:
        teams = get_teams()
        
        st.markdown("### 📋 現在のチーム一覧")
        if teams:
            for i, t in enumerate(teams):
                # ✅ 修正: 9列に対応
                team_id, team_name, descriptions, is_active, created_by, created_at, updated_at = t
                if is_active==1:
                    status = "🟢 正常"
                else:
                    status = "⚠️ 非アクティブ"
                with st.expander(f"{status} `{team_name}` → (更新: {updated_at})"):
                    # 編集フォーム
                    with st.form(f"edit_team_{team_id}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            team_name_col = st.text_input("チーム名", value=team_name, key=f"name_{team_id}")
                        
                        with col2:
                            team_descriptions_col = st.text_area("説明", value=descriptions, key=f"desc_{team_id}")
                        with col3:
                            team_is_active_col = st.checkbox("有効化", value=bool(is_active), key=f"active_{team_id}")
                        
                        # 更新・削除ボタン
                        col_update, col_delete = st.columns(2)
                        
                        with col_update:
                            if st.form_submit_button("💾 更新", type="primary"):
                                try:
                                    update_team(
                                        id=team_id, team_name=team_name_col, descriptions=team_descriptions_col, is_active=int(team_is_active_col)
                                    )
                                    st.success(f"✅ チーム '{team_name_col}' を更新しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 更新エラー: {e}")
                        
                        with col_delete:
                            if st.form_submit_button("🗑️ 削除", type="secondary"):
                                try:
                                    delete_team(team_id)
                                    st.warning(f"⚠️ チーム '{team_name}' を削除しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 削除エラー: {e}")
        else:
            st.info("登録されているチームがありません。")

        # ✅ 新規チーム追加（検証強化）
        st.markdown("---")
        st.subheader("🆕 チーム追加フォーム")
        with st.form("add_team_form"):
            new_name = st.text_input("チーム名", placeholder="例: sales_team_alpha")
            new_descriptions = st.text_area("テキストプロンプト", placeholder="営業評価用のプロンプトを入力", height=100)
            new_is_active = st.checkbox("有効化")
            
            if st.form_submit_button("✅ チームを登録"):
                if not new_name.strip():
                    st.error("❌ Please write a team name")
                    st.stop
                else:
                    success,message=create_team(team_name=new_name,descriptions=new_descriptions,is_active=new_is_active,created_by=adm_user_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)    
    except Exception as e:
        st.error(f"チーム管理でエラーが発生しました: {e}")