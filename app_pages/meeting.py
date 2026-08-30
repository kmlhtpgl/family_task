import html
from datetime import date, datetime, timedelta

import streamlit as st

from utils.db_helpers import (
    add_meeting_note,
    update_meeting_note,
    delete_meeting_note,
    add_meeting_comment,
    delete_meeting_comment,
    get_or_create_meeting_session,
    set_meeting_session_closed,
    carry_over_unfinished,
)


def format_note_date(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return str(value)
    return dt.strftime("%d %b %Y, %H:%M")


def fmt_sunday(value):
    if not value:
        return "Unknown"
    try:
        d = datetime.fromisoformat(str(value)).date()
    except (ValueError, TypeError):
        return str(value)
    return d.strftime("%A %d %b %Y")


def upcoming_sunday(today=None):
    today = today or date.today()
    if today.weekday() == 6:  # Sunday
        return today
    return today + timedelta(days=(6 - today.weekday()))


def most_recent_past_session(sessions, week_date):
    """Return the most recent closed/past session strictly before week_date, or None."""
    target = datetime.fromisoformat(str(week_date)).date() if week_date else date.today()
    past = [
        s for s in sessions
        if datetime.fromisoformat(str(s.get("week_date"))).date() < target
    ]
    past.sort(key=lambda s: str(s.get("week_date", "")), reverse=True)
    return past[0] if past else None


def meeting_page(data):
    st.header("👪 Meeting")
    st.caption("Weekly family meeting, held every Sunday. Set up the week, tick items off, keep a record.")

    sessions = list(data.get("meeting_sessions", []))
    notes = list(data.get("meeting_notes", []))
    templates = list(data.get("meeting_templates", []))

    upcoming = upcoming_sunday()
    upcoming_str = upcoming.isoformat()

    session_by_date = {}
    for s in sessions:
        try:
            session_by_date[str(datetime.fromisoformat(str(s.get("week_date"))).date())] = s
        except (ValueError, TypeError):
            continue

    # Build the selectable list (sessions sorted newest first, plus placeholder for upcoming)
    ordered = sorted(
        sessions,
        key=lambda s: str(s.get("week_date", "")),
        reverse=True,
    )

    def session_label(s):
        try:
            wd = datetime.fromisoformat(str(s.get("week_date"))).date()
        except (ValueError, TypeError):
            wd = None
        if s.get("closed"):
            tag = "🔒 Archived"
        elif wd == upcoming:
            tag = "🟢 Active"
        else:
            tag = ""
        base = fmt_sunday(s.get("week_date")) if wd else "Unknown"
        return (base + ("  · " + tag if tag else ""))

    selector_values = []  # list of (key, display)
    for s in ordered:
        selector_values.append(("id", s["id"], session_label(s)))
    has_upcoming_session = upcoming_str in session_by_date
    if not has_upcoming_session:
        selector_values.insert(0, ("upcoming", None, f"📅 Coming up · {fmt_sunday(upcoming_str)} (not set up yet)"))

    if selector_values:
        labels = [v[2] for v in selector_values]
        default_idx = 0
        st.caption("Choose a meeting week:")
        choice = st.selectbox(
            "Meeting week",
            labels,
            index=default_idx,
            key="meeting_week_select",
            label_visibility="collapsed",
        )
        chosen = selector_values[labels.index(choice)]
        chosen_kind, chosen_id, _ = chosen
    else:
        chosen_kind, chosen_id = "upcoming", None

    if chosen_kind == "upcoming":
        session = None
        week_date = upcoming
    else:
        session = next((s for s in sessions if s["id"] == chosen_id), None)
        try:
            week_date = datetime.fromisoformat(str(session.get("week_date"))).date() if session else upcoming
        except (ValueError, TypeError):
            week_date = upcoming

    is_current_week = (week_date == upcoming)
    is_archived = bool(session and session.get("closed"))

    # ── Set up this week ──
    if chosen_kind == "upcoming" or (session is None):
        st.divider()
        st.subheader(f"📅 Set up this week's meeting ({fmt_sunday(week_date)})")
        with st.form("setup_meeting_form"):
            carry = st.checkbox("Carry over unfinished items from last meeting", value=True)
            t_options = {t["title"]: t for t in sorted(templates, key=lambda x: x["title"].lower())} if templates else {}
            selected_titles = st.multiselect(
                "Add from common templates (optional)",
                list(t_options.keys()),
            ) if templates else []
            setup_submit = st.form_submit_button("Set up meeting", type="primary", use_container_width=True)

        if setup_submit:
            new_session = get_or_create_meeting_session(week_date, title="Weekly Family Meeting")
            added = 0
            if carry:
                prev = most_recent_past_session(sessions, week_date)
                if prev:
                    carried = carry_over_unfinished(prev["id"], new_session["id"])
                    added += len(carried)
            for title in selected_titles:
                t = t_options[title]
                add_meeting_note(
                    title=t["title"],
                    content=(t.get("content") or "").strip() or None,
                    author=(t.get("author") or "").strip() or None,
                    session_id=new_session["id"],
                    week_date=str(week_date),
                )
                added += 1
            st.success(f"✅ Meeting set up! {added} item(s) added.")
            st.rerun()
        return

    # ── Current / selected week checklist ──
    session_notes = [
        n for n in notes
        if str(n.get("session_id")) == str(session["id"])
    ]
    session_notes.sort(key=lambda n: str(n.get("created_at", "")), reverse=True)

    done_count = len([n for n in session_notes if n.get("done")])
    header = fmt_sunday(session.get("week_date"))
    if is_archived:
        header += "  ·  🔒 Archived"
    st.divider()
    st.write(f"### ✅ {header} ({done_count}/{len(session_notes)} done)")
    if session_notes:
        pct = int((done_count / len(session_notes)) * 100)
        st.progress(pct / 100, text=f"{pct}% complete")

    if not is_archived and session:
        if st.button("🔒 Close / archive this meeting", key="close_meeting"):
            set_meeting_session_closed(session["id"], True)
            st.rerun()

    if is_archived:
        # Read-only view with reopen button
        if st.button("↩️ Reopen this meeting", key="reopen_meeting"):
            set_meeting_session_closed(session["id"], False)
            st.rerun()
        with st.container(border=True):
            if not session_notes:
                st.info("No items recorded in this meeting.")
            for note in session_notes:
                note_id = note["id"]
                is_done = bool(note.get("done"))
                created = format_note_date(note.get("created_at"))
                author_line = f" — {note['author']}" if note.get("author") else ""
                meta = (created + author_line) if created else (author_line or "Unknown date")
                title_html = html.escape(note["title"])
                if is_done:
                    st.markdown(f"<span style='text-decoration:line-through;opacity:0.6;'><b>📌 {title_html}</b></span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**📌 {title_html}**")
                st.caption(f"🕐 {meta}")
                if note.get("content"):
                    content_html = html.escape(note["content"]).replace("\n", "<br>")
                    style = "opacity:0.6;" if is_done else ""
                    st.markdown(f"<div style='{style}'>{content_html}</div>", unsafe_allow_html=True)
                render_comments(note, data, allow_edit=False)
            st.markdown("")
        return

    # ── Active week: add item + templates + checklist ──
    st.write("### ➕ Add Item")
    with st.form("add_meeting_note_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            title = st.text_input("Title", placeholder="e.g. Sort out summer plans")
        with col2:
            author = st.text_input("Author (optional)", placeholder="e.g. Mum")
        content = st.text_area(
            "Details (optional)",
            placeholder="Anything to remember about this item...",
            height=100,
        )
        submitted = st.form_submit_button("Save Item", type="primary", use_container_width=True)

        if submitted:
            if not title.strip():
                st.error("Please enter a title.")
            else:
                add_meeting_note(
                    title=title.strip(),
                    content=content.strip() if content.strip() else None,
                    author=author.strip() if author.strip() else None,
                    session_id=session["id"],
                    week_date=str(week_date),
                )
                st.success("✅ Item added!")
                st.rerun()

    st.divider()

    if templates:
        with st.expander("➕ Add from common templates", expanded=False):
            t_options = {t["title"]: t for t in sorted(templates, key=lambda x: x["title"].lower())}
            selected_titles = st.multiselect("Choose templates to add to the meeting list", list(t_options.keys()))
            if st.button("Add Selected to Meeting", type="primary", disabled=not selected_titles):
                if not selected_titles:
                    st.error("Select at least one template.")
                else:
                    for t_title in selected_titles:
                        t = t_options[t_title]
                        add_meeting_note(
                            title=t["title"],
                            content=(t.get("content") or "").strip() or None,
                            author=(t.get("author") or "").strip() or None,
                            session_id=session["id"],
                            week_date=str(week_date),
                        )
                    st.success(f"✅ {len(selected_titles)} item(s) added!")
                    st.rerun()

    st.divider()

    if not session_notes:
        st.info("No meeting items yet for this week. Add your first one above, or use 'Set up this week'.")
        return

    if "editing_note_id" not in st.session_state:
        st.session_state.editing_note_id = None

    for note in session_notes:
        note_id = note["id"]
        is_done = bool(note.get("done"))
        created = format_note_date(note.get("created_at"))
        author_line = f" — {note['author']}" if note.get("author") else ""
        meta = (created + author_line) if created else (author_line or "Unknown date")

        is_editing = st.session_state.editing_note_id == note_id

        with st.container(border=True):
            if not is_editing:
                col_check, col_head, col_act = st.columns([0.6, 3.4, 1])
                with col_check:
                    done_btn = "✅" if is_done else "⬜"
                    if st.button(done_btn, key=f"done_note_{note_id}", help="Mark done / undo"):
                        update_meeting_note(note_id, {"done": not is_done})
                        st.rerun()
                with col_head:
                    title_html = html.escape(note["title"])
                    if is_done:
                        st.markdown(
                            f"<span style='text-decoration:line-through;opacity:0.6;'><b>📌 {title_html}</b></span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**📌 {title_html}**")
                    st.caption(f"🕐 {meta}")
                with col_act:
                    act_cols = st.columns(2)
                    with act_cols[0]:
                        if st.button("✏️", key=f"edit_note_{note_id}", help="Edit"):
                            st.session_state.editing_note_id = note_id
                            st.rerun()
                    with act_cols[1]:
                        if st.button("🗑️", key=f"del_note_{note_id}", help="Delete"):
                            delete_meeting_note(note_id)
                            st.rerun()
                if note.get("content"):
                    content_html = html.escape(note["content"]).replace("\n", "<br>")
                    style = "opacity:0.6;" if is_done else ""
                    st.markdown(f"<div style='{style}'>{content_html}</div>", unsafe_allow_html=True)
                render_comments(note, data)
            else:
                st.markdown(f"**Edit: {note['title']}**")
                with st.form(f"edit_note_form_{note_id}"):
                    new_title = st.text_input("Title", value=note["title"], key=f"nt_{note_id}")
                    new_content = st.text_area(
                        "Details",
                        value=note.get("content") or "",
                        height=100,
                        key=f"nc_{note_id}",
                    )
                    new_author = st.text_input(
                        "Author (optional)",
                        value=note.get("author") or "",
                        key=f"na_{note_id}",
                    )
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        save_clicked = st.form_submit_button("💾 Save", use_container_width=True)
                    with ecol2:
                        cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

                if save_clicked:
                    if not new_title.strip():
                        st.error("Please enter a title.")
                    else:
                        update_meeting_note(note_id, {
                            "title": new_title.strip(),
                            "content": new_content.strip() if new_content.strip() else None,
                            "author": new_author.strip() if new_author.strip() else None,
                            "done": bool(note.get("done")),
                        })
                        st.session_state.editing_note_id = None
                        st.success("✅ Item updated!")
                        st.rerun()

                if cancel_clicked:
                    st.session_state.editing_note_id = None
                    st.rerun()


def render_comments(note, data, allow_edit=True):
    """Render a note's comments. allow_edit=False shows a read-only archived view."""
    note_id = note["id"]
    note_comments = [
        c for c in data.get("meeting_comments", [])
        if str(c.get("meeting_note_id")) == str(note_id)
    ]
    note_comments.sort(key=lambda c: str(c.get("created_at", "")), reverse=True)
    with st.expander(f"💬 Comments ({len(note_comments)})", expanded=False):
        if allow_edit:
            with st.form(f"add_comment_form_{note_id}"):
                c_col1, c_col2 = st.columns([3, 1])
                with c_col1:
                    c_body = st.text_input("Comment", key=f"cb_{note_id}", placeholder="Write a comment...")
                with c_col2:
                    c_author = st.text_input("Name (optional)", key=f"ca_{note_id}", placeholder="e.g. Dad")
                c_submit = st.form_submit_button("Add comment", use_container_width=True)
            if c_submit:
                if not c_body.strip():
                    st.error("Please write a comment.")
                else:
                    add_meeting_comment(
                        meeting_note_id=note_id,
                        body=c_body.strip(),
                        author=c_author.strip() if c_author.strip() else None,
                    )
                    st.success("💬 Comment added!")
                    st.rerun()
        if note_comments:
            for c in note_comments:
                if allow_edit:
                    c_row = st.columns([0.95, 0.05])
                else:
                    c_row = [st.container()]
                with c_row[0]:
                    c_created = format_note_date(c.get("created_at"))
                    c_author_line = f" — {c['author']}" if c.get("author") else ""
                    c_meta = (c_created + c_author_line) if c_created else (c_author_line or "Unknown date")
                    c_body_html = html.escape(c.get("body", "")).replace("\n", "<br>")
                    st.markdown(
                        f"<div style='border-left:3px solid var(--border);padding-left:10px;margin:6px 0;'>"
                        f"<span style='opacity:0.6;font-size:0.85em;'>💬 {c_meta}</span><br>{c_body_html}</div>",
                        unsafe_allow_html=True,
                    )
                if allow_edit and len(c_row) > 1:
                    with c_row[1]:
                        if st.button("🗑️", key=f"del_comment_{c['id']}", help="Delete comment"):
                            delete_meeting_comment(c["id"])
                            st.rerun()
