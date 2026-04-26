import streamlit as st
from pathlib import Path

from utils.task_helpers import get_total_points_for_kid
from utils.book_helpers import get_finished_books, split_books_by_language


def kids_profiles_page(data):
    st.header("Kids Profiles")

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
        show_profile_photo(kid)

        st.subheader(kid["name"])
        st.write(f"Age: {kid.get('age', 'Not entered')}")

        total_points = get_total_points_for_kid(data, kid["id"])
        st.metric("Total Points", total_points)

    with col2:
        show_child_tasks(data, kid)
        show_child_read_books(data, kid)


def show_profile_photo(kid):
    photo_path = kid.get("photo_path")

    if photo_path and Path(photo_path).exists():
        st.image(photo_path, width=180)
    else:
        st.write("👤 No profile photo yet")


def show_child_tasks(data, kid):
    st.subheader("Current Tasks")

    child_tasks = [
        task for task in data["tasks"]
        if task["kid_id"] == kid["id"]
    ]

    if not child_tasks:
        st.caption("No tasks assigned yet.")
        return

    for task in child_tasks:
        st.write(
            f"- **{task['title']}** — "
            f"{task['status']} — "
            f"{task['points']} points"
        )


def show_child_read_books(data, kid):
    st.subheader("Read Books")

    finished_books = get_finished_books(data, kid["id"])
    english_books, turkish_books = split_books_by_language(finished_books)

    st.write("### English Books")

    if english_books:
        for book in english_books:
            st.write(f"- {book['title']} ({book['total_pages']} pages)")
    else:
        st.caption("No English books finished yet.")

    st.write("### Turkish Books")

    if turkish_books:
        for book in turkish_books:
            st.write(f"- {book['title']} ({book['total_pages']} pages)")
    else:
        st.caption("No Turkish books finished yet.")
