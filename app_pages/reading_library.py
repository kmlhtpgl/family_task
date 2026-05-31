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

    reader_group = st.segmented_control(
        "Type", ["Kids", "Parents"], key="reader_group"
    )

    reader_id = None
    is_parent = False

    if reader_group == "Kids" and data["kids"]:
        kid_names = [kid["name"] for kid in data["kids"]]
        selected = st.radio("Choose reader", kid_names, horizontal=True, key="reader_kid")
        reader_id = next(k["id"] for k in data["kids"] if k["name"] == selected)
    elif reader_group == "Parents" and data.get("parents"):
        parent_names = [p["name"] for p in data["parents"]]
        selected = st.radio("Choose reader", parent_names, horizontal=True, key="reader_parent")
        reader_id = next(p["id"] for p in data["parents"] if p["name"] == selected)
        is_parent = True

    if reader_id is None:
        st.info("Select a reader above.")
        return

    if not is_parent:
        show_books_in_progress(data, reader_id, is_parent=False)
        st.divider()
        show_finished_books(data, reader_id, is_parent=False)
    else:
        show_books_in_progress(data, reader_id, is_parent=True)
        st.divider()
        show_finished_books(data, reader_id, is_parent=True)


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
                    st.success("✅ Book is removed!")
                    st.rerun()


def show_finished_books(data, reader_id, is_parent=False):
    st.subheader("✨ Finished Books")

    if is_parent:
        finished_books = get_finished_books_for_parent(data, reader_id)
    else:
        finished_books = get_finished_books(data, reader_id)

    english_books, turkish_books = split_books_by_language(finished_books)

    search_finished = st.text_input("🔍 Search finished books", placeholder="Type book name to filter...", label_visibility="collapsed")

    if search_finished:
        english_books = [b for b in english_books if search_finished.lower() in b["title"].lower()]
        turkish_books = [b for b in turkish_books if search_finished.lower() in b["title"].lower()]

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"### 🇬🇧 English ({len(english_books)} finished)")

        if english_books:
            for book in english_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.markdown(
                    f'<div class="task-item" style="border-left-color:#4CAF50;">'
                    f'<span>✅ {book["title"]}{writer}</span>'
                    f' <span style="color:#666;">{book["total_pages"]} pages</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No English books finished yet." if not search_finished else "No matches.")

    with col2:
        st.write(f"### 🇹🇷 Turkish ({len(turkish_books)} finished)")

        if turkish_books:
            for book in turkish_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                st.markdown(
                    f'<div class="task-item" style="border-left-color:#4CAF50;">'
                    f'<span>✅ {book["title"]}{writer}</span>'
                    f' <span style="color:#666;">{book["total_pages"]} pages</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No Turkish books finished yet." if not search_finished else "No matches.")
