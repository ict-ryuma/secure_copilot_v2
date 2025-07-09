# backend/knowledge_writer.py

import os
import yaml
from datetime import datetime

# 保存先ディレクトリ
KNOWLEDGE_DIR = "team_knowledge"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def save_knowledge_yaml(team: str, title: str, content: str, username: str, entry_type: str = "商材一覧"):
    """
    チーム or 全社のナレッジ（YAML形式）に追記保存する関数

    :param team: チーム名（例: A_team, B_team, company）
    :param title: 登録タイトル
    :param content: 本文（文章 or PDF抽出）
    :param username: 登録者名
    :param entry_type: セクション名（例: "商材一覧", "ビジョン一覧"）
    """
    file_path = os.path.join(KNOWLEDGE_DIR, f"{team}.yaml")

    # 既存読み込み or 初期化
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    if entry_type not in data:
        data[entry_type] = []

    new_entry = {
        "タイトル": title,
        "内容": content,
        "登録者": username,
        "登録日時": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    existing_titles = [item["タイトル"] for item in data[entry_type]]
    if title in existing_titles:
        raise ValueError(f"同じタイトル「{title}」が既に存在します。別の名前にしてください。")

    data[entry_type].append(new_entry)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
