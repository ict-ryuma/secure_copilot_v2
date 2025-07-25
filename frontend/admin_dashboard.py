import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import yaml
# import sqlite3
import fitz  # PyMuPDF
import pandas as pd
import json
from datetime import datetime, date, time
from dotenv import load_dotenv
from backend.mysql_connector import execute_query
from backend.auth import (
    get_current_user, register_user, get_all_teams, login_user,
    update_user_role, delete_user
)
from backend.db_team_master import (
    create_team_master_table, insert_team_prompt,
    fetch_all_team_prompts, update_team_prompt, delete_team_prompt
)
from backend.db_prompt_key_master import (
    create_prompt_key_master_table, insert_prompt_key,
    fetch_all_prompt_keys
)
import requests
# ✅ 修正: backend/save_log.py の拡張版関数を使用
from backend.save_log import (
    create_conversation_logs_table, save_conversation_log, get_conversation_logs,
    get_team_dashboard_stats, get_followup_schedule, delete_conversation_log
)

# --- パス設定 ---
BASE_DIR = Path(__file__).resolve().parents[1]
VISION_PATH = os.path.join(BASE_DIR, "team_knowledge", "company.yaml")

# ✅ 修正: 全てのDBパスを統一
USER_DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"
PROMPT_DB_PATH = "/home/ec2-user/secure_copilot_v2/score_log.db"

load_dotenv()

# ✅ ヘルパー関数: ステータスバッジ（先頭で定義）
def get_status_badge(status):
    """商談状態をバッジ形式で返す"""
    badges = {
        "成約": "🟢 成約",
        "失注": "🔴 失注", 
        "再商談": "🟡 再商談",
        "未設定": "⚪ 未設定"
    }
    return badges.get(status, "⚪ 未設定")

# ✅ 修正: プレースホルダーチームを除外した安全なチーム取得
def get_all_teams_safe():
    """team_masterから実際に登録されたアクティブなチームのみを返す"""
    try:
        # まずbackend.authのget_all_teamsを試行
        from backend.auth import get_all_teams
        teams = get_all_teams()
        
        # プレースホルダーチームを除外
        filtered_teams = [team for team in teams if team not in ['A_team', 'B_team', 'C_team', 'F_team']]
        if filtered_teams:
            return filtered_teams
    except (ImportError, AttributeError):
        pass
    
    # フォールバック: team_masterテーブルから直接取得
    try:
        # conn = sqlite3.connect(PROMPT_DB_PATH)
        # cursor = conn.cursor()
        
        # ✅ 修正: 列名を team_name に統一
        execute_query("""
            SELECT team_name FROM team_master 
            WHERE is_active = 1 
            AND team_name NOT IN ('A_team', 'B_team', 'C_team', 'F_team')
            ORDER BY team_name
        """, fetch=True)
        teams = [row[0] for row in teams]
        print(f"🔍 取得したアクティブチーム（プレースホルダー除外）: {teams}")
        return teams
        
    except Exception as e:
        print(f"❌ チーム取得エラー: {e}")
        return []

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
        success, team_name, is_admin = login_user(username, password)
        if success and is_admin:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.team_name = team_name
            st.session_state.is_admin = True
            st.rerun()
        elif success:
            st.error("❌ 管理者ではありません。")
        else:
            st.error("❌ ログインに失敗しました。")
    st.stop()

# --- 管理者権限チェック ---
try:
    user = get_current_user(st.session_state.username)
    if not user["is_admin"]:
        st.error("このページは管理者専用です。ログインしてください。")
        st.stop()
except Exception as e:
    st.error(f"ユーザー情報の取得に失敗しました: {e}")
    st.stop()

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

# --- メニュー分岐 ---
if menu == "ユーザー登録":
    st.subheader("👤 新規ユーザー登録")
    new_username = st.text_input("ユーザー名")
    new_password = st.text_input("パスワード", type="password")
    
    try:
        from backend.auth import get_all_teams_safe, register_user
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

# ✅ 修正: ユーザー一覧編集セクション
elif menu == "ユーザー一覧":
    st.subheader("👥 登録ユーザー一覧と編集")
    try:
        from backend.auth import get_all_teams_safe, validate_team_comprehensive, update_user_role, diagnose_team_integrity
        
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

# ✅ 修正: チーム管理セクション
elif menu == "チーム管理":
    st.subheader("🏷️ チーム一覧管理")
    try:
        create_team_master_table()
        teams = fetch_all_team_prompts()
        
        st.markdown("### 📋 現在のチーム一覧")
        if teams:
            for i, t in enumerate(teams):
                # ✅ 修正: 9列に対応
                team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = t
                
                # ✅ 包括的検証結果表示
                from backend.auth import validate_team_comprehensive
                validation = validate_team_comprehensive(team_name)
                
                if validation["valid"]:
                    status = "🟢 正常"
                elif validation["reason"] == "placeholder_team":
                    status = "🚨 プレースホルダー"
                elif validation["reason"] == "team_inactive":
                    status = "⚪ 無効"
                elif validation["reason"] == "prompt_incomplete":
                    status = "⚠️ プロンプト不完全"
                else:
                    status = "❌ 問題あり"
                
                with st.expander(f"{status} `{team_name}` → プロンプトキー: `{prompt_key}` (更新: {updated_at})"):
                    # 検証結果詳細
                    if not validation["valid"]:
                        st.warning(f"**問題:** {validation['message']}")
                        if "suggestions" in validation:
                            st.write("**対処法:**")
                            for suggestion in validation["suggestions"]:
                                st.write(f"- {suggestion}")
                    
                    # 編集フォーム
                    with st.form(f"edit_team_{team_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_name = st.text_input("チーム名", value=team_name, key=f"name_{team_id}")
                            edit_key = st.text_input("プロンプトキー", value=prompt_key, key=f"key_{team_id}")
                            edit_active = st.checkbox("有効化", value=bool(is_active), key=f"active_{team_id}")
                        
                        with col2:
                            edit_notes = st.text_area("備考", value=notes or "", height=100, key=f"notes_{team_id}")
                        
                        # 更新・削除ボタン
                        col_update, col_delete = st.columns(2)
                        
                        with col_update:
                            if st.form_submit_button("💾 更新", type="primary"):
                                try:
                                    update_team_prompt(
                                        team_id, edit_name, edit_key, text_prompt, 
                                        audio_prompt, score_items, edit_notes, int(edit_active)
                                    )
                                    st.success(f"✅ チーム '{edit_name}' を更新しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 更新エラー: {e}")
                        
                        with col_delete:
                            if st.form_submit_button("🗑️ 削除", type="secondary"):
                                try:
                                    delete_team_prompt(team_id)
                                    st.warning(f"⚠️ チーム '{team_name}' を削除しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 削除エラー: {e}")
        else:
            st.info("登録されているチームがありません。")

        # ✅ 新規チーム追加（検証強化）
        st.markdown("---")
        st.subheader("🆕 チーム追加フォーム")
        with st.form("add_team_form"):
            new_name = st.text_input("チーム名", placeholder="例: sales_team_alpha")
            new_key = st.text_input("プロンプトキー", placeholder="例: prompt_sales_alpha")
            new_text = st.text_area("テキストプロンプト", placeholder="営業評価用のプロンプトを入力", height=100)
            new_audio = st.text_area("音声プロンプト", placeholder="音声評価用のプロンプトを入力", height=80)
            new_score = st.text_input("スコア項目（カンマ区切り）", placeholder="ヒアリング姿勢,説明のわかりやすさ,...")
            new_desc = st.text_area("備考", height=60)
            
            if st.form_submit_button("✅ チームを登録"):
                if new_name.strip() and new_key.strip():
                    # ✅ プレースホルダーチーム名のチェック
                    if new_name.strip() in ['A_team', 'B_team', 'C_team', 'F_team']:
                        st.error("❌ プレースホルダーチーム名（A_team, B_team, C_team, F_team）は使用できません")
                    else:
                        try:
                            insert_team_prompt(
                                name=new_name.strip(),
                                key=new_key.strip(),
                                text_prompt=new_text or "デフォルトテキストプロンプト",
                                audio_prompt=new_audio or "デフォルト音声プロンプト",
                                score_items=new_score or "ヒアリング姿勢,説明のわかりやすさ,クロージングの一貫性,感情の乗せ方と誠実さ,対話のテンポ",
                                notes=new_desc or "（備考なし）"
                            )
                            st.success(f"✅ チーム '{new_name.strip()}' を追加しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ チーム追加エラー: {e}")
                else:
                    st.warning("⚠️ チーム名とプロンプトキーは必須です")
                    
    except Exception as e:
        st.error(f"チーム管理でエラーが発生しました: {e}")

elif menu == "チームプロンプト設定":
    st.subheader("🧠 チームプロンプト管理（DBベース）")
    try:
        teams = fetch_all_team_prompts()
        for team in teams:
            # ✅ 修正: 9列に対応
            team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team
            
            st.markdown("---")
            with st.expander(f"✏️ {team_name} ({prompt_key}) - 更新: {updated_at}"):
                with st.form(f"form_{team_id}"):
                    new_name = st.text_input("チーム名", team_name)
                    new_key = st.text_input("プロンプトキー", prompt_key)
                    new_text = st.text_area("テキストプロンプト", text_prompt, height=120)
                    new_audio = st.text_area("音声プロンプト", audio_prompt, height=80)
                    new_score = st.text_input("スコア項目（カンマ区切り）", score_items)
                    new_note = st.text_area("補足・備考", notes)
                    is_active_flag = st.checkbox("✅ このチームを有効にする", value=is_active == 1)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 更新"):
                            update_team_prompt(team_id, new_name, new_key, new_text, new_audio, new_score, new_note, int(is_active_flag))
                            st.success("更新しました")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ 削除"):
                            delete_team_prompt(team_id)
                            st.warning("削除しました")
                            st.rerun()
    except Exception as e:
        st.error(f"プロンプト設定でエラーが発生しました: {e}")

elif menu == "プロンプトキー管理":
    st.subheader("📋 プロンプトキー一覧と操作")
    try:
        create_prompt_key_master_table()
        
        # ✅ 修正: team_masterテーブルから取得（統一）
        # conn = sqlite3.connect(PROMPT_DB_PATH)
        # cursor = conn.cursor()
        keys = execute_query("""
            SELECT id, prompt_key, notes as description, is_active, updated_at 
            FROM team_master 
            ORDER BY team_name
        """, fetch=True)
        # keys = cursor.fetchall()
        # conn.close()

        # 既存のプロンプトキー表示ロジックはそのまま
        for key in keys:
            id_, prompt_key, description, is_active, created_at = key
            status = "🟢 有効" if is_active else "⚪️ 無効"
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**{status}** `{prompt_key}` — {description or '(説明なし)'}")
                st.caption(f"作成日: {created_at}")
            with col2:
                if is_active:
                    if st.button(f"⚪️ 無効化", key=f"deactivate_{id_}"):
                        # conn = sqlite3.connect(PROMPT_DB_PATH)
                        # cursor = conn.cursor()
                        execute_query("UPDATE prompt_key_master SET is_active = 0 WHERE id = %s", (id_,))
                        # conn.commit()
                        # conn.close()
                        st.success(f"'{prompt_key}' を無効化しました")
                        st.rerun()

        st.markdown("---")
        st.subheader("🆕 プロンプトキー新規追加")
        with st.form("new_prompt_form"):
            new_key = st.text_input("プロンプトキー名")
            new_desc = st.text_area("説明", height=80)
            if st.form_submit_button("✅ 登録"):
                if new_key:
                    # team_masterテーブルに統一して登録
                    insert_team_prompt(
                        name=f"チーム_{new_key}",
                        key=new_key.strip(),
                        text_prompt="デフォルトプロンプト",
                        audio_prompt="デフォルト音声プロンプト", 
                        score_items='["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
                        notes=new_desc.strip()
                    )
                    st.success(f"✅ '{new_key}' を登録しました")
                    st.rerun()
                else:
                    st.warning("プロンプトキー名を入力してください")
    except Exception as e:
        st.error(f"プロンプトキー管理でエラーが発生しました: {e}")

elif menu == "会社ビジョン学習":
    st.subheader("🏢 会社ビジョンを学習させる")
    
    # ✅ 現在の保存先パスを表示
    st.info(f"📁 保存先: `{VISION_PATH}`")
    
    # ✅ 既存ファイルの確認と詳細表示
    if os.path.exists(VISION_PATH):
        try:
            with open(VISION_PATH, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f)
            
            if existing_data and "company_vision" in existing_data:
                # ファイル情報の表示
                file_size = os.path.getsize(VISION_PATH)
                file_mtime = os.path.getmtime(VISION_PATH)
                import datetime
                formatted_time = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y年%m月%d日 %H:%M:%S")
                
                st.success("✅ 会社ビジョンが設定済みです")
                
                # ✅ 詳細情報カード
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 文字数", f"{len(existing_data['company_vision'])}文字")
                with col2:
                    st.metric("💾 ファイルサイズ", f"{file_size}bytes")
                with col3:
                    st.metric("🕒 最終更新", formatted_time)
                
                # ✅ メタデータ表示（更新者、タイムスタンプなど）
                if "updated_by" in existing_data:
                    st.caption(f"👤 更新者: {existing_data['updated_by']}")
                if "original_filename" in existing_data:
                    st.caption(f"📎 元ファイル名: {existing_data['original_filename']}")
                
                # ✅ 内容プレビュー（折りたたみ式）
                with st.expander("📄 現在の会社ビジョン内容を確認"):
                    st.text_area(
                        "設定済みの内容", 
                        existing_data["company_vision"], 
                        height=250, 
                        disabled=True,
                        help="この内容がAIの評価に使用されます"
                    )
                
                # ✅ バックアップ機能
                if st.button("💾 現在の内容をバックアップ", help="現在の設定を日時付きでバックアップします"):
                    backup_filename = f"company_vision_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                    backup_path = os.path.join(os.path.dirname(VISION_PATH), backup_filename)
                    
                    with open(backup_path, "w", encoding="utf-8") as f:
                        yaml.dump(existing_data, f, allow_unicode=True, default_flow_style=False)
                    
                    st.success(f"✅ バックアップを作成しました: {backup_filename}")
                    
            else:
                st.warning("⚠️ ファイルは存在しますが、内容が正しくありません")
                
        except Exception as e:
            st.error(f"❌ 既存ファイルの読み込みエラー: {e}")
    else:
        st.warning("⚠️ まだ会社ビジョンが設定されていません")
        st.info("👇 下記の方法で会社ビジョンを設定してください")
    
    st.markdown("---")
    
    # ✅ 入力方法選択（より分かりやすく）
    st.subheader("📋 会社ビジョンの登録・更新")
    input_method = st.radio(
        "入力方法を選択してください", 
        ["📁 PDFファイルからアップロード", "✏️ テキストを直接入力"],
        help="PDFから自動抽出するか、テキストを直接貼り付けるかを選択"
    )
    
    extracted_text = ""
    original_filename = ""
    
    if input_method == "📁 PDFファイルからアップロード":
        uploaded_file = st.file_uploader(
            "会社ビジョン・ミッション資料（PDF）をアップロード", 
            type=["pdf"],
            help="会社案内、ビジョン資料、企業理念などのPDFファイルを選択してください"
        )
        
        if uploaded_file:
            original_filename = uploaded_file.name
            st.info(f"📎 選択されたファイル: **{original_filename}**")
            
            try:
                # ✅ プログレスバー表示
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("PDF読み込み中...")
                progress_bar.progress(25)
                
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    status_text.text(f"テキスト抽出中... ({len(doc)}ページ)")
                    progress_bar.progress(50)
                    
                    pages_text = []
                    for i, page in enumerate(doc):
                        pages_text.append(page.get_text())
                        progress_bar.progress(50 + (i + 1) / len(doc) * 30)
                    
                    extracted_text = "\n".join(pages_text)
                
                progress_bar.progress(100)
                status_text.text("✅ 完了")
                
                if extracted_text.strip():
                    st.success(f"✅ PDFからテキストを抽出しました（{len(extracted_text)}文字、{len(doc)}ページ）")
                    
                    # ✅ プレビュー表示（最初の500文字）
                    preview_text = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
                    st.text_area(
                        "抽出内容プレビュー（最初の500文字）", 
                        preview_text, 
                        height=150, 
                        disabled=True
                    )
                    
                    # ✅ 全文表示オプション
                    if st.checkbox("📖 抽出された全文を表示"):
                        st.text_area("抽出された全文", extracted_text, height=300, key="pdf_full_text")
                        
                else:
                    st.warning("⚠️ PDFからテキストを抽出できませんでした")
                    st.info("💡 スキャンされた画像PDFの場合、OCR処理が必要です")
                    
            except ImportError:
                st.error("❌ PyMuPDF (fitz) がインストールされていません")
                st.code("pip install PyMuPDF", language="bash")
            except Exception as e:
                st.error(f"❌ PDF読み込みエラー: {e}")
                with st.expander("🔧 詳細エラー情報"):
                    st.code(f"エラー詳細: {str(e)}")
    
    elif input_method == "✏️ テキストを直接入力":
        st.info("💡 会社のビジョン、ミッション、価値観、企業理念などを入力してください")
        extracted_text = st.text_area(
            "会社ビジョン・企業理念", 
            height=300, 
            placeholder="""例：
【企業ビジョン】
私たちは、革新的なソリューションを通じて...

【ミッション】
顧客の成功を第一に考え...

【コアバリュー】
1. 誠実性
2. 革新性
3. 顧客第一主義""",
            key="manual_vision_text"
        )
        
        if extracted_text.strip():
            st.success(f"✅ テキストが入力されました（{len(extracted_text)}文字）")
    
    # ✅ 保存処理（改良版）
    if extracted_text.strip():
        st.markdown("---")
        st.subheader("💾 保存設定")
        
        # ✅ 保存前の確認
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**保存される内容:**")
            st.info(f"📝 文字数: {len(extracted_text)}文字")
            if original_filename:
                st.info(f"📎 元ファイル: {original_filename}")
        
        with col2:
            if st.button("📥 保存する", type="primary", help="会社ビジョンとしてAIに学習させます"):
                try:
                    # ✅ ディレクトリ作成
                    vision_dir = os.path.dirname(VISION_PATH)
                    if not os.path.exists(vision_dir):
                        os.makedirs(vision_dir, exist_ok=True)
                        st.info(f"📁 ディレクトリを作成: {vision_dir}")
                    
                    # ✅ 詳細なメタデータ付きで保存
                    import datetime
                    vision_data = {
                        "company_vision": extracted_text.strip(),
                        "updated_by": st.session_state.get("username", "unknown"),
                        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "character_count": len(extracted_text.strip()),
                        "input_method": input_method,
                        "original_filename": original_filename if original_filename else "manual_input"
                    }
                    
                    with open(VISION_PATH, "w", encoding="utf-8") as f:
                        yaml.dump(vision_data, f, allow_unicode=True, default_flow_style=False)
                    
                    st.success("✅ 会社ビジョンを保存しました！")
                    st.balloons()
                    
                    # ✅ 保存結果の詳細表示
                    st.info(f"""
                    💾 **保存完了情報**
                    - ファイル: {os.path.basename(VISION_PATH)}
                    - サイズ: {os.path.getsize(VISION_PATH)} bytes
                    - 更新者: {vision_data['updated_by']}
                    - 更新日時: {vision_data['updated_at']}
                    """)
                    
                    # ✅ 自動リロード
                    st.rerun()
                    
                except PermissionError:
                    st.error("❌ ファイル書き込み権限がありません")
                    st.code(f"権限確認: chmod 755 {os.path.dirname(VISION_PATH)}")
                except Exception as e:
                    st.error(f"❌ 保存エラー: {e}")
                    with st.expander("🔧 詳細エラー情報"):
                        st.code(f"詳細: {str(e)}")
    
    # ✅ 操作ガイド
    with st.expander("❓ 会社ビジョン学習について"):
        st.markdown("""
        ### 📚 会社ビジョン学習機能とは？
        
        この機能では、会社の理念やビジョンをAIに学習させることで、
        営業評価がより会社の方針に沿った内容になります。
        
        ### 📋 設定できる内容
        - 🎯 企業ビジョン・ミッション
        - 💎 コアバリュー・企業価値観
        - 🏢 企業理念・経営方針
        - 🎪 企業文化・行動指針
        
        ### 🔄 活用方法
        設定された内容は、営業通話の評価時にAIが参考にして、
        会社の価値観に合った評価・アドバイスを提供します。
        """)
    
    # ✅ 技術情報（管理者向け）
    with st.expander("🔧 技術情報"):
        st.code(f"""
パス情報:
- 保存先: {VISION_PATH}
- ディレクトリ: {os.path.dirname(VISION_PATH)}
- ファイル存在: {os.path.exists(VISION_PATH)}
- ディレクトリ存在: {os.path.exists(os.path.dirname(VISION_PATH))}

依存関係:
- PyMuPDF: {"✅ OK" if 'fitz' in globals() else "❌ 未インストール"}
- YAML: {"✅ OK" if 'yaml' in globals() else "❌ 未インストール"}
        """)

elif menu == "ユーザー一覧":
    st.subheader("👥 登録ユーザー一覧と編集")
    try:
        # ✅ ユーザー情報は USER_DB_PATH を使用
        # conn = sqlite3.connect(USER_DB_PATH)
        # cursor = conn.cursor()
        users = execute_query("SELECT username, team_name, is_admin FROM users ORDER BY team_name, username", fetch=True)

        # ✅ 修正: プレースホルダー除外版の安全なチーム一覧取得
        available_teams = get_all_teams_safe()
        
        # ✅ チームが存在しない場合の警告
        if not available_teams:
            st.error("⚠️ アクティブなチームがありません。先に「チーム管理」でチームを作成してください。")
            st.info("💡 現在登録されているユーザーの編集はできますが、新しいチームへの変更はできません。")

        if users:
            current_team = None
            for username, team, is_admin in users:
                if current_team != team:
                    st.markdown(f"### 🏷️ チーム: `{team}`")
                    current_team = team
                
                # ✅ チーム存在確認（プレースホルダー検出強化）
                from backend.prompt_loader import check_team_exists
                team_status = check_team_exists(team)
                
                # ✅ プレースホルダーチームの警告
                is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
                if is_placeholder:
                    st.warning(f"⚠️ ユーザー `{username}` はプレースホルダーチーム `{team}` に所属しています。実際のチームに変更してください。")
                elif not team_status["exists"]:
                    st.warning(f"⚠️ ユーザー `{username}` のチーム `{team}` が存在しません")
                elif not team_status["active"]:
                    st.warning(f"⚠️ ユーザー `{username}` のチーム `{team}` が無効化されています")
                
                # ✅ チーム変更機能付きフォーム
                with st.form(f"user_form_{username}"):
                    cols = st.columns([3, 2, 2, 2])
                    
                    with cols[0]:
                        st.markdown(f"**{username}**")
                        if is_placeholder:
                            st.caption("🚨 プレースホルダーチーム")
                        elif not team_status["exists"] or not team_status["active"]:
                            st.caption("🚨 チーム要修正")
                    
                    with cols[1]:
                        # ✅ チーム選択ボックス（プレースホルダー除外）
                        if available_teams:
                            try:
                                current_team_index = available_teams.index(team) if team in available_teams else 0
                            except ValueError:
                                current_team_index = 0
                                
                            new_team = st.selectbox(
                                "チーム", 
                                options=available_teams,
                                index=current_team_index,
                                key=f"team_{username}",
                                help="アクティブなチームのみ表示（プレースホルダー除外）"
                            )
                        else:
                            st.warning("利用可能なチームなし")
                            new_team = team  # 変更なし
                    
                    with cols[2]:
                        admin_flag = st.checkbox(
                            "管理者", 
                            value=bool(is_admin), 
                            key=f"admin_{username}"
                        )
                    
                    with cols[3]:
                        if st.form_submit_button("🗑️ 削除", type="secondary"):
                            if delete_user(username):
                                st.warning(f"{username} を削除しました")
                                st.rerun()
                            else:
                                st.error("削除に失敗しました")
                    
                    # ✅ 更新ボタン（チーム変更対応 + セッション同期）
                    if available_teams and st.form_submit_button(f"💾 更新（{username}）", type="primary"):
                        if update_user_role(username, admin_flag, new_team):
                            success_msg = f"{username} を更新しました"
                            if new_team != team:
                                success_msg += f" (チーム: {team} → {new_team})"
                                if is_placeholder:
                                    success_msg += " ✅ プレースホルダーチームから移行完了"
                            
                            st.success(success_msg)
                            
                            # ✅ セッション同期：更新対象ユーザーがログイン中の場合
                            if st.session_state.get("username") == username:
                                st.session_state.team_name = new_team
                                st.session_state.is_admin = admin_flag
                                st.session_state.prompts = {}  # プロンプト再取得を強制
                                st.info("🔄 あなたのセッション情報を更新しました。プロンプトを再取得してください。")
                            
                            st.rerun()
                        else:
                            st.error("更新に失敗しました")
        else:
            st.info("登録されているユーザーがいません。")
            
        # ✅ チーム整合性チェック機能（プレースホルダー検出強化）
        st.markdown("---")
        st.subheader("🔧 整合性チェック")
        
        if st.button("🔍 全ユーザーのチーム状態をチェック"):
            check_results = []
            placeholder_count = 0
            
            for username, team, is_admin in users:
                is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
                
                if is_placeholder:
                    placeholder_count += 1
                    check_results.append({
                        "username": username,
                        "team": team,
                        "type": "placeholder",
                        "message": f"プレースホルダーチーム '{team}' を使用中"
                    })
                else:
                    from backend.prompt_loader import check_team_exists
                    team_status = check_team_exists(team)
                    
                    if not team_status["exists"] or not team_status["active"]:
                        check_results.append({
                            "username": username,
                            "team": team,
                            "type": "invalid",
                            "message": team_status["message"]
                        })
            
            # 結果表示
            problems = [r for r in check_results if r["type"] in ["placeholder", "invalid"]]
            
            if problems:
                st.error(f"🚨 {len(problems)}件の問題が見つかりました")
                
                # プレースホルダーチーム問題
                placeholder_problems = [p for p in problems if p["type"] == "placeholder"]
                if placeholder_problems:
                    st.warning(f"📋 プレースホルダーチーム使用: {len(placeholder_problems)}件")
                    for problem in placeholder_problems:
                        st.write(f"  - **{problem['username']}**: {problem['message']}")
                
                # 無効チーム問題
                invalid_problems = [p for p in problems if p["type"] == "invalid"]
                if invalid_problems:
                    st.error(f"❌ 無効チーム: {len(invalid_problems)}件")
                    for problem in invalid_problems:
                        st.write(f"  - **{problem['username']}**: {problem['message']}")
                        
                # 修正提案
                if placeholder_problems:
                    st.info("💡 **修正方法**: 上記のユーザーを実際のチームに変更してください。")
                    
            else:
                st.success("✅ 全ユーザーのチーム設定は正常です（プレースホルダーチーム使用なし）")
            
        # ✅ デバッグ情報（管理者のみ）
        with st.expander("🔧 デバッグ情報"):
            st.write(f"**利用可能なチーム（プレースホルダー除外）:** {available_teams}")
            st.write(f"**ユーザーDB:** {USER_DB_PATH}")
            st.write(f"**プロンプトDB:** {PROMPT_DB_PATH}")
            
            # 全ユーザーのチーム分布
            team_counts = {}
            for username, team, is_admin in users:
                team_counts[team] = team_counts.get(team, 0) + 1
            
            st.write("**チーム別ユーザー数:**")
            for team, count in sorted(team_counts.items()):
                is_placeholder = team in ['A_team', 'B_team', 'C_team', 'F_team']
                status = "🚨 プレースホルダー" if is_placeholder else "✅ 正常"
                st.write(f"  - {team}: {count}人 ({status})")
            
    except Exception as e:
        st.error(f"ユーザー一覧でエラーが発生しました: {e}")
        st.code(f"詳細エラー: {str(e)}")
        st.stop()

elif menu == "チームごとのプロンプトキー設定":
    st.subheader("🧩 チームごとのプロンプトキー設定")
    try:
        teams = fetch_all_team_prompts()
        
        # ✅ 有効なプロンプトキーを直接SQLで取得
        # conn = sqlite3.connect(PROMPT_DB_PATH)
        # cursor = conn.cursor()
        key_options = execute_query("SELECT prompt_key FROM team_master WHERE is_active = 1", fetch=True)
        if not key_options:
            st.info("有効なプロンプトキーがありません。まずはプロンプトキーを登録してください。")
        else:
            for team in teams:
                # ✅ 修正: 9列に対応
                team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team

                st.markdown(f"---\n### 🧩 {team_name}")
                st.caption(f"最終更新: {updated_at}")
                
                with st.form(f"form_update_key_{team_id}"):
                    st.caption(f"プロンプトキー（現在: `{prompt_key}`）")
                    current_index = key_options.index(prompt_key) if prompt_key in key_options else 0
                    new_key = st.selectbox("プロンプトキーを選択", key_options, index=current_index)
                    
                    if st.form_submit_button("更新する"):
                        update_team_prompt(
                            team_id, team_name, new_key,
                            text_prompt, audio_prompt, score_items, notes, is_active
                        )
                        st.success(f"{team_name} のプロンプトキーを `{new_key}` に更新しました")
                        st.rerun()
    except Exception as e:
        st.error(f"プロンプトキー設定でエラーが発生しました: {e}")

# ✅ 修正: 商談評価ログ登録セクションを完全削除し、閲覧専用の商談分析に統合
elif menu == "📊 商談振り返り・分析":
    st.subheader("📊 商談記録・分析ダッシュボード")
    
    # ✅ 注意書き：データソース説明
    st.info("💡 商談データは商談AIシステムから自動的に保存されます。こちらは閲覧・分析専用です。")
    
    # ✅ 強化されたフィルター設定
    with st.expander("🔍 検索・フィルター設定", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_username = st.selectbox(
                "👤 担当者でフィルター",
                options=["全員"] + [st.session_state.get("username", "")],
                help="特定の担当者の記録のみ表示"
            )
            
            status_filter = st.selectbox(
                "🚦 商談状態",
                options=["全て", "成約", "失注", "再商談", "未設定"],
                help="AIが分類した商談結果で絞り込み"
            )
        
        with col2:
            start_date = st.date_input(
                "📅 開始日",
                value=date.today().replace(day=1),
                help="この日付以降の記録を表示"
            )
            
            customer_filter = st.text_input(
                "👤 顧客名検索",
                placeholder="顧客名の一部を入力",
                help="顧客名で部分検索"
            )
        
        with col3:
            end_date = st.date_input(
                "📅 終了日",
                value=date.today(),
                help="この日付以前の記録を表示"
            )
            
            tag_filter = st.text_input(
                "🏷️ タグ検索",
                placeholder="タグで検索",
                help="AIが付与したタグで検索"
            )
        
        # ✅ スコア範囲フィルター
        score_range = st.slider(
            "📊 スコア範囲",
            min_value=0.0,
            max_value=100.0,
            value=(0.0, 100.0),
            help="AIが評価したスコア範囲で絞り込み"
        )
    
    # ✅ データ取得（フィルター強化版）
    try:
        username_filter = None if filter_username == "全員" else filter_username
        
        # ✅ 拡張版get_conversation_logs使用（引数調整）
        logs = get_conversation_logs(
            username=username_filter,
            start_date=start_date,
            end_date=end_date
            # ✅ 注意: 他のフィルター引数はget_conversation_logs関数の仕様に合わせて調整
        )
        
        if logs:
            st.success(f"✅ {len(logs)}件の商談記録が見つかりました")
            
            # ✅ 統計情報表示（拡張版）
            scores = [log[6] for log in logs if log[6] is not None]
            status_counts = {}
            for log in logs:
                status = log[9] if len(log) > 9 else "未設定"
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_score = sum(scores)/len(scores) if scores else 0
                st.metric("📊 平均スコア", f"{avg_score:.1f}点")
            with col2:
                st.metric("📝 商談数", f"{len(logs)}件")
            with col3:
                success_count = status_counts.get("成約", 0)
                total_completed = success_count + status_counts.get("失注", 0)
                success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0
                st.metric("📈 成約率", f"{success_rate:.1f}%")
            with col4:
                followup_count = status_counts.get("再商談", 0)
                st.metric("🟡 再商談", f"{followup_count}件")
            
            # ✅ ステータス分布表示
            if status_counts:
                st.markdown("### 🚦 商談状態の分布（AI分類）")
                status_cols = st.columns(len(status_counts))
                for i, (status, count) in enumerate(status_counts.items()):
                    with status_cols[i]:
                        badge = get_status_badge(status)
                        st.metric(badge, f"{count}件")
            
            st.markdown("---")
            
            # ✅ 商談ログ一覧表示（閲覧専用）
            st.subheader("📋 商談記録一覧（閲覧専用）")
            st.caption("📝 データは商談AIシステムから自動取得されています")
            
            # ✅ 表示件数制限とページング
            display_limit = st.selectbox("表示件数", [10, 20, 50, 100], index=1)
            
            for i, log in enumerate(logs[:display_limit]):
                log_id = log[0]
                log_date = log[1]
                log_time = log[2] if log[2] else "未設定"
                customer_name = log[3] or "（顧客名未記入）"
                conversation_text = log[4]
                gpt_feedback = log[5]
                score = log[6]
                username = log[7]
                created_at = log[8]
                status = log[9] if len(log) > 9 else "未設定"
                followup_date = log[10] if len(log) > 10 else None
                tags = log[11] if len(log) > 11 else ""
                
                status_badge = get_status_badge(status)
                title = f"📅 {log_date} {log_time} | {customer_name} | {status_badge} | 📊 {score or 'N/A'}点"
                
                with st.expander(title):
                    # ✅ 基本情報（2列レイアウト）
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.markdown("**📋 商談情報**")
                        st.write(f"📅 実施日時: {log_date} {log_time}")
                        st.write(f"👤 お客様: {customer_name}")
                        st.write(f"📊 AIスコア: {score}点" if score else "📊 AIスコア: 未評価")
                        st.write(f"🚦 AI分類: {status_badge}")
                    
                    with info_col2:
                        st.markdown("**🔍 記録情報**")
                        st.write(f"📝 担当者: {username}")
                        st.write(f"📅 登録日時: {created_at}")
                        if followup_date:
                            st.write(f"📅 フォロー予定: {followup_date}")
                        if tags:
                            st.write(f"🏷️ AIタグ: {tags}")
                    
                    # ✅ 会話内容表示
                    if conversation_text:
                        st.markdown("### 💬 会話内容・商談要約")
                        st.text_area(
                            "会話内容", 
                            conversation_text, 
                            height=150, 
                            disabled=True, 
                            key=f"conv_{log_id}",
                            help="商談AIシステムで記録された内容"
                        )
                    
                    # ✅ AI評価・フィードバック表示
                    if gpt_feedback:
                        st.markdown("### 🤖 AI評価・フィードバック")
                        st.text_area(
                            "AI評価", 
                            gpt_feedback, 
                            height=150, 
                            disabled=True, 
                            key=f"gpt_{log_id}",
                            help="AIが自動生成した評価とアドバイス"
                        )
                    
                    # ✅ 記録メタデータ（管理者のみ）
                    if st.session_state.get("is_admin", False):
                        with st.expander("🔧 記録詳細（管理者のみ）"):
                            st.code(f"""
記録ID: {log_id}
データソース: 商談AIシステム
登録タイムスタンプ: {created_at}
フィールド数: {len(log)}
                            """)
            
            # ✅ ページング情報
            if len(logs) > display_limit:
                st.info(f"📄 {display_limit}件を表示中（全{len(logs)}件）")
                st.write("💡 表示件数を変更するか、フィルター条件を調整してください")
        
        else:
            st.info("📭 指定した条件の商談記録は見つかりませんでした")
            st.markdown("""
            ### 💡 商談データについて
            
            - **データソース**: 商談AIシステムから自動連携
            - **更新頻度**: リアルタイム（商談終了後すぐに反映）
            - **AI分類**: 成約/失注/再商談は自動判定
            - **スコア**: AIが会話内容を分析して自動算出
            
            商談記録が表示されない場合は、商談AIシステムでの商談実施を確認してください。
            """)
    
    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
        st.code(f"詳細: {str(e)}")
        st.info("💡 商談AIシステムとの連携に問題がある可能性があります。システム管理者にお問い合わせください。")

# ✅ 既存のチーム別ダッシュボードとフォローアップ管理は変更なし
elif menu == "🏢 チーム別ダッシュボード":
    if not st.session_state.get("is_admin", False):
        st.error("❌ この機能は管理者のみ利用可能です")
        st.stop()
    
    st.subheader("🏢 チーム別パフォーマンスダッシュボード")
    st.info("💡 管理者向け: チーム全体の商談状況とKPIを確認できます")
    
    # ✅ 修正: 安全なチーム取得
    available_teams = get_all_teams_safe()
    selected_team = st.selectbox(
        "📊 分析対象チーム",
        options=["全社"] + available_teams,
        help="特定チームまたは全社の統計を表示"
    )
    
    # ✅ 統計取得
    team_filter = None if selected_team == "全社" else selected_team
    stats = get_team_dashboard_stats(team_filter)
    
    # ✅ KPI表示
    st.markdown("### 📊 主要KPI")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 総商談数",
            stats["total_logs"],
            help="登録されている商談の総数"
        )
    
    with col2:
        st.metric(
            "📊 平均スコア",
            f"{stats['avg_score']}点",
            help="全商談の平均評価スコア"
        )
    
    with col3:
        st.metric(
            "📈 成約率",
            f"{stats['success_rate']}%",
            help="成約/失注の割合"
        )
    
    with col4:
        st.metric(
            "🚀 今月の活動",
            f"{stats['recent_activity']}件",
            help="今月登録された商談数"
        )
    
    # ✅ ステータス分布
    if stats["status_breakdown"]:
        st.markdown("### 🚦 商談状態の分布")
        status_cols = st.columns(len(stats["status_breakdown"]))
        
        for i, (status, count) in enumerate(stats["status_breakdown"].items()):
            with status_cols[i]:
                badge = get_status_badge(status)
                percentage = (count / stats["total_logs"] * 100) if stats["total_logs"] > 0 else 0
                st.metric(
                    badge,
                    f"{count}件",
                    delta=f"{percentage:.1f}%"
                )
    
    # ✅ チーム別詳細ログ表示
    st.markdown("### 📋 最近のチーム活動")
    recent_logs = get_conversation_logs(
        start_date=date.today().replace(day=1),  # 今月分
        end_date=date.today()
    )
    
    if recent_logs:
        # 簡易表示版
        for log in recent_logs[:10]:  # 最新10件
            log_date = log[1]
            customer_name = log[3] or "（顧客名未記入）"
            score = log[6]
            username = log[7]
            status = log[9] if len(log) > 9 else "未設定"
            status_badge = get_status_badge(status)
            
            st.write(f"📅 {log_date} | 👤 {username} | 🏢 {customer_name} | {status_badge} | 📊 {score or 'N/A'}点")
    else:
        st.info("今月の活動記録がありません")

elif menu == "📅 フォローアップ管理":
    st.subheader("📅 フォローアップ管理")
    st.info("💡 再商談予定の管理とスケジュール確認ができます")
    
    # ✅ フィルター設定
    col1, col2 = st.columns(2)
    with col1:
        show_all_users = st.checkbox("全ユーザーの予定を表示", value=st.session_state.get("is_admin", False))
        range_days = st.slider("表示期間（日）", 7, 90, 30)
    
    with col2:
        if not show_all_users:
            filter_username = st.session_state.get("username")
            st.info(f"表示対象: {filter_username}")
        else:
            filter_username = None
            st.info("表示対象: 全ユーザー")
    
    # ✅ フォローアップ予定取得
    followup_logs = get_followup_schedule(
        username=filter_username,
        date_range_days=range_days
    )
    
    if followup_logs:
        st.success(f"✅ {len(followup_logs)}件のフォローアップ予定があります")
        
        # ✅ カレンダー風表示
        st.markdown("### 📅 フォローアップスケジュール")
        
        today = date.today()
        upcoming_soon = []
        later = []
        
        for log in followup_logs:
            followup_date_str = log[10] if len(log) > 10 else None
            if followup_date_str:
                try:
                    followup_date = datetime.strptime(followup_date_str, '%Y-%m-%d').date()
                    days_until = (followup_date - today).days
                    
                    if days_until <= 7:
                        upcoming_soon.append((log, days_until))
                    else:
                        later.append((log, days_until))
                except:
                    pass
        
        # ✅ 緊急度別表示
        if upcoming_soon:
            st.markdown("#### 🚨 今週中のフォローアップ")
            for log, days_until in sorted(upcoming_soon, key=lambda x: x[1]):
                log_date = log[1]
                customer_name = log[3] or "（顧客名未記入）"
                username = log[7]
                followup_date = log[10]
                
                urgency = "🔴 今日" if days_until == 0 else f"🟡 {days_until}日後"
                st.write(f"{urgency} | 📅 {followup_date} | 👤 {username} | 🏢 {customer_name} | (初回: {log_date})")
        
        if later:
            st.markdown("#### 📅 今後のフォローアップ")
            for log, days_until in sorted(later, key=lambda x: x[1])[:10]:
                log_date = log[1]
                customer_name = log[3] or "（顧客名未記入）"
                username = log[7]
                followup_date = log[10]
                
                st.write(f"📅 {followup_date} ({days_until}日後) | 👤 {username} | 🏢 {customer_name}")
    
    else:
        st.info("📭 現在フォローアップ予定はありません")
        st.write("💡 再商談ステータスで商談を登録すると、ここに表示されます")
