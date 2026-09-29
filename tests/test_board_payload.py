"""The Board payload is what the canvas renders, so it is asserted directly.

No Streamlit, no browser, no Supabase: build_board_payload is pure, which is
the reason it is shaped this way.
"""

from datetime import date, timedelta

from tests.fixtures import sample_data
from utils.board.payload import (
    ARC_FUTURE,
    DISPLAY_ARC_FUTURE,
    DISPLAY_ARC_PAST,
    WEEKDAYS,
    build_arc,
    build_board_payload,
    initials,
)
from utils.task_helpers import OVERDUE_DAYS, can_mark_done


def payload(today=None):
    return build_board_payload(sample_data(), on_date=today or date.today())


def test_payload_is_json_serialisable():
    import json

    json.dumps(payload())  # must not raise


def test_the_strip_offers_a_whole_week_around_today():
    """Seven cells, three back and three ahead, with today in the middle.

    The strip was cut to today and the two days behind it because a future day
    used to be a dead end: a child could walk onto Tuesday while the real date
    was Sunday, and every row there was not yet due, so `can_mark_done` refused
    them all. That is now handled where it belongs -- the row says "Not yet" and
    is not clickable -- so a future day is a day you can look ahead on rather
    than a trap. Hiding the days was treating the symptom.

    Three either side is a week, which is as long as anyone plans chores for.
    """
    arc = payload()["arc"]
    today = date.today()

    assert len(arc) == 7
    assert [d["date"] for d in arc] == [
        (today + timedelta(days=n)).isoformat()
        for n in range(-DISPLAY_ARC_PAST, DISPLAY_ARC_FUTURE + 1)
    ]
    assert [d["is_past"] for d in arc] == [True, True, True, False, False, False, False]
    assert [d["is_future"] for d in arc] == [False, False, False, False, True, True, True]
    # Anchored on today, which is the middle cell rather than the last one.
    assert arc[DISPLAY_ARC_PAST]["date"] == today.isoformat()


def test_the_real_today_is_not_moved_by_browsing_back():
    """Today stays today however far back the strip is scrolled.

    `is_today` and `is_selected` were one flag, so selecting yesterday enlarged
    yesterday, filled the arc up to yesterday, and captioned it "Today" while
    the real today sat next to it unlabelled. The wall was pointing at the
    wrong day while naming it the right one.
    """
    yesterday = date.today() - timedelta(days=1)
    result = build_board_payload(sample_data(), on_date=yesterday)
    arc = result["arc"]
    yesterday_cell = DISPLAY_ARC_PAST - 1
    today_cell = DISPLAY_ARC_PAST

    assert arc[yesterday_cell]["is_selected"] is True
    assert arc[yesterday_cell]["is_today"] is False
    assert arc[today_cell]["is_today"] is True
    assert arc[today_cell]["is_selected"] is False
    # The day being browsed is announced separately from the real one.
    assert result["is_selected_today"] is False
    assert result["today"] == date.today().isoformat()
    # Exactly one of each, so the canvas cannot end up with two "today" discs.
    assert [d["is_today"] for d in arc].count(True) == 1
    assert [d["is_selected"] for d in arc].count(True) == 1


def test_browsing_today_marks_today_as_both():
    """The common case has to stay unambiguous rather than double-marked."""
    arc = payload()["arc"]
    today_cell = next(d for d in arc if d["is_today"])
    assert today_cell["is_selected"] is True
    assert payload()["is_selected_today"] is True


def test_every_future_day_on_the_strip_is_visible_but_not_tickable():
    """A future day shows its work and refuses to be ticked, in every lane.

    This is the trade the three-day strip made by hiding future days: on one,
    every row was locked and read "Not yet". Hiding the day was treating that.
    Now the day is offered, its work is listed so you can see what is coming,
    and every row is locked with no action, so there is nothing to tap and no
    way for the row and the write path to disagree.

    Asserted over the whole strip rather than one day, because a day that
    quietly became tickable would be the exact bug this guards.
    """
    result = build_board_payload(sample_data(), on_date=date.today())
    future_cells = [c for c in result["arc"] if c["is_future"]]
    assert len(future_cells) == DISPLAY_ARC_FUTURE

    for cell in future_cells:
        rows = [
            t
            for lane in result["lanes"]
            for group in lane["groups"]
            for t in group["tasks"]
            if t["due"] == cell["date"]
        ]
        if not rows:
            continue
        # Listed, so the day is worth looking at...
        assert rows, cell["date"]
        # ...and not tappable, so looking at it cannot be mistaken for doing it.
        for row in rows:
            assert row["lock"] == "future", (cell["date"], row["title"])
            assert row["action"] is None, (cell["date"], row["title"])


def test_past_and_present_days_still_offer_their_work_to_be_ticked():
    """The other half of the same rule: hiding the future days is not a licence
    to lock the real ones. A day in the past is where a mis-click gets fixed, so
    its rows have to stay live."""
    result = build_board_payload(sample_data(), on_date=date.today())
    tickable = [
        c
        for c in result["arc"]
        if not c["is_future"]
        and any(
            t["action"] == "complete"
            for lane in result["lanes"]
            for group in lane["groups"]
            for t in group["tasks"]
            if t["due"] == c["date"]
        )
    ]
    assert tickable, "no non-future day on the strip offers a tickable row"


def test_only_the_days_around_today_are_called_yesterday_or_tomorrow():
    """Relative names stay off the days they do not describe.

    The old three-case expression returned "Tomorrow" for every future offset
    and "Yesterday" for every past one, so a wider strip would have called
    Saturday "Tomorrow" and Monday "Yesterday". Only the adjacent days get a
    relative name; the rest fall back to the weekday.
    """
    arc = payload()["arc"]
    by_date = {d["date"]: d for d in arc}
    today = date.today()
    assert by_date[(today - timedelta(days=1)).isoformat()]["relative"] == "Yesterday"
    assert by_date[today.isoformat()]["relative"] == "Today"
    assert by_date[(today - timedelta(days=2)).isoformat()]["relative"] is None
    # The canvas falls back to the weekday, so the cell is still named.
    assert by_date[(today - timedelta(days=2)).isoformat()]["label"]


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
                # Yesterday, so the day falls inside the compact arc.
                "due_date": (today - timedelta(days=1)).isoformat(),
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
    # All 40 were finished today but were due yesterday, so today reads as
    # a day with nothing scheduled rather than as 4000% complete.
    assert next(d for d in arc if d["is_today"])["ratio"] is None
    yesterday = next(d for d in arc if d["date"] == (today - timedelta(days=1)).isoformat())
    assert (yesterday["total"], yesterday["done"]) == (40, 40)
    assert yesterday["ratio"] == 1.0


def test_arc_marks_an_empty_day_empty_rather_than_complete():
    # A day with nothing on it has no ratio, so the canvas can draw it as
    # "nothing due" instead of a full green bar that reads as 100% done.
    arc = build_arc([], date(2026, 4, 27))
    assert all(d["ratio"] is None for d in arc)
    assert all(d["total"] == 0 and d["done"] == 0 and d["open"] == 0 for d in arc)


def test_a_future_dated_view_does_not_unlock_a_task_that_is_not_due_yet():
    """The tick rule is asked about *now*, whoever is looking.

    The rule used to be evaluated against the day being viewed, so a payload
    built for a future day reported a not-yet-due task as tickable. The strip no
    longer offers a future day, which hides the path, but the payload is a public
    function and the board page is not its only caller: anything rendering a
    future day would have gotten rows that offer a tick the write path refuses.

    So the rule is pinned to the real today here rather than to the day in the
    argument, and this test fails if that ever drifts back.
    """
    tomorrow = date.today() + timedelta(days=1)
    result = build_board_payload(sample_data(), on_date=tomorrow)
    rows = [
        t
        for lane in result["lanes"]
        for group in lane["groups"]
        for t in group["tasks"]
    ]
    not_yet_due = [t for t in rows if t["due"] == tomorrow.isoformat()]

    # Fixture task 2 is due tomorrow. Whether or not a future view lists it, it
    # cannot be tickable while the real date is still today.
    assert not_yet_due
    for row in not_yet_due:
        assert row["lock"] == "future", row
        assert row["action"] is None, row


def test_every_day_the_board_offers_agrees_with_the_write_path():
    """The row and the write must ask the rule the same question.

    The payload decides whether a row shows a tick and `complete_task` decides
    independently whether to honour it. If they ever ask about different days,
    one of them is lying to a child, and the board offers actions it will then
    refuse -- which is the bug this suite exists to keep out.

    Compared against `can_mark_done` rather than by calling `complete_task`,
    because the rule is the whole question here: this is a check that the
    payload asks it, not a test of the write, and doing a write to ask it would
    mean a test that can only pass by touching a database.
    """
    from utils.task_helpers import can_mark_done

    checked = 0
    for offset in (-2, -1, 0):
        day = date.today() + timedelta(days=offset)
        data = sample_data()
        result = build_board_payload(data, on_date=day)
        by_id = {t["id"]: t for t in data["tasks"]}
        for lane in result["lanes"]:
            for group in lane["groups"]:
                for row in group["tasks"]:
                    # The same call the write path makes, on the real today.
                    allowed, reason = can_mark_done(by_id[row["id"]])
                    assert (row["lock"] is None) == allowed, (
                        f"row {row['id']} on {day}: payload says lock={row['lock']!r}, "
                        f"the rule says {allowed} ({reason})"
                    )
                    if row["action"] == "complete":
                        assert allowed, f"row {row['id']} offers a tick the rule refuses"
                        checked += 1
    # If this ever asserts over nothing, the fixture no longer exercises the
    # rule and the test is passing for the wrong reason.
    assert checked > 0


def test_tomorrows_tasks_are_listed_on_tomorrow_and_not_on_today():
    """A not-yet-due task belongs to its own day, and only to that day.

    Tomorrow's chores are visible when you select tomorrow, where they are
    listed and locked, so the day is worth looking at. They are not dragged into
    today's lane, which used to be the reason future days were hidden: mixing
    them in made today look like a trap. The strip reaching tomorrow is fine
    now that each day holds only its own work.
    """
    result = build_board_payload(sample_data(), on_date=date.today())
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    # The strip reaches it again.
    assert any(d["date"] == tomorrow for d in result["arc"])

    # On tomorrow it is listed, and locked.
    on_tomorrow = build_board_payload(sample_data(), on_date=date.today() + timedelta(days=1))
    listed_tomorrow = {
        t["id"] for lane in on_tomorrow["lanes"] for g in lane["groups"] for t in g["tasks"]
    }
    entry = next(
        t
        for lane in on_tomorrow["lanes"]
        for g in lane["groups"]
        for t in g["tasks"]
        if t["id"] == 2
    )
    assert 2 in listed_tomorrow
    assert entry["lock"] == "future"
    assert entry["action"] is None

    # On today it is not listed at all. Fixture task 2 is due tomorrow.
    lane = result["lanes"][0]
    listed_today = {t["id"] for group in lane["groups"] for t in group["tasks"]}
    assert 2 not in listed_today


def test_people_carry_kids_then_parents_with_stable_accents():
    people = payload()["people"]
    assert [p["kind"] for p in people] == ["kid"] * 3 + ["parent"] * 2
    assert [p["id"] for p in people] == [1, 2, 3, 1, 2]
    # An accent is an identity, so it is the hue that has to be distinct and
    # stable. It is not a finished colour: the lightness is the Board's mode and
    # arrives from the stylesheet, so the same person is a different colour in
    # daylight without being a different person. Comparing the whole dict to a
    # string is what the old shape allowed and this one does not.
    identities = [(p["accent"]["chroma"], p["accent"]["hue"]) for p in people]
    assert len(set(identities)) == len(identities), "accents must be distinguishable"
    assert "oklch" not in str(people[0]["accent"]), "the payload must not bake in a lightness"
    # Same input, same colours: a wall display is recognised by colour.
    assert identities == [
        (p["accent"]["chroma"], p["accent"]["hue"]) for p in payload()["people"]
    ]


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
    # Every one of them is listed. Groups used to be capped here, which hid two
    # of these eight behind a "+2 more" line that pointed at another app.
    assert len(overdue["tasks"]) == 8
    assert overdue["total"] == 8
    # Alphabetically, which is what makes a two-per-row list findable. The
    # titles here are "task -10" and so on, so that is a string order and not
    # the numeric one the ids suggest.
    assert [t["title"] for t in overdue["tasks"]] == [
        "task -10", "task -3", "task -4", "task -5", "task -6", "task -7",
        "task -8", "task -9",
    ]
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


def test_a_group_is_listed_alphabetically():
    """Position is the only way to find a task in a two-per-row list.

    So the order cannot depend on the order the database happened to return, or
    on when a task was ticked: the list has to stay put while the day changes
    under it.
    """
    def task(tid, title):
        return {
            "id": tid, "title": title, "kid_id": 1, "parent_id": None,
            "due_date": date.today().isoformat(), "points": 10, "status": "Backlog",
            "repeat_type": "once", "completed_date": None, "completed_week": None,
            "created_at": date.today().isoformat(),
        }

    # Supplied in a deliberately unhelpful order: capitals first, and a title
    # with the stray leading space a free-text form will happily store.
    data = {**sample_data(), "tasks": [
        task(1, "Water the plants"),
        task(2, "Bathroom"),
        task(3, "bed, make"),
        task(4, "  feed the cat"),
        task(5, "Tidy bedroom"),
    ]}
    lane = build_board_payload(data, on_date=date.today(), compact=True)["lanes"][0]
    titles = [t["title"] for t in group(lane, "today")["tasks"]]
    # Casefolded, so a capitalised title does not sort ahead of every lowercase
    # one; the leading space ignored, so it cannot float to the front. The title
    # is stored and shown as typed -- this is a sort, not a rewrite.
    assert titles == [
        "Bathroom", "bed, make", "  feed the cat", "Tidy bedroom", "Water the plants",
    ]


def test_titles_sharing_a_name_keep_a_stable_order():
    """Recurring chores repeat their title, and one is pre-generated for every
    upcoming day. They must not swap places between reruns, or the row under a
    finger moves as the board repaints."""
    def task(tid, title, due):
        return {
            "id": tid, "title": title, "kid_id": 1, "parent_id": None,
            "due_date": due, "points": 10, "status": "Backlog",
            "repeat_type": "daily", "completed_date": None, "completed_week": None,
            "created_at": due,
        }

    today = date.today()
    same = "Fajr"
    forwards = [task(n, same, today.isoformat()) for n in range(5)]
    orders = [forwards, list(reversed(forwards)), forwards[2:] + forwards[:2]]
    rendered = []
    for order in orders:
        data = {**sample_data(), "tasks": order}
        rendered.append(
            [
                t["id"]
                for t in group(
                    build_board_payload(data, on_date=today, compact=True)["lanes"][0],
                    "today",
                )["tasks"]
            ]
        )
    assert rendered[0] == [0, 1, 2, 3, 4]
    assert rendered[1] == rendered[0] == rendered[2]


def test_awkward_tasks_do_not_break_the_ordering():
    """A task can arrive with no title at all, and ids come from several sources.

    Neither may raise out of the sort and take the whole board with it.
    """
    def entry(tid, title):
        return {
            "id": tid, "title": title, "kid_id": 1, "parent_id": None,
            "due_date": date.today().isoformat(), "points": 10, "status": "Backlog",
            "repeat_type": "once", "completed_date": None, "completed_week": None,
            "created_at": date.today().isoformat(),
        }

    lane = build_board_payload(
        {**sample_data(), "tasks": [entry(None, "Alpha"), entry(2, None)]},
        on_date=date.today(),
        compact=True,
    )["lanes"][0]
    # Empty sorts first rather than raising, so a task added without a title
    # cannot take the whole board down.
    assert [t["title"] for t in group(lane, "today")["tasks"]] == [None, "Alpha"]


def test_the_order_holds_for_mixed_id_types():
    """Task ids are numeric from the database, but a task built elsewhere can
    carry a string. The comparison has to stay total."""
    def entry(tid, title):
        return {
            "id": tid, "title": title, "kid_id": 1, "parent_id": None,
            "due_date": date.today().isoformat(), "points": 10, "status": "Backlog",
            "repeat_type": "once", "completed_date": None, "completed_week": None,
            "created_at": date.today().isoformat(),
        }

    lane = build_board_payload(
        {**sample_data(), "tasks": [entry("b", "Same"), entry(7, "Same"),
                                    entry("a", "Same")]},
        on_date=date.today(),
        compact=True,
    )["lanes"][0]
    tasks = group(lane, "today")["tasks"]
    assert [t["title"] for t in tasks] == ["Same", "Same", "Same"]
    # Numeric ids first in their own order, then the strings: a total order
    # rather than a comparison that raises when it meets a str.
    assert [t["id"] for t in tasks] == [7, "a", "b"]


def test_the_order_does_not_depend_on_the_order_the_data_arrives_in():
    """The repaint that follows a tick rebuilds this payload from the database.

    If the list followed the order it came back in, a task could move under a
    finger at the moment somebody was reaching for it, so the same set of tasks
    has to render the same way however it is supplied.
    """
    def task(tid, title):
        return {
            "id": tid, "title": title, "kid_id": 1, "parent_id": None,
            "due_date": date.today().isoformat(), "points": 10, "status": "Backlog",
            "repeat_type": "once", "completed_date": None, "completed_week": None,
            "created_at": date.today().isoformat(),
        }

    titles = ["Zebra", "apple", "Mango", "bed", "Feed"]
    forwards = [task(n, t) for n, t in enumerate(titles)]
    orders = [forwards, list(reversed(forwards)), sorted(forwards, key=lambda t: t["id"])]
    rendered = []
    for order in orders:
        lane = build_board_payload(
            {**sample_data(), "tasks": order}, on_date=date.today(), compact=True
        )["lanes"][0]
        rendered.append([t["title"] for t in group(lane, "today")["tasks"]])
    assert rendered[0] == ["apple", "bed", "Feed", "Mango", "Zebra"]
    assert rendered[1] == rendered[0] == rendered[2]


def test_a_long_group_is_listed_in_full_and_reports_nothing_hidden():
    """No cap, and nothing to point at another app.

    Groups were capped here and the overflow summarised as "+N more, shown in
    the classic app". That was hiding real work: on the 27th a child had 14
    finished chores against a Done cap of 8, so six finished chores were off the
    wall with the board naming somewhere else to look. A display whose purpose
    is to show what was done cannot be the thing that decides some of it does
    not count. Thirty past-due tasks now render as thirty rows.
    """
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
    assert len(overdue["tasks"]) == 30
    assert overdue["total"] == 30
    # Nothing is dropped, so there is nothing to report. The key is gone from
    # the payload rather than left at zero for the canvas to keep explaining.
    assert "hidden" not in overdue
    assert result["totals"]["overdue"] == 30


def test_a_big_finished_day_is_listed_in_full():
    """The case that actually bit: 14 done against a cap of 8.

    Keyed on the due date now, so this is 14 chores due on one day and finished,
    which is the shape the cap used to cut in half.
    """
    today = date.today()
    tasks = [
        {
            "id": 200 + n,
            "title": f"chore {n}",
            "kid_id": 1,
            "parent_id": None,
            "due_date": today.isoformat(),
            "points": 10,
            "status": "Done",
            "repeat_type": "once",
            "completed_date": today.isoformat(),
            "completed_week": None,
            "created_at": today.isoformat(),
        }
        for n in range(14)
    ]
    result = build_board_payload({**sample_data(), "tasks": tasks}, on_date=today)
    done = group(result["lanes"][0], "done")
    assert len(done["tasks"]) == 14
    assert done["total"] == 14
    assert result["totals"]["done_today"] == 14
    # Every one of them is still undoable, which is the other half of it.
    assert all(t["action"] == "reopen" for t in done["tasks"])


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


def test_every_group_lists_all_of_its_tasks():
    """The count above a group is the number of rows under it, always.

    These two used to disagree whenever a group overflowed, which is how a wall
    could say "6 tasks" over four of them.
    """
    for lane in payload()["lanes"]:
        for g in lane["groups"]:
            assert g["total"] == len(g["tasks"]), g["key"]
            assert "hidden" not in g


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
    assert len(empty["arc"]) == DISPLAY_ARC_PAST + DISPLAY_ARC_FUTURE + 1
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
    assert len(result["arc"]) == DISPLAY_ARC_PAST + DISPLAY_ARC_FUTURE + 1


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


def test_the_header_date_stays_on_the_real_today():
    """Browsing the week must not move the date under the clock.

    `today_label` is rendered next to the live clock, so it is the one piece of
    the board that can only mean one thing. It followed the day picker, so
    looking at Wednesday made the wall claim it was Wednesday.
    """
    real_today = date.today()
    assert payload()["today_label"] == (
        f"{WEEKDAYS[real_today.weekday()]} {real_today.day} {real_today:%b %Y}"
    )
    for offset in (-3, -1, 1, 3):
        other = payload(today=real_today + timedelta(days=offset))
        assert other["today_label"] == payload()["today_label"]
        assert other["today"] == real_today.isoformat()
        # The day being looked at is reported separately, so the canvas can
        # label the day it is showing without touching the header's.
        assert other["selected"] == (real_today + timedelta(days=offset)).isoformat()
        assert other["is_selected_today"] is False
    assert payload()["is_selected_today"] is True


def test_a_day_is_named_after_itself_once_it_is_not_today():
    """The "Today" heading follows the picker instead of being a literal.

    Selecting a day used to produce a column headed "Today" listing that day's
    work, which is a wall board contradicting itself about which day it was on.
    """
    wednesday = payload(today=date.today() + timedelta(days=1))
    names = {g["key"]: g["name"] for g in wednesday["lanes"][0]["groups"]}
    if "today" in names:
        assert names["today"] == wednesday["selected_label"]

    # The finished group is no longer named after a day at all. It used to read
    # "Done on Sun 27", which was actively wrong: the group is the work *due*
    # that day, so chores ticked late said they were finished on a day they were
    # only due on. The day is already spelled out in the heading above it.
    today_names = {g["key"]: g["name"] for g in payload()["lanes"][0]["groups"]}
    if "done" in today_names:
        assert today_names["done"] == "Done"
    if "today" in today_names:
        assert today_names["today"] == "Today"
    for lane_names in (
        {g["key"]: g["name"] for g in wednesday["lanes"][0]["groups"]},
    ):
        if "done" in lane_names:
            assert lane_names["done"] == "Done"


def test_a_completed_task_belongs_to_its_due_day_and_not_to_its_finish_day():
    """A task stays in its own day, and a past day is a record.

    Finished tasks used to be pulled in by completion date, which filed a chore
    due the 27th under the 29th. Keying the group on the due date puts each task
    on the one day it belongs to. And that day, being in the past, is read-only:
    the row is there to say what was done, not to be undone from.
    """
    today = date.today()
    saturday = today + timedelta(days=2)
    data = sample_data()
    # Due on the day before, but finished on Saturday.
    task = next(t for t in data["tasks"] if t["id"] == 3)  # five days overdue
    task["status"] = "Done"
    task["completed_date"] = saturday.isoformat()

    result = build_board_payload(data, on_date=saturday, compact=True)
    lane = next(l for l in result["lanes"] if l["key"] == "kid:3")
    done = next((g for g in lane["groups"] if g["key"] == "done"), None)
    # Task 3 was due five days back, so it is not part of Saturday's workload.
    # Finishing it on Saturday does not move it there.
    assert done is None

    # Instead, it appears on its due day in the Done group, listed and finished.
    due_day = date.fromisoformat(task["due_date"])
    result_due = build_board_payload(data, on_date=due_day, compact=True)
    lane_due = next(l for l in result_due["lanes"] if l["key"] == "kid:3")
    done_due = next((g for g in lane_due["groups"] if g["key"] == "done"), None)
    assert done_due is not None
    entry = next(t for t in done_due["tasks"] if t["title"] == "Water the plants")
    assert entry["finished"] is True
    # Read-only: a past day is a record of the week, and those points are
    # already counted in its total. Reopening from here rewrites a banked week.
    assert entry["action"] is None
    # And it is not captioned as owing, which is what the tick rule's lock
    # would otherwise say about a chore that is already finished.
    assert entry["lock"] == "overdue"


def _finished_task_on(day, task_id=901):
    """A chore due, and finished, on `day`."""
    year, week_num, _ = day.isocalendar()
    return {
        "id": task_id,
        "title": "Chore",
        "kid_id": 1,
        "parent_id": None,
        "due_date": day.isoformat(),
        "points": 10,
        "status": "Done",
        "repeat_type": "once",
        "created_at": day.isoformat(),
        "completed_date": day.isoformat(),
        "completed_week": f"{year}-W{week_num}",
    }


def _action_for(task_id, data, on_date):
    """The action the payload offers for one task on one day, or None if absent."""
    result = build_board_payload(data, on_date=on_date, compact=True)
    rows = [
        t
        for lane in result["lanes"]
        for g in lane["groups"]
        for t in g["tasks"]
        if t["id"] == task_id
    ]
    return rows[0]["action"] if rows else None


def test_undo_is_offered_for_today_and_the_two_days_before_it():
    """Today, yesterday and the day before are live; anything else is a record.

    Undo was the real today alone, on the grounds that a past day is history and
    reopening from there rewrites a week whose points have been banked. But the
    tick window is `OVERDUE_DAYS`, which is also two days back: a chore could be
    *finished* from two days ago but not *corrected* from there, so the wall
    showed a record under a day the family was still allowed to work in. The
    window is now one window, read from the same constant on both sides.
    """
    today = date.today()
    base = sample_data()

    for offset in range(-DISPLAY_ARC_PAST, DISPLAY_ARC_FUTURE + 1):
        day = today + timedelta(days=offset)
        data = {**base, "tasks": [_finished_task_on(day)] + base["tasks"]}
        action = _action_for(901, data, day)

        if -OVERDUE_DAYS <= offset <= 0:
            assert action == "reopen", f"{day} should offer undo, offered {action!r}"
        else:
            # Further back than the window, or ahead of today: look, but do not touch.
            assert action is None, f"{day} should be a record, offered {action!r}"


def test_an_open_task_can_still_be_finished_from_a_past_day():
    """The 'done' half of the ask: the tick itself, not just the undo.

    A chore due yesterday is inside the window, so browsing back to it and
    ticking it books the completion to yesterday -- which is the day the board
    is showing, not the day of the tap.
    """
    today = date.today()
    base = sample_data()

    for offset in range(-OVERDUE_DAYS, 1):
        day = today + timedelta(days=offset)
        open_task = {
            "id": 902,
            "title": "Set the table",
            "kid_id": 1,
            "parent_id": None,
            "due_date": day.isoformat(),
            "points": 10,
            "status": "Backlog",
            "repeat_type": "once",
            "created_at": day.isoformat(),
            "completed_date": None,
            "completed_week": None,
        }
        data = {**base, "tasks": [open_task] + base["tasks"]}
        assert _action_for(902, data, day) == "complete", f"{day} should offer a tick"


def test_an_open_task_from_a_past_day_does_not_leak_onto_another_day():
    """A task belongs to its own day. The wider undo window does not move that.

    Offering yesterday's chore on today's board would file it under the wrong
    day, and ticking it there would book the completion to today.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    base = sample_data()
    open_task = {
        "id": 902,
        "title": "Set the table",
        "kid_id": 1,
        "parent_id": None,
        "due_date": yesterday.isoformat(),
        "points": 10,
        "status": "Backlog",
        "repeat_type": "once",
        "created_at": yesterday.isoformat(),
        "completed_date": None,
        "completed_week": None,
    }
    data = {**base, "tasks": [open_task] + base["tasks"]}

    assert _action_for(902, data, today) is None


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


def test_undoing_from_a_day_returns_the_task_to_that_same_day():
    """The round trip that points 4 and 6 asked for, end to end on the payload.

    Tick a chore on the day you are looking at, then undo it from that same day.
    It has to come back up there. The old code filed the tick under its
    completion date while listing the day by due date, so on a cross-day tick the
    task left the screen entirely when undone and reappeared days away.
    """
    today = date.today()
    data = sample_data()
    task = next(t for t in data["tasks"] if t["id"] == 1)  # "Set the table"

    # Ticked, booking the completion to the day being viewed.
    done = {**task, "status": "Done", "completed_date": today.isoformat()}
    ticked = {**data, "tasks": [done if t["id"] == 1 else t for t in data["tasks"]]}

    on_day = build_board_payload(ticked, on_date=today, compact=True)
    lane = next(l for l in on_day["lanes"] if l["key"] == "kid:1")
    assert group(lane, "done") is not None

    # Undone, which is what the write path leaves behind.
    undone = {**data, "tasks": [task if t["id"] == 1 else t for t in data["tasks"]]}
    after = build_board_payload(undone, on_date=today, compact=True)
    lane_after = next(l for l in after["lanes"] if l["key"] == "kid:1")

    # Back in the open work of the day it was undone on, and tickable again.
    titles = [t["title"] for t in group(lane_after, "today")["tasks"]]
    assert "Set the table" in titles
    entry = next(t for t in group(lane_after, "today")["tasks"] if t["title"] == "Set the table")
    assert entry["action"] == "complete"
    # Out of the finished group. Zayd's "Read 20 pages" is still done today, so
    # the group is not empty; this is about the one task.
    assert "Set the table" not in [t["title"] for t in group(lane_after, "done")["tasks"]]


def test_a_task_is_only_ever_on_its_own_due_day():
    """One task, one day. The rule the two above are both consequences of.

    481 of 1158 finished chores in the live data were completed on a day other
    than their due date, so any rule that lets a task follow its completion date
    has to cope with a lot of them. Selecting any other day shows none of them.
    """
    today = date.today()
    data = sample_data()
    task = next(t for t in data["tasks"] if t["id"] == 3)  # due 5 days back
    finished_late = {**task, "status": "Done", "completed_date": today.isoformat()}
    patched = {**data, "tasks": [finished_late if t["id"] == 3 else t for t in data["tasks"]]}

    due_day = date.fromisoformat(task["due_date"])
    for offset in range(-DISPLAY_ARC_PAST, DISPLAY_ARC_FUTURE + 1):
        day = due_day + timedelta(days=offset)
        if day == due_day:
            continue
        result = build_board_payload(patched, on_date=day, compact=True)
        listed = [
            t["id"]
            for lane in result["lanes"]
            for g in lane["groups"]
            for t in g["tasks"]
        ]
        assert 3 not in listed, day.isoformat()


def test_a_finished_task_is_never_offered_a_tick_to_earn_points_again():
    """A finished row is never a "complete" row, whatever the date rule says.

    Undo used to be offered on any day, and was built by falling through to the
    tick for anything that was not done. That fallback is gone, and this is the
    case that would have caught it: a chore finished and inside the overdue
    window, so the tick rule *allows* it. Folding the two branches together
    would hand it a "complete" tick and re-award points for work already banked.
    """
    data = sample_data()
    task = next(t for t in data["tasks"] if t["id"] == 3)  # five days overdue
    task["status"] = "Done"
    task["completed_date"] = date.today().isoformat()

    # Asked about a day where the tick rule does allow it, to make the point.
    yesterday = date.today() - timedelta(days=1)
    task["due_date"] = yesterday.isoformat()
    allowed, _ = can_mark_done(task)
    assert allowed, "this test is not exercising what it claims"

    result = build_board_payload(data, on_date=yesterday, compact=True)
    lane = next(l for l in result["lanes"] if l["key"] == "kid:3")
    entry = group(lane, "done")["tasks"][0]
    assert entry["finished"] is True
    assert entry["lock"] is None, "the tick rule does allow this date"
    # The verb is the undo, never a fresh tick: re-awarding points for work
    # already banked is the failure this test exists to catch.
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
