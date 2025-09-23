import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
from outcomes import outcome_array,display_outcome
import requests
import time
from users.hyouka_view_process import replyProcess
from backend.save_log import save_evaluation
from backend.shodans import update_shodan_status,update_shodan_outcome
from logger_config import logger

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
        

# import streamlit as st

def mi_hyouka_list(shodan_label, shodan_id, db_outcome):
    # Create card container
    with st.container():
        col1, col2 = st.columns([4, 1])  # left wide, right narrow

        with col1:
            st.markdown(
                f"""
                <div style="
                    padding: 12px;
                    border-radius: 12px;
                    background-color: #f9f9f9;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                ">
                    ✨ 商談: <span style="color:#2b6cb0;">{shodan_label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            # st.write(db_outcome)
            try:
                db_outcome_int = int(db_outcome)
            except (ValueError, TypeError):
                db_outcome_int = -1  # fallback to default
            # Prepare options
            options = [-1] + list(outcome_array.keys())

            # Determine default index
            if db_outcome_int in options:
                # st.write(options)
                default_index = options.index(db_outcome_int)
            else:
                default_index = 0  # default to -1 ("Please select an outcome")
            # st.write(default_index)
            selected_outcome = st.selectbox(
                "結果を設定",
                options=[-1] + list(outcome_array.keys()),
                index=default_index,
                help="結果を設定してください。",
                format_func=lambda val: "結果を選択してください。" if val == -1 else display_outcome(val),
                key=f"outcome_select_{shodan_id}",  # unique key
                label_visibility="collapsed"  # hides label AND extra space
            )

            # st.write("Selected value:", selected_val)
            if selected_outcome != -1 and selected_outcome != db_outcome_int:
                success,message=update_shodan_outcome(shodan_id, selected_outcome)
                if success:
                    st.success(f"✅ {message}")
                    st.experimental_rerun()
                else:
                    st.error(f"❌ {message}")

def evaluation_action(shodans):
    user_id = st.session_state.get("user_id", "")

    # Initialize state
    if "evaluation_started" not in st.session_state:
        st.session_state["evaluation_started"] = False

    # Show button only if not started yet
    st.write("### ▶ 一度に処理できる評価は最大10件までです。")
    if not st.session_state["evaluation_started"]:
        if st.button("🎯 評価・改善提案を受け取る", key="all_evaluation_btn"):
            st.session_state["evaluation_started"] = True
            st.experimental_rerun()

    # If started, run evaluation
    if st.session_state["evaluation_started"]:
        progress = st.progress(0, text="🧠 GPT評価中...")
        try:
            # ✅ Process only 10 items at a time
            max_items = 10
            total = len(shodans)
            batch = shodans[:max_items]   # take first 10 only
            # st.write(f"batch: {len(batch)}")
            # ====================================
            # Collect all outcomes in an array
            batch_outcomes = [item.get('outcome') for item in batch]

            # Check if any outcome is None or not in outcome_array
            invalid_outcomes = [o for o in batch_outcomes if o is None or int(o) not in outcome_array.keys()]
            # st.write(f"invalid_outcomes: {invalid_outcomes}")

            if invalid_outcomes:
                message = f"⚠️ 最初の {len(batch)} 件の商談のうち {len(invalid_outcomes)} 件で、結果が未設定または無効です。"
                st.warning(message)
                if st.button("🔄 Reload", key="reload_button"):
                    st.session_state["evaluation_started"] = False
                    st.rerun()
                return # Stop further processing
            else:
                message = "✅ すべての商談に有効な結果が設定されています。"
                st.success(message)
    # ===================================
            for idx, row in enumerate(batch, start=1):
                # st.write(f"{row}")
                sid = row['shodan_id']
                exp_label = f"{row['shodan_date']} | {display_outcome(row['outcome'])} | {row['prompt_key']}"

                with st.expander(exp_label, expanded=False):
                    st.text_area("商談テキスト", row['shodan_text'], height=50, disabled=True, key=f"shodan_text_{sid}")

                    with st.spinner("🧠 GPTに問い合わせ中..."):
                        try:
                            full_prompt = f"{row['text_prompt']}\n\n{row['shodan_text']}"
                            start_time = time.time()

                            res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=90)
                            res.raise_for_status()

                            reply = res.json().get("reply", "").strip()
                            member_name = row.get("username", "Unknown User")

                            replyArr = {
                                "reply": reply,
                                "member_name": member_name,
                                "score_items": row['score_items'],
                                "audio_prompt": row['audio_prompt'],
                                "full_prompt": full_prompt,
                                "audio_file": row['audio_file'],
                                "audio_features": None,
                                "audio_feedback": None
                            }
                            success, audio_features, audio_feedback = replyProcess(**replyArr)
                            if success:
                                update_shodan_status(sid, is_evaluated=1, is_evaluation_saved=None)
                                save_payload = {
                                    "shodan_id": sid,
                                    "reply": reply,
                                    "full_prompt": full_prompt,
                                    "audio_features": audio_features,
                                    "audio_feedback": audio_feedback,
                                    "evaluated_by": user_id
                                }
                                ok, msg = save_evaluation(**save_payload)
                                if ok:
                                    update_shodan_status(sid, is_evaluated=None, is_evaluation_saved=1)
                                    st.success(f"{msg}")
                                else:
                                    st.error(f"{msg}")
                            else:
                                st.error("評価に失敗しました。")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        elapsed = int(time.time() - start_time)
                        st.success(f"✅ GPTの処理が完了しました（所要時間: {elapsed} 秒）")

                # progress.progress(int(idx / len(shodans) * 100), text=f"{idx}/{len(shodans)} 完了")
                progress.progress(int(idx / max_items * 100), text=f"{idx}/{min(total, max_items)} 完了")

            
            progress.progress(100, text=f"🎉 最大 {max_items} 件の評価が完了しました！")
            if idx == len(batch):
                if st.button("🔄 Reload", key="reload_button"):
                    st.session_state["evaluation_started"] = False
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")
    # else:
    #     st.info("Reload the page if you want to start evaluation.")
    st.session_state["evaluation_started"] = False
















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







# def initialize_selectbox():
#     st.session_state.selected_action = "操作を選んでください"

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






