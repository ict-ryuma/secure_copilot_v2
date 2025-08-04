import json
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
from bunseki_functions import promptChecking,setPrompts,evaluationForm, submitEvaluation,saveEvaluation,replyProcess

from backend.save_log import init_db,getUniqueEvaluations,get_all_evaluations,getEvaluationById
from backend.audio_features import extract_audio_features_from_uploaded_file, evaluate_with_gpt
from backend.auth import init_auth_db
from backend.prompt_loader import get_prompts_for_team, get_available_teams_for_user

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
                user_id = result.get("id", "")
                if team_name:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.team_name = team_name
                    st.session_state.user_id = user_id
                    st.session_state.is_admin = result.get("is_admin", False)
                    st.rerun()
                else:
                    st.error("❌ チーム情報が取得できませんでした。")
                    st.stop()

            except requests.exceptions.HTTPError as e:
                # res.responseオブジェクトからステータスコードを取得
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
                error_msg = "❌ 認証エラー: ユーザー名またはパスワードが間違っています。" if status_code == 401 else f"❌ HTTPエラー: {str(e)}"
                st.error(error_msg)
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
            st.session_state["evaluation_saved"] = True
            try:
                team_name = st.session_state.get("team_name", "").strip()
                if team_name:
                    prompts = get_prompts_for_team(team_name)
                    st.session_state.prompts = prompts
                    
                    if prompts.get("error", False):
                        st.error(f"⚠️ {prompts.get('message', 'プロンプト取得エラー')}")
                    else:
                        st.success("✅ 最新のプロンプトを取得しました")
                        st.rerun()
                else:
                    st.error("❌ チーム情報が取得できません")
            except Exception as e:
                st.error(f"❌ プロンプト更新エラー: {e}")
        st.session_state.view_flag = "evaluation_form"
        
        if st.button("🔓 ログアウト"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.team_name = ""
            st.session_state.is_admin = False
            st.session_state.prompts = {}
            st.rerun()
        st.markdown("---")
        evaluations = getUniqueEvaluations(st.session_state.get("user_id", ""))
        st.session_state.evaluations = evaluations
        # label_list = evaluations  # Use full rows as selectbox options
        evaluation_options = [None] + evaluations

        selected_row = st.selectbox(
            "評価を選択",
            options=evaluation_options,
            format_func=lambda row: "評価を選んでください" if row is None else f"{row[3]}",
            index=0
        )
        # Skip first dummy row if needed
        if selected_row is not None:
            selected_id = selected_row[0]
            # st.session_state.get("evaluation_saved")
            st.session_state["evaluation_saved"] = True
            st.session_state["form_submitted"] = None
            # st.success(f"✅ 選択されたアクション: {selected_row[3]} ({selected_row[4]}) - ID: {selected_id}")
            # st.session_state.view_flag = "evaluation"
            if "eachEvaluation" in st.session_state and st.session_state.eachEvaluation:
                del st.session_state["eachEvaluation"]
            
            st.write("▼ 以下の操作を選択してください")
            allEvaluations = get_all_evaluations(st.session_state.get("user_id", ""), selected_row[3])
            for evaluation in allEvaluations:
                evaluation_id = evaluation[0]  # Use the ID from this row
                evaluation_member_id = evaluation[1]  # Member ID
                evaluation_created_at = evaluation[13]  # Created at
                evaluation_shodan_date = evaluation[3]  # Assuming this is the label like 削除, 編集 etc.
                evaluation_outcome = evaluation[4]  # Assuming this is the outcome
                evaluation_label = f"{evaluation_created_at}_{evaluation_outcome}"
                
                # Make button key unique using selected_id and action
                if st.button(f"{evaluation_label}", key=f"{evaluation_label}_{evaluation_id}"):
                    # st.write(f"{evaluation_label} 実行中: ID = {evaluation_id}")
                    eachEvaluation = getEvaluationById(evaluation_id)
                    st.session_state.eachEvaluation = eachEvaluation
                    st.session_state.view_flag = "evaluation"
        else:
            st.session_state["evaluation_saved"] = True
            st.session_state["form_submitted"] = None


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
if st.session_state.view_flag == "evaluation_form":
    promptChecking(team_name)
    custom_prompt, audio_prompt, score_items= setPrompts()
    # evaluationForm()
    submitEvaluation(custom_prompt, audio_prompt, score_items)
    saveEvaluation()
elif st.session_state.view_flag == "evaluation":
    # st.success(f"✅ 選択されたアクション: {selected_label} (ID: {selected_id})")
    # st.success(f"✅ ID: {selected_id}")
    if "eachEvaluation" in st.session_state and st.session_state.eachEvaluation:
        # st.success(f"✅ EV: {st.session_state.get('eachEvaluation',[])}")
        eachEvaluationSession = st.session_state.eachEvaluation[0]

        member_name = eachEvaluationSession[2]  # Member name
        shodan_date = eachEvaluationSession[3]  # Shodan date
        outcome = eachEvaluationSession[4]  # Outcome
        reply = json.loads(eachEvaluationSession[5])  # Assuming this is the reply text
        score_items = json.loads(eachEvaluationSession[6])  # Score items
        audio_prompt = eachEvaluationSession[7]  # Audio prompt
        full_prompt = eachEvaluationSession[8]  # Full prompt text
        audio_file = eachEvaluationSession[9]  # Audio file
        audio_features = json.loads(eachEvaluationSession[10])  # Parsed
        audio_feedback = json.loads(eachEvaluationSession[11])  # Parsed
        parsed = json.loads(eachEvaluationSession[12])  # Parsed
        replyProcess(reply,score_items, member_name, shodan_date, audio_prompt,full_prompt, None, audio_features, audio_feedback)
        st.markdown("---")
        st.subheader("💾 結果登録：成約状況")
        if outcome=="成約":
            st.success(f"🟢 {outcome}")
        elif outcome=="失注":
            st.error(f"🔴 {outcome}")
        elif outcome=="再商談":
            st.warning(f"🟡 {outcome}")

# ✅ プロンプト取得とエラーハンドリング（大幅改善）
def load_team_prompts():
    """チームプロンプトを安全に取得・セッションに保存"""
    
    team_name = st.session_state.get("team_name", "").strip()
    
    if not team_name:
        st.error("❌ チーム情報（team_name）が取得できていません。ログインし直してください。")
        st.session_state.logged_in = False
        return False
    
    print(f"🔍 プロンプト取得開始: team_name='{team_name}'")
    
    try:
        # ✅ エラーハンドリング強化版でプロンプト取得
        prompts = get_prompts_for_team(team_name)
        st.session_state.prompts = prompts
        
        # ✅ エラーがある場合の詳細処理
        if prompts.get("error", False):
            error_type = prompts.get("error_type", "unknown")
            error_message = prompts.get("message", "不明なエラー")
            suggested_action = prompts.get("suggested_action", "管理者にお問い合わせください")
            
            # ✅ エラータイプ別の対応
            if error_type == "team_not_found":
                st.error(f"🚫 {error_message}")
                st.warning("💡 **解決方法:** 管理者にチーム登録を依頼してください")
                
                with st.expander("🔧 詳細情報と対処法"):
                    st.write("**状況:** あなたのチームがシステムに登録されていません")
                    st.write("**原因:** team_masterテーブルにチーム情報がない")
                    st.write("**対処:** 以下の手順で解決してください")
                    st.write("1. 管理者に連絡してチーム作成を依頼")
                    st.write("2. 管理者ダッシュボードでチーム登録")
                    st.write("3. ユーザー設定でチーム変更")
                    st.write("4. 再ログイン")
                
                # ✅ 利用可能チーム表示
                available_teams = get_available_teams_for_user()
                if available_teams:
                    st.info(f"📋 **現在利用可能なチーム:** {', '.join(available_teams)}")
                else:
                    st.warning("⚠️ 現在利用可能なチームがありません")
                
            elif error_type == "team_inactive":
                st.warning(f"⚠️ {error_message}")
                st.info("💡 **解決方法:** 管理者にチームの有効化を依頼するか、別のチームに変更してください")
                
                available_teams = get_available_teams_for_user()
                if available_teams:
                    st.success(f"✅ **有効なチーム:** {', '.join(available_teams)}")
                else:
                    st.error("❌ 現在有効なチームがありません")
                
            elif error_type in ["prompt_not_found", "prompt_incomplete"]:
                st.warning(f"⚠️ {error_message}")
                st.info(f"💡 **解決方法:** {suggested_action}")
                
                if error_type == "prompt_incomplete":
                    missing_fields = prompts.get("missing_fields", {})
                    st.write("**不足している設定:**")
                    for field, is_missing in missing_fields.items():
                        if is_missing:
                            st.write(f"- {field}")
                
            else:
                st.error(f"❌ {error_message}")
                st.info(f"💡 **解決方法:** {suggested_action}")
            
            # ✅ 管理者向けリンク
            if st.session_state.get("is_admin", False):
                st.markdown("---")
                st.info("🛠️ **管理者の方へ:** [管理者ダッシュボード](http://localhost:8501) でチーム・プロンプト設定を確認してください")
            
            # ✅ 緊急時用：デフォルトプロンプトで継続
            if st.button("🚨 デフォルト設定で一時的に継続"):
                st.session_state.prompts = {
                    "error": False,
                    "text_prompt": "以下の会話内容を読み、営業スキルを10点満点で評価してください。",
                    "audio_prompt": "音声の印象を評価してください。",
                    "score_items": ["ヒアリング姿勢", "説明のわかりやすさ", "クロージングの一貫性", "感情の乗せ方と誠実さ", "対話のテンポ"],
                    "notes": "緊急時デフォルト設定"
                }
                st.warning("⚠️ デフォルト設定で継続します。正式な設定は管理者にご相談ください。")
                st.rerun()
            
            return False
            
        else:
            print(f"✅ プロンプト取得成功 for team '{team_name}'")
            return True
            
    except Exception as e:
        st.error(f"❌ システムエラー: {e}")
        st.info("💡 ページを再読み込みするか、管理者にお問い合わせください。")
        
        # ✅ 管理者の場合は詳細エラー表示
        if st.session_state.get("is_admin", False):
            with st.expander("🔧 詳細エラー情報（管理者のみ）"):
                st.code(f"team_name: {team_name}")
                st.code(f"error: {str(e)}")
                st.code(f"DB_PATH: {get_prompts_for_team.__module__}")
        
        return False

# ✅ メインロジック部分の修正
def main_app():
    """メインアプリケーション"""
    
    # ✅ プロンプトが未取得、またはエラーがある場合は取得
    if "prompts" not in st.session_state or not st.session_state.prompts or st.session_state.prompts.get("error", False):
        if not load_team_prompts():
            st.stop()  # プロンプト取得に失敗した場合は停止
    
    # ✅ セッションからプロンプトを取得
    prompts = st.session_state.prompts
    
    if not prompts or prompts.get("error", False):
        st.error("プロンプト設定に問題があります。上記の指示に従って解決してください。")
        st.stop()
    
    # ✅ 各種プロンプトを展開
    custom_prompt = prompts.get("text_prompt", "")
    audio_prompt = prompts.get("audio_prompt", "")
    score_items = prompts.get("score_items", [])
    
    # ✅ デバッグ用：プロンプト内容確認
    print(f"🔍 使用中プロンプト:")
    print(f"  - team_name: {prompts.get('team_name')}")
    print(f"  - prompt_key: {prompts.get('prompt_key')}")
    print(f"  - text_prompt: '{custom_prompt[:100]}...' (長さ: {len(custom_prompt)})")
    print(f"  - audio_prompt: '{audio_prompt[:50]}...' (長さ: {len(audio_prompt)})")
    print(f"  - score_items: {score_items}")
    
    # ✅ プロンプトが空の場合の警告
    if not custom_prompt.strip():
        st.warning("⚠️ テキスト評価プロンプトが設定されていません。管理者にお問い合わせください。")

# ✅ メイン実行部分
if __name__ == "__main__":
    # ログイン処理（既存）
    if not st.session_state.get("logged_in", False):
        # ログイン画面表示
        # ...existing login code...
        pass
    else:
        # ログイン済みの場合、メインアプリを実行
        main_app()
