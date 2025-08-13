import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher
import extra_streamlit_components as stx
import bcrypt
from backend.auth import get_all_users,login_user
from logger_config import logger
import json

def login_check(app_name=None):
    cookie_manager = stx.CookieManager(key="cookie_manager_logout")
    # Restore from cookie if available
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = False
        logger.info(f"authentication_status1: {st.session_state['authentication_status']}")
        st.stop

    cookie_val = cookie_manager.get(f"{app_name}-user")
    if isinstance(cookie_val, str):
        cookie_user_data = json.loads(cookie_val)
    elif isinstance(cookie_val, dict):
        cookie_user_data = cookie_val
    else:
        cookie_user_data = {}
    if cookie_user_data:
        cookie_user_id = cookie_user_data.get("userid")
        cookie_username = cookie_user_data.get("username")

    if cookie_user_data and cookie_user_id and cookie_username and not st.session_state["authentication_status"]:
        # Assume session is valid (you could re-check DB here)
        st.session_state["authentication_status"] = True
        st.session_state["username"] = cookie_username
        st.session_state["user_id"] = int(cookie_user_id)
        
    return cookie_manager,cookie_user_data


