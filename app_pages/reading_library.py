from datetime import date
from html import escape

import streamlit as st

from utils.book_helpers import (
    calculate_book_progress,
    format_date_short,
    format_elapsed,
    get_books_in_progress,
    get_books_in_progress_for_parent,
    get_finished_books,
    get_finished_books_for_parent,
    split_books_by_language
)
from utils.db_helpers import update_book, delete_book, add_reading_log
from utils.data_helpers import today_string
from utils.page_chrome import render_focus_panel, render_page_header, render_stat_strip


def reading_library_page(data):
    render_page_header("Reading", "Keep books, pages, and progress moving together.")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    reader_labels = [f"Kid · {k['name']}" for k in data["kids"]]
    reader_labels += [f"Parent · {p['name']}" for p in data.get("parents", [])]

    selected_label = st.radio("Choose reader", reader_labels, horizontal=True, key="reader_select")

    if selected_label.startswith("Kid · "):
        name = selected_label.replace("Kid · ", "")
        reader_id = next(k["id"] for k in data["kids"] if k["name"] == name)
        current = get_books_in_progress(data, reader_id)
        finished = get_finished_books(data, reader_id)
        is_parent = False
    else:
        name = selected_label.replace("Parent · ", "")
        reader_id = next(p["id"] for p in data["parents"] if p["name"] == name)
        current = get_books_in_progress_for_parent(data, reader_id)
        finished = get_finished_books_for_parent(data, reader_id)
        is_parent = True

    pages_in_motion = sum(int(book.get("current_page", 0)) for book in current)
    pages_today = sum(
        int(log.get("pages_read", 0))
        for log in data.get("reading_log", [])
        if log.get("read_date") == today_string()
        and ((log.get("parent_id") == reader_id) if is_parent else (log.get("kid_id") == reader_id))
    )
    render_stat_strip([
        ("In progress", str(len(current)), "books currently open"),
        ("Finished", str(len(finished)), "books completed"),
        ("Today", str(pages_today), "pages logged today"),
    ])
    focus = current[0] if current else None
    render_focus_panel(
        "Continue reading",
        focus["title"] if focus else "Choose a book to begin",
        f"{focus.get('current_page', 0)} of {focus.get('total_pages', 0)} pages complete" if focus else "Your active reading queue is clear",
        f"{round(calculate_book_progress(focus) * 100)}%" if focus else "0%",
        "complete",
    )
    st.markdown('<div class="reading-shelf-heading"><span>ACTIVE SHELF</span><strong>Books in progress</strong><small>Update a page count to keep the shelf alive.</small></div>', unsafe_allow_html=True)
    show_books_in_progress(data, reader_id, is_parent=is_parent)
    st.divider()
    show_finished_books(data, reader_id, is_parent=is_parent)


def show_books_in_progress(data, reader_id, is_parent=False):
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

            language_name = book["language"]
            writer_info = book.get("writer", "") or "Independent reading"

            assigned_date = format_date_short(book.get("created_at", ""))
            elapsed = format_elapsed(book.get("created_at", ""))

            st.markdown(
                f'<div class="book-card">'
                f'<div class="book-card__cover"><span>{progress_pct}</span><small>%</small></div>'
                f'<div class="book-card__body"><div class="book-card__top">'
                f'<div><div class="book-card__title">{escape(book["title"])}</div>'
                f'<div class="book-card__writer">{escape(writer_info)}</div></div>'
                f'<span class="book-card__language">{escape(language_name)}</span></div>'
                f'<div class="book-card__progress-label"><span>{book.get("current_page", 0)} / {book["total_pages"]} pages</span><span>{progress_pct}%</span></div>'
                f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
                f'<div class="book-card__meta">Assigned {assigned_date}{" · " + elapsed + " ago" if elapsed else ""}</div></div>'
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
                old_page = int(book.get("current_page", 0))
                updates = {
                    "current_page": int(current_page)
                }

                if current_page >= book["total_pages"]:
                    updates["status"] = "Finished"
                    updates["finished_date"] = today_string()

                added = int(current_page) - old_page
                if added > 0:
                    log_reading(data, book, reader_id, is_parent, added)

                update_book(book["id"], updates)
                st.success(f"Updated: {book['title']} ({progress_pct}%)")
                st.rerun()

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Mark as finished", key=f"finish_book_{book['id']}"):
                    remaining = int(book["total_pages"]) - int(book.get("current_page", 0))
                    updates = {
                        "current_page": int(book["total_pages"]),
                        "status": "Finished",
                        "finished_date": today_string()
                    }

                    if remaining > 0:
                        log_reading(data, book, reader_id, is_parent, remaining)

                    update_book(book["id"], updates)
                    st.rerun()

            with col2:
                if st.button("Remove book", key=f"remove_reading_book_{book['id']}"):
                    delete_book(book["id"])
                    st.success("Book is removed.")
                    st.rerun()


def show_finished_books(data, reader_id, is_parent=False):
    st.markdown('<div class="reading-archive-heading"><span>THE ARCHIVE</span><strong>Finished books</strong><small>Everything you have already carried across the line.</small></div>', unsafe_allow_html=True)

    if is_parent:
        finished_books = get_finished_books_for_parent(data, reader_id)
    else:
        finished_books = get_finished_books(data, reader_id)

    english_books, turkish_books = split_books_by_language(finished_books)

    search_finished = st.text_input("Search finished books", placeholder="Find a finished title...", label_visibility="collapsed")

    if search_finished:
        english_books = [b for b in english_books if search_finished.lower() in b["title"].lower()]
        turkish_books = [b for b in turkish_books if search_finished.lower() in b["title"].lower()]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f'<div class="archive-column-title">English <span>{len(english_books)}</span></div>', unsafe_allow_html=True)

        if english_books:
            for book in english_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                assigned_date = format_date_short(book.get("created_at", ""))
                finished_date = format_date_short(book.get("finished_date", ""))
                elapsed = format_elapsed(book.get("created_at", ""), book.get("finished_date"))
                elapsed_display = f"· ⏱️ {elapsed}" if elapsed else ""
                st.markdown(
                    f'<div class="finished-book-card">'
                    f'<div class="row-title">{escape(book["title"])}{escape(writer)}</div>'
                    f'<div class="row-meta">{book["total_pages"]} pages · {assigned_date} → {finished_date} {elapsed_display}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No English books finished yet." if not search_finished else "No matches.")

    with col2:
        st.markdown(f'<div class="archive-column-title">Turkish <span>{len(turkish_books)}</span></div>', unsafe_allow_html=True)

        if turkish_books:
            for book in turkish_books:
                writer = f" — {book.get('writer', '')}" if book.get("writer") else ""
                assigned_date = format_date_short(book.get("created_at", ""))
                finished_date = format_date_short(book.get("finished_date", ""))
                elapsed = format_elapsed(book.get("created_at", ""), book.get("finished_date"))
                elapsed_display = f"· ⏱️ {elapsed}" if elapsed else ""
                st.markdown(
                    f'<div class="finished-book-card">'
                    f'<div class="row-title">{escape(book["title"])}{escape(writer)}</div>'
                    f'<div class="row-meta">{book["total_pages"]} pages · {assigned_date} → {finished_date} {elapsed_display}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No Turkish books finished yet." if not search_finished else "No matches.")


def log_reading(data, book, reader_id, is_parent=False, pages_read=0):
    """Auto-log pages read for a book update, attributed to the correct person."""
    if pages_read <= 0:
        return
    entry = {
        "book_id": book["id"],
        "language": book.get("language", "English"),
        "pages_read": int(pages_read),
        "read_date": today_string(),
    }
    if is_parent:
        entry["parent_id"] = reader_id
    else:
        entry["kid_id"] = reader_id
    add_reading_log(entry)
