import streamlit as st
from backend.mysql_connector import execute_query
from backend.auth import get_all_teams_safe, validate_team_comprehensive, update_user_role, diagnose_team_integrity,delete_user,register_user
# from backend.prompt_loader import check_team_exists

# USER_DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"
# PROMPT_DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"
def register():
    st.subheader("👤 新規ユーザー登録")
    new_username = st.text_input("ユーザー名")
    new_password = st.text_input("パスワード", type="password")
    
    try:
        team_options = get_all_teams_safe()  # ✅ 統一関数使用
        
        if not team_options:
            st.error("⚠️ 現在利用可能なアクティブチームがありません。")
            st.info("💡 先に「チーム管理」でチームを作成・有効化してください。")
            
            with st.expander("🔧 チーム作成手順"):
                st.write("1. 「チーム管理」メニューを選択")
                st.write("2. 「チーム追加フォーム」でチーム情報を入力")
                st.write("3. 「チームを登録」ボタンをクリック")
                st.write("4. チームが有効化されていることを確認")
                st.write("5. このページに戻ってユーザー登録")
            
            st.stop()
        
        # ✅ チーム選択（プレースホルダー完全排除）
        selected_team = st.selectbox(
            "チームを選択", 
            options=team_options,
            help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）"
        )
        is_admin_flag = st.checkbox("管理者として登録")

        if st.button("登録実行"):
            if new_username.strip() and new_password.strip():
                # ✅ 修正: register_user の戻り値を適切に処理
                success, message = register_user(new_username, new_password, selected_team, is_admin_flag)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ 登録に失敗しました:")
                    st.error(message)
                    
                    # ✅ 詳細エラー情報の表示
                    if "対処法:" in message:
                        error_parts = message.split("対処法:")
                        if len(error_parts) == 2:
                            st.warning(f"💡 **対処法:** {error_parts[1].strip()}")
            else:
                st.warning("⚠️ ユーザー名とパスワードを入力してください")
                
    except Exception as e:
        st.error(f"チーム一覧の取得に失敗しました: {e}")
        with st.expander("🔧 エラー詳細"):
            st.code(f"エラー: {str(e)}")


def userLists():
    st.subheader("👥 登録ユーザー一覧と編集")
    try:
        # ユーザー情報取得
        # conn = sqlite3.connect(USER_DB_PATH)
        # cursor = conn.cursor()
        users = execute_query("SELECT username, team_name, is_admin FROM users ORDER BY team_name, username", fetch=True)

        # ✅ 統一関数でチーム一覧取得
        available_teams = get_all_teams_safe()
        
        # ✅ チームが存在しない場合の詳細警告
        if not available_teams:
            st.error("⚠️ アクティブなチームがありません。先に「チーム管理」でチームを作成してください。")
            st.info("💡 現在登録されているユーザーの確認はできますが、チーム変更はできません。")
            
            with st.expander("🔧 解決手順"):
                st.write("1. 「チーム管理」でチームを作成")
                st.write("2. チームを有効化")
                st.write("3. このページに戻ってユーザー編集")

        # ✅ 包括的診断機能
        st.markdown("### 🔧 チーム整合性診断")
        if st.button("🔍 全ユーザーのチーム状態を診断"):
            with st.spinner("診断中..."):
                diagnosis = diagnose_team_integrity()
                
                if "error" in diagnosis:
                    st.error(f"❌ 診断エラー: {diagnosis['error']}")
                else:
                    summary = diagnosis["summary"]
                    st.metric("正常なユーザー", f"{summary['healthy_users']}/{diagnosis['total_users']}", f"{summary['health_percentage']}%")
                    
                    if diagnosis["user_issues"]:
                        st.error(f"🚨 {summary['problematic_users']}件の問題が発見されました")
                        
                        for issue in diagnosis["user_issues"]:
                            with st.expander(f"❌ {issue['username']} ({issue['issue_type']})"):
                                st.write(f"**チーム:** {issue['team_name']}")
                                st.write(f"**問題:** {issue['message']}")
                                st.write("**対処法:**")
                                for suggestion in issue['suggestions']:
                                    st.write(f"- {suggestion}")
                    else:
                        st.success("✅ 全ユーザーのチーム設定は正常です")

        if users:
            st.markdown("### 👥 ユーザー一覧")
            
            for username, team, is_admin in users:
                # ✅ 包括的チーム検証
                team_validation = validate_team_comprehensive(team)
                
                with st.expander(f"👤 {username} (チーム: {team})"):
                    # ✅ チーム状態の詳細表示
                    if team_validation["valid"]:
                        st.success("✅ チーム設定は正常です")
                    else:
                        st.error(f"❌ {team_validation['message']}")
                        
                        # 対処法表示
                        if "suggestions" in team_validation:
                            st.write("**対処法:**")
                            for suggestion in team_validation["suggestions"]:
                                st.write(f"- {suggestion}")
                    
                    # ✅ ユーザー編集フォーム
                    with st.form(f"user_form_{username}"):
                        cols = st.columns([3, 3, 2, 2])
                        
                        with cols[0]:
                            st.markdown(f"**ユーザー名:** {username}")
                            st.markdown(f"**現在のチーム:** {team}")
                        
                        with cols[1]:
                            # ✅ チーム選択（有効チームのみ）
                            if available_teams:
                                try:
                                    current_index = available_teams.index(team) if team in available_teams else 0
                                except ValueError:
                                    current_index = 0
                                
                                new_team = st.selectbox(
                                    "新しいチーム", 
                                    options=available_teams,
                                    index=current_index,
                                    key=f"team_{username}",
                                    help="アクティブなチームのみ表示（プレースホルダー除外）"
                                )
                            else:
                                st.warning("利用可能なチームなし")
                                new_team = team
                        
                        with cols[2]:
                            admin_flag = st.checkbox(
                                "管理者", 
                                value=bool(is_admin), 
                                key=f"admin_{username}"
                            )
                        
                        with cols[3]:
                            # ✅ 更新ボタン
                            if available_teams and st.form_submit_button("💾 更新", type="primary"):
                                success, message = update_user_role(username, admin_flag, new_team)
                                
                                if success:
                                    st.success(message)
                                    
                                    # ✅ セッション同期
                                    if st.session_state.get("username") == username:
                                        st.session_state.team_name = new_team
                                        st.session_state.is_admin = admin_flag
                                        if "prompts" in st.session_state:
                                            del st.session_state.prompts
                                        st.info("🔄 あなたのセッション情報を更新しました")
                                    
                                    st.rerun()
                                else:
                                    st.error(f"❌ 更新失敗: {message}")
        else:
            st.info("登録されているユーザーがいません。")
            
    except Exception as e:
        st.error(f"ユーザー一覧でエラーが発生しました: {e}")
        st.code(f"詳細: {str(e)}")


# def userLists():
#     st.subheader("👥 登録ユーザー一覧と編集")
#     try:
#         # ✅ ユーザー情報は USER_DB_PATH を使用
#         # conn = sqlite3.connect(USER_DB_PATH)
#         # cursor = conn.cursor()
#         users = execute_query("SELECT username, team_name, is_admin FROM users ORDER BY team_name, username", fetch=True)

#         # ✅ 修正: プレースホルダー除外版の安全なチーム一覧取得
#         available_teams = get_all_teams_safe()
        
#         # ✅ チームが存在しない場合の警告
#         if not available_teams:
#             st.error("⚠️ アクティブなチームがありません。先に「チーム管理」でチームを作成してください。")
#             st.info("💡 現在登録されているユーザーの編集はできますが、新しいチームへの変更はできません。")

#         if users:
#             current_team = None
#             for username, team, is_admin in users:
#                 if current_team != team:
#                     st.markdown(f"### 🏷️ チーム: `{team}`")
#                     current_team = team
                
#                 # ✅ チーム存在確認（プレースホルダー検出強化）
                
#                 team_status = check_team_exists(team)
                
#                 # ✅ プレースホルダーチームの警告
#                 is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
#                 if is_placeholder:
#                     st.warning(f"⚠️ ユーザー `{username}` はプレースホルダーチーム `{team}` に所属しています。実際のチームに変更してください。")
#                 elif not team_status["exists"]:
#                     st.warning(f"⚠️ ユーザー `{username}` のチーム `{team}` が存在しません")
#                 elif not team_status["active"]:
#                     st.warning(f"⚠️ ユーザー `{username}` のチーム `{team}` が無効化されています")
                
#                 # ✅ チーム変更機能付きフォーム
#                 with st.form(f"user_form_{username}"):
#                     cols = st.columns([3, 2, 2, 2])
                    
#                     with cols[0]:
#                         st.markdown(f"**{username}**")
#                         if is_placeholder:
#                             st.caption("🚨 プレースホルダーチーム")
#                         elif not team_status["exists"] or not team_status["active"]:
#                             st.caption("🚨 チーム要修正")
                    
#                     with cols[1]:
#                         # ✅ チーム選択ボックス（プレースホルダー除外）
#                         if available_teams:
#                             try:
#                                 current_team_index = available_teams.index(team) if team in available_teams else 0
#                             except ValueError:
#                                 current_team_index = 0
                                
#                             new_team = st.selectbox(
#                                 "チーム", 
#                                 options=available_teams,
#                                 index=current_team_index,
#                                 key=f"team_{username}",
#                                 help="アクティブなチームのみ表示（プレースホルダー除外）"
#                             )
#                         else:
#                             st.warning("利用可能なチームなし")
#                             new_team = team  # 変更なし
                    
#                     with cols[2]:
#                         admin_flag = st.checkbox(
#                             "管理者", 
#                             value=bool(is_admin), 
#                             key=f"admin_{username}"
#                         )
                    
#                     with cols[3]:
#                         if st.form_submit_button("🗑️ 削除", type="secondary"):
#                             if delete_user(username):
#                                 st.warning(f"{username} を削除しました")
#                                 st.rerun()
#                             else:
#                                 st.error("削除に失敗しました")
                    
#                     # ✅ 更新ボタン（チーム変更対応 + セッション同期）
#                     if available_teams and st.form_submit_button(f"💾 更新（{username}）", type="primary"):
#                         if update_user_role(username, admin_flag, new_team):
#                             success_msg = f"{username} を更新しました"
#                             if new_team != team:
#                                 success_msg += f" (チーム: {team} → {new_team})"
#                                 if is_placeholder:
#                                     success_msg += " ✅ プレースホルダーチームから移行完了"
                            
#                             st.success(success_msg)
                            
#                             # ✅ セッション同期：更新対象ユーザーがログイン中の場合
#                             if st.session_state.get("username") == username:
#                                 st.session_state.team_name = new_team
#                                 st.session_state.is_admin = admin_flag
#                                 st.session_state.prompts = {}  # プロンプト再取得を強制
#                                 st.info("🔄 あなたのセッション情報を更新しました。プロンプトを再取得してください。")
                            
#                             st.rerun()
#                         else:
#                             st.error("更新に失敗しました")
#         else:
#             st.info("登録されているユーザーがいません。")
            
#         # ✅ チーム整合性チェック機能（プレースホルダー検出強化）
#         st.markdown("---")
#         st.subheader("🔧 整合性チェック")
        
#         if st.button("🔍 全ユーザーのチーム状態をチェック"):
#             check_results = []
#             placeholder_count = 0
            
#             for username, team, is_admin in users:
#                 is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
                
#                 if is_placeholder:
#                     placeholder_count += 1
#                     check_results.append({
#                         "username": username,
#                         "team": team,
#                         "type": "placeholder",
#                         "message": f"プレースホルダーチーム '{team}' を使用中"
#                     })
#                 else:
#                     team_status = check_team_exists(team)
                    
#                     if not team_status["exists"] or not team_status["active"]:
#                         check_results.append({
#                             "username": username,
#                             "team": team,
#                             "type": "invalid",
#                             "message": team_status["message"]
#                         })
            
#             # 結果表示
#             problems = [r for r in check_results if r["type"] in ["placeholder", "invalid"]]
            
#             if problems:
#                 st.error(f"🚨 {len(problems)}件の問題が見つかりました")
                
#                 # プレースホルダーチーム問題
#                 placeholder_problems = [p for p in problems if p["type"] == "placeholder"]
#                 if placeholder_problems:
#                     st.warning(f"📋 プレースホルダーチーム使用: {len(placeholder_problems)}件")
#                     for problem in placeholder_problems:
#                         st.write(f"  - **{problem['username']}**: {problem['message']}")
                
#                 # 無効チーム問題
#                 invalid_problems = [p for p in problems if p["type"] == "invalid"]
#                 if invalid_problems:
#                     st.error(f"❌ 無効チーム: {len(invalid_problems)}件")
#                     for problem in invalid_problems:
#                         st.write(f"  - **{problem['username']}**: {problem['message']}")
                        
#                 # 修正提案
#                 if placeholder_problems:
#                     st.info("💡 **修正方法**: 上記のユーザーを実際のチームに変更してください。")
                    
#             else:
#                 st.success("✅ 全ユーザーのチーム設定は正常です（プレースホルダーチーム使用なし）")
            
#         # ✅ デバッグ情報（管理者のみ）
#         with st.expander("🔧 デバッグ情報"):
#             st.write(f"**利用可能なチーム（プレースホルダー除外）:** {available_teams}")
#             st.write(f"**ユーザーDB:** {USER_DB_PATH}")
#             st.write(f"**プロンプトDB:** {PROMPT_DB_PATH}")
            
#             # 全ユーザーのチーム分布
#             team_counts = {}
#             for username, team, is_admin in users:
#                 team_counts[team] = team_counts.get(team, 0) + 1
            
#             st.write("**チーム別ユーザー数:**")
#             for team, count in sorted(team_counts.items()):
#                 is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
#                 status = "🚨 プレースホルダー" if is_placeholder else "✅ 正常"
#                 st.write(f"  - {team}: {count}人 ({status})")
            
#     except Exception as e:
#         st.error(f"ユーザー一覧でエラーが発生しました: {e}")
#         st.code(f"詳細エラー: {str(e)}")
#         st.stop()