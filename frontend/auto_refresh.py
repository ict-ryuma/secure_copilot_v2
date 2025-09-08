from streamlit_autorefresh import st_autorefresh
from team_validation import get_valid_team_for_user

def auto_refresh_view(cookie_manager, app_name):
    # Auto-refresh every 5 seconds
    count = st_autorefresh(interval=5000, limit=None, key="team_autorefresh")
    # Fetch the latest valid teams on every refresh
    get_valid_team_for_user(cookie_manager, app_name)

