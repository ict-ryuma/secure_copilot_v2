import streamlit as st
from datetime import datetime, date, time
from backend.save_log import (get_followup_schedule)
def followup_management():
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