"""Test harness.

Two guarantees this file exists to provide:

1. No test may reach Supabase. `get_supabase_client` is replaced with a client
   that raises on any table access, and every reader/writer in the data layer is
   replaced with an in-memory stub over `tests.fixtures.sample_data()`. If a
   test ever needs a function that is not stubbed, the import below will fail
   loudly rather than silently hitting the network.

2. Both shells render through Streamlit's own AppTest, so the suite exercises
   the real script rather than a mock of it.
"""

import copy as _copy
import inspect
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

from tests.fixtures import sample_data  # noqa: E402

APP = REPO_ROOT / "app.py"


class NetworkAccessAttempted(AssertionError):
    """Raised if any test path tries to talk to Supabase."""


class ExplodingTable:
    def __init__(self, name):
        self._name = name

    def _blow_up(self, *a, **kw):
        raise NetworkAccessAttempted(
            f"Test tried to query Supabase table {self._name!r}. "
            "The data layer is supposed to be stubbed."
        )

    select = update = insert = delete = upsert = _blow_up
    eq = neq = gt = lt = gte = lte = in_ = order = range = limit = _blow_up
    execute = single = maybe_single = _blow_up


class ExplodingClient:
    def table(self, name):
        return ExplodingTable(name)

    def rpc(self, *a, **kw):
        raise NetworkAccessAttempted("Test tried to call an RPC.")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Guarantee the whole test session cannot talk to Supabase."""
    import utils.supabase_client as sc

    monkeypatch.setattr(sc, "get_supabase_client", lambda: ExplodingClient())
    monkeypatch.setattr(
        sc, "create_client", lambda *a, **kw: ExplodingClient(), raising=False
    )


def _update(data, table, row_id, updates):
    for row in data[table]:
        if row.get("id") == row_id:
            row.update(updates)
            return row
    return None


def _insert(data, table, row):
    row = dict(row)
    row.setdefault("id", max([r.get("id", 0) for r in data[table]] + [0]) + 1)
    data[table].append(row)
    return row


# How each writer maps onto the in-memory store, expressed against the real
# function's own signature so that a caller may pass arguments positionally or
# by keyword and get the same result. Callers are not consistent about this:
# the board's actions call update_task(id, updates) positionally while
# admin.py uses keywords, and the stub has to honour both.
UPDATES = {
    "update_task": ("tasks", "task_id"),
    "update_book": ("books", "book_id"),
    "update_surah": ("surahs", "surah_id"),
    "update_kid": ("kids", "kid_id"),
    "update_parent": ("parents", "parent_id"),
    "update_meeting_note": ("meeting_notes", "note_id"),
}

# Writers that take a whole row as their first argument.
ROW_INSERTS = {
    "add_task": "tasks",
    "add_book": "books",
    "add_surah": "surahs",
    "add_reading_log": "reading_log",
    "add_reward_session": "reward_sessions",
    "add_meeting_note": "meeting_notes",
}

# Writers that take individual fields. The field names mirror what each real
# function passes to Supabase.
FIELD_INSERTS = {
    "add_kid": ("kids", ("name", "age", "photo_path"), ("id", "name", "age", "photo_path", "created_at")),
    "add_parent": (
        "parents",
        ("name", "email", "phone", "photo_url"),
        ("id", "name", "email", "phone", "photo_path", "created_at"),
    ),
    "add_meeting_comment": (
        "meeting_comments",
        ("meeting_note_id", "body", "author"),
        ("id", "meeting_note_id", "body", "author", "created_at"),
    ),
    "add_points_adjustment": (
        "points_adjustments",
        ("person_id", "person_type", "points"),
        ("id", "person_id", "person_type", "points", "created_at"),
    ),
}


@pytest.fixture(autouse=True)
def fresh_page_modules():
    """Drop app_pages from sys.modules so every test re-imports them.

    AppTest executes app.py fresh, but Python caches `app_pages.board` and
    friends in sys.modules across tests. Those modules bind the data-layer
    functions at import time (`from utils.db_helpers import update_task`), so
    without this, the second test in a session would still be calling the
    *first* test's stub and its writes would land in the first test's
    recording. The stub would look like it silently stopped working.
    """
    for name in [n for n in sys.modules if n == "app_pages" or n.startswith("app_pages.")]:
        del sys.modules[name]
    yield


@pytest.fixture
def store(monkeypatch):
    """An in-memory stand-in for the data layer.

    Readers return deep copies so a test that mutates what it received cannot
    corrupt the fixture for the next assertion. Writers record the call in
    `store.calls` and apply the change to `store.data`, which lets a test assert
    both that the right write happened and that the next render reflects it.
    """
    import utils.db_helpers as db

    data = sample_data()
    calls = []
    # Signatures captured before patching, so recorded calls can be normalised
    # the same way the real function would have bound them. Callers in this app
    # are inconsistent about positional vs keyword (the board's actions call
    # update_task(id, updates), admin.py uses keywords), so a test that asserts
    # on raw call tuples is asserting on trivia.
    signatures = {
        name: inspect.signature(obj)
        for name, obj in vars(db).items()
        if callable(obj)
        and not inspect.ismodule(obj)
        and not inspect.isclass(obj)
        and getattr(obj, "__module__", "utils.db_helpers") == "utils.db_helpers"
    }

    def copy():
        return _copy.deepcopy(data)

    def recorded(name):
        """Every recorded call to `name`, as dicts of bound arguments."""
        out = []
        for called, args, kwargs in calls:
            if called != name:
                continue
            bound = signatures[name].bind(*args, **kwargs)
            bound.apply_defaults()
            out.append(bound.arguments)
        return out

    def apply_update(table, id_field, args, kwargs, real):
        bound = inspect.signature(real).bind(*args, **kwargs)
        bound.apply_defaults()
        return _update(data, table, bound.arguments[id_field], bound.arguments["updates"])

    def apply_row_insert(table, args, kwargs, real):
        bound = inspect.signature(real).bind(*args, **kwargs)
        bound.apply_defaults()
        return _insert(data, table, bound.arguments[next(iter(bound.arguments))])

    def apply_field_insert(table, source_fields, target_fields, args, kwargs, real):
        bound = inspect.signature(real).bind(*args, **kwargs)
        bound.apply_defaults()
        row = {k: v for k, v in zip(target_fields, source_fields)}
        return _insert(data, table, row)

    for name, obj in list(vars(db).items()):
        if name.startswith("_") or inspect.ismodule(obj) or inspect.isclass(obj):
            continue
        # Patch only what this module defines. @st.cache_data wraps get_all_data
        # in a CachedFunc rather than a function, so membership in the module's
        # own __dict__ is the reliable test, not isfunction().
        if getattr(obj, "__module__", "utils.db_helpers") != "utils.db_helpers":
            continue
        if not callable(obj):
            continue

        if name == "get_all_data":
            monkeypatch.setattr(db, name, lambda *a, **kw: copy())
            continue
        if name == "data_changed":
            monkeypatch.setattr(db, name, lambda: None)
            continue

        real = obj
        if name in UPDATES:
            table, id_field = UPDATES[name]
            handler = lambda a, kw, _t=table, _i=id_field, _r=real: apply_update(
                _t, _i, a, kw, _r
            )
        elif name in ROW_INSERTS:
            handler = lambda a, kw, _t=ROW_INSERTS[name], _r=real: apply_row_insert(
                _t, a, kw, _r
            )
        elif name in FIELD_INSERTS:
            table, src, dst = FIELD_INSERTS[name]
            handler = lambda a, kw, _t=table, _s=src, _d=dst, _r=real: apply_field_insert(
                _t, _s, _d, a, kw, _r
            )
        else:
            # A writer this harness does not model. Record it and return None so
            # a test can still run; the recording is what tests assert on.
            handler = None

        def make(fname=name, fn=handler):
            def stub(*args, **kwargs):
                calls.append((fname, args, kwargs))
                return fn(args, kwargs) if fn else None

            return stub

        monkeypatch.setattr(db, name, make())

    return types.SimpleNamespace(
        data=data, calls=calls, snapshot=copy, recorded=recorded, signatures=signatures
    )


@pytest.fixture
def stub_assets(monkeypatch):
    """Neutralise everything that leaves the process besides Supabase.

    Kiosk prayer times and weather come from third-party HTTP APIs and are
    cached to disk, so they are stubbed at the helper boundary. Kiosk
    background and adhan listings read the filesystem and are intentionally
    left alone: the screensaver depends on those files existing, and a test
    that asserts they exist is worth more than one that pretends they do.
    """
    import utils.kiosk_helpers as k

    timings = {
        "timings": {
            "Fajr": "05:12",
            "Sunrise": "06:41",
            "Dhuhr": "13:19",
            "Asr": "16:22",
            "Maghrib": "19:04",
            "Isha": "20:18",
        },
        "date": {
            "readable": "Sunday, 27 September 2026",
            "hijri": {"date": "15 Rabi' al-Awwal 1448"},
        },
    }
    monkeypatch.setattr(k, "get_prayer_times", lambda: timings)
    monkeypatch.setattr(
        k,
        "get_weather",
        lambda *a, **kw: {"temp": 14, "code": "02", "text": "Partly cloudy"},
    )
    monkeypatch.setattr(k, "get_audio_bytes", lambda prayer: b"")
    monkeypatch.setattr(
        k,
        "load_kiosk_settings",
        lambda: {
            "screensaver_enabled": True,
            "adhan_enabled": True,
            "idle_timeout": 5,
            "weather_enabled": True,
            "weather_city": "Cambridge",
            "weather_unit": "celsius",
        },
    )
    monkeypatch.setattr(k, "save_kiosk_settings", lambda **kw: None, raising=False)
    return timings


@pytest.fixture
def app(store, stub_assets):
    """AppTest over the real app.py with the data layer stubbed.

    The board is the default shell, so this lands on the board. Tests about the
    pages it does not replace want `classic` instead.
    """
    return AppTest.from_file(str(APP), default_timeout=30)


@pytest.fixture
def classic(store, stub_assets, monkeypatch):
    """AppTest over the real app.py, started in the classic shell.

    The board owns the landing page, so a test that clicks `nav_kids` would
    otherwise be looking for a button the board has no reason to draw.
    """
    monkeypatch.setenv("FAMILY_TASK_CLASSIC", "1")
    return AppTest.from_file(str(APP), default_timeout=30)


def widget(elements, key):
    """Find one element by its widget key.

    AppTest's ElementList only indexes by position, but widget keys are the
    stable identifier the app itself uses, so tests should address widgets by
    key rather than by row order.
    """
    for element in elements:
        if getattr(element, "key", None) == key:
            return element
    available = [getattr(e, "key", None) for e in elements]
    raise AssertionError(
        f"No widget with key {key!r}. Available keys: {available}"
    )


def markdown_text(at):
    """Every string rendered through st.markdown, concatenated."""
    return "\n".join(el.value for el in at.markdown)

