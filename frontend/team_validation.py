from backend.teams import get_user_team
import streamlit as st
from frontend.admins.login_check import session_and_cookie_set


def get_valid_team_for_user(cookie_manager,app_name) -> dict:
    """
    Validates that the logged-in user is a member of the team with the given team_id.
    Returns the Team object if valid, otherwise raises ValueError.
    """
    team_id = st.session_state.get("team_id", "")
    current_user_id = st.session_state.get("user_id", "")
    current_username = st.session_state.get("username", "")
    current_is_admin = st.session_state.get("is_admin", "")
    team = get_user_team(current_user_id)
    if team[0] != team_id:
        session_and_cookie_set(current_user_id,current_username,team[0],team[1],current_is_admin,cookie_manager,app_name)
