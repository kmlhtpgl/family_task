from utils.data_helpers import today_string, current_week_key


TASK_STATUSES = ["Backlog", "In Progress", "Done"]


def move_task(task, new_status):
    """
    Moves a task to a new status.

    If the task is moved to Done, completion date and week are saved.
    If it is moved out of Done, completion information is removed.
    """
    old_status = task["status"]

    if old_status == new_status:
        return False

    task["status"] = new_status

    if old_status != "Done" and new_status == "Done":
        task["completed_date"] = today_string()
        task["completed_week"] = current_week_key()

    elif old_status == "Done" and new_status != "Done":
        task.pop("completed_date", None)
        task.pop("completed_week", None)

    return True


def get_today_tasks(data):
    """
    Returns unfinished tasks due today (kids and parents).
    """
    return [
        task for task in data["tasks"]
        if task.get("due_date") == today_string()
        and task.get("status") != "Done"
    ]


def get_weekly_points_for_kid(data, kid_id):
    """
    Calculates this week's points for one child.
    """
    week = current_week_key()

    return sum(
        task.get("points", 0)
        for task in data["tasks"]
        if task.get("kid_id") == kid_id
        and task.get("status") == "Done"
        and task.get("completed_week") == week
    )


def get_weekly_points_for_parent(data, parent_id):
    """
    Calculates this week's points for one parent.
    """
    week = current_week_key()

    return sum(
        task.get("points", 0)
        for task in data["tasks"]
        if task.get("parent_id") == parent_id
        and task.get("status") == "Done"
        and task.get("completed_week") == week
    )


def get_total_points_for_kid(data, kid_id):
    """
    Calculates all completed task points for one child.
    """
    return sum(
        task.get("points", 0)
        for task in data["tasks"]
        if task.get("kid_id") == kid_id
        and task.get("status") == "Done"
    )


def get_total_points_for_parent(data, parent_id):
    """
    Calculates all completed task points for one parent.
    """
    return sum(
        task.get("points", 0)
        for task in data["tasks"]
        if task.get("parent_id") == parent_id
        and task.get("status") == "Done"
    )


RANKS = [
    ("Iron", 0, 9, "🪨"),
    ("Iron", 10, 19, "🪨"),
    ("Iron", 20, 29, "🪨"),
    ("Bronze", 30, 49, "🥉"),
    ("Bronze", 50, 69, "🥉"),
    ("Bronze", 70, 89, "🥉"),
    ("Silver", 90, 119, "🥈"),
    ("Silver", 120, 149, "🥈"),
    ("Silver", 150, 179, "🥈"),
    ("Gold", 180, 224, "🥇"),
    ("Gold", 225, 269, "🥇"),
    ("Gold", 270, 314, "🥇"),
    ("Platinum", 315, 374, "💎"),
    ("Platinum", 375, 434, "💎"),
    ("Platinum", 435, 494, "💎"),
    ("Diamond", 495, 569, "💠"),
    ("Diamond", 570, 644, "💠"),
    ("Diamond", 645, 719, "💠"),
    ("Ascendant", 720, 809, "🌟"),
    ("Ascendant", 810, 899, "🌟"),
    ("Ascendant", 900, 989, "🌟"),
    ("Immortal", 990, 1099, "🔥"),
    ("Immortal", 1100, 1209, "🔥"),
    ("Immortal", 1210, 1319, "🔥"),
    ("Radiant", 1320, float("inf"), "👑"),
]


def get_rank(points):
    for name, low, high, icon in RANKS:
        if low <= points <= high:
            tier = name
            if name == "Radiant":
                return tier, icon
            if name == "Immortal":
                sub = (points - low) // 110 + 1
                return f"{tier} {sub}", icon
            # Iron - Ascendant: 3 sub-ranks
            spread = high - low + 1
            step = spread // 3
            sub = (points - low) // step + 1
            return f"{tier} {sub}", icon
    return "Unranked", "❓"


def get_weekly_leaderboard(data):
    """
    Returns children ordered by their weekly points.
    """
    scores = []

    for kid in data["kids"]:
        scores.append(
            {
                "name": kid["name"],
                "points": get_weekly_points_for_kid(data, kid["id"])
            }
        )

    return sorted(scores, key=lambda item: item["points"], reverse=True)


def get_weekly_parent_leaderboard(data):
    """
    Returns parents ordered by their weekly points.
    """
    scores = []

    for parent in data.get("parents", []):
        scores.append(
            {
                "name": parent["name"],
                "points": get_weekly_points_for_parent(data, parent["id"])
            }
        )

    return sorted(scores, key=lambda item: item["points"], reverse=True)
