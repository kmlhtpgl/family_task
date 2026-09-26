import streamlit as st
from datetime import date, timedelta
from collections import defaultdict

from utils.task_helpers import (
    get_rank,
    get_total_points_for_kid, get_total_points_for_parent,
    get_weekly_points_for_kid, get_weekly_points_for_parent,
    TASK_STATUSES, get_effective_points,
    OVERDUE_DAYS, can_mark_done,
)
from utils.db_helpers import update_task

PRAYER_NAMES = ["Fecr", "Zuhr", "Asr", "Maghrib", "Isha"]


def dashboard_page(data):
    if not data["kids"] and not data.get("parents"):
        st.info("No children or parents added yet. Go to Admin to add them first.")
        return

    week_offset = st.session_state.get("week_offset", 0)
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)

    col_theme, col_prev, col_week, col_next = st.columns([1, 1, 5, 1])
    with col_theme:
        icon = "☀️" if st.session_state.dark_mode else "🌙"
        if st.button(
            icon,
            key="dashboard_theme_toggle",
            type="secondary",
            use_container_width=True,
            help="Toggle Day/Night theme",
        ):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_prev:
        if st.button("◀", key="prev_week", type="secondary", use_container_width=True):
            st.session_state.week_offset = week_offset - 1
            st.rerun()
    with col_week:
        if week_offset == 0:
            week_range = f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
            st.markdown(
                f'<div class="week-heading">📅 This Week <span class="week-range">{week_range}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            week_range = f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
            st.markdown(
                f'<div class="week-heading">📅 {week_range}</div>',
                unsafe_allow_html=True,
            )
    with col_next:
        if st.button("▶", key="next_week", type="secondary", use_container_width=True):
            st.session_state.week_offset = week_offset + 1
            st.rerun()

    # ── Section 1: Weekly Tasks ──
    col_head, col_show = st.columns([3, 1])
    with col_head:
        st.subheader("📅 Weekly Tasks")
    with col_show:
        show_all_week = st.toggle(
            "Show all week",
            key="show_all_week_toggle",
            help="Show and enable all 7 days of the week",
        )

    person_options = {}
    for kid in data["kids"]:
        person_options[f"🧒 {kid['name']}"] = ("kid", kid["id"])
    for parent in data.get("parents", []):
        person_options[f"👨‍👩‍👧 {parent['name']}"] = ("parent", parent["id"])

    if person_options:
        selected_person = st.segmented_control(
            "Person", list(person_options.keys()), default=list(person_options.keys())[0], key="weekly_person_cal"
        )
        if selected_person is None:
            selected_person = list(person_options.keys())[0]
        person_type, person_id = person_options[selected_person]

        person_tasks = []
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
            person_tasks.append((task, due_date))

        if show_all_week:
            display_dates = [monday + timedelta(days=i) for i in range(7)]
        else:
            display_dates = [today - timedelta(days=1), today, today + timedelta(days=1)]

        tasks_by_date = defaultdict(list)
        for task, due_date in person_tasks:
            if due_date in display_dates:
                tasks_by_date[due_date].append(task)

        if not any(tasks_by_date.get(d) for d in display_dates):
            if show_all_week:
                st.info(f"No tasks for {selected_person} this week.")
            else:
                st.info(f"No tasks for {selected_person} due yesterday, today or tomorrow.")
        else:
            st.markdown('<div class="week-grid"></div>', unsafe_allow_html=True)
            DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cols = st.columns(len(display_dates))
            for col, current_date in zip(cols, display_dates):
                day_tasks = tasks_by_date.get(current_date, [])
                day_tasks.sort(key=lambda t: t["title"])
                is_today = current_date == date.today()

                with col:
                    head_class = "day-head day-head--today" if is_today else "day-head"
                    st.markdown(
                        f'<div class="{head_class}">'
                        f"<b>{DAY_SHORT[current_date.weekday()]}</b> "
                        f"<small>{current_date.strftime('%m/%d')}</small>"
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
                                allowed, reason = can_mark_done(task)
                                if not allowed:
                                    if reason == "future":
                                        st.info(
                                            f"⏳ '{task['title']}' is due {task['due_date']} "
                                            f"and can't be completed before its due date."
                                        )
                                    else:
                                        st.warning(
                                            f"⚠️ '{task['title']}' is more than {OVERDUE_DAYS} days overdue "
                                            f"and can't be marked done now."
                                        )
                                    continue
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
            <div class="card card--stat card--center card--pad-sm">
                <div class="icon">{emoji}</div>
                <h4 class="row-title" style="margin:0.25rem 0;">{name}</h4>
                <div class="value">{pts}</div>
                <div class="label">pts this week</div>
                <hr>
                <div style="font-size:1.25rem;">{icon}</div>
                <div class="row-faint">{rank}</div>
                <hr>
                <div class="num strong" style="font-size:1.0625rem;color:var(--danger);">🕌 {missed}</div>
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
        header_cols[0].markdown('<div class="th">Prayer</div>', unsafe_allow_html=True)
        for i, kid in enumerate(kids_sorted):
            header_cols[i + 1].markdown(f'<div class="th center">🧒 {kid["name"]}</div>', unsafe_allow_html=True)

        for prayer in PRAYER_NAMES:
            cols = st.columns([2] + [1] * len(kids_sorted))
            cols[0].write(prayer)
            for i, kid in enumerate(kids_sorted):
                count = missed[prayer].get(kid["id"], 0)
                tone = "count--missed" if count > 0 else "count--ok"
                cols[i + 1].markdown(
                    f'<div class="count center {tone}">{count}</div>',
                    unsafe_allow_html=True,
                )

        total_cols = st.columns([2] + [1] * len(kids_sorted))
        total_cols[0].markdown('<div class="th">Total</div>', unsafe_allow_html=True)
        for i, kid in enumerate(kids_sorted):
            total = sum(missed[p][kid["id"]] for p in PRAYER_NAMES)
            total_cols[i + 1].markdown(
                f'<div class="count count--total center">{total}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    book_count = len([b for b in data["books"] if b.get("status") == "In Progress"])
    surah_count = len([s for s in data.get("surahs", []) if s.get("status") != "Memorized"])

    mini_cols = st.columns(2)
    with mini_cols[0]:
        st.markdown(f"""
        <div class="card card--center card--pad-sm">
            <div class="icon">📚</div>
            <div class="value">{book_count}</div>
            <div class="label">Books in progress</div>
        </div>
        """, unsafe_allow_html=True)
    with mini_cols[1]:
        st.markdown(f"""
        <div class="card card--center card--pad-sm">
            <div class="icon">📖</div>
            <div class="value">{surah_count}</div>
            <div class="label">Surahs in progress</div>
        </div>
        """, unsafe_allow_html=True)
