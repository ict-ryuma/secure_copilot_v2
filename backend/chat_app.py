import streamlit as st
import openai
import os
import json
import requests
from dotenv import load_dotenv

# .envからAzure OpenAI設定を読み込み
load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")  # ✅ 最新版に更新
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
    st.header("⚙️ API設定")
    use_unified_api = st.checkbox("🔄 統一APIエンドポイントを使用", value=True)
    api_url = st.text_input("APIエンドポイント", value="http://localhost:8000/secure-gpt-chat")
    
    st.markdown("---")
    st.info("📌 通話テキストを入力し、AIの評価を得ましょう")

# メイン入力
text_input = st.text_area("📞 通話テキストをここに貼ってください", height=250)

# ✅ 早期ガード：入力チェック
if st.button("🚀 分析スタート"):
    if not text_input.strip():
        st.warning("⚠️ 通話テキストを入力してください")
        st.stop()

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

※出力は必ず有効なJSON形式で、キー名の揺れやコメント等は含めず、パース可能な形で返答してください。
"""

        try:
            if use_unified_api:
                # ✅ 統一APIエンドポイントを使用
                response = requests.post(
                    api_url, 
                    json={"user_message": prompt},  # ✅ user_message キーで統一
                    timeout=30
                )
                response.raise_for_status()
                result = response.json().get("reply", "エラー")
                
                # ✅ JSON解析の安定化
                try:
                    parsed_result = json.loads(result)
                    st.success("✅ 分析完了！（統一API経由）")
                    
                    # ✅ 構造化表示
                    st.subheader("📊 評価結果")
                    if "評価" in parsed_result:
                        for key, value in parsed_result["評価"].items():
                            st.metric(key, f"{value}/10")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if "強み" in parsed_result:
                            st.subheader("💪 強み")
                            for item in parsed_result["強み"]:
                                st.write(f"- {item}")
                        
                        if "重要な洞察" in parsed_result:
                            st.subheader("💡 重要な洞察")
                            for item in parsed_result["重要な洞察"]:
                                st.write(f"- {item}")
                    
                    with col2:
                        if "改善点" in parsed_result:
                            st.subheader("🛠️ 改善点")
                            for item in parsed_result["改善点"]:
                                st.write(f"- {item}")
                        
                        if "推奨ステップ" in parsed_result:
                            st.subheader("🎯 推奨ステップ")
                            for item in parsed_result["推奨ステップ"]:
                                st.write(f"- {item}")
                    
                    # ✅ 生JSONも表示
                    with st.expander("🔍 生JSONデータ"):
                        st.code(json.dumps(parsed_result, ensure_ascii=False, indent=2), language="json")
                        
                except json.JSONDecodeError:
                    st.warning("⚠️ JSONパースに失敗しました。生テキストを表示します。")
                    st.code(result, language="text")
                    
            else:
                # ✅ 従来のOpenAI直接呼び出し
                response = openai.ChatCompletion.create(
                    engine=deployment_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                result = response["choices"][0]["message"]["content"]
                
                # ✅ JSON解析の安定化
                try:
                    parsed_result = json.loads(result)
                    st.success("✅ 分析完了！（直接OpenAI）")
                    st.code(json.dumps(parsed_result, ensure_ascii=False, indent=2), language="json")
                except json.JSONDecodeError:
                    st.warning("⚠️ JSONパースに失敗しました。生テキストを表示します。")
                    st.code(result, language="text")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ API接続エラー: {e}")
            st.info("💡 統一APIが動作していない場合は、サイドバーでチェックを外して直接OpenAIを使用してください。")
        except Exception as e:
            st.error(f"❌ エラー発生: {e}")
            
        # ✅ チーム・担当者情報の保存（オプション）
        if team and member:
            st.info(f"📝 チーム: {team} | 担当者: {member}")
