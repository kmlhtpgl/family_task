import streamlit as st
from datetime import date, timedelta
from collections import defaultdict

from utils.task_helpers import (
    get_rank,
    get_total_points_for_kid, get_total_points_for_parent,
    get_weekly_points_for_kid, get_weekly_points_for_parent,
    TASK_STATUSES, get_effective_points,
)
from utils.db_helpers import update_task

PRAYER_NAMES = ["Fecr", "Zuhr", "Asr", "Maghrib", "Isha"]


def dashboard_page(data):
    st.header("📊 Weekly Dashboard")

    if not data["kids"] and not data.get("parents"):
        st.info("No children or parents added yet. Go to Admin to add them first.")
        return

    week_offset = st.session_state.get("week_offset", 0)
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)

    col_prev, col_week, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ Prev", key="prev_week"):
            st.session_state.week_offset = week_offset - 1
            st.rerun()
    with col_week:
        if week_offset == 0:
            st.markdown(f"<h3 style='text-align:center;color:var(--primary);'>📅 This Week</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align:center;color:var(--primary);'>📅 {monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}</h3>", unsafe_allow_html=True)
        st.caption(f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}")
    with col_next:
        if st.button("Next ▶", key="next_week"):
            st.session_state.week_offset = week_offset + 1
            st.rerun()

    # ── Section 1: Weekly Tasks ──
    st.subheader("📅 Weekly Tasks")

    person_options = {}
    for kid in data["kids"]:
        person_options[f"🧒 {kid['name']}"] = ("kid", kid["id"])
    for parent in data.get("parents", []):
        person_options[f"👨‍👩‍👧 {parent['name']}"] = ("parent", parent["id"])

    if person_options:
        selected_person = st.segmented_control(
            "Person", list(person_options.keys()), default=list(person_options.keys())[0], key="weekly_person"
        )
        person_type, person_id = person_options[selected_person]

        weekly_tasks = []
        for task in data["tasks"]:
            if person_type == "kid" and task.get("kid_id") != person_id:
                continue
            if person_type == "parent" and task.get("parent_id") != person_id:
                continue
            due = task.get("due_date")
            if not due:
                continue
            try:
                due_date = date.fromisoformat(due)
            except (ValueError, TypeError):
                continue
            if not (monday <= due_date <= sunday):
                continue
            weekly_tasks.append(task)

        tasks_by_day = defaultdict(list)
        for task in weekly_tasks:
            d = date.fromisoformat(task["due_date"])
            tasks_by_day[d.weekday()].append(task)

        if not weekly_tasks:
            st.info(f"No tasks for {selected_person} this week.")
        else:
            DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cols = st.columns(7)
            for day_idx in range(7):
                current_date = monday + timedelta(days=day_idx)
                day_tasks = tasks_by_day.get(day_idx, [])
                day_tasks.sort(key=lambda t: t["title"])
                is_today = current_date == date.today()

                with cols[day_idx]:
                    header_bg = "background:var(--primary);color:white;border-radius:8px;padding:6px 4px;" if is_today else ""
                    st.markdown(
                        f"<div style='text-align:center;{header_bg}'>"
                        f"<b>{DAY_SHORT[day_idx]}</b><br>"
                        f"<small>{current_date.strftime('%m/%d')}</small>"
                        f"<br><small>{len(day_tasks)}</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    for task in day_tasks:
                        icon = "✅" if task["status"] == "Done" else "📋"
                        if st.button(f"{icon} {task['title']}", key=f"cal_{task['id']}", use_container_width=True):
                            if task["status"] == "Done":
                                updates = {
                                    "status": "Backlog",
                                    "completed_date": None,
                                    "completed_week": None,
                                }
                                update_task(task["id"], updates)
                                st.success(f"↩️ {task['title']} moved back to Backlog.")
                            else:
                                today_dt = date.today()
                                year, week_num, _ = today_dt.isocalendar()
                                updates = {
                                    "status": "Done",
                                    "completed_date": today_dt.isoformat(),
                                    "completed_week": f"{year}-W{week_num}",
                                }
                                update_task(task["id"], updates)
                                task_copy = {**task, "completed_date": today_dt.isoformat()}
                                effective = get_effective_points(task_copy)
                                if effective == 0:
                                    st.warning("⚠️ Overdue – 0 points awarded.")
                                else:
                                    st.success(f"✨ {effective} points added!")
                            st.rerun()
    else:
        st.info("No children or parents added yet.")

    # ── Section 2: Person Cards ──
    st.subheader("👨‍👩‍👧‍👦 This Week at a Glance")

    def count_missed_prayers(person_id, field):
        count = 0
        for t in data["tasks"]:
            if t.get(field) != person_id:
                continue
            if t.get("title") not in PRAYER_NAMES:
                continue
            if t.get("status") == "Done":
                continue
            due = t.get("due_date")
            if not due:
                continue
            try:
                d = date.fromisoformat(due)
                if monday <= d <= sunday:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count

    people = []
    for kid in data["kids"]:
        weekly_pts = get_weekly_points_for_kid(data, kid["id"])
        total_pts = get_total_points_for_kid(data, kid["id"])
        rank, icon = get_rank(total_pts)
        missed = count_missed_prayers(kid["id"], "kid_id")
        people.append(("🧒", kid["name"], weekly_pts, rank, icon, missed))

    for parent in data.get("parents", []):
        weekly_pts = get_weekly_points_for_parent(data, parent["id"])
        total_pts = get_total_points_for_parent(data, parent["id"])
        rank, icon = get_rank(total_pts)
        missed = count_missed_prayers(parent["id"], "parent_id")
        people.append(("👨‍👩‍👧", parent["name"], weekly_pts, rank, icon, missed))

    card_cols = st.columns(len(people))
    for i, (emoji, name, pts, rank, icon, missed) in enumerate(people):
        with card_cols[i]:
            st.markdown(f"""
            <div class="card card--stat" style="text-align:center;padding:16px;">
                <div style="font-size:2em;">{emoji}</div>
                <h4 style="margin:4px 0;font-size:0.95em;">{name}</h4>
                <div class="value" style="font-size:1.6em;">{pts}</div>
                <div class="label">pts this week</div>
                <hr style="margin:8px 0;">
                <div style="font-size:1.3em;">{icon}</div>
                <div style="font-size:0.8em;color:var(--text-secondary);">{rank}</div>
                <hr style="margin:8px 0;">
                <div style="font-size:1.1em;color:var(--danger);">🕌 {missed}</div>
                <div class="label">missed prayers</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Section 3: Weekly Summary ──
    st.subheader("📊 This Week Summary")

    st.markdown("**🕌 Missed Prayers This Week**")

    kids_sorted = sorted(data["kids"], key=lambda k: k["name"])
    missed = defaultdict(lambda: defaultdict(int))

    for task in data["tasks"]:
        if task.get("title") not in PRAYER_NAMES:
            continue
        kid_id = task.get("kid_id")
        if kid_id is None:
            continue
        due = task.get("due_date")
        if not due:
            continue
        try:
            due_date = date.fromisoformat(due)
        except (ValueError, TypeError):
            continue
        if not (monday <= due_date <= sunday):
            continue
        if task.get("status") != "Done":
            missed[task["title"]][kid_id] += 1

    if kids_sorted:
        header_cols = st.columns([2] + [1] * len(kids_sorted))
        header_cols[0].markdown("**Prayer**")
        for i, kid in enumerate(kids_sorted):
            header_cols[i + 1].markdown(f"**🧒 {kid['name']}**")

        for prayer in PRAYER_NAMES:
            cols = st.columns([2] + [1] * len(kids_sorted))
            cols[0].write(prayer)
            for i, kid in enumerate(kids_sorted):
                count = missed[prayer].get(kid["id"], 0)
                color = "var(--danger)" if count > 0 else "var(--success)"
                cols[i + 1].markdown(
                    f"<span style='color:{color};font-weight:700;'>{count}</span>",
                    unsafe_allow_html=True,
                )

        total_cols = st.columns([2] + [1] * len(kids_sorted))
        total_cols[0].markdown("**Total**")
        for i, kid in enumerate(kids_sorted):
            total = sum(missed[p][kid["id"]] for p in PRAYER_NAMES)
            total_cols[i + 1].markdown(
                f"<span style='font-weight:700;'>{total}</span>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    book_count = len([b for b in data["books"] if b.get("status") == "In Progress"])
    surah_count = len([s for s in data.get("surahs", []) if s.get("status") != "Memorized"])

    mini_cols = st.columns(2)
    with mini_cols[0]:
        st.markdown(f"""
        <div class="card" style="text-align:center;padding:12px;">
            <div style="font-size:1.5em;">📚</div>
            <div class="value" style="font-size:1.4em;">{book_count}</div>
            <div class="label">Books in progress</div>
        </div>
        """, unsafe_allow_html=True)
    with mini_cols[1]:
        st.markdown(f"""
        <div class="card" style="text-align:center;padding:12px;">
            <div style="font-size:1.5em;">📖</div>
            <div class="value" style="font-size:1.4em;">{surah_count}</div>
            <div class="label">Surahs in progress</div>
        </div>
        """, unsafe_allow_html=True)
