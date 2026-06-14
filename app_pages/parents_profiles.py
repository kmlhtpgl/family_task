from datetime import date

import streamlit as st

from utils.task_helpers import get_total_points_for_parent, get_weekly_points_for_parent, get_monthly_points_for_parent, get_rank, get_overdue_task_count
from utils.book_helpers import get_finished_books_for_parent, split_books_by_language
from utils.achievement_helpers import get_parent_achievements
from utils.data_helpers import today_string
from utils.styles import avatar_image, achievement_badge


def parents_profiles_page(data):
    st.header("👨‍👩‍👧‍👦 Parents Profiles")

    parents = data.get("parents", [])

    if not parents:
        st.info("No parents added yet. Go to Admin to add a parent.")
        return

    parent_options = {
        parent["name"]: parent["id"]
        for parent in parents
    }

    selected_name = st.selectbox(
        "Choose profile",
        list(parent_options.keys())
    )

    selected_parent = None

    for parent in parents:
        if parent["id"] == parent_options[selected_name]:
            selected_parent = parent
            break

    if selected_parent is None:
        st.error("Parent profile not found.")
        return

    show_parent_profile(data, selected_parent)


def show_parent_profile(data, parent):
    col1, col2 = st.columns([1, 2])

    with col1:
        avatar_image(parent.get("photo_url"), width=150)

        st.subheader(parent["name"])

        if parent.get("email"):
            st.write(f"📧 {parent['email']}")

        if parent.get("phone"):
            st.write(f"📞 {parent['phone']}")

        total_points = get_total_points_for_parent(data, parent["id"])
        weekly_points = get_weekly_points_for_parent(data, parent["id"])
        rank, icon = get_rank(total_points)

        st.markdown(
            f'<div class="metric-card"><h3>⭐ Total Points</h3><div class="value">{total_points}</div><div class="label">{weekly_points} this week</div></div>',
            unsafe_allow_html=True
        )

        today = date.today()
        monthly_pts = get_monthly_points_for_parent(data, parent["id"], today.year, today.month)
        gbp = monthly_pts / 300
        st.markdown(
            f'<div style="padding:12px;background:rgba(255,215,0,0.1);border-radius:12px;border:1px solid #FFD700;margin-top:8px;">'
            f'<strong>💰 This Month:</strong> {monthly_pts} pts = £{gbp:.2f}'
            f'</div>',
            unsafe_allow_html=True
        )

        overdue = get_overdue_task_count(data, parent["id"], is_kid=False)
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

        achievements = get_parent_achievements(data, parent["id"])

        if achievements:
            for ach in achievements:
                achievement_badge(ach["icon"], ach["label"])
        else:
            st.caption("Complete tasks and read books to earn badges!")

    with col2:
        show_parent_tasks(data, parent)
        show_parent_books(data, parent)


def show_parent_tasks(data, parent):
    st.subheader("📋 Assigned Tasks")

    assigned_tasks = [
        task for task in data["tasks"]
        if task.get("parent_id") == parent["id"]
    ]

    if not assigned_tasks:
        st.caption("No tasks assigned yet.")
        return

    today = today_string()
    active = [t for t in assigned_tasks if t["status"] != "Done" and t.get("due_date") == today]
    done = [t for t in assigned_tasks if t["status"] == "Done"]

    if active:
        st.write(f"**Today's Tasks ({len(active)})**")

        for task in active:
            status_class = task["status"].lower().replace(" ", "-")
            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span>{task["title"]}</span>'
                f'<span class="status-badge status-{status_class}">{task["status"]}</span>'
                f'<span>{task["points"]} pts</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    if done:
        st.write(f"**✅ Completed ({len(done)})**")

        for task in done[:5]:
            st.markdown(
                f'<div class="task-item" style="border-left-color:#4CAF50;">'
                f'<span>✅ {task["title"]}</span>'
                f'<span style="color:#4CAF50;font-weight:600;">+{task["points"]} pts</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        if len(done) > 5:
            st.caption(f"...and {len(done) - 5} more")


def show_parent_books(data, parent):
    st.subheader("📚 Reading List")

    assigned_books = [
        book for book in data["books"]
        if book.get("parent_id") == parent["id"]
    ]

    if not assigned_books:
        st.caption("No books assigned yet.")
        return

    in_progress = [b for b in assigned_books if b.get("status") != "Finished"]
    finished = [b for b in assigned_books if b.get("status") == "Finished"]

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

    st.write("### ✨ Finished")

    if finished:
        english_books, turkish_books = split_books_by_language(finished)

        if english_books:
            st.write("#### 🇬🇧 English")
            for book in english_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.write(f"✅ {book['title']}{writer} — {book['total_pages']} pages")

        if turkish_books:
            st.write("#### 🇹🇷 Turkish")
            for book in turkish_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.write(f"✅ {book['title']}{writer} — {book['total_pages']} pages")
    else:
        st.caption("No books finished yet.")
