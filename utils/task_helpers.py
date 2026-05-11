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
