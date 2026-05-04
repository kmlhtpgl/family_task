import streamlit as st

from utils.task_helpers import get_total_points_for_parent, get_weekly_points_for_parent
from utils.book_helpers import get_finished_books_for_parent, split_books_by_language


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
        show_profile_photo(parent)

        st.subheader(parent["name"])

        if parent.get("email"):
            st.write(f"📧 {parent['email']}")

        if parent.get("phone"):
            st.write(f"📞 {parent['phone']}")

        total_points = get_total_points_for_parent(data, parent["id"])
        weekly_points = get_weekly_points_for_parent(data, parent["id"])

        st.metric("Total Points", total_points)
        st.metric("This Week", weekly_points)

    with col2:
        show_parent_tasks(data, parent)
        show_parent_books(data, parent)


def show_profile_photo(parent):
    photo_url = parent.get("photo_url")

    if photo_url:
        st.image(photo_url, width=180)
    else:
        st.write("👤 No profile photo yet")


def show_parent_tasks(data, parent):
    st.subheader("Assigned Tasks")

    assigned_tasks = [
        task for task in data["tasks"]
        if task.get("parent_id") == parent["id"]
    ]

    if not assigned_tasks:
        st.caption("No tasks assigned yet.")
        return

    tasks_by_date = {}

    for task in assigned_tasks:
        due = task.get("due_date", "No date")

        if due not in tasks_by_date:
            tasks_by_date[due] = []

        tasks_by_date[due].append(task)

    for due_date, tasks in sorted(tasks_by_date.items()):
        st.write(f"### 📅 {due_date}")

        for task in tasks:
            status_emoji = {
                "Backlog": "📋",
                "In Progress": "⏳",
                "Done": "✅"
            }.get(task.get("status", ""), "❓")

            st.write(
                f"{status_emoji} **{task['title']}** — "
                f"{task['status']} — "
                f"{task['points']} points"
            )


def show_parent_books(data, parent):
    st.subheader("Reading List")

    assigned_books = [
        book for book in data["books"]
        if book.get("parent_id") == parent["id"]
    ]

    if not assigned_books:
        st.caption("No books assigned yet.")
        return

    in_progress = [b for b in assigned_books if b.get("status") != "Finished"]
    finished = [b for b in assigned_books if b.get("status") == "Finished"]

    st.write("### 📖 In Progress")

    if in_progress:
        for book in in_progress:
            st.write(f"📖 **{book['title']}** — {book['language']} ({book.get('current_page', 0)}/{book['total_pages']} pages)")
    else:
        st.caption("No books in progress.")

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
