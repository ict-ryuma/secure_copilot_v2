from backend.auth import get_all_users
from backend.teams import get_teams
import streamlit as st
from datetime import datetime, date, time
from outcomes import outcome_array,display_outcome

def shodan_search_filters(Type="user"):
    col1, col2, col3 = st.columns(3)
    selected_user_id = None
    selected_team = None
    phone_no=None
    evaluation_status=None
    team_id_filter=None
    if Type=="admin":
        users = get_all_users()
        team_options = get_teams(only_active=1)
        team_options_with_placeholder = [(-1, "全て")] + team_options
        # st.write(team_options)
        user_options = [(user['user_id'], user['username']) for user in users]
        # Add "全員" option with id None
        user_options = [(None, "全員")] + user_options
        # Show selectbox displaying username
        selected_user = col1.selectbox(
            "👤 担当者でフィルター",
            options=user_options,
            format_func=lambda x: x[1],  # show username
        )
        selected_user_id = selected_user[0]

        selected_team = col2.selectbox(
            "チームを選択",
            options=team_options_with_placeholder,
            format_func=lambda team: team[1],  # Display team_name
            help="登録済みのアクティブチームのみ選択可能です（プレースホルダーチーム除外）"
        )
        team_id_filter = None if selected_team[0] == -1 else selected_team[0]

        phone_no = col2.text_input(
            "📞 エージェント電話番号検索",
            placeholder="電話番号で検索",
            help="AIが付与した電話番号で検索",
            value=None
        )
        evaluation_options = {
            1: "✅ 評価済み",
            0: "❌ 未評価",
        }

        evaluation_status = col3.selectbox(
            "📝 評価状態",
            options=list(evaluation_options.keys()),
            index=0,  # デフォルトを「評価済み」に
            help="商談の評価状態で絞り込み",
            format_func=lambda val: evaluation_options[val],
        )

        customer_number = col3.text_input(
            "📞 顧客電話番号検索",
            placeholder="顧客電話番号で検索",
            help="AIが付与した顧客電話番号で検索",
            value=None
        )
    
    

    status = col1.selectbox(
        "🚦 商談状態",
        options=[-1] + list(outcome_array.keys()),
        help="AIが分類した商談結果で絞り込み",
        format_func=lambda val: "全て" if val == -1 else display_outcome(val),
    )
    kintone_id = col1.text_input(
        "Kintone ID検索",
        placeholder="Kintone IDの一部を入力",
        help="Kintone IDで部分検索",
        value=None
    )
    kintone_id = None if kintone_id == "" else kintone_id
    # st.info(f"選択チーム: {selected_team}")
    shodan_date_start = col2.date_input(
        "📅 開始日",
        value=date.today().replace(day=1),
        help="この日付以降の記録を表示",
        key="shodan_date_input_start"
    )
    shodan_date_end = col3.date_input(
        "📅 終了日",
        value=date.today(),
        help="この日付以前の記録を表示",
        key="shodan_date_input_end"
    )

    if Type=="user":
        customer_number = col2.text_input(
            "📞 顧客電話番号検索",
            placeholder="顧客電話番号で検索",
            help="AIが付与した顧客電話番号で検索",
            value=None
        )
    customer_number = None if customer_number == "" else customer_number
        # ✅ スコア範囲フィルター
    # score_range = st.slider(
    #     "📊 スコア範囲",
    #     min_value=0.0,
    #     max_value=100.0,
    #     value=(0.0, 100.0),
    #     help="AIが評価したスコア範囲で絞り込み"
    # )

    status_filter = None if status == -1 else status
    

    return selected_user_id, status_filter, kintone_id, team_id_filter, shodan_date_start, shodan_date_end, evaluation_status, phone_no, customer_number