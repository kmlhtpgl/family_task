import streamlit as st

from utils.book_helpers import (
    calculate_book_progress,
    get_books_in_progress,
    get_finished_books,
    split_books_by_language
)
from utils.db_helpers import update_book, delete_book
from utils.data_helpers import today_string


def reading_library_page(data):
    st.header("📚 Reading Library")

    if not data["kids"]:
        st.info("Add children first in Admin.")
        return

    kid_options = {
        kid["name"]: kid["id"]
        for kid in data["kids"]
    }

    selected_name = st.selectbox(
        "Choose child",
        list(kid_options.keys())
    )

    kid_id = kid_options[selected_name]

    show_books_in_progress(data, kid_id)
    st.divider()
    show_finished_books(data, kid_id)


def show_books_in_progress(data, kid_id):
    st.subheader("📖 Books in Progress")

    books = get_books_in_progress(data, kid_id)

    if not books:
        st.caption("No books in progress.")
        return

    for book in books:
        with st.container(border=True):
            st.write(f"### {book['title']}")
            st.write(f"Language: **{book['language']}**")
            st.write(f"Total pages: **{book['total_pages']}**")

            current_page = st.number_input(
                "Current page",
                min_value=0,
                max_value=int(book["total_pages"]),
                value=int(book.get("current_page", 0)),
                key=f"book_page_{book['id']}"
            )

            if current_page != book.get("current_page", 0):
                updates = {
                    "current_page": int(current_page)
                }

                if current_page >= book["total_pages"]:
                    updates["status"] = "Finished"
                    updates["finished_date"] = today_string()

                update_book(book["id"], updates)
                st.rerun()

            progress = calculate_book_progress(book)
            st.progress(progress)
            st.write(f"Progress: **{round(progress * 100)}%**")

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Mark as finished", key=f"finish_book_{book['id']}"):
                    updates = {
                        "current_page": int(book["total_pages"]),
                        "status": "Finished",
                        "finished_date": today_string()
                    }

                    update_book(book["id"], updates)
                    st.rerun()

            with col2:
                if st.button("🗑️ Remove book", key=f"remove_reading_book_{book['id']}"):
                    delete_book(book["id"])
                    st.warning("Book removed from reading list.")
                    st.rerun()


def show_finished_books(data, kid_id):
    st.subheader("✨ Finished Books")

    finished_books = get_finished_books(data, kid_id)
    english_books, turkish_books = split_books_by_language(finished_books)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 🇬🇧 English")

        if english_books:
            for book in english_books:
                st.write(f"✅ {book['title']} — {book['total_pages']} pages")
        else:
            st.caption("No English books finished yet.")

    with col2:
        st.write("### 🇹🇷 Turkish")

        if turkish_books:
            for book in turkish_books:
                st.write(f"✅ {book['title']} — {book['total_pages']} pages")
        else:
            st.caption("No Turkish books finished yet.")
