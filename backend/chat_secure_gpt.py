import os
import sys
import json
import traceback
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

# === FastAPI アプリ作成 ===
app = FastAPI()

# === /ping エンドポイント ===
@app.get("/ping")
def ping():
    return {"message": "pong"}

# === 環境変数読み込み ===
load_dotenv()

# === UTF-8出力強制 ===
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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

# === CORS設定 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
                        "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。\n\n"
                        "【評価項目（必ず「項目名: 数値/10」の形式で出力してください）】\n"
                        "- ヒアリング姿勢\n"
                        "- 説明のわかりやすさ\n"
                        "- クロージングの一貫性\n"
                        "- 感情の乗せ方と誠実さ\n"
                        "- 対話のテンポ\n\n"
                        "【出力フォーマット】\n"
                        "ヒアリング姿勢: 7.5/10\n"
                        "説明のわかりやすさ: 8.0/10\n"
                        "クロージングの一貫性: 6.5/10\n"
                        "感情の乗せ方と誠実さ: 7.0/10\n"
                        "対話のテンポ: 8.5/10\n\n"
                        "強み:\n- ...\n\n"
                        "改善点:\n- ...\n\n"
                        "注意すべきポイント:\n- ...\n\n"
                        "次に取るべき推奨アクション:\n"
                        "- ...\n"
                        "- ...\n"
                        "- ...\n\n"
                        "※必ずすべて日本語で、簡潔に、漏れなく出力してください。"
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
