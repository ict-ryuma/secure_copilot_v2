import streamlit as st
from backend.db_team_master import (
    create_team_master_table, insert_team_prompt,
    fetch_all_team_prompts, update_team_prompt, delete_team_prompt
)
from backend.mysql_connector import execute_query
from backend.db_prompt_key_master import (
    create_prompt_key_master_table
)
def teamManage():
    st.subheader("🏷️ チーム一覧管理")
    try:
        create_team_master_table()
        teams = fetch_all_team_prompts()
        
        st.markdown("### 📋 現在のチーム一覧")
        if teams:
            for i, t in enumerate(teams):
                # ✅ 修正: 9列に対応
                team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = t
                
                # ✅ 包括的検証結果表示
                from backend.auth import validate_team_comprehensive
                validation = validate_team_comprehensive(team_name)
                
                if validation["valid"]:
                    status = "🟢 正常"
                elif validation["reason"] == "placeholder_team":
                    status = "🚨 プレースホルダー"
                elif validation["reason"] == "team_inactive":
                    status = "⚪ 無効"
                elif validation["reason"] == "prompt_incomplete":
                    status = "⚠️ プロンプト不完全"
                else:
                    status = "❌ 問題あり"
                
                with st.expander(f"{status} `{team_name}` → プロンプトキー: `{prompt_key}` (更新: {updated_at})"):
                    # 検証結果詳細
                    if not validation["valid"]:
                        st.warning(f"**問題:** {validation['message']}")
                        if "suggestions" in validation:
                            st.write("**対処法:**")
                            for suggestion in validation["suggestions"]:
                                st.write(f"- {suggestion}")
                    
                    # 編集フォーム
                    with st.form(f"edit_team_{team_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_name = st.text_input("チーム名", value=team_name, key=f"name_{team_id}")
                            edit_key = st.text_input("プロンプトキー", value=prompt_key, key=f"key_{team_id}")
                            edit_active = st.checkbox("有効化", value=bool(is_active), key=f"active_{team_id}")
                        
                        with col2:
                            edit_notes = st.text_area("備考", value=notes or "", height=100, key=f"notes_{team_id}")
                        
                        # 更新・削除ボタン
                        col_update, col_delete = st.columns(2)
                        
                        with col_update:
                            if st.form_submit_button("💾 更新", type="primary"):
                                try:
                                    update_team_prompt(
                                        team_id, edit_name, edit_key, text_prompt, 
                                        audio_prompt, score_items, edit_notes, int(edit_active)
                                    )
                                    st.success(f"✅ チーム '{edit_name}' を更新しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 更新エラー: {e}")
                        
                        with col_delete:
                            if st.form_submit_button("🗑️ 削除", type="secondary"):
                                try:
                                    delete_team_prompt(team_id)
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
            new_key = st.text_input("プロンプトキー", placeholder="例: prompt_sales_alpha")
            new_text = st.text_area("テキストプロンプト", placeholder="営業評価用のプロンプトを入力", height=100)
            new_audio = st.text_area("音声プロンプト", placeholder="音声評価用のプロンプトを入力", height=80)
            new_score = st.text_input("スコア項目（カンマ区切り）", placeholder="ヒアリング姿勢,説明のわかりやすさ,...")
            new_desc = st.text_area("備考", height=60)
            
            if st.form_submit_button("✅ チームを登録"):
                if new_name.strip() and new_key.strip():
                    # ✅ プレースホルダーチーム名のチェック
                    if new_name.strip() in ['A_team', 'B_team', 'C_team', 'F_team']:
                        st.error("❌ プレースホルダーチーム名（A_team, B_team, C_team, F_team）は使用できません")
                    else:
                        try:
                            insert_team_prompt(
                                name=new_name.strip(),
                                key=new_key.strip(),
                                text_prompt=new_text or "デフォルトテキストプロンプト",
                                audio_prompt=new_audio or "デフォルト音声プロンプト",
                                score_items=new_score or "ヒアリング姿勢,説明のわかりやすさ,クロージングの一貫性,感情の乗せ方と誠実さ,対話のテンポ",
                                notes=new_desc or "（備考なし）"
                            )
                            st.success(f"✅ チーム '{new_name.strip()}' を追加しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ チーム追加エラー: {e}")
                else:
                    st.warning("⚠️ チーム名とプロンプトキーは必須です")
                    
    except Exception as e:
        st.error(f"チーム管理でエラーが発生しました: {e}")



def teamPromptSettings():
    st.subheader("🧠 チームプロンプト管理（DBベース）")
    try:
        teams = fetch_all_team_prompts()
        for team in teams:
            # ✅ 修正: 9列に対応
            team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team
            
            st.markdown("---")
            with st.expander(f"✏️ {team_name} ({prompt_key}) - 更新: {updated_at}"):
                with st.form(f"form_{team_id}"):
                    new_name = st.text_input("チーム名", team_name)
                    new_key = st.text_input("プロンプトキー", prompt_key)
                    new_text = st.text_area("テキストプロンプト", text_prompt, height=120)
                    new_audio = st.text_area("音声プロンプト", audio_prompt, height=80)
                    new_score = st.text_input("スコア項目（カンマ区切り）", score_items)
                    new_note = st.text_area("補足・備考", notes)
                    is_active_flag = st.checkbox("✅ このチームを有効にする", value=is_active == 1)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 更新"):
                            update_team_prompt(team_id, new_name, new_key, new_text, new_audio, new_score, new_note, int(is_active_flag))
                            st.success("更新しました")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ 削除"):
                            delete_team_prompt(team_id)
                            st.warning("削除しました")
                            st.rerun()
    except Exception as e:
        st.error(f"プロンプト設定でエラーが発生しました: {e}")


def teamPromptKeyManage():
    st.subheader("📋 プロンプトキー一覧と操作")
    try:
        create_prompt_key_master_table()
        
        # ✅ 修正: team_masterテーブルから取得（統一）
        # conn = sqlite3.connect(PROMPT_DB_PATH)
        # cursor = conn.cursor()
        keys = execute_query("""
            SELECT id, prompt_key, notes as description, is_active, updated_at 
            FROM team_master 
            ORDER BY team_name
        """, fetch=True)
        # keys = cursor.fetchall()
        # conn.close()

        # 既存のプロンプトキー表示ロジックはそのまま
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
                        # conn = sqlite3.connect(PROMPT_DB_PATH)
                        # cursor = conn.cursor()
                        execute_query("UPDATE prompt_key_master SET is_active = 0 WHERE id = %s", (id_,))
                        # conn.commit()
                        # conn.close()
                        st.success(f"'{prompt_key}' を無効化しました")
                        st.rerun()

        st.markdown("---")
        st.subheader("🆕 プロンプトキー新規追加")
        with st.form("new_prompt_form"):
            new_key = st.text_input("プロンプトキー名")
            new_desc = st.text_area("説明", height=80)
            if st.form_submit_button("✅ 登録"):
                if new_key:
                    # team_masterテーブルに統一して登録
                    insert_team_prompt(
                        name=f"チーム_{new_key}",
                        key=new_key.strip(),
                        text_prompt="デフォルトプロンプト",
                        audio_prompt="デフォルト音声プロンプト", 
                        score_items='["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
                        notes=new_desc.strip()
                    )
                    st.success(f"✅ '{new_key}' を登録しました")
                    st.rerun()
                else:
                    st.warning("プロンプトキー名を入力してください")
    except Exception as e:
        st.error(f"プロンプトキー管理でエラーが発生しました: {e}")


def teamPromptKeySettings():
    st.subheader("🧩 チームごとのプロンプトキー設定")
    try:
        teams = fetch_all_team_prompts()
        
        # ✅ 有効なプロンプトキーを直接SQLで取得
        # conn = sqlite3.connect(PROMPT_DB_PATH)
        # cursor = conn.cursor()
        key_options = execute_query("SELECT prompt_key FROM team_master WHERE is_active = 1", fetch=True)
        if not key_options:
            st.info("有効なプロンプトキーがありません。まずはプロンプトキーを登録してください。")
        else:
            for team in teams:
                # ✅ 修正: 9列に対応
                team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team

                st.markdown(f"---\n### 🧩 {team_name}")
                st.caption(f"最終更新: {updated_at}")
                
                with st.form(f"form_update_key_{team_id}"):
                    st.caption(f"プロンプトキー（現在: `{prompt_key}`）")
                    current_index = key_options.index(prompt_key) if prompt_key in key_options else 0
                    new_key = st.selectbox("プロンプトキーを選択", key_options, index=current_index)
                    
                    if st.form_submit_button("更新する"):
                        update_team_prompt(
                            team_id, team_name, new_key,
                            text_prompt, audio_prompt, score_items, notes, is_active
                        )
                        st.success(f"{team_name} のプロンプトキーを `{new_key}` に更新しました")
                        st.rerun()
    except Exception as e:
        st.error(f"プロンプトキー設定でエラーが発生しました: {e}")