import streamlit as st
from datetime import date, timedelta

from utils.data_helpers import get_kid, today_string, current_week_key
from utils.task_helpers import get_today_tasks, get_weekly_leaderboard, get_weekly_parent_leaderboard, TASK_STATUSES
from utils.db_helpers import update_task


def dashboard_page(data):
    st.header("📊 Daily Dashboard")

    # Week selector
    week_offset = st.session_state.get("week_offset", 0)

    col_prev, col_week, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.button("◀ Prev", key="prev_week"):
            st.session_state.week_offset = week_offset - 1
            st.rerun()

    with col_week:
        target_week = date.today() + timedelta(weeks=week_offset)
        year, week_num, _ = target_week.isocalendar()
        week_label = f"Week {week_num} ({year})"

        if week_offset == 0:
            st.markdown(f"<h3 style='text-align:center;color:#FF8A80;'>📅 This Week</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align:center;color:#FF8A80;'>📅 {week_label}</h3>", unsafe_allow_html=True)

    with col_next:
        if st.button("Next ▶", key="next_week"):
            st.session_state.week_offset = week_offset + 1
            st.rerun()

    st.write(f"Today: **{today_string()}**")

    if not data["kids"] and not data.get("parents"):
        st.info("No children or parents added yet. Go to Admin to add them first.")
        return

    # Quick summary metrics
    st.subheader("📈 Quick Stats")

    all_tasks = data["tasks"]
    done_tasks = [t for t in all_tasks if t.get("status") == "Done"]
    in_progress_tasks = [t for t in all_tasks if t.get("status") == "In Progress"]
    all_books = data["books"]
    finished_books = [b for b in all_books if b.get("status") == "Finished"]

    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.markdown(
            f'<div class="metric-card"><h3>✅ Done Tasks</h3><div class="value">{len(done_tasks)}</div><div class="label">Total completed</div></div>',
            unsafe_allow_html=True
        )

    with metric_cols[1]:
        st.markdown(
            f'<div class="metric-card"><h3>⏳ In Progress</h3><div class="value">{len(in_progress_tasks)}</div><div class="label">Active now</div></div>',
            unsafe_allow_html=True
        )

    with metric_cols[2]:
        st.markdown(
            f'<div class="metric-card"><h3>📚 Books Done</h3><div class="value">{len(finished_books)}</div><div class="label">Total read</div></div>',
            unsafe_allow_html=True
        )

    with metric_cols[3]:
        total_points = sum(t.get("points", 0) for t in done_tasks)
        st.markdown(
            f'<div class="metric-card"><h3>⭐ Total Points</h3><div class="value">{total_points}</div><div class="label">Family total</div></div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Tabs for tasks vs charts vs leaderboard
    tab_tasks, tab_charts, tab_leaderboard = st.tabs(["📋 Tasks", "📊 Charts", "🏆 Leaderboard"])

    with tab_tasks:
        show_today_tasks(data)

    with tab_charts:
        show_progress_charts(data)

    with tab_leaderboard:
        show_weekly_leaderboard(data, week_offset)


def show_today_tasks(data):
    st.subheader("📋 Today's Tasks")

    today_tasks = get_today_tasks(data)

    if not today_tasks:
        st.success("✅ No unfinished tasks for today!")
        return

    for task in today_tasks:
        assignee_label = get_assignee_display(data, task)

        with st.container():
            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<h4 style="margin:0;">{task["title"]}</h4>'
                f'<p style="margin:5px 0 0 0;color:#666;">{assignee_label} • {task["points"]} points</p>'
                f'</div>'
                f'<span class="status-badge status-{task["status"].lower().replace(" ", "-")}">{task["status"]}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            new_status = st.selectbox(
                "Move task",
                TASK_STATUSES,
                index=TASK_STATUSES.index(task["status"]),
                key=f"dashboard_task_{task['id']}",
                label_visibility="collapsed"
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


def show_progress_charts(data):
    st.subheader("📊 Progress Charts")

    # Tasks by status
    st.write("### Tasks by Status")

    status_counts = {status: 0 for status in TASK_STATUSES}

    for task in data["tasks"]:
        status_counts[task.get("status", "Backlog")] += 1

    chart_data = {
        "Status": list(status_counts.keys()),
        "Count": list(status_counts.values())
    }

    st.bar_chart(chart_data, x="Status", y="Count", color="#FF8A80", horizontal=True)

    st.divider()

    # Books by status
    st.write("### Reading Progress")

    books_in_progress = [b for b in data["books"] if b.get("status") == "In Progress"]
    books_finished = [b for b in data["books"] if b.get("status") == "Finished"]

    book_data = {
        "Status": ["In Progress", "Finished"],
        "Count": [len(books_in_progress), len(books_finished)]
    }

    st.bar_chart(book_data, x="Status", y="Count", color="#4ECDC4", horizontal=True)

    st.divider()

    # Points per child this week
    st.write("### Points per Child (This Week)")

    week = current_week_key()
    child_points = []

    for kid in data["kids"]:
        points = sum(
            t.get("points", 0)
            for t in data["tasks"]
            if t.get("kid_id") == kid["id"]
            and t.get("status") == "Done"
            and t.get("completed_week") == week
        )

        child_points.append({"name": kid["name"], "points": points})

    if child_points:
        child_df = {
            "Child": [c["name"] for c in child_points],
            "Points": [c["points"] for c in child_points]
        }

        st.bar_chart(child_df, x="Child", y="Points", color="#FFD93D", horizontal=True)
    else:
        st.info("No points earned this week yet.")

    st.divider()

    # Parent points
    if data.get("parents"):
        st.write("### Points per Parent (This Week)")

        parent_points = []

        for parent in data["parents"]:
            points = sum(
                t.get("points", 0)
                for t in data["tasks"]
                if t.get("parent_id") == parent["id"]
                and t.get("status") == "Done"
                and t.get("completed_week") == week
            )

            parent_points.append({"name": parent["name"], "points": points})

        if parent_points:
            parent_df = {
                "Parent": [p["name"] for p in parent_points],
                "Points": [p["points"] for p in parent_points]
            }

            st.bar_chart(parent_df, x="Parent", y="Points", color="#4ECDC4", horizontal=True)


def show_weekly_leaderboard(data, week_offset=0):
    st.subheader("👧 Kids Leaderboard")

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

            st.markdown(
                f'<div class="task-item">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="font-size:1.5em;">{medal}</span>'
                f'<strong>{child["name"]}</strong>'
                f'<strong>{child["points"]} points</strong>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("No points yet.")

    parents = data.get("parents", [])

    if parents:
        st.subheader("👨‍👩‍👧 Parents Leaderboard")

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

                st.markdown(
                    f'<div class="task-item">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="font-size:1.5em;">{medal}</span>'
                    f'<strong>{parent["name"]}</strong>'
                    f'<strong>{parent["points"]} points</strong>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
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
