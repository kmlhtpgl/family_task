import json
from pathlib import Path


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

BOOK_TEMPLATE_FILE = DATA_DIR / "book_templates.json"


DEFAULT_BOOK_TEMPLATES = [
    {
        "id": 1,
        "title": "The Very Hungry Caterpillar",
        "language": "English",
        "total_pages": 26
    },
    {
        "id": 2,
        "title": "Charlotte's Web",
        "language": "English",
        "total_pages": 184
    },
    {
        "id": 3,
        "title": "Matilda",
        "language": "English",
        "total_pages": 240
    },
    {
        "id": 4,
        "title": "Küçük Prens",
        "language": "Turkish",
        "total_pages": 112
    },
    {
        "id": 5,
        "title": "Şeker Portakalı",
        "language": "Turkish",
        "total_pages": 184
    }
]


def load_book_templates():
    """
    Loads book templates from data/book_templates.json.
    If the file is missing, empty or broken, it creates a default book list.
    """
    if not BOOK_TEMPLATE_FILE.exists() or BOOK_TEMPLATE_FILE.stat().st_size == 0:
        save_book_templates(DEFAULT_BOOK_TEMPLATES)
        return DEFAULT_BOOK_TEMPLATES.copy()

    try:
        with open(BOOK_TEMPLATE_FILE, "r", encoding="utf-8") as file:
            templates = json.load(file)

        if not isinstance(templates, list):
            save_book_templates(DEFAULT_BOOK_TEMPLATES)
            return DEFAULT_BOOK_TEMPLATES.copy()

        return templates

    except json.JSONDecodeError:
        save_book_templates(DEFAULT_BOOK_TEMPLATES)
        return DEFAULT_BOOK_TEMPLATES.copy()


def save_book_templates(templates):
    """
    Saves book templates into data/book_templates.json.
    """
    with open(BOOK_TEMPLATE_FILE, "w", encoding="utf-8") as file:
        json.dump(templates, file, indent=4, ensure_ascii=False)


def next_book_template_id(templates):
    """
    Gives the next available book template ID.
    """
    if not templates:
        return 1

    return max(template["id"] for template in templates) + 1
