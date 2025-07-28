# backend/analyze_logs.py（完全版）

import pandas as pd
import json
from collections import Counter
from .mysql_connector import get_connection

DB_PATH = "logs.db"

# データ読み込み関数
def load_logs():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM evaluations", conn)
        return df
    finally:
        conn.close()


# 営業ごとのスコア平均を抽出（評価スコアはJSONで格納されている前提）
def get_average_scores_per_member():
    df = load_logs()
    df = df[df["score_json"].notnull() & df["score_json"].str.len() > 2]
    records = []
    for _, row in df.iterrows():
        try:
            score = json.loads(row["score_json"])
            score["member_name"] = row["member_name"]
            records.append(score)
        except Exception:
            continue
    score_df = pd.DataFrame(records)
    if "member_name" not in score_df.columns or score_df.empty:
        return pd.DataFrame()
    return score_df.groupby("member_name").mean(numeric_only=True).reset_index()

# 成約データのみから強み・改善点のキーワードを抽出
def get_top_keywords_from_column(column_name="full_text", label="成約", top_n=10):
    df = load_logs()
    df = df[df["status"] == label]
    texts = " ".join(df[column_name].dropna().tolist())
    tokens = [word.strip(".\n ・:：、。・-()") for word in texts.split() if len(word) > 1]
    freq = Counter(tokens)
    return freq.most_common(top_n)

# 成約率の計算
def get_success_ratio():
    df = load_logs()
    if "status" not in df.columns:
        return 0
    total = len(df)
    success = len(df[df["status"] == "成約"])
    return round(success / total * 100, 2) if total > 0 else 0.0
