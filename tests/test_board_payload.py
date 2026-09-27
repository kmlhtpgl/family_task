"""The Board payload is what the canvas renders, so it is asserted directly.

No Streamlit, no browser, no Supabase: build_board_payload is pure, which is
the reason it is shaped this way.
"""

from datetime import date, timedelta

from tests.fixtures import sample_data
from utils.board.payload import (
    ARC_FUTURE,
    GROUP_LIMITS,
    build_arc,
    build_board_payload,
    initials,
)
from utils.task_helpers import OVERDUE_DAYS


def payload(today=None):
    return build_board_payload(sample_data(), on_date=today or date.today())


def test_payload_is_json_serialisable():
    import json

    json.dumps(payload())  # must not raise


def test_arc_spans_today_with_three_days_either_side():
    arc = payload()["arc"]
    assert len(arc) == 7
    assert [d["is_today"] for d in arc].count(True) == 1
    today = arc[3]
    assert today["date"] == date.today().isoformat()
    assert [d["is_past"] for d in arc] == [True] * 3 + [False] * 4
    assert [d["is_future"] for d in arc] == [False] * 4 + [True] * 3


def test_arc_measures_each_day_against_itself():
    """The fraction is "of the work due that day, how much is done".

    Counting by completion date instead put tasks finished on a day against a
    different day's denominator, and produced 250% on a real wall board.
    """
    arc = payload()["arc"]
    today_cell = next(d for d in arc if d["is_today"])
    # Six tasks are due today: 1, 4, 6, 7, 8, 9. Only task 4 is done.
    assert today_cell["total"] == 6
    assert today_cell["open"] == 5
    assert today_cell["done"] == 1
    assert today_cell["ratio"] == 1 / 6


def test_arc_ratio_never_exceeds_one():
    """A task completed on a day it was not due must not inflate that day.

    This is the shape of the real bug: 1,780 past-due tasks get finished in
    batches, so completion dates and due dates disagree constantly.
    """
    today = date.today()
    tasks = [
        {
            "id": n,
            "title": f"t{n}",
            "kid_id": 1,
            "parent_id": None,
            # Two days back, so the day falls inside the arc.
            "due_date": (today - timedelta(days=2)).isoformat(),
            "points": 10,
            "status": "Done",
            "completed_date": today.isoformat(),
            "completed_week": None,
            "repeat_type": "once",
            "created_at": today.isoformat(),
        }
        for n in range(40)
    ]
    arc = build_arc(tasks, today)
    for cell in arc:
        assert cell["done"] + cell["open"] == cell["total"]
        if cell["ratio"] is not None:
            assert 0 <= cell["ratio"] <= 1, cell
    # All 40 were finished today but were due two days ago, so today reads as
    # a day with nothing scheduled rather than as 4000% complete.
    assert next(d for d in arc if d["is_today"])["ratio"] is None
    two_days_back = next(d for d in arc if d["date"] == (today - timedelta(days=2)).isoformat())
    assert (two_days_back["total"], two_days_back["done"]) == (40, 40)
    assert two_days_back["ratio"] == 1.0


def test_arc_marks_an_empty_day_empty_rather_than_complete():
    # A day with nothing on it has no ratio, so the canvas can draw it as
    # "nothing due" instead of a full green bar that reads as 100% done.
    arc = build_arc([], date(2026, 4, 27))
    assert all(d["ratio"] is None for d in arc)
    assert all(d["total"] == 0 and d["done"] == 0 and d["open"] == 0 for d in arc)


def test_future_day_counts_only_what_is_due_then():
    arc = payload()["arc"]
    tomorrow = next(d for d in arc if d["is_future"])
    # Fixture task 2 is due tomorrow and still open, so nothing is done.
    assert tomorrow["total"] == 1
    assert tomorrow["open"] == 1
    assert tomorrow["done"] == 0
    assert tomorrow["ratio"] == 0


def test_people_carry_kids_then_parents_with_stable_accents():
    people = payload()["people"]
    assert [p["kind"] for p in people] == ["kid"] * 3 + ["parent"] * 2
    assert [p["id"] for p in people] == [1, 2, 3, 1, 2]
    accents = [p["accent"] for p in people]
    assert len(set(accents)) == len(accents), "accents must be distinguishable"
    # Same input, same colours: a wall display is recognised by colour.
    assert accents == [p["accent"] for p in payload()["people"]]


def test_names_are_whitespace_normalised():
    """One real child is stored with leading spaces, which pushed the name off
    centre in the rail."""
    data = sample_data()
    data["kids"][2]["name"] = "           Ekrem"
    result = build_board_payload(data, on_date=date.today())
    ekrem = next(p for p in result["people"] if p["id"] == 3)
    assert ekrem["name"] == "Ekrem"
    assert ekrem["initials"] == "EK"
    lane = next(l for l in result["lanes"] if l["person_id"] == 3)
    assert lane["name"] == "Ekrem"


def test_people_initials_handle_one_and_many_names():
    assert initials("Zayd") == "ZA"
    assert initials("Maryam Ahmed") == "MA"
    assert initials("Naim Salih") == "NS"
    assert initials("  ") == "?"
    assert initials(None) == "?"


def test_today_counts_are_per_person_and_ignore_other_days():
    people = {p["name"]: p for p in payload()["people"]}
    # Zayd (kid 1): tasks 1, 7, 8 open today; task 4 done today.
    assert people["Zayd"]["due_today"] == 3
    assert people["Zayd"]["done_today"] == 1
    # Maryam (kid 2): task 9 open today. Task 2 is due tomorrow, so not counted.
    assert people["Maryam"]["due_today"] == 1
    assert people["Maryam"]["done_today"] == 0
    # Bilal (kid 3): nothing due today.
    assert people["Bilal"]["due_today"] == 0
    # Yusuf (parent 1) has task 6 due today; Amina (parent 2) has nothing.
    assert people["Yusuf"]["due_today"] == 1
    assert people["Amina"]["due_today"] == 0


def test_kid_and_parent_with_the_same_id_are_kept_apart():
    """Kid 1 and parent 1 are different people who happen to share a number.

    Their task counts were being merged into one figure before the counts were
    keyed on table plus id.
    """
    people = {(p["kind"], p["id"]): p for p in payload()["people"]}
    assert people[("kid", 1)]["due_today"] == 3
    assert people[("parent", 1)]["due_today"] == 1
    assert people[("kid", 1)]["due_today"] != people[("parent", 1)]["due_today"]


def test_overdue_counts_only_unfinished_tasks_past_the_window():
    people = {p["name"]: p for p in payload()["people"]}
    # Bilal's task 3 is 5 days overdue, past OVERDUE_DAYS.
    assert people["Bilal"]["overdue"] == 1
    # Nobody else has anything past the window.
    assert people["Zayd"]["overdue"] == 0
    assert people["Amina"]["overdue"] == 0


def group(lane, key):
    return next((g for g in lane["groups"] if g["key"] == key), None)


def test_lane_groups_are_ordered_past_due_today_then_coming_up():
    lane = next(l for l in payload()["lanes"] if l["person_id"] == 2)
    assert [g["key"] for g in lane["groups"]] == ["today", "later"]
    assert [t["title"] for t in group(lane, "later")["tasks"]] == ["Science project"]
    # Task 9, "Asr", is due today and open.
    assert [t["title"] for t in group(lane, "today")["tasks"]] == ["Asr"]
    assert lane["counts"] == {
        "overdue": 0,
        "today": 1,
        "later": 1,
        "anytime": 0,
        "scheduled": 0,
        "done": 0,
    }


def test_empty_groups_are_left_out_entirely():
    """The canvas renders `groups` directly, so a group with nothing in it has
    to be absent rather than present and empty."""
    lane = next(l for l in payload()["lanes"] if l["person_id"] == 2)
    assert group(lane, "overdue") is None
    assert group(lane, "done") is None
    assert group(lane, "anytime") is None
    for g in lane["groups"]:
        assert g["tasks"], f"empty group survived: {g['key']}"


def test_lock_is_null_only_where_can_mark_done_allows():
    lane = next(l for l in payload()["lanes"] if l["person_id"] == 1)
    # Task 1 is due today, so it may be ticked.
    today = next(t for t in group(lane, "today")["tasks"] if t["id"] == 1)
    assert today["lock"] is None
    assert today["overdue"] is False
    # Task 2 is due tomorrow, so the canvas has to explain why it is locked.
    maryam = next(l for l in payload()["lanes"] if l["person_id"] == 2)
    assert next(t for t in group(maryam, "later")["tasks"] if t["id"] == 2)["lock"] == "future"
    # Task 3 is past the window, so it is locked as overdue and flagged.
    bilal = next(l for l in payload()["lanes"] if l["person_id"] == 3)
    task3 = next(t for t in group(bilal, "overdue")["tasks"] if t["id"] == 3)
    assert task3["lock"] == "overdue"
    assert task3["overdue"] is True


def test_lock_threshold_is_exactly_overdue_days():
    # A task exactly OVERDUE_DAYS late is still tickable; one day more is not.
    today = date.today()
    edge = sample_data()["tasks"][0]
    edge.update(due_date=(today - timedelta(days=OVERDUE_DAYS)).isoformat())

    just_inside = build_board_payload(
        {**sample_data(), "tasks": [edge]}, on_date=today
    )
    lane = just_inside["lanes"][0]
    assert group(lane, "overdue") is None
    # Still tickable, so it stays on the board as work to do now.
    entry = next(t for t in group(lane, "today")["tasks"] if t["id"] == edge["id"])
    assert entry["lock"] is None
    assert entry["late"] is True
    assert entry["overdue"] is False
    assert just_inside["totals"]["overdue"] == 0

    edge["due_date"] = (today - timedelta(days=OVERDUE_DAYS + 1)).isoformat()
    just_outside = build_board_payload(
        {**sample_data(), "tasks": [edge]}, on_date=today
    )
    assert len(group(just_outside["lanes"][0], "overdue")["tasks"]) == 1


def test_no_open_task_falls_between_the_buckets():
    """Every unfinished task must appear in exactly one bucket.

    A task due one or two days ago is tickable, so it is neither done nor out of
    reach nor in the future. Before it was routed into "today" it matched no
    branch at all and vanished from the board, which with a real year of history
    is a lot of silently missing work.
    """
    today = date.today()
    tasks = []
    for offset in range(-10, 11):
        due = (today + timedelta(days=offset)).isoformat()
        tasks.append(
            {
                "id": offset,
                "title": f"task {offset}",
                "kid_id": 1,
                "parent_id": None,
                "due_date": due,
                "points": 10,
                "status": "Backlog",
                "repeat_type": "once",
                "completed_date": None,
                "completed_week": None,
                "created_at": due,
            }
        )
    # Plus one with no date at all.
    tasks.append(
        {
            "id": 99,
            "title": "undated",
            "kid_id": 1,
            "parent_id": None,
            "due_date": None,
            "points": 10,
            "status": "Backlog",
            "repeat_type": "once",
            "completed_date": None,
            "completed_week": None,
            "created_at": today.isoformat(),
        }
    )

    result = build_board_payload(
        {**sample_data(), "tasks": tasks}, on_date=today
    )
    lane = result["lanes"][0]

    # Every unfinished task is accounted for in exactly one bucket. Counts are
    # used rather than the rendered tasks, because the rendered lists are capped
    # for the wall display and would hide the very loss being checked for.
    counts = lane["counts"]
    # `done` is the one bucket that is not open work, and it is empty here.
    assert counts["done"] == 0
    assert sum(counts.values()) == len(tasks)
    assert counts == {
        # Three or more days late. `is_task_overdue` asks whether the task is
        # *more* than OVERDUE_DAYS late, so offsets -3 and older.
        "overdue": 8,
        # Due today plus offsets -1 and -2, the late-but-still-tickable tail.
        "today": 3,
        # Offsets 1..3 fall inside the arc horizon and are listed.
        "later": 3,
        # Offsets 4..10 are pre-generated chores past the horizon: counted only.
        "scheduled": 7,
        "anytime": 1,
        # Completed today, so it can be undone from the board.
        "done": 0,
    }
    # And no task is in two of them.
    seen = [t["id"] for g in lane["groups"] for t in g["tasks"]]
    assert len(seen) == len(set(seen)), "a task landed in two buckets"
    assert sorted(seen) == sorted(set(seen))

    overdue = group(lane, "overdue")
    # Capped for the wall display, and honest about what it dropped.
    assert len(overdue["tasks"]) == GROUP_LIMITS["overdue"]
    assert overdue["total"] == 8
    assert overdue["hidden"] == 2
    assert [t["id"] for t in overdue["tasks"]] == [-10, -9, -8, -7, -6, -5]
    today_group = group(lane, "today")
    assert sorted(t["id"] for t in today_group["tasks"]) == [-2, -1, 0]
    # The two at the edge of the window are marked late but stay tickable.
    edge = [t for t in today_group["tasks"] if t["id"] in (-2, -1)]
    assert all(t["late"] and not t["overdue"] and t["lock"] is None for t in edge)
    assert next(t for t in today_group["tasks"] if t["id"] == 0)["late"] is False
    assert [t["id"] for t in group(lane, "anytime")["tasks"]] == [99]
    # Nothing past the horizon is listed, but the count is not lost either.
    assert sorted(t["id"] for t in group(lane, "later")["tasks"]) == [1, 2, 3]
    assert lane["scheduled"] == 7
    assert all(t["id"] < 4 for t in group(lane, "later")["tasks"])


def test_groups_are_capped_and_report_what_did_not_fit():
    """A wall display cannot show 300 past-due tasks. The cap is applied here so
    the remainder is counted rather than silently dropped."""
    today = date.today()
    tasks = [
        {
            "id": 100 + n,
            "title": f"late {n}",
            "kid_id": 1,
            "parent_id": None,
            "due_date": (today - timedelta(days=5)).isoformat(),
            "points": 10,
            "status": "Backlog",
            "repeat_type": "once",
            "completed_date": None,
            "completed_week": None,
            "created_at": today.isoformat(),
        }
        for n in range(30)
    ]
    result = build_board_payload({**sample_data(), "tasks": tasks}, on_date=today)
    overdue = group(result["lanes"][0], "overdue")
    assert len(overdue["tasks"]) == GROUP_LIMITS["overdue"]
    assert overdue["total"] == 30
    assert overdue["hidden"] == 30 - GROUP_LIMITS["overdue"]
    # The full count is still what the totals report.
    assert result["totals"]["overdue"] == 30


def test_pre_generated_future_chores_are_counted_not_listed():
    """This app pre-generates recurring chores a year into the future -- one real
    child has 872 of them. Listing them as "coming up" pushed the actual day off
    the board, so anything past the arc horizon is a number, not a list.
    """
    today = date.today()
    tasks = [
        {
            "id": 500 + n,
            "title": f"chore {n}",
            "kid_id": 1,
            "parent_id": None,
            "due_date": (today + timedelta(days=n)).isoformat(),
            "points": 10,
            "status": "Backlog",
            "repeat_type": "Every day",
            "completed_date": None,
            "completed_week": None,
            "created_at": today.isoformat(),
        }
        for n in range(1, 61)  # the next two months of daily chores
    ]
    result = build_board_payload({**sample_data(), "tasks": tasks}, on_date=today)
    lane = result["lanes"][0]

    listed = group(lane, "later")
    # The horizon is today + ARC_FUTURE days, so the next three are listed.
    assert [t["id"] for t in listed["tasks"]] == [501, 502, 503]
    assert all(
        d["due"] <= (today + timedelta(days=ARC_FUTURE)).isoformat()
        for d in listed["tasks"]
    )
    # 60 chores, 3 inside the horizon, the rest accounted for but not listed.
    assert lane["scheduled"] == 57
    assert lane["counts"]["scheduled"] == 57
    # Every task is still counted somewhere.
    assert sum(lane["counts"].values()) == 60


def test_a_group_that_fits_reports_nothing_hidden():
    lane = next(l for l in payload()["lanes"] if l["person_id"] == 2)
    for g in lane["groups"]:
        assert g["hidden"] == 0
        assert g["total"] == len(g["tasks"])


def test_effective_points_are_computed_by_the_python_rule():
    """A task completed long after its due date is worth 0, not its face value.

    The canvas shows what a task is actually worth, so it must not recompute
    this in JavaScript or the two would disagree.
    """
    lane = next(l for l in payload()["lanes"] if l["person_id"] == 2)
    # Fixture task 5 is done, so it is not in an open lane at all.
    assert get_task_by_id(lane, 5) is None
    assert all(t["id"] != 5 for g in lane["groups"] for t in g["tasks"])

    people = {p["name"]: p for p in payload()["people"]}
    # Task 5's face value is 20 but it was completed 6 days after a due date 4
    # days back, so the overdue rule values it at 0. Mary's total is therefore
    # just her 15-point adjustment, not 15 + 20.
    assert people["Maryam"]["total_points"] == 15
    # Zayd's task 4 was completed on its due date, so it keeps its 15 points
    # and his total has no adjustment on top.
    assert people["Zayd"]["total_points"] == 15


def get_task_by_id(lane, task_id):
    for g in lane["groups"]:
        for t in g["tasks"]:
            if t["id"] == task_id:
                return t
    return None


def test_undated_task_is_tickedable_and_stays_visible():
    """A task with no due date has always been completable, so the board keeps it.

    It is counted in none of the day cells, because it has no day. Dropping it
    from the lane would make live work look like it does not exist.
    """
    bilal = next(l for l in payload()["lanes"] if l["person_id"] == 3)
    # Fixture task 10, "Make dua", has due_date None.
    anytime = next(t for t in group(bilal, "anytime")["tasks"] if t["id"] == 10)
    assert anytime["due"] is None
    assert anytime["lock"] is None, "an undated task is always completable"
    assert bilal["counts"]["anytime"] == 1
    # Still not part of any day's load.
    assert payload()["totals"]["open_today"] == 5
    assert payload()["totals"]["overdue"] == 1


def test_totals_summarise_the_day():
    totals = payload()["totals"]
    assert totals["kids"] == 3
    assert totals["parents"] == 2
    assert totals["open_today"] == 5
    assert totals["done_today"] == 1
    assert totals["overdue"] == 1
    assert totals["progress"] == 1 / 6


def test_totals_progress_is_none_on_an_empty_day():
    data = sample_data()
    empty = build_board_payload({**data, "tasks": []}, on_date=date.today())
    assert empty["totals"]["progress"] is None
    assert empty["totals"]["open_today"] == 0


def test_a_day_with_no_data_still_renders_every_cell():
    empty = build_board_payload({**sample_data(), "tasks": []}, on_date=date.today())
    assert len(empty["arc"]) == 7
    # One lane per person, kids and parents, all empty. A person whose lane is
    # clear still belongs on the board; the board must not quietly drop them
    # because they finished.
    assert len(empty["lanes"]) == 5
    for lane in empty["lanes"]:
        assert lane["counts"] == {
            "overdue": 0,
            "today": 0,
            "later": 0,
            "anytime": 0,
            "scheduled": 0,
            "done": 0,
        }
    assert empty["totals"]["progress"] is None
    assert empty["totals"]["overdue"] == 0


def test_people_survive_being_deleted_while_tasks_remain():
    """Orphaned tasks must not invent a person or crash the payload."""
    data = sample_data()
    data["kids"] = []
    result = build_board_payload(data, on_date=date.today())
    assert [p["kind"] for p in result["people"]] == ["parent"] * 2
    # The parents survive; only the deleted kids' lanes are gone.
    assert [l["key"] for l in result["lanes"]] == ["parent:1", "parent:2"]


def test_missing_tables_do_not_explode():
    result = build_board_payload({}, on_date=date.today())
    assert result["people"] == []
    assert result["lanes"] == []
    assert result["totals"]["overdue"] == 0
    assert len(result["arc"]) == 7


def test_overdue_days_is_sent_so_the_canvas_can_explain_the_rule():
    assert payload()["overdue_days"] == OVERDUE_DAYS


def test_lanes_cover_kids_and_parents_with_unambiguous_keys():
    """Kid 1 and parent 1 are different people who share a number.

    They are two buttons in the rail, so selecting one must never show the
    other's work.
    """
    result = build_board_payload(sample_data(), on_date=date.today())
    keys = [l["key"] for l in result["lanes"]]
    assert keys == ["kid:1", "kid:2", "kid:3", "parent:1", "parent:2"]
    assert len(set(keys)) == len(keys)

    # Each lane holds only its owner's tasks.
    kid1 = next(l for l in result["lanes"] if l["key"] == "kid:1")
    parent1 = next(l for l in result["lanes"] if l["key"] == "parent:1")
    assert kid1["person_id"] == parent1["person_id"] == 1
    assert kid1["kind"] == "kid" and parent1["kind"] == "parent"
    kid1_titles = {t["title"] for g in kid1["groups"] for t in g["tasks"]}
    parent1_titles = {t["title"] for g in parent1["groups"] for t in g["tasks"]}
    assert kid1_titles and parent1_titles
    assert not (kid1_titles & parent1_titles)

    # The rail publishes the same key, so the canvas selects by identity rather
    # than by a number that two people share.
    rail_keys = [p["key"] for p in result["people"]]
    assert rail_keys == keys


def test_orphan_parent_tasks_do_not_crash_a_lane():
    """A task pointing at a person who no longer exists is simply not in a lane."""
    data = sample_data()
    data["tasks"] = data["tasks"] + [
        {
            "id": 99,
            "title": "Ghost",
            "kid_id": None,
            "parent_id": 4242,
            "due_date": date.today().isoformat(),
            "points": 10,
            "status": "Pending",
            "completed_date": None,
            "completed_week": None,
            "repeat_type": "once",
            "created_at": date.today().isoformat(),
        }
    ]
    result = build_board_payload(data, on_date=date.today())
    assert "parent:4242" not in [l["key"] for l in result["lanes"]]
    # Still counted in the family-wide totals, because the work is real.
    assert result["totals"]["open_today"] >= 1


def test_a_task_finished_today_stays_on_the_board_to_be_undone():
    """Otherwise a mis-click on a wall tablet is only fixable in the database.

    The task leaves the open buckets the moment it is done, so without this group
    it would vanish -- and with it the only affordance for putting it back.
    """
    data = sample_data()
    # Task 1 is "Set the table", due today, and open.
    task = next(t for t in data["tasks"] if t["id"] == 1)
    task["status"] = "Done"
    task["completed_date"] = date.today().isoformat()

    lane = next(l for l in build_board_payload(data)["lanes"] if l["key"] == "kid:1")
    done = group(lane, "done")
    assert done is not None
    # Zayd also finished "Read 20 pages" today, so this is a list rather than
    # a single row.
    assert "Set the table" in [t["title"] for t in done["tasks"]]
    # It has left the outstanding work. Zayd's prayers are still there, so this
    # is about the one task, not about the group being empty.
    assert "Set the table" not in [t["title"] for t in group(lane, "today")["tasks"]]
    assert lane["counts"]["done"] == 2


def test_only_todays_completions_are_kept_for_undo():
    """A wall board cannot show a year of finished chores.

    Yesterday's work is gone from the board, which is the point: this is a
    record of what is outstanding, not an archive.
    """
    data = sample_data()
    # Bilal, who has nothing completed today, so the only candidate is the task
    # being pushed into the past here.
    task = next(t for t in data["tasks"] if t["id"] == 3)
    task["status"] = "Done"
    task["completed_date"] = (date.today() - timedelta(days=1)).isoformat()

    lane = next(l for l in build_board_payload(data)["lanes"] if l["key"] == "kid:3")
    assert group(lane, "done") is None


def test_a_finished_task_offers_undo_even_when_it_cannot_be_completed():
    """can_mark_done would refuse a task this overdue, and it must refuse a
    finished one too -- but the row still has to be clickable, or the only way
    to undo is the database."""
    data = sample_data()
    task = next(t for t in data["tasks"] if t["id"] == 3)  # five days overdue
    task["status"] = "Done"
    task["completed_date"] = date.today().isoformat()

    lane = next(l for l in build_board_payload(data)["lanes"] if l["key"] == "kid:3")
    entry = group(lane, "done")["tasks"][0]
    assert entry["action"] == "reopen"


def test_the_action_verb_is_stated_not_inferred():
    """The canvas must not work out "complete" or "reopen" from the status."""
    payload = build_board_payload(sample_data())
    for lane in payload["lanes"]:
        for group_ in lane["groups"]:
            for entry in group_["tasks"]:
                if entry["status"] == "Done":
                    assert entry["action"] == "reopen"
                elif entry["lock"] is None:
                    assert entry["action"] == "complete"
                else:
                    assert entry["action"] is None
