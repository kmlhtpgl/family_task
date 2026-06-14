import streamlit as st
from datetime import date, timedelta

from utils.db_helpers import mark_prayer_done, mark_prayer_not_done

PRAYER_NAMES = ["Fajr", "Zuhr", "Asr", "Maghrib", "Isha"]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def prayer_page(data):
    st.header("🕌 Prayer Tracker")
    st.caption("Tap a prayer to mark it done or undo it.")

    if not data["kids"] and not data.get("parents"):
        st.info("No children or parents added yet.")
        return

    labels = [f"🧒 {k['name']}" for k in data["kids"]]
    labels += [f"👨‍👩‍👧 {p['name']}" for p in data.get("parents", [])]
    selected = st.radio("Who do you want to track?", labels, horizontal=True, key="prayer_person")

    if selected.startswith("🧒 "):
        name = selected.replace("🧒 ", "")
        person_id = next(k["id"] for k in data["kids"] if k["name"] == name)
        person_type = "kid"
    else:
        name = selected.replace("👨‍👩‍👧 ", "")
        person_id = next(p["id"] for p in data["parents"] if p["name"] == name)
        person_type = "parent"

    week_offset = st.session_state.get("prayer_week_offset", 0)
    col_prev, col_week, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ Prev"):
            st.session_state.prayer_week_offset = week_offset - 1
            st.rerun()
    with col_week:
        today = date.today()
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        sunday = monday + timedelta(days=6)
        st.markdown(
            f"<h3 style='text-align:center;color:#FF8A80;'>"
            f"{monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}"
            f"</h3>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next ▶"):
            st.session_state.prayer_week_offset = week_offset + 1
            st.rerun()

    monday = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=week_offset)

    prayer_logs = data.get("prayer_logs", [])
    done_set = set()
    for log in prayer_logs:
        if log["person_id"] == person_id and log["person_type"] == person_type:
            done_set.add((log["prayer_name"], log["prayer_date"]))

    st.markdown("---")
    header_cols = st.columns([2] + [1] * 5)
    header_cols[0].markdown("**Day**")
    for j, prayer in enumerate(PRAYER_NAMES):
        header_cols[j + 1].markdown(f"**{prayer[:3]}**", help=prayer)

    weekly_done = 0
    daily_totals = []
    prayer_totals = {p: 0 for p in PRAYER_NAMES}

    for i in range(7):
        day = monday + timedelta(days=i)
        day_str = day.isoformat()
        day_label = f"{DAY_NAMES[i]} {day.day}"
        row_done = 0

        cols = st.columns([2] + [1] * 5)
        cols[0].write(day_label)

        for j, prayer in enumerate(PRAYER_NAMES):
            is_done = (prayer, day_str) in done_set
            key = f"pray_{person_id}_{prayer}_{day_str}"

            if is_done:
                row_done += 1
                weekly_done += 1
                prayer_totals[prayer] += 1
                if cols[j + 1].button("✅", key=key):
                    mark_prayer_not_done(person_id, person_type, prayer, day_str)
                    st.rerun()
            else:
                if cols[j + 1].button("☐", key=key):
                    mark_prayer_done(person_id, person_type, prayer, day_str)
                    st.rerun()

        daily_totals.append(row_done)

    st.divider()

    total_possible = 35
    pct = weekly_done / total_possible * 100
    st.subheader("📊 Weekly Summary")
    st.progress(pct / 100, text=f"{weekly_done} / {total_possible} prayers completed ({pct:.0f}%)")

    st.markdown("**Per prayer:**")
    cols = st.columns(5)
    for j, prayer in enumerate(PRAYER_NAMES):
        cols[j].metric(prayer, f"{prayer_totals[prayer]} / 7")

    st.markdown("**Per day:**")
    cols = st.columns(7)
    for i in range(7):
        day = monday + timedelta(days=i)
        cols[i].metric(DAY_NAMES[i], f"{daily_totals[i]} / 5", help=day.strftime("%b %d"))
