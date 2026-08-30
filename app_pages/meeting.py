import html
from datetime import datetime

import streamlit as st

from utils.db_helpers import add_meeting_note, update_meeting_note, delete_meeting_note, add_meeting_comment


def format_note_date(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return str(value)
    return dt.strftime("%d %b %Y, %H:%M")


def meeting_page(data):
    st.header("👪 Meeting")
    st.caption("Weekly family meeting agenda & checklist. Tick items off as they are done.")

    notes = data.get("meeting_notes", [])

    if "editing_note_id" not in st.session_state:
        st.session_state.editing_note_id = None

    # ── Add new item ──
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
                )
                st.success("✅ Item added!")
                st.rerun()

    st.divider()

    # ── Add from templates ──
    templates = data.get("meeting_templates", [])
    if templates:
        with st.expander("➕ Add from common templates", expanded=False):
            t_options = {t["title"]: t for t in sorted(templates, key=lambda x: x["title"].lower())}
            selected_titles = st.multiselect("Choose templates to add to the meeting list", list(t_options.keys()))
            if st.button("Add Selected to Meeting", type="primary", disabled=not selected_titles):
                if not selected_titles:
                    st.error("Select at least one template.")
                else:
                    for title in selected_titles:
                        t = t_options[title]
                        add_meeting_note(
                            title=t["title"],
                            content=(t.get("content") or "").strip() or None,
                            author=(t.get("author") or "").strip() or None,
                        )
                    st.success(f"✅ {len(selected_titles)} item(s) added!")
                    st.rerun()

    # ── Checklist ──
    if not notes:
        st.info("No meeting items yet. Add your first one above.")
        return

    done_count = len([n for n in notes if n.get("done")])
    st.write(f"### ✅ Meeting List ({done_count}/{len(notes)} done)")

    sorted_notes = sorted(notes, key=lambda n: str(n.get("created_at", "")), reverse=True)

    for note in sorted_notes:
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

                # ── Comments ──
                note_comments = [
                    c for c in data.get("meeting_comments", [])
                    if str(c.get("meeting_note_id")) == str(note_id)
                ]
                note_comments.sort(key=lambda c: str(c.get("created_at", "")), reverse=True)
                with st.expander(f"💬 Comments ({len(note_comments)})", expanded=False):
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
                            c_created = format_note_date(c.get("created_at"))
                            c_author_line = f" — {c['author']}" if c.get("author") else ""
                            c_meta = (c_created + c_author_line) if c_created else (c_author_line or "Unknown date")
                            c_body_html = html.escape(c.get("body", "")).replace("\n", "<br>")
                            st.markdown(
                                f"<div style='border-left:3px solid var(--border);padding-left:10px;margin:6px 0;'>"
                                f"<span style='opacity:0.6;font-size:0.85em;'>💬 {c_meta}</span><br>{c_body_html}</div>",
                                unsafe_allow_html=True,
                            )
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