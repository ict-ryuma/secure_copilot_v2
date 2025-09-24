import streamlit as st

from backend.save_log import get_evaluations_admin
import json

from .adminFunctions import get_status_badge
from users.hyouka_view_process import replyProcess
from outcomes import outcome_array,display_outcome
from users.bunseki_functions import mi_hyouka_list,evaluation_action
from frontend.pagination import paginate
from shodan_search import shodan_search_filters

def shodan_bunseki():
    st.subheader("📊 商談記録・分析ダッシュボード")
    
    # ✅ 注意書き：データソース説明
    st.info("💡 商談データは商談AIシステムから自動的に保存されます。こちらは閲覧・分析専用です。")

    # ✅ 強化されたフィルター設定
    with st.expander("🔍 検索・フィルター設定", expanded=True):
        selected_user_id, status, kintone_id, team_id_filter, shodan_date_start, shodan_date_end, evaluation_status, phone_no, customer_number=shodan_search_filters(Type="admin")
    try:
        # ✅ データ取得（フィルター強化版）
        logs = get_evaluations_admin(
            member_id=selected_user_id,
            shodan_date_start=shodan_date_start,
            shodan_date_end=shodan_date_end,
            kintone_id=kintone_id,
            phone_no=phone_no,
            customer_number=customer_number,
            outcome=status,
            evaluation_status=evaluation_status,
            team_id=team_id_filter
            # score_range=score_range,
        )
        # st.write(logs)
        if logs:
            st.success(f"✅ {len(logs)}件の商談記録が見つかりました")
            # st.info("💡 表示されているのは「評価済み」の商談記録です。未評価の記録を表示するには、フィルター設定で「未評価」を選択してください。")
            status_counts = {}
            for log in logs:
                try:
                    outcome = int(log.get("outcome"))
                except (ValueError, TypeError):
                    outcome = None
                if outcome is not None:
                    status_counts[outcome] = status_counts.get(outcome, 0) + 1

            # --- KPIエリア ---
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📝 商談数", f"{len(logs)}件")

            with col2:
                success_count = status_counts.get(0, 0)  # 成約
                total_completed = success_count + status_counts.get(1, 0)  # 成約 + 未成約
                success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0
                st.metric("📈 成約率", f"{success_rate:.1f}%")

            with col3:
                followup_count = status_counts.get(2, 0)  # 再商談
                st.metric("🟡 再商談", f"{followup_count}件")

            # --- 商談状態の分布 ---
            if status_counts:
                st.markdown("### 🚦 商談状態の分布（AI分類）")

                # outcome_array のキー順で並び替え → 動的対応
                ordered = [(k, status_counts.get(k, 0)) for k in outcome_array.keys()]

                status_cols = st.columns(len(ordered))
                for i, (val, count) in enumerate(ordered):
                    with status_cols[i]:
                        badge = display_outcome(val)
                        st.metric(badge, f"{count}件")
            st.markdown("---")
            st.subheader("📋 商談記録一覧（閲覧専用）")
            st.caption("📝 データは商談AIシステムから自動取得されています")
            # ✅ 表示件数制限とページング
            page_datas, start_idx, _ = paginate(logs)
            # --- Display shodans ---
            for i, log in enumerate(page_datas, start=start_idx):
                # shodan_id = log['shodan_id']
                # log_date = log['created_at']
                # log_time = log[2] if log[2] else "未設定"
                member_name = log['username'] or "（顧客名未記入）"
                # score = log[8]
                created_at = log['created_at']
                # status = log[6] if len(log) > 6 else "未設定"
                # followup_date = log[5] if len(log) > 5 else None
                status_badge = display_outcome(log['outcome'])
                # formatted = log_date.strftime("%Y年%02m月%02d日 %H時%M分%S秒")
                formatted = log['shodan_date'].strftime("%Y年%02m月%02d日")
                title = f"{i+1} 📅 {formatted} | {member_name} | {status_badge}"
                # title = f" 📅 {formatted} | {member_name} | {status_badge}"
                # | 📊 {score or 'N/A'}点"
                if evaluation_status == 1:
                    with st.expander(title):
                        st.caption(f"商談日付: {log['shodan_date']} | Kintone ID: {log['kintone_id']} | 電話番号: {log['phone_no']}")
                        full_prompt = f"{log['text_prompt']}\n\n{log['shodan_text']}"
                        replyArr = {
                            "reply": json.loads(log['reply']),
                            "member_name": member_name,
                            "score_items": log['score_items'],
                            "audio_prompt": log['audio_prompt'],
                            "full_prompt": full_prompt,
                            "audio_file": None,
                            "audio_features": json.loads(log['audio_features']),
                            "audio_feedback": json.loads(log['audio_feedback']),
                        }

                        success, audio_features, audio_feedback = replyProcess(**replyArr)
                        # ✅ 基本情報（2列レイアウト）
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.markdown("**📋 商談情報**")
                            st.write(f"📅 実施日時: {created_at}")
                            st.write(f"👤 お客様: {member_name}")
                            # st.write(f"📊 AIスコア: {score}点" if score else "📊 AIスコア: 未評価")
                            st.write(f"🚦 AI分類: {status_badge}")
                        
                        with info_col2:
                            st.markdown("**🔍 記録情報**")
                            st.write(f"📝 担当者: {member_name}")
                            st.write(f"📅 登録日時: {created_at}")
                else:
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        mi_hyouka_list(title, log['shodan_id'], log['outcome'])
                    # with col2:
                    #     if st.button("❌", key=f"delete_{log['id']}"):
                    #         # 👉 do your delete logic here
                    #         # st.session_state["deleted_shodan"] = log['id']
                    #         st.success(f"商談 {title} を削除しました")
            if evaluation_status == 0:
                evaluation_action(page_datas)
                # st.write(f"page_datas: {len(page_datas)}")
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
# =============================OLD CODE=============================
    # ✅ データ取得（フィルター強化版）
    # try:
    #     username_filter = None if filter_username == "全員" else filter_username
        
    #     # ✅ 拡張版get_conversation_logs使用（引数調整）
    #     logs = get_conversation_logs(
    #         username=username_filter,
    #         start_date=start_date,
    #         end_date=end_date
    #         # ✅ 注意: 他のフィルター引数はget_conversation_logs関数の仕様に合わせて調整
    #     )
        
    #     if logs:
    #         st.success(f"✅ {len(logs)}件の商談記録が見つかりました")
            
            # # ✅ 統計情報表示（拡張版）
            # scores = [log[6] for log in logs if log[6] is not None]
            # status_counts = {}
            # for log in logs:
            #     status = log[9] if len(log) > 9 else "未設定"
            #     status_counts[status] = status_counts.get(status, 0) + 1
            
            # col1, col2, col3, col4 = st.columns(4)
            # with col1:
            #     avg_score = sum(scores)/len(scores) if scores else 0
            #     st.metric("📊 平均スコア", f"{avg_score:.1f}点")
            # with col2:
            #     st.metric("📝 商談数", f"{len(logs)}件")
            # with col3:
            #     success_count = status_counts.get("成約", 0)
            #     total_completed = success_count + status_counts.get("失注", 0)
            #     success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0
            #     st.metric("📈 成約率", f"{success_rate:.1f}%")
            # with col4:
            #     followup_count = status_counts.get("再商談", 0)
            #     st.metric("🟡 再商談", f"{followup_count}件")
            
            # # ✅ ステータス分布表示
            # if status_counts:
            #     st.markdown("### 🚦 商談状態の分布（AI分類）")
            #     status_cols = st.columns(len(status_counts))
            #     for i, (status, count) in enumerate(status_counts.items()):
            #         with status_cols[i]:
            #             badge = get_status_badge(status)
            #             st.metric(badge, f"{count}件")
            
            # st.markdown("---")
            
            # # ✅ 商談ログ一覧表示（閲覧専用）
            # st.subheader("📋 商談記録一覧（閲覧専用）")
            # st.caption("📝 データは商談AIシステムから自動取得されています")
            
            # # ✅ 表示件数制限とページング
            # display_limit = st.selectbox("表示件数", [10, 20, 50, 100], index=1)
            
            # for i, log in enumerate(logs[:display_limit]):
            #     log_id = log[0]
            #     log_date = log[1]
            #     log_time = log[2] if log[2] else "未設定"
            #     customer_name = log[3] or "（顧客名未記入）"
            #     conversation_text = log[4]
            #     gpt_feedback = log[5]
            #     score = log[6]
            #     username = log[7]
            #     created_at = log[8]
            #     status = log[9] if len(log) > 9 else "未設定"
            #     followup_date = log[10] if len(log) > 10 else None
            #     tags = log[11] if len(log) > 11 else ""
                
            #     status_badge = get_status_badge(status)
            #     title = f"📅 {log_date} {log_time} | {customer_name} | {status_badge} | 📊 {score or 'N/A'}点"
                
            #     with st.expander(title):
            #         # ✅ 基本情報（2列レイアウト）
            #         info_col1, info_col2 = st.columns(2)
            #         with info_col1:
            #             st.markdown("**📋 商談情報**")
            #             st.write(f"📅 実施日時: {log_date} {log_time}")
            #             st.write(f"👤 お客様: {customer_name}")
            #             st.write(f"📊 AIスコア: {score}点" if score else "📊 AIスコア: 未評価")
            #             st.write(f"🚦 AI分類: {status_badge}")
                    
            #         with info_col2:
            #             st.markdown("**🔍 記録情報**")
            #             st.write(f"📝 担当者: {username}")
            #             st.write(f"📅 登録日時: {created_at}")
            #             if followup_date:
            #                 st.write(f"📅 フォロー予定: {followup_date}")
            #             if tags:
            #                 st.write(f"🏷️ AIタグ: {tags}")
                    
            #         # ✅ 会話内容表示
            #         if conversation_text:
            #             st.markdown("### 💬 会話内容・商談要約")
            #             st.text_area(
            #                 "会話内容", 
            #                 conversation_text, 
            #                 height=150, 
            #                 disabled=True, 
            #                 key=f"conv_{log_id}",
            #                 help="商談AIシステムで記録された内容"
            #             )
                    
            #         # ✅ AI評価・フィードバック表示
            #         if gpt_feedback:
            #             st.markdown("### 🤖 AI評価・フィードバック")
            #             st.text_area(
            #                 "AI評価", 
            #                 gpt_feedback, 
            #                 height=150, 
            #                 disabled=True, 
            #                 key=f"gpt_{log_id}",
            #                 help="AIが自動生成した評価とアドバイス"
            #             )
                    
            #         # ✅ 記録メタデータ（管理者のみ）
            #         if st.session_state.get("is_admin", False):
            #             with st.expander("🔧 記録詳細（管理者のみ）"):
            #                 st.code(f"""
            #                     記録ID: {log_id}
            #                     データソース: 商談AIシステム
            #                     登録タイムスタンプ: {created_at}
            #                     フィールド数: {len(log)}
            #                 """)
            
            # # ✅ ページング情報
            # if len(logs) > display_limit:
            #     st.info(f"📄 {display_limit}件を表示中（全{len(logs)}件）")
            #     st.write("💡 表示件数を変更するか、フィルター条件を調整してください")
        
        # else:
        #     st.info("📭 指定した条件の商談記録は見つかりませんでした")
        #     st.markdown("""
        #     ### 💡 商談データについて
            
        #     - **データソース**: 商談AIシステムから自動連携
        #     - **更新頻度**: リアルタイム（商談終了後すぐに反映）
        #     - **AI分類**: 成約/失注/再商談は自動判定
        #     - **スコア**: AIが会話内容を分析して自動算出
            
        #     商談記録が表示されない場合は、商談AIシステムでの商談実施を確認してください。
        #     """)
    
    # except Exception as e:
    #     st.error(f"❌ データ取得エラー: {e}")
    #     st.code(f"詳細: {str(e)}")
    #     st.info("💡 商談AIシステムとの連携に問題がある可能性があります。システム管理者にお問い合わせください。")