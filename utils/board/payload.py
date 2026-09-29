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
# The strip shows the same week the bucket rules are built around. It used to
# offer today and the two days behind it only, on the theory that a future day
# is a dead end: a child walks onto it and every task refuses to be ticked.
# That is no longer a reason to hide the days, because a future row now says so
# itself -- it is locked and captioned "Not yet" rather than offering a live tick
# that the write path then withdraws. Looking ahead is the point of a week strip.
DISPLAY_ARC_PAST = 3
DISPLAY_ARC_FUTURE = 3

# Curated, not hashed. A wall display is looked at by name, so a person's colour
# has to be the same every render and recognisable at a distance.
#
# A colour is sent as the numbers that are an identity, not as a finished
# oklch() string, because lightness is lighting rather than identity and is left
# to the Board's --person-lightness token. At the night base the six come out
# vivid on a dark wall; the same values on a near-white one sit between 2.08:1
# and 2.59:1, so every lane label and flag becomes illegible in daylight and
# nothing catches it. Holding the base in one stylesheet line is what lets one
# person be both recognisable and legible in both modes.
#
# `lift` is the small per-person offset on top of that base. It is kept because
# these six are not only differently hued: a couple of them are neighbours on the
# wheel, and the difference in lightness is what keeps them tellable apart at
# distance. They are set so that the night values come out exactly as before.
ACCENT_HUES = [
    {"chroma": 0.17, "hue": 232, "lift": -0.01},
    {"chroma": 0.16, "hue": 62, "lift": 0.03},
    {"chroma": 0.18, "hue": 330, "lift": -0.01},
    {"chroma": 0.15, "hue": 150, "lift": 0.01},
    {"chroma": 0.16, "hue": 292, "lift": -0.02},
    {"chroma": 0.14, "hue": 96, "lift": 0.05},
]

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Only the three days around the anchor are worth a word; the rest of the week
# is named by its weekday. Spelling every cell out as a relative day would also
# have been wrong: with a seven-day strip the old three-case expression called
# every past day "Yesterday" and every future one "Tomorrow".
RELATIVE_LABELS = {-1: "Yesterday", 0: "Today", 1: "Tomorrow"}

# Order is the order a person wants them in: what went wrong, what is on today,
# what is coming.
GROUP_META = (
    ("overdue", "Past due", "late"),
    ("today", "Today", ""),
    ("later", "Coming up", ""),
    ("anytime", "Anytime", ""),
    # Last, and never named after a day any more. It is the finished half of
    # whichever day is on screen, so the day is already spelled out in the
    # neighbouring heading and repeating it here made "Done on Sun 27" read as
    # finished-on-Sunday for chores that were merely due Sunday.
    #
    # It exists so a tick can be undone: without it a completed task leaves the
    # board entirely and a mis-click on a wall tablet is only fixable by going
    # to the database.
    ("done", "Done", "done"),
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


def _undoable(on_date: date, rule_date: date) -> bool:
    """Whether a finished task on the day being looked at may be reopened.

    The real today and the OVERDUE_DAYS days before it are one window, and it is
    the window `can_mark_done` already lets work be completed in. Undo is scoped
    to the same days so the two cannot disagree: a chore you are allowed to
    finish from a given day, you are also allowed to correct from that day.

    This is deliberately the same `OVERDUE_DAYS` constant rather than a second
    number. Undo used to be the real today alone, which meant a chore finished
    from two days ago could not be undone from the day it was finished on --
    the wall showed it as a record while the very tick that created it was
    still inside the window a child could use on the real today.

    Days further back than the window, and days ahead of it, stay read-only.
    """
    return 0 <= (rule_date - on_date).days <= OVERDUE_DAYS


def _task_entry(task, on_date: date, rule_date: date) -> dict:
    """One task, with the tick rule already decided.

    `on_date` is the day being looked at and decides what the row is *about*:
    whether it reads as late, and which day it belongs to. `rule_date` decides
    whether it may be *ticked*, and is always the real today.

    Those used to be the same day, which meant the board asked a question on
    yesterday's behalf using tomorrow's rules. Browsing to a future day, a task
    due then passed the rule -- it was not late, and it was not in the past --
    so the row rendered a live tick that the write path then refused with "Not
    due yet". The wall offered an action and withdrew it on contact.

    Asking the real question -- may this be ticked *now* -- keeps the row and
    the write in agreement, and it is the honest one: you cannot tick tomorrow's
    chores today by looking at tomorrow.
    """
    allowed, reason = can_mark_done(task, on_date=rule_date)
    due = task.get("due_date")
    finished = task.get("status") == "Done"
    # What a click on this row should ask for. Stated here so the canvas never
    # infers it from the status and cannot offer the wrong verb.
    #
    # Undo belongs to today and the days before it inside the tick window; see
    # `_undoable`. Further back than that, a day is a record: the points from
    # those chores were counted in that week's total already, so reopening from
    # there rewrites a week that has been banked.
    #
    # This does not consult `allowed` on purpose. can_mark_done gates earning
    # points, not correcting a mistake, so a chore too far overdue to earn
    # anything is still undoable today. Worked out as a separate branch rather
    # than folded into the tick below, because a finished task that fell through
    # would be offered "complete" on any day it happened to be inside the window.
    if finished:
        action = "reopen" if _undoable(on_date, rule_date) else None
    else:
        action = "complete" if allowed else None
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "points": task.get("points", 0),
        "effective_points": get_effective_points(task),
        "status": task.get("status"),
        # Said outright rather than left for the canvas to read off `status`.
        # A finished task is not "late" and not "past due", whatever the tick
        # rule says about its date, and captioned "Past due" under a heading
        # that says "Done" reads as work that is still outstanding.
        "finished": finished,
        "due": due,
        "overdue": is_task_overdue(task),
        # Due in the past but still inside the tick window: tickable, but it is
        # behind. Distinct from `overdue`, which means the window has passed.
        "late": bool(due and due < on_date.isoformat() and not finished),
        # None when the task may be ticked. "future" / "overdue" otherwise, so
        # the canvas can explain a locked task instead of just greying it out.
        "lock": None if allowed else reason,
        "action": action,
    }


def _groups(buckets, labels: dict | None = None) -> list[dict]:
    """Shape the buckets into renderable groups.

    A group with nothing in it is left out entirely, so the canvas renders
    `groups` directly rather than having to hide empty sections.

    Every task is listed. Groups used to be capped here and the overflow was
    summarised as "+6 more, shown in the classic app", which quietly hid real
    work: with a Done cap of 8, a child with 14 finished chores on the 27th was
    missing six of them from the wall with nothing on the board to say which
    six. A cap that hides a child's finished work to keep a screen tidy is the
    wrong trade for a display the point of which is to show what was done. The
    stage scrolls, so a long day gets longer rather than becoming a lie.

    `labels` renames groups after the day being looked at.
    """
    labels = labels or {}
    groups = []
    for key, name, tone in GROUP_META:
        name = labels.get(key, name)
        tasks = buckets.get(key) or []
        if not tasks:
            continue
        groups.append(
            {
                "key": key,
                "name": name,
                "tone": tone,
                "tasks": sorted(tasks, key=_sort_key),
                "total": len(tasks),
            }
        )
    return groups


def _sort_key(entry: dict) -> tuple:
    """Alphabetical order for a group, on the title as a person reads it.

    Two tasks a row makes position the only way to find one, and a wall list
    that reorders itself whenever a task is ticked or a day is chosen cannot be
    scanned at all. Sorting here rather than in the canvas keeps the order the
    same everywhere the group is shown, and keeps it assertable without a
    browser.

    Casefolded so `Bed, make` and `Bathroom` do not sort by ASCII value and put
    every capitalised title first, and whitespace collapsed so a stray space
    typed into the form cannot push a task to the front. A missing title sorts
    as empty rather than raising, because the form allows it.

    The id is the final tie-break so that recurring chores sharing a title keep
    one fixed order instead of following whatever order the database happened to
    return that time -- a chore is pre-generated for every upcoming day, so that
    order is not stable between reads, and a row that swaps under a finger is
    worse than an arbitrary one. A non-numeric id sorts with the rest at the
    front, which keeps the comparison total instead of raising on mixed data.
    """
    text = " ".join((entry.get("title") or "").split())
    task_id = entry.get("id")
    if not isinstance(task_id, int):
        # Numeric ids always come from the database and are never negative, so
        # a text id sorts after them and still compares as a string.
        task_id = str(task_id)
        return (text.casefold(), text, 1, task_id)
    return (text.casefold(), text, 0, task_id)


def _bucket(tasks, on_date: date, rule_date: date | None = None) -> dict:
    """Split one person's open tasks by when they are pressing.

    "anytime" holds tasks with no due date. They are dropped from the day
    counts by definition, but `can_mark_done` has always allowed them, so hiding
    them from the board would make live work look like it does not exist.

    `rule_date` is the real today and only reaches `_task_entry`; the splitting
    itself is all relative to the day being looked at.
    """
    rule_date = rule_date or on_date
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
            # Keyed on the day the work was *for*, not the day it was finished.
            #
            # 481 of 1158 completed chores in the live data were ticked on a day
            # other than their due date, so keying the group on completion date
            # filed a chore due the 27th under the 29th, next to work that had
            # nothing to do with it. Undoing it from the 29th then cleared the
            # completion and the task left the day you were looking at entirely,
            # reappearing on the 27th where nobody was. One task, one day.
            if due == today:
                out["done"].append(_task_entry(task, on_date, rule_date))
            continue
        if is_task_overdue(task):
            out["overdue"].append(_task_entry(task, on_date, rule_date))
        elif not due:
            out["anytime"].append(_task_entry(task, on_date, rule_date))
        elif due <= today:
            out["today"].append(_task_entry(task, on_date, rule_date))
        elif due <= horizon:
            out["later"].append(_task_entry(task, on_date, rule_date))
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
                # Two flags, because "today" and "the day you are looking at"
                # are two different days as soon as you browse back. They used to
                # share one, so selecting yesterday enlarged Monday, filled the
                # arc up to Monday, and called Monday "Today" -- while the real
                # Tuesday sat beside it unlabelled. The wall was pointing at the
                # wrong day and calling it the right one.
                "is_today": day == anchor_date,
                "is_selected": day == on_date,
                "relative": RELATIVE_LABELS.get(offset),
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
                "accent": dict(ACCENT_HUES[index % len(ACCENT_HUES)]),
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
                "accent": dict(ACCENT_HUES[index % len(ACCENT_HUES)]),
                "weekly_points": get_weekly_points_for_parent(data, parent["id"]),
                "total_points": get_total_points_for_parent(data, parent["id"]),
                "due_today": today_due.get(key, 0),
                "done_today": today_done.get(key, 0),
                "overdue": overdue.get(key, 0),
            }
        )
    return people


def _build_lane(
    kind: str,
    person: dict,
    tasks: list,
    on_date: date,
    labels: dict,
    rule_date: date | None = None,
) -> dict:
    """One person's column of work, for a child or a parent alike."""
    owner = "kid_id" if kind == "kid" else "parent_id"
    own = [t for t in tasks if t.get(owner) == person["id"]]
    buckets = _bucket(own, on_date, rule_date)
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
        "groups": _groups(buckets, labels),
    }


def build_board_payload(
    data,
    on_date: date | None = None,
    flash: dict | None = None,
    compact: bool = False,
) -> dict:
    """The whole Board, as JSON-ready primitives.

    Reports what is due, what is done, and what may be ticked, and issues no
    writes. Each task carries the `action` it would send, decided here by the
    same rules the write path enforces, so the canvas never has to work out what
    is allowed. `tools/spike_check.py` drives the resulting round trip in a
    real browser.

    The mode is deliberately not here. It is a per-device display preference that
    the frame and the app both read out of the same localStorage key, and putting
    it in this payload would mean Python had to know the user's choice -- which it
    cannot, because only the browser can read localStorage. The result would be
    the app asserting "night" at a tablet that had been left in day mode, on
    every reload. One source of truth, read by both documents, and the two
    cannot disagree.
    """

    on_date = on_date or date.today()
    tasks = data.get("tasks", [])
    iso = on_date.isoformat()
    real_today = date.today()
    is_selected_today = on_date == real_today
    day_label = f"{WEEKDAYS[on_date.weekday()]} {on_date.day} {on_date:%b %Y}"
    # The wall is a short-horizon action surface, not an archive. A day shows
    # the work due on it, and the finished work from that same day.
    #
    # It used to also pull in anything *completed* on the day, which is how a
    # chore due Sunday and ticked Monday came to sit under Monday. That put
    # someone else's date on it: a task that is not due today has no business in
    # today's list, and undoing it from the wrong day moved it across the strip
    # instead of bringing it back. A task belongs to its own day or to no day.
    visible_tasks = (
        [task for task in tasks if task.get("due_date") == iso] if compact else tasks
    )
    group_labels = {}
    if not is_selected_today:
        # The day's own workload column is the only heading that needs the date.
        # "Today" and "Done today" used to be hardcoded, so choosing any other
        # day produced a column headed "Today" listing that day's work -- a wall
        # board contradicting itself about which day it was on.
        group_labels["today"] = day_label

    # Kids and parents get lanes too. They are the same shape of work, and
    # leaving parents out meant two of the five buttons in the rail fell through
    # to the everyone view. Identity is (kind, id) rather than id alone: the two
    # tables number independently, so kid 1 and parent 1 are different people.
    lanes = [
        _build_lane("kid", kid, visible_tasks, on_date, group_labels, rule_date=real_today)
        for kid in data.get("kids", [])
    ] + [
        _build_lane("parent", parent, visible_tasks, on_date, group_labels, rule_date=real_today)
        for parent in data.get("parents", [])
    ]

    day_tasks = [t for t in visible_tasks if t.get("due_date") == iso]
    open_today = [t for t in day_tasks if t.get("status") != "Done"]
    # Counted off the day's own tasks rather than the whole visible set, so the
    # header number and the Done group agree, and so the unfiltered everyone
    # view does not count every finished chore in the family. Both sides are
    # keyed on the due date now, so "6 done" and the six rows underneath it are
    # the same six tasks.
    done_today = [t for t in day_tasks if t.get("status") == "Done"]
    all_overdue = [t for t in tasks if is_task_overdue(t)]

    return {
        "generated_at": on_date.isoformat(),
        # The result of the last tick, shown once. Null on every other render.
        "flash": flash,
        # The header's date is always the real one. It used to follow the day
        # picker, so browsing to another day rewrote the date under the clock on
        # the wall -- the one piece of the board that cannot mean anything else.
        "today": real_today.isoformat(),
        "today_label": f"{WEEKDAYS[real_today.weekday()]} {real_today.day} {real_today:%b %Y}",
        # The day actually being looked at, and whether that is today.
        "selected": iso,
        "selected_label": day_label,
        "is_selected_today": is_selected_today,
        "overdue_days": OVERDUE_DAYS,
        "arc": build_arc(tasks, on_date, anchor_date=real_today),
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
