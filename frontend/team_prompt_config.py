import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend import db_team_master, db_prompt_key_master

st.set_page_config(page_title="チーム × プロンプトキー設定", page_icon="🧩")

st.title("🧩 チームごとのプロンプトキー設定")
st.info("🔒 **注意:** このページではプロンプトキーの変更のみ可能です。新規チーム作成は管理者ダッシュボードで行ってください。")

# ✅ 統一されたチーム取得・検証
def get_valid_teams_with_validation():
    """有効なチームのみを取得（包括的検証付き）"""
    try:
        from backend.auth import get_all_teams_safe, validate_team_comprehensive
        
        # 統一関数でチーム取得
        safe_teams = get_all_teams_safe()
        
        if not safe_teams:
            return [], "利用可能なアクティブチームがありません"
        
        # 各チームの包括検証
        validated_teams = []
        validation_warnings = []
        
        for team_name in safe_teams:
            validation = validate_team_comprehensive(team_name)
            if validation["valid"]:
                validated_teams.append(team_name)
            else:
                validation_warnings.append(f"- {team_name}: {validation['message']}")
        
        warning_msg = None
        if validation_warnings:
            warning_msg = f"一部チームに問題があります:\n" + "\n".join(validation_warnings)
        
        return validated_teams, warning_msg
        
    except Exception as e:
        return [], f"チーム取得エラー: {str(e)}"

# --- データ取得・検証 ---
try:
    validated_teams, validation_warning = get_valid_teams_with_validation()
    prompt_keys = db_prompt_key_master.get_active_prompt_keys()
    
    # ✅ 検証結果の表示
    if validation_warning and "利用可能な" not in validation_warning:
        st.warning(f"⚠️ {validation_warning}")
    
    if not validated_teams:
        st.error("⚠️ 現在利用可能なアクティブチームがありません。")
        st.info("💡 管理者ダッシュボードの「チーム管理」でチームを作成・有効化してください。")
        
        with st.expander("🔧 チーム設定の手順"):
            st.write("1. 管理者ダッシュボードにアクセス")
            st.write("2. 「チーム管理」メニューを選択")
            st.write("3. 「チーム追加フォーム」で新しいチームを作成")
            st.write("4. チームが「有効」状態になっていることを確認")
            st.write("5. テキスト・音声プロンプト、スコア項目を設定")
            st.write("6. このページに戻ってプロンプトキー設定")
        
        st.stop()
    
    # ✅ チーム別プロンプトキー設定
    st.markdown("### 🏷️ 有効チーム一覧")
    
    # team_masterから詳細情報を取得
    teams_data = db_team_master.fetch_all_team_prompts()
    
    # 検証済みチームのみフィルタリング
    validated_teams_data = []
    for team_data in teams_data:
        team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team_data
        if team_name in validated_teams:
            validated_teams_data.append(team_data)
    
    if not validated_teams_data:
        st.warning("検証済みチームのデータが取得できませんでした。")
        st.stop()
    
    for team_data in validated_teams_data:
        team_id, team_name, prompt_key, text_prompt, audio_prompt, score_items, notes, is_active, updated_at = team_data
        
        st.markdown(f"### 🏷️ {team_name}")
        st.caption(f"最終更新: {updated_at}")
        
        # ✅ チーム検証状態表示
        from backend.auth import validate_team_comprehensive
        validation = validate_team_comprehensive(team_name)
        
        if validation["valid"]:
            st.success("✅ 設定完了 - 正常に利用可能")
        else:
            st.error(f"❌ 設定に問題があります: {validation['message']}")
            if "suggestions" in validation:
                st.write("**対処法:**")
                for suggestion in validation["suggestions"]:
                    st.write(f"- {suggestion}")
            continue  # 問題があるチームはスキップ
        
        col1, col2 = st.columns([5, 2])

        with col1:
            if prompt_keys:
                new_key = st.selectbox(
                    f"プロンプトキー（現在: `{prompt_key}`）",
                    options=prompt_keys,
                    index=prompt_keys.index(prompt_key) if prompt_key in prompt_keys else 0,
                    key=f"key_select_{team_id}",
                    help="このチームで使用するプロンプトキーを選択してください"
                )
            else:
                st.warning("利用可能なプロンプトキーがありません")
                new_key = prompt_key

        with col2:
            if prompt_keys and st.button("🔄 更新する", key=f"update_{team_id}"):
                try:
                    # チーム情報を再取得して更新
                    current = db_team_master.fetch_team_prompt_by_id(team_id)
                    if current:
                        # ✅ 修正: 9列に対応
                        _, _, _, text_prompt, audio_prompt, score_items, notes, is_active, _ = current
                        
                        db_team_master.update_team_prompt(
                            team_id=team_id,
                            name=team_name,  # ✅ チーム名は変更しない
                            key=new_key,
                            text_prompt=text_prompt,
                            audio_prompt=audio_prompt,
                            score_items=score_items,
                            notes=notes,
                            is_active=is_active
                        )
                        st.success(f"✅ {team_name} のプロンプトキーを '{new_key}' に更新しました")
                        st.rerun()
                    else:
                        st.error("❌ チーム情報の取得に失敗しました")
                        
                except Exception as e:
                    st.error(f"❌ 更新エラー: {str(e)}")

        st.markdown("---")

    # ✅ セキュリティ情報
    st.markdown("---")
    st.info("💡 **新しいチームの作成**: 管理者ダッシュボードの「チーム管理」で行ってください")
    st.info("🔒 **セキュリティポリシー**: このページでは既存チームのプロンプトキー変更のみ可能です")
    
    # ✅ 管理者向けリンク
    st.markdown("### 🛠️ 管理者向け")
    st.markdown("- [管理者ダッシュボード](http://localhost:8501) でチーム管理")
    st.markdown("- [プロンプト設定](http://localhost:8501) でテキスト・音声プロンプト編集")

except Exception as e:
    st.error(f"❌ システムエラー: {str(e)}")
    st.code(f"詳細: {str(e)}")
    
    with st.expander("🔧 トラブルシューティング"):
        st.write("1. 管理者ダッシュボードでチーム設定を確認")
        st.write("2. データベース接続を確認")
        st.write("3. team_masterテーブルの整合性を確認")
        st.write("4. システム管理者にお問い合わせ")
