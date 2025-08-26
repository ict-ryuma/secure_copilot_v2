import os
# from time import time
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
import math
import time

BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
GPT_API_URL = f"{BASE_API_URL}/secure-gpt-chat"




# def mi_hyouka_list_view():
#     """List non-evaluated shodans and run/save GPT evaluation safely."""

#     st.header("📋 商談一覧")
#     user_id = st.session_state.get("user_id", "")
#     shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=0)

#     if not (isinstance(shodans, list) and len(shodans) > 0):
#         st.info("No shodans found for this user.")
#         return

#     # Build tabs (use shodan_id for stable keys)
#     tab_labels = [f"{row[6]} | {display_outcome(row[9])} | {row[17]}" for row in shodans]
#     tabs = st.tabs(tab_labels)

#     for idx, tab in enumerate(tabs):
#         with tab:
#             row = shodans[idx]
#             sid = row[0]  # shodan_id

#             st.header(f"商談詳細: {row[6]} | {display_outcome(row[9])} | {row[17]}")
#             st.text_area("text_prompt", row[18], height=100, disabled=True, key=f"text_prompt_{sid}")
#             st.text_area("audio_prompt", row[19], height=50, disabled=True, key=f"audio_prompt_{sid}")
#             st.text_area("score_items", row[20], height=50, disabled=True, key=f"score_items_{sid}")
#             st.text_area("商談内容", row[7], height=50, disabled=True, key=f"shodan_text_{sid}")
#             st.text_input("Audio File", row[8], disabled=True, key=f"audio_file_{sid}")

#             # Session keys per shodan
#             # eval_key = f"eval_data_{sid}"       # holds GPT result dict
#             # save_key = f"save_result_{sid}"     # holds (success, message)
#             # saved_key = f"saved_{sid}"          # holds True after save

#             # --- Evaluate button ---
#             if st.button("🎯 評価・改善提案を受け取る", key=f"btn_eval_{sid}"):
#                 with st.spinner("🧠 GPTによる評価中..."):
#                     try:
#                         full_prompt = f"{row[18]}\n\n{row[7]}"
#                         res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=60)
#                         res.raise_for_status()
#                         reply = res.json().get("reply", "").strip()
#                         member_name = st.session_state.get("username", "")

#                         replyArr = {
#                             "reply": reply,
#                             "member_name": member_name,
#                             "score_items": row[20],
#                             "audio_prompt": row[19],
#                             "full_prompt": full_prompt,
#                             "audio_file": row[8],
#                             "audio_features": None,
#                             "audio_feedback": None
#                         }
#                         success, audio_features, audio_feedback = replyProcess(**replyArr)
#                         if success:
#                             update_shodan_status(sid, is_evaluated=1, is_evaluation_saved=None)
#                             if st.button("💾 保存", key=f"btn_save_{sid}"):
#                                 save_payload = {
#                                     "shodan_id": sid,
#                                     "reply": reply,
#                                     "full_prompt": full_prompt,
#                                     "audio_features": audio_features,
#                                     "audio_feedback": audio_feedback
#                                 }
#                                 ok, msg = save_evaluation(**save_payload)
#                                 if ok:
#                                     update_shodan_status(sid, is_evaluated=None, is_evaluation_saved=1)
#                                 st.success(msg) if ok else st.error(msg)

#                         else:
#                             st.error("Evaluation failed.")
#                     except Exception as e:
#                         st.error(f"❌ Error: {e}")

 # --- Show persistent save message ---
# if "save_message" in st.session_state and st.session_state.save_message:
#     if st.session_state.save_status == "success":
#         st.success(st.session_state.save_message)
#     else:
#         st.error(st.session_state.save_message)
    # Clear after showing once
    # st.session_state.save_message = None
    # st.session_state.save_status = None

            # --- Show GPT result ---
            # eval_data = st.session_state.get(eval_key)
            # if eval_data:
            #     st.text_area("GPT評価結果", eval_data["reply"], height=180, disabled=True, key=f"reply_{sid}")

            #     # Show save button only if not saved yet
            #     if not st.session_state.get(saved_key, False):
            #         if st.button("💾 保存", key=f"btn_save_{sid}"):
            #             save_payload = {
            #                 "shodan_id": eval_data["shodan_id"],
            #                 "reply": eval_data["reply"],
            #                 "full_prompt": eval_data["full_prompt"],
            #                 "audio_features": eval_data["audio_features"],
            #                 "audio_feedback": eval_data["audio_feedback"]
            #             }
            #             ok, msg = save_evaluation(**save_payload)
            #             st.session_state[save_key] = (ok, msg)
            #             if ok:
            #                 update_shodan_status(sid, is_evaluated=None, is_evaluation_saved=1)
            #                 st.session_state[saved_key] = True  # ✅ mark as saved

            # # --- Show save result message ---
            # if st.session_state.get(save_key):
            #     ok, msg = st.session_state[save_key]
            #     st.success(msg) if ok else st.error(msg)
# import streamlit as st
# import requests
# import time

# import streamlit as st
# import requests


def mi_hyouka_list_view():
    st.header("📋 商談一覧")
    user_id = st.session_state.get("user_id", "")
    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=0)

    if not (shodans and isinstance(shodans, list)):
        st.info("このユーザーの商談は見つかりませんでした。")
        return
    for row in shodans:
        shodan_label = f"{row[6]} | {display_outcome(row[9])} | {row[17]}"
        with st.container():
            st.markdown(
                f"""
                <div style="
                    padding: 12px; 
                    margin: 8px 0; 
                    border-radius: 12px; 
                    background-color: #f9f9f9; 
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin:0;">✨ 商談: <span style="color:#2b6cb0;">{shodan_label}</span></h4>
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.button("🎯 評価・改善提案を受け取る", key="all_evaluation_btn"):
        progress = st.progress(0, text="🧠 GPT評価中...")
        try:
            for idx, row in enumerate(shodans, start=1):
                sid = row[0]
                exp_label = f"{row[6]} | {display_outcome(row[9])} | {row[17]}"

                with st.expander(exp_label, expanded=False):
                    # st.text_area("text_prompt", row[18], height=100, disabled=True, key=f"text_prompt_{sid}")
                    # st.text_area("audio_prompt", row[19], height=50, disabled=True, key=f"audio_prompt_{sid}")
                    # st.text_area("score_items", row[20], height=50, disabled=True, key=f"score_items_{sid}")
                    st.text_area("商談テキスト", row[7], height=50, disabled=True, key=f"shodan_text_{sid}")

                    with st.spinner("🧠 GPTに問い合わせ中..."):
                        try:
                            full_prompt = f"{row[18]}\n\n{row[7]}"
                            start_time = time.time()  # ✅ correct usage

                            res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=90)
                            res.raise_for_status()

                            reply = res.json().get("reply", "").strip()
                            full_prompt = f"{row[18]}\n\n{row[7]}"
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
                                update_shodan_status(sid, is_evaluated=1, is_evaluation_saved=None)
                                save_payload = {
                                    "shodan_id": sid,
                                    "reply": reply,
                                    "full_prompt": full_prompt,
                                    "audio_features": audio_features,
                                    "audio_feedback": audio_feedback,
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
                        elapsed = int(time.time() - start_time)  # ✅ correct usage

                        st.success(f"✅ GPTの処理が完了しました（所要時間: {elapsed} 秒）")
                        # st.write(reply)

                # Update progress bar
                progress.progress(int(idx / len(shodans) * 100), text=f"{idx}/{len(shodans)} 完了")

            progress.progress(100, text="🎉 すべての評価が完了しました！")

        except Exception as e:
            st.error(f"❌ Error: {e}")

def hyouka_list_view():
    """評価済みの商談一覧表示（ページネーション付き、件数選択可能）"""

    st.header("📋 評価済み商談一覧")
    user_id = st.session_state.get("user_id", "")
    member_name = st.session_state.get("username", "")

    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=1)

    if not (shodans and isinstance(shodans, list) and len(shodans) > 0):
        st.info("No evaluated shodans found for this user.")
        return

    # --- Items per page select box ---
    items_per_page_options = [3, 5, 10, 20]
    if "items_per_page" not in st.session_state:
        st.session_state.items_per_page = 5

    items_per_page = st.selectbox(
        "Items per page:",
        items_per_page_options,
        index=items_per_page_options.index(st.session_state.items_per_page)
    )

    # Reset to first page if items_per_page changed
    if items_per_page != st.session_state.items_per_page:
        st.session_state.items_per_page = items_per_page
        st.session_state.current_page = 1

    total_items = len(shodans)
    total_pages = math.ceil(total_items / items_per_page)

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # --- Page navigation ---
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        prev_disabled = st.session_state.current_page == 1
        if st.button("⬅ Previous", disabled=prev_disabled):
            st.session_state.current_page -= 1
    with col3:
        next_disabled = st.session_state.current_page == total_pages
        if st.button("Next ➡", disabled=next_disabled):
            st.session_state.current_page += 1

    st.write(f"Page {st.session_state.current_page} / {total_pages}")

    # --- Slice shodans for current page ---
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_shodans = shodans[start_idx:end_idx]

    # --- Display shodans ---
    for i, shodan in enumerate(page_shodans, start=start_idx):
        tab_label = f"{shodan[6]} | {display_outcome(shodan[9])} | {shodan[17]}"
        with st.expander(tab_label):
            st.text_area("text_prompt", shodan[18], height=100, disabled=True, key=f"text_prompt_textarea_{i}")
            st.text_area("audio_prompt", shodan[19], height=50, disabled=True, key=f"audio_prompt_textarea_{i}")
            st.text_area("score_items", shodan[20], height=50, disabled=True, key=f"score_items_textarea_{i}")

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