import streamlit as st

def menu():
    st.header("📋 管理メニュー")
    menu = st.radio("操作を選択", [
        # "🔄 プロンプト再取得",
        "商談を作成",
        "未評価の商談を選択してください",
        "評価の商談を選択してください",
        "🔓 ログアウト",
    ])
    return menu
