import streamlit as st
from datetime import date

from utils.data_helpers import get_kid, today_string, current_week_key
from utils.task_helpers import get_today_tasks, get_weekly_leaderboard, get_weekly_parent_leaderboard, TASK_STATUSES
from utils.db_helpers import update_task


def dashboard_page(data):
    st.header("Daily Dashboard")

    st.write(f"Today: **{today_string()}**")
    st.write(f"This week: **{current_week_key()}**")

    if not data["kids"] and not data.get("parents"):
        st.info("No children or parents added yet. Go to Admin to add them first.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        show_today_tasks(data)

    with col2:
        show_weekly_leaderboard(data)


def show_today_tasks(data):
    st.subheader("Today's Tasks")

    today_tasks = get_today_tasks(data)

    if not today_tasks:
        st.success("No unfinished tasks for today.")
        return

    for task in today_tasks:
        assignee_label = get_assignee_display(data, task)

        with st.container(border=True):
            st.write(f"### {task['title']}")
            st.write(f"Assigned to: **{assignee_label}**")
            st.write(f"Status: **{task['status']}**")
            st.write(f"Reward: **{task['points']} points**")

            new_status = st.selectbox(
                "Move task",
                TASK_STATUSES,
                index=TASK_STATUSES.index(task["status"]),
                key=f"dashboard_task_{task['id']}"
            )

            if new_status != task["status"]:
                updates = {
                    "status": new_status
                }

                if task["status"] != "Done" and new_status == "Done":
                    today = date.today()
                    year, week, _ = today.isocalendar()

                    updates["completed_date"] = today.isoformat()
                    updates["completed_week"] = f"{year}-W{week}"

                elif task["status"] == "Done" and new_status != "Done":
                    updates["completed_date"] = None
                    updates["completed_week"] = None

                update_task(task["id"], updates)

                if new_status == "Done":
                    st.success(f"Well done! {task['points']} points added.")

                st.rerun()


def show_weekly_leaderboard(data):
    st.subheader("👧 Weekly Kids Leaderboard")

    leaderboard = get_weekly_leaderboard(data)

    if leaderboard:
        for index, child in enumerate(leaderboard, start=1):
            if index == 1:
                medal = "🥇"
            elif index == 2:
                medal = "🥈"
            elif index == 3:
                medal = "🥉"
            else:
                medal = "⭐"

            st.write(f"{medal} **{child['name']}** — {child['points']} points")
    else:
        st.info("No points yet.")

    parents = data.get("parents", [])

    if parents:
        st.subheader("👨‍👩‍👧 Weekly Parents Leaderboard")

        parent_leaderboard = get_weekly_parent_leaderboard(data)

        if parent_leaderboard:
            for index, parent in enumerate(parent_leaderboard, start=1):
                if index == 1:
                    medal = "🥇"
                elif index == 2:
                    medal = "🥈"
                elif index == 3:
                    medal = "🥉"
                else:
                    medal = "⭐"

                st.write(f"{medal} **{parent['name']}** — {parent['points']} points")
        else:
            st.info("No points yet.")


def get_assignee_display(data, task):
    if task.get("kid_id"):
        kid = get_kid(data, task["kid_id"])
        return f"👧 {kid['name']}" if kid else "👧 Unknown"

    if task.get("parent_id"):
        for parent in data.get("parents", []):
            if parent["id"] == task["parent_id"]:
                return f"👨‍👩‍👧 {parent['name']}"

        return "👨‍👩‍👧 Unknown"

    return "Unknown"
