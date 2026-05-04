import streamlit as st

from utils.task_helpers import get_total_points_for_kid
from utils.book_helpers import get_finished_books, split_books_by_language


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

        assigned_tasks = [
            task for task in data["tasks"]
            if task.get("parent_id") == parent["id"]
        ]

        done_tasks = [t for t in assigned_tasks if t.get("status") == "Done"]
        total_tasks = len(assigned_tasks)

        st.metric("Assigned Tasks", f"{len(done_tasks)} / {total_tasks}")

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
        st.caption("No tasks assigned to oversee yet.")
        return

    tasks_by_kid = {}

    for task in assigned_tasks:
        kid_id = task.get("kid_id")

        if kid_id not in tasks_by_kid:
            tasks_by_kid[kid_id] = []

        tasks_by_kid[kid_id].append(task)

    for kid_id, tasks in tasks_by_kid.items():
        kid_name = get_kid_name(data, kid_id)

        st.write(f"### {kid_name}")

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
    st.subheader("Assigned Books")

    assigned_books = [
        book for book in data["books"]
        if book.get("parent_id") == parent["id"]
    ]

    if not assigned_books:
        st.caption("No books assigned to oversee yet.")
        return

    books_by_kid = {}

    for book in assigned_books:
        kid_id = book.get("kid_id")

        if kid_id not in books_by_kid:
            books_by_kid[kid_id] = []

        books_by_kid[kid_id].append(book)

    for kid_id, books in books_by_kid.items():
        kid_name = get_kid_name(data, kid_id)

        st.write(f"### {kid_name}")

        for book in books:
            status_emoji = {
                "In Progress": "📖",
                "Finished": "✨"
            }.get(book.get("status", ""), "❓")

            st.write(
                f"{status_emoji} **{book['title']}** — "
                f"{book['status']} — "
                f"{book['language']}"
            )


def get_kid_name(data, kid_id):
    for kid in data.get("kids", []):
        if kid["id"] == kid_id:
            return kid["name"]

    return "Unknown Child"
