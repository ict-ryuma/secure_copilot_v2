import os
# from secure_copilot_v2.frontend.users.bunseki_functions import BASE_API_URL
import streamlit as st
import json
from users.hyouka_view_process import replyProcess
from backend.save_log import getUniqueEvaluations,get_all_evaluations,getEvaluationById
from backend.shodans import get_shodan_by_user,update_shodan_status
from outcomes import outcome_array,display_outcome
import requests
from logger_config import logger
from backend.save_log import save_evaluation




def single_hyouka_view(eachEvaluation):
    if eachEvaluation:
        eachEvaluationSession = eachEvaluation[0]
        member_name = eachEvaluationSession[2]  # Member name
        kintone_id = eachEvaluationSession[3]  # Kintone ID
        phone_no = eachEvaluationSession[4]  # Phone number
        shodan_date = eachEvaluationSession[5]  # Shodan date
        outcome = eachEvaluationSession[6]  # Outcome
        reply = json.loads(eachEvaluationSession[7])  # Assuming this is the reply text
        score_items = json.loads(eachEvaluationSession[8])  # Score items
        audio_prompt = eachEvaluationSession[9]  # Audio prompt
        full_prompt = eachEvaluationSession[10]  # Full prompt text
        audio_file = eachEvaluationSession[11]  # Audio file
        audio_features = json.loads(eachEvaluationSession[12])
        audio_feedback = json.loads(eachEvaluationSession[13])
        # parsed = json.loads(eachEvaluationSession[14])
        replyProcess(reply,score_items, member_name, kintone_id, phone_no, shodan_date, audio_prompt,full_prompt, audio_file, audio_features, audio_feedback)
        st.markdown("---")
        st.subheader("💾 結果登録：成約状況")
        if outcome=="成約":
            st.success(f"🟢 {outcome}")
        elif outcome=="失注":
            st.error(f"🔴 {outcome}")
        elif outcome=="再商談":
            st.warning(f"🟡 {outcome}")

def mi_hyouka_list_view():
    """List non-evaluated shodans and run/save GPT evaluation safely."""
    BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
    GPT_API_URL = f"{BASE_API_URL}/secure-gpt-chat"

    st.header("📋 商談一覧")
    user_id = st.session_state.get("user_id", "")
    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=0)

    if not (isinstance(shodans, list) and len(shodans) > 0):
        st.info("No shodans found for this user.")
        return

    # Build tabs (use shodan_id for stable keys)
    tab_labels = [f"{row[6]} | {display_outcome(row[9])} | {row[17]}" for row in shodans]
    tabs = st.tabs(tab_labels)

    for idx, tab in enumerate(tabs):
        with tab:
            row = shodans[idx]
            sid = row[0]  # shodan_id

            st.header(f"Shodan Details: {row[6]} | {display_outcome(row[9])} | {row[17]}")
            st.text_area("text_prompt", row[18], height=100, disabled=True, key=f"text_prompt_{sid}")
            st.text_area("audio_prompt", row[19], height=50, disabled=True, key=f"audio_prompt_{sid}")
            st.text_area("score_items", row[20], height=50, disabled=True, key=f"score_items_{sid}")
            st.text_area("Shodan Text", row[7], height=50, disabled=True, key=f"shodan_text_{sid}")
            st.text_input("Audio File", row[8], disabled=True, key=f"audio_file_{sid}")

            # Session keys per shodan
            eval_key = f"eval_data_{sid}"       # holds GPT result dict
            save_key = f"save_result_{sid}"     # holds (success, message)

            # --- Evaluate button (runs once on click) ---
            if st.button("🎯 評価・改善提案を受け取る", key=f"btn_eval_{sid}"):
                with st.spinner("🧠 GPTによる評価中..."):
                    try:
                        full_prompt = f"{row[18]}\n\n{row[7]}"
                        res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=60)
                        res.raise_for_status()
                        reply = res.json().get("reply", "").strip()
                        member_name = st.session_state.get("username", "")

                        replyArr = {
                            "reply": reply,
                            "member_name": member_name,
                            "score_items": row[20],
                            "audio_prompt": row[19],
                            "full_prompt": full_prompt,
                            "audio_file": row[8],
                            "audio_features": None,
                            "audio_feedback": None
                        }
                        success, audio_features, audio_feedback = replyProcess(**replyArr)
                        if success:
                            # Store only for this shodan
                            st.session_state[eval_key] = {
                                "shodan_id": sid,
                                "reply": reply,
                                "full_prompt": full_prompt,
                                "audio_features": audio_features,
                                "audio_feedback": audio_feedback,
                            }
                            # Mark as evaluated (only this sid)
                            update_shodan_status(sid, is_evaluated=1, is_evaluation_saved=None)
                        else:
                            st.error("Evaluation failed.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            # --- Show result & Save button only if this shodan has eval data ---
            eval_data = st.session_state.get(eval_key)
            if eval_data:
                # st.text_area("GPT Feedback", eval_data["reply"], height=180, disabled=True, key=f"reply_{sid}")

                if st.button("💾 保存", key=f"btn_save_{sid}"):
                    save_payload = {
                        "shodan_id": eval_data["shodan_id"],
                        "reply": eval_data["reply"],
                        "full_prompt": eval_data["full_prompt"],
                        "audio_features": eval_data["audio_features"],
                        "audio_feedback": eval_data["audio_feedback"]
                    }
                    ok, msg = save_evaluation(**save_payload)
                    st.session_state[save_key] = (ok, msg)
                    if ok:
                        # Mark as saved (only this sid)
                        update_shodan_status(sid, is_evaluated=None, is_evaluation_saved=1)
                        st.rerun()

            # --- Show save result message (persisted across reruns) ---
            if st.session_state.get(save_key):
                ok, msg = st.session_state[save_key]
                st.success(msg) if ok else st.error(msg)


def hyouka_list_view():
    """評価済みの商談一覧表示"""
    # BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
    # GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"
    st.header("📋 評価済み商談一覧")
    user_id=st.session_state.get("user_id", "")
    member_name = st.session_state.get("username", "")
    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=1)
    # st.write(shodans)
    if shodans and isinstance(shodans, list) and len(shodans) > 0:
        # Build tab labels dynamically
        for i, shodan in enumerate(shodans):
            # st.write(f"Shodan: {shodan}")  # Assuming the first column is the ID
            tab_label = [f"{shodan[6]} | {display_outcome(shodan[9])} | {shodan[17]}"]
            # for tab_label in tab_labels:
            #    st.write(tab_label)
            with st.expander(f"{tab_label}"):
                # st.write("**現在のプロンプト設定:**")
                        st.text_area(f"text_prompt", shodan[5], height=100, disabled=True, key="text_prompt_textarea_"+str(i))
                        st.text_area(f"audio_prompt", shodan[6], height=50, disabled=True, key="audio_prompt_textarea_"+str(i))
                        st.text_area(f"score_items", shodan[7], height=50, disabled=True, key="score_items_textarea_"+str(i))
                        replyArr = {
                            "reply": json.loads(shodan[23]),
                            "member_name": member_name,
                            "score_items": shodan[20],
                            "audio_prompt": shodan[19],
                            "full_prompt": shodan[24],
                            "audio_file": None,
                            "audio_features": json.loads(shodan[25]),
                            "audio_feedback": json.loads(shodan[26])
                        }
                        # st.write(replyArr)
                        success, audio_features, audio_feedback = replyProcess(**replyArr)

    else:
        st.info("No evaluated shodans found for this user.")

    # evaluations = getUniqueEvaluations(st.session_state.get("user_id", ""))
    # st.session_state.evaluations = evaluations
    # evaluation_options = [None] + evaluations
    # selected_row = st.selectbox(
    #     "評価を選択",
    #     options=evaluation_options,
    #     format_func=lambda row: "評価を選んでください" if row is None else f"{row[5]}",
    #     index=0,
    #     key="evaluation_select"
    # )
    # # Skip first dummy row if needed
    # if selected_row is not None:
    #     st.session_state.evaluation_saved = True
    #     selected_id = selected_row[0]
    #     if "eachEvaluation" in st.session_state and st.session_state.eachEvaluation:
    #         del st.session_state["eachEvaluation"]
        
    #     st.write("▼ 以下の操作を選択してください")
    #     allEvaluations = get_all_evaluations(st.session_state.get("user_id", ""), selected_row[5])
    #     for evaluation in allEvaluations:
    #         evaluation_id = evaluation[0]  # Use the ID from this row
    #         evaluation_member_id = evaluation[1]  # Member ID
    #         evaluation_created_at = evaluation[15]  # Created at
    #         evaluation_shodan_date = evaluation[5]  # Assuming this is the label like 削除, 編集 etc.
    #         evaluation_outcome = evaluation[6]  # Assuming this is the outcome
    #         evaluation_label = f"{evaluation_created_at}_{evaluation_outcome}"
            
    #         # Make button key unique using selected_id and action
    #         if st.button(f"{evaluation_label}", key=f"{evaluation_label}_{evaluation_id}"):
    #             eachEvaluation = getEvaluationById(evaluation_id)
    #             st.session_state.eachEvaluation = eachEvaluation
    #             st.session_state.view_flag = "evaluation"
    #             single_hyouka_view(eachEvaluation)