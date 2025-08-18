import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment

BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"
# --- 音声変換処理 ---
def convert_to_wav(uploaded_file):
    name, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower().replace('.', '')
    valid_exts = ["wav", "mp3", "m4a", "webm"]
    if ext not in valid_exts:
        st.error(f"❌ このファイル形式（.{ext}）は対応していません。対応形式: {', '.join(valid_exts)}")
        st.stop()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_in:
        tmp_in.write(uploaded_file.read())
        tmp_in.flush()
        audio = AudioSegment.from_file(tmp_in.name, format=ext)
        audio = audio.set_frame_rate(16000).set_channels(1)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
            audio.export(tmp_out.name, format="wav")
            return tmp_out.name
# def promptChecking(team_name):
#     # ✅ プロンプトが未取得なら取得（エラーハンドリング強化版）
#     if "prompts" not in st.session_state or not st.session_state.prompts:
#         try:
#             prompts = get_prompts_for_team(team_name)
#             st.session_state.prompts = prompts
            
#             # ✅ エラーがある場合の処理
#             if prompts.get("error", False):
#                 error_type = prompts.get("error_type", "unknown")
#                 error_message = prompts.get("message", "不明なエラー")
                
#                 # ✅ エラータイプ別の対応
#                 if error_type == "team_not_found":
#                     st.error(f"🚫 {error_message}")
#                     st.warning("💡 **解決方法:** 管理者にチーム登録を依頼してください")
                    
#                     with st.expander("🔧 一時的な回避方法"):
#                         st.write("1. 管理者ダッシュボードで新しいチームを作成")
#                         st.write("2. ユーザー一覧でチーム変更")
#                         st.write("3. 再ログイン")
                    
#                     # ✅ 利用可能チーム表示
#                     available_teams = get_available_teams_for_user()
#                     if available_teams:
#                         st.info(f"📋 **利用可能なチーム:** {', '.join(available_teams)}")
                    
#                 elif error_type == "team_inactive":
#                     st.warning(f"⚠️ {error_message}")
#                     st.info("💡 **解決方法:** 管理者にチームの有効化を依頼するか、別のチームに変更してください")
                    
#                     available_teams = get_available_teams_for_user()
#                     if available_teams:
#                         st.success(f"✅ **有効なチーム:** {', '.join(available_teams)}")
                    
#                 elif error_type == "prompt_not_found":
#                     st.warning(f"⚠️ {error_message}")
#                     st.info("💡 **解決方法:** 管理者にプロンプト設定の完了を依頼してください")
                    
#                 else:
#                     st.error(f"❌ {error_message}")
                
#                 # ✅ 管理者向けリンク
#                 if st.session_state.get("is_admin", False):
#                     st.markdown("---")
#                     st.info("🛠️ **管理者の方へ:** [管理者ダッシュボード](http://localhost:8501) でチーム・プロンプト設定を確認してください")
                
#                 # ✅ 緊急時用：デフォルトプロンプトで継続
#                 if st.button("🚨 デフォルト設定で一時的に継続"):
#                     st.session_state.prompts = {
#                         "error": False,
#                         "text_prompt": "以下の会話内容を読み、営業スキルを10点満点で評価してください。",
#                         "audio_prompt": "音声の印象を評価してください。",
#                         "score_items": ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"],
#                         "notes": "デフォルト設定"
#                     }
#                     st.warning("⚠️ デフォルト設定で継続します。正式な設定は管理者にご相談ください。")
#                     st.rerun()
                
#             else:
#                 print(f"✅ プロンプト取得成功 for team '{team_name}'")
                
#         except Exception as e:
#             st.error(f"❌ システムエラー: {e}")
#             st.info("💡 ページを再読み込みするか、管理者にお問い合わせください。")
            
#             # ✅ 管理者の場合は詳細エラー表示
#             if st.session_state.get("is_admin", False):
#                 with st.expander("🔧 詳細エラー情報（管理者のみ）"):
#                     st.code(f"team_name: {team_name}")
#                     st.code(f"error: {str(e)}")
            
#             st.session_state.logged_in = False
#             st.stop()







def initialize_selectbox():
    st.session_state.selected_action = "操作を選んでください"

# def get_prompt():
#     # st.write("ボタンがクリックされました！")  # デバッグ用
#     st.session_state["form_submitted"] = False
#     st.session_state["evaluation_select"] = None
#     try:
#         team_name = st.session_state.get("team_name", "").strip()
#         if not team_name:
#             st.error("❌ チーム情報（team_name）が取得できていません。ログインし直してください。")
#             st.session_state.logged_in = False
#             return False
#         if team_name:
#             prompts = get_prompts_for_team(team_name)
#             st.session_state.prompts = prompts
            
#             if prompts.get("error", False):
#                 st.error(f"⚠️ {prompts.get('message', 'プロンプト取得エラー')}")
#             else:
#                 st.success("✅ 最新のプロンプトを取得しました")
#                 st.rerun()
#         else:
#             st.error("❌ チーム情報が取得できません")
#     except Exception as e:
#         st.error(f"❌ プロンプト更新エラー: {e}")
#     st.session_state.view_flag = "evaluation_form"






