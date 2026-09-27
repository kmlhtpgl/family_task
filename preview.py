"""Run the real app.py against the committed sample family.

    path/to/venv/bin/python -m streamlit run preview.py

The fixtures in tests/fixtures.py are the whole point: nobody should have to tap
a real chore on the wall tablet to find out a tick is broken. This serves the
real app -- same pages, same board, same kiosk mount -- with the data layer
swapped for an in-memory store, so a click can be made as often as anyone likes.

This file has to sit at the repository root rather than in tools/, because
Streamlit serves /static relative to the main script's own directory. Run it
from tools/ and every board stylesheet and script 404s, leaving a blank iframe
that looks like a rendering bug.

The patch is applied before app.py is run, not after, because app.py does
`from utils.db_helpers import get_all_data` at import time. Anything that
imports the data layer by name has to be imported first, and the real app
second.
"""

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tests.fixtures import sample_data  # noqa: E402
import utils.db_helpers as db  # noqa: E402

# The script below is re-executed from the top on every Streamlit interaction, so
# a plain module-level dict is rebuilt on each click and the board snaps back to
# the fixture state the moment anything is ticked. The store has to live on disk
# like the log does, or the preview quietly lies about persistence.
WRITES_LOG = Path(
    sys.argv[1] if len(sys.argv) > 1 else REPO / ".screens" / "writes.json"
)
STORE_PATH = WRITES_LOG.with_name(WRITES_LOG.stem + "-store.json")

_store = (
    json.loads(STORE_PATH.read_text())
    if STORE_PATH.exists()
    else sample_data()
)


def _save():
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(_store, default=str))


def _log(entry):
    WRITES_LOG.parent.mkdir(parents=True, exist_ok=True)
    history = json.loads(WRITES_LOG.read_text()) if WRITES_LOG.exists() else []
    history.append(entry)
    WRITES_LOG.write_text(json.dumps(history, indent=1))


def _update_task(task_id=None, updates=None, **kwargs):
    task_id = task_id if task_id is not None else kwargs.get("task_id")
    updates = updates if updates is not None else kwargs.get("updates", {})
    _log({"fn": "update_task", "task_id": task_id, "updates": updates})
    for task in _store["tasks"]:
        if task["id"] == task_id:
            task.update(updates or {})
    _save()
    return True


def patch_data_layer():
    db.get_all_data = lambda *a, **k: copy.deepcopy(_store)
    db.update_task = _update_task
    db.data_changed = lambda *a, **k: None
    # Totals would otherwise read the live table, and a preview that silently
    # shows a different number from the real app is worse than no preview.
    for name in dir(db):
        if name.startswith(("get_weekly_points", "get_total_points")):
            setattr(db, name, lambda *a, **k: 0)
        if name.startswith(
            ("get_points_adjustment", "get_kid_points", "get_parent_points")
        ):
            setattr(db, name, lambda *a, **k: [])


patch_data_layer()

import runpy  # noqa: E402

runpy.run_path(str(REPO / "app.py"), run_name="__main__")
