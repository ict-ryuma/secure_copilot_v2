import streamlit as st
import pandas as pd
import os
import datetime

# --- 設定 ---
LOG_DIR = "data/chat_logs"

# --- ユーザー選択 ---
st.sidebar.title("🧑‍💼 ユーザー選択")
user_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".csv")]
user_ids = sorted([f.replace(".csv", "") for f in user_files])

selected_user = st.sidebar.selectbox("ユーザーIDを選択", user_ids)

# --- ログ読み込み ---
def load_chat_log(user_id):
    filepath = os.path.join(LOG_DIR, f"{user_id}.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df.sort_values("timestamp")
    else:
        return pd.DataFrame()

df_logs = load_chat_log(selected_user)

# --- HOTワードスコア表示 ---
def compute_hot_score(df):
    hot_words = ["価格", "高い", "不安", "迷い", "即決", "条件"]
    score = 0
    for word in hot_words:
        score += df["user_message"].str.contains(word, na=False).sum()
    return score

# --- ログ表示 ---
st.title("📊 マネージャーダッシュボード")
st.subheader(f"🗂 ユーザー: {selected_user}")
st.write(df_logs[["timestamp", "user_message", "assistant_response"]])

# --- HOTスコア表示 ---
hot_score = compute_hot_score(df_logs)
st.metric(label="🔥 HOTワードスコア", value=hot_score)

# --- 指示投稿UI ---
st.subheader("✍ マネージャー指示投稿")
with st.form("指示フォーム"):
    instruction = st.text_area("ユーザーへの指示やアドバイス", height=100)
    submitted = st.form_submit_button("送信する")
    if submitted and instruction:
        timestamp = datetime.datetime.now().isoformat()
        st.success(f"✅ 指示送信済み: {instruction}")
        # 保存先が必要なら追記（CSVやDB）

