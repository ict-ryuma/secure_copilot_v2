import streamlit as st
from logger_config import logger
import requests
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
import yaml
from backend.save_log import save_evaluation
from users.load_prompts import load_team_prompts,setPrompts
from backend.shodans import save_shodan
from users.audio_functions import save_audio_file
from datetime import datetime
from outcomes import outcome_array,display_outcome






BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"


def evaluationForm(dbPrompts):
    user_id=st.session_state.get("user_id", "")
    team_id=st.session_state.get("team_id", "")
    # selected_prompts=setPrompts(dbPrompts)
    # st.write(dbPrompts)
    st.subheader("👨‍💼 営業評価フォーム")
    # with st.form(key="eval_form_1"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        member_name = st.text_input(
            "営業担当者名",
            key="tantoshamei",
            value=st.session_state.get("username", ""),
            placeholder="例：佐藤",
            disabled=True
        )
    with col2:
        kintone_id = st.text_input("Kintone ID", key="kintone_id", value="", help="KintoneのIDを入力してください", placeholder="例：12345")
    with col3:
        phone_no = st.text_input("電話番号", key="phone_no", value="", help="電話番号を入力してください", placeholder="例：080-1234-5678")
    with col4:
        shodan_date = st.date_input("商談日付", key="shodan_date_input", value=None, help="商談の日付を入力してください（例：2023-01-01）")
    user_input = st.text_area("▼ 商談テキストをここに貼り付けてください", height=300, key="user_input_textarea")
    audio_file = st.file_uploader("🎙️ 音声ファイルをアップロード", type=["wav", "mp3", "m4a", "webm"])

    # アウトカム選択（必須）
    # Radio selection
    outcome = st.radio(
        "商談の結果を選択してください",
        options=list(outcome_array.keys()),  # values = 0,1,2
        format_func=display_outcome,        # what the user sees
        help="商談の結果を選択してください",
        index=None,                         # no default selection
        horizontal=True
    )

    if st.button("💾保存", key="save_button"):
        audio_file_path =None
        # if selected_prompts is None:
        #     st.error("❌ プロンプトが選択されていません。プロンプトを選択してください。")
        #     st.stop()
        if not user_input.strip():
            st.warning("⚠️ テキストが空です。入力してください。")
            st.stop()
        elif dbPrompts is None:  # ✅ プロンプト空チェック追加
            st.error("❌ 評価プロンプトが設定されていません。管理者にプロンプト設定を依頼してください。")
            st.stop()
        elif shodan_date is None:
            st.warning("❌ 商談日付が入力されていません。入力してください。")
            st.stop()
        elif not (kintone_id.strip() or phone_no.strip()):
            st.warning("❌ Kintone ID または電話番号のいずれかを入力してください。")
            st.stop()
        elif outcome is None:
            st.error("❌ 商談の結果を選択してください。")
            st.stop()
        elif audio_file is not None:
            audio_file_path = save_audio_file(audio_file, upload_dir = "uploads")
            if audio_file_path is None:
                st.error("❌ 音声ファイルの保存に失敗しました。")
        for i, selected_prompt in enumerate(dbPrompts):
            shodan_array = {
                "user_id": user_id,
                "team_id": team_id,
                "prompt_id": selected_prompt[1],  # assuming selected_prompt is (id, name)
                "prompt_key": selected_prompt[4],  # assuming selected_prompt is (id, name)
                "kintone_id": kintone_id,
                "phone_no": phone_no,
                "shodan_date": str(shodan_date) if shodan_date else None,
                "shodan_text": user_input,
                "audio_file": audio_file_path,  # use saved filename, not st.file_uploader object
                "outcome": outcome,
                "created_by": user_id
            }
            success,message=save_shodan(shodan_array)
            if not success:
                st.error(message)
            else:
                st.success(message)




# def submitEvaluation(custom_prompt, audio_prompt, score_items):
#     st.success(custom_prompt)
#     st.success(audio_prompt)
#     st.success(score_items)
#     member_name,kintone_id,phone_no, shodan_date, user_input, audio_file, submitted = evaluationForm()
#     if submitted:
#         if not user_input.strip():
#             st.warning("⚠️ テキストが空です。入力してください。")
#             st.stop()
#         elif not custom_prompt.strip():  # ✅ プロンプト空チェック追加
#             st.error("❌ 評価プロンプトが設定されていません。管理者にプロンプト設定を依頼してください。")
#             st.stop()
#         elif shodan_date is None:
#             st.warning("❌ 商談日付が入力されていません。入力してください。")
#             st.stop()
#         elif not (kintone_id.strip() or phone_no.strip()):
#             st.warning("❌ Kintone ID または電話番号のいずれかを入力してください。")
#             st.stop()
#         else:
#             with st.spinner("🧠 GPTによる評価中..."):
#                 try:
#                     # ✅ 送信内容をデバッグ出力
#                     full_prompt = f"{custom_prompt}\n\n{user_input}"
#                     print(f"🔍 GPTに送信する内容（最初の200文字）: '{full_prompt[:200]}...'")
                    
#                     # ✅ "text" → "user_message" に変更
#                     res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=60)
#                     res.raise_for_status()
#                     reply = res.json().get("reply", "").strip()
#                     print(f"🔍 GPT出力の原文（最初の200文字）: '{reply[:200]}...'")

#                     replyProcess(reply,score_items, member_name,kintone_id,phone_no,shodan_date, audio_prompt,full_prompt,audio_file, None,None)
#                 except requests.exceptions.RequestException as e:
#                     st.error(f"❌ リクエストエラー: {e}")
#                     with st.expander("🔧 詳細エラー情報"):
#                         st.code(f"エラータイプ: {type(e).__name__}")
#                         st.code(f"エラー詳細: {str(e)}")
#                 except Exception as e:
#                     st.error(f"❌ 予期しないエラー: {e}")
#                     with st.expander("🔧 詳細エラー情報"):
#                         st.code(f"エラータイプ: {type(e).__name__}")
#                         st.code(f"エラー詳細: {str(e)}")
#                         import traceback
#                         st.code(f"スタックトレース:\n{traceback.format_exc()}")

# def saveEvaluation():
#     # ✅ Show 成約/失注/再商談 only if the previous form was submitted and GPT responded
#     if "form_submitted" in st.session_state and st.session_state.get("form_submitted")==True:
#         user_id = st.session_state.get("user_id", "")
#         # try:
#         #     alreadyLogged = already_logged(user_id)
#         # except Exception as e:
#         #     st.error(f"❌ Function error: {e}")
#         #     alreadyLogged = False
#         # if alreadyLogged:
#         #     st.info("✅ この評価はすでに保存済みです。")
#         # else:
#         if not st.session_state.get("evaluation_saved"):  # Only show once
#             # with st.form("evaluation_form"):
#             st.markdown("---")
#             st.subheader("💾 結果登録：成約状況")
#             cols = st.columns(3)

#             if cols[0].button("🟢 成約"):
#                 st.session_state["outcome"] = "成約"
#                 st.session_state["evaluation_saved"] = True
#                 st.experimental_rerun()

#             if cols[1].button("🔴 失注"):
#                 st.session_state["outcome"] = "失注"
#                 st.session_state["evaluation_saved"] = True
#                 st.experimental_rerun()

#             if cols[2].button("🟡 再商談"):
#                 st.session_state["outcome"] = "再商談"
#                 st.session_state["evaluation_saved"] = True
#                 st.experimental_rerun()
#         if st.session_state.get("evaluation_saved") and "outcome" in st.session_state:
#             # Only save once
#             user_id = st.session_state.get("user_id", "")
#             logger.info(f"user_id: {user_id}")
#             logger.info(f"latest_member_name: {st.session_state['latest_member_name']}")
#             logger.info(f"latest_kintone_id: {st.session_state['latest_kintone_id']}")
#             logger.info(f"latest_phone_no: {st.session_state['latest_phone_no']}")
#             logger.info(f"latest_shodan_date: {st.session_state['latest_shodan_date']}")
#             logger.info(f"outcome: {st.session_state['outcome']}")
#             logger.info(f"latest_reply: {st.session_state['latest_reply']}")
#             logger.info(f"latest_score_items: {st.session_state['latest_score_items']}")
#             logger.info(f"latest_audio_prompt: {st.session_state['latest_audio_prompt']}")
#             logger.info(f"latest_full_prompt: {st.session_state['latest_full_prompt']}")
#             logger.info(f"latest_audio_file: {st.session_state['latest_audio_file']}")
#             logger.info(f"latest_audio_features: {st.session_state['latest_audio_features']}")
#             logger.info(f"latest_audio_feedback: {st.session_state['latest_audio_feedback']}")
#             logger.info(f"latest_parsed: {st.session_state['latest_parsed']}")
#             try:
#                 save_evaluation(
#                     user_id,
#                     st.session_state["latest_member_name"],
#                     st.session_state["latest_kintone_id"],
#                     st.session_state["latest_phone_no"],
#                     st.session_state["latest_shodan_date"],
#                     st.session_state["outcome"],
#                     st.session_state["latest_reply"],
#                     st.session_state["latest_score_items"],
#                     st.session_state["latest_audio_prompt"],
#                     st.session_state["latest_full_prompt"],
#                     st.session_state["latest_audio_file"],
#                     st.session_state["latest_audio_features"],
#                     st.session_state["latest_audio_feedback"],
#                     # st.session_state["latest_parsed"],
#                 )
#                 st.success(f"✅ {st.session_state['outcome']}として保存しました！")
#                 st.session_state["form_submitted"] = False
#                 logger.info(f"save_evaluation ended successfully for user_id: {user_id}")
#             except Exception as e:
#                 logger.error(f"❌ システムエラー: {e}")



def hyouka_form():
    dbPrompts = load_team_prompts()
    evaluationForm(dbPrompts)
    # prompts=st.session_state.prompts
    # custom_prompt=prompts.get("text_prompt","")
    # audio_prompt=prompts.get("audio_prompt","")
    # score_items=prompts.get("score_items","")
    # st.success(prompts)
    # st.success(custom_prompt)
    # custom_prompt,audio_prompt,score_items=setPrompts()
    # submitEvaluation(custom_prompt, audio_prompt, score_items)
    # saveEvaluation()