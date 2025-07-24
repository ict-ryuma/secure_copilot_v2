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

    print("🛰️ /login 受信 username:", data.username)
    print("✅ verify_user result:", is_valid, info)

    if not is_valid:
        return {
            "success": False,
            "message": info.get("error", "認証に失敗しました")
        }

    # ✅ 基本応答
    response = {
        "success": True,
        "team_name": info.get("team_name", ""),
        "is_admin": info.get("is_admin", False),
        "username": data.username
    }
    
    # ✅ チーム問題がある場合は詳細情報を追加
    if "team_error" in info:
        response.update({
            "team_error": info["team_error"],
            "team_message": info["team_message"],
            "team_suggestions": info.get("team_suggestions", [])
        })
        print(f"⚠️ ログイン時チーム問題検出: {info['team_error']}")
    
    return response

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

# ✅ チーム別プロンプト取得エンドポイント
@app.get("/team-prompts/{team_name}")
def get_team_prompts_api(team_name: str):
    """指定チームのプロンプト設定を取得（API用）"""
    try:
        from backend.prompt_loader import get_prompts_for_team
        prompts = get_prompts_for_team(team_name)
        
        return {
            "success": not prompts.get("error", False),
            "team_name": team_name,
            "data": prompts
        }
    except Exception as e:
        return {
            "success": False,
            "team_name": team_name,
            "error": str(e)
        }

# ✅ 利用可能チーム一覧エンドポイント
@app.get("/available-teams")
def get_available_teams_api():
    """利用可能なアクティブチーム一覧を取得（統一版）"""
    try:
        from backend.auth import get_all_teams_safe
        teams = get_all_teams_safe()
        
        return {
            "success": True,
            "teams": teams,
            "count": len(teams)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "teams": []
        }

# ✅ 既存のデバッグエンドポイントを拡張
@app.get("/debug-prompts/{team_name}")
def debug_prompts(team_name: str):
    try:
        from backend.prompt_loader import get_prompts_for_team, debug_team_prompts, check_team_exists
        
        # 各種デバッグ情報を取得
        prompts = get_prompts_for_team(team_name)
        team_status = check_team_exists(team_name)
        debug_info = debug_team_prompts(team_name)
        
        return {
            "team_name": team_name,
            "prompts_result": prompts,
            "team_status": team_status,
            "debug_info": debug_info,
            "db_path": "/home/ec2-user/secure_copilot_v2/score_log.db"
        }
    except Exception as e:
        return {
            "team_name": team_name,
            "error": str(e)
        }

# ✅ チャットエンドポイントでチーム別プロンプト使用
class ChatInputWithTeam(BaseModel):
    user_message: str
    team_name: str = ""
    use_team_prompt: bool = True

@app.post("/secure-gpt-chat-v2")
async def secure_chat_with_team(payload: ChatInputWithTeam):
    """チーム別プロンプトを使用したチャット（v2）"""
    try:
        print(f"📥 チーム別チャット受信: team='{payload.team_name}', message='{payload.user_message[:100]}...'")
        
        # ✅ チーム別プロンプト取得
        if payload.use_team_prompt and payload.team_name:
            from backend.prompt_loader import get_prompts_for_team
            prompts = get_prompts_for_team(payload.team_name)
            
            if not prompts.get("error", False):
                system_prompt = prompts.get("text_prompt", "")
                print(f"✅ チーム '{payload.team_name}' のプロンプト使用")
            else:
                # エラーの場合はデフォルトプロンプト
                system_prompt = (
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
                print(f"⚠️ チーム '{payload.team_name}' プロンプト取得失敗、デフォルト使用")
        else:
            # デフォルトプロンプト
            system_prompt = (
                "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。"
                # ...デフォルトプロンプト内容...
            )
            print("📝 デフォルトプロンプト使用")
        
        # ✅ GPT API呼び出し
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.user_message}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        
        return {
            "reply": reply,
            "team_name": payload.team_name,
            "prompt_used": "team_specific" if payload.use_team_prompt and payload.team_name else "default"
        }

    except Exception as e:
        print("❌ チーム別チャットエラー:")
        print(f"   エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "error": f"エラーが発生しました: {str(e)}",
            "team_name": payload.team_name
        }

# ユーザー情報取得部分を修正
def refresh_user_session():
    """ユーザーセッション情報を最新に更新"""
    if st.session_state.get("logged_in") and st.session_state.get("username"):
        try:
            from backend.auth import get_current_user
            user_info = get_current_user(st.session_state.username)
            
            # セッション情報を最新に更新
            st.session_state.team_name = user_info["team_name"]
            st.session_state.is_admin = user_info["is_admin"]
            
            # プロンプトキャッシュをクリア
            if "prompts" in st.session_state:
                del st.session_state.prompts
                
            print(f"🔄 セッション更新: {st.session_state.username} → チーム: {user_info['team_name']}")
            
        except Exception as e:
            print(f"❌ セッション更新エラー: {e}")

# ログイン後とページ読み込み時に実行
if st.session_state.get("logged_in"):
    refresh_user_session()
