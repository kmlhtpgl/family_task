import streamlit as st
from datetime import date, datetime, timedelta

from utils.task_helpers import TASK_STATUSES
from utils.db_helpers import (
    add_kid,
    add_tasks,
    add_books,
    add_task_template,
    replace_task_templates,
    add_book_template,
    replace_book_templates
)


def admin_page(data):
    st.header("Admin Panel")
    st.caption("Add children, task templates, book templates, tasks and books.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Add Child",
            "Task List",
            "Assign Task",
            "Book List",
            "Assign Book",
            "Settings"
        ]
    )

    with tab1:
        add_child_tab()

    with tab2:
        task_list_tab(data)

    with tab3:
        assign_task_tab(data)

    with tab4:
        book_list_tab(data)

    with tab5:
        assign_book_tab(data)

    with tab6:
        settings_tab()


# -----------------------
# Add Child
# -----------------------

def add_child_tab():
    st.subheader("Add Child")

    st.warning(
        "For now, photos are not saved safely in Supabase Storage. "
        "We can add proper photo storage in the next step."
    )

    with st.form("add_child_form"):
        name = st.text_input("Child name")
        age = st.number_input("Age", min_value=1, max_value=18, value=6)

        submitted = st.form_submit_button("Add Child")

        if submitted:
            if not name.strip():
                st.error("Please enter the child’s name.")
                return

            add_kid(
                name=name.strip(),
                age=int(age),
                photo_path=None
            )

            st.success("Child added successfully.")
            st.rerun()


# -----------------------
# Task List
# -----------------------

def task_list_tab(data):
    st.subheader("Task List")

    st.info(
        "This task list is now saved in Supabase. "
        "It is no longer dependent on the local JSON file."
    )

    templates = data["task_templates"]

    st.write("### Add New Task Quickly")

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
    st.write("### Edit Task List")

    if not templates:
        st.caption("No tasks in the task list.")
        return

    edited_templates = st.data_editor(
        templates,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn(
                "ID",
                disabled=True
            ),
            "title": st.column_config.TextColumn(
                "Task Name",
                required=True
            ),
            "default_points": st.column_config.NumberColumn(
                "Points",
                min_value=1,
                max_value=100,
                required=True
            )
        },
        key="task_template_editor"
    )

    if st.button("Save Edited Task List"):
        cleaned_templates = clean_task_templates(edited_templates)
        replace_task_templates(cleaned_templates)

        st.success("Task list saved in Supabase.")
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
    st.subheader("Assign Task")

    if not data["kids"]:
        st.info("Add children first.")
        return

    task_templates = data["task_templates"]

    if not task_templates:
        st.info("Add tasks to the Task List first.")
        return

    kid_options = {
        kid["name"]: kid["id"]
        for kid in data["kids"]
    }

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
            ["All children"] + list(kid_options.keys())
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

            if assign_to == "All children":
                selected_kid_ids = list(kid_options.values())
            else:
                selected_kid_ids = [kid_options[assign_to]]

            new_tasks = []

            for due_date in selected_dates:
                for kid_id in selected_kid_ids:
                    new_task = {
                        "title": selected_template["title"],
                        "kid_id": kid_id,
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
    st.subheader("Book List")

    st.info(
        "This book list is now saved in Supabase. "
        "It is no longer dependent on the local JSON file."
    )

    book_templates = data["book_templates"]

    st.write("### Add New Book Quickly")

    with st.form("add_book_template_form"):
        title = st.text_input("Book name")

        language = st.selectbox(
            "Language",
            ["English", "Turkish"],
            key="book_template_language"
        )

        total_pages = st.number_input(
            "Total pages",
            min_value=1,
            max_value=5000,
            value=100,
            key="book_template_total_pages"
        )

        submitted = st.form_submit_button("Add Book to List")

        if submitted:
            if not title.strip():
                st.error("Please enter the book name.")
                return

            add_book_template(
                title=title.strip(),
                language=language,
                total_pages=int(total_pages)
            )

            st.success("Book added to the book list.")
            st.rerun()

    st.divider()
    st.write("### Edit Book List")

    if not book_templates:
        st.caption("No books in the book list.")
        return

    edited_books = st.data_editor(
        book_templates,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn(
                "ID",
                disabled=True
            ),
            "title": st.column_config.TextColumn(
                "Book Name",
                required=True
            ),
            "language": st.column_config.SelectboxColumn(
                "Language",
                options=["English", "Turkish"],
                required=True
            ),
            "total_pages": st.column_config.NumberColumn(
                "Total Pages",
                min_value=1,
                max_value=5000,
                required=True
            )
        },
        key="book_template_editor"
    )

    if st.button("Save Edited Book List"):
        cleaned_books = clean_book_templates(edited_books)
        replace_book_templates(cleaned_books)

        st.success("Book list saved in Supabase.")
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

        cleaned.append(
            {
                "title": title,
                "language": language,
                "total_pages": total_pages
            }
        )

    return cleaned


# -----------------------
# Assign Book
# -----------------------

def assign_book_tab(data):
    st.subheader("Assign Book")

    if not data["kids"]:
        st.info("Add children first.")
        return

    book_templates = data["book_templates"]

    if not book_templates:
        st.info("Add books to the Book List first.")
        return

    kid_options = {
        kid["name"]: kid["id"]
        for kid in data["kids"]
    }

    book_options = {
        f"{book['title']} ({book['language']}, {book['total_pages']} pages)": book
        for book in book_templates
    }

    with st.form("assign_book_form"):
        selected_book_label = st.selectbox(
            "Choose book from list",
            list(book_options.keys())
        )

        assign_to = st.selectbox(
            "Assign to",
            ["All children"] + list(kid_options.keys()),
            key="assign_book_to"
        )

        selected_book = book_options[selected_book_label]

        st.write(f"Language: **{selected_book['language']}**")
        st.write(f"Total pages: **{selected_book['total_pages']}**")

        submitted = st.form_submit_button("Assign Book")

        if submitted:
            if assign_to == "All children":
                selected_kid_ids = list(kid_options.values())
            else:
                selected_kid_ids = [kid_options[assign_to]]

            new_books = []

            for kid_id in selected_kid_ids:
                new_book = {
                    "title": selected_book["title"],
                    "kid_id": kid_id,
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
    st.subheader("Settings")

    st.info(
        "Main family data is now saved in Supabase. "
        "The old JSON files are no longer used for children, tasks, books, task lists or book lists."
    )

    st.warning(
        "Profile photos are not fully moved to Supabase Storage yet. "
        "That can be the next improvement."
    )
