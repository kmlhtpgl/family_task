"""Committed sample family data for the test suite.

data/family_task_data.json is a live cache and is gitignored, so the suite
cannot depend on it. Dates are generated relative to today so that
date-sensitive rules (future tasks, overdue decay) are exercised whichever day
the suite runs.
"""

from datetime import date, timedelta

WEEK_KEY = "%G-W%V"


def _week_key(d):
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def _days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


def _days_ahead(n):
    return (date.today() + timedelta(days=n)).isoformat()


def sample_data(today=None):
    """A small but complete family: 2 parents, 3 kids, tasks, books, surahs.

    Deliberately includes one of every case the board has to render:
      - a task due today, doable          -> completes, awards points
      - a task due in the future          -> rejected with reason "future"
      - a task 5 days overdue             -> rejected with reason "overdue"
      - a task completed long ago         -> points decay to 0
      - a done task                       -> undo path
    """
    today = today or date.today()
    this_week = _week_key(today)

    parents = [
        {"id": 1, "name": "Yusuf", "created_at": _days_ago(400)},
        {"id": 2, "name": "Amina", "created_at": _days_ago(400)},
    ]

    kids = [
        {"id": 1, "name": "Zayd", "age": 9, "photo_path": None, "created_at": _days_ago(380)},
        {"id": 2, "name": "Maryam", "age": 7, "photo_path": None, "created_at": _days_ago(300)},
        {"id": 3, "name": "Bilal", "age": 5, "photo_path": None, "created_at": _days_ago(200)},
    ]

    def task(tid, title, **kw):
        base = {
            "id": tid,
            "title": title,
            "kid_id": None,
            "parent_id": None,
            "due_date": None,
            "points": 10,
            "status": "Backlog",
            "repeat_type": "once",
            "created_at": _days_ago(30),
            "completed_date": None,
            "completed_week": None,
        }
        base.update(kw)
        return base

    tasks = [
        # doable today, awards points
        task(1, "Set the table", kid_id=1, due_date=today.isoformat(), points=10),
        # in the future -> "future"
        task(2, "Science project", kid_id=2, due_date=_days_ahead(1), points=25),
        # 5 days overdue -> "overdue"
        task(3, "Water the plants", kid_id=3, due_date=_days_ago(5), points=5),
        # completed today, still counts
        task(
            4, "Read 20 pages", kid_id=1, due_date=today.isoformat(), points=15,
            status="Done", completed_date=today.isoformat(), completed_week=this_week,
        ),
        # completed 6 days after a due date 4 days back -> points decay to 0
        task(
            5, "Tidy bedroom", kid_id=2, due_date=_days_ago(4), points=20,
            status="Done", completed_date=_days_ago(-2), completed_week=this_week,
        ),
        # parent's own task
        task(6, "Pay the bills", parent_id=1, due_date=today.isoformat(), points=30),
        # prayers, as tracked by the app
        task(7, "Fecr", kid_id=1, due_date=today.isoformat(), points=5),
        task(8, "Zuhr", kid_id=1, due_date=today.isoformat(), points=5),
        task(9, "Asr", kid_id=2, due_date=today.isoformat(), points=5),
        # undated task: always completable
        task(10, "Make dua", kid_id=3, points=5),
    ]

    books = [
        {
            "id": 1, "title": "The Secret Garden", "kid_id": 1, "language": "en",
            "total_pages": 240, "current_page": 180, "status": "In Progress",
            "created_at": _days_ago(20), "finished_date": None,
        },
        {
            "id": 2, "title": "Malory Towers", "kid_id": 2, "language": "en",
            "total_pages": 320, "current_page": 320, "status": "Finished",
            "created_at": _days_ago(60), "finished_date": _days_ago(2),
        },
    ]

    surahs = [
        {
            "id": 1, "name": "Al-Baqarah", "kid_id": 1, "parent_id": None,
            "type": "surah", "total_ayahs": 286, "memorized_ayahs": 90,
            "status": "In Progress", "last_practiced_date": _days_ago(1),
            "finished_date": None,
        },
        {
            "id": 2, "name": "Yasin", "kid_id": 2, "parent_id": None,
            "type": "surah", "total_ayahs": 83, "memorized_ayahs": 83,
            "status": "Memorized", "last_practiced_date": _days_ago(4),
            "finished_date": _days_ago(4),
        },
        {
            "id": 3, "name": "Al-Fatihah", "kid_id": 3, "parent_id": None,
            "type": "surah", "total_ayahs": 7, "memorized_ayahs": 7,
            "status": "Memorized", "last_practiced_date": _days_ago(90),
            "finished_date": _days_ago(90),
        },
        {
            "id": 4, "name": "Dua for travel", "kid_id": 1, "parent_id": None,
            "type": "dua", "total_ayahs": 3, "memorized_ayahs": 1,
            "status": "In Progress", "last_practiced_date": _days_ago(2),
            "finished_date": None,
        },
    ]

    return {
        "parents": parents,
        "kids": kids,
        "tasks": tasks,
        "books": books,
        "surahs": surahs,
        "reading_log": [],
        "reward_sessions": [],
        "points_adjustments": [{"id": 1, "person_id": 2, "person_type": "kid", "points": 15}],
        "meeting_notes": [],
        "meeting_comments": [],
        "meeting_templates": [],
        "meeting_sessions": [],
        "task_templates": [
            {"id": 1, "title": "Tidy bedroom", "default_points": 10, "created_at": _days_ago(90)},
            {"id": 2, "title": "Read 20 pages", "default_points": 15, "created_at": _days_ago(90)},
        ],
        "book_templates": [
            {"id": 1, "title": "The Secret Garden", "default_pages": 240, "created_at": _days_ago(90)},
        ],
        "settings": {"points_for_done": 10},
    }
