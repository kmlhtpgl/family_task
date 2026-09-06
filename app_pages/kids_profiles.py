from datetime import date, timedelta
from collections import OrderedDict

import streamlit as st

from utils.task_helpers import get_total_points_for_kid, get_monthly_points_for_kid, get_rank, get_overdue_task_count
from utils.book_helpers import get_finished_books, split_books_by_language
from utils.surah_helpers import (
    calculate_surah_progress,
    get_quran_surahs_in_progress,
    get_finished_quran_surahs,
    get_duas_in_progress,
    get_finished_duas,
)
from utils.achievement_helpers import get_kid_achievements
from utils.styles import avatar_image, achievement_badge
from utils.summary_helpers import compute_weekly_summary


def kids_profiles_page(data):
    st.header("👨‍👩‍👧‍👦 Kids Profiles")

    if not data["kids"]:
        st.info("No children added yet. Go to Admin to add a child.")
        return

    kid_options = {
        kid["name"]: kid["id"]
        for kid in data["kids"]
    }

    selected_name = st.selectbox(
        "Choose profile",
        list(kid_options.keys())
    )

    selected_kid = None

    for kid in data["kids"]:
        if kid["id"] == kid_options[selected_name]:
            selected_kid = kid
            break

    if selected_kid is None:
        st.error("Child profile not found.")
        return

    show_kid_profile(data, selected_kid)


def show_kid_profile(data, kid):
    col1, col2 = st.columns([1, 2])

    with col1:
        avatar_image(kid.get("photo_path"), width=150)

        st.subheader(kid["name"])
        st.write(f"Age: **{kid.get('age', 'Not entered')}**")

        total_points = get_total_points_for_kid(data, kid["id"])
        rank, icon = get_rank(total_points)
        st.markdown(
            f'<div class="metric-card"><h3>⭐ Total Points</h3><div class="value">{total_points}</div></div>',
            unsafe_allow_html=True
        )

        today = date.today()
        monthly_pts = get_monthly_points_for_kid(data, kid["id"], today.year, today.month)
        gbp = monthly_pts / 300
        st.markdown(
            f'<div style="padding:12px;background:rgba(255,215,0,0.1);border-radius:12px;border:1px solid #FFD700;margin-top:8px;">'
            f'<strong>💰 This Month:</strong> {monthly_pts} pts = £{gbp:.2f}'
            f'</div>',
            unsafe_allow_html=True
        )

        overdue = get_overdue_task_count(data, kid["id"], is_kid=True)
        if overdue > 0:
            st.markdown(
                f'<div style="padding:12px;background:rgba(255,0,0,0.08);border-radius:12px;border:1px solid #FF4444;margin-top:8px;">'
                f'<strong>⚠️ Overdue:</strong> {overdue} task(s) past due date'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown(
            f'<div style="text-align:center;padding:12px;background:linear-gradient(135deg,var(--primary),var(--accent));border-radius:12px;color:white;margin-top:8px;">'
            f'<span style="font-size:2.5em;">{icon}</span><br>'
            f'<strong style="font-size:1.2em;">{rank}</strong>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.divider()
        st.write("### 🏆 Achievements")

        achievements = get_kid_achievements(data, kid["id"])

        if achievements:
            for ach in achievements:
                achievement_badge(ach["icon"], ach["label"])
        else:
            st.caption("Complete tasks and read books to earn badges!")

    with col2:
        show_weekly_summary(data, kid)
        show_child_read_books(data, kid)
        show_child_quran(data, kid)


def show_child_read_books(data, kid):
    st.subheader("📚 Reading")

    finished_books = get_finished_books(data, kid["id"])
    english_books, turkish_books = split_books_by_language(finished_books)

    in_progress = [
        b for b in data["books"]
        if b.get("kid_id") == kid["id"]
        and b.get("status") != "Finished"
    ]

    if in_progress:
        st.write("### 📖 In Progress")

        for book in in_progress:
            progress = book.get("current_page", 0) / book["total_pages"] if book["total_pages"] > 0 else 0
            progress_pct = round(progress * 100)
            writer = f" — {book.get('writer', '')}" if book.get("writer") else ""

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span>{book["title"]}{writer}</span>'
                f'<span>{book["language"]}</span>'
                f'<span>{progress_pct}%</span>'
                f'</div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.write("### English Books")

    if english_books:
        for book in english_books:
            writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
            st.write(f"🇬🇧 {book['title']}{writer} ({book['total_pages']} pages)")
    else:
        st.caption("No English books finished yet.")

    st.write("### Turkish Books")

    if turkish_books:
        for book in turkish_books:
            writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
            st.write(f"🇹🇷 {book['title']}{writer} ({book['total_pages']} pages)")
    else:
        st.caption("No Turkish books finished yet.")


def show_child_quran(data, kid):
    st.subheader("📖 Quran Memorization")

    surahs = get_quran_surahs_in_progress(data, kid["id"])
    finished_surahs = get_finished_quran_surahs(data, kid["id"])
    duas = get_duas_in_progress(data, kid["id"])
    finished_duas = get_finished_duas(data, kid["id"])

    if surahs:
        st.write("**📖 Surahs in Progress**")

        for s in surahs:
            progress = calculate_surah_progress(s)
            progress_pct = round(progress * 100)

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span>{s["name"]}</span>'
                f'<span>{s.get("memorized_ayahs", 0)}/{s["total_ayahs"]} ({progress_pct}%)</span>'
                f'</div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    if duas:
        st.write("**🤲 Duas in Progress**")

        for d in duas:
            progress = calculate_surah_progress(d)
            progress_pct = round(progress * 100)

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span>{d["name"]}</span>'
                f'<span>{d.get("memorized_ayahs", 0)}/{d["total_ayahs"]} ({progress_pct}%)</span>'
                f'</div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    memorized = len(finished_surahs) + len(finished_duas)
    if memorized > 0:
        st.markdown(
            f'<div style="padding:8px;background:rgba(76,175,80,0.08);border-radius:8px;margin-top:8px;">'
            f'<strong>✨ Memorized:</strong> {len(finished_surahs)} surahs, {len(finished_duas)} duas'
            f'</div>',
            unsafe_allow_html=True
        )

    if not surahs and not duas and memorized == 0:
        st.caption("No surahs or duas assigned yet.")


def show_weekly_summary(data, kid):
    st.divider()
    st.subheader("📊 Weekly Summary")

    today = date.today()
    week_offset = st.session_state.get("kid_week_offset", 0)

    col_prev, col_week, col_next = st.columns([1, 5, 1])
    with col_prev:
        if st.button("◀", key="kid_prev_week", type="secondary", use_container_width=True):
            st.session_state.kid_week_offset = week_offset - 1
            st.rerun()
    with col_week:
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        sunday = monday + timedelta(days=6)
        label = f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
        if week_offset == 0:
            label = f"This Week · {label}"
        st.markdown(
            f"<div style='text-align:center;'><b style='color:var(--primary);'>{label}</b></div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("▶", key="kid_next_week", type="secondary", use_container_width=True):
            st.session_state.kid_week_offset = week_offset + 1
            st.rerun()

    summary = compute_weekly_summary(data, kid["id"], monday, sunday)

    st.markdown("**📚 Reading this week**")
    en_a, tr_a, read_tot = st.columns(3)
    with en_a:
        st.markdown(
            f'<div class="metric-card" style="text-align:center;"><div style="font-size:1.4em;">🇬🇧</div>'
            f'<div class="value">{summary["en_pages"]}</div><div class="label">English pages</div></div>',
            unsafe_allow_html=True
        )
    with tr_a:
        st.markdown(
            f'<div class="metric-card" style="text-align:center;"><div style="font-size:1.4em;">🇹🇷</div>'
            f'<div class="value">{summary["tr_pages"]}</div><div class="label">Turkish pages</div></div>',
            unsafe_allow_html=True
        )
    with read_tot:
        st.markdown(
            f'<div class="metric-card" style="text-align:center;"><div style="font-size:1.4em;">📖</div>'
            f'<div class="value">{summary["en_pages"] + summary["tr_pages"]}</div><div class="label">Total pages</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("**📋 Tasks this week**")

    agg = OrderedDict()
    for task in summary["done_tasks"]:
        title = task["title"]
        agg.setdefault(title, [0, 0])[0] += 1
        agg[title][1] += 1
    for task in summary["not_done_tasks"]:
        title = task["title"]
        agg.setdefault(title, [0, 0])[1] += 1

    total_done = sum(v[0] for v in agg.values())
    total_assigned = sum(v[1] for v in agg.values())

    if agg:
        for title, (done, total) in sorted(agg.items()):
            complete = done == total
            icon = "✅" if complete else "📋"
            color = "var(--success)" if complete else "var(--danger)"
            st.markdown(
                f'<div class="task-item">'
                f'<span>{icon} {title}</span>'
                f'<span style="color:{color};font-weight:700;">{done}/{total}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("No tasks assigned this week.")

    if total_assigned:
        st.markdown(
            f'<div style="padding:8px;background:rgba(16,185,129,0.08);border-radius:8px;margin-top:8px;">'
            f'<strong>🏁 {total_done} of {total_assigned} tasks done this week</strong>'
            f'</div>',
            unsafe_allow_html=True
        )
