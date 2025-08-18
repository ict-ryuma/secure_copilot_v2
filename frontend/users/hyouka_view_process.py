import streamlit as st
from backend.audio_features import extract_audio_features_from_uploaded_file, evaluate_with_gpt
from backend.extract_score import extract_scores_and_sections

from logger_config import logger

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