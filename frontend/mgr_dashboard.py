import streamlit as st
import pandas as pd
import os
import datetime

# --- 設定 ---
LOG_DIR = "data/chat_logs"

# ディレクトリが存在しない場合は作成
os.makedirs(LOG_DIR, exist_ok=True)

# --- ユーザー選択 ---
st.sidebar.title("🧑‍💼 ユーザー選択")

try:
    user_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".csv")]
    user_ids = sorted([f.replace(".csv", "") for f in user_files])
except FileNotFoundError:
    user_files = []
    user_ids = []

# --- ログ読み込み ---
def load_chat_log(user_id):
    filepath = os.path.join(LOG_DIR, f"{user_id}.csv")
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            # カラム名を確認・表示（デバッグ用）
            st.sidebar.write(f"CSVカラム: {list(df.columns)}")
            
            # timestampカラムが存在する場合のみ変換
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df.sort_values("timestamp")
            else:
                return df
        except Exception as e:
            st.sidebar.error(f"CSV読み込みエラー: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

# --- HOTワードスコア表示 ---
def compute_hot_score(df):
    if df.empty:
        return 0
    
    hot_words = ["価格", "高い", "不安", "迷い", "即決", "条件"]
    score = 0
    
    # user_messageカラムが存在する場合のみ計算
    if "user_message" in df.columns:
        for word in hot_words:
            score += df["user_message"].str.contains(word, na=False).sum()
    
    return score

# --- メイン画面 ---
st.title("📊 マネージャーダッシュボード")

if user_ids:
    selected_user = st.sidebar.selectbox("ユーザーIDを選択", user_ids)
    
    if selected_user:
        st.subheader(f"🗂 ユーザー: {selected_user}")
        df_logs = load_chat_log(selected_user)
        
        if not df_logs.empty:
            # 利用可能なカラムを表示
            st.write("**利用可能なデータ:**")
            st.dataframe(df_logs)
            
            # 期待されるカラムが存在する場合のみ表示
            expected_columns = ["timestamp", "user_message", "assistant_response"]
            available_columns = [col for col in expected_columns if col in df_logs.columns]
            
            if available_columns:
                st.write("**抽出されたログ:**")
                st.write(df_logs[available_columns])
            
            # --- HOTスコア表示 ---
            hot_score = compute_hot_score(df_logs)
            st.metric(label="🔥 HOTワードスコア", value=hot_score)
        else:
            st.info("このユーザーのチャットログはまだありません")
    else:
        st.info("ユーザーを選択してください")
else:
    st.warning("チャットログファイルが見つかりません")
    st.info("ログファイルは `data/chat_logs/` ディレクトリに配置してください")

# --- 指示投稿UI ---
st.subheader("✍ マネージャー指示投稿")
with st.form("指示フォーム"):
    instruction = st.text_area("ユーザーへの指示やアドバイス", height=100)
    submitted = st.form_submit_button("送信する")
    if submitted and instruction:
        timestamp = datetime.datetime.now().isoformat()
        st.success(f"✅ 指示送信済み: {instruction}")
        # 保存先が必要なら追記（CSVやDB）
