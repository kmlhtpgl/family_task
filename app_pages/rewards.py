from datetime import date, datetime

import streamlit as st

from utils.task_helpers import get_monthly_points_for_kid, get_monthly_points_for_parent
from utils.db_helpers import add_reward_session, update_reward_session


POINTS_PER_GBP = 300


def rewards_page(data):
    st.header("💰 Monthly Rewards")
    st.caption(f"Every {POINTS_PER_GBP} points = £1 GBP")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    today = date.today()
    year = today.year
    current_month = today.month

    col1, col2 = st.columns([1, 4])
    with col1:
        month_offset = st.number_input(
            "Month offset",
            min_value=-24,
            max_value=0,
            value=0,
            step=1,
            key="reward_month_offset",
            label_visibility="collapsed"
        )
    with col2:
        target_month = current_month + month_offset
        target_year = year
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1

        month_name = datetime(target_year, target_month, 1).strftime("%B %Y")
        st.markdown(f"<h3 style='text-align:center;'>{month_name}</h3>", unsafe_allow_html=True)

    st.divider()

    for kid in data["kids"]:
        show_kid_reward(data, kid, target_year, target_month)

    for parent in data.get("parents", []):
        show_parent_reward(data, parent, target_year, target_month)


def show_kid_reward(data, kid, year, month):
    pts = get_monthly_points_for_kid(data, kid["id"], year, month)
    gbp = pts / POINTS_PER_GBP

    existing = find_existing_session(data, kid["id"], year, month, is_kid=True)

    with st.container():
        st.markdown(
            f'<div class="task-item">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<h4 style="margin:0;">🧒 {kid["name"]}</h4>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<span style="font-size:1.5em;font-weight:700;color:#FF8A80;">{pts} pts</span><br>'
            f'<span style="font-size:1.2em;font-weight:600;">= £{gbp:.2f}</span>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if pts > 0:
            if existing:
                if existing.get("paid"):
                    st.success("✅ Paid")
                else:
                    if st.button(f"💰 Mark as paid for {kid['name']}", key=f"pay_kid_{kid['id']}_{year}_{month}"):
                        update_reward_session(existing["id"], {"paid": True, "paid_at": date.today().isoformat()})
                        st.rerun()
            else:
                if st.button(f"💾 Save reward for {kid['name']}", key=f"save_kid_{kid['id']}_{year}_{month}"):
                    add_reward_session({
                        "kid_id": kid["id"],
                        "parent_id": None,
                        "month": f"{year:04d}-{month:02d}",
                        "total_points": int(pts),
                        "reward_amount": round(gbp, 2),
                        "paid": False
                    })
                    st.rerun()


def show_parent_reward(data, parent, year, month):
    pts = get_monthly_points_for_parent(data, parent["id"], year, month)
    gbp = pts / POINTS_PER_GBP

    existing = find_existing_session(data, parent["id"], year, month, is_kid=False)

    with st.container():
        st.markdown(
            f'<div class="task-item">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<h4 style="margin:0;">👨‍👩‍👧 {parent["name"]}</h4>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<span style="font-size:1.5em;font-weight:700;color:#FF8A80;">{pts} pts</span><br>'
            f'<span style="font-size:1.2em;font-weight:600;">= £{gbp:.2f}</span>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if pts > 0:
            if existing:
                if existing.get("paid"):
                    st.success("✅ Paid")
                else:
                    if st.button(f"💰 Mark as paid for {parent['name']}", key=f"pay_parent_{parent['id']}_{year}_{month}"):
                        update_reward_session(existing["id"], {"paid": True, "paid_at": date.today().isoformat()})
                        st.rerun()
            else:
                if st.button(f"💾 Save reward for {parent['name']}", key=f"save_parent_{parent['id']}_{year}_{month}"):
                    add_reward_session({
                        "kid_id": None,
                        "parent_id": parent["id"],
                        "month": f"{year:04d}-{month:02d}",
                        "total_points": int(pts),
                        "reward_amount": round(gbp, 2),
                        "paid": False
                    })
                    st.rerun()


def find_existing_session(data, person_id, year, month, is_kid=True):
    month_str = f"{year:04d}-{month:02d}"
    field = "kid_id" if is_kid else "parent_id"
    for session in data.get("reward_sessions", []):
        if session.get(field) == person_id and session.get("month") == month_str:
            return session
    return None
