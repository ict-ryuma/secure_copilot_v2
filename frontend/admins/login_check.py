import streamlit as st
import extra_streamlit_components as stx
from backend.auth import login_user
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
def session_and_cookie_set(user_id,username,team_name,is_admin,cookie_manager,app_name):
        st.session_state.logged_in = True
        st.session_state["authentication_status"] = True
        st.session_state["username"] = username
        st.session_state["user_id"] = user_id
        st.session_state["team_name"] = team_name
        st.session_state["is_admin"] = is_admin

        # Save cookies for persistent login
        cookie_value = json.dumps({"userid": user_id, "username": username})
        cookie_manager.set(f"{app_name}-user", cookie_value, max_age=30*24*60*60)
        cookie_manager.set(f"{app_name}-userid", str(user_id), max_age=30*24*60*60)
        st.experimental_rerun()
def login(cookie_manager,app_name,login_type="admin"):
    input_username = st.text_input("ユーザー名")
    input_password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        success, user_id,username,team_name,is_admin= login_user(input_username, input_password)  

        if success and is_admin:
            session_and_cookie_set(user_id,username,team_name,is_admin,cookie_manager,app_name)
        elif success and not is_admin:
            if login_type=="admin":
                st.error("❌ 管理者ではありません。")
            elif login_type=="user":
                session_and_cookie_set(user_id,username,team_name,is_admin,cookie_manager,app_name)
        else:
            st.error("❌ ユーザー名またはパスワードが正しくありません。")
    st.stop()


