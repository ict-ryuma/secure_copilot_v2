import streamlit as st
from datetime import datetime, date, time
from backend.save_log import get_evaluations_admin
from backend.auth import get_all_users
import json

from .adminFunctions import get_status_badge
from bunseki_functions import replyProcess

def shodanBunseki():
    st.subheader("📊 商談記録・分析ダッシュボード")
    
    # ✅ 注意書き：データソース説明
    st.info("💡 商談データは商談AIシステムから自動的に保存されます。こちらは閲覧・分析専用です。")

    # ✅ 強化されたフィルター設定
    with st.expander("🔍 検索・フィルター設定", expanded=True):
        users = get_all_users()
        user_options = [(user["id"], user["username"]) for user in users]
        # Add "全員" option with id None
        user_options = [(None, "全員")] + user_options
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Show selectbox displaying username
            selected_user = st.selectbox(
                "👤 担当者でフィルター",
                options=user_options,
                format_func=lambda x: x[1],  # show username
            )
            selected_user_id = selected_user[0]
            
            status = st.selectbox(
                "🚦 商談状態",
                options=["全て", "成約", "失注", "再商談", "未設定"],
                help="AIが分類した商談結果で絞り込み"
            )
        
        with col2:
            shodan_date_start = st.date_input(
                "📅 開始日",
                value=date.today().replace(day=1),
                help="この日付以降の記録を表示",
                key="shodan_date_input_start"
            )
            
            # customer_filter = st.text_input(
            #     "👤 顧客名検索",
            #     placeholder="顧客名の一部を入力",
            #     help="顧客名で部分検索"
            # )
            kintone_id = st.text_input(
                "Kintone ID検索",
                placeholder="Kintone IDの一部を入力",
                help="Kintone IDで部分検索"
            )
        
        with col3:
            shodan_date_end = st.date_input(
                "📅 終了日",
                value=date.today(),
                help="この日付以前の記録を表示",
                key="shodan_date_input_end"
            )

            # st.date_input("商談日付", key="shodan_date_input", value=None, help="商談の日付を入力してください（例：2023-01-01）")
            
            # tag_filter = st.text_input(
            #     "🏷️ タグ検索",
            #     placeholder="タグで検索",
            #     help="AIが付与したタグで検索"
            # )
            phone_no = st.text_input(
                "📞 電話番号検索",
                placeholder="電話番号で検索",
                help="AIが付与した電話番号で検索"
            )
        
        # ✅ スコア範囲フィルター
        # score_range = st.slider(
        #     "📊 スコア範囲",
        #     min_value=0.0,
        #     max_value=100.0,
        #     value=(0.0, 100.0),
        #     help="AIが評価したスコア範囲で絞り込み"
        # )
    

    try:
        # ✅ データ取得（フィルター強化版）
        status_filter = None if status == "全て" else status
        # st.success(f"✅ filter_username: {selected_user_id}. status_filter: {status_filter}, start_date: {shodan_date_start}, end_date: {shodan_date_end}, kintone_id: {kintone_id}, phone_no: {phone_no}, score_range: {score_range}")
        logs = get_evaluations_admin(
            selected_user_id,
            shodan_date_start,
            shodan_date_end,
            kintone_id,
            phone_no,
            # score_range,
            status_filter
        )
        if logs:
            st.success(f"✅ {len(logs)}件の商談記録が見つかりました")
            status_counts = {}
            for log in logs:
                status = log[6] if len(log) > 6 else "未設定"
                status_counts[status] = status_counts.get(status, 0) + 1
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📝 商談数", f"{len(logs)}件")
            with col2:
                success_count = status_counts.get("成約", 0)
                total_completed = success_count + status_counts.get("失注", 0)
                success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0
                st.metric("📈 成約率", f"{success_rate:.1f}%")
            with col3:
                followup_count = status_counts.get("再商談", 0)
                st.metric("🟡 再商談", f"{followup_count}件")

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
                log_date = log[15]
                # log_time = log[2] if log[2] else "未設定"
                customer_name = log[2] or "（顧客名未記入）"
                # conversation_text = log[10]
                # gpt_feedback = log[13]
                # score = log[8]
                # username = log[2]
                created_at = log[15]
                status = log[6] if len(log) > 6 else "未設定"
                # followup_date = log[5] if len(log) > 5 else None
                # tags = log[11] if len(log) > 11 else ""
                
                status_badge = get_status_badge(status)
                # dt = datetime.strptime(log_date, "%Y-%m-%d %H:%M:%S")
                formatted = log_date.strftime("%Y年%02m月%02d日 %H時%M分%S秒")
                title = f"{i+1} 📅 {formatted} | {customer_name} | {status_badge}"
                # | 📊 {score or 'N/A'}点"
                
                with st.expander(title):
                    replyProcess(json.loads(log[7]),json.loads(log[8]), log[2],kintone_id,phone_no, log[5], log[9],log[10],log[11],json.loads(log[12]),json.loads(log[13]))
                    # ✅ 基本情報（2列レイアウト）
                    # info_col1, info_col2 = st.columns(2)
                    # with info_col1:
                    #     st.markdown("**📋 商談情報**")
                    #     st.write(f"📅 実施日時: {log_date}")
                    #     st.write(f"👤 お客様: {customer_name}")
                    #     st.write(f"📊 AIスコア: {score}点" if score else "📊 AIスコア: 未評価")
                    #     st.write(f"🚦 AI分類: {status_badge}")
                    
                    # with info_col2:
                    #     st.markdown("**🔍 記録情報**")
                    #     st.write(f"📝 担当者: {username}")
                    #     st.write(f"📅 登録日時: {created_at}")
                    #     if followup_date:
                    #         st.write(f"📅 フォロー予定: {followup_date}")
                    #     # if tags:
                    #     #     st.write(f"🏷️ AIタグ: {tags}")
                    
                    # # ✅ 会話内容表示
                    # if conversation_text:
                    #     st.markdown("### 💬 会話内容・商談要約")
                    #     st.text_area(
                    #         "会話内容", 
                    #         conversation_text, 
                    #         height=150, 
                    #         disabled=True, 
                    #         key=f"conv_{log_id}",
                    #         help="商談AIシステムで記録された内容"
                    #     )
                    
                    # # ✅ AI評価・フィードバック表示
                    # if gpt_feedback:
                    #     st.markdown("### 🤖 AI評価・フィードバック")
                    #     st.text_area(
                    #         "AI評価", 
                    #         gpt_feedback, 
                    #         height=150, 
                    #         disabled=True, 
                    #         key=f"gpt_{log_id}",
                    #         help="AIが自動生成した評価とアドバイス"
                    #     )
                    
                # ✅ 記録メタデータ（管理者のみ）
                if st.session_state.get("is_admin", False):
                    with st.expander("🔧 記録詳細（管理者のみ）"):
                        st.code(f"""
                            記録ID: {log_id}
                            データソース: 商談AIシステム
                            登録タイムスタンプ: {created_at}
                            フィールド数: {len(logs)}
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