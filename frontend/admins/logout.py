import streamlit as st

def logout(cookie_manager,app_name):
    # st.markdown("---")
    if st.button("🔓 ログアウト"):
        # Delete cookies
        cookie_manager.delete(f"{app_name}-user",key=f"{app_name}-user-set")
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.team_name = ""
        st.session_state.is_admin = False
        st.session_state.authentication_status = False
        st.session_state.user_id = ""
        st.session_state.team_id = ""

        # Rerun to return to login page
        if "logged_in" not in st.session_state:
            st.experimental_rerun()