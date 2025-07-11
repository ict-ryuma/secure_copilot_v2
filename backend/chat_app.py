import streamlit as st
import openai
import os
from dotenv import load_dotenv

# .envからAzure OpenAI設定を読み込み
load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# --- UI ---
st.set_page_config(page_title="セールス通話コーチ", layout="wide")
st.title("🎙️ セールス通話フィードバックチャット")

# サイドバーでチームや担当選択
with st.sidebar:
    st.header("🔧 チーム設定")
    team = st.selectbox("チーム", ["Aチーム", "Bチーム", "Cチーム"])
    member = st.text_input("担当者名")
    st.markdown("---")
    st.info("📌 通話テキストを入力し、AIの評価を得ましょう")

# メイン入力
text_input = st.text_area("📞 通話テキストをここに貼ってください", height=250)

# 送信ボタン
if st.button("🚀 分析スタート") and text_input:
    with st.spinner("AIが通話内容を評価中..."):
        prompt = f"""
あなたはプロフェッショナルな営業コーチです。
以下の通話記録をもとに、営業担当者のトークを以下の観点で評価してください：

1. ラポール構築
2. プレゼンテーション
3. クロージング
4. ヒアリング
5. 異議処理

さらに以下も抽出してください：
- 強み
- 改善点
- 重要な洞察
- 推奨ステップ

出力形式は以下のようなJSON構造でお願いします：

{{
  "評価": {{
    "ラポール構築": 数値,
    "プレゼンテーション": 数値,
    "クロージング": 数値,
    "ヒアリング": 数値,
    "異議処理": 数値
  }},
  "強み": ["箇条書き"],
  "改善点": ["箇条書き"],
  "重要な洞察": ["箇条書き"],
  "推奨ステップ": ["箇条書き"]
}}

以下が通話テキストです：
{text_input}
"""

        try:
            response = openai.ChatCompletion.create(
                engine=deployment_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result = response["choices"][0]["message"]["content"]
            st.success("✅ 分析完了！")
            st.code(result, language="json")

        except Exception as e:
            st.error(f"エラー発生: {e}")
