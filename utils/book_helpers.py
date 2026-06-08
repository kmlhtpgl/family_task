from datetime import date, datetime

from utils.data_helpers import today_string


def calculate_book_progress(book):
    """
    Calculates reading progress as a number between 0 and 1.
    """
    total_pages = book.get("total_pages", 0)

    if total_pages <= 0:
        return 0

    current_page = book.get("current_page", 0)
    return current_page / total_pages


def update_book_page(book, current_page):
    """
    Updates the current page of a book.

    If the current page reaches the total pages,
    the book is marked as finished.
    """
    book["current_page"] = current_page

    if current_page >= book["total_pages"]:
        book["status"] = "Finished"
        book["finished_date"] = today_string()

    return book


def mark_book_finished(book):
    """
    Marks a book as finished.
    """
    book["current_page"] = book["total_pages"]
    book["status"] = "Finished"
    book["finished_date"] = today_string()

    return book


def get_books_for_kid(data, kid_id):
    """
    Returns all books for one child.
    """
    return [
        book for book in data["books"]
        if book.get("kid_id") == kid_id
    ]


def get_books_for_parent(data, parent_id):
    """
    Returns all books for one parent.
    """
    return [
        book for book in data["books"]
        if book.get("parent_id") == parent_id
    ]


def get_books_in_progress(data, kid_id):
    """
    Returns books that are not finished yet.
    """
    return [
        book for book in data["books"]
        if book.get("kid_id") == kid_id
        and book.get("status") != "Finished"
    ]


def get_books_in_progress_for_parent(data, parent_id):
    """
    Returns books that are not finished yet for a parent.
    """
    return [
        book for book in data["books"]
        if book.get("parent_id") == parent_id
        and book.get("status") != "Finished"
    ]


def get_finished_books(data, kid_id):
    """
    Returns finished books for one child.
    """
    return [
        book for book in data["books"]
        if book.get("kid_id") == kid_id
        and book.get("status") == "Finished"
    ]


def get_finished_books_for_parent(data, parent_id):
    """
    Returns finished books for one parent.
    """
    return [
        book for book in data["books"]
        if book.get("parent_id") == parent_id
        and book.get("status") == "Finished"
    ]


def split_books_by_language(books):
    """
    Separates books into English and Turkish lists.
    """
    english_books = [
        book for book in books
        if book.get("language") == "English"
    ]

    turkish_books = [
        book for book in books
        if book.get("language") == "Turkish"
    ]

    return english_books, turkish_books


def format_date_short(iso_str):
    if not iso_str:
        return "Unknown"

    if "T" in iso_str:
        dt = datetime.fromisoformat(iso_str)
    else:
        dt = date.fromisoformat(iso_str)

    return dt.strftime("%b %d, %Y")


def format_elapsed(start_iso, end_date_str=None):
    if not start_iso:
        return ""

    start = datetime.fromisoformat(start_iso).date()
    end = date.fromisoformat(end_date_str) if end_date_str else date.today()

    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day

    if days < 0:
        months -= 1
        prev_month = end.month - 1
        prev_month_year = end.year
        if prev_month == 0:
            prev_month = 12
            prev_month_year -= 1
        days_in_prev_month = (
            date(prev_month_year, prev_month + 1, 1)
            - date(prev_month_year, prev_month, 1)
        ).days
        days += days_in_prev_month

    if months < 0:
        years -= 1
        months += 12

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    parts.append(f"{days} day{'s' if days != 1 else ''}")

    return ", ".join(parts)
