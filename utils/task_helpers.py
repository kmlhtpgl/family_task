from datetime import date, timedelta

from utils.data_helpers import today_string, current_week_key


TASK_STATUSES = ["Backlog", "In Progress", "Done"]

OVERDUE_DAYS = 2


def get_effective_points(task):
    """
    Returns task points, applying the overdue penalty.
    If a Done task was completed more than OVERDUE_DAYS after its due date,
    the points are reduced to 0.
    """
    points = task.get("points", 0)
    if task.get("status") != "Done":
        return points
    due = task.get("due_date")
    completed = task.get("completed_date")
    if not due or not completed:
        return points
    try:
        due_date = date.fromisoformat(due)
        completed_date = date.fromisoformat(completed)
        if (completed_date - due_date).days > OVERDUE_DAYS:
            return 0
    except (ValueError, TypeError):
        pass
    return points


def is_task_overdue(task):
    """Check if a task is overdue by more than OVERDUE_DAYS."""
    due = task.get("due_date")
    if not due:
        return False
    try:
        due_date = date.fromisoformat(due)
        return (date.today() - due_date).days > OVERDUE_DAYS and task.get("status") != "Done"
    except (ValueError, TypeError):
        return False


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
    Calculates this week's points for one child (with overdue penalty).
    """
    week = current_week_key()

    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("kid_id") == kid_id
        and task.get("status") == "Done"
        and task.get("completed_week") == week
    )


def get_weekly_points_for_parent(data, parent_id):
    """
    Calculates this week's points for one parent (with overdue penalty).
    """
    week = current_week_key()

    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("parent_id") == parent_id
        and task.get("status") == "Done"
        and task.get("completed_week") == week
    )


def get_total_points_for_kid(data, kid_id):
    """
    Calculates all completed task points for one child (with overdue penalty).
    """
    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("kid_id") == kid_id
        and task.get("status") == "Done"
    )


def get_total_points_for_parent(data, parent_id):
    """
    Calculates all completed task points for one parent (with overdue penalty).
    """
    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("parent_id") == parent_id
        and task.get("status") == "Done"
    )


def get_monthly_points_for_kid(data, kid_id, year, month):
    """
    Calculates points for one child in a specific month (with overdue penalty).
    year: int, month: int (1-12)
    """
    month_str = f"{year:04d}-{month:02d}"
    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("kid_id") == kid_id
        and task.get("status") == "Done"
        and task.get("completed_date", "").startswith(month_str)
    )


def get_monthly_points_for_parent(data, parent_id, year, month):
    """
    Calculates points for one parent in a specific month (with overdue penalty).
    """
    month_str = f"{year:04d}-{month:02d}"
    return sum(
        get_effective_points(task)
        for task in data["tasks"]
        if task.get("parent_id") == parent_id
        and task.get("status") == "Done"
        and task.get("completed_date", "").startswith(month_str)
    )


def get_monthly_points_for_all(data, year, month):
    """
    Calculates total points for everyone in a specific month.
    Returns dict of {person_id: points} with a type flag.
    """
    month_str = f"{year:04d}-{month:02d}"
    scores = {}

    for kid in data["kids"]:
        pts = get_monthly_points_for_kid(data, kid["id"], year, month)
        if pts > 0:
            scores[kid["id"]] = {"name": kid["name"], "points": pts, "type": "kid"}

    for parent in data.get("parents", []):
        pts = get_monthly_points_for_parent(data, parent["id"], year, month)
        if pts > 0:
            scores[parent["id"]] = {"name": parent["name"], "points": pts, "type": "parent"}

    return scores


def get_monthly_adjustment_points(data, person_id, person_type, year, month):
    """
    Sums bonus/penalty point adjustments for a person in a specific month.
    Adjustments only affect monthly reward calculations.
    """
    month_str = f"{year:04d}-{month:02d}"
    total = 0
    for adj in data.get("points_adjustments", []):
        if adj.get("person_id") == person_id and adj.get("person_type") == person_type:
            created = adj.get("created_at", "")
            if created.startswith(month_str):
                total += adj.get("points", 0)
    return total


def get_overdue_task_count(data, person_id, is_kid=True):
    """Count how many overdue tasks a person has."""
    count = 0
    for task in data["tasks"]:
        if is_kid and task.get("kid_id") != person_id:
            continue
        if not is_kid and task.get("parent_id") != person_id:
            continue
        if is_task_overdue(task):
            count += 1
    return count


TIERS = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal"]
TIER_ICONS = {"Iron": "🪨", "Bronze": "🥉", "Silver": "🥈", "Gold": "🥇", "Platinum": "💎", "Diamond": "💠", "Ascendant": "🌟", "Immortal": "🔥", "Radiant": "👑"}
PTS_PER_SUB_RANK = 100
SUBS_PER_TIER = 3
PTS_PER_TIER = PTS_PER_SUB_RANK * SUBS_PER_TIER  # 300


def get_rank(points):
    max_tier_index = PTS_PER_TIER * len(TIERS)  # 2400
    if points >= max_tier_index:
        return "Radiant", TIER_ICONS["Radiant"]
    tier_index = points // PTS_PER_TIER
    sub_index = (points % PTS_PER_TIER) // PTS_PER_SUB_RANK + 1
    tier_name = TIERS[tier_index]
    return f"{tier_name} {sub_index}", TIER_ICONS[tier_name]


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
