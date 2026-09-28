from html import escape

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
    kid_ids = {k["id"] for k in data["kids"]}
    tasks = data["tasks"]

    missed = defaultdict(lambda: defaultdict(int))
    daily = {
        monday + timedelta(days=i): {"total": 0, "done": 0}
        for i in range(7)
    }

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
        daily[due_date]["total"] += 1
        if task.get("status") != "Done":
            missed[title][kid_id] += 1
        else:
            daily[due_date]["done"] += 1

    kids_sorted = sorted(data["kids"], key=lambda k: k["name"])
    missed_total = sum(missed[prayer].get(kid["id"], 0) for prayer in PRAYER_NAMES for kid in kids_sorted)
    total_prayers = sum(day["total"] for day in daily.values())
    completed_prayers = total_prayers - missed_total
    coverage = round((completed_prayers / total_prayers) * 100) if total_prayers else 100
    render_stat_strip([
        ("Missed", str(missed_total), "prayer tasks this week"),
        ("Children", str(len(kids_sorted)), "in this report"),
        ("Coverage", f"{coverage}%", "completed prayer tasks"),
    ])
    render_focus_panel("Weekly focus", "Prayer consistency", "A seven-day rhythm, with every missed entry visible", f"{coverage}%", "covered")

    strip = []
    for day, values in daily.items():
        ratio = round((values["done"] / values["total"]) * 100) if values["total"] else 100
        tone = "clear" if ratio == 100 else ("partial" if ratio >= 50 else "missed")
        strip.append(
            f'<div class="prayer-day prayer-day--{tone}"><span>{day.strftime("%a")}</span>'
            f'<strong>{day.day}</strong><small>{values["done"]}/{values["total"]}</small></div>'
        )
    st.markdown(
        '<div class="prayer-rhythm-heading"><span>THE RHYTHM</span><strong>Seven days at a glance</strong>'
        '<small>Completed / scheduled prayers</small></div>'
        f'<div class="prayer-rhythm">{"".join(strip)}</div>',
        unsafe_allow_html=True,
    )

    cells = []
    cells.append('<div class="prayer-heatmap prayer-heatmap--head"><div>Child</div>' + ''.join(f'<div>{escape(prayer)}</div>' for prayer in PRAYER_NAMES) + '<div>Total</div></div>')
    for kid in kids_sorted:
        total = sum(missed[prayer].get(kid["id"], 0) for prayer in PRAYER_NAMES)
        row = [f'<div class="prayer-heatmap"><div class="prayer-kid">{escape(kid["name"])}</div>']
        for prayer in PRAYER_NAMES:
            count = missed[prayer].get(kid["id"], 0)
            cls = "prayer-cell--missed" if count else "prayer-cell--clear"
            row.append(f'<div class="prayer-cell {cls}">{count if count else "OK"}</div>')
        row.append(f'<div class="prayer-total">{total}</div></div>')
        cells.append("".join(row))
    st.markdown(
        '<div class="prayer-heatmap-heading"><span>THE HEATMAP</span><strong>Where attention is needed</strong>'
        '<small>Each cell is the number of missed assignments this week</small></div>'
        + "".join(cells),
        unsafe_allow_html=True,
    )
