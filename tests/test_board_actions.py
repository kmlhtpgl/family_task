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
from pathlib import Path

import pytest
import streamlit as st

from tests.fixtures import sample_data
from utils.board.payload import build_board_payload
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


def _completion_update(on_date=None):
    """The row a completion is expected to write.

    The week is unpadded to match `current_week_key`, which is what the weekly
    point totals compare against. These tests ran for months agreeing on that by
    accident: the only weeks where padding matters are the first nine, and no
    test fixed a date in one, so "W05" against a "W5" would have gone unnoticed
    until January -- and it would have cost a child their points.
    """
    day = on_date or dt.date.today()
    year, week, _ = day.isocalendar()
    return {
        "status": "Done",
        "completed_date": day.isoformat(),
        "completed_week": f"{year}-W{week}",
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
            "completed_week": _completion_update()["completed_week"],
            "repeat_type": "once", "created_at": dt.date.today().isoformat(),
        }
    )
    result = complete_task(data, 98)
    assert result["noop"] is True
    assert result["points"] == 0


# ── The day the tick is booked to ────────────────────────────────────────────


def test_a_tick_is_booked_to_the_day_being_looked_at(data, store):
    """Recording yesterday's chore must not file it under today.

    The board browses back two days so a job done yesterday can be recorded at
    all. Booking that to the real today put the task in the "Done" group of a
    different day to the one being looked at: it vanished off the wall in front
    of the child and the day's total never moved. From across a room, a task
    that leaves when you tick it looks like a board that has lost it.
    """
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = complete_task(data, 1, on_date=yesterday)

    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update(yesterday)}
    ]
    assert result["date"] == yesterday.isoformat()


def test_the_week_key_follows_the_day_being_booked(data, store):
    """A different day can be a different week, and the points are looked up by it.

    The week number is not decoration: the weekly totals sum over tasks whose
    `completed_week` equals the current one, so booking to the browsed day has to
    write that day's week or the points get counted in a week nobody is reading.
    """
    last_week = dt.date.today() - dt.timedelta(days=7)
    result = complete_task(data, 1, on_date=last_week)

    assert result["ok"] is True
    written = store.recorded("update_task")[0]["updates"]
    assert written["completed_week"] == _completion_update(last_week)["completed_week"]
    assert written["completed_week"] != _completion_update()["completed_week"]


def test_a_tick_with_no_day_in_front_of_it_books_today(data, store):
    """The default keeps the board usable outside the page.

    A caller with no board in front of it -- an import, a test, anything reusing
    this -- should get the old behaviour rather than a TypeError.
    """
    complete_task(data, 1)
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update()}
    ]


def test_the_confirmation_says_which_day_was_booked(data, store):
    """A tap is the only place a child is told what it did.

    Two messages both reading "Read a book. 10 points." could have come from two
    different days, which is the confusion the day-aware write exists to remove.
    """
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = complete_task(data, 1, on_date=yesterday)

    named = f"{yesterday:%a} {yesterday.day}"
    assert named in result["message"]
    assert "done for" in result["message"]


def test_the_day_named_is_short_enough_to_read_on_a_tablet(data, store):
    """A full written date wraps a confirmation on the board's own width."""
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = complete_task(data, 1, on_date=yesterday)
    message = result["message"]

    assert f"{yesterday:%B}" not in message
    assert message.count("\n") == 0
    assert len(message) < 60


# ── Refused ─────────────────────────────────────────────────────────────────


def test_a_future_task_cannot_be_completed(data, store):
    result = complete_task(data, 2)
    assert result["ok"] is False
    assert result["lock"] == "future"
    assert store.recorded("update_task") == []


def test_browsing_to_a_future_day_does_not_unlock_a_future_task(data, store):
    """The tick rule is a fact about now, not about the day on screen.

    The board used to ask this question using the day being looked at, so
    browsing forward made a not-yet-due task pass: the row rendered a live tick
    and the write then refused it with "Not due yet". The wall offered an action
    and withdrew it on contact.

    `on_date` here is the day the child is *looking* at. It must not become a
    licence to tick a chore early -- you cannot do tomorrow's washing today by
    navigating to tomorrow.
    """
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    result = complete_task(data, 2, on_date=tomorrow)

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


def test_apply_action_books_the_completion_to_the_browsed_day(data, store, session):
    """The day travels through the action channel, not just the direct call.

    `complete_task` booking to the browsed day is only worth anything if the page
    passes that day in. This is the seam where it was dropped: `apply_action` took
    no day, read the real one, and every tick through the board went to today.
    """
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = apply_action(
        data, {"verb": COMPLETE, "task_id": 1, "seq": 1}, on_date=yesterday
    )

    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update(yesterday)}
    ]


def test_apply_action_still_refuses_a_future_task_on_a_future_day(data, store, session):
    """The rule is not something the caller can talk its way past.

    The page now hands `apply_action` a day, so the day is an input to a write
    for the first time. Passing a future one must not become a licence to tick
    early -- that is the difference between a date and a permission.
    """
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    result = apply_action(
        data, {"verb": COMPLETE, "task_id": 2, "seq": 1}, on_date=tomorrow
    )

    assert result["ok"] is False
    assert result["lock"] == "future"
    assert store.recorded("update_task") == []


def test_apply_action_with_no_day_books_today(data, store, session):
    """A caller that does not know about days keeps the old behaviour."""
    result = apply_action(data, {"verb": COMPLETE, "task_id": 1, "seq": 1})

    assert result["ok"] is True
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update()}
    ]


def test_undo_is_never_told_which_day_to_book(data, store, session):
    """Only a completion books a date.

    An undo clears the completion rather than recording one, so the day on screen
    is not an input to it. Handing it a date would invite somebody to later make
    undo *set* a date, which is how a reopened task ends up stuck in a Done group.
    """
    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = apply_action(
        data, {"verb": REOPEN, "task_id": 4, "seq": 1}, on_date=yesterday
    )

    assert result["ok"] is True
    written = store.recorded("update_task")[0]["updates"]
    assert written["completed_date"] is None
    assert written["completed_week"] is None


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


def test_a_past_day_tick_leaves_the_task_in_the_browsed_day_done_group(data, store):
    """The whole reason for the fix, as one behaviour end to end.

    Tick a task while browsing yesterday and the day's Done group has to gain it
    and today's has to stay as it was. Before, the tick was written to today:
    today's total jumped by one the child was not looking at, yesterday's did not
    move, and the row they had just tapped disappeared from the board in front
    of them. On a wall that reads as the board losing track of a job.
    """
    yesterday = dt.date.today() - dt.timedelta(days=1)
    # The task is due yesterday, so it belongs to that day's lane and group.
    # `store.data` rather than `data`: the stub applies the write to the copy
    # the next render reads, which is what makes the assertion about the board
    # rather than about the function's return value.
    _task(store.data, 1)["due_date"] = yesterday.isoformat()

    before = build_board_payload(store.data, on_date=yesterday)
    assert 1 not in [t["id"] for t in _done(before, kid=1)]

    complete_task(store.data, 1, on_date=yesterday)

    after = build_board_payload(store.data, on_date=yesterday)
    assert 1 in [t["id"] for t in _done(after, kid=1)]
    # And today's Done group is untouched: the work was booked to yesterday.
    today_after = build_board_payload(store.data, on_date=dt.date.today())
    assert 1 not in [t["id"] for t in _done(today_after, kid=1)]


def _done(payload, kid):
    return [
        t
        for lane in payload["lanes"]
        if lane["person_id"] == kid
        for group in lane["groups"]
        if group["key"] == "done"
        for t in group["tasks"]
    ]


def test_undoing_from_a_past_day_returns_the_task_to_that_day(data, store):
    """A wrong tick has to be undoable from where it was made.

    The child taps something by mistake on Monday, goes back to Monday to fix it,
    and the task reappears in Monday's list. If undo dropped the completion
    without booking it anywhere, the task would fall out of every day at once and
    be unreachable from the board entirely.
    """
    result = reopen_task(data, 4)
    assert result["ok"] is True
    written = store.recorded("update_task")[0]["updates"]
    assert written["status"] == "Backlog"
    assert written["completed_date"] is None
    # The due date is untouched, so the task returns to the day it belongs to.
    assert "due_date" not in written


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


def test_a_remounted_frame_is_told_where_the_seq_count_reached(data, store, session):
    """Coming back to the board must not cost the user their clicks.

    The seq lives in the frame, so leaving the board for another page and
    returning remounts it at 1 while Python still remembers the count. Every
    click up to the remembered number was then dropped as a replay: the day
    picker and the task ticks were dead until a refresh, which is the one thing
    that clears session state. The payload now carries the count so a fresh
    frame resumes above it.
    """
    from utils.board.bridge import HANDLED_SEQ_KEY, SEQ_FIELD, is_new, seq_floor

    session[HANDLED_SEQ_KEY] = 3
    # The next action a remounted frame sends must be accepted, not discarded.
    assert seq_floor() == 3
    assert is_new({"verb": COMPLETE, "task_id": 1, "seq": seq_floor() + 1})
    assert not is_new({"verb": COMPLETE, "task_id": 1, "seq": seq_floor()})
    # And the frame is handed the number in the payload it paints from.
    assert SEQ_FIELD == "handled_seq"


def test_a_fresh_session_reports_a_floor_a_frame_can_start_from(data, store, session):
    from utils.board.bridge import HANDLED_SEQ_KEY, is_new, seq_floor

    session[HANDLED_SEQ_KEY] = 0
    assert seq_floor() == 0
    assert is_new({"verb": COMPLETE, "task_id": 1, "seq": 1})


def test_seq_floor_survives_a_nonsense_stored_value(data, store, session):
    """A corrupted session must not turn every later action into a replay."""
    from utils.board.bridge import HANDLED_SEQ_KEY, is_new, seq_floor

    session[HANDLED_SEQ_KEY] = "not a number"
    assert seq_floor() == 0
    session[HANDLED_SEQ_KEY] = None
    assert seq_floor() == 0
    session[HANDLED_SEQ_KEY] = 5
    assert is_new({"verb": COMPLETE, "task_id": 1, "seq": 6})


def test_the_frame_continues_its_count_from_the_payload():
    """The JS half of the contract, asserted on the source.

    The frame is the only place that knows the count, so without this seed a
    remount silently restarts it. A browser test would catch the symptom; this
    catches the cause, and runs without one.
    """
    source = (Path(__file__).resolve().parent.parent / "static" / "board" / "board.js").read_text()
    assert "payload.handled_seq" in source
    assert "floor > state.seq" in source, "the frame must not lower its own count"


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


def test_the_page_passes_the_day_it_rendered_the_row_for():
    """The JS half of the day-aware write, asserted on the source.

    The page computes `on_date` to build the payload and then, previously, threw
    it away and called `apply_action(data, action)`. Tests on the function would
    have kept passing forever: `complete_task` books to the day it is *given*,
    and the page was giving it none. So the call site itself has to be checked.
    """
    source = (Path(__file__).resolve().parent.parent / "app_pages" / "board.py").read_text()
    assert "apply_action(data, action, on_date=on_date)" in source, (
        "the board must hand the write the day it rendered the row for"
    )


def test_the_canvas_uses_today_and_the_selection_as_separate_facts():
    """The arc has two ideas of "the day", and they are not the same day.

    One flag drove the enlarged disc, the progress fill and the caption at once,
    so browsing to yesterday made the wall call Monday "Today". Reading
    `is_today` for today and `is_selected` for the ring is what keeps the
    emphasis and the browsing in step; a single flag would be a one-word change
    away from the bug coming straight back.
    """
    source = (Path(__file__).resolve().parent.parent / "static" / "board" / "board.js").read_text()
    assert "day.is_today" in source, "today must still be marked as today"
    assert "day.is_selected" in source, "the browsed day must be marked separately"
    # The fill was driven by the selected day, which made it mean "how far back
    # you have scrolled" rather than "how far through the week we are".
    assert "arc__fill" not in source, "the progress fill went with the future days"
