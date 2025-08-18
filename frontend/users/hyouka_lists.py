import streamlit as st
import json
from users.hyouka_view_process import replyProcess
from backend.save_log import getUniqueEvaluations,get_all_evaluations,getEvaluationById




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
def hyouka_list_view():
    evaluations = getUniqueEvaluations(st.session_state.get("user_id", ""))
    st.session_state.evaluations = evaluations
    evaluation_options = [None] + evaluations
    selected_row = st.selectbox(
        "評価を選択",
        options=evaluation_options,
        format_func=lambda row: "評価を選んでください" if row is None else f"{row[5]}",
        index=0,
        key="evaluation_select"
    )
    # Skip first dummy row if needed
    if selected_row is not None:
        st.session_state.evaluation_saved = True
        selected_id = selected_row[0]
        if "eachEvaluation" in st.session_state and st.session_state.eachEvaluation:
            del st.session_state["eachEvaluation"]
        
        st.write("▼ 以下の操作を選択してください")
        allEvaluations = get_all_evaluations(st.session_state.get("user_id", ""), selected_row[5])
        for evaluation in allEvaluations:
            evaluation_id = evaluation[0]  # Use the ID from this row
            evaluation_member_id = evaluation[1]  # Member ID
            evaluation_created_at = evaluation[15]  # Created at
            evaluation_shodan_date = evaluation[5]  # Assuming this is the label like 削除, 編集 etc.
            evaluation_outcome = evaluation[6]  # Assuming this is the outcome
            evaluation_label = f"{evaluation_created_at}_{evaluation_outcome}"
            
            # Make button key unique using selected_id and action
            if st.button(f"{evaluation_label}", key=f"{evaluation_label}_{evaluation_id}"):
                eachEvaluation = getEvaluationById(evaluation_id)
                st.session_state.eachEvaluation = eachEvaluation
                st.session_state.view_flag = "evaluation"
                single_hyouka_view(eachEvaluation)