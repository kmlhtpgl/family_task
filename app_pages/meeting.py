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
    st.header("👪 Family Meeting")
    st.caption("Notes, agenda and decisions from your family meetings.")

    notes = data.get("meeting_notes", [])

    if "editing_note_id" not in st.session_state:
        st.session_state.editing_note_id = None

    # ── Add new note ──
    st.write("### ➕ Add Meeting Note")
    with st.form("add_meeting_note_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            title = st.text_input("Title", placeholder="e.g. Weekly family meeting")
        with col2:
            author = st.text_input("Author (optional)", placeholder="e.g. Dad")
        content = st.text_area(
            "Notes",
            placeholder="What was discussed, decisions made, actions agreed...",
            height=150,
        )
        submitted = st.form_submit_button("Save Note", type="primary", use_container_width=True)

        if submitted:
            if not title.strip():
                st.error("Please enter a title.")
            else:
                add_meeting_note(
                    title=title.strip(),
                    content=content.strip() if content.strip() else None,
                    author=author.strip() if author.strip() else None,
                )
                st.success("✅ Meeting note added!")
                st.rerun()

    st.divider()

    # ── Notes list ──
    st.write(f"### 📝 Notes ({len(notes)})")

    if not notes:
        st.info("No meeting notes yet. Add your first one above.")
        return

    sorted_notes = sorted(notes, key=lambda n: str(n.get("created_at", "")), reverse=True)

    for note in sorted_notes:
        note_id = note["id"]
        created = format_note_date(note.get("created_at"))
        author_line = f" — {note['author']}" if note.get("author") else ""
        meta = (created + author_line) if created else (author_line or "Unknown date")

        is_editing = st.session_state.editing_note_id == note_id

        with st.container(border=True):
            if not is_editing:
                col_head, col_act = st.columns([4, 1])
                with col_head:
                    st.markdown(f"**📌 {note['title']}**")
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
                    st.markdown(note["content"])
            else:
                st.markdown(f"**Edit: {note['title']}**")
                with st.form(f"edit_note_form_{note_id}"):
                    new_title = st.text_input("Title", value=note["title"], key=f"nt_{note_id}")
                    new_content = st.text_area(
                        "Notes",
                        value=note.get("content") or "",
                        height=120,
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
                        })
                        st.session_state.editing_note_id = None
                        st.success("✅ Note updated!")
                        st.rerun()

                if cancel_clicked:
                    st.session_state.editing_note_id = None
                    st.rerun()