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

    kid_options = {
        kid["name"]: kid["id"]
        for kid in data["kids"]
    }

    parent_options = {
        parent["name"]: parent["id"]
        for parent in data.get("parents", [])
    }

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

    filtered_tasks = daily_tasks

    if selected_filter == "All tasks":
        pass

    elif selected_filter == "👧 All children":
        filtered_tasks = [
            task for task in daily_tasks
            if task.get("kid_id") is not None
        ]

    elif selected_filter == "👨‍👩‍👧 All parents":
        filtered_tasks = [
            task for task in daily_tasks
            if task.get("parent_id") is not None
        ]

    elif selected_filter.startswith("👧 ") and "All children" not in selected_filter:
        kid_name = selected_filter.replace("👧 ", "")

        if kid_name in kid_options:
            filtered_tasks = [
                task for task in daily_tasks
                if task.get("kid_id") == kid_options[kid_name]
            ]

    elif selected_filter.startswith("👨‍👩‍👧 ") and "All parents" not in selected_filter:
        parent_name = selected_filter.replace("👨‍👩‍👧 ", "")

        if parent_name in parent_options:
            filtered_tasks = [
                task for task in daily_tasks
                if task.get("parent_id") == parent_options[parent_name]
            ]

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

                item_label = (
                    f"#{task['id']} | {task['title']} | "
                    f"{assignee_label} | {task['points']} points"
                )

                items.append(item_label)
                item_to_task_id[item_label] = task["id"]

        containers.append(
            {
                "header": status,
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
        background: linear-gradient(135deg, rgba(255, 138, 128, 0.05), rgba(78, 205, 196, 0.05));
        border-radius: 12px;
        padding: 12px;
        border: 2px solid #FF8A80;
        display: flex;
        flex-direction: column;
    }

    .sortable-container-header {
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 12px;
        color: #FF8A80;
        background-color: white;
        padding: 8px;
        border-radius: 8px;
    }

    .sortable-container-body {
        flex: 1;
        height: 100%;
    }

    .sortable-item {
        background: linear-gradient(135deg, #FF8A80 0%, #4ECDC4 100%);
        color: white !important;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 6px solid #FF6B6B;
        box-shadow: 0 4px 12px rgba(255, 138, 128, 0.2);
        font-size: 15px;
        font-weight: 600;
        cursor: grab;
        transition: all 0.3s ease;
    }

    .sortable-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255, 138, 128, 0.3);
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
        new_status = container["header"]

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
