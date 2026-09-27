"""Turns app data into the one dict the Board's canvas renders.

Pure on purpose: it takes the `get_all_data()` dict and a date, and returns
plain JSON. Nothing here writes, and nothing here reads session state, so the
whole payload can be asserted in tests without Supabase or a browser.

The rules stay in Python. `can_mark_done`, `get_effective_points` and
`OVERDUE_DAYS` are the authority on whether a task may be ticked and what it is
worth; the canvas is told the answer per task rather than being trusted to
recompute it in JavaScript.
"""

from datetime import date, timedelta

from utils.task_helpers import (
    OVERDUE_DAYS,
    can_mark_done,
    get_effective_points,
    get_total_points_for_kid,
    get_total_points_for_parent,
    get_weekly_points_for_kid,
    get_weekly_points_for_parent,
    is_task_overdue,
)

# Past days behind today, future days ahead. Three either side reads as a week
# on a wall without turning into a month strip nobody can scan from across a room.
ARC_PAST = 3
ARC_FUTURE = 3
# The compact picker shows only the actionable three-day window. The task list
# keeps the existing three-day future horizon for recurring-work accounting.
DISPLAY_ARC_PAST = 1
DISPLAY_ARC_FUTURE = 1

# Curated, not hashed. A wall display is looked at by name, so a person's colour
# has to be the same every render and recognisable at a distance.
ACCENTS = [
    "oklch(0.72 0.17 232)",
    "oklch(0.76 0.16 62)",
    "oklch(0.72 0.18 330)",
    "oklch(0.74 0.15 150)",
    "oklch(0.71 0.16 292)",
    "oklch(0.78 0.14 96)",
]

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# A wall display is read from across a room, so a lane cannot be an unbounded
# list. The cap is decided here rather than in the canvas so it can be asserted
# without a browser, and so the "+N more" count is computed from the same list
# that was truncated.
GROUP_LIMITS = {"overdue": 6, "today": 14, "later": 6, "anytime": 6, "done": 8}

# Order is the order a person wants them in: what went wrong, what is on today,
# what is coming.
GROUP_META = (
    ("overdue", "Past due", "late"),
    ("today", "Today", ""),
    ("later", "Coming up", ""),
    ("anytime", "Anytime", ""),
    # Last, and only ever today's. It exists so a tick can be undone: without
    # it a completed task leaves the board entirely and a mis-click on a wall
    # tablet is only fixable by going to the database.
    ("done", "Done today", "done"),
)


def clean_name(name: str | None) -> str:
    """Names arrive from a free-text form and keep whatever whitespace was typed.
    One real child is stored as "           Ekrem", which pushed the name off
    centre in the rail and into the initial of a wide layout."""
    return " ".join((name or "").split())


def initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _task_entry(task, on_date: date) -> dict:
    """One task, with the tick rule already decided."""
    allowed, reason = can_mark_done(task, on_date=on_date)
    due = task.get("due_date")
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "points": task.get("points", 0),
        "effective_points": get_effective_points(task),
        "status": task.get("status"),
        "due": due,
        "overdue": is_task_overdue(task),
        # Due in the past but still inside the tick window: tickable, but it is
        # behind. Distinct from `overdue`, which means the window has passed.
        "late": bool(due and due < on_date.isoformat() and task.get("status") != "Done"),
        # None when the task may be ticked. "future" / "overdue" otherwise, so
        # the canvas can explain a locked task instead of just greying it out.
        "lock": None if allowed else reason,
        # What a click on this row should ask for. Stated here so the canvas
        # never infers it from the status and cannot offer the wrong verb. A
        # completed task is always reopenable: undoing a mis-click must not be
        # gated by the same rule that gates earning points.
        "action": (
            "reopen"
            if task.get("status") == "Done"
            else ("complete" if allowed else None)
        ),
    }


def _groups(buckets) -> list[dict]:
    """Shape the buckets into renderable groups, capped for a wall display.

    A group with nothing in it is left out entirely, so the canvas renders
    `groups` directly rather than having to hide empty sections. `hidden` is
    the number that did not fit, and `total` is how many exist, so the canvas
    can say "17 more past due" without being told anything it could get wrong.
    """
    groups = []
    for key, name, tone in GROUP_META:
        tasks = buckets.get(key) or []
        if not tasks:
            continue
        limit = GROUP_LIMITS[key]
        groups.append(
            {
                "key": key,
                "name": name,
                "tone": tone,
                "tasks": tasks[:limit],
                "total": len(tasks),
                "hidden": max(0, len(tasks) - limit),
            }
        )
    return groups


def _bucket(tasks, on_date: date) -> dict:
    """Split one person's open tasks by when they are pressing.

    "anytime" holds tasks with no due date. They are dropped from the day
    counts by definition, but `can_mark_done` has always allowed them, so hiding
    them from the board would make live work look like it does not exist.
    """
    out = {
        "overdue": [],
        "today": [],
        "later": [],
        "anytime": [],
        "done": [],
        "scheduled": 0,
    }
    # A task stays tickable until OVERDUE_DAYS have passed, so anything due
    # inside that window is still live work. The late-but-tickable tail of the
    # past therefore belongs in "today" alongside the rest of what needs doing
    # now; a bucket it matches none of is a bucket it disappears from. Anything
    # older than the window is caught as overdue above, so the split here needs
    # no date arithmetic of its own.
    today = on_date.isoformat()
    # This app pre-generates recurring chores far into the future -- one child
    # has 872 of them. Listing them as "coming up" would be a wall of noise and
    # would push the actual day off the board, so anything past the arc horizon
    # is counted rather than listed. The count is still reported, so nothing is
    # hidden.
    horizon = (on_date + timedelta(days=ARC_FUTURE)).isoformat()
    for task in tasks:
        due = task.get("due_date")
        if task.get("status") == "Done":
            if task.get("completed_date") == today:
                out["done"].append(_task_entry(task, on_date))
            continue
        if is_task_overdue(task):
            out["overdue"].append(_task_entry(task, on_date))
        elif not due:
            out["anytime"].append(_task_entry(task, on_date))
        elif due <= today:
            out["today"].append(_task_entry(task, on_date))
        elif due <= horizon:
            out["later"].append(_task_entry(task, on_date))
        else:
            out["scheduled"] += 1
    return out


def build_arc(tasks, on_date: date, anchor_date: date | None = None) -> list[dict]:
    """The day strip: one cell per day, each carrying its own load."""
    anchor_date = anchor_date or on_date
    by_day: dict[str, list] = {}
    for task in tasks:
        due = task.get("due_date")
        if due:
            by_day.setdefault(due, []).append(task)

    arc = []
    for offset in range(-DISPLAY_ARC_PAST, DISPLAY_ARC_FUTURE + 1):
        day = anchor_date + timedelta(days=offset)
        iso = day.isoformat()
        scheduled = by_day.get(iso, [])
        # Of the work scheduled for this day, how much is finished.
        #
        # Counting by completion date instead would be meaningless here: a chore
        # done on Saturday may have been due on Thursday, so "completed that day"
        # over "due that day" produced figures like 250% on a real wall board.
        # Both sides here are tasks due on this day, so the fraction is bounded
        # and means what it looks like it means.
        open_count = sum(1 for t in scheduled if t.get("status") != "Done")
        done_count = len(scheduled) - open_count
        arc.append(
            {
                "date": iso,
                "label": WEEKDAYS[day.weekday()],
                "day": day.day,
                "is_today": day == on_date,
                "is_real_today": day == anchor_date,
                "relative": "Yesterday" if offset == -1 else ("Today" if offset == 0 else "Tomorrow"),
                "is_past": offset < 0,
                "is_future": offset > 0,
                "total": len(scheduled),
                "open": open_count,
                "done": done_count,
                # None rather than 0 for a day with nothing on it, so the canvas
                # can render an empty day as empty instead of as "complete".
                "ratio": (done_count / len(scheduled)) if scheduled else None,
            }
        )
    return arc


def build_people(data, tasks, on_date: date) -> list[dict]:
    iso = on_date.isoformat()
    today_due: dict[str, int] = {}
    today_done: dict[str, int] = {}
    overdue: dict[str, int] = {}

    for task in tasks:
        # Kids and parents live in different tables and their ids are
        # independent, so kid 1 and parent 1 are different people who happen to
        # share a number. Keying on the id alone silently merged their counts.
        owners = []
        if task.get("kid_id") is not None:
            owners.append(f"kid:{task['kid_id']}")
        if task.get("parent_id") is not None:
            owners.append(f"parent:{task['parent_id']}")
        for key in owners:
            if task.get("status") == "Done" and task.get("completed_date") == iso:
                today_done[key] = today_done.get(key, 0) + 1
            elif task.get("due_date") == iso:
                today_due[key] = today_due.get(key, 0) + 1
            if is_task_overdue(task):
                overdue[key] = overdue.get(key, 0) + 1

    people = []
    for index, kid in enumerate(data.get("kids", [])):
        key = f"kid:{kid['id']}"
        people.append(
            {
                "id": kid["id"],
                "kind": "kid",
                "key": key,
                "name": clean_name(kid.get("name")),
                "initials": initials(kid.get("name")),
                "meta": f"age {kid.get('age')}" if kid.get("age") else "",
                "photo": kid.get("photo_path"),
                "accent": ACCENTS[index % len(ACCENTS)],
                "weekly_points": get_weekly_points_for_kid(data, kid["id"]),
                "total_points": get_total_points_for_kid(data, kid["id"]),
                "due_today": today_due.get(key, 0),
                "done_today": today_done.get(key, 0),
                "overdue": overdue.get(key, 0),
            }
        )

    for index, parent in enumerate(data.get("parents", []), start=len(people)):
        key = f"parent:{parent['id']}"
        people.append(
            {
                "id": parent["id"],
                "kind": "parent",
                "key": key,
                "name": clean_name(parent.get("name")),
                "initials": initials(parent.get("name")),
                "meta": "",
                "photo": parent.get("photo_url"),
                "accent": ACCENTS[index % len(ACCENTS)],
                "weekly_points": get_weekly_points_for_parent(data, parent["id"]),
                "total_points": get_total_points_for_parent(data, parent["id"]),
                "due_today": today_due.get(key, 0),
                "done_today": today_done.get(key, 0),
                "overdue": overdue.get(key, 0),
            }
        )
    return people


def _build_lane(kind: str, person: dict, tasks: list, on_date: date) -> dict:
    """One person's column of work, for a child or a parent alike."""
    owner = "kid_id" if kind == "kid" else "parent_id"
    own = [t for t in tasks if t.get(owner) == person["id"]]
    buckets = _bucket(own, on_date)
    name = person.get("name")
    return {
        "kind": kind,
        "person_id": person["id"],
        # Composite because the two tables number independently: kid 1 and
        # parent 1 must not resolve to the same selection.
        "key": f"{kind}:{person['id']}",
        "name": clean_name(name),
        "initials": initials(name),
        "photo": person.get("photo_path") or person.get("photo_url"),
        # Every bucket accounted for, including the future chores that are
        # counted rather than listed.
        "counts": {
            key: (len(items) if isinstance(items, list) else items)
            for key, items in buckets.items()
        },
        "scheduled": buckets["scheduled"],
        "groups": _groups(buckets),
    }


def build_board_payload(data, on_date: date | None = None, flash: dict | None = None) -> dict:
    """The whole Board, as JSON-ready primitives.

    Reports what is due, what is done, and what may be ticked, and issues no
    writes. Each task carries the `action` it would send, decided here by the
    same rules the write path enforces, so the canvas never has to work out what
    is allowed. `tools/spike_check.py` drives the resulting round trip in a
    real browser.
    """
    on_date = on_date or date.today()
    tasks = data.get("tasks", [])
    iso = on_date.isoformat()

    # Kids and parents get lanes too. They are the same shape of work, and
    # leaving parents out meant two of the five buttons in the rail fell through
    # to the everyone view. Identity is (kind, id) rather than id alone: the two
    # tables number independently, so kid 1 and parent 1 are different people.
    lanes = [
        _build_lane("kid", kid, tasks, on_date) for kid in data.get("kids", [])
    ] + [
        _build_lane("parent", parent, tasks, on_date)
        for parent in data.get("parents", [])
    ]

    open_today = [t for t in tasks if t.get("due_date") == iso and t.get("status") != "Done"]
    done_today = [
        t
        for t in tasks
        if t.get("status") == "Done" and t.get("completed_date") == iso
    ]
    all_overdue = [t for t in tasks if is_task_overdue(t)]

    return {
        "generated_at": on_date.isoformat(),
        # The result of the last tick, shown once. Null on every other render.
        "flash": flash,
        "today": iso,
        "today_label": f"{WEEKDAYS[on_date.weekday()]} {on_date.day} {on_date:%b %Y}",
        "overdue_days": OVERDUE_DAYS,
        "arc": build_arc(tasks, on_date, anchor_date=date.today()),
        "people": build_people(data, tasks, on_date),
        "lanes": lanes,
        "totals": {
            "kids": len(data.get("kids", [])),
            "parents": len(data.get("parents", [])),
            "open_today": len(open_today),
            "done_today": len(done_today),
            "overdue": len(all_overdue),
            # Share of today's work that is finished, counting both the tasks
            # already done and the ones still open.
            "progress": (
                len(done_today) / (len(done_today) + len(open_today))
                if (open_today or done_today)
                else None
            ),
        },
    }
