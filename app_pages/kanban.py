import streamlit as st
from datetime import date
from streamlit_sortables import sort_items

from utils.data_helpers import get_kid
from utils.task_helpers import TASK_STATUSES
from utils.db_helpers import update_task


def kanban_page(data):
    st.header("Daily Kanban Board")
    st.caption("Drag tasks between Backlog, In Progress and Done.")

    if not data["kids"]:
        st.info("Add children first in Admin.")
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
        for parent in data["parents"]
    }

    selected_child = st.selectbox(
        "Choose child",
        ["All children"] + list(kid_options.keys()) +list(parent_options.keys())
    )

    daily_tasks = [
        task for task in data["tasks"]
        if task.get("due_date") == selected_date.isoformat()
    ]

    if selected_child == "All children":
        filtered_tasks = daily_tasks
    elif selected_child_id == kid_options[selected_child]: 
        filtered_tasks = [
            task for task in daily_tasks
            if task["kid_id"] == selected_child_id
        ]
    else:
        selected_child_id = parent_options[selected_child]
        filtered_tasks = [
            task for task in daily_tasks
            if task["parent_id"] == selected_child_id
        ]    

    if not filtered_tasks:
        st.info("No tasks for this date.")
        return

    st.write(f"Showing tasks for: **{selected_date.isoformat()}**")

    item_to_task_id = {}
    containers = []

    for status in TASK_STATUSES:
        items = []

        for task in filtered_tasks:
            if task["status"] == status:
                kid = get_kid(data, task["kid_id"])
                kid_name = kid["name"] if kid else "Unknown"

                item_label = (
                    f"#{task['id']} | {task['title']} | "
                    f"{kid_name} | {task['points']} points"
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
        align-items: stretch;  /* Forces all columns to have equal height */
    }

    .sortable-container {
        flex: 1;
        min-width: 0;
        min-height: 720px;  /* Keep columns the same height */
        background-color: #f4f5f7;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #ddd;
        display: flex;
        flex-direction: column;
    }

    .sortable-container-header {
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 12px;
        color: #172b4d;
        background-color: white;
        padding: 8px;
    }

    .sortable-container-body {
        flex: 1;
        height: 100%;  /* Ensures items fill the column equally */
    }

    .sortable-item {
        background-color: white !important;
        color: #172b4d !important;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 6px solid #2684ff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
        font-size: 15px;
        font-weight: 500;
        cursor: grab;
    }

    .sortable-item:active {
        cursor: grabbing;
    }
    """
    sorted_containers = sort_items(
        containers,
        multi_containers=True,
        custom_style=custom_style,
        key=f"kanban_sortable_{selected_date}_{selected_child}"
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
