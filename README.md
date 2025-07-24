# 🚀 Secure Copilot v2 - 商談評価AIシステム

## 📌 プロジェクト概要
Secure Copilot v2 は、営業商談をAIで評価・管理する社内向けアプリケーションです。  
Streamlit によるフロントエンド（営業用・管理者用UI）と、FastAPI によるバックエンド（GPT連携API）を統合しています。

---

## 🧱 技術スタック

| 項目         | 使用技術               |
|--------------|------------------------|
| OS           | Amazon Linux 2         |
| Python       | 3.11.x（venv 管理）    |
| フロントエンド | Streamlit              |
| バックエンド | FastAPI + Uvicorn      |
| モデル連携   | Azure OpenAI GPT-4     |
| DB           | SQLite3（ユーザー/チーム管理） |
| サービス管理 | systemd 永続化構成     |

---

## 🧩 ディレクトリ構成

secure_copilot_v2/
├── backend/
│ ├── auth.py # 認証・ユーザー管理ロジック
│ ├── chat_secure_gpt.py # GPT連携FastAPI（main）
│ ├── db_team_master.py # チームDB操作
│ ├── db_prompt_key_master.py # プロンプトキーDB操作
│ └── ...
│
├── frontend/
│ ├── app.py # 営業用ダッシュボード（8501）
│ ├── admin_dashboard.py # 管理者用UI（8503）
│ ├── mgr_dashboard.py # マネージャーダッシュボード（未使用可）
│ └── ...
│
├── .env # APIキーや設定（外部秘）
├── requirements.txt # Python依存パッケージ一覧
├── Dockerfile # オプション：コンテナ化用
└── systemd/
├── copilot-main.service # Streamlit app（8501）
├── copilot-admin.service # 管理ダッシュボード（8503）
└── copilot-api.service # FastAPI（8000）


---

## 📦 仮想環境（venv）

```bash
cd ~/secure_copilot_v2
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

⚙️ systemd サービス一覧（永続化）
| 機能名       | サービス名           | ポート  | 説明                            |
| --------- | --------------- | ---- | ----------------------------- |
| 営業ダッシュボード | `copilot-main`  | 8501 | `frontend/app.py`             |
| 管理者UI     | `copilot-admin` | 8503 | `frontend/admin_dashboard.py` |
| GPTバックエンド | `copilot-api`   | 8000 | `backend/chat_secure_gpt.py`  |

# 全サービスリロード・起動
sudo systemctl daemon-reload
sudo systemctl enable copilot-main copilot-admin copilot-api
sudo systemctl start  copilot-main copilot-admin copilot-api

# 起動状況の確認
sudo systemctl status copilot-main
sudo systemctl status copilot-admin
sudo systemctl status copilot-api

# ポート確認
sudo lsof -i :8000     # GPT API
sudo lsof -i :8501     # 営業用アプリ
sudo lsof -i :8503     # 管理ダッシュボード

🌐 アクセスURL（ブラウザ）
| サービス            | ポート  | URL例（IPは各環境で確認）                             |
| --------------- | ---- | ------------------------------------------- |
| 営業UI（Streamlit） | 8501 | `http://<your-ec2-ip>:8501`                 |
| 管理UI（Streamlit） | 8503 | `http://<your-ec2-ip>:8503`                 |
| FastAPIエンドポイント  | 8000 | `http://<your-ec2-ip>:8000/secure-gpt-chat` |

# Azure OpenAI
OPENAI_API_TYPE=azure
AZURE_OPENAI_KEY=sk-xxxxxxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Backend APIエンドポイント（営業UIから使用）
LOGIN_API_URL=http://<your-ec2-ip>:8000/login
GPT_API_URL=http://<your-ec2-ip>:8000/secure-gpt-chat

# DBファイル
USER_DB_PATH=backend/user_db.db
PROMPT_CONFIG_PATH=prompt_config.yaml

👥 初期ユーザー登録
管理者ダッシュボード（/admin_dashboard.py）から初期ユーザー登録
パスワードはSHA256ハッシュで保存（auth.py）

💡 補足メモ
auth.py に get_current_user() のダミー実装あり（セッション不要化の仮対応）
チーム・プロンプトキー・事業ビジョンも今後 db_xxx.py 経由で拡張可能

📚 補足資料
Azure OpenAI: https://learn.microsoft.com/ja-jp/azure/cognitive-services/openai/
Streamlit: https://docs.streamlit.io/
FastAPI: https://fastapi.tiangolo.com/

