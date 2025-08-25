import streamlit as st
from backend.prompt_loader import get_prompts_for_team, get_available_teams_for_user
from logger_config import logger
import os


def load_team_prompts():
    """チームプロンプトを安全に取得・セッションに保存"""
    team_name = st.session_state.get("team_name", "").strip()
    team_id = st.session_state.get("team_id", "")
    user_id = st.session_state.get("user_id", "")
    if not team_name:
        st.error("❌ チーム情報（team_name）が取得できていません。ログインし直してください。")
        st.session_state.logged_in = False
        return False

    dbPrompts = get_prompts_for_team(team_id=team_id, team_name=team_name, is_active=1)
    return dbPrompts


def setPrompts(prompt_options):
    """プロンプトをセッションに設定"""
    st.title("📞 商談テキスト評価AI")
    st.info("👤 あなたの営業トークをGPTと音声特徴で評価します")
    if not prompt_options or isinstance(prompt_options, tuple) and prompt_options[0] is False:
        st.error("❌ プロンプトの取得に失敗しました。管理者にお問い合わせください。")
        return None
    
    selected_prompts = st.multiselect(
        "プロンプトを選択",
        options=prompt_options,
        default=[],  # nothing selected initially
        format_func=lambda row: f"{row[4]}",  # Display prompt text
        help="登録済みのアクティブプロンプトのみ選択可能です",
        key="prompt_multiselect"
    )
    if selected_prompts:
            for i, selected_prompt in enumerate(selected_prompts):
                with st.expander(f"🔧 デバッグ情報（管理者のみ）- {selected_prompt[4]}"):
            # st.write("**現在のプロンプト設定:**")
                    st.text_area(f"text_prompt", selected_prompt[5], height=100, disabled=True, key="text_prompt_textarea_"+str(i))
                    st.text_area(f"audio_prompt", selected_prompt[6], height=50, disabled=True, key="audio_prompt_textarea_"+str(i))
                    st.text_area(f"score_items", selected_prompt[7], height=50, disabled=True, key="score_items_textarea_"+str(i))
            return selected_prompts
    return None

    # if "prompts" not in st.session_state:
    #     # error_type = prompts.get("error_type", "unknown")
    
        
        
    #     print(f"🔍 プロンプト取得開始: team_name='{team_name}'")
        
    #     try:
    #         # ✅ エラーハンドリング強化版でプロンプト取得
    #         
    #         st.session_state.prompts = prompts
            
    #         # ✅ エラーがある場合の詳細処理
    #         if prompts.get("error", False):
    #             error_type = prompts.get("error_type", "unknown")
    #             error_message = prompts.get("message", "不明なエラー")
    #             suggested_action = prompts.get("suggested_action", "管理者にお問い合わせください")
                
    #             # ✅ エラータイプ別の対応
    #             if error_type == "team_not_found":
    #                 st.error(f"🚫 {error_message}")
    #                 st.warning("💡 **解決方法:** 管理者にチーム登録を依頼してください")
                    
    #                 with st.expander("🔧 詳細情報と対処法"):
    #                     st.write("**状況:** あなたのチームがシステムに登録されていません")
    #                     st.write("**原因:** team_masterテーブルにチーム情報がない")
    #                     st.write("**対処:** 以下の手順で解決してください")
    #                     st.write("1. 管理者に連絡してチーム作成を依頼")
    #                     st.write("2. 管理者ダッシュボードでチーム登録")
    #                     st.write("3. ユーザー設定でチーム変更")
    #                     st.write("4. 再ログイン")
                    
    #                 # ✅ 利用可能チーム表示
    #                 available_teams = get_available_teams_for_user()
    #                 if available_teams:
    #                     st.info(f"📋 **現在利用可能なチーム:** {', '.join(available_teams)}")
    #                 else:
    #                     st.warning("⚠️ 現在利用可能なチームがありません")
                    
    #             elif error_type == "team_inactive":
    #                 st.warning(f"⚠️ {error_message}")
    #                 st.info("💡 **解決方法:** 管理者にチームの有効化を依頼するか、別のチームに変更してください")
                    
    #                 available_teams = get_available_teams_for_user()
    #                 if available_teams:
    #                     st.success(f"✅ **有効なチーム:** {', '.join(available_teams)}")
    #                 else:
    #                     st.error("❌ 現在有効なチームがありません")
                    
    #             elif error_type in ["prompt_not_found", "prompt_incomplete"]:
    #                 st.warning(f"⚠️ {error_message}")
    #                 st.info(f"💡 **解決方法:** {suggested_action}")
                    
    #                 if error_type == "prompt_incomplete":
    #                     missing_fields = prompts.get("missing_fields", {})
    #                     st.write("**不足している設定:**")
    #                     for field, is_missing in missing_fields.items():
    #                         if is_missing:
    #                             st.write(f"- {field}")
                    
    #             else:
    #                 st.error(f"❌ {error_message}")
    #                 st.info(f"💡 **解決方法:** {suggested_action}")
                
    #             # ✅ 管理者向けリンク
    #             if st.session_state.get("is_admin", False):
    #                 st.markdown("---")
    #                 st.info("🛠️ **管理者の方へ:** [管理者ダッシュボード](http://localhost:8503) でチーム・プロンプト設定を確認してください")
                
    #             # ✅ 緊急時用：デフォルトプロンプトで継続
    #             if st.button("🚨 デフォルト設定で一時的に継続"):
    #                 st.session_state.prompts = {
    #                     "error": False,
    #                     "text_prompt": "以下の会話内容を読み、営業スキルを10点満点で評価してください。",
    #                     "audio_prompt": "音声の印象を評価してください。",
    #                     "score_items": ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"],
    #                     "notes": "緊急時デフォルト設定"
    #                 }
    #                 logger.info(f"Prompt: {st.session_state.prompts}")
    #                 st.warning("⚠️ デフォルト設定で継続します。正式な設定は管理者にご相談ください。")
    #                 # st.rerun()
                
    #             return True
                
    #         else:
    #             print(f"✅ プロンプト取得成功 for team '{team_name}'")
    #             return True
                
    #     except Exception as e:
    #         st.error(f"❌ システムエラー: {e}")
    #         st.info("💡 ページを再読み込みするか、管理者にお問い合わせください。")
            
    #         # ✅ 管理者の場合は詳細エラー表示
    #         if st.session_state.get("is_admin", False):
    #             with st.expander("🔧 詳細エラー情報（管理者のみ）"):
    #                 st.code(f"team_name: {team_name}")
    #                 st.code(f"error: {str(e)}")
    #                 st.code(f"DB_PATH: {get_prompts_for_team.__module__}")
            
    #         return False
    # else:
    #     st.write("Prompt set successfully")


# def setPrompts():
    # ✅ セッションからプロンプトを取得
    # prompts = st.session_state.prompts
    # st.success(prompts)

    # if not prompts or prompts.get("error", False):
    #     st.error("プロンプト設定に問題があります。管理者にお問い合わせください。")
    #     st.stop()

    # ✅ 各種プロンプトを展開
    # custom_prompt = prompts.get("text_prompt", "")
    # audio_prompt = prompts.get("audio_prompt", "")
    # score_items = prompts.get("score_items", [])

    # ✅ デバッグ用：プロンプト内容確認
    # print(f"🔍 取得したプロンプト:")
    # print(f"  - text_prompt: '{custom_prompt[:100]}...' (長さ: {len(custom_prompt)})")
    # print(f"  - audio_prompt: '{audio_prompt[:50]}...' (長さ: {len(audio_prompt)})")
    # print(f"  - score_items: {score_items}")

    # ✅ プロンプトが空の場合の警告
    # if not custom_prompt.strip():
    #     st.warning("⚠️ テキスト評価プロンプトが設定されていません。管理者にお問い合わせください。")

    # --- 評価フォーム ---
    # st.title("📞 商談テキスト評価AI")
    # st.info("👤 あなたの営業トークをGPTと音声特徴で評価します")

    # ✅ デバッグ用：現在のプロンプト表示（管理者のみ）
    # if st.session_state.get("is_admin", False):
    #     with st.expander("🔧 デバッグ情報（管理者のみ）"):
    #         st.write("**現在のプロンプト設定:**")
    #         st.text_area("text_prompt", custom_prompt, height=100, disabled=True, key="text_prompt_textarea")
    #         st.text_area("audio_prompt", audio_prompt, height=50, disabled=True, key="audio_prompt_textarea")
    #         st.write(f"score_items: {score_items}")
    
    # return custom_prompt, audio_prompt, score_items