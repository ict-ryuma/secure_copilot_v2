import streamlit as st
from .adminFunctions import get_all_teams_safe, get_status_badge
from datetime import datetime, date, time
from backend.save_log import (
    get_conversation_logs,get_team_dashboard_stats
)
def tpdb(): 
    # Team Performance Dashboard

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