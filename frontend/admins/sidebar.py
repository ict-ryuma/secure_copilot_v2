import streamlit as st
# from backend.auth import get_current_user,login_user

def sidebar():
    with st.sidebar:
        st.header("📋 管理メニュー")
        menu = st.radio("操作を選択", [
            "ユーザー登録", "チーム管理",
            "チームプロンプト設定", "プロンプトキー管理",
            "会社ビジョン学習", "ユーザー一覧",
            "チームごとのプロンプトキー設定",
            "📊 商談振り返り・分析",  # ✅ 商談評価ログ登録を削除
            "🏢 チーム別ダッシュボード",
            "📅 フォローアップ管理"
        ])
        st.markdown("---")
        if st.button("🔓 ログアウト"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.team_name = ""
            st.session_state.is_admin = False
            st.rerun()
        return menu
