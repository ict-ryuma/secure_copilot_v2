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

LOGIN_API_URL = os.getenv("LOGIN_API_URL", "http://localhost:8000/login")
GPT_API_URL = os.getenv("GPT_API_URL", "http://localhost:8000/secure-gpt-chat")

st.set_page_config(page_title="📞 商談テキスト評価AI", layout="wide")

# --- セッション初期化 ---
# --- ログイン画面 ---
# --- サイドバー：ログインUI or ログイン情報 ---
with st.sidebar:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.team_name = ""
        st.session_state.is_admin = False
        st.session_state.prompts = {}

    # デバッグ情報表示
    st.write(f"🔍 Debug: logged_in = {st.session_state.logged_in}")
    
    if not st.session_state.logged_in:
        st.markdown("## 🔐 ログイン")
        username = st.text_input("ユーザー名", key="username_input").strip()
        password = st.text_input("パスワード", type="password", key="password_input").strip()

        if st.button("ログイン"):
            if not username or not password:
                st.warning("⚠️ ユーザー名とパスワードを入力してください。")
                st.stop()

            try:
                res = requests.post(
                    LOGIN_API_URL,
                    json={"username": username, "password": password}
                )
                res.raise_for_status()
                result = res.json()
                team_name = result.get("team_name", "")
                if team_name:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.team_name = team_name
                    st.session_state.is_admin = result.get("is_admin", False)
                    st.rerun()
                else:
                    st.error("❌ チーム情報が取得できませんでした。")
                    st.stop()

            except requests.exceptions.HTTPError as e:
                st.error("❌ 認証エラー: ユーザー名またはパスワードが間違っています。" if res.status_code == 401 else str(e))
                st.stop()
            except Exception as e:
                st.error(f"❌ システムエラー: {e}")
                st.stop()

    else:
        st.markdown("## 👤 ログイン情報")
        st.markdown(f"- ユーザー名: `{st.session_state.username}`")
        st.markdown(f"- チーム: `{st.session_state.team_name}`")
        
        st.markdown("---")
        
        if st.button("🔄 プロンプト再取得"):
            st.write("ボタンがクリックされました！")  # デバッグ用
            try:
                team_name = st.session_state.get("team_name", "").strip()
                if team_name:
                    prompts = get_prompts_for_team(team_name)
                    st.session_state.prompts = prompts
                    st.success("✅ 最新のプロンプトを取得しました")
                    st.rerun()
                else:
                    st.error("❌ チーム情報が取得できません")
            except Exception as e:
                st.error(f"❌ プロンプト更新エラー: {e}")
        
        if st.button("🔓 ログアウト"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.team_name = ""
            st.session_state.is_admin = False
            st.session_state.prompts = {}
            st.rerun()

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
# --- プロンプト取得（ログイン済みチェック） ---
if not st.session_state.logged_in:
    st.stop()

# ✅ デバッグログで team_name 確認
team_name = st.session_state.get("team_name", "").strip()
print(f"✅ セッションから取得した team_name: '{team_name}'")

if not team_name:
    st.error("❌ チーム情報（team_name）が取得できていません。ログインし直してください。")
    st.session_state.logged_in = False
    st.stop()

# ✅ プロンプトが未取得なら取得（このタイミングが最も安全）
if "prompts" not in st.session_state or not st.session_state.prompts:
    try:
        prompts = get_prompts_for_team(team_name)
        st.session_state.prompts = prompts
        print(f"✅ プロンプト取得成功 for team '{team_name}'")
    except ValueError as e:
        st.error(f"❌ プロンプト取得エラー: {e}")
        st.session_state.logged_in = False
        st.stop()

# ✅ セッションからプロンプトを取得
prompts = st.session_state.prompts

if not prompts:
    st.error("ログインしてプロンプトを取得してください。")
    st.stop()

# ✅ 各種プロンプトを展開
custom_prompt = prompts.get("text_prompt", "")
audio_prompt = prompts.get("audio_prompt", "")
score_items = prompts.get("score_items", [])

# ✅ デバッグ用：プロンプト内容確認
print(f"🔍 取得したプロンプト:")
print(f"  - text_prompt: '{custom_prompt[:100]}...' (長さ: {len(custom_prompt)})")
print(f"  - audio_prompt: '{audio_prompt[:50]}...' (長さ: {len(audio_prompt)})")
print(f"  - score_items: {score_items}")

# ✅ プロンプトが空の場合の警告
if not custom_prompt.strip():
    st.warning("⚠️ テキスト評価プロンプトが設定されていません。管理者にお問い合わせください。")

# --- 評価フォーム ---
st.title("📞 商談テキスト評価AI")
st.info("👤 あなたの営業トークをGPTと音声特徴で評価します")

# ✅ デバッグ用：現在のプロンプト表示（管理者のみ）
if st.session_state.get("is_admin", False):
    with st.expander("🔧 デバッグ情報（管理者のみ）"):
        st.write("**現在のプロンプト設定:**")
        st.text_area("text_prompt", custom_prompt, height=100, disabled=True)
        st.text_area("audio_prompt", audio_prompt, height=50, disabled=True)
        st.write(f"score_items: {score_items}")

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
    elif not custom_prompt.strip():  # ✅ プロンプト空チェック追加
        st.error("❌ 評価プロンプトが設定されていません。管理者にプロンプト設定を依頼してください。")
    else:
        with st.spinner("🧠 GPTによる評価中..."):
            try:
                # ✅ 送信内容をデバッグ出力
                full_prompt = f"{custom_prompt}\n\n{user_input}"
                print(f"🔍 GPTに送信する内容（最初の200文字）: '{full_prompt[:200]}...'")
                
                # ✅ "text" → "user_message" に変更
                res = requests.post(GPT_API_URL, json={"user_message": full_prompt}, timeout=60)
                res.raise_for_status()
                reply = res.json().get("reply", "").strip()
                print(f"🔍 GPT出力の原文（最初の200文字）: '{reply[:200]}...'")
                
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
                    st.error("❌ GPTからの返信が空です。以下を確認してください：")
                    st.write("1. プロンプト設定が正しいか")
                    st.write("2. GPTサーバーが正常に動作しているか") 
                    st.write("3. 商談テキストに問題がないか")
                    
                    # ✅ デバッグ情報表示
                    if st.session_state.get("is_admin", False):
                        st.write("**送信したプロンプト（最初の500文字）:**")
                        st.text(full_prompt[:500])
            except requests.exceptions.RequestException as e:
                st.error(f"❌ リクエストエラー: {e}")
            except Exception as e:
                st.error(f"❌ 予期しないエラー: {e}")
