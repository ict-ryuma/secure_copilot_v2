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


def shodan_form_fields(dbPrompts):
    user_id=st.session_state.get("user_id", "")
    # team_id=st.session_state.get("team_id", "")
    # selected_prompts=setPrompts(dbPrompts)
    # st.write(dbPrompts)
    st.subheader("👨‍💼 営業評価フォーム")
    # with st.form(key="eval_form_1"):
    col1, col2 = st.columns(2)
    # with col1:
    col1.text_input(
        "営業担当者名",
        key="tantoshamei",
        value=st.session_state.get("username", ""),
        placeholder="例：佐藤",
        disabled=True
    )
    kintone_id = col2.text_input("Kintone ID", key="kintone_id", value="", help="KintoneのIDを入力してください", placeholder="例：12345")
    phone_no = col1.text_input("エージェント電話番号", key="phone_no", value="", help="エージェントの電話番号を入力してください", placeholder="例：080-1234-5678")
    customer_number = col2.text_input("顧客電話番号", key="customer_number", value="", help="顧客電話番号を入力してください", placeholder="例：080-1234-5678")
    shodan_date = col1.date_input("商談日付", key="shodan_date_input", value=None, help="商談の日付を入力してください（例：2023-01-01）")

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
        elif not (kintone_id.strip() or customer_number.strip()):
            st.warning("❌ Kintone ID または顧客電話番号のいずれかを入力してください。")
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
                "team_has_prompt_id": selected_prompt[0],
                "prompt_key": selected_prompt[4],  # assuming selected_prompt is (id, name)
                "kintone_id": kintone_id,
                "phone_no": phone_no,
                "customer_number": customer_number,
                "shodan_date": str(shodan_date) if shodan_date else None,
                "shodan_text": user_input,
                "audio_file": audio_file_path,  # use saved filename, not st.file_uploader object
                "outcome": outcome,
                "created_by": user_id
            }
            success,message=save_shodan(shodan_array)
            if not success:
                st.error(message)
                # Delete the file if it exists
                if audio_file_path and os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
            else:
                st.success(message)
def shodan_form():
    dbPrompts = load_team_prompts()
    shodan_form_fields(dbPrompts)