import streamlit as st
from datetime import date
from streamlit_sortables import sort_items

from utils.data_helpers import get_kid
from utils.task_helpers import TASK_STATUSES, get_effective_points, OVERDUE_DAYS, can_mark_done
from utils.db_helpers import update_task


# Mirrors the board palette in utils/styles.py. Kept as literals because the
# board lives in its own iframe; update both together if the palette changes.
_BOARD_PALETTE = {
    "light": {
        "col_backlog_bg": "#FAFAFA",
        "col_backlog_border": "#DEDEDE",
        "col_backlog_head": "#575757",
        "col_backlog_head_bg": "#F2F2F2",
        "col_done_bg": "#F6F9F7",
        "col_done_border": "#3D7A4A",
        "col_done_head": "#3D7A4A",
        "col_done_head_bg": "#E9F2EC",
        "item_bg": "#FFFFFF",
        "item_fg": "#1F1F1F",
        "item_border": "#EBEBEB",
        "item_shadow": "0 1px 0 rgba(31,31,31,0.06)",
        "item_shadow_hover": "0 1px 1px rgba(31,31,31,0.10)",
    },
    "dark": {
        "col_backlog_bg": "#26262C",
        "col_backlog_border": "#43434D",
        "col_backlog_head": "#A8A8B3",
        "col_backlog_head_bg": "#2E2E35",
        "col_done_bg": "#18251C",
        "col_done_border": "#5FB37A",
        "col_done_head": "#5FB37A",
        "col_done_head_bg": "#1E2F24",
        "item_bg": "#1E1E23",
        "item_fg": "#EDEDF0",
        "item_border": "#32323A",
        "item_shadow": "0 1px 0 rgba(0,0,0,0.30)",
        "item_shadow_hover": "0 1px 1px rgba(0,0,0,0.40)",
    },
}


def _board_css(dark_mode: bool) -> str:
    p = _BOARD_PALETTE["dark" if dark_mode else "light"]
    return f"""
    .sortable-component {{
        display: flex;
        gap: 16px;
        width: 100%;
        height: 100%;
        align-items: stretch;
    }}

    .sortable-container {{
        flex: 1;
        min-width: 0;
        min-height: 720px;
        border-radius: 14px;
        padding: 14px;
        border: 1px solid;
        display: flex;
        flex-direction: column;
    }}

    .sortable-container[data-header="Backlog"] {{
        background: {p['col_backlog_bg']};
        border-color: {p['col_backlog_border']};
    }}

    .sortable-container[data-header*="Done"] {{
        background: {p['col_done_bg']};
        border-color: {p['col_done_border']};
    }}

    .sortable-container-header {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: -0.01em;
        margin-bottom: 12px;
        padding: 8px 10px;
        border-radius: 8px;
        text-align: center;
    }}

    .sortable-container[data-header="Backlog"] .sortable-container-header {{
        color: {p['col_backlog_head']};
        background: {p['col_backlog_head_bg']};
    }}

    .sortable-container[data-header*="Done"] .sortable-container-header {{
        color: {p['col_done_head']};
        background: {p['col_done_head_bg']};
    }}

    .sortable-container-body {{ flex: 1; }}

    .sortable-item {{
        background: {p['item_bg']};
        color: {p['item_fg']} !important;
        border: 1px solid {p['item_border']};
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13.5px;
        font-weight: 500;
        line-height: 1.45;
        cursor: grab;
        transition: box-shadow 0.16s ease, transform 0.16s ease;
        box-shadow: {p['item_shadow']};
    }}

    .sortable-item:hover {{
        transform: translateY(-1px);
        box-shadow: {p['item_shadow_hover']};
    }}

    .sortable-item:active {{ cursor: grabbing; }}
    """


def kanban_page(data):
    st.header("🎯 Daily Board")
    st.caption("Drag tasks between Backlog and Done.")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    selected_date = st.date_input(
        "Choose task date",
        value=date.today()
    )

    filter_labels = ["All"]
    filter_labels.extend([f"🧒 {kid['name']}" for kid in data["kids"]])
    filter_labels.extend([f"👨‍👩‍👧 {p['name']}" for p in data.get("parents", [])])

    selected_filter = st.segmented_control(
        "Filter", filter_labels, default="All", key="kanban_filter"
    )

    daily_tasks = [
        task for task in data["tasks"]
        if task.get("due_date") == selected_date.isoformat()
    ]

    filtered_tasks = filter_tasks(daily_tasks, selected_filter, data)

    if not filtered_tasks:
        st.info("No tasks for this date.")
        return

    st.write(f"Showing tasks for: **{selected_date.isoformat()}** ({len(filtered_tasks)} tasks)")

    item_to_task_id = {}
    containers = []

    for status in TASK_STATUSES:
        items = []

        for task in filtered_tasks:
            if task["status"] == status:
                assignee_label = get_assignee_label(data, task)

                status_emoji = {
                    "Backlog": "📋",
                    "Done": "✅"
                }.get(status, "❓")

                item_label = (
                    f"{status_emoji} {task['title']} | {assignee_label} | {task['points']} pts"
                )

                items.append(item_label)
                item_to_task_id[item_label] = task["id"]

        containers.append(
            {
                "header": f"{status} ({len(items)})",
                "items": items
            }
        )

    # This board renders inside a streamlit-sortables iframe, a separate
    # document that does NOT inherit the app's CSS custom properties. The values
    # below are therefore literals, resolved per theme from session state, rather
    # than var(--...) references.
    custom_style = _board_css(dark_mode=bool(st.session_state.get("dark_mode")))

    sorted_containers = sort_items(
        containers,
        multi_containers=True,
        custom_style=custom_style,
        key=f"kanban_sortable_{selected_date}_{selected_filter}"
    )

    changed = update_task_statuses_from_board(
        data,
        sorted_containers,
        item_to_task_id
    )

    if changed:
        st.success("Board updated automatically.")
        st.rerun()


def update_task_statuses_from_board(data, sorted_containers, item_to_task_id):
    changed = False
    overdue_warnings = []
    blocked_tasks = []

    for container in sorted_containers:
        new_status = container["header"].split(" (")[0]

        if new_status not in TASK_STATUSES:
            continue

        for item_label in container["items"]:
            task_id = item_to_task_id.get(item_label)

            if task_id is None:
                continue

            for task in data["tasks"]:
                if task["id"] == task_id:
                    old_status = task["status"]

                    if old_status != new_status:
                        if new_status == "Done":
                            allowed, reason = can_mark_done(task)
                            if not allowed:
                                blocked_tasks.append(task["title"])
                                break

                        updates = {
                            "status": new_status
                        }

                        if old_status != "Done" and new_status == "Done":
                            today = date.today()
                            year, week, _ = today.isocalendar()

                            updates["completed_date"] = today.isoformat()
                            updates["completed_week"] = f"{year}-W{week}"

                            task_copy = {**task, "completed_date": today.isoformat()}
                            effective = get_effective_points(task_copy)
                            if effective == 0:
                                overdue_warnings.append(task["title"])

                        elif old_status == "Done" and new_status != "Done":
                            updates["completed_date"] = None
                            updates["completed_week"] = None

                        update_task(task_id, updates)
                        changed = True

                    break

    if blocked_tasks:
        st.warning(
            f"⚠️ Can't mark as done (future or more than {OVERDUE_DAYS} days overdue): "
            f"{', '.join(blocked_tasks)}"
        )

    if overdue_warnings:
        st.warning(
            f"⚠️ {len(overdue_warnings)} task(s) were overdue by more than {OVERDUE_DAYS} days. "
            f"0 points awarded for: {', '.join(overdue_warnings)}"
        )

    if changed or blocked_tasks:
        st.rerun()

    return changed


def filter_tasks(tasks, selected_filter, data):
    if selected_filter == "All":
        return tasks

    if selected_filter.startswith("🧒 "):
        name = selected_filter.replace("🧒 ", "")
        kid = next((k for k in data["kids"] if k["name"] == name), None)
        if kid:
            return [t for t in tasks if t.get("kid_id") == kid["id"]]

    if selected_filter.startswith("👨‍👩‍👧 "):
        name = selected_filter.replace("👨‍👩‍👧 ", "")
        parent = next((p for p in data.get("parents", []) if p["name"] == name), None)
        if parent:
            return [t for t in tasks if t.get("parent_id") == parent["id"]]

    return tasks


def get_assignee_label(data, task):
    if task.get("kid_id"):
        kid = get_kid(data, task["kid_id"])
        return f"🧒 {kid['name']}" if kid else "🧒 Unknown"

    if task.get("parent_id"):
        for parent in data.get("parents", []):
            if parent["id"] == task["parent_id"]:
                return f"👨‍👩‍👧 {parent['name']}"

        return "👨‍👩‍👧 Unknown"

    return "Unknown"
