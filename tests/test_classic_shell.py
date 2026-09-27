"""The classic shell must keep working, page by page.

This is the regression net for the rewrite. The Board replaces these pages, but
only after it is proven; until then every one of them has to keep rendering,
in both themes, against the stubbed data layer.
"""

import pytest

from tests.conftest import markdown_text, widget

# Every destination the classic navbar offers. kanban is listed because it
# exists today; Phase 5 removes it along with streamlit-sortables.
CLASSIC_PAGES = [
    "dashboard",
    "kanban",
    "parents",
    "kids",
    "reading",
    "quran",
    "prayer",
    "rewards",
    "meeting",
    "admin",
]

# Pages that need the password gate opened first.
GATED = {"admin"}


def open_page(at, page, authenticated=True):
    if authenticated and page in GATED:
        at.session_state["admin_authenticated"] = True
    widget(at.button, f"nav_{page}").click().run()
    return at


@pytest.mark.parametrize("page", CLASSIC_PAGES)
def test_classic_page_renders(app, page):
    at = app.run()
    assert not at.exception, [str(e.value) for e in at.exception]

    open_page(at, page)

    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["page"] == page


def test_dashboard_shows_family_and_todays_tasks(app):
    at = app.run()
    text = markdown_text(at)
    # Task titles live in button labels, not markdown, so read both.
    labels = [b.label for b in at.button]

    for name in ("Zayd", "Maryam", "Bilal", "Yusuf", "Amina"):
        assert name in text, f"{name} missing from the dashboard"

    assert any("Set the table" in label for label in labels)
    assert "pts this week" in text


def test_completing_a_task_writes_through(app, store):
    at = app.run()

    widget(at.button, "cal_1").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert store.recorded("update_task") == [
        {"task_id": 1, "updates": _completion_update()}
    ]


def test_tick_gives_no_visible_confirmation(app, store):
    """Documents a real defect in the classic dashboard.

    dashboard.py calls st.success() and then st.rerun() on the very next line,
    which discards the message before it is ever painted. Ticking a task on the
    classic dashboard therefore gives no feedback at all: the row simply
    changes. The Board is expected to do better than this, so the test records
    the current behaviour rather than asserting it is desirable.
    """
    at = app.run()
    widget(at.button, "cal_1").click().run()

    assert store.recorded("update_task"), "the write itself must still happen"
    assert list(at.success) == [], "classic dashboard swallows its own confirmation"


def _completion_update():
    """The payload app.py writes when a task is ticked today."""
    import datetime as dt

    today = dt.date.today()
    year, week, _ = today.isocalendar()
    return {
        "status": "Done",
        "completed_date": today.isoformat(),
        "completed_week": f"{year}-W{week:02d}",
    }


def test_future_task_cannot_be_completed(app, store):
    at = app.run()
    widget(at.button_group, "weekly_person_cal").set_value("🧒 Maryam").run()

    widget(at.button, "cal_2").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert store.recorded("update_task") == []
    assert any("can't be completed before" in i.value for i in at.info)


def test_badly_overdue_task_cannot_be_completed(app, store):
    at = app.run()
    # The default view is yesterday..tomorrow, which can never be more than
    # OVERDUE_DAYS late, so the overdue guard is only reachable with the week
    # expanded. This is the same path a real user takes.
    widget(at.toggle, "show_all_week_toggle").set_value(True).run()
    widget(at.button_group, "weekly_person_cal").set_value("🧒 Bilal").run()

    widget(at.button, "cal_3").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert store.recorded("update_task") == []
    assert any("overdue" in w.value.lower() for w in at.warning)


def test_undoing_a_done_task_clears_completion(app, store):
    at = app.run()
    widget(at.button, "cal_4").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert store.recorded("update_task") == [
        {
            "task_id": 4,
            "updates": {"status": "Backlog", "completed_date": None, "completed_week": None},
        }
    ]


def test_kanban_page_still_renders_before_it_is_deleted(app):
    at = app.run()
    open_page(at, "kanban")
    assert not at.exception, [str(e.value) for e in at.exception]
    assert any("Daily Board" in h.value for h in at.header)


def test_admin_requires_authentication(app):
    at = app.run()
    open_page(at, "admin", authenticated=False)
    assert any("password-protected" in w.value for w in at.warning)


def test_admin_renders_when_authenticated(app):
    at = app.run()
    open_page(at, "admin")
    assert not at.exception, [str(e.value) for e in at.exception]
