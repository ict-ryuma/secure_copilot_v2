import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from admins.sidebar import sidebar
from admins.users import register, userLists
from admins.teams_and_prompt import teamManage,teamPromptSettings,teamPromptKeyManage,teamPromptKeySettings
from admins.company_visions import companyVisionLearn
from admins.shodan_bunseki import shodanBunseki
from admins.team_performance_dashboard import tpdb
from admins.followup_management import followupManagement
from admins.login_check import login

load_dotenv()
login()
# sidebar 
menu = sidebar()
# --- メニュー分岐 ---
if menu == "ユーザー登録":
    register()
# ✅ 修正: ユーザー一覧編集セクション
elif menu == "ユーザー一覧":
    userLists()

# ✅ 修正: チーム管理セクション
elif menu == "チーム管理":
    teamManage()

elif menu == "チームプロンプト設定":
    teamPromptSettings()

elif menu == "プロンプトキー管理":
    teamPromptKeyManage()

elif menu == "会社ビジョン学習":
    companyVisionLearn()

elif menu == "ユーザー一覧":
   userLists()

elif menu == "チームごとのプロンプトキー設定":
    teamPromptKeySettings()

# ✅ 修正: 商談評価ログ登録セクションを完全削除し、閲覧専用の商談分析に統合
elif menu == "📊 商談振り返り・分析":
    shodanBunseki()

# ✅ 既存のチーム別ダッシュボードとフォローアップ管理は変更なし
elif menu == "🏢 チーム別ダッシュボード":
    tpdb()

elif menu == "📅 フォローアップ管理":
    followupManagement()
