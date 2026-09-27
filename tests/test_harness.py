"""Smoke test: the harness itself works and the app boots offline."""

import pytest

from streamlit.testing.v1 import AppTest

from tests.conftest import APP


def test_harness_boots_the_app(app):
    at = app.run()
    assert not at.exception, [str(e.value) for e in at.exception]


def test_harness_blocks_supabase(store):
    import utils.db_helpers as db

    # get_all_data is stubbed, so it must not raise.
    assert "kids" in db.get_all_data()


def test_supabase_client_itself_is_armed():
    from tests.conftest import ExplodingClient, NetworkAccessAttempted

    with pytest.raises(NetworkAccessAttempted):
        ExplodingClient().table("tasks").select("*").execute()


def test_fixture_covers_every_date_case(store):
    from utils.task_helpers import can_mark_done, get_effective_points

    by_id = {t["id"]: t for t in store.data["tasks"]}

    assert can_mark_done(by_id[1])[0] is True
    assert can_mark_done(by_id[2]) == (False, "future")
    assert can_mark_done(by_id[3]) == (False, "overdue")
    assert get_effective_points(by_id[5]) == 0
    assert get_effective_points(by_id[4]) == 15
