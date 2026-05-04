import streamlit as st

from utils.task_helpers import get_total_points_for_parent, get_weekly_points_for_parent
from utils.book_helpers import get_finished_books_for_parent, split_books_by_language
from utils.achievement_helpers import get_parent_achievements
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

        st.markdown(
            f'<div class="metric-card"><h3>⭐ Total Points</h3><div class="value">{total_points}</div><div class="label">{weekly_points} this week</div></div>',
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

    active = [t for t in assigned_tasks if t["status"] != "Done"]
    done = [t for t in assigned_tasks if t["status"] == "Done"]

    tasks_by_date = {}

    for task in active:
        due = task.get("due_date", "No date")

        if due not in tasks_by_date:
            tasks_by_date[due] = []

        tasks_by_date[due].append(task)

    if tasks_by_date:
        for due_date, tasks in sorted(tasks_by_date.items()):
            st.write(f"### 📅 {due_date}")

            for task in tasks:
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

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span>{book["title"]}</span>'
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
                st.write(f"✅ {book['title']} — {book['total_pages']} pages")

        if turkish_books:
            st.write("#### 🇹🇷 Turkish")
            for book in turkish_books:
                st.write(f"✅ {book['title']} — {book['total_pages']} pages")
    else:
        st.caption("No books finished yet.")
