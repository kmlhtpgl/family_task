import html
from datetime import datetime

import streamlit as st

from utils.db_helpers import add_meeting_note, update_meeting_note, delete_meeting_note


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