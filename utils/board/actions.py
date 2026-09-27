"""Ticking a task from the Board.

The canvas never decides whether a task may be completed. It asks; this module
answers, and the only thing that writes is `update_task`. The reasons are
concrete:

* `can_mark_done` is the app's rule for the whole codebase -- a task can be
  finished on or after its due date, and no more than OVERDUE_DAYS after it.
  Duplicating that rule in JavaScript would let the board drift away from the
  classic app the moment the rule changes.
* The payload already carries a `lock` per task, so the canvas can render a
  locked task honestly. It is a *display* of the rule, never a substitute for
  applying it. A browser that ignores `lock` gets no further than this module.
* An action can arrive twice. Streamlit holds a widget value until it changes,
  and a rerun replays it, so "already in the target state" is a normal case and
  must be a no-op rather than a second write.
* A write can fail quietly. `update_task` reports how many rows it changed, and
  a tap has to be able to say so, because the alternative is a board that
  congratulates you for something it did not do.
"""

from datetime import date

from utils import db_helpers
from utils.task_helpers import can_mark_done, get_effective_points

COMPLETE = "complete"
REOPEN = "reopen"

LOCK_MESSAGES = {
    "future": "Not due yet, so it can't be completed.",
    "overdue": "Too long overdue to complete now.",
}


WRITE_FAILED = "That didn't save. Try again."
NO_CONNECTION = "Couldn't reach the database. Check the connection and try again."


def _find(data: dict, task_id):
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def _write(task_id, updates) -> str | None:
    """Perform the write, and report failure in the only terms that matter.

    The real `update_task` hands back the rows Supabase actually changed. An
    empty list is how PostgREST says "nothing matched" -- a task deleted on
    another screen, or a row-level security policy quietly refusing the write --
    and at the call site that is indistinguishable from success unless somebody
    looks. Ignoring it is how a tap ends up announcing "done, 10 points" over a
    task that never moved, and the family only finds out by looking at the
    board again later.

    Returns None when the write went through, or a message when it did not.
    A falsy non-list return is treated as success: it is what the test harness
    and any caller that only wants fire-and-forget already produce, and reading
    it as failure would break them for no gain.
    """
    try:
        changed = db_helpers.update_task(task_id, updates)
    except Exception:
        # A tablet that has just lost wifi, or a key the database has stopped
        # accepting. A traceback on the wall is not an answer to a tap.
        return NO_CONNECTION
    if isinstance(changed, list) and not changed:
        return WRITE_FAILED
    return None


def complete_task(data: dict, task_id) -> dict:
    """Mark a task Done, if the app's rules allow it right now."""
    task = _find(data, task_id)
    if task is None:
        return {"ok": False, "task_id": task_id, "message": "That task no longer exists."}

    # Replaying the same action is the normal case on a rerun, not an error.
    if task.get("status") == "Done":
        return {
            "ok": True,
            "task_id": task_id,
            "noop": True,
            "points": get_effective_points(task),
            "message": f"{task.get('title')} is already done.",
        }

    allowed, reason = can_mark_done(task)
    if not allowed:
        return {
            "ok": False,
            "task_id": task_id,
            "lock": reason,
            "message": LOCK_MESSAGES.get(reason, "That task can't be completed now."),
        }

    today = date.today()
    year, week_num, _ = today.isocalendar()
    updates = {
        "status": "Done",
        "completed_date": today.isoformat(),
        "completed_week": f"{year}-W{week_num}",
    }
    failure = _write(task_id, updates)
    if failure:
        return {
            "ok": False,
            "task_id": task_id,
            "points": 0,
            "message": f"{task.get('title')}: {failure}",
        }

    # The points shown have to be the ones that will be awarded, which means
    # measuring after the write, not before it.
    awarded = get_effective_points({**task, **updates})
    return {
        "ok": True,
        "task_id": task_id,
        "points": awarded,
        "zero_points": awarded == 0,
        "message": (
            f"{task.get('title')} done, but 0 points: it was overdue."
            if awarded == 0
            else f"{task.get('title')} done. {awarded} points."
        ),
    }


def reopen_task(data: dict, task_id) -> dict:
    """Put a completed task back to Backlog.

    Undoing is always allowed. can_mark_done is a gate on earning points, not on
    correcting a mistake, and locking someone out of their own correction is how
    a rule like this turns into data nobody trusts.
    """
    task = _find(data, task_id)
    if task is None:
        return {"ok": False, "task_id": task_id, "message": "That task no longer exists."}

    if task.get("status") != "Done":
        return {
            "ok": True,
            "task_id": task_id,
            "noop": True,
            "message": f"{task.get('title')} is not done.",
        }

    failure = _write(
        task_id,
        {"status": "Backlog", "completed_date": None, "completed_week": None},
    )
    if failure:
        return {
            "ok": False,
            "task_id": task_id,
            "message": f"{task.get('title')}: {failure}",
        }
    return {
        "ok": True,
        "task_id": task_id,
        "message": f"{task.get('title')} moved back to Backlog.",
    }


VERBS = {COMPLETE: complete_task, REOPEN: reopen_task}


def apply_action(data: dict, action: dict | None) -> dict | None:
    """Run one board action, or do nothing when there is not a new one."""
    from utils.board.bridge import is_new, mark_handled

    if not is_new(action):
        return None

    verb = action.get("verb")
    handler = VERBS.get(verb)
    result = (
        handler(data, action.get("task_id"))
        if handler
        else {"ok": False, "message": f"Unknown action {verb!r}."}
    )
    # Marked only after the write is attempted, so a failed action is not
    # silently swallowed on the next rerun.
    mark_handled(action)
    return result
