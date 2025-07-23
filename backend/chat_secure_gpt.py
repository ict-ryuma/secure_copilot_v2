import os
import sys
import json
import traceback
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
print("✅ 実行中ファイル:", __file__)
from openai import AzureOpenAI, OpenAI
from backend.auth import verify_user

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
    user_message: str  # ✅ text → user_message に変更

class LoginRequest(BaseModel):
    username: str
    password: str

# === チャットエンドポイント ===
@app.post("/secure-gpt-chat")
async def secure_chat(payload: ChatInput):
    try:
        print("📥 user_message 受信:")
        print(payload.user_message[:1000])  # ✅ payload.text → payload.user_message

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
                    "content": payload.user_message  # ✅ payload.text → payload.user_message
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
from backend.auth import verify_user  # ✅ 差し替えポイント！

@app.post("/login")
async def login(data: LoginRequest):
    is_valid, info = verify_user(data.username, data.password)

    # ✅ ここにデバッグログ追加！
    print("🛰️ /login 受信 username:", data.username)
    print("✅ verify_user info:", info)
    print("🔥 /login → FastAPI 側の info 中身:", info)

    return {
        "success": is_valid,
        "team_name": info.get("team_name", ""),
        "is_admin": info.get("is_admin", False),
        "username": data.username
    }

# === ✅ デバッグ用エンドポイント ===
@app.get("/debug-user")
def debug_user():
    from backend.auth import login_user, hash_password
    password = "star76"
    hashed = hash_password(password)
    result = login_user("ryuma", password)
    return {
        "hashed_input": hashed,
        "login_result": result
    }

# === ✅ デバッグ用プロンプト確認エンドポイント ===
@app.get("/debug-prompts/{team_name}")
def debug_prompts(team_name: str):
    try:
        from backend.prompt_loader import get_prompts_for_team
        prompts = get_prompts_for_team(team_name)
        return {
            "team_name": team_name,
            "prompts_found": prompts,
            "db_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")
        }
    except Exception as e:
        return {"error": str(e)}

# === ✅ デバッグ用テーブル確認エンドポイント ===
@app.get("/debug-db")
def debug_db():
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "score_log.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        result = {"db_path": db_path, "tables": tables}
        
        if "team_master" in tables:
            cursor.execute("SELECT team_name, text_prompt FROM team_master LIMIT 3")
            result["team_master_sample"] = cursor.fetchall()
        
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}
