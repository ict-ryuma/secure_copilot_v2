import os
import streamlit as st
import json
from users.hyouka_view_process import replyProcess
from backend.save_log import getUniqueEvaluations,get_all_evaluations,getEvaluationById
from backend.shodans import get_shodan_by_user,update_shodan_status
from outcomes import outcome_array,display_outcome
import requests
from logger_config import logger
from backend.save_log import save_evaluation
import time
from users.bunseki_functions import mi_hyouka_list,evaluation_action
from frontend.pagination import paginate

BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
GPT_API_URL = f"{BASE_API_URL}/secure-gpt-chat"


def mi_hyouka_list_view():
    st.header("📋 商談一覧")
    user_id = st.session_state.get("user_id", "")
    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=0)

    if not (shodans and isinstance(shodans, list)):
        st.info("このユーザーの商談は見つかりませんでした。")
        return
    # st.write(shodans)
    for row in shodans:
        shodan_label = f"{row['shodan_date']} | {display_outcome(row['outcome'])} | {row['prompt_key']}"
        mi_hyouka_list(shodan_label)
    evaluation_action(shodans)


def hyouka_list_view():
    """評価済みの商談一覧表示（ページネーション付き、件数選択可能）"""

    st.header("📋 評価済み商談一覧")
    user_id = st.session_state.get("user_id", "")
    member_name = st.session_state.get("username", "")

    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=1)

    if not (shodans and isinstance(shodans, list) and len(shodans) > 0):
        st.info("No evaluated shodans found for this user.")
        return

    page_datas, start_idx, _ = paginate(shodans)

    # --- Display shodans ---
    for i, shodan in enumerate(page_datas, start=start_idx):
        tab_label = f"{shodan['shodan_date']} | {display_outcome(shodan['outcome'])} | {shodan['prompt_key']}"
        with st.expander(tab_label):
            st.text_area("text_prompt", shodan['text_prompt'], height=100, disabled=True, key=f"text_prompt_textarea_{i}")
            st.text_area("audio_prompt", shodan['audio_prompt'], height=50, disabled=True, key=f"audio_prompt_textarea_{i}")
            st.text_area("score_items", shodan['score_items'], height=50, disabled=True, key=f"score_items_textarea_{i}")

            replyArr = {
                "reply": json.loads(shodan['reply']),
                "member_name": member_name,
                "score_items": shodan['score_items'],
                "audio_prompt": shodan['audio_prompt'],
                "full_prompt": shodan['full_prompt'],
                "audio_file": None,
                "audio_features": json.loads(shodan['audio_features']),
                "audio_feedback": json.loads(shodan['audio_feedback'])
            }
            success, audio_features, audio_feedback = replyProcess(**replyArr)



# def hyouka_list_view():
#     """評価済みの商談一覧表示"""
#     # BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
#     # GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"
#     st.header("📋 評価済み商談一覧")
#     user_id=st.session_state.get("user_id", "")
#     member_name = st.session_state.get("username", "")
#     shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=1)
#     # st.write(shodans)
#     if shodans and isinstance(shodans, list) and len(shodans) > 0:
#         # Build tab labels dynamically
#         for i, shodan in enumerate(shodans):
#             # st.write(f"Shodan: {shodan}")  # Assuming the first column is the ID
#             tab_label = [f"{shodan[6]} | {display_outcome(shodan[9])} | {shodan[17]}"]
#             # for tab_label in tab_labels:
#             with st.expander(f"{tab_label}"):
#                 # st.write("**現在のプロンプト設定:**")
#                 st.text_area(f"text_prompt", shodan[5], height=100, disabled=True, key="text_prompt_textarea_"+str(i))
#                 st.text_area(f"audio_prompt", shodan[6], height=50, disabled=True, key="audio_prompt_textarea_"+str(i))
#                 st.text_area(f"score_items", shodan[7], height=50, disabled=True, key="score_items_textarea_"+str(i))
#                 replyArr = {
#                     "reply": json.loads(shodan[23]),
#                     "member_name": member_name,
#                     "score_items": shodan[20],
#                     "audio_prompt": shodan[19],
#                     "full_prompt": shodan[24],
#                     "audio_file": None,
#                     "audio_features": json.loads(shodan[25]),
#                     "audio_feedback": json.loads(shodan[26])
#                 }
#                 success, audio_features, audio_feedback = replyProcess(**replyArr)

#     else:
#         st.info("No evaluated shodans found for this user.")

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