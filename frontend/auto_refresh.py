# import streamlit as st
# import time

# from team_validation import get_valid_team_for_user

# def auto_refresh_view(cookie_manager, app_name):
#     """
#     A view that auto-refreshes every 5 seconds to show updated team information.
#     """
#     # st.title("リアルタイムチーム情報")
#     # st.write("このページは5秒ごとに自動更新され、最新のチーム情報を表示します。")

#     # Refresh every 5 seconds
#     st_autorefresh = st.experimental_rerun  # newer versions auto rerun
#     count = st.experimental_get_query_params().get("count", [0])[0]

#     st_autorefresh = st.experimental_autorefresh(interval=5000, key="team_refresh")

#     # Always fetch from backend
#     valid_teams = get_valid_team_for_user(cookie_manager, app_name)

#     st.write("✅ 利用可能なチーム (リアルタイム更新)", valid_teams)

# import streamlit as st
# from team_validation import get_valid_team_for_user

# def auto_refresh_view(cookie_manager, app_name):
#     # 🔄 Auto refresh every 5 seconds (5000 ms)
#     st.autorefresh(interval=5000, key="team_refresh")

#     # ✅ Always fetch from backend
#     valid_teams = get_valid_team_for_user(cookie_manager, app_name)

#     st.write("✅ 利用可能なチーム (リアルタイム更新)", valid_teams)

from itertools import count
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from team_validation import get_valid_team_for_user

def auto_refresh_view(cookie_manager, app_name):
    # Auto-refresh every 5 seconds
    count = st_autorefresh(interval=5000, limit=None, key="team_autorefresh")
    # Fetch the latest valid teams on every refresh
    get_valid_team_for_user(cookie_manager, app_name)

