import streamlit as st

def logout(cookie_manager,app_name):
    st.markdown("---")
    if st.button("🔓 ログアウト"):
        # Delete cookies
        cookie_manager.delete(f"{app_name}-user")
        cookie_manager.delete(f"{app_name}-userid")
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.team_name = ""
        st.session_state.is_admin = False
        st.session_state.authentication_status = False
        st.session_state["username"] = ""
        st.session_state["user_id"] = ""
        # Rerun to return to login page
        st.experimental_rerun()
        st.stop