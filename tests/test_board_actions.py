"""What a tick is allowed to do.

These rules used to be covered by clicking buttons on the classic dashboard,
which meant asserting them through the UI: a rendered row, a rerun, and a
message that the dashboard then threw away. The board asks instead of being
clicked into, so the same rules are asserted here, against the function that
actually applies them.

Two things are being protected, and they are not the same thing:

* The tick rules themselves -- a task may be done on or after its due date and
  no more than OVERDUE_DAYS after it, and undo is always allowed.
* The fact that the canvas cannot get around them. `can_mark_done` is called
  here on the server even though the payload already told the browser which
  rows are locked, because a client that ignores `lock` must not be able to
  award itself points.
"""

import datetime as dt

import pytest
import streamlit as st

from tests.fixtures import sample_data
from utils.board.actions import COMPLETE, REOPEN, apply_action, complete_task, reopen_task


@pytest.fixture
def data():
    return sample_data()


@pytest.fixture
def session(monkeypatch):
    """A plain dict standing in for Streamlit's session.

    The seq de-duplication reads session state, and driving it through AppTest
    for every case would test the widget rather than the rule.
    """
    fake = {}
    monkeypatch.setattr(st, "session_state", fake, raising=False)
    return fake


def _task(data, task_id):
    return next(t for t in data["tasks"] if t["id"] == task_id)


def _completion_update():
    today = dt.date.today()
    year, week, _ = today.isocalendar()
    return {
        "status": "Done",
        "completed_date": today.isoformat(),
        "completed_week": f"{year}-W{week:02d}",
    }


# ── Allowed ─────────────────────────────────────────────────────────────────


def test_completing_a_due_task_writes_through(data, store):
    result = complete_task(data, 1)

    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update()}
    ]


def test_an_undated_task_can_always_be_completed(data, store):
    """can_mark_done has always allowed these, so the board must too."""
    result = complete_task(data, 10)
    assert result["ok"] is True
    assert store.recorded("update_task")


def test_a_parent_task_is_written_the_same_way(data, store):
    result = complete_task(data, 6)
    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {"task_id": 6, "updates": _completion_update()}
    ]


def test_points_reported_are_the_points_awarded(data, store):
    """Measured after the write, not before it.

    get_effective_points only decays points for a task that is already Done, so
    reading it off the pre-write task would report full points for a chore that
    had been left for a week.
    """
    result = complete_task(data, 1)
    assert result["points"] == 10
    assert result["zero_points"] is False


def test_a_task_finished_late_reports_no_points(data, store):
    """The decay is reachable on tasks finished late by another route -- an admin
    edit, or history written before the rule existed -- so the board must not
    promise points it will not pay out."""
    data["tasks"].append(
        {
            "id": 98, "title": "Late one", "kid_id": 1, "parent_id": None,
            "due_date": (dt.date.today() - dt.timedelta(days=9)).isoformat(),
            "points": 20, "status": "Done",
            "completed_date": dt.date.today().isoformat(),
            "completed_week": f"{dt.date.today().isocalendar()[0]}-W{dt.date.today().isocalendar()[1]:02d}",
            "repeat_type": "once", "created_at": dt.date.today().isoformat(),
        }
    )
    result = complete_task(data, 98)
    assert result["noop"] is True
    assert result["points"] == 0


# ── Refused ─────────────────────────────────────────────────────────────────


def test_a_future_task_cannot_be_completed(data, store):
    result = complete_task(data, 2)
    assert result["ok"] is False
    assert result["lock"] == "future"
    assert store.recorded("update_task") == []


def test_a_badly_overdue_task_cannot_be_completed(data, store):
    result = complete_task(data, 3)
    assert result["ok"] is False
    assert result["lock"] == "overdue"
    assert store.recorded("update_task") == []


def test_a_refusal_explains_itself(data, store):
    """The board shows the message, so it has to be about this task."""
    assert "can't be completed" in complete_task(data, 2)["message"]
    assert "overdue" in complete_task(data, 3)["message"]


def test_a_missing_task_is_refused_not_crashed(data, store):
    result = complete_task(data, 12345)
    assert result["ok"] is False
    assert store.recorded("update_task") == []


def test_the_lock_in_the_payload_is_not_what_decides(data, store):
    """The canvas is told which rows are locked, and must still be refused.

    This is the whole reason the rule is applied on the server: a browser that
    decided for itself would be free to ignore the lock it was given.
    """
    payload_task = {
        "id": 3, "title": "Water the plants", "lock": None,  # lying
        "action": "complete",
    }
    assert payload_task["lock"] is None
    result = complete_task(data, payload_task["id"])
    assert result["ok"] is False
    assert store.recorded("update_task") == []


# ── Undo ────────────────────────────────────────────────────────────────────


def test_reopening_clears_the_completion(data, store):
    result = reopen_task(data, 4)
    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {
            "task_id": 4,
            "updates": {
                "status": "Backlog",
                "completed_date": None,
                "completed_week": None,
            },
        }
    ]


def test_reopening_is_never_gated_by_the_tick_rules(data, store):
    """can_mark_done decides who earns points, not who may correct a mistake.

    Task 3 is far too overdue to complete. If it were ever completed, undoing it
    still has to work, or a mis-click becomes permanent.
    """
    _task(data, 3)["status"] = "Done"
    _task(data, 3)["completed_date"] = dt.date.today().isoformat()
    result = reopen_task(data, 3)
    assert result["ok"] is True
    assert store.recorded("update_task")


# ── Replays ─────────────────────────────────────────────────────────────────


def test_completing_an_already_done_task_writes_nothing(data, store):
    result = complete_task(data, 4)
    assert result["ok"] is True
    assert result["noop"] is True
    assert store.recorded("update_task") == []


def test_reopening_a_task_that_is_not_done_writes_nothing(data, store):
    result = reopen_task(data, 1)
    assert result["noop"] is True
    assert store.recorded("update_task") == []


# ── Writes that do not land ──────────────────────────────────────────────────


def test_a_write_that_changed_nothing_is_reported_as_a_failure(data, store, monkeypatch):
    """The case that used to report success over a task that never moved.

    The real `update_task` returns the rows Supabase changed, so an empty list
    means the row was gone or a policy refused it. Ignoring the return value
    made a tap announce "done, 10 points" and repaint nothing, and the only way
    to find out was to go and look at the board again.
    """
    _refuse_writes(monkeypatch, returning=[])

    result = complete_task(data, 1)

    assert result["ok"] is False
    assert "didn't save" in result["message"]
    assert "points" not in result or result["points"] == 0


def test_a_refused_write_names_the_task_it_failed_on(data, store, monkeypatch):
    _refuse_writes(monkeypatch, returning=[])
    result = complete_task(data, 1)
    assert result["message"].startswith("Set the table")


def test_an_unreachable_database_is_not_a_traceback(data, store, monkeypatch):
    """A tablet that loses wifi should say so, not show a stack trace."""
    _refuse_writes(monkeypatch, raising=ConnectionError("no route to host"))

    result = complete_task(data, 1)

    assert result["ok"] is False
    assert "connection" in result["message"].lower()


def test_a_failed_undo_says_so_rather_than_claiming_it_moved(data, store, monkeypatch):
    _refuse_writes(monkeypatch, returning=[])
    result = reopen_task(data, 4)
    assert result["ok"] is False
    assert "Read 20 pages" in result["message"]


def test_a_write_that_lands_is_still_a_success(data, store, monkeypatch):
    """The real client returns the changed rows; that must read as success."""
    _refuse_writes(monkeypatch, returning=[{"id": 1, "status": "Done"}])
    result = complete_task(data, 1)
    assert result["ok"] is True
    assert result["points"] == 10


def _refuse_writes(monkeypatch, returning=None, raising=None):
    """Swap in an `update_task` that fails the way the real one can."""
    from utils import db_helpers

    def failing(*args, **kwargs):
        if raising is not None:
            raise raising
        return returning

    monkeypatch.setattr(db_helpers, "update_task", failing)
    return failing


# ── The action channel ──────────────────────────────────────────────────────


def test_apply_action_ignores_a_replayed_action(data, store, session):
    """Streamlit holds a widget value until it changes, so every rerun replays
    the last action. Without the seq check, one tap would tick a task on every
    subsequent rerun for the life of the session."""
    from utils.board.bridge import HANDLED_SEQ_KEY

    session[HANDLED_SEQ_KEY] = 0
    action = {"verb": COMPLETE, "task_id": 1, "seq": 1}

    assert apply_action(data, action) is not None
    assert len(store.recorded("update_task")) == 1

    for _ in range(3):
        assert apply_action(data, action) is None
    assert len(store.recorded("update_task")) == 1, "a replayed action wrote again"

    # A genuinely new action still lands.
    assert apply_action(data, {**action, "seq": 2}) is not None
    assert len(store.recorded("update_task")) == 2


def test_apply_action_ignores_junk(data, store, session):
    from utils.board.bridge import HANDLED_SEQ_KEY

    session[HANDLED_SEQ_KEY] = 0
    for value in (None, {}, "complete", {"verb": COMPLETE}, {"verb": COMPLETE, "seq": "x"}):
        assert apply_action(data, value) is None
    assert store.recorded("update_task") == []


def test_an_unknown_verb_is_reported_and_still_marks_itself_handled(data, store, session):
    """Marking it handled stops the board retrying a verb that will never work;
    not marking it would spin the board forever on a bad payload."""
    from utils.board.bridge import HANDLED_SEQ_KEY

    session[HANDLED_SEQ_KEY] = 0
    result = apply_action(data, {"verb": "selfdestruct", "task_id": 1, "seq": 1})
    assert result["ok"] is False
    assert apply_action(data, {"verb": "selfdestruct", "task_id": 1, "seq": 1}) is None
    assert store.recorded("update_task") == []


def test_reopen_is_a_known_verb(data):
    from utils.board.actions import VERBS

    assert set(VERBS) == {COMPLETE, REOPEN}
