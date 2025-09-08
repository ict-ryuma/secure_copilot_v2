import streamlit as st
from backend.prompts import get_prompts,create_prompt,update_prompt,delete_prompt
from pagination import paginate

def prompt_manage():
    adm_user_id = st.session_state["user_id"]
    st.subheader("🏷️ プロンプト一覧管理")

    try:
        prompts=get_prompts(only_active=None)
        st.markdown("### 📋 現在のプロンプト一覧")
        if prompts:
            page_datas, start_idx, _ = paginate(prompts)
            for i, prompt in enumerate(page_datas):
                # st.write(prompt)
                prompt_id, prompt_key, text_prompt,audio_prompt,score_items,notes, is_active, created_by, created_at, updated_at = prompt
                if is_active==1:
                    status = "🟢 正常"
                else:
                    status = "⚠️ 非アクティブ"
                with st.expander(f"{status} `{prompt_key}` → (更新: {updated_at})"):
                    # 編集フォーム
                    with st.form(f"edit_prompt_{prompt_id}"):
                        col1= st.columns(1)[0]
                        
                        with col1:
                            prompt_key_col = st.text_input("プロンプトキー", value=prompt_key, key=f"prompt_key_{prompt_id}")
                            text_prompt_col = st.text_area("説テキストプロンプト明", value=text_prompt, key=f"text_prompt_{prompt_id}")
                            audio_prompt_col = st.text_area("音声プロンプト", value=audio_prompt, key=f"audio_prompt_{prompt_id}")
                            score_items_col = st.text_area("スコア項目（カンマ区切り）", value=score_items, key=f"score_items_{prompt_id}")
                            note_col = st.text_area("補足・備考", value=notes, key=f"notes_{prompt_id}")
                            is_active_flag = st.checkbox("✅ このプロンプトキーを有効にする", value=is_active)
                        
                        # 更新・削除ボタン
                        col_update, col_delete = st.columns(2)
                        
                        with col_update:
                            if st.form_submit_button("💾 更新", type="primary"):
                                try:
                                    update_prompt(
                                        id=prompt_id, prompt_key=prompt_key_col, text_prompt=text_prompt_col,audio_prompt=audio_prompt_col,score_items=score_items_col,notes=note_col, is_active=int(is_active_flag)
                                    )
                                    st.success(f"✅ プロンプト '{prompt_key_col}' を更新しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 更新エラー: {e}")
                        
                        with col_delete:
                            if st.form_submit_button("🗑️ 削除", type="secondary"):
                                try:
                                    delete_prompt(prompt_id)
                                    st.warning(f"⚠️ プロンプト '{prompt_key_col}' を削除しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 削除エラー: {e}")
        else:
            st.info("登録されているプロンプトがありません。")

        # ✅ 新規プロンプト追加（検証強化）
        st.markdown("---")
        st.subheader("🆕 プロンプト追加フォーム")
        with st.form("add_prompt_form"):
            new_prompt_key = st.text_input("プロンプトキー", placeholder="例: prompt_a_team")
            new_text_prompt = st.text_area("テキストプロンプト", placeholder="テキストプロンプト", height=120)
            new_audio_prompt = st.text_area("音声プロンプト", placeholder="音声プロンプト", height=80)
            new_score_items = st.text_area("スコア項目（カンマ区切り）", placeholder="スコア項目（カンマ区切り）")
            new_notes = st.text_area("補足・備考", placeholder="補足・備考")
            new_is_active = st.checkbox("有効化")
            
            if st.form_submit_button("✅ プロンプトを登録"):
                if not new_prompt_key.strip():
                    st.error("❌ Please write a プロンプトキー")
                    st.stop
                else:
                    try:
                        success,message=create_prompt(
                            prompt_key=new_prompt_key, 
                            text_prompt=new_text_prompt or "デフォルトテキストプロンプト",
                            audio_prompt=new_audio_prompt or "デフォルト音声プロンプト",
                            score_items=new_score_items or "ヒアリング姿勢,説明のわかりやすさ,クロージングの一貫性,感情の乗せ方と誠実さ,対話のテンポ",
                            notes=new_notes or "（備考なし）",
                            is_active=new_is_active,
                            created_by=adm_user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"プロンプト登録でエラーが発生しました: {e}")
    except Exception as e:
        st.error(f"プロンプト設定でエラーが発生しました: {e}")