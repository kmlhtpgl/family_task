from datetime import date, datetime
from html import escape

import streamlit as st
from utils.page_chrome import render_focus_panel, render_page_header, render_stat_strip

from utils.task_helpers import get_monthly_points_for_kid, get_monthly_points_for_parent, get_monthly_adjustment_points
from utils.db_helpers import add_reward_session, update_reward_session


POINTS_PER_GBP = 300


def rewards_page(data):
    render_page_header("Rewards", "Turn steady effort into a simple, visible monthly goal.")
    st.caption(f"Every {POINTS_PER_GBP} points = £1 GBP")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first in Admin.")
        return

    today = date.today()
    month_offset = st.session_state.get("reward_month_offset", 0)
    nav_left, nav_month, nav_right = st.columns([1, 5, 1])
    with nav_left:
        if st.button("Previous", key="reward_previous_month", disabled=month_offset <= -24):
            st.session_state.reward_month_offset = month_offset - 1
            st.rerun()
    with nav_month:
        target_month = today.month + month_offset
        target_year = today.year
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        month_name = datetime(target_year, target_month, 1).strftime("%B %Y")
        st.markdown(
            f'<div class="reward-month-marker"><span>EXCHANGE PERIOD</span><strong>{month_name}</strong>'
            f'<small>{"Current month" if month_offset == 0 else "Historical month"}</small></div>',
            unsafe_allow_html=True,
        )
    with nav_right:
        if st.button("Next", key="reward_next_month", disabled=month_offset >= 0):
            st.session_state.reward_month_offset = month_offset + 1
            st.rerun()

    total_points = sum(get_monthly_points_for_kid(data, kid["id"], target_year, target_month) + get_monthly_adjustment_points(data, kid["id"], "kid", target_year, target_month) for kid in data["kids"])
    total_points += sum(get_monthly_points_for_parent(data, parent["id"], target_year, target_month) + get_monthly_adjustment_points(data, parent["id"], "parent", target_year, target_month) for parent in data.get("parents", []))
    saved = sum(1 for session in data.get("reward_sessions", []) if session.get("month") == f"{target_year:04d}-{target_month:02d}")
    paid = sum(1 for session in data.get("reward_sessions", []) if session.get("month") == f"{target_year:04d}-{target_month:02d}" and session.get("paid"))
    render_stat_strip([
        ("Earned", str(total_points), "points this month"),
        ("Saved", str(saved), "reward records"),
        ("Paid", str(paid), "completed payouts"),
    ])
    render_focus_panel("Exchange focus", month_name, "Every 300 points unlocks one pound of reward value", f"£{total_points / POINTS_PER_GBP:.2f}", "household value")

    people = []
    for kid in data["kids"]:
        points = get_monthly_points_for_kid(data, kid["id"], target_year, target_month) + get_monthly_adjustment_points(data, kid["id"], "kid", target_year, target_month)
        people.append((kid["name"], "Kid", points))
    for parent in data.get("parents", []):
        points = get_monthly_points_for_parent(data, parent["id"], target_year, target_month) + get_monthly_adjustment_points(data, parent["id"], "parent", target_year, target_month)
        people.append((parent["name"], "Parent", points))
    people.sort(key=lambda item: item[2], reverse=True)
    leaderboard = "".join(
        f'<div class="reward-leader-row"><span class="reward-leader-rank">{index:02d}</span>'
        f'<span class="reward-leader-name">{escape(name)}<small>{kind}</small></span>'
        f'<span class="reward-leader-points">{points}<small>pts</small></span></div>'
        for index, (name, kind, points) in enumerate(people, start=1)
    )
    st.markdown(
        '<div class="reward-leaderboard-heading"><span>THE LADDER</span><strong>Household momentum</strong>'
        '<small>Who is building the most reward value this month?</small></div>'
        f'<div class="reward-leaderboard">{leaderboard}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="reward-exchange-heading"><span>THE EXCHANGE</span><strong>Reward accounts</strong><small>Save an account when the month is ready, then mark it paid.</small></div>', unsafe_allow_html=True)

    for kid in data["kids"]:
        show_kid_reward(data, kid, target_year, target_month)

    for parent in data.get("parents", []):
        show_parent_reward(data, parent, target_year, target_month)


def show_kid_reward(data, kid, year, month):
    task_pts = get_monthly_points_for_kid(data, kid["id"], year, month)
    adj_pts = get_monthly_adjustment_points(data, kid["id"], "kid", year, month)
    pts = task_pts + adj_pts
    gbp = pts / POINTS_PER_GBP

    existing = find_existing_session(data, kid["id"], year, month, is_kid=True)

    with st.container():
        render_reward_card(kid["name"], "Kid", pts, gbp, existing)

        if pts > 0:
            if existing:
                if existing.get("paid"):
                    st.success("✅ Paid")
                else:
                    if st.button(f"Mark {kid['name']} paid", key=f"pay_kid_{kid['id']}_{year}_{month}"):
                        update_reward_session(existing["id"], {"paid": True, "paid_at": date.today().isoformat()})
                        st.rerun()
            else:
                if st.button(f"Save {kid['name']} reward", key=f"save_kid_{kid['id']}_{year}_{month}"):
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
    task_pts = get_monthly_points_for_parent(data, parent["id"], year, month)
    adj_pts = get_monthly_adjustment_points(data, parent["id"], "parent", year, month)
    pts = task_pts + adj_pts
    gbp = pts / POINTS_PER_GBP

    existing = find_existing_session(data, parent["id"], year, month, is_kid=False)

    with st.container():
        render_reward_card(parent["name"], "Parent", pts, gbp, existing)

        if pts > 0:
            if existing:
                if existing.get("paid"):
                    st.success("✅ Paid")
                else:
                    if st.button(f"Mark {parent['name']} paid", key=f"pay_parent_{parent['id']}_{year}_{month}"):
                        update_reward_session(existing["id"], {"paid": True, "paid_at": date.today().isoformat()})
                        st.rerun()
            else:
                if st.button(f"Save {parent['name']} reward", key=f"save_parent_{parent['id']}_{year}_{month}"):
                    add_reward_session({
                        "kid_id": None,
                        "parent_id": parent["id"],
                        "month": f"{year:04d}-{month:02d}",
                        "total_points": int(pts),
                        "reward_amount": round(gbp, 2),
                        "paid": False
                    })
                    st.rerun()


def render_reward_card(name, kind, points, gbp, existing):
    progress = (points % POINTS_PER_GBP) / POINTS_PER_GBP if points else 0
    status = "Paid" if existing and existing.get("paid") else ("Saved" if existing else "Not saved")
    st.markdown(
        f'<div class="reward-exchange-card"><div class="reward-exchange-card__identity">'
        f'<span class="reward-exchange-card__kind">{escape(kind)}</span>'
        f'<strong>{escape(name)}</strong><small>{status}</small></div>'
        f'<div class="reward-exchange-card__value"><strong>{points}</strong><small>points</small>'
        f'<span>£{gbp:.2f}</span></div>'
        f'<div class="reward-exchange-card__progress"><div style="width:{round(progress * 100)}%"></div></div>'
        f'<div class="reward-exchange-card__hint">{round(progress * 100)}% toward the next £1 milestone</div></div>',
        unsafe_allow_html=True,
    )


def find_existing_session(data, person_id, year, month, is_kid=True):
    month_str = f"{year:04d}-{month:02d}"
    field = "kid_id" if is_kid else "parent_id"
    for session in data.get("reward_sessions", []):
        if session.get(field) == person_id and session.get("month") == month_str:
            return session
    return None
