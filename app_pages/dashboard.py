import streamlit as st

from utils.data_helpers import save_data, get_kid, today_string, current_week_key
from utils.task_helpers import get_today_tasks, get_weekly_leaderboard, move_task, TASK_STATUSES


def dashboard_page(data):
    st.header("Daily Dashboard")

    st.write(f"Today: **{today_string()}**")
    st.write(f"This week: **{current_week_key()}**")

    if not data["kids"]:
        st.info("No children added yet. Go to Admin and add your children first.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        show_today_tasks(data)

    with col2:
        show_weekly_leaderboard(data)


def show_today_tasks(data):
    st.subheader("Today’s Tasks")

    today_tasks = get_today_tasks(data)

    if not today_tasks:
        st.success("No unfinished tasks for today.")
        return

    for task in today_tasks:
        kid = get_kid(data, task["kid_id"])

        with st.container(border=True):
            st.write(f"### {task['title']}")
            st.write(f"Child: **{kid['name'] if kid else 'Unknown'}**")
            st.write(f"Status: **{task['status']}**")
            st.write(f"Reward: **{task['points']} points**")

            new_status = st.selectbox(
                "Move task",
                TASK_STATUSES,
                index=TASK_STATUSES.index(task["status"]),
                key=f"dashboard_task_{task['id']}"
            )

            if new_status != task["status"]:
                moved = move_task(task, new_status)

                if moved:
                    save_data(data)

                    if new_status == "Done":
                        st.success(f"Well done! {task['points']} points added.")

                    st.rerun()


def show_weekly_leaderboard(data):
    st.subheader("Weekly Leaderboard")

    leaderboard = get_weekly_leaderboard(data)

    if not leaderboard:
        st.info("No points yet.")
        return

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
