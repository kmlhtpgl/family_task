from datetime import date


def compute_weekly_summary(data, person_id, monday, sunday, is_kid=True):
    """
    Returns a weekly summary dict for one person between monday and sunday (inclusive):
      done_tasks    - tasks completed (Done) with completed_date in range
      not_done_tasks- tasks due in range (due_date in range) not completed (status != Done)
      en_pages      - English pages read in range (from reading_log)
      tr_pages      - Turkish pages read in range (from reading_log)

    When is_kid is True the tasks/reading belong to a child (kid_id), otherwise to a parent (parent_id).
    """
    done_tasks = []
    not_done_tasks = []

    for task in data.get("tasks", []):
        matches = task.get("kid_id") == person_id if is_kid else task.get("parent_id") == person_id
        if not matches:
            continue
        if task.get("status") == "Done":
            completed = task.get("completed_date")
            if completed and in_range(completed, monday, sunday):
                done_tasks.append(task)
        else:
            due = task.get("due_date")
            if due and in_range(due, monday, sunday):
                not_done_tasks.append(task)

    en_pages = 0
    tr_pages = 0
    for entry in data.get("reading_log", []):
        matches = entry.get("kid_id") == person_id if is_kid else entry.get("parent_id") == person_id
        if not matches:
            continue
        read_date = entry.get("read_date")
        if not read_date or not in_range(read_date, monday, sunday):
            continue
        pages = entry.get("pages_read", 0) or 0
        language = (entry.get("language") or "").lower()
        if language == "english":
            en_pages += pages
        elif language == "turkish":
            tr_pages += pages

    return {
        "done_tasks": done_tasks,
        "not_done_tasks": not_done_tasks,
        "en_pages": en_pages,
        "tr_pages": tr_pages,
    }


def in_range(date_str, monday, sunday):
    try:
        d = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return False
    return monday <= d <= sunday
