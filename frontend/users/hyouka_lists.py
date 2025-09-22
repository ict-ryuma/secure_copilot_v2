import os
import streamlit as st
import json
from users.hyouka_view_process import replyProcess
from backend.shodans import get_shodan_by_user
from outcomes import outcome_array,display_outcome
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
    page_datas, start_idx, _ = paginate(shodans)
    for i, row in enumerate(page_datas, start=start_idx):
        shodan_label = f"{row['shodan_date']} | {display_outcome(row['outcome'])} | {row['prompt_key']}"
        mi_hyouka_list(shodan_label, row['shodan_id'],row['outcome'])
    evaluation_action(page_datas)


def hyouka_list_view():
    """評価済みの商談一覧表示（ページネーション付き、件数選択可能）"""

    st.header("📋 評価済み商談一覧")
    user_id = st.session_state.get("user_id", "")
    member_name = st.session_state.get("username", "")

    shodans = get_shodan_by_user(user_id=user_id, is_evaluated=None, is_evaluation_saved=1)

    if not (shodans and isinstance(shodans, list) and len(shodans) > 0):
        st.info("このユーザーには評価済みの商談が見つかりませんでした。")
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
                "audio_feedback": json.loads(shodan['audio_feedback']) if shodan['audio_feedback'] else None
            }
            success, audio_features, audio_feedback = replyProcess(**replyArr)