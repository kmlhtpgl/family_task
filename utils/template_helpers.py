import json
from pathlib import Path


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TASK_TEMPLATE_FILE = DATA_DIR / "task_templates.json"


DEFAULT_TASK_TEMPLATES = [
    {
        "id": 1,
        "title": "Make bed",
        "default_points": 10
    },
    {
        "id": 2,
        "title": "Brush teeth",
        "default_points": 5
    },
    {
        "id": 3,
        "title": "Read 20 minutes",
        "default_points": 15
    },
    {
        "id": 4,
        "title": "Do homework",
        "default_points": 20
    },
    {
        "id": 5,
        "title": "Practise Quran",
        "default_points": 15
    },
    {
        "id": 6,
        "title": "Practise Turkish reading",
        "default_points": 15
    },
    {
        "id": 7,
        "title": "Tidy bedroom",
        "default_points": 10
    },
    {
        "id": 8,
        "title": "Help set the table",
        "default_points": 10
    },
    {
        "id": 9,
        "title": "Prepare school bag",
        "default_points": 10
    }
]


def load_task_templates():
    """
    Loads task templates from data/task_templates.json.
    If the file is missing, empty or broken, it creates a default task list.
    """
    if not TASK_TEMPLATE_FILE.exists() or TASK_TEMPLATE_FILE.stat().st_size == 0:
        save_task_templates(DEFAULT_TASK_TEMPLATES)
        return DEFAULT_TASK_TEMPLATES.copy()

    try:
        with open(TASK_TEMPLATE_FILE, "r", encoding="utf-8") as file:
            templates = json.load(file)

        if not isinstance(templates, list):
            save_task_templates(DEFAULT_TASK_TEMPLATES)
            return DEFAULT_TASK_TEMPLATES.copy()

        return templates

    except json.JSONDecodeError:
        save_task_templates(DEFAULT_TASK_TEMPLATES)
        return DEFAULT_TASK_TEMPLATES.copy()


def save_task_templates(templates):
    """
    Saves task templates into data/task_templates.json.
    """
    with open(TASK_TEMPLATE_FILE, "w", encoding="utf-8") as file:
        json.dump(templates, file, indent=4, ensure_ascii=False)


def next_template_id(templates):
    """
    Gives the next available task template ID.
    """
    if not templates:
        return 1

    return max(template["id"] for template in templates) + 1
