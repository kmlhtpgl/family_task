"""Throwaway entry point for the Phase 1 bridge spike.

    python -m streamlit run spike.py

Run tools/spike_check.py against it. Replaced by the real board in Phase 2.

The write is kept in process memory by default. A browser-driven check that
writes to the real Supabase table makes its own assertion order-dependent: the
first run completes the task, and every run after it finds status == "Done" and
skips the write. It also means running the spike by hand edits live data. So
reaching the real table takes an explicit FAMILY_TASK_SPIKE_REAL_WRITE=1.
"""

import os

import streamlit as st

from utils.board.bridge import is_new, mark_handled, render
from utils.db_helpers import get_all_data

st.set_page_config(page_title="Spike", layout="wide")

REAL_WRITE = os.environ.get("FAMILY_TASK_SPIKE_REAL_WRITE") == "1"

if "spike_applied" not in st.session_state:
    st.session_state.spike_applied = []
if "spike_runs" not in st.session_state:
    st.session_state.spike_runs = 0
st.session_state.spike_runs += 1

data = get_all_data()
tasks = data.get("tasks", [])

payload = {
    "runs": st.session_state.spike_runs,
    "people": [{"name": k["name"], "id": k["id"]} for k in data.get("kids", [])],
    "echo": list(st.session_state.spike_applied),
}

action = render(payload)

if is_new(action):
    mark_handled(action)
    if action["verb"] == "complete_task":
        task = next((t for t in tasks if t["id"] == action.get("task_id")), None)
        if REAL_WRITE and task and task["status"] != "Done":
            from utils.db_helpers import update_task

            update_task(task["id"], {"status": "Done"})
            st.session_state.spike_applied.append(task["id"])
        else:
            # The bridge is what is under test, not the write. Gating the
            # recorded write on the task's live status makes the assertion
            # depend on what earlier runs left behind, so the in-memory write
            # always records and the task lookup is only checked for having
            # found the right row.
            st.session_state.spike_task_ids = st.session_state.get("spike_task_ids", [])
            st.session_state.spike_writes = st.session_state.get("spike_writes", 0) + 1
            st.session_state.spike_applied.append(
                task["id"] if task else action.get("task_id")
            )
            st.session_state.spike_task_ids.append(action.get("task_id"))

st.write(f"run #{st.session_state.spike_runs}")
st.write(f"action = {action!r}")
st.write(f"applied = {st.session_state.spike_applied}")
st.write(f"task_ids = {st.session_state.get('spike_task_ids', [])}")
st.write(f"writes = {st.session_state.get('spike_writes', 'n/a')}")
