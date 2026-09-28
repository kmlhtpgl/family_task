import streamlit as st
from utils.page_chrome import render_focus_panel, render_page_header, render_stat_strip
from datetime import date, timedelta
from collections import defaultdict

PRAYER_NAMES = ["Fecr", "Zuhr", "Asr", "Maghrib", "Isha"]


def prayer_page(data):
    render_page_header("Prayer", "A weekly view of consistency and missed prayers.")

    if not data["kids"]:
        st.info("No children added yet.")
        return

    week_offset = st.session_state.get("prayer_week_offset", 0)
    col_prev, col_week, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ Prev"):
            st.session_state.prayer_week_offset = week_offset - 1
            st.rerun()
    with col_week:
        today = date.today()
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        sunday = monday + timedelta(days=6)
        week_range = f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
        st.markdown(
            f'<div class="week-heading">{week_range}</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next ▶"):
            st.session_state.prayer_week_offset = week_offset + 1
            st.rerun()

    monday = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)
    week_dates = {monday + timedelta(days=i) for i in range(7)}

    kid_ids = {k["id"] for k in data["kids"]}
    tasks = data["tasks"]

    missed = defaultdict(lambda: defaultdict(int))

    for task in tasks:
        kid_id = task.get("kid_id")
        if kid_id is None or kid_id not in kid_ids:
            continue
        title = task.get("title", "")
        if title not in PRAYER_NAMES:
            continue
        due = task.get("due_date")
        if not due:
            continue
        try:
            due_date = date.fromisoformat(due)
        except (ValueError, TypeError):
            continue
        if not (monday <= due_date <= sunday):
            continue
        if task.get("status") != "Done":
            missed[title][kid_id] += 1

    kids_sorted = sorted(data["kids"], key=lambda k: k["name"])
    missed_total = sum(missed[prayer].get(kid["id"], 0) for prayer in PRAYER_NAMES for kid in kids_sorted)
    render_stat_strip([
        ("Missed", str(missed_total), "prayer tasks this week"),
        ("Children", str(len(kids_sorted)), "in this report"),
        ("Coverage", f"{max(0, 100 - missed_total)}%", "simple consistency view"),
    ])
    render_focus_panel("Weekly focus", "Prayer consistency", "Missed prayers across the selected week", str(missed_total), "missed entries")

    header_cols = st.columns([2] + [1] * len(kids_sorted))
    header_cols[0].markdown('<div class="th">Prayer</div>', unsafe_allow_html=True)
    for i, kid in enumerate(kids_sorted):
        header_cols[i + 1].markdown(
            f'<div class="th center">{kid["name"]}</div>', unsafe_allow_html=True
        )

    for prayer in PRAYER_NAMES:
        cols = st.columns([2] + [1] * len(kids_sorted))
        cols[0].write(prayer)
        for i, kid in enumerate(kids_sorted):
            count = missed[prayer].get(kid["id"], 0)
            tone = "count--missed" if count > 0 else "count--ok"
            cols[i + 1].markdown(
                f'<div class="count center {tone}">{count}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    total_cols = st.columns([2] + [1] * len(kids_sorted))
    total_cols[0].markdown('<div class="th">Total</div>', unsafe_allow_html=True)
    for i, kid in enumerate(kids_sorted):
        total = sum(missed[p][kid["id"]] for p in PRAYER_NAMES)
        total_cols[i + 1].markdown(
            f'<div class="count count--total center">{total}</div>',
            unsafe_allow_html=True,
        )
