import streamlit as st
from datetime import date
from streamlit_sortables import sort_items

from utils.data_helpers import get_kid
from utils.task_helpers import TASK_STATUSES
from utils.db_helpers import update_task


def kanban_page(data):
    st.header("🎯 Daily Kanban Board")
    st.caption("Drag tasks between Backlog, In Progress and Done.")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    selected_date = st.date_input(
        "Choose task date",
        value=date.today()
    )

    kid_options = {kid["name"]: kid["id"] for kid in data["kids"]}
    parent_options = {p["name"]: p["id"] for p in data.get("parents", [])}

    filter_labels = ["All tasks"]

    if kid_options:
        filter_labels.append("👧 All children")

    if parent_options:
        filter_labels.append("👨‍👩‍👧 All parents")

    filter_labels.extend([f"👧 {name}" for name in kid_options.keys()])
    filter_labels.extend([f"👨‍👩‍👧 {name}" for name in parent_options.keys()])

    selected_filter = st.selectbox(
        "Filter tasks",
        filter_labels
    )

    daily_tasks = [
        task for task in data["tasks"]
        if task.get("due_date") == selected_date.isoformat()
    ]

    filtered_tasks = filter_tasks(daily_tasks, selected_filter, kid_options, parent_options)

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
                    "In Progress": "⏳",
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

    custom_style = """
    .sortable-component {
        display: flex;
        gap: 20px;
        width: 100%;
        height: 100%;
        align-items: stretch;
    }

    .sortable-container {
        flex: 1;
        min-width: 0;
        min-height: 720px;
        border-radius: 15px;
        padding: 15px;
        border: 2px solid;
        display: flex;
        flex-direction: column;
    }

    .sortable-container[data-header="Backlog"] {
        background: linear-gradient(135deg, rgba(158, 158, 158, 0.05), rgba(158, 158, 158, 0.02));
        border-color: #9E9E9E;
    }

    .sortable-container[data-header*="In Progress"] {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.05), rgba(255, 152, 0, 0.02));
        border-color: #FF9800;
    }

    .sortable-container[data-header*="Done"] {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.05), rgba(76, 175, 80, 0.02));
        border-color: #4CAF50;
    }

    .sortable-container-header {
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 15px;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }

    .sortable-container[data-header="Backlog"] .sortable-container-header {
        color: #9E9E9E;
        background: rgba(158, 158, 158, 0.1);
    }

    .sortable-container[data-header*="In Progress"] .sortable-container-header {
        color: #FF9800;
        background: rgba(255, 152, 0, 0.1);
    }

    .sortable-container[data-header*="Done"] .sortable-container-header {
        color: #4CAF50;
        background: rgba(76, 175, 80, 0.1);
    }

    .sortable-container-body {
        flex: 1;
    }

    .sortable-item {
        background: linear-gradient(135deg, #FF8A80 0%, #4ECDC4 100%);
        color: white !important;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: 600;
        cursor: grab;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .sortable-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }

    .sortable-item:active {
        cursor: grabbing;
    }
    """
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
                        updates = {
                            "status": new_status
                        }

                        if old_status != "Done" and new_status == "Done":
                            today = date.today()
                            year, week, _ = today.isocalendar()

                            updates["completed_date"] = today.isoformat()
                            updates["completed_week"] = f"{year}-W{week}"

                        elif old_status == "Done" and new_status != "Done":
                            updates["completed_date"] = None
                            updates["completed_week"] = None

                        update_task(task_id, updates)
                        changed = True

                    break

    return changed


def filter_tasks(tasks, selected_filter, kid_options, parent_options):
    if selected_filter == "All tasks":
        return tasks

    if selected_filter == "👧 All children":
        return [t for t in tasks if t.get("kid_id") is not None]

    if selected_filter == "👨‍👩‍👧 All parents":
        return [t for t in tasks if t.get("parent_id") is not None]

    if selected_filter.startswith("👧 ") and "All children" not in selected_filter:
        kid_name = selected_filter.replace("👧 ", "")

        if kid_name in kid_options:
            return [t for t in tasks if t.get("kid_id") == kid_options[kid_name]]

    if selected_filter.startswith("👨‍👩‍👧 ") and "All parents" not in selected_filter:
        parent_name = selected_filter.replace("👨‍👩‍👧 ", "")

        if parent_name in parent_options:
            return [t for t in tasks if t.get("parent_id") == parent_options[parent_name]]

    return tasks


def get_assignee_label(data, task):
    if task.get("kid_id"):
        kid = get_kid(data, task["kid_id"])
        return f"👧 {kid['name']}" if kid else "👧 Unknown"

    if task.get("parent_id"):
        for parent in data.get("parents", []):
            if parent["id"] == task["parent_id"]:
                return f"👨‍👩‍👧 {parent['name']}"

        return "👨‍👩‍👧 Unknown"

    return "Unknown"
