import streamlit as st

from utils.book_helpers import (
    calculate_book_progress,
    get_books_in_progress,
    get_books_in_progress_for_parent,
    get_finished_books,
    get_finished_books_for_parent,
    split_books_by_language
)
from utils.db_helpers import update_book, delete_book
from utils.data_helpers import today_string


def reading_library_page(data):
    st.header("📚 Reading Library")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    reader_options = build_reader_options(data)

    selected_label = st.selectbox(
        "Choose reader",
        list(reader_options.keys())
    )

    reader_info = reader_options[selected_label]

    if reader_info["type"] == "kid":
        show_books_in_progress(data, reader_info["id"], is_parent=False)
        st.divider()
        show_finished_books(data, reader_info["id"], is_parent=False)
    else:
        show_books_in_progress(data, reader_info["id"], is_parent=True)
        st.divider()
        show_finished_books(data, reader_info["id"], is_parent=True)


def build_reader_options(data):
    options = {}

    for kid in data["kids"]:
        options[f"👧 {kid['name']}"] = {"type": "kid", "id": kid["id"]}

    for parent in data.get("parents", []):
        options[f"👨‍👩‍👧 {parent['name']}"] = {"type": "parent", "id": parent["id"]}

    return options


def show_books_in_progress(data, reader_id, is_parent=False):
    st.subheader("📖 Books in Progress")

    if is_parent:
        books = get_books_in_progress_for_parent(data, reader_id)
    else:
        books = get_books_in_progress(data, reader_id)

    if not books:
        st.caption("No books in progress.")
        return

    for book in books:
        with st.container():
            progress = calculate_book_progress(book)
            progress_pct = round(progress * 100)

            language_flag = "🇬🇧" if book["language"] == "English" else "🇹🇷"
            writer_info = f"✍️ {book.get('writer', 'Unknown')}" if book.get("writer") else ""

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<h4 style="margin:0;">{book["title"]}</h4>'
                f'<span style="color:#666;">{language_flag} {book["total_pages"]} pages</span>'
                f'</div>'
                f'{"<p style=\"margin:5px 0 0 0;color:#888;font-size:0.9em;\">" + writer_info + "</p>" if writer_info else ""}'
                f'<div style="margin-top:10px;">'
                f'<span style="font-size:0.9em;color:#666;">{book.get("current_page", 0)} / {book["total_pages"]} pages ({progress_pct}%)</span>'
                f'</div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            current_page = st.number_input(
                "Current page",
                min_value=0,
                max_value=int(book["total_pages"]),
                value=int(book.get("current_page", 0)),
                key=f"book_page_{book['id']}",
                label_visibility="collapsed"
            )

            if current_page != book.get("current_page", 0):
                updates = {
                    "current_page": int(current_page)
                }

                if current_page >= book["total_pages"]:
                    updates["status"] = "Finished"
                    updates["finished_date"] = today_string()

                update_book(book["id"], updates)
                st.success(f"📖 Updated: {book['title']} ({progress_pct}%)")
                st.rerun()

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


def show_finished_books(data, reader_id, is_parent=False):
    st.subheader("✨ Finished Books")

    if is_parent:
        finished_books = get_finished_books_for_parent(data, reader_id)
    else:
        finished_books = get_finished_books(data, reader_id)

    english_books, turkish_books = split_books_by_language(finished_books)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 🇬🇧 English")

        if english_books:
            for book in english_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.markdown(
                    f'<div class="task-item" style="border-left-color:#4CAF50;">'
                    f'<span>✅ {book["title"]}{writer}</span>'
                    f'<span style="color:#666;">{book["total_pages"]} pages</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No English books finished yet.")

    with col2:
        st.write("### 🇹🇷 Turkish")

        if turkish_books:
            for book in turkish_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.markdown(
                    f'<div class="task-item" style="border-left-color:#4CAF50;">'
                    f'<span>✅ {book["title"]}{writer}</span>'
                    f'<span style="color:#666;">{book["total_pages"]} pages</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No Turkish books finished yet.")
