import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from datas.users import migrate_users
from datas.teams import create_teams
from datas.prompts import create_prompts
from datas.user_has_team import create_user_has_teams
from datas.team_has_prompts import create_team_has_prompts

print("✅ MySQL設定で起動")



if __name__ == "__main__":
    # Admin 
    migrate_users("Secured Admin","admin","admin123",1)
    # 追加ユーザー例
    migrate_users("Ryuma Hoshi","ryuma", "star76", True)
    migrate_users("My User","user1", "password1", False)

    create_teams()
    create_prompts()
    create_user_has_teams()
    create_team_has_prompts()
