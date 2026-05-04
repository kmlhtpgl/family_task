from utils.task_helpers import get_total_points_for_kid, get_total_points_for_parent


def get_kid_achievements(data, kid_id):
    """
    Calculate achievements for a child based on completed tasks and books.
    Returns a list of achievement dicts with icon and label.
    """
    achievements = []

    total_points = get_total_points_for_kid(data, kid_id)

    kid_tasks = [t for t in data["tasks"] if t.get("kid_id") == kid_id and t.get("status") == "Done"]
    kid_books = [b for b in data["books"] if b.get("kid_id") == kid_id and b.get("status") == "Finished"]

    total_tasks_done = len(kid_tasks)
    total_books_done = len(kid_books)

    points_milestones = [
        (10, "🌟 First 10 Points"),
        (50, "⭐ 50 Points Club"),
        (100, "🏆 100 Points Master"),
        (250, "👑 250 Points Legend"),
        (500, "💎 500 Points Champion"),
    ]

    for threshold, label in points_milestones:
        if total_points >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    task_milestones = [
        (5, "✅ 5 Tasks Done"),
        (20, "🎯 20 Tasks Done"),
        (50, "🏅 50 Tasks Done"),
        (100, "🎖️ 100 Tasks Done"),
    ]

    for threshold, label in task_milestones:
        if total_tasks_done >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    book_milestones = [
        (1, "📖 First Book"),
        (5, "📚 5 Books Read"),
        (10, "📕 10 Books Read"),
        (25, "📗 Bookworm"),
    ]

    for threshold, label in book_milestones:
        if total_books_done >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    streak = calculate_task_streak(data, kid_id, is_parent=False)

    if streak >= 3:
        achievements.append({"icon": "🔥", "label": f"{streak} Day Streak"})

    if streak >= 7:
        achievements.append({"icon": "💪", "label": "Week Warrior"})

    if total_tasks_done > 0 and total_books_done > 0:
        achievements.append({"icon": "🌈", "label": "Task & Reader"})

    return achievements


def get_parent_achievements(data, parent_id):
    """
    Calculate achievements for a parent based on completed tasks and books.
    """
    achievements = []

    total_points = get_total_points_for_parent(data, parent_id)

    parent_tasks = [t for t in data["tasks"] if t.get("parent_id") == parent_id and t.get("status") == "Done"]
    parent_books = [b for b in data["books"] if b.get("parent_id") == parent_id and b.get("status") == "Finished"]

    total_tasks_done = len(parent_tasks)
    total_books_done = len(parent_books)

    points_milestones = [
        (10, "🌟 First 10 Points"),
        (50, "⭐ 50 Points Club"),
        (100, "🏆 100 Points Master"),
        (250, "👑 250 Points Legend"),
    ]

    for threshold, label in points_milestones:
        if total_points >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    task_milestones = [
        (5, "✅ 5 Tasks Done"),
        (20, "🎯 20 Tasks Done"),
        (50, "🏅 50 Tasks Done"),
    ]

    for threshold, label in task_milestones:
        if total_tasks_done >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    book_milestones = [
        (1, "📖 First Book"),
        (5, "📚 5 Books Read"),
        (10, "📕 10 Books Read"),
    ]

    for threshold, label in book_milestones:
        if total_books_done >= threshold:
            achievements.append({"icon": label.split(" ")[0], "label": label.split(" ", 1)[1]})

    streak = calculate_task_streak(data, parent_id, is_parent=True)

    if streak >= 3:
        achievements.append({"icon": "🔥", "label": f"{streak} Day Streak"})

    if total_tasks_done > 0 and total_books_done > 0:
        achievements.append({"icon": "🌈", "label": "Task & Reader"})

    return achievements


def calculate_task_streak(data, person_id, is_parent=False):
    """
    Calculate the current streak of consecutive days with completed tasks.
    """
    from datetime import date, timedelta

    if is_parent:
        completed_tasks = [
            t for t in data["tasks"]
            if t.get("parent_id") == person_id
            and t.get("status") == "Done"
            and t.get("completed_date")
        ]
    else:
        completed_tasks = [
            t for t in data["tasks"]
            if t.get("kid_id") == person_id
            and t.get("status") == "Done"
            and t.get("completed_date")
        ]

    if not completed_tasks:
        return 0

    completed_dates = set(t["completed_date"] for t in completed_tasks)

    streak = 0
    current_date = date.today()

    while current_date.isoformat() in completed_dates:
        streak += 1
        current_date -= timedelta(days=1)

    if streak == 0 and (current_date - timedelta(days=1)).isoformat() in completed_dates:
        current_date -= timedelta(days=1)

        while current_date.isoformat() in completed_dates:
            streak += 1
            current_date -= timedelta(days=1)

    return streak
