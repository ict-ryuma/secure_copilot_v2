import streamlit as st

def menu():
    st.header("📋 管理メニュー")
    menu = st.radio("操作を選択", [
        "🔄 プロンプト再取得",
        "評価を作成",
        "評価を選択",
        "🔓 ログアウト",
    ])
    return menu
