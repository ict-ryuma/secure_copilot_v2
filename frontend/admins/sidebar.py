import streamlit as st
from backend.auth import get_current_user,login_user

def sidebar():
    with st.sidebar:
        # --- セッション初期化 ---
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.team_name = ""
            st.session_state.is_admin = False

        # --- ログイン画面 ---
        if not st.session_state.logged_in:
            st.subheader("🔐 管理者ログイン")
            username = st.text_input("ユーザー名").strip()
            password = st.text_input("パスワード", type="password").strip()

            if st.button("ログイン"):
                success,id, team_name, is_admin = login_user(username, password)
                if success and is_admin:
                    st.session_state.logged_in = True
                    st.session_state.user_id = id
                    st.session_state.username = username
                    st.session_state.team_name = team_name
                    st.session_state.is_admin = True
                    st.rerun()
                elif success:
                    st.error("❌ 管理者ではありません。")
                else:
                    st.error("❌ ログインに失敗しました。")
            st.stop()

        st.title("🔧 管理者ダッシュボード")
        st.write(f"ようこそ、{st.session_state.username}さん！")
        # --- 管理者権限チェック ---
        try:
            user = get_current_user(st.session_state.username)
            if not user["is_admin"]:
                st.error("このページは管理者専用です。ログインしてください。")
                st.stop()
        except Exception as e:
            st.error(f"ユーザー情報の取得に失敗しました: {e}")
            st.stop()


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
