import streamlit as st

def menu():
    st.header("📋 管理メニュー")

    # Define menu options
    options = [
        "商談を作成",
        "未評価の商談を選択してください",
        "評価の商談を選択してください"
    ]

    # Initialize default menu selection after login
    if "menu_selected" not in st.session_state:
        st.session_state.menu_selected = options[0]  # first item as default

    menu = st.radio(
        "操作を選択",
        options,
        index=options.index(st.session_state.menu_selected),  # restore from session
        key="menu_selected"
    )
    return menu

