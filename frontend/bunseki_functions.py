import streamlit as st
from backend.prompt_loader import get_prompts_for_team, get_available_teams_for_user
import requests
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
import yaml
from backend.audio_features import extract_audio_features_from_uploaded_file, evaluate_with_gpt
from backend.extract_score import extract_scores_and_sections
from backend.save_log import save_evaluation
from logger_config import logger

GPT_API_URL = os.getenv("GPT_API_URL", "http://localhost:8000/secure-gpt-chat")
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
def promptChecking(team_name):
    # ✅ プロンプトが未取得なら取得（エラーハンドリング強化版）
    if "prompts" not in st.session_state or not st.session_state.prompts:
        try:
            prompts = get_prompts_for_team(team_name)
            st.session_state.prompts = prompts
            
            # ✅ エラーがある場合の処理
            if prompts.get("error", False):
                error_type = prompts.get("error_type", "unknown")
                error_message = prompts.get("message", "不明なエラー")
                
                # ✅ エラータイプ別の対応
                if error_type == "team_not_found":
                    st.error(f"🚫 {error_message}")
                    st.warning("💡 **解決方法:** 管理者にチーム登録を依頼してください")
                    
                    with st.expander("🔧 一時的な回避方法"):
                        st.write("1. 管理者ダッシュボードで新しいチームを作成")
                        st.write("2. ユーザー一覧でチーム変更")
                        st.write("3. 再ログイン")
                    
                    # ✅ 利用可能チーム表示
                    available_teams = get_available_teams_for_user()
                    if available_teams:
                        st.info(f"📋 **利用可能なチーム:** {', '.join(available_teams)}")
                    
                elif error_type == "team_inactive":
                    st.warning(f"⚠️ {error_message}")
                    st.info("💡 **解決方法:** 管理者にチームの有効化を依頼するか、別のチームに変更してください")
                    
                    available_teams = get_available_teams_for_user()
                    if available_teams:
                        st.success(f"✅ **有効なチーム:** {', '.join(available_teams)}")
                    
                elif error_type == "prompt_not_found":
                    st.warning(f"⚠️ {error_message}")
                    st.info("💡 **解決方法:** 管理者にプロンプト設定の完了を依頼してください")
                    
                else:
                    st.error(f"❌ {error_message}")
                
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
                        "notes": "デフォルト設定"
                    }
                    st.warning("⚠️ デフォルト設定で継続します。正式な設定は管理者にご相談ください。")
                    st.rerun()
                
            else:
                print(f"✅ プロンプト取得成功 for team '{team_name}'")
                
        except Exception as e:
            st.error(f"❌ システムエラー: {e}")
            st.info("💡 ページを再読み込みするか、管理者にお問い合わせください。")
            
            # ✅ 管理者の場合は詳細エラー表示
            if st.session_state.get("is_admin", False):
                with st.expander("🔧 詳細エラー情報（管理者のみ）"):
                    st.code(f"team_name: {team_name}")
                    st.code(f"error: {str(e)}")
            
            st.session_state.logged_in = False
            st.stop()

def setPrompts():
    # ✅ セッションからプロンプトを取得
    prompts = st.session_state.prompts

    if not prompts or prompts.get("error", False):
        st.error("プロンプト設定に問題があります。管理者にお問い合わせください。")
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
            st.text_area("text_prompt", custom_prompt, height=100, disabled=True, key="text_prompt_textarea")
            st.text_area("audio_prompt", audio_prompt, height=50, disabled=True, key="audio_prompt_textarea")
            st.write(f"score_items: {score_items}")
    
    return custom_prompt, audio_prompt, score_items

def evaluationForm():
    st.subheader("👨‍💼 営業評価フォーム")
    with st.form(key="eval_form_1"):
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
        submitted = st.form_submit_button("🎯 評価・改善提案を受け取る")
    return member_name,kintone_id,phone_no, shodan_date, user_input, audio_file, submitted
def replyProcess(reply,score_items, member_name,kintone_id,phone_no, shodan_date, audio_prompt,full_prompt,audio_file,audio_features,audio_feedback):
    if reply:
        parsed = extract_scores_and_sections(reply, score_items)

        st.success(f"✅ 営業評価結果：{member_name or '匿名'}")
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
        elif audio_feedback:
            st.markdown("### 🎧 音声特徴量（参考）")
            st.json(audio_features)

            st.markdown("### 🤖 GPTによる音声評価")
            st.success(audio_feedback)
        
        st.session_state["form_submitted"] = True
        st.session_state["evaluation_saved"] = False

        st.session_state["latest_reply"] = reply
        st.session_state["latest_score_items"] = score_items
        st.session_state["latest_member_name"] = member_name
        st.session_state["latest_kintone_id"] = kintone_id
        st.session_state["latest_phone_no"] = phone_no
        st.session_state["latest_shodan_date"] = shodan_date
        st.session_state["latest_audio_prompt"] = audio_prompt
        st.session_state["latest_full_prompt"] = full_prompt
        st.session_state["latest_audio_file"] = audio_file
        st.session_state["latest_parsed"] = parsed
        st.session_state["latest_audio_features"] = audio_features if audio_features else None
        st.session_state["latest_audio_feedback"] = audio_feedback if audio_feedback else None
    else:
        st.error("❌ GPTからの返信が空です。以下を確認してください：")
        st.write("1. プロンプト設定が正しいか")
        st.write("2. GPTサーバーが正常に動作しているか") 
        st.write("3. 商談テキストに問題がないか")
        
        # ✅ デバッグ情報表示
        if st.session_state.get("is_admin", False):
            st.write("**送信したプロンプト（最初の500文字）:**")
            st.text(full_prompt[:500])
def submitEvaluation(custom_prompt, audio_prompt, score_items):
    member_name,kintone_id,phone_no, shodan_date, user_input, audio_file, submitted = evaluationForm()
    if submitted:
        if not user_input.strip():
            st.warning("⚠️ テキストが空です。入力してください。")
        elif not custom_prompt.strip():  # ✅ プロンプト空チェック追加
            st.error("❌ 評価プロンプトが設定されていません。管理者にプロンプト設定を依頼してください。")
        elif shodan_date is None:
            st.warning("❌ 商談日付が入力されていません。入力してください。")
        elif not (kintone_id.strip() or phone_no.strip()):
            st.warning("❌ Kintone ID または電話番号のいずれかを入力してください。")
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

                    replyProcess(reply,score_items, member_name,kintone_id,phone_no,shodan_date, audio_prompt,full_prompt,audio_file, None,None)
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ リクエストエラー: {e}")
                    with st.expander("🔧 詳細エラー情報"):
                        st.code(f"エラータイプ: {type(e).__name__}")
                        st.code(f"エラー詳細: {str(e)}")
                except Exception as e:
                    st.error(f"❌ 予期しないエラー: {e}")
                    with st.expander("🔧 詳細エラー情報"):
                        st.code(f"エラータイプ: {type(e).__name__}")
                        st.code(f"エラー詳細: {str(e)}")
                        import traceback
                        st.code(f"スタックトレース:\n{traceback.format_exc()}")

def saveEvaluation():
    # ✅ Show 成約/失注/再商談 only if the previous form was submitted and GPT responded
    if "form_submitted" in st.session_state and st.session_state.get("form_submitted")==True:
        user_id = st.session_state.get("user_id", "")
        # try:
        #     alreadyLogged = already_logged(user_id)
        # except Exception as e:
        #     st.error(f"❌ Function error: {e}")
        #     alreadyLogged = False
        # if alreadyLogged:
        #     st.info("✅ この評価はすでに保存済みです。")
        # else:
        if not st.session_state.get("evaluation_saved"):  # Only show once
            # with st.form("evaluation_form"):
            st.markdown("---")
            st.subheader("💾 結果登録：成約状況")
            cols = st.columns(3)

            if cols[0].button("🟢 成約"):
                st.session_state["outcome"] = "成約"
                st.session_state["evaluation_saved"] = True
                st.experimental_rerun()

            if cols[1].button("🔴 失注"):
                st.session_state["outcome"] = "失注"
                st.session_state["evaluation_saved"] = True
                st.experimental_rerun()

            if cols[2].button("🟡 再商談"):
                st.session_state["outcome"] = "再商談"
                st.session_state["evaluation_saved"] = True
                st.experimental_rerun()
        if st.session_state.get("evaluation_saved") and "outcome" in st.session_state:
            # Only save once
            user_id = st.session_state.get("user_id", "")
            logger.info(f"user_id: {user_id}")
            logger.info(f"latest_member_name: {st.session_state['latest_member_name']}")
            logger.info(f"latest_kintone_id: {st.session_state['latest_kintone_id']}")
            logger.info(f"latest_phone_no: {st.session_state['latest_phone_no']}")
            logger.info(f"latest_shodan_date: {st.session_state['latest_shodan_date']}")
            logger.info(f"outcome: {st.session_state['outcome']}")
            logger.info(f"latest_reply: {st.session_state['latest_reply']}")
            logger.info(f"latest_score_items: {st.session_state['latest_score_items']}")
            logger.info(f"latest_audio_prompt: {st.session_state['latest_audio_prompt']}")
            logger.info(f"latest_full_prompt: {st.session_state['latest_full_prompt']}")
            logger.info(f"latest_audio_file: {st.session_state['latest_audio_file']}")
            logger.info(f"latest_audio_features: {st.session_state['latest_audio_features']}")
            logger.info(f"latest_audio_feedback: {st.session_state['latest_audio_feedback']}")
            logger.info(f"latest_parsed: {st.session_state['latest_parsed']}")
            try:
                save_evaluation(
                    user_id,
                    st.session_state["latest_member_name"],
                    st.session_state["latest_kintone_id"],
                    st.session_state["latest_phone_no"],
                    st.session_state["latest_shodan_date"],
                    st.session_state["outcome"],
                    st.session_state["latest_reply"],
                    st.session_state["latest_score_items"],
                    st.session_state["latest_audio_prompt"],
                    st.session_state["latest_full_prompt"],
                    st.session_state["latest_audio_file"],
                    st.session_state["latest_audio_features"],
                    st.session_state["latest_audio_feedback"],
                    st.session_state["latest_parsed"],
                )
                st.success(f"✅ {st.session_state['outcome']}として保存しました！")
                st.session_state["form_submitted"] = False
                logger.info(f"save_evaluation ended successfully for user_id: {user_id}")
            except Exception as e:
                logger.error(f"❌ システムエラー: {e}")

def initialize_selectbox():
    st.session_state.selected_action = "操作を選んでください"