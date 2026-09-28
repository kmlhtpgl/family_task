from datetime import date, timedelta
from collections import OrderedDict

import streamlit as st

from utils.task_helpers import get_total_points_for_kid, get_monthly_points_for_kid, get_weekly_points_for_kid, get_rank
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
from utils.page_chrome import render_page_header, render_profile_identity, render_stat_strip


def kids_profiles_page(data):
    render_page_header("Kids", "See each child’s momentum, commitments, and wins.")

    completed = sum(1 for task in data.get("tasks", []) if task.get("status") == "Done")
    reading = sum(1 for book in data.get("books", []) if book.get("kid_id") is not None)
    render_stat_strip([
        ("People", str(len(data.get("kids", []))), "kid profiles"),
        ("Reading", str(reading), "books in the household"),
        ("Completed", str(completed), "all-time completions"),
    ])

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
    total_points = get_total_points_for_kid(data, kid["id"])
    rank, _ = get_rank(total_points)
    today = date.today()
    monthly_pts = get_monthly_points_for_kid(data, kid["id"], today.year, today.month)

    hero_left, hero_right = st.columns([1, 4])
    with hero_left:
        avatar_image(kid.get("photo_path"), width=160)
    with hero_right:
        render_profile_identity(kid["name"], "Kid profile", f"Age {kid.get('age', 'not entered')}", rank)

    render_stat_strip([
        ("Total points", str(total_points), "all-time progress"),
        ("This month", str(monthly_pts), "points in the current month"),
        ("Weekly pace", str(get_weekly_points_for_kid(data, kid["id"])), "points earned this week"),
    ])

    show_weekly_summary(data, kid)
    learning_left, learning_right = st.columns(2)
    with learning_left:
        show_child_read_books(data, kid)
    with learning_right:
        show_child_quran(data, kid)

    achievements = get_kid_achievements(data, kid["id"])
    st.markdown('<div class="profile-achievement-deck"><div class="route-section-label">Achievements</div>', unsafe_allow_html=True)
    if achievements:
        for ach in achievements:
            achievement_badge(ach["icon"], ach["label"])
    else:
        st.caption("Complete tasks and read books to earn badges!")
    st.markdown('</div>', unsafe_allow_html=True)


def show_child_read_books(data, kid):
    st.markdown('<div class="profile-module-title">Reading studio</div><div class="profile-module-subtitle">Books in motion and finished shelves</div>', unsafe_allow_html=True)

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
                f'<div class="row">'
                f'<span class="row-title">{book["title"]}{writer}</span>'
                f'<span class="row-meta">{book["language"]}</span>'
                f'<span class="row-meta num">{progress_pct}%</span>'
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
    st.markdown('<div class="profile-module-title">Quran studio</div><div class="profile-module-subtitle">Surahs and duas in practice</div>', unsafe_allow_html=True)

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
                f'<div class="row">'
                f'<span class="row-title">{s["name"]}</span>'
                f'<span class="row-meta num">{s.get("memorized_ayahs", 0)}/{s["total_ayahs"]} ({progress_pct}%)</span>'
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
                f'<div class="row">'
                f'<span class="row-title">{d["name"]}</span>'
                f'<span class="row-meta num">{d.get("memorized_ayahs", 0)}/{d["total_ayahs"]} ({progress_pct}%)</span>'
                f'</div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    memorized = len(finished_surahs) + len(finished_duas)
    if memorized > 0:
        st.markdown(
            f'<div class="banner banner--ok">'
            f'<strong>✨ Memorized:</strong> {len(finished_surahs)} surahs, {len(finished_duas)} duas'
            f'</div>',
            unsafe_allow_html=True
        )

    if not surahs and not duas and memorized == 0:
        st.caption("No surahs or duas assigned yet.")


def show_weekly_summary(data, kid):
    st.markdown('<div class="profile-wide-module"><div class="profile-module-title">Momentum map</div><div class="profile-module-subtitle">A weekly view of effort, not just outcomes</div>', unsafe_allow_html=True)

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
        week_range = f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
        if week_offset == 0:
            week_range = f"This Week · {week_range}"
        st.markdown(
            f'<div class="week-heading">{week_range}</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("▶", key="kid_next_week", type="secondary", use_container_width=True):
            st.session_state.kid_week_offset = week_offset + 1
            st.rerun()

    summary = compute_weekly_summary(data, kid["id"], monday, sunday)

    st.markdown('<div class="profile-weekly-heading"><span>01</span> Reading this week <small>Pages and language momentum</small></div>', unsafe_allow_html=True)
    en_a, tr_a, read_tot = st.columns(3)
    with en_a:
        st.markdown(
            f'<div class="metric-card"><div class="icon">🇬🇧</div>'
            f'<div class="value">{summary["en_pages"]}</div><div class="label">English pages</div></div>',
            unsafe_allow_html=True
        )
    with tr_a:
        st.markdown(
            f'<div class="metric-card"><div class="icon">🇹🇷</div>'
            f'<div class="value">{summary["tr_pages"]}</div><div class="label">Turkish pages</div></div>',
            unsafe_allow_html=True
        )
    with read_tot:
        st.markdown(
            f'<div class="metric-card"><div class="icon">📖</div>'
            f'<div class="value">{summary["en_pages"] + summary["tr_pages"]}</div><div class="label">Total pages</div></div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="profile-weekly-heading"><span>02</span> Tasks this week <small>Completion across the selected week</small></div>', unsafe_allow_html=True)

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
            tone = "text-success" if complete else "text-danger"
            st.markdown(
                f'<div class="profile-week-task">'
                f'<span class="row-title">{title}</span>'
                f'<span class="num strong {tone}">{done}/{total}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("No tasks assigned this week.")

    if total_assigned:
        st.markdown(
            f'<div class="banner banner--ok">'
            f'<strong>{total_done} of {total_assigned} tasks done this week</strong>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
