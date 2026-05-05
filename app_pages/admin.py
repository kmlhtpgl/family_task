import streamlit as st
from datetime import date, datetime, timedelta

from utils.task_helpers import TASK_STATUSES
from utils.db_helpers import (
    add_kid,
    update_kid,
    delete_kid,
    add_parent,
    update_parent,
    delete_parent,
    add_tasks,
    add_books,
    add_task_template,
    update_task_template,
    delete_task_template,
    replace_task_templates,
    add_book_template,
    replace_book_template,
    delete_book_template,
    replace_book_templates
)
from utils.storage_helpers import upload_profile_photo, delete_profile_photo


def admin_page(data):
    st.header("⚙️ Admin Panel")
    st.caption("Manage your family: parents, children, tasks, books, and more.")

    admin_tabs = [
        ("parents", "👨‍👩‍👧‍👦 Parents"),
        ("children", "👧 Children"),
        ("task_list", "📋 Task List"),
        ("assign_task", "🎯 Assign Task"),
        ("book_list", "📚 Book List"),
        ("assign_book", "📖 Assign Book"),
        ("settings", "⚙️ Settings")
    ]

    if "admin_tab" not in st.session_state:
        st.session_state.admin_tab = "parents"

    tab_cols = st.columns(len(admin_tabs), gap="small")

    for col, (tab_key, tab_label) in zip(tab_cols, admin_tabs):
        is_active = tab_key == st.session_state.admin_tab
        btn_type = "primary" if is_active else "secondary"

        if col.button(tab_label, key=f"admin_nav_{tab_key}", use_container_width=True, type=btn_type):
            st.session_state.admin_tab = tab_key
            st.rerun()

    st.divider()

    active = st.session_state.admin_tab

    if active == "parents":
        parents_tab(data)
    elif active == "children":
        add_child_tab(data)
    elif active == "task_list":
        task_list_tab(data)
    elif active == "assign_task":
        assign_task_tab(data)
    elif active == "book_list":
        book_list_tab(data)
    elif active == "assign_book":
        assign_book_tab(data)
    elif active == "settings":
        settings_tab()


# -----------------------
# Parents Management
# -----------------------

def parents_tab(data):
    st.subheader("👨‍👩‍👧‍👦 Parents Management")
    st.caption("Add and manage parent profiles for task and book assignments.")

    # Add Parent Form
    st.write("### Add New Parent")
    with st.form("add_parent_form"):
        col1, col2 = st.columns([1, 2])

        with col1:
            uploaded_photo = st.file_uploader(
                "Profile photo",
                type=["jpg", "jpeg", "png"],
                key="new_parent_photo"
            )

        with col2:
            name = st.text_input("Parent name")
            email = st.text_input("Email (optional)")
            phone = st.text_input("Phone (optional)")

        submitted = st.form_submit_button("Add Parent")

        if submitted:
            if not name.strip():
                st.error("Please enter the parent's name.")
                return

            photo_url = None

            if uploaded_photo:
                try:
                    photo_url = upload_profile_photo(
                        uploaded_photo.getvalue(),
                        uploaded_photo.name
                    )
                    st.success("Photo uploaded!")
                except Exception as e:
                    st.error(f"Failed to upload photo: {e}")

            add_parent(
                name=name.strip(),
                email=email.strip() if email else None,
                phone=phone.strip() if phone else None,
                photo_url=photo_url
            )

            st.success("Parent added successfully! ✅")
            st.rerun()

    st.divider()

    # Display Parents
    st.write("### Parents List")
    parents = data.get("parents", [])

    if not parents:
        st.caption("No parents added yet.")
        return

    for parent in parents:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

            with col1:
                if parent.get("photo_url"):
                    st.markdown(
                        f'<img src="{parent["photo_url"]}" class="avatar-circle" width="80" height="80" />',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="avatar-circle" style="width:80px;height:80px;background:linear-gradient(135deg,#FF8A80,#4ECDC4);display:flex;align-items:center;justify-content:center;font-size:30px;color:white;">👤</div>',
                        unsafe_allow_html=True
                    )

            with col2:
                st.write(f"**{parent['name']}**")
                if parent.get("email"):
                    st.caption(f"📧 {parent['email']}")
                if parent.get("phone"):
                    st.caption(f"📞 {parent['phone']}")

            with col3:
                if st.button("✏️ Edit", key=f"edit_parent_{parent['id']}"):
                    st.session_state.editing_parent_id = parent['id']
                    st.rerun()

            with col4:
                if st.button("🗑️ Delete", key=f"delete_parent_{parent['id']}"):
                    if parent.get("photo_url"):
                        delete_profile_photo(parent["photo_url"])

                    delete_parent(parent['id'])
                    st.warning(f"Parent '{parent['name']}' removed.")
                    st.rerun()

        # Edit form if selected
        if st.session_state.get("editing_parent_id") == parent["id"]:
            st.write("#### Edit Parent")
            with st.form(f"edit_parent_form_{parent['id']}"):
                col1, col2 = st.columns([1, 2])

                with col1:
                    uploaded_photo = st.file_uploader(
                        "New photo (optional)",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_parent_photo_{parent['id']}"
                    )

                    if parent.get("photo_url"):
                        st.markdown(
                            f'<img src="{parent["photo_url"]}" class="avatar-circle" width="80" height="80" />',
                            unsafe_allow_html=True
                        )

                        if st.button("🗑️ Remove photo", key=f"remove_parent_photo_{parent['id']}"):
                            delete_profile_photo(parent["photo_url"])
                            update_parent(parent['id'], {"photo_url": None})
                            st.success("Photo removed.")
                            st.session_state.editing_parent_id = None
                            st.rerun()

                with col2:
                    new_name = st.text_input("Parent name", value=parent['name'])
                    new_email = st.text_input("Email", value=parent.get("email", ""))
                    new_phone = st.text_input("Phone", value=parent.get("phone", ""))

                if st.form_submit_button("Save Changes"):
                    updates = {
                        "name": new_name.strip(),
                        "email": new_email.strip() if new_email else None,
                        "phone": new_phone.strip() if new_phone else None
                    }

                    if uploaded_photo:
                        try:
                            if parent.get("photo_url"):
                                delete_profile_photo(parent["photo_url"])

                            updates["photo_url"] = upload_profile_photo(
                                uploaded_photo.getvalue(),
                                uploaded_photo.name
                            )
                        except Exception as e:
                            st.error(f"Failed to upload photo: {e}")

                    update_parent(parent['id'], updates)
                    st.success("Parent updated! ✅")
                    st.session_state.editing_parent_id = None
                    st.rerun()


# -----------------------
# Add Child
# -----------------------

def add_child_tab(data):
    st.subheader("👧 Children Management")

    # Add Child Form
    st.write("### Add New Child")
    with st.form("add_child_form"):
        col1, col2 = st.columns([1, 2])

        with col1:
            uploaded_photo = st.file_uploader(
                "Profile photo",
                type=["jpg", "jpeg", "png"],
                key="new_kid_photo"
            )

        with col2:
            name = st.text_input("Child name")
            age = st.number_input("Age", min_value=1, max_value=18, value=6)

        submitted = st.form_submit_button("Add Child")

        if submitted:
            if not name.strip():
                st.error("Please enter the child's name.")
                return

            photo_url = None

            if uploaded_photo:
                try:
                    photo_url = upload_profile_photo(
                        uploaded_photo.getvalue(),
                        uploaded_photo.name
                    )
                    st.success("Photo uploaded!")
                except Exception as e:
                    st.error(f"Failed to upload photo: {e}")

            add_kid(
                name=name.strip(),
                age=int(age),
                photo_path=photo_url
            )

            st.success("Child added successfully.")
            st.rerun()

    st.divider()

    # Display Children
    st.write("### Children List")
    kids = data.get("kids", [])

    if not kids:
        st.caption("No children added yet.")
        return

    for kid in kids:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

            with col1:
                if kid.get("photo_path"):
                    st.markdown(
                        f'<img src="{kid["photo_path"]}" class="avatar-circle" width="80" height="80" />',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="avatar-circle" style="width:80px;height:80px;background:linear-gradient(135deg,#FF8A80,#4ECDC4);display:flex;align-items:center;justify-content:center;font-size:30px;color:white;">👤</div>',
                        unsafe_allow_html=True
                    )

            with col2:
                st.write(f"**{kid['name']}**")
                st.caption(f"Age: {kid.get('age', 'Not set')}")

            with col3:
                if st.button("✏️ Edit", key=f"edit_kid_{kid['id']}"):
                    st.session_state.editing_kid_id = kid['id']
                    st.rerun()

            with col4:
                if st.button("🗑️ Delete", key=f"delete_kid_{kid['id']}"):
                    if kid.get("photo_path"):
                        delete_profile_photo(kid["photo_path"])

                    delete_kid(kid['id'])
                    st.warning(f"Child '{kid['name']}' removed.")
                    st.rerun()

        # Edit form if selected
        if st.session_state.get("editing_kid_id") == kid["id"]:
            st.write("#### Edit Child")
            with st.form(f"edit_kid_form_{kid['id']}"):
                col1, col2 = st.columns([1, 2])

                with col1:
                    uploaded_photo = st.file_uploader(
                        "New photo (optional)",
                        type=["jpg", "jpeg", "png"],
                        key=f"edit_kid_photo_{kid['id']}"
                    )

                    if kid.get("photo_path"):
                        st.markdown(
                            f'<img src="{kid["photo_path"]}" class="avatar-circle" width="80" height="80" />',
                            unsafe_allow_html=True
                        )

                        if st.button("🗑️ Remove photo", key=f"remove_kid_photo_{kid['id']}"):
                            delete_profile_photo(kid["photo_path"])
                            update_kid(kid['id'], {"photo_path": None})
                            st.success("Photo removed.")
                            st.session_state.editing_kid_id = None
                            st.rerun()

                with col2:
                    new_name = st.text_input("Child name", value=kid['name'])
                    new_age = st.number_input("Age", min_value=1, max_value=18, value=kid.get('age', 6))

                if st.form_submit_button("Save Changes"):
                    updates = {
                        "name": new_name.strip(),
                        "age": int(new_age)
                    }

                    if uploaded_photo:
                        try:
                            if kid.get("photo_path"):
                                delete_profile_photo(kid["photo_path"])

                            updates["photo_path"] = upload_profile_photo(
                                uploaded_photo.getvalue(),
                                uploaded_photo.name
                            )
                        except Exception as e:
                            st.error(f"Failed to upload photo: {e}")

                    update_kid(kid['id'], updates)
                    st.success("Child updated! ✅")
                    st.session_state.editing_kid_id = None
                    st.rerun()


# -----------------------
# Task List
# -----------------------

def task_list_tab(data):
    st.subheader("📋 Task List")

    st.info("Add, edit or remove tasks from your task library.")

    templates = data["task_templates"]

    # Initialize editing state
    if "editing_task_id" not in st.session_state:
        st.session_state.editing_task_id = None

    st.write("### ➕ Add New Task")

    with st.form("add_task_template_form"):
        title = st.text_input("Task name")
        default_points = st.number_input(
            "Default points",
            min_value=1,
            max_value=100,
            value=10
        )

        submitted = st.form_submit_button("Add Task")

        if submitted:
            if not title.strip():
                st.error("Please enter a task name.")
                return

            add_task_template(
                title=title.strip(),
                default_points=int(default_points)
            )

            st.success("Task added to the task list.")
            st.rerun()

    st.divider()

    if not templates:
        st.caption("No tasks in the task list yet.")
        return

    st.write("### 📝 Your Tasks")

    for template in templates:
        with st.container(border=True):
            col_info, col_actions = st.columns([4, 1])

            with col_info:
                if st.session_state.editing_task_id != template['id']:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:15px;padding:8px 0;">'
                        f'<div style="width:50px;height:50px;background:linear-gradient(135deg,#FF8A80,#4ECDC4);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.5em;flex-shrink:0;">📋</div>'
                        f'<div>'
                        f'<div style="font-size:1.1em;font-weight:700;">{template["title"]}</div>'
                        f'<div style="color:#888;font-size:0.85em;">⭐ {template["default_points"]} points</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Edit form
                    new_title = st.text_input("Task name", value=template["title"], key=f"tt_{template['id']}")
                    new_points = st.number_input(
                        "Default points",
                        min_value=1,
                        max_value=100,
                        value=int(template.get("default_points", 10)),
                        key=f"tp_{template['id']}"
                    )

                    edit_cols = st.columns(2)
                    with edit_cols[0]:
                        if st.button("💾 Save", key=f"save_task_{template['id']}", use_container_width=True):
                            if not new_title.strip():
                                st.error("Task name is required.")
                            else:
                                update_task_template(template["id"], {
                                    "title": new_title.strip(),
                                    "default_points": int(new_points)
                                })
                                st.session_state.editing_task_id = None
                                st.success("Task updated!")
                                st.rerun()

                    with edit_cols[1]:
                        if st.button("Cancel", key=f"cancel_task_{template['id']}", use_container_width=True):
                            st.session_state.editing_task_id = None
                            st.rerun()

            with col_actions:
                if st.button("✏️", key=f"edit_btn_task_{template['id']}", help="Edit"):
                    st.session_state.editing_task_id = template['id']
                    st.rerun()

                if st.button("🗑️", key=f"del_btn_task_{template['id']}", help="Delete"):
                    delete_task_template(template["id"])
                    st.warning("Task removed.")
                    st.rerun()


def clean_task_templates(templates):
    cleaned = []

    for template in templates:
        title = str(template.get("title", "")).strip()

        if not title:
            continue

        default_points = int(template.get("default_points", 10))

        cleaned.append(
            {
                "title": title,
                "default_points": default_points
            }
        )

    return cleaned


# -----------------------
# Assign Task
# -----------------------

def assign_task_tab(data):
    st.subheader("🎯 Assign Task")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first.")
        return

    task_templates = data["task_templates"]

    if not task_templates:
        st.info("Add tasks to the Task List first.")
        return

    assignee_options = build_assignee_options(data)
    task_options = {
        template["title"]: template
        for template in task_templates
    }

    with st.form("assign_task_form"):
        selected_task_title = st.selectbox(
            "Choose task from list",
            list(task_options.keys())
        )

        assign_to = st.selectbox(
            "Assign to",
            list(assignee_options.keys()),
            key="assign_task_to"
        )

        repeat_type = st.radio(
            "Task date option",
            [
                "One date only",
                "Every day",
                "Specific days of the week"
            ]
        )

        selected_dates = []

        if repeat_type == "One date only":
            single_date = st.date_input(
                "Due date",
                value=date.today()
            )
            selected_dates = [single_date]

        elif repeat_type == "Every day":
            start_date = st.date_input(
                "Start date",
                value=date.today(),
                key="daily_start_date"
            )

            end_date = st.date_input(
                "End date",
                value=date.today() + timedelta(days=7),
                key="daily_end_date"
            )

            selected_dates = generate_daily_dates(start_date, end_date)

        elif repeat_type == "Specific days of the week":
            start_date = st.date_input(
                "Start date",
                value=date.today(),
                key="weekly_start_date"
            )

            end_date = st.date_input(
                "End date",
                value=date.today() + timedelta(days=30),
                key="weekly_end_date"
            )

            selected_weekdays = st.multiselect(
                "Choose days",
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday"
                ],
                default=["Monday", "Wednesday", "Friday"]
            )

            selected_dates = generate_weekday_dates(
                start_date,
                end_date,
                selected_weekdays
            )

        selected_template = task_options[selected_task_title]

        points = st.number_input(
            "Reward points",
            min_value=1,
            max_value=100,
            value=int(selected_template["default_points"])
        )

        status = st.selectbox(
            "Starting column",
            TASK_STATUSES
        )

        submitted = st.form_submit_button("Assign Task")

        if submitted:
            if not selected_dates:
                st.error("Please choose at least one valid date.")
                return

            selected_assignees = assignee_options[assign_to]

            new_tasks = []

            for due_date in selected_dates:
                for assignee in selected_assignees:
                    new_task = {
                        "title": selected_template["title"],
                        "kid_id": assignee.get("kid_id"),
                        "parent_id": assignee.get("parent_id"),
                        "due_date": due_date.isoformat(),
                        "points": int(points),
                        "status": status,
                        "repeat_type": repeat_type
                    }

                    if status == "Done":
                        year, week, _ = due_date.isocalendar()
                        new_task["completed_date"] = due_date.isoformat()
                        new_task["completed_week"] = f"{year}-W{week}"

                    new_tasks.append(new_task)

            add_tasks(new_tasks)

            st.success(f"{len(new_tasks)} task(s) created in Supabase.")
            st.rerun()


def build_assignee_options(data):
    options = {}

    kid_options = {kid["name"]: kid["id"] for kid in data["kids"]}
    parent_options = {p["name"]: p["id"] for p in data.get("parents", [])}

    all_kids = list(kid_options.keys())
    all_parents = list(parent_options.keys())

    if all_kids and all_parents:
        options["All children"] = [{"kid_id": kid_options[n], "parent_id": None} for n in all_kids]
        options["All parents"] = [{"kid_id": None, "parent_id": parent_options[n]} for n in all_parents]

    if all_kids:
        for name in all_kids:
            options[f"👧 {name}"] = [{"kid_id": kid_options[name], "parent_id": None}]

    if all_parents:
        for name in all_parents:
            options[f"👨‍👩‍👧 {name}"] = [{"kid_id": None, "parent_id": parent_options[name]}]

    return options


def generate_daily_dates(start_date, end_date):
    if end_date < start_date:
        return []

    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def generate_weekday_dates(start_date, end_date, selected_weekdays):
    if end_date < start_date:
        return []

    weekday_numbers = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    selected_weekday_numbers = [
        weekday_numbers[day]
        for day in selected_weekdays
    ]

    dates = []
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() in selected_weekday_numbers:
            dates.append(current_date)

        current_date += timedelta(days=1)

    return dates


# -----------------------
# Book List
# -----------------------

def book_list_tab(data):
    st.subheader("📚 Book List")

    st.info("Add, edit or remove books from your reading library.")

    book_templates = data["book_templates"]

    st.write("### ➕ Add New Book")

    with st.form("add_book_template_form"):
        title = st.text_input("Book name")
        writer = st.text_input("Writer/Author (optional)")

        col_lang, col_pages = st.columns(2)

        with col_lang:
            language = st.selectbox(
                "Language",
                ["English", "Turkish"],
                key="book_template_language"
            )

        with col_pages:
            total_pages = st.number_input(
                "Total pages",
                min_value=1,
                max_value=5000,
                value=100,
                key="book_template_total_pages"
            )

        submitted = st.form_submit_button("Add Book")

        if submitted:
            if not title.strip():
                st.error("Please enter the book name.")
                return

            add_book_template(
                title=title.strip(),
                language=language,
                total_pages=int(total_pages),
                writer=writer.strip() if writer else None
            )

            st.success("Book added to the book list.")
            st.rerun()

    st.divider()

    if not book_templates:
        st.caption("No books in the book list yet.")
        return

    st.write("### 📖 Your Books")

    for book in book_templates:
        lang_flag = "🇬🇧" if book.get("language") == "English" else "🇹🇷"

        with st.container(border=True):
            col_info, col_actions = st.columns([4, 1])

            with col_info:
                is_editing = st.session_state.get(f"edit_book_{book['id']}", False)

                if not is_editing:
                    writer_line = f"✍️ {book['writer']}" if book.get("writer") else "✍️ Unknown"

                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:15px;padding:8px 0;">'
                        f'<div style="width:50px;height:65px;background:linear-gradient(135deg,#FF8A80,#4ECDC4);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.5em;flex-shrink:0;">📖</div>'
                        f'<div>'
                        f'<div style="font-size:1.1em;font-weight:700;">{book["title"]}</div>'
                        f'<div style="color:#888;font-size:0.85em;">{writer_line} · {lang_flag} · {book["total_pages"]} pages</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    with st.form(f"edit_book_form_{book['id']}"):
                        new_title = st.text_input("Book name", value=book["title"], key=f"et_{book['id']}")
                        new_writer = st.text_input("Writer", value=book.get("writer", "") or "", key=f"ew_{book['id']}")

                        new_lang = st.selectbox(
                            "Language",
                            ["English", "Turkish"],
                            index=0 if book.get("language") == "English" else 1,
                            key=f"el_{book['id']}"
                        )

                        new_pages = st.number_input(
                            "Total pages",
                            min_value=1,
                            max_value=5000,
                            value=int(book.get("total_pages", 100)),
                            key=f"ep_{book['id']}"
                        )

                        edit_cols = st.columns(2)

                        with edit_cols[0]:
                            save_clicked = st.form_submit_button("💾 Save", use_container_width=True)

                        with edit_cols[1]:
                            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

                        if save_clicked:
                            if not new_title.strip():
                                st.error("Book name is required.")
                            else:
                                cleaned = clean_book_templates([{
                                    "id": book["id"],
                                    "title": new_title.strip(),
                                    "writer": new_writer.strip() if new_writer.strip() else None,
                                    "language": new_lang,
                                    "total_pages": int(new_pages)
                                }])

                                if cleaned:
                                    replace_book_template(book["id"], cleaned[0])

                                st.session_state[f"edit_book_{book['id']}"] = False
                                st.success("Book updated!")
                                st.rerun()

                        if cancel_clicked:
                            st.session_state[f"edit_book_{book['id']}"] = False
                            st.rerun()

                    continue

            with col_actions:
                if st.button("✏️", key=f"edit_btn_book_{book['id']}", help="Edit"):
                    st.session_state[f"edit_book_{book['id']}"] = True
                    st.rerun()

                if st.button("🗑️", key=f"del_btn_book_{book['id']}", help="Delete"):
                    delete_book_template(book["id"])
                    st.warning("Book removed.")
                    st.rerun()

def clean_book_templates(book_templates):
    cleaned = []

    for book in book_templates:
        title = str(book.get("title", "")).strip()

        if not title:
            continue

        language = book.get("language", "English")

        if language not in ["English", "Turkish"]:
            language = "English"

        total_pages = int(book.get("total_pages", 100))

        writer = str(book.get("writer", "")).strip() if book.get("writer") else None

        cleaned.append(
            {
                "title": title,
                "writer": writer,
                "language": language,
                "total_pages": total_pages
            }
        )

    return cleaned


# -----------------------
# Assign Book
# -----------------------

def assign_book_tab(data):
    st.subheader("📖 Assign Book")

    if not data["kids"] and not data.get("parents"):
        st.info("Add children or parents first.")
        return

    book_templates = data["book_templates"]

    if not book_templates:
        st.info("Add books to the Book List first.")
        return

    assignee_options = build_assignee_options(data)
    book_options = {
        f"{book['title']} {'— ' + book.get('writer', 'Unknown') if book.get('writer') else ''} ({book['language']}, {book['total_pages']} pages)": book
        for book in book_templates
    }

    with st.form("assign_book_form"):
        selected_book_label = st.selectbox(
            "Choose book from list",
            list(book_options.keys()),
            key="assign_book_select"
        )

        assign_to = st.selectbox(
            "Assign to",
            list(assignee_options.keys()),
            key="assign_book_to"
        )

        selected_book = book_options[selected_book_label]

        if selected_book.get("writer"):
            st.write(f"✍️ **{selected_book['writer']}**")

        st.write(f"Language: **{selected_book['language']}**")
        st.write(f"Total pages: **{selected_book['total_pages']}**")

        submitted = st.form_submit_button("Assign Book")

        if submitted:
            selected_assignees = assignee_options[assign_to]

            new_books = []

            for assignee in selected_assignees:
                new_book = {
                    "title": selected_book["title"],
                    "kid_id": assignee.get("kid_id"),
                    "parent_id": assignee.get("parent_id"),
                    "language": selected_book["language"],
                    "total_pages": int(selected_book["total_pages"]),
                    "current_page": 0,
                    "status": "In Progress"
                }

                new_books.append(new_book)

            add_books(new_books)

            st.success(f"{len(new_books)} book(s) assigned in Supabase.")
            st.rerun()


# -----------------------
# Settings
# -----------------------

def settings_tab():
    st.subheader("⚙️ Settings")

    st.info(
        "Main family data is now saved in Supabase. "
        "Profile photos are stored in Supabase Storage."
    )

    st.success("✅ Parent and child profiles with photos are fully available!")
