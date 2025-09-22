import streamlit as st
from backend.audio_features import extract_audio_features_from_uploaded_file, evaluate_with_gpt
from backend.extract_score import extract_scores_and_sections

from logger_config import logger

def replyProcess(reply,member_name,score_items, audio_prompt,full_prompt,audio_file,audio_features,audio_feedback):
    if reply:
        parsed = extract_scores_and_sections(reply, score_items)
        logger.info(f"✅ GPT返信解析成功: {parsed}")

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
                # wav_path = convert_to_wav(audio_file)
                # wav_path = audio_file
                st.markdown("### 🎧 音声特徴量（参考）")
                audio_features = extract_audio_features_from_uploaded_file(audio_file)
                st.json(audio_features)

                success, audio_feedback = evaluate_with_gpt(f"{audio_prompt}\n\n{audio_features}")
                st.markdown("### 🤖 GPTによる音声評価")
                if success:
                    st.success(audio_feedback)
                    return success, audio_features, audio_feedback
                else:
                    logger.error(audio_feedback)
                    return False, audio_features, None
            except Exception as e:
                logger.error(f"❌ 音声処理エラー (In reply process): {e}")
                return False, audio_features, None
        elif audio_feedback:
            st.markdown("### 🎧 音声特徴量（参考）")
            st.json(audio_features)

            st.markdown("### 🤖 GPTによる音声評価")
            st.success(audio_feedback)
            return True, audio_features, audio_feedback
    else:
        st.error("❌ GPTからの返信が空です。以下を確認してください：")
        st.write("1. プロンプト設定が正しいか")
        st.write("2. GPTサーバーが正常に動作しているか") 
        st.write("3. 商談テキストに問題がないか")
        
        # ✅ デバッグ情報表示
        if st.session_state.get("is_admin", False):
            st.write("**送信したプロンプト（最初の500文字）:**")
            st.text(full_prompt[:500])
        return False,audio_features,None