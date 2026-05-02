import json
from pathlib import Path
from datetime import date


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

PHOTO_DIR = Path("profile_photos")
PHOTO_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "family_task_data.json"


DEFAULT_DATA = {
    "parents": [],
    "kids": [],
    "tasks": [],
    "books": [],
    "task_templates": [],
    "settings": {
        "points_for_done": 10
    }
}


def load_data():
    """
    Loads app data from the JSON file.
    If the file does not exist, is empty, or is broken,
    it creates default data.
    """
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        # This keeps old data files working when we add new features.
        if "parents" not in data:
            data["parents"] = []

        if "kids" not in data:
            data["kids"] = []

        if "tasks" not in data:
            data["tasks"] = []

        if "books" not in data:
            data["books"] = []

        if "task_templates" not in data:
            data["task_templates"] = []

        if "settings" not in data:
            data["settings"] = {"points_for_done": 10}

        if "points_for_done" not in data["settings"]:
            data["settings"]["points_for_done"] = 10

        save_data(data)
        return data

    except json.JSONDecodeError:
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()


def save_data(data):
    """
    Saves app data into the JSON file.
    """
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def next_id(items):
    """
    Gives the next available ID for kids, tasks or books.
    """
    if not items:
        return 1

    return max(item["id"] for item in items) + 1


def today_string():
    """
    Returns today's date as text.
    Example: 2026-04-26
    """
    return date.today().isoformat()


def current_week_key():
    """
    Returns the current week.
    Example: 2026-W17
    """
    year, week, _ = date.today().isocalendar()
    return f"{year}-W{week}"


def get_parent(data, parent_id):
    """
    Finds one parent by ID.
    """
    for parent in data["parents"]:
        if parent["id"] == parent_id:
            return parent

    return None


def get_kid(data, kid_id):
    """
    Finds one child by ID.
    """
    for kid in data["kids"]:
        if kid["id"] == kid_id:
            return kid

    return None


def get_task(data, task_id):
    """
    Finds one task by ID.
    """
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task

    return None


def get_book(data, book_id):
    """
    Finds one book by ID.
    """
    for book in data["books"]:
        if book["id"] == book_id:
            return book

    return None
