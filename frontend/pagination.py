import streamlit as st
import math

def paginate(datas):
    # --- Init persistent state ---
    st.session_state.setdefault("items_per_page", 5)
    st.session_state.setdefault("current_page", 1)

    # --- Items per page select box ---
    items_per_page_options = [3, 5, 10, 20]
    items_per_page = st.selectbox(
        "1ページあたりの件数",
        items_per_page_options,
        index=items_per_page_options.index(st.session_state.items_per_page),
        key="items_per_page_select",
    )

    # If changed, reset to page 1 and rerun for consistent UI
    if items_per_page != st.session_state.items_per_page:
        st.session_state.items_per_page = items_per_page
        st.session_state.current_page = 1
        st.rerun()

    total_items = len(datas)
    total_pages = max(1, math.ceil(total_items / st.session_state.items_per_page))

    # --- Clamp BEFORE rendering buttons ---
    st.session_state.current_page = int(
        min(max(st.session_state.current_page, 1), total_pages)
    )

    # --- Page navigation ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        prev_disabled = st.session_state.current_page <= 1
        if st.button("⬅ 前へ", disabled=prev_disabled, key="prev_btn"):
            if st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()

    with col3:
        next_disabled = st.session_state.current_page >= total_pages
        if st.button("次へ ➡", disabled=next_disabled, key="next_btn"):
            if st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()

    st.write(f"ページ {st.session_state.current_page} / {total_pages}")

    # --- Slice data for current page ---
    start_idx = (st.session_state.current_page - 1) * st.session_state.items_per_page
    end_idx = min(start_idx + st.session_state.items_per_page, total_items)
    page_datas = datas[start_idx:end_idx]

    return page_datas, start_idx, end_idx

