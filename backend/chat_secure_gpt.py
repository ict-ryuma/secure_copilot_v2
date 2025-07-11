import os
import sys
import json
import traceback
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# openai モジュールは 1.x 系を使用
from openai import AzureOpenAI, OpenAI

# === 環境変数読み込み ===
load_dotenv()

# === UTF-8出力強制 ===
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass  # reconfigureが存在しないPythonバージョン用に対処

# === クライアント初期化 ===
API_TYPE = os.getenv("OPENAI_API_TYPE", "openai")

if API_TYPE == "azure":
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL = "gpt-4"

# === FastAPI アプリ作成 ===
app = FastAPI()

# === CORS設定 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === モデル定義 ===
class ChatInput(BaseModel):
    user_message: str

class LoginRequest(BaseModel):
    username: str
    password: str

# === チャットエンドポイント ===
@app.post("/secure-gpt-chat")
async def secure_chat(payload: ChatInput):
    try:
        print("📥 user_message 受信:")
        print(payload.user_message[:1000])

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは営業会話の改善アドバイザーです。\n"
                        "次の5つに分けて日本語でフィードバックを出してください：\n"
                        "1. ラポール構築\n"
                        "2. プレゼンテーション\n"
                        "3. クロージング\n"
                        "4. ヒアリング\n"
                        "5. 異議処理\n"
                        "さらに以下も記載：\n"
                        "- 強み\n"
                        "- 改善点\n"
                        "- 注意すべきポイント\n"
                        "- 次に取るべき推奨アクション（3つ）\n"
                        "すべて日本語で簡潔に書いてください。"
                    )
                },
                {
                    "role": "user",
                    "content": payload.user_message
                }
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        return json.loads(json.dumps({"reply": reply}, ensure_ascii=False))

    except Exception as e:
        print("❌ エラー発生:")
        traceback.print_exc()
        return json.loads(json.dumps({
            "error": f"エラーが発生しました: {str(e)}"
        }, ensure_ascii=False))

# === エイリアス用チャットエンドポイント ===
@app.post("/chat")
async def alias_chat(payload: ChatInput):
    return await secure_chat(payload)

# === 🔐 ログインエンドポイント ===
@app.post("/login")
async def login(data: LoginRequest):
    if data.username == "ryuma" and data.password == "pass":
        return {
            "success": True,
            "team_name": "A_team",
            "is_admin": True
        }
    return {
        "success": False,
        "message": "ユーザー名またはパスワードが間違っています"
    }
