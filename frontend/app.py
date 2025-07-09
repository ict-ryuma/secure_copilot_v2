import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import requests
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
import yaml

from backend.save_log import init_db, save_evaluation, already_logged
from backend.extract_score import extract_scores_and_sections
from backend.audio_features import extract_audio_features_from_uploaded_file, evaluate_with_gpt
from backend.auth import init_auth_db
from backend.prompt_loader import get_prompts_for_team

# --- 初期化 ---
load_dotenv()
init_db()
init_auth_db()

LOGIN_API_URL = os.getenv("LOGIN_API_URL", "http://localhost:8001/login")
GPT_API_URL = os.getenv("GPT_API_URL", "http://localhost:8000/secure-gpt-chat")

st.set_page_config(page_title="📞 商談テキスト評価AI", layout="wide")

# --- セッション初期化 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.team_name = ""
    st.session_state.is_admin = False

# --- ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🔐 セールス評価AI ログイン")
    username = st.text_input("ユーザー名").strip()
    password = st.text_input("パスワード", type="password").strip()

    if st.button("ログイン"):
        try:
            res = requests.post(LOGIN_API_URL, json={"username": username, "password": password}, timeout=10)
            res.raise_for_status()
            result = res.json()
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.team_name = result.get("team_name", "")
            st.session_state.is_admin = result.get("is_admin", False)
            st.success(f"{st.session_state.team_name} チームの {username} さん、ログイン完了！")
            st.rerun()
        except requests.exceptions.HTTPError as e:
            if res.status_code == 401:
                st.error("❌ ユーザー名またはパスワードが正しくありません。")
            else:
                st.error(f"❌ 認証APIエラー: {e}")
        except Exception as e:
            st.error(f"❌ システムエラー: {e}")
    st.stop()

# --- プロンプト取得 ---
prompts = get_prompts_for_team(st.session_state.team_name)
custom_prompt = prompts["text_prompt"]
audio_prompt = prompts["audio_prompt"]
score_items = prompts.get("score_items", [])

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

# --- 評価フォーム ---
st.title("📞 商談テキスト評価AI")
st.info("👤 あなたの営業トークをGPTと音声特徴で評価します")

st.subheader("👨‍💼 営業評価フォーム")
with st.form(key="eval_form"):
    col1, col2 = st.columns(2)
    with col1:
        member_name = st.text_input("営業担当者名", placeholder="例：佐藤")
    with col2:
        deal_id = st.text_input("商談ID", placeholder="例：D123")
    user_input = st.text_area("▼ 商談テキストをここに貼り付けてください", height=300)
    audio_file = st.file_uploader("🎙️ 音声ファイルをアップロード", type=["wav", "mp3", "m4a", "webm"])
    submitted = st.form_submit_button("🎯 評価・改善提案を受け取る")

if submitted:
    if not user_input.strip():
        st.warning("⚠️ テキストが空です。入力してください。")
    else:
        with st.spinner("🧠 GPTによる評価中..."):
            try:
                res = requests.post(GPT_API_URL, json={"user_message": f"{custom_prompt}\n\n{user_input}"}, timeout=60)
                res.raise_for_status()
                reply = res.json().get("reply", "").strip()
                if reply:
                    parsed = extract_scores_and_sections(reply, score_items)

                    st.success(f"✅ 営業評価結果：{member_name or '匿名'}（商談ID: {deal_id or '未指定'}）")
                    st.markdown("### 📝 GPT評価出力")
                    st.markdown(reply.replace("\n", "  \n"))

                    st.markdown("### 📊 評価スコア")
                    for k, v in parsed["scores"].items():
                        st.markdown(f"- {k}: **{v}/10**")

                    st.markdown("### 💪 強み")
                    st.info(parsed["strengths"] or "（なし）")

                    st.markdown("### 🛠️ 改善点")
                    st.warning(parsed["improvements"] or "（なし）")

                    st.markdown("### ⚠️ 注意すべきポイント")
                    st.error(parsed["cautions"] or "（なし）")

                    st.markdown("### 🧭 推奨アクション")
                    st.success(parsed["actions"] or "（なし）")

                    if audio_file:
                        try:
                            wav_path = convert_to_wav(audio_file)
                            st.markdown("### 🎧 音声特徴量（参考）")
                            audio_features = extract_audio_features_from_uploaded_file(wav_path)
                            st.json(audio_features)

                            audio_feedback = evaluate_with_gpt(f"{audio_prompt}\n\n{audio_features}")
                            st.markdown("### 🤖 GPTによる音声評価")
                            st.success(audio_feedback)
                        except Exception as e:
                            st.error(f"❌ 音声処理エラー: {e}")

                    if already_logged(deal_id, member_name):
                        st.info("✅ この評価はすでに保存済みです。")
                    else:
                        st.markdown("---")
                        st.subheader("💾 結果登録：成約状況")
                        cols = st.columns(3)
                        if cols[0].button("🟢 成約"):
                            save_evaluation(deal_id, member_name, "成約", parsed, reply)
                            st.success("✅ 成約として保存しました！")
                        if cols[1].button("🔴 失注"):
                            save_evaluation(deal_id, member_name, "失注", parsed, reply)
                            st.success("✅ 失注として保存しました！")
                        if cols[2].button("🟡 再商談"):
                            save_evaluation(deal_id, member_name, "再商談", parsed, reply)
                            st.success("✅ 再商談として保存しました！")
                else:
                    st.warning("⚠️ GPTからの返信が空です。")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ リクエストエラー: {e}")
            except Exception as e:
                st.error(f"❌ 予期しないエラー: {e}")
