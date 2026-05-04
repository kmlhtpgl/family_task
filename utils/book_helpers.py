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
